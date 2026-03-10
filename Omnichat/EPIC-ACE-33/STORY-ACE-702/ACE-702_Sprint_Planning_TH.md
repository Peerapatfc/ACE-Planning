# Sprint Planning: ACE-702 - STORY-MKT-02: Scheduled Polling Framework v1

## 📋 ภาพรวมของ Story
**เป้าหมาย:** สร้างระบบ Polling ส่วนกลางที่ทำงานตามเวลาที่กำหนด (Scheduled) เพื่อคอยดึงข้อมูล (ข้อความ, คำสั่งซื้อ) จาก API ของ Marketplace (TikTok, Shopee, Lazada) อัตโนมัติ โดยแยกตาม `channel_account`.
**สิ่งที่ต้องส่งมอบ:** 
- ระบบตั้งเวลา (Scheduler) และ Queue สำหรับรัน Job.
- ระบบลายนํ้า (Watermark) เพื่อจดจำเวลาล่าสุดที่ดึงข้อมูลไปแล้ว ป้องกันการดึงซ้ำ.
- ระบบควบคุม Rate Limit และ Concurrency (จำกัดการทำงานพร้อมกัน).
- ส่งข้อมูลดิบที่ได้เข้าสู่ท่อ Normalization Pipeline (NDP-03).

## 🛠️ สถานะการพัฒนาในปัจจุบัน
จากการวิเคราะห์ Codebase (`/Users/peerapatpongnipakorn/Work/AI-Knowledge/ace`):
- **โครงสร้างพื้นฐานที่ขาดหาย:** ยังไม่มีระบบ Watermark (ตาราง `watermarks`) หรือระบบ Polling อัตโนมัติส่วนกลางใน `omnichat-service` มาก่อน
- **รูปแบบที่ใช้งานอยู่ (Patterns):** ระบบมี Worker แยกต่างหากอยู่บ้างแล้ว (เช่น `omnichat-normalizer-worker`) ซึ่งบ่งบอกว่าสถาปัตยกรรมของระบบรองรับการใช้ Queue (e.g. SQS, BullMQ) ได้ดี
- **สิ่งที่ต้องทำ:** นั่่นหมายความว่าเราต้องสร้าง Framework นี้ขึ้นมาใหม่ทั้งหมด รวมไปถึงการออกแบบ Database Schema สำหรับ Watermark และตั้ง Worker วนรอบ (Cron).

## 📝 การแบ่งย่อย Subtask (Subtask Breakdown)
| ID | ชื่อ Subtask | สถานะ | รายละเอียด |
|---|---|---|---|
| MKT-02.1 | Define Polling Architecture & Queue | TO DO | ติดตั้งระบบ Cron Scheduler, คิวพักงาน, และ Worker สำหรับสั่งให้เกิดการวนไปเรียก API ของแต่ละ `channel_account`. |
| MKT-02.2 | Implement Watermark State Check | TO DO | สร้าง Database Schema และ Logic สำหรับจำเวลาล่าสุด (Watermark) ที่เรียก API สำเร็จ เพื่อป้องกันข้อมูลซ้ำซ้อน. |
| MKT-02.3 | Implement Rate Limiting & Backoff | TO DO | สร้างระบบป้องกันการดึง API ถี่เกินไป และระบบหน่วงเวลา (Exponential backoff) กรณีที่ API ล่มหรือตอบกลับ Error กลับมา. |

## ⚠️ ข้อเสนอแนะ & Edge Cases (สิ่งที่ควรระวัง)
1. **Clock Skew & Watermark Overlap:** ตอนที่จะดึงข้อมูลรอบใหม่ ควรทดเวลาถอยหลังเผื่อไว้เล็กน้อย (เช่น ลบไป 5 นาทีจาก Watermark อันเก่า) เผื่อมีบางข้อความที่เพิ่งเข้าตอนรอยต่อของเวลาดึงรอบที่แล้ว แล้วใช้ `message_id` ในการเช็คไม่ให้เกิด Duplicate ข้อมูลเก่าเอาแทน.
2. **Concurrency Control (การควบคุมให้รันงานเดียว):** ต้องล็อค (Lock) ไว้ว่าใน 1 `channel_account` จะต้องรัน Poll Job ได้แค่ 1 อันในเวลาเดียวกัน ถ้ารอบที่แล้วดึงข้อมูลเยอะและยังไม่เสร็จ รอบใหม่ที่ตั้งเวลาไว้ต้องข้ามไปก่อน หรือรอจนกว่าจะปลดล็อค.
3. **Queue Resilience:** หาก API ของแพลตฟอร์มใด (เช่น Shopee) เกิดล่มหนัก ระบบ Polling ควรเว้นระยะให้แพลตฟอร์มนั้นนานขึ้นแบบเห็นได้ชัด (Massive backoff) เพื่อป้องกันไม่ให้ไปแย่งพื้นที่คิวประมวลผลของ Channel อื่นๆที่ยังปกติอยู่.
