# EPIC-ACE-1618: SLA Subtask Summary (ClickUp-ready)

> Subtask names per story — aligned to repo structure at `apps/omnichat-service/` and `apps/workspace-admin/`

---

## ACE-1640 — STORY-SLA-01: SLA Configuration UI (8 SP)

| # | Subtask | Type |
|---|---------|------|
| 1.1 | SLA Config API & DB Schema | Backend |
| 1.2 | Global Settings Section UI | Frontend |
| 1.3 | Channel SLA Targets UI | Frontend |
| 1.4 | Warning Logic (FB/IG + BH missing) | Frontend |
| 1.5 | Form Validation & Save Flow | Frontend |

**Notes:**
- 1.1: `sla_configs` table migration + `GET /sla/config` + `PATCH /sla/config` + RBAC guard (`config_sla` permission มีอยู่แล้วใน `rbac.types.ts`)
- 1.2: Global toggle, due soon threshold input, BH toggle + preview fetch จาก SETTINGS-02
- 1.3: Per-channel rows — toggle, number input, unit dropdown (minutes/hours), reset button, info tooltip
- 1.4: FB/IG target > 1440min → warning banner; BH toggle ON + ไม่มี BH data → warning + link
- 1.5: Input validation > 0, save-all button, API error states

---

## ACE-1641 — STORY-SLA-02: SLA Timer Engine (13 SP)

| # | Subtask | Type |
|---|---------|------|
| 2.1 | DB Schema & Migration | Backend |
| 2.2 | Timer Start Logic (inbound hook) | Backend |
| 2.3 | Business Hours Calculation Functions | Backend |
| 2.4 | Timer Stop & Status Transitions | Backend |
| 2.5 | Follow-up Cycle & API Response | Backend |

**Notes:**
- 2.1: เพิ่ม `sla_status`, `sla_met_at`, `sla_bh_aware` ใน `conversations` table (`sla_due_at` + `waiting_since_at` มีแล้ว)
- 2.2: แก้ `messages.service.ts` inbound hook — อ่าน `first_response_minutes` จาก `sla_configs` แทน `SLA_DURATION_MS` hardcode; เซ็ต `sla_status = 'active'`
- 2.3: Pure functions `calculate_sla_due_at` (24/7 + BH-aware) + `next_bh_open_at(timestamp, bh_schedule, timezone)`; location: `src/sla/utils/bh-calculator.ts`
- 2.4: แก้ agent reply hook → `sla_status = 'met'` + `sla_met_at = now()`; internal note exclusion; `due_soon` threshold check
- 2.5: Follow-up cycle — `sla_status = 'met'` + new inbound → recalculate + reset `active`; expose `sla_status`, `remaining_seconds`, `sla_bh_aware` ใน `GET /conversations/:id`

---

## ACE-1642 — STORY-SLA-03: Timer Display in Inbox (5 SP)

| # | Subtask | Type |
|---|---------|------|
| 3.1 | Timer Badge Component | Frontend |
| 3.2 | Overdue Filter Pill | Frontend |
| 3.3 | Auto-refresh & SLA Sort | Frontend |

**Notes:**
- 3.1: เพิ่ม badge ใน `conversation-item.tsx` — สี active=เขียว / due_soon=เหลือง / breached=แดง; format: `Xh Ym` / `Xm` / `Overdue +Xm`; met + disabled ไม่แสดง; เพิ่ม `sla_status` + `remaining_seconds` ใน `omnichat.ts` types
- 3.2: Pill "Overdue" ใน filter bar → ส่ง `is_overdue=true` (backend รองรับแล้ว); sort by longest overdue first; `sla_status=breached` only
- 3.3: `setInterval` 30s refetch สำหรับ conversations ที่มี active SLA; "SLA due soonest" sort by `sla_due_at ASC` (backend รองรับแล้ว)

---

## ACE-1643 — STORY-SLA-04: Breach Detection & Auto-tag (5 SP)

| # | Subtask | Type |
|---|---------|------|
| 4.1 | Breach Detection Job | Backend |
| 4.2 | System Tag Creation (sla_met + sla_breached) | Backend |
| 4.3 | System Tag Protection | Backend |
| 4.4 | SLA Events Table & Analytics | Backend |

**Notes:**
- 4.1: BullMQ worker ทุก 1 นาที; scan `WHERE sla_due_at <= NOW() AND sla_status IN ('active','due_soon')`; เปลี่ยน `sla_status = 'breached'`; fire breach event (→ epic 2.8 notification)
- 4.2: `sla_met` real-time จาก agent reply hook (Task 2.4); `sla_breached` จาก breach job; `INSERT ... ON CONFLICT DO NOTHING` (idempotent)
- 4.3: `is_system = true` flag บน tag; DELETE → 403 ทุก role (`throw new ForbiddenException('system tag ไม่สามารถลบได้')`); UI ซ่อน delete button ออกจาก DOM + lock icon
- 4.4: `conversation_sla_events` table migration — `cycle_number`, `event_type` (met/breached), `response_time_sec`; searchable ใน inbox search

---

## Summary

| Story | Subtasks | SP |
|-------|----------|----|
| ACE-1640 SLA Config UI | 5 | 8 |
| ACE-1641 Timer Engine | 5 | 13 |
| ACE-1642 Timer Display | 3 | 5 |
| ACE-1643 Breach + Tag | 4 | 5 |
| **Total** | **17** | **31 SP** |

---

## Dependency Order

```
ACE-1640 (Config UI + sla_configs table)
    └─→ ACE-1641 (Timer Engine reads config)
            └─→ ACE-1642 (Display consumes API)
            └─→ ACE-1643 (Breach job reads sla_status)
```

**Repo context:** ดู `story-task-breakdown.md` สำหรับ task-level detail + ไฟล์ที่ต้องแก้
