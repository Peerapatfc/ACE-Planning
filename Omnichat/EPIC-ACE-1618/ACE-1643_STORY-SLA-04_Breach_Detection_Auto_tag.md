# STORY-SLA-04: Breach Detection & Auto-tag

**ClickUp ID:** ACE-1643
**Status:** To Do
**Sprint:** Sprint 6 (5/18–5/29)
**Points:** 5 SP
**Parent Epic:** ACE-1618
**Assignees:** Peerapat Pongnipakorn
**URL:** https://app.clickup.com/t/86d2pte6q

---

## User Story

As a Support Team
I want SLA breaches and successes to be automatically detected and tagged on conversations
so that breached conversations are easy to audit, filter, and track without manual effort.

---

## Detail / Description

Story นี้ build **background job** ที่ detect breach และ auto-tag — เป็น **pure backend story** ไม่มี UI
Focus ที่ detection + tagging เท่านั้น (notification เมื่อ breach อยู่ใน epic 2.8)

### Auto-tag Summary

| Tag | เกิดขึ้นตอนไหน | ลักษณะ |
|-----|---------------|--------|
| `sla_met` | agent ส่ง first reply ก่อน `sla_due_at` | system tag, ลบไม่ได้, บันทึก response time |
| `sla_breached` | `sla_due_at <= NOW()` และยังไม่มีใครตอบ | system tag, ลบไม่ได้, คงอยู่แม้ agent ตอบทีหลัง |

### sla_met Tag

- เกิดขึ้น **real-time**: ตอนที่ agent message ถูก save — ไม่ต้องรอ background job
- เก็บ `response_time_seconds = sla_met_at - sla_first_inbound_at` สำหรับ analytics
- ถ้า conversation มีหลาย SLA cycle → `sla_met` tag ถูกเพิ่มทุกครั้งที่ agent ตอบทัน (1 tag ต่อ 1 cycle)

### sla_breached Tag

- เกิดจาก background job ที่ run ทุก **1 นาที**
- Scan: `WHERE sla_due_at <= NOW() AND sla_status IN (active, due_soon)`
- เปลี่ยน `sla_status` → `breached`
- เพิ่ม system tag `sla_breached` ถ้ายังไม่มี (idempotent)
- Tag **คงอยู่**เป็น audit trail แม้ agent ตอบทีหลัง — ห้ามลบ
- Trigger notification event breach (handle ใน epic 2.8)

### System Tags

- `is_system = true` flag
- ลบไม่ได้ทั้ง UI และ API — return error 403 ถ้าพยายามลบ
- แสดงใน UI ด้วย visual ที่ต่างจาก user tags เช่น lock icon เล็กๆ

### Scope

- Background job: scan → breach detected → เปลี่ยน status → add tag
- `sla_met` tag: เพิ่มตอน agent reply (trigger from SLA-02 logic)
- `sla_breached` tag: เพิ่มโดย breach job
- System tag protection: ทั้ง API และ frontend
- Job idempotency: run ซ้ำบน conversation เดิมไม่ duplicate tag
- **ไม่รวม** notification เมื่อ breach

---

## Acceptance Criteria

**AC1: sla_met tag is automatically added when agent replies before deadline**
- Given conversation has `sla_status = active` with `sla_due_at` in the future
- When an agent sends an outbound reply
- Then system tag `"sla_met"` is added to the conversation
- And `response_time_seconds` is recorded for analytics

**AC2: Breach is detected within 1 minute of deadline passing**
- Given conversation has `sla_due_at` in the past and `sla_status = active` or `due_soon`
- When the background job runs
- Then `sla_status` changes to `breached` within 1 minute of `sla_due_at`
- And this transition triggers a breach notification event

**AC3: sla_breached system tag is added on breach detection**
- Given a breach is detected by the background job
- When the job processes the conversation
- Then system tag `"sla_breached"` is added with `is_system = true`
- And the tag is visible and searchable

**AC4: Background job is idempotent — running multiple times does not create duplicate tags**
- Given conversation already has `sla_breached` system tag
- When the background job runs again on the same conversation
- Then no duplicate `sla_breached` tag is created
- And `sla_status` remains `breached` (no state regression)

**AC5: sla_breached tag remains as audit trail after late reply**
- Given conversation has been tagged `sla_breached`
- When an agent replies after the breach
- Then the `sla_breached` tag is NOT removed
- And the late reply time is recorded for analytics

**AC6: System tags cannot be deleted by any user role**
- Given conversation has `sla_breached` or `sla_met` system tag
- When any user (Agent, Supervisor, or Admin) attempts to delete the tag via UI or API
- Then request is rejected with error: `"system tag ไม่สามารถลบได้"`
- And the tag remains on the conversation

**AC7: System tags are visually distinct from user-created tags**
- Given conversation has both `sla_breached` (system) and a user tag (e.g. "VIP")
- Then `sla_breached` shows a lock icon distinguishing it as system tag
- And user tags do not show this indicator

**AC8: sla_met and sla_breached tags are searchable in inbox search**
- When agent types `"sla_breached"` in the search bar
- Then conversations tagged with `sla_breached` appear in search results (same for `sla_met`)

**AC9: Each SLA cycle creates an independent event record**
- Given conversation has completed cycle 1 with `sla_met`
- When customer sends new message starting cycle 2
- Then new `sla_event` record is created for cycle 2 with `cycle_number = 2`
- And cycle 1 `sla_met` record is preserved unchanged
- And `sla_status` on the conversation resets to `active` for cycle 2

