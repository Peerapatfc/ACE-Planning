# STORY-CTX-02: Identity Model and Merge Rules v1 (Safe Linking Policy + Manual Link)

As a Support Agent
I want clear identity linking rules and a safe manual linking tool
so that I can connect the same customer across channels without accidentally merging different people.

**Definitions**
1. Identity = ตัวตนของลูกค้าในแต่ละช่องทาง เช่น LINE user id, FB, IG user id, marketplace buyer id, Shopify customer id
2. Contact = กลุ่มของ identities ที่ทีมยืนยันว่าเป็น “คนเดียวกัน” ใน tenant เดียว
3. Link = การนำ identity หนึ่งไปผูกอยู่ใต้ contact เดียวกัน (ไม่ลบ conversation เดิม)

ทำ merge rules v1 ที่ต้องเน้น “ถูกต้อง ปลอดภัย ตรวจสอบได้ และแก้ไขได้”
โดยที่
* Auto link ภายใน identity เดียวกันที่ deterministic เช่น same tenant + same channel_account + same external_user_id = same contact (deterministic)
* Same channel account, same external user id
* If tenant_id same AND channel_type same AND channel_account_id same AND external_user_id same
* Then map to the same identity record and the same contact_id
* No cross-channel auto-merge
* LINE กับ FB/IG/Marketplace/Shopify ห้าม auto-link ข้าม channel ใน v1 เสี่ยง false positive สูง
* ให้ agent ทำ manual link เมื่อมีหลักฐาน และต้องมี audit trail + undo

**Candidate suggestion rules**
ระบบสามารถแนะนำ candidate ให้ได้ แต่ต้องมี evidence ที่ชัดเจน
* Show only High and Medium candidates by default
* Low candidates ต้องไปอยู่ “Search results” หรืออยู่ใน “Show more” และมี warning

**Search based linking rules**
ถ้า suggested ไม่เจอ ให้ agent ค้นหา identity ได้โดยกรอกค่า
1. Search keys allowed: Phone, Email, Order id, Channel identity id (LINE user id, PSID, IG id, buyer id), Customer id
2. Search scope: Must be within same tenant only, Results must show shop context for marketplace
3. Result safety: Never show full sensitive value by default

**Scope of this story:**
1. Identity data model v1 for contact identities
2. Auto linking within same channel scope
3. Manual link and unlink identities into a single contact_id
4. Audit trail for link actions
5. Not include ML based suggestions (R2)

**Acceptance Criteria**
1. **Deterministic auto linking within same channel account**
Given messages arrive with the same external_user_id under the same channel_account
When contacts are resolved
Then they map to the same contact_id consistently
2. **Cross channel identities are not auto merged**
Given a customer appears on LINE and Facebook
When identities are created
Then the system keeps them as separate identities until an explicit link exists
3. **Manual link creates a linkage with audit**
Given an agent selects identity A and identity B
When they confirm link with a reason
Then the system links both identities under one contact_id and stores linked_by, linked_at, and reason
4. **Manual unlink is supported and reversible**
Given identities were linked manually
When an authorized user unlinks them
Then the system separates identities according to the previous state and records unlink audit details
5. **Identity masking and copy behavior**
Given identities are displayed
When shown in UI
Then sensitive parts are masked according to masking rules, but copy to clipboard provides full value (if authorized)

**Data**
tenant_id, contact_id, identity_id, linked_by, linked_at, reason, unlinked_by, unlinked_at

**Integrations**
None

**Offer Logic**
None

**Dependencies**
Contact profile panel exists

**Special focus**
* Prevent wrong merge because it becomes privacy incident (confirm dialog)
* Keep workflow simple for pilot

**QA / Test Considerations**
**Primary flows**
* Link LINE identity and marketplace identity then view unified contact panel
* Unlink and verify separation
**Edge Cases**
* Linking identities with incomplete info
* High volume agents linking simultaneously
**Business-Critical Must Not Break**
* Wrong merge can expose data to wrong customer context
**Test Types**
* API tests for link and unlink
* UI tests for confirmation flow
* Security tests cross tenant link attempt
