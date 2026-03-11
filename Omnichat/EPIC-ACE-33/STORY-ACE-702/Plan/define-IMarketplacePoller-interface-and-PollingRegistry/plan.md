# Plan: Commit 4 — IMarketplacePoller interface and PollingRegistry

## Context
Part of EPIC-ACE-33 ACE-702. Defines the contract that all marketplace pollers (TikTok, Shopee, Lazada — coming in ACE-703/704/705) must implement, and the registry that the orchestrator (Commit 5) uses to look up the correct poller by `channel_type`.

## Commit Message
```text
feat(omnichat-service): define IMarketplacePoller interface and PollingRegistry
```

## Files to Create

### 1. `ace/apps/omnichat-service/src/polling/interfaces/marketplace-poller.interface.ts`

```typescript
import { ChannelAccount } from '../../generated/prisma/client';

export interface PollingContext {
  since: Date;           // last_fetch_at ?? (now - 5min)
  tenantId: string;
  fetchBatchId: string;  // uuid
}

export interface PollingOutcome {
  itemsIngested: number;
  rateLimited: boolean;
  retryAfterMs?: number;
}

export interface IMarketplacePoller {
  poll(account: ChannelAccount, context: PollingContext): Promise<PollingOutcome>;
}
```

### 2. `ace/apps/omnichat-service/src/polling/polling.registry.ts`
`@Injectable()` class with `register()` + `get()` methods.

- No constructor args — no concrete poller implementations exist yet (ACE-703/704/705)
- `register(channelType, poller)` — used by `PollingModule` in Commit 6
- `get(channelType)` — throws `NotFoundException` if not registered
- Uses `ChannelType` enum from `../../channel-accounts/types`.

## Patterns to Follow
- Mirror `StrategyRegistry` at `src/channel-accounts/strategies/strategy.registry.ts`
- Interface file mirrors `src/channel-accounts/strategies/account-channel.strategy.ts`
- Import `ChannelAccount` from `../../generated/prisma/client` (same path pattern used elsewhere)

## Verification
- `pnpm --filter omnichat-service build` — TypeScript compiles without errors