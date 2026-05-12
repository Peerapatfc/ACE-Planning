# EPIC-ACE-1618: Story Task Breakdown (With Repo Context)

Task แต่ละ story พร้อมคำอธิบายว่าทำอะไร — อิงจากสิ่งที่มีอยู่แล้วใน repo จริง (เฉพาะที่ยังต้องทำ)

> **Legend:** 🔧 มีโค้ดอยู่แล้วแต่ต้องแก้ | (ไม่มีไอคอน) สร้างใหม่ทั้งหมด

---

## สิ่งที่มีอยู่แล้วใน repo (อย่าทำซ้ำ)

| สิ่งที่มี | ไฟล์ | หมายเหตุ |
|----------|------|----------|
| `sla_due_at` field บน Conversation | `omnichat-service/prisma/schema.prisma` | มี index พร้อมแล้ว |
| `waiting_since_at` field | schema.prisma | ใช้แทน `sla_first_inbound_at` ได้บางส่วน |
| `last_inbound_at` field | schema.prisma | track message ล่าสุดของลูกค้า |
| Inbound hook เซ็ต `sla_due_at` | `messages.service.ts` | มีแต่ hardcode 12h — ต้องแก้ |
| Agent reply hook clear `sla_due_at = null` | `messages.service.ts` | มีแต่ logic ผิด — ต้องแก้ |
| `sort_by: 'sla_due_soonest'` | `conversations.service.ts` + frontend | ครบทั้ง backend + UI แล้ว |
| `is_overdue` filter ใน list API | `conversations.service.ts` | filter `sla_due_at < now()` |
| `config_sla` permission | `packages/shared/src/types/rbac.types.ts` | Admin/Supervisor ได้, Agent ไม่ได้ |
| `SLA_DURATION_MS = 12h` constant | `packages/shared/src/constants/common.constants.ts` | hardcoded — ต้องแทนที่ด้วย config |

---

## SLA-01 — SLA Configuration UI (8 SP)

> **เป้าหมาย:** สร้างหน้า Settings ให้ Admin/Supervisor ตั้งค่า SLA ได้ต่อ channel และเปิด BH mode

---

### Task 1.1 — สร้าง `sla_configs` table + migration
**ทำอะไร:** สร้างตารางใหม่เพื่อเก็บ config SLA per channel per workspace  
**ทำไม:** ปัจจุบัน `SLA_DURATION_MS` hardcode 12h อยู่ใน constant — ไม่สามารถ config ต่อ channel ได้

```sql
-- omnichat-service migration ใหม่
workspace_id          VARCHAR
channel_type          VARCHAR   -- facebook, instagram, line, shopee, lazada, tiktok_shop
enabled               BOOLEAN   DEFAULT true
first_response_minutes INT      -- แทน SLA_DURATION_MS ที่ hardcode
due_soon_minutes      INT
bh_aware              BOOLEAN   DEFAULT false
created_at, updated_at TIMESTAMP
PRIMARY KEY (workspace_id, channel_type)
```

---

### Task 1.2 — API: `GET /sla/config`
**ทำอะไร:** endpoint ดึง config ทั้งหมดของ workspace นั้น รวม global toggle  
**ทำไม:** หน้า Settings ต้องโหลดค่าเดิมมาแสดง ตอนนี้ไม่มี endpoint นี้

**Location:** `apps/api-gateway/src/omnichat/` → route ใหม่, permission: `config_sla`

---

### Task 1.3 — API: `PATCH /sla/config`
**ทำอะไร:** endpoint รับค่าที่ user แก้แล้ว upsert ลง `sla_configs` table  
**ทำไม:** ถ้าไม่มีนี้ กด Save แล้วค่าไม่ persist

**Rule:** save แล้วกระทบเฉพาะ conversation ใหม่ — conversation ที่เปิดอยู่แล้วไม่โดน

---

### Task 1.4 — UI: Global Settings card
**ทำอะไร:** ส่วนบนหน้า Settings > SLA — toggle เปิด/ปิด SLA ทั้ง workspace + input due soon threshold  
**ทำไม:** ไม่มีหน้า Settings > SLA ใน workspace-admin เลย ต้องสร้างใหม่

**Location:** `apps/workspace-admin/src/app/(main)/dashboard/settings/sla/page.tsx` (ใหม่)

---

### Task 1.5 — UI: Channel SLA Targets card (per-channel rows)
**ทำอะไร:** แสดง row ต่อ channel — toggle + number input + unit + info icon + reset to default  
**ทำไม:** ไม่มี UI ส่วนนี้เลย

---

