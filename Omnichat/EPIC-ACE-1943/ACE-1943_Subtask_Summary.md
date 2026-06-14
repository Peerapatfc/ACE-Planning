# EPIC-ACE-1943: Notification Center Subtask Summary

> Proposed ClickUp subtasks per story — ready to create in ClickUp

---

## ACE-1944 — STORY-NOTIF-01: Notification Infrastructure (13 SP) — Backlog

| Subtask | Type | Notes |
|---|---|---|
| BE — Notifications & Dedup DB Migration | Backend | `notifications` table (notification_id, workspace_id, user_id, event_type enum, conversation_id, actor_id, metadata JSONB, is_read, read_at, created_at) + `notification_dedup` table (conversation_id, event_type, cycle_key) |
| BE — NotificationService: createNotification + Delivery Pipeline | Backend | Centralized `createNotification(userId, eventType, payload)` + pipeline: global rule check → recipient resolve → personal pref check → insert + WS push; stub pass-all until NOTIF-04/05 wire |
| BE — Event Triggers: Conversation Events | Backend | Hook createNotification ใน conversations.service.ts — assigned/reassigned/unassigned/new_conversation; metadata: customer_name, channel, assigned_by_name |
| BE — Event Triggers: Message Events | Backend | Hook ใน messages.service.ts — customer_replied (message_preview 80 chars) + mention (note_id, note_preview 80 chars) |
| BE — Event Triggers: SLA Events + Deduplication | Backend | Hook ใน SLA breach job — sla_due_soon (dedup per cycle_key), sla_breached (agent only), sla_breached_team (supervisor+admin); dedup guard via notification_dedup table |
| BE — Event Triggers: Channel Error | Backend | Hook channel error handler → createNotification สำหรับ Admin เท่านั้น (fixed recipient) |
| BE — WebSocket Delivery + Reconnect Handler | Backend | Push full payload ไป `user:{user_id}:notifications` ทันที; reconnect: client ส่ง last_seen_at → server query missed notifications |
| BE — Notification REST APIs | Backend | GET /notifications (paginated 50/page), GET /notifications/unread-count, PATCH /notifications/:id/read, PATCH /notifications/read-all; location: apps/api-gateway/src/omnichat/notifications/ |
| BE — Retention Job: 30-day soft-delete | Backend | BullMQ daily job soft-delete WHERE created_at < NOW() - 30 days |

**Notes:**
- `actor_id` nullable — system events (SLA, channel_error) ไม่มี human actor
- `message_preview` + `note_preview` truncate ที่ 80 chars + "..."
- WebSocket channel naming: `user:{user_id}:notifications` scoped per user (security)
- Dedup key สำหรับ `sla_due_soon`: `(conversation_id, sla_cycle_start_at)` reset เมื่อ met → new_cycle

---

## ACE-1945 — STORY-NOTIF-02: Bell Icon & Unread Badge (3 SP) — Backlog

| Subtask | Type | Notes |
|---|---|---|
| FE — Bell Icon + Active State ใน Top Nav | Frontend | Bell icon ฝั่งขวา nav bar (ข้างๆ profile icon) เห็นทุกหน้า; active visual state เมื่อ panel เปิด |
| FE — Unread Badge Component + WebSocket Listener | Frontend | Badge: 1–99 ตัวเลข, "99+" ถ้า>99, ซ่อนเมื่อ 0; fetch GET /notifications/unread-count ตอน page load; subscribe WS channel → increment real-time; optimistic clear เมื่อ mark all read |

**Notes:**
- Badge sync ต้องใช้ WebSocket หลัก ไม่ rely on polling
- เพิ่ม `notification-bell.tsx` component ใหม่ใน dashboard/_components/

---

## ACE-1946 — STORY-NOTIF-03: Notification Panel & History (8 SP) — Backlog

| Subtask | Type | Notes |
|---|---|---|
| FE — Notification Types + Panel Container | Frontend | เพิ่ม Notification type + NotificationEventType enum ใน omnichat.ts; Panel dropdown anchored ใต้ bell; z-index > content; เปิด/ปิดด้วย bell click หรือ click outside |
| FE — Notification Item Component | Frontend | Event icon (colored ตาม group), actor+verb+object text, channel badge, relative time, unread dot, background state, SLA border-left แดง สำหรับ sla_due_soon/sla_breached |
| FE — Relative Time Util (Thai format) | Frontend | formatRelativeTime(createdAt) → Thai string ตาม 7-tier format table ใน Epic spec; location: src/utils/notification-time.ts |
| FE — Click Notification: Navigate + Mark Read | Frontend | Click → navigate ไป conversation → PATCH /notifications/:id/read → badge -1 → close panel; optimistic local state update; graceful 404: toast "โน้ตนี้ถูกลบแล้ว" หรือ "Conversation นี้ไม่พบ" |
| FE — Mark All Read + Infinite Scroll + Empty State | Frontend | "อ่านทั้งหมด" button → PATCH /notifications/read-all → badge หาย; infinite scroll 50/page ด้วย Intersection Observer; empty state icon + "ไม่มีการแจ้งเตือน"; re-fetch ทุกครั้งที่เปิด panel |

