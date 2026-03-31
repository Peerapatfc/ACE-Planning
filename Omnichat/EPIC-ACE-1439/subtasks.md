# EPIC ACE-1439 — Subtask Breakdown (Mapped to Codebase)

> Generated: 2026-03-31
> Total: 34 subtasks / 40 SP (includes 8 Meilisearch subtasks)

## Current Implementation Baseline

| Layer | What already exists | Key file |
|---|---|---|
| FE store | `filter`, `statusFilters`, `searchQuery`, `channelFilter` (single), `sortOrder` ('asc'/'desc'), `tagFilter`, `nextCursor` | `apps/workspace-admin/src/app/(main)/dashboard/chats/_store/chat-store.ts` |
| FE list | Search bar (debounce 500ms), channel/status/assignee/tag filters, active chips, URL params (nuqs), virtual scroll | `apps/workspace-admin/src/app/(main)/dashboard/chats/_components/conversation-list/conversation-list.tsx` |
| FE API | `listConversations({ channel_type, status, sort_order, search, is_read, assignee, tag_id, limit, cursor })` | `apps/workspace-admin/src/app/(main)/dashboard/chats/_api/conversations.api.ts` |
| BE DTO | `status` (comma-sep multi), `channel_type` (single), `sort_order` ('asc'/'desc'), `search`, `is_read`, `assigned_agent_id`, `tag_id`, cursor | `apps/omnichat-service/src/conversations/dto/list-conversations.dto.ts` |

---

## ACE-1440 · STORY-SFS-01: Unified Search with Results — 13 SP

> ClickUp: https://app.clickup.com/t/86d2cxnk4

| # | Task | Layer | SP | Key Files |
|---|---|---|---|---|
| 1 | [BE] Search API: grouped results (Conversations + Messages) | BE | 3 | `omnichat-service/src/conversations/conversations.service.ts`, `dto/list-conversations.dto.ts` (add `search_mode=grouped`), `api-gateway/src/omnichat/controllers/conversations.controller.ts` |
| 2 | [BE] Message full-text search with snippet | BE | 2 | `omnichat-service/src/messages/messages.service.ts` — full-text search on `content`, return snippet + `conversation_id`, `channel_type`, `contact_name`, `created_at` scoped to `tenant_id` |
| 3 | [FE] Grouped search results UI | FE | 3 | NEW `conversation-list/search-results-view.tsx` — CONVERSATIONS(N) + MESSAGES(N), up to 5 per section, hidden when 0, status badge per result card |
| 4 | [FE] Click message result → scroll to matched message | FE | 2 | `chat-store.ts` (add `highlightMessageId: string \| null`), `chat-view/chat-view.tsx` (scroll + highlight on mount), banner "ข้อความอาจอยู่เกินหน้าที่โหลด" if not found in 3 pages |
| 5 | [FE] Search debounce 300ms + min 2 chars | FE | 0.5 | `conversation-list.tsx` line 189 — change `500` → `300`; add `if (value.length > 0 && value.length < 2) return` guard |
| 6 | [FE] "ดูทั้งหมด" load more + hide empty section | FE | 2.5 | Extend `search-results-view.tsx` — "ดูทั้งหมด" triggers `GET /conversations?search=...&search_mode=conversations&cursor=` for full results; hide section when `total=0` |

**Total: 13 SP**

### Gap vs Current Code
- ❌ Search currently returns flat conversation list only (no message snippets)
- ❌ No grouped CONVERSATIONS + MESSAGES display
- ❌ No scroll-to-message on click
- ❌ Debounce is 500ms (spec: 300ms)
- ❌ No min-2-chars enforcement

---

## ACE-1441 · STORY-SFS-02: Filter System — 6 SP

> ClickUp: https://app.clickup.com/t/86d2cxntq

