# ACE-29 STORY-FND-05: Implement Basic Admin Connect Flow Wireframe and UI Mock

> **Status:** `BACKLOG` &nbsp; | &nbsp; **Assignees:** Tanawin(Toy), Siraphob Reanmanorom

## 📝 Description
As a Tenant Admin
I want a basic connect channel flow design and UI mock
so that engineers can implement connection setup consistently and reduce rework later.
Detail / Description
ยังไม่ต้อง implement UI จริงเต็มระบบ แต่ต้องมี wireframe และ UI mock ที่ทีม dev และ PO เห็นตรงกันว่า connect flow เป็นอย่างไร หน้าไหนแสดงอะไร และข้อมูลใดมาจาก API ใด เพื่อไม่ให้การทำงานต่อช่องทางกลายเป็นงาน ad hoc
Scope of this story:
Wireframe หน้ารายการช่องทางที่เชื่อมแล้ว
Wireframe หน้าทำ connect per channel พร้อมสถานะและขั้นตอน
UI mock สำหรับ status connected or error และ last checked
ระบุ field ที่ต้องใช้จาก backend
ไม่รวม front end implementation จริง
Acceptance Criteria
Wireframe covers required flows
Given the 6 channels in scope
When the UX delivers wireframes
Then the wireframes include list view, connect flow, disconnect or reconnect actions, and status display
UI mock maps to backend fields
Given the ChannelAccount and status model
When the UX delivers the UI spec
Then each UI element is mapped to a backend field or API response
Review and sign off
Given wireframe and mock are ready
When PO PM Dev QA review
Then feedback is incorporated and the spec is approved for implementation
UI/UX Notes
ใช้ layout แบบ simple admin console
มี section แยก Social vs Marketplace เพื่อสื่อว่า Marketplace baseline ใน R1
มี message ชัดเจนเรื่อง known limitations
Technical Notes
ระบุ API contract ที่ frontend ต้องเรียก เช่น list accounts, status, connect initiation, callback
ถ้าช่องทางต้อง OAuth ให้ระบุ redirect and callback behavior อย่างชัดเจน
APIs 
Draft API contract list endpoints and payload shapes
Data 
UI consumes ChannelAccount list and connection status fields
Integrations 
Connect flow varies by platform, spec ต้องระบุ per channel
Offer Logic 
None
Dependencies 
ต้องมี schema และ status fields จาก FND 01 and FND 04
Special focus 
Keep scope minimal to support delivery speed in A1
QA / Test Considerations
Primary flows
None required since this is design spec, but QA should review for testability
Edge Cases
Multiple accounts per channel display and selection
Partial connect states
Business-Critical Must Not Break
Connect flow must not imply features that are out of scope for R1
Test Types
Design review checklist
Spec validation against backend contracts

---

## 📋 Custom Fields
| Field | Value |
|---|---|
| Product | Omni |
| Product | ['25200cc8-2645-48fd-a858-654bc6c971df'] |

## 🏗️ Subtasks
| Subtask | Status |
|---|---|
| Tenant Management | BACKLOG |
| Web hook log | BACKLOG |
| [QA] | BACKLOG |

## 🔧 Technical Requirements
| Requirement | Needed? |
|---|---|
| Sequence Diagram | ❌ |
| ER Diagram | ✅ |
| API Spec | ✅ |