**Notes:**
- Optimistic update ก่อน API return สำหรับ mark read + mark all
- Panel ต้อง merge กับ WebSocket events ที่เกิดระหว่าง panel ปิด
- Navigate ห้าม full page reload

---

## ACE-1947 — STORY-NOTIF-04: Notification Rules Configuration (8 SP) — Backlog

| Subtask | Type | Notes |
|---|---|---|
| BE — notification_rules DB Migration | Backend | `notification_rules` table: workspace_id, event_type, enabled, recipients JSONB, escalation_minutes NULLABLE, updated_by, updated_at; PRIMARY KEY (workspace_id, event_type); default values per Epic spec |
| BE — Notification Rules APIs + Wire into Pipeline | Backend | GET /notification-rules (return defaults ถ้าไม่มี record), PATCH /notification-rules; wire rules check เข้า NotificationService delivery pipeline (แทน stub ใน NOTIF-01); permission: config_notifications |
| BE — Escalation Job: supervisor notify after breach + X min | Backend | BullMQ job scan: sla_status='breached' + elapsed > escalation_minutes + no agent reply → fire escalation notification ไป Supervisor; rate-limit max 5/user/min; `mention` + `channel_error` recipients hardcode ใน service ไม่ใช่ใน table |
| FE — Notification Rules Settings Page | Frontend | Settings > Notifications > Rules; 4 กลุ่ม event rows; แต่ละ row: toggle + ชื่อ + description + recipient multi-select; SLA events: due_soon_minutes read-only + escalation minutes input; RBAC guard: redirect Agent; location: settings/notifications/rules/page.tsx |

**Notes:**
- Rule changes มีผลกับ new events ทันที — notifications ที่อยู่ใน bell แล้วไม่หาย
- `mention` + `channel_error` recipients fixed ใน code ไม่สามารถแก้ได้ใน UI
- RBAC: เพิ่ม `config_notifications` permission ใน rbac.types.ts

---

## ACE-1948 — STORY-NOTIF-05: Personal Notification Preferences (5 SP) — Backlog

| Subtask | Type | Notes |
|---|---|---|
| BE — notification_preferences DB Migration + APIs + Wire into Pipeline | Backend | `notification_preferences` table: user_id, workspace_id, event_type, muted; PRIMARY KEY (user_id, workspace_id, event_type); default unmuted (no row = unmuted); GET + PATCH /notification-preferences (scoped by JWT user_id); wire personal pref check เข้า pipeline step 4 (แทน stub NOTIF-01) |
| FE — My Preferences Settings Page | Frontend | Settings > Notifications > My Preferences; filter events ตาม role (ดู matrix ใน story doc); greyed out + tooltip "ปิดโดย Admin ของ workspace" สำหรับ globally disabled events; load global rules + preferences ก่อน render; ทุก role เข้าได้; location: settings/notifications/preferences/page.tsx |

**Notes:**
- Global rule priority > personal preference เสมอ
- Default state: all unmuted (new user ไม่มี record = รับทุกอย่าง)
- Personal mute ต้องไม่กระทบ user อื่น — scope ด้วย user_id จาก JWT

---

## Summary

| Story | Status | Subtasks | SP |
|-------|--------|----------|----|
| ACE-1944 NOTIF-01 Infrastructure | Backlog | 9 | 13 |
| ACE-1945 NOTIF-02 Bell + Badge | Backlog | 2 | 3 |
| ACE-1946 NOTIF-03 Panel + History | Backlog | 5 | 8 |
| ACE-1947 NOTIF-04 Rules Config | Backlog | 4 | 8 |
| ACE-1948 NOTIF-05 Personal Prefs | Backlog | 2 | 5 |
| **Total** | | **22** | **37 SP** |

---

## Dependency Order

```
ACE-1944 (NOTIF-01 Infrastructure — DB + Service + WebSocket + APIs)
    └─→ ACE-1945 (NOTIF-02 Bell — ต้องมี WS + unread-count API)
            └─→ ACE-1946 (NOTIF-03 Panel — ต้องมี bell + REST APIs)
    └─→ ACE-1947 (NOTIF-04 Rules — ต้องมี pipeline stub + sla_configs from SLA-01)
    └─→ ACE-1948 (NOTIF-05 Prefs — ต้องมี pipeline stub)

External dependencies:
    SLA-02 (sla_due_at, sla_status) → NOTIF-01 SLA triggers
    SLA-04 (breach event fire) → NOTIF-01 SLA triggers
```

**Repo context:** ดู `story-task-breakdown.md` สำหรับ task-level detail + ไฟล์ที่ต้องสร้าง/แก้
