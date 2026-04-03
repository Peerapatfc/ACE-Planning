# EPIC ACE-1614: Settings & Configuration — คำอธิบายแบบเข้าใจง่าย

## สรุปภาพรวม

Settings คือ area รวม config ทั้งหมดที่ตั้งครั้งเดียวแล้วมีผลกับทั้ง workspace — ทั้งข้อมูลองค์กร, เวลาทำการ, และการจัดการสมาชิกทีม

Epic นี้มี **dependency chain** ชัดเจน:

```
SET-01 (Shell & Navigation)
  └── SET-02 (Business Information & Business Hours)
        └── SET-03 (Members & Roles + Work Shift)
```

SET-03 ต้องรอ SET-02 เสร็จก่อน เพราะ toggle "Same as business hours" ใน work shift ของแต่ละ user อ่านข้อมูลจาก SET-02 โดยตรง

---

## Settings Sections — ใครเข้าได้บ้าง

| Settings Section | Admin | Supervisor | Agent |
|---|---|---|---|
| Business Information | ✅ | ❌ | ❌ |
| Members & Roles | ✅ | ❌ | ❌ |
| Channels (มีอยู่แล้ว) | ✅ | ❌ | ❌ |
| SLA Rules (via SLA-01) | ✅ | ✅ | ❌ |
| Notification Rules (via NOTIF-04) | ✅ | ✅ | ❌ |
| My Preferences (via NOTIF-05) | ✅ | ✅ | ✅ |

> Section ที่ไม่มีสิทธิ์จะ **ไม่อยู่ใน UI เลย** — ไม่ใช่ greyed out ไม่ใช่ disable ไม่มีใน DOM เลย

---

## 3 Stories — สิ่งที่ต้องสร้าง

### Story SET-01: Settings Shell & Sidebar Navigation

**คืออะไร?** Pure frontend — สร้าง layout และ navigation shell ของ Settings area ทั้งหมด ยังไม่มี content จริง แค่ shell, routing, และ sidebar ที่ filter ตาม role Content ของแต่ละ section จะ build ใน stories ถัดไป

**Layout:**
```
┌─────────────────────────────────────────────────┐
│  Top Navigation                                  │
├─────────────┬───────────────────────────────────┤
│             │  Settings > Business Information   │  ← Breadcrumb
│  Sidebar    │                                    │
│  ─────────  │  [Content Area]                    │
│  Business   │  (placeholder รอ SET-02,            │
│  Information│   SET-03, SLA-01, NOTIF-04/05)     │
│  Members    │                                    │
│  Channels   │                                    │
│  SLA Rules  │                                    │
│  Notif. ▸   │                                    │
│  My Prefs   │                                    │
└─────────────┴───────────────────────────────────┘
```

**Sidebar ตาม role:**
```
Admin     → เห็นทุก 6 section
Supervisor → เห็นแค่: SLA Rules, Notification Rules, My Preferences
Agent     → เห็นแค่: My Preferences
```

**Auto-redirect:** เมื่อ user เข้า `/settings` โดยตรง ระบบ redirect ไป section แรกที่มีสิทธิ์อัตโนมัติ — ไม่มีหน้าขาว

**Route guard:** พิมพ์ URL ของ section ที่ไม่มีสิทธิ์โดยตรง → redirect ไป 403 Section ที่ไม่มีสิทธิ์ **ไม่อยู่ใน DOM เลย** ไม่ใช่แค่ hidden ด้วย CSS

**Active section:** Highlight ใน sidebar (left border + background) + breadcrumb "Settings > [ชื่อ Section]" ด้านบน content area

---

### Story SET-02: Business Information & Business Hours

**คืออะไร?** หน้าสำหรับ Admin เท่านั้น แบ่งเป็น 2 sections: ข้อมูลตัวตนของ workspace และเวลาทำการ

**Section 1 — Business Information:**

| Field | แก้ไขได้? | หมายเหตุ |
|---|---|---|
| Company Logo | ✅ | JPG/PNG, ไม่เกิน 2MB, preview ทันที |
| Organization Name | ✅ | บังคับกรอก — save ไม่ได้ถ้าว่าง |
| Email | ✅ | contact email ของ workspace (ไม่ใช่ login email) |
| Phone Number | ✅ | |
| Store ID | ❌ | Read-only + copy to clipboard สร้างตอน workspace ถูกสร้าง **ไม่เปลี่ยนแปลงได้** |
| Timezone | ❌ | อ่านจาก workspace config แสดงผลเท่านั้น |

**Section 2 — Business Hours:**

