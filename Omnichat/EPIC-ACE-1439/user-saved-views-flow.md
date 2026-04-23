# User Saved Views — High-Level Implementation Flow

## Overview

Per-user named filter+sort snapshots ("saved views") displayed as pill buttons above the conversation list, enabling agents to switch working modes in one click.

---

## Architecture Layers

```
┌──────────────────────────────────────────────────────────────┐
│  Frontend (Next.js 16 App Router)                            │
│  workspace-admin                                             │
│                                                              │
│  ConversationList                                            │
│    └── SavedViewsPillRow        ← 6 system pills +          │
│          ├── [System Pills]        up to 14 user views       │
│          └── [User Saved Views]                              │
│                                                              │
│  Modals                                                      │
│    ├── SaveViewModal            ← capture current filters    │
│    └── ManageViewsModal         ← delete / set default only  │
│                                                              │
│  State                                                       │
│    ├── saved-views-store (Zustand)  ← CRUD + active pill    │
│    └── chat-store.applyViewSnapshot ← apply to nuqs params  │
│                                                              │
│  API Layer                                                   │
│    └── saved-views.api.ts       ← server actions → gateway  │
└─────────────────────┬────────────────────────────────────────┘
                      │ HTTP REST
┌─────────────────────▼────────────────────────────────────────┐
│  API Gateway (NestJS)                                        │
│  api-gateway                                                 │
│                                                              │
│  SavedViewsController  GET/POST/PATCH/DELETE /saved-views    │
│  SavedViewsService     ← HTTP proxy                          │
└─────────────────────┬────────────────────────────────────────┘
                      │ HTTP (internal)
┌─────────────────────▼────────────────────────────────────────┐
│  Omnichat Service (NestJS)                                   │
│  omnichat-service                                            │
│                                                              │
│  SavedViewsController  REST endpoints                        │
│  SavedViewsService     business logic                        │
│    ├── max 14 views per user                                 │
│    ├── unique name per user                                  │
│    └── default-view swap (atomic transaction)                │
│  DTOs + class-validator                                      │
└─────────────────────┬────────────────────────────────────────┘
                      │ Prisma ORM
┌─────────────────────▼────────────────────────────────────────┐
│  PostgreSQL                                                  │
│  user_saved_views table                                      │
│  (tenant_id, agent_id, name, snapshot JSON, is_default)      │
└──────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Save a View
```
User clicks "Save View"
  → SaveViewModal opens (pre-fills current filter/sort state from nuqs)
  → User enters name, optionally includes search query
  → Submit → saved-views.api.ts (server action)
    → POST /v1/omnichat/saved-views (api-gateway)
      → POST /saved-views (omnichat-service)
        → validate: max 14 check, duplicate name check
        → Prisma: INSERT INTO user_saved_views
  → saved-views-store refreshes list
  → New pill appears in SavedViewsPillRow
```

### Apply a View
```
User clicks a pill
  → saved-views-store sets activePillId
  → chat-store.applyViewSnapshot(snapshot)
    → updates nuqs URL params (status, channel, assignee, tag, sort, q, is_overdue)
  → ConversationList re-fetches with new filters
```

### Default View on Mount
```
ConversationList mounts
  → saved-views-store.fetchViews() fetches all saved views
  → check: all URL params are at defaults (clean state)?
    → yes: find view with is_default=true → auto-apply snapshot
    → no: skip (user has active filters from URL)
```

### Manage Views
```
User opens ManageViewsModal
  → lists all saved views
  → Set Default → PATCH /saved-views/:id { is_default: true }
    → service atomically clears old default, sets new
  → Delete → DELETE /saved-views/:id
    → if deleted view was default → activePillId resets to system:all
  → saved-views-store refreshes, pill row updates
  (NO rename — UpdateSavedViewDto only contains is_default)
```

---

## Implementation Tasks (16 Steps)

| # | Layer | Task |
|---|-------|------|
| 0 | omnichat-service | Add `is_overdue` filter to `ListConversationsDto` + `conversations.service.ts` |
| 1 | Database | Add `UserSavedView` Prisma model + migrate |
| 2 | omnichat-service | Create DTOs (create / list / update / delete) |
| 3 | omnichat-service | `SavedViewsService` with business logic + unit tests |
| 4 | omnichat-service | `SavedViewsController` REST endpoints + unit tests |
| 5 | omnichat-service | `SavedViewsModule` + register in `AppModule` |
| 6 | api-gateway | Create gateway DTOs |
| 7 | api-gateway | `SavedViewsService` (HTTP proxy to omnichat-service) |
| 8 | api-gateway | `SavedViewsController` + register in `OmnichatModule` |
| 9 | Frontend | Types: `ViewSnapshot`, `SavedView`, `SystemPill` + `SYSTEM_PILLS` constants |
| 10 | Frontend | Server actions (`saved-views.api.ts`) |
| 11 | Frontend | Zustand store + `chat-store.applyViewSnapshot` action |
| 12 | Frontend | `SaveViewModal` component (React Hook Form + Zod, Thai UI) |
| 13 | Frontend | `ManageViewsModal` component (delete + set default only) |
| 14 | Frontend | `SavedViewsPillRow` component (system + user pills + save button) |
| 15 | Frontend | Wire `SavedViewsPillRow` into `ConversationList` + `is_overdue` nuqs param + default-view auto-apply |

---

## ViewSnapshot Shape

```typescript
type ViewSnapshot = {
  status:     string;  // e.g. "open,in_progress" — comma-separated ConversationStatus
  channel:    string;  // e.g. "line,facebook"    — comma-separated ChannelType
  assignee:   string;  // "" | "me" | "none"
  tag:        string;  // comma-separated tag UUIDs
  sort:       string;  // "latest_activity" | "oldest_waiting" | "sla_due_soonest"
  q:          string;  // search text (empty when not included at save time)
  is_overdue: string;  // "true" | "" — used by the "overdue" system pill
}
```

Snapshot mirrors nuqs URL params 1:1, so applying a view is just setting URL state — no custom mapping needed.

---

## Key Business Rules

- Max **14** user-created views per user (6 system + 14 = **20 total visible pills**) — enforced in `SavedViewsService` + UI disables button at limit
- View **name must be unique** per user (tenant + agent scope) — DB `@@unique` + service `ConflictException` + optimistic client-side check
- Only **one default** view at a time — swap is done atomically in a `$transaction`
- Soft-delete via `deleted_at` — views are never hard-deleted from DB; deleting a default resets `is_default=false`
- **No rename** — `UpdateSavedViewDto` contains `is_default` only; `ManageViewsModal` has delete + set-default only
- System pills (`all`, `my open`, `unassigned`, `in progress`, `pending`, `overdue`) are **client-side constants** (`SYSTEM_PILLS`), never stored in DB
- `is_overdue` filter on backend: `sla_due_at < NOW()` with status in `(open, in_progress, pending)`
