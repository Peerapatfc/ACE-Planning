# STORY-RBAC-01: Permission Model & API Enforcement — Plain English Explanation

## Overview

RBAC-01 builds the **permission enforcement layer** that every API endpoint must pass through before executing. The result is a "gate" that enforces which role can do what — and if you don't have permission, the system blocks you immediately before the handler even runs.

**Simple analogy:**
Think of it as a keycard system in an office building — every door checks your card before opening. Your card is your role (admin / supervisor / agent). No amount of asking nicely will open a door your card doesn't authorize.

> **Key principle:** Permission is always checked at the backend — frontend hiding menus is just UX, not real security.

---

## 1. ER Diagram — Database Tables (What data do we store?)

### 10 Tables in 3 Groups

#### Group A: Identity, Membership & Permissions (user-service DB)

| Table | What is it? | Status |
|---|---|---|
| **users** | People who log in — admins, supervisors, agents | Existing |
| **refresh_tokens** | Tokens for refreshing JWT sessions | Existing |
| **workspace_members** | Records which user belongs to which workspace and with what role | **New — RBAC-02** |
| **permissions** | Registry of all actions in the system, e.g. `assign_conversation` | **New — RBAC-01** |
| **role_permissions** | Matrix of which role can perform which action | **New — RBAC-01** |
| **frontend_route_permissions** | Maps route URLs to permissions — used by frontend route guard (RBAC-03) | **New — RBAC-01** |

#### Group B: Tenant Management (tenant-service DB)

| Table | What is it? | Status |
|---|---|---|
| **tenants** | Companies using the platform | Existing |
| **invitations** | Invitations for new members, now with `role` and `invited_by` fields | Modified — RBAC-02 |

#### Group C: Conversation Data (omnichat-service DB)

| Table | What is it? | Status |
|---|---|---|
| **conversations** | Chat rooms | Existing |
| **messages** | Messages, now with `replied_by` to record who sent each reply | Modified — RBAC-01 |

### Relationships — Read it like this

```
ABC Shop (tenant)
├── [user-service DB]
│   ├── User: Nid (users)
│   │   └── refresh_tokens (JWT session)
│   ├── workspace_members: Nid → role: admin       ← RBAC-01/02 checks here
│   ├── workspace_members: Oh  → role: supervisor
│   ├── workspace_members: Mac → role: agent
│   ├── permissions: assign_conversation, manage_members, ... (9 actions)
│   └── role_permissions: admin → assign ✅, agent → assign ❌, ...
│
├── [tenant-service DB]
│   └── tenants: ABC Shop, invitations
│
└── [omnichat-service DB]
    ├── Conversation #1 (customer chat)
    │   ├── Message: "I'm interested"      replied_by: null (customer message)
    │   └── Message: "Ready to ship!"      replied_by: Nid's user_id  ← RBAC-01 enforces NOT NULL
```

### Cross-Service References — Why some fields have no FK

```
user-service DB            tenant-service DB
───────────────            ─────────────────
workspace_members          tenants
  tenant_id ────────────▶  id
  (no DB FK)

user-service DB            omnichat-service DB
───────────────            ───────────────────
users                      messages
  id ───────────────────▶  replied_by
                           (no DB FK)
```

Because each service has its own separate database — PostgreSQL cannot enforce FK constraints across different databases. Application code validates the reference instead.

Note: `workspace_members.user_id` → `users.id` are both in user-service DB — a real DB FK applies here.

### Key points about workspace_members

- Lives in **user-service DB** (not omnichat-service or tenant-service)
- `user_id` → `users.id` — same DB, real FK
- `tenant_id` → `tenants.id` — cross-service reference, no DB FK
- Role is NOT stored in the JWT — **fetched from DB on every request** → a role change takes effect on the very next request, no logout required

---

## 2. Sequence Diagrams — Execution Order (What happens in what order?)

### Services Involved

