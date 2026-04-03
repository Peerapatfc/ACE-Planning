# EPIC ACE-1610 RBAC — Gap Analysis & Implementation Plan

## Executive Summary

All three stories are in **Backlog** status. Code exploration reveals:

| Story | Epic Requirement | Implementation Status | % Done |
|---|---|---|---|
| RBAC-01 | Permission Model & API Enforcement | **Not started** | ~0% |
| RBAC-02 | Member Management | **Scaffolding only** | ~20% |
| RBAC-03 | Frontend Permission Enforcement | **Not started** | ~0% |

The platform has no role concept in any database schema, no JWT role claim, no permission middleware, and no `canDo()` abstraction. The invitation flow has basic token mechanics but is missing the `role` field, resend/cancel actions, email delivery, and every admin-protection rule. The frontend role check is a hardcoded `role: "admin"` string in the layout — not real data.

---

## RBAC-01 — Permission Model & API Enforcement

### What Exists

- `jwt-auth.guard.ts` in api-gateway (authentication only — no authorization)
- `JwtPayload` type in `@monorepo/shared` with fields: `sub`, `tenantId`, `email`, `firstName`, `lastName` — **no `role` field**
- Message record has `agent_id` field — **not `replied_by`**; no immutability constraint

### What Is Missing

| Gap | Detail | Files to create/change |
|---|---|---|
| `workspace_members` table | Junction table `(user_id, workspace_id, role)` doesn't exist in any Prisma schema | `tenant-service/prisma/schema.prisma` |
| Role enum | `admin \| supervisor \| agent` not defined anywhere | New constant in `@monorepo/shared` |
| `role` in JWT payload | `JwtPayload` interface lacks `role`; `issueTokens()` doesn't look up or embed role | `shared/src/types/auth.types.ts`, `api-gateway/src/auth/auth.service.ts` |
| `canDo()` helper | No action-based permission function exists anywhere | New service/util in `api-gateway` or `@monorepo/shared` |
| Permission matrix constant | No single place defining which roles can do which of the 9 actions | New constants file |
| Permission middleware/guard | No NestJS guard evaluates `canDo()` before endpoint handler | New `PermissionGuard` + `@RequirePermission()` decorator |
| Protected endpoints | `POST /conversations/:id/assign`, SLA config, member management, channel management, workspace config — none have permission guards | Multiple controllers |
| `replied_by` field on Message | Schema uses `agent_id`; field must be renamed/added and must be non-nullable and immutable | `omnichat-service/prisma/schema.prisma`, `messages.service.ts` |
| Admin protection service | No service enforcing "workspace must have ≥1 admin" before role-change or remove | New shared service in `tenant-service` |
| 403 error format | No standardized `{ error: "permission_denied", action: "...", required_role: "..." }` response | Shared error DTO |

### Implementation Plan

**Step 1 — Data Model (prerequisite for everything)**

Add `WorkspaceMember` to `tenant-service/prisma/schema.prisma`:

```prisma
model WorkspaceMember {
  id           String    @id @default(uuid())
  tenant_id    String
  user_id      String
  role         String    // admin | supervisor | agent
  joined_at    DateTime  @default(now())
  created_at   DateTime  @default(now())
  updated_at   DateTime  @updatedAt
  deleted_at   DateTime?

  tenant Tenant @relation(fields: [tenant_id], references: [id])

  @@unique([tenant_id, user_id])
  @@index([tenant_id, role])
  @@map("workspace_members")
}
```

Rename `agent_id` → `replied_by` on `Message` in `omnichat-service/prisma/schema.prisma` (make non-nullable for outbound direction).

**Step 2 — Role in JWT**

- Add `role: string` to `JwtPayload` in `packages/shared/src/types/auth.types.ts`
- Update `issueTokens()` in `api-gateway/src/auth/auth.service.ts` to query `WorkspaceMember` and embed role in access token

**Step 3 — Permission Matrix + `canDo()` Helper**

Create `packages/shared/src/constants/permissions.ts`:

