# ACE-1502: Contact Context API — Sequence Diagram

## Context

Contact Context API — exposes a single read endpoint for the Contact Profile panel and a patch endpoint for inline edits. Part of STORY-CTX-01 (ACE-1366).

### Source

| Story | Coverage |
|---|---|
| ACE-1366 (CTX-01) | Contact Profile: overview, identities, key events, recent conversations |
| ACE-1502 | Contact Context API implementation |

---

## Service Overview

| Service | App Name | Transport | Port |
|---|---|---|---|
| **API Gateway** | `api-gateway` | HTTP REST (entry point, auth) | :3000 |
| **Omnichat Service** | `omnichat-service` | TCP (microservice) | HTTP :3003 / TCP :4003 |
| **PostgreSQL** | — | Prisma ORM | — |

---

## 1. GET Contact Context

`GET /api/v1/omnichat/contacts/:contactId/context`

Returns the full contact profile panel payload: overview, identities, key events, recent conversations, last purchase stub, and customer notes.

```mermaid
sequenceDiagram
    participant Client as Inbox UI
    participant APIGw as API Gateway<br/>(api-gateway :3000)
    participant OmniSvc as Omnichat Service<br/>(omnichat-service TCP :4003)
    participant DB as PostgreSQL

    %% === PHASE 1: HTTP Request + Auth ===
    Client->>APIGw: GET /api/v1/omnichat/contacts/:contactId/context<br/>Authorization: Bearer <token>
    APIGw->>APIGw: JWT auth → extract { userId, tenantId }
    APIGw->>APIGw: Validate contactId (ParseUUIDPipe)

    %% === PHASE 2: TCP to Omnichat Service ===
    APIGw->>OmniSvc: TCP { cmd: 'get_contact_context' }<br/>{ contactId, tenantId }

    %% === PHASE 3: Contact Lookup ===
    OmniSvc->>DB: SELECT * FROM contacts<br/>WHERE id = :contactId AND tenant_id = :tenantId<br/>AND deleted_at IS NULL
    DB-->>OmniSvc: contact row

    alt Contact not found
        OmniSvc-->>APIGw: RpcException { statusCode: 404 }
        APIGw-->>Client: 404 Not Found
    end

    %% === PHASE 4: Parallel Data Fetch ===
    Note over OmniSvc,DB: Promise.all — 5 parallel queries

    par Total conversation count
        OmniSvc->>DB: COUNT conversations<br/>WHERE contact_id = :id AND tenant_id = :tid
        DB-->>OmniSvc: totalConversations: number
    and Distinct tags across all conversations
        OmniSvc->>DB: SELECT DISTINCT conversationTags JOIN tags<br/>WHERE conversation.contact_id = :id
        DB-->>OmniSvc: tagRecords[]
    and Channel identities (distinct channel accounts)
        OmniSvc->>DB: SELECT DISTINCT conversations<br/>GROUP BY channel_account_id<br/>JOIN channel_accounts
        DB-->>OmniSvc: distinctConvs[] (one per channel identity)
    and Recent conversations (latest 5)
        OmniSvc->>DB: SELECT conversations JOIN channel_accounts<br/>ORDER BY updated_at DESC LIMIT 5
        DB-->>OmniSvc: recentConvs[]
    and Key events (buildKeyEvents)
        Note over OmniSvc,DB: Inner Promise.all — 3 parallel queries (take 15 each)
        OmniSvc->>DB: SELECT conversationAssignments<br/>WHERE conversation.contact_id = :id<br/>ORDER BY created_at DESC LIMIT 15
        DB-->>OmniSvc: assignments[]
        OmniSvc->>DB: SELECT conversationStatusHistory<br/>WHERE conversation.contact_id = :id<br/>ORDER BY created_at DESC LIMIT 15
        DB-->>OmniSvc: statusChanges[]
        OmniSvc->>DB: SELECT conversationTags JOIN tags<br/>WHERE conversation.contact_id = :id<br/>ORDER BY created_at DESC LIMIT 15
        DB-->>OmniSvc: tagChanges[]
    end

    %% === PHASE 5: Build Key Events ===
    OmniSvc->>OmniSvc: Merge assignments + statusChanges + tagChanges<br/>Sort by created_at DESC → slice top 5

    %% === PHASE 6: Build Response ===
    OmniSvc->>OmniSvc: maskExternalUserId(external_user_id)<br/>(first 4 + ••• + last 4 chars)
    OmniSvc->>OmniSvc: Build contact context payload

    OmniSvc-->>APIGw: {<br/>  overview: { id, display_name, avatar_url, last_seen_at,<br/>    total_conversations, phone, email, address,<br/>    language_preference, tags[] },<br/>  identities: [{ channel_type, channel_account_id,<br/>    channel_account_name, external_user_id (masked) }],<br/>  key_events: [{ type, description, actor_name, created_at }] (max 5),<br/>  recent_conversations: [{ id, status, last_message_preview,<br/>    last_message_at, channel_type, channel_account_name }] (max 5),<br/>  last_purchase_stub: null,<br/>  customer_notes: []<br/>}

    APIGw-->>Client: 200 OK { ...contactContext }
```

