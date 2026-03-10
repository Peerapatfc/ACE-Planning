# ACE-40 STORY-NDP-04: Implement Attachment Storage v1 Metadata and Secure Retrieval

> **Status:** `BACKLOG` &nbsp; | &nbsp; **Assignees:** _Unassigned_

## 📝 Description
As a System
I want attachment metadata and storage integration
so that inbound images and files can be stored securely and referenced in conversation timelines.
Detail / Description
ทำ attachment pipeline ให้พร้อมสำหรับ inbox ในอนาคต โดย R1 must have คือ LINE images end to end คือเก็บ binary ใน object storage และเก็บ metadata ใน DB พร้อม status เพื่อรองรับ retry และไม่ทำให้ webhook ล่ม
Scope of this story:
Attachment metadata model and persistence
Object storage integration
LINE image download store retrieve flow end to end
Signed URL or proxy retrieval strategy
Size limits and basic content type validation
Acceptance Criteria
LINE image downloaded and stored end to end
Given a LINE inbound image event
When the system processes the event
Then it downloads the binary stores it in object storage and creates an attachment record linked to the message
Secure retrieval does not expose storage secrets
Given an attachment exists
When a client requests access
Then the system returns a signed URL or proxy endpoint with time limited access and no secret leakage
Validation for size and content type
Given an attachment exceeds limits or has unsupported content type
When processing occurs
Then the attachment is rejected or marked unsupported and the message still persists
Attachment failure does not drop message persistence
Given attachment download fails
When processing the message
Then message is persisted and attachment is marked failed with failure reason and retryable flag
Controlled retries with backoff and cap
Given a temporary failure
When retry is triggered
Then it retries with backoff up to a defined limit and stops with final failed state after limit
Tenant isolation for attachment access
Given attachments exist for two tenants
When one tenant requests another tenant attachment
Then access is denied
UI/UX Notes
Inbox UI later should show placeholders for pending or failed attachments
Surface file size and type from metadata
Technical Notes
APIs 
GET attachment secure link or proxy
Internal worker job for downloading and storing media
Data 
attachments includes storage_key size content_type status failure_reason checksum optional
Integrations 
Object storage provider
LINE content API for media download
Offer Logic 
None
Dependencies 
Object storage and IAM roles ready
NDP 02 persistence ready
Special focus 
Security and access control
Avoid long running work in webhook response path by using async worker where needed
QA / Test Considerations
Primary flows
Ingest LINE image and retrieve via secure link
Verify link expiration behavior
Edge Cases
Corrupted file
Duplicate media id
Large image causing timeout
Business-Critical Must Not Break
Must not leak storage credentials
Must not allow cross tenant access
Test Types
Integration tests with object storage
Security tests for signed URL or proxy access rules

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
| API | BACKLOG |
| S3 Service | BACKLOG |

## 🔧 Technical Requirements
| Requirement | Needed? |
|---|---|
| Sequence Diagram | ❌ |
| ER Diagram | ✅ |
| API Spec | ✅ |
