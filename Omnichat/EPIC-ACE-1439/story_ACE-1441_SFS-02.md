# STORY-SFS-02: Filter System

| Field | Value |
|-------|-------|
| **ClickUp ID** | ACE-1441 |
| **Task ID** | 86d2cxntq |
| **Type** | User Story Card |
| **Status** | To Do |
| **Story Points** | 6 SP |
| **Parent Epic** | EPIC-A2.4: Search/Filter/Sort/Saved Views (ACE-1439) |
| **ACE Product** | Omni |
| **Project** | ACE |
| **List** | Omni › Ready to Sprint |
| **Created by** | Thanyapong |
| **Assignees** | — |
| **Priority** | — |
| **ClickUp URL** | https://app.clickup.com/t/86d2cxntq |

---

## User Story

> As a **Support Agent**,
> I want to **use structured filters that work together with search**
> so that I can **narrow down the inbox and search results to the exact subset I need**.

---

## Description

Filters are structured condition-based narrowing that must work together with search via AND semantics. Filter state must clearly display what is active and be resettable in one click.

### Scope

- Filter panel / filter bar
- MVP filter fields: `channel_type` (multi-select), `status` (4 states), `assignee`, `overdue`
- Filters apply to both Inbox list and Search grouped results
- Active filter chips with X remove per chip
- Reset all → System Default View
- Filter state persists via URL query params

**Out of scope:** `has_attachment` filter, tag filter dropdown, source label filter, advanced multi-condition builder

---

## Acceptance Criteria

### AC-1: Filters apply as AND with search
- **Given** a search query is active and filters are selected
- **When** results are shown
- **Then** the system returns only items matching the search query AND all selected filters

### AC-2: Channel filter is multi-select
- **Given** conversations exist across multiple channels
- **When** the agent selects LINE and Shopee in the channel filter
- **Then** only conversations from LINE or Shopee are shown (OR within channel values, AND with other filters)
- **And** active filter chips show each selected channel separately with an X to remove

### AC-3: Status filter supports all 4 states in multi-select
- **Given** conversations exist in open, in progress, pending, and completed states
- **When** the agent selects `open` and `in_progress` in the status filter
- **Then** only conversations in either of those states are shown
- **And** when no status is selected the default shows all 4 states

### AC-4: Assignment filter works correctly
- **Given** conversations have different assignees
- **When** the agent filters `status=open` and `assignee=mine`
- **Then** the list shows only conversations that are open and assigned to the current agent

### AC-5: Overdue filter is hidden when SLA is disabled
- **Given** SLA feature is disabled for the tenant
- **When** the filter bar renders
- **Then** the Overdue filter option is hidden entirely (not merely disabled)

- **Given** SLA feature is enabled and some conversations are overdue
- **When** the agent enables the overdue filter
- **Then** only overdue conversations are shown and the UI indicates overdue state

### AC-6: Reset all clears filters and restores System Default View
- **Given** multiple filters are active
- **When** the agent clicks Reset all
- **Then** all filters are cleared, search query is cleared, and the list returns to System Default View (section 1.1a)

### AC-7: Filter state persists via URL params across page refresh
- **Given** the agent has active filters (e.g. `channel=LINE, status=open`)
- **When** they refresh the page or share the URL
- **Then** the same filters are restored automatically from URL query params
- **And** the URL format is e.g. `?channel=LINE,Facebook&status=open,in_progress`

> _(Tech improvement — implement when there is a real use case)_

### AC-8: Filters must never leak data cross-tenant
- **Given** multiple tenants exist in the system
- **When** any filter combination is applied
- **Then** results include only data belonging to the current tenant

---

## UI/UX Notes

- Filter bar with dropdowns above conversation list
- Active filters displayed as chips with X to remove per filter
- Channel filter: multi-select dropdown with checkboxes
- Status filter: multi-select dropdown (open, in progress, pending, completed)
- Overdue filter: hidden entirely when SLA disabled
- Reset all: one-click
- Red badge count on each filter section showing number of active selections
- Show agent names in assignee filter

---

## Sub-tasks

| ID | Name | SP | URL |
|----|------|----|-----|
| ACE-1462 | Task | 1 SP | https://app.clickup.com/t/86d2d39e4 |

---

_Exported from ClickUp on 2026-03-31. Source: https://app.clickup.com/t/86d2cxntq_
