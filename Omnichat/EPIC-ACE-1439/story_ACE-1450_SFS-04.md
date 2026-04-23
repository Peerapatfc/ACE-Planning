# STORY-SFS-04: User Saved Views

| Field | Value |
|-------|-------|
| **ClickUp ID** | ACE-1450 |
| **Task ID** | 86d2cxp5u |
| **Type** | User Story Card |
| **Status** | In Progress |
| **Story Points** | 5 SP |
| **Parent Epic** | EPIC-A2.4: Search/Filter/Sort/Saved Views (ACE-1439) |
| **ACE Product** | Omni |
| **Project** | ACE |
| **Sprint** | Sprint 3 (3/24 - 4/7) |
| **List** | Omni › Ready to Sprint |
| **Created by** | Thanyapong |
| **Assignees** | Peerapat Pongnipakorn |
| **Priority** | — |
| **ClickUp URL** | https://app.clickup.com/t/86d2cxp5u |

---

## User Story

> As a **Support Agent**,
> I want to **save my current inbox view as a named preset and access it as quick filter pills**
> so that I can **switch between common working modes in one click**.

---

## Description

คุณเลือก "user saved view" ดังนั้นเราจะทำ views แบบ per-user

Saved view คือชุดของ:
- filters (structured)
- sort mode
- optional include search query (ให้เป็น option toggle เพื่อความยืดหยุ่น)

แล้วแสดงเป็น pills บน UI เพื่อกดสลับเร็ว
ต้องมี set default view และ reset behavior ชัดเจน

Saved views are **per-user** presets. Each saved view stores:
- Filters (structured)
- Sort mode
- Optional: search query text (configurable via toggle)

Views are displayed as pills above the conversation list for quick switching. Applying a saved view **replaces** the current state (no merge).

### Scope

- Built-in system pills (hardcoded — ไม่สามารถ edit หรือ delete ได้)
- Create saved view from current state (capture-first flow)
- Rename / delete saved view
- Set default view for user
- Applying a saved view REPLACES current state (ไม่ merge)
- Reset all → System Default View
- Max **20 saved views** per user

**Out of scope:** shared team views (R2), pill reorder / drag-and-drop (R2)

---

## Acceptance Criteria

### AC-1: Create saved view from current filters and sort
- **Given** the agent has selected filters and sort mode on the inbox
- **When** the agent clicks Save view and enters a name
- **Then** the system creates a saved view for that user and it appears as a pill immediately

### AC-2: Optional include search query in saved view
- **Given** the agent has a search query in the search bar
- **When** saving a view with `include_query` enabled
- **Then** the view stores the query text and applying the view restores that query as well
- **And** when `include_query` is disabled the view saves only filters and sort

> _Phase 1: query is stored as text — known to break if tag is renamed. Document for users._

### AC-3: Applying saved view replaces current state
- **Given** the agent has an active search query "refund" and applies a saved view with saved query "สลิป"
- **When** the view pill is clicked
- **Then** the current query is replaced by "สลิป", current filters are replaced by the view's filters, and the search bar updates to show the new query

### AC-4: Apply saved view updates list instantly
- **Given** multiple saved views exist
- **When** the agent clicks a view pill
- **Then** filters, sort, and optional query are applied and the list refreshes to match that view

### AC-5: Set default view persists and auto-applies on entry
- **Given** the agent selects Set as default on a saved view
- **When** they reopen inbox later
- **Then** the default view is applied automatically on page load

### AC-6: Rename and delete saved view
- **Given** a saved view exists
- **When** the agent renames or deletes it
- **Then** the UI updates accordingly and deleting the default view reverts to System Default View (section 1.1a)

### AC-7: Max 20 saved views per user
- **Given** a user already has 20 saved views
- **When** the agent attempts to create a 21st saved view
- **Then** the system shows an error: "คุณมี saved views ครบ 20 อัน กรุณาลบก่อนสร้างใหม่" and does not create the view

### AC-8: Reset all returns to System Default View
- **Given** a saved view is active and the agent has changed filters manually
- **When** the agent clicks Reset all
- **Then** the system clears all changes and returns to System Default View (section 1.1a), not to the active saved view

### AC-9: Built-in system pills always visible and non-editable
- **Given** any user opens inbox
- **When** the pill row renders
- **Then** built-in system pills (My Open, Unassigned, etc.) are always shown first before user saved views
- **And** built-in pills cannot be deleted or renamed

### AC-10: Tenant isolation and user scoping
- **Given** multiple users exist in the same tenant
- **When** user A saves views
- **Then** user B cannot see user A's views (unless shared views are enabled — out of scope)

### AC-11: Duplicate saved view name not allowed
- **Given** a saved view with the same name already exists
- **When** the agent attempts to create a new view with that name
- **Then** the system shows a warning that the name is duplicate and does not save the view

---

## UI/UX Notes

- Pills row above conversation list: `[Built-in pills] [User saved view pills] [+ Save view]`
- Manage views modal with list, rename, delete, set default
- **Clear search** (removes query only) is separate from **Reset all** (removes everything)
- Show warning in save modal if query text contains tag names

---

## Subtasks

| ID | Title | Status |
|----|-------|--------|
| [ACE-1552](https://app.clickup.com/t/86d2g1yhh) | User Saved Views Model , Service | To Do |
| [ACE-1553](https://app.clickup.com/t/86d2g1z3w) | API : Create,Get,Delete | To Do |
| [ACE-1554](https://app.clickup.com/t/86d2g20kr) | FE : Apply Saved Views Components | To Do |
| [ACE-1555](https://app.clickup.com/t/86d2g20v7) | FE : Create Saved Views Components | To Do |
| [ACE-1556](https://app.clickup.com/t/86d2g21wj) | FE : Modal alert create views more than 20 | To Do |

---

_Exported from ClickUp on 2026-04-07. Source: https://app.clickup.com/t/86d2cxp5u_