| # | Task | Layer | SP | Key Files |
|---|---|---|---|---|
| 1 | [BE] Channel filter: multi-select support | BE | 1 | `dto/list-conversations.dto.ts` — change `@IsIn(CHANNEL_TYPES)` to `@Matches(/^(LINE\|FACEBOOK\|...)(,(...))*/)`; `conversations.service.ts` — update WHERE to `channel_type IN [...]` |
| 2 | [FE] Channel filter: multi-select UI | FE | 1.5 | `chat-store.ts` — `channelFilter: ChannelFilter` → `channelFilters: ChannelType[]`; `conversation-list.tsx` lines 424-462 — replace single-select popover with multi-select checkboxes; `types/omnichat.ts` — update type; `conversations.api.ts` — comma-join array |
| 3 | [BE] Overdue filter param (SLA-gated) | BE | 0.5 | `dto/list-conversations.dto.ts` — add `@IsOptional() @IsBooleanString() is_overdue?: string`; `conversations.service.ts` — add `WHERE sla_due_at < NOW()` when `is_overdue=true`; gated by tenant SLA flag |
| 4 | [FE] Overdue filter toggle | FE | 1 | `conversation-list.tsx` — add Overdue toggle in filter row, hidden when `!tenant.sla_enabled`; `chat-store.ts` — add `isOverdue: boolean` + `setOverdueFilter()`; `conversations.api.ts` — add `is_overdue` param |
| 5 | [FE] Channel filter chips (one per selected channel) | FE | 1 | `conversation-list.tsx` lines 611-627 — replace single channel chip with `channelFilters.map(ch => <chip key={ch}>{ch} <X onClick={() => removeChannel(ch)} />)` |
| 6 | [FE] Assignee filter: add specific agent option | FE | 1 | `conversation-list.tsx` assignee popover (lines 509-550) — add agent list from `useAgents()`; `chat-store.ts` — separate `assignedAgentId: string \| 'me' \| 'none' \| null` from legacy `filter: ConversationFilter`; `conversations.api.ts` — pass agent UUID |

**Total: 6 SP**

### Gap vs Current Code
- ✅ Multi-select status — already implemented
- ✅ Active filter chips + X per chip — already implemented
- ✅ URL params (nuqs) — already implemented
- ✅ Reset all (handleClearAllFilters) — already implemented
- ❌ Channel is single-select (spec: multi-select)
- ❌ Overdue/SLA filter — missing
- ❌ Channel chips show single value only
- ❌ Assignee filter only supports mine/unassigned/all (spec: includes specific agent name)

---

## ACE-1442 · STORY-SFS-03: Sort Options — 5 SP

> ClickUp: https://app.clickup.com/t/86d2cxp0v

| # | Task | Layer | SP | Key Files |
|---|---|---|---|---|
| 1 | [BE] Sort modes: oldest_waiting + sla_due_soonest | BE | 2 | `dto/list-conversations.dto.ts` — add `sort_by?: 'latest_activity' \| 'oldest_waiting' \| 'sla_due_soonest'` alongside existing `sort_order`; `conversations.service.ts` — `oldest_waiting`: `ORDER BY last_inbound_at ASC NULLS LAST`; `sla_due_soonest`: `ORDER BY sla_due_at ASC NULLS LAST`; `api-gateway/conversations.controller.ts` — proxy new param |
| 2 | [FE] Sort dropdown: 3 named modes | FE | 1 | `conversation-list.tsx` lines 57-60 — replace `SORT_OPTIONS` with `[{value:'latest_activity',...},{value:'oldest_waiting',...},{value:'sla_due_soonest',...}]`; `chat-store.ts` — `sortOrder: SortOrder` → `sortBy: SortMode`; `types/omnichat.ts` — new `SortMode` type; `conversations.api.ts` — rename param `sort_order` → `sort_by` |
| 3 | [FE] "New conversations available" banner | FE | 1 | `chat-store.ts` `pollConversations()` — when `sortBy !== 'latest_activity'`, don't merge new conversations into list; store in `pendingConversations: OmniConversation[]`; `conversation-list.tsx` — show sticky banner "N new conversations" → click to apply |
| 4 | [FE] Persist sort on back-navigation | FE | 1 | `chat-store.ts` — confirm `setActiveConversation()` does NOT reset `sortBy` or `nextCursor`; `conversation-list.tsx` `hasInitialized` effect — ensure sort is restored from URL before first fetch; add `sort` to nuqs params (already exists as `sort` key, verify mapping) |

**Total: 5 SP**