```
                         ┌─────────────────┐
Client (Browser/App) ──▶ │ OmnichatService │  ←── Receives request, validates JWT
                         └───────┬─────────┘
                                 │ Checks permission before any work
                                 ▼
                         ┌─────────────────┐
                         │  Permission     │  ←── "Guard" — always runs first
                         │  Middleware     │
                         └───────┬─────────┘
                                 │ MessagePattern (never queries DB directly)
                                 ▼
                         ┌─────────────────┐
                         │  UserService    │  ←── Identity & auth hub
                         └───────┬─────────┘
                                 │
                         ┌───────┴──────────┐
                         ▼                  ▼
                    [user-service DB]    [omnichat-service DB]
                    workspace_members    conversations, messages
                    permissions
```

### 5 Flows

#### Flow 1: Normal Permission Check — Most important

**Scenario:** Mac (Agent) tries to assign a conversation, which requires Supervisor or above

```
Steps:

1. Mac sends POST /workspaces/:workspaceId/conversations/:id/assign
   → OmnichatService validates JWT → extracts Mac's userId

2. No token? → 401 Unauthorized immediately (permission check not even reached)

3. PermissionMiddleware receives (userId, tenantId, action="assign_conversation")
   → Sends MessagePattern to UserService:
     { cmd: 'get_workspace_member_role', payload: { userId, tenantId } }
   → UserService queries workspace_members → role = "agent"

4. No membership record? → 403 immediately (doesn't reveal whether the workspace exists)

5. canDo("agent", "assign_conversation") → false
   → 403 Forbidden:
     { "error": "permission_denied", "action": "assign_conversation", "required_role": "supervisor" }
   → Handler is never called ✓
```

> **Why does middleware use MessagePattern instead of querying DB directly?** Because omnichat-service and user-service have separate databases. Direct cross-database queries would violate the service boundary — MessagePattern keeps each service owning its own data.

#### Flow 2: Fail-Closed — Unknown action

**Scenario:** A request arrives with an action not present in the permission matrix

```
1. PermissionMiddleware receives action = "unknown_action"
2. Fetches role from UserService → role = "admin"
3. canDo("admin", "unknown_action") → action not in matrix → DENY
4. Returns 403 Forbidden

Note: No 500 thrown — designed to always "close first" when uncertain
```

> **Fail-Closed means:** When the system doesn't know whether to allow something — deny it by default. Better to block and investigate than to accidentally permit and fix later.

#### Flow 3: Admin Protection — Role Change

**Scenario:** Admin tries to downgrade their own role to Supervisor but is the only Admin left

```
1. PATCH /workspaces/:workspaceId/members/:memberId { role: "supervisor" }
   → PermissionMiddleware passes (caller has manage_members permission)

2. AdminProtectionService checks first:
   SELECT COUNT(*) FROM workspace_members WHERE tenant_id = ? AND role = 'admin'
   → adminCount = 1

3. Target is the last Admin → BLOCK
   → 400 Bad Request:
     { "error": "workspace_must_have_at_least_one_admin" }

If adminCount >= 2 → allow → UPDATE role proceeds normally
```

#### Flow 4: Admin Protection — Remove Member

**Scenario:** Admin A tries to remove Admin B, who is the last Admin

```
1. DELETE /workspaces/:workspaceId/members/:memberId
2. AdminProtectionService checks target's role → "admin"
3. Target is admin → count remaining admins
   → adminCount = 1 → BLOCK → 400

If target is not admin, or adminCount >= 2 → deletion proceeds
   → After removal: revoke all tokens for the removed user (via user-service)
```

> **Why revoke tokens too?** Without revocation, a removed member's JWT stays valid until natural expiry — they could continue using the platform even after being kicked out.

#### Flow 5: Reply — Recording who sent each message

**Scenario:** An Agent replies to a customer message

