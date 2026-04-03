# EPIC ACE-1610: RBAC (Role-Based Access Control) — Plain English Explanation

## Overview

RBAC is the foundation that every feature on the platform relies on. Previously, the platform had only a single user with no role system — because there was only one tenant. As teams grow, the platform needs to control "who can do what" in order to:
- Prevent unauthorized access (e.g., Agents should not see full system config)
- Enable a clear audit trail — know who replied to which conversation, who changed what config
- Support multi-person teams where Admin, Supervisor, and Agent each have different responsibilities

**Simple analogy:**
Think of it like a company building's access card system — the security guard (Admin) has a master key, the floor manager (Supervisor) can enter most rooms, and the staff (Agent) can only enter their own work area.

---

## 3 Roles Supported at MVP

| Role | Who Is This? | What They Can Do |
|---|---|---|
| **Admin** | Owner / System Administrator | Configure everything, manage members, manage channels, see everything (auto-created when workspace is created) |
| **Supervisor** | CS Team Lead | View all inbox, assign/reassign conversations, configure SLA and notifications, view team reports |
| **Agent** | CS Staff | View all inbox, reply to any conversation, change conversation status |

> **Note:** The First Admin = the person who creates the workspace gets Admin role automatically. No invitation needed.

---

## Permission Matrix — Who Can Do What

| Permission | Admin | Supervisor | Agent |
|---|---|---|---|
| View all conversations | ✅ | ✅ | ✅ |
| Reply to any conversation | ✅ | ✅ | ✅ |
| Assign / Reassign conversation | ✅ | ✅ | ❌ |
| Change conversation status | ✅ | ✅ | ✅ |
| Configure SLA rules | ✅ | ✅ | ❌ |
| Configure notification rules | ✅ | ✅ | ❌ |
| Set personal notification preferences | ✅ | ✅ | ✅ |
| View team reports / analytics (later) | ✅ | ✅ | ❌ |
| Invite / Remove member | ✅ | ❌ | ❌ |
| Change member role | ✅ | ❌ | ❌ |
| Manage channels | ✅ | ❌ | ❌ |
| Access Settings > Workspace | ✅ | ❌ | ❌ |
| Access Settings > Channels | ✅ | ❌ | ❌ |
| Access Settings > SLA | ✅ | ✅ | ❌ |
| Access Settings > Notification Rules | ✅ | ✅ | ❌ |
| Access Settings > My Preferences | ✅ | ✅ | ✅ |

---

## 3 Stories — What Gets Built

### Story RBAC-01: Permission Model & API Enforcement (Backend)

**What is it?** Pure backend — no UI. Defines roles, permission rules, and enforces 403 Forbidden at the API layer. This is the foundation every other feature references.

**Key design decision — action-based, not role-based:**
Rather than checking `if role == "admin"` in each endpoint, the system uses a `canDo()` helper:

```
canDo(userId, workspaceId, action) → boolean

Examples:
  canDo(user1, ws1, "assign_conversation")  → true  (Supervisor)
  canDo(user2, ws1, "assign_conversation")  → false (Agent)
  canDo(user3, ws1, "manage_members")       → false (Supervisor)
```

Why action-based? Easier to extend in the future — add a new action in one place, not scattered across endpoints.

**9 Protected Actions:**

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

**Role is scoped per workspace:**
```
User is Admin in Workspace A, Agent in Workspace B
→ Calls manage_members with Workspace B context
→ Permission check evaluates Workspace B role (Agent)
→ Returns 403 — even though Admin in another workspace
```

**What happens when a request is unauthorized:**
```
Agent calls POST /conversations/:id/assign
→ Permission middleware runs BEFORE the handler
→ Agent does not have assign_conversation permission
→ Response: 403 Forbidden
  { "error": "permission_denied", "action": "assign_conversation", "required_role": "..." }
→ Handler function never executes
```

**Reply log — `replied_by` field:**
Every outbound message records who sent it. `replied_by = user_id` is always set, never null, and immutable after creation.

---

### Story RBAC-02: Member Management

**What is it?** The flow for inviting new members, changing roles, and removing members — Admin only.

**Invitation Flow:**
```
1. Admin goes to Settings > Members → clicks "Invite Member"
2. Enters email + selects role (Admin / Supervisor / Agent) → clicks Send
3. System sends invitation email from no-reply@domain (domain TBD)
   with a link containing a cryptographically random token (32-byte hex)
   valid for 7 days

4. Recipient clicks link:
   → If no account: register first, then join workspace
   → If existing account: login, then join workspace
   → Receives the assigned role immediately

5. If not accepted within 7 days:
   → Link expires (enforced at backend, not just UI)
   → Admin must click Resend → new link + new 7-day timer
```

**Page structure:**

```
Settings > Members
├── Active Members
│   └── Table: Name | Email | Role | Joined date | Last active | Actions
│       → Change role via inline dropdown (confirm dialog before applying)
│       → Remove button (confirm dialog with warning)
│
└── Pending Invitations
    └── Table: Email | Role | Sent date | Expires | Status | Actions (Resend / Cancel)
```

**Admin Protection Rules — prevents the workspace from becoming Admin-less:**

