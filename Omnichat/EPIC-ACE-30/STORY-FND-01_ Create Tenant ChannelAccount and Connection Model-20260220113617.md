# STORY-FND-01: Create Tenant ChannelAccount and Connection Model

## Service Routing

| External Path (API Gateway :3000) | Proxies To | Internal Path |
| ---| ---| --- |
| `POST /api/v1/tenants` | tenant-service :3012 | `POST /internal/tenants` |
| `GET /api/v1/tenants` | tenant-service :3012 | `GET /internal/tenants` |
| `GET /api/v1/tenants/:id` | tenant-service :3012 | `GET /internal/tenants/:id` |
| `PATCH /api/v1/tenants/:id` | tenant-service :3012 | `PATCH /internal/tenants/:id` |
| `DELETE /api/v1/tenants/:id` | tenant-service :3012 | `DELETE /internal/tenants/:id` |
| `POST /api/v1/channel-accounts` | omnichat-service :3011 | `POST /internal/channel-accounts` |
| `GET /api/v1/channel-accounts` | omnichat-service :3011 | `GET /internal/channel-accounts` |
| `PATCH /api/v1/channel-accounts/:id` | omnichat-service :3011 | `PATCH /internal/channel-accounts/:id` |
| `DELETE /api/v1/channel-accounts/:id` | omnichat-service :3011 | `DELETE /internal/channel-accounts/:id` |
| `PATCH /api/v1/channel-accounts/:id/connection` | omnichat-service :3011 | `PATCH /internal/channel-accounts/:id/connection` |
| `POST /api/v1/channel-accounts/:id/credential-ref` | omnichat-service :3011 | `POST /internal/channel-accounts/:id/credential-ref` |
| `GET /api/v1/channel-accounts/:id/credential-ref` | omnichat-service :3011 | `GET /internal/channel-accounts/:id/credential-ref` |
| `PATCH /api/v1/channel-credential-refs/:id` | omnichat-service :3011 | `PATCH /internal/channel-credential-refs/:id` |
| `DELETE /api/v1/channel-credential-refs/:id` | omnichat-service :3011 | `DELETE /internal/channel-credential-refs/:id` |

* * *
## Internal APIs (Service-to-Service)
> **หมายเหตุ:** Internal APIs ใช้สำหรับ service-to-service เท่านั้น — API Gateway ต้อง block `/internal/*` และ `/files/*` จากภายนอก
### Tenant Service (`/internal/*`)

| Method | Path | Request Body | Query | Response | Description |
| ---| ---| ---| ---| ---| --- |
| `POST` | `/internal/tenants` | `{ name: string, status?: string }` | — | `Tenant` | สร้าง tenant |
| `GET` | `/internal/tenants` | — | — | `{ tenants: Tenant[], total: number, limit: number, offset: number }` | ดึงรายการ tenant ทั้งหมด |
| `GET` | `/internal/tenants/:id` | — | — | `Tenant` | ดึง tenant ตาม ID |
| `PATCH` | `/internal/tenants/:id` | `{ name?: string, status?: string }` | — | `Tenant` | แก้ไข tenant |
| `DELETE` | `/internal/tenants/:id` | — | — | `{ message: string }` | Soft delete tenant |

### Omnichat Service (`/internal/*`)
**Channel Accounts**

| Method | Path | Request Body | Query | Response | Description |
| ---| ---| ---| ---| ---| --- |
| `POST` | `/internal/channel-accounts` | `{ tenant_id, channel_type, external_account_id, display_name?, credential_ref_id?, created_by? }` | — | `ChannelAccount` | สร้าง / restore channel account |
| `GET` | `/internal/channel-accounts` | — | `tenant_id, channel_type?` | `{ accounts: ChannelAccount[], total: number, limit: number, offset: number }` | ดึงรายการ channel account |
| `PATCH` | `/internal/channel-accounts/:id` | `{ display_name? }` | — | `ChannelAccount` | แก้ไข display name |
| `DELETE` | `/internal/channel-accounts/:id` | — | — | `{ message: string }` | Soft delete channel account |
| `PATCH` | `/internal/channel-accounts/:id/connection` | `{ connection_status, last_error_summary?, error_code_category? }` | — | `ChannelAccount` | อัปเดตสถานะ connection |
| `POST` | `/internal/channel-accounts/:id/credential-ref` | `{ provider, reference_key, description? }` | — | `ChannelCredentialRef` | สร้าง / restore credential ref |
| `GET` | `/internal/channel-accounts/:id/credential-ref` | — | — | `ChannelCredentialRef` | ดึง credential ref ของ account |

**Channel Credential Refs**

| Method | Path | Request Body | Query | Response | Description |
| ---| ---| ---| ---| ---| --- |
| `PATCH` | `/internal/channel-credential-refs/:id` | `{ provider?, reference_key?, description? }` | — | `ChannelCredentialRef` | แก้ไข credential ref |
| `DELETE` | `/internal/channel-credential-refs/:id` | — | — | `{ message: string }` | Soft delete credential ref |

* * *
## Common Headers & Conventions

| Item | Value | Note |
| ---| ---| --- |
| Content-Type | `application/json` | ทุก request |
| API Prefix | `/api/v1` | เฉพาะ external (API Gateway) |
| Internal Prefix | `/internal` | เฉพาะ service-to-service |
| Soft Delete | `deleted_at: Date | null` | ใช้ทุก entity แทนการลบจริง |
| UUID | `@default(uuid())` | Primary key ทุก entity |
| Status (Tenant) | `active | inactive | suspended` |  |
| Status (ChannelAccount) | `active | inactive` |  |
| Connection Status | `pending | connected | error | disconnected | expired` |  |
| Channel Types | `LINE | FACEBOOK | INSTAGRAM | TIKTOK | SHOPEE | LAZADA` |  |

##