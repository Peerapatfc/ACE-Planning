# Plan: TikTok Scheduled Polling — fetch Chat Messages & enqueue for normalization

## Context
Task `86d271eun` (subtask of STORY-MKT-02) requires replacing the `TiktokPoller` stub with a real implementation that:
- Calls TikTok Shop API v2 to fetch chat messages since the last successful poll
- Publishes each message as a `RawWebhookMessage` to the SQS queue consumed by `omnichat-normalizer-worker`

The polling framework (orchestrator, state, backoff, registry) is already complete. Only the TikTok-specific pieces are missing.

## Architecture Overview
```text
PollingOrchestratorService (cron every 5 min)
  └── TiktokPoller.poll(account, context)
        ├── CredentialVaultService  ← decrypt access_token from ChannelCredentialRef
        ├── TiktokExternalService   ← call TikTok Shop API v2 (conversations → messages)
        └── PollingQueueService     ← publish RawWebhookMessage to SQS (same queue as omnichat-gateway)
```

## Files to Create

### 1. `ace/apps/omnichat-service/src/external/types/tiktok.ts`
TikTok Shop API v2 response types:
- `TiktokApiResponse<T>` — base wrapper `{ code, message, data }`
- `TiktokConversation` — `{ conversation_id, latest_message_time, latest_message_type, ... }`
- `TiktokMessage` — `{ message_id, sender, create_time, message_content: { type, text } }`
- `TiktokConversationListData` — `{ conversations[], next_page_token, has_more }`
- `TiktokMessageListData` — `{ messages[], next_page_token, has_more }`

### 2. `ace/apps/omnichat-service/src/external/services/tiktok-external.service.ts`
TikTok Shop Open API v2 HTTP client.

**Base URL**: `https://open-api.tiktokglobalshop.com`

**Auth**: `x-tts-access-token: {access_token}` header + `HMAC-SHA256` signature query param.

**Signature algorithm (TikTok Shop API standard)**:
```text
base_string = app_secret + endpoint_path + sorted_params_concat + app_secret
sign = HMAC-SHA256(base_string, app_secret).toUpperCase()
```

**Methods**:
```typescript
async listConversations(opts: {
  accessToken: string;
  shopId: string;
  pageToken?: string;
  pageSize?: number;
}): Promise<TiktokConversationListData>

async listMessages(opts: {
  accessToken: string;
  conversationId: string;
  shopId: string;
  pageToken?: string;
  pageSize?: number;
  sortOrder?: 'asc' | 'desc';
}): Promise<TiktokMessageListData>
```

**Rate limit detection**: TikTok returns `code: 4029xxx` in response body for rate limiting.
Throw a custom `TiktokRateLimitError` with `retryAfter` from response headers.

**Inject**: `HttpService` (from `@nestjs/axios`), `ConfigService`

### 3. `ace/apps/omnichat-service/src/marketplace-polling/services/polling-queue.service.ts`
Lightweight SQS publisher — reuses the same config path as `omnichat-gateway` SQS.

**Config key**: `omnichatService.omnichatNormalizerWorker.sqs` (already in `configuration.ts` with `accessKeyId`, `secretAccessKey`, `region`, `endpoint`, `queueUrl`)

**Method**:
```typescript
async publish(message: RawWebhookMessage): Promise<void>
```

**Implementation mirrors `QueueService.sendToSqs()` in omnichat-gateway**:
- `MessageGroupId` = `${platform}-${channelId}-${sourceUserId}`
- `MessageDeduplicationId` = SHA-256 of `{ platform, channelId, tenantId, channelAccountId, payload }`
- No Redis fallback (polling can retry on next cycle)

## Files to Modify

### 4. `ace/apps/omnichat-service/src/marketplace-polling/pollers/tiktok-poller.ts` (full replacement)
```typescript
async poll(account: ChannelAccount, context: PollingContext): Promise<PollingOutcome>
```

