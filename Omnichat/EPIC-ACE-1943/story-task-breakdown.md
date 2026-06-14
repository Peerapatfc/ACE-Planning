# EPIC-ACE-1943: Story Task Breakdown

Task แต่ละ story พร้อมคำอธิบายว่าทำอะไร — อิงจากสิ่งที่มีอยู่แล้วใน repo จริง (เฉพาะที่ยังต้องทำ)

> **Legend:** 🔧 มีโค้ดอยู่แล้วแต่ต้องแก้ | (ไม่มีไอคอน) สร้างใหม่ทั้งหมด

---

## สิ่งที่มีอยู่แล้วใน repo (อย่าทำซ้ำ)

| สิ่งที่มี | ไฟล์ | หมายเหตุ |
|----------|------|----------|
| BullMQ worker infrastructure | `apps/omnichat-gateway/` | ใช้แล้วใน SLA breach job — reuse pattern นี้ |
| WebSocket setup | `apps/omnichat-gateway/` | มี gateway อยู่แล้ว — เพิ่ม channel ใหม่ |
| `sla_due_at`, `sla_status` fields | Conversations table (SLA-02) | ใช้ trigger `sla_due_soon` / `sla_breached` |
| Breach event fire | SLA-04 breach detection job | hook จุดนี้สำหรับ `sla_breached` notification |
| `config_sla` RBAC permission | `packages/shared/src/types/rbac.types.ts` | pattern สำหรับ `config_notifications` |
| Conversation assignment logic | `omnichat-service/` | hook จุดนี้สำหรับ `conversation_assigned` trigger |
| Internal notes / mention parsing | `omnichat-service/` | hook จุดนี้สำหรับ `mention` trigger |
| Top navigation bar | `apps/workspace-admin/src/app/(main)/` | เพิ่ม bell icon ตรงนี้ |
| Settings shell (SETTINGS-01) | `apps/workspace-admin/src/app/(main)/dashboard/settings/` | เพิ่ม Notifications route ตรงนี้ |

---

## NOTIF-01 — Notification Infrastructure (13 SP)

> **เป้าหมาย:** สร้าง backend foundation ที่ stories อื่นทุกตัวต้องพึ่งพา — DB, service, WebSocket, API endpoints, dedup, retention

---

### Task 1.1 — DB migration: `notifications` + `notification_dedup` tables
**ทำอะไร:** สร้าง 2 ตารางใหม่ใน omnichat-service

**Location:** `apps/omnichat-service/prisma/schema.prisma`

```sql
-- notifications table
notification_id   UUID PRIMARY KEY
workspace_id      UUID NOT NULL
user_id           UUID NOT NULL
event_type        ENUM  -- 10 types (ดู enum ด้านล่าง)
conversation_id   UUID NULLABLE
actor_id          UUID NULLABLE
metadata          JSONB
is_read           BOOLEAN DEFAULT false
read_at           TIMESTAMP NULLABLE
created_at        TIMESTAMP WITH TIME ZONE
-- INDEX: (user_id, is_read, created_at) สำหรับ unread count + list query

-- notification_dedup table (สำหรับ prevent sla_due_soon duplicate)
conversation_id   UUID NOT NULL
event_type        VARCHAR NOT NULL
cycle_key         VARCHAR NOT NULL  -- sla_cycle_start_at เป็น string
PRIMARY KEY (conversation_id, event_type, cycle_key)
```

**event_type enum:**
```
conversation_assigned | conversation_reassigned | conversation_unassigned | new_conversation |
customer_replied | mention | sla_due_soon | sla_breached | sla_breached_team | channel_error
```

---

### Task 1.2 — `NotificationService`: core `createNotification` function
**ทำอะไร:** สร้าง centralized service — `createNotification(userId, eventType, payload)` — ทุก trigger ต้องผ่านที่เดียว  
**ทำไม:** ถ้า notification logic กระจาย feature-by-feature จะ duplicate และ maintain ยาก

**Location:** `apps/omnichat-service/src/notifications/notification.service.ts` (ใหม่)

