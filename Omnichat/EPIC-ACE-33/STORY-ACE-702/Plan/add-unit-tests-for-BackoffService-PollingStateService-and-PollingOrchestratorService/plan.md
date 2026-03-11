# Plan: Commit 8 — Unit tests for BackoffService, PollingStateService, PollingOrchestratorService

## Context
Part of EPIC-ACE-33 ACE-702. Validates the core polling logic — backoff math, state persistence, and orchestrator flow — before marketplace connectors are added.

## Commit Message
`test(omnichat-service): add unit tests for BackoffService, PollingStateService, and PollingOrchestratorService`

## Files to Create

### 1. `ace/apps/omnichat-service/src/polling/backoff.service.spec.ts`
Pure unit tests — no mocks needed (no dependencies).

| Test | Assertion |
|---|---|
| `calculateBackoffMs(1)` | `= 60_000` |
| `calculateBackoffMs(2)` | `= 120_000` |
| `calculateBackoffMs(3)` | `= 240_000` |
| `calculateBackoffMs(4)` | `= 480_000` |
| `calculateBackoffMs(5)` | `= 960_000` (cap) |
| `calculateBackoffMs(10)` | `= 960_000` (still cap) |
| `calculateRateLimitBackoffMs(30, 1)` | `= 30_000` (uses header) |
| `calculateRateLimitBackoffMs(0, 5)` | `= 960_000` (fallback to exponential) |
| `getBackoffUntil(60_000)` | `≈ new Date(Date.now() + 60_000)` |

### 2. `ace/apps/omnichat-service/src/polling/polling-state.service.spec.ts`
Mock `PrismaService.marketplacePollingState` with `jest.fn()`.

| Test | Setup | Assertion |
|---|---|---|
| `getState` — found | `findUnique` resolves state | returns state |
| `getState` — not found | `findUnique` resolves null | returns null |
| `isInBackoff` — null state | `findUnique` → null | false |
| `isInBackoff` — null `backoff_until` | state has `backoff_until: null` | false |
| `isInBackoff` — past `backoff_until` | `backoff_until` = yesterday | false |
| `isInBackoff` — future `backoff_until` | `backoff_until` = tomorrow | true |
| `markSuccess` | `upsert` called | correct update/create payload: `consecutive_failures=0`, `backoff_until=null` |
| `markFailure` | `upsert` called | correct payload: `consecutive_failures: { increment: 1 }`, `backoff_until`, `last_error=error.message` |

### 3. `ace/apps/omnichat-service/src/polling/polling-orchestrator.service.spec.ts`
Mock: `PrismaService`, `PollingStateService`, `BackoffService`, `PollingRegistry`, `ConfigService`, and `Logger` (spy to suppress).

| Test | Setup | Assertion |
|---|---|---|
| `runCycle` — no accounts | `findMany` → `[]` | returns early, no poller called |
| `runCycle` — Promise.allSettled absorbs error | one account poller throws | other account still processed, no unhandled throw |
| `runCycle` — accumulates counts | 2 accounts, 2 poll types each succeed | log shows correct ingested / failures |
| `pollAccount` — in backoff | `isInBackoff` → true | returns `{itemsIngested:0, rateLimited:false}`, poller NOT called |
| `pollAccount` — poller throws | poller rejects | `markFailure` called with exponential backoff, error re-thrown |
| `pollAccount` — rate-limited | `outcome.rateLimited=true`, `retryAfterMs=60000` | `markFailure` called with rate-limit backoff |
| `pollAccount` — success | `outcome={itemsIngested:3, rateLimited:false}` | `markSuccess` called, returns outcome |

## Patterns to Follow
* Module setup: `Test.createTestingModule({ providers: [...] }).compile()` — same as `queue.service.spec.ts`
* Prisma mock: `{ marketplacePollingState: { findUnique: jest.fn(), upsert: jest.fn() }, channelAccount: { findMany: jest.fn() } }`
* `jest.clearAllMocks()` in `beforeEach`
* Suppress Logger: `jest.spyOn(Logger.prototype, 'log').mockImplementation()`
* Helper: `createMockAccount(overrides?)` for test fixtures

## Verification
* `pnpm --filter omnichat-service test` — all tests pass
* `pnpm --filter omnichat-service test:cov` — polling/ coverage visible