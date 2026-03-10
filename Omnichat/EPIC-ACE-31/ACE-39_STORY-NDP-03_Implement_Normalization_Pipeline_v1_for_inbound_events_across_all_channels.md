# ACE-39 STORY-NDP-03: Implement Normalization Pipeline v1 for inbound events across all channels

> **Status:** `BACKLOG` &nbsp; | &nbsp; **Assignees:** _Unassigned_

## 📝 Description
As a Connector Platform
I want a normalization pipeline that converts inbound channel payloads into normalized schema v1
so that connectors can share one ingestion path and persistence is consistent across channels.
Detail / Description
Story นี้คือ “Normalization layer กลาง” ที่เอา raw event จาก connector ไม่ว่าจะมาจาก webhook หรือ polling แล้วแปลงเป็น object มาตรฐาน จากนั้นเรียก persistence เพื่อ upsert และ insert
Marketplace ใน R1 เราต้องรองรับทั้งหมด คือ chat messages, order reference events และ fetch history results แต่ยังเก็บแบบ reference metadata ก่อน ไม่ทำ OMS เต็ม
Scope of this story:
Define a normalization contract per channel
Implement mapping functions for each channel type
line 
facebook
instagram 
tiktok 
shopee 
lazada
Support minimal event categories for R1
inbound chat message text
inbound chat message with attachment metadata
order reference events for marketplace
fetch history ingestion results
Persist normalized entities using NDP 02 services
Optional raw event store with PII safe rules
Acceptance Criteria
Unified normalization interface and error format
Given any raw inbound event
When normalization is executed
Then it returns a normalized object or a structured validation error using a consistent interface across channels
Social mapping produces consistent normalized messages
Given a LINE Facebook or Instagram inbound text event
When it is normalized
Then output includes tenant_id channel_type channel_account_id external ids conversation mapping inputs direction inbound and text content
Marketplace mapping supports chat order reference and fetch history
Given marketplace sources provide chat messages order references and fetch history results
When each is normalized
Then the system persists normalized messages with metadata indicating event category and includes marketplace_order_id when present
Raw payload storage is linked and PII safe
Given raw event storage is enabled
When an event is processed
Then raw payload is stored linked to normalized message and sensitive fields are redacted per policy
Failures are isolated and recorded without blocking pipeline
Given one event fails normalization
When it is processed
Then a failure record is stored with reason and subsequent events continue processing
Retry does not create duplicates
Given the same raw event is delivered multiple times
When the pipeline processes it
Then NDP 02 idempotency prevents duplicate message records
UI/UX Notes
None
Technical Notes
APIs 
Internal ingestion interface
POST internal ingest event Or consume from queue inbound_events
Data 
Store event_type and source_category in message metadata
Optionally store fetch_batch_id to group imported history for marketplace
Integrations 
Requires connector raw events from webhook endpoints and polling collectors
Offer Logic 
None
Dependencies 
FND 03 webhook endpoints
Polling collectors for marketplace baseline
NDP 01 and NDP 02 ready
Special focus 
Keep mapping minimal and extensible
Do not block A2 by building a complex rules engine here
QA / Test Considerations
Primary flows
Normalize and persist one inbound text message per channel
Normalize and persist order reference event
Normalize and persist fetch history batch with multiple messages
Edge Cases
Missing external_message_id fallback to deterministic hash plus timestamp bucket
Unsupported message types store as unsupported_event with raw reference
Emoji and non UTF text must persist correctly
Business-Critical Must Not Break
Enforce tenant isolation always
Never store secrets in raw payload logs
Test Types
Unit tests per channel mapper with fixtures
Integration tests end to end ingest to DB
Regression fixture suite

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
| Social / Marketplace Adapter | BACKLOG |
| [QA] | BACKLOG |

## 🔧 Technical Requirements
| Requirement | Needed? |
|---|---|
| Sequence Diagram | ❌ |
| ER Diagram | ✅ |
| API Spec | ✅ |
