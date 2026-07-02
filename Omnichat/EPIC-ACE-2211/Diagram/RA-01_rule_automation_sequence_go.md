# RA-01 Rule Management (CRUD) — Sequence Diagram (Go / `ace-omnichat-go`)

> STORY: [ACE-2212](../ACE-2212_STORY-RA-01_Rule_Management_CRUD.md) · EPIC: [ACE-2211](../ACE-2211_EPIC-A4.1_Rule_Automation.md) · ER: [rule_automation_er_go.md](./rule_automation_er_go.md)
> Scope: **CRUD เท่านั้น** rule execution engine = RA-02/03/04 ไม่อยู่ในนี้
> Layering: `handler` → `orchestration` interface → **`core`** → `domain port` (repo) — ชื่อทุกตัว **verified กับ repo จริง** (ดู §Naming reference)

---

## Naming reference (verified จาก repo จริง)

| ใน diagram | สัญลักษณ์/ชื่อจริงใน repo | อ้างอิง |
|---|---|---|
| claims | `clerk.SessionClaimsFromContext(ctx)` → `claims.ActiveOrganizationID` (org_xxx), `claims.Subject` (userId) | `handler/conversation/handler.go:33` |
| resolve wsID | `o.resolveWorkspaceID(ctx, clerkOrgOrUUID)` — `len==36`→UUID else `WorkspaceRepository.GetIDByClerkOrgID` | `manageconversation/orchestrator.go:36` |
| response | `response.Success / Created / BadRequest / Unauthorized / NotFound / Conflict / UnprocessableEntity / InternalServerError` — body `{message, data}` | `delivery/http/response/response.go` |
| bind/validate | `c.Bind(&req)` แล้ว `c.Validate(&req)` (แยกกัน) | `handler/conversation/handler.go:39-43` |
| **Orch** | `manageautomationrules.Orchestrator` (interface ใน `port.go`) — method รับ `XxxInput` DTO | pattern: `manageconversation.Orchestrator` |
| **Core** | `core/automationrule.Service` (struct) | pattern: `core/notification.Service` |
| **Repo** | domain iface `domain/identity.AutomationRuleRepository` → impl `repository/postgres/identity/` — `List / GetByID / CountActive / Create / Update / SetEnabled / Delete` | pattern: `TagRepository`, `ConversationRepository` |
| **Redis** | `*redis.Client` (go-redis v9) — `Get / Set / Del(ctx, key, …)` | `infrastructure/cache/redis/redis.go` |
| logger | `logger.Component("automationrule_orch")` · `log.Error().Err(e).Str(k,v).Msg(…)` | `manageconversation/orchestrator.go:51` |

> **ทำไมมี Core (ไม่ใช่ pass-through):** `List/GetByID/Validate/CountActive/cache` ถูกใช้ทั้ง CRUD orchestrator (RA-01) และ execution engine `core/messaging` (RA-02+ ตอน eval โหลด active rules + validate) = capability shared ข้าม orchestrator จริง ตาม CLAUDE.md **Orch** = flow+policy (resolve, ตัดสิน limit-20) · **Core** = capability (repo+cache+validate)

---

## Participants

| diagram | ไฟล์จริง (ใหม่ ยกเว้นระบุ) |
|---|---|
| **FE** | `workspace-admin` settings/automation |
| **H** Handler | `delivery/http/handler/automationrule/handler.go` |
| **MW** AuthMW | `delivery/http/middleware/` (Clerk — มีอยู่แล้ว) |
| **PG** PermGuard ⚠️ | RBAC guard — **ยังไม่มีในrepo** (§หมายเหตุ) |
| **O** Orch | `usecase/orchestration/manageautomationrules/` |
| **C** Core | `usecase/core/automationrule/` (Service) |
| **Repo** | `repository/postgres/identity/automationrule_repository.go` |
| **R** Redis | `*redis.Client` — key `automation:rules:list:{wsID}` |
| **DB** | Postgres `identity.automation_rules` |

---

## S0 — Common preamble (auth + permission + resolve)

