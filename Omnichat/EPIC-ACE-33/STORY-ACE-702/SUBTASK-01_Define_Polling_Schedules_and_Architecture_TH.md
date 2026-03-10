# Subtask 1: Define Polling Schedules & Architecture

**สถานะ**: TO DO

## รายละเอียด
สร้างโครงสร้างพื้นฐานสำหรับระบบ Polling: ประกอบด้วยตัว Scheduler (ตั้งเวลา) ที่จะส่ง Job ไปรอในคิว (เช่น SQS, BullMQ) และกลุ่ม Worker คอยหยิบงานตาม `channel_account` ไปดึงข้อมูลจาก API

## รายละเอียดการพัฒนา
1. **ไฟล์ที่เกี่ยวข้อง**: 
   - `apps/omnichat-service/src/polling/` (สร้าง Module ใหม่)
   - `infrastructure/` (กำหนด Queue)
2. **สถานะปัจจุบัน**: ระบบยังไม่มี Worker ดึงข้อมูลแบบตั้งเวลา (Scheduled Polling Worker) ตรงกลาง สำหรับ `channel_accounts`.
3. **สิ่งที่ต้องทำ**: 
   - สร้าง Cron Job (เช่น ใช้ `@nestjs/schedule`) คอยตื่นมาเช็คตาราง `channel_accounts` เลือกเฉพาะ Channel ที่ต้องพึ่ง Polling (TikTok, Shopee, Lazada) และสถานะ ACTIVE 
   - ยิงคำสั่ง `PollJob` ของแต่ละ Account เข้าไปรอใน Message Broker (คิว)
   - สร้าง Worker Service อีกฝั่งคอยรอรับงาน `PollJob` ไปประมวลผล
   - บังคับใช้ Concurrency Control (อาจใช้ Redis Lock หรือ FIFO Queue) เพื่อให้มั่นใจว่า 1 `channel_account` จะโดนดึงแค่ 1 Job ใน 1 ช่วงเวลาเท่านั้น ห้ามทำงานทับซ้อนกัน
