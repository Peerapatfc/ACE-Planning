# ACE-38 (NDP-02): Message Persistence v1 — API Table

## Context

Internal service interfaces for the persistence layer. Not exposed as REST API directly — consumed by NDP-03 (Normalization) and NDP-05 (Query API).

---

## Persistence Service (Write)

| Method | Interface | Description | Key Params |
|---|---|---|---|
| `persistInboundMessage` | Internal | Upsert contact + conversation, idempotent insert message | `normalizedEvent { tenant_id, channel_type, external_user_id, external_thread_id, external_message_id, content, ... }` |
| `persistOutboundMessage` | Internal | Insert outbound message, update conversation | `{ tenant_id, conversation_id, channel_account_id, content, content_type, sender_display_name }` |
| `updateMessageStatus` | Internal | Update message after channel API response | `{ message_id, external_message_id?, status }` |
| `persistAttachmentMetadata` | Internal | Insert attachment metadata (status=pending) | `{ message_id, tenant_id, type, content_type, size }` |

---

## Query Service (Read)

| Method | Interface | Description | Key Params |
|---|---|---|---|
| `listConversations` | Internal | List conversations for tenant with filters | `{ tenant_id, channel_type?, channel_account_id?, status?, cursor?, limit? }` |
| `listMessages` | Internal | Paginated messages for a conversation | `{ tenant_id, conversation_id, cursor?, limit? }` |
| `getConversation` | Internal | Get single conversation with summary | `{ tenant_id, conversation_id }` |
| `getMessage` | Internal | Get single message with attachments | `{ tenant_id, message_id }` |

---

## Response Contracts

### persistInboundMessage Response

```json
{
  "message_id": "uuid",
  "contact_id": "uuid",
  "conversation_id": "uuid",
  "is_duplicate": false
}
```

### listMessages Response

```json
{
  "data": [
    {
      "id": "uuid",
      "direction": "inbound",
      "sender_type": "contact",
      "sender_display_name": "John Doe",
      "content": "สวัสดีครับ",
      "content_type": "text",
      "metadata": {},
      "status": "received",
      "channel_timestamp": "2025-01-15T10:30:00Z",
      "created_at": "2025-01-15T10:30:01Z",
      "attachments": [
        { "id": "uuid", "type": "image", "content_type": "image/jpeg", "size": 245678, "status": "uploaded", "failure_reason": null }
      ]
    }
  ],
  "meta": { "cursor": "2025-01-15T10:30:01Z", "has_more": true }
}
```

### listConversations Response

```json
{
  "data": [
    {
      "id": "uuid",
      "channel_type": "LINE",
      "channel_account_id": "uuid",
      "contact": { "id": "uuid", "display_name": "John Doe", "avatar_url": "https://..." },
      "status": "open",
      "last_message_preview": "สวัสดีครับ",
      "last_message_at": "2025-01-15T10:30:00Z"
    }
  ],
  "meta": { "cursor": "2025-01-15T10:30:00Z", "has_more": true }
}
```
