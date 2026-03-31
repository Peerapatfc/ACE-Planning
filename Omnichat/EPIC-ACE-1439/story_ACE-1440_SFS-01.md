# STORY-SFS-01: Unified Search with Results

| Field | Value |
|-------|-------|
| **ClickUp ID** | ACE-1440 |
| **Task ID** | 86d2cxnk4 |
| **Type** | User Story Card |
| **Status** | To Do |
| **Story Points** | 13 SP |
| **Parent Epic** | EPIC-A2.4: Search/Filter/Sort/Saved Views (ACE-1439) |
| **ACE Product** | Omni |
| **Project** | ACE |
| **List** | Omni › Ready to Sprint |
| **Created by** | Thanyapong |
| **Assignees** | — |
| **Priority** | — |
| **ClickUp URL** | https://app.clickup.com/t/86d2cxnk4 |

---

## User Story

> As a **Support Agent**,
> I want to **search across conversations and messages using a single search bar**
> so that I can **quickly find customers and specific message content without manual scrolling**.

---

## Description

User types a single query — the system searches all fields simultaneously and displays results in 2 grouped sections:

- **CONVERSATIONS (N)** — match from contact name, identifier, order ID, tag text
- **MESSAGES (N)** — match from message text

### Scope

- Search bar on inbox list — debounce 300ms, min 2 chars
- Grouped sections: CONVERSATIONS + MESSAGES in one view; sections with no results are hidden
- Click conversation result → open conversation
- Click message result → open conversation + scroll/highlight to matched message
- Active filters remain applied during search (AND semantics)
- X on search bar = Clear search (clears query only; filters remain)

**Out of scope:** advanced ranking, semantic search, tag filter dropdown, phone/SKU search

---

## Acceptance Criteria

### AC-1: Empty state and error state
- **Given** no results match or the search API fails
- **When** the UI renders results
- **Then** it shows a clear empty state or a retry action and does not lose the previous inbox view state unexpectedly

### AC-2: Search returns grouped results in a single view
- **Given** the agent enters a query with 2 or more characters
- **When** search is executed
- **Then** CONVERSATIONS section and MESSAGES section are displayed in a single scrollable view without any tab switching required
- **And** sections with no results are hidden automatically

### AC-3: Conversations section returns matching results
- **Given** the agent enters a query matching contact name, identifier, order ID, or tag text
- **When** search is executed
- **Then** the Conversations section shows up to 5 matching conversations with name, channel badge, status badge, and `last_message_at`
- **And** a "ดูทั้งหมด (N)" button appears when total results exceed 5

### AC-4: Messages section returns matching message snippets
- **Given** messages exist containing the keyword in text
- **When** the agent searches by that keyword
- **Then** the Messages section shows up to 5 results with highlighted snippet, conversation name, channel badge, and timestamp
- **And** a "ดูทั้งหมด (N)" button appears when total results exceed 5

### AC-5: Tag search works via text match
- **Given** a tag "VIP" exists on a conversation
- **When** the agent types "VIP" in the search bar
- **Then** that conversation appears in the Conversations section with the tag badge visible

> **Known limitation:** Phase 1 uses text match only — results will change if the tag is renamed or deleted. Fix via `tag_id` filter in R2.

### AC-6: Per-channel identifier search returns correct conversations
- **Given** conversations exist with channel-specific identifiers
- **When** the agent types a Shopee Order ID, LINE User ID, or Shopify Order #1234
- **Then** the matching conversation from that channel appears in the Conversations section

### AC-7: Click message result navigates and highlights matched message
- **Given** a message search result is clicked
- **When** the conversation opens
- **Then** the timeline scrolls to the matched message and highlights it visually
- **And** if the message is not found within 3 pages of pagination, a banner "ข้อความอาจอยู่เกินหน้าที่โหลด" is shown and the timeline scrolls to top

### AC-8: Minimum query length enforced
- **Given** the agent types fewer than 2 characters in the search bar
- **When** the UI renders
- **Then** no search request is triggered and the inbox list remains unchanged

### AC-9: Active filters apply to search results
- **Given** `channel=LINE` filter is active
- **When** the agent searches for "refund"
- **Then** results show only LINE conversations and messages matching the query
- **And** filter chips remain visible in the filter bar indicating filters are still applied

### AC-10: All statuses included in results with status badge
- **Given** conversations across all statuses exist
- **When** the agent performs a search
- **Then** completed conversations are included in results alongside open, in progress, and pending
- **And** each result card shows the status badge so the agent can distinguish
- **And** the agent can filter out completed via the status filter if needed

### AC-11: Search respects tenant isolation and permission scope
- **Given** two tenants have similar keywords
- **When** the agent in tenant A searches
- **Then** results include only tenant A data and only conversations the agent is permitted to view

### AC-12: Debounce and performance
- **Given** the agent types in the search bar
- **When** they pause typing for 300ms (debounce interval)
- **Then** a search request is triggered, the UI shows a loading state, and the inbox list does not freeze
- **And** search API p95 response time must be under 500ms for dataset of 1M+ messages per tenant

---

## UI/UX Notes

- Section headers: **"CONVERSATIONS (N)"** and **"MESSAGES (N)"** in uppercase muted text
- Keyword highlighted in both conversation preview and message snippet
- "ดูทั้งหมด (N)" button when section has > 5 results
- X on search bar = Clear search only (does not clear filters)
- Empty sections hidden; if only Conversations section has results, only that is shown
- Status badge displayed on every result card

---

## Sub-tasks

| ID | Name | SP | URL |
|----|------|----|-----|
| ACE-1461 | task (ห้ามลบฝากแต้มเฉยๆ) | 3 SP | https://app.clickup.com/t/86d2d349h |

---

_Exported from ClickUp on 2026-03-31. Source: https://app.clickup.com/t/86d2cxnk4_
