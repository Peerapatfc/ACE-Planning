# Subtask 2: เพิ่มและอัปเดต Unit Tests

**สถานะ**: TO DO / IN PROGRESS

## รายละเอียด (Description)
เพิ่มและอัปเดตชุดทดสอบ (Unit tests) ในไฟล์ `messages.service.spec.ts` ตรวจสอบกระบวนการ deterministic conversation mapping ให้ครอบคลุมเพื่อระวังโค้ดพังเวลาทำ Refactor ในอนาคต

## ขั้นตอนการทำงาน (Implementation Details)
1. **ไฟล์เป้าหมาย**: `apps/omnichat-service/src/messages/messages.service.spec.ts`
2. **สถานะปัจจุบัน**: ในไฟล์ดังกล่าวมี Block การทำเทสชื่อว่า `fallback_thread_key determinism` เขียนเช็กเบื้องต้นเอาไว้อยู่แล้วว่าถ้าไม่มี `external_thread_id` ฟังก์ชันควรไปเรียก fallback
3. **สิ่งที่ต้องทำ (Action Required)**: 
   - ลองรันคำสั่ง test ก่อนด้วย `pnpm test` หรือคำสั่งรันเฉพาะไฟล์เพื่อดูว่าผ่านไหม
   - เช็กเรื่อง Coverage ดูว่า `PrismaService` ถูก Mock แล้ว assert argument ที่ส่งเข้าหาถูกช่อง fallback ด้วยค่า string Hash เดิมเสมอ (Deterministic)
   - ถ้าในอนาคตเรามีการเขียนดักเคสเพิ่มเติม (เช่น ถ้าเป็นกลุ่ม ให้ใช้ Group ID แทน User ID) จะต้องมาเขียนเทสเคสครอบคลุมดักไว้ด้วย