### Gap vs Current Code
- ✅ Sort dropdown exists (asc/desc)
- ✅ Sort persists in URL params
- ❌ "Oldest first" uses `last_message_at ASC` (spec: needs `last_inbound_at ASC NULLS LAST`)
- ❌ "SLA due soonest" mode — missing entirely
- ❌ "New conversations available" banner — pollConversations currently merges silently
- ❌ Named sort modes (API currently only accepts 'asc' | 'desc')

---

## ACE-1450 · STORY-SFS-04: User Saved Views — 5 SP

> ClickUp: https://app.clickup.com/t/86d2cxp5u

| # | Task | Layer | SP | Key Files |
|---|---|---|---|---|
| 1 | [BE] SavedView DB model + migration | BE | 1 | `apps/omnichat-service/prisma/schema.prisma` — new model `SavedView { id String @id @default(uuid()), user_id String, tenant_id String, name String, filters Json, sort_by String, include_query Boolean @default(false), query_text String?, is_default Boolean @default(false), created_at DateTime @default(now()), updated_at DateTime @updatedAt }`; generate Prisma migration |
| 2 | [BE] Saved views CRUD API | BE | 1.5 | NEW module `apps/omnichat-service/src/saved-views/` — `GET /saved-views` (list by user+tenant), `POST /saved-views` (max 20, no dupe names), `PATCH /saved-views/:id` (rename), `DELETE /saved-views/:id`, `PATCH /saved-views/:id/set-default`; wire through `apps/api-gateway/src/omnichat/`; FE API: add `saved-views.api.ts` |
| 3 | [FE] System pills row (All, My Open, Unassigned…) | FE | 0.5 | NEW `conversation-list/inbox-pills.tsx` — hardcoded pills: All / My Open (`assignee=me AND status=open`) / Unassigned (`assignee=none AND status=open`) / In Progress / Pending / Overdue (SLA-gated); click → `applyPreset()`; click active → `resetAll()`; integrate into `conversation-list.tsx` above filter bar |
| 4 | [FE] User saved views pills + Save view dialog | FE | 1.5 | NEW `conversation-list/saved-views-manager.tsx` — fetch `GET /saved-views`; render user pills after system pills; "+" Save view → `SaveViewDialog` (name, include_query toggle, max-20 guard, dupe-name guard); click pill → `applyView()`; `chat-store.ts` — add `activeViewId: string \| null`, `applyView(view: SavedView)` action that replaces searchQuery + filters + sortBy atomically and resets cursor |
| 5 | [FE] Manage views modal + default auto-apply | FE | 0.5 | NEW `ManageViewsModal` — list views with rename/delete/set-default actions; `conversation-list.tsx` `hasInitialized` effect — after fetching saved views, if one `is_default=true`, call `applyView(defaultView)` before `fetchConversations()` |

**Total: 5 SP**

### Gap vs Current Code
- ❌ Feature entirely missing — no saved views in any layer
- ❌ No system pills row
- ❌ No SavedView backend model
- ❌ No saved views API endpoints

---

## ACE-1440 · Meilisearch Integration — 7 SP

> ClickUp parent: https://app.clickup.com/t/86d2cxnk4
> Reference: `meilisearch-evaluation.md`

| # | Task | Layer | SP | Key Files |
|---|---|---|---|---|
| 1 | [INFRA] Add Meilisearch to docker-compose + env vars | INFRA | 0.5 | `docker-compose.yml` — add `meilisearch:v1.11` service; `.env` — add `MEILISEARCH_HOST`, `MEILISEARCH_API_KEY` |
| 2 | [BE] SearchModule + SearchService (index/delete wrappers) | BE | 1 | NEW `apps/omnichat-service/src/search/search.service.ts` — wrappers for `addDocuments`, `deleteDocument` per index; NestJS module wiring |
| 3 | [BE] Index design + settings for `conversations` + `messages` indexes | BE | 0.5 | `search.service.ts` — `updateSettings()` for searchable/filterable/sortable attributes on both indexes |
| 4 | [BE] Event hooks: sync message create/update/delete → Meilisearch | BE | 1 | `messages.service.ts` — call `searchService.indexMessage()` on create; `searchService.deleteMessage()` on soft-delete |
| 5 | [BE] Backfill CLI command for existing messages per tenant | BE | 1 | NEW `apps/omnichat-service/src/search/search-backfill.command.ts` — batch cursor loop over `message` table, push to Meilisearch in batches of 500 |
| 6 | [BE] Grouped search endpoint using Meilisearch /multi-search | BE | 1.5 | `conversations.controller.ts` — new `GET /conversations/search`; `search.service.ts` — `groupedSearch()` calls Meilisearch `/multi-search` returning `{ conversations, messages }` |
| 7 | [BE] PostgreSQL fallback for grouped search (circuit breaker) | BE | 0.5 | `search.service.ts` — try/catch around Meilisearch call; on error fallback to `conversations.service.ts` ILIKE query |
| 8 | [BE] Daily reconciliation job (PG vs Meili doc count per tenant) | BE | 1 | NEW `apps/omnichat-service/src/search/search-reconcile.job.ts` — BullMQ cron; compare `prisma.message.count` vs Meili `estimatedNbDocuments` per tenant; log discrepancy |

