# STORY-BC-01: Create and Edit Broadcast — Sequence Diagrams

**Source:** [ClickUp Doc — Sequence Diagram / EPIC-A5: Broadcast / STORY-BC-01](https://app.clickup.com/25605274/v/dc/rdd4u-133996/rdd4u-90296) | **Epic:** [ACE-2236](https://app.clickup.com/t/86d318wjb) | **Story:** [ACE-2294](https://app.clickup.com/t/86d32c7k4)

Stack จริง = Go monolith ace-omnichat-go + Next.js ace-omnichat-web (base origin/dev)
Layering ตาม `_shared/ARCHITECTURE.md`: handler → orchestrator (interface) → repository port / provider port
orchestration package = `managebroadcast` · domain + repository package = `broadcast` (precedent automation) · DB schema = `messaging` · ไม่มี Core
ขอบเขต BC-01 = save + response · action draft = ทำครบในนี้ · send now = save แล้ว fire-and-forget dispatch (TODO → BC-03) · schedule = save status=scheduled แล้วจบ (worker ส่งทีหลัง = BC-03)

**Actor resolution:** handler map claims.ActiveOrganizationID/claims.Subject → in.ClerkOrgID/in.ClerkUserID (DTO) · orchestrator resolveActor(ClerkOrgID, ClerkUserID) → (workspaceID, actorID) ผ่าน GetByClerkOrgID + member lookup · ไม่ส่ง claims เข้า orchestrator

**Error convention:** business error → HTTP 200 + `{ error_code, message }` (NOT_FOUND · INVALID_STATUS · VALIDATION_ERROR) · success → 200/201 + data · system/infra (S3 put, DB) → 5xx · permission (mw RequirePermission) = 403 [ดูหมายเหตุ]

**Transaction:** mutation ห่อ DB write ด้วย tx (begin/commit) · S3 put อยู่นอก tx (ก่อน) · commit fail → compensate ลบ S3 ที่เพิ่ง put · ลบ S3 orphan/objects ทำหลัง commit

**รูปภาพ:** ตอน save · รูปเต็ม → original_key + resize preview → preview_key (S3 private · key unique uuid) · ส่ง LINE ตอน BC-03 (originalContentUrl + previewImageUrl)

**Broadcast code** = YYMM-000X · per workspace · reset ทุกเดือน · gen ตอน save · โชว์เป็น "Broadcast ID"
Delete / List / Cancel Schedule = AC ของ BC-05/BC-06 (implement จริงตอน BC-05/06)

**Permission (RBAC):** mutation ผูก `RequirePermission("org:broadcast:manage")` · read ไม่ gate · key ใหม่ ต้องสร้างใน Clerk Dashboard

## 1. Create — POST /broadcasts (multipart)

```mermaid
sequenceDiagram
  autonumber
  participant FE as [Client] ace-omnichat-web
  participant API as [Server] handler/broadcast
  participant ORCH as [Orchestration] managebroadcast
  participant S3 as [Provider] S3 object store
  participant REPO as [Repository] broadcast (messaging schema)

  Note over FE: ฟอร์มหน้าเดียว · ปุ่ม: Save draft / Schedule / Send now
  FE->>API: POST /broadcasts (multipart: action + fields + messages + image files)
  Note over API: mw: ClerkAuth + RequirePermission("org:broadcast:manage") (ไม่ผ่าน → 403) · c.Bind()+c.Validate()<br/>re-validate รูป (JPEG/PNG <= 10MB · fail → 200 {error_code: VALIDATION_ERROR}) · map claims → in.ClerkOrgID/ClerkUserID
  API->>ORCH: Save(in{ClerkOrgID, ClerkUserID, action, name, schedule, <br/>targeting, notificationDisabled, messages, imageFiles})
  Note over ORCH: resolveActor(ClerkOrgID, ClerkUserID) → workspaceID + actorID
  Note over ORCH: validate channel_account_id เป็นของ workspace (ไม่ใช่ → 200 {error_code: VALIDATION_ERROR}) · validation: draft = soft (allow incomplete) · send·schedule = hard [TODO → BC-03 AC2]<br/>gen original_key + preview_key (unique uuid) ต่อรูป · resize preview · content_type/size จากไฟล์
  Note over ORCH: key template — original_key = broadcasts/{workspaceID}/{uuid}/original.{ext}<br/>preview_key = broadcasts/{workspaceID}/{uuid}/preview.{ext}<br/>({uuid} = สุ่มใหม่ต่อรูป · ext จาก content_type · ไม่ผูก broadcast_id เพราะ put ก่อน insert)
  ORCH->>S3: PutObject รูปเต็ม (original_key) + preview (preview_key) · เฉพาะ image · private
  S3-->>ORCH: ok (ETag)
  Note over ORCH: put fail → 5xx (system · ยังไม่ begin tx · ไม่มี DB write · ไม่มี orphan)
  Note over ORCH,REPO: begin tx
  ORCH->>REPO: next code = MAX(seq ของ workspace+YYMM รวม soft-deleted)+1 → YYMM-000X
  ORCH->>REPO: INSERT broadcasts (code, status, created_by=updated_by=actorID, updated_at=NOW()) <br/>+ INSERT broadcast_messages ทุก bubble (position · text_content หรือ original_key/preview_key/content_type/size)
  Note over REPO: UNIQUE(workspace_id, code) · ชน → retry code +1
  REPO-->>ORCH: id
  Note over ORCH,REPO: commit (fail → 5xx + compensate ลบ S3 ที่เพิ่ง put)
  opt action = Send now  [TODO → BC-03 ACE-2457]
    ORCH-)ORCH: spawn dispatch async — fire-and-forget (go func + detached ctx + recover · ยิง LINE เบื้องหลัง · ไม่บล็อค response)
  end
  ORCH-->>API: id, code, status, updatedAt
  API-->>FE: 201 { id, code, status, updatedAt }
```

## 2. Edit — PATCH /broadcasts/{id} (multipart)

```mermaid
sequenceDiagram
  autonumber
  participant FE as [Client] ace-omnichat-web
  participant API as [Server] handler/broadcast
  participant ORCH as [Orchestration] managebroadcast
  participant S3 as [Provider] S3 object store
  participant REPO as [Repository] broadcast (messaging schema)

  Note over FE: ฟอร์มเดียวกับ create · ปุ่ม: Save draft / Schedule / Send now
  FE->>API: PATCH /broadcasts/{id} (multipart: action + updated fields + messages + image files)
  Note over API: mw: RequirePermission("org:broadcast:manage") · c.Bind()+c.Validate()<br/>re-validate รูป (JPEG/PNG <= 10MB · fail → 200 {error_code: VALIDATION_ERROR}) · map claims → in.ClerkOrgID/ClerkUserID
  API->>ORCH: Update(in{id, ClerkOrgID, ClerkUserID, action, name, schedule, <br/>targeting, notificationDisabled, messages, imageFiles})
  Note over ORCH: resolveActor(ClerkOrgID, ClerkUserID) → workspaceID + actorID
  ORCH->>REPO: load broadcast + broadcast_messages by (id, workspaceID) → ไม่พบ = 200 {error_code: NOT_FOUND, message} (เก็บ set {original_key, preview_key} เดิม)
  REPO-->>ORCH: broadcast + messages เดิม
  Note over ORCH: guard status เดิม ∈ {draft, scheduled} (อื่น → 200 {error_code: INVALID_STATUS, message}) · validate channel_account_id (ไม่ใช่ → 200 {error_code: VALIDATION_ERROR})<br/>validation draft=soft / send·schedule=hard [TODO → BC-03 AC2] · gen key (unique uuid) + resize preview ของรูปใหม่ · รูปไม่เปลี่ยน = อ้าง key เดิม
  Note over ORCH: key template — original_key = broadcasts/{workspaceID}/{uuid}/original.{ext} · preview_key = .../preview.{ext} ({uuid} สุ่มใหม่ต่อรูป · ไม่ผูก broadcast_id)
  ORCH->>S3: PutObject รูปเต็ม + preview · เฉพาะรูปใหม่/เปลี่ยน · private
  S3-->>ORCH: ok (ETag)
  Note over ORCH: put fail → 5xx (system · ยังไม่ begin tx)
  Note over ORCH,REPO: begin tx
  ORCH->>REPO: UPDATE broadcasts (code/created_by คงเดิม · updated_by=actorID · updated_at=NOW()) <br/>· replace messages = DELETE เดิม (by broadcast_id) → INSERT ชุดใหม่ (position)
  REPO-->>ORCH: ok
  Note over ORCH,REPO: commit (fail → 5xx + compensate ลบ S3 ที่เพิ่ง put · รูปเก่ายังอยู่)
  ORCH->>S3: delete {original_key, preview_key} เดิมที่ไม่อยู่ในชุดใหม่ (orphan · หลัง commit)
  opt action = Send now  [TODO → BC-03 ACE-2457]
    ORCH-)ORCH: spawn dispatch async — fire-and-forget (ยิง LINE เบื้องหลัง · ไม่บล็อค response)
  end
  ORCH-->>API: id, code, status, updatedAt
  API-->>FE: 200 { id, code, status, updatedAt }
```

## 3. Delete — DELETE /broadcasts/{id}

```mermaid
sequenceDiagram
  autonumber
  participant FE as [Client] ace-omnichat-web
  participant API as [Server] handler/broadcast
  participant ORCH as [Orchestration] managebroadcast
  participant S3 as [Provider] S3 object store
  participant REPO as [Repository] broadcast (messaging schema)

  FE->>API: DELETE /broadcasts/{id}
  Note over API: mw: RequirePermission("org:broadcast:manage") · map claims → in.ClerkOrgID/ClerkUserID
  API->>ORCH: DeleteDraft(in{id, ClerkOrgID, ClerkUserID})
  Note over ORCH: resolveActor(ClerkOrgID, ClerkUserID) → workspaceID + actorID
  ORCH->>REPO: load broadcast + broadcast_messages by (id, workspaceID) → ไม่พบ = 200 {error_code: NOT_FOUND, message} (เก็บ set {original_key, preview_key})
  REPO-->>ORCH: broadcast + messages
  Note over ORCH: guard status = draft (อื่น → 200 {error_code: INVALID_STATUS, message})
  Note over ORCH,REPO: begin tx
  ORCH->>REPO: UPDATE broadcasts (deleted_at=NOW(), updated_by=actorID) [soft delete]
  REPO-->>ORCH: ok
  Note over ORCH,REPO: commit
  ORCH->>S3: delete {original_key, preview_key} ที่ load มา (หลัง commit · fail = orphan → GC · ไม่ rollback)
  ORCH-->>API: ok
  API-->>FE: 200 ok
```

## 4. Get by ID — GET /broadcasts/{id}

```mermaid
sequenceDiagram
  autonumber
  participant FE as [Client] ace-omnichat-web
  participant API as [Server] handler/broadcast
  participant ORCH as [Orchestration] managebroadcast
  participant S3 as [Provider] S3 object store
  participant REPO as [Repository] broadcast (messaging schema)

  FE->>API: GET /broadcasts/{id}
  Note over API: mw: ClerkAuth เท่านั้น (ทุก role อ่านได้ · Agent view-only) · map claims → in.ClerkOrgID
  API->>ORCH: GetByID(in{id, ClerkOrgID})
  Note over ORCH: resolve workspace — GetByClerkOrgID(ClerkOrgID) → workspaceID (read · ไม่ต้อง member/actor)
  ORCH->>REPO: load broadcast + broadcast_messages by (id, workspaceID) → ไม่พบ = 200 {error_code: NOT_FOUND, message} (order by position · resolve created_by/updated_by จาก identity.users)
  REPO-->>ORCH: broadcast + messages + audit
  ORCH->>S3: gen signed URL จาก original_key + preview_key · private
  S3-->>ORCH: signed URLs
  ORCH-->>API: output DTO
  API-->>FE: 200 { broadcast, messages }
```

## 5. List — GET /broadcasts

```mermaid
sequenceDiagram
  autonumber
  participant FE as [Client] ace-omnichat-web
  participant API as [Server] handler/broadcast
  participant ORCH as [Orchestration] managebroadcast
  participant REPO as [Repository] broadcast (messaging schema)

  FE->>API: GET /broadcasts?status&q&lineOA&dateFrom&dateTo&page
  Note over API: mw: ClerkAuth เท่านั้น (ทุก role อ่านได้) · map claims → in.ClerkOrgID
  API->>ORCH: List(in{ClerkOrgID, filter})
  Note over ORCH: resolve workspace — GetByClerkOrgID(ClerkOrgID) → workspaceID (read · ไม่ต้อง member/actor)
  ORCH->>REPO: SELECT broadcasts WHERE workspace_id + deleted_at IS NULL <br/>+ filters · sort updated_at DESC · page 10 (index workspace_id+status / workspace_id+updated_at)
  REPO-->>ORCH: rows + total
  ORCH-->>API: items + total
  API-->>FE: 200 { items, total } (ว่าง = 200 items:[] · ไม่ error)
```

## 6. Cancel Schedule — POST /broadcasts/{id}/cancel-schedule

```mermaid
sequenceDiagram
  autonumber
  participant FE as [Client] ace-omnichat-web
  participant API as [Server] handler/broadcast
  participant ORCH as [Orchestration] managebroadcast
  participant REPO as [Repository] broadcast (messaging schema)

  FE->>API: POST /broadcasts/{id}/cancel-schedule
  Note over API: mw: RequirePermission("org:broadcast:manage") · map claims → in.ClerkOrgID/ClerkUserID
  API->>ORCH: CancelSchedule(in{id, ClerkOrgID, ClerkUserID})
  Note over ORCH: resolveActor(ClerkOrgID, ClerkUserID) → workspaceID + actorID
  ORCH->>REPO: load broadcast by (id, workspaceID) → ไม่พบ = 200 {error_code: NOT_FOUND, message}
  REPO-->>ORCH: broadcast
  Note over ORCH: guard status = scheduled (อื่น → 200 {error_code: INVALID_STATUS, message})
  Note over ORCH,REPO: begin tx
  ORCH->>REPO: UPDATE broadcasts (status → draft · scheduled_at → null · updated_by=actorID · updated_at=NOW())
  REPO-->>ORCH: ok
  Note over ORCH,REPO: commit
  ORCH-->>API: ok
  API-->>FE: 200 ok
```

## หมายเหตุ (จุดที่รวบเพื่อความกระชับ)

- **Error convention** — business error → HTTP 200 + `{ error_code, message }` (FE โชว์ message ได้เลย ไม่ต้อง handle HTTP error) · error_code: NOT_FOUND (by-id ไม่พบ/cross-workspace) · INVALID_STATUS (status guard) · VALIDATION_ERROR (รูป/channel/required) · system/infra (S3 put fail, DB error) → 5xx · success → 200/201 + data
- **Handler convention** — business error → response 200 + error_code (helper ใหม่ เช่น `BusinessError(c, code, msg)`) · ไม่ใช้ response.NotFound/Conflict (4xx) สำหรับ business · system → InternalServerError(500) · เหตุผล: HTTP status = signal ให้ monitoring/Grafana (อนาคต) — business error ไม่ควรปนใน error rate · CLAUDE.md ("wrong tenant → 404") = convention เดิม ยังไม่อัปเดต (ไม่ใช่เราผิด) · repo-wide + แก้ CLAUDE.md = doc task แยก (lead เคาะ)
- **Permission (403) คงเดิม** — RequirePermission เป็น shared mw (rbac.go return 403) · เป็น auth layer ไม่ใช่ business/domain error · ถ้าจะให้ 403 → 200+code ด้วย = ต้องแก้ mw กลาง (กระทบทั้ง repo) · แยก flag เป็น task ต่างหาก
- **Workspace scoping** — by-id op load WHERE id + workspace_id → ไม่พบ = 200 {error_code: NOT_FOUND} (มาสก์ cross-workspace ด้วย code เดียวกัน → ไม่ leak) · list scope workspace_id
- **status guard** — edit ∈ {draft, scheduled} · delete = draft · cancel = scheduled · ผิด → 200 {error_code: INVALID_STATUS}
- **Transaction** — mutation ห่อ DB write ด้วย begin tx ... commit · S3 put นอก tx (ก่อน) · commit fail → 5xx + compensate ลบ S3 ที่เพิ่ง put · ลบ S3 orphan/objects หลัง commit · read (get/list) ไม่มี tx
- **Common skeleton (6 เส้น pattern เดียวกัน)** — FE→API → Note(mw · bind/validate · map claims) → API→ORCH(in{...}) → Note(resolve) → [by-id: load →ไม่พบ 200 NOT_FOUND] → [Note guards] → [S3 put นอก tx] → begin tx → REPO write → commit → [S3 cleanup] → [opt Send now] → ORCH→API → API→FE
- **รูปภาพ (2 objects/image)** — original_key (รูปเต็ม → originalContentUrl) + preview_key (resize ตอน save → previewImageUrl) · S3 private · key unique uuid ต่อ upload (ห้าม derive จาก position) · preview ในหน้า = signed URL · size = โชว์ "2.3 MB" (AC10)
- **broadcast_messages handling** — Create: INSERT ทุก bubble (position) · Edit = full replace: load เดิม (เก็บ 2 key set) → put รูปใหม่ → tx DELETE เดิม → INSERT ชุดใหม่ → หลัง commit ลบ S3 orphan · full-replace เพราะ leaf + position จาก FE
- **Fire-and-forget (Send now)** — spawn goroutine ก่อน return (go func + detached ctx + recover) · ORCH-)ORCH มาก่อน ORCH-->>API · ส่งจริง = BC-03 (อาจใช้ asynq queue เพื่อ durability)
- **send fields (sent_at, error_reason)** — BC-01 ปล่อย null
- **Actor resolution** — resolveActor(ClerkOrgID[, ClerkUserID]) → (workspaceID[, actorID]) · read ใช้แค่ workspaceID · mutation ใช้ actorID (created_by/updated_by)
- **Save → response → action** — draft = BC-01 ทำครบ · schedule = status scheduled (worker BC-03) · send now = status sending · fire-and-forget (BC-03)
- **Response body** — create 201 { id, code, status, updatedAt } · edit 200 { id, code, status, updatedAt } · business error 200 { error_code, message } · UI = FE ตัดสินจาก action/status/error_code
- **notification_disabled** — compose-time (admin toggle · default false) · BC-03 → LINE notificationDisabled
- **Broadcast code** — MAX(seq ของ workspace+เดือน รวม soft-deleted)+1 → YYMM-000X · UNIQUE (workspace_id, code) · ชน → retry +1
- **Package / schema / layering** — package broadcast · orchestration managebroadcast · schema messaging · handler → orchestrator → repo/S3 · ไม่มี Core
- **targeting** = everyone อย่างเดียว · specific/tags = BC-02
