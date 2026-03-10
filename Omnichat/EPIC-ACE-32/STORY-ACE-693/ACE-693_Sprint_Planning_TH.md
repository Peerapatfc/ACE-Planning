# การวางแผนสปริ้นต์ (Sprint Planning): ACE-693 Meta Connector v1 Facebook Messenger Inbound and Outbound Text

## 1. การแบ่งงาน (Subtask Breakdown) และสถานะปัจจุบัน
จากการตรวจสอบสถาปัตยกรรมโปรเจกต์ (ในส่วนของ `omnichat-service`, `omnichat-gateway` และ `omnichat-normalizer-worker`) นี่คือแผนการจัดการงานสำหรับการทำสปริ้นต์:

- **[ ] Subtask 1: พัฒนาระบบ Inbound Webhook Normalization (Mapper)**:
  - **สถานะ**: ยังไม่ได้ทำ (TO DO) ตัวระบบมีการรับค่า `RawWebhookMessage` ด้วย `ChannelExtractorService.extractFacebook` แล้ว แต่ยังขาด Mapper สำหรับแปลงข้อมูลให้เป็นโครงสร้างมาตรฐาน
  - **สิ่งที่ต้องทำ**: สร้างไฟล์ `facebook-channel-mapper.ts` ในฝั่ง Worker เพื่อแปลง raw payload จาก Meta ให้อยู่ในรูป schema v1 (`InboundEvent` DTO) อย่าลืมดึง `message.mid` มาใส่เป็น `external_message_id` เพื่อรองรับระบบ Idempotency 

- **[ ] Subtask 2: พัฒนาระบบ Outbound Sending (ส่งข้อความออก)**:
  - **สถานะ**: ยังไม่ได้ทำ (TO DO) ฟังก์ชัน `pushMessage` ในไฟล์ `facebook.strategy.ts` ยังถูกทิ้งไว้เป็นกรอบเปล่าๆ (throws NotImplementedException)
  - **สิ่งที่ต้องทำ**: เขียนโค้ดเรียกใช้งาน Meta Graph API ฝั่ง `/me/messages` เพื่อดันข้อความส่งกลับไปยังผู้ใช้งาน และเตรียมคืนค่า `message_id` กลับมาใน `PushMessageResult`

- **[ ] Subtask 3: จัดการตีความประเภท Error (Advanced Error Handling)**:
  - **สถานะ**: ยังไม่ได้ทำ (TO DO) ต่อเนื่องจากข้อสอง ตอนที่ยิงส่งออกไป ต้องคอยดัก Error Codes ต่างๆ
  - **สิ่งที่ต้องทำ**: หาก Meta ตอบกลับเป็น error ประเภท Permission issue หรือ Token invalid ต้องจับแยก category ให้เป็น `auth_error` แล้วส่ง boolean `isSuccess: false` พร้อมแนบ Message เหตุผลไป โค้ดด้านบนจะได้ปรับสถานะช่องทางให้เป็น Error อัตโนมัติ

- **[ ] Subtask 4: ตรวจสอบความถูกต้องของ Webhook Setup**:
  - **สถานะ**: เสร็จไปบางส่วน (DONE/REVIEW) ระบบมีเส้น API `GET /webhooks/facebook` ส่ง `hub.challenge` ไปตอบ Meta แล้วผ่านหมด และการทำ HMCA validation จาก Payload ด้วยท่ายืนยัน `validateFacebookSignature` ก็มีครบ
  - **สิ่งที่ต้องทำ**: แค่รีวิวรันเทสอีกรอบว่าเวลา body เข้ามาหนักๆ จะไม่พัง

## 2. ข้อเสนอแนะ & Edge Cases ที่ควรระวัง

1. **ระวัง Event ที่ไม่ใช่การแชท (Read, Delivery, Postback)**:
   - **ความเสี่ยง**: Webhook ของ Meta ชอบพ่วงสถานะการอ่าน (read), สถานะข้อความไปถึง (delivery) หรือเหตุการณ์การกดปุ่ม (postback) มารัวๆ ท่ามกลาง webhook ปกติ
   - **ข้อเสนอแนะ**: แน่ใจว่าไฟล์ `facebook-channel-mapper.ts` ที่จะสร้างใหม่ มีลอจิกคอยคัดพวกนี้ทิ้ง (drop หรือคืนค่าเป็น null) ไปเลยอย่างเซฟๆ เพื่อไม่ให้ Worker มันหยิบไปทำเป็นข้อความเปล่าในระบบเรา 

2. **การทำ Threading กับ Facebook**:
   - **ความเสี่ยง**: ขจัดความกังวลทิ้งไปได้เลย เนื่องจาก Meta ใช้ Page-Scoped ID (PSID) ส่งมาในชื่อฟิลด์ `sender.id` 
   - **ข้อเสนอแนะ**: แค่โยนไอดีตัวนี้เข้าไปที่ `external_user_id` ก็พอ เพราะ `MessagesService` ของเรามันฉลาดพอที่จะหั่น `external_user_id` ผสมกับอวาตาร์ตัวมันเองสร้างเป็น Hash Thread ยูนีคอยู่แล้วสำหรับ Facebook v1 ดังนั้นไม้ต้องเพิ่มท่าพิสดาร

3. **ข้อความขาเข้าที่มีรูปภาพหรือไฟล์ต่างๆ**:
   - **ความเสี่ยง**: แม้ในโจทย์บอกว่ายังไม่ทำเรื่องส่งรูป "Not include attachments" แต่ระบบของ Meta ก็คงยิงรูปลูกค้าเข้ามาอยู่ดี
   - **ข้อเสนอแนะ**: Mapper ควรเขียนเช็กเผื่อ array ตรง `message.attachments` ไว้ด้วย อาจจะให้มัน drop ทิ้งไปเงียบๆ ก่อนค่อยคุยกันต่อ หรือใส่ string แจ้งเตือนแอดมินเข้าไปแทนว่า `[ไม่รองรับรูปภาพในเวอร์ชันนี้]` ដើម្បីกัน App พังเวลาพยายามดึง Text เปล่าๆ
