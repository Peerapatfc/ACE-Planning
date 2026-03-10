# ACE-700 STORY-SOC-06: Meta Connector v1 Instagram DM Inbound and Outbound Text

> **Status:** `TO DO` &nbsp; | &nbsp; **Assignees:** `Unassigned`

## 📝 Description
As a Connector Service, I want to receive and send Instagram DM text messages and persist them in normalized schema so that Instagram conversations are usable in pilot as GA light.

**Detail / Description:**
Story นี้คล้าย Facebook แต่เป็น Instagram DM โดยใช้ Meta permissions and webhooks สำหรับ IG ต้องทำ mapping IG account id to tenant channel_account และ persist ให้ถูกต้อง

**Scope of this story:**
1. Inbound: ingest IG DM text events, normalize, persist.
2. Outbound: send IG DM text via Meta API, persist outbound.
3. Threading v1 for IG using external user id and ig account id.
4. Not include media attachments in R1.

**Acceptance Criteria:**
1. **Inbound IG DM normalized and persisted:** Given an Instagram DM inbound text event arrives, when processed, then it is normalized and persisted with correct tenant channel_account mapping.
2. **Outbound IG DM send and timeline persistence:** Given an IG conversation exists, when outbound send is requested, then the system sends via Meta API and persists outbound message linked to the same conversation.
3. **Idempotency prevents duplicates:** Given duplicate webhook deliveries occur, when processed, then only one inbound message is stored.
4. **Connection status reflects permission or token issues:** Given Meta returns permission error or token invalid, when ingest or send fails, then the channel account status is updated to error with error category and recommended remediation.
5. **Threading correctness for primary case:** Given multiple DMs from the same user to the same IG account, when processed, then they are mapped to the same `conversation_id` ensuring a single thread per user per account.

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
