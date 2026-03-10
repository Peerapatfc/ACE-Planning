# EPIC ACE-31: Normalized Data Platform v1 — Consolidated API Table

## Context

Consolidated API surface for the entire Normalized Data Platform — combining webhooks, internal service APIs, public query APIs, and file service endpoints from all five stories.

### Source Stories

| Story | API Contribution |
|---|---|
| **FND-01** | **Tenant CRUD, Channel Account CRUD, Connection model, Credential Refs** → see [STORY-FND-01](./STORY-FND-01_%20Create%20Tenant%20ChannelAccount%20and%20Connection%20Model-20260220113617.md) |
| ACE-37 (NDP-01) | Webhooks, internal APIs (raw-events, messages/inbound, attachments), file service |
| ACE-38 (NDP-02) | Persistence patterns: idempotent upserts, deterministic conflict keys |
| ACE-39 (NDP-03) | Internal ingestion interface, normalization contracts, failure review |
| ACE-40 (NDP-04) | Public attachment APIs (metadata, download), internal worker interface |
| ACE-41 (NDP-05) | Public query APIs (conversations, messages, contacts) |

---

## Service Routing

| Path Prefix | Routed To | Notes |
|---|---|---|
| `/api/v1/tenants/*` | **API Gateway** (:3000) → **Tenant Service** (:3012) | Defined in FND-01 |
| `/api/v1/channel-accounts/*` | **API Gateway** (:3000) → **Omnichat Service** (:3011) | Defined in FND-01 |
| `/api/v1/*` (other) | **API Gateway** (:3000) → **Omnichat Service** (:3011) | Auth & tenant extraction at API Gateway |
| `/webhooks/*` | **Omnichat Gateway** (:3010) | Direct — no API Gateway, signature validation at Gateway |
| `/raw-events/*`, `/messages/*`, `/attachments/*` (internal) | **Omnichat Service** (:3011) | Service-to-service only — not routed by API Gateway, accessible via private network only |
| `/files/*` | **File Service** (:3005) | Service-to-service only — not routed by API Gateway, accessible via private network only |

---

## 1. Webhooks — Inbound (Omnichat Gateway)

Source: NDP-01

| Method | Endpoint | Description | Key Params |
|---|---|---|---|
| POST | `/webhooks/line` | Receive LINE webhook events | Signature in `X-Line-Signature` header |
| POST | `/webhooks/facebook` | Receive Facebook Messenger webhook events | Signature in `X-Hub-Signature-256` header |
| POST | `/webhooks/instagram` | Receive Instagram Messaging webhook events | Signature in `X-Hub-Signature-256` header |
| POST | `/webhooks/tiktok` | Receive TikTok webhook events | Signature in header |
| POST | `/webhooks/shopee` | Receive Shopee webhook events | Signature in header |
| POST | `/webhooks/lazada` | Receive Lazada webhook events | Signature in header |

---

## 2. Public REST APIs (API Gateway → Omnichat Service)

> **Tenant & Channel Account APIs** are defined in **STORY-FND-01** (Tenant CRUD, Channel Account CRUD, Connection, Credential Refs). This document covers NDP-specific APIs only.

### 2.1 Contacts

Source: NDP-01 (schema readiness), NDP-05 (optional lookup)

| Method | Endpoint | Description | Key Params |
|---|---|---|---|
| GET | `/api/v1/contacts` | List contacts | `?channel_type=`, `?search=`, `?cursor=`, `?limit=` |
| GET | `/api/v1/contacts/:id` | Get contact detail | — |
| PATCH | `/api/v1/contacts/:id` | Update contact metadata | `display_name`, `profile_metadata` |

**Response: GET `/api/v1/contacts/:id`**

```json
{
  "data": {
    "id": "uuid",
    "channel_type": "LINE",
    "external_user_id": "U1234...",
    "display_name": "John Doe",
    "avatar_url": "https://...",
    "profile_metadata": {},
    "first_seen_at": "2025-01-10T08:00:00Z",
    "last_seen_at": "2025-01-15T10:30:00Z"
  }
}
```