### Task 1.6 — UI: Warning FB/IG > 24h
**ทำอะไร:** validate ฝั่ง client — ถ้า target เกิน 1440 นาที (24h) บน Facebook หรือ Instagram แสดง warning banner  
**ทำไม:** ป้องกัน admin ตั้งค่าแล้วเสีย messaging window โดยไม่รู้

---

### Task 1.7 — UI: Business Hours toggle + preview + warning
**ทำอะไร:** toggle BH mode + ดึง schedule จาก SETTINGS-02 มาแสดง preview + warning ถ้า BH ไม่ได้ set  
**ทำไม:** admin ต้องเห็นว่า BH ของ workspace ตั้งไว้ว่าอะไรก่อนเปิด toggle

---

### Task 1.8 🔧 — RBAC Guard ใช้ `config_sla` permission ที่มีอยู่แล้ว
**ทำอะไร:** ต่อ `config_sla` permission ที่ define ไว้แล้วใน `rbac.types.ts` เข้ากับ endpoint ใหม่  
**ทำไม:** permission define แล้วแต่ยังไม่มี endpoint ที่ใช้งาน

**Note:** `config_sla` action มีอยู่แล้วใน shared package — แค่ wire เข้า guard

---

## SLA-02 — SLA Timer Engine (13 SP)

> **เป้าหมาย:** อัปเกรด SLA logic ที่มีอยู่ (hardcode 12h) ให้อ่านจาก config, เพิ่ม status machine, รองรับ BH mode

---

### Task 2.1 🔧 — DB migration: เพิ่ม SLA fields ที่ยังขาด
**ทำอะไร:** `sla_due_at` และ `waiting_since_at` มีแล้ว — เพิ่มเฉพาะที่ขาด  
**ทำไม:** ปัจจุบัน `sla_status` ไม่มี, ใช้ null/non-null ของ `sla_due_at` แทน — ไม่รองรับ state machine เต็มรูปแบบ

**Fields ที่ต้องเพิ่ม:**
```sql
-- เพิ่มใน conversations table
sla_status   VARCHAR DEFAULT 'disabled'  -- disabled|active|due_soon|breached|met
sla_met_at   TIMESTAMP WITH TIME ZONE    -- ตอน agent ตอบทัน
sla_bh_aware BOOLEAN DEFAULT false       -- บันทึก mode ตอน calculate

-- หมายเหตุ: sla_due_at มีแล้ว, waiting_since_at ใช้แทน sla_first_inbound_at ได้
```

---

### Task 2.2 🔧 — แก้ Inbound hook ให้อ่าน config แทน hardcode
**ทำอะไร:** แก้ `messages.service.ts` ที่ตอนนี้ใช้ `SLA_DURATION_MS` hardcode → ให้ query `sla_configs` table แทน  
**ทำไม:** `SLA_DURATION_MS = 12h` ทุก channel — ต้องอ่านค่า `first_response_minutes` ต่อ channel จาก config

**ไฟล์ที่แก้:** `apps/omnichat-service/src/messages/messages.service.ts`

```typescript
// เดิม (hardcode)
sla_due_at: new Date(messageTimestamp.getTime() + SLA_DURATION_MS)

// ใหม่ (อ่านจาก config)
const config = await slaConfigService.getConfig(tenantId, channelType)
sla_due_at: calculateSlaDueAt(messageTimestamp, config, bhSchedule)
sla_status: 'active'
```

---

### Task 2.3 — Function: `calculate_sla_due_at` โหมด 24/7
**ทำอะไร:** extract logic คำนวณ deadline ออกมาเป็น pure function แยกต่างหาก  
**ทำไม:** ปัจจุบัน inline อยู่ใน service — ต้อง testable แยกและ reuse ได้

```typescript
// 24/7: sla_due_at = inbound_at + target_minutes
calculateSlaDueAt(inboundAt, targetMinutes) → Date
```

---

### Task 2.4 — Function: `next_bh_open_at(timestamp, bh_schedule, timezone)`
**ทำอะไร:** pure function รับเวลาที่ message เข้า → คืน timestamp ที่ BH จะเปิดครั้งถัดไป  
**ทำไม:** BH mode ต้องการ function นี้เป็น building block — ต้องถูกต้องทุก edge case

**Location:** `apps/omnichat-service/src/sla/utils/bh-calculator.ts` (ใหม่)

---

### Task 2.5 — Function: `calculate_sla_due_at` โหมด BH-aware
**ทำอะไร:** คำนวณ deadline โดย skip เวลานอก Business Hours โดยใช้ `next_bh_open_at`  
**ทำไม:** ต้องรองรับ 2 mode — ปัจจุบันมีแค่ 24/7

