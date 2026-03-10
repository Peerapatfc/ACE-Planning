# ACE-37 (NDP-01): Define Normalized Schema v1 — Sequence Diagram (Microservice Architecture)

## Context

Sequence diagrams aligned with the actual microservice architecture of the project — clearly separated services communicating via **AWS SQS FIFO** (webhook → normalizer) and **HTTP** (inter-service sync calls).

---

## Service Overview

| Service | App Name (code) | Responsibility | Transport |
|---|---|---|---|
| **Omnichat Gateway** | `omnichat-gateway` | Inbound only — receive webhooks, validate signature, publish to SQS | HTTP REST (port 3010) |
| **Normalizer Worker** | `omnichat-normalizer-worker` | Poll SQS, PII redaction, normalize, download attachments — persist ผ่าน Omnichat Service (HTTP) | SQS Consumer (background) |
| **Omnichat Service** | `omnichat-service` | Core business logic — outbound messages (send directly to channel APIs), conversation management | HTTP (port 3011) |
| **File Service** | `file-service` | Manage S3 (presigned upload URL, binary upload — public bucket, static URLs) | HTTP (inter-service) |
| **API Gateway** | `api-gateway` | Entry point, routing, auth | HTTP REST (port 3000) |

### Rate Limiting (Omnichat Gateway)

| Window | Limit |
|---|---|
| Short (per second) | 5 requests |
| Long (per minute) | 100 requests |

---

## 1. Inbound Message Flow

```mermaid
sequenceDiagram
    participant Channel as Channel Platform<br/>(LINE/Facebook/Instagram/TikTok/Shopee/Lazada)
    participant Gateway as Omnichat Gateway<br/>(omnichat-gateway)
    participant SQS as AWS SQS FIFO
    participant Worker as Normalizer Worker<br/>(omnichat-normalizer-worker)
    participant OmniSvc as Omnichat Service<br/>(omnichat-service :3011)
    participant DB as PostgreSQL
    participant FileSvc as File Service
    participant S3 as S3

    %% Step 1: Receive webhook
    Channel->>Gateway: POST /webhooks/{channel_type}
    Gateway->>Gateway: Validate signature (HMAC-SHA256)<br/>& validate channel (channelId active?)

    %% Step 2: Publish to SQS FIFO
    Gateway->>SQS: SendMessage (FIFO)<br/>MessageGroupId: {platform}-{channelId}<br/>DeduplicationId: SHA256(payload)
    Note over Gateway,SQS: RawWebhookMessage:<br/>{ platform, channelId, rawPayload,<br/>timestamp, signature, headers }
    SQS-->>Gateway: MessageId
    Gateway-->>Channel: 200 OK

    %% Step 3: Worker polls SQS (async, does not block webhook response)
    Note over SQS,Worker: Async — long polling (20s wait, 10 messages/batch)
    SQS->>Worker: ReceiveMessage (batch up to 10)<br/>VisibilityTimeout: 5 min
    Worker->>Worker: Parse RawWebhookMessage

    %% Step 4: PII Redaction (platform fields only, message content is NOT redacted)
    Worker->>Worker: PII Redactor — redact(rawPayload, platform)
    Note over Worker: Redact: userId, display_name, avatar_url,<br/>phone, email, recipient_address<br/>NOT redacted: message text/caption<br/>→ redacted_payload (pii_safe=true)

    %% Step 5: Store raw event
    Worker->>OmniSvc: POST /internal/raw-events<br/>{ redacted_payload, channel_type, tenant_id, pii_safe }
    OmniSvc->>DB: INSERT raw_events<br/>(redacted_payload, channel_type, tenant_id, pii_safe=true)
    DB-->>OmniSvc: raw_event_id
    OmniSvc-->>Worker: { raw_event_id }

    %% Step 6: Normalize via Channel Mapper (Strategy Pattern)
    Worker->>Worker: ChannelMapper.normalize(rawPayload)<br/>LINE → LineMapper<br/>Facebook → FacebookMapper<br/>Instagram → InstagramMapper<br/>TikTok → TikTokMapper<br/>Shopee → ShopeeMapper<br/>Lazada → LazadaMapper

    %% Step 7: Persist normalized data
    Worker->>OmniSvc: POST /internal/messages/inbound<br/>{ contact, conversation, message, attachments_metadata? }
    OmniSvc->>DB: UPSERT contacts<br/>ON CONFLICT (tenant_id, channel_type, external_user_id)<br/>DO UPDATE SET display_name, last_seen_at
    DB-->>OmniSvc: contact_id

    OmniSvc->>DB: UPSERT conversations<br/>ON CONFLICT (tenant_id, channel_account_id, external_thread_id)<br/>DO UPDATE SET last_message_at, last_message_preview
    DB-->>OmniSvc: conversation_id

    OmniSvc->>DB: INSERT messages<br/>ON CONFLICT (tenant_id, channel_type, external_message_id)<br/>DO NOTHING
    DB-->>OmniSvc: message_id

    OmniSvc-->>Worker: { contact_id, conversation_id, message_id }

    %% Step 8: Acknowledge SQS message (before downloading attachments)
    Worker->>SQS: DeleteMessage
    Note over Worker: Core message processing complete —<br/>acknowledge early to avoid blocking the queue

    %% Step 9: Handle attachments (fire-and-forget after acknowledge)
    alt Has Attachments
        Worker->>OmniSvc: POST /internal/attachments<br/>{ message_id, type, content_type, tenant_id }
        OmniSvc->>DB: INSERT attachments<br/>(message_id, type, content_type, status='pending', tenant_id)
        DB-->>OmniSvc: attachment_id
        OmniSvc-->>Worker: { attachment_id }

        Worker->>Channel: Download file from channel URL
        Channel-->>Worker: binary file + content_type
        Worker->>Worker: SHA-256 checksum(binary)
        Worker->>FileSvc: POST /files/upload<br/>{ binary, content_type, tenant_id, folder: 'attachments' }
        FileSvc->>S3: PutObject
        S3-->>FileSvc: storage_key
        FileSvc-->>Worker: { storage_key }
        Worker->>OmniSvc: PATCH /internal/attachments/:id<br/>{ storage_key, size, checksum, status: 'uploaded' }
        OmniSvc->>DB: UPDATE attachments<br/>SET storage_key=?, status='uploaded',<br/>size=?, checksum=?<br/>WHERE id=? AND tenant_id=?

        alt Download or Upload Failed
            Worker->>OmniSvc: PATCH /internal/attachments/:id<br/>{ status: 'failed' }
            OmniSvc->>DB: UPDATE attachments<br/>SET status='failed' WHERE id=?
            Note over Worker: Log error — message is already persisted.<br/>Failed attachments will be retried via scheduled job later.
        end
    end
```

