# Subtask 1: พัฒนาระบบ Inbound Webhook Normalization (Mapper)

**สถานะ**: TO DO

## รายละเอียด (Description)
ตัวระบบมีการรับค่า `RawWebhookMessage` ด้วย `ChannelExtractorService.extractFacebook` แล้ว แต่ยังขาดส่วนของ Mapper ในฝั่ง Worker ที่จะแปลงให้ข้อมูลดิบจาก Meta ไปอยู่ในโครงสร้างมาตรฐาน (Schema v1 `InboundEvent` DTO) ตามที่ระบบเราต้องการ

## ขั้นตอนการทำงาน (Implementation Details)
1. **ไฟล์เป้าหมาย**: สร้างไฟล์ `apps/omnichat-normalizer-worker/src/worker/channel-mapper/mappers/facebook-channel-mapper.ts`
2. **สิ่งที่ต้องทำ (Action Required)**: 
   - รับผิดชอบเขียนลอจิกแปลงฟิลด์ให้ครบถ้วนใน `FacebookChannelMapper`
   - ต้องแน่ใจว่าดึง `message.mid` มาใส่ในฟิลด์ `external_message_id` ให้ถูกต้อง เพื่อให้แน่ใจว่าเวลาระบบทำงานซ้ำ (Idempotency) ในตอนที่ Meta ยิง webhook มาเบิ้ล ระบบ `MessagesService` จะได้ไม่เซฟเดต้าเบสซ้ำซ้อน
   - ตอนดึงข้อความให้คัดแยกส่วนที่เป็นรูปภาพหรือไฟล์แนบ (Attachments) ทิ้งอย่างปลอดภัย เพื่อไม่ให้ Worker พังยามที่ไม่ได้ส่ง Text เปล่าๆ มา
   - เพิ่มคลาสใหม่ให้ Registry รู้จักในไฟล์ `channel-mapper-registry.ts`
