# Implementation Plan — RA-01: Rule Management (CRUD)

> EPIC: [ACE-2211](./ACE-2211_EPIC-A4.1_Rule_Automation.md) · STORY: [ACE-2212](./ACE-2212_STORY-RA-01_Rule_Management_CRUD.md)
> Diagrams: [API](./Diagram/RA-01_api_table.md) · [ER](./Diagram/RA-01_rule_automation_er.md) · [Sequence](./Diagram/RA-01_rule_automation_sequence.md)
> Scope: **CRUD เท่านั้น** (list / create / edit / enable-disable / delete + permission). Rule **execution engine** (evaluate, auto-reply, auto-tag, SLA guard) = RA-02/03/04 — out of scope here.
> Repo: `ace/` (pnpm monorepo). ทุก path/line ในเอกสารนี้ **verify กับ repo จริงแล้ว** (ไม่ใช่จาก diagram เพียงอย่างเดียว).

---

## 0. สรุปสถาปัตยกรรม (1 ย่อหน้า)

FE (`workspace-admin`) → **api-gateway** (HTTP, `@RequirePermission` global guard) → **omnichat-service** (HTTP proxy ผ่าน `HttpService.axiosRef`) → Prisma/Postgres + Redis cache. ตารางทั้งหมดอยู่ใน omnichat-service DB เดียว — JOIN/FK จริงได้. pattern เดียวกับ **saved-views** (BE+gateway) และ **notification-rules** (FE + permission precedent).

ลำดับ implement (ตาม dependency): **DB migration + shared types → omnichat-service CRUD → api-gateway proxy → workspace-admin FE → tests**.

---

## 1. การแก้ไข/ตัดสินใจสำคัญที่ grounded กับโค้ดจริง (อ่านก่อน)

ประเด็นเหล่านี้ต่างจาก หรือ เติมรายละเอียดให้ diagram — ยืนยันกับ repo แล้ว:

| # | เรื่อง | ข้อเท็จจริงจากโค้ดจริง | ผลต่อ plan |
|---|--------|------------------------|------------|
| 1 | `messages.sender_type` | เป็น `String` (ไม่ใช่ enum) — `schema.prisma:262` comment `// contact \| agent \| system` | เพิ่มค่า `'rule'` = **ไม่ต้อง migration** แค่ allow ใน validation/typing (ของ RA-03 ตอนส่งจริง) |
| 2 | `conversation_tags` | **มี `deleted_at` + `deleted_by_id` อยู่แล้ว** (`schema.prisma:380-382`) — soft-delete append-only ตาม ER doc | migration เพิ่ม **แค่ 1 column**: `tagged_by_type` |
| 3 | Role→permission matrix | **ไม่ได้อยู่ใน** `rbac.types.ts` — อยู่ใน `apps/user-service/prisma/seed.ts` `PERMISSION_MATRIX` แล้ว load runtime ผ่าน RPC (`permission-matrix.service.ts`) | ต้องแก้ **3 จุด**: shared const + seed + FE enum (+ matrix spec test) แล้ว **re-run seed** |
| 4 | จำนวน permission | ER doc กำหนด **3 ตัว** (`view_/manage_/delete_automation_rules`) — *ไม่ใช่* `config_*` ตัวเดียวแบบ notification | ใช้ 3 ตัวตาม ER doc |
| 5 | Create ตอน active เต็ม 20 | **product decision 2026-06-24 supersede STORY AC#1 Sc.2 / EPIC** | create **ไม่ block** → บันทึกเป็น `enabled=false` + `forced_inactive:true` (ดู §3.2). Enable (toggle) ตอน=20 → **409** |
| 6 | Toggle | API ส่ง `{ enabled: boolean }` ชัดเจน (ไม่ใช่ derive จาก state) | endpoint `PATCH /:id/enabled` รับ body `{enabled}` + re-check limit เมื่อ `true` |
| 7 | Hard delete | ER doc: **ไม่มี `deleted_at`** บน `automation_rules` (ต่างจากตารางอื่น) | `prisma.delete()` จริง — ไม่มี soft flag |

> ⚠️ **DISSENT / ต้องเคลียร์กับ PO ก่อนเริ่ม:**
> (a) **#5 supersede** — STORY AC#1 Sc.2 + EPIC ยังเขียน "block create" ต้องอัปเดต AC ให้ตรงกับ create-as-inactive ก่อน dev FE (กระทบ wording + flow).
> (b) **single vs multi action ต่อ rule** — ER doc flag ไว้: STORY ออกแบบเป็น 1 action/rule (`action_type` เดี่ยว) แต่ตัวอย่าง execution ใน EPIC อ่านได้ว่า 1 rule หลาย action. RA-01 ยึด **1 action/rule**; ถ้า PO ต้องการ multi-action ต้องเปลี่ยน schema เป็น `actions: [{type,config}]` → **กระทบ schema + API ทั้งชุด** ควรตัดสินใจก่อน migration.