### 2.2 Conversations

Source: NDP-05

| Method | Endpoint | Description | Key Params |
|---|---|---|---|
| GET | `/api/v1/conversations` | List conversations (Inbox) | `?status=`, `?channel_type=`, `?channel_account_id=`, `?cursor=`, `?limit=`, `?sort=last_message_at`, `?order=desc` |
| GET | `/api/v1/conversations/:id` | Get conversation detail | — |
| PATCH | `/api/v1/conversations/:id` | Update conversation status or mark as read | `status?` (open/closed/snoozed), `is_read?` (true/false) |
| GET | `/api/v1/conversations/:id/messages` | Get message timeline | `?cursor=`, `?limit=` |

**Response: GET `/api/v1/conversations`**

```json
{
  "data": [
    {
      "id": "uuid",
      "channel_type": "LINE",
      "channel_account_id": "uuid",
      "channel_account_name": "My LINE OA",
      "status": "open",
      "is_read": false,
      "contact": {
        "id": "uuid",
        "display_name": "John Doe",
        "avatar_url": "https://...",
        "external_user_id": "U1234..."
      },
      "last_message_preview": "สวัสดีครับ ต้องการสอบถาม...",
      "last_message_at": "2025-01-15T10:30:00Z",
      "created_at": "2025-01-10T08:00:00Z"
    }
  ],
  "meta": { "cursor": "2025-01-15T10:30:00Z", "has_more": true }
}
```

**Response: GET `/api/v1/conversations/:id`**

```json
{
  "data": {
    "id": "uuid",
    "channel_type": "LINE",
    "channel_account": {
      "id": "uuid",
      "display_name": "My LINE OA",
      "channel_type": "LINE"
    },
    "contact": {
      "id": "uuid",
      "display_name": "John Doe",
      "avatar_url": "https://...",
      "external_user_id": "U1234...",
      "profile_metadata": {}
    },
    "status": "open",
    "is_read": false,
    "read_at": null,
    "external_thread_id": "T5678...",
    "last_message_preview": "สวัสดีครับ",
    "last_message_at": "2025-01-15T10:30:00Z",
    "created_at": "2025-01-10T08:00:00Z"
  }
}
```

**Response: GET `/api/v1/conversations/:id/messages`**

```json
{
  "data": [
    {
      "id": "uuid",
      "direction": "inbound",
      "sender_type": "contact",
      "sender_display_name": "John Doe",
      "content": "สวัสดีครับ ต้องการสอบถามเรื่องสินค้า",
      "content_type": "text",
      "metadata": {},
      "event_type": "message",
      "status": "received",
      "channel_timestamp": "2025-01-15T10:30:00Z",
      "created_at": "2025-01-15T10:30:01Z",
      "attachments": []
    },
    {
      "id": "uuid",
      "direction": "inbound",
      "sender_type": "contact",
      "sender_display_name": "John Doe",
      "content": "",
      "content_type": "image",
      "metadata": {},
      "event_type": "message",
      "status": "received",
      "channel_timestamp": "2025-01-15T10:31:00Z",
      "created_at": "2025-01-15T10:31:01Z",
      "attachments": [
        {
          "id": "uuid",
          "type": "image",
          "content_type": "image/jpeg",
          "size": 245678,
          "status": "uploaded",
          "file_url": "https://{bucket}.s3.amazonaws.com/{tenant_id}/{attachment_id}/photo.jpg",
          "failure_reason": null,
          "metadata": { "original_filename": "photo.jpg" }
        }
      ]
    }
  ],
  "meta": { "cursor": "2025-01-15T10:30:01Z", "has_more": true }
}
```

### 2.3 Messages

Source: NDP-01 (schema readiness), NDP-02 (outbound persistence), NDP-05 (query)

