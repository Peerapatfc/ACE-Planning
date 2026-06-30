# EPIC-ACE-2211: Story Task Breakdown

Task แต่ละ story พร้อมคำอธิบายว่าทำอะไร — **reconcile กับ repo จริง (`ace/` @ branch `dev`)** ทุก path/field/enum verify แล้วพร้อม `file:line` anchor

> **Legend:** 🔧 มีโค้ดอยู่แล้วแต่ต้องแก้ | (ไม่มีไอคอน) สร้างใหม่ทั้งหมด | ⚠️ จุดที่แผนเดิมระบุผิดจากของจริง — แก้แล้วในเอกสารนี้

---

## ⚠️ สิ่งที่แผนเดิมระบุผิด (แก้แล้ว — อ่านก่อน)

| แผนเดิมเขียนว่า | ของจริงใน repo | ผลกระทบ |
|----------------|----------------|---------|
| `sender_type` เป็น enum `human/bot/system` | เป็น **plain `String`** ที่ `schema.prisma:262` ค่า `contact \| agent \| system` (ไม่มี enum ใน Prisma) | Task 3.4 ไม่ใช่ enum migration — เป็น app-level convention |
| `first_human_response_at` ใช้นับ FRT | **ไม่มี field นี้** — FRT นับจาก `Conversation.sla_first_inbound_at` (`schema.prisma:214`) + SLA state machine ใน `messages.service.ts:103-262` + `ConversationSlaEvent.response_time_sec` | Task 3.x SLA attribution ต้องอ้างชื่อ field จริง |
| `conversation_tags` มี `tagged_by_type` + `tagged_by_rule_id` | **ไม่มี** — `ConversationTag` (`schema.prisma:373-390`) มี `is_system`, `created_by_id`, `deleted_by_id`, `deleted_at` (soft-delete) | Task 4.2 ต้อง add column จริงเข้า model จริง |
| Tag application อยู่ใน `src/tags/` | CRUD อยู่ที่ `src/tags/` ✓ แต่ **การติด tag ให้ conversation** อยู่ที่ `ConversationsService.updateConversationTags()` `conversations.service.ts:1941` (PATCH `/conversations/:id/tags`) | Task 4.1 ต้องเรียก conversations service ไม่ใช่ tags |
| Business hours อยู่ใน omnichat-service (SETTINGS-02) | logic อยู่ที่ `packages/shared/src/utils/business-hours.utils.ts` (`nextBhOpenAt`, `calculateSlaDueAt`); **config เก็บที่ `tenant-service`** ตาราง `business_hour_days` (per-tenant 7 แถว) | Task 2.5 ต้องดึง config ข้าม service + import shared util |
| BullMQ worker อยู่ใน `omnichat-gateway` + SLA breach job ใช้ BullMQ | gateway ใช้ **AWS SQS**; SLA breach เป็น **`@Cron`** ที่ `sla/sla-cron.service.ts:58` + Redis lock; **BullMQ อยู่ที่ `ai-ingestion-service` + `ai-extractor-worker`** | Task 3.1 retry pattern ต้องเลือกใหม่ (ดู 3.1) |
| Settings shell อยู่ที่ `(main)/dashboard/settings/` | จริงคือ `(main)/settings/` (เป็น sibling ของ `dashboard` ไม่ใช่ลูก) | ทุก path frontend (1.4–1.8, 2.7, 2.8, 3.5, 4.3, 4.4) แก้แล้ว |
| api-gateway ใหม่อยู่ที่ `.../omnichat/automation-rules/` (per-feature folder) | convention จริงคือ flat `controllers/` `services/` `dto/` ใน `src/omnichat/` (เช่น `sla.controller.ts`) register ใน `omnichat.module.ts` | Task 1.2 path แก้แล้ว |
| RBAC แยก permission per-action (create/edit/delete/read) | permission เป็น **coarse action** (`config_sla`, `view_sla`) — ไม่มี CRUD suffix | Task 1.3 แยก Supervisor/Admin ต้อง enforce ใน app logic ไม่ใช่ permission (ดู 1.3) |
| Shopee/TikTok เป็น channel ที่ส่ง auto-reply ได้ | **Shopee ไม่มี strategy เลย** (มีแค่ enum + stub poller); **TikTok `pushMessage` คืน `'not yet supported'`** (`tiktok.strategy.ts:173`) | Task 3.1 ต้อง guard channel ที่ส่งไม่ได้ (ดู 3.1) |

---

## 🎨 Mockup Reconciliation (อัปเดตหลังได้ UI mockup — ปิด D6 บางส่วน)

เทียบ mockup 7 จอ (Rule List · New Rule · Step 1 Trigger · Step 2 auto-reply · Step 2 add-tag · Saved) กับ spec:

**ตรงกับ spec ✅:** action-first entry · 2-step wizard + step indicator (step ผ่านแล้ว = ✓ เขียว) · AND/OR toggle · condition card (type/operator/value/×) · variable toolbar + live preview + badge "Auto-reply" · cooldown (required + unit dropdown) · auto-gen rule name ("Auto-reply · …" / "Tag · …", แก้ได้หลัง save) · tag inline create (+ Create) · append-only info · active/inactive section + counter (2/20) · fired count · toggle · kebab · created/updated-by · role-gated view (Admin/Supervisor/Agent + "Viewing as: … Full access")

**ต่างจาก spec / ต้องตัดสินใจ ⚠️:**

