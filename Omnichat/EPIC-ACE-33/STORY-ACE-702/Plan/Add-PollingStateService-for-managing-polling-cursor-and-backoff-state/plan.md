# Plan: Commit 3 — Add PollingStateService

## Context
Part of EPIC-ACE-33 ACE-702. `PollingStateService` manages the `MarketplacePollingState` DB records — tracking polling cursors (`last_fetch_at`) and backoff state. It is the primary persistence layer used by the orchestrator (Commit 5) to decide whether to skip an account and to record poll outcomes.

## Commit Message
```text
feat(omnichat-service): add PollingStateService for managing polling cursor and backoff state
```

## File to Create
`ace/apps/omnichat-service/src/polling/polling-state.service.ts`

Depends on: `PrismaService` (injected via constructor).

## Methods

| Method | Logic |
| :--- | :--- |
| `getState(accountId, pollType)` | `findUnique` by `@@unique(channel_account_id, poll_type)` |
| `isInBackoff(accountId, pollType): Promise<boolean>` | `state.backoff_until > new Date()` |
| `markSuccess(accountId, pollType, lastEventAt)` | upsert: `consecutive_failures=0`, `backoff_until=null`, `last_fetch_at=lastEventAt` |
| `markFailure(accountId, pollType, error, backoffUntil)` | upsert: `consecutive_failures: { increment: 1 }`, `backoff_until`, `last_error=error.message` |

Prisma compound key accessor: `channel_account_id_poll_type` (auto-generated from `@@unique`).

## Patterns to Follow
- `private prisma: PrismaService` injection — matches existing services (e.g., `src/channel-accounts/channel-accounts.service.ts`)
- Import from `'../prisma/prisma.service'`

## Verification
- `pnpm --filter omnichat-service build` — TypeScript compiles without errors