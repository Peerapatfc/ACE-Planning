# ACE-41 STORY-NDP-05: Conversation Timeline Query API v1 for Inbox readiness

> **Status:** `BACKLOG` &nbsp; | &nbsp; **Assignees:** Attachai Saorangtoi

## 📝 Description
As a Frontend or Inbox Service
I want conversation and message timeline query APIs
so that the Unified Inbox epic can display message history reliably with pagination and filters.
Detail / Description
Story นี้คือ “Read side API” ที่ Epic A2 Unified Inbox ต้องใช้ในอนาคต โดยต้อง list conversations และ fetch timeline พร้อม pagination ที่เสถียร ไม่ duplicate ไม่ skip แม้จะมี message ใหม่เข้าระหว่างโหลด
ยังไม่รวมงาน assignment SLA tags และ agent workflow
Scope of this story:
List conversations by tenant with filters channel_type and channel_account_id
Fetch messages by conversation with cursor pagination
Include attachment metadata in timeline response
Include conversation summary fields last_message_at and last_message_preview
Exclude assignment SLA tags routing logic

Acceptance Criteria
Stable conversation list ordering and pagination
Given many conversations exist
When listing conversations with page size and cursor
Then results are ordered by last_message_at desc and pagination is stable across pages
Timeline returns chronological messages with attachments
Given a conversation has messages and attachments
When fetching timeline with cursor
Then messages are returned chronologically with attachment metadata included
Pagination consistency under concurrent writes
Given new messages arrive during pagination
When fetching next page using cursor
Then the system does not duplicate or skip messages within the contract and documents expected behavior
Filters by channel work correctly
Given conversations across channels
When filtering by channel_type and channel_account_id
Then only matching conversations are returned
Access control enforces tenant boundaries
Given a conversation belongs to another tenant
When a client requests it
Then access is denied
Performance baseline for pilot readiness
Given pilot volume assumptions
When listing conversations and timelines
Then p95 response time meets agreed staging baseline and queries use correct indexes
UI/UX Notes
Support rendering message bubble types later by including sender_type and display_name
Provide channel badge fields or channel_type for UI
Technical Notes
APIs 
GET conversations
GET conversations/id/timeline
Optional GET contacts lookup for display
Data 
Indexes on tenant_id last_message_at and tenant_id conversation_id created_at
Integrations 
None
Offer Logic 
None
Dependencies 
NDP 02 persistence stable
last_message_at update logic implemented
Special focus 
Cursor pagination contract must be clearly documented
Ensure no cross tenant leakage
QA / Test Considerations
Primary flows
List conversations open one conversation load more and verify ordering
Edge Cases
Conversation with only attachments
Long text with emojis
Messages without preview content
Business-Critical Must Not Break
No cross tenant reads
No duplicate messages in pagination
Test Types
Integration tests for APIs
Load smoke tests for list and timeline

---

## 📋 Custom Fields
| Field | Value |
|---|---|
| Product | Omni |
| Product | ['25200cc8-2645-48fd-a858-654bc6c971df'] |

## 🏗️ Subtasks
| Subtask | Status |
|---|---|
| API : GET conversations | BACKLOG |
| API : GET conversations/id | BACKLOG |
| [QA] | BACKLOG |

## 🔧 Technical Requirements
| Requirement | Needed? |
|---|---|
| Sequence Diagram | ❌ |
| ER Diagram | ❌ |
| API Spec | ✅ |