| # | จุด | mockup | spec/breakdown | action |
|---|-----|--------|----------------|--------|
| M1 | Keyword หลายคำต่อ condition | `contains 'ยกเลิก', 'cancel'` | value เดี่ยว | **แก้แล้ว** (1.1 schema → array, 2.3 evaluator → match คำใดคำหนึ่ง) |
| M2 | Test panel | inline ในการ์ด Keyword (`🧪 ทดสอบ…`) | แยก panel ใต้ cards (2.8) | ใช้ inline ตาม mockup (ง่ายกว่า) → ปรับ 2.8 |
| M3 | Fallback value ต่อ variable | **ไม่มีใน Step 2** | มี (3.2, 3.5) | **Decision D8:** เก็บ (เพิ่ม design) หรือ ตัด (YAGNI) |
| M4 | Pills filter (All/Auto-reply/Tag) | **ไม่มี** | มี (1.4) | **Decision D9:** ตัด (≤20 rules) หรือ เพิ่ม |
| M5 | Cooldown default | 30 นาที | 5 นาที | เลือก default ให้ตรงกัน (เล็กน้อย) |
| M6 | Action-first entry | full page | "modal" (1.6) | page ก็ได้ — ปรับถ้อยคำ 1.6 |
| M7 | Tag picker | chips คลิกเลือก (ไม่มี search box) | search + checkbox list (4.3) | ถ้า tag เยอะต้องมี search; ตอนนี้ chips พอ — confirm |
| M8 | ขอบเขตการมีผล | "มีผลกับ conversation ที่เข้ามาหลัง save เท่านั้น" (จอ Saved) | **ไม่มีใน spec** | **เพิ่มเป็น requirement** → engine (2.1) ไม่ย้อนหลัง conversation เดิม |

**🔴 ขัดกับ reality (สำคัญ):**

| จุด | mockup แสดง | ความจริง | action |
|-----|-------------|----------|--------|
| Shopee/TikTok auto-reply | Rule List มี "Auto-reply · Shopee new"; channel picker (Step 1 auto-reply) เลือก Shopee/TikTok ได้ **ไม่มี warning** | Shopee/TikTok ส่ง auto-reply ไม่ได้ (ดูตารางบนสุด) | **Decision D5 (ชัดขึ้น):** mockup = allow เงียบ ๆ → ต้องเลือก: ซ่อน/disable 2 channel ใน picker ของ *auto-reply* rule, โชว์ warning, หรือ allow+skip+log |

**design ยังไม่ครอบ (ต้องเพิ่ม):**
- **Business hours condition card** (workspace toggle + day/time picker + midnight/timezone) — evaluator หนักสุด (2.5) แต่ mockup ไม่โชว์ UI → **D6 ยังเปิดเฉพาะส่วน BH**
- **Delete confirmation dialog** (1.8) — mockup ไม่โชว์
- add-tag preview "จะติด label เหล่านี้: […]" (mockup ใช้ chip selection แทน — อาจไม่ต้องมี preview แยก)

---

## สิ่งที่มีอยู่แล้วใน repo (reuse — อย่าทำซ้ำ)

| สิ่งที่มี | ไฟล์จริง (`file:line`) | หมายเหตุ reuse |
|----------|------------------------|----------------|
| Inbound message handler | `apps/omnichat-service/src/messages/messages.service.ts:85` `createInbound()` | hook rule engine ใน post-save block (~`:290-346`) — non-blocking side-effect |
| Ingestion entry จริง | `apps/omnichat-normalizer-worker/src/worker/worker.service.ts:235` (SQS consumer) → `:344` hardcode `sender_type:'contact'` | normalizer คือ true entry; omnichat-service คือ persistence layer |
| Outbound send (per-channel) | `apps/omnichat-service/src/channel-accounts/strategies/strategy.registry.ts` + `ConversationsService.sendMessage()` `conversations.service.ts:649-732` | reuse สำหรับ auto-reply executor — รองรับ **LINE/FB/IG/Lazada เท่านั้น** |
| AI reply pattern (อ้างอิงได้) | `apps/omnichat-service/src/messages/messages.service.ts` `processAiReply()` ~`:691-728` | ส่ง auto-reply ด้วย strategy.pushMessage แล้ว persist (ตอนนี้ใช้ `sender_type:'agent'`) |
| Conversation tag apply | `apps/omnichat-service/src/conversations/conversations.service.ts:1941` `updateConversationTags()` + controller `:143` | reuse สำหรับ auto-tag executor (action `'add'`) |
| Tag CRUD | `apps/omnichat-service/src/tags/tags.service.ts` (`createTag/listTags/updateTag/deleteTag`) | reuse สำหรับ create-inline ใน wizard |
| Business hours logic | `packages/shared/src/utils/business-hours.utils.ts` (`nextBhOpenAt`, `calculateSlaDueAt`) | handle timezone/midnight/dual-shift แล้ว — detect inside BH ด้วย `nextBhOpenAt(ts)===ts` |
| Business hours config | `apps/tenant-service` ตาราง `business_hour_days` + `tenants.service.ts:69-115` converters | per-**tenant** ดึงข้าม service |
| SLA cron (worker pattern ref) | `apps/omnichat-service/src/sla/sla-cron.service.ts:58` `@Cron` + Redis lock | pattern สำหรับงาน scheduled (ไม่ใช่ queue) |
| BullMQ pattern (retry ref) | `apps/ai-ingestion-service/src/ingestions/ingestions.service.ts:45-58` (`attempts:3, backoff:exponential 5000ms`) + `ai-extractor-worker` `@Processor`/`WorkerHost` | pattern สำหรับ retry job ถ้าทำ auto-reply แบบ queue |
| Inline retry pattern (alt) | `apps/omnichat-gateway/src/queue/queue.service.ts` `executeWithRetry()` | pattern retry แบบ inline ถ้าไม่ทำ queue |
| Notification rule engine (closest analog) | `apps/notification-service/.../notification-rules.service.ts:132-155` `getEffectiveRule()` (inline, sync, Redis cache 3600s) | rule engine รันแบบ inline ได้ — ไม่จำเป็นต้อง queue |
| RBAC permission list | `packages/shared/src/types/rbac.types.ts:6-20` `PERMISSION_ACTIONS` | เพิ่ม `config_automation_rules` (+ optional `view_automation_rules`) |
| RBAC seed | `apps/user-service/prisma/seed.ts` `PERMISSION_MATRIX` (`:16-100`) + `seedPermissions()` (`:102-128`) | assign permission → role ตรงนี้ |
| RBAC guard | `apps/api-gateway/src/permissions/` `permission.guard.ts` + `permission.decorator.ts` (`@RequirePermission`) | endpoint ใหม่ใช้ decorator นี้ |
| Frontend permission enum | `apps/workspace-admin/src/lib/permissions.ts` | เพิ่ม `CONFIG_AUTOMATION_RULES` |
| Settings shell | `apps/workspace-admin/src/app/(main)/settings/` (`sla/`, `notification-rules/` เป็น sibling ใกล้สุด) | เพิ่ม `automation/rules/` ตรงนี้ |
| api-gateway omnichat convention | `apps/api-gateway/src/omnichat/` (`controllers/`, `services/`, `dto/`, `omnichat.module.ts`) global prefix `api/v1` | mirror `sla.controller.ts` / `services/sla.service.ts` |
| Schema location | `apps/omnichat-service/prisma/schema.prisma` (Prisma + PostgreSQL) | Message `:251-292`, Conversation `:194-249`, ConversationTag `:373-390` |

