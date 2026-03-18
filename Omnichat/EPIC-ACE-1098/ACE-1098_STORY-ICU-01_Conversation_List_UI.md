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

**Figma Reference:** [Figma Design](https://www.figma.com/design/xvB8RfVaiaKcGtlVBeSJVg/Design-System---Zimple-Solution?node-id=262-18409&m=dev)

**Layout:** Left pane conversation list with right border separator. Right pane is the conversation timeline (may be empty until a conversation is selected).

**Header Section:**
* Left side: Inbox icon (mail) + "Inbox" title (semibold, 16px)
* Right side: 3 ghost icon buttons in a row:
  * Filter icon button — opens filter options
  * Sort icon button (arrow-up-down) — controls sort order
  * Search icon button (magnifier) — opens search input

**Filter Tabs:**
* Horizontal tab bar below the header with 3 tabs:
  * `All` — shows all conversations, with unread count badge (e.g. "6") in primary style
  * `Unread` — filters to conversations with unread messages
  * `Unassigned` — filters to conversations with no assigned agent
* Active tab: primary background with white text (pill style)
* Inactive tab: muted text, transparent background, hover state

**Conversation Card — Structure:**
Each card is a list item with 12px horizontal padding and 12px vertical padding:

| Element | Description | Style |
|---------|-------------|-------|
| **Avatar** | 40x40 circular profile image | `rounded-full` |
| **Channel badge** | 16x16 icon overlay on avatar (bottom-right) | LINE (green #06C755), Facebook (blue #1877F2), Shopee (orange #EE4D2D), Lazada, Instagram (gradient), TikTok (black) |
| **Contact name** | Display name of the contact | Medium weight, 14px, foreground color |
| **Channel account** | Account name + channel type | Regular weight, 12px, muted (#737373) — e.g. "Zimple Solution (Line OA)" |
| **More options** | Ellipsis-vertical icon button (top-right of card) | Ghost style, muted color |
| **Last message preview** | Single-line truncated text + read receipt icon | 12px, ellipsis overflow |
| **Read status icon** | Double-check icon (check-check) for sent/read messages | 14px, primary color, shown after message text |
| **Unread count badge** | Red (#EF001D) circular badge with count number | White text, rounded-full, shown at end of message row |
| **Tags** | Outline badges in a row (e.g. "Label", "Label") with `+N` overflow count | Border border-color, 11px font, rounded-full, max 4 visible |
| **Assignee badge** | Small chip with channel icon + agent name (e.g. LINE icon + "Anupong Jin...") | Muted background, 12px, rounded, truncated at ~120px |
| **Unassigned indicator** | User-round-plus icon (no background) | Muted color, shown when no agent assigned |
| **Timestamp** | Time display (right-aligned on the bottom row) | 11px, muted (#737373) — e.g. "09:34 AM" |

**Card Visual States:**
* **Selected/Active card:** Left border 2px primary color + light primary tint background (`primary/5`)
* **Unread conversation:** Contact name in semibold, message preview in darker foreground, red unread count badge visible
* **Read conversation:** Contact name in medium weight, message preview in muted (#737373), double-check icon shown, no unread badge

**Filters:** Tab-based quick toggles (All / Unread / Unassigned), no page reload required

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
