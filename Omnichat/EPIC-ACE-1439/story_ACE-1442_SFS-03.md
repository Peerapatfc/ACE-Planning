# STORY-SFS-03: Sort Options

| Field | Value |
|-------|-------|
| **ClickUp ID** | ACE-1442 |
| **Task ID** | 86d2cxp0v |
| **Type** | User Story Card |
| **Status** | To Do |
| **Story Points** | 5 SP |
| **Parent Epic** | EPIC-A2.4: Search/Filter/Sort/Saved Views (ACE-1439) |
| **ACE Product** | Omni |
| **Project** | ACE |
| **List** | Omni › Ready to Sprint |
| **Created by** | Thanyapong |
| **Assignees** | — |
| **Priority** | — |
| **ClickUp URL** | https://app.clickup.com/t/86d2cxp0v |

---

## User Story

> As a **Support Agent**,
> I want to **sort the inbox list by different strategies**
> so that I can **prioritize work efficiently depending on the situation**.

---

## Description

Sort orders the conversation list after filters and search have been applied. MVP has 3 non-overlapping sort modes, each targeting a distinct use case:

| Mode | Use Case |
|------|---------|
| **Latest activity** _(default)_ | General monitoring — see most recently active conversations |
| **Oldest waiting** | Triage — find conversations waiting longest without a reply; prevent SLA miss |
| **SLA due soonest** | Focus on conversations closest to reply deadline |

### Scope

- Sort dropdown with 3 modes on inbox list
- Sort applies to **Conversation list only** (Messages section in search uses relevance ordering)
- UI indicator for active sort

**Out of scope:** custom sort per agent, priority scoring

---

## Acceptance Criteria

### AC-1: Default sort is latest activity
- **Given** the agent opens the inbox
- **When** the list loads
- **Then** conversations are sorted by `last_message_at DESC` by default

### AC-2: Sort by oldest waiting shows unanswered conversations first
- **Given** conversations exist with different last inbound message times
- **When** the agent selects **Oldest waiting**
- **Then** conversations are sorted by `last_inbound_at ASC` showing those waiting longest at the top
- **And** conversations where the last message was outbound (already answered) do not dominate the top
- **And** conversations with `NULL last_inbound_at` appear at the end (NULLS LAST)

### AC-3: Sort by SLA due soonest works when SLA is enabled
- **Given** SLA due timestamps exist
- **When** the agent selects **SLA due soonest**
- **Then** the list reorders by `sla_due_at ASC`
- **And** conversations with `NULL sla_due_at` appear at the end (NULLS LAST)

### AC-4: Sort applies to Conversation list only
- **Given** the agent is viewing search results with Messages section visible
- **When** the agent changes sort mode
- **Then** only the Conversations section reorders
- **And** the Messages section always uses relevance ordering and is not affected by the sort dropdown

### AC-5: Sorting works together with filters and search
- **Given** a search query and filters are active
- **When** the agent changes sort mode
- **Then** the same filtered and searched set is reordered without losing filters or query

### AC-6: Pagination remains stable per sort mode
- **Given** there are many conversations
- **When** the agent loads more while a sort mode is active
- **Then** the next page continues the same sort order without duplicates or skips

### AC-7: New inbound during pagination does not reorder current view
- **Given** the agent is paginating through the conversation list
- **When** a new message arrives on a conversation
- **Then** the conversation does not jump position in the current loaded view
- **And** a "New conversations available" indicator may appear to prompt manual refresh

### AC-8: Sort state persists during navigation
- **Given** the agent selects a sort mode
- **When** they open a conversation and return to the list
- **Then** the sort mode remains applied

---

## UI/UX Notes

- Sort dropdown near filters — shows active sort label
- "New conversations available" banner when new inbound arrives during pagination

---

_Exported from ClickUp on 2026-03-31. Source: https://app.clickup.com/t/86d2cxp0v_