> **หมายเหตุ "workspace" vs "tenant":** ทั้ง repo ใช้ `tenant_id` เป็น key จริง ("workspace" เป็นคำ product-facing) — ใน schema/API ทุกที่ใช้ `tenant_id`

---

## RA-01 — Rule Management (CRUD) (8 SP)

> **เป้าหมาย:** DB + API CRUD สำหรับ automation rules + frontend shell (list, wizard, permission)

---

### Task 1.1 — DB migration: `automation_rules` table
**ทำอะไร:** สร้างตารางหลักเก็บ rule configuration

**Location:** `apps/omnichat-service/prisma/schema.prisma` (Prisma model + migration)

```prisma
model AutomationRule {
  id            String    @id @default(uuid())
  tenant_id     String                          // ⚠️ tenant_id ไม่ใช่ workspace_id
  name          String
  conditions    Json      @db.JsonB             // { logic: 'and'|'or', items: [...] }
  action_type   String                          // 'auto_reply' | 'add_tag' (String + comment, ตาม convention repo — ไม่ใช้ Prisma enum)
  action_config Json      @db.JsonB
  is_active     Boolean   @default(true)
  fired_count   Int       @default(0)
  created_by_id String
  updated_by_id String?
  created_at    DateTime  @default(now())
  updated_at    DateTime  @updatedAt

  @@index([tenant_id, is_active, created_at])    // list + execution order
  @@map("automation_rules")
}
```

**⚠️ Convention note:** repo เก็บ field แบบ enum-ish เป็น `String` + comment (เช่น `status`, `sender_type`) ไม่ใช้ Prisma `enum` — ทำตามนี้เพื่อ consistency

**conditions JSONB structure:**
```json
{
  "logic": "and",
  "items": [
    { "type": "keyword", "operator": "contains", "value": ["ยกเลิก", "cancel"] },
    { "type": "channel", "value": ["lazada"] },
    { "type": "business_hours", "operator": "outside", "use_workspace": true }
  ]
}
```

---

### Task 1.2 — API: CRUD endpoints (api-gateway → omnichat-service)
**ทำอะไร:** REST endpoints ครบ CRUD + toggle ที่ api-gateway proxy ไป omnichat-service

| Method | Path (`api/v1` prefix) | ทำอะไร |
|--------|------------------------|--------|
| `GET` | `/omnichat/automation-rules` | list ทุก rule ของ tenant แยก active/inactive |
| `POST` | `/omnichat/automation-rules` | สร้าง rule — block ถ้า active = 20 |
| `GET` | `/omnichat/automation-rules/:id` | ดึง rule เดียว (สำหรับ edit pre-fill) |
| `PATCH` | `/omnichat/automation-rules/:id` | แก้ไข rule |
| `DELETE` | `/omnichat/automation-rules/:id` | hard delete — Admin เท่านั้น (enforce ใน controller) |
| `PATCH` | `/omnichat/automation-rules/:id/toggle` | enable/disable |

**⚠️ Location (แก้):** **ไม่ใช่** per-feature folder — ทำตาม convention จริง:
- `apps/api-gateway/src/omnichat/controllers/automation-rules.controller.ts` (mirror `sla.controller.ts`)
- `apps/api-gateway/src/omnichat/services/automation-rules.service.ts` (HttpService axios → omnichat-service, ส่ง `x-tenant-id` header)
- `apps/api-gateway/src/omnichat/dto/*.dto.ts`
- register controller+service ใน `apps/api-gateway/src/omnichat/omnichat.module.ts`
- backend CRUD จริงอยู่ที่ `apps/omnichat-service/src/automation-rules/` (controller/service/module — NestJS)

