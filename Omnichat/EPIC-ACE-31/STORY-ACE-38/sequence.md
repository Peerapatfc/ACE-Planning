# ACE-38 (NDP-02): Message Persistence v1 — Sequence Diagram

## Context

Sequence diagrams for the persistence layer: idempotent message inserts, deterministic upserts for contacts/conversations, outbound message persistence, and query capabilities. Depends on ACE-37 schema.

---

## 1. Idempotent Inbound Message Persist

```mermaid
sequenceDiagram
    participant Caller as Normalizer / Connector
    participant Svc as Persistence Service
    participant DB as PostgreSQL

    Caller->>Svc: persistInboundMessage(normalizedEvent)
    Svc->>Svc: Validate required fields (tenant_id, channel_type, content, external_ids)

    alt Validation Failed
        Svc-->>Caller: 400 ValidationError (no partial records written)
    end

    Svc->>DB: UPSERT contacts<br/>ON CONFLICT (tenant_id, channel_type, external_user_id)<br/>DO UPDATE SET display_name, avatar_url, last_seen_at
    DB-->>Svc: contact_id (stable)

    Svc->>DB: UPSERT conversations<br/>ON CONFLICT (tenant_id, channel_account_id, external_thread_id)<br/>DO UPDATE SET last_message_at, last_message_preview, status
    DB-->>Svc: conversation_id (stable)

    Note over Svc,DB: Idempotency key = tenant_id + channel_type + external_message_id

    Svc->>DB: INSERT messages<br/>ON CONFLICT (tenant_id, channel_type, external_message_id)<br/>DO NOTHING
    DB-->>Svc: message_id (new or existing)

    alt Has Attachment Metadata
        Svc->>DB: INSERT attachments (message_id, type, content_type, size, status='pending')
        DB-->>Svc: attachment_id
    end

    Svc-->>Caller: { message_id, contact_id, conversation_id, is_duplicate: bool }
```

---

## 2. Outbound Message Persist

```mermaid
sequenceDiagram
    participant Caller as Omni API / Send Service
    participant Svc as Persistence Service
    participant DB as PostgreSQL

    Caller->>Svc: persistOutboundMessage(conversation_id, content, channel_account_id, tenant_id)
    Svc->>Svc: Validate conversation exists & belongs to tenant

    alt Validation Failed
        Svc-->>Caller: 400 ValidationError
    end

    Svc->>DB: INSERT messages (conversation_id, direction='outbound', content, status='pending', tenant_id)
    DB-->>Svc: message_id

    Svc->>DB: UPDATE conversations SET last_message_at=NOW(), last_message_preview=content
    DB-->>Svc: OK

    Svc-->>Caller: { message_id, status: 'pending' }

    Note over Caller: After Channel API responds:
    Caller->>Svc: updateMessageStatus(message_id, external_message_id, status='sent')
    Svc->>DB: UPDATE messages SET external_message_id=?, status='sent'
    Svc-->>Caller: OK
```

---

## 3. Conversation Timeline Query

```mermaid
sequenceDiagram
    participant Caller as Query API / Inbox
    participant Svc as Persistence Service
    participant DB as PostgreSQL

    Caller->>Svc: listMessages(tenant_id, conversation_id, cursor?, limit=20)
    Svc->>Svc: Validate tenant_id + conversation ownership

    Svc->>DB: SELECT messages<br/>WHERE tenant_id=? AND conversation_id=?<br/>AND created_at < cursor<br/>ORDER BY created_at DESC<br/>LIMIT 21
    DB-->>Svc: messages[] (fetch limit+1 for has_more)

    Svc->>DB: SELECT attachments WHERE message_id IN (...)
    DB-->>Svc: attachments[]

    Svc->>Svc: Build response, set next_cursor = last item's created_at
    Svc-->>Caller: { data: messages[], meta: { cursor, has_more } }
```

---

## 4. Missing Thread ID Fallback

```mermaid
sequenceDiagram
    participant Svc as Persistence Service
    participant DB as PostgreSQL

    Note over Svc: Some channels don't provide external_thread_id

    alt external_thread_id is present
        Svc->>DB: UPSERT conversations<br/>ON CONFLICT (tenant_id, channel_account_id, external_thread_id)
    else external_thread_id is NULL
        Svc->>Svc: Generate fallback key:<br/>hash(external_user_id + channel_account_id)
        Svc->>DB: UPSERT conversations<br/>ON CONFLICT (tenant_id, channel_account_id, fallback_thread_key)
    end
    DB-->>Svc: conversation_id
```
