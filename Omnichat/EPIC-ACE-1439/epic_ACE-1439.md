# EPIC-A2.4: Search / Filter / Sort / Saved Views

| Field | Value |
|-------|-------|
| **ClickUp ID** | ACE-1439 |
| **Task ID** | 86d2cxk7y |
| **Type** | Epic |
| **Status** | To Do |
| **ACE Product** | Omni |
| **Project** | ACE |
| **List** | Omni › Ready to Sprint |
| **Parent Epic** | OMNI-MS-A2: Unified Inbox (ACE-1097) |
| **Created by** | Thanyapong |
| **Assignees** | — |
| **Priority** | — |
| **Story Points** | — (see child stories) |
| **ClickUp URL** | https://app.clickup.com/t/86d2cxk7y |

---

## Epic Summary

This epic covers the **Search, Filter, Sort, and Saved Views** capabilities for the Omnichat Unified Inbox (Phase 1 / MVP). It defines the semantics and UX for three distinct inbox-interaction modes:

- **Search** — free-text keyword search across conversations and messages
- **Filter** — structured constraint-based narrowing (channel, status, assignee, overdue)
- **Sort** — ordering of results after filtering

These three modes compose with **AND semantics** (commutative), and the epic also establishes **Saved Views** (per-user named presets) and the **System Default View** as a single source of truth for the ground-zero state.

---

## 1. Epic Description

### 1.1 Concepts & Definitions

| Term | Definition | Example |
|------|-----------|---------|
| **Search** | Free-text / keyword query — finds items matching text | `refund`, `ORD-8823`, `VIP`, `@handle` |
| **Filter** | Structured constraints — selects a subset matching criteria | `channel=LINE`, `status=open`, `assignee=me` |
| **Sort** | Ordering of the result set | `sort by last_message_at DESC`, `oldest waiting` |

### 1.1a System Default View (Single Source of Truth)

| Dimension | Default Value |
|-----------|--------------|
| Sort | Latest activity (`last_message_at DESC`) |
| Status filter | All: open, in progress, pending, completed |
| Channel filter | All channels |
| Assignee filter | All agents |
| Search query | Empty |

### 1.2 Search — What Can Be Searched (Phase 1 MVP)

**A) Common fields (all channels)**
- Contact display name
- Contact identifiers (masked — searchable by actual value)
- Message text (keyword in message)
- Tags on conversation (text match — e.g. type "VIP" → finds conversations tagged "VIP")
- Conversation ID (internal, for support team)
- Order ID typed by customer in messages (free text match)

**B) Per-channel identifiers**

| Channel | Searchable Identifiers | Notes |
|---------|----------------------|-------|
| LINE | LINE User ID (`external_user_id`), display name | |
| Facebook | PSID, display name / page name | |
| Instagram | IG User ID, username (@handle) | |
| Shopee | Buyer ID, Shop Buyer ID, Shopee Order ID | Order ID most important |
| Lazada | Buyer ID, Lazada Order ID | |
| TikTok | TikTok User ID, display name, TikTok Order ID | |
| Shopify | Customer name, Shopify Order #1234, email (partial/masked) | Email masked, partial search OK |

**C) NOT searched in Phase 1**
- Product name / SKU
- System event text (imported, external_native)
- Phone number
- Tag filter dropdown (tag management UI required first)

> **Known limitation:** Saved views that store a tag-name query (e.g. "VIP") will break if the tag is renamed. Fix via `tag_id` filter in R2.

### 1.3 Search + Filter Combined

- Result set = **Search AND Filter** (always commutative)
- Applying filter first then searching → search queries the already-filtered set
- Applying search first then filtering → filter narrows the search results
- Outcome is identical either way

### 1.4 Filter Fields (MVP)

| Filter | Type | Values |
|--------|------|--------|
| Channel | Multi-select | LINE, Facebook, Instagram, Shopee, Lazada, TikTok, Shopify |
| Status | Multi-select | open, in progress, pending, completed |
| Assignment | Single-select | mine, unassigned, all, specific agent name |
| SLA / Overdue | Toggle | overdue only (hidden when SLA feature is off) |

### 1.5 Quick Filter Pills (System Built-ins)

