# Subtask 4: ตรวจสอบความถูกต้องของ Webhook Setup

**สถานะ**: เสร็จไปบางส่วน (DONE / IN REVIEW)

## รายละเอียด (Description)
ดำเนินการตรวจสอบโครงสร้างสถาปัตยกรรม (Sanity check) ให้การ์ดรปภ.หน้าบ้านว่าขั้นตอนการทำ Meta Challenge Verification และการเข้ารหัสเซ็นรับ payload ถูกต้อง ปลอดภัย และไม่ปัดข้อความจริงทิ้ง

## ขั้นตอนการตรวจสอบ (Verification Details)
1. **พื้นที่เป้าหมาย**: ไฟล์ `webhook.controller.ts` และ `webhook-validation.service.ts` ใน `omnichat-gateway`
2. **สถานะปัจจุบัน**: ระบบตอบรับคำร้อง `GET /webhooks/facebook` ส่ง `hub.challenge` ไปตอบกลับอย่างงดงาม และมี HMAC `sha256` คอยเช็กความถูกต้องผ่านกระบวนการ `validateFacebookSignature` ครบถ้วนแล้ว
3. **สิ่งที่ต้องทำ (Action Required)**: 
   - ทำ Integration tests ดูว่าถ้ามีการยิง webhook ถี่ๆ มันจะไปปะทะให้คอขวดหรือทำให้ลอจิกเด้ง 403 Forbidden ออกมามั่วไหม
   - ไม่น่าจะต้องมีการเขียนโค้ดเพิ่มเว้นแต่เจอตัวแปรแปลกปลอมมาใหม่