แต่ละวัน (อาทิตย์–เสาร์) มี row เป็นของตัวเอง:

```
[ ] อาทิตย์   [ปิด]
[✓] จันทร์    09:00 ▾  ถึง  18:00 ▾   [+]  [Copy times to all]
[✓] อังคาร    09:00 ▾  ถึง  18:00 ▾   [+]
[✓] พุธ       09:00 ▾  ถึง  18:00 ▾   [+]
...
```

- **Toggle ต่อวัน:** เปิด/ปิดวันนั้น — time input แสดง/ซ่อนตามที่ toggle
- **Time dropdown:** ทุก 30 นาที ตั้งแต่ 00:00 ถึง 23:30
- **เพิ่ม shift (+):** เพิ่ม time range ที่ 2 สำหรับทำงานแบบแยกช่วง เช่น 09:00–12:00 และ 13:00–18:00
- **ลบ shift (−):** ลบ row shift ที่เพิ่มมา
- **"Copy times to all":** copy เวลาของวันนั้นไปทุกวันที่ toggle เปิดอยู่

**รูปแบบข้อมูลที่เก็บ:**
```json
{ "day": "monday", "enabled": true, "shifts": [{ "start": "09:00", "end": "18:00" }] }
```

**ทำไม Business Hours สำคัญต่อ story อื่น:**
- SET-03 toggle "Same as business hours" อ่านข้อมูลจากที่นี่
- อนาคต: SLA timer หยุดนับนอกเวลา business hours

---

### Story SET-03: Members & Roles Page + Edit User + Work Shift

**คืออะไร?** หน้าจัดการ member ที่สมบูรณ์ ใช้ API จาก RBAC-02 ร่วมกับ Edit User modal ที่ตั้งค่า work shift ของแต่ละ user ด้วย

**คอลัมน์ในรายการ member:**

| คอลัมน์ | หมายเหตุ |
|---|---|
| ชื่อ + Avatar | แสดงรูปโปรไฟล์ |
| Email | แสดงอย่างเดียว |
| Role | Badge (Admin / Supervisor / Agent) — อ่านได้ใน list, เปลี่ยนได้ผ่าน Edit modal |
| Work Shift | Summary: "Same as BH" หรือ "จ-ศ 09:00-18:00" หรือ "ไม่ได้ตั้ง" |
| Last Active | relative time เช่น "2 ชม. ที่แล้ว" |
| Actions | ปุ่ม Edit → เปิด Edit modal |

**Edit User Modal — 2 sections:**

```
┌─────────────────────────────────────┐
│  แก้ไขข้อมูลสมาชิก                   │
├─────────────────────────────────────┤
│  User Information                   │
│  ชื่อ-นามสกุล: [สมชาย ใจดี    ]     │
│  Email:        abc@co.com    🔒     │  ← read-only แก้ไขไม่ได้
│  Role:         [Supervisor  ▾]      │
├─────────────────────────────────────┤
│  User's Work Shift                  │
│  [✓] Same as business hours         │
│      Preview: จ-ศ 09:00-18:00       │
│                                     │
│  (ถ้า toggle ปิด:)                  │
│  [จ] 09:00 → 18:00  [+]             │
│  [อ] 09:00 → 18:00  [+]             │
│  ...                                │
├─────────────────────────────────────┤
│                        [บันทึก]     │
│  [ลบสมาชิกออกจาก workspace]         │  ← ด้านล่างสุด แยกชัดเจน
└─────────────────────────────────────┘
```

**Toggle "Same as business hours" — จุดออกแบบสำคัญ:**
```
Toggle เปิด  → เก็บ flag: same_as_business_hours = true
               ไม่ copy ค่าเวลามาเป็น snapshot
               → ถ้า Admin แก้ business hours ใน SET-02 ทีหลัง
                 เวลาทำงาน effective ของ user นี้อัปเดตอัตโนมัติ

Toggle ปิด  → เก็บ shift แบบ custom อิสระ
               → การเปลี่ยน business hours ไม่กระทบ user นี้
```

**หน้า Pending Invitations** (ใช้ข้อมูลจาก RBAC-02):
- แสดง: Email, Role, วันที่ส่ง, สถานะหมดอายุ, ปุ่ม Resend / Cancel
- invitation ที่หมดอายุแสดงผลต่างจาก invitation ที่ active อยู่

**Remove member จาก Edit modal:**
- กด Remove → confirm dialog (แจ้งผลกระทบที่จะเกิดขึ้น)
- ยืนยัน → member ถูกลบ, session ถูก revoke ทันที, หายจาก list
- ยกเลิก → modal ยังเปิดอยู่ ไม่มีอะไรเปลี่ยน

