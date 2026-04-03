# EPIC ACE-1610: RBAC (Role-Based Access Control) — คำอธิบายแบบเข้าใจง่าย

## สรุปภาพรวม

RBAC คือ foundation ที่ทุก feature บน platform อ้างอิง ก่อนหน้านี้ platform มีแค่ single user ไม่มีระบบ role เพราะมีแค่ tenant เดียว เมื่อ team เริ่มขยาย จำเป็นต้องมีระบบควบคุมว่า "ใครทำอะไรได้บ้าง" เพื่อ:
- ป้องกันการ access ข้อมูลที่ไม่ควร เช่น Agent เห็น config ทั้งหมดของระบบ
- Audit trail ที่ชัดเจน รู้ว่าใครตอบ conversation ไหน ใคร config อะไร
- รองรับ team ที่มีหลายคน Admin, Supervisor, Agent มีหน้าที่ต่างกัน

**เปรียบเทียบง่าย ๆ:**
เหมือนระบบบัตรผ่านของตึกบริษัท — รปภ. (Admin) มีกุญแจหลักเปิดได้ทุกห้อง หัวหน้า (Supervisor) เข้าได้ส่วนใหญ่ พนักงาน (Agent) เข้าได้แค่พื้นที่ทำงานตัวเอง

---

## 3 Roles ที่ MVP รองรับ

| Role | คือใคร | ทำอะไรได้บ้าง |
|---|---|---|
| **Admin** | เจ้าของ / ผู้ดูแลระบบ | Config ทุกอย่าง, manage members, manage channels, ดูได้ทุกอย่าง (สร้างโดยอัตโนมัติเมื่อ workspace ถูกสร้าง) |
| **Supervisor** | หัวหน้าทีม CS | ดู inbox ทั้งหมด, assign/reassign conversation, config SLA และ notification, ดู report ของทีม |
| **Agent** | CS staff | ดู inbox ทั้งหมด, ตอบ conversation ได้ทุก conversation, เปลี่ยน status |

> **Note:** First Admin = คนที่สร้าง workspace จะได้รับ Admin role อัตโนมัติ ไม่ต้องถูก invite

---

## Permission Matrix — ใครทำอะไรได้บ้าง

| Permission | Admin | Supervisor | Agent |
|---|---|---|---|
| ดู conversation ทั้งหมด | ✅ | ✅ | ✅ |
| ตอบ conversation ทุก conversation | ✅ | ✅ | ✅ |
| Assign / Reassign conversation | ✅ | ✅ | ❌ |
| เปลี่ยน status conversation | ✅ | ✅ | ✅ |
| Config SLA rules | ✅ | ✅ | ❌ |
| Config notification rules | ✅ | ✅ | ❌ |
| ตั้งค่า personal notification preferences | ✅ | ✅ | ✅ |
| ดู team report / analytics (later) | ✅ | ✅ | ❌ |
| Invite / Remove member | ✅ | ❌ | ❌ |
| เปลี่ยน role ของ member | ✅ | ❌ | ❌ |
| Manage channels | ✅ | ❌ | ❌ |
| Access Settings > Workspace | ✅ | ❌ | ❌ |
| Access Settings > Channels | ✅ | ❌ | ❌ |
| Access Settings > SLA | ✅ | ✅ | ❌ |
| Access Settings > Notification Rules | ✅ | ✅ | ❌ |
| Access Settings > My Preferences | ✅ | ✅ | ✅ |

---

## 3 Stories — สิ่งที่ต้องสร้าง

### Story RBAC-01: Permission Model & API Enforcement (Backend)

**คืออะไร?** Pure backend story ไม่มี UI — กำหนด role, permission rules และบังคับ 403 Forbidden ที่ API layer เป็น foundation ที่ทุก feature อื่นต้องอ้างอิง

**จุดออกแบบสำคัญ — ตรวจแบบ action-based ไม่ใช่ role-based โดยตรง:**
แทนที่จะเขียน `if role == "admin"` ในแต่ละ endpoint ระบบใช้ `canDo()` helper:

