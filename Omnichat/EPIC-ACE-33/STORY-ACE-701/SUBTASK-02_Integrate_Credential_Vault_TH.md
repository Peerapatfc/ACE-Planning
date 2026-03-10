# Subtask 2: Integrate Credential Vault

**สถานะ**: TO DO

## รายละเอียด
ตรวจสอบให้แน่ใจว่า Access Token และ Refresh Token ที่ดึงมาจากขั้นตอนการเชื่อมต่อ Marketplace จะถูกเข้ารหัสอย่างปลอดภัยและจัดเก็บผ่านระบบ Credential Vault (อ้างอิง FND-02).

## รายละเอียดการพัฒนา
1. **ไฟล์ที่เกี่ยวข้อง**: 
   - `apps/omnichat-service/src/channel-accounts/services/marketplace-auth.service.ts` (New)
   - `apps/omnichat-service/src/vault/vault.service.ts` (สมมติว่าเป็นระบบตาม FND-02)
2. **สถานะปัจจุบัน**: การจัดเก็บ Token พื้นฐานของ Channel มีการรองรับแล้ว แต่จำเป็นต้องเชื่อมเข้าสู่ระบบ Credential Vault (FND-02) ซึ่งมีความปลอดภัยสูงกว่า
3. **สิ่งที่ต้องทำ**: 
   - เมื่อสามารถแลก Token ได้สำเร็จ (จาก Subtask 1) ให้เรียกใช้ Vault Service เพื่อเข้ารหัสข้อมูล Credential ขั้นสุดท้าย (Encrypted at rest)
   - หลีกเลี่ยงการจัดเก็บ Access Token แบบตรงๆ ลงใน Table หลักของ `channel_accounts` โดยให้จัดเก็บเป็น Token Reference หรือ Vault ID แทน
   - ทำการ Mask หรือตัด (Redact) ข้อมูล Token ทั้งหมดออกจาก Log ของ Application (Observability) เพื่อป้องกันไม่ให้ข้อมูลสำคัญหลุดออกไป