**Total: 7 SP**

### Key Technical Decisions
- Meilisearch handles **search only** — filters/sort/pagination stay in PostgreSQL
- `tenant_id` filter is **mandatory** on every Meilisearch query (multi-tenant isolation)
- Index only `content_type = 'text'` messages — skip images/files/stickers
- Typo tolerance: enabled for conversations, **disabled** for messages (exact keyword matching preferred)
- See `meilisearch-evaluation.md` for full index schema, benchmark data, and rollback strategy

---

## ACE-1443 · STORY-SFS-05: Combined Query Semantics & State Management — 4 SP

> ClickUp: https://app.clickup.com/t/86d2cxpj6

| # | Task | Layer | SP | Key Files |
|---|---|---|---|---|
| 1 | [FE] Add clearSearch() and resetAll() to store | FE | 1 | `chat-store.ts` — add `clearSearch(): void` (sets `searchQuery=''`, resets cursor, does NOT touch filters/sortBy) and `resetAll(): void` (resets to System Default View: searchQuery='', channelFilters=[], statusFilters=[], assignedAgentId=null, isOverdue=false, sortBy='latest_activity', activeViewId=null); `conversation-list.tsx` — wire search-bar X to `clearSearch()`, "reset all" button to `resetAll()` |
| 2 | [FE] Show active view name in toolbar | FE | 1 | `chat-store.ts` — add `activeViewName: string \| null` (set by `applyView()` and pill clicks); `conversation-list.tsx` — show `"Active View: {activeViewName}"` label near pills row; clears to null after `resetAll()` or manual filter change |
| 3 | [FE] Enforce cursor reset on all filter actions | FE | 0.5 | `chat-store.ts` — audit: ensure new actions added by other stories (`setOverdueFilter`, `setChannelFilters`, `applyView`, multi-channel toggle) all include `nextCursor: null, hasMore: false` in their `set()` call; add unit test assertions |
| 4 | [BE] Tenant isolation audit for search queries | BE | 1 | `omnichat-service/src/conversations/conversations.service.ts` — verify every query path includes `WHERE tenant_id = $tenantId`; new message search from ACE-1440 must scope to tenant; `messages.service.ts` — same check; write integration test asserting tenant A search cannot return tenant B data |
| 5 | [FE] Sort affects Conversations only (not Messages) | FE | 0.5 | Enforce in `search-results-view.tsx` (ACE-1440 task 3) — sort dropdown change only calls re-fetch for conversations section, not messages section; add code comment: `// Messages section always uses relevance ordering — sort dropdown has no effect here` |

**Total: 4 SP**

### Gap vs Current Code
- ✅ AND semantics (buildApiParams) — already correct
- ✅ Cursor reset on setFilter/setSearch/setSortOrder — already done
- ✅ Stale pagination guard (baseParamsSignatureAtRequest) — already done
- ❌ No named `clearSearch()` / `resetAll()` actions (partially there via `handleClearAllFilters`)
- ❌ No active view name label
- ❌ New actions from other stories must explicitly reset cursor (needs enforcement)

---

## Full Subtask Summary

