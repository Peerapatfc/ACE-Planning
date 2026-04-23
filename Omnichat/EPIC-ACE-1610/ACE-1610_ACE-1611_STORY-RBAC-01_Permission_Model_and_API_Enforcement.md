# STORY-RBAC-01: Permission Model & API Enforcement

**Status:** To Do | **ClickUp:** [ACE-1611](https://app.clickup.com/t/86d2hd98g) | **Assignee:** Peerapat Pongnipakorn | **SP:** 13

## Implementation Tasks (ClickUp Subtasks)

| Task ID | Name | Status |
|---|---|---|
| [ACE-1664](https://app.clickup.com/t/86d2qhew6) | Design diagrams | To Do |
| [ACE-1666](https://app.clickup.com/t/86d2qhjqm) | Design database | To Do |
| [ACE-1665](https://app.clickup.com/t/86d2qhfaj) | Create module | To Do |
| [ACE-1667](https://app.clickup.com/t/86d2qhm3x) | Guard middleware permission | To Do |
| _(new)_ | Create & seed permissions table in DB | To Do |
| _(new)_ | Store frontend route permission map (from RBAC-03) in DB | To Do |

## User Story

As a Backend Engineer
I want a clearly defined role-based permission model enforced at the API layer
so that every feature on the platform has a single reliable source of truth for access control.

## Detail / Description

Story นี้เป็น pure backend story ไม่มี UI ผลลัพธ์คือ permission model ที่ทุก feature อื่นต้องนำไปอ้างอิง
ก่อนหน้านี้ platform ไม่มี role system เพราะมีแค่ tenant เดียวและใช้คนเดียว story นี้วาง foundation ให้ถูกต้องตั้งแต่ต้น

**Focus point:**
- Permission check ต้องทำที่ API layer (backend) เสมอ frontend hide เป็นแค่ UX ไม่ใช่ security
- ทุก protected endpoint ต้องผ่าน permission middleware ก่อน handler ทำงาน
- Role scope ต่อ workspace: user คนเดียวสามารถมี role ต่างกันใน workspace ต่างกันได้ (รองรับ future multi-tenant)
- Action-based check ดีกว่า role-based check โดยตรง เพราะ extend ได้ง่ายกว่าในอนาคต

## Action List ที่ต้องมี permission check

| Action | Admin | Supervisor | Agent |
|---|---|---|---|
| reply_any_conversation | ✅ | ✅ | ✅ |
| assign_conversation | ✅ | ✅ | ❌ |
| change_conversation_status | ✅ | ✅ | ✅ |
| config_sla | ✅ | ✅ | ❌ |
| config_notification | ✅ | ✅ | ❌ |
| view_team_report | ✅ | ✅ | ❌ |
| manage_members | ✅ | ❌ | ❌ |
| manage_channels | ✅ | ❌ | ❌ |
| manage_workspace | ✅ | ❌ | ❌ |

## Scope of this story

- Role enum: `admin | supervisor | agent` บน `workspace_members` table
- **Permissions table ใน DB**: เก็บ action list และ role-action mapping แทนการใช้ hardcoded constant
- **Frontend route permission map**: ดึง structure จาก RBAC-03 มาเก็บใน DB ด้วย (ดู dependency section)
- Permission middleware: check role → check action (จาก DB) → ถ้าไม่มีสิทธิ์ return 403 Forbidden
- `resolveRole(userId, tenantId) → role` async helper — `tenantId` มาจาก `workspaceId` ใน URL path param (same value)
- `canDo(role, action) → boolean` pure helper (check against in-memory loaded matrix)
- Route-to-action mapping: กำหนด explicit map ของ `(method + path) → action_name`
- ทุก action ใน Action List ด้านบนต้องมี middleware protect
- Reply log: บันทึกว่าใครเป็นคนส่งข้อความแต่ละครั้ง (`replied_by` field) — เฉพาะ human-sent messages
- Admin protection: check ก่อน role change หรือ remove (ต้องมี Admin เหลืออย่างน้อย 1 คน) — ใน shared service
- ไม่รวม UI, invite flow, route guard ซึ่งอยู่ใน RBAC-02 และ RBAC-03

## Acceptance Criteria

### Role enum is defined and validated on every member record
- Given a new member is being added to a workspace
- When the role field is set
- Then it must be one of: `admin | supervisor | agent`
- And attempting to store any other value returns a 400 validation error
- And the role is always scoped to a specific `workspace_id`

### Permission middleware blocks unauthorized requests before handler executes
- Given an Agent makes a POST request to `/conversations/:id/assign`
- When the request reaches the server
- Then the permission middleware runs before the handler
- And because Agent does not have `assign_conversation` permission
- Then the API returns 403 Forbidden with body `{ error: "permission_denied", action: "assign_conversation", required_role: "supervisor" }`
- And the handler function is never executed

### canDo helper returns correct boolean for every role × action combination
- Given `canDo` is called with `userId`, `tenantId`, and `action`
- When `action = assign_conversation` and `role = supervisor` → returns `true`
- When `action = assign_conversation` and `role = agent` → returns `false`
- When `action = manage_members` and `role = supervisor` → returns `false`
- And all actions × 3 roles combinations in the Action List are covered

### Permission is scoped correctly to the workspace context
- Given a user is Admin in Workspace A and Agent in Workspace B
- When they call a `manage_members` endpoint with Workspace B context
- Then the permission check evaluates their role in Workspace B (Agent)
- And returns 403 even though they are Admin in another workspace

### Reply log records who sent each message
- Given any user sends a reply to a conversation
- When the message is saved
- Then the message record stores `replied_by = user_id` of the sender
- And this field is always populated, never nullable

### Admin protection check prevents workspace from having zero Admins
- Given a workspace has exactly 1 Admin
- When any request attempts to change that Admin's role or remove them
- Then the API returns 400 with error `"workspace_must_have_at_least_one_admin"`

### Admin protection allows role change when multiple Admins exist
- Given a workspace has 2+ Admins
- When an Admin downgrades their own role to Supervisor
- Then the API allows the change and remaining Admin count is still ≥ 1

### Admin protection applies to removing another Admin, not just self-demotion
- Given workspace has exactly 2 Admins (A and B)
- When Admin A attempts to remove Admin B from the workspace
- Then Admin protection check runs and counts remaining Admins after removal
- And if count would drop to 0, API returns 400 with `"workspace_must_have_at_least_one_admin"`
- Given workspace has 3+ Admins
- When Admin A removes Admin B
- Then API allows the removal

### Authenticated user with no workspace membership is rejected with 403
- Given an authenticated user (valid token) has no membership record in a workspace
- When they call any protected endpoint with that workspace context
- Then API returns 403 Forbidden (not 404)
- And no workspace data is exposed in the response body

### Unknown action defaults to deny
- Given middleware is invoked with an action name not present in the permission matrix
- Then API returns 403 Forbidden
- And no 500 error is thrown

### replied_by field is immutable after message creation
- Given a message exists with `replied_by = user_id`
- When any request attempts to update the `replied_by` field on that message
- Then API returns 400 and the field remains unchanged

### Unauthenticated requests are rejected before reaching permission check
- Given a request arrives without a valid authentication token
- Then it returns 401 Unauthorized before reaching the permission middleware

### Permission check applies to all HTTP methods on protected resources
- Given an Agent sends GET, POST, PATCH, and DELETE requests to a protected endpoint
- Then the permission middleware runs on all methods and 403 is returned where applicable

## UI/UX Notes

Story นี้ไม่มี UI

## Technical Notes

**Dependencies:**
- Authentication system ต้องมีก่อน: `user_id` ต้องพร้อมก่อน permission check ทำงาน
- `workspace_members` table ต้องรองรับ `role` field ก่อน
- **RBAC-03**: ต้องได้ structure ของ frontend route permission map ก่อนจึงจะ store ใน DB ได้ (dependency ต่อ RBAC-03 spec)

**Architecture: Permission Matrix ใน DB (อัพเดทจาก comments)**
- Permission matrix **ไม่ใช่** hardcoded constant — เก็บใน `permissions` table ใน DB
- ใช้ seed script โหลดค่าเริ่มต้นตาม Action List ด้านบน
- Frontend route permission map (จาก RBAC-03) เก็บใน DB table แยก
- WorkspaceId resolution: ดึงจาก URL **path param** (`:workspaceId`) — ภายในใช้เป็น `tenantId` (same value, 1 workspace = 1 tenant) รองรับ 1 user หลาย workspace

**Microservice Architecture (อัพเดทจาก "scope users service")**
- `workspace_members` table อยู่ใน **user-service DB** — ไม่ใช่ omnichat-service หรือ tenant-service
- user-service คือ identity & auth hub: เก็บทั้ง user identity, membership, และ permission matrix ไว้ในที่เดียว
- Permission middleware **ไม่** query DB โดยตรง — ส่ง MessagePattern ไปหา user-service:
  ```
  { cmd: 'get_workspace_member_role' } → payload: { userId, tenantId } → return: role | null
  ```
- ต้องเพิ่ม method `getWorkspaceMemberRole(userId, tenantId)` ใน user-service

**Function design:**
- `resolveRole(userId, tenantId): Promise<Role>` — async, calls user-service via message bus
- `canDo(role, action): boolean` — pure function, checks in-memory loaded permission matrix
- Middleware combines both: `resolveRole` → `canDo` → pass or 403
- Route-to-action map กำหนดเป็น explicit constant ใน code, key ต้องตรงกับ key ใน DB permissions table

**Error response format (สม่ำเสมอทุก endpoint):**
```json
{ "error": "permission_denied", "action": "...", "required_role": "..." }
```

**Special focus:**
- `replied_by` field ต้อง immutable หลัง message ถูก create ห้าม update ทีหลัง (human-sent messages only — platform ยังไม่มี automated messages)
- Admin protection logic ใน shared service เดียว ทั้ง role change และ remove member เรียกใช้
- Permission check ต้องใช้ DB state ปัจจุบัน (ไม่ใช่ token claims) — ถ้า role เปลี่ยน mid-session ต้องมีผลทันที
- Fail-closed: action ที่ไม่อยู่ใน matrix → default deny (403), ไม่ใช่ 500

## QA / Test Considerations

**Primary flows:**
- Agent call assign endpoint → 403
- Supervisor call config_sla endpoint → 200
- Admin call manage_members endpoint → 200
- User ส่ง reply → `replied_by` บันทึกถูก `user_id`

**Edge Cases:**
- User ที่ไม่มี membership ใน workspace → 403 (ไม่ใช่ 404, เพื่อไม่ expose workspace existence)
- Token หมดอายุ → 401 ก่อน permission check
- Workspace มี Admin เดียว ขอ down role ตัวเอง → 400
- Admin A ขอลบ Admin B ซึ่งเป็น Admin คนเดียวที่เหลือ → 400
- Action ที่ไม่อยู่ใน permission matrix → 403 (fail-closed, ไม่ใช่ 500)
- Role ไม่ถูกต้อง (เช่น "superadmin") → 400 validation error
- Race condition: 2 requests พร้อมกันขอลบ Admin คนสุดท้าย → ต้องมี DB-level constraint หรือ optimistic lock ป้องกัน

**Business-Critical Must Not Break:**
- ทุก protected endpoint ต้องมี permission check
- `replied_by` ต้องไม่เป็น null บน outbound message ใดๆ
- Admin protection ต้องทำงานทั้ง role change และ remove member scenario

**Test Types:**
- Unit tests สำหรับ `canDo(role, action)` ครอบคลุมทุก role × action combination (27 combinations)
- Unit tests สำหรับ `resolveRole` (mock DB)
- Integration tests สำหรับ middleware บน protected endpoints (ทุก action ใน Action List)
- Integration tests สำหรับ unknown action → 403 (fail-closed)
- Integration tests สำหรับ non-member authenticated user → 403 not 404
- Admin protection tests: 1 Admin → block (self + other), 2 Admins → allow
- `replied_by` tests: verify field บันทึกถูกต้อง, verify immutability (attempt update → 400)

**Open Questions (ต้องตอบก่อน implement):**
- ~~"scope users service"~~ — ปิด: `workspace_members` table ต้อง **live ใน user-service DB** (ไม่ใช่ omnichat-service หรือ tenant-service) เพราะ user-service เป็น identity & auth hub รวบ user identity, membership, และ permission matrix ไว้ในที่เดียว ทำให้ omnichat-service ต้องถามแค่ service เดียว. Permission middleware resolve role ผ่าน MessagePattern `{ cmd: 'get_workspace_member_role' }` — ไม่ query DB โดยตรง. ต้องเพิ่ม method ใหม่ใน user-service ด้วย
- ~~WorkspaceId มาจาก path param หรือ header~~ — ปิด: ใช้ **path param** (`:workspaceId`) เพราะ 1 user อยู่ได้หลาย workspace ใน future — JWT มีแค่ `userId`, middleware resolves role ผ่าน `resolveRole(userId, tenantId)` โดย `tenantId = workspaceId` จาก path param (same value)
- ~~Bot/system messages: `replied_by` เป็น null ได้ไหม~~ — ปิด: platform ยังไม่มี automated messages ทุก message มาจาก human agent เท่านั้น `replied_by` never null ได้เลย
- ~~Route-to-action map ใครเป็น owner~~ — ปิด: dev เป็น owner, action key ใน code ต้องตรงกับ key ใน DB เสมอ — enforce ผ่าน startup validation หรือ test ที่ตรวจ consistency ระหว่าง DB กับ code constant
