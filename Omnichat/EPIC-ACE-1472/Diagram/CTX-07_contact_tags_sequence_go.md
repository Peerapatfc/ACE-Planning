# CTX-07 Contact Tags — Sequence Diagram (Go / `ace-omnichat-go`)

> STORY: [ACE-2714](https://app.clickup.com/t/86d3knuen) · EPIC: ACE-1472 · ER: [contact_tags_er_go.md](./contact_tags_er_go.md)
> Scope: assign/remove tag บน contact · create inline · library CRUD · filter · realtime — auto-tagging/bulk/SLA-routing อยู่นอก scope
> Layering: `handler` → `orchestration` interface → `domain port` (repo) — **ไม่มี Core** (§หมายเหตุ) ชื่อทุกตัว verified กับ repo จริง

---

## Naming reference (verified จาก repo จริง)

| ใน diagram    | สัญลักษณ์/ชื่อจริงใน repo                                                                                                                             | อ้างอิง                                    |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| claims        | `clerk.SessionClaimsFromContext(ctx)` → `claims.ActiveOrganizationID` (org_xxx), `claims.Subject` (userId)                                            | `handler/conversation/handler.go`          |
| RBAC          | `appMiddleware.RequirePermission("org:xxx")` — เช็ค `claims.HasPermission`                                                                            | `middleware/rbac.go:17`, `router.go:86-92` |
| resolve wsID  | `resolveWorkspaceID(ctx, clerkOrgOrUUID)` — `len==36`→UUID else `WorkspaceRepository.GetIDByClerkOrgID`                                               | `manageconversation/orchestrator.go:36`    |
| response      | `response.Success / Created / BadRequest / NotFound / Conflict / InternalServerError` — body `{message, data}`                                        | `delivery/http/response/response.go`       |
| bind/validate | `c.Bind(&req)` แล้ว `c.Validate(&req)` (แยกกัน)                                                                                                       | pattern ทุก handler                        |
| **Orch**      | `managecontacttags.Orchestrator` (interface ใน `port.go`) — method รับ `XxxInput` DTO                                                                 | pattern: `manageconversation.Orchestrator` |
| **Repo**      | domain iface `domain/messaging.ContactTagRepository` (ใน `domain/messaging/port.go`) → impl `repository/postgres/messaging/contact_tag_repository.go` | pattern: `TagRepo`                         |
| **PubSub**    | `pubsub.Publisher.Publish(ctx, wsID, pubsub.Event{Type, Payload})` → Redis channel `omnichat:events:{workspaceUUID}` → WS hub fan-out (ทั้ง workspace — FE กรองด้วย `payload.contactId` เอง แบบเดียวกับ `message:new`) | `infrastructure/pubsub/pubsub.go:58` · `_shared/REPOSITORY_SUMMARY.md` §Realtime |
| **Filter**    | `inbox.ListConversationsInput` — เพิ่ม field `ContactTagIDs []string` (มี `TagID` ของ conversation tag อยู่แล้วเป็น precedent)                        | `orchestration/inbox/model.go:7`           |
| logger        | `log.Error().Err(e).Str("contact_id", id).Msg(…)` ก่อน 500 เสมอ                                                                                       | CLAUDE.md                                  |

> **ทำไมไม่มี Core:** CRUD+assign ใช้ที่ orchestrator เดียว (`managecontacttags`) ส่วน filter (S6) เป็นแค่เงื่อนไข query ใน conversation list repo เดิม ไม่ใช่ logic ที่ share — pass-through Core ผิดกฎ `_shared/ARCHITECTURE.md` ("worse than calling the repo directly") ถ้าอนาคต auto-tagging (out of scope) มาจริงค่อยยก dedup/limit logic ขึ้น Core

---

## Participants

| diagram          | ไฟล์จริง (ใหม่ ยกเว้นระบุ)                                              |
| ---------------- | ----------------------------------------------------------------------- |
| **FE**           | contact info panel / filter panel / library panel (`ace-omnichat-web`)  |
| **H** Handler    | `delivery/http/handler/contacttag/handler.go`                           |
| **MW** AuthMW    | `delivery/http/middleware/clerk_auth.go` (มีอยู่แล้ว)                   |
| **RBAC**         | `middleware/rbac.go` `RequirePermission` (มีอยู่แล้ว — branch ACE-2722) |
| **O** Orch       | `usecase/orchestration/managecontacttags/`                              |
| **Repo**         | `repository/postgres/messaging/contact_tag_repository.go`               |
| **DB**           | Postgres `messaging.contact_tag_labels` + `messaging.contact_tags`      |
| **PS** PubSub    | `infrastructure/pubsub` → Redis → WS hub (มีอยู่แล้ว)                   |
| **IO** InboxOrch | `usecase/orchestration/inbox/` (แก้เพิ่ม filter — S6)                   |

**Permission ต่อ endpoint** (enforce ที่ router ด้วย `RequirePermission`):

| Method / Path                                | permission                     | role           |
| -------------------------------------------- | ------------------------------ | -------------- |
| `GET /v1/contact-tags` (typeahead + library) | — (แค่ auth)                   | ทุก role       |
| `POST /v1/contact-tags` (create inline)      | — (แค่ auth)                   | ทุก role       |
| `POST /v1/contacts/:id/tags/:tagId`          | — (แค่ auth)                   | ทุก role       |
| `DELETE /v1/contacts/:id/tags/:tagId`        | — (แค่ auth)                   | ทุก role       |
| `PUT /v1/contact-tags/:id` (rename)          | `org:contact_tag:manage` ⚠️NEW | Admin·Sup      |
| `DELETE /v1/contact-tags/:id`                | `org:workspace:manage`         | **Admin only** |

> ⚠️ **ต้องเพิ่ม Clerk permission ใหม่ 1 key**: `org:contact_tag:manage` ให้ role Admin+Supervisor (key เดิม 7 ตัวไม่มีตัวไหน semantic ตรง) ส่วน delete ใช้ `org:workspace:manage` ตาม precedent เดียวกับ automation delete — sync กับ branch `feat/ACE-2722-rbac-permission`

---

## S0 — Common preamble (auth + RBAC + resolve)

```mermaid
sequenceDiagram
    autonumber
    actor U as Agent/Sup/Admin
    participant FE as [Client] web
    participant MW as [Auth] clerk middleware
    participant RBAC as [Guard] RequirePermission
    participant H as [Handler] contacttag.Handler
    participant O as [Orch] managecontacttags

    U->>FE: action
    FE->>MW: HTTP + Bearer JWT
    alt JWT ไม่ถูก
        MW-->>FE: 401
    else ok
        MW->>RBAC: (เฉพาะ route ที่มี permission)
        alt ไม่มี permission
            RBAC-->>FE: 403 Forbidden
        else ผ่าน
            RBAC->>H: next()
            H->>H: claims → userId + org_xxx
            H->>O: <Method>Input{WorkspaceID: org_xxx, ...} (เช่น AssignTagInput)
            O->>O: resolveWorkspaceID(org_xxx) → wsID
            Note over O: UUID column ห้ามรับ org_xxx ตรง (CLAUDE.md)<br/>userId (user_xxx) → resolve เป็น identity.users.id ก่อนเขียน created_by_id
        end
    end
```

---

## S1 — Typeahead + Library list (GET /v1/contact-tags)

```mermaid
sequenceDiagram
    autonumber
    participant FE as [Client] typeahead / library panel
    participant H as [Handler] contacttag.Handler
    participant O as [Orch] managecontacttags
    participant Repo as [Repo] ContactTagRepo
    participant DB as [DB] contact_tag_labels + contact_tags

    Note over FE,O: S0 (แค่ auth — ทุก role) → wsID
    FE->>H: GET /v1/contact-tags?q=vi&withUsage=true
    H->>O: ListTags
    O->>Repo: List(wsID, q)
    Repo->>DB: query tag ใน workspace (เฉพาะยังไม่ลบ) + prefix search<br/>+ นับ usage ต่อ tag ในครั้งเดียว (LEFT JOIN — tag ที่ไม่มีคนใช้ได้ 0)
    DB-->>Repo: rows
    Repo-->>O: tags + usageCount
    O-->>H: 200 {tags:[{id,name,color,usageCount}]}
    Note over FE: typeahead: แสดง tag เดิมก่อน<br/>ไม่เจอ → แสดงตัวเลือก "สร้าง tag ใหม่ 'VI…'"<br/>library panel: ใช้ usageCount โชว์จำนวน contact
```

> query ด้วย `UPPER(q)` เพราะชื่อเก็บ normalized uppercase อยู่แล้ว (ER ตัดสินใจ #4) — ไม่ต้อง ILIKE
> **ไม่มี Redis cache (จงใจ — ต่างจาก RA-01):** automation cache เพราะ engine อ่านทุก inbound message (hot path) แต่อันนี้ยิงตาม human action + ตารางเล็ก + query index ครอบ และ `usageCount` เปลี่ยนทุกครั้งที่ assign/remove → ถ้า cache ต้อง bust ใน S2–S5 ทุกจุด ได้ไม่คุ้มเสีย ถ้า metrics ชี้ว่า typeahead หนักจริงค่อยเพิ่ม cache เฉพาะชื่อ tag ทีหลังโดยไม่แตะ API

---

## S2 — Create tag inline (POST /v1/contact-tags) `AC1 Sc.2`

```mermaid
sequenceDiagram
    autonumber
    actor U as Agent
    participant FE as [Client] typeahead
    participant H as [Handler] contacttag.Handler
    participant O as [Orch] managecontacttags
    participant Repo as [Repo] ContactTagRepo
    participant DB as [DB] contact_tag_labels

    U->>FE: พิมพ์ชื่อใหม่ → กด "สร้าง"
    FE->>H: POST {name}
    H->>H: bind + validate (required, max=30)
    alt validate fail
        H-->>FE: 400 "ชื่อ tag ต้องไม่เกิน 30 ตัวอักษร"
    else ok
        H->>O: CreateTag
        O->>O: normalize: TRIM → UPPER → validate ≤30 อีกรอบหลัง trim
        O->>Repo: Create(wsID, name)
        Repo->>DB: INSERT contact_tag_labels
        alt ชื่อซ้ำกับ tag ที่มีอยู่ (DB ปฏิเสธด้วย unique index — กันได้แม้สร้างพร้อมกัน)
            DB-->>Repo: insert ไม่สำเร็จ: ชื่อนี้มีแล้ว
            Repo-->>O: ErrTagExists
            O-->>H: 409 "มี tag ชื่อนี้อยู่แล้ว"
            Note over FE: refresh typeahead → tag โผล่ให้เลือก → assign ต่อได้
        else inserted
            DB-->>Repo: tag
            O-->>H: 201 {tag}
        end
    end
    FE->>H: POST /v1/contacts/:id/tags/:tagId (ต่อด้วย S3 — assign)
```

> **create แล้ว FE ยิง assign ต่อ (2 calls)** — ไม่ทำ endpoint create+assign รวม: reuse S3 ทั้งก้อน, ถ้า assign fail (เช่น เต็ม 10) tag ยังอยู่ใน library ให้เลือกครั้งหน้า = พฤติกรรมที่ถูกอยู่แล้ว
> **duplicate-name → 409 Conflict** ตาม `CreateTag` ของ conversation tag เดิม (`inbox/handler.go:307`) — API family เดียวกันต้องพฤติกรรมเดียวกัน สอง agent สร้าง "VIP" พร้อมกันก็ยังจบที่ tag เดียว: คนแรกได้ 201, คนที่สองได้ 409 → refresh typeahead แล้วเลือกตัวที่มี (unique index กัน tag ซ้ำที่ DB อยู่แล้ว)

---

## S3 — Assign tag (POST /v1/contacts/:id/tags/:tagId) `AC1 · AC6 · realtime`

```mermaid
sequenceDiagram
    autonumber
    actor U as Agent
    participant FE as [Client] contact info panel
    participant H as [Handler] contacttag.Handler
    participant O as [Orch] managecontacttags
    participant Repo as [Repo] ContactTagRepo
    participant DB as [DB] contact_tags
    participant PS as [PubSub] Redis→WS

    U->>FE: เลือก tag จาก typeahead
    FE->>H: POST assign
    Note over H,O: S0 (แค่ auth) → wsID + userId(UUID)
    H->>O: AssignTag
    O->>Repo: ContactExists(wsID, contactID) + TagExists(wsID, tagID)
    alt contact/tag ไม่เจอ (หรือคนละ workspace)
        O-->>H: 404
    else เจอ
        O->>Repo: AssignWithLimit(wsID, contactID, tagID, byUserID, limit=10)
        Note over Repo,DB: 1 txn: advisory lock(contact_id) → นับ tag active<br/>→ ถ้ายังไม่ครบ 10 ค่อย INSERT (atomic — เกิน 10 เป็นไปไม่ได้)<br/>pattern เดียวกับ automation limit-20 (RA-01 S4)
        Repo->>DB: BEGIN · lock · count · conditional INSERT · COMMIT
        alt count ≥ 10 (เต็ม)
            Repo-->>O: ErrTagLimitExceeded
            O-->>H: 409 "เกินจำนวน tag สูงสุดต่อ contact (10) — ถอด tag เดิมออกก่อน"
        else tag นี้ติดอยู่แล้ว (unique index — กันได้แม้ 2 agents กดพร้อมกัน)
            DB-->>Repo: insert ไม่สำเร็จ: ติดอยู่แล้ว
            Repo-->>O: already assigned
            O-->>H: 200 (no-op — ไม่ duplicate, QA edge case)
        else inserted
            DB-->>Repo: row (audit: ใคร+เมื่อไหร่ อยู่ในแถว)
            O->>PS: Publish(wsID, {Type:"contact_tag:updated",<br/>Payload:{contactId, tags:[...]}})
            O-->>H: 201 {tags ปัจจุบันของ contact}
        end
    end
    PS-->>FE: WS: ทุก client ที่เปิด conversation ของ contact นี้<br/>อัปเดต chip โดยไม่ต้อง refresh (AC1/AC3)
```

> **dedup ที่ DB ไม่ใช่ check-then-insert** — partial unique index ปิด race (ต่างจาก `conversation_tags` เดิมที่เช็คระดับ app) repo จับ 23505 เป็น no-op
> **limit 10 = hard limit (ปิด TOCTOU)** — count + insert อยู่ใน **transaction เดียว** + `pg_advisory_xact_lock(contact_id)` → การติด tag บน contact เดียวกัน serialize กัน เกิน 10 เป็นไปไม่ได้แม้ 2 agents ติดคนละ tag พร้อมกันตอนมี 9 ตัว lock เป็นราย contact — ติด tag คนละ contact ไม่บล็อกกัน pattern เดียวกับ `CreateWithLimit`/`EnableIfUnderLimit` ของ automation limit-20

---

## S4 — Remove tag (DELETE /v1/contacts/:id/tags/:tagId) `AC2 · realtime`

```mermaid
sequenceDiagram
    autonumber
    participant FE as [Client] chip × hover
    participant H as [Handler] contacttag.Handler
    participant O as [Orch] managecontacttags
    participant Repo as [Repo] ContactTagRepo
    participant DB as [DB] contact_tags
    participant PS as [PubSub] Redis→WS

    FE->>H: DELETE assign
    Note over H,O: S0 (แค่ auth) → wsID + userId
    H->>O: RemoveTag
    O->>Repo: Remove(wsID, contactID, tagID, byUserID)
    Repo->>DB: UPDATE contact_tags SET deleted_at=now(), deleted_by_id=?<br/>WHERE ... AND deleted_at IS NULL
    alt RowsAffected == 0 (ไม่ได้ติดอยู่ / ถูกถอดไปแล้ว / คนละ workspace)
        O-->>H: 200 (no-op — idempotent ตาม RemoveTag ของ conversation tag เดิม)
    else removed
        Note over DB: soft delete — แถวเก็บ audit ใครลบ+เมื่อไหร่<br/>tag ยังอยู่ใน library · contact อื่นไม่กระทบ (AC2)
        O->>PS: Publish contact_tag:updated {contactId, tags}
        O-->>H: 200
    end
    PS-->>FE: chip หายทุก conversation ของ contact ทันที
```

---

## S5 — Library: rename + delete (Admin panel) `AC5`

```mermaid
sequenceDiagram
    autonumber
    actor A as Admin (·Sup rename ได้)
    participant FE as [Client] library panel
    participant H as [Handler] contacttag.Handler
    participant O as [Orch] managecontacttags
    participant Repo as [Repo] ContactTagRepo
    participant DB as [DB] contact_tag_labels + contact_tags
    participant PS as [PubSub] Redis→WS

    rect rgb(240,248,255)
    Note over A,PS: Rename — RequirePermission(org:contact_tag:manage) → Agent=403
    A->>FE: rename "VIP" → "VIP GOLD"
    FE->>H: PUT /v1/contact-tags/:id {name}
    H->>O: RenameTag
    O->>O: normalize (trim+UPPER, ≤30)
    O->>Repo: Rename(wsID, tagID, name)
    Repo->>DB: UPDATE contact_tag_labels SET name=? WHERE id+wsID AND deleted_at IS NULL
    alt ชื่อชนกับ tag active อื่น
        DB-->>Repo: 23505
        O-->>H: 409 "มี tag ชื่อนี้อยู่แล้ว"
    else RowsAffected == 0
        O-->>H: 404
    else ok
        Note over DB: assignment อ้าง tag_id → ชื่อใหม่มีผล<br/>ทุก contact ทันที ไม่ต้องติดใหม่ (AC5 Sc.1)
        O->>PS: Publish contact_tag:renamed {tagId, name}
        O-->>H: 200
    end
    end

    rect rgb(255,245,240)
    Note over A,PS: Delete — RequirePermission(org:workspace:manage) → Sup/Agent=403
    A->>FE: กดลบ "wholesale"
    FE->>H: GET /v1/contact-tags (withUsage — S1)
    FE->>A: confirm "กระทบ contact 25 ราย" (AC5 Sc.2)
    A->>FE: ยืนยัน
    FE->>H: DELETE /v1/contact-tags/:id
    H->>O: DeleteTag
    O->>Repo: SoftDelete(wsID, tagID)
    Repo->>DB: UPDATE contact_tag_labels SET deleted_at=now() WHERE id+wsID AND deleted_at IS NULL
    alt RowsAffected == 0 (ไม่มี / ถูกลบไปแล้ว)
        O-->>H: 200 (no-op — idempotent ตาม DeleteTag เดิม)
    else ok
        Note over DB: แถว assignment ไม่แตะ (audit อยู่ครบ)<br/>ทุก read JOIN t.deleted_at IS NULL → tag หายทุกที่ทันที<br/>ชื่อเดิมสร้างใหม่ได้ (partial unique — ER)
        O->>PS: Publish contact_tag:deleted {tagId}
        O-->>H: 200
    end
    end
    PS-->>FE: ทุกหน้าจอที่เปิดอยู่ถอด chip / refresh list (QA edge: ลบขณะหน้าจออื่นแสดงอยู่)
```

---

## S6 — Filter conversation list ด้วย contact tag `AC4`

```mermaid
sequenceDiagram
    autonumber
    participant FE as [Client] filter panel (section แยกจาก Conversation tag)
    participant H as [Handler] inbox (มีอยู่แล้ว — แก้เพิ่ม param)
    participant IO as [Orch] inbox (มีอยู่แล้ว)
    participant Repo as [Repo] ConversationRepo (มีอยู่แล้ว — แก้ query)
    participant DB as [DB] conversations ⋈ contact_tags

    FE->>H: GET /v1/conversations?contactTagIds=a,b&status=open&...
    Note over H,IO: S0 (แค่ auth) → wsID · filter อยู่ใน URL param (AC4 Sc.2)
    H->>IO: ListConversations{..., ContactTagIDs}
    IO->>Repo: List(input)
    Repo->>DB: query conversations เดิม + เงื่อนไขใหม่:<br/>contact_id อยู่ในกลุ่ม contact ที่ติด tag ที่เลือก (subquery)<br/>AND กับ filter เดิมทุกตัว (query เต็มดูใน ER doc §Filter query)
    DB-->>Repo: rows (ทุก conversation ของ contact ที่ติด tag — ไม่สน conversation tag)
    Repo-->>IO: items
    IO-->>H: 200 {items, nextCursor}
    Note over FE: response ใส่ contactTags แยก field จาก tags (conversation)<br/>เพื่อ chip คนละ style (outline vs filled)
```

> เพิ่ม `ContactTagIDs []string` ใน `ListConversationsInput` (model.go:7) + `contactTags []TagItem` ใน `ConversationItem` — filter เดิม (`TagID`, `Status`, …) ไม่แตะ = saved view เดิมทำงานเหมือนเดิม (must-not-break)

---

## หมายเหตุสำคัญ

**Realtime event ใหม่ 3 type** ใน `infrastructure/pubsub/pubsub.go`: `contact_tag:updated` (assign/remove — payload `{contactId, tags[]}`), `contact_tag:renamed`, `contact_tag:deleted` — ใช้ Publisher + WS hub เดิมทั้งหมด ไม่มี infra ใหม่ FE subscribe ต่อ workspace channel อยู่แล้ว แค่ handle type ใหม่แล้ว update ทุก conversation view ที่ `contactId` ตรง

**Audit (AC1/AC2) = columns ในแถว assignment** — `created_by_id/created_at` (ใครติด) + `deleted_by_id/deleted_at` (ใครลบ) ไม่มีตาราง audit แยก ไม่มี endpoint ดู log ใน story นี้ (เก็บไว้ก่อน ครบตาม AC "บันทึก audit")

**userId จาก claims เป็น `user_xxx`** — ก่อนเขียน `created_by_id/deleted_by_id` (UUID) ต้อง resolve ผ่าน `identity.users` เหมือน pattern `resolveWorkspaceID` (CLAUDE.md: UUID column ห้ามรับ Clerk id ตรง)

**Error → response helper:**
| กรณี | helper | code |
|---|---|---|
| JWT/claims ไม่ถูก | `response.Unauthorized` | 401 |
| ไม่มี permission (rename/delete library) | RBAC middleware | 403 |
| **assign**: contact/tag ไม่เจอ / คนละ workspace | `response.NotFound` — pre-check ก่อน insert (จงใจต่างจาก `ApplyTag` เดิมที่ปล่อย FK พังเป็น 500 — CLAUDE.md ห้าม 500) | 404 |
| **rename**: tag ไม่เจอ | `response.NotFound` (ตาม `UpdateTag` เดิม) | 404 |
| bind/validate fail (ชื่อเกิน 30, ว่าง) | `response.BadRequest` | 400 |
| create/rename ชนชื่อ tag ที่มีอยู่ | `response.Conflict` (ตาม `ErrTagExists` เดิม) | 409 |
| เกิน 10 tags/contact | `response.Conflict` (ตาม automation limit-20 — `automationrule/handler.go:51`) | 409 |
| assign ซ้ำ (ติดอยู่แล้ว) | **200 no-op** — DB unique index กันแถวซ้ำ | 200 |
| remove/delete ของที่ไม่มี/ลบไปแล้ว | **200 no-op** — idempotent ตาม `RemoveTag`/`DeleteTag` เดิม | 200 |
| DB/infra error | `response.InternalServerError` (log ก่อน) | 500 |

**สิ่งที่ต้องทำนอก repo นี้:** เพิ่ม Clerk permission `org:contact_tag:manage` (Admin+Sup) ใน Clerk Dashboard — เป็น key ที่ 8 (ปัจจุบันมี 7) และอัปเดต rbac test ให้ครอบ

**Checklist ตาม `_shared` ที่ diagram ไม่ได้วาด (แต่ต้องทำ):**
- **Wire DI** — ผูก `ContactTagRepo` + `managecontacttags.Orchestrator` + handler ใน `internal/app/wire/wire.go` แล้ว regenerate `wire_gen.go` (Adding a New Route step 6)
- **อัปเดต `_shared/REPOSITORY_SUMMARY.md` หลัง ship** (กฎ "Keeping this in sync"): ตาราง HTTP API (+6 endpoints), Orchestration index (+`managecontacttags`), Handler index (+`contacttag`), Domain Model (+`ContactTagLabel`), Realtime Events (+`contact_tag:*` 3 types), Database Init Files (+`15_contact_tags.sql`) และเพิ่มกล่องใน system diagram ของ `ARCHITECTURE.md`