---

## 2. Outbound Message Flow

```mermaid
sequenceDiagram
    participant Agent as Agent / System
    participant APIGw as API Gateway<br/>(api-gateway :3000)
    participant OmniSvc as Omnichat Service<br/>(omnichat-service :3011)
    participant FileSvc as File Service
    participant DB as PostgreSQL
    participant S3 as S3
    participant Channel as Channel Platform<br/>(LINE/Facebook/Instagram/TikTok/Shopee/Lazada)

    %% Step 1: Agent sends message
    Agent->>APIGw: POST /api/v1/messages<br/>{ conversation_id, content, attachments? }
    APIGw->>APIGw: Auth & extract tenant_id

    %% Step 2: Route to Omnichat Service
    APIGw->>OmniSvc: POST /api/v1/messages<br/>{ conversation_id, content, tenant_id, attachments? }
    OmniSvc->>OmniSvc: Validate conversation ownership

    %% Step 3: Upload attachments via File Service (if any)
    alt Has Attachments
        OmniSvc->>FileSvc: POST /files/presigned-url<br/>{ filename, folder, tenant_id }
        FileSvc->>S3: CreatePresignedUrl
        S3-->>FileSvc: presigned_url
        FileSvc-->>OmniSvc: { upload_url, storage_key, file_url }
        OmniSvc->>S3: PUT binary file (via presigned URL)
        S3-->>OmniSvc: 200 OK
    end

    %% Step 4: Persist message
    OmniSvc->>DB: INSERT messages<br/>(conversation_id, direction='outbound',<br/>content, status='pending', tenant_id)
    DB-->>OmniSvc: message_id

    %% Step 5: Persist attachments (if any)
    alt Has Attachments
        OmniSvc->>DB: INSERT attachments<br/>(message_id, storage_key, file_url, status='uploaded', tenant_id)
    end

    %% Step 6: Update conversation
    OmniSvc->>DB: UPDATE conversations<br/>SET last_message_at=NOW(), last_message_preview=content

    %% Step 7: Send directly to channel platform
    OmniSvc->>OmniSvc: Resolve channel credentials<br/>& build platform-specific payload
    OmniSvc->>Channel: Send message via Channel API<br/>(LINE Reply/Push, FB Send API, etc.)
    Channel-->>OmniSvc: external_message_id

    %% Step 8: Update message status
    OmniSvc->>DB: UPDATE messages<br/>SET external_message_id=?, status='sent'

    alt Channel API Failed
        OmniSvc->>DB: UPDATE messages<br/>SET status='failed'
        OmniSvc-->>APIGw: { message_id, status: 'failed', error }
        APIGw-->>Agent: 500 { message_id, status: 'failed', error }
    end

    OmniSvc-->>APIGw: { message_id, status: 'sent' }
    APIGw-->>Agent: 200 OK { message_id, status: 'sent' }
```

