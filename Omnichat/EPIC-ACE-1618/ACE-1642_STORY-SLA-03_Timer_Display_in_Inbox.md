# STORY-SLA-03: Timer Display in Inbox

**ClickUp ID:** ACE-1642
**Status:** To Do
**Sprint:** Sprint 6 (5/18–5/29)
**Points:** 5 SP
**Parent Epic:** ACE-1618
**Assignees:** Peerapat Pongnipakorn, Tanawin (Toy), Siraphob Reanmanorom
**URL:** https://app.clickup.com/t/86d2pte3q

---

## User Story

As a CS Agent or Supervisor
I want to see SLA timers clearly in the conversation list and detail view, and filter conversations by overdue status
so that I can immediately understand which conversations need urgent attention without manual calculation.

---

## Detail / Description

Story นี้ build SLA timer display ทั้งหมดที่ agent เห็นใน inbox — consume `sla_status` และ `sla_due_at` จาก API ที่ SLA-02 build

**ไม่มี SLA logic ใน frontend** — ทุก state มาจาก backend

### Timer Display Formats

| สถานการณ์ | Format | ตัวอย่าง |
|----------|--------|---------|
| เหลือ > 1 ชั่วโมง | `"Xh Ym"` | `"8h 23m"` |
| เหลือ < 1 ชั่วโมง | `"Xm"` | `"23m"` |
| Breached | `"Overdue +Xm"` หรือ `"+Xh Ym"` | `"Overdue +14m"` หรือ `"Overdue +2h 5m"` |
| Met | ไม่แสดง timer | (ไม่มี badge) |
| Disabled | ไม่แสดง timer | (ไม่มี badge) |

### Overdue Filter Pill vs Due Soon Threshold

| Feature | รายละเอียด |
|---------|-----------|
| Overdue filter pill ใน inbox | อยู่ตลอด (ไม่ขึ้นกับ threshold) |
| Due soon threshold | ตัวเลขที่ตั้งใน SLA-01 → กระทบแค่การเปลี่ยนสีของ timer badge (เขียว→เหลือง) → กระทบ due_soon notification → **ไม่กระทบ Overdue pill** |

### Scope

- Timer badge ใน conversation list: แสดง remaining time หรือ "Overdue +Xm"
- 3 visual states: `active`=เขียว, `due_soon`=เหลือง, `breached`=แดง
- `met`/`disabled`: ไม่แสดง timer เลย
- Overdue filter pill: แสดงตลอดเวลาเมื่อ SLA enabled
- Overdue filter: กรอง `sla_status = breached` + sort by elapsed time (เกิน deadline นานที่สุดขึ้นก่อน)
- Auto-refresh: timer values อัปเดตทุก 30 วินาทีโดยไม่ต้อง page reload
- Sort by "SLA due soonest" อ้างอิง `sla_due_at` field จาก SLA-02

---

## Acceptance Criteria

**AC1: Timer badge appears in conversation list for active and due_soon SLA**
- Given a conversation has `sla_status = active` or `due_soon`
- When the conversation list renders
- Then a timer badge appears on the conversation row showing remaining time
- Format: `> 1h = Xh Ym`, `< 1h = Xm`

**AC2: Timer badge shows correct color per sla_status**
- `sla_status = active` → badge เขียว
- `sla_status = due_soon` → badge เหลือง/amber
- `sla_status = breached` → badge แดง, แสดง "Overdue +Xm" หรือ "Overdue +Xh Ym" (เพิ่มทุกนาที)

**AC3: No timer is shown for met or disabled conversations**
- `sla_status = met` → ไม่แสดง badge หรือ countdown ทั้งใน list และ detail
- `sla_status = disabled` → ไม่แสดง badge หรือ countdown

**AC4: "Overdue" filter pill appears when SLA is enabled**
- Overdue pill แสดงตลอดเมื่อ SLA enabled บน channel ใดก็ได้

**AC5: "Overdue" filter pill shows only breached conversations**
- Given Overdue pill is visible
- When agent clicks the Overdue pill
- Then only conversations with `sla_status = breached` are shown
- And sorted by elapsed overdue time with longest overdue first
- And the pill is highlighted to indicate active filter state
- When agent clicks the pill again → filter is cleared and all conversations return

**AC6: "Overdue" pill is separate from and does not require "due soon threshold" config**
- Given `due_soon_threshold` has NOT been configured in SLA settings
- When SLA is enabled on any channel
- Then the Overdue pill still appears in the inbox
- And conversations that breach their deadline show correctly
- The `due_soon_threshold` only affects the color change to amber, it does not control the Overdue pill

