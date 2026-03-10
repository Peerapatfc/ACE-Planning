# Subtask 4: ตรวจสอบกระบวนการ Webhook Normalization

**สถานะ**: TO DO

## รายละเอียด (Description)
ตรวจสอบกระบวนการแปลง webhook ภายใน `omnichat-gateway` ว่ามีการดึงข้อมูลค่าที่จำเป็นของ LINE ส่งต่อไปให้ฝั่ง service ได้อย่างถูกต้องและครบถ้วน เพื่อทำการ Normalization ให้อยู่ในรูปแบบโครงสร้างร่วมของระบบเรา

## ขั้นตอนการทำงาน (Implementation Details)
1. **ไฟล์เป้าหมาย**: `apps/omnichat-gateway/src/webhook/services/channel-extractor.service.ts`
2. **สถานการณ์ปัจจุบัน**: โค้ดในส่วน `extractLine` มีการใช้งาน `sourceUserId: event.source?.userId || 'unknown'`
3. **ความเสี่ยงที่พบ**:
   - ถ้า payload ส่งมาแบบไม่มี `userId` ตัวอย่างเช่นการที่ Bot ถูกดึงเข้ากลุ่ม LINE Group Chat ระบบจะส่งมาเป็น type `group` ซึ่งบางทีจะไม่มี `userId` ให้ 
   - การใช้คำว่า `'unknown'` เป็น fallback ไปยัง service จะทำให้การ Hash ผิดพลาด ผู้ใช้งานที่ไม่รู้จักทั้งหมดจะถูกจับเข้าห้องแชทเดียวกัน มั่วไปทั้ง Tenant แน่นอน
4. **สิ่งที่ต้องทำ (Action Required)**: 
   - ทีมพัฒนาต้องกลับไปทบทวนว่าเราจะใช้ `groupId` / `roomId` แทนกรณีที่ `userId` หายไปหรือไม่
   - อีกทางเลือกคือการข้าม payload หรือโยนเป็น Bad Request ออกไปเลยสำหรับเคสที่ขาด identifier ที่จำเป็น เพื่อไม่ให้ขยะ (ค่า unknown) เข้าไปทำให้ database เลอะเทอะ
   - เข้าไปลงมืออัปเดตแกะโค้ดใน `extractLine` เพื่อรับมือเรื่องนี้ให้เรียบร้อย
