# Subtask 3: Develop Multi-Shop Data Mapping

**สถานะ**: TO DO

## รายละเอียด
พัฒนาระบบและ Logic ในการ Map ข้อมูล เพื่อให้ Tenant เดียวสามารถเชื่อมต่อกับร้านค้า (Shop) ได้หลายร้านอย่างปลอดภัยแบบ 1-to-many โดยป้องกันไม่ให้ข้อมูลเก่าถูกเขียนทับดื้อๆ.

## รายละเอียดการพัฒนา
1. **ไฟล์ที่เกี่ยวข้อง**: 
   - `apps/omnichat-service/src/channel-accounts/channel-accounts.service.ts`
   - `packages/shared/src/types/` (ปรับปรุง payload)
2. **สถานะปัจจุบัน**: ระบบ `channel_accounts` สามารถบันทึกบัญชีภายนอกได้ แต่จำเป็นต้องเพิ่มการป้องกันข้อมูลซ้ำ (Duplication) และอุดช่องโหว่เมื่อมีหลาย Shop.
3. **สิ่งที่ต้องทำ**: 
   - สร้าง Logic เพื่อนำค่า `external_account_id` (เช่น shop_id หรือ seller_id) ที่ได้จาก Marketplace มาบันทึกผูกกับ `channel_account_id` ระบบเรา 
   - ก่อนจะ Insert ข้อมูล ต้องทำการเช็คก่อนว่า `external_account_id` นึ้ถูกผูกหรือใช้งานโดย Tenant ควบคุมอื่นหรือไม่ หากใช่ ให้ปฏิเสธขบวนการเพื่อป้องกันการปล้นสิทธิ์ (Account Hijacking)
   - หาก Tenant ผูกบัญชีเดิมซ้ำ (`external_account_id` ตัวเดิม) ให้ตัวระบบทำการ Update ข้อมูล หรือ Token ใน Vault ที่มีอยู่ แทนที่จะไปสร้าง Row ขึ้นมาใหม่ให้ซ้ำซ้อนกัน
