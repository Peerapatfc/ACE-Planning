# ACE-41 (NDP-05): Conversation Timeline Query API v1 — Sequence Diagram

## Context

Sequence diagrams for the read-side API: listing conversations for inbox view, fetching message timelines with attachments, and ensuring pagination consistency under concurrent writes.

---

## 1. List Conversations (Inbox View)

```mermaid
sequenceDiagram
    participant Client as Inbox UI
    participant API as Omni API
    participant DB as PostgreSQL

    Client->>API: GET /api/v1/conversations<br/>?status=open&channel_type=LINE<br/>&cursor=&limit=20

    API->>API: Extract tenant_id from auth context
    API->>API: Validate query params

    API->>DB: SELECT c.*, ct.display_name, ct.avatar_url<br/>FROM conversations c<br/>JOIN contacts ct ON c.contact_id = ct.id<br/>WHERE c.tenant_id = ?<br/>AND c.status = 'open'<br/>AND c.channel_type = 'LINE'<br/>AND c.deleted_at IS NULL<br/>AND c.last_message_at < cursor<br/>ORDER BY c.last_message_at DESC<br/>LIMIT 21
    DB-->>API: conversations[] (fetch limit+1 for has_more)

    API->>API: Build response with contact info,<br/>channel badge, last_message_preview

    API-->>Client: 200 OK { data: conversations[], meta: { cursor, has_more } }
```

---

## 2. Get Conversation Detail

```mermaid
sequenceDiagram
    participant Client as Inbox UI
    participant API as Omni API
    participant DB as PostgreSQL

    Client->>API: GET /api/v1/conversations/{id}
    API->>API: Extract tenant_id from auth context

    API->>DB: SELECT c.*, ct.display_name, ct.avatar_url, ct.external_user_id,<br/>ca.display_name as channel_name<br/>FROM conversations c<br/>JOIN contacts ct ON c.contact_id = ct.id<br/>JOIN channel_accounts ca ON c.channel_account_id = ca.id<br/>WHERE c.id = ? AND c.tenant_id = ?

    alt Not Found or Wrong Tenant
        DB-->>API: empty
        API-->>Client: 404 Not Found
    else Found
        DB-->>API: conversation with contact & channel info
        API-->>Client: 200 OK { data: conversation }
    end
```

---

## 3. Fetch Message Timeline with Attachments

```mermaid
sequenceDiagram
    participant Client as Inbox UI
    participant API as Omni API
    participant DB as PostgreSQL

    Client->>API: GET /api/v1/conversations/{id}/messages<br/>?cursor=&limit=20

    API->>API: Extract tenant_id, validate conversation ownership

    API->>DB: SELECT messages<br/>WHERE tenant_id = ? AND conversation_id = ?<br/>AND deleted_at IS NULL<br/>AND created_at < cursor<br/>ORDER BY created_at DESC<br/>LIMIT 21
    DB-->>API: messages[]

    API->>DB: SELECT attachments<br/>WHERE message_id IN (...)<br/>AND deleted_at IS NULL
    DB-->>API: attachments[]

    API->>API: Merge attachments into messages,<br/>build cursor from last message created_at

    API-->>Client: 200 OK { data: messages[], meta: { cursor, has_more } }

    Note over Client: UI renders messages as bubbles<br/>using sender_type + sender_display_name<br/>Shows channel_type badge
```

---

## 4. Pagination Consistency Under Concurrent Writes

```mermaid
sequenceDiagram
    participant Client as Inbox UI
    participant API as Omni API
    participant DB as PostgreSQL

    Note over Client,DB: Page 1: cursor = NOW (latest)

    Client->>API: GET /conversations/{id}/messages?limit=20
    API->>DB: SELECT ... WHERE created_at < NOW ORDER BY created_at DESC LIMIT 21
    DB-->>API: messages[1..20], has_more=true
    API-->>Client: cursor = messages[20].created_at

    Note over Client,DB: New message arrives between page loads<br/>created_at = NOW+1 (newer than cursor)

    Client->>API: GET /conversations/{id}/messages?cursor={msg20.created_at}&limit=20
    API->>DB: SELECT ... WHERE created_at < cursor ORDER BY created_at DESC LIMIT 21
    DB-->>API: messages[21..40]
    API-->>Client: No duplicates, no skips for older messages

    Note over Client: New message appears via<br/>real-time push (WebSocket/SSE)<br/>not via pagination
```
