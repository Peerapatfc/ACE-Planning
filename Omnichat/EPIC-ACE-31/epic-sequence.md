# EPIC ACE-31: Normalized Data Platform v1 — Consolidated Sequence Diagram

## Context

Consolidated sequence diagrams covering the full Normalized Data Platform — from webhook ingestion through normalization, persistence, attachment handling, and query APIs. Architecture follows the microservice layout defined in NDP-01.

### Source Stories

| Story | Flow Coverage |
|---|---|
| ACE-37 (NDP-01) | Microservice architecture, inbound/outbound/query flows (physical layout) |
| ACE-38 (NDP-02) | Persistence patterns: idempotent inserts, deterministic upserts, fallback thread key |
| ACE-39 (NDP-03) | Normalization: channel mappers, PII redaction, marketplace events, failure isolation |
| ACE-40 (NDP-04) | Attachment pipeline: async download, retry with backoff, signed URL retrieval |
| ACE-41 (NDP-05) | Query APIs: conversation list, timeline pagination, concurrent write consistency |

---

## Service Overview

| Service | App Name | Responsibility | Transport |
|---|---|---|---|
| **Omnichat Gateway** | `omnichat-gateway` | Inbound only — receive webhooks, validate signature, publish to SQS | HTTP REST (:3010) |
| **Normalizer Worker** | `omnichat-normalizer-worker` | Poll SQS, PII redaction, normalize, download attachments — persist via Omnichat Service (HTTP) | SQS Consumer |
| **Omnichat Service** | `omnichat-service` | Core business logic — DB owner, outbound messages, conversation management | HTTP (:3011) |
| **File Service** | `file-service` | Manage S3 (presigned upload URL, binary upload — public bucket, static URLs) | HTTP (inter-service) |
| **API Gateway** | `api-gateway` | Entry point, routing, auth | HTTP REST (:3000) |

### Rate Limiting (Omnichat Gateway)

| Window | Limit |
|---|---|
| Short (per second) | 5 requests |
| Long (per minute) | 100 requests |

### SQS FIFO Configuration

| Setting | Value | Rationale |
|---|---|---|
| Queue Type | FIFO (.fifo) | Exactly-once processing, message ordering per group |
| MessageGroupId | `{platform}-{channelId}` | Messages from the same channel are processed in order |
| DeduplicationId | SHA256(payload content) | Prevent duplicate webhook delivery |
| VisibilityTimeout | 5 minutes | Allow worker time to process before message returns to queue |
| WaitTimeSeconds | 20 seconds | Long polling — reduce empty receives |
| MaxMessages | 10 per batch | Worker receives a batch and processes with Promise.allSettled() |

---

## 1. Inbound Message Flow (Full End-to-End)

Combines: NDP-01 architecture + NDP-03 normalization + NDP-02 persistence + NDP-04 attachment handling