| Scenario | Decision |
|---|---|
| Admin downgrades own role | Allowed — only if at least 1 other active Admin exists |
| Admin downgrades another Admin | Allowed — only if at least 1 Admin remains after the change |
| Admin removes another Admin | Allowed — only if at least 1 Admin remains after the removal |
| Workspace has only 1 Admin left | That Admin cannot downgrade themselves or be removed |

**When a member is removed:**
- Session tokens revoked **immediately** — they cannot make any API calls
- Conversation history and messages are fully preserved
- Their name in reply logs shows as "former member (name)"

**When a role changes:**
- Session is NOT revoked — member stays logged in
- New permissions apply on their next API request (no re-login needed)

---

### Story RBAC-03: Frontend Permission Enforcement

**What is it?** The UI side — route guards, role-based visibility, and 403 handling. **Important:** frontend hiding is UX only — the backend 403 (RBAC-01) is the actual security.

**Route Permission Map:**

| Route | Admin | Supervisor | Agent |
|---|---|---|---|
| /inbox | ✅ | ✅ | ✅ |
| /settings/workspace/* | ✅ | ❌ | ❌ |
| /settings/channels | ✅ | ❌ | ❌ |
| /settings/sla | ✅ | ✅ | ❌ |
| /settings/notifications/rules | ✅ | ✅ | ❌ |
| /settings/notifications/preferences | ✅ | ✅ | ✅ |
| /settings/members | ✅ | ❌ | ❌ |

**`usePermission` hook — how components check permissions:**
```
usePermission("assign_conversation")  → true  (Supervisor or Admin)
usePermission("assign_conversation")  → false (Agent)

- Reads from cached session/app state (Redux, Zustand, Context)
- Zero extra API calls — derived locally from the auth token
- Updates when session refreshes after a role change
```

**3 enforcement layers:**

```
1. Route Guard (runs before any component renders)
   → Agent navigates to /settings/sla
   → Redirect to /inbox immediately — no page content ever shown
   → Toast: "คุณไม่มีสิทธิ์เข้าถึงหน้านี้"
   → Works on both initial load and mid-session navigation

2. UI Visibility (hidden, never greyed-out)
   → Settings sidebar shows only permitted sections:
      Admin     → all sections
      Supervisor → SLA + Notifications only
      Agent     → Notifications > My Preferences only
   → Assign panel: completely absent for Agent (not disabled, not greyed-out)

3. API Error Handling (graceful degradation)
   → Server returns 403 → show 403 page with "กลับหน้าหลัก" button
   → No crash, no blank page
   → 403 page does not expose which resource was being accessed
```

**Reply behavior — all roles can reply:**
```
Agent opens a conversation assigned to someone else
→ Reply input is fully enabled and functional
→ "assigned to [name]" banner shown for clarity
→ Agent sends reply → replied_by = this Agent's user_id (recorded by backend)
```

**No flash of unauthorized content:**
Restricted elements are never shown even momentarily before being hidden. Layout must not shift from elements appearing then disappearing. This is considered a bug if it happens.

**Session expiry mid-session:**
```
Session token expires while user is active
→ Redirect to login page
→ Current URL saved for return after re-login
→ Message: "กรุณา login ใหม่ session หมดอายุแล้ว"
```

---

## How the 3 Stories Connect

```
RBAC-01 (Backend — the actual security)
  → Defines action list and permission rules
  → Enforces 403 before any handler executes
  → Records replied_by on every message

RBAC-02 (Member Management)
  → Uses RBAC-01's Admin protection logic
  → Invitation flow + role/remove management
  → Revokes sessions on member removal

RBAC-03 (Frontend — UX layer)
  → Reads role from session token
  → Route guards block unauthorized pages
  → usePermission hook hides irrelevant UI elements
  → Handles 403 responses gracefully
  → Backend 403 (RBAC-01) is the real enforcement
```

---

## Summary Numbers

| Category | Count |
|---|---|
| Roles | 3 (Admin, Supervisor, Agent) |
| Stories | 3 (RBAC-01, RBAC-02, RBAC-03) |
| Protected actions | 9 actions |
| Protected routes (frontend) | 7 routes |
| Invitation expiry | 7 days |

---

## End-to-End Example: New team member joins and starts working

```
1. Admin opens Settings > Members → "Invite Member"
   → Email: agent@company.com, Role: Agent
   → System sends email from no-reply@domain
   → Pending invitation appears with 7-day expiry timer

2. Agent clicks the link within 7 days
   → Registers or logs in → joins workspace as Agent

3. Agent opens Inbox
   → Sees all conversations ✅
   → Reply input is enabled on every conversation ✅
   → Assign panel is completely absent ❌ (hidden by RBAC-03)
   → Menu does not show Settings > Channels, Settings > Members ❌

4. Agent manually types /settings/channels in the browser
   → Route guard runs before any render
   → Redirect to /inbox + toast "คุณไม่มีสิทธิ์เข้าถึงหน้านี้"

5. Agent opens a conversation assigned to another Agent
   → Sees "assigned to Agent Nid" banner
   → Reply input still fully functional — Agent can reply

6. Admin later removes Agent from workspace
   → All Agent's sessions revoked immediately
   → Agent's next API call returns 401 Unauthorized
   → Conversation history preserved; reply logs show "former member (Agent name)"

7. Admin tries to remove themselves when they are the last Admin
   → API returns 400: "ต้องมี Admin อย่างน้อย 1 คนใน workspace"
   → Action blocked at both frontend (disabled button) and backend (400 error)
```