**หมายเหตุ schema `team_id`:**
`workspace_members` table มี column `team_id` (nullable, default null) ตั้งแต่ story นี้ ไม่แสดงใน UI ที่ MVP — เตรียม schema ไว้สำหรับ Teams ใน Release 2

**`user_work_shifts` table:**
```
user_id, workspace_id, same_as_business_hours (boolean), shifts (JSON array), created_at, updated_at
```

---

## ความสัมพันธ์ระหว่าง 3 Stories

```
SET-01 (Shell)
  → สร้าง Settings layout และ sidebar ที่ filter ตาม role
  → Route guard บล็อก section ที่ไม่มีสิทธิ์
  → Auto-redirect ไป section แรกที่เข้าได้
  → Settings story อื่นทั้งหมดอยู่ใน shell นี้

SET-02 (Business Information & Hours)
  → Admin ตั้งข้อมูลองค์กรและเวลาทำการ
  → Business hours เป็น source of truth สำหรับ:
      - SET-03 toggle "Same as business hours"
      - อนาคต: SLA timer หยุดนับนอกเวลา

SET-03 (Members & Roles + Work Shift)
  → หน้า member management ที่สมบูรณ์ใน shell ของ SET-01
  → เรียก RBAC-02 API สำหรับ invite, เปลี่ยน role, remove
  → อ่านข้อมูล business hours จาก SET-02 ใน work shift toggle
  → Edit User modal ครอบคลุมทั้ง profile info และ schedule
```

---

## สรุปตัวเลข

| หมวด | จำนวน |
|---|---|
| Stories | 3 (SET-01, SET-02, SET-03) |
| Settings sections ทั้งหมด | 6 sections |
| Section ที่เฉพาะ Admin เข้าได้ | 3 (Business Info, Members, Channels) |
| Section ที่ Admin + Supervisor เข้าได้ | 2 (SLA, Notification Rules) |
| Section ที่ทุก role เข้าได้ | 1 (My Preferences) |

---

## ตัวอย่าง End-to-End: Admin ตั้งค่า workspace สำหรับทีมใหม่

```
1. Admin กดไอคอน Settings
   → Shell ของ SET-01 โหลด → sidebar แสดงทุก 6 section
   → Auto-select "Business Information" (section แรกที่เข้าได้)

2. Admin กรอก Business Information
   → Upload โลโก้บริษัท (JPG, 1.2MB → preview ขึ้นทันที)
   → ตั้งชื่อ Organization: "ร้าน ABC Shop"
   → ตั้ง Email: info@abcshop.com
   → Store ID: สร้างอัตโนมัติ, read-only (Admin copy ไปใช้กับ integration)
   → กด Save → toast "บันทึกข้อมูลเรียบร้อยแล้ว"

3. Admin ตั้ง Business Hours
   → Toggle จ-ศ เปิด ตั้งเวลา 09:00–18:00
   → กด "Copy times to all" ที่ วันจันทร์ → อ-ศ อัปเดตทันที
   → เพิ่ม shift ที่ 2 วันจันทร์: 09:00–12:00 และ 13:00–18:00 (พักกลางวัน)
   → เสาร์-อาทิตย์ยังปิดอยู่
   → กด Save

4. Admin invite สมาชิก (ผ่านปุ่ม Invite ใน Members page จาก RBAC-02)
   → Agent นิด accept invite → ปรากฏในรายการ member

5. Admin กด Edit ที่ Agent นิด
   → Edit modal เปิด
   → เปิด "Same as business hours" ON
     → เวลาทำงานของ Agent นิด ตามเวลาทำการของ workspace อัตโนมัติ
   → กด Save → Work Shift column แสดง "Same as BH"

6. ต่อมา Admin แก้ Business Hours (เพิ่มวันเสาร์เช้า)
   → เวลา effective ของ Agent นิด อัปเดตอัตโนมัติรวมวันเสาร์
   → ไม่ต้องแก้ทีละ user

7. Supervisor ล็อกอินแล้วกด Settings
   → Sidebar แสดงแค่: SLA Rules, Notification Rules, My Preferences
   → Business Information, Members & Roles, Channels ไม่ปรากฏใน UI เลย

8. Supervisor พิมพ์ /settings/members ใน URL bar โดยตรง
   → Route guard ทำงานก่อน render
   → Redirect ไป 403 "คุณไม่มีสิทธิ์เข้าถึงหน้านี้"
```
