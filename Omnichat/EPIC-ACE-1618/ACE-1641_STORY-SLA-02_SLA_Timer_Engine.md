# STORY-SLA-02: SLA Timer Engine

**ClickUp ID:** ACE-1641
**Status:** To Do
**Sprint:** Sprint 6 (5/18–5/29)
**Points:** 13 SP
**Parent Epic:** ACE-1618
**Assignees:** griangsak, Tanawin (Toy), wetchayan
**URL:** https://app.clickup.com/t/86d2pte0x

---

## User Story

As a Backend Engineer
I want a reliable server-side SLA timer that starts, tracks state transitions, stops accurately and calculates deadlines correctly in both 24/7 mode and Business Hours mode
so that SLA display (SLA-03) and breach detection (SLA-04) have correct and consistent data to work with and agents are not unfairly penalised for messages that arrive outside working hours.

---

## Detail / Description

Story นี้เป็น **pure backend story** ไม่มี UI — ผลลัพธ์คือ fields ใหม่บน conversations table และ logic ที่จัดการ state transitions ทั้งหมด

### Timer Start Logic

- Timer เริ่มเมื่อ: SLA enabled บน channel + conversation มี first inbound message จาก customer
- Timer **ไม่เริ่ม**ถ้า: SLA disabled, หรือ conversation เริ่มจาก outbound (agent ทัก customer ก่อน)
- ถ้า customer ส่งหลาย message ก่อนที่ agent จะตอบ → `sla_due_at` ยึดจาก first inbound เท่านั้น

### Timer Stop Logic

- Timer หยุดเมื่อ: agent ส่ง outbound message (reply ถึง customer) ครั้งแรก → status = `met`
- Internal note (บันทึกภายใน ไม่ถึง customer) **ไม่นับ**ว่าเป็น reply → timer ไม่หยุด
- System messages (auto-reply, bot) **ไม่นับ**ว่าเป็น human agent reply ใน SLA v1

### Follow-up Cycle

- เมื่อ status = `met` และ customer ส่งข้อความใหม่ → timer cycle ใหม่เริ่ม
- `sla_due_at` ใหม่ = `new_inbound_at + target_minutes` ของ channel นั้น
- status เปลี่ยนกลับเป็น `active` และนับใหม่

### Status Machine

```
disabled → (SLA enable + inbound message) → active → (เหลือ <= threshold) → due_soon → (deadline ผ่าน) → breached
active หรือ due_soon → (agent reply ก่อน deadline) → met
met → (customer follow-up) → active (new cycle)
```

---

## Business Hours Calculation Logic

ฟังก์ชัน: `calculate_sla_due_at(inbound_at, target_minutes, bh_schedule)`

| กรณี | Logic |
|------|-------|
| `bh_aware = false` | `sla_due_at = inbound_at + target_minutes` (24/7 เหมือนเดิม) |
| `bh_aware = true` — Message เข้าระหว่าง BH | `sla_due_at = inbound_at + target_minutes` (เหมือน 24/7 เพราะอยู่ใน BH อยู่แล้ว) |
| `bh_aware = true` — Message เข้านอก BH (กลางคืน/หลัง BH ปิด) | คำนวณ `next_bh_open_at` → `sla_due_at = next_bh_open_at + target_minutes` |
| `bh_aware = true` — Message เข้าวันที่ BH ปิดทั้งวัน (เช่น วันอาทิตย์) | คำนวณ `next_bh_open_at` = วันทำการถัดไปตอน BH เปิด → `sla_due_at = next_bh_open_at + target_minutes` |
| `bh_aware = true` — ไม่มี BH data (fallback) | `sla_due_at = inbound_at + target_minutes` + Log warning |

### `next_bh_open_at` Helper Function

- รับ timestamp และ `bh_schedule` → return timestamp ของเวลาที่ BH จะเปิดครั้งถัดไป
- ถ้า `inbound_at` อยู่ในช่วง BH อยู่แล้ว → return `inbound_at` (ไม่ต้อง skip)
- ถ้าอยู่หลัง BH ปิดของวันนี้ → return วันถัดไปที่มี BH ตอนเริ่มเปิด
- ถ้าวันนี้ไม่มี BH (เช่น วันอาทิตย์) → วนหาวันถัดไปที่มี BH
- ต้อง handle timezone อย่างถูกต้อง — ใช้ workspace timezone จาก SETTINGS-02

---

## Scope of This Story

