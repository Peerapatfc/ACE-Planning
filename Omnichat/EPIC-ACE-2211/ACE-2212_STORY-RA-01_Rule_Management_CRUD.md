# STORY-RA-01: Rule Management (CRUD)

**ClickUp ID:** ACE-2212
**Status:** Backlog
**Points:** 8 SP
**Parent Epic:** ACE-2211
**URL:** https://app.clickup.com/t/86d3115yy

---

## User Story

As an Admin / Supervisor / Agent,
I want to สร้าง แก้ไข ลบ enable/disable Automation Rule ได้จาก UI ตาม permission ของ role,
so that ทีม support จัดการ automation ได้เองโดยไม่ต้องพึ่ง developer และควบคุมได้ว่าใครทำอะไรได้บ้าง.

---

## Detail / Description

- Rule แต่ละตัวประกอบด้วย name (auto-generate จาก action+trigger), trigger conditions, actions, fired count, สถานะ active/inactive, created_by / updated_by + timestamp และ kebab
- Active rules จำกัดสูงสุด **20 rules** ต่อ Workspace; inactive rules ไม่จำกัดจำนวน
- การลบเป็น **hard delete** ถาวร ไม่มี undo เนื่องจากยังไม่มี history implementation; ลบได้เฉพาะ Admin เท่านั้น
- Wizard เริ่มจากการเลือก action ก่อน (action-first) ไม่ใช่ blank form เพื่อลด decision fatigue ของ admin
- Rule name auto-generate จาก action + trigger เช่น `'Auto-reply · Outside hours'` เพื่อลด friction ในการตั้งชื่อ
- มี pills filter หรือ tab แยก all / auto-reply / auto-tag (design ถามอาร์ต)

---

## Scope of This Story

- **Rule list:** ชื่อ rule, trigger summary, action summary, สถานะ active/inactive, fired count, created_by, updated_by + relative time + kebab
- **Active rules counter:** X/20 มีบอก user ด้วย ด้านหลัง เช่น Active (10/20) ส่วนอีกอัน Inactive (1)
- **สร้าง rule:** entry point 'คุณอยากให้ระบบทำอะไร?' → เลือก action → wizard 2 steps → save
- **Edit rule:** เปิด wizard pre-filled; มีผลเฉพาะ conversation ใหม่หลัง save
- **Enable/disable:** toggle ใน list ทันที ไม่มี page reload
- **ลบ rule:** hard delete + confirmation dialog แสดงชื่อ rule และ fired count; Admin เท่านั้น
- **Active section** (max 20) และ **Inactive section** (collapsed by default) แยกกันใน list
- **Permission:** Admin = full CRUD, Supervisor = สร้าง/แก้ไข (ลบไม่ได้), Agent = ดูอย่างเดียว
- created_by / updated_by แสดงบน rule card

### Out of Scope

- Soft delete / audit trail (ยังไม่มี history implementation)
- Drag-and-drop reorder
- Rule duplication
- Export/import rules

---

## Acceptance Criteria

**1. Active rules limit 20 — block เมื่อเต็ม**

Scenario 1
- Given มี active rules อยู่ 18 ตัว
- When Admin ดู list
- Then Counter แสดง 18/20 active rules

Scenario 2
- Given มี active rules อยู่ 20 ตัว
- When Admin กด New Rule
- Then ระบบ block พร้อม message 'ถึง limit 20 active rules กรุณาปิดบาง rule ก่อนสร้างใหม่' ไม่เปิด wizard

**2. Action-first entry point**

- Given Admin กด New Rule
- When dialog/modal ปรากฏ
- Then แสดงคำถาม 'คุณอยากให้ระบบทำอะไร?' พร้อม 2 ตัวเลือก: ส่งข้อความตอบอัตโนมัติ / ติด label ให้การสนทนา — ไม่มี blank form

**3. Auto-generate rule name**

Scenario 1
- Given Admin เลือก action = Auto-reply, trigger = Business hours: outside
- When ถึง review / save
- Then Rule name ถูก generate เป็น 'Auto-reply · Outside hours'; admin แก้ได้ก่อน save

Scenario 2
- Given Admin เลือก action = Add tag, keyword = 'ยกเลิก'
- When ถึง review / save
- Then Rule name generate เป็น 'Tag · ยกเลิก'

**4. Permission per role**

Scenario 1
- Given User role = Agent เปิดหน้า Rules
- When หน้า load
- Then เห็น list อ่านได้ ไม่มีปุ่ม New Rule, Edit, Delete; เห็นว่า rules ไหนเปิดอยู่ ไม่สามารถกดได้