| Pill | Filter Criteria | Notes |
|------|----------------|-------|
| All | (no filter) | = System Default View |
| My Open | `assignee=me AND status=open` | open only, not in progress |
| Unassigned | `assignee=none AND status=open` | |
| In Progress | `status=in_progress` | active conversations |
| Pending | `status=pending` | waiting for customer response |
| Overdue | `overdue=true` | shown only when SLA is enabled |

**Pill behavior:**
- Tap pill → apply preset (filters + sort)
- Tap same pill again → reset to System Default View
- **Reset all** button → clears all filters + search + sort → returns to System Default View (1.1a)

**Saved View preset stores:**
- Selected filters + sort mode + optional query text + name
- Max **20 saved views** per user

---

## 2. Child User Stories

| # | ID | Name | Story Points | Status | ClickUp URL |
|---|----|------|-------------|--------|-------------|
| 1 | **ACE-1440** | STORY-SFS-01: Unified Search with Results | 13 SP | To Do | https://app.clickup.com/t/86d2cxnk4 |
| 2 | **ACE-1441** | STORY-SFS-02: Filter System | 6 SP | To Do | https://app.clickup.com/t/86d2cxntq |
| 3 | **ACE-1442** | STORY-SFS-03: Sort Options | 5 SP | To Do | https://app.clickup.com/t/86d2cxp0v |
| 4 | **ACE-1450** | STORY-SFS-04: User Saved Views | 5 SP | To Do | https://app.clickup.com/t/86d2cxp5u |
| 5 | **ACE-1443** | STORY-SFS-05: Combined Query Semantics and State Management | 4 SP | To Do | https://app.clickup.com/t/86d2cxpj6 |

**Total Story Points: 33 SP**

---

## 3. User Story Details

---

### ACE-1440 · STORY-SFS-01: Unified Search with Results

> **13 Story Points** | To Do | https://app.clickup.com/t/86d2cxnk4

**User Story**
> As a Support Agent, I want to search across conversations and messages using a single search bar so that I can quickly find customers and specific message content without manual scrolling.

**Description**
User types a single query, the system searches all fields simultaneously and displays results in 2 grouped sections:
- **CONVERSATIONS (N)** — match from contact name, identifier, order ID, tag text
- **MESSAGES (N)** — match from message text

**Scope**
- Search bar on inbox list — debounce 300ms, min 2 chars
- Grouped sections: CONVERSATIONS + MESSAGES in one view; sections with no results are hidden
- Click conversation result → open conversation
- Click message result → open conversation + scroll/highlight to matched message
- Active filters remain applied during search (AND semantics)
- X on search bar = Clear search (clears query only; filters remain)
- **Out of scope:** advanced ranking, semantic search, tag filter dropdown, phone/SKU search

**Acceptance Criteria**

1. **Empty state and error state**
   - Given no results match or the search API fails → shows clear empty state or retry action; does not lose previous inbox view state

2. **Search returns grouped results in a single view**
   - Given query ≥ 2 chars → CONVERSATIONS and MESSAGES sections displayed in single scrollable view (no tab switching); sections with no results are hidden

3. **Conversations section returns matching results**
   - Given query matches contact name, identifier, order ID, or tag text → Conversations section shows up to 5 matches with name, channel badge, status badge, `last_message_at`; "ดูทั้งหมด (N)" button appears when total > 5

4. **Messages section returns matching message snippets**
   - Given keyword exists in message text → Messages section shows up to 5 results with highlighted snippet, conversation name, channel badge, timestamp; "ดูทั้งหมด (N)" when total > 5

5. **Tag search works via text match**
   - Given tag "VIP" exists → typing "VIP" shows that conversation in Conversations section with tag badge
   - _Known limitation: Phase 1 text match only — results change if tag is renamed/deleted. Fix via `tag_id` filter in R2_

6. **Per-channel identifier search returns correct conversations**
   - Given Shopee Order ID, LINE User ID, or Shopify Order #1234 is typed → matching conversation from that channel appears in Conversations section

7. **Click message result navigates and highlights matched message**
   - Given message result clicked → timeline scrolls to and highlights matched message
   - If message not found within 3 pages of pagination → banner "ข้อความอาจอยู่เกินหน้าที่โหลด" shown; timeline scrolls to top

