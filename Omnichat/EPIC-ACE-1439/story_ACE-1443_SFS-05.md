# STORY-SFS-05: Combined Query Semantics and State Management

| Field | Value |
|-------|-------|
| **ClickUp ID** | ACE-1443 |
| **Task ID** | 86d2cxpj6 |
| **Type** | User Story Card |
| **Status** | To Do |
| **Story Points** | 4 SP |
| **Parent Epic** | EPIC-A2.4: Search/Filter/Sort/Saved Views (ACE-1439) |
| **ACE Product** | Omni |
| **Project** | ACE |
| **List** | Omni › Ready to Sprint |
| **Created by** | Thanyapong |
| **Assignees** | — |
| **Priority** | — |
| **ClickUp URL** | https://app.clickup.com/t/86d2cxpj6 |

---

## User Story

> As a **Product and Engineering Team**,
> I want a **clear and consistent query semantics and state management model**
> so that **search, filters, sort, and saved views work together predictably and are easy to QA**.

---

## Description

This card defines the **central rules** ("กติกากลาง") that prevent bugs like "filter then search gives wrong results" or "sort then pagination breaks".

### Core Rules

- **Final result set** = Search **AND** Filters
- **Sort** applied after filtering
- **Saved view** applies (filters + sort + optional query) and **replaces** current state
- UI must clearly show active state
- **Pagination cursor** is tied to sort key and query context

### State Change Behavior

| Action | Effect | Notes |
|--------|--------|-------|
| Clear search (X on search bar) | Removes query text only; filters + sort remain | User clears keyword but keeps filter context |
| Reset all | Removes query + clears all filters + resets sort → System Default View (1.1a) | Returns to ground zero |

### Scope

- Define query precedence; implement consistently across list and search
- Clear reset rules (Clear search, Reset all, revert to System Default View)
- Pagination context rules for switching modes
- Performance targets for all operations

**Out of scope:** shareable team URLs (R2)

---

## Acceptance Criteria

### AC-1: AND semantics between search and filters
- **Given** a search query and multiple filters are active
- **When** results are computed
- **Then** only items matching the search query AND all filters are returned

### AC-2: Switching from inbox list to search preserves filters
- **Given** filters are active
- **When** agent enters a search query
- **Then** search results respect existing filters and UI clearly indicates filters are still applied via chips

### AC-3: Switching views replaces current filters and sort deterministically
- **Given** a saved view is selected
- **When** the agent applies it
- **Then** it overwrites current filter, sort, and query state to match the saved view and resets pagination cursor

### AC-4: Clear Search and Reset All behave differently and predictably

**Clear search:**
- **Given** the agent has active search query and filters
- **When** they click Clear search (X on search bar)
- **Then** only the query text is cleared and filters and sort remain unchanged

**Reset all:**
- **Given** the agent has active search query and filters
- **When** they click Reset all
- **Then** query, all filters, and sort are cleared and the system returns to System Default View (section 1.1a)

### AC-5: Pagination context is tied to query state
- **Given** agent paginates results under a specific query state
- **When** they change filters, search, or sort
- **Then** pagination cursor is reset and results refresh from page 1 of the new state

### AC-6: UI state is visible and testable
- **Given** filters, search, and view are active
- **When** the UI renders
- **Then** active view name, active filter chips, search query, and sort label are all displayed and can be validated in QA

### AC-7: No cross-tenant leakage through state
- **Given** query state may include values that overlap with other tenants
- **When** state is applied
- **Then** backend still enforces tenant isolation and does not return data from other tenants

### AC-8: Concurrent reassignment does not cause live list reorder
- **Given** agent A is viewing inbox with filter `assignee=mine`
- **When** agent B reassigns a conversation away from agent A while agent A has the list open
- **Then** the conversation does not disappear from agent A's current loaded view in real-time
- **And** on the next manual refresh or pagination the conversation will no longer appear in the filtered list

---

## UI/UX Notes

- Show "Active View: My Open" near pills row
- Show filter chips row with X to remove per chip
- Show search query in bar with X to Clear search
- One global Reset all button
- **Clear search** and **Reset all** must be visually distinct to prevent confusion

---

_Exported from ClickUp on 2026-03-31. Source: https://app.clickup.com/t/86d2cxpj6_
