# ACE-690 STORY-SOC-02: LINE OA Connector v1 Outbound Send Text and Persist

> **Status:** `TO DO` &nbsp; | &nbsp; **Assignees:** `Unassigned`

## 📝 Description
As a Support Agent System, I want to send outbound text messages to LINE OA and persist them in the same conversation timeline so that the inbox and audit history remain consistent during pilot.

**Detail / Description:**
Story นี้ทำให้ระบบเราส่งข้อความออกไปยัง LINE ได้ และบันทึก outbound message ลง message store ด้วย `direction`: outbound หลักๆคือส่งผ่าน LINE API ด้วย credential จาก vault และ handle error codes ให้ชัด เพื่อให้ทีม support รู้ว่า fail เพราะอะไร

**Scope of this story:**
1. Implement `sendMessage` for LINE text.
2. Validate conversation belongs to tenant and has LINE channel context.
3. Persist outbound message record on success and store failure reason on failure.
4. Basic rate limit handling (minimal, not full tuning).
5. Not include rich templates, stickers, or other message types in R1.

**Acceptance Criteria:**
1. **Validated outbound request uses correct tenant and channel account:** Given an agent requests to send a message for a conversation, when the system prepares the LINE API call, then it verifies tenant ownership and selects the correct `channel_account_id` and access token.
2. **LINE API send succeeds and outbound message is persisted:** Given LINE API returns success, when the send operation completes, then an outbound message record is created with `direction`: outbound and linked to the same `conversation_id`.
3. **Send failure is handled with clear error category:** Given LINE API returns an error such as unauthorized or invalid token, when the system handles the response, then it records a failure with error category `auth_error` and does not leak token information.
4. **Retry behavior is safe and does not duplicate outbound messages:** Given a transient network error occurs during send, when the system retries according to policy, then it does not create duplicate outbound records and final status is consistent.

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
