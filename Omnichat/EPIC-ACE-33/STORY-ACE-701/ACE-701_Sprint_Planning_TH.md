# Sprint Planning: ACE-701 - STORY-MKT-01: Marketplace Channel Onboarding v1

## 📋 ภาพรวมของ Story
**เป้าหมาย:** ให้ Tenant Admin สามารถเชื่อมต่อบัญชี TikTok, Shopee, และ Lazada เข้าสู่ระบบได้ เพื่อรองรับการดึงข้อความ คำสั่งซื้อ และการตอบกลับ
**สิ่งที่ต้องส่งมอบ:** 
- การเชื่อมต่อหลายบัญชีต่อหนึ่ง Tenant (Multi-account)
- การทำ Mapping ระหว่าง Shop/Seller (`external_account_id` -> `channel_account_id`)
- การจัดเก็บข้อมูล Credential อย่างปลอดภัย (Vault)
- การติดตามสถานะการเชื่อมต่อ และ Flow สำหรับ Reconnect

## 🛠️ สถานะการพัฒนาในปัจจุบัน
จากการวิเคราะห์ Codebase (`/Users/peerapatpongnipakorn/Work/AI-Knowledge/ace`):
- **Constants & Enums:** มีการกำหนด `ChannelType` พื้นฐานสำหรับ `tiktok`, `shopee`, และ `lazada` ไว้แล้วใน `packages/shared/src/constants/channel.constants.ts`
- **Channel Accounts:** มี Model และ Controller สำหรับจัดการระบบ `channel-accounts` พื้นฐาน (ใน `apps/omnichat-service` และ `api-gateway`)
- **ส่วนที่ยังขาด (Missing Pieces):**
  - Endpoint สำหรับจัดการ OAuth / API Key Callback ของ TikTok, Shopee, Lazada โดยเฉพาะ
  - การเชื่อมต่อระบบ Credential Vault (จาก FND-02) เพื่อเก็บ Access Token อย่างปลอดภัย
  - Logic ในการ Map ร้านค้าหลายร้านเข้ากับ Tenant เดียวโดยไม่ให้ข้อมูลทับซ้อน
  - ระบบแจ้งเตือนสถานะการเชื่อมต่อ (เช่น กรณี Token หมดอายุ) พร้อมฟิลด์แจ้งเตือนใน UI

## 📝 การแบ่งย่อย Subtask (Subtask Breakdown)
| ID | ชื่อ Subtask | สถานะ | รายละเอียด |
|---|---|---|---|
| MKT-01.1 | Implement Marketplace Connect Flows | TO DO | สร้าง Endpoint สำหรับดูแลเรื่อง Auth Flow ของ API TikTok, Shopee, Lazada |
| MKT-01.2 | Integrate Credential Vault | TO DO | จัดการเซฟ Access Token ลงใน Credential Vault (FND-02) พร้อมเข้ารหัสให้ปลอดภัย |
| MKT-01.3 | Develop Multi-Shop Data Mapping | TO DO | Map `external_account_id` (shop/seller ID) เข้ากับ `channel_account_id` แบบ 1-to-many ภายใต้ `tenant_id` เดียวกัน |
| MKT-01.4 | Implement Status Tracking & Reconnect | TO DO | เพิ่มฟิลด์ `connection_status` (Active, Expired, Error) และสร้าง Flow รองรับการต่ออายุหรือล็อกอินใหม่ |

## ⚠️ ข้อเสนอแนะ & Edge Cases (สิ่งที่ควรระวัง)
1. **อายุของ Token:** ตรวจสอบช่วงเวลาหมดอายุ (Expiration) ของ Token ในแต่ละแพลตฟอร์มอย่างละเอียด บางเจ้าอาจต้อง Refresh ทุกวัน ควรมี Job ช่วยต่ออายุอัตโนมัติ (ถ้า API รองรับ) หรือแจ้งเตือนสถานะให้ User มา Reconnect ทันเวลา
2. **การป้องกัน Shop ซ้ำ/ทับซ้อน:** จังหวะ Map ร้านค้า ต้องเช็คก่อนว่า `external_account_id` นั้นผูกกับ Tenant อื่นอยู่แลัวหรือไม่ เพื่อป้องกันการดึงสิทธิ์ (Hijacking) และรองรับเคสที่ User ผูกร้านค้าเดิมซ้ำเข้า Tenant เดิมได้โดยไม่พัง
3. **ความปลอดภัยของ Vault:** ห้ามให้ Credential สำคัญหลุดเข้าไปใน Application Logs เด็ดขาด (ต้อง Mask ข้อมูล)
