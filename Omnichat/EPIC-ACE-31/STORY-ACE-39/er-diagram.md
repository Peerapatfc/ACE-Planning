# ACE-39 (NDP-03): Normalization Pipeline v1 — ER Diagram

## Context

Extends ACE-37 schema with additional fields on `raw_events` for marketplace source categorization and normalization failure tracking.

---

## ER Diagram

```mermaid
erDiagram
    RAW_EVENTS {
        uuid id PK
        uuid tenant_id FK
        varchar channel_type
        uuid channel_account_id FK
        varchar external_event_id "idempotency key"
        jsonb payload "PII-redacted raw webhook body"
        varchar event_type
        varchar source_category "NEW: chat | order_reference | fetch_history"
        varchar fetch_batch_id "NEW: nullable, groups history imports"
        boolean pii_safe "default false, set true after redaction"
        varchar normalization_status "NEW: success | failed | unsupported"
        text error_detail "NEW: nullable, error message when normalization failed"
        jsonb error_context "NEW: nullable, field name, expected vs actual"
        timestamp received_at
        timestamp created_at
    }

    MESSAGES {
        uuid id PK
        uuid tenant_id FK
        uuid conversation_id FK
        uuid raw_event_id FK "nullable, link to raw event"
        varchar channel_type
        uuid channel_account_id FK
        varchar direction "inbound | outbound"
        varchar external_message_id "nullable"
        varchar sender_type "contact | agent | system"
        varchar sender_display_name
        text content
        varchar content_type "text | image | video | etc"
        varchar event_type "message (v1 supports message only; edit/delete/reaction deferred)"
        jsonb metadata "source_category, fetch_batch_id, marketplace: order_id/shop_id/order_status_ref, structured_content"
        varchar status "received | sent | delivered | read | failed"
        timestamp channel_timestamp
        timestamp created_at
        timestamp updated_at
        timestamp deleted_at "nullable, soft delete"
    }

    RAW_EVENTS ||--o| MESSAGES : "normalized to"
```

---

## New Fields on `raw_events` (vs ACE-37)

| Field | Type | Purpose |
|---|---|---|
| `source_category` | varchar | `chat`, `order_reference`, `fetch_history` — classify event origin |
| `fetch_batch_id` | varchar nullable | Group history import batches together |
| `normalization_status` | varchar | `success`, `failed`, `unsupported` — track normalization result |
| `error_detail` | text nullable | Human-readable error message when normalization failed |
| `error_context` | jsonb nullable | Field-level details for debugging (field name, expected vs actual) |

---

## New Indexes

| Table | Index | Purpose |
|---|---|---|
| `raw_events` | `(tenant_id, normalization_status, created_at)` WHERE normalization_status != 'success' | Query failed normalizations for review |
| `raw_events` | `(tenant_id, fetch_batch_id)` WHERE fetch_batch_id IS NOT NULL | Query history import batches |
