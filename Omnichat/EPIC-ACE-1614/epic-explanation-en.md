# EPIC ACE-1614: Settings & Configuration — Plain English Explanation

## Overview

Settings is the area that holds all one-time workspace configuration. Once set, these configs affect the entire workspace — business identity, working hours, and team member management.

The epic has a clear **dependency chain**:

```
SET-01 (Shell & Navigation)
  └── SET-02 (Business Information & Business Hours)
        └── SET-03 (Members & Roles + Work Shift)
```

SET-03 depends on SET-02 because the "Same as business hours" toggle in each user's work shift reads directly from SET-02's data.

---

## Settings Sections — Who Can Access What

| Settings Section | Admin | Supervisor | Agent |
|---|---|---|---|
| Business Information | ✅ | ❌ | ❌ |
| Members & Roles | ✅ | ❌ | ❌ |
| Channels (existing) | ✅ | ❌ | ❌ |
| SLA Rules (via SLA-01) | ✅ | ✅ | ❌ |
| Notification Rules (via NOTIF-04) | ✅ | ✅ | ❌ |
| My Preferences (via NOTIF-05) | ✅ | ✅ | ✅ |

> Sections the user cannot access are **completely absent from the UI** — not greyed out, not in the DOM at all.

---

## 3 Stories — What Gets Built

### Story SET-01: Settings Shell & Sidebar Navigation

**What is it?** Pure frontend — builds the layout and navigation shell for the entire Settings area. No content yet — just the shell, routing, and access-controlled sidebar. Content for each section is built in subsequent stories.

**Layout:**
```
┌─────────────────────────────────────────────────┐
│  Top Navigation                                  │
├─────────────┬───────────────────────────────────┤
│             │  Settings > Business Information   │  ← Breadcrumb
│  Sidebar    │                                    │
│  ─────────  │  [Content Area]                    │
│  Business   │  (placeholder, filled by SET-02,   │
│  Information│   SET-03, SLA-01, NOTIF-04/05)     │
│  Members    │                                    │
│  Channels   │                                    │
│  SLA Rules  │                                    │
│  Notif. ▸   │                                    │
│  My Prefs   │                                    │
└─────────────┴───────────────────────────────────┘
```

**Sidebar behavior per role:**
```
Admin     → sees all 6 sections
Supervisor → sees only: SLA Rules, Notification Rules, My Preferences
Agent     → sees only: My Preferences
```

**Auto-redirect:** When any user navigates to `/settings` directly, the system redirects to their first accessible section automatically — no blank screen.

**Route guard:** Direct URL access to a section the user can't access → redirect to 403. Restricted sections are **never in the DOM** — not even hidden with CSS.

**Active section:** Visual highlight in sidebar (left border indicator + background) + breadcrumb "Settings > [Section name]" at the top of the content area.

---

### Story SET-02: Business Information & Business Hours

**What is it?** Admin-only page with two sections: workspace identity and working hours schedule.

**Section 1 — Business Information:**

| Field | Editable? | Notes |
|---|---|---|
| Company Logo | ✅ | JPG/PNG, max 2MB, preview immediately |
| Organization Name | ✅ | Required — cannot save if empty |
| Email | ✅ | Contact email of workspace (not login email) |
| Phone Number | ✅ | |
| Store ID | ❌ | Read-only + copy to clipboard. Generated at workspace creation, **never regenerated** |
| Timezone | ❌ | Read from workspace config, display only |

**Section 2 — Business Hours:**

Each day of the week (Sunday–Saturday) has its own row:

```
[ ] Sunday     [OFF]
[✓] Monday     09:00 ▾  to  18:00 ▾   [+]  [Copy times to all]
[✓] Tuesday    09:00 ▾  to  18:00 ▾   [+]
[✓] Wednesday  09:00 ▾  to  18:00 ▾   [+]
...
```

- **Toggle per day:** Turn a day on/off — time inputs appear/hide accordingly
- **Time dropdown:** 30-minute intervals from 00:00 to 23:30
- **Add shift (+):** Add a second time range for split shifts (e.g., 09:00–12:00 and 13:00–18:00)
- **Remove shift (−):** Remove the extra shift row
- **"Copy times to all":** Takes the current day's time range and applies it to all toggled-on days

**Data format stored:**
```json
{ "day": "monday", "enabled": true, "shifts": [{ "start": "09:00", "end": "18:00" }] }
```

**Why Business Hours matters downstream:**
- SET-03 "Same as business hours" toggle reads this data
- Future: SLA timer pauses outside business hours

---

### Story SET-03: Members & Roles Page + Edit User + Work Shift

**What is it?** The complete member management page, combining RBAC-02's invite/role/remove APIs with an Edit User modal that also configures individual work shifts.

**Member List columns:**

| Column | Notes |
|---|---|
| Name + Avatar | Full name with profile picture |
| Email | Display only |
| Role | Badge (Admin / Supervisor / Agent) — read-only in list, changeable via Edit modal |
| Work Shift | Summary: "Same as BH" or "Mon–Fri 09:00–18:00" or "Not set" |
| Last Active | Relative time, e.g., "2h ago" |
| Actions | Edit button → opens Edit modal |