| Story | ID | Task | Layer | SP |
|---|---|---|---|---|
| ACE-1440 | SFS-01-BE-1 | [BE] Search API: grouped results (Conversations + Messages) | BE | 3 |
| ACE-1440 | SFS-01-BE-2 | [BE] Message full-text search with snippet | BE | 2 |
| ACE-1440 | SFS-01-FE-1 | [FE] Grouped search results UI | FE | 3 |
| ACE-1440 | SFS-01-FE-2 | [FE] Click message result → scroll to matched message | FE | 2 |
| ACE-1440 | SFS-01-FE-3 | [FE] Search debounce 300ms + min 2 chars | FE | 0.5 |
| ACE-1440 | SFS-01-FE-4 | [FE] "ดูทั้งหมด" load more + hide empty section | FE | 2.5 |
| ACE-1441 | SFS-02-BE-1 | [BE] Channel filter: multi-select support | BE | 1 |
| ACE-1441 | SFS-02-FE-1 | [FE] Channel filter: multi-select UI | FE | 1.5 |
| ACE-1441 | SFS-02-BE-2 | [BE] Overdue filter param (SLA-gated) | BE | 0.5 |
| ACE-1441 | SFS-02-FE-2 | [FE] Overdue filter toggle | FE | 1 |
| ACE-1441 | SFS-02-FE-3 | [FE] Channel filter chips (one per selected channel) | FE | 1 |
| ACE-1441 | SFS-02-FE-4 | [FE] Assignee filter: add specific agent option | FE | 1 |
| ACE-1442 | SFS-03-BE-1 | [BE] Sort modes: oldest_waiting + sla_due_soonest | BE | 2 |
| ACE-1442 | SFS-03-FE-1 | [FE] Sort dropdown: 3 named modes | FE | 1 |
| ACE-1442 | SFS-03-FE-2 | [FE] "New conversations available" banner | FE | 1 |
| ACE-1442 | SFS-03-FE-3 | [FE] Persist sort on back-navigation | FE | 1 |
| ACE-1450 | SFS-04-BE-1 | [BE] SavedView DB model + migration | BE | 1 |
| ACE-1450 | SFS-04-BE-2 | [BE] Saved views CRUD API | BE | 1.5 |
| ACE-1450 | SFS-04-FE-1 | [FE] System pills row (All, My Open, Unassigned…) | FE | 0.5 |
| ACE-1450 | SFS-04-FE-2 | [FE] User saved views pills + Save view dialog | FE | 1.5 |
| ACE-1450 | SFS-04-FE-3 | [FE] Manage views modal + default auto-apply | FE | 0.5 |
| ACE-1443 | SFS-05-FE-1 | [FE] Add clearSearch() and resetAll() to store | FE | 1 |
| ACE-1443 | SFS-05-FE-2 | [FE] Show active view name in toolbar | FE | 1 |
| ACE-1443 | SFS-05-FE-3 | [FE] Enforce cursor reset on all filter actions | FE | 0.5 |
| ACE-1443 | SFS-05-BE-1 | [BE] Tenant isolation audit for search queries | BE | 1 |
| ACE-1443 | SFS-05-FE-4 | [FE] Sort affects Conversations only (not Messages) | FE | 0.5 |
| ACE-1440 | MEI-01 | [INFRA] Add Meilisearch to docker-compose + env vars | INFRA | 0.5 |
| ACE-1440 | MEI-02 | [BE] SearchModule + SearchService (index/delete wrappers) | BE | 1 |
| ACE-1440 | MEI-03 | [BE] Index design + settings (conversations + messages) | BE | 0.5 |
| ACE-1440 | MEI-04 | [BE] Event hooks: sync message → Meilisearch | BE | 1 |
| ACE-1440 | MEI-05 | [BE] Backfill CLI command for existing messages per tenant | BE | 1 |
| ACE-1440 | MEI-06 | [BE] Grouped search endpoint using Meilisearch /multi-search | BE | 1.5 |
| ACE-1440 | MEI-07 | [BE] PostgreSQL fallback for grouped search (circuit breaker) | BE | 0.5 |
| ACE-1443 | MEI-08 | [BE] Daily reconciliation job (PG vs Meili doc count) | BE | 1 |
| **TOTAL** | | **34 subtasks** | | **40 SP** |
