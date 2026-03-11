# STORY-MKT-02: Scheduled Polling Framework v1 (ACE-702)

**Title:** STORY-MKT-02: Scheduled Polling Framework v1 for Marketplace Ingest

**User Story:**
As a System
I want a scheduled polling framework to periodically fetch new messages from marketplace APIs
so that we can ingest data without relying on webhooks which may be unreliable or unavailable for certain marketplaces.

**Detail / Description:**
ระบบ Polling ที่จะทำหน้าที่วน loop ไปตาม marketplace_accounts ที่ connected อยู่ เพื่อ fetch data (Chat Messages, Orders) ตาม interval ที่กำหนด โดยต้องจัดการเรื่อง error handling, rate limit และ tracking 'last fetched timestamp' เพื่อไม่ให้ดึงข้อมูลซ้ำ

**Scope of this story:**
1. Polling orchestrator (scheduler) for marketplace accounts
2. Generic polling service that can be extended for Tikok, Shopee, Lazada
3. Tracking last_fetch_timestamp per account/type
4. Handling API Rate Limits (Backoff mechanism)
5. Basic error logging for failed poll attempts

**Acceptance Criteria:**
1. Scheduled Trigger: The system triggers a poll task every X minutes (configurable) for all active marketplace accounts.
2. Avoid Duplicates: The system uses last_fetch_timestamp and marketplace-specific offsets to ensure no duplicate messages are ingested.
3. Error Resilience: If a poll fails, the system logs the error and retries in the next cycle without crashing the scheduler.
4. Scale-ready: The framework can handle multiple accounts across different marketplaces concurrently.

**Subtasks:**
- ACE-708: task
- ACE-1255: Diagrams
- ACE-1256: Shopee Scheduled Polling fetch Chat Message
- ACE-1257: Lazada Scheduled Polling fetch Chat Message
- ACE-1258: Tiktok Scheduled Polling fetch Chat Message