```typescript
export const PERMISSION_MATRIX: Record<string, string[]> = {
  reply_any_conversation:     ['admin', 'supervisor', 'agent'],
  assign_conversation:        ['admin', 'supervisor'],
  change_conversation_status: ['admin', 'supervisor', 'agent'],
  config_sla:                 ['admin', 'supervisor'],
  config_notification:        ['admin', 'supervisor'],
  view_team_report:           ['admin', 'supervisor'],
  manage_members:             ['admin'],
  manage_channels:            ['admin'],
  manage_workspace:           ['admin'],
};

export function canDo(role: string, action: string): boolean {
  return PERMISSION_MATRIX[action]?.includes(role) ?? false;
}
```

**Step 4 — NestJS `PermissionGuard`**

Create guard in `api-gateway/src/auth/guards/permission.guard.ts` that:
1. Reads `role` from JWT payload
2. Reads required action from `@RequirePermission('action_name')` decorator via `Reflector`
3. Calls `canDo(role, action)` → returns 403 with standardized body if false

```typescript
// 403 response body format
{ error: "permission_denied", action: "assign_conversation", required_role: "supervisor" }
```

**Step 5 — Apply Guard to All 9 Protected Action Endpoints**

Apply `@RequirePermission()` to every relevant controller method:

| Endpoint | Action |
|---|---|
| `POST /conversations/:id/assign` | `assign_conversation` |
| `PATCH /conversations/:id/status` | `change_conversation_status` |
| `POST/PATCH /settings/sla` | `config_sla` |
| `POST/PATCH /settings/notifications/rules` | `config_notification` |
| `GET /reports/team` | `view_team_report` |
| `POST/DELETE /settings/members` | `manage_members` |
| `POST/PATCH/DELETE /settings/channels` | `manage_channels` |
| `PATCH /settings/workspace` | `manage_workspace` |

**Step 6 — Admin Protection Service**

Create `tenant-service/src/tenants/admin-protection.service.ts`:

```typescript
async ensureAdminRemains(tenantId: string, excludeUserId: string): Promise<void> {
  const adminCount = await this.prisma.workspaceMember.count({
    where: {
      tenant_id: tenantId,
      role: 'admin',
      deleted_at: null,
      user_id: { not: excludeUserId },
    },
  });
  if (adminCount < 1) {
    throw new BadRequestException('workspace_must_have_at_least_one_admin');
  }
}
```

**Step 7 — First Admin on Workspace Creation**

In `api-gateway/src/auth/auth.service.ts` `register()`: after creating tenant + user, insert a `WorkspaceMember` row with `role: 'admin'`.

**Step 8 — `replied_by` Enforcement**

Update `omnichat-service/src/messages/messages.service.ts` outbound message creation to set `replied_by = agentUserId` from caller context. Field must be non-nullable for outbound messages and immutable after creation.

### Test Cases

| Test | Expectation |
|---|---|
| `canDo('agent', 'assign_conversation')` | `false` |
| `canDo('supervisor', 'config_sla')` | `true` |
| `canDo('supervisor', 'manage_members')` | `false` |
| Agent calls `POST /conversations/:id/assign` | `403 { error: "permission_denied", action: "assign_conversation" }` |
| User with no workspace membership calls protected endpoint | `403` (not 404) |
| Token missing / expired | `401` before permission check |
| Workspace has 1 admin, request to demote them | `400 workspace_must_have_at_least_one_admin` |
| Workspace has 2 admins, admin self-demotes | `200` |
| Outbound message created | `replied_by` = sender user ID, non-null |

### Acceptance Criteria

- All 9 actions from the permission matrix are enforced at API layer — verified by integration tests
- `canDo()` unit tests cover all 27 (9 actions × 3 roles) combinations
- No protected handler executes when caller lacks permission
- `replied_by` is never null on any outbound message record
- Workspace always has ≥1 admin

### Story Points: **8 points**
### Priority: **P0 — Blocks everything else**
### Risk: **HIGH** — Every other feature currently has zero access control. Schema migration requires coordination with omnichat-service migration (`replied_by` rename).

---

## RBAC-02 — Member Management

### What Exists

| Component | Status |
|---|---|
| Invitation token creation (32-byte hex) | ✅ Implemented |
| Invitation 7-day expiry | ✅ Implemented |
| Token hashing (SHA-256) | ✅ Implemented |
| Accept invitation page (UI) | ✅ Implemented |
| Invite member form (UI) | ✅ Implemented (basic, no role field) |
| Members list page (UI) | ✅ Scaffolded (read-only, no role/actions) |
| Invitations list page (UI) | ✅ Scaffolded (no Resend/Cancel) |

