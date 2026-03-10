# การวางแผนสปริ้นต์ (Sprint Planning): ACE-700 Meta Connector v1 Instagram DM Inbound and Outbound Text

## 1. การแบ่งงาน (Subtask Breakdown) และสถานะปัจจุบัน
จากการตรวจสอบสถาปัตยกรรมโปรเจกต์ (ในส่วนของ `omnichat-service`, `omnichat-gateway` และ `omnichat-normalizer-worker`) แชแนล Instagram ตอนนี้ถูกวางเพียงแค่ส่วนรับ Webhook เท่านั้น ลอจิกหลักอื่นๆ ยังขาดหายไป นี่คือแผนการจัดการงานสำหรับการทำสปริ้นต์:

- **[ ] Subtask 1: พัฒนาระบบ Inbound Webhook Normalization (Mapper)**:
  - **สถานะ**: ยังไม่ได้ทำ (TO DO) ตัวระบบต้อนรับ `RawWebhookMessage` ใน `omnichat-gateway` ด้วย `ChannelExtractorService.extractInstagram` แล้ว แต่ยังขาดการทำ Mapper สำหรับแปลงข้อมูลให้เป็น schema v1 ในฝั่ง Worker
  - **สิ่งที่ต้องทำ**: ต้องสร้างไฟล์ `instagram-channel-mapper.ts` เพื่อแปลง raw payload ดึงตัว `message.mid` มาใส่เป็น `external_message_id` เพื่อรองรับระบบ Idempotency 

- **[ ] Subtask 2: พัฒนาระบบ Outbound Sending (ส่งข้อความออก)**:
  - **สถานะ**: ยังไม่ได้ทำ (TO DO) ตอนนี้โฟลเดอร์ `omnichat-service/src/channel-accounts/strategies/` ยังไม่มีไฟล์ `instagram.strategy.ts` ตัวระบบจึงยังไม่รู้วิธีส่งข้อความกลับไปที่ Instagram
  - **สิ่งที่ต้องทำ**: สร้างคลาส `InstagramStrategy` และเขียนโค้ดเรียกใช้งาน `/me/messages` ผ่าน Graph API เพื่อดันข้อความ Text กลับไปยังลูกค้า

- **[ ] Subtask 3: จัดการประเภท Error ฝั่ง Instagram (Error Handling)**:
  - **สถานะ**: ยังไม่ได้ทำ (TO DO) ทำควบคู่ไปกับ Subtask 2
  - **สิ่งที่ต้องทำ**: หาก Meta ตอบกลับมาเป็น Permission issue หรือเหตุการณ์อื่นๆ ตอนส่งข้อความออก ให้จับแยก category คืนค่า `isSuccess: false` พร้อมอธิบาย `errorMessage` อย่างชัดเจน เพื่อให้ระบบกลางเปลี่ยน Status แจ้งเตือนแอดมิน 

- **[ ] Subtask 4: นำ Strategy ไปผูกเข้ากับ Registry กลาง**:
  - **สถานะ**: ยังไม่ได้ทำ (TO DO) 
  - **สิ่งที่ต้องทำ**: เข้าไปแก้ไฟล์ `strategy.registry.ts` เพื่อให้มันรู้จัก Provider ที่ชื่อ `INSTAGRAM` และสามารถโยนคำสั่งส่งข้อความเข้าหา `InstagramStrategy` ได้อย่างถูกต้อง

## 2. ข้อเสนอแนะ & Edge Cases ที่ควรระวัง

1. **กฎการแชทภายใน 24 ชั่วโมง (24-Hour Messaging Window)**:
   - **ความเสี่ยง**: กฎของ Instagram เข้มงวดมาก แอดมินต้องตอบกลับลูกค้าภายใน 24 ชั่วโมงเท่านั้น หากส่งข้อความออกไปนอกกฎนี้ Meta จะตีเป็น 400 Bad Request ย้อนกลับมาให้ 
   - **ข้อเสนอแนะ**: ลอจิกของการจัดการ Error ต้องรองรับและอ่าน Error Code ตัวนี้ เพื่อสื่อสารกลับมาหา UI ว่า "คุณตอบลูกค้าช้าเกินเวลาที่กำหนด" แชทจะไม่รวน

2. **ข้อความที่แนบ Reels/Story มาในโหมดข้อความ**:
   - **ความเสี่ยง**: ผู้ใช้งาน IG ชอบกดส่ง Story หรือ Reels เข้ามาทาง DM ซึ่ง payload มักจะไม่ใช่ text ธรรมดา
   - **ข้อเสนอแนะ**: Mapper สร้างใหม่ควรเรียนรู้ที่จะละทิ้ง attachment หรือเปลี่ยนมันให้เป็นข้อความ fallback อย่าง `[แชร์ Story - ยังไม่รองรับใน v1]` แทนที่จะปล่อยให้ Worker แปลงค่าไม่ได้แล้วพังเป็น exception กองค้างอยู่ในคิว

3. **การออกแบบ Threading สำหรับการสนทนา**:
   - **ความเสี่ยง**: การใช้ตัวตนฝั่ง IG จับคู่กับฝั่งแอคเคาท์ อาจมีโอกาสสับสนกับฝั่ง Facebook
   - **ข้อเสนอแนะ**: มั่นใจได้ว่า `MessagesService` ปัจจุบันของเรา สร้าง Thread โดยมีรากฐานมาจาก `tenant_id` + `channel_account_id` + `external_user_id` อยู่แล้ว ฉะนั้นข้อมูลจะแยกการสนทนากันขาด ไม่ปะปนกับช่องทาง Facebook ธรรมดา ขอแค่อ่านค่า ID ลูกค้าให้ถูกฟิลด์ก็ใช้งานได้เลย
