# ACE-37 STORY-NDP-01: Define Normalized Schema v1 Contact Conversation Message Attachment ChannelAccount

> **Status:** `IN DEVELOPMENT` &nbsp; | &nbsp; **Assignees:** Peerapat Pongnipakorn

## 📝 Description
As a Platform Engineer
I want a normalized data schema v1 for contacts conversations messages attachments and channel accounts
so that all channels can be stored and queried using one consistent model for Inbox AI and Analytics.
Detail / Description
“กำหนด Data Model กลาง” ของระบบ Omnichannel เพื่อให้ทุก channel (LINE Meta TikTok Shopee Lazada) ถูกแปลงและจัดเก็บเป็นรูปแบบเดียวกัน ลดการทำงานซ้ำของ dev และทำให้ Epic ถัดไปอย่าง Unified Inbox และ AI ใช้ข้อมูลได้ทันที เพื่อใช้งานจริงได้ง่ายต่อไป
ใช้ SQL database เช่น PostgreSQL เป็น primary store (เหมาะกับ multi tenant และ query timeline)
เก็บ raw payload ของแต่ละ channel เป็น JSONB (หรือ JSON column) เพื่อ debug และรองรับ field ใหม่ โดยไม่ต้อง migrate บ่อย
Attachment binary เก็บใน object storage เช่น S3 ส่วน DB เก็บแค่ metadata และ storage key
ตั้ง index และแนวทาง tenant isolation ไปตลอดจน security by design ตั้งแต่ day 1
Scope of this story:
Define entities และ relations ขั้นต่ำ
Tenant
ChannelAccount
Contact
Conversation
Message
Attachment
RawEvent optional but recommended
Define required fields and indexes for MVP performance
Define canonical identifiers and idempotency keys
Define minimal marketplace order reference structure (แค่ reference ไม่ใช่ OMS)
Provide migrations for staging environment
Acceptance Criteria
Multi tenant boundaries are explicit
Given a tenant id exists
When any entity record is created
Then tenant_id is required and used for access control and indexing in every table
Core message fields are complete and consistent
Given the schema v1 spec
When a message is stored
Then it includes message_id tenant_id channel_type channel_account_id conversation_id direction channel_timestamp created_at and content fields
Channel specific identifiers are preserved for traceability
Given an inbound event from any channel
When it is normalized
Then the record stores external_message_id external_user_id and external_thread_id when available for debugging and replay
Marketplace order references are supported without full OMS
Given a marketplace event includes order reference
When it is normalized
Then the message metadata includes marketplace_order_id shop_id and order_status_ref fields when present
Attachments store secure references not binaries in DB
Given an inbound attachment exists
When it is stored
Then attachment records include type size content_type storage_key status and optional checksum without storing binary in DB
Raw payload storage is safe and linked
Given raw payload storage is enabled
When an inbound event is processed
Then raw payload is stored as JSON or JSONB linked via raw_event_id with PII safe rules applied
UI/UX Notes
None for this story แต่ field naming ต้อง consistent เพราะ UI inbox จะดึงไปใช้ เช่น sender_display_name channel_badge last_message_preview
Technical Notes
APIs 
Not required in this story แต่ schema ต้องรองรับ planned APIs ใน story NDP 05
Data 
Recommended tables
channel_accounts
contacts
conversations
messages
attachments
raw_events optional
Recommended indexes
messages tenant_id created_at
messages tenant_id conversation_id created_at
conversations tenant_id channel_type external_thread_id
contacts tenant_id channel_type external_user_id
channel_accounts tenant_id channel_type external_account_id
Integrations 
None
Offer Logic 
None
Dependencies 
Tenant concept exists or can be mocked
channel_type enum and direction enum agreed
Special focus 
Keep schema stable for 6 months
Ensure tenant isolation and query performance for timeline
QA / Test Considerations
Primary flows
Apply migrations on staging
Insert one record per entity and query back by tenant
Edge Cases
Some channels lack external_thread_id for certain event types
Edited or deleted messages by platform store as event_type metadata v1
Business-Critical Must Not Break
Tenant isolation in all queries must be enforced
Test Types
Migration tests
Repository integration tests

---

## 📋 Custom Fields
| Field | Value |
|---|---|
| Product | Omni |
| Product | ['25200cc8-2645-48fd-a858-654bc6c971df'] |

## 🏗️ Subtasks
| Subtask | Status |
|---|---|
| Sequence Diagram | IN DEVELOPMENT |
| ER Diagram | IN DEVELOPMENT |
| API Table | IN DEVELOPMENT |
| Normalize Module | BACKLOG |
| [QA] | BACKLOG |

## 🔧 Technical Requirements
| Requirement | Needed? |
|---|---|
| Sequence Diagram | ❌ |
| ER Diagram | ✅ |
| API Spec | ✅ |