---

### Task 2.6 🔧 — แก้ Agent reply hook ให้เซ็ต status = `met` แทนการ clear null
**ทำอะไร:** แก้ `messages.service.ts` ส่วนที่ตอนนี้ทำ `sla_due_at: null` → เปลี่ยนเป็น set `sla_status = 'met'` + `sla_met_at = now()`  
**ทำไม:** พอ clear เป็น null แล้วไม่รู้ว่า met หรือ disabled — ต้องมี status ชัดเจน

**ไฟล์ที่แก้:** `apps/omnichat-service/src/messages/messages.service.ts`

```typescript
// เดิม
sla_due_at: null,
waiting_since_at: null,

// ใหม่
sla_status: 'met',
sla_met_at: new Date(),
// sla_due_at คงไว้ — เก็บเป็น history ว่า deadline คืออะไร
```

---

### Task 2.7 🔧 — Logic: Follow-up cycle (met → new inbound → active ใหม่)
**ทำอะไร:** แก้ inbound hook — ถ้า `sla_status = 'met'` และลูกค้าทักใหม่ → recalculate `sla_due_at` และ reset เป็น `active`  
**ทำไม:** ปัจจุบัน inbound hook มี guard `where: { waiting_since_at: null }` — แปลว่า met แล้วลูกค้าทักใหม่ จะไม่เซ็ต SLA ใหม่

**ไฟล์ที่แก้:** `apps/omnichat-service/src/messages/messages.service.ts`

---

### Task 2.8 🔧 — อัปเดต `GET /conversations/:id` response รวม SLA fields ใหม่
**ทำอะไร:** เพิ่ม `sla_status`, `remaining_seconds`, `sla_bh_aware` ใน response ของ conversation endpoint  
**ทำไม:** `sla_due_at` ส่งมาแล้ว แต่ frontend ต้องการ computed `remaining_seconds` และ `sla_status` string

**ไฟล์ที่แก้:** `apps/omnichat-service/src/conversations/conversations.service.ts`

---

### Task 2.9 — Unit tests: `next_bh_open_at` ทุก edge case
**ทำอะไร:** เขียน test ครอบทุก scenario — ใน BH, หลัง BH, วันหยุด, boundary 09:00/18:00, timezone ≠ UTC  
**ทำไม:** function นี้ซับซ้อน ถ้าผิดกระทบ sla_due_at ทุก conversation ที่ใช้ BH mode

---

### Task 2.10 — Unit tests: `calculate_sla_due_at` ทั้ง 2 mode
**ทำอะไร:** test การคำนวณ deadline — 24/7 กรณีทั่วไป + BH-aware ทุก case  
**ทำไม:** ค่า `sla_due_at` ผิด = sort ผิด, breach detect ผิด, display ผิด

---

## SLA-03 — Timer Display in Inbox (5 SP)

> **เป้าหมาย:** แสดง SLA badge ใน conversation list และ Overdue filter pill — backend API รองรับแล้วบางส่วน แต่ UI ยังไม่มี

---

### Task 3.1 — Timer badge component ใน ConversationItem
**ทำอะไร:** เพิ่ม SLA badge เข้าไปใน `conversation-item.tsx` ที่มีอยู่แล้ว — แสดง remaining time + สีตาม sla_status  
**ทำไม:** component มีอยู่แล้วแต่ไม่แสดง SLA เลย — `sla_due_at` ถูกส่งมาจาก API แล้วแต่ไม่ถูก render

**ไฟล์ที่แก้:** `apps/workspace-admin/src/app/(main)/dashboard/chats/_components/conversation-list/conversation-item.tsx`

| State | สี | แสดง |
|-------|-----|------|
| active | เขียว | `"8h 23m"` หรือ `"45m"` |
| due_soon | เหลือง | `"14m"` |
| breached | แดง | `"Overdue +14m"` |
| met / disabled | ไม่แสดง | ซ่อน badge |

---

### Task 3.2 — Timer format logic (util function)
**ทำอะไร:** แปลง `remaining_seconds` จาก API → human-readable string  
**ทำไม:** backend ส่ง seconds มา frontend ต้องแปลงก่อนแสดง

```typescript
// > 3600 sec → "8h 23m"
// ≤ 3600 sec → "45m"
// breached  → "Overdue +14m" (คำนวณ NOW() - sla_due_at)
formatSlaTimer(remainingSeconds: number, slaDueAt: Date): string
```

---