---

## 2. Phase 1 — DB migration + Shared types (blast radius: ทุก service ที่ import `@monorepo/shared`)

### 2.1 Prisma schema — `apps/omnichat-service/prisma/schema.prisma`

**(a) เพิ่ม model `AutomationRule`** (ต่อท้ายไฟล์ ก่อน/หลัง model สุดท้าย) — ใช้ block จาก ER doc verbatim:

```prisma
model AutomationRule {
  id              String   @id @default(uuid())
  tenant_id       String
  name            String
  action_type     String   // auto_reply | add_tag
  trigger_logic   String   @default("AND") // AND | OR
  conditions      Json     @db.JsonB
  action_config   Json     @db.JsonB
  enabled         Boolean  @default(true)
  fired_count     Int      @default(0)
  created_by      String
  created_by_name String
  updated_by      String?
  updated_by_name String?
  created_at      DateTime @default(now())
  updated_at      DateTime @updatedAt

  @@index([tenant_id, enabled, created_at(sort: Asc)]) // engine: active rules oldest-first
  @@index([tenant_id, created_at(sort: Desc)])         // list view
  @@map("automation_rules")
}
```
> ไม่มี `@@unique` (ชื่อซ้ำได้) · ไม่มี `deleted_at` (hard delete).

**(b) แก้ `ConversationTag`** — เพิ่ม 1 บรรทัด หลัง `is_system` (`schema.prisma:378`):

```prisma
  is_system       Boolean   @default(false)
  tagged_by_type  String    @default("manual") // 🆕 manual | rule
  created_by_id   String?
```

**(c) `messages.sender_type`** — ไม่แตะ schema (เป็น TEXT อยู่แล้ว). เพิ่มค่า `'rule'` ตอน execution (RA-03).

**Migration:**
```bash
pnpm --filter omnichat-service exec prisma migrate dev --name add_automation_rules_and_tagged_by_type
```
ตรวจ: migration sql มี `CREATE TABLE automation_rules` + 2 index + `ALTER TABLE conversation_tags ADD COLUMN tagged_by_type` และ regenerate Prisma client สำเร็จ.

### 2.2 Shared permission const — `packages/shared/src/types/rbac.types.ts`

เพิ่ม 3 ตัวใน `PERMISSION_ACTIONS` (ปัจจุบันบรรทัด 6-20) ก่อน `"manage_members"`:

```typescript
  "view_members",
  "view_automation_rules",      // 🆕 list — ทุก role
  "manage_automation_rules",    // 🆕 create/edit/enable/disable — admin, supervisor
  "delete_automation_rules",    // 🆕 hard delete — admin เท่านั้น
  "manage_members",
```
จากนั้น **rebuild shared** (services อื่น import จาก dist): `pnpm --filter @monorepo/shared build`.

### 2.3 Seed matrix — `apps/user-service/prisma/seed.ts`

เพิ่ม 3 entry ใน `PERMISSION_MATRIX` (รูปแบบเดียวกับ `config_notification_rules` ที่บรรทัด 52-57):

```typescript
  {
    action: 'view_automation_rules',
    description: 'View automation rules',
    roles: ['admin', 'supervisor', 'agent'],
    route_pattern: '/settings/automation',
  },
  {
    action: 'manage_automation_rules',
    description: 'Create / edit / enable / disable automation rules',
    roles: ['admin', 'supervisor'],
    route_pattern: '/settings/automation',
  },
  {
    action: 'delete_automation_rules',
    description: 'Hard delete automation rules',
    roles: ['admin'],
    route_pattern: '/settings/automation',
  },
```
**Re-run seed** (idempotent upsert): `pnpm --filter user-service exec prisma db seed`.
> ⚠️ ถ้าไม่ seed → `permission-matrix.service` จะ fail-closed (ทุก role โดน 403 บน action ใหม่).

### 2.4 FE permission enum — `apps/workspace-admin/src/lib/permissions.ts`

เพิ่ม 3 member (ตรงกับ string ใน shared):
```typescript
  VIEW_AUTOMATION_RULES = 'view_automation_rules',
  MANAGE_AUTOMATION_RULES = 'manage_automation_rules',
  DELETE_AUTOMATION_RULES = 'delete_automation_rules',
```

---

## 3. Phase 2 — omnichat-service CRUD (`apps/omnichat-service/src/automation/`)