```typescript
async createNotification(
  userId: string,
  eventType: EventType,
  payload: {
    workspaceId: string
    conversationId?: string
    actorId?: string
    metadata: Record<string, unknown>
  }
): Promise<void>
// insert notifications record → push WebSocket → return
```

---

### Task 1.3 — `NotificationService`: delivery pipeline (rule check + recipient resolve + WS push)
**ทำอะไร:** ต่อ delivery pipeline เข้าไปใน `createNotification` ก่อนที่จะ insert record

**Pipeline (ตาม Epic spec):**
1. Check global rule (NOTIF-04): ถ้า disabled → return early, ไม่ insert
2. Resolve recipients list จาก `notification_rules` + RBAC
3. สำหรับแต่ละ recipient: check personal preference (NOTIF-05) — ถ้า muted → skip คนนั้น
4. ผ่านทุก step → insert record → push WebSocket

**Note:** ตอนสร้าง NOTIF-01 ยังไม่มี `notification_rules` หรือ `notification_preferences` table → ให้ default ว่า "pass all" ก่อน แล้ว NOTIF-04 และ NOTIF-05 จะมา wire จริง

---

### Task 1.4 — Event triggers: Conversation events
**ทำอะไร:** hook `createNotification` เข้าใน conversation assignment logic

| Event | Hook จากไหน | Recipients |
|-------|------------|------------|
| `conversation_assigned` | `assignConversation()` | Agent ที่ถูก assign |
| `conversation_reassigned` | `reassignConversation()` | Agent เดิม |
| `conversation_unassigned` | `unassignConversation()` | Supervisor, Admin |
| `new_conversation` | `createConversation()` + ยังไม่มี assign | Supervisor, Admin |

**metadata ที่ต้องส่ง:** `{ conversation_id, customer_name, channel, assigned_by_name }`

**ไฟล์ที่แก้:** `apps/omnichat-service/src/conversations/conversations.service.ts`

---

### Task 1.5 — Event triggers: Message events
**ทำอะไร:** hook `createNotification` เข้าใน message handling

| Event | Hook จากไหน | Recipients |
|-------|------------|------------|
| `customer_replied` | inbound message hook | Agent ที่ assigned conversation นั้น |
| `mention` | internal note creation | User ที่ถูก @mention (เฉพาะคนนั้น) |

**metadata:** customer_replied = `{ conversation_id, customer_name, channel, message_preview (80 chars) }`  
mention = `{ conversation_id, note_id, actor_name, channel, note_preview (80 chars) }`

**ไฟล์ที่แก้:** `apps/omnichat-service/src/messages/messages.service.ts`

---

### Task 1.6 — Event triggers: SLA events
**ทำอะไร:** hook `createNotification` เข้ากับ SLA engine (SLA-02 + SLA-04)

| Event | Hook จากไหน | Recipients |
|-------|------------|------------|
| `sla_due_soon` | SLA timer check (when status → due_soon) | Agent assigned + Supervisor |
| `sla_breached` | SLA-04 breach detection job | Agent assigned เท่านั้น |
| `sla_breached_team` | SLA-04 breach detection job (พร้อมกัน) | Supervisor + Admin |

**Deduplication guard สำหรับ `sla_due_soon`:**
```typescript
// ก่อน createNotification
const key = `${conversationId}:${slaCycleStartAt.toISOString()}`
const exists = await notifDedup.findFirst({ where: { conversationId, eventType: 'sla_due_soon', cycleKey: key } })
if (exists) return  // skip duplicate
await notifDedup.create({ data: { conversationId, eventType: 'sla_due_soon', cycleKey: key } })
```

**ไฟล์ที่แก้:** SLA breach job + SLA status update hook

---

### Task 1.7 — Event triggers: Channel error
**ทำอะไร:** hook `createNotification` เมื่อ channel disconnect หรือ token หมดอายุ

**Recipients:** Admin เท่านั้น (fixed — ไม่ผ่าน notification_rules)  
**metadata:** `{ channel_type, error_description }`

**ไฟล์ที่แก้:** channel integration error handler (ใน omnichat-service หรือ omnichat-gateway)

---

### Task 1.8 — WebSocket delivery: channel `user:{user_id}:notifications`
**ทำอะไร:** push notification payload ไปยัง WebSocket channel ของ user นั้นทันที

