# STORY-ICU-01: Conversation List UI with filters and pagination
**ID:** ACE-1099
**Status:** TO DO
**Sprint Points:** 10
**Assignee:** Peerapat Pongnipakorn

**Description (User Story):**
> As a Support Agent
> I want to see a list of conversations across all connected channels with filters and pagination
> so that I can quickly find the right conversation and manage my workload efficiently.

**Detail / Description:**
> การ์ดนี้คือหน้าจอหลักฝั่งซ้ายของ Unified Inbox ที่ต้องใช้งานได้จริงใน pilot

**Acceptance Criteria:**
1. Load conversation list successfully from the backend API.
2. Pagination is stable and deterministic (load more or cursor-based as per API design).
3. Filters (channel, status, assignee) update the list content correctly.
4. Conversation card content is complete:
   * Given the list is rendered
   * When each conversation card is displayed
   * Then it shows contact display name or fallback identifier, channel badge, last message preview, last update time, and status or owner indicator
5. Loading and empty states are clear:
   * Given the API request is in progress or returns zero results
   * When the list renders
   * Then a loading skeleton is shown during load and an empty state is shown with guidance when no results match the filters

**UI/UX Notes:**

**Figma Reference:** [Figma Design](https://www.figma.com/design/MjqfuSKG8F5lUQEef2DR3a/-UI-Wireframe--Zimple-solution?node-id=418-3543&m=dev)

**Layout:** Left pane conversation list with right border separator. Right pane is the conversation timeline (may be empty until a conversation is selected).

**Header Section:**
* Title: "Your Inbox" (Heading 4, semibold 20px)
* Search icon button (top-right corner)
* Filter bar below title with:
  * Sidebar toggle button (panel-left-close icon, outlined style)
  * "All Channel" dropdown — filters by channel type
  * "Newest" dropdown with arrow-up-down sort icon — controls sort order

**Conversation Card — Structure:**
Each card is a rounded container (16px radius) with 8px padding and 12px gap between sections:

| Element | Description | Style |
|---------|-------------|-------|
| **Avatar** | 40x40 circular profile image | `rounded-full` |
| **Channel badge** | 16x16 icon overlay on avatar (bottom-right) | LINE (green), Facebook (blue), Shopee (orange #EE4D2D), Lazada, Instagram icons |
| **Contact name** | Display name of the contact | Medium weight, 16px, foreground color |
| **Channel account** | Account name + channel type | Regular weight, 12px, muted (#737373) — e.g. "Zimple Solution (Line OA)" |
| **More options** | Ellipsis-vertical icon button (top-right of card) | Ghost button style |
| **Last message preview** | Single-line truncated text | 14px, ellipsis overflow |
| **Read status icon** | Double-check icon (check-check) for sent/read messages | 16px, shown before message preview |
| **Unread count badge** | Red (#EF001D) circular badge with count number | White text, rounded-full, shown after message preview |
| **Tags** | Outline badges (e.g. "New Customer", "Sale", "Billing Issue") | Border #E5E5E5, 12px semibold, 8px rounded |
| **Assignee row** | "Assigned to [Name]" with chevron-down dropdown | 12px muted label, 12px foreground name |
| **Unassigned indicator** | User-round-plus icon in circular secondary background | 20x20, shown when no assignee |
| **Timestamp** | Relative time display | 12px, muted (#737373) — e.g. "09:34 AM" |

**Card Visual States:**
* **Selected/Active card:** Background `secondary` (#F5F5F5)
* **Unread conversation:** Message preview in darker foreground (#171717, `secondary-foreground`), red unread count badge visible
* **Read conversation:** Message preview in muted (#737373), double-check icon shown, no unread badge

**Filters:** Should be quick toggles (dropdowns) and not require page reload

**Technical Notes:**
* **APIs:**
  * GET conversations
  * Parameters: tenant scope via auth, page_size, cursor, filters (channel_type, status, assignee)
  * Response: items with conversation_id, contact_display_name, channel_type, last_message_preview, last_message_at, status, assignee_id, unread_count (optional), source flags (optional)
* **Data:**
  * Uses conversation summary fields such as last_message_at and last_message_preview that are updated by persistence layer
  * Cursor pagination contract must be documented and consistent with NDP 05

**Subtasks (5):** 
- ACE-1103, ACE-1383, ACE-1385, ACE-1384, ACE-1386

**Comments:**
* Attachai Saorangtoi: "Pagination: Limit 20"
