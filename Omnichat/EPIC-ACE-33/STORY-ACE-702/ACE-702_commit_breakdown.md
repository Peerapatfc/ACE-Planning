# ACE-702 — Commit Breakdown: Scheduled Polling Framework v1

**Story:** STORY-MKT-02: Scheduled Polling Framework v1 for Marketplace Ingest
**Epic:** EPIC-ACE-33
**Date:** 2026-03-10

---

## Commit Order

```
1 (schema) → 2 (backoff) → 3 (state) → 4 (interface/registry)
    → 5 (orchestrator) → 6 (module) → 7 (gateway)
    → 8 (tests)
```

> Commits 2–4 can be done in parallel (no dependencies between them)
> Commit 5 depends on all of 2–4

---

## `apps/omnichat-service` — 6 commits

### Commit 1
```
chore(omnichat-service): add MarketplacePollingState schema and migration
```
**Files:**
- `apps/omnichat-service/prisma/schema.prisma` — add `MarketplacePollingState` model, `polling_states` relation on `ChannelAccount`, `@@unique([channel_account_id, poll_type])`, `@@index([backoff_until])`
- `apps/omnichat-service/prisma/migrations/...` — migration file

---

### Commit 2
```
feat(omnichat-service): add BackoffService for exponential and rate-limit backoff
```
**Files:**
- `apps/omnichat-service/src/polling/backoff.service.ts`

**Methods:**
| Method | Description |
|--------|-------------|
| `calculateBackoffMs(failures: number): number` | Exponential: `60,000 × 2^(failures-1)`, capped at 16 min |
| `calculateRateLimitBackoffMs(retryAfterSec: number, failures: number): number` | Uses value from `Retry-After` header |
| `getBackoffUntil(backoffMs: number): Date` | Returns `now + backoffMs` |

---

### Commit 3
```
feat(omnichat-service): add PollingStateService for managing polling cursor and backoff state
```
**Files:**
- `apps/omnichat-service/src/polling/polling-state.service.ts`

**Methods:**
| Method | Description |
|--------|-------------|
| `getState(accountId, pollType)` | `findUnique` MarketplacePollingState |
| `isInBackoff(accountId, pollType): Promise<boolean>` | Checks if `backoff_until > now` |
| `markSuccess(accountId, pollType, lastEventAt)` | UPSERT: reset `consecutive_failures=0`, `backoff_until=NULL`, update `last_fetch_at` |
| `markFailure(accountId, pollType, error, backoffUntil)` | UPSERT: increment `consecutive_failures`, set `backoff_until`, set `last_error` |

---

### Commit 4
```
feat(omnichat-service): define IMarketplacePoller interface and PollingRegistry
```
**Files:**
- `apps/omnichat-service/src/polling/interfaces/marketplace-poller.interface.ts` — `IMarketplacePoller`, `PollingContext`, `PollingOutcome`
- `apps/omnichat-service/src/polling/polling.registry.ts` — maps `channel_type → IMarketplacePoller`

**Types:**
```typescript
interface PollingContext {
  since: Date;          // last_fetch_at ?? (now - 5min)
  tenantId: string;
  fetchBatchId: string; // uuid
}

interface PollingOutcome {
  itemsIngested: number;
  rateLimited: boolean;
  retryAfterMs?: number;
}

interface IMarketplacePoller {
  poll(account: ChannelAccount, context: PollingContext): Promise<PollingOutcome>;
}
```

---

### Commit 5
```
feat(omnichat-service): add PollingOrchestratorService with @Cron scheduler
```
**Files:**
- `apps/omnichat-service/src/polling/polling-orchestrator.service.ts`

**Flow:**
1. `@Cron(POLLING_CRON_EXPRESSION)` triggers `runCycle()`
2. Load active marketplace accounts (`status=active`, `connection_status=connected`, `channel_type IN (shopee, lazada, tiktok)`)
3. Split accounts into chunks based on `POLLING_CONCURRENCY_LIMIT` (default: 10)
4. Per account per pollType (`chat`, `order`):
   - Check `isInBackoff` → skip if true
   - Get `last_fetch_at` → build `PollingContext`
   - Call `poller.poll(account, context)`
   - Success → `markSuccess`
   - Rate limited → `markFailure` (using `Retry-After`)
   - Error → `markFailure` (exponential backoff)
5. Log summary: `accounts, ingested, failures, durationMs`

---

### Commit 6
```
feat(omnichat-service): wire PollingModule and register ScheduleModule
```
**Files:**
- `apps/omnichat-service/src/polling/polling.module.ts` — declare providers: `PollingOrchestratorService`, `PollingStateService`, `BackoffService`, `PollingRegistry`
- `apps/omnichat-service/src/app.module.ts` — import `ScheduleModule.forRoot()`, import `PollingModule`

---

## `apps/omnichat-gateway` — 1 commit

### Commit 7
```
feat(omnichat-gateway): add TCP handler for enqueue_polled_messages command
```
**Files:**
- `apps/omnichat-gateway/src/polling/polling.controller.ts` (or handler in existing gateway controller)

**Behavior:**
- `@MessagePattern('enqueue_polled_messages')`
- Receives `RawWebhookMessage[]` payload
- Forwards to SQS FIFO (`MessageGroupId: {platform}-{channelId}-{sourceUserId}`)
- Returns ack

---

## Tests — 1 commit

### Commit 8
```
test(omnichat-service): add unit tests for BackoffService, PollingStateService, and PollingOrchestratorService
```
**Files:**
- `apps/omnichat-service/src/polling/backoff.service.spec.ts`
- `apps/omnichat-service/src/polling/polling-state.service.spec.ts`
- `apps/omnichat-service/src/polling/polling-orchestrator.service.spec.ts`

**Test cases to cover:**
| Service | Case |
|---------|------|
| `BackoffService` | `failures=1` → 1 min, `failures=5+` → 16 min (cap), rate-limit uses Retry-After header |
| `PollingStateService` | `isInBackoff` → true/false based on timestamp, `markSuccess` resets failures, `markFailure` increments failures |
| `PollingOrchestratorService` | skips accounts in backoff, `Promise.allSettled` does not crash when poller throws, log summary is correct |
