# EPIC ACE-1943: Notification Center — คำอธิบายแบบเข้าใจง่าย

## สรุปภาพรวม

Epic นี้คือการสร้าง "ระบบแจ้งเตือน" (Notification Center) ที่แจ้งให้ Agent รู้ทันทีเมื่อมีเหตุการณ์สำคัญเกิดขึ้น เช่น ถูก assign งาน, ลูกค้าตอบกลับ, ถูก @mention ใน note, หรือ SLA ใกล้ครบกำหนด

เป้าหมายหลักคือทำให้ Agent **ไม่พลาด conversation สำคัญ** โดยไม่ต้องคอยกดรีเฟรชหน้าจอ และไม่โดน notification รบกวนมากจนทำงานไม่ได้

**เปรียบเทียบง่าย ๆ:**
เหมือนเสียงกริ่งโต๊ะทำงานที่ดังเฉพาะเมื่อมีงานสำคัญมาถึงโต๊ะของเราเท่านั้น ไม่ใช่ดังทุกครั้งที่มีเหตุการณ์ใดๆ ในบริษัท

---

## 1. แนวคิดหลัก (Core Concepts)

### 1.1 ใครได้รับ Notification อะไร

ระบบแบ่งประเภท event ออกเป็น 4 กลุ่ม ใครได้รับขึ้นอยู่กับ role และความเกี่ยวข้องกับ conversation นั้น:

**กลุ่มที่ 1 — Conversation Events (การเปลี่ยนแปลงการ assign):**
- ถูก assign conversation ให้ฉัน → ฉันได้รับ
- conversation ของฉันถูก reassign ให้คนอื่น → ฉัน (agent เดิม) ได้รับ
- conversation ไม่มีเจ้าของ → Supervisor และ Admin ได้รับ
- มี conversation ใหม่ยังไม่มีคนรับ → Supervisor และ Admin ได้รับ

**กลุ่มที่ 2 — Message Events (ข้อความ):**
- ลูกค้าตอบกลับใน conversation ที่ assigned ฉัน → ฉันได้รับ
- ถูก @mention ใน internal note → เฉพาะคนที่ถูก mention รับเท่านั้น

**กลุ่มที่ 3 — SLA Events (การแจ้งเตือน SLA):**
- SLA ใกล้ครบกำหนด → ฉันและ Supervisor ได้รับ
- SLA เกินกำหนดเฉพาะ conversation ของฉัน → ฉันได้รับ
- SLA เกินกำหนด ภาพรวมทีม → Supervisor และ Admin ได้รับ

**กลุ่มที่ 4 — System Events (ระบบ):**
- Channel มีปัญหา (token หมดอายุ, disconnect) → เฉพาะ Admin รับ

### 1.2 ลำดับขั้นตอนก่อนส่ง Notification

ทุก notification ต้องผ่านการตรวจ 5 ขั้นก่อนส่งถึงผู้รับ:

1. Event เกิดขึ้นในระบบ
2. ตรวจว่า Admin เปิด event นี้ไว้ที่ workspace ไหม (ถ้าปิดก็ไม่ส่งเลย)
3. ตรวจว่าใครควรได้รับ event นี้บ้าง
4. ตรวจว่า user แต่ละคนปิด (mute) event นี้ไว้เองหรือเปล่า
5. ถ้าผ่านครบ → สร้าง notification และส่งแบบ real-time

> **หลักสำคัญ:** Admin มีอำนาจสูงสุด ถ้าปิด event ระดับ workspace ทุกคนไม่ได้รับ ไม่ว่า personal setting จะตั้งอย่างไร

---

## 2. ส่วนประกอบบนหน้าจอ (UI Components)

### Bell Icon (ไอคอนกระดิ่ง)
- อยู่มุมขวาของ top navigation ทุกหน้า
- แสดงตัวเลขจำนวน notification ที่ยังไม่อ่าน (1–99, หรือ "99+" ถ้าเกิน)
- ถ้าอ่านหมดแล้วตัวเลขหายไป ไม่แสดง "0"
- ตัวเลขเพิ่มทันทีเมื่อมี notification ใหม่เข้า โดยไม่ต้อง refresh หน้า

### Notification Panel (หน้าต่างรายการแจ้งเตือน)
เปิดขึ้นเมื่อ click bell แสดงรายการ notification ตามลำดับล่าสุดก่อน ประกอบด้วย:

- **แต่ละ item แสดง:** ไอคอนสีตาม event, ชื่อคนทำ action, คำอธิบาย, ป้ายบอก channel (LINE, FB ฯลฯ), เวลาสัมพัทธ์
- **ยังไม่อ่าน:** มีจุดแดงด้านซ้าย และพื้นหลังเข้มกว่า
- **SLA notification:** มีเส้นสีแดงด้านซ้ายบ่ง urgency
- **กด item:** ไปที่ conversation และ mark as read อัตโนมัติ
- **"อ่านทั้งหมด":** อ่านทุก item ในคลิกเดียว
- **Infinite scroll:** โหลดเพิ่มเมื่อ scroll ลงถึงล่าง เก็บประวัติ 30 วัน

### หน้า Notification Rules (Admin/Supervisor เท่านั้น)
อยู่ใน Settings > Notifications > Rules ปรับได้ต่อ event:
- เปิด/ปิด event ทั้งหมดในระดับ workspace
- เลือกว่าใครได้รับ (assigned_agent / supervisor / admin)
- SLA: ดูค่า threshold ได้, ตั้ง escalation ได้ (แจ้ง supervisor อีกครั้งถ้าผ่านไป X นาทีหลัง breach แล้วยังไม่มีใครตอบ)

### หน้า My Preferences (ทุก role เข้าได้)
อยู่ใน Settings > Notifications > My Preferences ปรับส่วนตัว:
- Mute/Unmute แต่ละ event ได้เฉพาะตัวเอง ไม่กระทบ teammate
- Event ที่ Admin ปิดไว้ระดับ workspace จะ greyed out กด toggle ไม่ได้

---

## 3. ลำดับการทำงาน (User Flow)

#### สถานการณ์: ลูกค้าทักมาใน LINE ที่ assigned ให้ "น้องมิน" อยู่

1. **ลูกค้าส่งข้อความ:**
   - ระบบตรวจ → event `customer_replied` เปิดอยู่ (global rule ผ่าน)
   - ตรวจ recipient → `assigned_agent` = น้องมิน
   - ตรวจ personal preference → น้องมินไม่ได้ mute event นี้
   - ส่ง notification ให้น้องมินทันทีผ่าน WebSocket

2. **น้องมินเห็น badge เปลี่ยนเป็น "4" บน bell icon**

3. **น้องมิน click bell:**
   - Panel เปิดขึ้น แสดง notification ล่าสุดก่อน
   - เห็น item: "สมชาย ส่งข้อความใหม่ใน "สอบถามสินค้า" · LINE"

4. **น้องมิน click item นั้น:**
   - ระบบ navigate ไป conversation
   - mark notification as read → badge ลดเหลือ "3"
   - Panel ปิดอัตโนมัติ

#### สถานการณ์: SLA ใกล้ครบกำหนดแต่น้องมิน mute ไว้

- ระบบตรวจขั้นตอนที่ 4 → น้องมิน mute `sla_due_soon` ไว้
- น้องมินไม่ได้รับ notification นั้น
- Supervisor ยังได้รับตามปกติ (แยก scope ชัดเจน)

---

## สรุปรายละเอียด (Scope)

| หมวดหมู่ | รายละเอียด |
|---|---|
| Stories ที่พัฒนาใน Epic นี้ | 5 Stories (NOTIF-01 ถึง 05) |
| ประเภท event | 10 event ใน 4 กลุ่ม |
| การส่ง real-time | ผ่าน WebSocket ต่อ user แบบ scoped |
| การป้องกัน SLA ซ้ำ | deduplication ต่อ conversation ต่อ SLA cycle |
| อำนาจการควบคุม | Admin > Supervisor > Personal preference |
| เก็บประวัติ | 30 วัน |

---

## 4. คำอธิบายแต่ละ Story (Story Breakdown)

### STORY-NOTIF-01: Notification Infrastructure (Backend ฐานราก)

**เป้าหมาย:** สร้างระบบ backend ทั้งหมดที่ story อื่นต้องอาศัย ไม่มี UI เลย

**สิ่งที่จะทำ:**
- **Database:** ตาราง `notifications` เก็บทุก notification, ตาราง `notification_dedup` ป้องกัน SLA ซ้ำ
- **NotificationService:** Function กลางที่ทุก feature ต้องเรียกเพื่อสร้าง notification ห้ามสร้างเองโดยตรง
- **Event triggers:** เชื่อม service เข้ากับ conversation assignment, inbound message, SLA timer, channel error
- **WebSocket:** ส่ง notification แบบ real-time ผ่าน channel ส่วนตัว `user:{id}:notifications` ของแต่ละ user
- **Reconnect:** เมื่อ browser กลับมา online จะดึง notification ที่ miss ระหว่างออฟไลน์อัตโนมัติ
- **SLA dedup:** `sla_due_soon` fire ได้ครั้งเดียวต่อ conversation ต่อ SLA cycle (reset เมื่อลูกค้าตอบ)
- **Retention:** เก็บ 30 วันแล้ว soft-delete