**Permission:** `@RequirePermission('config_automation_rules')` บน write endpoints, `view_automation_rules` บน GET (ดู 1.3)

---

### Task 1.3 — RBAC: `config_automation_rules` permission
**ทำอะไร:** เพิ่ม permission เข้า RBAC + seed ให้ role

**ไฟล์ที่แก้ (paths จริง):**
- `packages/shared/src/types/rbac.types.ts:6-20` 🔧 — เพิ่ม `"config_automation_rules"` (+ optional `"view_automation_rules"`) เข้า `PERMISSION_ACTIONS`
- `apps/user-service/prisma/seed.ts` 🔧 — เพิ่ม entry ใน `PERMISSION_MATRIX` (`:16-100`); assign `config_automation_rules` → `['admin','supervisor']`, `view_automation_rules` → ทุก role
- `apps/workspace-admin/src/lib/permissions.ts` 🔧 — เพิ่ม `CONFIG_AUTOMATION_RULES = 'config_automation_rules'`

**⚠️ Granularity caveat:** permission เป็น coarse action — **แยกไม่ได้** ว่า Supervisor "create/edit แต่ลบไม่ได้" ผ่าน permission อย่างเดียว ทางเลือก:
- (แนะนำ) ใช้ `config_automation_rules` ครอบ create/edit/toggle แล้ว **hard-check `role === 'admin'` ใน DELETE controller**
- หรือเพิ่ม action แยก `delete_automation_rules` ให้เฉพาะ admin

---

### Task 1.4 — UI: Rule list page
**ทำอะไร:** หน้า Settings > Automation > Rules แสดง Active / Inactive

**⚠️ Location (แก้ — ไม่มี `dashboard/`):** `apps/workspace-admin/src/app/(main)/settings/automation/rules/page.tsx`

**ต้องสร้างครบ convention (อ้าง `settings/sla/`, `settings/notification-rules/`):**
- `automation/rules/layout.tsx` — permission gate: `checkPermission({ some: [Permission.CONFIG_AUTOMATION_RULES] })` → redirect `/unauthorized`
- `automation/rules/page.tsx` — header (`@container/main` wrapper, `<h1>` + `<p>`) + render main component
- `automation/rules/_components/` — UI components
- `automation/rules/_hooks/use-automation-rules.ts` — `useQuery` + `useQueryClient`
- `automation/rules/_lib/automation-rules-constants.ts` — zod schema, channel labels, defaults
- `apps/workspace-admin/src/server/automation-rules.ts` — server actions (`'use server'`, คืน `ActionResult<T>`, เรียก `httpClient`)
- เพิ่ม section เข้า `settings/_lib/settings-sections.ts` + nav `src/navigation/sidebar/sidebar-items.ts`

**⚠️ Complexity note:** หน้า settings เดิม (sla, notification-rules) เป็น single-form ธรรมดา — UI automation rules (list + wizard + modal) **หนักกว่ามาก** ไม่มี pattern เดิมตรงเป๊ะ ใช้ notification-rules เป็น reference เฉพาะ plumbing (permission/layout/server-action/useQuery)

**Layout:** Header "Automation Rules" + "Active (X/20)" + "+ New Rule" + pills (All / Auto-reply / Add tag); Active section (sorted `created_at`); Inactive section (collapsed)

---

### Task 1.5 — UI: Rule card component
**ทำอะไร:** card แสดง name, summaries, toggle, fired count, kebab

| Element | รายละเอียด |
|---------|----------|
| Rule name | ชื่อ + badge action type (Auto-reply / Add tag) |
| Trigger summary | เช่น "Keyword: ยกเลิก · Lazada" |
| Action summary | เช่น "Auto-reply · cooldown 5 min" |
| Toggle | enable/disable inline (`useMutation` + invalidate query — ไม่ reload) |
| Fired count | "ทำงานแล้ว 87 ครั้ง" |
| created_by/updated_by | subtle text + relative time |
| Kebab (⋮) | Edit / Delete (Delete เฉพาะ Admin) |

**Location:** `apps/workspace-admin/src/app/(main)/settings/automation/rules/_components/rule-card.tsx`

---

### Task 1.6 — UI: Action-first entry modal
**ทำอะไร:** modal เปิดเมื่อกด "+ New Rule" ถามก่อนว่าจะทำ action อะไร

**Location:** `.../settings/automation/rules/_components/action-first-modal.tsx` (ใช้ Dialog จาก `src/components/ui/`)

---

### Task 1.7 — UI: Rule wizard shell (2 steps) + step indicator
**ทำอะไร:** wizard container ใช้ร่วม create + edit

```
[Step 1: Trigger Conditions] → [Step 2: Action Detail (ขึ้นกับ action)] → [Review/Save]
```
- Step indicator — step ที่ผ่านแล้ว clickable
- Auto-generate rule name ตอน review: `Action · Trigger` เช่น "Auto-reply · Outside hours" (แก้ได้ก่อน save)
- Edit mode: pre-fill จาก `GET /omnichat/automation-rules/:id`

**Location:** `.../settings/automation/rules/_components/rule-wizard.tsx`

---

### Task 1.8 — UI: Hard delete confirmation dialog
**ทำอะไร:** dialog ยืนยันก่อน hard delete

```
ลบ rule "Auto-reply · Outside hours"?
Rule นี้ทำงานไปแล้ว 87 ครั้ง
⚠️ จะถูกลบถาวร ไม่สามารถกู้คืนได้
[ลบถาวร]  [Cancel]
```

