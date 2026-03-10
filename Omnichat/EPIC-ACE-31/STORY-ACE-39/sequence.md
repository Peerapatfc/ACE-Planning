# ACE-39 (NDP-03): Normalization Pipeline v1 — Sequence Diagram

## Context

Sequence diagrams for the normalization layer: converting raw channel payloads into normalized schema v1 objects. Covers social channels, marketplace channels, PII redaction, and failure isolation.

---

## 1. Unified Normalization Flow (Social Channels)

```mermaid
sequenceDiagram
    participant Webhook as Webhook Receiver
    participant Pipeline as Normalization Pipeline
    participant Mapper as Channel Mapper<br/>(LINE/FB/IG/TikTok)
    participant PII as PII Redactor
    participant Persist as Persistence Service<br/>(NDP-02)
    participant DB as PostgreSQL

    Webhook->>Pipeline: ingestEvent(raw_payload, channel_type, tenant_id)

    Pipeline->>PII: redactSensitiveFields(raw_payload)
    PII-->>Pipeline: redacted_payload

    Pipeline->>DB: INSERT raw_events (redacted_payload, channel_type, tenant_id)
    DB-->>Pipeline: raw_event_id

    Pipeline->>Mapper: normalize(raw_payload, channel_type)

    alt Normalization Success
        Mapper-->>Pipeline: NormalizedEvent { tenant_id, channel_type, external_ids, content, ... }
        Pipeline->>DB: UPDATE raw_events SET normalization_status='success'
        Pipeline->>Persist: persistInboundMessage(normalizedEvent, raw_event_id)
        Persist-->>Pipeline: { message_id, contact_id, conversation_id, is_duplicate }
        Pipeline-->>Webhook: { success: true, message_id }
    else Normalization Failure
        Mapper-->>Pipeline: NormalizationError { reason, field }
        Pipeline->>DB: UPDATE raw_events SET normalization_status='failed',<br/>error_detail, error_context
        Pipeline-->>Webhook: { success: false, error }
        Note over Pipeline: Failure isolated — next event continues
    end
```

---

## 2. Marketplace Normalization (Shopee/Lazada)

```mermaid
sequenceDiagram
    participant Source as Webhook / Polling Collector
    participant Pipeline as Normalization Pipeline
    participant Mapper as Marketplace Mapper<br/>(Shopee/Lazada)
    participant Persist as Persistence Service<br/>(NDP-02)
    participant DB as PostgreSQL

    Source->>Pipeline: ingestEvent(raw_payload, channel_type, tenant_id, event_category)

    alt event_category = chat_message
        Pipeline->>Mapper: normalizeChat(raw_payload)
        Mapper-->>Pipeline: NormalizedEvent { content, external_ids }
        Pipeline->>Persist: persistInboundMessage(normalizedEvent)

    else event_category = order_reference
        Pipeline->>Mapper: normalizeOrderRef(raw_payload)
        Mapper-->>Pipeline: NormalizedEvent { content, metadata: { marketplace_order_id, shop_id, order_status_ref } }
        Pipeline->>Persist: persistInboundMessage(normalizedEvent)

    else event_category = fetch_history
        Pipeline->>Mapper: normalizeHistoryBatch(raw_payload)
        Mapper-->>Pipeline: NormalizedEvent[] (batch)
        loop Each message in batch
            Pipeline->>Persist: persistInboundMessage(event, fetch_batch_id)
            Note over Persist: Idempotency prevents duplicates<br/>if history overlaps with live messages
        end
    end

    Pipeline-->>Source: { success: true, processed_count }
```

---

## 3. PII Redaction Flow

```mermaid
sequenceDiagram
    participant Pipeline as Normalization Pipeline
    participant PII as PII Redactor
    participant DB as PostgreSQL

    Pipeline->>PII: redact(raw_payload, channel_type)

    PII->>PII: Identify sensitive fields per channel policy
    Note over PII: LINE: access_token, user phone<br/>Facebook/Instagram: user email, phone<br/>Marketplace: buyer address, payment info

    PII->>PII: Replace sensitive values with [REDACTED]
    PII-->>Pipeline: { redacted_payload, pii_safe: true }

    Pipeline->>DB: INSERT raw_events (payload=redacted_payload, pii_safe=true)
```

---

## 4. Failure Isolation

```mermaid
sequenceDiagram
    participant Pipeline as Normalization Pipeline
    participant Mapper as Channel Mapper
    participant DB as PostgreSQL

    loop For each event in batch/queue
        Pipeline->>Mapper: normalize(event)

        alt Success
            Mapper-->>Pipeline: NormalizedEvent
            Pipeline->>DB: UPDATE raw_events SET normalization_status='success'
            Pipeline->>Pipeline: Continue to persistence
        else Mapping Error
            Mapper-->>Pipeline: Error (unknown field / missing id)
            Pipeline->>DB: UPDATE raw_events SET normalization_status='failed',<br/>error_detail, error_context
            Note over Pipeline: Skip this event, continue next
        else Unsupported Event Type
            Mapper-->>Pipeline: UnsupportedEvent
            Pipeline->>DB: UPDATE raw_events SET normalization_status='unsupported',<br/>error_detail
            Note over Pipeline: Log and skip
        end
    end
```