```
canDo(userId, workspaceId, action) → boolean

ตัวอย่าง:
  canDo(user1, ws1, "assign_conversation")  → true  (Supervisor)
  canDo(user2, ws1, "assign_conversation")  → false (Agent)
  canDo(user3, ws1, "manage_members")       → false (Supervisor)
```

ทำไมต้อง action-based? ง่ายต่อการ extend ในอนาคต — เพิ่ม action ใหม่ที่เดียว ไม่ต้องแก้กระจายทุก endpoint

**9 Protected Actions:**

| Action | Admin | Supervisor | Agent |
|---|---|---|---|
| reply_any_conversation | ✅ | ✅ | ✅ |
| assign_conversation | ✅ | ✅ | ❌ |
| change_conversation_status | ✅ | ✅ | ✅ |
| config_sla | ✅ | ✅ | ❌ |
| config_notification | ✅ | ✅ | ❌ |
| view_team_report | ✅ | ✅ | ❌ |
| manage_members | ✅ | ❌ | ❌ |
| manage_channels | ✅ | ❌ | ❌ |
| manage_workspace | ✅ | ❌ | ❌ |

**Role ผูกกับ workspace แต่ละอัน:**
```
User เป็น Admin ใน Workspace A แต่เป็น Agent ใน Workspace B
→ เรียก manage_members ด้วย context Workspace B
→ ระบบตรวจ role ใน Workspace B (Agent)
→ ตอบ 403 — แม้จะเป็น Admin ใน workspace อื่น
```

**เมื่อ request ไม่มีสิทธิ์:**
```
Agent เรียก POST /conversations/:id/assign
→ Permission middleware ทำงานก่อน handler
→ Agent ไม่มีสิทธิ์ assign_conversation
→ ตอบกลับ: 403 Forbidden
  { "error": "permission_denied", "action": "assign_conversation", "required_role": "..." }
→ Handler function ไม่ทำงานเลย
```

**Reply log — field `replied_by`:**
ข้อความ outbound ทุกข้อความบันทึกว่าใครส่ง `replied_by = user_id` ต้องมีเสมอ ห้าม null และ immutable หลัง create ไม่สามารถแก้ไขได้

---

### Story RBAC-02: Member Management

**คืออะไร?** Flow สำหรับ invite สมาชิกใหม่, เปลี่ยน role, และ remove สมาชิก — เฉพาะ Admin เท่านั้นที่ทำได้

**Invitation Flow:**
```
1. Admin ไปที่ Settings > Members → กด "Invite Member"
2. ใส่ email + เลือก role (Admin / Supervisor / Agent) → กด Send
3. ระบบส่ง email จาก no-reply@domain (รอยืนยันชื่อโดเมน)
   พร้อม link ที่มี token แบบ cryptographically random (32-byte hex)
   ใช้ได้ 7 วัน

4. ผู้รับกด link:
   → ถ้าไม่มี account: ลงทะเบียนก่อน แล้วเข้า workspace
   → ถ้ามี account อยู่แล้ว: login แล้วเข้า workspace
   → ได้รับ role ที่กำหนดทันที

5. ถ้าไม่ accept ภายใน 7 วัน:
   → link หมดอายุ (ตรวจที่ backend ไม่ใช่แค่ UI)
   → Admin ต้อง Resend เพื่อออก link ใหม่ + reset เวลา 7 วัน
```

**โครงสร้างหน้า:**

```
Settings > Members
├── Active Members
│   └── ตาราง: Name | Email | Role | Joined date | Last active | Actions
│       → เปลี่ยน role ผ่าน dropdown inline (มี confirm dialog ก่อนทำ)
│       → ปุ่ม Remove (มี confirm dialog พร้อม warning)
│
└── Pending Invitations
    └── ตาราง: Email | Role | Sent date | Expires | Status | Actions (Resend / Cancel)
```

**Admin Protection Rules — ป้องกันไม่ให้ workspace ไม่มี Admin เหลือ:**