8. **Minimum query length enforced**
   - Given < 2 chars typed → no search request triggered; inbox list unchanged

9. **Active filters apply to search results**
   - Given `channel=LINE` filter active and query "refund" → results show only LINE conversations/messages; filter chips remain visible

10. **All statuses included in results with status badge**
    - Given search performed → completed conversations included alongside open/in progress/pending; each result shows status badge; agent can filter out completed via status filter

11. **Search respects tenant isolation and permission scope**
    - Results include only the current tenant's data and only conversations the agent is permitted to view

12. **Debounce and performance**
    - Search triggered after 300ms pause; UI shows loading state; inbox does not freeze
    - API p95 response time < 500ms for 1M+ messages per tenant

**UI/UX Notes**
- Section headers: "CONVERSATIONS (N)" and "MESSAGES (N)" in uppercase muted text
- Keyword highlighted in both conversation preview and message snippet
- "ดูทั้งหมด (N)" button when section has > 5 results
- X on search bar = Clear search only (does not clear filters)
- Empty sections hidden; if only Conversations section has results, only that is shown
- Status badge displayed on every result card

---

### ACE-1441 · STORY-SFS-02: Filter System

> **6 Story Points** | To Do | https://app.clickup.com/t/86d2cxntq

**User Story**
> As a Support Agent, I want structured filters that work together with search so that I can narrow down the inbox and search results to the exact subset I need.

**Description**
Filters are structured condition-based narrowing that must work together with search via AND semantics. Filter state must clearly display what is active and be resettable in one click.

**Scope**
- Filter panel / filter bar
- MVP filter fields: `channel_type` (multi-select), `status` (4 states), `assignee`, `overdue`
- Filters apply to both Inbox list and Search grouped results
- Active filter chips with X remove per chip
- Reset all → System Default View
- Filter state persists via URL query params
- **Out of scope:** `has_attachment` filter, tag filter dropdown, source label filter, advanced multi-condition builder

**Acceptance Criteria**

1. **Filters apply as AND with search**
   - Results match search query AND all selected filters

2. **Channel filter is multi-select**
   - Selecting LINE + Shopee → shows LINE or Shopee conversations (OR within channel values, AND with other filters)
   - Active filter chips show each selected channel with X to remove

3. **Status filter supports all 4 states in multi-select**
   - Selecting `open` and `in_progress` → shows only those states
   - No status selected → default shows all 4 states

4. **Assignment filter works correctly**
   - `status=open AND assignee=mine` → only open conversations assigned to current agent

5. **Overdue filter is hidden when SLA is disabled**
   - SLA disabled → Overdue filter is hidden entirely (not merely disabled)
   - SLA enabled + overdue filter active → only overdue conversations shown

6. **Reset all clears filters and restores System Default View**
   - Clicking Reset all → all filters cleared, search query cleared, list returns to System Default View (1.1a)

7. **Filter state persists via URL params across page refresh**
   - Active filters (e.g. `channel=LINE,Facebook&status=open,in_progress`) survive page refresh and are restorable from URL
   - _(Tech improvement — implement when there is a real use case)_

8. **Filters must never leak data cross-tenant**
   - Any filter combination still returns only current tenant data

**UI/UX Notes**
- Filter bar with dropdowns above conversation list
- Active filters as chips with X remove per filter
- Channel filter: multi-select dropdown with checkboxes
- Status filter: multi-select dropdown (open, in progress, pending, completed)
- Overdue filter: hidden entirely when SLA disabled
- Reset all: one-click
- Red badge count on each filter section showing number of active selections
- Show agent names in assignee filter

---

### ACE-1442 · STORY-SFS-03: Sort Options

> **5 Story Points** | To Do | https://app.clickup.com/t/86d2cxp0v

**User Story**
> As a Support Agent, I want to sort the inbox list by different strategies so that I can prioritize work efficiently depending on the situation.

**Description**
Sort orders the conversation list after filters and search have been applied. MVP has 3 non-overlapping sort modes:

| Mode | Use Case |
|------|---------|
| Latest activity _(default)_ | General monitoring — see most recently active conversations |
| Oldest waiting | Triage — find conversations waiting longest without a reply; prevent SLA miss |
| SLA due soonest | Focus on conversations closest to reply deadline |

**Scope**
- Sort dropdown with 3 modes on inbox list
- Sort applies to Conversation list only (Messages section in search uses relevance ordering)
- UI indicator for active sort
- **Out of scope:** custom sort per agent, priority scoring

**Acceptance Criteria**

1. **Default sort is latest activity**
   - Inbox opens → conversations sorted by `last_message_at DESC`

2. **Sort by oldest waiting shows unanswered conversations first**
   - Sorted by `last_inbound_at ASC` (longest waiting at top)
   - Conversations where last message was outbound (already answered) do not dominate the top
   - `NULL last_inbound_at` → NULLS LAST

3. **Sort by SLA due soonest works when SLA is enabled**
   - Sorted by `sla_due_at ASC`; `NULL sla_due_at` → NULLS LAST

4. **Sort applies to Conversation list only**
   - Changing sort mode only reorders Conversations section; Messages section always uses relevance ordering

5. **Sorting works together with filters and search**
   - Changing sort mode reorders the same filtered/searched set without losing filters or query

6. **Pagination remains stable per sort mode**
   - Loading more pages continues the same sort order without duplicates or skips

7. **New inbound during pagination does not reorder current view**
   - New message arrival does not cause conversation to jump position in current loaded view
   - "New conversations available" indicator may appear to prompt manual refresh

8. **Sort state persists during navigation**
   - Opening a conversation and returning to list → sort mode remains applied

**UI/UX Notes**
- Sort dropdown near filters, shows active sort label
- "New conversations available" banner when new inbound arrives during pagination

---

### ACE-1450 · STORY-SFS-04: User Saved Views

> **5 Story Points** | To Do | https://app.clickup.com/t/86d2cxp5u

**User Story**
> As a Support Agent, I want to save my current inbox view as a named preset and access it as quick filter pills so that I can switch between common working modes in one click.

**Description**
Saved views are **per-user** presets. Each saved view stores:
- Filters (structured)
- Sort mode
- Optional: search query text (toggle)

Views are displayed as pills above the conversation list for quick switching.

**Scope**
- Built-in system pills (hardcoded — cannot edit or delete)
- Create saved view from current state (capture-first flow)
- Rename / delete saved view
- Set default view for user
- Applying a saved view **REPLACES** current state (no merge)
- Reset all → System Default View
- Max 20 saved views per user
- **Out of scope:** shared team views (R2), pill reorder / drag-and-drop (R2)

**Acceptance Criteria**

1. **Create saved view from current filters and sort**
   - Agent has selected filters + sort → clicks Save view + enters name → saved view created and appears as pill immediately

2. **Optional include search query in saved view**
   - `include_query=enabled` → view stores query text; applying view restores that query
   - `include_query=disabled` → view saves filters + sort only
   - _Phase 1: query stored as text — known to break if tag is renamed; document for users_

3. **Applying saved view replaces current state**
   - Active query "refund" + apply saved view with query "สลิป" → current query replaced by "สลิป", current filters replaced by view's filters, search bar updates

4. **Apply saved view updates list instantly**
   - Clicking a view pill → filters, sort, and optional query applied; list refreshes to match

5. **Set default view persists and auto-applies on entry**
   - After setting default → reopening inbox auto-applies that view on page load

6. **Rename and delete saved view**
   - Rename → UI updates accordingly
   - Delete default view → reverts to System Default View (1.1a)

7. **Max 20 saved views per user**
   - Attempting to create 21st view → error: "คุณมี saved views ครบ 20 อัน กรุณาลบก่อนสร้างใหม่"; view not created

8. **Reset all returns to System Default View**
   - Agent clicks Reset all → clears all changes; returns to System Default View (1.1a), not to the active saved view

9. **Built-in system pills always visible and non-editable**
   - Built-in pills (My Open, Unassigned, etc.) always shown first before user saved views
   - Built-in pills cannot be deleted or renamed

10. **Tenant isolation and user scoping**
    - User A's saved views are not visible to User B (unless shared views enabled — out of scope)