### What Is Missing

| Gap | Detail |
|---|---|
| `role` field on Invitation | `CreateInvitationDto` has no `role` — invitations can't carry a role assignment |
| `role` column in `invitations` table | `tenant-service` schema has no `role` on `Invitation` model |
| `workspace_members` table | Accepting an invitation has nowhere to store the resulting membership with role |
| Resend invitation | No endpoint (`PATCH /invitations/:id/resend`) and no UI action |
| Cancel invitation | No endpoint (`DELETE /invitations/:id`) and no UI action |
| Remove member | No endpoint and no UI |
| Change role | No endpoint and no UI |
| Session revocation on removal | No mechanism to revoke refresh tokens for a removed user |
| "former member" display | `replied_by` fallback for removed members not implemented |
| Admin protection on remove/role-change | No validation before any member action |
| Email delivery | `createInvitation()` creates the DB record only — no email is ever sent |
| Members page: role column | Table only shows Name, Email, Joined — missing Role, Last Active, Actions |
| Members page: actions | No inline role dropdown, no Remove button |
| Duplicate invite guard | Checks `tenant_id + email + status` but no role validation |
| Member limit enforcement | No limit check implemented |
| First Admin auto-assignment | When workspace is created, creator isn't added to `workspace_members` as admin |

### Implementation Plan

**Step 1 — Schema: add `role` to Invitation, create `WorkspaceMember`**
(Shared with RBAC-01 Step 1)

```prisma
// Add to Invitation model:
role String @default("agent") // admin | supervisor | agent
```

**Step 2 — Update `CreateInvitationDto`**

```typescript
@IsEnum(['admin', 'supervisor', 'agent'])
role: string;
```

**Step 3 — Resend Invitation Endpoint**

`PATCH /invitations/:id/resend` in `tenant-service`:
- Generate new token, update `token_hash`, `expires_at = now + 7d`, `status = 'pending'`
- Trigger email resend

**Step 4 — Cancel Invitation Endpoint**

`DELETE /invitations/:id` in `tenant-service`:
- Set `status = 'cancelled'`; existing token no longer validates on accept

**Step 5 — `acceptInvitation()` Creates WorkspaceMember**

Update `invitations.service.ts` `acceptInvitation()`:
- After marking accepted, upsert `WorkspaceMember` with the `role` from the invitation record

**Step 6 — Remove Member Endpoint**

`DELETE /workspace-members/:userId` in `tenant-service`:
- Calls admin-protection check (RBAC-01 Step 6)
- Sets `deleted_at` on `WorkspaceMember`
- Calls `user-service` via TCP to revoke all active refresh tokens for that `user_id`

**Step 7 — Change Role Endpoint**

`PATCH /workspace-members/:userId/role` in `tenant-service`:
- Calls admin-protection check
- Updates `role` on `WorkspaceMember`
- Does **not** revoke session — new permission takes effect on next API call

**Step 8 — Email Delivery Integration**

Integrate email sender (SES / SMTP / Resend) into `tenant-service`. Triggered after invitation create and resend. Template includes `{invitation_url}` pointing to `https://<domain>/invite/<raw_token>`.

> **External dependency:** Domain verification must complete before this can go to production. Development can proceed with mocked/console email.

**Step 9 — Frontend: Update Members Page**

Add Role column, Last Active column, inline role dropdown (with confirm dialog), Remove button (with confirm dialog) to `settings/members/page.tsx`.

**Step 10 — Frontend: Update Invitations Page**

Add Resend and Cancel action buttons to each pending invitation row. Add Role column.

**Step 11 — Frontend: Update Invite Form**

Add role selector (Admin / Supervisor / Agent) to `InviteMemberForm`.

### Test Cases

| Test | Expectation |
|---|---|
| Invite with role `agent` → accept → check `workspace_members` | Row exists with `role = 'agent'` |
| Invite same email twice | 409 Conflict |
| Accept invitation after 7 days | Rejected; status = `expired` |
| Cancel invitation → use original link | Invalid / 404 |
| Resend → old link invalid, new link works | ✅ |
| Remove member → member calls any API | 401 |
| Workspace with 1 admin → remove admin | 400 `workspace_must_have_at_least_one_admin` |
| Change role → next API call uses new permissions | ✅ (no re-login required) |
| Removed member reply log display | Shows `"former member (Name)"` |