```mermaid
sequenceDiagram
    autonumber
    actor U as Admin/Sup/Agent
    participant FE as [Client] workspace-admin
    participant H as [Handler] automationrule.Handler
    participant MW as [Auth] clerk middleware
    participant PG as [Guard] PermGuard ⚠️NEW
    participant O as [Orch] manageautomationrules

    U->>FE: action
    FE->>H: HTTP + Bearer JWT
    H->>MW: clerk middleware verify
    alt JWT ไม่ถูก
        MW-->>FE: 401
    else ok
        H->>H: clerk.SessionClaimsFromContext(ctx)
        alt !ok
            H-->>FE: 401
        else claims ok
            Note over H: claims.Subject = userId<br/>claims.ActiveOrganizationID = org_xxx
            H->>PG: require(permission, role@org)
            PG->>PG: resolve role จาก workspace_members.role
            alt role ไม่มีสิทธิ์
                PG-->>FE: 403 Forbidden
            else มีสิทธิ์
                H->>O: <Method> (WorkspaceID = claims.ActiveOrganizationID)
                O->>O: resolveWorkspaceID(org_xxx) → wsID
                Note over O: UUID column ห้ามรับ org_xxx ตรง (CLAUDE.md)
            end
        end
    end
```

**Permission ต่อ endpoint** (enforce ที่ PermGuard):

| Method / Path | permission | role |
|---|---|---|
| `GET /v1/automation-rules` | `view_automation_rules` | Admin·Sup·Agent |
| `POST /v1/automation-rules` | `manage_automation_rules` | Admin·Sup |
| `PATCH /v1/automation-rules/:id` | `manage_automation_rules` | Admin·Sup |
| `PATCH /v1/automation-rules/:id/enabled` | `manage_automation_rules` | Admin·Sup |
| `DELETE /v1/automation-rules/:id` | `delete_automation_rules` | **Admin only** |

---

## S1 — List (GET) `counter X/20`

```mermaid
sequenceDiagram
    autonumber
    participant H as [Handler] automationrule.Handler
    participant O as [Orch] manageautomationrules
    participant C as [Core] automationrule.Service
    participant R as [Cache] redis.Client
    participant Repo as [Repo] identity.AutomationRuleRepo
    participant DB as [DB] identity.automation_rules

    Note over H,O: S0: view = ทุก role → resolve wsID
    H->>O: List rules
    O->>C: List
    C->>R: get list cache
    alt cache hit
        R-->>C: rules (snapshot)
    else miss
        C->>Repo: List (active-first)
        Repo->>DB: select rules
        DB-->>Repo: rows
        Repo-->>C: rules
        C->>R: cache rules (TTL)
    end
    C-->>O: rules
    O->>O: count active / inactive
    O-->>H: 200 · rules + active/inactive count
```

---

## S2 — Create (POST) `create-as-inactive · min 1 condition`

```mermaid
sequenceDiagram
    autonumber
    actor U as Admin/Sup
    participant FE as [Client] workspace-admin
    participant H as [Handler] automationrule.Handler
    participant O as [Orch] manageautomationrules
    participant C as [Core] automationrule.Service
    participant Repo as [Repo] identity.AutomationRuleRepo
    participant DB as [DB] identity.automation_rules
    participant R as [Cache] redis.Client

    U->>FE: wizard action-first (auto-gen name ที่ FE)
    FE->>H: POST create rule
    Note over H: S0 (manage) → agent=403
    H->>H: bind + validate
    alt bind/validate fail
        H-->>FE: 400
    else ok
        H->>O: Create
        O->>C: Validate
        Note over C: conditions ≥ 1 · actionConfig ครบตาม actionType
        alt invalid
            C-->>O: ErrInvalidRule
            O-->>H: 400 "ต้องมีอย่างน้อย 1 เงื่อนไข"
        else valid
            O->>C: Create
            C->>Repo: CreateWithLimit(rule, 20)
            Note over Repo,DB: 1 txn: advisory lock(workspace_id) → count active<br/>→ enabled = (count < 20) → insert  (atomic — active ห้ามเกิน 20)
            Repo->>DB: BEGIN · lock · count · insert · COMMIT
            DB-->>Repo: rule + forced_inactive
            C->>R: del list cache
            C-->>O: rule, forced_inactive
            alt forced_inactive (เต็ม 20 → inactive)
                O-->>H: 201 {rule, forced_inactive: true}
            else active
                O-->>H: 201 {rule}
            end
        end
    end
```