### Task 3.3 — Overdue filter pill ใน inbox filter bar
**ทำอะไร:** เพิ่ม pill "Overdue" ใน filter bar ของ inbox  
**ทำไม:** `is_overdue` filter มีอยู่แล้วใน API (`conversations.service.ts`) แต่ UI ยังไม่มี pill ให้กด

**ไฟล์ที่แก้:** `apps/workspace-admin/src/app/(main)/dashboard/chats/_components/conversation-list/conversation-list.tsx`

**API param:** ส่ง `is_overdue=true` เมื่อกด pill — backend รองรับแล้ว

---

### Task 3.4 🔧 — อัปเดต Conversations API type ให้รวม SLA fields ใหม่
**ทำอะไร:** เพิ่ม `sla_status` และ `remaining_seconds` ใน TypeScript type ของ frontend  
**ทำไม:** `sla_due_at` อยู่ใน type แล้ว (`omnichat.ts`) แต่ต้องเพิ่ม field ใหม่จาก Task 2.8

**ไฟล์ที่แก้:** `apps/workspace-admin/src/types/omnichat.ts`

---

### Task 3.5 — Auto-refresh timer ทุก 30 วินาที
**ทำอะไร:** ตั้ง interval refetch SLA data สำหรับ conversations ที่มี active SLA ใน viewport  
**ทำไม:** timer ต้องนับต่อเรื่อยๆ ไม่งั้นตัวเลขจะ stale จนกว่าจะ reload หน้า

**Note:** ไม่ poll ทุก conversation — เฉพาะที่มี `sla_status` = active หรือ due_soon

---

## SLA-04 — Breach Detection & Auto-tag (5 SP)

> **เป้าหมาย:** background job detect breach + system tag `sla_met`/`sla_breached` ที่ลบไม่ได้

---

### Task 4.1 — DB migration: `conversation_tags` table
**ทำอะไร:** สร้างตารางเก็บ tag ของ conversation รองรับทั้ง user tag และ system tag  
**ทำไม:** ปัจจุบันไม่มี tagging system ใน omnichat-service เลย

```sql
tag_id          UUID PRIMARY KEY
conversation_id UUID NOT NULL
tenant_id       UUID NOT NULL
is_system       BOOLEAN DEFAULT false
tag_name        VARCHAR NOT NULL
created_at      TIMESTAMP WITH TIME ZONE
-- UNIQUE (conversation_id, tag_name) เพื่อ idempotency
```

---

### Task 4.2 — DB migration: `conversation_sla_events` table
**ทำอะไร:** สร้างตาราง audit trail บันทึกทุก SLA cycle — met / breached แยกต่อ round  
**ทำไม:** conversation เดียวมีได้หลาย cycle — ต้องเก็บ history แยกทุก cycle เพื่อ analytics

```sql
id              UUID PRIMARY KEY
conversation_id UUID NOT NULL
tenant_id       UUID NOT NULL
cycle_number    INT           -- 1, 2, 3...
event_type      VARCHAR       -- 'met' | 'breached'
inbound_at      TIMESTAMP
sla_due_at      TIMESTAMP
resolved_at     TIMESTAMP
response_time_sec INT         -- เฉพาะ met
created_at      TIMESTAMP WITH TIME ZONE
```

---

### Task 4.3 — Background job: Breach detection scan (ทุก 1 นาที)
**ทำอะไร:** BullMQ worker วิ่งทุก 1 นาที scan conversations ที่เลย deadline  
**ทำไม:** ไม่มี breach detection อยู่เลย — ตอนนี้ `sla_due_at` แค่เก็บ timestamp แต่ไม่มีใครตรวจ

**Infra:** ใช้ BullMQ ที่มีอยู่แล้วใน `omnichat-gateway`

**Query ที่ job ทำ:**
```sql
WHERE sla_due_at <= NOW()
  AND sla_status IN ('active', 'due_soon')
  AND tenant_id = ...
-- ต้องมี INDEX บน (sla_due_at, sla_status) — มีอยู่แล้วบางส่วน
```

**สิ่งที่ job ทำ:** เปลี่ยน `sla_status = 'breached'` → เพิ่ม tag `sla_breached` → บันทึก event → fire breach event (→ epic 2.8 notification)

---

### Task 4.4 — Logic: Idempotent tag insert
**ทำอะไร:** insert tag แบบ safe ไม่ duplicate ถ้า job run ซ้ำ  
**ทำไม:** ถ้า job crash แล้ว re-run ต้องไม่สร้าง tag ซ้ำ

```sql
INSERT INTO conversation_tags (...)
ON CONFLICT (conversation_id, tag_name) DO NOTHING
```

---

