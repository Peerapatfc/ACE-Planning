# Subtask 2: พัฒนาระบบ Outbound Sending (ส่งข้อความออก)

**สถานะ**: TO DO

## รายละเอียด (Description)
พัฒนาความสามารถหลักของระบบให้ผูกกับ Meta API เพื่อยิงข้อความ Text กลับไปตอบลูกค้าบน Facebook Messenger ผ่าน `/me/messages` endpoint โดยตรงอย่างรวดเร็ว

## ขั้นตอนการทำงาน (Implementation Details)
1. **ไฟล์เป้าหมาย**: `apps/omnichat-service/src/channel-accounts/strategies/facebook.strategy.ts`
2. **สถานการณ์ปัจจุบัน**: ฟังก์ชัน `pushMessage` ตอนนี้ยังไม่ได้เขียนโค้ด (throws NotImplementedException) ไว้
3. **สิ่งที่ต้องทำ (Action Required)**: 
   - อินทิเกรตโค้ดเข้าหา Graph API ตรงไปที่ `https://graph.facebook.com/v25.0/me/messages` จัดการพก page access token ไปให้พร้อมเพื่อยืนยันตัวตนว่ากระทำในนาม Channel ใด
   - ยัด payload เพื่อส่งไปหา `recipient.id` และข้อมูลข้อความที่มี
   - เมื่อยิงสำเร็จ ต้องหาวิธีจับค่า `message_id` คืนกลับมาในโครงสร้างตัวแปรของ `PushMessageResult` เพื่อให้ระบบจดจำ delivery tracking ได้บนแดชบอร์ด