> ✅ **Decision: create-as-inactive** — create ที่ active=20 **ไม่ block**: insert `enabled=false` + return `forced_inactive:true` (wizard ทำงานจบ, FE แจ้ง toast) จุด enforce limit-20 ย้ายไปที่ **enable/toggle** (S4 → 409)
> ℹ️ STORY AC#1 Sc.2 + EPIC ยังเขียน "block create / ไม่เปิด wizard" — **superseded โดย diagram นี้** (เลือกไม่แก้ story) **dev ยึด create-as-inactive ตาม diagram** ไม่ใช่ AC เดิม

---

## S3 — Edit (PATCH /:id) `ไม่ retroactive`

```mermaid
sequenceDiagram
    autonumber
    participant H as [Handler] automationrule.Handler
    participant O as [Orch] manageautomationrules
    participant C as [Core] automationrule.Service
    participant Repo as [Repo] identity.AutomationRuleRepo
    participant DB as [DB] identity.automation_rules
    participant R as [Cache] redis.Client

    Note over H,O: S0 (manage) → wsID
    H->>H: bind + validate
    H->>O: Update
    O->>C: GetByID
    C->>Repo: GetByID
    Repo->>DB: select by id + wsID
    alt ไม่เจอ / คนละ workspace
        C-->>O: nil
        O-->>H: 404 "ไม่พบ rule"
    else เจอ
        O->>C: Validate
        Note over C: actionType immutable — ตัดออกจาก patch
        alt invalid
            C-->>O: ErrInvalidRule
            O-->>H: 400
        else valid
            O->>C: Update
            C->>Repo: update
            Repo->>DB: update
            C->>R: del cache (list + engine)
            C-->>O: rule
            O-->>H: 200
        end
    end
    Note over DB: ไม่ retroactive — engine อ่านค่าใหม่รอบ inbound ถัดไป · conversation ที่เปิดอยู่ไม่กระทบ
```

---

## S4 — Toggle (PATCH /:id/enabled) `enforce limit-20`

```mermaid
sequenceDiagram
    autonumber
    participant FE as [Client] workspace-admin
    participant H as [Handler] automationrule.Handler
    participant O as [Orch] manageautomationrules
    participant C as [Core] automationrule.Service
    participant Repo as [Repo] identity.AutomationRuleRepo
    participant DB as [DB] identity.automation_rules
    participant R as [Cache] redis.Client

    FE->>H: PATCH /:id/enabled {enabled}
    Note over H,O: S0 (manage) → wsID
    H->>O: ToggleEnabled
    O->>C: GetByID
    alt ไม่เจอ
        C-->>O: nil
        O-->>H: 404
    else เจอ
        alt rule.enabled == req.enabled (ไม่เปลี่ยน)
            O-->>H: 200 (no-op)
        else inactive → active (เปิด)
            O->>C: SetEnabled(true)
            C->>Repo: EnableIfUnderLimit(wsID, id, 20)
            Note over Repo,DB: 1 txn: advisory lock(workspace_id) → count active<br/>→ ถ้า <20 UPDATE enabled=true  (atomic — ปิด TOCTOU)
            Repo->>DB: BEGIN · lock · count · conditional UPDATE · COMMIT
            alt count < 20 (สำเร็จ)
                DB-->>Repo: updated
                C->>R: del cache (list + engine)
                O-->>H: 200
            else count ≥ 20 (เต็ม)
                DB-->>Repo: not updated
                O-->>H: 409
            end
        else active → inactive (ปิด — ไม่ block)
            O->>C: SetEnabled(false)
            C->>Repo: update enabled
            Note over Repo,DB: fired_count ไม่แตะ
            C->>R: del cache (list + engine)
            O-->>H: 200
        end
    end
    H-->>FE: 200 → FE ย้าย card Active/Inactive (optimistic)
```

