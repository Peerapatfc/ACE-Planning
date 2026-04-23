# STORY-SET-02: Business Information & Business Hours

**ID:** ACE-1615 | **Status:** To Do | **Points:** 6  
**Assignee:** Tanawin(Toy) | **Sprint:** Sprint 4 (4/13 - 4/26)  
**URL:** https://app.clickup.com/t/86d2hd9ju  
**Depends on:** SET-01, RBAC-01

## User Story

As a Workspace Admin  
I want to configure business information and set working hours for each day of the week  
so that the platform knows when my team is available and can use this data for SLA calculations and work shift defaults.

## Description

หน้า `Settings > Business Information` แบ่งเป็น 2 sections:

### Section 1: Business Information
- Company Logo: upload image, preview, remove
- Organization Name (required)
- Email (editable — contact email ของ workspace ไม่ใช่ login email)
- Phone Number (editable)
- Store ID (read-only + copy to clipboard)
- Timezone (read-only — ตาม workspace timezone)

### Section 2: Business Hours
- Toggle เปิด/ปิดต่อวัน (อาทิตย์–เสาร์)
- Time range: เวลาเริ่ม → เวลาสิ้นสุด (dropdown 30 นาที interval)
- "Copy times to all" = copy เวลาของวันนั้นไปทุกวันที่ active
- Add (+): เพิ่ม shift สองช่วง เช่น 9-12 และ 13-18
- Remove (−): ลบ shift ที่เพิ่มมา

**Business Hours มีผลต่อ:**
- User's work shift toggle "Same as business hours" ใน SET-03
- SLA timer pause นอกเวลา business hours

## Scope

- Business Information form: logo upload, name, email, phone, Store ID (read-only), timezone (read-only)
- Business Hours: per-day toggle + time range + add shift + copy times to all
- Save button → success toast เมื่อบันทึก
- Validation: Organization Name required, time range valid (start < end)
- **ไม่รวม:** SLA-aware business hours, multi-timezone

## Acceptance Criteria

### Admin can update business information and save
- Update Organization Name, Email, Phone → Save → persisted
- Toast: "บันทึกข้อมูลเรียบร้อยแล้ว"

### Admin can upload and remove company logo
- Upload JPG/PNG max 2MB → preview shown immediately → saved to workspace
- Remove → default placeholder shown

### Organization Name is required
- Clear name → Save → error: "กรุณากรอกชื่อ Organization" — no request sent

### Store ID is read-only and copyable
- Field is read-only, cannot be edited
- Click copy icon → copied to clipboard → toast: "คัดลอกแล้ว"

### Admin can toggle business hours per day
- Toggle Sunday off → time range inputs hidden/disabled
- Toggle Monday on → time range inputs appear with defaults

### Admin can set time range per day
- Monday 09:00–18:00 → saved correctly

### Copy times to all
- Monday 09:00–18:00 → "Copy times to all" → all toggled-on days update
- Toggled-off days not affected

### Admin can add second shift (break time)
- Click + on Monday → second time row appears
- Click − → row removed

### Time range validation
- start 18:00, end 09:00 → error: "เวลาเริ่มต้องน้อยกว่าเวลาสิ้นสุด" — no request sent

### Business Hours accessible to other features
- SET-03 "Same as BH" toggle shows same schedule as saved here
- Available via API for SLA integration

## UI/UX Notes

- Business Information: card with form fields, Save button ด้านขวาล่าง
- Logo upload: dashed border placeholder → click → preview
- Store ID: input-like display, lock icon + copy icon
- Timezone: label read-only, no input
- Business Hours: แยก card จาก Business Information
- แต่ละวัน: toggle (ชื่อวัน) + time start dropdown + "to" + time end dropdown + (+) button
- "Copy times to all": ปรากฏบน row แรกที่ active เท่านั้น
- Time dropdown: 30 นาที interval 00:00–23:30

## Technical Notes

**Dependencies:**
- SET-01 Settings shell ต้องมีก่อน
- RBAC-01 เฉพาะ Admin เท่านั้นเข้าหน้านี้ได้
- File upload infrastructure รองรับ S3 or equivalent

**Special focus:**
- Business hours data format: `{ day: "monday", enabled: true, shifts: [{ start: "09:00", end: "18:00" }] }`
- Timezone field อ่านจาก workspace config — ไม่ hard-code ใน frontend
- Business hours API ต้องเป็น GET endpoint ที่ SET-03 เรียกได้
- Logo upload: validate file type + size ที่ client ก่อน upload
- Store ID ต้อง generate ตอนสร้าง workspace และ **immutable** (ไม่เคย regenerate)

## QA / Test Considerations

**Primary flows:**
- Update org name → save → ชื่อใหม่แสดงทันที
- Upload logo → save → logo แสดงใน workspace
- Toggle Monday on → set time → Copy to all → วันอื่น update
- Add second shift → save → persist ถูกต้อง

**Edge Cases:**
- Logo > 2MB → error message ชัดเจน
- Logo ไม่ใช่ JPG/PNG → validation error
- start > end → ไม่ให้ save
- Empty org name → ไม่ให้ save
- Copy to all เมื่อมีวันที่ toggle off → ข้ามวันนั้น
- Shift 2 overlap กับ shift 1 → validate

**Business-Critical Must Not Break:**
- Business hours ต้อง persist ถูกต้อง
- Store ID ต้องไม่แก้ไขได้

**Test Types:**
- API tests: `PATCH /workspace`, `PATCH /workspace/business-hours`
- UI form validation tests
- Image upload tests (valid/invalid type + size)
- Integration: business hours saved → SET-03 reads correctly

## Subtasks

| ID | Name | Points |
|----|------|--------|
| ACE-1627 | Design/Create config db business hours | 1 |
| ACE-1685 | Generate Store ID when Create Tenant | - |
| ACE-1680 | Create business information component | - |
| ACE-1681 | Create business hours component | - |
| ACE-1682 | Build api | - |
| ACE-1683 | Design diagrams | - |
| ACE-1684 | API Table | - |