**Location:** `.../settings/automation/rules/_components/delete-rule-dialog.tsx`

---

## RA-02 — Define Trigger Conditions (5 SP)

> **เป้าหมาย:** Rule evaluation engine (BE) + Wizard Step 1 UI + test panel

---

### Task 2.1 — Rule engine: message hook + evaluation orchestrator
**ทำอะไร:** hook `evaluateAndExecute()` เข้า inbound message handler

**Location (hook):** `apps/omnichat-service/src/messages/messages.service.ts` 🔧 — ใน post-save block (~`:290-346`) ที่มี meilisearch sync / AI auto-assign / Redis publish อยู่แล้ว → เพิ่มเป็น **non-blocking side-effect** (`.then()` / fire-and-forget) ไม่ให้ block การ save

```typescript
// post-save hook (~messages.service.ts:290-346) — รันเฉพาะ inbound จากลูกค้า
if (message.sender_type === 'contact') {              // ⚠️ 'contact' ไม่ใช่ 'human'
  void this.ruleEngine.evaluateAndExecute(conversation, message)  // non-blocking
}
```

**Location (engine):** `apps/omnichat-service/src/automation-rules/rule-engine.service.ts` (ใหม่, NestJS `@Injectable`)

**⚠️ Scope (จาก mockup จอ Saved):** rule "มีผลกับ conversation ที่เข้ามาหลัง save เท่านั้น" — engine evaluate เฉพาะ message ที่เข้า**หลัง** rule ถูกสร้าง ไม่ย้อนหลัง conversation/message เดิม (เทียบ `message.created_at`/`rule.created_at` หรือ evaluate เฉพาะ live inbound stream — ไม่มี backfill)

**⚠️ รันแบบ inline ได้:** notification rule engine (`notification-rules.service.ts:132-155`) รัน sync inline อยู่แล้ว — ไม่จำเป็นต้อง queue rule evaluation

---

### Task 2.2 — Rule engine: sender skip + message deduplication
**ทำอะไร:** 2 guards ก่อน evaluate

**⚠️ Sender skip (แก้):** ไม่มี "bot/system sender_type" — ค่าจริงคือ `contact|agent|system` ดังนั้น **evaluate เฉพาะ `sender_type === 'contact'`** (skip `agent`, `system`)
```typescript
if (message.sender_type !== 'contact') return  // skip non-customer messages
```

**⚠️ Message dedup 5s (สร้างใหม่):** dedup เดิมในระบบเป็น **24 ชม. ที่ webhook gateway** (`webhook-deduplication.service.ts`, `TTL=86400`) — ไม่ใช่ตัวนี้ ต้องสร้าง guard ใหม่:
```typescript
const dedupeKey = `rule_dedup:${conversationId}:${hash(message.content)}`
if (await redis.get(dedupeKey)) return
await redis.set(dedupeKey, '1', 'EX', 5)   // TTL 5s
```

---

### Task 2.3 — Condition evaluator: Keyword (contains / exact)
**ทำอะไร:** evaluate keyword — case-insensitive ไทย-อังกฤษ — **⚠️ รองรับหลายคำต่อ condition** (`value: string[]`) match ถ้าตรงคำใดคำหนึ่ง (OR ภายใน condition) — ตาม mockup `contains 'ยกเลิก', 'cancel'`

```typescript
function evaluateKeyword(c: KeywordCondition, text: string): boolean {
  const n = text.toLowerCase()
  const keywords = c.value.map(k => k.toLowerCase())   // value เป็น array
  if (c.operator === 'contains') return keywords.some(k => n.includes(k))
  if (c.operator === 'exact')    return keywords.some(k => n === k)
  return false
}
```
**Special chars:** escape ก่อน match — ไม่ treat เป็น regex

---

### Task 2.4 — Condition evaluator: Channel
**ทำอะไร:** ตรวจ `conversation.channel_type` อยู่ใน list ที่ rule กำหนด

```typescript
function evaluateChannel(c: ChannelCondition, channel: string): boolean {
  return c.value.includes(channel)  // multi-select OR
}
```
**⚠️ Note:** ดู channel-support matrix ใน Task 3.1 — Shopee inbound อาจไม่มาด้วยซ้ำ (stub poller); Shopee/TikTok ติด tag ได้แต่ auto-reply ส่งไม่ได้

---

### Task 2.5 — Condition evaluator: Business hours
**ทำอะไร:** ตรวจ within/outside business hours

**⚠️ Location (แก้):** logic อยู่ที่ `packages/shared/src/utils/business-hours.utils.ts` — `import { nextBhOpenAt } from '@monorepo/shared'`

**Detection pattern (ไม่มี `isWithinBusinessHours()` สำเร็จรูป):**
```typescript
const open = nextBhOpenAt(now, schedule, tz)
const isInside = open.getTime() === now.getTime()   // ===now → inside; >now → outside
```

**⚠️ Config source (แก้):** business hours config **ไม่ได้อยู่ใน omnichat-service** — ดึงจาก `tenant-service` (ตาราง `business_hour_days`, 7 แถว/tenant) ผ่าน TCP/HTTP → ได้ `BusinessHours[]` (DayWire[])

**มีให้แล้ว (ไม่ต้องทำเอง):** timezone, DST, midnight-crossing, dual-shift (lunch break) — `business-hours.utils.ts` handle ครบ

**Workspace toggle vs custom:** `use_workspace: true` → ดึง tenant config; `false` → ใช้ schedule ใน condition เอง (รูปแบบ DayWire เดียวกัน)

---

