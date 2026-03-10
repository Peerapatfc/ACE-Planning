# Subtask 1: ตรวจสอบการทำ Inbound Mapping

**สถานะ**: TO DO / DONE (ลอจิกมีอยู่แล้วใน Codebase ปัจจุบัน)

## รายละเอียด (Description)
ตรวจสอบไฟล์ `MessagesService` ว่ามีการใช้งาน `fallback_thread_key` โดยมาจากการ hash ค่า `external_user_id` + `channel_account_id` สำหรับ LINE inbound mapping เพื่อให้มั่นใจได้ว่ามีกระบวนการจัดกลุ่มการสนทนา (Conversation Mapping) ที่ถูกต้องสำหรับ channel ที่ไม่มี `thread_id` ส่งมาใน webhook 

## รายละเอียดการตรวจสอบ (Verification Details)
1. **ไฟล์เป้าหมาย**: `apps/omnichat-service/src/messages/messages.service.ts`
2. **สถานการณ์ปัจจุบัน**: เมธอด `resolveConversation` มีดักเช็กตัวแปร `external_thread_id` อยู่แล้ว หากไม่มีจะทำการตกลงไปใช้สเตป `computeFallbackThreadKey(external_user_id, channel_account_id)` ซึ่งใช้กระบวนการ SHA256 Hash ออกมาเป็นค่าที่คงที่แน่นอน (deterministic)
3. **การประเมิน**: ลอจิกที่เตรียมไว้ถูกต้องและสามารถทำงานได้ตาม Acceptance Criteria ของ Pilot phase
4. **สิ่งที่ต้องทำ (Action Required)**: แค่ตรวจสอบและเช็กความมั่นใจคู่กับทีม QA อีกครั้งว่าได้ผลตรงตามที่คาดหวัง สามารถทยอยย้ายสถานะเป็น DONE ได้เลย เพราะในแง่ของโค้ดทำส่วนนี้ไว้เรียบร้อยแล้ว (เว้นแต่จะมีบั๊คที่มาจาก edge case เช่น ทักมาจาก Group)
