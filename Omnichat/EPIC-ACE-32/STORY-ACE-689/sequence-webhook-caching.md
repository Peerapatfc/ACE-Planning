# ACE-972: Webhook Caching — Sequence Diagram

## Context

เพิ่ม caching layer ให้กับ inbound webhook flow เพื่อลด DB load และ duplicate processing โดยมี 2 ส่วนหลัก:

1. **Channel Mapping Cache** — cache `{channelId → tenant_id, channel_account_id}` ที่ Gateway เพื่อลด DB lookup ทุก request
2. **Payload Deduplication Cache** — เช็ค SHA256 hash ใน Redis ก่อนส่ง SQS เพื่อ reject duplicate webhook นอกเหนือจาก SQS FIFO 5-min dedup window

### Cache Strategy

| Cache | Storage | TTL | Invalidation |
|-------|---------|-----|-------------|
| Channel Mapping | Redis | 5 minutes | On channel config update (publish invalidation event) |
| Payload Dedup | Redis | 24 hours | Auto-expire (TTL only) |

---

## 1. Inbound Message Flow with Webhook Caching (Full)

แสดง flow เต็มตั้งแต่ webhook เข้ามาจนถึง persist โดยเน้น caching layer ที่เพิ่มเข้ามา

```mermaid
sequenceDiagram
    participant Channel as Channel Platform<br/>(LINE/Facebook/etc.)
    participant Gateway as Omnichat Gateway<br/>(omnichat-gateway :3010)
    participant Redis as Redis Cache
    participant SQS as AWS SQS FIFO
    participant Worker as Normalizer Worker<br/>(omnichat-normalizer-worker)
    participant OmniSvc as Omnichat Service<br/>(omnichat-service :3011)
    participant DB as PostgreSQL

    %% === PHASE 1: Webhook Reception ===
    Channel->>Gateway: POST /webhooks/{channel_type}
    Gateway->>Gateway: Validate signature (HMAC-SHA256)

    %% === PHASE 2: Channel Mapping Cache ===
    Note over Gateway,Redis: 🆕 Channel Mapping Cache
    Gateway->>Redis: GET channel_map:{platform}:{channelId}

    alt Cache HIT
        Redis-->>Gateway: { tenant_id, channel_account_id }
    else Cache MISS
        Redis-->>Gateway: null
        Gateway->>OmniSvc: GET /channels/resolve<br/>{ platform, channelId }
        OmniSvc->>DB: SELECT tenant_id, channel_account_id<br/>FROM channel_accounts<br/>WHERE platform = ? AND external_channel_id = ?
        DB-->>OmniSvc: { tenant_id, channel_account_id }
        OmniSvc-->>Gateway: { tenant_id, channel_account_id }
        Gateway->>Redis: SET channel_map:{platform}:{channelId}<br/>{ tenant_id, channel_account_id }<br/>EX 300 (5 min TTL)
    end

    alt Channel Not Found
        Gateway-->>Channel: 200 OK (silent drop — no retry)
        Note over Gateway: Log warning: unknown channel mapping
    end

    %% === PHASE 3: Payload Deduplication Cache ===
    Note over Gateway,Redis: 🆕 Payload Dedup Cache
    Gateway->>Gateway: Compute SHA256(payload)
    Gateway->>Redis: SET webhook_dedup:{hash}<br/>NX EX 86400 (24hr TTL, set-if-not-exists)

    alt Key Already Exists (Duplicate)
        Redis-->>Gateway: null (SET NX failed)
        Gateway-->>Channel: 200 OK (silent drop)
        Note over Gateway: Log info: duplicate webhook dropped
    else Key Set Successfully (New Event)
        Redis-->>Gateway: OK

        %% === PHASE 4: Publish to SQS ===
        Gateway->>SQS: SendMessage (FIFO)<br/>MessageGroupId: {platform}-{channelId}<br/>DeduplicationId: SHA256(payload)<br/>Body: { raw_payload, tenant_id, channel_account_id }
        SQS-->>Gateway: MessageId
        Gateway-->>Channel: 200 OK
    end

    %% === PHASE 5: Worker Consumes ===
    Note over SQS,Worker: Async — long polling (20s wait, 10 messages/batch)
    SQS->>Worker: ReceiveMessage (batch up to 10)

    %% === PHASE 6: PII Redaction ===
    Worker->>Worker: PII Redactor — redact(rawPayload, platform)

    %% === PHASE 7: Store Raw Event ===
    Worker->>OmniSvc: POST /raw-events<br/>{ redacted_payload, channel_type, tenant_id,<br/>channel_account_id, pii_safe }
    OmniSvc->>DB: INSERT raw_events
    DB-->>OmniSvc: raw_event_id
    OmniSvc-->>Worker: { raw_event_id }

    %% === PHASE 8: Normalize ===
    Worker->>Worker: ChannelMapper.normalize(rawPayload)

    alt Normalization Success
        %% === PHASE 9: Persist ===
        Worker->>OmniSvc: POST /messages/inbound<br/>{ contact, conversation, message }

        OmniSvc->>DB: UPSERT contacts<br/>ON CONFLICT (tenant_id, channel_type, external_user_id)
        DB-->>OmniSvc: contact_id

        OmniSvc->>DB: UPSERT conversations<br/>ON CONFLICT (tenant_id, channel_account_id, external_thread_id)
        DB-->>OmniSvc: conversation_id

        OmniSvc->>DB: INSERT messages<br/>ON CONFLICT (tenant_id, channel_type, external_message_id)<br/>DO NOTHING
        DB-->>OmniSvc: message_id

        OmniSvc-->>Worker: { contact_id, conversation_id, message_id, is_duplicate }

    else Normalization Failure
        Worker->>OmniSvc: PATCH /raw-events/:id<br/>{ normalization_status: 'failed', error_detail }
    end

    %% === PHASE 10: Acknowledge SQS ===
    Worker->>SQS: DeleteMessage
```

