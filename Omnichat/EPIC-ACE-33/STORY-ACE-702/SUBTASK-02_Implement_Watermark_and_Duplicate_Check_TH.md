# Subtask 2: Implement Watermark & Duplicate Check

**สถานะ**: TO DO

## รายละเอียด
สร้างระบบลายนํ้า (Watermark Tracking) เพื่อจดจำเวลา (หรือ Cursor) ล่าสุดที่ดึงข้อมูลสำเร็จของแต่ละ `channel_account` และ `event_type` ช่วยป้องกันไม่ให้โหลดข้อมูลซ้ำ และป้องกันข้อความตกหล่น.

## รายละเอียดการพัฒนา
1. **ไฟล์ที่เกี่ยวข้อง**: 
   - `apps/omnichat-service/src/polling/entities/watermark.entity.ts` (New)
   - `apps/omnichat-service/src/polling/services/watermark.service.ts` (New)
2. **สถานะปัจจุบัน**: ยังไม่มีระบบ Watermark เลย.
3. **สิ่งที่ต้องทำ**: 
   - สร้างตาราง `watermarks` ใน Database (ประกอบด้วย `id`, `tenant_id`, `channel_account_id`, `event_type`, `last_polled_cursor_or_timestamp`)
   - ก่อนที่ Worker จะรันดึง API ต้องไปอ่าน Watermark นี้มาก่อน
   - เวลาดึงข้อมูล ให้ดึงโดยเริ่มจากตังแต่ `[watermark - OVERLAP_BUFFER]` (เช่น ทดเวลาถอยหลัง 5 นาที) เพื่อเก็บตกข้อความที่อาจจะค้างอยู่ระหว่างรอยต่อของช่วงเวลาทำการ Poll รอบที่แล้ว
   - ข้อความที่ติดมาซ้ำในช่วง Overlap ให้ใช้ Message ID ภายนอกในการตัดทิ้ง (De-duplicate)
   - หลังจากดึงและส่งข้อมูลต่อไปที่ Normalizer เรียบร้อย ให้อัปเดต Watermark เป็นเวลาล่าสุดที่ดึงมาได้