```mermaid
sequenceDiagram
    participant Channel as Channel Platform<br/>(LINE/Facebook/Instagram/TikTok/Shopee/Lazada)
    participant Gateway as Omnichat Gateway<br/>(omnichat-gateway :3010)
    participant SQS as AWS SQS FIFO
    participant Worker as Normalizer Worker<br/>(omnichat-normalizer-worker)
    participant OmniSvc as Omnichat Service<br/>(omnichat-service :3011)
    participant DB as PostgreSQL
    participant FileSvc as File Service
    participant S3 as S3

    %% === PHASE 1: Webhook Reception (NDP-01) ===
    Channel->>Gateway: POST /webhooks/{channel_type}
    Gateway->>Gateway: Validate signature (HMAC-SHA256)<br/>& validate channel (channelId active?)

    Gateway->>SQS: SendMessage (FIFO)<br/>MessageGroupId: {platform}-{channelId}<br/>DeduplicationId: SHA256(payload)
    SQS-->>Gateway: MessageId
    Gateway-->>Channel: 200 OK

    %% === PHASE 2: Worker Consumes (NDP-01, NDP-03) ===
    Note over SQS,Worker: Async — long polling (20s wait, 10 messages/batch)
    SQS->>Worker: ReceiveMessage (batch up to 10)<br/>VisibilityTimeout: 5 min

    %% === PHASE 3: PII Redaction (NDP-03) ===
    Worker->>Worker: PII Redactor — redact(rawPayload, platform)
    Note over Worker: Redact: userId, display_name, avatar_url,<br/>phone, email, recipient_address<br/>NOT redacted: message text/caption

    %% === PHASE 4: Store Raw Event (NDP-01, NDP-03) ===
    Worker->>OmniSvc: POST /raw-events<br/>{ redacted_payload, channel_type, tenant_id,<br/>source_category, fetch_batch_id?, pii_safe }
    OmniSvc->>DB: INSERT raw_events
    DB-->>OmniSvc: raw_event_id
    OmniSvc-->>Worker: { raw_event_id }

    %% === PHASE 5: Normalize (NDP-03) ===
    Worker->>Worker: ChannelMapper.normalize(rawPayload)<br/>Strategy Pattern per channel

    alt Normalization Success
        %% === PHASE 6: Persist (NDP-02) ===
        Worker->>OmniSvc: POST /messages/inbound<br/>{ contact, conversation, message, attachments_metadata? }

        OmniSvc->>DB: UPSERT contacts<br/>ON CONFLICT (tenant_id, channel_type, external_user_id)<br/>DO UPDATE SET display_name, avatar_url, last_seen_at
        DB-->>OmniSvc: contact_id (stable)

        OmniSvc->>OmniSvc: Resolve thread key<br/>(external_thread_id or fallback_thread_key)
        OmniSvc->>DB: UPSERT conversations<br/>ON CONFLICT (tenant_id, channel_account_id, external_thread_id)<br/>DO UPDATE SET last_message_at, last_message_preview, is_read=false
        DB-->>OmniSvc: conversation_id (stable)

        OmniSvc->>DB: INSERT messages<br/>ON CONFLICT (tenant_id, channel_type, external_message_id)<br/>DO NOTHING
        DB-->>OmniSvc: message_id

        OmniSvc-->>Worker: { contact_id, conversation_id, message_id, is_duplicate }

    else Normalization Failure (NDP-03)
        Worker->>OmniSvc: PATCH /raw-events/:id<br/>{ normalization_status: 'failed', error_detail, error_context }
        OmniSvc->>DB: UPDATE raw_events SET normalization_status='failed', error_detail, error_context
        Note over Worker: Failure isolated — next event continues
    end

    %% === PHASE 7: Acknowledge SQS ===
    Worker->>SQS: DeleteMessage
    Note over Worker: Core message processing complete —<br/>acknowledge early to avoid blocking the queue

    %% === PHASE 8: Async Attachment Download (NDP-04) ===
    alt Has Attachments
        Worker->>OmniSvc: POST /attachments<br/>{ message_id, type, content_type, download_url, tenant_id }
        OmniSvc->>DB: INSERT attachments (status='pending')
        DB-->>OmniSvc: attachment_id
        OmniSvc-->>Worker: { attachment_id }

        Worker->>Channel: Download file from channel URL
        Worker->>Worker: Validate size & content_type

        alt Download & Validation OK
            Worker->>Worker: SHA-256 checksum(binary)
            Worker->>FileSvc: POST /files/upload<br/>{ binary, content_type, tenant_id, folder }
            FileSvc->>S3: PutObject (public bucket)
            S3-->>FileSvc: { storage_key, file_url }
            FileSvc-->>Worker: { storage_key, file_url }
            Worker->>OmniSvc: PATCH /attachments/:id<br/>{ storage_key, file_url, size, checksum, status: 'uploaded' }

        else Download Failed (retryable)
            Worker->>OmniSvc: PATCH /attachments/:id<br/>{ retry_count+=1 }
            Note over Worker: Re-enqueue with backoff<br/>(delay: 2^retry_count * 1000ms)<br/>Max 3 retries → then status='failed'

        else Validation Failed (size/type)
            Worker->>OmniSvc: PATCH /attachments/:id<br/>{ status: 'rejected', failure_reason }
        end
    end
```