- เพิ่ม fields บน `conversations` table: `sla_due_at`, `sla_met_at`, `sla_status`, `sla_first_inbound_at`
- เพิ่ม field: `sla_bh_aware BOOLEAN` (บันทึก mode ที่ใช้ตอน `sla_due_at` คำนวณ)
- Logic: คำนวณ `sla_due_at` เมื่อ first inbound message เข้า
- Logic: เปลี่ยน status → `met` และบันทึก `sla_met_at` เมื่อ agent reply
- Logic: เปลี่ยน status → `due_soon` เมื่อ remaining time <= threshold (on-read หรือ cron)
- Function: `calculate_sla_due_at` รองรับทั้ง 24/7 และ BH mode
- Function: `next_bh_open_at` helper
- API: `GET /conversations/:id` → response รวม `sla_status`, `sla_due_at`, `remaining_seconds`, `sla_bh_aware`

---

## Acceptance Criteria

**AC1: sla_due_at is calculated with 24/7 logic when bh_aware is false**
- Given SLA is enabled for Shopee with 12-hour target and `bh_aware = false`
- When a customer sends the first message at any time
- Then `sla_due_at = first_inbound_at + 720 minutes`
- And `sla_bh_aware = false` is recorded on the conversation

**AC2: sla_due_at is calculated from inbound time when message arrives during Business Hours**
- Given `bh_aware = true`, Business Hours = Mon-Fri 09:00-18:00, target = 1 hour
- When a customer sends a message on Monday at 10:00
- Then `sla_due_at = Monday 11:00` (10:00 + 1h)
- And `sla_bh_aware = true` is recorded

**AC3: sla_due_at is calculated from next BH open time when message arrives outside Business Hours**
- Given `bh_aware = true`, Business Hours = Mon-Fri 09:00-18:00, target = 1 hour
- When a customer sends a message on Friday at 23:00
- Then `next_bh_open_at = Monday 09:00` (เพราะ Sat-Sun ไม่มี BH)
- And `sla_due_at = Monday 10:00` (09:00 + 1h)
- And the agent has until Monday 10:00 to reply, not Friday 00:00

**AC4: sla_due_at skips correctly when message arrives after Business Hours same day**
- Given `bh_aware = true`, Business Hours = Mon-Fri 09:00-18:00, target = 1 hour
- When a customer sends a message on Monday at 19:00
- Then `next_bh_open_at = Tuesday 09:00`
- And `sla_due_at = Tuesday 10:00`

**AC5: sla_due_at falls on next business day when message arrives on a non-working day**
- Given `bh_aware = true`, Business Hours = Mon-Fri 09:00-18:00, target = 2 hours
- When a customer sends a message on Saturday at 14:00
- Then `next_bh_open_at = Monday 09:00`
- And `sla_due_at = Monday 11:00` (09:00 + 2h)

**AC6: sla_bh_aware mode is recorded on the conversation at creation time**
- Given `bh_aware = true` in SLA config
- When `sla_due_at` is calculated for a new conversation
- Then `sla_bh_aware = true` is stored on the conversation
- If the config is later changed to `bh_aware = false` → existing conversations retain original value (no retroactive change)

**AC7: Message arriving inside BH with deadline falling outside BH is pushed to next BH**
- Given `bh_aware = true`, BH = Mon-Fri 09:00-18:00, target = 1 hour
- When a customer sends a message on Monday at 17:59
- Then `remaining_bh_today = 1 minute` (18:00 - 17:59)
- And `remaining_target = 60 - 1 = 59 minutes`
- And `sla_due_at = Tuesday 09:59` (09:00 + 59min)
- And the agent is not expected to reply within the last 1 minute of the working day

**AC8: SLA timer does not start on outbound-first conversations**
- Given an agent initiates a conversation by sending the first message
- When the conversation is created
- Then `sla_due_at = null` and `sla_status = disabled`
- When the customer later replies → `sla_due_at` is calculated from that customer reply using the current `bh_aware` config

**AC9: Multiple inbound messages before agent reply do not reset the timer**
- Given a conversation has `sla_due_at` already set
- When the customer sends additional messages before any agent reply
- Then `sla_due_at` remains unchanged

**AC10: Internal note does not trigger SLA met**
- Given a conversation has `sla_status = active`
- When an agent saves an internal note
- Then `sla_status` remains `active` and `sla_met_at` is not set

**AC11: sla_status changes to met when agent sends first outbound reply**
- Given a conversation has `sla_status = active` or `due_soon`
- When an agent sends an outbound message to the customer
- Then `sla_status = met` and `sla_met_at` is recorded

**AC12: Customer follow-up after met starts a new timer cycle**
- Given `sla_status = met`
- When the customer sends a new message
- Then a new `sla_due_at` is calculated using the **same** `bh_aware` mode as the original
- And `sla_status` resets to `active`

---

## Technical Notes

