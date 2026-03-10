# ACE-39 (NDP-03): Normalization Pipeline v1 — API Table

## Context

Internal ingestion interface and per-channel normalization contracts. Defines the NormalizedEvent and NormalizationError data structures.

---

## Internal Ingestion Interface

| Method | Endpoint | Description | Key Params |
|---|---|---|---|
| POST | `/internal/ingest` or Queue consumer | Ingest raw event into pipeline | `{ raw_payload, channel_type, tenant_id, channel_account_id, event_category? }` |

---

## Normalization Contract (Per Channel)

| Channel | Mapper | Input | Output |
|---|---|---|---|
| LINE | `LineMapper.normalize()` | LINE webhook event body | `NormalizedEvent` |
| Facebook | `FacebookMapper.normalize()` | FB Messenger webhook entry | `NormalizedEvent` |
| Instagram | `InstagramMapper.normalize()` | IG Messaging webhook entry | `NormalizedEvent` |
| TikTok | `TikTokMapper.normalize()` | TikTok webhook event | `NormalizedEvent` |
| Shopee | `ShopeeMapper.normalizeChat()` | Shopee chat message | `NormalizedEvent` |
| Shopee | `ShopeeMapper.normalizeOrderRef()` | Shopee order event | `NormalizedEvent` with order metadata |
| Shopee | `ShopeeMapper.normalizeHistoryBatch()` | Shopee fetch history result | `NormalizedEvent[]` |
| Lazada | `LazadaMapper.normalizeChat()` | Lazada chat message | `NormalizedEvent` |
| Lazada | `LazadaMapper.normalizeOrderRef()` | Lazada order event | `NormalizedEvent` with order metadata |
| Lazada | `LazadaMapper.normalizeHistoryBatch()` | Lazada fetch history result | `NormalizedEvent[]` |

---

## NormalizedEvent Contract

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

---

## NormalizationError Contract

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

> **Note:** Normalization failures are tracked directly on the `raw_events` table via `normalization_status`, `error_detail`, and `error_context` fields. No separate failure table needed for v1.
