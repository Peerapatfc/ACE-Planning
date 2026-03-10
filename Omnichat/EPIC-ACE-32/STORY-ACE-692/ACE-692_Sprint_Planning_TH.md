# การวางแผนสปริ้นต์ (Sprint Planning): ACE-692 กฎการจัดกลุ่มข้อความ LINE OA (Threading Rules v1)

## 1. การแบ่งงาน (Subtask Breakdown) และสถานะปัจจุบัน
จากการตรวจสอบโค้ดในโปรเจกต์ (ในส่วนของ `omnichat-service` และ `omnichat-gateway`) พบว่าลอจิกหลักๆ ได้ถูกเขียนไว้แล้ว นี่คือแผนการจัดการสปริ้นต์อัปเดตล่าสุด:

- **[x] ตรวจสอบ `MessagesService` ว่าใช้งาน `fallback_thread_key` หรือไม่**:
  - **สถานะ**: ทำเสร็จแล้ว ฟังก์ชัน `resolveConversation` มีการใช้ SHA256 ผสมระหว่าง `external_user_id` และ `channel_account_id` ให้เป็น Key 
  - **สิ่งที่ต้องทำ**: เปลี่ยนสถานะเป็น Done
- **[x] ตรวจสอบการผูกข้อความขาออก (Outbound) ให้จับคู่กับ `conversationId` เดิมใน `sendMessage`**:
  - **สถานะ**: ทำเสร็จแล้ว ทาง `ConversationsService.sendMessage` มีการรับ Parameter เป็น `conversationId` และใช้เซฟข้อความใหม่ลงฐานข้อมูลเลย ไม่มีการเปิดห้องแชทใหม่
  - **สิ่งที่ต้องทำ**: เปลี่ยนสถานะเป็น Done
- **[x] เพิ่ม/อัปเดต Unit Tests ใน `messages.service.spec.ts`**:
  - **สถานะ**: เกือบสมบูรณ์แบบ มี Test Case เรื่อง `fallback_thread_key determinism` ครอบคลุมอยู่แล้ว
  - **สิ่งที่ต้องทำ**: ลองรันเทสให้ผ่าน และเขียนเพิ่มกรณี Edge cases ขาดหายเล็กน้อย
- **[ ] ตรวจสอบ `omnichat-gateway` webhook normalization ว่าส่ง field ถูกต้องหรือไม่**:
  - **สถานะ**: เสร็จไปบางส่วน ใน `ChannelExtractorService.extractLine` มีการถึงค่า `sourceUserId: event.source?.userId || 'unknown'`
  - **สิ่งที่ต้องทำ**: ควรเช็กว่าถ้าไม่มี `userId` แล้วเรา default เป็น `'unknown'` จะมีปัญหาอะไรบ้าง แนะนำให้จัดการอย่างรัดกุมกว่านี้
- **[ ] จัดทำเอกสารข้อจำกัด (Limitations) สำหรับ LINE**:
  - **สถานะ**: ต้องทำ (To Do)
  - **สิ่งที่ต้องทำ**: เขียนคู่มือหรือหน้า Wiki ระบุเอาไว้ว่าตอนนี้ยังไม่รองรับ LINE Group Chats หรือ Room

## 2. ข้อเสนอแนะ & Edge Cases ที่ควรระวัง

1. **การจัดการ LINE Group Chat และ Room**:
   - **ความเสี่ยง**: LINE payload อาจจะส่ง `event.source.type` มาเป็น `group` หรือ `room` ซึ่งจะไม่มี `userId` ในบางครั้ง หากโค้ดเรา fallback กลับไปใช้คำว่า `'unknown'` จะทำให้ทุกๆ กรุ๊ปแชทถูกจับไปรวมใน `fallback_thread_key` เดียวกันแบบผิดพลาด
   - **ข้อเสนอแนะ**: ควรไปอัปเดต `ChannelExtractorService.extractLine` ให้ดักเช็กประเภทของ source ก่อน ถ้าเป็นกลุ่มอาจจะใช้ `groupId` เข้ามาเป็น key แทน หรือไม่งั้นต้องเขียนดักเพื่อ reject payload ถ้าตอนนี้ไม่อยากให้ระบบรองรับกลุ่ม

2. **Event ประเภทอื่นๆ ที่ไม่ใช่ข้อความ (Non-Message Events)**:
   - **ความเสี่ยง**: ขาเข้าอาจจะมี event อย่าง `follow`, `unfollow`, และ `postback` ด้วย
   - **ข้อเสนอแนะ**: ควรตรวจสอบให้แน่ใจว่าระบบสามารถ process event เหล่านี้ได้โดยไม่ error และไม่สร้าง conversation ลอยๆ หากไม่จำเป็น

3. **ปัญหาตัวแปรชนกันกรณีใช้ค่าตัวแทน `'unknown'`**:
   - **ความเสี่ยง**: ต่อเนื่องจากข้อแรก หากไม่มี sender id แล้วเราใช้ `'unknown'` เป็น key ผู้ใช้งานที่ไม่ระบุตัวตนทั้งหมดจาก LINE OA นั้นจะถูกผูกเข้าห้องแชทเดียวกันทั้งหมด (ชนกัน)
   - **ข้อเสนอแนะ**: ควรพิจารณา Drop event นั้นทิ้งแล้ว Throw 400 Bad Request แทนดีกว่าการใช้ค่า `'unknown'` ไปสร้าง data ขยะในระบบ