### Task 4.5 — Trigger: `sla_met` tag real-time จาก agent reply hook
**ทำอะไร:** ต่อจาก Task 2.6 (agent reply) — เมื่อเซ็ต `sla_status = 'met'` ให้เพิ่ม tag `sla_met` ทันที พร้อมบันทึก event  
**ทำไม:** `sla_met` ต้องเกิด real-time ไม่รอ job — agent ตอบแล้ว tag ต้องปรากฏเดี๋ยวนี้

**บันทึก:** `response_time_sec = sla_met_at - waiting_since_at` ลง `conversation_sla_events`

---

### Task 4.6 — API protection: DELETE system tag → 403
**ทำอะไร:** ใส่ guard ใน tag delete endpoint — `is_system = true` → reject ทันที ทุก role  
**ทำไม:** system tag คือ audit trail ถาวร — Admin ก็ลบไม่ได้

```typescript
if (tag.is_system) {
  throw new ForbiddenException('system tag ไม่สามารถลบได้')
}
```

---

### Task 4.7 — UI: System tag visual (lock icon + ไม่มี delete button)
**ทำอะไร:** แสดง system tag ด้วย lock icon และซ่อน delete button ออกจาก DOM  
**ทำไม:** user ต้องรู้ก่อนจะพยายามลบว่า tag นี้พิเศษ — ไม่ใช่ disable ปุ่ม แต่ซ่อนออกไปเลย

---

### Task 4.8 — Search: `sla_breached`/`sla_met` searchable ใน inbox
**ทำอะไร:** ให้ search bar ใน inbox ค้นหา conversations ด้วยชื่อ system tag ได้  
**ทำไม:** Supervisor ต้องการ pull รายการ breach ทั้งหมดผ่าน search

---

## Summary

| Story | Task ใหม่ | Task แก้ 🔧 | SP |
|-------|-----------|----------|----|
| SLA-01 Config UI | 7 | 1 | 8 |
| SLA-02 Timer Engine | 5 | 5 | 13 |
| SLA-03 Display | 4 | 1 | 5 |
| SLA-04 Breach+Tag | 8 | 0 | 5 |
| **รวม** | **24** | **7** | **31 SP** |

---

## Dependency ระหว่าง Task

```
[1.1] sla_configs table (migration)
    → [1.2] GET /sla/config
    → [1.3] PATCH /sla/config
    → [1.4–1.7] UI (ต้องมี API ก่อน)

[2.1] migration เพิ่ม sla_status, sla_met_at, sla_bh_aware
    → [2.2] แก้ inbound hook อ่านจาก config  ← ต้องมี [1.1] ก่อน
    → [2.3] function calculate 24/7
    → [2.4] function next_bh_open_at
        → [2.5] function calculate BH-aware
    → [2.6] แก้ agent reply hook → sla_status='met'
        → [4.5] sla_met tag real-time
    → [2.7] แก้ follow-up cycle logic
    → [2.8] update API response
        → [3.1–3.5] ทุก task SLA-03 (frontend ต้องการ API)
        -- sort sla_due_soonest มีอยู่แล้ว — ไม่ต้องทำ

[4.1] conversation_tags table
[4.2] conversation_sla_events table
    → [4.3] breach detection job ← ต้องมี [2.1] ด้วย
        → [4.4] idempotent insert
    → [4.6] API delete protection
    → [4.7] UI lock icon

[2.9–2.10] unit tests (ทำได้พร้อมกับ 2.3–2.5)
```

---

## ไฟล์หลักที่ต้องแก้ (จาก repo จริง)

| ไฟล์ | แก้เพราะ |
|------|----------|
| `apps/omnichat-service/src/messages/messages.service.ts` | Task 2.2, 2.6, 2.7 — แก้ hook |
| `apps/omnichat-service/src/conversations/conversations.service.ts` | Task 2.8 — เพิ่ม SLA fields ใน response |
| `apps/omnichat-service/prisma/schema.prisma` | Task 2.1, 4.1, 4.2 — migration ใหม่ |
| `packages/shared/src/constants/common.constants.ts` | ลบ/deprecate `SLA_DURATION_MS` |
| `apps/workspace-admin/src/app/(main)/dashboard/chats/_components/conversation-list/conversation-item.tsx` | Task 3.1 — เพิ่ม badge |
| `apps/workspace-admin/src/app/(main)/dashboard/chats/_components/conversation-list/conversation-list.tsx` | Task 3.3 — เพิ่ม Overdue pill |
| `apps/workspace-admin/src/types/omnichat.ts` | Task 3.4 — เพิ่ม SLA fields ใน type |
