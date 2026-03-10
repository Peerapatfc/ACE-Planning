# ACE-37 (NDP-01): Define Normalized Schema v1 — API Table

## Context

APIs ที่อยู่ใน scope ของ ACE-37 — เฉพาะ Webhooks, Internal APIs, และ File Service ที่ใช้ใน sequence diagram เท่านั้น Public CRUD APIs (Channel Accounts, Contacts, Conversations, Messages, Attachments) อยู่ใน [api-table-public.md](api-table-public.md) สำหรับ story NDP-05

---

## Service Routing

| Path Prefix | Routed To | Notes |
|---|---|---|
| `/api/v1/*` | **API Gateway** (:3000) → **Omnichat Service** (:3011) | Auth & tenant extraction at API Gateway, business logic at Omnichat Service |
| `/webhooks/*` | **Omnichat Gateway** (:3010) | Direct — no API Gateway, signature validation at Gateway |
| `/internal/*` | **Omnichat Service** (:3011) | Service-to-service only — API Gateway ต้อง block จากภายนอก |
| `/files/*` | **File Service** (:3005) | Service-to-service only — API Gateway ต้อง block จากภายนอก |

---

## Webhooks (Inbound)

| Method | Endpoint | Description | Key Params |
|---|---|---|---|
| POST | `/webhooks/line` | Receive LINE webhook events | Signature in header |
| POST | `/webhooks/facebook` | Receive Facebook Messenger webhook events | Signature in header |
| POST | `/webhooks/instagram` | Receive Instagram Messaging webhook events | Signature in header |
| POST | `/webhooks/tiktok` | Receive TikTok webhook events | Signature in header |
| POST | `/webhooks/shopee` | Receive Shopee webhook events | Signature in header |
| POST | `/webhooks/lazada` | Receive Lazada webhook events | Signature in header |

## Internal APIs (Service-to-Service)

> **หมายเหตุ:** Internal APIs ใช้สำหรับ service-to-service เท่านั้น — API Gateway ต้อง block `/internal/*` และ `/files/*` จากภายนอก

### Omnichat Service (`/internal/*`)

| Method | Endpoint | Caller | Description | Key Params |
|---|---|---|---|---|
| POST | `/internal/raw-events` | Normalizer Worker | Store redacted raw webhook event | `redacted_payload`, `channel_type`, `tenant_id`, `pii_safe` |
| POST | `/internal/messages/inbound` | Normalizer Worker | Persist normalized inbound data (contact + conversation + message) | `contact`, `conversation`, `message`, `attachments_metadata?` |
| POST | `/internal/attachments` | Normalizer Worker | Create attachment record (status: pending) | `message_id`, `type`, `content_type`, `tenant_id` |
| PATCH | `/internal/attachments/:id` | Normalizer Worker | Update attachment after upload or on failure | `storage_key`, `size`, `checksum`, `status` |

### File Service (`/files/*`)

| Method | Endpoint | Caller | Description | Key Params |
|---|---|---|---|---|
| POST | `/files/presigned-url` | Omnichat Service | Generate S3 presigned upload URL (returns presigned PUT URL + static file_url) | `filename`, `folder`, `tenant_id` |
| POST | `/files/upload` | Normalizer Worker | Upload binary file to S3 (returns storage_key + static file_url) | `binary`, `content_type`, `tenant_id`, `folder` |

## Common Headers & Conventions

| Header | Description |
|---|---|
| `X-Tenant-Id` | Required on all API calls for tenant isolation |
| `Authorization` | Bearer token for authentication |

| Convention | Detail |
|---|---|
| Pagination | Cursor-based using `?cursor=` and `?limit=` (default 20, max 100) |
| Sorting | `?sort=field` and `?order=asc|desc` |
| Response envelope | `{ data: T, meta: { cursor, has_more } }` |
| Error format | `{ error: { code, message, details? } }` |
| Timestamps | ISO 8601 UTC |
| IDs | UUID v4 |