**Channel naming:** `user:{user_id}:notifications` — scoped per user เพื่อ security  
**Payload:** full notification record ที่เพิ่ง insert

**ไฟล์ที่แก้:** `apps/omnichat-gateway/` — เพิ่ม channel ใหม่เข้าไปใน gateway

---

### Task 1.9 — Reconnect handling: fetch missed notifications
**ทำอะไร:** เมื่อ client reconnect → client ส่ง `last_seen_at` → server query notifications ที่ miss

**Flow:**
```typescript
// Client ส่ง: { event: 'notifications:catch_up', payload: { last_seen_at: ISO_string } }
// Server query:
WHERE user_id = X AND workspace_id = Y AND created_at > last_seen_at
ORDER BY created_at ASC
// ส่งกลับ array of notifications ที่ miss
```

---

### Task 1.10 — REST APIs: Notifications endpoints
**ทำอะไร:** สร้าง REST endpoints สำหรับ frontend ทุก story ใช้

| Method | Path | ทำอะไร |
|--------|------|--------|
| `GET` | `/notifications` | list (paginated 50/page, sort created_at DESC, filter unread) |
| `GET` | `/notifications/unread-count` | count ที่ยัง is_read = false |
| `PATCH` | `/notifications/:id/read` | mark 1 notification เป็น read |
| `PATCH` | `/notifications/read-all` | mark all ของ user นี้ใน workspace นี้ |

**Location:** `apps/api-gateway/src/omnichat/notifications/` (ใหม่)

---

### Task 1.11 — Retention job: soft-delete after 30 days
**ทำอะไร:** BullMQ job วิ่งรายวัน soft-delete notifications ที่ `created_at < NOW() - 30 days`  
**ทำไม:** ถ้าไม่มี retention table ขยายไม่หยุด

**Infra:** reuse BullMQ pattern จาก SLA-04 breach job

---

## NOTIF-02 — Bell Icon & Unread Badge (3 SP)

> **เป้าหมาย:** Bell icon ใน top nav + badge count real-time — pure frontend, depends on NOTIF-01 WebSocket + API

---

### Task 2.1 — Bell icon component ใน top navigation
**ทำอะไร:** เพิ่ม bell icon ใน top nav bar ฝั่งขวา ข้างๆ profile icon — เห็นทุกหน้า  
**ทำไม:** ไม่มี notification entry point ใน nav เลย

**Location:** `apps/workspace-admin/src/app/(main)/dashboard/_components/top-nav.tsx` (หรือ nav component ที่มีอยู่)

---

### Task 2.2 — Unread badge component
**ทำอะไร:** badge แสดง unread count — 1–99 เลขตรง, >99 แสดง "99+", count = 0 ซ่อน badge  
**ทำไม:** user ต้องรู้จำนวน unread ก่อน open panel

**Load count:** fetch `GET /notifications/unread-count` ตอน page load  
**Location:** `apps/workspace-admin/src/app/(main)/dashboard/_components/notification-bell.tsx` (ใหม่)

---

### Task 2.3 — WebSocket listener: badge increment real-time
**ทำอะไร:** subscribe channel `user:{user_id}:notifications` — เมื่อ event เข้า increment badge ทันที  
**ทำไม:** ถ้า poll อย่างเดียว badge stale จนกว่า user จะ reload

**Optimistic update:** mark all as read → badge หายทันที ก่อน API return

---

### Task 2.4 — Bell active state เมื่อ panel เปิด
**ทำอะไร:** bell icon เปลี่ยน visual เมื่อ panel เปิด (filled หรือ highlighted) — กลับ default เมื่อปิด  
**ทำไม:** user ต้องรู้ว่า panel เปิดอยู่หรือเปล่า

---

## NOTIF-03 — Notification Panel & History (8 SP)

> **เป้าหมาย:** Panel content ทั้งหมด — list, mark read, navigate, infinite scroll, graceful handling

---

### Task 3.1 — Notification panel container
**ทำอะไร:** panel dropdown anchored ใต้ bell — เปิด/ปิดด้วย click bell หรือ click นอก panel  
**ทำไม:** ต้องมี container ก่อนถึงจะ render content ใน NOTIF-03 tasks อื่นได้

