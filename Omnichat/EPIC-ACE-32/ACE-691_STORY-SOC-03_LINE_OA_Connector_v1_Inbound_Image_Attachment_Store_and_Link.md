# ACE-691 STORY-SOC-03: LINE OA Connector v1 Inbound Image Attachment Store and Link

> **Status:** `TO DO` &nbsp; | &nbsp; **Assignees:** `Unassigned`

## 📝 Description
As a Connector Service, I want to ingest LINE inbound image messages and store attachments securely so that images can be displayed later in the inbox and remain tenant isolated.

**Detail / Description:**
Story นี้ต้องทำให้รูปเข้าได้จริง โดย workflow คือรับ event รูป แล้วดาวน์โหลด binary จาก LINE content API แล้วเก็บลง object storage แล้วสร้าง attachment record เชื่อมกับ message ถ้า attachment fail ต้องไม่ทำให้ message หาย

**Scope of this story:**
1. Handle LINE inbound image message event.
2. Download content from LINE content API.
3. Store binary in object storage and create attachment metadata record.
4. Link attachment to message in schema v1.
5. Support retry and failure state for attachment processing.
6. Not include other attachment types beyond image in R1.

**Acceptance Criteria:**
1. **Image event is normalized and message is persisted even if attachment is delayed:** Given a LINE inbound image event arrives, when it is processed, then a message record is persisted and attachment processing is triggered asynchronously or within controlled time.
2. **Image binary is downloaded and stored securely:** Given a valid LINE image content id exists, when the system fetches the binary, then it stores it in object storage and creates an attachment record with `storage_key` and metadata.
3. **Secure retrieval reference is created:** Given an attachment record exists, when a client requests access to the image, then the system provides a signed URL or proxy link with expiry and tenant check enforced.
4. **Attachment failure does not drop message and is observable:** Given the image download fails, when processing completes, then the message remains persisted and attachment status is failed with `failure_reason` and retryable flag.

---

## 📋 Custom Fields
| Field | Value |
|---|---|
| Product | Omni |

## 🏗️ Subtasks
| Subtask | Status |
|---|---|
| None | None |

## 🔧 Technical Requirements
| Requirement | Needed? |
|---|---|
| Sequence Diagram | ❌ |
| ER Diagram | ✅ |
| API Spec | ✅ |