| Method | Endpoint | Description | Key Params |
|---|---|---|---|
| POST | `/api/v1/messages` | Send outbound message | `conversation_id`, `content`, `content_type`, `sender_display_name`, `attachments[]?` |
| GET | `/api/v1/messages/:id` | Get message detail with attachments | — |

**Response: GET `/api/v1/messages/:id`**

```json
{
  "data": {
    "id": "uuid",
    "conversation_id": "uuid",
    "channel_type": "LINE",
    "direction": "inbound",
    "sender_type": "contact",
    "sender_display_name": "John Doe",
    "content": "สวัสดีครับ",
    "content_type": "image",
    "metadata": {},
    "event_type": "message",
    "status": "received",
    "channel_timestamp": "2025-01-15T10:31:00Z",
    "created_at": "2025-01-15T10:31:01Z",
    "attachments": [
      {
        "id": "uuid",
        "type": "image",
        "content_type": "image/jpeg",
        "size": 245678,
        "status": "uploaded",
        "file_url": "https://{bucket}.s3.amazonaws.com/{tenant_id}/{attachment_id}/photo.jpg",
        "failure_reason": null,
        "checksum": "sha256:abc123...",
        "metadata": { "original_filename": "photo.jpg" }
      }
    ]
  }
}
```

### 2.4 Attachments

Source: NDP-04

| Method | Endpoint | Description | Key Params |
|---|---|---|---|
| GET | `/api/v1/attachments/:id` | Get attachment metadata | — |
| GET | `/api/v1/attachments/:id/download` | Get download URL (static) | — |

**Response: GET `/api/v1/attachments/:id/download`**

```json
// Status = uploaded → return static public URL (no expiry)
{ "data": { "url": "https://{bucket}.s3.amazonaws.com/{tenant_id}/{attachment_id}/photo.jpg" } }

// Status = pending
{ "data": { "status": "pending", "message": "Attachment is still being processed" } }

// Status = failed
{ "data": { "status": "failed", "failure_reason": "download_timeout_after_retries", "retryable": true } }
```

> **Note:** S3 bucket is public. `file_url` is a permanent static URL — no presigned download URL needed. Auth is handled at the application level.

---

## 3. Internal APIs — Service-to-Service

> These endpoints are exposed directly by each service (no `/internal/*` prefix) — consistent with FND-01 pattern.
> Security is enforced at **network level**: services are accessible only within the private network; API Gateway does **not** route these paths externally.

### 3.1 Omnichat Service — Write (NDP-01, NDP-02)

| Method | Endpoint | Caller | Description | Key Params |
|---|---|---|---|---|
| POST | `/raw-events` | Normalizer Worker | Store redacted raw webhook event | `redacted_payload`, `channel_type`, `tenant_id`, `source_category`, `fetch_batch_id?`, `pii_safe` |
| PATCH | `/raw-events/:id` | Normalizer Worker | Update normalization status (on failure) | `normalization_status`, `error_detail?`, `error_context?` |
| POST | `/messages/inbound` | Normalizer Worker | Persist normalized inbound data (upsert contact + conversation + insert message) | `contact`, `conversation`, `message`, `attachments_metadata?` |
| POST | `/attachments` | Normalizer Worker | Create attachment record (status: pending) | `message_id`, `type`, `content_type`, `download_url`, `tenant_id` |
| PATCH | `/attachments/:id` | Normalizer Worker | Update attachment after upload or on failure | `storage_key?`, `file_url?`, `size?`, `checksum?`, `status`, `failure_reason?`, `retry_count?` |

### 3.2 File Service (NDP-01)

| Method | Endpoint | Caller | Description | Key Params |
|---|---|---|---|---|
| POST | `/files/presigned-url` | Omnichat Service | Generate S3 presigned upload URL (returns presigned PUT URL + static file_url) | `filename`, `folder`, `tenant_id` |
| POST | `/files/upload` | Normalizer Worker | Upload binary file to S3 (returns storage_key + static file_url) | `binary`, `content_type`, `tenant_id`, `folder` |

