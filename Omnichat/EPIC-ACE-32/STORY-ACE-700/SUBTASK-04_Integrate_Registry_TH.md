# Subtask 4: นำ Strategy ไปผูกเข้ากับ Registry กลาง

**สถานะ**: TO DO

## รายละเอียด (Description)
เพื่อให้ระบบภาพใหญ่และหน้าบ้านสามารถใช้คำสั่งโยนข้อความมาให้ `InstagramStrategy` จัดการทำงานต่อได้ ทางผู้พัฒนาจำเป็นต้องเชื่อมจูนสวิตช์ของมันไว้ในฐานระบบตั้งค่ากลางของเซอร์วิสนั้นเอง (Registry)

## ขั้นตอนการตรวจสอบ (Verification Details)
1. **พื้นที่เป้าหมาย**: `apps/omnichat-service/src/channel-accounts/strategies/strategy.registry.ts`
2. **สถานะปัจจุบัน**: ตอนนี้มีของ Facebook และ Line เสียบรอกันไว้อยู่ แต่ไม่มี Instagram เลย
3. **สิ่งที่ต้องทำ (Action Required)**: 
   - แงะเอาคลาส `InstagramStrategy` (จากที่เราสร้างใน Subtask 2) เข้าไป Inject
   - ชี้เป้าในระบบ Map ให้รู้ว่าเมื่อไหร่ที่มีการอ้างอิงถึง `ChannelType.INSTAGRAM` ก็ให้กระโดดเข้ามาใช้งาน Class provider ตัวนี้ได้เลย โฟลว์โปรแกรมจะได้เดินจากหน้าบ้านทะลุกระบบออก Meta ได้ຢ່າງลื่นไหล