**AC10: Conversation can have both sla_met and sla_breached records across different cycles**
- Given cycle 1 resulted in `sla_met` and cycle 2 resulted in `sla_breached`
- Then both records exist: `[cycle 1: met]` and `[cycle 2: breached]`
- And neither record is deleted or overwritten by the other (immutable audit trail)

**AC11: UI and badge reflect the latest cycle's SLA status**
- Given cycle 1 = `sla_met` and cycle 2 = `sla_breached`
- When the conversation renders in the inbox
- Then the SLA badge shows "Overdue +Xm" based on cycle 2
- And the conversation appears in the Overdue filter
- And `sla_breached` (cycle 2) tag is displayed, not `sla_met` (cycle 1)

**AC12: Breach detection job handles multi-cycle conversations correctly**
- Given cycle 2 deadline has passed and no reply was made
- When the breach detection job runs
- Then `sla_status = breached` for cycle 2
- And `sla_breached` tag added for cycle 2 (idempotent)
- And existing `sla_met` tag from cycle 1 is untouched

**AC13: SLA analytics can distinguish met vs breached per cycle**
- Given conversation has `sla_met` on cycle 1 and `sla_breached` on cycle 2
- Then `response_time_sec` from cycle 1 is available for met-rate calculation
- And elapsed breach time from cycle 2 is available for breach-rate calculation
- And both are queryable independently

---

## UI/UX Notes

- `sla_breached` tag: สีแดง badge พร้อม lock icon เล็กๆ
- `sla_met` tag: สีเขียว badge พร้อม lock icon เล็กๆ
- Tooltip บน system tag: "System tag สร้างโดยระบบอัตโนมัติ ไม่สามารถลบได้"
- Delete button: ไม่แสดงเลยสำหรับ system tags (not in DOM) หรือ disable พร้อม tooltip

---

## Technical Notes

### Dependencies
- **SLA-02** — `sla_due_at`, `sla_status`, `sla_first_inbound_at` ต้องมีก่อน
- Background job infrastructure (cron หรือ queue worker) ต้องรองรับ run ทุก 1 นาที
- Breach event ต้อง trigger notification (handle แยกใน epic 2.8)

### DB Schema

```sql
-- conversation_tags table
tag_id          UUID PRIMARY KEY
conversation_id UUID NOT NULL
is_system       BOOLEAN DEFAULT false
tag_name        VARCHAR NOT NULL
created_at      TIMESTAMP WITH TIME ZONE

-- conversation_sla_events table
id              UUID PRIMARY KEY
conversation_id UUID NOT NULL
cycle_number    INT           -- cycle ที่ 1, 2, 3...
event_type      VARCHAR       -- 'met' หรือ 'breached'
inbound_at      TIMESTAMP     -- first_inbound ของ cycle นั้น
sla_due_at      TIMESTAMP     -- deadline ของ cycle นั้น
resolved_at     TIMESTAMP     -- ตอน met / ตอน breach detected
response_time_sec INT         -- เฉพาะ met: สำหรับ analytics
created_at      TIMESTAMP WITH TIME ZONE
```

### Special Focus

- Job query ต้องมี INDEX บน `sla_due_at` และ `sla_status` เพื่อ performance
- Idempotency: ใช้ `INSERT ... ON CONFLICT DO NOTHING` สำหรับ tag insert
- `sla_met` tag trigger: fire จาก SLA-02 agent reply logic ทันที — ไม่ต้องรอ job
- `sla_breached` tag: lock ด้วย DB constraint `is_system = true` → DELETE protected ที่ layer DB
- Breach job ควร log จำนวน conversations ที่ process ในแต่ละ run เพื่อ monitoring

### Example Multi-cycle Flow

```
Cycle 1:
  ลูกค้าทัก 10:00 → sla_due_at 11:00
  Agent ตอบ 10:45 → sla_met tag [cycle=1] ✓

Cycle 2:
  ลูกค้าทักใหม่ 14:00 → sla_due_at 15:00
  Agent ไม่ตอบ → sla_breached tag [cycle=2] ✗

UI แสดง: sla_breached (latest cycle)
History: [cycle 1: met 10:45] [cycle 2: breached 15:01]
```

---

## QA / Test Considerations

### Primary Flows
- Agent reply ก่อน deadline → `sla_met` tag ปรากฏทันที
- Deadline ผ่าน → job run → `sla_breached` tag ปรากฏภายใน 1 นาที
- Job run ซ้ำ → tag ไม่ duplicate
- Late reply หลัง breach → `sla_breached` tag ยังคงอยู่

### Edge Cases
- Agent/Supervisor/Admin พยายามลบ system tag → error 403
- Conversation มีหลาย breach cycle → tag แยก record ตาม cycle
- Job crash และ run ใหม่ → no duplicate, no missed breaches
- Search "sla_breached" → conversations ปรากฏ

### Business-Critical Must Not Break
- Breach detection ต้องไม่ miss — miss = ซ่อน urgency จาก supervisor
- System tags ต้องเป็น audit trail ถาวร — ห้ามลบแม้แต่ Admin
- `sla_met` tag ต้อง add real-time — ไม่ใช่รอ job

### Test Types
- Unit tests: breach detection logic
- Idempotency tests: run job หลายครั้ง → tag count ไม่เพิ่ม
- Integration tests: deadline → job → status change + tag
- API tests: DELETE system tag → 403
- Search tests: `sla_breached` tag searchable

---

## Subtasks

| Task | Assignee | Status |
|---|---|---|
| [ACE-2233](https://app.clickup.com/t/86d315tu3) BE — Create SLA Event & System Tag Schema | Peerapat | To Do |
| [ACE-2234](https://app.clickup.com/t/86d315u2q) BE — Create Breach Detection job | Peerapat | To Do |
