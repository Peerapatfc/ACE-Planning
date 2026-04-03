# STORY-RBAC-01: Permission Model & API Enforcement

**Status:** Backlog

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
- Permission middleware: check role → check action → ถ้าไม่มีสิทธิ์ return 403 Forbidden
- `canDo(userId, workspaceId, action)` helper function สำหรับ check permission แบบ programmatic
- ทุก action ใน Action List ด้านบนต้องมี middleware protect
- Reply log: บันทึกว่าใครเป็นคนส่งข้อความแต่ละครั้ง (`replied_by` field)
- Admin protection: check ก่อน role change หรือ remove (ต้องมี Admin เหลืออย่างน้อย 1 คน)
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
- Then the API returns 403 Forbidden with body `{ error: "permission_denied", action: "assign_conversation" }`
- And the handler function is never executed

### canDo helper returns correct boolean for every role × action combination
- Given `canDo` is called with `userId`, `workspaceId`, and `action`
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

**Special focus:**
- `canDo()` ต้องเป็น pure function: รับ `(userId, workspaceId, action)` → boolean ไม่มี side effect
- Permission matrix ควรอยู่ใน config file หรือ constant เดียว อย่า hard-code ซ้ำในแต่ละ endpoint
- Error response format: `{ error: "permission_denied", action: "...", required_role: "..." }`
- `replied_by` field ต้อง immutable หลัง message ถูก create ห้าม update ทีหลัง
- Admin protection logic ควรอยู่ใน shared service ที่ทั้ง role change และ remove member เรียกใช้

## QA / Test Considerations

**Primary flows:**
- Agent call assign endpoint → 403
- Supervisor call config_sla endpoint → 200
- Admin call manage_members endpoint → 200
- User ส่ง reply → `replied_by` บันทึกถูก `user_id`

**Edge Cases:**
- User ที่ไม่มี membership ใน workspace → 403 (ไม่ใช่ 404)
- Token หมดอายุ → 401 ก่อน permission check
- Workspace มี Admin เดียว ขอ down role ตัวเอง → 400
- Role ไม่ถูกต้อง (เช่น "superadmin") → 400 validation error

**Business-Critical Must Not Break:**
- ทุก protected endpoint ต้องมี permission check
- `replied_by` ต้องไม่เป็น null บน outbound message ใดๆ
- Admin protection ต้องทำงานทั้ง role change และ remove member scenario

**Test Types:**
- Unit tests สำหรับ `canDo` ครอบคลุมทุก role × action combination
- Integration tests สำหรับ middleware บน protected endpoints
- Admin protection tests: 1 Admin → block, 2 Admins → allow
- `replied_by` tests: verify field บันทึกถูกต้องทุก message type
