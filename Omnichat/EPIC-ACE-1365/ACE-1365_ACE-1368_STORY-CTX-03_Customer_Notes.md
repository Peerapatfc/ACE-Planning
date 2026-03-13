# STORY-CTX-03: Customer Notes (Contact Level) with Pin and Visibility Rules

As a Support Agent
I want to add and view customer notes on the contact profile
so that important context like VIP status or warnings is available across all conversations.

**Detail / Description**
Customer notes ต่างจาก internal notes ใน conversation
1. เป็น note ระดับ contact ใช้ข้ามทุก conversation
2. เห็นได้ทุก agent ใน tenant
3. ต้องมี pin เพื่อให้ note สำคัญอยู่ด้านบน
4. ต้องมี audit ว่าใครเขียนเมื่อไหร่

**Scope of this story:**
1. Create edit delete customer notes on contact
2. Pin and unpin note
3. Show notes in contact panel
4. Mentions optional not required
5. Not include external notifications

**Acceptance Criteria**
1. **Add customer note**
Given an agent is viewing a contact profile
When they add a customer note
Then the note is saved and visible to other agents in the tenant
2. **Edit and delete with audit**
Given a note exists
When the author or authorized role edits or deletes it
Then the system updates or marks deleted and records updated_by and updated_at
3. **Pin behavior**
Given multiple notes exist
When an agent pins a note
Then pinned notes appear at the top consistently across sessions (latest on top)
4. **Tenant isolation**
Given a note belongs to a contact in tenant A
When a user from tenant B attempts to access it
Then access is denied
5. **Notes never leak to customer channels**
Given customer notes exist
When the agent sends an outbound message
Then notes are not included in outbound payloads and are never visible to the customer

**UI/UX Notes**
* Notes section in contact panel with Add note
* Pinned note displayed as highlight card
* Show author and timestamp

**Technical Notes**
**Data**
customer_notes table
tenant_id, contact_id, note_id, content, is_pinned, created_by, updated_by, created_at, updated_at, deleted_at

**Integrations**
None

**Offer Logic**
None

**Dependencies**
1. Contact profile API exists
2. User identity exists for authorship

**Special focus**
* Prevent accidental customer exposure
* Keep notes concise and actionable

**QA / Test Considerations**
**Primary flows**
* Add note pin note and confirm visible across conversations
**Edge Cases**
* Very long notes should be truncated with expand
* Deleted note should not break ordering
**Business-Critical Must Not Break**
* Notes must not leak to customer
**Test Types**
* API tests for CRUD and pin
* UI tests for display and ordering
* Security tests tenant isolation
