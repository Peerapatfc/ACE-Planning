# STORY-NOTIF-04: Notification Rules Configuration

**Status:** Backlog | **ClickUp:** [ACE-1947](https://app.clickup.com/t/86d2u4b1n) | **Epic:** [ACE-1943](https://app.clickup.com/t/86d2u3v89)

## User Story

As an Admin or Supervisor
I want to configure which notification events are enabled and who receives them at the workspace level
so that the team receives the right alerts without being overwhelmed by noise, and I can fine-tune SLA thresholds and escalation rules.

## Detail / Description

Content ของ Settings > Notifications > Rules: workspace-level config ที่กระทบทุก user ใน workspace  
Admin/Supervisor config ได้ ผลของ rules นี้ถูก check โดย NOTIF-01 ก่อน create notification ทุกครั้ง

**สิ่งที่ config ได้ต่อ event:**
- Toggle: เปิด/ปิด event ทั้งหมด (global disable)
- Recipients: เลือกว่าใครได้รับ `assigned_agent | supervisor | admin` (multi-select)
- เฉพาะ SLA events: มี additional config
  - `sla_due_soon` threshold: กี่นาทีก่อน deadline → notify (ดึงจาก SLA-01 `due_soon_threshold` แสดงตัวเลขเฉยๆ ไม่สามารถปรับได้ที่นี่ ถ้าจะปรับต้องไปปรับที่ SLA)
  - `sla_breached_team` escalation: ถ้าผ่านมา X นาทีหลัง breach และยังไม่มีใครตอบ → notify supervisor (`escalation_minutes` อยู่บน row `sla_breached_team` — ดังนั้นปิด `sla_breached_team` = ปิด escalation ด้วย, intended behavior ✅ confirmed 2026-06-12)

**Rules Page Layout:**
- แบ่งเป็น 4 กลุ่ม: Conversation Events / Message Events / SLA Events / System Events
- แต่ละ event เป็น row: [toggle] [ชื่อ event] [คำอธิบาย] [recipient multi-select] [additional config ถ้ามี]
- Save button ด้านล่าง

## Default Values เมื่อ workspace เริ่มต้น

| Event | Default enabled | Default recipients |
|---|---|---|
| conversation_assigned | ✅ เปิด | assigned_agent |
| conversation_reassigned | ✅ เปิด | assigned_agent (เดิม) |
| conversation_unassigned | ✅ เปิด | supervisor, admin |
| new_conversation | ✅ เปิด | supervisor, admin |
| customer_replied | ✅ เปิด | assigned_agent |
| mention | ✅ เปิด | mentioned_user (fixed เปลี่ยนไม่ได้) |
| sla_due_soon | ✅ เปิด | assigned_agent, supervisor |
| sla_breached | ✅ เปิด | assigned_agent |
| sla_breached_team | ✅ เปิด | supervisor, admin |
| channel_error | ✅ เปิด | admin (fixed เปลี่ยนไม่ได้) |

**Scope of this story:**
- Settings > Notifications > Rules page: list ของ events ที่ config ได้
- Per event: toggle + recipient multi-select + description
- SLA events: เพิ่ม threshold (due_soon) ดึงจาก sla มาแสดง และ escalation config (breach + X min)
- Save และแสดง success toast
- Rule changes มีผลกับ new events ทันที ไม่กระทบ notifications ที่อยู่ใน bell แล้ว
- ไม่รวม personal preference (อยู่ใน NOTIF-05)

## Acceptance Criteria

### Admin/Supervisor can enable or disable a notification event globally
**Given** Admin is on Settings > Notifications > Rules  
**When** they toggle off the "new_conversation" event and save  
**Then** no user in the workspace receives `new_conversation` notifications from this point on  
**When** toggled back on and saved  
**Then** notifications resume for new occurrences  
**And** existing unread notifications already in the bell are not affected

### Admin/Supervisor can configure recipients per event
**Given** Admin sets `sla_breached` recipients to [assigned_agent, supervisor]  
**When** an SLA breach occurs  
**Then** the assigned agent receives a `sla_breached` notification  
**And** all Supervisors receive a `sla_breached_team` notification  
**And** Admin does not receive it unless Admin is also in the recipients list

### mention and channel_error have fixed recipients
**Given** Admin views the Notification Rules page  
**When** they see the `mention` event row  
**Then** the recipient shows "ผู้ที่ถูก mention"  
**When** they see the `channel_error` event row  
**Then** the recipient shows "Admin เท่านั้น"

### Admin/Supervisor can configure escalation rule after SLA breach
**Given** Admin sets escalation: notify supervisor 30 minutes after breach if no reply  
**When** a conversation breaches SLA and 30 minutes pass without any agent reply  
**Then** an escalation notification is sent to all Supervisors  
**And** it is a separate notification distinct from the initial `sla_breached_team` notification  
**And** if an agent replies within 30 minutes, escalation does NOT fire

### Escalation does not spam supervisors when many conversations breach simultaneously
**Given** 10 conversations breach simultaneously and escalation is configured  
**When** escalation fires  
**Then** supervisors receive individual notifications per conversation  
**And** a rate-limit prevents more than 5 escalation notifications per minute per user

> ⚠️ **AC rate-limit รอ PO เคาะ (2026-06-12):** AC ข้อนี้ตั้งบน premise ว่ามี intrusive UI (toast) ซึ่งไม่มีใน UX จริง — real-time surface มีแค่ bell badge + panel ดังนั้น design ปัจจุบัน**ไม่มี rate-limit ที่ delivery** (push ครบทุกใบ badge ตรงกับความจริงเสมอ) ส่วน throughput คุมที่ source ด้วย cron batch 500/รอบ — เสนอ: (a) ตัด AC ข้อนี้ หรือ (b) defer เป็น future-proofing เมื่อมี toast/sound — ดู `Diagram/NOTIF-04_escalation_v3_sequence.md` (ส่วน AC "individual notifications per conversation" ด้านบนยังถูกต้องตามเดิม)

### Disabling sla_breached_team also disables escalation
**Given** Admin disables the `sla_breached_team` event  
**When** a conversation breaches SLA and `escalation_minutes` pass without any agent reply  
**Then** no team breach notification is sent  
**And** no escalation notification is sent (escalation config lives on the `sla_breached_team` rule — intended coupling)

### Rule changes take effect immediately for new events
**Given** Admin saves a rule change disabling `customer_replied`  
**When** a customer replies to a conversation after the save  
**Then** no `customer_replied` notification is created  
**And** notifications already in the bell from before the change remain unaffected

### Only Admin and Supervisor can access Notification Rules settings
**Given** an Agent navigates to Settings > Notifications > Rules  
**Then** they are redirected and see an Access Denied page

## Technical Notes

**Dependencies:**
- NOTIF-01: rules ต้อง wire เข้ากับ `NotificationService` ก่อน create notification
- SLA-01: `due_soon_minutes` ที่ต้อง sync กับ SLA timer config
- SETTINGS-01: Settings shell
- RBAC-01: เฉพาะ Admin/Supervisor เข้า Notification Rules ได้

**Special focus:**
- `notification_rules` table: `workspace_id, event_type, enabled, recipients (JSON array), due_soon_minutes (nullable), escalation_minutes (nullable), updated_by, updated_at`
- Delivery pipeline check: NOTIF-01 query `notification_rules` ก่อน `createNotification`
- `mention` และ `channel_error` recipients ต้อง hardcode ใน notification logic ไม่ใช่ใน `notification_rules` table
- Escalation job: scan conversations WHERE `sla_breached` + `elapsed > escalation_minutes` + no reply → fire escalation notification
- ~~Escalation rate-limit: max 5 escalation notifications per user per minute~~ ⚠️ รอ PO — premise (toast) ไม่มีใน UX จริง; throughput คุมที่ cron batch 500/รอบแทน (ดู escalation v3)

## QA / Test Considerations

**Primary flows:**
- Disable event → event occurs → verify ไม่มี notification
- Set recipients → verify ถูกคนรับ
- Set escalation 30m → breach + 30m ไม่มีใครตอบ → supervisor รับ noti

**Edge Cases:**
- Escalation fires 10 convs พร้อมกัน → bell มีครบ 10 ใบ, badge เพิ่มครบ (ไม่มี rate-limit — ⚠️ AC เดิมรอ PO เคาะ)
- Rule change → existing notifications ใน bell ไม่หาย

**Business-Critical Must Not Break:**
- SLA `due_soon` threshold sync กับ SLA-01 ต้องทำงาน
- Escalation ต้องทำงาน

**Test Types:**
- Rule config tests: enable/disable + recipients
- Escalation timer tests
- Bulk breach tests: backlog 2,000 convs → drain 500/รอบ cron, bell/badge ครบทุกใบ (~~rate-limit tests~~ ⚠️ รอ PO)
- Integration: rule change → delivery behavior changes
