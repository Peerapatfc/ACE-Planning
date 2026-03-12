# ACE-702: Scheduled Polling Framework v1 — Implementation Plan

## Context
ACE-702 builds the core scheduled polling infrastructure for marketplace channels (Shopee, Lazada, TikTok). These channels don't support inbound webhooks, so the system must periodically pull chat messages via their APIs. This story delivers the framework only — the actual API calls per marketplace are implemented in ACE-1256/1257/1258.

## Scope (ACE-702 only)

| In Scope | Out of Scope |
| :--- | :--- |
| Polling orchestrator with `@Cron` | Actual Shopee/Lazada/TikTok API calls (ACE-1256/57/58) |
| `PollingStateService` (`last_fetch_at`, `backoff`) | Mapper implementations in `normalizer-worker` |
| `BackoffService` (exponential + rate-limit) | Order polling (`poll_type=order`) |
| `IMarketplacePoller` interface + `PollingRegistry` | CI/CD / deployment |
| Prisma schema: `MarketplacePollingState` | |
| Gateway TCP endpoint: `enqueue_polled_messages` | |
| Stub pollers (return empty results, compile & wire correctly) | |

## Codebase State (Current)
- **`omnichat-service`**: Has `ChannelAccount`, `CredentialsService`, no scheduler (`@nestjs/schedule` not installed)
- **`omnichat-gateway`**: HTTP-only (port 3001) — has `QueueService` for SQS but NO TCP server
- **`packages/config`**: Has SQS config, no polling-specific config
- **`packages/shared`**: Has `CHANNEL_TYPES` constant (includes shopee/lazada/tiktok), no `RawWebhookMessage` type in shared (lives in gateway's `webhook-message.dto.ts`)
- **`MarketplacePollingState`**: NOT in `schema.prisma` yet (generated files exist from an old attempt but schema is clean)

## Implementation Steps

### Step 1 — Prisma Schema (`omnichat-service`)
**File:** `ace/apps/omnichat-service/prisma/schema.prisma`

Add to `ChannelAccount` model:
```prisma
polling_states MarketplacePollingState[]
```

Add new model:
```prisma
model MarketplacePollingState {
  id                   String    @id @default(uuid())
  channel_account_id   String
  poll_type            String    // "chat" | "order"
  last_fetch_at        DateTime?
  backoff_until        DateTime?
  consecutive_failures Int       @default(0)
  last_error           String?
  created_at           DateTime  @default(now())
  updated_at           DateTime  @updatedAt

  channel_account ChannelAccount @relation(fields: [channel_account_id], references: [id])

  @@unique([channel_account_id, poll_type])
  @@index([backoff_until])
  @@map("marketplace_polling_states")
}
```
Then run: `pnpm --filter omnichat-service prisma migrate dev --name add_marketplace_polling_state`

### Step 2 — Install `@nestjs/schedule` in `omnichat-service`
```bash
pnpm --filter omnichat-service add @nestjs/schedule
```

### Step 3 — Polling Config (`packages/config`)
**File:** `ace/packages/config/src/configuration.ts`

Add to config object:
```typescript
marketplacePolling: {
  cronExpression: process.env.POLLING_CRON_EXPRESSION ?? '0 */5 * * * *', // every 5 min
  concurrencyLimit: parseInt(process.env.POLLING_CONCURRENCY_LIMIT ?? '10'),
  defaultLookbackMs: parseInt(process.env.POLLING_DEFAULT_LOOKBACK_MS ?? '300000'), // 5 min
  backoff: {
    baseMs: parseInt(process.env.POLLING_BACKOFF_BASE_MS ?? '60000'),
    maxMs: parseInt(process.env.POLLING_BACKOFF_MAX_MS ?? '960000'), // 16 min
  },
},
```

### Step 4 — New Module: `marketplace-polling` (`omnichat-service`)
**Directory:** `ace/apps/omnichat-service/src/marketplace-polling/`

#### 4a. Interface + Types
**File:** `interfaces/marketplace-poller.interface.ts`
```typescript
export interface PollingContext {
  since: Date;
  accountId: string;
  tenantId: string;
}

export interface PollingOutcome {
  itemsIngested: number;
  rateLimited: boolean;
  retryAfterMs?: number;
}

export interface IMarketplacePoller {
  readonly channelType: string; // 'shopee' | 'lazada' | 'tiktok'
  poll(account: ChannelAccount, context: PollingContext): Promise<PollingOutcome>;
}
```

#### 4b. PollingRegistry
**File:** `registry/polling-registry.ts`
- Simple `Map<string, IMarketplacePoller>`
- `register(poller: IMarketplacePoller)` — called in module factory
- `get(channelType: string)` — returns poller or undefined

#### 4c. BackoffService
**File:** `services/backoff.service.ts`
- `calculateBackoffMs(consecutiveFailures: number): number` — baseMs × 2^(n-1), capped at maxMs
- `calculateRateLimitBackoffMs(retryAfterSec: number, consecutiveFailures: number): number` — use Retry-After header value directly
- `getBackoffUntil(backoffMs: number): Date` — new Date(Date.now() + backoffMs)

#### 4d. PollingStateService
**File:** `services/polling-state.service.ts`
Uses `PrismaService`. Methods:
- `getState(accountId, pollType)` → `MarketplacePollingState | null`
- `isInBackoff(accountId, pollType)` → `boolean` (check backoff_until > now)
- `markSuccess(accountId, pollType, lastEventAt: Date | null)` → upsert: set `last_fetch_at`, reset `consecutive_failures=0`, `backoff_until=null`
- `markFailure(accountId, pollType, error: string, backoffUntil: Date)` → upsert: increment `consecutive_failures++`, set `backoff_until`, `last_error`

#### 4e. PollingOrchestratorService
**File:** `services/polling-orchestrator.service.ts`
```typescript
@Injectable()
export class PollingOrchestratorService {
  @Cron(configService.get('marketplacePolling.cronExpression'))
  async runCycle(): Promise<void> {
    // 1. Load active marketplace accounts (shopee, lazada, tiktok only)
    // 2. Chunk into CONCURRENCY_LIMIT batches
    // 3. Promise.allSettled per chunk
    //    For each account × ['chat']:
    //      a. isInBackoff? → skip
    //      b. getState → build PollingContext (since = last_fetch_at ?? now - lookback)
    //      c. registry.get(channel_type).poll(account, context)
    //      d. outcome.rateLimited → markFailure with rate-limit backoff
    //      e. success → markSuccess(lastEventAt)
    //      f. error thrown → markFailure with exponential backoff
    // 4. Log summary
  }
}
```
**Key behaviors:**
- `Promise.allSettled` at chunk level — one account failure doesn't crash the cycle
- Each account error is caught individually → `markFailure` → continue
- Summary log: `{ accounts: N, ingested: X, skipped: Y, failures: Z, durationMs: W }`

#### 4f. Stub Pollers (to be filled in ACE-1256/57/58)
- `pollers/shopee-poller.ts` — implements `IMarketplacePoller`, `poll()` returns `{ itemsIngested: 0, rateLimited: false }`
- `pollers/lazada-poller.ts` — same stub
- `pollers/tiktok-poller.ts` — same stub

#### 4g. MarketplacePollingModule
**File:** `marketplace-polling.module.ts`
```typescript
@Module({
  imports: [
    ScheduleModule.forRoot(),    // only here, not in AppModule
    PrismaModule,
    CredentialsModule,
    ClientsModule.registerAsync([{
      name: 'OMNICHAT_GATEWAY',
      transport: Transport.TCP,
      options: { host: gatewayTcpHost, port: gatewayTcpPort }
    }]),
  ],
  providers: [
    BackoffService,
    PollingStateService,
    ShopeePoller,
    LazadaPoller,
    TiktokPoller,
    {
      provide: PollingRegistry,
      useFactory: (shopee, lazada, tiktok) => {
        const r = new PollingRegistry();
        [shopee, lazada, tiktok].forEach(p => r.register(p));
        return r;
      },
      inject: [ShopeePoller, LazadaPoller, TiktokPoller],
    },
    PollingOrchestratorService,
  ],
})
export class MarketplacePollingModule {}
```
*Note on TCP client:* The orchestrator itself doesn't call the gateway — individual pollers do (they receive the TCP client via injection). This keeps orchestrator agnostic of transport.

### Step 5 — Update `app.module.ts` (`omnichat-service`)
**File:** `ace/apps/omnichat-service/src/app.module.ts`
Add `MarketplacePollingModule` to imports array.

### Step 6 — Gateway TCP Server + Enqueue Handler (`omnichat-gateway`)
#### 6a. Add TCP microservice to gateway `main.ts`
**File:** `ace/apps/omnichat-gateway/src/main.ts`
```typescript
app.connectMicroservice<MicroserviceOptions>({
  transport: Transport.TCP,
  options: {
    host: configService.get('shared.omnichatGateway.tcp.host'),
    port: configService.get('shared.omnichatGateway.tcp.tcp_port'), // new config key
  },
});
await app.startAllMicroservices();
```

#### 6b. New polling module in gateway
**File:** `ace/apps/omnichat-gateway/src/polling/polling.module.ts`
**File:** `ace/apps/omnichat-gateway/src/polling/polling-enqueue.controller.ts`
```typescript
@Controller()
export class PollingEnqueueController {
  constructor(private readonly queueService: QueueService) {}

  @MessagePattern({ cmd: 'enqueue_polled_messages' })
  async enqueuePolledMessages(
    @Payload() messages: RawWebhookMessage[],
  ): Promise<{ enqueued: number }> {
    let enqueued = 0;
    for (const message of messages) {
      await this.queueService.sendMessage(message);
      enqueued++;
    }
    return { enqueued };
  }
}
```

#### 6c. Add gateway TCP port to `packages/config`
**File:** `ace/packages/config/src/configuration.ts`
Add `omnichatGateway.tcp_port` (e.g., 4001) to shared config.

#### 6d. Update gateway `app.module.ts`
Import `PollingModule`.

### Step 7 — `RawWebhookMessage` type alignment
**File:** `ace/apps/omnichat-gateway/src/webhook/dto/webhook-message.dto.ts`
Verify `source_category` and `fetch_batch_id` fields are present (from exploration, `RawEvent` model has these fields). Add to the interface if missing.

## Files to Create/Modify Summary

| File | Action |
| :--- | :--- |
| `omnichat-service/prisma/schema.prisma` | Add `MarketplacePollingState` + relation |
| `omnichat-service/src/marketplace-polling/interfaces/marketplace-poller.interface.ts` | CREATE |
| `omnichat-service/src/marketplace-polling/registry/polling-registry.ts` | CREATE |
| `omnichat-service/src/marketplace-polling/services/backoff.service.ts` | CREATE |
| `omnichat-service/src/marketplace-polling/services/polling-state.service.ts` | CREATE |
| `omnichat-service/src/marketplace-polling/services/polling-orchestrator.service.ts` | CREATE |
| `omnichat-service/src/marketplace-polling/pollers/shopee-poller.ts` | CREATE (stub) |
| `omnichat-service/src/marketplace-polling/pollers/lazada-poller.ts` | CREATE (stub) |
| `omnichat-service/src/marketplace-polling/pollers/tiktok-poller.ts` | CREATE (stub) |
| `omnichat-service/src/marketplace-polling/marketplace-polling.module.ts` | CREATE |
| `omnichat-service/src/app.module.ts` | MODIFY — add `MarketplacePollingModule` |
| `omnichat-gateway/src/main.ts` | MODIFY — add TCP server |
| `omnichat-gateway/src/polling/polling.module.ts` | CREATE |
| `omnichat-gateway/src/polling/polling-enqueue.controller.ts` | CREATE |
| `omnichat-gateway/src/app.module.ts` | MODIFY — add `PollingModule` |
| `packages/config/src/configuration.ts` | MODIFY — add polling config + gateway TCP port |

## Reuse Points (Existing Code)

| What to reuse | Location |
| :--- | :--- |
| `CredentialsService.getDecryptedCredential()` | `omnichat-service/src/credentials/services/credentials.service.ts` |
| `PrismaService` | `omnichat-service/src/prisma/prisma.service.ts` |
| `QueueService.sendMessage()` | `omnichat-gateway/src/queue/queue.service.ts` |
| `RawWebhookMessage` interface | `omnichat-gateway/src/webhook/dto/webhook-message.dto.ts` |
| Strategy pattern (`PollingRegistry` mirrors `StrategyRegistry`) | `omnichat-service/src/channel-accounts/strategies/strategy.registry.ts` |
| TCP client pattern | `omnichat-normalizer-worker/src/worker/omnichat-api-client/omnichat-api-client.service.ts` |

## Verification Plan
1. **Unit tests — `BackoffService`**: test `calculateBackoffMs(1..5)` returns `60s→120s→240s→480s→960s` (capped)
2. **Unit tests — `PollingStateService`**: mock Prisma, test `markSuccess` resets failures, test `isInBackoff` returns correct boolean
3. **Integration smoke test**:
   - Create a Shopee `ChannelAccount` with `status=active`, `connection_status=connected`
   - Wait for cron cycle or call `runCycle()` directly in test
   - Verify `MarketplacePollingState` record is created with `consecutive_failures=0`
   - **Backoff test:** Manually set `backoff_until = now + 1h` → run cycle → verify account is skipped (no API call)
   - **Gateway TCP test:** Call `enqueue_polled_messages` via TCP with stub payload → verify message appears in SQS (LocalStack)
4. **Build check**: `pnpm --filter omnichat-service build` and `pnpm --filter omnichat-gateway build` pass with no TypeScript errors