### Task 2.6 — Condition evaluator: AND/OR combinator
**ทำอะไร:** combine ผล evaluators

```typescript
function evaluateConditions(items: RuleCondition[], logic: 'and'|'or', ctx: EvalContext): boolean {
  const r = items.map(c => evaluateCondition(c, ctx))
  return logic === 'and' ? r.every(Boolean) : r.some(Boolean)
}
```

---

### Task 2.7 — UI: Wizard Step 1 — Condition builder
**ทำอะไร:** condition cards + AND/OR toggle

**Condition card:** `[Type dropdown] [Operator ถ้ามี] [Value input] [× ลบ]`
**Business hours card:** toggle "ใช้ Workspace hours" default on → ปิดแล้วโชว์ custom day/time picker (reuse component จาก `settings/business/_components/`)
**AND/OR toggle:** inline badge ระหว่าง cards
**Info box:** "ข้อความจาก agent/system จะไม่ trigger rule (เฉพาะข้อความจากลูกค้า)"

**Location:** `.../settings/automation/rules/_components/step-conditions.tsx`

---

### Task 2.8 — UI: Test panel (real-time match + highlight)
**ทำอะไร:** input ทดสอบ → highlight card ที่ match/ไม่ match ทันที

**Logic:** evaluate ใน browser ด้วย logic เดียวกับ backend (keyword + channel + BH) ไม่ call API
**Result:** Match (เขียว) / No match + เหตุผล (แดง)

**Location:** `.../settings/automation/rules/_components/condition-test-panel.tsx`

---

## RA-03 — Send Auto-reply Message (2 SP)

> **เป้าหมาย:** Auto-reply executor (BE) + variable resolver + Wizard Step 2 UI

---

### Task 3.1 — Auto-reply executor
**ทำอะไร:** execute auto-reply — ส่งผ่าน channel เดียวกัน + guards

**Location:** `apps/omnichat-service/src/automation-rules/actions/auto-reply.executor.ts` (ใหม่ — inject `ConversationsService` + `StrategyRegistry`)

**⚠️ Channel send matrix (สำคัญ — verify แล้ว):**
| Channel | ส่ง auto-reply ได้? | หลักฐาน |
|---------|---------------------|---------|
| LINE, Facebook, Instagram, Lazada | ✅ ได้ | registered ใน `strategy.registry.ts:23-26` + pushMessage ใช้งานจริง |
| TikTok | ❌ ไม่ได้ | `tiktok.strategy.ts:173` คืน `'TikTok push message is not yet supported'` |
| Shopee | ❌ ไม่ได้ | **ไม่มี `shopee.strategy.ts`** + ไม่ register ใน registry (มีแค่ stub poller) |

**Guards ตามลำดับ:**
1. Skip ถ้า `conversation.status === 'completed'` (`schema.prisma:202`)
2. **⚠️ Channel-support guard:** ถ้า channel ส่งไม่ได้ (TikTok/Shopee) → skip + log (actions อื่นเช่น tag ยังทำงาน)
3. Cooldown: Redis key `rule_cooldown:{ruleId}:{conversationId}` → skip ถ้ายัง active (ดู 3.3)
4. Only-first-wins: รับ flag `autoreply_sent` จาก engine — true → skip
5. Resolve variables → ส่งผ่าน **`ConversationsService.sendMessage()`** (`conversations.service.ts:649-732`) หรือ `strategyRegistry.get(channel).pushMessage()` โดยตรง → retry ถ้า fail (ดู retry option ด้านล่าง)
6. persist message ด้วย `sender_type = 'rule'` + set cooldown + `autoreply_sent = true`

**⚠️ Retry pattern (เลือก — แผนเดิมอ้าง BullMQ ผิดที่):**
- Option A (inline, แนะนำสำหรับ scope นี้): inline retry แบบ `omnichat-gateway/queue.service.ts` `executeWithRetry()` — 3 ครั้ง exponential backoff
- Option B (queue): ทำตาม BullMQ pattern `ai-ingestion-service:45-58` (`attempts:3, backoff:{exponential, 2000}`) + `@Processor` consumer — ถ้าต้องการ durability

**⚠️ SLA / FRT attribution (แก้ชื่อ field):** ไม่มี `first_human_response_at` — FRT นับจาก SLA state machine ใน `messages.service.ts:103-262` (ใช้ `sla_first_inbound_at` + สร้าง `ConversationSlaEvent`) ต้อง **ไม่ให้ message `sender_type='rule'` ไป advance "first agent response"** ของ state machine (เหมือน auto-reply ไม่ใช่การตอบของ agent)

---

### Task 3.2 — Variable resolver + fallback
**ทำอะไร:** resolve template variables ก่อนส่ง

```typescript
function resolveVariables(tpl: string, ctx: ResolveContext, fb: Record<string,string>): string {
  return tpl
    .replace(/\{\{customer_name\}\}/g, ctx.customerName ?? fb['customer_name'] ?? '')
    .replace(/\{\{channel\}\}/g,       ctx.channel      ?? fb['channel'] ?? '')
    .replace(/\{\{current_time\}\}/g,  formatTime(ctx.now) ?? fb['current_time'] ?? '')
}
```
**Error case:** syntax ผิด (`{{customer name}}` มีช่องว่าง) → skip resolve, log warning, ส่ง literal

---

### Task 3.3 — Cooldown state (Redis)
**ทำอะไร:** เก็บ cooldown per conversation per rule

