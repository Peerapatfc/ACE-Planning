# STORY-MKT-01: Marketplace Channel Onboarding v1 (ACE-701)

**Title:** STORY-MKT-01: Marketplace Channel Onboarding v1 Connect Credentials and Account Mapping

**User Story:**
As a Tenant Admin
I want to connect TikTok, Shopee, and Lazada accounts into our system
so that we can ingest messages, orders, references, and enable outbound replies for baseline pilot usage.

**Detail / Description:**
Story นี้เป็น onboarding เฉพาะ marketplace (TikTok, Shopee, Lazada) ให้ “ต่อได้จริง” แบบ multi accounts ต่อ tenant ได้ สิ่งสำคัญคือ mapping ระหว่าง tenant กับร้านค้า marketplace (shop id, seller id) และเก็บ credential แบบปลอดภัย พร้อมสถานะ connected/error รวมถึงเตรียม data ที่ scheduled poll จะใช้ เช่น shop_id, region, marketplace_account_id

**Scope of this story:**
1. Connect flow spec และ backend support สำหรับ TikTok, Shopee, Lazada
2. Store credentials securely via Credential Vault (จาก FND-02) และเก็บ metadata ที่จำเป็น
3. Map marketplace external_account_id to channel_account_id and tenant_id
4. Connection status fields updated and visible
5. Support reconnect and token rotation flow (minimal)
6. Not include polling ingest logic (ไปอยู่ MKT-02 และ channel stories)

**Acceptance Criteria:**
1. Multi-tenant connect mapping is correct: Given a tenant exists, When the admin connects a marketplace account, Then the system creates a channel_account record with tenant_id, channel_type, and external_account_id that maps to the correct marketplace shop.
2. Credentials stored securely and not exposed: Given credential material is returned from marketplace auth, When the system stores credentials, Then they are saved in the encrypted vault and never logged in plain text.
3. Handle Re-authentication: When a token is expired or revoked, Then the connection status is updated to 'error' and the user can re-authenticate.
4. Support Multi-Account: A single tenant can connect multiple accounts from the same marketplace (e.g., 2 Shopee shops).
5. Data mapping for Polling: Necessary marketplace metadata (shop_id, region) is stored and accessible for the polling service.
6. Access control prevents cross-tenant connection leakage: Given two tenants exist, When messages are received for Tenant A's shop, Then they cannot be accessed by Tenant B.

**Subtasks:**
- ACE-1248: Connect Shopee & Update Channel Info
- ACE-1249: Connect Lazada & Update Channel Info
- ACE-1250: Connect Tiktok & Update Channel Info
- ACE-1251: Reconnect Shopee
- ACE-1252: Reconnect Lazada
- ACE-1253: Reconnect Tiktok
- ACE-1254: Diagrams
