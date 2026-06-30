## Sequence Diagrams — RA-01: Rule Automation / Rule Management (CRUD)

> EPIC: [ACE-2211 Rule Automation](../ACE-2211_EPIC-A4.1_Rule_Automation.md) · STORY: [ACE-2212 Rule Management CRUD](../ACE-2212_STORY-RA-01_Rule_Management_CRUD.md) · ER: [RA-01_rule_automation_er.md](./RA-01_rule_automation_er.md)
> Transport: api-gateway → omnichat-service ใช้ **HTTP proxy** (`HttpService.axiosRef`) ตาม pattern config-CRUD เดิม (saved-views / credentials) — ไม่ใช่ TCP
> ไฟล์นี้ = **CRUD (STORY-RA-01)** เท่านั้น — Diagram 1–5 · **Rule Execution engine** (evaluate / auto-reply / auto-tag) ย้ายไป [RA-execution_overview.md](./RA-execution_overview.md) เพราะเป็น scope ของ RA-02/03/04

---

### 1 — Load Rules Page (list + counters)

ทุก role เข้าถึงได้ (`view_automation_rules`) — ปุ่ม/action ถูก gate ที่ FE ตาม role + บังคับซ้ำที่ API

```mermaid
sequenceDiagram
  autonumber
  participant FE as workspace-admin
  participant API as api-gateway (HTTP)
  participant OmniSvc as omnichat-service
  participant Redis as Redis
  participant DB_O as omnichat-service DB

  Note over FE: layout guard: checkPermission(view_automation_rules)<br/>ทุก role ผ่าน — FE ซ่อนปุ่ม New/Edit/Delete ตาม role (admin/supervisor เท่านั้นที่เห็น manage)

  FE->>API: GET /v1/omnichat/automation/rules
  API->>API: @RequirePermission('view_automation_rules')<br/>(global APP_GUARD resolve role จาก user-service)
  alt permission denied (direct API, no role)
    API-->>FE: 403 permission_denied
  else allowed
    API->>OmniSvc: HTTP GET /automation/rules { tenant_id }
    OmniSvc->>Redis: GET automation:rules:list:{tenant_id}<br/>(defs + display + fired_count snapshot)
    opt cache miss
      OmniSvc->>DB_O: SELECT automation_rules WHERE tenant_id<br/>ORDER BY enabled DESC, created_at DESC
      DB_O-->>OmniSvc: rules[] (active + inactive)
      OmniSvc->>Redis: SET automation:rules:list:{tenant_id} EX 3600
    end
    OmniSvc->>DB_O: SELECT id, fired_count WHERE tenant_id AND enabled = true<br/>(สดเฉพาะ active ≤20 — inactive fired_count นิ่ง ใช้จาก cache)
    DB_O-->>OmniSvc: active_counts[]
    OmniSvc->>OmniSvc: merge → active: override ด้วย fresh count · inactive: ใช้ cached (frozen)<br/>build summary: trigger/action summary, fired_count,<br/>created_by_name / updated_by_name + relative time<br/>active_count = rules.filter(enabled).length
    OmniSvc-->>API: { rules[], active_count, inactive_count }
    API-->>FE: 200 { rules, active_count, inactive_count }
  end

  FE->>FE: render Active section (X/20) + Inactive section (collapsed, แสดง "Inactive (n)")<br/>Agent → read-only (toggle/kebab disabled)
```

