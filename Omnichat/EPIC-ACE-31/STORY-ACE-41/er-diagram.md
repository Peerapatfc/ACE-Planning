# ACE-41 (NDP-05): Conversation Timeline Query API v1 — ER Diagram

## Context

Uses ACE-37 + ACE-38 schema. This diagram highlights the fields and indexes critical for query performance and UI rendering.

---

## ER Diagram

```mermaid
erDiagram
    CONVERSATIONS {
        uuid id PK
        uuid tenant_id FK
        uuid channel_account_id FK
        uuid contact_id FK
        varchar channel_type "filter param"
        varchar external_thread_id
        varchar status "open | closed | snoozed - filter param"
        boolean is_read "default false, filter unread conversations"
        timestamp read_at "nullable, when agent last read"
        text last_message_preview "shown in conversation list"
        timestamp last_message_at "primary sort field for inbox"
        timestamp created_at
        timestamp updated_at
        timestamp deleted_at
    }

    CONTACTS {
        uuid id PK
        uuid tenant_id FK
        varchar channel_type
        varchar external_user_id
        varchar display_name "shown in conversation list and bubbles"
        varchar avatar_url "shown in conversation list"
        jsonb profile_metadata
        timestamp first_seen_at
        timestamp last_seen_at
        timestamp created_at
        timestamp updated_at
        timestamp deleted_at
    }

    MESSAGES {
        uuid id PK
        uuid tenant_id FK
        uuid conversation_id FK
        varchar channel_type
        uuid channel_account_id FK
        varchar direction "inbound | outbound"
        varchar sender_type "contact | agent | system - for bubble rendering"
        varchar sender_display_name "shown on message bubble"
        text content "message body"
        varchar content_type "text | image | etc"
        varchar event_type "message (v1 supports message only; edit/delete/reaction deferred)"
        varchar status "received | sent | delivered | read | failed"
        timestamp channel_timestamp
        timestamp created_at
        timestamp updated_at
        timestamp deleted_at
    }

    ATTACHMENTS {
        uuid id PK
        uuid tenant_id FK
        uuid message_id FK
        varchar type "image | video | audio | file | sticker"
        varchar content_type "MIME type"
        bigint size "bytes - shown in UI"
        varchar storage_key
        varchar status "pending | uploading | uploaded | failed | rejected"
        varchar failure_reason "nullable, shown when status=failed/rejected"
        varchar checksum
        jsonb metadata "original_filename"
        timestamp created_at
        timestamp deleted_at
    }

    CHANNEL_ACCOUNTS {
        uuid id PK
        uuid tenant_id FK
        varchar channel_type
        varchar external_account_id
        varchar display_name "channel name shown in UI"
        varchar status
        timestamp created_at
        timestamp updated_at
        timestamp deleted_at
    }

    CHANNEL_ACCOUNTS ||--o{ CONVERSATIONS : "receives"
    CONTACTS ||--o{ CONVERSATIONS : "participates in"
    CONVERSATIONS ||--o{ MESSAGES : "contains"
    MESSAGES ||--o{ ATTACHMENTS : "has"
```

---

## Key Indexes for Query Performance

| Table | Index | Used By | Purpose |
|---|---|---|---|
| `conversations` | `(tenant_id, status, last_message_at DESC)` | List conversations | Inbox sort + filter |
| `conversations` | `(tenant_id, channel_type, last_message_at DESC)` | Filter by channel | Channel filter |
| `conversations` | `(tenant_id, channel_account_id, last_message_at DESC)` | Filter by account | Account filter |
| `messages` | `(tenant_id, conversation_id, created_at DESC)` | Timeline pagination | Cursor-based pagination |
| `attachments` | `(message_id)` | Timeline join | Fetch attachments for messages |

---

## Performance Baseline Targets

| Query | Target p95 | Volume Assumption |
|---|---|---|
| List conversations (20 items) | < 100ms | 10K conversations per tenant |
| Message timeline (20 items) | < 80ms | 1K messages per conversation |
| Conversation detail | < 50ms | Single row + JOINs |
