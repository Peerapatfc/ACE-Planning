# EPIC-A4.1: Rule Automation

**ClickUp ID:** ACE-2211
**Status:** To Do
**Product:** Omni
**Type:** Epic
**URL:** https://app.clickup.com/t/86d3115uz
**Last Synced:** 2026-06-30

---

## Overview

Rule Automation ให้ Admin และ Supervisor ตั้งค่า automation สำหรับ conversation ได้เองโดยไม่ต้องพึ่ง developer ลด manual work ของทีม support และสร้าง consistent experience ให้ลูกค้า โดยมีแนวคิดหลัก:

- **Action-first:** เริ่มจากเลือกว่าอยากให้ระบบทำอะไร ไม่ใช่ blank form
- **2-step wizard เท่านั้น:** Step 1 Triggers → Step 2 Action detail ลด decision fatigue
- **Auto-generate rule name:** admin ไม่ต้องคิดชื่อก่อนทำงาน
- **Background safety:** bot skip, dedup, sender_type, SLA field ทำงานอัตโนมัติ ไม่ expose ใน UI

---

## Stories

| Story | ชื่อ | สาระสำคัญ | Status | SP | URL |
|-------|------|-----------|--------|----|-----|
| ACE-2212 | STORY-RA-01: Rule Management (CRUD) | Rule list, wizard action-first, CRUD + permission matrix | 🔵 In Progress | 8 | https://app.clickup.com/t/86d3115yy |
| ACE-2213 | STORY-RA-02: Define Trigger Conditions | Keyword / Channel / Business hours + AND/OR logic + test panel | 🔵 In Progress | 5 | https://app.clickup.com/t/86d31160t |
| ACE-2214 | STORY-RA-03: Send Auto-reply Message | Text editor, template variables, cooldown, only-first-wins | 🔵 In Progress | 2 | https://app.clickup.com/t/86d31162h |
| ACE-2215 | STORY-RA-04: Auto-Tag Conversation | Append-only tag, tagged_by_type metadata, inline create | ⚪ To Do | 3 | https://app.clickup.com/t/86d311653 |

**Total: 18 SP**

---

## Trigger Conditions

| Type | Options | Notes |
|------|---------|-------|
| Keyword match | contains, exact | Case-insensitive ไทย-อังกฤษ |
| Channel | Multi-select | LINE, Facebook, Instagram, Shopee, Lazada, TikTok |
| Business hours | within / outside | รวม day of week + timezone; toggle Workspace hours |

---

## Actions

| Action | Key config | Important notes |
|--------|-----------|----------------|
| Auto-reply | Message + variables + cooldown (required) | Only-first-wins, sender_type = rule, ไม่นับ FRT |
| Add tag | Multi-select + create inline | Append-only, tagged_by_type = rule |

---

## Rule Execution Logic

เมื่อ message เข้า ระบบจะ:

1. ตรวจว่า message มาจาก bot/system หรือไม่ → ถ้าใช่ skip ทั้งหมด (background)
2. ตรวจ message deduplication 5-second window → ถ้าซ้ำ **skip** (background)
3. Evaluate conditions ทุก active rule ณ เวลาที่ message เข้า (single-pass)
4. Execute actions ของ rules ที่ match ทั้งหมด เรียงตาม `created_at` (เก่าสุดก่อน)
   - **Add tag:** ทุก rule ที่ match ติด tag ได้ (append-only, ไม่ duplicate)
   - **Auto-reply:** ส่งเพียงครั้งเดียวจาก rule เก่าสุด — rule อื่น skip auto-reply แต่ actions อื่นยังทำงาน

**ตัวอย่าง:**
- Rule A: auto-reply "สวัสดี" ส่ง ✓ / tag: off-hours ติด ✓
- Rule B: auto-reply "ขอบคุณ" skip ✗ (เพราะ A ส่งไปแล้ว) / tag: shopee ติด ✓
- Rule C: tag: cancellation-risk ติด ✓

**สิ่งที่ทำงาน background (ไม่ expose ใน UI):**
- `sender_type = 'rule'` ใน message record ป้องกัน agent KPI ผิดพลาด
- `first_human_response_at` แยกจาก `first_response_at` SLA metric ถูกต้อง
- Bot sender skip message จาก bot/system ไม่ trigger rule
- Message deduplication 5s window ป้องกัน trigger ซ้ำจาก message เดิม

---

## Permission Matrix

| การกระทำ | Admin | Supervisor | Agent |
|----------|-------|-----------|-------|
| ดู rule list | ✓ | ✓ | ✓ |
| สร้าง / แก้ไข rule | ✓ | ✓ | ✗ |
| Enable / Disable rule | ✓ | ✓ | ✗ |
| ลบ rule (hard delete) | ✓ | ✗ | ✗ |

---

## Business Edge Cases

### Rule Execution & Loop Prevention