**AC7: Timer values refresh without page reload**
- Given an agent has the inbox open
- When 30 seconds pass
- Then timer values update to reflect current remaining or elapsed time
- And visual state transitions automatically if a threshold is crossed (e.g. green → amber without reload)

**AC8: "Sort by SLA due soonest" sorts by sla_due_at ascending**
- Given multiple conversations have active SLA timers
- When agent selects "SLA due soonest" from sort dropdown
- Then conversations sorted by `sla_due_at` ascending (closest deadline first)
- And breached conversations appear at the top

---

## UI/UX Notes

- Timer badge ใน list: ขนาดเล็ก เขียว/เหลือง/แดง
- Overdue pill: อยู่ใน filter bar เดียวกับ "all", "my open", "unassigned" ฯลฯ
- Overdue elapsed time แสดงเพิ่มทุก 1 นาที — ไม่ต้องแม่นยำถึงวินาที
- ถ้า conversation อยู่ใน Overdue filter แล้ว agent ตอบ → conversation หายออกจาก Overdue list ทันที (refresh)

---

## Technical Notes

### Dependencies
- **SLA-02** — `sla_status`, `sla_due_at`, `remaining_seconds` ต้องอยู่ใน `GET /conversations` API
- **SLA-01** — `due_soon_threshold` config ต้องอ่านได้เพื่อ determine เมื่อจะเปลี่ยนสี
- Inbox API ต้องรองรับ filter parameter `sla_status=breached`
- Inbox API ต้องรองรับ sort parameter `sla_due_at_asc`

### Special Focus

- ใช้ `sla_due_at` จาก API เพื่อ compute display time ฝั่ง client แบบ countdown — ไม่ต้อง poll บ่อย
- Auto-refresh: `setInterval` ทุก 30s fetch updated `remaining_seconds` สำหรับ conversations ที่เปิดอยู่
- Overdue elapsed time: เก็บ `sla_due_at` ฝั่ง client แล้วคำนวณ `NOW() - sla_due_at` ทุก 30s
- Timezone: `sla_due_at` เป็น UTC — convert ด้วย workspace timezone ตอน display
- Performance: ไม่ต้อง poll ทุก conversation — poll เฉพาะ conversations ที่มี active SLA ใน viewport

---

## QA / Test Considerations

### Primary Flows
- Active conv → green badge → due_soon → amber → breach → red "Overdue +Xm"
- Met conv → ไม่เห็น badge ใน list หรือ detail
- SLA enabled on Shopee → Overdue pill ปรากฏ (แม้ไม่มี threshold)
- Click Overdue pill → เห็นเฉพาะ breached convs → sort by longest overdue
- Agent reply → conv หายออกจาก Overdue list

### Edge Cases
- `due_soon_threshold` ไม่ได้ตั้ง → Overdue pill ยังปรากฏ
- SLA disabled ทุก channel → Overdue pill ไม่ปรากฏ
- Sort by SLA due soonest + Overdue pill → breached convs ขึ้นก่อน
- Timezone ต่างกัน → timer แสดงถูกต้องตาม workspace timezone

### Business-Critical Must Not Break
- Overdue pill ต้องปรากฏเมื่อ SLA enabled โดยไม่ต้อง config threshold
- Timer display ต้องไม่แสดงค่าผิดเพราะ timezone
- Agent ตอบแล้ว → SLA state update ต้องสะท้อนใน inbox ไม่เกิน next 30s refresh

### Test Types
- UI tests: timer badge 3 states, met/disabled no badge
- Filter tests: Overdue pill toggle
- Sort tests: SLA due soonest
- Integration: timer transitions without page reload

---

## Sequence Diagrams

See [ACE-1642_STORY-SLA-03_Sequence_Diagrams.md](ACE-1642_STORY-SLA-03_Sequence_Diagrams.md)

---

## Subtasks

| Task | Assignee | Status |
|---|---|---|
| [ACE-2228](https://app.clickup.com/t/86d315qfz) FE — Add SLA Timer Badge in Conversation List | Siraphob | To Do |
| [ACE-2229](https://app.clickup.com/t/86d315r23) FE — Implement Overdue Filter Pill | Siraphob | To Do |
| [ACE-2232](https://app.clickup.com/t/86d315t7u) FE — Implement sort by overdue | Tanawin (Toy) | To Do |
| [ACE-2230](https://app.clickup.com/t/86d315rz8) BE — Add Inbox SLA Filter Support | Peerapat | To Do |
| [ACE-2231](https://app.clickup.com/t/86d315t4b) BE — Add SLA Sorting Support | Peerapat | To Do |
