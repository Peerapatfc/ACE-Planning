# ACE-1611: RBAC-01 — API Documentation

Source: story `ACE-1611` scope only. Member management HTTP endpoints (list, invite, change role, remove) belong to **RBAC-02**.

This story delivers **infrastructure** — not feature endpoints. The API surface is:
1. Permission enforcement contract (how every protected endpoint behaves)
2. `GET /auth/me/permissions` — permission matrix query for authenticated user
3. User-service internal TCP patterns (new handlers added by this story)

---

## Guard Chain (applies to every HTTP endpoint)

```
Request
  └── ThrottlerGuard          rate limit
  └── JwtAuthGuard            verify JWT → 401 if invalid/expired/blocked
  └── PermissionGuard         resolveRole → canDo → 403 if denied
  └── Route Handler           executes only if all guards pass
```

**`@Public()`** — bypasses both JwtAuthGuard and PermissionGuard (e.g. login, register).  
**No `@RequirePermission()`** — PermissionGuard passes automatically; JWT still required.  
**`@RequirePermission('action')`** — PermissionGuard resolves role via TCP then checks matrix.

Role is **never cached in JWT** — resolved from DB on every request via `get_workspace_member_role` TCP call. Role changes take effect on the next request.

---

## GET /auth/me/permissions

Returns the permission actions the caller is allowed to perform in their current workspace.

**Auth:** Bearer JWT required  
**Permission:** none (JWT only)

**Response 200:**
```json
{
  "role": "supervisor",
  "allowed_actions": [
    "reply_any_conversation",
    "assign_conversation",
    "change_conversation_status",
    "config_sla",
    "config_notification",
    "config_notification_rules",
    "config_notification_preferences",
    "view_team_report"
  ]
}
```

`tenantId` is taken from the JWT — role resolved from DB, not from token claims.

---

## Error Response Contract

Every permission error returns a consistent shape regardless of endpoint.

### 401 Unauthorized

JWT missing, expired, or user is on the Redis blocklist.

```json
{
  "statusCode": 401,
  "message": "Unauthorized"
}
```

Must be returned **before** the permission check runs — JwtAuthGuard fires first.

---

### 403 Permission Denied

Returned by PermissionGuard in all of these cases:

| Cause | `action` present | `required_role` present |
|---|:---:|:---:|
| Caller lacks the required action | ✅ | ✅ |
| Caller has no membership in workspace | ❌ | ❌ |
| TCP call to user-service fails (fail-closed) | ❌ | ❌ |
| Action not found in permission matrix (unknown action) | ❌ | ❌ |

**With action context** (most common):
```json
{
  "error": "permission_denied",
  "action": "assign_conversation",
  "required_role": "admin | supervisor"
}
```

**Without action context** (no membership / TCP failure / unknown action):
```json
{
  "error": "permission_denied"
}
```

> **Fail-closed rule:** Unknown action names → 403, never 500.  
> **Non-member rule:** No membership record → 403, not 404 (workspace existence not revealed).

---

### 400 Admin Protection Violation

Returned by the shared admin protection service when a role change or member removal would leave the workspace with zero admins.

```json
{
  "error": "workspace_must_have_at_least_one_admin"
}
```

Called by RBAC-02 endpoints (change role, remove member) via the shared service defined in this story.

---

## Permission Matrix

Stored in `permissions` + `role_permissions` tables (user-service DB). Seeded at setup. Loaded into memory at API Gateway startup — no DB hit per request.

| Action | Admin | Supervisor | Agent |
|---|:---:|:---:|:---:|
| `reply_any_conversation` | ✅ | ✅ | ✅ |
| `assign_conversation` | ✅ | ✅ | ❌ |
| `change_conversation_status` | ✅ | ✅ | ✅ |
| `config_sla` | ✅ | ✅ | ❌ |
| `config_notification` | ✅ | ✅ | ❌ |
| `config_notification_rules` | ✅ | ✅ | ❌ |
| `config_notification_preferences` | ✅ | ✅ | ❌ |
| `view_team_report` | ✅ | ✅ | ❌ |
| `manage_members` | ✅ | ❌ | ❌ |
| `manage_channels` | ✅ | ❌ | ❌ |
| `manage_workspace` | ✅ | ❌ | ❌ |

Apply to any new endpoint: `@RequirePermission('action_name')` on the controller method.

---

## Internal TCP Message Patterns (user-service)

New handlers added by this story. Called from API Gateway via NestJS TCP transport — not HTTP.

### `get_workspace_member_role`

Called by PermissionGuard on every protected request to resolve the caller's role.

**Payload:**
```json
{ "user_id": "uuid", "tenant_id": "uuid" }
```

**Returns:** `"admin" | "supervisor" | "agent" | null`

Returns `null` when:
- No `WorkspaceMember` row found for `(tenant_id, user_id)`
- Member exists but `status = "removed"`

PermissionGuard treats `null` as → 403 Forbidden.

---

### `get_all_role_permissions`

Called by PermissionMatrixService at startup (and on manual reload) to build the in-memory matrix.

**Payload:** `{}`

**Returns:**
```json
[
  { "action": "assign_conversation", "role": "admin",      "allowed": true  },
  { "action": "assign_conversation", "role": "supervisor", "allowed": true  },
  { "action": "assign_conversation", "role": "agent",      "allowed": false }
]
```

Matrix is `Map<action, Set<role>>` — only entries where `allowed = true` are added.

---

## Reply Log — `replied_by` Field

This story adds `replied_by` (user UUID) to every outbound message record.

| Rule | Detail |
|---|---|
| Always populated | Never null on human-sent messages |
| Immutable | Any attempt to update `replied_by` after creation → 400 |
| Scope | Human-sent messages only (platform has no automated messages yet) |

HTTP behavior for update attempt:
```json
HTTP 400
{ "error": "replied_by_is_immutable" }
```

---

## How to Protect a New Endpoint

```typescript
@Controller('settings')
@ApiBearerAuth()
export class SettingsController {
  @Get('sla')
  @RequirePermission('config_sla')          // ← add this decorator
  async getSla(@CurrentUser() user: AuthUser) {
    // guard already verified role — safe to proceed
  }
}
```

The `action` string must match a key in the `permissions` table. Mismatch → fail-closed (403).