### Key Events Types

| `type` | Source Table | Description Format |
|---|---|---|
| `assigned` | `conversationAssignment` | `"Assigned to {agent_name}"` or `"Unassigned"` |
| `status_change` | `conversationStatusHistory` | `"Status changed from {from} to {to}"` |
| `tag_change` | `conversationTag` | `"Tag "{name}" added"` |

---

## 2. PATCH Contact (Inline Edit)

`PATCH /api/v1/omnichat/contacts/:contactId`

Updates `display_name` and/or `profile_metadata` fields on a contact. Uses a raw SQL `UPDATE` with partial JSONB merge for metadata.

```mermaid
sequenceDiagram
    participant Client as Inbox UI
    participant APIGw as API Gateway<br/>(api-gateway :3000)
    participant OmniSvc as Omnichat Service<br/>(omnichat-service TCP :4003)
    participant DB as PostgreSQL

    %% === PHASE 1: HTTP Request + Auth ===
    Client->>APIGw: PATCH /api/v1/omnichat/contacts/:contactId<br/>Authorization: Bearer <token><br/>Body: { display_name?, profile_metadata?: { phone?, email?, address?, language_preference? } }
    APIGw->>APIGw: JWT auth → extract { userId, tenantId }
    APIGw->>APIGw: Validate contactId (ParseUUIDPipe)<br/>Validate body (UpdateContactPayloadDto)

    %% === PHASE 2: TCP to Omnichat Service ===
    APIGw->>OmniSvc: TCP { cmd: 'update_contact' }<br/>{ contactId, dto: { tenant_id, display_name?, profile_metadata? } }

    %% === PHASE 3: Build & Execute UPDATE ===
    OmniSvc->>OmniSvc: Build SET clauses from non-undefined fields<br/>display_name = :value<br/>profile_metadata = COALESCE(profile_metadata, '{}') || :json<br/>updated_at = NOW()

    OmniSvc->>DB: UPDATE contacts SET ...<br/>WHERE id = :contactId AND tenant_id = :tenantId<br/>AND deleted_at IS NULL
    DB-->>OmniSvc: affected rows count

    alt Contact not found (affected = 0)
        OmniSvc-->>APIGw: RpcException { statusCode: 404 }
        APIGw-->>Client: 404 Not Found
    end

    OmniSvc-->>APIGw: void
    APIGw-->>Client: 200 OK
```

> **JSONB merge:** `profile_metadata` uses `COALESCE(profile_metadata, '{}') || :json` — partial patch, existing keys not in the request body are preserved.

---

## Service Communication Map

```
┌─────────────┐
│  Inbox UI   │
└──────┬──────┘
       │ HTTP REST
       ▼
┌──────────────────────────────────────────┐
│ API Gateway (api-gateway :3000)          │
│                                          │
│  ContactsController                      │
│   GET  /omnichat/contacts/:id/context    │
│   PATCH /omnichat/contacts/:id           │
│                                          │
│  ContactsService                         │
│   → omnichatClient.send(cmd, payload)    │
└──────────────────┬───────────────────────┘
                   │ TCP (NestJS microservice)
                   ▼
┌──────────────────────────────────────────┐
│ Omnichat Service (omnichat-service :4003)│
│                                          │
│  ContactsController (@MessagePattern)    │
│   cmd: get_contact_context               │
│   cmd: update_contact                    │
│                                          │
│  ContactsService                         │
│   getContactContext() → 6 DB queries     │
│   updateContact()    → 1 raw UPDATE      │
└──────────────────┬───────────────────────┘
                   │ Prisma ORM
                   ▼
           ┌──────────────┐
           │  PostgreSQL  │
           └──────────────┘
```

---

## Flow Summary

| # | Endpoint | Method | Transport | DB Queries | Response |
|---|---|---|---|---|---|
| 1 | `/omnichat/contacts/:id/context` | GET | HTTP → TCP | 1 contact lookup + 5 parallel (incl. 3 inner) = 8 total | `{ overview, identities, key_events, recent_conversations, last_purchase_stub, customer_notes }` |
| 2 | `/omnichat/contacts/:id` | PATCH | HTTP → TCP | 1 raw UPDATE | `void` (200 OK) |
