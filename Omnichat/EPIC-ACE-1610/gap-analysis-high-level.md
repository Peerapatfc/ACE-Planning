# EPIC ACE-1610 RBAC — High-Level Gap Analysis

## Overall Status

| Story | Title | Status | Done |
|---|---|---|---|
| ACE-1611 (RBAC-01) | Permission Model & API Enforcement | Backlog | 0% |
| ACE-1612 (RBAC-02) | Member Management | Backlog | ~20% |
| ACE-1613 (RBAC-03) | Frontend Permission Enforcement | Backlog | 0% |

**Root cause:** The platform has no role system at the data, API, or UI layer. Every authenticated user is treated as a single omnipotent actor. The invitation scaffolding exists but is incomplete and has no role field.

---

## What Has Been Built

| Area | What Exists |
|---|---|
| Authentication | JWT login/register, refresh token, session cookies |
| Invitation basics | Token generation (32-byte hex), 7-day expiry, SHA-256 hash, accept flow |
| Members UI | Read-only table (name, email, joined date — no role, no actions) |
| Invitations UI | List page with invite form (no role selector, no Resend/Cancel) |
| Unauthorized page | Static `/unauthorized` page — not wired to any permission check |

---

## What Is Missing — Summary

### RBAC-01: Permission Model & API Enforcement

> **Nothing is implemented. This is the security foundation.**

- No `workspace_members` table — roles don't exist in any database
- No `role` in JWT — the token carries no authorization information
- No `canDo()` function — no permission abstraction exists
- No permission middleware — every API endpoint is wide open to any authenticated user
- No `replied_by` field on messages — no audit trail of who replied
- No admin protection — nothing prevents a workspace from losing its last admin

### RBAC-02: Member Management

> **Invitation scaffolding exists but is role-unaware and incomplete.**

- Invitation has no `role` field — you can invite someone but can't assign a role
- No Resend invitation (endpoint or UI)
- No Cancel invitation (endpoint or UI)
- No Remove member (endpoint or UI)
- No Change role (endpoint or UI)
- No session revocation when a member is removed
- No email delivery — invitations are created in the DB but no email is ever sent
- No admin protection rules enforced

### RBAC-03: Frontend Permission Enforcement

> **Nothing is implemented. Role is currently hardcoded as `"admin"` for all users.**

- `role: "admin"` is a hardcoded string in the layout — not from real user data
- No `usePermission` hook
- No role-based route guards — settings pages are accessible to anyone logged in
- No role-based sidebar filtering — all menu items shown to all users
- No 403 error handling — API errors cause blank screens or crashes
- No session expiry with return URL

---

## Priority & Effort

| Priority | What | Points |
|---|---|---|
| P0 | workspace_members table + role enum | 5 |
| P0 | Permission matrix + `canDo()` helper | 3 |
| P0 | Permission middleware on all protected endpoints | 5 |
| P0 | Admin protection service | 2 |
| P0 | Role embedded in JWT | 2 |
| P0 | `usePermission` hook + route guards (FE) | 8 |
| P1 | `replied_by` audit field on messages | 3 |
| P1 | Complete Member Management API (resend, cancel, change role, remove) | 8 |
| P1 | Email delivery integration | 5 |
| P1 | Complete Members UI (role, actions) + Sidebar filtering | 8 |
| P1 | 403 handling + session expiry + assign panel | 5 |
| **Total** | | **54 pts** |

---

## Dependencies & Blockers

```
RBAC-01 (Backend)  ──► RBAC-02 (Member Mgmt)  ──► RBAC-03 (Frontend)
     │                        │
     │                   Email domain must
     └── Role in JWT          be verified first
         required for
         RBAC-03 to start
```

| Blocker | Owner | Impact |
|---|---|---|
| Email domain not yet verified (noted in story) | Ops/Infra | RBAC-02 cannot go to production without it |
| `workspace_members` table doesn't exist | Backend | Blocks RBAC-01, RBAC-02, and RBAC-03 entirely |
| Role not in JWT | Backend | Blocks all frontend permission checks |

---

## Risk Snapshot

| Risk | Level |
|---|---|
| No access control exists today — all API endpoints are open | 🔴 Critical |
| Email domain not confirmed — invite emails can't be sent | 🔴 Critical |
| Session revocation on member remove requires new cross-service pattern | 🟡 Medium |
| Hardcoded `role: "admin"` in UI — any role-aware demo will appear wrong | 🟡 Medium |
| Flash of unauthorized content if FE guards are client-side only | 🟡 Medium |

---

## Recommended Approach

**Sprint 1 — Build the foundation (RBAC-01)**
Get the database, permission logic, and API enforcement in place. Nothing else in the RBAC epic can be built correctly without this.

**Sprint 2 — Member management + UI enforcement (RBAC-02 + RBAC-03 in parallel)**
Backend team completes invitation role support, resend/cancel, role change, and member removal. Frontend team implements `usePermission`, route guards, and sidebar filtering using the role now available in JWT.

**Gate before release:** Email domain must be verified and email delivery tested end-to-end before the feature ships to users.