**แนะนำ Redis** (consistent กับ codebase ที่ใช้ Redis เยอะ — `packages/redis`):
```
key: rule_cooldown:{ruleId}:{conversationId}
TTL: cooldown_minutes * 60
```
(DB table เป็น option สำรองถ้าต้อง audit cooldown history)

---

### Task 3.4 — 🔧 ⚠️ Establish `'rule'` sender_type convention (ไม่ใช่ enum migration)
**ทำอะไร:** `sender_type` เป็น **plain `String`** (`schema.prisma:262`) ไม่ใช่ Prisma enum — ไม่มี migration enum ให้แก้

**งานจริง:**
- ใช้ค่า `'rule'` เป็น convention ใหม่ (เพิ่ม `'rule'` ใน comment `// contact | agent | system | rule` + validation layer ถ้ามี)
- ทำให้ `ConversationsService.sendMessage()` รับ optional `sender_type` (ตอนนี้ hardcode `'agent'` ที่ `:649-732`; AI reply ก็ `'agent'`)
- ตรวจทุกที่ที่ filter agent KPI / SLA ให้ exclude `sender_type='rule'`

---

### Task 3.5 — UI: Wizard Step 2 — Auto-reply config
**ทำอะไร:** Step 2 สำหรับ action = `auto_reply`

**Elements:**
- Text editor multi-line (max 2,000) + char count
- Variable toolbar: `{{customer_name}}` `{{channel}}` `{{current_time}}` — click insert at cursor
- Fallback inputs (per variable ที่ใช้)
- Preview: resolved real-time (dummy: ชื่อ สมปอง, channel LINE, เวลา 14:30)
- Cooldown field: required, default 5, unit (นาที/ชม.), asterisk
- Info box: "Auto-reply ไม่นับเป็น First Response Time ของ agent" + **"บางช่องทาง (TikTok, Shopee) ยังส่ง auto-reply ไม่ได้ — rule จะติด tag ได้แต่ข้ามการตอบ"**

**Location:** `.../settings/automation/rules/_components/step-action-autoreply.tsx`

---

## RA-04 — Auto-Tag Conversation (3 SP)

> **เป้าหมาย:** Auto-tag executor (BE) + Wizard Step 2 UI (Add tag) + tooltip

---

### Task 4.1 — Auto-tag executor
**ทำอะไร:** execute add_tag — append-only, dedup, skip ถ้า tag หาย

**Location:** `apps/omnichat-service/src/automation-rules/actions/auto-tag.executor.ts` (ใหม่)

**⚠️ เรียก conversation service จริง (ไม่ใช่ tags module):** `ConversationsService.updateConversationTags(conversationId, { tag_id, action: 'add', tenant_id })` (`conversations.service.ts:1941`) — ทำทีละ tag

```typescript
async executeAddTag(conv: Conversation, tagIds: string[], ruleId: string): Promise<void> {
  // existing tags = ConversationTag ที่ deleted_at IS NULL (soft-delete model)
  const existing = new Set(conv.tags.filter(t => !t.deleted_at).map(t => t.tag_id))
  for (const tagId of tagIds) {
    const tag = await this.tagsService.findById(tagId)
    if (!tag) { logger.warn(`tag not found: ${tagId} — skip`); continue }  // ไม่ throw
    if (existing.has(tagId)) continue                                       // dedup
    await this.conversationsService.updateConversationTags(conv.id, {
      tenant_id: conv.tenant_id, tag_id: tagId, action: 'add',
      // metadata จาก Task 4.2:
      tagged_by_type: 'rule', tagged_by_rule_id: ruleId,
    })
  }
}
```

**⚠️ Append-only = soft-delete model:** `ConversationTag` ใช้ `deleted_at` (soft delete) — dedup ต้องเช็ค `deleted_at IS NULL`

---

### Task 4.2 — 🔧 ⚠️ เพิ่ม metadata columns เข้า `ConversationTag`
**ทำอะไร:** เพิ่ม column attribution เข้า model จริง

**ไฟล์:** `apps/omnichat-service/prisma/schema.prisma` model `ConversationTag` (`:373-390`)

**Model จริงตอนนี้:** `id, tenant_id, conversation_id, tag_id, is_system, created_by_id, deleted_by_id, created_at, deleted_at` (ไม่มี tagged_by_*)

**เพิ่ม:**
```prisma
tagged_by_type    String?  // 'human' | 'rule'  (default 'human' ตอน app-level)
tagged_by_rule_id String?  // FK → automation_rules.id, ON DELETE SET NULL
```
**⚠️ Note:** มี `is_system` (Boolean) + `created_by_id` อยู่แล้ว — `tagged_by_type='rule'` แยกจาก `is_system` (system tag ≠ rule tag) ให้ชัดเจน

---

### Task 4.3 — UI: Wizard Step 2 — Add tag config
**ทำอะไร:** Step 2 สำหรับ action = `add_tag`

**Elements:**
- Tag picker: search + scrollable list + checkbox multi-select (ดึงจาก Tag CRUD `GET /tags`)
- "Create new": search ไม่เจอ → "+ Create tag: [ชื่อ]" → Enter → เรียก `createTag` แล้วเลือกทันที
- Selected: chips + × ลบ
- Preview: "จะติด label เหล่านี้: [chips]"

**Location:** `.../settings/automation/rules/_components/step-action-addtag.tsx`

---

### Task 4.4 — UI: Tooltip "tagged by rule" บน conversation view
**ทำอะไร:** tag chip ที่ `tagged_by_type = 'rule'` → tooltip ตอน hover

**Tooltip:** "tagged by rule: [ชื่อ rule]"

