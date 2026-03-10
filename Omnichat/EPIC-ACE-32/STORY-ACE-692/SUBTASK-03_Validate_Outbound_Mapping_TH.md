# Subtask 3: ตรวจสอบความถูกต้องของการ Mapping ข้อความขาออก (Outbound)

**สถานะ**: TO DO / DONE (ลอจิกมีอยู่แล้วใน Codebase ปัจจุบัน)

## รายละเอียด (Description)
ตรวจสอบว่าข้อความขาออก (Outbound) ถูก mapping กลับเข้าไปหา `conversationId` เดิมในฟังก์ชัน `sendMessage` อย่างถูกต้อง ระบบต้องเปิดป้องกันไม่ให้มีการสร้าง Conversation Record ใหม่ซ้ำซ้อนเวลาตอบกลับลูกค้า

## รายละเอียดการตรวจสอบ (Validation Details)
1. **ไฟล์เป้าหมาย**: `apps/omnichat-service/src/conversations/conversations.service.ts`
2. **สถานะปัจจุบัน**: ในฟังก์ชัน `sendMessage` จะรับ Parameter ตัวแรกเป็น `conversationId` เสมอ ระบบจะเอา ID นี้ไปหาใน Database ว่ามีห้องนี้อยู่จริงไหม จากนั้นก็ Create ข้อความที่มี `direction: 'outbound'` ผูกเข้ากับ `conversation_id: conversationId` ตัวนี้โดยตรงเลย
3. **การประเมิน**: เนื่องจากสถาปัตยกรรมถูกออกแบบมาให้ส่งผ่าน Conversation อยู่แล้วจึงไม่มีปัญหาด้ายลอจิกในการเพิ่ม Record ซ้ำซ้อน
4. **สิ่งที่ต้องทำ (Action Required)**: เพียงแค่ทำ Manual Test ให้มั่นใจบนหน้าบ้านว่า Dashboard เห็นข้อความของแอดมินตอบกลับสลับกับการสนทนาของลูกค้าในหนึ่ง Timeline (Thread) อย่างไร้รอยต่อ ตรงจุดนี้ด้านโค้ดถือว่าพร้อมแล้ว
