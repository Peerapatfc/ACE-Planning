# Subtask 1: Implement Marketplace Connect Flows

**สถานะ**: TO DO

## รายละเอียด
สร้างระบบการเชื่อมต่อและ Callback Endpoints สำหรับจัดการกระบวนการยืนยันตัวตน (OAuth และ API Key) ให้กับ API ของแพลตฟอร์ม TikTok, Shopee และ Lazada.

## รายละเอียดการพัฒนา
1. **ไฟล์ที่เกี่ยวข้อง**: 
   - `apps/omnichat-service/src/channel-accounts/controllers/marketplace-auth.controller.ts` (New)
   - `apps/omnichat-service/src/channel-accounts/services/marketplace-auth.service.ts` (New)
2. **สถานะปัจจุบัน**: ระบบสามารถเชื่อมต่อพื้นฐานกับช่องทาง LINE และ Meta ได้ แต่ยังไม่มี endpoints สำหรับรองรับ Auth Callback ของทั้ง 3 Marketplaces
3. **สิ่งที่ต้องทำ**: 
   - สร้าง Callback URLs สำหรับ OAuth2.0 ของ TikTok และ Shopee เพื่อรับ Authorization Code หลังจากที่ User ล็อกอิน
   - สร้างระบบจัดการการส่ง API Key สำหรับเจรจากับ Lazada
   - นำ Authorization Code ที่ได้ ไปแลกเป็น Access Token และ Refresh Token
   - ตรวจสอบให้แน่ใจว่า Callback URL สามารถระบุ Tenant ID ต้นทางที่กดเชื่อมต่อได้อย่างถูกต้องปลอดภัย
