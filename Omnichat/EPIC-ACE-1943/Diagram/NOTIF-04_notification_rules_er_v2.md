## ER Diagram — NOTIF-04: Notification Rules Configuration (v2)

> **v2 (2026-06-12):** escalation notification เปลี่ยนเป็น event_type ใหม่ `sla_escalation` (เดิม `sla_breached_team` + `metadata.is_escalation`) — เหตุผลใน [NOTIF-04_escalation_v3_sequence.md](./NOTIF-04_escalation_v3_sequence.md)
> ไฟล์เดิม: [NOTIF-04_notification_rules_er.md](./NOTIF-04_notification_rules_er.md) — **superseded** เก็บไว้อ้างอิง

> Prisma model names = PascalCase / DB table names (@@map) = snake_case

```mermaid
erDiagram

  notification_rules {
    string    id                  PK  "uuid"
    string    tenant_id               "logical ref — no FK (คนละ DB)"
    string    event_type              "10 configurable values — ไม่มี sla_escalation"
    boolean   enabled                 "default true"
    json      recipients              "assigned_agent | supervisor | admin"
    int       escalation_minutes      "nullable — sla_breached_team only"
    string    updated_by              "nullable — user_id ของคนแก้ล่าสุด"
    datetime  created_at
    datetime  updated_at
  }

  notifications {
    string    id                  PK  "uuid"
    string    tenant_id               "logical ref — no FK (คนละ DB)"
    string    user_id
    string    event_type              "10 ค่า configurable + sla_escalation"
    string    conversation_id         "nullable"
    string    actor_id                "nullable"
    json      metadata
    boolean   is_read                 "default false"
    datetime  read_at                 "nullable"
    datetime  created_at
  }

  workspace_sla_configs {
    string    id                  PK  "uuid"
    string    tenant_id               "logical ref — no FK (คนละ DB)"
    boolean   enabled
    int       due_soon_minutes        "source of truth for sla_due_soon threshold"
    boolean   bh_aware
    datetime  created_at
    datetime  updated_at
  }

  tenants {
    string    id                  PK  "uuid"
    string    name
    string    slug
    datetime  created_at
  }

  tenants                ||--o{  notification_rules     : "has rules (logical, cross-service)"
  tenants                ||--o{  notifications           : "has notifications (logical, cross-service)"
  tenants                ||--o|  workspace_sla_configs  : "has sla config (logical, cross-service)"
```

**Prisma model → DB table mapping + ตารางไหนอยู่ service ไหน**

| Prisma model         | DB table (`@@map`) = entity name in diagram | Service / Database (Prisma schema แยกกัน) |
| -------------------- | ------------------------------------------- | ------------------------------------------ |
| `NotificationRule`   | `notification_rules`                        | **notification-service DB** (NOTIF-04 เพิ่ม) |
| `Notification`       | `notifications`                             | **notification-service DB** (NOTIF-01 เพิ่ม) |
| `WorkspaceSlaConfig` | `workspace_sla_configs`                     | **omnichat-service DB** (มีอยู่แล้ว — SLA-01) |
| `Tenant`             | `tenants`                                   | **tenant-service DB** (มีอยู่แล้ว)           |

> ⚠️ **3 databases คนละ service — ความสัมพันธ์ใน diagram เป็น logical ทั้งหมด ไม่มี FK constraint จริง:**
>
> - JOIN ข้ามตารางต่าง service **ไม่ได้** — ต้องยิง TCP ถาม service เจ้าของ (เหตุผลเดียวกับที่ escalation dedup ใช้ `conversation_sla_events` ฝั่ง omnichat ได้ใน query เดียว แต่ใช้ `notifications` ไม่ได้)
> - **ไม่มี cascade delete** — tenant ถูกลบ rows ใน `notification_rules` / `notifications` ไม่หายเอง (orphan rows — ยอมรับได้ / จัดการด้วย cleanup job ภายหลัง)
> - Prisma ของ notification-service ไม่มี model `Tenant` — ห้ามพยายามเขียน `@relation` ไปหา

**event_type values**