---

## 3. Query Conversation Timeline

```mermaid
sequenceDiagram
    participant Client as Inbox UI / AI
    participant APIGw as API Gateway<br/>(api-gateway :3000)
    participant OmniSvc as Omnichat Service<br/>(omnichat-service :3011)
    participant DB as PostgreSQL

    %% Step 1: Client requests timeline
    Client->>APIGw: GET /api/v1/conversations/{id}/messages<br/>?cursor=&limit=20
    APIGw->>APIGw: Auth & extract tenant_id

    %% Step 2: Route to Omnichat Service
    APIGw->>OmniSvc: GET /api/v1/conversations/:id/messages<br/>{ conversation_id, cursor, limit, tenant_id }
    OmniSvc->>OmniSvc: Validate conversation ownership

    %% Step 3: Query messages
    OmniSvc->>DB: SELECT messages<br/>WHERE tenant_id=? AND conversation_id=?<br/>AND deleted_at IS NULL<br/>AND created_at < cursor<br/>ORDER BY created_at DESC<br/>LIMIT 21
    DB-->>OmniSvc: messages[] (limit+1 for has_more)

    %% Step 4: Query attachments (metadata + file_url)
    OmniSvc->>DB: SELECT attachments<br/>WHERE message_id IN (...)<br/>AND deleted_at IS NULL
    DB-->>OmniSvc: attachments[] (includes file_url for uploaded)

    %% Step 5: Build response
    OmniSvc->>OmniSvc: Merge attachment metadata + file_url into messages,<br/>build next_cursor from last item's created_at

    OmniSvc-->>APIGw: { data: messages[], meta: { cursor, has_more } }
    APIGw-->>Client: 200 OK { data: messages[], meta: { cursor, has_more } }
```

---

## SQS FIFO Configuration

| Setting | Value | Rationale |
|---|---|---|
| **Queue Type** | FIFO (.fifo) | Exactly-once processing, message ordering per group |
| **MessageGroupId** | `{platform}-{channelId}` | Messages from the same channel are processed in order |
| **DeduplicationId** | SHA256(payload content) | Prevent duplicate webhook delivery |
| **VisibilityTimeout** | 5 minutes | Allow worker time to process before message returns to queue |
| **WaitTimeSeconds** | 20 seconds | Long polling — reduce empty receives |
| **MaxMessages** | 10 per batch | Worker receives a batch and processes with Promise.allSettled() |

---

## Service Communication Map

