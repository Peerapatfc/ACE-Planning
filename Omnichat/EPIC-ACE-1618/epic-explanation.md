# EPIC-ACE-1618: SLA Management — คำอธิบายภาษาคน

**ClickUp:** [ACE-1618](https://app.clickup.com/t/86d2hdp46) | **Status:** To Do | **Total:** 31 SP

---

## SLA คืออะไร และทำไมต้องมี?

**SLA (Service Level Agreement)** คือข้อตกลงเรื่องความเร็วในการตอบ — ระบบบอกว่า "conversation นี้ต้องตอบภายใน X ชั่วโมง" และตามดูว่าทีม CS ทำได้ตามเป้าหรือเปล่า

**ปัญหาที่แก้:**
- ตอนนี้ agent ไม่รู้ว่า conversation ไหน "เร่งด่วน" จริงๆ โดยไม่นับเอง
- Supervisor ไม่มี audit trail ว่าตอบทันหรือพลาด deadline ไปกี่ conversation
- Message เข้าตี 3 แล้ว breach ตอนเช้า — ไม่ fair กับทีม

**SLA v1 วัดแค่ First Response Time (FRT):** นับตั้งแต่ลูกค้าส่งข้อความครั้งแรก → จนถึงตอนที่ agent ตอบครั้งแรก

---

## SLA Status ทั้งหมด

```
Message เข้า
    ↓
[active] → เหลือ <= threshold นาที → [due_soon] → เลย deadline → [breached]
    ↓                ↓
    └──── agent ตอบก่อน deadline ────→ [met]
    
met → ลูกค้าส่งใหม่ → [active] (cycle ใหม่)
```

| Status | ความหมาย | สีใน UI | Timer แสดงอะไร |
|--------|----------|---------|----------------|
| `disabled` | SLA ปิด หรือ agent ทักก่อน | ไม่แสดง | ไม่แสดง |
| `active` | นับเวลาอยู่ เหลือเยอะ | เขียว | `8h 23m` |
| `due_soon` | เหลือน้อยกว่า threshold | เหลือง/amber | `14m` |
| `breached` | เลย deadline แล้ว | แดง | `Overdue +14m` |
| `met` | ตอบทันก่อน deadline | ไม่แสดง | ไม่แสดง |

---

## Business Hours Aware คืออะไร?

ปัญหา: ลูกค้าทักตี 3 → SLA นับ → ตอน 9 โมงเช้า agent มางาน deadline ผ่านไปแล้ว → breach ทั้งที่ยังไม่ได้เริ่มงาน

**Simple BH-aware (v1 ที่ implement):**

| กรณี | ตัวอย่าง | sla_due_at คือ |
|------|----------|----------------|
| Message เข้าระหว่าง BH | BH 09-18, เข้า 10:00, target 1h | 11:00 วันเดียวกัน |
| Message เข้าหลัง BH ปิด | BH 09-18, เข้า 19:00, target 1h | 10:00 วันถัดไป |
| Message เข้ากลางคืน | BH 09-18, เข้า 23:00, target 1h | 10:00 วันถัดไป |
| Message เข้าวันเสาร์ | BH จ-ศ 09-18, เข้าเสาร์ 14:00, target 2h | 11:00 วันจันทร์ |
| เข้าตอนใกล้ปิด BH | เข้า 17:59, target 1h | 09:59 วันถัดไป |

> ถ้า BH toggle ปิด → ใช้ 24/7 เหมือนเดิม (backward compatible)

---

## Story Breakdown (4 Stories)

| Story | ชื่อ | ทำอะไร | ใคร | SP |
|-------|------|--------|-----|-----|
| **SLA-01** | SLA Configuration UI | Settings page: ตั้งค่า target time ต่อ channel, due soon threshold, BH toggle | Admin/Supervisor | 8 |
| **SLA-02** | SLA Timer Engine | Backend: คำนวณ `sla_due_at`, state machine, BH calculation | Backend | 13 |
| **SLA-03** | Timer Display in Inbox | Frontend: badge สี 3 สถานะ, Overdue filter pill, auto-refresh 30s | Agent/Supervisor | 5 |
| **SLA-04** | Breach Detection & Auto-tag | Background job ทุก 1 นาที, system tag `sla_met`/`sla_breached` | Backend | 5 |

**Dependency chain:**
```
SLA-01 (config) → SLA-02 (engine อ่าน config) → SLA-03 (display ใช้ engine state) → SLA-04 (breach job ใช้ engine state)
```

---

## SLA-01: Settings UI (8 SP)

**หน้า Settings > SLA** มี 2 ส่วน:

**Global Settings card:**
- Global toggle เปิด/ปิด SLA ทั้งหมด
- Due soon threshold (นาที) — เมื่อเหลือน้อยกว่านี้ = badge เปลี่ยนเหลือง
- Business Hours toggle — ถ้าเปิดจะแสดง preview schedule จาก SETTINGS-02

**Channel SLA Targets card (ต่อ row):**
- Toggle เปิด/ปิดต่อ channel
- Number input + unit (minutes/hours) + default ตาม recommended
- Info icon tooltip อธิบาย platform constraint
- Warning ถ้า Facebook/Instagram > 24h
- Reset to default button

**Rules สำคัญ:**
- Save config ใหม่ **ไม่กระทบ conversations ที่เปิดอยู่แล้ว** — มีผลกับ conversations ใหม่เท่านั้น
- BH toggle เปิดไม่ได้ถ้าไม่มี BH data ใน SETTINGS-02
- เฉพาะ Admin/Supervisor เข้าถึงได้

**Recommended defaults ต่อ channel:**

| Channel | Default | เหตุผล |
|---------|---------|--------|
| Facebook | 1h | มี 24h messaging window |
| Instagram | 1h | Strict กว่า FB — หลัง 7 วันปิดสนิท |
| LINE | 1h | Business expectation ทั่วไป |
| Shopee | 12h | Marketplace ลูกค้ารอได้นานกว่า |
| Lazada | 12h | Marketplace best practice |
| TikTok Shop | 12h | วัด After-Sales Handling Time |

---

## SLA-02: Timer Engine (13 SP) — หัวใจของทั้ง epic

**Pure backend story — ไม่มี UI**

**Fields ใหม่บน `conversations` table:**
```
sla_due_at           TIMESTAMP WITH TIME ZONE
sla_met_at           TIMESTAMP WITH TIME ZONE
sla_status           VARCHAR  -- disabled|active|due_soon|breached|met
sla_first_inbound_at TIMESTAMP WITH TIME ZONE
sla_bh_aware         BOOLEAN  -- บันทึก mode ตอน calculate
```

**Timer เริ่ม/หยุดเมื่อ:**
- เริ่ม: first inbound message จาก customer + SLA enabled บน channel นั้น
- ไม่เริ่ม: agent ทักก่อน (outbound-first), SLA ปิด
- หยุด → met: agent ส่ง outbound reply ครั้งแรก
- ไม่หยุด: internal note, bot/auto-reply
- Follow-up: ลูกค้าทักใหม่หลัง met → cycle ใหม่เริ่มทันที

**Function `next_bh_open_at(timestamp, bh_schedule, timezone)`:**
- ถ้าอยู่ใน BH แล้ว → return timestamp เดิม
- ถ้าหลัง BH ปิด → return วันถัดไปตอน BH เปิด
- ถ้าวันนี้ไม่มี BH → วนหาวันที่มี BH ถัดไป
- ทุก timestamp เก็บ UTC, แปลงด้วย workspace timezone ตอน compare

---

## SLA-03: Timer Display (5 SP)

**Frontend consume ข้อมูลจาก SLA-02 — ไม่มี SLA logic เอง**

**Timer badge format:**
- เหลือ > 1h → `"8h 23m"` (เขียว/เหลือง/แดง)
- เหลือ < 1h → `"23m"`
- Breached → `"Overdue +14m"` หรือ `"Overdue +2h 5m"` (แดง, นับเพิ่มทุก 1 นาที)
- Met/Disabled → ไม่แสดง badge

**Overdue filter pill:**
- อยู่ใน filter bar เดียวกับ "all", "my open", "unassigned"
- กรอง `sla_status = breached` → sort by elapsed overdue (เกิน deadline นานที่สุดขึ้นก่อน)
- ปรากฏตลอดเมื่อ SLA enabled **โดยไม่ต้องตั้ง due_soon_threshold ก่อน**

**Auto-refresh:** `setInterval` ทุก 30 วินาที — poll เฉพาะ conversations ที่มี active SLA ใน viewport

---

## SLA-04: Breach Detection & Auto-tag (5 SP)

**Pure backend — background job + tag management**

**`sla_met` tag:**
- เพิ่ม real-time ตอน agent ส่ง reply (trigger จาก SLA-02) — ไม่รอ job
- เก็บ `response_time_seconds` สำหรับ analytics

**`sla_breached` tag:**
- Job scan ทุก **1 นาที**: `WHERE sla_due_at <= NOW() AND sla_status IN ('active', 'due_soon')`
- เปลี่ยน status → breached + เพิ่ม tag (idempotent — run ซ้ำไม่ duplicate)
- Tag **ลบไม่ได้** — เป็น audit trail ถาวร แม้ agent ตอบทีหลัง
- ใครพยายามลบ (Agent/Supervisor/Admin) → error 403

**System tags ใน UI:**
- แสดง lock icon เล็กๆ แยกจาก user tags
- Tooltip: "System tag สร้างโดยระบบอัตโนมัติ ไม่สามารถลบได้"

**Multi-cycle audit trail:**
```
Cycle 1: ลูกค้าทัก 10:00 → due 11:00 → agent ตอบ 10:45 → [sla_met, cycle=1] ✓
Cycle 2: ลูกค้าทักใหม่ 14:00 → due 15:00 → ไม่มีใครตอบ → [sla_breached, cycle=2] ✗
UI badge: Overdue +Xm (latest cycle = 2)
History: cycle 1 met, cycle 2 breached — ทั้งคู่อยู่ครบ
```

---

## Data Model Overview

```
sla_configs
  workspace_id, channel_type, enabled, first_response_minutes
  due_soon_minutes, bh_aware, created_at, updated_at

conversations (fields เพิ่ม)
  sla_due_at, sla_met_at, sla_status
  sla_first_inbound_at, sla_bh_aware

conversation_tags
  tag_id, conversation_id, is_system, tag_name, created_at

conversation_sla_events
  id, conversation_id, cycle_number
  event_type (met|breached), inbound_at, sla_due_at
  resolved_at, response_time_sec, created_at
```

---

## สิ่งที่ต้องระวัง (Critical Rules)

| Rule | เหตุผล |
|------|--------|
| Config save ไม่กระทบ conversations เปิดอยู่ | เปลี่ยน target ไม่ควร retroactive — ไม่ fair กับ agent |
| System tags ลบไม่ได้เด็ดขาด | Audit trail สำหรับ compliance |
| `sla_met` ต้อง real-time ไม่รอ job | Agent ตอบแล้ว timer ต้องหยุดทันที |
| BH fallback ถ้าไม่มี BH data | ห้าม crash — ใช้ 24/7 แทนพร้อม log warning |
| Timezone เก็บ UTC, convert เมื่อ compare BH | ห้าม off-by-one จาก timezone conversion |
| Overdue pill ไม่ต้องรอ due_soon_threshold | Filter คนละ feature กับ badge สี |
| Index บน `sla_due_at` + `sla_status` | Job query ทุก 1 นาที — ต้องเร็ว |

---

## Dependencies ภายใน Epic

```
SETTINGS-01 (Settings shell)
SETTINGS-02 (Business Hours API)
    ↓
SLA-01 (Settings UI: config + BH toggle)
    ↓
SLA-02 (Timer Engine: calculate sla_due_at, state transitions)
    ↓
SLA-03 (Display: badge, Overdue pill, auto-refresh)
SLA-04 (Breach job: detect → tag → event → [notification epic 2.8])
```

> Notification เมื่อ breach **ไม่อยู่ใน epic นี้** — อยู่ใน epic 2.8 (Notification Center)