**ไฟล์ที่แก้:** component ที่ render tag chips ใน conversation detail ของ workspace-admin (หา component ที่ map conversation tags → chips; แก้ให้อ่าน `tagged_by_type`/`tagged_by_rule_id` จาก Task 4.2)

---

## Summary

| Story | Task ใหม่ | Task แก้ 🔧 | SP |
|-------|-----------|----------|----|
| RA-01 Rule Management | 8 | 0 | 8 |
| RA-02 Trigger Conditions | 7 | 1 (2.1 hook) | 5 |
| RA-03 Auto-reply | 4 | 1 (3.4 convention) | 2 |
| RA-04 Auto-tag | 3 | 1 (4.2 columns) | 3 |
| **รวม** | **22** | **3** | **18 SP** |

> **SP note:** Task 3.4 เบาลง (ไม่ใช่ enum migration) แต่ Task 3.1 หนักขึ้น (channel-support guard + เลือก retry pattern + SLA exclusion) และ Task 2.5 หนักขึ้น (ดึง BH config ข้าม service) — net SP ใกล้เคียงเดิม

---

## Dependency ระหว่าง Task

```
[1.1] automation_rules table
    → [1.2] CRUD APIs (api-gateway controllers/services + omnichat-service backend)
        → [1.3] RBAC permission
        → [1.4–1.8] Frontend (list + wizard + delete dialog) — ต้องมี layout.tsx + server actions + hooks

[2.1] Message hook + rule engine orchestrator ← ต้องมี [1.1] table
    → [2.2] sender skip ('contact' only) + dedup guard (5s, สร้างใหม่)
    → [2.3–2.6] Condition evaluators (parallel ได้; 2.5 ขึ้นกับ tenant-service BH config)
    → (ส่งผล) [3.1] Auto-reply executor
    → (ส่งผล) [4.1] Auto-tag executor

[3.4] sender_type 'rule' convention ← ทำก่อน [3.1]
[4.2] tagged_by_* columns ← ทำก่อน [4.1]

[2.7] Step 1 Conditions UI ← ต้องมี [1.7] wizard shell
[2.8] Test panel ← ต้องมี [2.7]
[3.5] Step 2 Auto-reply UI ← ต้องมี [1.7]
[4.3] Step 2 Add tag UI ← ต้องมี [1.7]
[4.4] Tooltip ← ต้องมี [4.2]
```

---

## ไฟล์หลักที่ต้องสร้าง/แก้ (verify กับ repo จริงแล้ว)

| ไฟล์ | สร้าง/แก้เพราะ |
|------|---------------|
| `apps/omnichat-service/prisma/schema.prisma` | Task 1.1 (AutomationRule), 4.2 (ConversationTag columns), 3.4 (sender_type comment) |
| `apps/omnichat-service/src/automation-rules/rule-engine.service.ts` | Task 2.1 orchestrator (ใหม่) |
| `apps/omnichat-service/src/automation-rules/actions/auto-reply.executor.ts` | Task 3.1 (ใหม่) |
| `apps/omnichat-service/src/automation-rules/actions/auto-tag.executor.ts` | Task 4.1 (ใหม่) |
| `apps/omnichat-service/src/automation-rules/automation-rules.{controller,service,module}.ts` | Task 1.2 backend CRUD (ใหม่) |
| `apps/omnichat-service/src/messages/messages.service.ts` | Task 2.1 🔧 hook engine ใน post-save (~:290-346) |
| `apps/omnichat-service/src/conversations/conversations.service.ts` | Task 3.4 🔧 `sendMessage` รับ `sender_type`; Task 4.1 reuse `updateConversationTags` |
| `apps/api-gateway/src/omnichat/controllers/automation-rules.controller.ts` | Task 1.2 (ใหม่, mirror sla.controller.ts) |
| `apps/api-gateway/src/omnichat/services/automation-rules.service.ts` | Task 1.2 (ใหม่, HttpService → omnichat-service) |
| `apps/api-gateway/src/omnichat/omnichat.module.ts` | Task 1.2 🔧 register controller + service |
| `packages/shared/src/types/rbac.types.ts` | Task 1.3 🔧 `config_automation_rules` |
| `apps/user-service/prisma/seed.ts` | Task 1.3 🔧 PERMISSION_MATRIX |
| `apps/workspace-admin/src/lib/permissions.ts` | Task 1.3 🔧 `CONFIG_AUTOMATION_RULES` |
| `apps/workspace-admin/src/app/(main)/settings/automation/rules/{layout,page}.tsx` | Task 1.4 (ใหม่) |
| `apps/workspace-admin/src/app/(main)/settings/automation/rules/_components/*.tsx` | Task 1.5, 1.6, 1.7, 1.8, 2.7, 2.8, 3.5, 4.3 (ใหม่) |
| `apps/workspace-admin/src/app/(main)/settings/automation/rules/_hooks/use-automation-rules.ts` | Task 1.4 (ใหม่) |
| `apps/workspace-admin/src/app/(main)/settings/automation/rules/_lib/automation-rules-constants.ts` | Task 1.4 (ใหม่) |
| `apps/workspace-admin/src/server/automation-rules.ts` | Task 1.4 server actions (ใหม่) |
| `apps/workspace-admin/src/app/(main)/settings/_lib/settings-sections.ts` | Task 1.4 🔧 เพิ่ม section |
| `apps/workspace-admin/src/navigation/sidebar/sidebar-items.ts` | Task 1.4 🔧 nav item |
| conversation tag chip component (workspace-admin conversation detail) | Task 4.4 🔧 tooltip |