### Dependencies
- **SLA-01** — `sla_configs` table รวม `bh_aware` field และ `first_response_minutes`
- **SETTINGS-02** — `GET /workspace/business-hours` ต้องพร้อมเพื่อ `next_bh_open_at` ทำงานได้
- Workspace timezone จาก SETTINGS-02 ต้องใช้ตลอด calculation — ห้าม hardcode timezone
- Inbound message event pipeline ต้องส่ง trigger พร้อม timestamp ที่แม่นยำ

### Special Focus

```sql
-- conversations table additions
sla_due_at          TIMESTAMP WITH TIME ZONE
sla_met_at          TIMESTAMP WITH TIME ZONE
sla_status          VARCHAR  -- disabled|active|due_soon|breached|met
sla_first_inbound_at TIMESTAMP WITH TIME ZONE
sla_bh_aware        BOOLEAN DEFAULT false
```

```
next_bh_open_at(timestamp, bh_schedule, timezone) → timestamp
  -- ควรเป็น pure function ที่ test ได้ง่าย

bh_schedule format:
[{ day: "monday", start: "09:00", end: "18:00" }, ...]
```

- ทุก timestamp เก็บเป็น UTC, แปลงเป็น workspace timezone เมื่อ compare กับ BH schedule
- ถ้า `target_minutes` ยาวมากจน `sla_due_at` ข้ามหลายวัน → ยังคำนวณได้ถูกต้องเพราะแค่บวก `target_minutes` จาก `next_bh_open_at`

---

## QA / Test Considerations

### Primary Flows
- `bh_aware=false` + message เข้าตี 3 → `sla_due_at = T+target` (24/7)
- `bh_aware=true` + message เข้าระหว่าง BH → `sla_due_at = T+target`
- `bh_aware=true` + message เข้าใกล้ปิด BH (17:59) → `sla_due_at` = วันถัดไป 09:00+remaining
- `bh_aware=true` + message เข้าหลัง BH ปิด (19:00) → `sla_due_at` = วันถัดไป 09:00+target
- `bh_aware=true` + message เข้าวันเสาร์ → `sla_due_at` = จันทร์ 09:00+target
- Internal note → timer ไม่หยุด
- Customer follow-up หลัง met → new cycle ใช้ `bh_aware` mode เดิม

### Edge Cases
- BH schedule ว่าง (ไม่มีวันไหนเปิดเลย) → fallback 24/7
- Message เข้าตอน 09:00 พอดี (boundary) → ถือว่าอยู่ใน BH
- Message เข้าตอน 18:00 พอดี (boundary) → ถือว่านอก BH (BH ปิดแล้ว)
- `target_minutes = 0` → validation error (SLA-01 handle)
- Workspace timezone ≠ server timezone → ผลลัพธ์ถูกต้อง
- BH config เปลี่ยนระหว่างที่ conversation เปิดอยู่ → `sla_due_at` ไม่เปลี่ยนตาม

### Business-Critical Must Not Break
- `sla_due_at` ต้องแม่นยำทุกกรณี — ค่าผิดกระทบ sort, filter, breach detection
- BH fallback ต้องทำงานถ้าไม่มี BH data — ห้าม crash หรือ skip calculation
- Timezone handling ต้องถูกต้อง — ห้าม off-by-one จาก timezone conversion

### Test Types
- Unit tests: `next_bh_open_at` สำหรับทุก day × time combination
- Unit tests: `calculate_sla_due_at` ทั้ง `bh_aware=true/false`
- Edge case tests: weekend, after-hours, boundary times (09:00, 18:00)
- Timezone tests: messages ข้ามเที่ยงคืน, workspace timezone ≠ UTC
- Fallback tests: `bh_aware=false` → 24/7 fallback
- Integration tests: inbound message → sla fields updated correctly

---

## Subtasks

| Task | Assignee | Status |
|---|---|---|
| [ACE-1663](https://app.clickup.com/t/86d2q9tkn) BE — Add SLA fields to conversations (2 SP) | griangsak | To Do |
| [ACE-2223](https://app.clickup.com/t/86d315md5) BE — Timer start logic | Tanawin (Toy) | To Do |
| [ACE-2224](https://app.clickup.com/t/86d315p3v) BE — Timer stop logic | griangsak | To Do |
| [ACE-2226](https://app.clickup.com/t/86d315pux) BE — Implement Business Hours SLA Calculation | griangsak | To Do |
| [ACE-2227](https://app.clickup.com/t/86d315q34) BE — Implement SLA Follow-up Cycle Logic | griangsak | To Do |
| [ACE-2235](https://app.clickup.com/t/86d315xjm) BE — Implement Websocket | wetchayan | To Do |
