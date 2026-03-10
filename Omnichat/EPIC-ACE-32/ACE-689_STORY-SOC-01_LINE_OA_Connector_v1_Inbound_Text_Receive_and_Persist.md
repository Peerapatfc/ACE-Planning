# ACE-689 STORY-SOC-01: LINE OA Connector v1 Inbound Text Receive and Persist

> **Status:** `TO DO` &nbsp; | &nbsp; **Assignees:** `Unassigned`

## 📝 Description
As a Connector Service, I want to ingest LINE OA inbound text events and persist them using the normalized pipeline so that messages from LINE appear in our unified conversation store for pilot usage.

**Detail / Description:**
Story นี้ทำให้ LINE ส่งข้อความเข้ามาแล้วระบบเรารับได้จริง end to end ตั้งแต่ webhook verify ผ่าน แล้วเข้า normalization pipeline แล้ว persist เป็น Contact Conversation Message ใน schema v1 เป้าหมายคือให้ทีมสามารถเริ่มทำ Unified Inbox ต่อได้ทันที โดยไม่ต้องแก้ ingestion path ใหม่

**Acceptance Criteria:**
1. Given a LINE event contains destination or channel identifiers, when the system processes the event, then it resolves `tenant_id` and `channel_account_id` correctly and rejects unknown mapping with clear error category.
2. Normalization to schema v1 is complete for inbound text.
3. Given an inbound LINE text message event, when the normalization pipeline runs, then it produces a normalized message with `channel_type`: line, `direction`: inbound, `external_message_id`, `external_user_id`, conversation mapping inputs, and `content_text`.
4. **Persistence creates correct entities:** Given the normalized message is produced, when persistence executes, then a contact is upserted, a conversation is created or reused, and exactly one message is inserted and linked correctly.
5. **Idempotency prevents duplicates on retry:** Given LINE retries the same webhook event, when the pipeline processes the duplicate delivery, then only one message record exists and the duplicate is rejected or treated as already processed.
6. **Failure handling and observability minimum:** Given persistence fails due to transient DB error, when ingestion occurs, then the failure is logged with trace id and error category, and connection status or ingest health counters are updated without exposing secrets.

**UI/UX Notes:**
- None directly แต่ต้องมี field สำหรับ inbox ในอนาคต เช่น `sender_display_name`, `channel_type`, `timestamp`.

**Technical Notes:**
- APIs: Public webhook endpoint already exists from FND 03. Internal ingest entrypoint or queue consumer from NDP 03.
- Unknown destination mapping should not crash service.

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