> **no-op bailout:** enforce limit เฉพาะ transition `inactive→active` — re-enable ของที่ active อยู่แล้ว = no-op 200
> **atomic limit (ปิด TOCTOU):** count + write อยู่ใน **transaction เดียว** + `pg_advisory_xact_lock(workspace_id)` → op ที่เพิ่ม active (create S2 + enable S4) serialize ต่อ workspace → active **ห้ามเกิน 20 เด็ดขาด** ไม่ใช่ check-then-act repo ใช้ lock เดียวกันใน `CreateWithLimit` / `EnableIfUnderLimit` (คุมทั้ง 2 flow)

---

## S5 — Delete (DELETE /:id) `hard delete, Admin only`

```mermaid
sequenceDiagram
    autonumber
    actor A as Admin
    participant FE as [Client] workspace-admin
    participant H as [Handler] automationrule.Handler
    participant O as [Orch] manageautomationrules
    participant C as [Core] automationrule.Service
    participant Repo as [Repo] identity.AutomationRuleRepo
    participant DB as [DB] identity.automation_rules
    participant R as [Cache] redis.Client

    A->>FE: kebab (⋮) → Delete → confirm (ชื่อ + fired_count + warning)
    A->>FE: กด "ลบถาวร"
    FE->>H: DELETE rule
    Note over H: S0 (delete = Admin only) → Sup/Agent = 403
    H->>O: Delete
    O->>C: GetByID
    alt ไม่เจอ
        C-->>O: nil
        O-->>H: 404
    else เจอ
        O->>C: Delete
        C->>Repo: Delete
        Repo->>DB: hard delete
        Note over DB: ไม่มี deleted_at · ไม่มี FK ชี้เข้า → ไม่ต้อง cascade<br/>conversation_tags.tagged_by_rule_name (snapshot) ยังอยู่ → tooltip รอด
        C->>R: del list cache
        C-->>O: ok
        O-->>H: 200
    end
    H-->>FE: 200 → rule หายจาก list ทันที
```

---

## S6 — Permission enforced ที่ API (AC#4 Sc.3)

```mermaid
sequenceDiagram
    autonumber
    actor X as Supervisor/Agent
    participant FE as [Client] workspace-admin
    participant PG as [Guard] PermGuard ⚠️NEW
    participant O as [Orch] manageautomationrules

    Note over X: bypass UI — ยิง API ตรง
    X->>FE: DELETE /v1/automation-rules/:id (Supervisor)
    FE->>PG: require(delete_automation_rules, role=supervisor)
    PG-->>FE: 403 Forbidden
    Note over O: ไม่ถึง Orch/Core — enforce ที่ guard ไม่ใช่แค่ซ่อนปุ่ม UI
```

---

## หมายเหตุสำคัญ

**⚠️ PermGuard ยังไม่มีในrepo** — ค้น `internal/delivery/` ไม่เจอ role-gate สักจุด ต้องสร้าง: middleware map `(permission, role)→allow/deny` + resolve role จาก `identity.workspace_members.role` (cache ได้) role constant มีแล้ว: `ClerkRoleAdmin = "org:admin"` (`core/notification/service.go:40`) ควรแยกเป็น story — blast radius กว้างกว่า automation

**Repo interface placement (CLAUDE.md):** `AutomationRuleRepository` ควรนิยามใน `domain/identity/port.go` แล้ว `repository/postgres/identity` implement (หมายเหตุ: โค้ดจริงบางที่เช่น `manageconversation/port.go` นิยาม repo interface ใน orchestration — ขัด checklist ตามใหม่ควรวางใน domain)

**Error → response helper:**
| กรณี | helper | code |
|---|---|---|
| JWT/claims ไม่ถูก | `response.Unauthorized` | 401 |
| role ไม่มีสิทธิ์ | (PermGuard) | 403 |
| ไม่พบ rule / คนละ workspace | `response.NotFound` | 404 |
| bind/validate fail | `response.BadRequest` | 400 |
| **enable** ตอน active เต็ม 20 (create ไม่ block — inactive แทน) | `response.Conflict` | 409 |
| DB/infra error | `response.InternalServerError` (log ก่อน — CLAUDE.md) | 500 |

**Redis (Core เป็นเจ้าของ):** ทุก write → `C.Del(ctx,"automation:rules:list:{wsID}")` list = cache-aside (`Get`→miss→DB→`Set` 3600s) engine cache `automation:rules:{wsID}` (active-only) เป็นของ RA-02+ CRUD แค่ Del ให้