**Notes:**
- counter `Active (X/20)` — `inactive` ไม่นับ limit; section Inactive collapsed by default (AC#7)
- FE guard ใช้ pattern เดียวกับ `settings/sla/layout.tsx` → `checkPermission` → `redirect('/unauthorized')` ถ้า role ไม่มีสิทธิ์เข้าหน้า (ที่นี่ทุก role เข้าได้)
- **list cache** `automation:rules:list:{tenant_id}` EX 3600 (NOTIF-04 style cache-miss) เก็บ **ทั้ง rule** (defs + display + `fired_count` snapshot) — DEL ทุก CRUD write
- **`fired_count` query สดเฉพาะ active rule** — engine fire ได้เฉพาะ `enabled = true` → **inactive fired_count นิ่ง (frozen)** ใช้ค่าจาก cache ได้เลย; query แค่ `SELECT id, fired_count WHERE tenant_id AND enabled = true` (≤20 แถว) แล้ว override เฉพาะ active → ค่า real-time + query เบาสุด (inactive ไม่จำกัดจำนวนแต่ไม่แตะ DB)
- re-enable rule = CRUD write = DEL cache → rule ที่กลับมา active จะถูก query สดรอบถัดไปเอง (ไม่มีเคส count ค้าง)
- แยก key จาก **engine cache** `automation:rules:{tenant_id}` (active-only, ASC) เพราะ list ถือทั้ง active+inactive + display order ต่างกัน — ทั้ง 2 key DEL พร้อมกันทุก CRUD write

> **Mock request/response ทุก endpoint** → [RA-01_api_table.md](./RA-01_api_table.md)

---

### 2 — Create Rule (action-first wizard → save)

```mermaid
sequenceDiagram
  autonumber
  participant FE as workspace-admin
  participant API as api-gateway (HTTP)
  participant OmniSvc as omnichat-service
  participant Redis as Redis
  participant DB_O as omnichat-service DB

  Note over FE: กด "+ New Rule" → modal ถาม "คุณอยากให้ระบบทำอะไร?"<br/>2 ตัวเลือก: ส่งข้อความตอบอัตโนมัติ (auto_reply) / ติด label (add_tag)<br/>— ไม่มี blank form (AC#2)

  FE->>FE: เลือก action → Step 1 Triggers → Step 2 Action detail<br/>auto-gen name เช่น "Auto-reply · Outside hours" (admin แก้ได้)
  FE->>API: POST /v1/omnichat/automation/rules<br/>{ name, action_type, trigger_logic, conditions[], action_config }
  API->>API: @RequirePermission('manage_automation_rules')<br/>+ DTO shape validation (class-validator)
  alt permission denied (Agent)
    API-->>FE: 403 permission_denied
  else allowed
    API->>OmniSvc: HTTP POST /automation/rules { tenant_id, created_by, created_by_name, ...dto }
    OmniSvc->>OmniSvc: validate business rules:<br/>1. conditions ≥ 1 (else 400 "ต้องมีอย่างน้อย 1 เงื่อนไข")<br/>2. action_config ครบตาม action_type (auto_reply ต้องมี cooldown_minutes)<br/>3. tag_ids มีอยู่จริง (add_tag)
    OmniSvc->>DB_O: SELECT COUNT(*) automation_rules<br/>WHERE tenant_id AND enabled = true
    alt active_count ≥ 20 (เต็ม — บังคับ inactive, ไม่ block การสร้าง)
      OmniSvc->>DB_O: INSERT automation_rules { ...dto, enabled: FALSE, fired_count: 0 }
      DB_O-->>OmniSvc: rule (inactive)
      OmniSvc->>Redis: DEL automation:rules:list:{tenant_id}<br/>(engine cache ไม่ต้อง DEL — rule ใหม่ inactive, engine อ่านเฉพาะ active)
      OmniSvc-->>API: 201 { rule, forced_inactive: true }
      API-->>FE: 201 { rule, forced_inactive: true }
      FE->>FE: ปิด wizard → rule โผล่ใน Inactive section<br/>+ notice "active เต็ม 20/20 — บันทึกเป็น inactive, ปิด rule อื่นก่อนจึงเปิดใช้ได้"
    else under limit
      OmniSvc->>DB_O: INSERT automation_rules { ...dto, enabled: true, fired_count: 0 }
      DB_O-->>OmniSvc: rule
      OmniSvc->>Redis: DEL automation:rules:{tenant_id} + automation:rules:list:{tenant_id}<br/>→ engine + list page re-read on next access
      OmniSvc-->>API: 201 { rule }
      API-->>FE: 201 { rule }
      FE->>FE: ปิด wizard → rule ปรากฏใน Active list + success toast
    end
  end
```

**Notes:**
- **active limit 20 — create ไม่ block:** สร้างได้เสมอ; ถ้า active เต็ม 20 ตอน save → rule ใหม่ถูกบันทึกเป็น **inactive** (`enabled=false`), เปิดใช้ไม่ได้จนกว่าจะ disable rule active ตัวอื่นก่อน (การ enable เช็คซ้ำที่ Diagram 3 = 409) — เช็คที่ omnichat-service ครอบทุก caller
- ⚠️ **supersede STORY AC#1 Scenario 2 + EPIC** (เดิมเขียน "block create, ไม่เปิด wizard") → เปลี่ยนเป็น **create-as-inactive** ตาม product decision (2026-06-24) — ต้องอัปเดต AC ใน STORY/EPIC ให้ตรงด้วย
- auto-gen name ทำที่ **FE** (เห็น preview ใน wizard) แต่ส่ง `name` มากับ payload — server ไม่ regen (admin แก้ได้)
- network error ตอน save → FE เก็บ state wizard ไว้ครบ + retry prompt (QA edge case) — เป็น FE concern, ไม่มี server state
- หลัง insert DEL ทั้ง **engine cache** (`automation:rules:{tenant_id}`) และ **list cache** (`automation:rules:list:{tenant_id}`) — มีผลทันที (TTL 3600 เป็น safety net)

> **Mock request/response ทุก endpoint** → [RA-01_api_table.md](./RA-01_api_table.md)

---

### 3 — Enable / Disable toggle

```mermaid
sequenceDiagram
  autonumber
  participant FE as workspace-admin
  participant API as api-gateway (HTTP)
  participant OmniSvc as omnichat-service
  participant Redis as Redis
  participant DB_O as omnichat-service DB

  FE->>API: PATCH /v1/omnichat/automation/rules/:id/enabled<br/>{ enabled: true | false }
  API->>API: @RequirePermission('manage_automation_rules')
  alt denied (Agent)
    API-->>FE: 403 permission_denied
  else allowed
    API->>OmniSvc: HTTP PATCH /automation/rules/:id/enabled { tenant_id, enabled, updated_by }
    alt enabling (enabled = true)
      OmniSvc->>DB_O: SELECT COUNT(*) WHERE tenant_id AND enabled = true
      alt active_count ≥ 20
        OmniSvc-->>API: 409 active_rule_limit_reached
        API-->>FE: 409 { error: "ปิดบาง rule ก่อน" }
      else under limit
        OmniSvc->>DB_O: UPDATE automation_rules SET enabled = true, updated_by, updated_at = NOW()
        OmniSvc->>Redis: DEL automation:rules:{tenant_id} + automation:rules:list:{tenant_id}
        OmniSvc-->>API: 200 { rule }
        API-->>FE: 200 { rule }
      end
    else disabling (enabled = false)
      OmniSvc->>DB_O: UPDATE automation_rules SET enabled = false, updated_by, updated_at = NOW()<br/>(fired_count ไม่แตะ)
      OmniSvc->>Redis: DEL automation:rules:{tenant_id} + automation:rules:list:{tenant_id}
      OmniSvc-->>API: 200 { rule }
      API-->>FE: 200 { rule }
    end
    FE->>FE: rule ย้าย section ทันที (Active ⇄ Inactive) ไม่ reload, fired_count คงเดิม
  end
```

**Notes:**
- **must-not-break:** disable แล้ว engine ต้องไม่ evaluate rule นั้นทันที — `DEL automation:rules:{tenant_id}` (engine cache) ทำให้ message ถัดไป re-read active rules (rule ที่ disable หลุดจาก `WHERE enabled = true`); list cache DEL คู่กัน
- disable ไม่ลด `fired_count` (ประวัติการ fire ต้องคงอยู่)
- enable เช็ค limit 20 ซ้ำ (เคส: active=20 → disable 1 → enable อีกตัว = ต้อง block ถ้ากลับไป 20)

---

### 4 — Edit Rule (pre-filled, ไม่ retroactive)

```mermaid
sequenceDiagram
  autonumber
  participant FE as workspace-admin
  participant API as api-gateway (HTTP)
  participant OmniSvc as omnichat-service
  participant Redis as Redis
  participant DB_O as omnichat-service DB

  FE->>API: GET /v1/omnichat/automation/rules/:id
  API->>API: @RequirePermission('manage_automation_rules')
  API->>OmniSvc: HTTP GET /automation/rules/:id { tenant_id }
  OmniSvc->>DB_O: SELECT automation_rules WHERE id AND tenant_id
  DB_O-->>OmniSvc: rule
  OmniSvc-->>API: 200 { rule }
  API-->>FE: 200 { rule }
  FE->>FE: เปิด wizard pre-filled (action_type lock, conditions + action_config เติมครบ)

  FE->>API: PATCH /v1/omnichat/automation/rules/:id<br/>{ name?, trigger_logic?, conditions?, action_config? }
  API->>API: @RequirePermission('manage_automation_rules')
  API->>OmniSvc: HTTP PATCH /automation/rules/:id { tenant_id, updated_by, updated_by_name, ...dto }
  OmniSvc->>OmniSvc: validate (conditions ≥ 1, action_config ครบ)
  alt invalid
    OmniSvc-->>API: 400 Bad Request
    API-->>FE: 400 { error }
  else valid
    OmniSvc->>DB_O: UPDATE automation_rules SET ...dto, updated_by, updated_at = NOW()
    OmniSvc->>Redis: DEL automation:rules:{tenant_id} + automation:rules:list:{tenant_id}
    OmniSvc-->>API: 200 { rule }
    API-->>FE: 200 { rule }
    FE->>FE: ปิด wizard + success toast
  end

  Note over FE,DB_O: conversation ที่ in-progress ไม่ถูกกระทบ —<br/>rule ใหม่มีผลกับ message ที่เข้า "หลัง" save เท่านั้น (ไม่ retroactive, AC#6)
```

**Notes:**
- **ไม่ retroactive by design** — engine evaluate rules ณ เวลาที่ message เข้า (single-pass) เสมอ ไม่มี job ย้อนหลัง → message เก่าที่ process ไปแล้วไม่ re-run (must-not-break)
- `action_type` แก้ไม่ได้ตอน edit (ชนิด action fix ตั้งแต่ entry) — เปลี่ยน action = สร้าง rule ใหม่
- `updated_by` = คนกด save ล่าสุด (audit) — โชว์ "แก้ล่าสุดโดย" บน card

---

### 5 — Delete Rule (hard delete, Admin only)

```mermaid
sequenceDiagram
  autonumber
  participant FE as workspace-admin
  participant API as api-gateway (HTTP)
  participant OmniSvc as omnichat-service
  participant Redis as Redis
  participant DB_O as omnichat-service DB

  Note over FE: Delete อยู่ใน kebab menu (⋮) เท่านั้น — Supervisor/Agent ไม่เห็นเมนูนี้

  FE->>FE: กด Delete → confirmation dialog แสดง<br/>ชื่อ rule + "ทำงานไปแล้ว {fired_count} ครั้ง" + warning "ลบถาวร กู้คืนไม่ได้"
  alt Admin กด Cancel
    FE->>FE: dismiss — rule ยังอยู่ครบ ไม่มีการเปลี่ยนแปลง (AC#5 Scenario 3)
  else Admin กด "ลบถาวร"
    FE->>API: DELETE /v1/omnichat/automation/rules/:id
    API->>API: @RequirePermission('delete_automation_rules')<br/>(admin เท่านั้น — resolve role จาก user-service)
    alt role != admin (Supervisor/Agent ยิง API ตรง)
      API-->>FE: 403 permission_denied
      Note over API: bypass ผ่าน URL กันได้ — check ทั้ง UI และ API (EPIC edge case)
    else admin
      API->>OmniSvc: HTTP DELETE /automation/rules/:id { tenant_id }
      OmniSvc->>DB_O: DELETE FROM automation_rules WHERE id AND tenant_id<br/>(hard delete — ไม่มี soft flag หลงเหลือ)
      DB_O-->>OmniSvc: deleted
      OmniSvc->>Redis: DEL automation:rules:{tenant_id} + automation:rules:list:{tenant_id}
      OmniSvc-->>API: 200 { success: true }
      API-->>FE: 200 OK
      FE->>FE: rule หายจาก list ทันที (AC#5 Scenario 2)
    end
  end
```

**Notes:**
- **hard delete** ลบจริงจาก DB — ไม่มี undo (story: ยังไม่มี history) → confirmation dialog เป็น safety net ตัวเดียว แสดง `fired_count` ให้ admin เห็น impact ก่อนลบ
- cooldown keys (`automation:cooldown:{rule_id}:*`) ที่ค้างใน Redis = orphan, หมดอายุเองตาม TTL — ไม่ต้อง cleanup
- `conversation_tags` / `messages` ที่ rule นี้เคยติด/ส่ง **คงอยู่** (tagged_by_type='rule' / sender_type='rule' ไม่อ้าง FK ไป rule) — ลบ rule ไม่กระทบ data ที่ติดไปแล้ว

---

## Transport Reference (RA-01 — CRUD)

| From                    | To                      | Protocol       | Key                                                          |
| ----------------------- | ----------------------- | -------------- | ------------------------------------------------------------ |
| workspace-admin         | api-gateway (HTTP)      | HTTP           | `GET /v1/omnichat/automation/rules` (list)                   |
| workspace-admin         | api-gateway (HTTP)      | HTTP           | `GET /v1/omnichat/automation/rules/:id` (edit pre-fill)      |
| workspace-admin         | api-gateway (HTTP)      | HTTP           | `POST /v1/omnichat/automation/rules` (create)                |
| workspace-admin         | api-gateway (HTTP)      | HTTP           | `PATCH /v1/omnichat/automation/rules/:id` (edit)             |
| workspace-admin         | api-gateway (HTTP)      | HTTP           | `PATCH /v1/omnichat/automation/rules/:id/enabled` (toggle)   |
| workspace-admin         | api-gateway (HTTP)      | HTTP           | `DELETE /v1/omnichat/automation/rules/:id` (hard delete)     |
| api-gateway (HTTP)      | omnichat-service        | HTTP proxy     | `axiosRef` → `/automation/rules*` (pattern เดียวกับ saved-views) |
| api-gateway             | user-service            | TCP send       | `{ cmd: 'get_member_role' }` (PermissionGuard resolve role)  |
| omnichat-service        | Redis                   | GET/SET        | `automation:rules:list:{tenant_id}` (EX 3600 — list-page cache; fresh `fired_count` for **active only**) |
| omnichat-service        | Redis                   | DEL            | `automation:rules:{tenant_id}` + `automation:rules:list:{tenant_id}` — invalidate ทั้ง engine cache + list cache ทุก CRUD write |

> engine-side transport (inbound trigger, `pushMessage`, dedup, cooldown, `omnichat:events` publish → WS) ย้ายไป [RA-execution_overview.md](./RA-execution_overview.md)

---

## Changes to Existing Code (RA-01 — CRUD)

| File / Layer                                                  | Change                                                                                         |
| ------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `omnichat-service/prisma/schema.prisma`                       | Add `AutomationRule` model; add `tagged_by_type` to `ConversationTag`; doc `rule` ใน `sender_type` |
| `omnichat-service/src/automation/` (new)                      | `automation.controller.ts` (HTTP CRUD) + `automation.service.ts` (CRUD + limit-20) — *(`rule-engine.service.ts` อยู่ [RA-execution_overview.md](./RA-execution_overview.md))* |
| `api-gateway/src/omnichat/`                                   | `automation.controller.ts` + `automation.service.ts` (HTTP proxy, `@RequirePermission`)        |
| `packages/shared/src/types/rbac.types.ts`                     | Add `view_automation_rules`, `manage_automation_rules`, `delete_automation_rules` + matrix     |
| `workspace-admin/src/app/(main)/.../automation/` (new)        | route + `_api/` (Server Actions) + `_hooks/` + `_store/` + `_components/` (wizard, list, dialogs) |

---

## TODO Tracker (RA-01 — CRUD)

| ref     | งาน                                                              | story    | blocked by         |
| ------- | ---------------------------------------------------------------- | -------- | ------------------ |
| RA-01   | `automation_rules` migration + `tagged_by_type` + `sender_type` 'rule' | RA-01    | —                  |
| RA-01   | CRUD API + limit-20 + permission matrix (Diagram 1–5)            | RA-01    | migration done     |
| RA-01   | Rule list UI + action-first wizard (2 steps) + delete dialog    | RA-01    | API done           |

> execution TODO (RA-02 conditions / RA-03 auto-reply / RA-04 auto-tag / SLA-met guard) → [RA-execution_overview.md](./RA-execution_overview.md)