| Scenario / เคส | ปัญหา / Risk | Business Decision / Solution |
|----------------|-------------|------------------------------|
| Customer ส่ง message ซ้ำหลายครั้งเร็วๆ | Rule trigger ซ้ำทำให้ส่ง auto-reply หลายอัน รบกวน customer | Message dedup 5s window (background) evaluate ครั้งเดียว; cooldown ป้องกันการส่งซ้ำ |
| Bot/platform ส่ง automated message เข้า conversation | Keyword match ทำให้ rule fire โดยไม่ควร เช่น Shopee notification มีคำว่า 'ยกเลิก' | Bot sender skip (background) ตรวจ sender_type ก่อน evaluate; ถ้าเป็น bot skip ทันที |
| หลาย rule match พร้อมกัน ทุกอันมี auto-reply | Customer ได้รับ auto-reply หลายอัน | Only-first-wins: ส่งเพียงครั้งเดียวจาก rule เก่าสุด; rule อื่น skip auto-reply แต่ actions อื่นยังทำงาน |
| Customer ตอบ auto-reply → trigger rule ซ้ำ | Loop: reply → trigger → reply → trigger... | Cooldown required ป้องกัน loop; cooldown นับ per-conversation-per-rule |

### Business Hours & Timezone

| Scenario / เคส | ปัญหา / Risk | Business Decision / Solution |
|----------------|-------------|------------------------------|
| Admin ตั้ง business hours ไม่ตรงกับ Workspace timezone | Rule fire ผิดเวลา | Toggle 'ใช้ Workspace hours' เป็น default — ถ้าปรับ custom ต้องเลือก timezone บังคับ |
| Workspace timezone เปลี่ยน แต่ rule ที่ toggle Workspace hours ยังใช้ค่าเก่า | Rule fire ผิดเวลาโดยที่ admin ไม่รู้ตัว | Rule ที่ toggle = on ดึง Workspace timezone ทุกครั้งที่ evaluate ไม่ cache ค่า |
| Admin ตั้ง time range ข้าม midnight เช่น 22:00–06:00 | ระบบคำนวณผิด ตีความว่า start > end = error | ใช้ ui เดียวกันกับ business hours ป้องกันเรื่องนี้ไว้แล้ว |

### SLA & Attribution

| Scenario / เคส | ปัญหา / Risk | Business Decision / Solution |
|----------------|-------------|------------------------------|
| Bot auto-reply ทำให้ FRT หยุดนับ | SLA metric ดีเกินจริง agent performance report ผิดพลาด | `sender_type = 'rule'` ใน message; `first_human_response_at` แยกจาก `first_response_at`; SLA ใช้ human field; auto-reply ไม่นับ FRT |
| ไม่รู้ว่า message ไหน agent ตอบ message ไหน rule ตอบ | Audit / tracing ทำไม่ได้; KPI agent ผิด | sender_type enum ใน message: human / rule / system; KPI dashboard filter by sender_type |
| Tag ที่ rule ติดปนกับ tag ที่ agent ติดใน report | ไม่รู้ว่า tag มาจากคนหรือ automation | `tagged_by_type = 'rule'` ใน metadata; report filter แยก manual / automated tagging ได้ |

### Rule Management & Permission

| Scenario / เคส | ปัญหา / Risk | Business Decision / Solution |
|----------------|-------------|------------------------------|
| Admin ลบ rule โดยไม่ตั้งใจ | Rule หาย fired count และ configuration หายหมด | Confirmation dialog แสดงชื่อ rule + fired count + warning ถาวร; delete button อยู่ใน kebab menu (⋮) |
| Agent เข้า URL /rules/{id}/edit โดยตรง | Bypass permission ผ่าน URL | Permission check ทำงานทั้ง UI และ API; 403 Forbidden สำหรับ Agent |
| Active rules เต็ม 20 ตัว ไม่สามารถสร้างใหม่ได้ | Team ไม่สามารถ respond ต่อ business ใหม่ได้ | Block create พร้อม message ชัดเจน 'ปิดบาง rule ก่อน'; inactive rules ไม่นับ limit |

### Tag Integrity

| Scenario / เคส | ปัญหา / Risk | Business Decision / Solution |
|----------------|-------------|------------------------------|
| Tag ถูกลบออกจาก system หลัง rule สร้าง | Rule crash หรือ action อื่นหยุดทำงาน | Skip tag ที่หายไปโดยไม่ error log warning; actions อื่นใน rule ยังทำงานปกติ |
| Rule ติด tag ที่ conversation มีอยู่แล้ว | Duplicate tag ทำให้ display แปลก | Dedup ก่อนติด; ถ้ามีแล้ว skip tag นั้น |
| Agent ลบ tag ที่ rule ติด แต่ rule trigger ซ้ำ | Tag กลับมาทำให้ agent งง | ถ้า cooldown ยังไม่หมด rule ไม่ trigger ซ้ำ; tag ถูกลบโดย agent จะ stay ลบจนกว่า cooldown หมดและ rule trigger ใหม่ |

---

## Wireframe

https://claude.ai/public/artifacts/6d86c342-2c98-44d3-8e74-65943003d3d3