### Acceptance Criteria

- Invitation flow end-to-end: invite (with role) → email sent → accept within 7 days → `workspace_members` row with correct role
- Resend resets expiry; old token invalidated
- Removed member receives 401 on their next API call (session revoked immediately)
- Workspace always has ≥1 admin — enforced at backend
- All member management actions accessible only to Admin role (guarded by RBAC-01 `manage_members` permission)

### Story Points: **13 points**
### Priority: **P1 — Requires RBAC-01 as prerequisite**
### Risk: **MEDIUM-HIGH** — Email delivery has external dependency (domain verification). Session revocation requires cross-service TCP communication not yet established between `tenant-service` and `user-service`.

---

## RBAC-03 — Frontend Permission Enforcement

### What Exists

| Component | Status |
|---|---|
| Auth-only redirect in `(main)/layout.tsx` | ✅ Redirects to `/login` if no session |
| `/unauthorized` page (static) | ✅ Exists but not wired to role-based checks |
| Next.js App Router (supports layout-level SSR guards) | ✅ Architecture supports the pattern |

### What Is Missing

| Gap | Detail |
|---|---|
| `role` in session/app state | JWT payload has no role; `currentUser` in dashboard layout hardcodes `role: "admin"` literal |
| `usePermission` hook | Does not exist |
| Route guards (role-based) | Layout only checks `me` (auth), not `me.role` per route |
| Role-based sidebar filtering | Sidebar renders all items for all users |
| Assign panel visibility | No `canDo` check — Agent sees Assign button |
| 403 page integration | `/unauthorized` page exists but 403 API responses don't trigger it |
| Flash-of-unauthorized-content prevention | No SSR role check before rendering restricted pages |
| Session expiry with return URL | On 401, redirects to `/login` but doesn't save current URL |
| Conversation assigned-to banner | "assigned to [Agent Name]" banner not implemented |
| `usePermission` updates on role change | No invalidation mechanism when role changes mid-session |

### Implementation Plan

**Step 1 — Embed Role in Session**

After RBAC-01 adds `role` to JWT, update `getMeAction()` in `workspace-admin/src/server/auth.ts` to decode and return `role`. Update `CurrentUser` interface:

```typescript
export interface CurrentUser {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  avatar_url: string | null;
  role: 'admin' | 'supervisor' | 'agent';
}
```

Remove hardcoded `role: "admin"` from `workspace-admin/src/app/(main)/dashboard/layout.tsx`.

**Step 2 — `usePermission` Hook**

Create `workspace-admin/src/hooks/use-permission.ts`:

```typescript
// Reads role from Zustand/React Context populated at session load
// Returns boolean — never calls an API
export function usePermission(action: PermissionAction): boolean {
  const role = useCurrentUserStore((s) => s.role);
  return canDo(role, action); // imported from @monorepo/shared
}
```

**Step 3 — Role-Based Route Guards**

For each restricted settings route, add a server-side check in the layout or page:

```typescript
// e.g., app/(main)/settings/sla/layout.tsx
const me = await getMeAction();
if (!canDo(me.role, 'config_sla')) {
  redirect('/inbox?error=unauthorized');
}
```

This executes before any page content renders — prevents flash of unauthorized content.

**Route Permission Map:**

| Route | Required Action |
|---|---|
| `/settings/workspace/*` | `manage_workspace` |
| `/settings/channels` | `manage_channels` |
| `/settings/sla` | `config_sla` |
| `/settings/notifications/rules` | `config_notification` |
| `/settings/notifications/preferences` | (all roles — no guard needed) |
| `/settings/members` | `manage_members` |

**Step 4 — Role-Based Sidebar Filtering**

Update `AppSidebar` / sidebar-items logic to filter `NavGroup` items based on `currentUser.role` before rendering:

- **Admin:** all sections
- **Supervisor:** SLA, Notifications only (Workspace, Channels, Members absent from DOM)
- **Agent:** Notifications > My Preferences only

Hidden items must be **completely absent from DOM** — not greyed-out or hidden via CSS.

**Step 5 — Assign Panel Conditional Rendering**

Wrap `AssignPanel` in conversation detail with:

```tsx
{canDo(currentUser.role, 'assign_conversation') && <AssignPanel ... />}
```