**Tech:** z-index สูงกว่า content, position absolute ใต้ bell icon, Intersection Observer สำหรับ infinite scroll sentinel

**Location:** `apps/workspace-admin/src/app/(main)/dashboard/_components/notification-panel.tsx` (ใหม่)

---

### Task 3.2 — TypeScript types: Notification data
**ทำอะไร:** เพิ่ม `Notification` type และ `NotificationEventType` enum ใน frontend types  
**ทำไม:** ทุก component ใน NOTIF-02 และ NOTIF-03 ต้องการ type นี้

**ไฟล์ที่แก้:** `apps/workspace-admin/src/types/omnichat.ts`

```typescript
type NotificationEventType =
  | 'conversation_assigned' | 'conversation_reassigned' | 'conversation_unassigned'
  | 'new_conversation' | 'customer_replied' | 'mention'
  | 'sla_due_soon' | 'sla_breached' | 'sla_breached_team' | 'channel_error'

interface Notification {
  notification_id: string
  event_type: NotificationEventType
  conversation_id: string | null
  actor_id: string | null
  metadata: Record<string, unknown>
  is_read: boolean
  read_at: string | null
  created_at: string
}
```

---

### Task 3.3 — Notification item component
**ทำอะไร:** single item component ตาม design pattern ใน Epic Overview

| Component | รายละเอียด |
|-----------|----------|
| Event icon | วงกลม colored ตาม event group: Assignment=น้ำเงิน / Message=เขียว / SLA=แดง+amber / System=เทา |
| Text | actor + verb + object ตาม text template ใน Epic + channel badge |
| Time | relative time (ดู util ใน Task 3.4) |
| Unread dot | จุดแดง ซ้ายสุด เฉพาะ `is_read = false` |
| Background | is_read=false → พื้นอ่อน / is_read=true → ขาว |
| SLA border | `sla_due_soon`, `sla_breached` → border-left สีแดง |

**Location:** `apps/workspace-admin/src/app/(main)/dashboard/_components/notification-item.tsx` (ใหม่)

---

### Task 3.4 — Relative time util function
**ทำอะไร:** แปลง `created_at` timestamp → Thai relative time string ตาม format table ใน Epic

```typescript
formatRelativeTime(createdAt: Date): string
// < 1min → "เมื่อสักครู่"
// 1–59min → "5 นาทีที่ผ่านมา"
// 1–23h → "2 ชั่วโมงที่ผ่านมา"
// today >23h → "วันนี้ 09:30 น."
// yesterday → "เมื่อวาน 14:22 น."
// 2–6 days → "อังคาร 25 มี.ค."
// > 1 week → "15 ก.พ. 2568"
```

**Location:** `apps/workspace-admin/src/utils/notification-time.ts` (ใหม่)

---

### Task 3.5 — Click notification: navigate + mark read + close panel
**ทำอะไร:** click notification item → navigate ไป conversation → `PATCH /notifications/:id/read` → badge -1 → close panel  
**ทำไม:** เป็น golden path หลักของ Notification Center

**Optimistic:** update `is_read` ใน local state ก่อน API return  
**Note:** ไม่ต้อง pre-check destination ก่อน navigate — handle error หลัง 404

---

### Task 3.6 — Graceful handling เมื่อ destination ถูกลบ
**ทำอะไร:** catch 404 หลัง navigate → แสดง toast ตาม case แล้วอยู่ที่เดิม

| กรณี | toast | action |
|------|-------|--------|
| note ถูกลบ | "โน้ตนี้ถูกลบแล้ว" | อยู่ที่ current page |
| conversation ถูกลบ | "Conversation นี้ไม่พบ" | อยู่ที่ inbox |

**ทำไม:** ห้าม crash — notification ถูก soft-delete ไม่ได้ retroactive เพราะเป็น audit trail

---

### Task 3.7 — "อ่านทั้งหมด" button
**ทำอะไร:** button ใน panel header → `PATCH /notifications/read-all` → clear badge → update all items เป็น read state  
**Optimistic update:** badge หาย + items เปลี่ยน background ทันที ก่อน API return

---

