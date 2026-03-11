# Plan: Commit 2 — Add BackoffService

## Context
Part of EPIC-ACE-33 ACE-702 (Scheduled Polling Framework). `BackoffService` is a pure utility that calculates how long to wait before retrying a failed marketplace API poll — using exponential backoff or respecting the `Retry-After` header from a `429` response.

## Commit Message
```text
feat(omnichat-service): add BackoffService for exponential and rate-limit backoff
```

## File to Create
`ace/apps/omnichat-service/src/polling/backoff.service.ts`

Pure `@Injectable()` service — no constructor dependencies.

## Methods

| Method | Signature | Logic |
| :--- | :--- | :--- |
| `calculateBackoffMs` | `(failures: number): number` | `min(60_000 × 2^(failures-1), 960_000)` |
| `calculateRateLimitBackoffMs` | `(retryAfterSec: number, failures: number): number` | `retryAfterSec > 0 → retryAfterSec * 1000`, else fall back to `calculateBackoffMs(failures)` |
| `getBackoffUntil` | `(backoffMs: number): Date` | `new Date(Date.now() + backoffMs)` |

## Backoff table
- failure 1 → 60,000 ms (1 min)
- failure 2 → 120,000 ms (2 min)
- failure 3 → 240,000 ms (4 min)
- failure 4 → 480,000 ms (8 min)
- failure 5+ → 960,000 ms (16 min, capped)

**Note:** No module file needed yet — `BackoffService` will be registered in `PollingModule` in Commit 6.

## Patterns to Follow
- Service style: matches existing services (e.g., `ace/apps/omnichat-service/src/credentials/credentials.service.ts`)
- `@Injectable()` decorator, no constructor args needed

## Verification
- `pnpm --filter omnichat-service build` — TypeScript compiles without errors