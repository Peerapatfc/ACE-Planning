# STORY-NOTIF-01: Notification Infrastructure

**Status:** Backlog | **ClickUp:** [ACE-1944](https://app.clickup.com/t/86d2u4a6t) | **Epic:** [ACE-1943](https://app.clickup.com/t/86d2u3v89)

## User Story

As a Backend Engineer
I want a centralized notification infrastructure that can create, store, and deliver notification events to the right users in real-time
so that all notification UI stories (NOTIF-02, 03, 04, 05) have a single reliable foundation to build on.

## Detail / Description

Pure backend story ไม่มี UI ผลลัพธ์คือ data model, delivery service, WebSocket channel, และ event triggers ที่ครบถ้วน

**Scope of this story:**
- Notifications table: เก็บ record ทุก notification
- NotificationService: `createNotification(userId, eventType, payload)` เป็น centralized function
- Event triggers: wire `createNotification` ใน conversation assignment, inbound message, SLA events, channel error
- WebSocket delivery: push notification ไปยัง channel `user:{user_id}:notifications` แบบ real-time
- Reconnect handling: เมื่อ client reconnect ต้อง fetch notifications ที่ miss ตั้งแต่ `last_seen_at`
- Deduplication: `sla_due_soon` ต้องไม่ fire ซ้ำสำหรับ conversation เดิมใน same cycle
- Retention: เก็บ 30 วัน แล้ว soft-delete
- ไม่รวม UI bell, panel, rules config, personal preference (อยู่ใน NOTIF-02 ถึง 05)

## Schema

**notifications table:**
```
notification_id, workspace_id, user_id, event_type (enum), conversation_id (nullable),
actor_id (nullable), metadata (JSON), is_read (boolean default false),
read_at (timestamp nullable), created_at
```

**notification_dedup table:**
```
conversation_id, event_type, cycle_key  -- สำหรับ prevent duplicate sla_due_soon
```

**event_type enum:**
```
conversation_assigned | conversation_reassigned | conversation_unassigned | new_conversation |
customer_replied | mention | sla_due_soon | sla_breached | sla_breached_team | channel_error
```

## Metadata JSON Structure ต่อ event type

| event_type | metadata fields |
|---|---|
| conversation_assigned | `{ conversation_id, customer_name, channel, assigned_by_name }` |
| customer_replied | `{ conversation_id, customer_name, channel, message_preview (ตัดที่ 80 chars) }` |
| mention | `{ conversation_id, note_id, actor_name, channel, note_preview (ตัดที่ 80 chars) }` |
| sla_due_soon | `{ conversation_id, customer_name, channel, remaining_minutes }` |
| sla_breached | `{ conversation_id, customer_name, channel, elapsed_minutes }` |
| channel_error | `{ channel_type, error_description }` |

## Acceptance Criteria

### Notification record created correctly for each event type
**Given** a conversation is assigned to Agent A  
**When** the assignment is saved  
**Then** a notification record is created with `event_type = conversation_assigned`  
**And** `user_id = Agent A`, `actor_id = assigning user`, `conversation_id = conversation`  
**And** metadata contains `customer_name`, `channel`, `assigned_by_name`

### Notification delivered in real-time via WebSocket
**Given** Agent A has an active WebSocket connection on channel `user:{A_id}:notifications`  
**When** a notification is created for Agent A  
**Then** the full notification payload is pushed to the WebSocket channel immediately  
**And** Agent A's bell badge updates without requiring a page refresh

### Notification scoped to correct recipient only
**Given** Agent A and Agent B are in the same workspace  
**When** a conversation is assigned only to Agent A  
**Then** only Agent A receives the notification  
**And** Agent B receives nothing even if they have an active WebSocket connection

### Missed notifications fetched when client reconnects
**Given** Agent A's WebSocket was disconnected for 10 minutes  
**When** Agent A reconnects to the WebSocket  
**Then** the client requests notifications created since `last_seen_at`  
**And** all missed notifications during the disconnection are retrieved  
**And** the bell badge count updates to reflect the correct unread total

### sla_due_soon does not fire duplicate for same conversation in same cycle
**Given** a conversation has `sla_status = due_soon`  
**When** the SLA engine checks and a `sla_due_soon` notification was already sent for this conversation in this cycle  
**Then** no additional `sla_due_soon` notification is created  
**When** the customer sends a new message and a new SLA cycle begins  
**Then** the deduplication resets and the next `sla_due_soon` can fire again

### sla_breached and sla_breached_team fire to different recipients
**Given** a conversation assigned to Agent A breaches its SLA  
**When** breach is detected  
**Then** a `sla_breached` notification is sent only to Agent A  
**And** a `sla_breached_team` notification is sent to all Supervisors and Admins in the workspace  
**And** Agent A does not receive the `sla_breached_team` notification

### channel_error notification sent only to Admins
**Given** a channel has an error (e.g. Instagram token expired)  
**When** the error is detected  
**Then** only Admin users in the workspace receive a `channel_error` notification  
**And** Supervisors and Agents do not receive it

### Notifications older than 30 days cleaned up
**Given** notifications exist that are older than 30 days  
**When** the retention job runs  
**Then** those notifications are soft-deleted or archived  
**And** recent notifications within 30 days are unaffected

### Notification not created when global rule is disabled
**Given** NOTIF-04 has disabled the `new_conversation` event globally  
**When** a new conversation arrives  
**Then** `NotificationService` does NOT create any notification record for this event  
**And** no WebSocket push is sent

## Technical Notes

**Dependencies:**
- RBAC-01: user role สำหรับ routing (ใคร receive อะไร)
- SLA-02: `sla_due_at` สำหรับ `due_soon` trigger
- SLA-04: breach event สำหรับ `sla_breached` notification
- NOTIF-04: global rules ต้องถูก check ก่อน `createNotification` ทำงาน

**Special focus:**
- `NotificationService` ต้องเป็น centralized service ห้าม duplicate notification logic ใน feature files
- WebSocket channel naming: `user:{user_id}:notifications` scoped ต่อ user เพื่อ security
- Reconnect flow: client ส่ง `{ last_seen_at }` → server query `notifications WHERE created_at > last_seen_at AND user_id = X`
- Deduplication key สำหรับ `sla_due_soon`: `(conversation_id, sla_cycle_start_at)` reset เมื่อ met → new_cycle
- `actor_id` เป็น nullable เพราะ system events (SLA, channel_error) ไม่มี human actor
- `message_preview` และ `note_preview` ต้อง truncate ที่ 80 chars + "..." เพื่อ avoid data bloat ใน metadata

## QA / Test Considerations

**Primary flows:**
- Conversation assigned → notification created ถูก `user_id`, `actor_id`, metadata
- WebSocket push → bell badge update real-time
- `sla_due_soon` → fire ครั้งเดียวต่อ cycle → met → new inbound → fire ได้อีก
- `sla_breached` → agent รับ `sla_breached`, supervisor รับ `sla_breached_team`

**Edge Cases:**
- WebSocket disconnect → reconnect → fetch missed → badge update
- `sla_due_soon` fire ซ้ำบน conversation เดิม → deduplicate
- Global rule disabled → notification ไม่ถูกสร้าง
- Notification ถึง user ที่ถูก remove → 403/ignore gracefully

**Business-Critical Must Not Break:**
- Notification ต้องไม่ข้าม user หรือ tenant (security critical)
- `sla_due_soon` deduplication ต้องทำงาน
- WebSocket reconnect ต้องไม่ miss notification

**Test Types:**
- Integration tests: event trigger → notification created → WebSocket pushed
- Scoping tests: notification ไม่ข้าม user
- Deduplication tests: duplicate fire prevention
- Retention tests: 30-day cleanup
- Load tests: many concurrent WebSocket connections