`notification_rules` — 10 ค่า configurable (1 row ต่อค่า ต่อ tenant):

```
conversation_assigned | conversation_reassigned | conversation_unassigned
new_conversation | customer_replied | mention
sla_due_soon | sla_breached | sla_breached_team | channel_error
```

`notifications` — 10 ค่าข้างบน + **`sla_escalation`**:

> `sla_escalation` เป็น notification event อย่างเดียว — **ไม่มี row ใน `notification_rules` และไม่ configurable** (ไม่โผล่ในหน้า settings) — `checkGlobalRule` special-case อ่าน `enabled` + `escalation_minutes` จาก row `sla_breached_team` แล้ว hardcode recipients = supervisor (ดู `NOTIF-04_escalation_v3_sequence.md`)
> ค่า enum อยู่ที่ `packages/shared` `NotificationEventType` — เพิ่ม `SLA_ESCALATION = 'sla_escalation'` 1 บรรทัด, **ไม่มี DB migration** (column เป็น TEXT)

**recipients JSON** — per `NotificationRule` row

| value            | meaning                                       |
| ---------------- | --------------------------------------------- |
| `assigned_agent` | agent currently assigned to the conversation  |
| `supervisor`     | all members with supervisor role in workspace |
| `admin`          | all members with admin role in workspace      |

> `mention` and `channel_error` recipients are **hardcoded** in notification logic — column `recipients` ของ 2 event นี้ไม่ถูกใช้ตอน delivery (เก็บเป็น `[]`) และตอน Save ถ้าส่งค่ามาแก้จะถูก **reject 400** (ดู validation ใน Diagram 2)

> `due_soon_minutes` ไม่เก็บใน `notification_rules` — UI อ่านตรงจาก `workspace_sla_configs.due_soon_minutes` (read-only display เท่านั้น, แก้ได้ที่ SLA settings เท่านั้น)

**Column notes**

| column               | detail                                                                                                                                                    |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `escalation_minutes` | nullable; only meaningful for `event_type = sla_breached_team`; X minutes after breach with no agent reply → escalation notification fires to supervisors **as `event_type: sla_escalation`** — ปิด `sla_breached_team` (`enabled = false`) = ปิด escalation ด้วย (intended ✅ confirmed 2026-06-12) |
| `updated_by`         | nullable; user_id จาก JWT ของคนที่กด Save — audit ว่าใครแก้ rule (`null` = row จาก seed/default ยังไม่มีใครแก้)                                              |

**Unique constraint**

```prisma
@@unique([tenant_id, event_type])
```

One row per event type per workspace — upsert on save.

**Indexes**

```prisma
// notification_rules
@@index([tenant_id])           // checkGlobalRule() lookup
@@index([tenant_id, enabled])  // filter disabled rules fast

// notifications
@@index([tenant_id, user_id, is_read, created_at])
@@index([tenant_id, user_id, conversation_id, is_read])
```

**Relationship with NOTIF-01 delivery pipeline**

`checkGlobalRule(tenant_id, event_type)` in `notification-service`:

0. ถ้า `event_type = sla_escalation` → **special-case ก่อนทุกอย่าง**: อ่าน row `sla_breached_team` — `enabled = false` → skip, else recipients = hardcoded `[supervisor]` (ไม่ใช้ `rules.recipients` และห้ามตกไป `DEFAULT_RULES` — ไม่มี key นี้)
1. SELECT `notification_rules` WHERE `tenant_id` + `event_type`
2. If row not found → fallback ใช้ `DEFAULT_RULES[event_type]` (hardcoded map — ดูด้านล่าง)
3. If `enabled = false` → skip `INSERT notifications`
4. If `enabled = true` → use `recipients` to resolve target `user_id` list, then `INSERT notifications` per recipient

**DEFAULT_RULES — fallback + seed source เดียวกัน**

