# ACE-41 (NDP-05): Conversation Timeline Query API v1 — API Table

## Context

Full REST API specification for the read-side query APIs. These endpoints are consumed by Unified Inbox UI and AI services.

---

## Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/conversations` | List conversations for inbox |
| GET | `/api/v1/conversations/:id` | Get conversation detail |
| GET | `/api/v1/conversations/:id/messages` | Get message timeline |
| GET | `/api/v1/messages/:id` | Get message detail with attachments |
| GET | `/api/v1/contacts/:id` | Get contact detail (optional) |

---

## GET `/api/v1/conversations`

### Query Parameters

| Param | Type | Default | Description |
|---|---|---|---|
| `status` | string | — | Filter: `open`, `closed`, `snoozed` |
| `channel_type` | string | — | Filter: `LINE`, `FACEBOOK`, `INSTAGRAM`, `TIKTOK`, `SHOPEE`, `LAZADA` |
| `channel_account_id` | uuid | — | Filter by specific channel account |
| `cursor` | string | — | Cursor for pagination (last_message_at) |
| `limit` | integer | 20 | Page size (max 100) |
| `sort` | string | `last_message_at` | Sort field |
| `order` | string | `desc` | `asc` or `desc` |

### Response

```json
{
  "data": [
    {
      "id": "uuid",
      "channel_type": "LINE",
      "channel_account_id": "uuid",
      "channel_account_name": "My LINE OA",
      "status": "open",
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
  "meta": {
    "cursor": "2025-01-15T10:30:00Z",
    "has_more": true
  }
}
```

---

## GET `/api/v1/conversations/:id`

### Response

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
    "external_thread_id": "T5678...",
    "last_message_preview": "สวัสดีครับ",
    "last_message_at": "2025-01-15T10:30:00Z",
    "created_at": "2025-01-10T08:00:00Z"
  }
}
```

---

## GET `/api/v1/conversations/:id/messages`

### Query Parameters

| Param | Type | Default | Description |
|---|---|---|---|
| `cursor` | string | — | Cursor for pagination (created_at of last item) |
| `limit` | integer | 20 | Page size (max 100) |

### Response

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
          "failure_reason": null,
          "metadata": { "original_filename": "photo.jpg" }
        }
      ]
    },
    {
      "id": "uuid",
      "direction": "outbound",
      "sender_type": "agent",
      "sender_display_name": "Agent Smith",
      "content": "สวัสดีครับ ยินดีให้บริการ",
      "content_type": "text",
      "metadata": {},
      "event_type": "message",
      "status": "delivered",
      "channel_timestamp": "2025-01-15T10:32:00Z",
      "created_at": "2025-01-15T10:32:01Z",
      "attachments": []
    }
  ],
  "meta": {
    "cursor": "2025-01-15T10:30:01Z",
    "has_more": true
  }
}
```

---

## GET `/api/v1/messages/:id`

### Response

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
        "failure_reason": null,
        "checksum": "sha256:abc123...",
        "metadata": { "original_filename": "photo.jpg" }
      }
    ]
  }
}
```

---

## GET `/api/v1/contacts/:id`

### Response

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

---

## Common Headers

| Header | Description |
|---|---|
| `X-Tenant-Id` | Required — all queries scoped to tenant |
| `Authorization` | Bearer token |

## Error Response

```json
{
  "error": {
    "code": "CONVERSATION_NOT_FOUND",
    "message": "Conversation not found or access denied"
  }
}
```

## Pagination Contract

- Cursor-based using `created_at` (messages) or `last_message_at` (conversations)
- Cursor value = ISO 8601 timestamp of last item
- `has_more: true` when there are more items beyond current page
- New messages arriving during pagination do NOT affect older pages (no duplicates, no skips)
- New messages are delivered via real-time channel (WebSocket/SSE), not pagination
