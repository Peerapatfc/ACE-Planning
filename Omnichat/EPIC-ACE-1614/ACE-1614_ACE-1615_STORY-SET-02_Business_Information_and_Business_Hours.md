# STORY-SET-02: Business Information & Business Hours

**Status:** Backlog

**Depends On:** SET-01

## User Story

As a Workspace Admin
I want to configure business information and set working hours for each day of the week
so that the platform knows when my team is available and can use this data for SLA calculations and work shift defaults.

## Detail / Description

หน้า Settings > Business Information แบ่งเป็น 2 sections:

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
- "Copy times to all" = copy เวลาของวันนั้นไปทุกวันที่ active
- Add (+) สำหรับเพิ่ม shift สองช่วง เช่น 9-12 และ 13-18
- Remove (−) สำหรับลบ shift ที่เพิ่มมา

**Business Hours มีผลต่อ:**
- User's work shift toggle "Same as business hours" ใน SET-03
- SLA timer pause นอกเวลา business hours

## Scope of this story

- Business Information form: logo upload, name, email, phone, Store ID (read-only), timezone (read-only)
- Business Hours: per-day toggle + time range + add shift + copy times to all
- Save button แสดง success toast เมื่อบันทึก
- Validation: Organization Name required, time range valid (start < end)
- ไม่รวม: SLA-aware business hours, multi-timezone

## Acceptance Criteria

### Admin can update business information and save successfully
- When they update Organization Name, Email, or Phone Number and click Save
- Then changes are persisted and success toast "บันทึกข้อมูลเรียบร้อยแล้ว" appears

### Admin can upload and remove company logo
- Upload: JPG/PNG, max 2MB → preview shown immediately → saved on click Save
- Remove: logo cleared, default placeholder shown

### Organization Name is required and validated
- Clearing Organization Name and clicking Save → inline error "กรุณากรอกชื่อ Organization"
- Save request is not sent to the server

### Store ID is read-only and copyable
- Field is read-only and cannot be edited
- Click copy icon → copied to clipboard + toast "คัดลอกแล้ว"

### Admin can toggle business hours per day
- Toggle Sunday off → time range inputs hidden/disabled
- Toggle Monday on → time range inputs appear with default values

### Admin can set time range per day
- Select 09:00 start and 18:00 end → saved correctly

### Copy times to all applies current day time to all active days
- Monday 09:00–18:00 + click "Copy times to all" → all toggled-on days updated
- Days that are toggled off are not affected

### Admin can add a second shift for a day (break time)
- Click + → second time range row appears
- Click − → that shift row is removed

### Time range validation prevents invalid ranges
- Start 18:00, End 09:00 → validation error "เวลาเริ่มต้องน้อยกว่าเวลาสิ้นสุด"

### Business Hours data is accessible to other features
- SET-03 "Same as business hours" toggle reads from this data
- Data available via API for future SLA integration

## UI/UX Notes

- Business Information section: card with form fields, Save button ด้านขวาล่าง
- Logo upload: dashed border placeholder → click to select → preview
- Store ID: input-like display มี lock icon + copy icon ด้านขวา
- Timezone: label read-only ไม่มี input
- Business Hours: แยก card จาก Business Information
- แต่ละวัน: toggle (ชื่อวัน) + time start dropdown + "to" + time end dropdown + + button
- "Copy times to all" ปรากฏบน row แรกที่ active เท่านั้น
- Time dropdown: 30 นาที interval ตั้งแต่ 00:00 ถึง 23:30

## Technical Notes

**Dependencies:**
- SET-01 Settings shell ต้องมีก่อน
- RBAC-01 เฉพาะ Admin เท่านั้นเข้าหน้านี้ได้
- File upload infrastructure ต้องรองรับ image upload ไปยัง S3 หรือ equivalent

**Special focus:**
- Business hours data format: `{ day: "monday", enabled: true, shifts: [{ start: "09:00", end: "18:00" }] }`
- timezone field อ่านจาก workspace config ไม่ hard-code ใน frontend
- Business hours API ต้องเป็น GET endpoint ที่ SET-03 เรียกได้
- Logo upload: validate file type และ size ที่ client ก่อน upload
- Store ID ต้อง generate ตอนสร้าง workspace และไม่เคย regenerate (immutable)

## QA / Test Considerations

**Primary flows:**
- Update organization name → save → เห็นชื่อใหม่ใน UI ทันที
- Upload logo → save → logo แสดงใน workspace
- Toggle Monday on → set time → Copy to all → วันอื่น update
- Add second shift → save → persist ถูกต้อง

**Edge Cases:**
- Logo file > 2MB → error message ชัดเจน
- Logo file ไม่ใช่ JPG/PNG → validation error
- Start time > end time → ไม่ให้ save
- Organization Name empty → ไม่ให้ save
- Copy to all เมื่อมีวันที่ toggle off → ข้ามวันนั้น
- Add shift ครั้งที่ 2 แล้ว overlap กับ shift แรก → validate

**Business-Critical Must Not Break:**
- Business hours ต้องถูก persist อย่างถูกต้อง
- Store ID ต้องไม่แก้ไขได้

**Test Types:**
- API tests สำหรับ `PATCH /workspace` และ `PATCH /workspace/business-hours`
- UI form validation tests
- Image upload tests (valid/invalid file type + size)
- Integration test: business hours saved → SET-03 reads correctly