โครงสร้าง module ใหม่ (mirror `saved-views/` + dual HTTP/TCP จาก `tags/`):

```
apps/omnichat-service/src/automation/
├── automation.module.ts          // imports: [PrismaModule, RedisModule]
├── automation.controller.ts       // HTTP @Get/@Post/@Patch/@Delete + TCP @MessagePattern (mirror tags.controller.ts)
├── automation.service.ts          // CRUD + limit-20 + Redis cache
└── dto/
    ├── create-rule.dto.ts          // class-validator; รับ tenant_id/created_by/created_by_name (gateway เติม)
    ├── update-rule.dto.ts          // ทุก field optional; action_type แก้ไม่ได้
    └── toggle-enabled.dto.ts        // { enabled: boolean }
```
ลงทะเบียน `AutomationModule` ใน `apps/omnichat-service/src/app.module.ts` (ข้าง `SavedViewsModule`).

**Controller:** bare `@Controller('automation/rules')`, HTTP routes + TCP `@MessagePattern({cmd:'...'})` ห่อด้วย `try/catch → RpcException` (copy รูปแบบจาก `tags.controller.ts`). `tenant_id`/`created_by` มาจาก body (gateway เติม) ไม่ใช่ JWT.

### 3.1 Service — endpoint → logic

| op | logic หลัก |
|----|-----------|
| `list(tenant_id)` | ดู §3.3 (cache + fired_count) → `{ rules[], active_count, inactive_count }` เรียง `enabled DESC, created_at DESC` |
| `getOne(id, tenant_id)` | `findFirst({where:{id,tenant_id}})` → ไม่เจอ `NotFoundException('ไม่พบ rule ที่ต้องการ')` |
| `create(dto)` | ดู §3.2 |
| `update(id, dto)` | validate (≥1 condition, action_config ครบ) → `update` set `updated_by/_name`, **ห้ามแก้ `action_type`** → DEL cache |
| `toggleEnabled(id,{enabled})` | ถ้า `enabled=true` → `count(enabled=true) ≥ 20` → **`ConflictException` (409)**; else update; `fired_count` ไม่แตะ → DEL cache |
| `delete(id, tenant_id)` | `prisma.delete()` จริง (hard) → DEL cache → `{success:true}` |

ทุก write (create/update/toggle/delete) ต้อง **DEL ทั้ง 2 Redis key** (§3.3).

### 3.2 Create — limit-20 = create-as-inactive (ไม่ block)

```
validate: conditions.length ≥ 1  (else BadRequestException 'ต้องมีอย่างน้อย 1 เงื่อนไข')
          action_config ครบตาม action_type (auto_reply ต้องมี message + cooldown_minutes; add_tag ต้องมี tag_ids ≥ 1)
active = count(tenant_id, enabled=true)
if active >= 20:  INSERT { ...dto, enabled: false, fired_count: 0 }  → return { rule, forced_inactive: true }   // 201
else:             INSERT { ...dto, enabled: true,  fired_count: 0 }  → return { rule }                         // 201
DEL cache ทั้ง 2 key (กรณี forced_inactive จะ DEL แค่ list cache ก็พอ — rule ใหม่ inactive engine ไม่อ่าน แต่ DEL คู่ปลอดภัยกว่า)
```

### 3.3 Redis cache (key ตาม ER doc — ไม่ใช่ชื่อที่ generate มั่ว)

ใช้ `RedisService.getClient()` (จาก `@monorepo/redis`), fire-and-forget + `.catch()`:

| key | TTL | purpose |
|-----|-----|---------|
| `automation:rules:list:{tenant_id}` | 3600s | list-page cache: ทุก rule (defs+display+`fired_count` snapshot, active+inactive) |
| `automation:rules:{tenant_id}` | 3600s | engine cache (active-only, ASC) — RA-02+ ใช้; CRUD แค่ DEL ให้ |

**list() flow:** GET list cache → miss: query DB (`ORDER BY enabled DESC, created_at DESC`) แล้ว SET EX 3600. จากนั้น query สด `SELECT id, fired_count WHERE tenant_id AND enabled=true` (≤20 แถว) → override `fired_count` เฉพาะ active (inactive ใช้ค่า frozen จาก cache). `active_count = rules.filter(enabled).length`.
**ทุก CRUD write:** `DEL automation:rules:{tenant_id}` + `automation:rules:list:{tenant_id}`.

---

## 4. Phase 3 — api-gateway proxy + permission (`apps/api-gateway/src/omnichat/`)

mirror `controllers/saved-views.controller.ts` + `services/saved-views.service.ts`. ลงทะเบียนใน `omnichat.module.ts` (controllers + providers array).