---

## 4. Normalization Contracts (NDP-03)

### 4.1 NormalizedEvent Contract

```json
{
  "tenant_id": "uuid",
  "channel_type": "LINE | FACEBOOK | INSTAGRAM | TIKTOK | SHOPEE | LAZADA",
  "channel_account_id": "uuid",
  "external_message_id": "string (fallback: hash + timestamp)",
  "external_user_id": "string",
  "external_thread_id": "string | null",
  "direction": "inbound",
  "sender_display_name": "string | null",
  "content": "string",
  "content_type": "text | image | video | audio | file | sticker",
  "event_type": "message",
  "channel_timestamp": "ISO 8601 datetime",
  "metadata": {
    "source_category": "chat | order_reference | fetch_history",
    "marketplace_order_id": "string | null",
    "shop_id": "string | null",
    "order_status_ref": "string | null",
    "fetch_batch_id": "string | null",
    "structured_content": "object | null (marketplace order refs, rich content)"
  },
  "attachments": [
    {
      "type": "image | video | audio | file",
      "content_type": "MIME type",
      "size": "number | null",
      "download_url": "string (channel-specific URL for async download)"
    }
  ]
}
```

### 4.2 NormalizationError Contract

```json
{
  "success": false,
  "error_type": "mapping_error | unsupported_event | validation_error",
  "error_detail": "Human-readable error message",
  "error_context": {
    "field": "string | null",
    "expected": "string | null",
    "actual": "string | null"
  },
  "channel_type": "string",
  "raw_event_id": "uuid | null"
}
```

---

## 5. Common Headers & Conventions

### Headers

| Header | Description | Applies To |
|---|---|---|
| `X-Tenant-Id` | Required — all queries scoped to tenant | All API calls |
| `Authorization` | Bearer token for authentication | Public APIs |
| `Cache-Control` | Standard caching — static URLs are permanent | Attachment download |

### Conventions

| Convention | Detail |
|---|---|
| Pagination | Cursor-based using `?cursor=` and `?limit=` (default 20, max 100) |
| Sorting | `?sort=field` and `?order=asc|desc` |
| Response envelope | `{ data: T, meta: { cursor, has_more } }` |
| Error format | `{ error: { code, message, details? } }` |
| Timestamps | ISO 8601 UTC |
| IDs | UUID v4 |

### Error Response

```json
{
  "error": {
    "code": "CONVERSATION_NOT_FOUND",
    "message": "Conversation not found or access denied",
    "details": {}
  }
}
```

### Pagination Contract

- Cursor-based using `created_at` (messages) or `last_message_at` (conversations)
- Cursor value = ISO 8601 timestamp of last item
- `has_more: true` when there are more items beyond current page
- New messages arriving during pagination do NOT affect older pages (no duplicates, no skips)
- New messages are delivered via real-time channel (WebSocket/SSE), not pagination

---

## API Summary by Category

| Category | Count | Endpoints |
|---|---|---|
| **Webhooks** | 6 | POST `/webhooks/{channel}` x 6 channels |
| **Public - Contacts** | 3 | List, Get, Update on `/api/v1/contacts` |
| **Public - Conversations** | 4 | List, Get, Update, Messages on `/api/v1/conversations` |
| **Public - Messages** | 2 | Send, Get on `/api/v1/messages` |
| **Public - Attachments** | 2 | Metadata, Download on `/api/v1/attachments` |
| **Internal - Persistence** | 5 | raw-events (POST + PATCH), messages/inbound, attachments CRUD |
| **Internal - File Service** | 2 | presigned-url, upload |
| **Subtotal (this doc)** | **24** | |
| **FND-01 (separate)** | 14 | Tenant CRUD (5) + Channel Account CRUD (5) + Connection (1) + Credential Refs (3) |
