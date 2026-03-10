# ACE-693 STORY-SOC-05: Meta Connector v1 Facebook Messenger Inbound and Outbound Text

> **Status:** `TO DO` &nbsp; | &nbsp; **Assignees:** `Unassigned`

## 📝 Description
As a Connector Service, I want to receive and send Facebook Messenger text messages and persist them in normalized schema so that Facebook conversations can be used in pilot as GA light.

**Detail / Description:**
Story นี้ทำ end to end สำหรับ Facebook Messenger ทั้งรับและส่งข้อความ text โดยใช้ webhook events จาก Meta และส่งออกด้วย API ต้องทำ mapping ได้อย่างถูกต้องและต้องจัดการ error category เช่น permission issue, token invalid

**Scope of this story:**
1. Inbound: consume webhook events and normalize to schema v1 and persist.
2. Outbound: send text message via Meta API and persist outbound record.
3. Basic threading v1 for Facebook using external user id and page id.
4. Not include attachments and not include advanced features like reactions.

**Acceptance Criteria:**
1. **Meta webhook challenge verification remains valid:** Given Meta performs webhook verification, when our endpoint is called, then verification succeeds and events are delivered.
2. **Inbound text message normalized and persisted:** Given a Facebook inbound text event arrives, when processed, then it is normalized into schema v1 and persisted with correct tenant and channel_account mapping.
3. **Outbound text send and persistence:** Given a conversation exists for Facebook channel, when an outbound send is requested, then the system sends via Meta API and persists an outbound message linked to the conversation.
4. **Idempotency for inbound webhook retries:** Given Meta retries a webhook delivery, when the same event arrives twice, then only one inbound message is stored.
5. **Error handling and status update:** Given Meta returns token invalid or permission error, when sending fails, then the error is categorized as `auth_error` and the channel connection status may be updated for observability.

---

## 📋 Custom Fields
| Field | Value |
|---|---|
| Product | Omni |

## 🏗️ Subtasks
| Subtask | Status |
|---|---|
| Task1 (ACE-707) | TO DO |

## 🔧 Technical Requirements
| Requirement | Needed? |
|---|---|
| Sequence Diagram | ❌ |
| ER Diagram | ✅ |
| API Spec | ✅ |
