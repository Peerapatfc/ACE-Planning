# Subtask 4: Implement Status Tracking & Reconnect Flow

**สถานะ**: TO DO

## รายละเอียด
สร้างระบบแจ้งเตือนและระบุสถานะการเชื่อมต่อ (Status) เช่น Active, Expired (หมดอายุ) หรือ Error และเปิดให้ User เข้ามากด Reconnect หรือ Refresh สิทธิ์เชื่อมต่อใหม่ได้อย่างราบรื่น

## รายละเอียดการพัฒนา
1. **ไฟล์ที่เกี่ยวข้อง**: 
   - `apps/omnichat-service/src/channel-accounts/channel-accounts.service.ts`
2. **สถานะปัจจุบัน**: หากการเชื่อมต่อหลุดหรือ Token หมดอายุ ระบบอาจพังแบบเงียบๆ ทำให้ Tenant Admin ไม่ทราบสถานะการต่อร้านที่แท้จริง
3. **สิ่งที่ต้องทำ**: 
   - บันทึกสถานะการเชื่อมต่อลง Entity ใน Database เช่น ฟิลด์ `connection_status` (เก็บเป็น Enum: `ACTIVE`, `EXPIRED`, `ERROR`)
   - หาก API Marketplace รองรับ ให้เขียนระบบ Background คอยตรวจสอบและ Refresh ต่ออายุ Token ล่วงหน้า 
   - ดึงค่าสถานะส่งไปขึ้นบน Frontend ให้ชัดเจน หากสถานะกลายเป็น `EXPIRED` ให้มีปุ่มกดให้ User รันสคริปต์ Re-authenticate (หมุนกลับไป Flow 1) อีกครั้ง โดยต้องอัปเดตข้อมูลของ `channel_account_id` เดิมที่มีอยู่ แทนที่จะไปสร้างของใหม่
