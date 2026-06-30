# STORY-RA-04: Auto-Tag Conversation

**ClickUp ID:** ACE-2215
**Status:** To Do
**Points:** 3 SP
**Assignees:** Tanawin(Toy)
**Parent Epic:** ACE-2211
**URL:** https://app.clickup.com/t/86d311653

---

## User Story

As an Admin / Supervisor,
I want to ให้ rule ติด tag ให้ conversation อัตโนมัติแบบ append-only พร้อม metadata,
so that ลด manual tagging ของ agent และ filter / report มีความถูกต้องสม่ำเสมอ.

---

## Detail / Description

- **Append-only** เสมอ — ไม่ลบ tag เดิม ไม่ duplicate tag ที่มีอยู่แล้ว
- Admin เลือกได้หลาย tag ใน 1 rule และสร้าง tag ใหม่ **inline** ได้โดยไม่ต้องออกจาก wizard
- Tag ที่ rule ติดมี metadata `tagged_by_type = 'rule'` สำหรับแยก KPI — แต่แสดงเหมือน tag ปกติใน conversation view
- Agent ยังสามารถลบ tag ที่ rule ติดได้เหมือน tag ที่ agent ติดเอง
- ถ้า tag ถูกลบออกจาก system หลังจากสร้าง rule: rule skip tag นั้นโดยไม่ crash และ actions อื่นยังทำงาน

---

## Scope of This Story

- **Tag picker:** searchable, multi-select จาก existing tags
- **Create new tag inline:** พิมพ์ชื่อ → Enter หรือกด '+ Create' สร้างใน system และเลือกทันที
- **Append-only:** ไม่ลบ tag เดิม, ไม่ duplicate
- `tagged_by_type = 'rule'` ใน tag metadata (background สำหรับ KPI filter)
- Agent ลบ tag ที่ rule ติดได้เหมือน tag ปกติ
- Tag ที่หายจาก system → skip + log warning ไม่ crash
- Tag ที่ rule ติด: tooltip 'tagged by rule: [ชื่อ]' เมื่อ hover

### Out of Scope

- Auto-untag action
- Remove specific tag action
- Tag-based SLA

---

## Acceptance Criteria

**1. Append-only ไม่ลบ tag เดิม**

- Given Conversation มี tag 'billing' อยู่แล้ว, rule มี 'Add tag: cancellation-risk'
- When rule trigger
- Then Conversation มีทั้ง 'billing' และ 'cancellation-risk'; 'billing' ไม่หาย

**2. Append-only ไม่ duplicate**

- Given Conversation มี tag 'urgent' อยู่แล้ว, rule มี 'Add tag: urgent'
- When rule trigger
- Then Tag 'urgent' ไม่เพิ่มซ้ำ ยังมีแค่อันเดียว

**3. หลาย tag ใน 1 rule**

- Given Admin เลือก 'cancellation-risk' และ 'off-hours' ใน action เดียว
- When rule trigger
- Then ทั้งสอง tag ถูกติดพร้อมกัน

**4. Create inline**

- Given Admin พิมพ์ 'shopee-complaint' ที่ยังไม่มีใน system
- When กด Enter หรือ '+ Create'
- Then Tag 'shopee-complaint' ถูกสร้างใน system และเลือกเข้า action ทันที ไม่ต้องออกจาก wizard

**5. Tag metadata (background)**

Scenario 1
- Given Rule ติด tag 'off-hours'
- When ดู tag metadata ใน conversation
- Then `tag.tagged_by_type = 'rule'` แยกจาก tag ที่ agent ติด (`tagged_by_type = 'human'`)

Scenario 2
- Given KPI report filter 'ไม่รวม auto-tagged'
- When generate report
- Then Tags ที่ `tagged_by_type = 'rule'` ถูก exclude ออกจาก agent tagging metric

**6. Agent ลบ tag ที่ rule ติดได้**

- Given Rule ติด tag 'spam' ให้ conversation
- When Agent คลิก × ลบ tag 'spam'
- Then Tag ถูกลบออก; rule ไม่ re-tag ใน conversation เดิม

**7. Tag ถูกลบจาก system ไม่ crash**

- Given Rule มี 'Add tag: old-tag' แต่ 'old-tag' ถูกลบออกจาก system แล้ว
- When rule trigger
- Then Skip tag นั้น — log: `tag not found: old-tag`; actions อื่นใน rule ยังทำงานปกติ ไม่มี error

**8. Tooltip บน tag ที่ rule ติด**

- Given Rule ติด tag 'off-hours'
- When Agent hover บน tag 'off-hours' ใน conversation
- Then Tooltip แสดง 'tagged by rule: Auto-reply · Outside hours'

---

## UI/UX Notes

- Tag picker: search input + scrollable list + checkbox multi-select
- Tags ที่เลือกแล้ว: chip ใน action card พร้อม × ลบออก หรือกดอีกครั้งเพื่อลบออก
- Option '+ Create tag: [ชื่อที่พิมพ์]' ปรากฏเมื่อ search ไม่เจอ tag
- **Preview:** 'จะติด label เหล่านี้: [chip list]' แสดงก่อน save
- Tooltip บน tag ที่ rule ติดใน conversation: 'tagged by rule: [ชื่อ rule]'

---

## QA / Test Considerations

### Primary Flows
- Admin search tag → select หลาย tag → create tag ใหม่ inline → save
- Rule trigger → check duplicate per tag → append tags ที่ไม่ duplicate → set `tagged_by_type = rule`
- Tag ถูกลบจาก system → skip + log → continue actions อื่น

### Edge Cases
- Tag ชื่อซ้ำ case-insensitive: 'VIP' และ 'vip' ถือเป็น tag เดียวกัน — dedup
- Admin ไม่เลือก tag ใดเลยใน Add tag action → validate error 'เลือกอย่างน้อย 1 label'
- Tag ชื่อยาวเกิน 50 ตัวอักษร → validate error ระหว่าง create inline
- Rule trigger แต่ tag ที่เลือกทุกอันมีอยู่ใน conversation แล้ว → skip ทั้งหมด (ไม่ใช่ error) — log: `all tags already exist`

### Business-Critical "Must Not Break"
- Append-only เสมอ ไม่มีกรณีใดที่ rule จะลบ tag ที่มีอยู่เดิม
- `tagged_by_type = 'rule'` ต้องถูกต้องเสมอสำหรับ tag ที่ rule ติด
- Tag ที่หายจาก system ต้องไม่ทำให้ rule crash หรือหยุด actions อื่น

### Test Types
- Unit: append-only (no delete existing, no duplicate)
- Unit: `tagged_by_type` metadata
- Unit: missing tag graceful skip
- Unit: case-insensitive dedup
- Integration: tag creation API
- Integration: conversation tag update
- E2E: rule trigger → verify tags appear + tooltip 'tagged by rule'
- E2E: agent removes rule-tagged → verify removed
- E2E: tag deleted from system → rule still runs other actions