```typescript
// notification-service — single source of truth สำหรับค่า default
const DEFAULT_RULES: Record<EventType, { enabled: boolean; recipients: Role[] }> = {
  conversation_assigned:   { enabled: true, recipients: ['assigned_agent'] },
  conversation_reassigned: { enabled: true, recipients: ['assigned_agent'] }, // = agent คนเดิม
  conversation_unassigned: { enabled: true, recipients: ['supervisor', 'admin'] },
  new_conversation:        { enabled: true, recipients: ['supervisor', 'admin'] },
  customer_replied:        { enabled: true, recipients: ['assigned_agent'] },
  mention:                 { enabled: true, recipients: [] }, // hardcoded: mentioned_agent_ids
  sla_due_soon:            { enabled: true, recipients: ['assigned_agent', 'supervisor'] },
  sla_breached:            { enabled: true, recipients: ['assigned_agent'] },
  sla_breached_team:       { enabled: true, recipients: ['supervisor', 'admin'] },
  channel_error:           { enabled: true, recipients: [] }, // hardcoded: admin only
};
// ไม่มี key `sla_escalation` โดยตั้งใจ — ไม่ใช่ configurable event
// (checkGlobalRule special-case อ่าน row sla_breached_team ก่อนถึง fallback นี้)
```

ใช้ 2 ที่ — **ห้ามเขียนค่า default ซ้ำที่อื่น**:

1. **Seed** ตอน workspace created / data migration → INSERT จาก map นี้
2. **Fallback** ใน `checkGlobalRule()` เมื่อ row not found — เคสที่เกิดได้จริง:
   - seed ตอน workspace created fail เงียบ (fire-and-forget ไม่มี retry)
   - data migration ตกบาง tenant
   - เพิ่ม event_type ใหม่ในอนาคต → tenant เก่าไม่มี row ของ event ใหม่ (เคสหลัก)

**Escalation job (v3)** — ดู diagram เต็มใน `NOTIF-04_escalation_v3_sequence.md`

```
markEscalated() ใน SlaCronService.runCycle() (omnichat-service — lock เดิม)

→ TCP send get_escalation_configs ครั้งเดียวต่อรอบ
   (SELECT notification_rules WHERE escalation_minutes IS NOT NULL AND enabled = true)
→ scan conversations WHERE sla_status = breached
   AND sla_due_at <= NOW() - escalation_minutes
   AND NOT EXISTS (conversation_sla_events
                   WHERE event_type = escalated AND cycle_number = ปัจจุบัน)
   LIMIT 500 ต่อรอบ (batch เดียวกับ markBreached — throughput control ตัวจริง)
   ← dedup ในตัว query — conv ที่ fire แล้วไม่ถูกคืนอีก (steady state = 0 rows)
→ INSERT conversation_sla_events (escalated, cycle_number) — unique constraint กัน race
→ emit create_notification 1 ครั้งต่อ conversation
   { event_type: sla_escalation, metadata: { cycle_number, ... } }
→ NotiSvc fan-out supervisors — INSERT + PUBLISH ครบทุกใบ
   (ไม่มี rate-limit ที่ delivery — UX เป็น bell badge อย่างเดียว ไม่มี toast
    ดูเหตุผลใน NOTIF-04_escalation_v3_sequence.md)
```

> หมายเหตุ: `conversation_sla_events.event_type = 'escalated'` (omnichat-service — ใช้ dedup ภายใน) เป็น**คนละ field คนละ table** กับ `notifications.event_type = 'sla_escalation'` (notification-service — ตัว notification ที่ user เห็น)

**Escalation notification metadata shape**

```json
{
  "customer_name": "...",
  "channel": "line",
  "elapsed_minutes": 45,
  "cycle_number": 2
}
```

> escalation แยกจาก `sla_breached_team` ด้วย **event_type `sla_escalation`** — NotiSvc special-case recipients (supervisor เท่านั้น) และ NOTIF-02/03 bell UI switch ตาม event_type ได้ตรงๆ ไม่ต้องอ่าน metadata — metadata เหลือเฉพาะ display payload (**ไม่มี logic flag**) — **dedup ไม่ได้ใช้ตาราง `notifications`** (ย้ายไป `conversation_sla_events` ฝั่ง omnichat ตาม v2) `cycle_number` เก็บไว้เพื่อ traceability