**Controller** `@Controller('omnichat/automation/rules')` (global prefix `/v1` เติมเอง) + `@CurrentUser()` ดึง `{userId, tenantId}` จาก JWT, inject เข้า body ตอน proxy (FE ไม่ส่ง tenant_id/created_by):

| Method | Path | `@RequirePermission` | Role |
|--------|------|----------------------|------|
| GET | `/v1/omnichat/automation/rules` | `view_automation_rules` | Admin·Sup·Agent |
| GET | `/v1/omnichat/automation/rules/:id` | `manage_automation_rules` | Admin·Sup |
| POST | `/v1/omnichat/automation/rules` | `manage_automation_rules` | Admin·Sup |
| PATCH | `/v1/omnichat/automation/rules/:id` | `manage_automation_rules` | Admin·Sup |
| PATCH | `/v1/omnichat/automation/rules/:id/enabled` | `manage_automation_rules` | Admin·Sup |
| DELETE | `/v1/omnichat/automation/rules/:id` | `delete_automation_rules` | **Admin only** |

**Service:** `httpService.axiosRef.{get,post,patch,delete}` ไป `http://${host}:${port}/automation/rules*` (base URL จาก `ConfigService` key เดียวกับ `saved-views.service.ts` ใช้: `shared.omnichatService.http.{host,port}`). GET/DELETE ส่ง `tenant_id` เป็น `params`; POST/PATCH ส่งใน body พร้อม `created_by`/`updated_by`. error: catch `AxiosError` → `throw new HttpException(err.response?.data ?? {message:'Bad Gateway'}, err.response?.status ?? 502)`.

**DTO** (`dto/`): `create-rule.dto.ts` (name, action_type, trigger_logic, conditions[], action_config — class-validator), `update-rule.dto.ts` (ทุก field optional, **ไม่มี** action_type), `toggle-enabled.dto.ts` (`{enabled:boolean}`).

> permission guard เป็น global `APP_GUARD` แล้ว (`app.module.ts`) — แค่ใส่ `@RequirePermission(...)` พอ ไม่ต้อง `@UseGuards`. Guard resolve role ผ่าน RPC `get_workspace_member_role` → Agent ยิง DELETE ตรง = 403 อัตโนมัติ.

---

## 5. Phase 4 — workspace-admin FE (`src/app/(main)/settings/automation/`)

mirror `settings/notification-rules/` (layout guard + _api/_hooks) + `dashboard/chats/_store` (Zustand optimistic).

```
settings/automation/
├── layout.tsx        // checkPermission({ some:[Permission.VIEW_AUTOMATION_RULES] }) → redirect('/unauthorized')
├── page.tsx          // h1 + description + <RuleList/>
├── _api/automation-rules.ts   // 'use server'; ActionResult<T>; httpClient.{get,post,patch,delete} → /v1/omnichat/automation/rules
├── _hooks/use-automation-rules.ts  // TanStack useQuery(list) + mutations (create/update/toggle/delete) → invalidate
├── _store/automation-store.ts      // Zustand: optimistic enable/disable toggle (bailout pattern)
├── _lib/automation-constants.ts    // action/trigger labels, auto-gen name helper, summary builders
└── _components/
    ├── rule-list.tsx              // Active (X/20) + Inactive (collapsed) sections, fired_count, created/updated_by
    ├── rule-card.tsx              // + kebab menu (Edit / Delete) gate ตาม role
    ├── new-rule-modal.tsx         // action-first: "คุณอยากให้ระบบทำอะไร?" (auto_reply / add_tag)
    ├── rule-wizard.tsx            // 2-step: Step1 Triggers → Step2 Action detail; step indicator; auto-gen name preview
    └── delete-confirm-dialog.tsx  // AlertDialog: ชื่อ rule + fired_count + warning ถาวร
```

**Register route (sync 2 ไฟล์):**
- `settings/_lib/settings-sections.ts` — เพิ่ม entry ก่อน "My Preferences" (บรรทัด 43): `{ title:"Automation", url:"/settings/automation", permissions:[Permission.VIEW_AUTOMATION_RULES] }`
- `navigation/sidebar/sidebar-items.ts` — เพิ่ม item เดียวกัน + icon (เช่น `Zap` จาก lucide-react). **ต้อง sync URL+permission ให้ตรง 2 ไฟล์.**

