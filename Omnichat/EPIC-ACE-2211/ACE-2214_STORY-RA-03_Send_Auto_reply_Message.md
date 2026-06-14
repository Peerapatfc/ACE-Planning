# STORY-RA-03: Send Auto-reply Message

**ClickUp ID:** ACE-2214
**Status:** Backlog
**Points:** 2 SP
**Parent Epic:** ACE-2211
**URL:** https://app.clickup.com/t/86d31162h

---

## User Story

As an Admin / Supervisor,
I want to กำหนด auto-reply message พร้อม template variables, fallback values และ cooldown บังคับ,
so that ลูกค้าได้รับ response ทันที ไม่เกิด message spam และ attribution ใน log ถูกต้องสำหรับ SLA tracking.

---

## Detail / Description

- Auto-reply ส่งข้อความผ่าน **channel เดียวกัน** กับที่ลูกค้าส่งมา (LINE reply to LINE, Shopee reply to Shopee)
- รองรับ template variables: `{{customer_name}}`, `{{channel}}`, `{{current_time}}` พร้อม fallback value ต่อ variable เมื่อค่าไม่มี
- **Cooldown** เป็น required field — ไม่อนุญาตให้ save โดยไม่กำหนด และไม่อนุญาตให้ = 0; แสดงเป็นภาษา plain ว่า 'ส่งได้สูงสุด 1 ครั้ง ต่อ X นาที ต่อการสนทนา'
- เมื่อหลาย rule match พร้อมกัน ส่ง auto-reply เพียงครั้งเดียวจาก rule ที่สร้างก่อน (**oldest first**) — rule อื่นที่มี auto-reply ถูก skip แต่ actions อื่นยังทำงาน
- Auto-reply ไม่เปลี่ยน conversation status — status ยังคงเป็น open จนกว่า agent จะ act on it
- สิ่งที่อยู่ใน background (ไม่ expose ใน UI): `sender_type = 'rule'` ใน message record, ไม่นับเป็น `first_human_response_at` สำหรับ SLA

---

## Scope of This Story

- **Text editor:** multi-line, character count < 2,000, placeholder
- **Template variables:** `{{customer_name}}`, `{{channel}}`, `{{current_time}}` — click to insert
- **Fallback value** per variable: handle default gracefully เมื่อ variable ไม่มีค่า
- **Preview panel:** resolved message ด้วย dummy data real-time
- **Cooldown:** required field, default 5 นาที, แสดงเป็นภาษา plain
- **Only-first-wins:** หลาย rule match → auto-reply จาก rule เก่าสุด rule เดียว
- ไม่ส่งถ้า conversation ถูก resolve (completed) ก่อน action execute
- Retry 3 ครั้ง exponential backoff ถ้า channel API fail (background)
- `sender_type = 'rule'` ใน message record (background) — handle in ui gracefully (บ่งบอกยังไงก็ได้ว่าเป็น rule ตอบ)
- `first_human_response_at` ไม่ถูก set โดย auto-reply (background)

### Out of Scope

- Rich message (image/button/carousel)
- Delay / scheduled send

---

## Acceptance Criteria

**1. ส่งผ่าน channel เดียวกัน**

Scenario 1
- Given Conversation มาจาก Shopee และ rule trigger
- When auto-reply execute
- Then Message ส่งผ่าน Shopee API ไม่ส่งผ่าน channel อื่น

Scenario 2
- Given Conversation มาจาก LINE
- When auto-reply execute
- Then Message ส่งผ่าน LINE API

**2. Template variables resolve**

Scenario 1
- Given Template: 'สวัสดี {{customer_name}} ขอบคุณที่ติดต่อผ่าน {{channel}}'
- When rule trigger กับ customer ชื่อ สมปอง จาก LINE
- Then ลูกค้าได้รับ: 'สวัสดี สมปอง ขอบคุณที่ติดต่อผ่าน LINE'

Scenario 2
- Given Template มี {{customer_name}} แต่ไม่มีชื่อ customer ใน system, fallback = 'คุณลูกค้า'
- When rule trigger
- Then ส่ง 'สวัสดี คุณลูกค้า...' ไม่ส่ง literal '{{customer_name}}'

**3. Cooldown required, ห้ามเป็น 0**

Scenario 1
- Given Admin ไม่ได้กรอก cooldown
- When กด Save
- Then Validation error: 'กรุณากำหนดความถี่ในการส่ง' block save

Scenario 2
- Given Admin กรอก cooldown = 0
- When กด Save
- Then Validation error: 'ต้องมากกว่า 0' block save

Scenario 3
- Given Rule cooldown 30 นาที trigger ไปแล้ว 10 นาทีก่อน ใน conversation เดียวกัน
- When condition match ซ้ำ
- Then ไม่ส่ง auto-reply — log: `skipped: cooldown active (20 min remaining)`