```
1. POST /workspaces/:workspaceId/conversations/:id/reply { content: "..." }
   → PermissionMiddleware passes (reply_any_conversation — all roles allowed)

2. MessageHandler:
   → Extracts userId from JWT (does NOT accept replied_by from client)
   → INSERT INTO messages (conversation_id, content, replied_by)
     VALUES (?, ?, userId)
   → replied_by is always NOT NULL ← DB constraint enforced

3. Returns 201 Created: { id, content, replied_by: userId, created_at }

If client tries to update replied_by later → 400 field is immutable
```

---

## 3. Permission Matrix — What each role can do

| Action | Admin | Supervisor | Agent | Endpoint |
|---|---|---|---|---|
| `reply_any_conversation` | ✅ | ✅ | ✅ | POST .../reply |
| `assign_conversation` | ✅ | ✅ | ❌ | POST .../assign |
| `change_conversation_status` | ✅ | ✅ | ✅ | PATCH .../status |
| `config_sla` | ✅ | ✅ | ❌ | PATCH .../sla |
| `config_notification` | ✅ | ✅ | ❌ | PATCH .../notifications |
| `view_team_report` | ✅ | ✅ | ❌ | GET .../reports/team |
| `manage_members` | ✅ | ❌ | ❌ | GET/PATCH/DELETE .../members |
| `manage_channels` | ✅ | ❌ | ❌ | POST/PATCH/DELETE .../channels |
| `manage_workspace` | ✅ | ❌ | ❌ | PATCH /workspaces/:id |

This matrix is stored in the DB (`role_permissions` table) — not hardcoded in source code.
It is loaded into memory at startup, and `canDo(role, action)` checks the in-memory copy instead of querying the DB on every request.

---

## 4. Error Response — Standard Format

```
401 Unauthorized  → No token, or token expired
                    { "error": "unauthorized" }

403 Forbidden     → Valid token, but insufficient role or not a workspace member
                    { "error": "permission_denied",
                      "action": "assign_conversation",
                      "required_role": "supervisor" }

400 Bad Request   → Admin protection — action would leave workspace with 0 admins
                    { "error": "workspace_must_have_at_least_one_admin" }
```

---

## Summary Numbers

| Category | Count |
|---|---|
| New / modified tables | 5 tables (workspace_members, invitations, permissions, role_permissions, frontend_route_permissions) |
| Sequence flows | 5 flows |
| Protected actions | 9 actions |
| Roles | 3 roles (admin, supervisor, agent) |
| Role × Action combinations | 27 combinations (all unit-tested) |

---

## End-to-End Example: Users attempting various actions

```
Setup:
  Nid  → role: Admin      in Workspace A
  Oh   → role: Supervisor in Workspace A
  Mac  → role: Agent      in Workspace A
  Nid  → role: Agent      in Workspace B  ← same person, different workspace, different role

────────────────────────────────────────────────────────────

Scenario 1: Mac (Agent) tries to assign a conversation in Workspace A
→ resolveRole(Mac, workspaceA) → "agent"
→ canDo("agent", "assign_conversation") → false
→ 403 Forbidden ✓

Scenario 2: Nid (Admin in A) tries to assign in Workspace B
→ resolveRole(Nid, workspaceB) → "agent"
→ canDo("agent", "assign_conversation") → false
→ 403 Forbidden ✓  ← permissions are workspace-scoped, never cross over

Scenario 3: Oh (Supervisor) replies to a customer
→ resolveRole(Oh, workspaceA) → "supervisor"
→ canDo("supervisor", "reply_any_conversation") → true
→ Handler runs → INSERT message (replied_by = Oh's userId) ✓

Scenario 4: Nid (only Admin) tries to downgrade their own role
→ Permission check passes (has manage_members)
→ AdminProtectionService: adminCount = 1 → BLOCK
→ 400 workspace_must_have_at_least_one_admin ✓

Scenario 5: Mac's JWT is still valid, but their role was just changed to Supervisor
→ resolveRole fetches from DB every time → immediately returns "supervisor"
→ New permissions apply on the very next request, no logout required ✓
```
