# STORY-CTX-01: Contact Profile (Profile Panel + Key Events + History)

**Acceptance Criteria**
Given the contact has multiple channel identities
When the panel renders
Then it shows each identity with channel badge, masked id

Given assignment status and SLA events exist
When the panel renders
Then it shows a chronological list of key events with author and time for the last 5 events
1. **Recent conversations section works and navigates**
Given the contact has multiple conversations
When the agent clicks a recent conversation item
Then the inbox navigates to that conversation and preserves the current view state predictably
2. **Graceful handling of missing data**
Given some fields are unavailable such as last seen
When the panel renders
Then it shows placeholders and does not break layout

**UI/UX Notes**
* Recommended panel sections order
* Overview -> Identities -> Last Purchase Snapshot -> Customer Notes -> Key Events -> Recent Conversations
* Keep it collapsible to reduce clutter
* Skeleton loading
* key event แสดงเป็น mini activity feed ใน contact panel หรือ conversation header เพื่อให้เห็นว่ามีการอัพเดต event เกิดขึ้น

**Technical Notes**
**APIs**
1. GET contact context
2. returns overview, identities, key_events, recent_conversations, last_purchase_stub, customer_notes
3. GET recent conversations separately if needed as dev design

**Data**
1. key_events derived from conversation activity table or event stream
2. recent conversations derived from conversations table filtered by contact_id

**Integrations**
1. None external

**Offer Logic**
1. None

**Dependencies**
1. Contact and conversation entities exist from A1
2. A2 assignment, status,
3. A2 SLA produce events (hold wait till SLA coming in but prepare field priliminary)

**Special focus**
Keep panel lightweight and fast