Scenario 4
- Given Rule cooldown 5 นาที ผ่านมา 6 นาทีแล้ว
- When condition match
- Then ส่ง auto-reply ปกติ; cooldown นับใหม่

Scenario 5
- Given Conversation ใหม่ (คนละ conversation) trigger rule เดียวกัน ระหว่าง cooldown ของ conversation แรก
- When trigger
- Then ส่ง auto-reply ปกติ; cooldown นับแยกต่อ conversation ไม่ใช่ global

**4. Only-first-wins เมื่อหลาย rule match**

- Given Rule A (สร้างก่อน) และ Rule B ทั้งคู่มี auto-reply และ match พร้อมกัน
- When execute
- Then ส่ง auto-reply เพียง 1 ครั้งจาก Rule A; Rule B skip auto-reply แต่ tag ของ Rule B ยังถูกติด

**5. ไม่ส่งถ้า conversation resolved แล้ว**

- Given Conversation มี status = completed
- When rule trigger
- Then Skip auto-reply — log: `skipped: conversation already completed`; conversation status ไม่เปลี่ยน

**6. sender_type = rule ใน message record (background)**

Scenario 1
- Given Auto-reply ถูกส่งสำเร็จ
- When ดู message record
- Then `message.sender_type = 'rule'` ไม่ใช่ชื่อ agent; timeline แสดง 'Auto-reply · Rule: [ชื่อ]'

Scenario 2
- Given Auto-reply ถูกส่ง
- When คำนวณ FRT สำหรับ SLA
- Then `first_human_response_at` ไม่ถูก update; FRT นับต่อจนกว่า agent จะ reply จริง

**7. Character limit ต่อ channel**

- Given Admin พิมพ์ข้อความเกิน limit ของ channel เช่น Shopee (2,000 chars)
- When พิมพ์ถึง limit
- Then แสดง warning สีส้มบน character count; block save ถ้าเกิน

**8. Channel API fail retry**

Scenario 1
- Given Channel API return error ครั้งแรก
- When ส่ง auto-reply
- Then Retry อีก 2 ครั้ง (total 3 attempts); ถ้าสำเร็จใน attempt ที่ 2 หรือ 3 ถือว่า executed ปกติ

Scenario 2
- Given Channel API fail ครบ 3 attempts
- When retry หมด
- Then Log error: `auto-reply delivery failed`; conversation ไม่ถูกกระทบ; actions อื่นยังทำงาน

---

## UI/UX Notes

- **Variable toolbar:** ปุ่ม `{{customer_name}}` `{{channel}}` `{{current_time}}` — คลิกแทรกที่ cursor
- **Preview panel:** resolved real-time ด้วย dummy data (ชื่อ: สมปอง, channel: Shopee, เวลา: 20:45)
- **Cooldown:** 'ส่งได้สูงสุด 1 ครั้ง ต่อ [5] [นาที/ชั่วโมง] ต่อการสนทนา' — required, asterisk
- Character count สีแดงเมื่อเกิน limit
- **Timeline:** message แสดง badge 'Auto-reply · Rule: [ชื่อ]' ไม่แสดงชื่อ agent
- **Info box:** 'Auto-reply ไม่นับเป็น First Response Time ของ agent'

---

## QA / Test Considerations

### Primary Flows
- Admin กรอก message → แทรก variable → กำหนด fallback → กำหนด cooldown → preview → save
- Rule trigger → resolve variables → check cooldown → check conversation status → send → log `sender_type = rule`
- Only-first-wins: Rule A send → Rule B skip auto-reply → Rule B tag ยังทำงาน

### Edge Cases
- Message ว่าง → validation error 'กรุณากรอกข้อความ' block save
- Variable syntax ผิด เช่น `{{customer name}}` มีช่องว่าง → highlight error ใน editor
- Cooldown = 0 → validation error block save
- Conversation resolved (completed) ก่อน rule execute → skip ไม่ error
- ส่งผ่าน channel ที่ไม่รองรับ plain text (เช่น channel ใหม่) → log error + skip

### Business-Critical "Must Not Break"
- `sender_type` ต้องเป็น `'rule'` เสมอ ห้ามเป็นชื่อ agent ไม่ว่ากรณีใด
- `first_human_response_at` ต้องไม่ถูก set โดย auto-reply
- Cooldown ต้องทำงาน per-conversation-per-rule ไม่ใช่ global
- Only-first-wins ต้องแม่นยำ ส่งครั้งเดียวเสมอแม้มีหลาย rule match

### Test Types
- Unit: variable resolver + fallback logic
- Unit: cooldown timer per-conversation-per-rule
- Unit: only-first-wins logic
- Unit: `sender_type = rule` ใน message record
- Unit: `first_human_response_at` ไม่ถูก update
- Unit: character limit validation per channel
- Integration: message delivery API per channel
- E2E: trigger → verify timeline label 'Auto-reply · Rule: [name]'
- E2E: 2 rules match → verify single auto-reply sent
- E2E: cooldown active → verify skip + log