### Task 3.8 — Infinite scroll: load more (50 items/page)
**ทำอะไร:** ใช้ Intersection Observer บน sentinel element ด้านล่าง → fetch page ถัดไป → append ต่อท้าย list  
**ทำไม:** history 30 วันอาจมีหลายร้อย notifications — ไม่ load ทั้งหมดครั้งเดียว

**Loading indicator:** แสดงระหว่าง fetch แต่ละ page

---

### Task 3.9 — Empty state + Panel re-fetch
**ทำอะไร:** ถ้า notification = 0 แสดง icon + "ไม่มีการแจ้งเตือน"  
**Re-fetch logic:** panel re-fetch ทุกครั้งที่เปิด + merge กับ WebSocket events ที่เกิดระหว่าง panel ปิด

---

## NOTIF-04 — Notification Rules Configuration (8 SP)

> **เป้าหมาย:** Settings page สำหรับ Admin/Supervisor config rules + escalation job backend

---

### Task 4.1 — DB migration: `notification_rules` table
**ทำอะไร:** ตารางเก็บ workspace-level config ต่อ event

**Location:** `apps/omnichat-service/prisma/schema.prisma`

```sql
workspace_id        UUID NOT NULL
event_type          ENUM NOT NULL
enabled             BOOLEAN DEFAULT true
recipients          JSONB            -- ["assigned_agent", "supervisor", "admin"]
escalation_minutes  INT NULLABLE     -- เฉพาะ sla_breached
updated_by          UUID
updated_at          TIMESTAMP WITH TIME ZONE
PRIMARY KEY (workspace_id, event_type)
```

**Note:** `mention` + `channel_error` recipients hardcode ใน NotificationService ไม่เก็บใน table

---

### Task 4.2 — API: `GET /notification-rules`
**ทำอะไร:** ดึง rules ทั้งหมดของ workspace — ถ้ายังไม่มี record ให้ return default values ตาม Epic spec  
**ทำไม:** หน้า Settings ต้องโหลดค่าปัจจุบันมาแสดง

**Permission:** `config_notifications` (RBAC — Admin/Supervisor)

---

### Task 4.3 — API: `PATCH /notification-rules`
**ทำอะไร:** upsert rules ที่ user แก้ลง `notification_rules` table  
**ทำไม:** ถ้าไม่มีนี้ กด Save แล้วค่าไม่ persist

**Rule:** บังคับมีผลกับ events ใหม่เท่านั้น — notifications ที่อยู่ใน bell แล้วไม่หาย

---

### Task 4.4 — Wire `notification_rules` check เข้า NotificationService delivery pipeline
**ทำอะไร:** แก้ Task 1.3 stub → query `notification_rules` จริงก่อน createNotification  
**ทำไม:** ตอน NOTIF-01 ทำ pipeline เป็น "pass all" — NOTIF-04 มา wire จริง

**ไฟล์ที่แก้:** `apps/omnichat-service/src/notifications/notification.service.ts`

---

### Task 4.5 — Escalation job: notify supervisor หลัง breach + X minutes
**ทำอะไร:** BullMQ job scan conversations WHERE `sla_status = breached` + `elapsed > escalation_minutes` + ยังไม่มี agent reply → fire escalation notification ไป Supervisor

**Rate-limit:** max 5 escalation notifications per user per minute

```typescript
// query
WHERE sla_status = 'breached'
  AND (NOW() - sla_due_at) > escalation_minutes interval
  AND last_agent_reply_at IS NULL
  AND escalation_sent = false
```

**Infra:** reuse BullMQ — เพิ่ม field `escalation_sent` บน conversations หรือ sla_events

---

### Task 4.6 — UI: Notification Rules settings page
**ทำอะไร:** สร้างหน้า Settings > Notifications > Rules — 4 กลุ่ม event rows  
**ทำไม:** ไม่มีหน้า Notification Rules เลย ต้องสร้างใหม่

**Layout:** แต่ละ event เป็น row: [toggle] [ชื่อ event] [คำอธิบาย] [recipient multi-select] [additional config ถ้ามี]  
**Location:** `apps/workspace-admin/src/app/(main)/dashboard/settings/notifications/rules/page.tsx` (ใหม่)

