# ACE-26 STORY-FND-02: Implement Secure Credential Storage and Access Controls

> **Status:** `BACKLOG` &nbsp; | &nbsp; **Assignees:** _Unassigned_

## 📝 Description
As a System Owner
I want secure credential storage and controlled access to channel tokens and secrets
so that we protect customer accounts and meet basic security expectations for pilot usage.
Detail / Description
เมื่อเชื่อมต่อ LINE Meta และ marketplace เราจะได้ token secret key หรือ refresh token ต้องเก็บแบบปลอดภัย ไม่เก็บใน code หรือ plain text ใน DB ทั่วไป และต้องกำหนดสิทธิ์การอ่านให้จำกัดเฉพาะ service ที่ต้องใช้ รวมถึงรองรับ rotation หรือ reconnect ขั้นต่ำ
Scope of this story:
เลือกแนวทางเก็บ secret เช่น secret manager หรือ encrypted store
สร้าง abstraction CredentialVault interface ที่ connector ใช้เรียก
เก็บ credential แบบมี version และ metadata: created at, expires at, last rotated, scope
Access control: service roles ที่อ่านได้, admin view แบบ mask ได้
ไม่รวมการทำ SSO RBAC enterprise (อยู่นอก scope epic นี้)
Acceptance Criteria
Credentials are never stored in plain text
Given the system receives a token or secret for a channel
When the credential is stored
Then it is encrypted at rest and is not visible in logs or plain database fields
Only authorized services can read credentials
Given a credential exists
When an unauthorized caller requests credential material
Then access is denied and an audit entry is recorded
Safe masking for admin viewing
Given an admin views connection details
When the UI requests credential display
Then only masked values are returned and full secrets are never exposed
UI/UX Notes
UI แสดงได้แค่ masked token fingerprint และ expiry time
มีข้อความแนะนำ reconnect เมื่อ token invalid
Technical Notes
ห้าม log token ใน request logs
ใช้ key rotation strategy ตั้งแต่ต้น 
ต้องมี audit log ขั้นต่ำสำหรับ credential access
APIs 
PUT store credential for channel account
GET masked credential metadata
POST revoke or rotate credential
Data 
credential_store: encrypted blob, key id, version, expiry, channel_account_id
Integrations 
Secret manager provider ตาม infra ที่ใช้จริง
Offer Logic 
None
Dependencies 
DevOps ต้องเตรียม secret manager และ IAM roles
ต้องมี channel_account_id จาก FND 01
Special focus 
Security review เบื้องต้นก่อนเปิด pilot
QA / Test Considerations
Primary flows
Store credential, retrieve for connector, verify masked view
Edge Cases
token หมดอายุแต่ยังถูกเรียกใช้
credential version mismatch ระหว่าง service
Business-Critical Must Not Break
ห้ามมีการรั่ว token ลง log หรือ error message เด็ดขาด
Test Types
Unit tests for encryption wrapper
Integration tests with secret store in staging
Security tests for access control

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
| API Table | BACKLOG |
| Create Credential Store Module (on Tenant Service) | BACKLOG |
| Uni test | BACKLOG |
| [QA] | BACKLOG |

## 🔧 Technical Requirements
| Requirement | Needed? |
|---|---|
| Sequence Diagram | ❌ |
| ER Diagram | ❌ |
| API Spec | ✅ |