Scenario 2
- Given User role = Supervisor กด kebab menu บน rule
- When menu เปิด
- Then เห็นเฉพาะ Edit ไม่มี Delete

Scenario 3
- Given Supervisor พยายาม call DELETE /rules/{id} โดยตรง
- When API call
- Then 403 Forbidden — permission check ทำงานทั้ง UI และ API

**5. Hard delete ลบถาวรพร้อม confirmation**

Scenario 1
- Given Admin กด Delete บน rule ที่ fired ไปแล้ว 87 ครั้ง
- When dialog ปรากฏ
- Then Dialog แสดง: ชื่อ rule, 'Rule นี้ทำงานไปแล้ว 87 ครั้ง', warning 'จะถูกลบถาวร ไม่สามารถกู้คืนได้' และปุ่ม 'ลบถาวร' / 'Cancel'

Scenario 2
- Given Admin กด 'ลบถาวร'
- When confirm
- Then Rule หายจาก list ทันที ลบออกจาก DB จริง

Scenario 3
- Given Admin กด Cancel
- When dismiss
- Then Rule ยังอยู่ครบ ไม่มีการเปลี่ยนแปลง

**6. Edit rule ไม่กระทบ in-progress conversations**

- Given มี conversation ที่กำลัง open อยู่และ rule match condition
- When Admin แก้ไข rule และ save
- Then Conversation ที่เปิดอยู่ไม่ถูกกระทบ; rule ใหม่มีผลกับ message ที่เข้ามาหลัง save เท่านั้น (ไม่ retroactive)

**7. Inactive section collapse by default**

- Given มี inactive rules อยู่ 3 ตัว
- When Admin เปิดหน้า Rules
- Then Inactive section collapsed แสดงแค่ 'Inactive (3)'; กดขยายเพื่อดูได้

---

## UI/UX Notes

- Entry: ปุ่ม '+ New Rule' เปิด modal ถามก่อนว่า 'อยากให้ระบบทำอะไร?'
- Delete อยู่ใน kebab menu (⋮) เท่านั้น ป้องกัน accidental delete
- Counter '18/20'
- Inactive section collapsed by default; expand ได้
- Rule card แสดง created_by / updated_by + relative time แบบ subtle
- Wizard 2 steps: Step 1 = Trigger conditions, Step 2 = Action detail
- Step indicator บน wizard — step ที่ผ่านแล้ว click กลับได้

---

## QA / Test Considerations

### Primary Flows
- Admin กด New Rule → เลือก action → Step 1 Triggers → Step 2 Action detail → Save → rule ปรากฏใน Active list
- Admin toggle disable → rule ย้ายไป Inactive section ทันที (ไม่เสีย fired count)
- Admin เข้า Edit → แก้ไข conditions → Save → มีผลกับ conversation ถัดไป
- Admin กด Delete → confirm dialog → hard delete → หายจาก list

### Edge Cases
- Network error ขณะ save wizard → ข้อมูลที่กรอกยังอยู่ครบ แสดง retry prompt
- Admin save rule โดยไม่มี condition ใดเลย → Validation error 'ต้องมีอย่างน้อย 1 เงื่อนไข'
- Active rules = 20 → Admin disable 1 ตัว → Active = 19 → สร้างใหม่ได้ทันที
- Rule name ซ้ำกับ rule อื่น → allow แต่แสดง warning tooltip ว่าชื่อซ้ำ
- Supervisor พยายามเข้า URL /rules/{id}/delete โดยตรง → 403 + redirect

### Business-Critical "Must Not Break"
- Rule ที่ disabled ต้องไม่ evaluate conversation ทันทีที่ toggle
- Agent ต้องไม่สามารถสร้าง/แก้/ลบ rule ได้ ไม่ว่าผ่าน UI หรือ API call
- Edit rule ต้องไม่กระทบ conversation ที่ in-progress ไม่ว่ากรณีใด
- Hard delete ต้องลบจาก DB จริง ไม่มี soft flag ใดหลงเหลือ

### Test Types
- Unit: validation (name required, min 1 condition, min 1 action)
- Unit: active rule limit block ที่ 20
- Integration: CRUD API + permission per role
- E2E: full wizard (action-first) → save → ปรากฏใน list
- E2E: disable rule → ไม่ evaluate conversation ใหม่
- E2E: hard delete → confirm → หายจาก DB
- Security: Agent/Supervisor ไม่สามารถ DELETE ผ่าน API โดยตรง
