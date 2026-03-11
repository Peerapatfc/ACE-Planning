# Plan: Commit 5 — Add PollingOrchestratorService

## Context
Part of EPIC-ACE-33 ACE-702. The orchestrator is the heart of the polling framework — a cron-driven service that every 5 minutes loads active marketplace accounts, checks backoff state, calls the correct poller via PollingRegistry, and records success/failure via PollingStateService.

## Commit Message
`feat(omnichat-service): add PollingOrchestratorService with @Cron scheduler`

## File to Create
`ace/apps/omnichat-service/src/polling/polling-orchestrator.service.ts`
Dependencies injected: `PrismaService`, `PollingStateService`, `BackoffService`, `PollingRegistry`, `ConfigService`

### Key design decisions:

* `@Cron('0 */5 * * * *')` on `runCycle()`
* Active marketplace accounts: `status='active'`, `connection_status='connected'`, `channel_type IN ['tiktok','shopee','lazada']`, `deleted_at=null`
* Poll types per account: `['chat', 'order']`
* Concurrency: `Promise.allSettled()` on chunks of 10 (configurable via `polling.concurrencyLimit`)
* Default `since`: now - 5min when no prior `last_fetch_at`
* `fetchBatchId`: `crypto.randomUUID()`

### Logic flow for each account+pollType:

1. `isInBackoff()` → skip if true
2. `getState()` → `since` = `last_fetch_at` ?? now-5min
3. `pollingRegistry.get(channel_type).poll(account, context)`
4. On success → `markSuccess(accountId, pollType, new Date())`
5. On rate-limit (`outcome.rateLimited && outcome.retryAfterMs`) → `markFailure()` with `calculateRateLimitBackoffMs(retryAfterMs/1000, failures)`
6. On thrown error → `markFailure()` with `calculateBackoffMs(failures+1)`

Note: `@Cron` is imported from `@nestjs/schedule` which is not yet installed — Commit 6 installs the package and adds `ScheduleModule.forRoot()`.

## Methods Summary

| Method | Visibility | Description |
|---|---|---|
| `runCycle()` | public @Cron | Main entry — loads accounts, chunks, processes all |
| `getActiveMarketplaceAccounts()` | private | `prisma.channelAccount.findMany(...)` |
| `chunkAccounts(accounts, size)` | private | Splits array into chunks |
| `processAccount(account)` | private | Iterates poll types, calls `pollAccount`, returns `{ingested, failures}` |
| `pollAccount(account, pollType)` | private | Full backoff-check → poll → outcome-handle flow |
| `getDefaultSince()` | private | `new Date(Date.now() - 5 * 60 * 1000)` |

## Patterns to Follow
* Logger: `private readonly logger = new Logger(PollingOrchestratorService.name)`
* Channel type strings: lowercase enum values `'tiktok'`, `'shopee'`, `'lazada'` (matching `ChannelType` enum values)
* `markFailure` takes `Error` object — wrap string messages in `new Error(...)`
* `PollingRegistry.get()` already throws `NotFoundException` — no null-check needed

## Verification
`pnpm --filter omnichat-service build` — after Commit 6 installs `@nestjs/schedule`