---

## 2. Outbound Message Flow

Combines: NDP-01 architecture + NDP-02 persistence

```mermaid
sequenceDiagram
    participant Agent as Agent / System
    participant APIGw as API Gateway<br/>(api-gateway :3000)
    participant OmniSvc as Omnichat Service<br/>(omnichat-service :3011)
    participant FileSvc as File Service
    participant DB as PostgreSQL
    participant S3 as S3
    participant Channel as Channel Platform

    %% Step 1: Agent sends message
    Agent->>APIGw: POST /api/v1/messages<br/>{ conversation_id, content, attachments? }
    APIGw->>APIGw: Auth & extract tenant_id

    %% Step 2: Validate & route
    APIGw->>OmniSvc: POST /api/v1/messages<br/>{ conversation_id, content, tenant_id, attachments? }
    OmniSvc->>OmniSvc: Validate conversation ownership (tenant_id)

    %% Step 3: Upload attachments via File Service (if any)
    alt Has Attachments
        OmniSvc->>FileSvc: POST /files/presigned-url<br/>{ filename, folder, tenant_id }
        FileSvc->>S3: CreatePresignedUrl (public bucket)
        S3-->>FileSvc: presigned_url
        FileSvc-->>OmniSvc: { upload_url, storage_key, file_url }
        OmniSvc->>S3: PUT binary file (via presigned URL)
        S3-->>OmniSvc: 200 OK
    end

    %% Step 4: Persist message (NDP-02)
    OmniSvc->>DB: INSERT messages<br/>(conversation_id, direction='outbound',<br/>content, sender_type='agent',<br/>sender_display_name, status='pending', tenant_id)
    DB-->>OmniSvc: message_id

    %% Step 5: Persist attachments (if any)
    alt Has Attachments
        OmniSvc->>DB: INSERT attachments<br/>(message_id, storage_key, file_url, status='uploaded', tenant_id)
    end

    %% Step 6: Update conversation
    OmniSvc->>DB: UPDATE conversations<br/>SET last_message_at=NOW(), last_message_preview=content

    %% Step 7: Send to channel platform
    OmniSvc->>OmniSvc: Resolve channel credentials<br/>& build platform-specific payload
    OmniSvc->>Channel: Send message via Channel API<br/>(LINE Reply/Push, FB Send API, etc.)
    Channel-->>OmniSvc: external_message_id

    %% Step 8: Update status
    OmniSvc->>DB: UPDATE messages<br/>SET external_message_id=?, status='sent'

    alt Channel API Failed
        OmniSvc->>DB: UPDATE messages SET status='failed'
        OmniSvc-->>APIGw: { message_id, status: 'failed', error }
        APIGw-->>Agent: 500 { message_id, status: 'failed', error }
    end

    OmniSvc-->>APIGw: { message_id, status: 'sent' }
    APIGw-->>Agent: 200 OK { message_id, status: 'sent' }
```

---

## 3. Query Conversation List (Inbox View)

Source: NDP-05

```mermaid
sequenceDiagram
    participant Client as Inbox UI / AI
    participant APIGw as API Gateway<br/>(api-gateway :3000)
    participant OmniSvc as Omnichat Service<br/>(omnichat-service :3011)
    participant DB as PostgreSQL

    Client->>APIGw: GET /api/v1/conversations<br/>?status=open&channel_type=LINE<br/>&cursor=&limit=20
    APIGw->>APIGw: Auth & extract tenant_id

    APIGw->>OmniSvc: GET /api/v1/conversations<br/>{ tenant_id, status, channel_type, cursor, limit }

    OmniSvc->>DB: Query conversations JOIN contacts<br/>(filter: tenant, status, channel_type, cursor)<br/>ORDER BY last_message_at DESC LIMIT 21
    DB-->>OmniSvc: conversations[] (limit+1 for has_more)

    OmniSvc->>OmniSvc: Build response with contact info,<br/>channel badge, last_message_preview

    OmniSvc-->>APIGw: { data: conversations[], meta: { cursor, has_more } }
    APIGw-->>Client: 200 OK
```

