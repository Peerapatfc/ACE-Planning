# Subtask 2: พัฒนาระบบ Outbound Sending (ส่งข้อความออก)

**สถานะ**: TO DO

## รายละเอียด (Description)
สร้างไฟล์ `InstagramStrategy` เพื่อให้เซิร์ฟเวอร์สามารถจัดส่งข้อความ Text กลับไปหาระบบ Instagram Direct Message (DM) ของลูกค้าเป้าหมายได้

## ขั้นตอนการทำงาน (Implementation Details)
1. **ไฟล์เป้าหมาย**: สร้างไฟล์ `apps/omnichat-service/src/channel-accounts/strategies/instagram.strategy.ts`
2. **สถานการณ์ปัจจุบัน**: ในโฟลเดอร์เดียวกันนี้มีแค่ของ Facebook และ Line ของฝั่ง Instagram ยังไม่มีเลยแม้แต่น้อย
3. **สิ่งที่ต้องทำ (Action Required)**: 
   - นำคลาสใหม่นี้ไปสืบทอด (implement) หน้าที่จาก `AccountChannelStrategy`
   - เขียนเมธอดให้โยน POST payload วิ่งเข้าสู่ Meta Graph API ขาของ `/me/messages` ขน access token ไปใช้ยืนยันเสร็จสรรพ
   - แกะ `message_id` ที่ Meta ตีกลับมาระบุว่าสำเร็จแล้ว นำกลับมายัดใส่ Object ตอบกลับ (`PushMessageResult`) แบบหล่อๆ ให้แดชบอร์ดรับไปโชว์แจ้งเตือน
