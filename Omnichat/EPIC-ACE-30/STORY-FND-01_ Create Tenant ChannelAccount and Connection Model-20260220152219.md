# STORY-FND-01: Create Tenant ChannelAccount and Connection Model

## Service Routing

| External Path (API Gateway :3000) | Proxies To | Internal Path |
| ---| ---| --- |
| `POST /api/v1/tenants` | tenant-service :3012 | `POST /tenants` |
| `GET /api/v1/tenants` | tenant-service :3012 | `GET /tenants` |
| `GET /api/v1/tenants/:id` | tenant-service :3012 | `GET /tenants/:id` |
| `PATCH /api/v1/tenants/:id` | tenant-service :3012 | `PATCH /tenants/:id` |
| `DELETE /api/v1/tenants/:id` | tenant-service :3012 | `DELETE /tenants/:id` |
| `POST /api/v1/omnichat/channel-accounts` | omnichat-service :3011 | `POST /channel-accounts` |
| `GET /api/v1/omnichat/channel-accounts` | omnichat-service :3011 | `GET /channel-accounts` |
| `PATCH /api/v1/omnichat/channel-accounts/:id` | omnichat-service :3011 | `PATCH /channel-accounts/:id` |
| `DELETE /api/v1/omnichat/channel-accounts/:id` | omnichat-service :3011 | `DELETE /channel-accounts/:id` |
| `PATCH /api/v1/omnichat/channel-accounts/:id/connection` | omnichat-service :3011 | `PATCH /channel-accounts/:id/connection` |
| `POST /api/v1/omnichat/channel-accounts/:id/credential-ref` | omnichat-service :3011 | `POST /channel-accounts/:id/credential-ref` |
| `GET /api/v1/omnichat/channel-accounts/:id/credential-ref` | omnichat-service :3011 | `GET /channel-accounts/:id/credential-ref` |
| `PATCH /api/v1/omnichat/channel-credential-refs/:id` | omnichat-service :3011 | `PATCH /channel-credential-refs/:id` |
| `DELETE /api/v1/omnichat/channel-credential-refs/:id` | omnichat-service :3011 | `DELETE /channel-credential-refs/:id` |

* * *
## Internal APIs (Service-to-Service)
> **หมายเหตุ:** Internal APIs ใช้สำหรับ service-to-service เท่านั้น
### Tenant Service ()

| Method | Path | Request Body | Query | Response | Description |
| ---| ---| ---| ---| ---| --- |
| `POST` | `/tenants` | `{ name: string, status?: string }` | — | `Tenant` | สร้าง tenant |
| `GET` | `/tenants` | — | — | `{ tenants: Tenant[], total: number, limit: number, offset: number }` | ดึงรายการ tenant ทั้งหมด |
| `GET` | `/tenants/:id` | — | — | `Tenant` | ดึง tenant ตาม ID |
| `PATCH` | `/tenants/:id` | `{ name?: string, status?: string }` | — | `Tenant` | แก้ไข tenant |
| `DELETE` | `/tenants/:id` | — | — | `{ message: string }` | Soft delete tenant |

### Omnichat Service ()
**Channel Accounts**

| Method | Path | Request Body | Query | Response | Description |
| ---| ---| ---| ---| ---| --- |
| `POST` | `/channel-accounts` | `{ tenant_id, channel_type, external_account_id, display_name?, credential_ref_id?, created_by? }` | — | `ChannelAccount` | สร้าง / restore channel account |
| `GET` | `/channel-accounts` | — | `tenant_id, channel_type?` | `{ accounts: ChannelAccount[], total: number, limit: number, offset: number }` | ดึงรายการ channel account |
| `PATCH` | `/channel-accounts/:id` | `{ display_name? }` | — | `ChannelAccount` | แก้ไข display name |
| `DELETE` | `/channel-accounts/:id` | — | — | `{ message: string }` | Soft delete channel account |
| `PATCH` | `/channel-accounts/:id/connection` | `{ connection_status, last_error_summary?, error_code_category? }` | — | `ChannelAccount` | อัปเดตสถานะ connection |
| `POST` | `/channel-accounts/:id/credential-ref` | `{ provider, reference_key, description? }` | — | `ChannelCredentialRef` | สร้าง / restore credential ref |
| `GET` | `/channel-accounts/:id/credential-ref` | — | — | `ChannelCredentialRef` | ดึง credential ref ของ account |

**Channel Credential Refs**

| Method | Path | Request Body | Query | Response | Description |
| ---| ---| ---| ---| ---| --- |
| `PATCH` | `/channel-credential-refs/:id` | `{ provider?, reference_key?, description? }` | — | `ChannelCredentialRef` | แก้ไข credential ref |
| `DELETE` | `/channel-credential-refs/:id` | — | — | `{ message: string }` | Soft delete credential ref |

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