Must be SSR-rendered conditionally (not a client-side toggle) to prevent flash.

**Step 6 — 403 API Error Handling**

In the HTTP client, intercept 403 responses and redirect to `/unauthorized`. The `/unauthorized` page must not expose which resource was being accessed.

**Step 7 — Session Expiry with Return URL**

On 401 response, save current path and redirect:

```
/login?returnTo={encodeURIComponent(currentPath)}
```

Display message: `"กรุณา login ใหม่ session หมดอายุแล้ว"`. After login success, read `returnTo` param and redirect there.

**Step 8 — Conversation Assigned-To Banner**

In conversation view, when `conversation.assigned_agent_id !== currentUser.id` (and conversation is assigned), show banner: `"Assigned to {assigned_agent_name}"`. Data is already in the `Conversation` model — no extra API call needed.

**Step 9 — `usePermission` Invalidation on Role Change**

When the token refresh flow issues a new access token (with updated role), re-derive role from the new token and update the Zustand store. Hook consumers reactively re-render with updated permission values.

### Test Cases

| Test | Expectation |
|---|---|
| Agent navigates directly to `/settings/sla` | Redirect to `/inbox` + toast; no SLA content in DOM |
| Supervisor opens Settings sidebar | Only SLA and Notifications present; no Workspace / Members |
| Agent opens Settings sidebar | Only Notifications > My Preferences present |
| Agent opens conversation assigned to another agent | Reply input enabled; "Assigned to [Name]" banner visible; no Assign panel |
| Server returns 403 | `/unauthorized` page shown with back button; no crash |
| `usePermission('assign_conversation')` — Supervisor | `true` |
| `usePermission('assign_conversation')` — Agent | `false` |
| Session token expires mid-session | Redirect to `/login?returnTo=...` with expiry message |
| Role changed server-side → user refreshes token | New permissions applied without full page reload |

### Acceptance Criteria

- No restricted element appears in the DOM — even briefly — for users without permission (verified by visual regression + DOM inspection)
- Agent cannot see Assign panel in any conversation under any circumstance
- Route guard redirects before page render on unauthorized route access
- `usePermission` derives from cached session — zero extra API calls per render
- 403 responses from server never cause blank page or crash
- Session expiry preserves current URL for post-login return

### Story Points: **8 points**
### Priority: **P2 — Requires RBAC-01 (role in JWT) as hard prerequisite**
### Risk: **MEDIUM** — Flash-of-unauthorized-content requires SSR-first checks; any client-side shortcut will fail the acceptance criteria. React Compiler (enabled in this project) may affect `usePermission` memoization — test carefully.

---

## Priority Ranking

| Rank | Feature | Story | Points | Blocks |
|---|---|---|---|---|
| P0-1 | `workspace_members` table & role enum | RBAC-01/02 | 5 | Everything |
| P0-2 | Permission matrix & `canDo()` helper | RBAC-01 | 3 | All guards |
| P0-3 | Permission middleware on protected endpoints | RBAC-01 | 5 | API security |
| P0-4 | Admin protection service | RBAC-01/02 | 2 | Member ops |
| P0-5 | `usePermission` hook & role in JWT | RBAC-03 | 3 | All FE guards |
| P0-6 | Route guards | RBAC-03 | 5 | Settings access |
| P1-1 | `replied_by` field on messages | RBAC-01 | 3 | Audit trail |
| P1-2 | Complete Member Management API | RBAC-02 | 8 | Admin workflow |
| P1-3 | Email delivery integration | RBAC-02 | 5 | Invite flow |
| P1-4 | Complete Members Management UI | RBAC-02 | 5 | Admin usability |
| P1-5 | Role-based sidebar filtering | RBAC-03 | 3 | UX clarity |
| P1-6 | 403 page & session expiry handling | RBAC-03 | 3 | Error UX |
| P1-7 | Assign panel visibility & banner | RBAC-03 | 2 | Agent UX |

**Total: 52 story points**

---

## Recommended Sprint Breakdown

### Sprint A — Backend Foundation (23 points)

| Task | Points |
|---|---|
| `workspace_members` table + `role` on Invitation schema | 5 |
| Permission matrix + `canDo()` in `@monorepo/shared` | 3 |
| `PermissionGuard` + `@RequirePermission()` decorator | 5 |
| Admin protection service | 2 |
| Role embedded in JWT (`issueTokens` update) | 2 |
| First Admin auto-assignment on workspace creation | 1 |
| `replied_by` field on Message | 3 |
| Unit tests: 27 `canDo()` combinations | 2 |

