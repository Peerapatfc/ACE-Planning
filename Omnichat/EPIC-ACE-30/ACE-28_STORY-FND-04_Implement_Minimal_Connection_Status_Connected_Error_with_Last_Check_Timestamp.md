# ACE-28 STORY-FND-04: Implement Minimal Connection Status Connected Error with Last Check Timestamp

> **Status:** `BACKLOG` &nbsp; | &nbsp; **Assignees:** _Unassigned_

## 📝 Description
As a Support Operator
I want a minimal connection status per channel account
so that we can quickly detect broken connections and guide recovery during pilot.
Detail / Description
ต้องมีสถานะการเชื่อมต่อของแต่ละ channel account อย่างน้อย connected หรือ error พร้อมเวลา last checked และ error summary เพื่อให้ทีมรู้ว่าช่องทางไหนมีปัญหา และใช้ประกอบ runbook และการแก้ปัญหา
Scope of this story:
สถานะ connected, error
last checked timestamp
last error summary and error code category
endpoint สำหรับอ่านสถานะและอัปเดตสถานะจาก connector
ไม่รวม dashboard analytics หรือ advanced monitoring
Acceptance Criteria
Status is updated by connector health check
Given a channel account is connected
When the connector performs a health check or detects failure
Then the status and last checked are updated accordingly
Status is visible to admin and support
Given multiple channel accounts exist
When an admin requests connection status
Then the system returns status, last checked, and last error summary for each account
Error does not expose sensitive data
Given an error occurs during connection or ingestion
When the error summary is stored and displayed
Then it contains no secrets and no raw tokens
UI/UX Notes
UI แสดง badge connected or error และ last checked
ถ้า error ให้แสดง recommended action เช่น reconnect or check webhook
Technical Notes
กำหนด error categories ให้เป็นมาตรฐาน เช่น auth_error, webhook_error, rate_limit, unknown
Connector ต้องเขียน status update ทุกครั้งที่เกิด failure สำคัญ
APIs 
GET connection status list by tenant
PATCH status update by connector service
Data 
status fields on channel_account or separate channel_connection table
Integrations 
None
Offer Logic 
None
Dependencies 
ChannelAccount model from FND 01
Basic webhook or health check signals from FND 03
Special focus 
Keep it minimal but useful, do not build a full monitoring product here
QA / Test Considerations
Primary flows
Simulate success and failure, verify status transitions and timestamps
Edge Cases
Flapping statuses from intermittent errors (สถานะไม่เถียร ติดๆดับๆ)
Out of order updates from multiple workers
Business-Critical Must Not Break
Status must reflect reality enough to support pilot operations
Test Types
Unit tests for status state machine
Integration tests for status API responses

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
| Create Connector Service | BACKLOG |
| Unit test | BACKLOG |
| [QA] | BACKLOG |

## 🔧 Technical Requirements
| Requirement | Needed? |
|---|---|
| Sequence Diagram | ❌ |
| ER Diagram | ❌ |
| API Spec | ✅ |
