# STORY-SLA-01: SLA Configuration UI

**ClickUp ID:** ACE-1640
**Status:** In Progress
**Sprint:** Sprint 6 (5/18–5/29)
**Points:** 8 SP
**Parent Epic:** ACE-1618
**Assignees:** Tanawin (Toy), Siraphob Reanmanorom
**URL:** https://app.clickup.com/t/86d2ptdux

---

## User Story

As an Admin or Supervisor
I want to configure SLA response time targets per channel, set a due soon threshold, and optionally enable Business Hours mode
so that the platform knows how long agents have to respond on each channel and can track compliance automatically and SLA deadlines are fair and reflect my team's actual working hours, conversations arriving outside office hours will not immediately breach when the team starts work.

---

## Detail / Description

หน้า **Settings > SLA** เป็นที่รวม config ทั้งหมดที่เกี่ยวกับ SLA ประกอบด้วย 2 ส่วนหลัก:
- **Global Settings:** global toggle + due soon threshold + Business Hours toggle
- **Channel SLA Targets:** per-channel toggle + target time + reset to default + platform context tooltip + warning

### Scope

- Global toggle: เปิด/ปิด SLA feature ทั้งหมด (เมื่อปิด = ทุก channel ไม่มี timer)
- Per-channel toggle: เปิด/ปิด SLA สำหรับแต่ละ channel อิสระกัน
- Target time input: ตัวเลข + unit (minutes/hours) ต่อ channel พร้อม default ตาม recommended
- Due soon threshold: global setting (นาที) เมื่อเหลือเวลาน้อยกว่านี้ = due_soon
- Platform context tooltip: แต่ละ channel มีคำอธิบายว่า platform กำหนดอะไรบ้าง
- Warning ถ้า Facebook/Instagram target > 24h
- Reset to default per channel
- Business Hours aware: toggle "นับเฉพาะ business hours"
- BH mode preview schedule + warning ถ้าไม่มี BH data

**ไม่รวม (R2):** break กลางวัน, multi-timezone, per-channel BH, SLA per customer tier/group/agent

### Business Hours Mode

- Toggle "นับ SLA เฉพาะในช่วง Business Hours"
- ถ้าเปิด: `sla_due_at` คำนวณโดย skip เวลานอก BH (SLA-02 handle logic)
- ถ้าปิด (default): นับ 24/7 เหมือนเดิม
- Dependency: SETTINGS-02 Business Hours ต้องมีข้อมูลก่อน toggle นี้จึงทำงานได้
- เมื่อ toggle เปิด: แสดง preview schedule สั้นๆ ที่ดึงจาก SETTINGS-02 เช่น "จ-ศ 09:00-18:00"
- ถ้า toggle เปิดแต่ไม่มี Business Hours ใน SETTINGS-02: แสดง warning พร้อม link ไปตั้งค่า

---

## Acceptance Criteria

**AC1: Global SLA toggle enables or disables the entire SLA feature**
- Given Admin/Supervisor is on Settings > SLA
- When they toggle "Enable SLA" off
- Then all SLA timers across all channels stop and conversations show no timer
- And per-channel toggles are greyed out
- When toggled back on → SLA resumes for channels that were individually enabled before

**AC2: Admin/Supervisor can enable or disable SLA per channel independently**
- Given global SLA is enabled
- When Admin/Supervisor toggles SLA off for LINE
- Then new LINE conversations no longer get SLA timers
- And existing LINE conversations with active timers retain their current state
- And other channels are not affected

**AC3: Admin/Supervisor can set first response time target per channel**
- Given SLA is enabled for Shopee
- When Admin/Supervisor enters 12 with unit "hours" and saves
- Then new Shopee conversations use a 12-hour SLA target
- And existing conversations already open are not retroactively affected

**AC4: Platform context tooltip shows relevant messaging window information per channel**
- Given Admin/Supervisor hovers over the info icon next to Facebook
- When the tooltip opens
- Then it explains Facebook's 24h messaging window and the consequence of not replying in time
- And LINE tooltip explains it has no messaging window restriction

**AC5: Warning appears when Facebook or Instagram target exceeds 24 hours**
- Given Admin/Supervisor sets Facebook target to more than 24 hours
- When the value is entered or saved
- Then a warning appears: "⚠️ Facebook มี 24h messaging window — target เกิน 24h อาจทำให้เสียสิทธิ์ส่ง promotional message"
- And the save is still allowed (warning only, not a block)

**AC6: Due soon threshold is configurable globally**
- Given Admin/Supervisor sets due soon threshold to 20 minutes
- Then conversations with remaining time <= 20 minutes change to sla_status = due_soon
- And the threshold applies to all channels uniformly
- And this threshold is separate from and does not affect the Overdue filter pill

**AC7: Business Hours toggle enables BH-aware SLA calculation**
- Given SETTINGS-02 has Business Hours configured (e.g. Mon-Fri 09:00-18:00)
- When Admin/Supervisor enables "Count SLA only during Business Hours" toggle
- Then a preview of the current Business Hours schedule appears below the toggle
- And when saved, new conversations will have `sla_due_at` calculated using Business Hours logic

