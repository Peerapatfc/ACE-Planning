# ACE-25 STORY-FND-01: Create Tenant ChannelAccount and Connection Model

> **Status:** `IN DEVELOPMENT` &nbsp; | &nbsp; **Assignees:** griangsak

## 📝 Description
As a Platform Admin
I want a tenant level channel account and connection model
so that one tenant can connect multiple accounts per channel and we can manage connection state consistently.
Detail / Description
ต้องมีโครงสร้างข้อมูลกลางที่รองรับ 1 tenant ต่อหลายช่องทาง และต่อ 1 ช่องทางได้หลายบัญชี เช่น LINE OA หลายอัน หรือหลาย Facebook Page พร้อมเก็บสถานะการเชื่อมต่อและ metadata ที่จำเป็น เพื่อให้ connector และ inbox ในอนาคตใช้งานต่อได้โดยไม่ต้องเปลี่ยน schema ใหญ่
Scope of this story:
ออกแบบ entity และความสัมพันธ์ขั้นต่ำ: Tenant, ChannelAccount, ChannelConnection, ChannelCredentialRef
รองรับ channels: line, facebook, instagram, tiktok, shopee, lazada
เก็บข้อมูลหลัก: external account id, display name, connected status, last checked, last error, created by, updated at
รองรับ multi account per channel per tenant
ไม่รวมหน้าจอ UI (ไปอยู่ story FND 05)
Acceptance Criteria
Channel account model supports multi accounts
Given a tenant exists
When the system creates channel accounts for multiple channels and multiple accounts per channel
Then all channel accounts are stored with unique keys per tenant and can be retrieved by tenant id and channel type
Connection state is trackable
Given a channel account is created
When connection status is updated to connected or error
Then the latest status, last checked timestamp, and last error summary are persisted and queryable
Audit fields and soft delete
Given a channel account exists
When an admin removes a connection
Then the record is either soft deleted or marked disconnected with retained history as defined by the data policy
UI/UX Notes
ไม่มี UI ใน story นี้
แต่ต้องมี field ที่ UI จะใช้แสดงได้ เช่น display name, status, last checked, last error
Technical Notes
ใช้แนวทาง schema ที่ “ไม่ผูกกับ vendor” เพื่อกัน API change
แยก credential เป็น reference (ไม่เก็บ token ตรง ๆ ใน record นี้) เพื่อให้ security ทำงานง่าย
มี enum สำหรับ channel และ status
APIs 
POST create channel account
GET list channel accounts by tenant
PATCH update connection status and metadata
(ชื่อ path ให้ทีมไปกำหนดตาม convention)
Data 
Tables or collections: channel_accounts, channel_connections
Index: tenant_id, channel_type, external_account_id
Integrations 
ยังไม่เชื่อม platform จริงใน story นี้
Offer Logic 
None
Dependencies
เลือก DB และ migration framework ให้พร้อม
ต้องมี tenant model อยู่แล้วหรือสร้าง mock tenant ได้
Special focus 
Data design ต้องรองรับ scale และการเพิ่ม channel ใหม่ในอนาคต
QA / Test Considerations
Primary flows
Create tenant, create multiple channel accounts, update status
Edge Cases
สร้าง account ซ้ำด้วย external_account_id เดิม
เปลี่ยนชื่อ display name จาก platform
Business-Critical Must Not Break
การ query list channel accounts ต่อ tenant ต้องเสถียร เพราะทุก epic หลังจากนี้ใช้ต่อ
Test Types
Unit tests schema and repository
Integration tests for CRUD endpoints and indexes

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
| Create Tenant Service | BACKLOG |
| Create Tenant Module | BACKLOG |
| Create Channel Account Module | BACKLOG |
| Create Channel Connection Module | BACKLOG |
| Create Channel Credential Ref Module | BACKLOG |
| Unit Test Service | BACKLOG |
| [QA] | BACKLOG |

## 🔧 Technical Requirements
| Requirement | Needed? |
|---|---|
| Sequence Diagram | ❌ |
| ER Diagram | ✅ |
| API Spec | ✅ |