| Scenario | Decision |
|---|---|
| Admin down role ตัวเอง | ได้ ถ้ามี Admin คนอื่นที่ active อยู่อย่างน้อย 1 คน |
| Admin down role Admin อีกคน | ได้ ถ้ายังมี Admin เหลืออย่างน้อย 1 คนหลังเปลี่ยน |
| Admin remove Admin อีกคน | ได้ ถ้ายังมี Admin เหลืออย่างน้อย 1 คนหลัง remove |
| Workspace มี Admin เหลือ 1 คน | Admin คนนั้นไม่สามารถ down role ตัวเองหรือถูก remove ได้เลย |

**เมื่อ member ถูก remove:**
- Session token ถูก revoke **ทันที** — เรียก API ต่อไปได้เลย 401
- ประวัติ conversation และข้อความเก็บไว้ครบ
- ชื่อใน reply log แสดงเป็น "former member (ชื่อ)"

**เมื่อ role เปลี่ยน:**
- Session ไม่ถูก revoke — member ยังล็อกอินอยู่ได้
- Permission ใหม่มีผลทันทีใน request ถัดไป ไม่ต้อง re-login

---

### Story RBAC-03: Frontend Permission Enforcement

**คืออะไร?** ฝั่ง UI — route guard, ซ่อน/แสดง element ตาม role และจัดการ 403 **สำคัญ:** การ hide ที่ frontend คือ UX เท่านั้น — backend 403 (RBAC-01) คือ security จริง

**Route Permission Map:**