### Sprint B — Member Management + Frontend (29 points)

| Task | Points |
|---|---|
| `role` on `CreateInvitationDto` + `acceptInvitation()` creates WorkspaceMember | 2 |
| Resend + Cancel invitation endpoints | 3 |
| Change role + Remove member endpoints (with session revocation) | 5 |
| Email delivery integration | 5 |
| Complete Members page UI (role, last active, change role, remove) | 5 |
| `usePermission` hook | 3 |
| Role-based route guards (6 routes) | 3 |
| Role-based sidebar filtering | 3 |

> RBAC-03 items can begin in parallel once Sprint A's JWT role change is available.

---

## Risk Summary

| Risk | Severity | Mitigation |
|---|---|---|
| Schema migration — all existing users have no `workspace_members` row | HIGH | Run seeder to insert Admin rows for all existing tenant users during migration |
| `replied_by` rename on `messages` table — may break existing queries | MEDIUM | Add new column, backfill from `agent_id`, deprecate old column in separate migration |
| Email domain not yet verified (per story note) | HIGH | Mock/console email in dev; set as release gate before production |
| Session revocation cross-service (tenant-service → user-service) | HIGH | New TCP message `{ cmd: 'revoke_all_tokens' }` — validate TCP channel pattern with integration test |
| Flash-of-unauthorized-content in Next.js App Router | MEDIUM | Enforce SSR-level role checks in server layouts, not client components — validate in code review |
| Hardcoded `role: "admin"` in dashboard layout | HIGH | Must be removed before any role-aware feature is demoed or tested |
| React Compiler may affect `usePermission` memoization | LOW | Test hook behavior carefully; avoid manual `useMemo` wrapping unless compiler output verified |
| Missed endpoint in permission coverage | MEDIUM | Create endpoint audit checklist; automated test that verifies all HTTP routes pass through guard |

---

## Deliverables Per Story

### RBAC-01 Deliverables

- `workspace_members` Prisma migration + seeder for existing users
- `WorkspaceRole` type + `WorkspaceAction` type in `@monorepo/shared`
- `PERMISSION_MATRIX` constant + `canDo()` pure function in `@monorepo/shared`
- `PermissionGuard` + `@RequirePermission()` decorator in api-gateway
- `role` field added to `JwtPayload` and embedded in `issueTokens()`
- `replied_by` field on Message (non-nullable for outbound, immutable after create)
- Admin protection service (`ensureAdminRemains`)
- First Admin seeding in `register()` flow
- Unit tests: all 27 `canDo()` combinations
- Integration tests: middleware on all 9 protected actions
- Integration tests: admin protection edge cases

### RBAC-02 Deliverables

- `role` added to `Invitation` model + `CreateInvitationDto`
- `acceptInvitation()` creates `WorkspaceMember` with role from invitation
- Resend invitation API (`PATCH /invitations/:id/resend`)
- Cancel invitation API (`DELETE /invitations/:id`)
- Change role API (`PATCH /workspace-members/:userId/role`)
- Remove member API (`DELETE /workspace-members/:userId`) + session revocation
- Email delivery integration (SES/SMTP) with invitation template
- Updated Members page UI: Role, Last Active, inline role change, Remove
- Updated Invitations page UI: Role column, Resend + Cancel actions
- Updated Invite form: role selector
- API tests: full invitation lifecycle (invite → accept → expire → resend)
- Session revocation tests: removed member → 401

### RBAC-03 Deliverables

- `role` in `CurrentUser` type and returned from `getMeAction()`
- Removed hardcoded `role: "admin"` from dashboard layout
- `usePermission(action)` hook
- Server-side route guards for all 6 protected routes
- Role-filtered sidebar navigation (3 role variants)
- Assign panel conditional rendering (SSR — no DOM trace for Agent)
- 403 error page integration (triggered by API 403 responses)
- Session expiry with return URL preservation
- Conversation assigned-to banner
- Unit tests: `usePermission` × all roles × all actions (27 combinations)
- E2E tests (Playwright): direct URL navigation to each restricted route per role
- Visual regression: sidebar rendering per role