11. **Same saved view name not allowed**
    - Attempting to save a view with a duplicate name → warning shown; save blocked

**UI/UX Notes**
- Pills row above conversation list: `[Built-in pills] [User saved view pills] [+ Save view]`
- Manage views modal with list, rename, delete, set default
- **Clear search** (removes query only) is separate from **Reset all** (removes everything)
- Show warning in save modal if query text contains tag names

---

### ACE-1443 · STORY-SFS-05: Combined Query Semantics and State Management

> **4 Story Points** | To Do | https://app.clickup.com/t/86d2cxpj6

**User Story**
> As a Product and Engineering Team, I want a clear and consistent query semantics and state management model so that search, filters, sort, and saved views work together predictably and are easy to QA.

**Description**
This card defines the **central rules** that prevent bugs like "filter then search gives wrong results" or "sort then pagination breaks". It establishes:

- Final result set = **Search AND Filters**
- Sort applied **after** filtering
- Saved view applies (filters + sort + optional query) and **replaces** current state
- UI must clearly show active state
- Pagination cursor is tied to sort key and query context

**State change table:**

| Action | Effect | Notes |
|--------|--------|-------|
| Clear search (X on search bar) | Removes query text only; filters + sort remain | User clears keyword but keeps filter context |
| Reset all | Removes query + clears filters + resets sort → System Default View (1.1a) | Returns to ground zero |

**Scope**
- Define query precedence; implement consistently across list and search
- Clear reset rules (Clear search, Reset all, revert to System Default View)
- Pagination context rules for switching modes
- Performance targets for all operations
- **Out of scope:** shareable team URLs (R2)

**Acceptance Criteria**

1. **AND semantics between search and filters**
   - Results match search query AND all active filters

2. **Switching from inbox list to search preserves filters**
   - Entering a search query → search results respect existing filters; UI shows filter chips indicating filters still applied

3. **Switching views replaces current filters and sort deterministically**
   - Applying a saved view → overwrites current filter, sort, and query state; resets pagination cursor

4. **Clear Search and Reset All behave differently and predictably**
   - Clear search (X) → only query text cleared; filters and sort remain
   - Reset all → query + all filters + sort cleared; returns to System Default View (1.1a)

5. **Pagination context is tied to query state**
   - Changing filters, search, or sort → pagination cursor reset; results refresh from page 1

6. **UI state is visible and testable**
   - Active view name, active filter chips, search query, and sort label all displayed and QA-verifiable

7. **No cross-tenant leakage through state**
   - Backend enforces tenant isolation regardless of state values

8. **Concurrent reassignment does not cause live list reorder**
   - Agent B reassigns a conversation away from Agent A while Agent A has list open → conversation does not disappear from Agent A's current view in real-time
   - On next manual refresh or pagination → conversation no longer appears in filtered list

**UI/UX Notes**
- Show "Active View: My Open" near pills row
- Show filter chips row with X to remove per chip
- Show search query in bar with X to Clear search
- One global Reset all button
- Clear search and Reset all visually distinct to prevent confusion

---

## 4. Story Points Summary

| Story ID | Name | Story Points |
|----------|------|-------------|
| ACE-1440 | STORY-SFS-01: Unified Search with Results | 13 |
| ACE-1441 | STORY-SFS-02: Filter System | 6 |
| ACE-1442 | STORY-SFS-03: Sort Options | 5 |
| ACE-1450 | STORY-SFS-04: User Saved Views | 5 |
| ACE-1443 | STORY-SFS-05: Combined Query Semantics and State Management | 4 |
| **Total** | | **33 SP** |

---

## 5. Metadata

| Field | Value |
|-------|-------|
| **Space** | ACE (90166312955) |
| **List** | Omni (901613518748) |
| **Folder** | Ready to Sprint (90168511925) |
| **ACE Product** | Omni |
| **Project** | ACE |
| **Watchers** | Thanyapong |
| **Created** | 2025-04-19 (epoch 1774236039274) |
| **Last Updated** | 2025-04-20 (epoch 1774324964289) |
| **Tags** | — |
| **Priority** | — |
| **Due Date** | — |

---

_Exported from ClickUp on 2026-03-31. Source: https://app.clickup.com/t/86d2cxk7y_
