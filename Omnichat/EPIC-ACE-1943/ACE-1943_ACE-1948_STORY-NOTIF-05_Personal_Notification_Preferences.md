# STORY-NOTIF-05: Personal Notification Preferences

**Status:** Backlog | **ClickUp:** [ACE-1948](https://app.clickup.com/t/86d2u4b9b) | **Epic:** [ACE-1943](https://app.clickup.com/t/86d2u3v89)

## User Story

As any logged-in user (Admin / Supervisor / Agent)
I want to control which notification types I personally receive
so that I can reduce distracting noise without affecting my teammates' notification settings.

## Detail / Description

Content ของ Settings > Notifications > My Preferences  
Personal setting ที่มีผลเฉพาะตัวเอง ทุก role เข้าถึงได้ เป็น section เดียวใน Settings > Notifications ที่ Agent เห็น

- Agent ที่ได้ notification ทุกอย่างอาจจะเยอะเกินจนทำให้ปิด browser notifications ทั้งหมด
- ทีมเล็กบางคนอาจไม่ต้องการ `customer_replied` ทุก message ถ้า review inbox อยู่แล้ว
- ขาด personal preference → agent ไม่มีทางปิด noise → ประสบการณ์ไม่ค่อยดี

## Preference Matrix (สิ่งที่แต่ละ role mute ได้)

| Event | Agent | Supervisor | Admin |
|---|---|---|---|
| conversation_assigned | ✅ | ✅ | ✅ |
| conversation_reassigned | ✅ | ✅ | ✅ |
| conversation_unassigned | ❌ | ✅ | ✅ |
| new_conversation | ❌ | ✅ | ✅ |
| customer_replied | ✅ | ✅ | ✅ |
| mention | ✅ | ✅ | ✅ |
| sla_due_soon | ✅ | ✅ | ✅ |
| sla_breached | ✅ | ✅ | ✅ |
| sla_breached_team | ❌ | ✅ | ✅ |
| channel_error | ❌ | ❌ | ✅ |

> ❌ = Role นั้นไม่ได้รับ event นี้อยู่แล้วตาม NOTIF-04 rules ไม่ต้องมีให้ mute

## Preference Priority Rules

- ถ้า global rule (NOTIF-04) disabled event → personal preference ไม่สามารถ enable ได้ → greyed out + tooltip
- ถ้า global rule enabled + user muted → user ไม่รับ แต่คนอื่นยังรับปกติ
- ถ้า global rule enabled + user ไม่ได้ mute → รับตาม global rule
- Default: ทุก event unmuted user รับทุกอย่างตาม global rules จนกว่าจะ mute เอง

## My Preferences Page Layout

- คำอธิบาย: "การตั้งค่าเหล่านี้มีผลเฉพาะบัญชีของคุณ ไม่กระทบสมาชิกคนอื่น"
- List ของ events ที่ role นี้ได้รับ: [toggle] [ชื่อ event] [คำอธิบาย]
- Event ที่ global rule disabled: greyed out + tooltip "ปิดโดย Admin ของ workspace"
- Save button

**Scope of this story:**
- Settings > Notifications > My Preferences page
- Toggle mute/unmute per event ที่ role นั้นได้รับ
- Greyed out + tooltip สำหรับ event ที่ global rule ปิดอยู่
- ทุก role เข้าถึงได้ (SETTINGS-01 route ถูก setup ให้แล้ว)
- ไม่รวม email notification, quiet hours, notification frequency (R2)

## Acceptance Criteria

### User can mute a specific notification event for themselves only
**Given** an Agent is on Settings > Notifications > My Preferences  
**When** they mute `customer_replied` and save  
**Then** that Agent no longer receives `customer_replied` notifications in their bell  
**And** other agents' notification settings are completely unaffected  
**And** Supervisors who are recipients of `customer_replied` still receive it

### Personal mute does not override global rule
**Given** Admin has disabled `new_conversation` globally in NOTIF-04  
**When** a Supervisor opens My Preferences  
**Then** `new_conversation` is greyed out and cannot be toggled  
**And** a tooltip reads: "ปิดโดย Admin ของ workspace กรุณาติดต่อ Admin เพื่อเปิดใช้งาน"

### Agent does not see events they cannot receive
**Given** an Agent opens My Preferences  
**When** the page renders  
**Then** only events Agent can receive are shown: `conversation_assigned`, `conversation_reassigned`, `customer_replied`, `mention`, `sla_due_soon`, `sla_breached`  
**And** events like `new_conversation`, `sla_breached_team`, `channel_error` are not shown for Agent

### Unmuting an event resumes delivery immediately
**Given** an Agent previously muted `sla_due_soon`  
**When** they unmute it and save  
**Then** the Agent begins receiving `sla_due_soon` notifications for new occurrences

### Default state is all unmuted for new users
**Given** a new user joins the workspace  
**When** they open My Preferences for the first time  
**Then** all applicable events are toggled ON (unmuted)  
**And** no event is muted by default

### All roles can access My Preferences page
**Given** an Agent is logged in  
**When** they navigate to Settings > Notifications > My Preferences  
**Then** the page loads successfully without access denied error

### Preference changes take effect immediately for subsequent events
**Given** a user saves a new preference  
**When** a new notification event occurs after the save  
**Then** the new preference is applied to that event  
**And** notifications already in the bell before the change are not removed

## Technical Notes

**Dependencies:**
- NOTIF-01: delivery pipeline ต้อง check personal preference ก่อน deliver (step 4 ใน pipeline)
- NOTIF-04: global rules ต้อง check ก่อน personal preference (step 2-3)
- SETTINGS-01: My Preferences route ต้อง accessible ให้ Agent
- RBAC-01: ทุก role เข้า My Preferences ได้ แต่ events ที่แสดงต่างกันตาม role

**Special focus:**
- `notification_preferences` table: `user_id, workspace_id, event_type, muted (boolean)`
- Default: ถ้าไม่มี record ใน preferences table → ถือว่า unmuted
- Delivery check: query preferences WHERE `user_id AND event_type AND muted = true` → skip delivery
- Page render: filter events ตาม role ก่อนแสดง
- Greyed out logic: ถ้า `notification_rules WHERE event_type AND enabled = false` → grey out ใน UI

## QA / Test Considerations

**Primary flows:**
- Agent mute `customer_replied` → conversation unassigned → agent ไม่รับ | supervisor ยังรับ
- Global disabled → greyed out ใน preferences

**Edge Cases:**
- Agent mute then unmute → delivery resumes
- New user → all unmuted
- Role ที่ไม่ควรเห็น event → ไม่แสดงใน page

**Business-Critical Must Not Break:**
- Personal mute ต้องไม่กระทบ user อื่น แยก scope ชัดเจน
- Global rule ต้องมีความสำคัญสูงกว่า personal preference เสมอ

**Test Types:**
- Unit tests: delivery pipeline ตาม personal preference
- UI tests: greyed out event
- Integration: mute → no delivery | unmute → delivery resumes
- Role visibility tests