**AC8: Warning appears if Business Hours toggle is enabled but no Business Hours are configured**
- Given SETTINGS-02 Business Hours has NOT been configured
- When Admin/Supervisor enables the Business Hours toggle
- Then a warning appears: "⚠️ ยังไม่ได้ตั้ง Business Hours — กรุณาตั้งค่าก่อนที่ Settings > Business Information"
- And a link to SETTINGS-02 is provided
- And the toggle reverts to off or save is blocked until BH is configured

**AC9: Reset to default restores channel to recommended value**
- Given Admin/Supervisor has changed Shopee SLA to 3 hours
- When they click "Reset to default" for Shopee and confirm
- Then the target reverts to 12 hours (the recommended default)

**AC10: Form validates input before saving**
- Given Admin/Supervisor enters 0 or a negative number as target time
- When they click Save
- Then a validation error appears: "ค่าต้องมากกว่า 0"
- And the save request is not sent

**AC11: Only Admin and Supervisor can access SLA settings**
- Given an Agent navigates to Settings > SLA
- Then they are redirected and see an Access Denied message

---

## UI/UX Notes

- Page แบ่งเป็น 2 card: **"Global Settings"** (global toggle + due soon threshold) + **"Channel SLA Targets"** (per-channel rows)
- BH toggle: เมื่อ on → preview schedule ปรากฏด้านล่าง toggle ทันที
- BH preview format: "จ-ศ 09:00-18:00" หรือ "จ-อา 09:00-18:00" ตาม SETTINGS-02
- Warning ถ้าไม่มี BH data: แสดง amber box พร้อมปุ่ม "ตั้งค่า Business Hours →"
- Per-channel row: toggle + channel icon + channel name + number input + unit dropdown (minutes/hours) + default + reset button + info icon
- Warning banner ปรากฏใต้ channel row เมื่อ target ขัดแย้งกับ platform window
- Save button: save ทั้งหน้าครั้งเดียว รวม BH toggle อยู่ด้านล่างสุด

---

## Technical Notes

### Dependencies
- **SETTINGS-01** — Settings shell
- **SETTINGS-02** — Business Hours API (`GET /workspace/business-hours`) ต้องพร้อมก่อน BH toggle ทำงาน
- **RBAC-01** — เฉพาะ Admin/Supervisor
- **SLA-02** — `bh_aware` flag ที่ save ที่นี่จะถูก SLA engine อ่านไปใช้

### Special Focus

```sql
-- sla_configs table
workspace_id, channel_type, enabled, first_response_minutes,
due_soon_minutes, bh_aware BOOLEAN DEFAULT false,
created_at, updated_at
```

- `global_sla_enabled` flag เก็บระดับ workspace ไม่ใช่ per-channel
- ถ้า `bh_aware = true` แต่ `GET /workspace/business-hours` return empty → warning ใน UI และ SLA-02 fallback เป็น 24/7
- Warning logic: ถ้า channel = facebook หรือ instagram และ `first_response_minutes > 1440` (24h) → show warning
- Save config ใหม่ → ไม่กระทบ conversations ที่เปิดอยู่แล้ว มีผลกับ conversations ใหม่เท่านั้น (ไม่ retroactive)

---

## QA / Test Considerations

### Primary Flows
- เปิด BH toggle + มี BH data → preview แสดง → save → conversations ใหม่ใช้ BH mode
- เปิด BH toggle + ไม่มี BH data → warning แสดง → link ไป SETTINGS-02
- ปิด BH toggle → 24/7 mode เหมือนเดิม
- Set Facebook > 24h → warning ปรากฏ

### Edge Cases
- BH toggle on + BH schedule มีแค่บางวัน (เช่น จ-ศ) → message วันเสาร์ handle ยังไง (รายละเอียดใน SLA-02)
- BH data เปลี่ยนหลัง toggle เปิดแล้ว → conversations เก่าไม่กระทบ, ใหม่ใช้ BH ใหม่
- Input 0 → validation error

### Business-Critical Must Not Break
- BH toggle ต้องไม่เปิดได้ถ้าไม่มี BH data — ห้าม `sla_due_at` ผิดเพราะ BH config ไม่ครบ
- Config save ต้องไม่กระทบ conversations เปิดอยู่แล้ว

### Test Types
- UI tests: BH toggle on/off, preview fetch, warning state
- API tests: `PATCH /sla/config` พร้อม `bh_aware` field
- Integration: BH toggle save → SLA-02 reads `bh_aware` correctly

---

## Subtasks

| Task | Assignee | Status |
|---|---|---|
| [ACE-2219](https://app.clickup.com/t/86d315hdt) FE — Implement Global SLA Toggle | Tanawin (Toy) | In Progress |
| [ACE-2220](https://app.clickup.com/t/86d315hjy) BE — Create SLA Config Schema & Migration | Siraphob | Reviewing |
| [ACE-2221](https://app.clickup.com/t/86d315j6t) BE — SLA Config APIs | Siraphob | In Progress |