| Route | Admin | Supervisor | Agent |
|---|---|---|---|
| /inbox | ✅ | ✅ | ✅ |
| /settings/workspace/* | ✅ | ❌ | ❌ |
| /settings/channels | ✅ | ❌ | ❌ |
| /settings/sla | ✅ | ✅ | ❌ |
| /settings/notifications/rules | ✅ | ✅ | ❌ |
| /settings/notifications/preferences | ✅ | ✅ | ✅ |
| /settings/members | ✅ | ❌ | ❌ |

**`usePermission` hook — วิธี component ตรวจสิทธิ์:**
```
usePermission("assign_conversation")  → true  (Supervisor หรือ Admin)
usePermission("assign_conversation")  → false (Agent)

- อ่านจาก session/app state (Redux, Zustand, Context)
- ไม่เรียก API เพิ่ม — derive จาก auth token ที่มีอยู่แล้ว
- update เมื่อ session refresh หลัง role เปลี่ยน
```

**3 layers การบังคับ:**

```
1. Route Guard (ทำงานก่อน component render ใดๆ)
   → Agent navigate ไป /settings/sla
   → Redirect ไป /inbox ทันที — ไม่มี page content โผล่เลย
   → Toast: "คุณไม่มีสิทธิ์เข้าถึงหน้านี้"
   → ทำงานทั้ง initial load และ navigation ระหว่าง session

2. UI Visibility (hidden ไม่ใช่ greyed-out)
   → Settings sidebar แสดงเฉพาะ section ที่มีสิทธิ์:
      Admin     → ทุก section
      Supervisor → SLA + Notifications เท่านั้น
      Agent     → Notifications > My Preferences เท่านั้น
   → Assign panel: ไม่อยู่ใน UI เลยสำหรับ Agent (ไม่ใช่แค่ disable หรือ grey)

3. API Error Handling (จัดการ error อย่างสวยงาม)
   → Server ตอบ 403 → แสดงหน้า 403 พร้อมปุ่ม "กลับหน้าหลัก"
   → ไม่ crash และไม่แสดงหน้าขาว
   → หน้า 403 ไม่เปิดเผยว่ากำลัง access resource อะไร
```

**Reply behavior — ทุก role ตอบได้:**
```
Agent เปิด conversation ที่ assigned ให้คนอื่น
→ reply input เปิดใช้งานได้ปกติ
→ แสดง banner "assigned to Agent นิด" เพื่อความชัดเจน
→ Agent ส่ง reply → replied_by = user_id ของ Agent นี้ (backend บันทึก)
```

**ห้ามมี flash of unauthorized content:**
Element ที่ไม่มีสิทธิ์ต้องไม่โผล่ขึ้นมาแม้แต่ชั่วขณะก่อนถูกซ่อน Layout ต้องไม่กระโดดจาก element โผล่แล้วหาย ถือเป็น bug ถ้าเกิดขึ้น

**Session หมดอายุระหว่างใช้งาน:**
```
Session token หมดอายุขณะ user กำลัง active อยู่
→ Redirect ไปหน้า login
→ บันทึก URL ปัจจุบันเพื่อ return หลัง login ใหม่
→ แสดงข้อความ: "กรุณา login ใหม่ session หมดอายุแล้ว"
```

---

## ความสัมพันธ์ระหว่าง 3 Stories

```
RBAC-01 (Backend — security จริง)
  → กำหนด action list และ permission rules
  → บังคับ 403 ก่อน handler ทำงาน
  → บันทึก replied_by ทุกข้อความ

RBAC-02 (Member Management)
  → ใช้ Admin protection logic จาก RBAC-01
  → Invitation flow + จัดการ role/remove
  → Revoke session เมื่อ remove member

RBAC-03 (Frontend — UX layer)
  → อ่าน role จาก session token
  → Route guard บล็อกหน้าที่ไม่มีสิทธิ์
  → usePermission hook ซ่อน UI element ที่ไม่ควรเห็น
  → จัดการ 403 response อย่างสวยงาม
  → Backend 403 (RBAC-01) คือ security จริง
```

---

## สรุปตัวเลข

| หมวด | จำนวน |
|---|---|
| Roles | 3 (Admin, Supervisor, Agent) |
| Stories | 3 (RBAC-01, RBAC-02, RBAC-03) |
| Protected actions | 9 actions |
| Protected routes (frontend) | 7 routes |
| Invitation expiry | 7 วัน |

---

## ตัวอย่าง End-to-End: สมาชิกใหม่เข้าร่วมทีมและเริ่มทำงาน

```
1. Admin เปิด Settings > Members → "Invite Member"
   → Email: agent@company.com, Role: Agent
   → ระบบส่ง email จาก no-reply@domain
   → pending invitation โผล่ขึ้นในรายการพร้อม timer 7 วัน

2. Agent กด link ภายใน 7 วัน
   → ลงทะเบียนหรือ login → เข้า workspace ด้วย role Agent

3. Agent เปิด Inbox
   → เห็น conversation ทั้งหมด ✅
   → reply input เปิดใช้ได้ทุก conversation ✅
   → ไม่มี Assign panel ใน UI เลย ❌ (RBAC-03 ซ่อนไว้)
   → เมนูไม่มี Settings > Channels, Settings > Members ❌

4. Agent พิมพ์ /settings/channels ในเบราว์เซอร์โดยตรง
   → Route guard ทำงานก่อน render ใดๆ
   → Redirect ไป /inbox + toast "คุณไม่มีสิทธิ์เข้าถึงหน้านี้"

5. Agent เปิด conversation ที่ assigned ให้ Agent คนอื่น
   → เห็น banner "assigned to Agent นิด"
   → reply input ยังใช้งานได้ปกติ — ตอบได้เลย

6. Admin ลบ Agent ออกจาก workspace ภายหลัง
   → Session ของ Agent ถูก revoke ทันที
   → Agent เรียก API ครั้งต่อไป → 401 Unauthorized
   → ประวัติ conversation ยังอยู่ครบ; reply log แสดง "former member (ชื่อ Agent)"

7. Admin พยายาม remove ตัวเองขณะเป็น Admin คนสุดท้าย
   → API ตอบ 400: "ต้องมี Admin อย่างน้อย 1 คนใน workspace"
   → Action ถูกบล็อกทั้ง frontend (ปุ่ม disable) และ backend (error 400)
```