---

### Task 4.7 — UI: SLA additional config (threshold + escalation input)
**ทำอะไร:** ใน SLA event rows เพิ่ม:
- `sla_due_soon`: แสดง due_soon_minutes แบบ read-only (ดึงจาก SLA-01 config) + tooltip "แก้ที่ Settings > SLA"
- `sla_breached`: input "แจ้งเตือน Supervisor หลัง X นาที ถ้ายังไม่มีการตอบกลับ"

---

### Task 4.8 — RBAC guard: Admin/Supervisor only สำหรับ Notification Rules
**ทำอะไร:** เพิ่ม `config_notifications` permission + guard บน endpoints + redirect ถ้า Agent เข้า Rules page  
**ทำไม:** Agent ต้องเข้าหน้า My Preferences ได้ แต่เข้าหน้า Rules ไม่ได้

---

## NOTIF-05 — Personal Notification Preferences (5 SP)

> **เป้าหมาย:** My Preferences page สำหรับทุก role + wire personal preference check เข้า delivery pipeline

---

### Task 5.1 — DB migration: `notification_preferences` table
**ทำอะไร:** ตารางเก็บ personal mute ต่อ user ต่อ event

**Location:** `apps/omnichat-service/prisma/schema.prisma`

```sql
user_id      UUID NOT NULL
workspace_id UUID NOT NULL
event_type   ENUM NOT NULL
muted        BOOLEAN DEFAULT false
PRIMARY KEY (user_id, workspace_id, event_type)
```

**Default behavior:** ถ้าไม่มี record → ถือว่า unmuted (ไม่ต้อง insert row สำหรับทุก event)

---

### Task 5.2 — API: `GET /notification-preferences` + `PATCH /notification-preferences`
**ทำอะไร:** 2 endpoints สำหรับ load + save personal preferences ของ user ที่ call

**Permission:** ทุก role เรียกได้ (scoped ด้วย `user_id` จาก JWT เสมอ)

---

### Task 5.3 — Wire personal preference check เข้า NotificationService delivery pipeline
**ทำอะไร:** แก้ Task 1.3 stub step 4 → query `notification_preferences` จริงก่อน deliver  
**ทำไม:** ตอน NOTIF-01 ทำ pipeline เป็น "pass all" — NOTIF-05 มา wire จริง

**Query:**
```sql
SELECT muted FROM notification_preferences
WHERE user_id = ? AND workspace_id = ? AND event_type = ?
-- ถ้าไม่มี row → unmuted → deliver
-- ถ้า muted = true → skip user นั้น
```

---

### Task 5.4 — UI: My Preferences settings page
**ทำอะไร:** สร้างหน้า Settings > Notifications > My Preferences — list events ตาม role ที่รับได้  
**ทำไม:** ไม่มีหน้านี้เลย Agent ไม่มีทาง reduce noise

**Location:** `apps/workspace-admin/src/app/(main)/dashboard/settings/notifications/preferences/page.tsx` (ใหม่)

**Role-based event visibility:**
| Event | Agent | Supervisor | Admin |
|-------|-------|-----------|-------|
| conversation_assigned | ✅ | ✅ | ✅ |
| conversation_reassigned | ✅ | ✅ | ✅ |
| conversation_unassigned | — | ✅ | ✅ |
| new_conversation | — | ✅ | ✅ |
| customer_replied | ✅ | ✅ | ✅ |
| mention | ✅ | ✅ | ✅ |
| sla_due_soon | ✅ | ✅ | ✅ |
| sla_breached | ✅ | ✅ | ✅ |
| sla_breached_team | — | ✅ | ✅ |
| channel_error | — | — | ✅ |

---

### Task 5.5 — UI: Greyed out state สำหรับ event ที่ global rule ปิด
**ทำอะไร:** ถ้า event นั้น `notification_rules.enabled = false` → toggle ถูก disable + tooltip  
**ทำไม:** user ต้องรู้ว่า Admin ปิดไว้ ไม่ใช่ bug

**Tooltip text:** "ปิดโดย Admin ของ workspace กรุณาติดต่อ Admin เพื่อเปิดใช้งาน"  
**Implementation:** load global rules พร้อมกับ preferences → merge ก่อน render

