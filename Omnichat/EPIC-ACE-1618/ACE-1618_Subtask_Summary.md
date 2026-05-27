# EPIC-ACE-1618: SLA Subtask Summary (Actual ClickUp)

> Actual ClickUp subtasks per story — synced from ClickUp Sprint 6 (5/18–5/29)

---

## ACE-1640 — STORY-SLA-01: SLA Configuration UI (8 SP) — In Progress

| ClickUp ID | Subtask | Type | Assignee | Status |
|---|---|---|---|---|
| [ACE-2219](https://app.clickup.com/t/86d315hdt) | FE — Implement Global SLA Toggle | Frontend | Tanawin (Toy) | In Progress |
| [ACE-2220](https://app.clickup.com/t/86d315hjy) | BE — Create SLA Config Schema & Migration | Backend | Siraphob | Reviewing |
| [ACE-2221](https://app.clickup.com/t/86d315j6t) | BE — SLA Config APIs | Backend | Siraphob | In Progress |

**Notes:**
- ACE-2220: `sla_configs` table migration — `workspace_id`, `channel_type`, `enabled`, `first_response_minutes`, `due_soon_minutes`, `bh_aware`
- ACE-2221: `GET /sla/config` + `PATCH /sla/config` + RBAC guard (`config_sla` permission)
- ACE-2219: Global toggle, due soon threshold input, BH toggle + preview, per-channel rows, warning logic (FB/IG > 24h), form validation

---

## ACE-1641 — STORY-SLA-02: SLA Timer Engine (13 SP) — To Do

| ClickUp ID | Subtask | Type | Assignee | Status |
|---|---|---|---|---|
| [ACE-1663](https://app.clickup.com/t/86d2q9tkn) | BE — Add SLA fields to conversations (2 SP) | Backend | griangsak | To Do |
| [ACE-2223](https://app.clickup.com/t/86d315md5) | BE — Timer start logic | Backend | Tanawin (Toy) | To Do |
| [ACE-2224](https://app.clickup.com/t/86d315p3v) | BE — Timer stop logic | Backend | griangsak | To Do |
| [ACE-2226](https://app.clickup.com/t/86d315pux) | BE — Implement Business Hours SLA Calculation | Backend | griangsak | To Do |
| [ACE-2227](https://app.clickup.com/t/86d315q34) | BE — Implement SLA Follow-up Cycle Logic | Backend | griangsak | To Do |
| [ACE-2235](https://app.clickup.com/t/86d315xjm) | BE — Implement Websocket | Backend | wetchayan | To Do |

**Notes:**
- ACE-1663: migration เพิ่ม `sla_status`, `sla_met_at`, `sla_bh_aware` บน `conversations` table (`sla_due_at` มีแล้ว)
- ACE-2223: แก้ inbound hook ใน `messages.service.ts` — อ่าน `first_response_minutes` จาก `sla_configs` แทน `SLA_DURATION_MS` hardcode; เซ็ต `sla_status = 'active'`
- ACE-2224: แก้ agent reply hook → `sla_status = 'met'` + `sla_met_at = now()`; internal note exclusion; `due_soon` threshold check
- ACE-2226: pure functions `calculate_sla_due_at` (BH-aware) + `next_bh_open_at(timestamp, bh_schedule, timezone)`; location: `src/sla/utils/bh-calculator.ts`
- ACE-2227: Follow-up cycle — `sla_status = 'met'` + new inbound → recalculate + reset `active`; expose `sla_status`, `remaining_seconds`, `sla_bh_aware` ใน `GET /conversations/:id`
- ACE-2235: WebSocket push เมื่อ SLA state เปลี่ยน (real-time update ฝั่ง frontend)

---

## ACE-1642 — STORY-SLA-03: Timer Display in Inbox (5 SP) — To Do

| ClickUp ID | Subtask | Type | Assignee | Status |
|---|---|---|---|---|
| [ACE-2228](https://app.clickup.com/t/86d315qfz) | FE — Add SLA Timer Badge in Conversation List | Frontend | Siraphob | To Do |
| [ACE-2229](https://app.clickup.com/t/86d315r23) | FE — Implement Overdue Filter Pill | Frontend | Siraphob | To Do |
| [ACE-2232](https://app.clickup.com/t/86d315t7u) | FE — Implement sort by overdue | Frontend | Tanawin (Toy) | To Do |
| [ACE-2230](https://app.clickup.com/t/86d315rz8) | BE — Add Inbox SLA Filter Support | Backend | Peerapat | To Do |
| [ACE-2231](https://app.clickup.com/t/86d315t4b) | BE — Add SLA Sorting Support | Backend | Peerapat | To Do |

**Notes:**
- ACE-2228: badge ใน `conversation-item.tsx` — active=เขียว/due_soon=เหลือง/breached=แดง; format `Xh Ym` / `Xm` / `Overdue +Xm`; met+disabled ไม่แสดง
- ACE-2229: pill "Overdue" ใน filter bar → filter `sla_status=breached`; sort by elapsed overdue; highlighted เมื่อ active
- ACE-2232: "SLA due soonest" sort → `sla_due_at ASC`; breached convs ขึ้นก่อน
- ACE-2230: `GET /conversations` รองรับ `?sla_status=breached` filter param
- ACE-2231: `GET /conversations` รองรับ `?sort=sla_due_at_asc` sort param

---

## ACE-1643 — STORY-SLA-04: Breach Detection & Auto-tag (5 SP) — To Do

| ClickUp ID | Subtask | Type | Assignee | Status |
|---|---|---|---|---|
| [ACE-2233](https://app.clickup.com/t/86d315tu3) | BE — Create SLA Event & System Tag Schema | Backend | Peerapat | To Do |
| [ACE-2234](https://app.clickup.com/t/86d315u2q) | BE — Create Breach Detection job | Backend | Peerapat | To Do |

**Notes:**
- ACE-2233: migration สร้าง `conversation_tags` (tag_id, conversation_id, is_system, tag_name) + `conversation_sla_events` (cycle_number, event_type, inbound_at, sla_due_at, resolved_at, response_time_sec); DELETE protection `is_system=true` → 403
- ACE-2234: BullMQ job ทุก 1 นาที; scan `WHERE sla_due_at <= NOW() AND sla_status IN ('active','due_soon')`; เปลี่ยน status → breached; `INSERT ... ON CONFLICT DO NOTHING` (idempotent); `sla_met` tag real-time จาก agent reply hook; fire breach event (→ epic 2.8)

---

## Summary

| Story | Status | Subtasks | SP |
|-------|--------|----------|----|
| ACE-1640 SLA Config UI | In Progress | 3 | 8 |
| ACE-1641 Timer Engine | To Do | 6 | 13 |
| ACE-1642 Timer Display | To Do | 5 | 5 |
| ACE-1643 Breach + Tag | To Do | 2 | 5 |
| **Total** | | **16** | **31 SP** |

---

## Dependency Order

```
ACE-1640 (Config UI + sla_configs table)
    └─→ ACE-1641 (Timer Engine reads config)
            └─→ ACE-1642 (Display consumes API)
            └─→ ACE-1643 (Breach job reads sla_status)
```

**Repo context:** ดู `story-task-breakdown.md` สำหรับ task-level detail + ไฟล์ที่ต้องแก้
