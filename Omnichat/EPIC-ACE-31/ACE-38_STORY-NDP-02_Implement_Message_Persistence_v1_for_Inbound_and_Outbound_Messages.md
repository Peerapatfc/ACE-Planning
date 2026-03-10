# ACE-38 STORY-NDP-02: Implement Message Persistence v1 for Inbound and Outbound Messages

> **Status:** `BACKLOG` &nbsp; | &nbsp; **Assignees:** _Unassigned_

## 📝 Description
As a Backend Service
I want a persistence layer to store and retrieve normalized conversations and messages
so that downstream services can build Unified Inbox and audit message history reliably.
Detail / Description
ทำ “Persistence layer” ให้ใช้งานได้จริง คือรับ normalized object แล้ว persist ลง DB แบบถูกต้อง มีการ upsert contact และ conversation อย่าง deterministic และ insert message แบบ idempotent เพื่อกัน duplicate จาก webhook retry
ต้องรองรับทั้ง inbound และ outbound เพื่อให้ timeline ใน inbox ต่อเนื่อง ไม่ขาดตอน
Scope of this story:
Implement repositories services for
upsert contact
upsert conversation
insert message with idempotency
insert attachment metadata
Query functions ที่ inbox จะใช้
list conversations by tenant and channel
list messages by conversation with pagination
Persist outbound messages to keep timeline consistent
Does not implement connectors and UI
Acceptance Criteria
Idempotent message insert prevents duplicates
Given an inbound event with a stable idempotency key
When the system processes the same event twice
Then only one message record exists and the second attempt returns the existing message_id
Contact upsert is deterministic per tenant and channel
Given an external_user_id from a channel
When the system upserts a contact multiple times
Then the same contact_id is returned for that tenant and channel scope
Conversation mapping is stable for social threads
Given a channel thread id or equivalent identifier
When multiple messages arrive for the same thread
Then they map to the same conversation_id consistently
Outbound messages are persisted and linked correctly
Given an outbound send operation succeeds
When persistence is called
Then a message is stored with direction outbound and linked to the correct conversation_id and channel_account_id
Timeline query supports ordering and cursor pagination
Given a conversation with many messages
When requesting messages with page size and cursor
Then messages are returned in chronological order with stable pagination contract
Validation rejects malformed normalized objects safely
Given a malformed normalized message missing required fields
When persistence is attempted
Then the system returns a validation error and no partial corrupted records are written
UI/UX Notes
None แต่ timeline response ควรรองรับ render ได้ง่าย เช่น include sender type user or agent and display name
Technical Notes
APIs 
Internal service functions are acceptable
Data 
Store created_at and channel_timestamp separately
Store content_text and content_struct metadata for marketplace references
Integrations 
None
Offer Logic 
None
Dependencies 
NDP 01 schema migrations complete
Idempotency key strategy agreed
Special focus 
Query performance for timeline and conversation list
Strict tenant filtering on every repository method
QA / Test Considerations
Primary flows
Persist inbound message then read timeline
Persist outbound message then verify timeline continuity
Upsert contact and conversation then verify ids stable
Edge Cases
Out of order events arriving late
Missing thread id fallback rule v1 such as external_user_id plus channel_account_id plus time bucket
Same external_message_id across different accounts must be scoped by tenant and channel_account
Business-Critical Must Not Break
No cross tenant leakage
No duplicate messages on retries
Test Types
Integration tests with DB
Load smoke test for timeline queries

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
| Conversation / Message / Attachment Module | BACKLOG |
| Contact Module | BACKLOG |

## 🔧 Technical Requirements
| Requirement | Needed? |
|---|---|
| Sequence Diagram | ❌ |
| ER Diagram | ✅ |
| API Spec | ✅ |
