# Subtask 1: พัฒนาระบบ Inbound Webhook Normalization (Mapper)

**สถานะ**: TO DO

## รายละเอียด (Description)
ปัจจุบันตัวเกตเวย์รับทราบและแกะ `RawWebhookMessage` ฝั่ง Instagram มาด้วยคำสั่ง `ChannelExtractorService.extractInstagram` เรียบร้อยแล้ว แต่ทว่าที่ฝั่ง `omnichat-normalizer-worker` ยังขาดกระบวนการ Mapper สำหรับทำให้อยู่ในโครงสร้างมาตรฐานเดียวกัน (Schema v1 `InboundEvent` DTO)

## ขั้นตอนการทำงาน (Implementation Details)
1. **ไฟล์เป้าหมาย**: สร้างไฟล์ `apps/omnichat-normalizer-worker/src/worker/channel-mapper/mappers/instagram-channel-mapper.ts`
2. **สิ่งที่ต้องทำ (Action Required)**: 
   - รับผิดชอบเขียนลอจิกแปลงฟิลด์ให้ครบใน `InstagramChannelMapper`
   - ต้องดึง `message.mid` (หรือตำแหน่งที่คล้ายกัน) มาใส่ในฟิลด์ `external_message_id` ให้ได้ เพื่อให้ระบบ Idempotency สามารถป้องกันคิวเบิ้ลเวลา Meta ยิงซ้ำ
   - จัดการดึงแค่ Text ล้วนให้ปลอดภัย ฟอร์แมตแปลกๆ อย่าง Story Mention หรือรูปภาพ ให้แปลงเป็น String ข้อความเตือนหรือไม่ก็ปล่อยผ่านไป (Drop) ป้องกัน Worker พัง
   - ลงทะเบียนให้ Registry รู้จัก `PlatformType.INSTAGRAM` ที่ไฟล์ `channel-mapper-registry.ts`
