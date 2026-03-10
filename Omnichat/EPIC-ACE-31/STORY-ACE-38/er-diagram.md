# ACE-38 (NDP-02): Message Persistence v1 — ER Diagram

## Context

Extends ACE-37 schema with fields required for persistence logic: idempotency keys, deterministic upserts, and sender info for timeline rendering. Marketplace structured content is stored in the existing `metadata` jsonb field.

---

## ER Diagram

```mermaid
erDiagram
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
        timestamp deleted_at "nullable, soft delete"
    }

    CONVERSATIONS {
        uuid id PK
        uuid tenant_id FK
        uuid channel_account_id FK
        uuid contact_id FK
        varchar channel_type
        varchar external_thread_id "nullable for some channels"
        varchar fallback_thread_key "NEW: hash(external_user_id + channel_account_id) when no thread_id"
        varchar status "open | closed | snoozed"
        boolean is_read "default false, set true when agent opens conversation"
        timestamp read_at "nullable, when agent last read"
        text last_message_preview "updated on every new message"
        timestamp last_message_at "updated on every new message"
        timestamp created_at
        timestamp updated_at
        timestamp deleted_at "nullable, soft delete"
    }

    MESSAGES {
        uuid id PK
        uuid tenant_id FK
        uuid conversation_id FK
        uuid raw_event_id FK "nullable"
        varchar channel_type
        uuid channel_account_id FK
        varchar direction "inbound | outbound"
        varchar external_message_id "nullable, part of idempotency key"
        varchar sender_type "NEW: contact | agent | system"
        varchar sender_display_name "NEW: for timeline bubble rendering"
        text content
        varchar content_type "text | image | video | etc"
        varchar event_type "message (v1 supports message only; edit/delete/reaction deferred)"
        jsonb metadata "channel-specific extras, marketplace structured content"
        varchar status "received | sent | delivered | read | failed"
        timestamp channel_timestamp
        timestamp created_at
        timestamp updated_at
        timestamp deleted_at "nullable, soft delete"
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
        timestamp deleted_at "nullable, soft delete"
    }

    CONTACTS ||--o{ CONVERSATIONS : "participates in"
    CONVERSATIONS ||--o{ MESSAGES : "contains"
    MESSAGES ||--o{ ATTACHMENTS : "has"
```

---

## New Fields (vs ACE-37)

| Table | Field | Type | Purpose |
|---|---|---|---|
| `conversations` | `fallback_thread_key` | varchar | Deterministic key when `external_thread_id` is null |
| `messages` | `sender_type` | varchar | Distinguish contact vs agent vs system for UI bubble |
| `messages` | `sender_display_name` | varchar | Display name for timeline rendering |

---

## New Indexes

| Table | Index | Purpose |
|---|---|---|
| `messages` | `UNIQUE (tenant_id, channel_type, external_message_id)` WHERE external_message_id IS NOT NULL | Idempotency check |
| `conversations` | `UNIQUE (tenant_id, channel_account_id, fallback_thread_key)` WHERE fallback_thread_key IS NOT NULL | Fallback thread dedup |
