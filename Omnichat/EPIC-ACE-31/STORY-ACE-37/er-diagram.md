# ACE-37 (NDP-01): Define Normalized Schema v1 — ER Diagram

## Context

Entity-Relationship diagram for the normalized data schema v1. All channels (LINE, Facebook, Instagram, TikTok, Shopee, Lazada) are stored in one consistent model with multi-tenant isolation by design.

---

## ER Diagram

```mermaid
erDiagram
    TENANT {
        uuid id PK
        varchar name
        varchar status
        timestamp created_at
        timestamp updated_at
        timestamp deleted_at "nullable"
    }

    CHANNEL_ACCOUNTS {
        uuid id PK
        uuid tenant_id FK
        varchar channel_type "LINE | FACEBOOK | INSTAGRAM | TIKTOK | SHOPEE | LAZADA"
        varchar external_account_id "unique per channel"
        varchar display_name
        uuid credential_ref_id FK "ref to credential_store (FND-02)"
        varchar status "active | inactive"
        varchar connection_status "connected | error"
        timestamp last_checked_at "nullable"
        text last_error_summary "nullable, no secrets"
        varchar error_code_category "nullable: auth_error | webhook_error | rate_limit | unknown"
        timestamp created_at
        timestamp updated_at
        timestamp deleted_at "nullable"
    }

    CONTACTS {
        uuid id PK
        uuid tenant_id FK
        varchar channel_type
        varchar external_user_id
        varchar display_name
        varchar avatar_url
        jsonb profile_metadata
        timestamp first_seen_at
        timestamp last_seen_at
        timestamp created_at
        timestamp updated_at
        timestamp deleted_at "nullable"
    }

    CONVERSATIONS {
        uuid id PK
        uuid tenant_id FK
        uuid channel_account_id FK
        uuid contact_id FK
        varchar channel_type
        varchar external_thread_id "nullable for some channels"
        varchar status "open | closed | snoozed"
        boolean is_read "default false, set true when agent opens conversation"
        timestamp read_at "nullable, when agent last read"
        text last_message_preview
        timestamp last_message_at
        timestamp created_at
        timestamp updated_at
        timestamp deleted_at "nullable"
    }

    MESSAGES {
        uuid id PK
        uuid tenant_id FK
        uuid conversation_id FK
        uuid raw_event_id FK "nullable"
        varchar channel_type
        uuid channel_account_id FK
        varchar direction "inbound | outbound"
        varchar external_message_id "nullable"
        text content
        varchar content_type "text | image | video | audio | file | sticker | template | etc"
        varchar event_type "message (v1 supports message only; edit/delete/reaction deferred)"
        jsonb metadata "channel-specific extras, marketplace_order_id, shop_id, order_status_ref"
        varchar status "received | sent | delivered | read | failed"
        timestamp channel_timestamp "original timestamp from channel"
        timestamp created_at
        timestamp updated_at
        timestamp deleted_at "nullable"
    }

    ATTACHMENTS {
        uuid id PK
        uuid tenant_id FK
        uuid message_id FK
        varchar type "image | video | audio | file | sticker"
        varchar content_type "MIME type"
        bigint size "bytes"
        varchar storage_key "S3 key"
        varchar status "pending | uploaded | failed"
        varchar checksum "nullable, SHA-256"
        jsonb metadata "original_filename, channel-specific extras"
        timestamp created_at
        timestamp deleted_at "nullable"
    }

    RAW_EVENTS {
        uuid id PK
        uuid tenant_id FK
        varchar channel_type
        uuid channel_account_id FK
        varchar external_event_id "idempotency key"
        jsonb payload "PII-redacted raw webhook body"
        varchar event_type
        boolean pii_safe "default false"
        timestamp received_at
        timestamp created_at
    }

    TENANT ||--o{ CHANNEL_ACCOUNTS : "has"
    TENANT ||--o{ CONTACTS : "has"
    TENANT ||--o{ CONVERSATIONS : "has"
    TENANT ||--o{ MESSAGES : "has"
    TENANT ||--o{ ATTACHMENTS : "has"
    TENANT ||--o{ RAW_EVENTS : "has"
    CHANNEL_ACCOUNTS ||--o{ CONVERSATIONS : "receives"
    CONTACTS ||--o{ CONVERSATIONS : "participates in"
    CONVERSATIONS ||--o{ MESSAGES : "contains"
    MESSAGES ||--o{ ATTACHMENTS : "has"
    MESSAGES ||--o| RAW_EVENTS : "linked to"
```

---

## Recommended Indexes

| Table | Index | Purpose |
|---|---|---|
| `messages` | `(tenant_id, created_at)` | Global timeline query |
| `messages` | `(tenant_id, conversation_id, created_at)` | Conversation thread pagination |
| `conversations` | `(tenant_id, channel_type, external_thread_id)` | Upsert lookup on inbound event |
| `contacts` | `(tenant_id, channel_type, external_user_id)` | Upsert contact on inbound event |
| `channel_accounts` | `(tenant_id, channel_type, external_account_id)` | Lookup channel account |
| `raw_events` | `(tenant_id, channel_type, external_event_id)` | Idempotency check |
| `attachments` | `(message_id)` | Join attachments to message |
| `conversations` | `(tenant_id, status, last_message_at)` | Inbox list sorted by recent |

---

## Unique Constraints

| Table | Constraint |
|---|---|
| `contacts` | `UNIQUE (tenant_id, channel_type, external_user_id)` |
| `channel_accounts` | `UNIQUE (tenant_id, channel_type, external_account_id)` |
| `conversations` | `UNIQUE (tenant_id, channel_account_id, external_thread_id)` WHERE external_thread_id IS NOT NULL |
| `messages` | `UNIQUE (tenant_id, channel_type, external_message_id)` WHERE external_message_id IS NOT NULL |
| `raw_events` | `UNIQUE (tenant_id, channel_type, external_event_id)` |