**Edit User Modal — 2 sections:**

```
┌─────────────────────────────────────┐
│  Edit User                          │
├─────────────────────────────────────┤
│  User Information                   │
│  Full Name:  [John Smith      ]     │
│  Email:      john@company.com 🔒    │  ← read-only, cannot be changed
│  Role:       [Supervisor    ▾]      │
├─────────────────────────────────────┤
│  User's Work Shift                  │
│  [✓] Same as business hours         │
│      Preview: Mon–Fri 09:00–18:00   │
│                                     │
│  (or if toggled off:)               │
│  [Mon] 09:00 → 18:00  [+]           │
│  [Tue] 09:00 → 18:00  [+]           │
│  ...                                │
├─────────────────────────────────────┤
│                           [Save]    │
│  [Remove member]                    │  ← at bottom, visually separated
└─────────────────────────────────────┘
```

**"Same as business hours" toggle — important design:**
```
Toggle ON  → stores flag: same_as_business_hours = true
             Does NOT copy the current hours as a snapshot
             → If Admin updates business hours in SET-02 later,
               this user's effective schedule updates automatically

Toggle OFF → stores custom shifts independently
             → Business hours changes do NOT affect this user
```

**Pending Invitations section** (reuses RBAC-02 data):
- Shows: Email, Role, Sent date, Expiry status, Resend / Cancel buttons
- Expired invitations are visually distinct from active pending ones

**Remove member from Edit modal:**
- Click Remove → confirm dialog (warns about access revocation)
- Confirm → member removed, all sessions revoked immediately, disappears from list
- Cancel → modal stays open, nothing changes

**`team_id` schema note:**
`workspace_members` table gets a `team_id` column (nullable, defaults to null) starting from this story. Not shown in UI in MVP — schema-only preparation for Teams in Release 2.

**`user_work_shifts` table:**
```
user_id, workspace_id, same_as_business_hours (boolean), shifts (JSON array), created_at, updated_at
```

---

## How the 3 Stories Connect

```
SET-01 (Shell)
  → Builds the Settings layout and filtered sidebar
  → Route guards blocking unauthorized sections
  → Auto-redirect to first accessible section
  → All other Settings stories live inside this shell

SET-02 (Business Information & Hours)
  → Admin sets workspace identity and working hours
  → Business hours data is the source of truth for:
      - SET-03 "Same as business hours" toggle
      - Future: SLA timer pause logic

SET-03 (Members & Roles + Work Shift)
  → Full member management page inside the SET-01 shell
  → Calls RBAC-02 APIs for invite, role change, remove
  → Reads SET-02 business hours for work shift toggle
  → Edit User modal covers both profile info and schedule
```

---

## Summary Numbers

| Category | Count |
|---|---|
| Stories | 3 (SET-01, SET-02, SET-03) |
| Settings sections total | 6 sections |
| Sections only Admin can access | 3 (Business Info, Members, Channels) |
| Sections Admin + Supervisor can access | 2 (SLA, Notification Rules) |
| Sections all roles can access | 1 (My Preferences) |

---

## End-to-End Example: Admin sets up workspace for a new team

```
1. Admin clicks Settings icon
   → SET-01 shell loads → sidebar shows all 6 sections
   → Auto-selects "Business Information" (first accessible section)

2. Admin fills in Business Information
   → Uploads company logo (JPG, 1.2MB → preview shown)
   → Sets Organization Name: "ABC Shop"
   → Sets Email: info@abcshop.com
   → Store ID: auto-generated, read-only (Admin copies it for integrations)
   → Clicks Save → toast "บันทึกข้อมูลเรียบร้อยแล้ว"

3. Admin sets Business Hours
   → Toggles Mon–Fri ON, sets 09:00–18:00
   → Clicks "Copy times to all" on Monday → Tue–Fri updated instantly
   → Adds second shift on Monday: 09:00–12:00 and 13:00–18:00 (lunch break)
   → Sat–Sun stays OFF
   → Clicks Save

4. Admin invites team members (via RBAC-02 invite button on Members page)
   → Agent Nid accepts invite → appears in member list

5. Admin clicks Edit on Agent Nid
   → Edit modal opens
   → Sets "Same as business hours" ON
     → Agent Nid's work shift auto-follows workspace hours
   → Clicks Save → Work Shift column shows "Same as BH"

6. Later, Admin updates Business Hours (adds Saturday morning)
   → Agent Nid's effective schedule automatically includes Saturday
   → No need to edit each user separately

7. Supervisor logs in and clicks Settings
   → Sidebar shows only: SLA Rules, Notification Rules, My Preferences
   → Business Information, Members & Roles, Channels are absent from UI

8. Supervisor tries to type /settings/members in the URL bar
   → Route guard intercepts → redirect to 403
   → "You don't have permission to access this page"
```