```
┌──────────────┐
│   Channel    │
│  Platforms   │
└──────┬───────┘
       │ Webhook (HTTP)              ▲
       ▼                             │ Channel API (HTTP)
┌──────────────────┐    SQS FIFO    ┌──────────────────────┐
│ Omnichat Gateway │───────────────▶│  Normalizer Worker    │
│ (omnichat-gateway│                │  (omnichat-normalizer │
│  :3010)          │                │   -worker)            │
│                  │                │                       │
│ Inbound only:    │                │  - PII Redactor       │
│  - Signature     │                │  - Channel Mapper     │
│    Validation    │                │    (Strategy Pattern)  │
│  - Rate Limiting │                │  - Attachment download │
│    (5/s, 100/m)  │                │    (fire-and-forget)  │
│  - SQS publish   │                │  - Persist ผ่าน       │
└──────────────────┘                │    OmniSvc (HTTP)     │
                                    └──────┬──────┬─────────┘
                                           │      │
                                      HTTP ┘      │ HTTP
                                     (persist)    │ (upload)
                                           │      │
                                           ▼      ▼
                              ┌──────────────┐  ┌──────────────┐
                              │ Omnichat     │  │ File Service │──▶ S3
                              │ Service      │  │ (file-service│
                              │ (omnichat-   │  │  :HTTP)      │
                              │  service     │  └──────────────┘
                              │  :3011)      │        ▲
                              │              │        │ HTTP
                              │  - DB owner  │────────┘
                              │  - Resolve   │
                              │    credentials│
                              │  - Build     │──▶ Channel Platforms
                              │    payload   │    (HTTP — outbound)
                              │  - Send to   │
                              │    Channel   │
                              └──────┬───────┘
                                     │
                                     │ DB
                                     ▼
                              ┌──────────┐
                              │PostgreSQL│
                              └──────────┘
                                     ▲
                                     │ HTTP
┌──────────────┐             ┌──────────────┐
│   Agent /    │             │ API Gateway  │
│   Inbox UI   │────HTTP────▶│ (api-gateway │
└──────────────┘             │  :3000)      │
                             └──────────────┘
```

---

## Changes from Original (sequence.md)

| Topic | Original (sequence.md) | Updated (microservice — matches code) |
|---|---|---|
| **Webhook** | Webhook Receiver (single service) | `omnichat-gateway` as separate service — port 3010 |
| **Webhook → Normalizer** | Direct call | **AWS SQS FIFO** — async, decoupled |
| **Rate Limiting** | None | Throttler: 5 req/sec, 100 req/min |
| **Normalization** | Single pipeline handles everything (sync) | `omnichat-normalizer-worker` polls SQS (async) |
| **Message Ordering** | Implicit | SQS FIFO MessageGroupId: `{platform}-{channelId}` |
| **Deduplication** | None | SHA256 content-based deduplication |
| **Channel Mapper** | Generic "Normalize via Channel Mapper" | Strategy Pattern — each channel has its own Mapper |
| **DB Access** | All services call DB directly | **Omnichat Service เป็น DB owner ตัวเดียว** — Normalizer Worker persist ผ่าน OmniSvc (HTTP internal API) |
| **File Upload (outbound)** | API → S3 directly | API Gateway → Omnichat Service → File Service (HTTP) → S3 |
| **Attachment Download** | Queue → Worker → S3 (implicit) | Normalizer Worker handles it (fire-and-forget after SQS acknowledge) → File Service (HTTP) → S3 |
| **Attachment Download URL** | Not shown | Static public URL from DB (`file_url`) — no presigned download needed |
| **API Gateway** | Single "Omni API" | `api-gateway` :3000 routes to `omnichat-service` via HTTP |
| **Queue** | Amazon SQS (name only) | Full SQS FIFO flow: Send → Receive → Process → Delete |
| **Attachment Worker** | Separate worker | Not separated (MVP) — Normalizer Worker handles it; can split later if needed for scale |

---

## Implementation Status

| Component | Status | Notes |
|---|---|---|
| `omnichat-gateway` | **Partial** | LINE + Facebook webhook implemented; Instagram/TikTok/Shopee/Lazada are stubs |
| `omnichat-normalizer-worker` | **Scaffold** | SQS consumer works but missing PII redaction, Channel Mapper, attachment download — DB persist ผ่าน OmniSvc (HTTP) |
| `omnichat-service` | **Scaffold** | Nearly empty — no business logic yet |
| `file-service` | **Exists** | Already in use (shared with knowledge base) |
| Prisma Schema (omnichat tables) | **Not started** | No contacts, conversations, messages, attachments, raw_events tables yet |
| Shared Types | **Partial** | `PlatformType` enum + `RawWebhookMessage` exist but are duplicated across 2 services (not yet moved to shared package) |