---

## Summary

| Story | Task ใหม่ | Task แก้ 🔧 | SP |
|-------|-----------|----------|----|
| NOTIF-01 Infrastructure | 11 | 0 | 13 |
| NOTIF-02 Bell + Badge | 4 | 0 | 3 |
| NOTIF-03 Panel + History | 9 | 0 | 8 |
| NOTIF-04 Rules Config | 8 | 0 | 8 |
| NOTIF-05 Personal Prefs | 5 | 0 | 5 |
| **รวม** | **37** | **0** | **37 SP** |

---

## Dependency ระหว่าง Task

```
[1.1] notifications + notification_dedup tables
    → [1.2] NotificationService core
        → [1.3] delivery pipeline (stub: pass all)
            → [1.4] conversation event triggers
            → [1.5] message event triggers
            → [1.6] SLA event triggers ← ต้องมี SLA-02 + SLA-04 ก่อน
            → [1.7] channel_error trigger
        → [1.8] WebSocket delivery
        → [1.9] reconnect handler
    → [1.10] REST APIs
    → [1.11] retention job (ทำได้ parallel กับ task อื่น)

[2.x] NOTIF-02 ← ต้องมี [1.8] WebSocket + [1.10] GET /notifications/unread-count ก่อน
    → [3.1–3.9] NOTIF-03 ← ต้องมี [2.1] bell + [1.10] REST APIs ก่อน

[4.1] notification_rules table
    → [4.2] GET /notification-rules
    → [4.3] PATCH /notification-rules
    → [4.4] wire rules check เข้า pipeline ← แก้ [1.3] stub
    → [4.5] escalation job ← ต้องมี SLA-04 breach + [4.3] rules ก่อน
    → [4.6–4.7] UI ← ต้องมี [4.2][4.3] ก่อน
    → [4.8] RBAC guard

[5.1] notification_preferences table
    → [5.2] GET/PATCH /notification-preferences
    → [5.3] wire preferences check เข้า pipeline ← แก้ [1.3] stub
    → [5.4–5.5] UI ← ต้องมี [5.2] + [4.2] (สำหรับ greyed out logic) ก่อน
```

---

## ไฟล์หลักที่ต้องสร้าง/แก้ (จาก repo จริง)

| ไฟล์ | สร้าง/แก้เพราะ |
|------|---------------|
| `apps/omnichat-service/prisma/schema.prisma` | Task 1.1, 4.1, 5.1 — 3 tables ใหม่ |
| `apps/omnichat-service/src/notifications/notification.service.ts` | Task 1.2, 1.3, 4.4, 5.3 — core service |
| `apps/omnichat-service/src/conversations/conversations.service.ts` | Task 1.4 — conversation event triggers |
| `apps/omnichat-service/src/messages/messages.service.ts` | Task 1.5 — message event triggers |
| `apps/omnichat-gateway/` (SLA breach job) | Task 1.6 — SLA event triggers |
| `apps/api-gateway/src/omnichat/notifications/` | Task 1.10, 4.2, 4.3, 5.2 — REST APIs ใหม่ |
| `apps/workspace-admin/src/app/(main)/dashboard/_components/top-nav.tsx` | Task 2.1 — bell icon |
| `apps/workspace-admin/src/app/(main)/dashboard/_components/notification-bell.tsx` | Task 2.2–2.4 — bell + badge |
| `apps/workspace-admin/src/app/(main)/dashboard/_components/notification-panel.tsx` | Task 3.1 — panel container |
| `apps/workspace-admin/src/app/(main)/dashboard/_components/notification-item.tsx` | Task 3.3 — item component |
| `apps/workspace-admin/src/utils/notification-time.ts` | Task 3.4 — relative time util |
| `apps/workspace-admin/src/types/omnichat.ts` | Task 3.2 — Notification types |
| `apps/workspace-admin/src/app/(main)/dashboard/settings/notifications/rules/page.tsx` | Task 4.6–4.7 — Rules page |
| `apps/workspace-admin/src/app/(main)/dashboard/settings/notifications/preferences/page.tsx` | Task 5.4–5.5 — My Preferences page |
