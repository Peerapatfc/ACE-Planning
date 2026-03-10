# ACE-27 STORY-FND-03: Implement Webhook Endpoints and Signature Verification for LINE and Meta

> **Status:** `BACKLOG` &nbsp; | &nbsp; **Assignees:** _Unassigned_

## 📝 Description
As a Connector Service
I want verified webhook endpoints for LINE and Meta
so that inbound events are authentic and can be ingested reliably.
Detail / Description
LINE และ Meta ใช้ webhook ส่ง event เข้ามา เราต้องมี endpoint ที่รับ event ได้ ตรวจ signature ได้ และตอบกลับตามที่ platform ต้องการ เพื่อให้การ verify ผ่านและ event เข้า pipeline ได้จริง
Scope of this story:
สร้าง webhook routes สำหรับ LINE และ Meta
ตรวจ signature ตามวิธีของแต่ละ platform
Parse payload แบบขั้นต่ำให้ส่งต่อ ingestion pipeline ได้
Handle challenge verification ที่ Meta ต้องใช้
Basic error handling และ response code ที่ถูกต้อง
ไม่รวม normalization ลึกและ persistence (ไปอยู่หมวด Normalized data)
Acceptance Criteria
Webhook verification passes for LINE
Given LINE sends a signed webhook request
When the request reaches our webhook endpoint
Then the signature is validated and a 200 response is returned for valid requests
Webhook verification passes for Meta challenge
Given Meta performs webhook verification challenge
When our endpoint receives the challenge request
Then the system responds with the correct challenge response and verification succeeds
Invalid signatures are rejected
Given a request with missing or invalid signature
When it hits the webhook endpoint
Then it is rejected with appropriate status and does not enter ingestion pipeline
UI/UX Notes
None
Technical Notes
ต้องมี trace id ต่อ request และ log ไม่เก็บ PII เกินจำเป็น
ต้อง handle retries จาก platform อย่างปลอดภัย
ต้อง map channel account จาก page id or line destination id ไปยัง tenant
APIs 
Public webhook endpoints for LINE and Meta
Internal enqueue endpoint or message bus publish call
Data 
Raw event log optional ระวัง PII ด้วย
Integrations 
LINE Messaging API
Meta Webhooks for Messenger and Instagram
Offer Logic 
None
Dependencies 
Domain and SSL for staging
Credential vault เพื่อดึง signing secret
ChannelAccount mapping ที่สร้างใน FND 01
Special focus 
Correctness and security of verification
Latency must be low to avoid webhook timeouts
QA / Test Considerations
Primary flows
Verify webhook for LINE and Meta in staging with test tools
Confirm events arrive and are accepted
Edge Cases
Duplicate webhook deliveries
Timeout and retry
Payload schema changes minor fields
Business-Critical Must Not Break
Accept valid events consistently, reject invalid events always
Test Types
Integration tests using platform sandbox
Contract tests with recorded payload fixtures

---

## 📋 Custom Fields
| Field | Value |
|---|---|
| Product | Omni |
| Product | ['25200cc8-2645-48fd-a858-654bc6c971df'] |

## 🏗️ Subtasks
| Subtask | Status |
|---|---|
| Sequence Diagram | BACKLOG |
| ER Diagram | BACKLOG |
| Create Web-hook service | BACKLOG |
| Create Web-hook module (แยก Endpoint แต่ละ Platform) | BACKLOG |
| Create Web-hook log module | BACKLOG |
| Unit test | BACKLOG |
| [QA] | BACKLOG |

## 🔧 Technical Requirements
| Requirement | Needed? |
|---|---|
| Sequence Diagram | ❌ |
| ER Diagram | ✅ |
| API Spec | ✅ |