---

## 2. Channel Mapping Cache Invalidation

เมื่อ channel config ถูกแก้ไข (เช่น disable channel, เปลี่ยน tenant) ต้อง invalidate cache

```mermaid
sequenceDiagram
    participant Admin as Admin UI
    participant APIGw as API Gateway
    participant OmniSvc as Omnichat Service
    participant DB as PostgreSQL
    participant Redis as Redis Cache

    Admin->>APIGw: PUT /api/v1/channels/:id<br/>{ status: 'inactive', ... }
    APIGw->>OmniSvc: PUT /api/v1/channels/:id

    OmniSvc->>DB: UPDATE channel_accounts<br/>SET status = 'inactive'
    DB-->>OmniSvc: OK

    %% Invalidate cache
    Note over OmniSvc,Redis: 🆕 Cache Invalidation
    OmniSvc->>Redis: DEL channel_map:{platform}:{channelId}
    Redis-->>OmniSvc: OK

    OmniSvc-->>APIGw: { channel_id, status: 'inactive' }
    APIGw-->>Admin: 200 OK
```

---

## 3. Deduplication — Defense in Depth

แสดง 3 ชั้นของ deduplication ที่ทำงานร่วมกัน

```mermaid
flowchart TD
    A[Webhook Arrives] --> B{Redis Dedup Cache<br/>SET NX hash, TTL 24hr}
    B -->|Key exists: DUPLICATE| C[Drop + 200 OK<br/>Layer 1: Redis]
    B -->|Key set: NEW| D{SQS FIFO Dedup<br/>5-min window}
    D -->|Duplicate within 5min| E[SQS rejects silently<br/>Layer 2: SQS]
    D -->|Accepted| F[Worker processes]
    F --> G{DB INSERT ON CONFLICT<br/>DO NOTHING}
    G -->|Conflict: already exists| H[Skip insert, return is_duplicate=true<br/>Layer 3: DB]
    G -->|No conflict| I[Message persisted successfully]

    style B fill:#ff9,stroke:#333
    style D fill:#9cf,stroke:#333
    style G fill:#9f9,stroke:#333
```

---

## Cache Key Design

| Cache | Key Pattern | Value | TTL | Notes |
|-------|------------|-------|-----|-------|
| Channel Mapping | `channel_map:{platform}:{channelId}` | `{ tenant_id, channel_account_id, status }` | 5 min | Invalidate on channel config change |
| Payload Dedup | `webhook_dedup:{sha256_hash}` | `1` (flag) | 24 hr | `SET NX` — atomic check-and-set |

### Examples

```
# Channel Mapping
channel_map:line:U1234567890abcdef → { "tenant_id": "t_001", "channel_account_id": "ca_123" }

# Payload Dedup
webhook_dedup:a3f2b8c9d1e4... → 1
```

---

## Comparison: Before vs After

| Aspect | Before (No Cache) | After (With Cache) |
|--------|-------------------|-------------------|
| Channel resolve | DB query every request | Redis GET (sub-ms) → DB only on cache miss |
| Duplicate webhook | SQS 5-min dedup + DB ON CONFLICT | Redis 24hr dedup → SQS 5-min → DB ON CONFLICT |
| Gateway latency | ~50-100ms (DB lookup + SQS) | ~5-10ms (cache hit) / ~50-100ms (cache miss) |
| DB load (resolve) | O(n) queries per n webhooks | O(1) per TTL window per channel |
| Duplicate protection window | 5 min (SQS) | 24 hr (Redis) + 5 min (SQS) + forever (DB) |