**Implementation steps**:
1. Retrieve `access_token`: fetch `ChannelCredentialRef` where `channel_account_id = account.id` AND `credential_type = 'access_token'` via Prisma, then get active `CredentialVersion` → decrypt with `CredentialVaultService.decrypt(blob)`. If missing → log warn, return `{ itemsIngested: 0 }`.
2. List conversations (paginated):
   - Call `tiktokExternalService.listConversations({ accessToken, shopId: account.external_account_id })`
   - Continue paginating while `has_more === true`
   - Filter: only conversations with `latest_message_time >= context.since` (unix seconds)
3. For each conversation, list messages (paginated):
   - Call `tiktokExternalService.listMessages({ accessToken, conversationId, shopId })`
   - Filter: only messages with `create_time >= context.since`
   - `sort_order`: `'asc'` to get oldest first
4. Build `RawWebhookMessage` per message:
```json
{
  "platform": "TIKTOK",
  "channelId": "account.external_account_id",  // shop_id
  "tenantId": "account.tenant_id",
  "channelAccountId": "account.id",
  "sourceUserId": "message.sender.open_id",
  "rawPayload": { "conversation_id": "...", "message": "..." },
  "timestamp": "<current Date>",
  "signature": "",
  "headers": {},
  "source_category": "chat",
  "fetch_batch_id": "batchId"   // single UUID generated at start of poll() call
}
```
5. Publish each via `PollingQueueService.publish(msg)`
6. Return `{ itemsIngested: count, rateLimited: false }`

**Rate limit handling**: Catch `TiktokRateLimitError` → return `{ itemsIngested: partial, rateLimited: true, retryAfterMs: error.retryAfterMs }`.
Orchestrator already handles this by calling `backoffService.calculateRateLimitBackoffMs()`.

**Inject**: `PrismaService`, `CredentialVaultService`, `TiktokExternalService`, `PollingQueueService`

### 5. `ace/apps/omnichat-service/src/marketplace-polling/marketplace-polling.module.ts`
- Add `HttpModule` import
- Add providers: `PollingQueueService`, `TiktokExternalService`, `CredentialVaultService`
- Inject into `TiktokPoller`'s factory (not needed — NestJS DI handles it automatically)

### 6. `ace/apps/omnichat-service/src/external/external.module.ts`
- Add `TiktokExternalService` to providers and exports

### 7. `ace/packages/config/src/configuration.ts`
Add TikTok app credentials under `omnichatService`:
```typescript
tiktok: {
  appKey: process.env.TIKTOK_APP_KEY || '',
  appSecret: process.env.TIKTOK_APP_SECRET || '',
},
```

## Key Reuse
| What | Where |
| :--- | :--- |
| `PollingContext`, `PollingOutcome`, `IMarketplacePoller` | `marketplace-poller.interface.ts` |
| `CredentialVaultService.decrypt()` | `credentials/services/credential-vault.service.ts` |
| `PrismaService` | `prisma/prisma.service.ts` |
| SQS config path `omnichatService.omnichatNormalizerWorker.sqs` | `packages/config/src/configuration.ts:204` |
| `RawWebhookMessage` DTO (with `source_category`, `fetch_batch_id`) | `omnichat-gateway/src/webhook/dto/webhook-message.dto.ts` |
| `SendMessageCommand` + dedup + group patterns | `omnichat-gateway/src/queue/queue.service.ts:156` |
| HMAC sig pattern | `omnichat-service/src/external/services/lazada-external.service.ts:24` |

## Verification
**Unit test `tiktok-poller.spec.ts`**:
- Mock `TiktokExternalService` returning 2 pages of conversations with messages
- Verify `PollingQueueService.publish` called once per message
- Verify `PollingOutcome.itemsIngested` equals total message count
- Test rate limit path returns `rateLimited: true`
- Test missing credential returns `{ itemsIngested: 0 }` without throwing

**Unit test `polling-queue.service.spec.ts`**:
- Mock `SQSClient.send()`
- Verify `MessageGroupId` format and `MessageDeduplicationId` is SHA-256 hash

**Manual / integration test**:
- Set up a TikTok Shop sandbox account, store `access_token` via `POST /credentials` API
- Run `pnpm --filter omnichat-service start:dev`
- Trigger one poll cycle via `PollingOrchestratorService.runCycle()`
- Verify SQS message appears in LocalStack and `omnichat-normalizer-worker` receives it