> **Pagination consistency:** Cursor-based pagination on `last_message_at` ensures no duplicates or skips under concurrent writes. New messages (with newer timestamps) do not affect pages already fetched.

---

## 4. Query Conversation Timeline (Messages + Attachments)

Combines: NDP-01 architecture + NDP-02 persistence + NDP-05 query API

> **Note:** Timeline returns attachment metadata **including `file_url`** (static public URL, no expiry) for uploaded attachments. A separate endpoint `GET /api/v1/attachments/:id/download` is available for attachment status checks (pending/failed), but not shown here as the primary access path is via timeline.

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
    OmniSvc->>OmniSvc: Validate conversation ownership (tenant_id)

    %% Step 3: Query messages (NDP-02)
    OmniSvc->>DB: Query messages by conversation<br/>(filter: tenant, cursor)<br/>ORDER BY created_at DESC LIMIT 21
    DB-->>OmniSvc: messages[] (limit+1 for has_more)

    %% Step 4: Query attachments (metadata + file_url)
    OmniSvc->>DB: Query attachments for fetched messages
    DB-->>OmniSvc: attachments[] (includes file_url for uploaded)

    %% Step 5: Build response
    OmniSvc->>OmniSvc: Merge attachment metadata + file_url into messages,<br/>build next_cursor from last item's created_at

    OmniSvc-->>APIGw: { data: messages[], meta: { cursor, has_more } }
    APIGw-->>Client: 200 OK
```

> **Pagination consistency:** Cursor-based pagination on `created_at` ensures no duplicates or skips under concurrent writes. New messages appear via real-time push (WebSocket/SSE), not via pagination.

---

## 5. Marketplace Normalization (Shopee/Lazada)

Source: NDP-03

```mermaid
sequenceDiagram
    participant Source as Webhook / Polling Collector
    participant Worker as Normalizer Worker
    participant OmniSvc as Omnichat Service
    participant DB as PostgreSQL

    Source->>Worker: Raw marketplace event (via SQS)

    alt event_category = chat_message
        Worker->>Worker: MarketplaceMapper.normalizeChat(rawPayload)
        Worker->>OmniSvc: POST /messages/inbound<br/>{ contact, conversation, message }
        OmniSvc-->>Worker: { message_id }

    else event_category = order_reference
        Worker->>Worker: MarketplaceMapper.normalizeOrderRef(rawPayload)
        Worker->>OmniSvc: POST /messages/inbound<br/>{ message with metadata: marketplace_order_id, shop_id, order_status_ref }
        OmniSvc-->>Worker: { message_id }

    else event_category = fetch_history
        Worker->>Worker: MarketplaceMapper.normalizeHistoryBatch(rawPayload)
        loop Each message in batch
            Worker->>OmniSvc: POST /messages/inbound<br/>{ message, fetch_batch_id }
            Note over OmniSvc: Idempotency prevents duplicates<br/>if history overlaps with live messages
        end
    end

    Worker-->>Source: { success, processed_count }
```


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
│  - SQS publish   │                │  - Persist via        │
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
                              │  - Outbound  │
                              │    send      │──▶ Channel Platforms
                              │  - Business  │    (HTTP — outbound)
                              │    logic     │
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

## Flow Summary

| # | Flow | Direction | Sync/Async | Source Stories | Key Points |
|---|---|---|---|---|---|
| 1 | Inbound Message | Channel → System | Async (SQS) | NDP-01,02,03,04 | Fast webhook response, PII redaction, idempotent persist, async attachments |
| 2 | Outbound Message | System → Channel | Sync send | NDP-01,02 | Upload S3 first, persist, then send to channel |
| 3 | Conversation List | Client ← System | Sync read | NDP-05 | Cursor pagination on last_message_at, no duplicates under concurrent writes |
| 4 | Message Timeline | Client ← System | Sync read | NDP-02,04,05 | Cursor pagination on created_at, attachment metadata + file_url (static public URL) |
| 5 | Marketplace Normalization | Webhook/Poll → System | Async | NDP-03 | Chat, order reference, fetch history batch |
