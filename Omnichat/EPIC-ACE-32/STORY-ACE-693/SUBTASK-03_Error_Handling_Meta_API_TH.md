# Subtask 3: จัดการตีความประเภท Error (Advanced Error Handling)

**สถานะ**: TO DO

## รายละเอียด (Description)
พัฒนาระบบดักจับ Error ที่สมบูรณ์แบบ ควบคู่ไปกับโค้ดฝั่งส่งข้อความออกของ Facebook โดยตัว Strategy ต้องสามารถตีความและแยกหมวดหมู่ล้มเหลวให้ระบบแม่ (Orchestrator) รับทราบได้อย่างชัดเจน 

## ขั้นตอนการทำงาน (Implementation Details)
1. **ไฟล์เป้าหมาย**: `apps/omnichat-service/src/channel-accounts/strategies/facebook.strategy.ts` (ในบล็อค catch ของฟังก์ชัน pushMessage)
2. **สถานการณ์ปัจจุบัน**: ยังไม่มีอะไรถูกเขียนไว้ในส่วนนี้เลย
3. **สิ่งที่ต้องทำ (Action Required)**: 
   - หากยิง Meta API ผิดพลาด 通常 API จะตอบกลับมาเป็นพวก `OAuthException` หรืออธิบายเหตุผลตรงๆ มาว่า token หมดอายุ หรือขาด Permission ขอบข่ายไหน
   - เขียนลอจิกคัดแยก Error โยนกลับเข้า Response กลางให้เรียบร้อย โดยใส่ `isSuccess = false` และแนบเนื้อหา `errorMessage` ระบบ MessagesService จะหยิบไปตีตรา Database เป็น `auth_error` หรือ `failed` ต่อไปเองเลยอัตโนมัติ 
   - ตรวจสอบให้มั่นใจว่าข้อมูล Error จะมี Log เพียงพอช่วยฝ่ายเทคนิคสืบสวนต่อได้ แต่ไม่หลุดรั่วทะลุมาโชว์ Token ของลูกค้าใน Log
