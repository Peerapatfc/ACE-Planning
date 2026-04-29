# STORY-SET-02: Business Information & Business Hours

**ID:** ACE-1615 | **Status:** In Progress | **Points:** 6 | **Sprint:** Sprint 4 (4/13 - 4/26)  
**Assignee:** Tanawin (Toy) | **URL:** https://app.clickup.com/t/86d2hd9ju  
**Parent:** [ACE-1614 EPIC](ACE-1614-EPIC-Settings-Configuration.md)

## User Story

> As a Workspace Admin  
> I want to configure business information and set working hours for each day of the week  
> so that the platform knows when my team is available and can use this data for SLA calculations and work shift defaults.

## Description

หน้า `Settings > Business Information` แบ่งเป็น 2 sections:

**Section 1: Business Information**
- Company Logo: upload image, preview, remove
- Organization Name (required)
- Email (editable — contact email ของ workspace ไม่ใช่ login email)
- Phone Number (editable)
- Store ID (read-only + copy to clipboard)
- Timezone (read-only display)

**Section 2: Business Hours**
- Toggle เปิด/ปิดต่อวัน (อาทิตย์–เสาร์)
- Time range: เวลาเริ่ม → เวลาสิ้นสุด (dropdown 30 นาที interval)
- "Copy times to all" shortcut = copy เวลาของวันนั้นไปทุกวันที่ active
- Add (+): เพิ่ม shift สองช่วง เช่น 9-12 และ 13-18 (break กลางวัน)
- Remove (−): ลบ shift ที่เพิ่มมา

**Business Hours มีผลต่อ:**
- User's work shift toggle "Same as business hours" ใน SET-03
- SLA timer pause นอกเวลา business hours

## Scope

- Business Information form: logo upload, name, email, phone, Store ID (read-only), timezone (read-only)
- Business Hours: per-day toggle + time range + add shift + copy times to all
- Save button แสดง success toast เมื่อบันทึก
- Validation: Organization Name required, time range valid (start < end)
- ไม่รวม: SLA-aware business hours, multi-timezone

## Acceptance Criteria

**Admin can update business information and save**
- Given: Admin on `Settings > Business Information`
- When: update Organization Name, Email, or Phone → click Save
- Then: changes persisted, success toast "บันทึกข้อมูลเรียบร้อยแล้ว", values reflected immediately

**Admin can upload and remove company logo**
- When: click logo upload area → select JPG/PNG (max 2MB)
- Then: preview shown immediately, saved logo displays in workspace
- When: click Remove logo → logo cleared, default placeholder shown

**Organization Name required**
- When: Admin clears Organization Name → Save
- Then: inline error "กรุณากรอกชื่อ Organization", save request not sent

**Store ID read-only and copyable**
- Then: field is read-only, cannot be edited
- When: click copy icon → Store ID copied to clipboard, toast "คัดลอกแล้ว"

**Admin can toggle business hours per day**
- When: toggle Sunday off → time range inputs hidden/disabled
- When: toggle Monday on → time range inputs appear with default values

**Admin can set time range per day**
- Given: Monday toggled on
- When: select 09:00 start, 18:00 end → Save
- Then: business hours for Monday show 09:00–18:00

**Copy times to all**
- Given: Monday set to 09:00–18:00, other days toggled on
- When: click "Copy times to all" on Monday row
- Then: all other toggled-on days updated to 09:00–18:00, toggled-off days unaffected

**Add second shift (break time)**
- When: click + on Monday row → second time range row appears
- When: click − → that shift row removed

**Time range validation**
- When: start time = 18:00, end time = 09:00 → Save
- Then: validation error "เวลาเริ่มต้องน้อยกว่าเวลาสิ้นสุด", save not sent

**Business Hours data accessible to other features**
- Given: Admin saved business hours
- When: SET-03 Edit User modal loads with "Same as business hours" toggle on
- Then: work shift preview shows same schedule as Business Hours
- And: data available via API for SLA integration

## UI/UX Notes

- Business Information section: card with form fields, Save button ขวาล่าง
- Logo upload: dashed border placeholder → click to select → preview (กลม/square ตาม design)
- Store ID: input-like display มี lock icon + copy icon ด้านขวา
- Timezone: read-only label ไม่มี input
- Business Hours section: แยก card จาก Business Information
- แต่ละวัน: toggle (ชื่อวัน) + time start dropdown + "to" + time end dropdown + + button
- "Copy times to all" ปรากฏบน row แรกที่ active เท่านั้น
- Time dropdown: 30 นาที interval 00:00–23:30
- Save button: sticky ด้านล่าง หรืออยู่ใน section card

## Technical Notes

**Dependencies**
- SET-01: Settings shell ต้องมีก่อน
- RBAC-01: เฉพาะ Admin เข้าหน้านี้ได้
- File upload infrastructure ต้องรองรับ image upload ไปยัง S3 หรือ equivalent

**Special focus**
- Business hours data format: `{ day: "monday", enabled: true, shifts: [{ start: "09:00", end: "18:00" }] }`
- timezone field อ่านจาก workspace config ไม่ hard-code ใน frontend
- Business hours API ต้องเป็น GET endpoint ที่ SET-03 เรียกได้เพื่อ populate "Same as business hours"
- Logo upload: validate file type (JPG, PNG) และ size (max 2MB) ที่ client ก่อน upload
- Store ID ต้อง generate ตอนสร้าง workspace และไม่เคย regenerate (immutable)

## QA / Test Considerations

**Primary flows**
- Update organization name → save → เห็นชื่อใหม่ใน UI ทันที
- Upload logo → save → logo แสดงใน workspace
- Toggle Monday on → set time → Copy to all → วันอื่น update
- Add second shift → save → persist ถูกต้อง

**Edge cases**
- Logo file > 2MB → error message ชัดเจน
- Logo file ไม่ใช่ JPG/PNG → validation error
- Start time > end time → ไม่ให้ save
- Organization Name empty → ไม่ให้ save
- Copy to all เมื่อมีวันที่ toggle off → ข้ามวันนั้น
- Add shift ครั้งที่ 2 แล้ว overlap กับ shift แรก → validate

**Business-critical must not break**
- Business hours ต้องถูก persist อย่างถูกต้อง
- Store ID ต้องไม่แก้ไขได้ — เป็น identifier ที่ใช้ใน external integration

**Test types**
- API tests: `PATCH /workspace` และ `PATCH /workspace/business-hours`
- UI form validation tests
- Image upload tests (valid/invalid file type + size)
- Integration test: business hours saved → SET-03 reads correctly

## Subtasks

| Task | Name | Status |
|------|------|--------|
| [ACE-1627](https://app.clickup.com/t/86d2jh3te) | Design/Create config db business hours | To Do |
| [ACE-1685](https://app.clickup.com/t/86d2qk1zb) | Generate Store ID when Create Tenant | In Progress |
| [ACE-1680](https://app.clickup.com/t/86d2qjy8a) | Create business information component | In Progress |
| [ACE-1681](https://app.clickup.com/t/86d2qjyf2) | Create business hours component | To Do |
| [ACE-1682](https://app.clickup.com/t/86d2qjywe) | Build api | In Progress |
| [ACE-1683](https://app.clickup.com/t/86d2qjzhw) | Design diagrams | In Progress |
| [ACE-1684](https://app.clickup.com/t/86d2qjznb) | API Table | To Do |
