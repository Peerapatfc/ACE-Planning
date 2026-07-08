# STORY-BC-03: Send Broadcast

**Status:** To Do | **ClickUp:** [ACE-2457](https://app.clickup.com/t/86d3bfjck) | **Epic:** [ACE-2236](https://app.clickup.com/t/86d318wjb)

## User Story

**AS** a user
**I WANT TO** ส่ง broadcast พร้อม confirmation dialog และ real-time progress tracking
**SO THAT** ฉันสามารถติดตามการส่งและจัดการ quota overage ตามประเภท plan

## Description

ระบบให้ส่ง broadcast แบบ batch (500 contacts/batch) ด้วย parallel processing (max 3 batches พร้อมกัน) และแสดง confirmation dialog ก่อนส่ง

**Features:**
- Dialog ยืนยันก่อนส่ง
- ตรวจสอบ quota ก่อนส่ง (Free/Basic block, Pro อนุญาต overage)
- Toast message ถ้าส่งไม่ผ่าน (Free/Basic plan)
- Batch processing (500 contacts/batch, max 3 concurrent)
- หลังส่งเสร็จ → auto-redirect ไปหน้า broadcast list

## Acceptance Criteria

### AC1: Dialog ยืนยันก่อนส่ง
**GIVEN** Admin กด "Send"
**WHEN** dialog ปรากฏ
**THEN** แสดง:
- ข้อความ: "คุณต้องการส่ง broadcast นี้ใช่หรือไม่"
- ปุ่ม: [ยกเลิก] [ส่ง]

**WHEN** Admin กด [ส่ง] → ดำเนินการส่ง แล้วปิด dialog AND redirect ไปหน้า Broadcast List ทันที AND broadcast แสดง status = "กำลังส่ง"
**WHEN** Admin กด [ยกเลิก] → ยกเลิกการส่ง แล้วกลับไปที่ form

Status อัปเดตอัตโนมัติเมื่อส่งเสร็จ (Sent / Sent with error / Error)

### AC2: Required field validation on proceed
**GIVEN** Admin clicks to Send AND broadcast is incomplete
**THEN** system validates ALL required fields:
- **LINE OA selected?** If NO → dropdown RED, error: "กรุณาเลือก LINE OA"
- **Broadcast name filled?** If NO → name field RED, error: "กรุณาใส่ชื่อ Broadcast"
- **At least 1 message exists?** If NO → error: "กรุณาเพิ่มข้อความอย่างน้อย 1 ข้อความ", highlights empty state area RED
- **Each message has content?** Text empty → RED, "กรุณากรอกข้อความ" | Image not uploaded → RED, "กรุณาอัปโหลดรูปภาพ"
- **If scheduled, valid date/time?** If past → error: "โปรดกำหนดวันเวลาบรอดแคสต์ให้เป็นวันเวลาในอนาคต"

AND scrolls to first error

### AC3: Quota check ก่อนส่ง
**GIVEN** Admin กด [ส่ง] และ redirect มาหน้า Broadcast List แล้ว
**WHEN** ระบบตรวจสอบ quota (background) AND plan = Free/Basic AND quota ไม่พอ
**THEN** broadcast status เปลี่ยนเป็น "Error" พร้อม reason `quota_exceeded`

### AC4: Recipients แบ่งเป็น batch 500
**GIVEN** broadcast มี 3200 target recipients
**WHEN** ระบบเริ่มส่ง
**THEN** แบ่งเป็น: Batch 1-6 (500 each) + Batch 7 (200)

### AC5: Parallel processing max 3 batches
**GIVEN** มี 7 batches ที่ต้องส่ง
**WHEN** ระบบเริ่ม process
**THEN** ส่ง batches 1, 2, 3 พร้อมกัน
- เมื่อ batch 1 เสร็จ → เริ่ม batch 4
- เมื่อ batch 2 เสร็จ → เริ่ม batch 5
- เมื่อ batch 3 เสร็จ → เริ่ม batch 6
- ไม่เกิน 3 batches พร้อมกัน

### AC6: Track failed recipients
**GIVEN** batch processing
**WHEN** LINE API คืน error สำหรับ recipient
**THEN** บันทึก failure พร้อมเหตุผล:
- `user_blocked` - User บล็อก bot
- `user_not_found` - User ID ไม่พบ
- `invalid_message` - ข้อความรูปแบบผิด
- `rate_limited` - API rate limit
- `server_error` - LINE server error

AND ดำเนินการต่อ recipients ที่เหลือใน batch (ไม่หยุด broadcast)

### AC7: Quota หมดขณะส่ง (Race condition)
**GIVEN** Admin A ส่ง 5000 contacts AND quota = 6000 ตอนเริ่ม
**WHEN** Admin B ส่ง 4000 messages พร้อมกัน AND quota เปลี่ยนเป็น 2000
**THEN** ระบบหยุดส่ง batch ที่เหลือทันที AND mark recipients ที่ยังไม่ได้รับเป็น `failed` (reason: `quota_exceeded`) AND ดำเนินการตาม AC8

### AC8: Broadcast completion status
**GIVEN** ครบทุก batch (skip หรือ success)
**WHEN** ระบบจบการส่ง
**THEN** ตรวจสอบ:

| Case | Condition | Toast | Status |
|---|---|---|---|
| ส่งสำเร็จทั้งหมด | sent_count > 0 AND failed_count = 0 | "Broadcast id: {id} send successfully" | Sent |
| ส่งสำเร็จบางส่วน | sent_count > 0 AND failed_count > 0 | "Broadcast id: {id} sent with failures" | Sent with error |
| ส่งไม่สำเร็จเลย | sent_count = 0 AND failed_count > 0 | "Broadcast id: {id} send failed" | Error |

**Toast delivery rule:**
- Toast แสดงเฉพาะ user ที่กด Send เท่านั้น
- แสดงไม่ว่า user จะอยู่หน้าไหนในระบบก็ตาม (global toast)
- ถ้า user ออกจากระบบไปแล้วก่อนส่งเสร็จ → ไม่แสดง toast

### AC9: Error handling per batch
**GIVEN** batch processing
**WHEN** batch ล้มเหลว (network error, timeout)
**THEN** retry batch 3 ครั้ง:
- Attempt 1: ทันที
- Attempt 2: หลัง 2 วินาที
- Attempt 3: หลัง 4 วินาที
- ถ้า attempt 3 ยังไม่สำเร็จ → skip batch AND ข้ามไปที่ batch ถัดไป

### AC10: Rate limit handling per recipient (429)
**GIVEN** batch กำลัง process recipients
**WHEN** LINE API คืน `429 Too Many Requests` สำหรับ recipient รายบุคคล
**THEN** retry recipient นั้น 3 ครั้ง:
- Attempt 1: หลัง 1 วินาที
- Attempt 2: หลัง 2 วินาที
- Attempt 3: หลัง 4 วินาที

AND ถ้า attempt 3 ยังได้ 429 → skip recipient AND บันทึก failure reason: `rate_limited`