**Patterns ที่ต้องตาม (repo rule):**
- Server Action คืน `ActionResult<T> = {data:T}|{error:string}` — **ห้าม throw** (Next.js sanitize). `_hooks/` เช็ค `'error' in result` แล้ว throw client-side.
- `httpClient` จาก `src/server/http.config.ts` (inject Bearer จาก cookie + auto-refresh) — ใช้ตัวเดียว.
- Zustand toggle = optimistic + rollback on error; bailout (`return state`) ถ้าไม่เปลี่ยน.
- Role gate UI: ซ่อนปุ่ม New/Edit/Delete ตาม permission (client check) — layout guard กันแค่หน้า (VIEW = ทุก role เข้าได้), การ enforce จริงอยู่ที่ API (403).
- auto-gen name ทำที่ FE (preview ใน wizard) ส่ง `name` มากับ payload; network error ตอน save → เก็บ wizard state + retry prompt.

---

## 6. Phase 5 — Tests & Verification (มี evidence ก่อนปิดงาน)

| ระดับ | ที่ไหน | เคส |
|-------|--------|-----|
| Unit (BE) | `automation.service.spec.ts` | validation (≥1 condition, action_config ครบ); limit-20 → create-as-inactive; toggle enable ที่ 20 → 409; hard delete |
| Unit (perm) | `permission-matrix.service.spec.ts` | เพิ่ม 9 rows (3 action × 3 role) + cases: view=ทุก role, manage=admin/sup, delete=admin only — **update assertion count** |
| Integration | gateway | CRUD + permission per role; Agent/Supervisor ยิง DELETE ตรง = 403 |
| E2E | FE | wizard action-first → save → ขึ้น Active list; disable → ย้าย Inactive ไม่เสีย fired_count; delete confirm → หาย |

**Verification commands:**
```bash
pnpm --filter @monorepo/shared build                 # หลังแก้ rbac.types.ts
pnpm --filter omnichat-service exec prisma migrate dev --name add_automation_rules_and_tagged_by_type
pnpm --filter user-service exec prisma db seed        # โหลด permission ใหม่
cd apps/omnichat-service && npx jest --testPathPatterns="automation" --no-coverage
cd apps/api-gateway && npx jest --testPathPatterns="permission-matrix" --no-coverage
pnpm --filter workspace-admin lint
```

---

## 7. File checklist (ทั้งหมด)

| Phase | ไฟล์ | action |
|-------|------|--------|
| 1 | `omnichat-service/prisma/schema.prisma` | + model `AutomationRule`; + `tagged_by_type` ใน `ConversationTag` |
| 1 | `packages/shared/src/types/rbac.types.ts` | + 3 permission strings → rebuild shared |
| 1 | `user-service/prisma/seed.ts` | + 3 `PERMISSION_MATRIX` entries → re-seed |
| 1 | `workspace-admin/src/lib/permissions.ts` | + 3 enum members |
| 2 | `omnichat-service/src/automation/*` (ใหม่) | controller + service + module + 3 dto |
| 2 | `omnichat-service/src/app.module.ts` | register `AutomationModule` |
| 3 | `api-gateway/src/omnichat/controllers/automation.controller.ts` (ใหม่) | 6 endpoints + `@RequirePermission` |
| 3 | `api-gateway/src/omnichat/services/automation.service.ts` (ใหม่) | axiosRef proxy + error map |
| 3 | `api-gateway/src/omnichat/dto/*` (ใหม่) | create/update/toggle dto |
| 3 | `api-gateway/src/omnichat/omnichat.module.ts` | register controller + service |
| 4 | `workspace-admin/.../settings/automation/*` (ใหม่) | layout/page/_api/_hooks/_store/_lib/_components |
| 4 | `workspace-admin/.../settings/_lib/settings-sections.ts` | + entry |
| 4 | `workspace-admin/src/navigation/sidebar/sidebar-items.ts` | + item (sync) |
| 5 | spec files | unit + permission-matrix + e2e |

---

## 8. Out of scope (RA-01) / Open questions

- **Execution engine** (evaluate conditions, send auto-reply, auto-tag, dedup/cooldown Redis keys, SLA-met guard, `sender_type='rule'` ตอนส่งจริง) → RA-02/03/04 ([RA-execution_overview.md] อ้างใน sequence doc).
- **Channel send capability**: TIKTOK ส่งไม่ได้ (`'not yet supported'`), SHOPEE ไม่มี strategy → auto_reply skip บน 2 channel นี้ (tag ยังทำงาน). เป็นเรื่อง engine — RA-01 แค่สร้าง rule ได้.
- Soft delete / audit trail, drag-reorder, duplicate, export/import — out of scope (STORY).
- **Open Q (ต้องเคลียร์ก่อน dev):** §1 DISSENT (a) supersede AC create-as-inactive, (b) single vs multi-action per rule.