**ทำไมสำคัญ:** ถ้าไม่มี story นี้ story อื่นทั้งหมดไม่มีอะไรให้อ่านหรือเขียน

---

### STORY-NOTIF-02: Bell Icon & Unread Badge (กระดิ่งกับตัวเลขยังไม่อ่าน)

**เป้าหมาย:** สร้าง bell icon บน navigation ที่แสดงจำนวน notification ยังไม่อ่านแบบ real-time

**สิ่งที่จะทำ:**
- **Badge format:** แสดง 1–99 เป็นตัวเลข, "99+" ถ้าเกิน 99, ซ่อนเลยถ้า = 0
- **โหลดครั้งแรก:** fetch จาก API เพื่อแสดง count ที่ถูกต้องตั้งแต่ต้น
- **Real-time:** badge เพิ่มทันทีเมื่อ WebSocket ส่ง notification ใหม่มา ไม่ต้อง refresh
- **Mark all read:** badge หายทันทีก่อน API response กลับมา (optimistic update)
- **Active state:** bell เปลี่ยน visual เมื่อ panel (NOTIF-03) เปิดอยู่

---

### STORY-NOTIF-03: Notification Panel & History (หน้าต่างรายการและประวัติ)

**เป้าหมาย:** สร้าง panel dropdown ที่เปิดเมื่อ click bell แสดง notification list พร้อมจัดการ read/unread

**สิ่งที่จะทำ:**
- **Panel layout:** Header "การแจ้งเตือน" + ปุ่ม "อ่านทั้งหมด" + รายการ + empty state
- **แต่ละ item:** ไอคอน, ชื่อ actor, คำอธิบาย, channel badge, เวลาสัมพัทธ์, จุดแดงถ้ายังไม่อ่าน
- **SLA items:** มี border-left สีแดงเพิ่มเติมบ่ง urgency
- **Infinite scroll:** โหลดเพิ่ม 50 items ต่อ page เมื่อ scroll ถึงล่าง
- **Graceful handling:** ถ้า note หรือ conversation ถูกลบไปแล้ว แสดง toast แทนการ crash

**Graceful errors:**
- ลบ note ทั้งอัน → toast: "โน้ตนี้ถูกลบแล้ว" อยู่หน้าเดิม
- ลบ conversation → toast: "Conversation นี้ไม่พบ" อยู่ที่ inbox
- ลบ mention แต่ note ยังอยู่ → navigate ไป note ตามปกติ ไม่มี error

---

### STORY-NOTIF-04: Notification Rules Configuration (ตั้งค่ากฎระดับ Workspace)

**เป้าหมาย:** ให้ Admin/Supervisor config ได้ว่า event ใดเปิด/ปิด และใครได้รับ ใน Settings > Notifications > Rules

**สิ่งที่จะทำ:**
- **Toggle:** เปิด/ปิด event ทั้งหมดในระดับ workspace ถ้าปิดทุกคนไม่ได้รับ
- **Recipients:** เลือก multi-select ว่าใครรับ (assigned_agent / supervisor / admin)
- **SLA config:** ดู threshold ของ `sla_due_soon` (อ่านได้อย่างเดียว แก้ที่ SLA settings), ตั้ง escalation หลัง breach
- **Fixed recipients:** `mention` → คนที่ถูก mention เสมอ, `channel_error` → Admin เสมอ (เปลี่ยนไม่ได้)
- **Escalation rate-limit:** สูงสุด 5 escalation ต่อ user ต่อนาที กัน supervisor รับ noti ท่วมเมื่อ breach พร้อมกันหลายอัน
- **Agent เข้าหน้านี้ไม่ได้:** ถูก redirect ไปหน้า Access Denied

---

### STORY-NOTIF-05: Personal Notification Preferences (ตั้งค่าส่วนตัว)

**เป้าหมาย:** ให้ผู้ใช้ทุก role mute/unmute event ได้เฉพาะตัวเอง ใน Settings > Notifications > My Preferences

**สิ่งที่จะทำ:**
- **Personal mute:** toggle แต่ละ event ได้ เฉพาะตัวเอง ไม่กระทบ teammate เลย
- **Role filter:** Agent เห็นเฉพาะ event ที่ตัวเองรับได้ ไม่เห็น `new_conversation`, `sla_breached_team` ฯลฯ
- **Greyed out:** event ที่ Admin ปิดระดับ workspace จะ greyed out + tooltip "ปิดโดย Admin ของ workspace"
- **Default:** user ใหม่ทุกคน unmuted ทั้งหมด mute ได้เองเท่านั้น
- **ผลทันที:** เปลี่ยนแล้ว event ถัดไปใช้ preference ใหม่เลย notification ที่อยู่ใน bell แล้วไม่ถูกลบ
