Plan: Shopee Scheduled Polling — Chat Message (ACE-1256)
TL;DR: ACE-1256 requires replacing the ShopeePoller stub with a working implementation that calls Shopee Open Platform Chat API (v2), publishes raw messages to SQS, and adding a ShopeeChannelMapper in omnichat-normalizer-worker to normalize those messages. The pattern mirrors the existing TiktokPoller + future TiktokChannelMapper design, but auth differs — Shopee uses HMAC-SHA256 request signing (partner_id + partner_key from config, access_token + shop_id per account from CredentialVault).

Scope
Two services are touched:

omnichat-service — polling logic & Shopee external API client
omnichat-normalizer-worker — message normalization mapper
Steps
A — omnichat-service: Shopee types & external service
Create apps/omnichat-service/src/external/types/shopee.ts

Types: ShopeeConversation (fields: conversation_id, to_id, to_name, latest_message_id, latest_message_content, last_message_timestamp), ShopeeMessage (fields: message_id, conversation_id, message_type, content, from_id, from_name, to_id, to_name, create_time, source_content), ShopeeGetConversationListResponse, ShopeeGetMessageListResponse
Error class: ShopeeRateLimitError extends Error with retryAfterMs: number
Create apps/omnichat-service/src/external/services/shopee-external.service.ts

@Injectable() class using HttpService (Axios)
Base URL: https://partner.shopeemobile.com (from ConfigService)
Config keys needed: SHOPEE_PARTNER_ID, SHOPEE_PARTNER_KEY (app-level env vars)
Auth per request: build HMAC-SHA256 signature → {partner_id}{api_path}{timestamp}{access_token}{shop_id} signed with partner_key; append partner_id, timestamp, access_token, sign, shop_id as query params
Method getConversationList(params: { accessToken, shopId, offset?: number, pageSize?: number, lastMessageTs?: number }): calls GET /api/v2/sellerchat/get_conversation_list, returns ShopeeGetConversationListResponse
Method getMessageList(params: { accessToken, shopId, conversationId, offset?: string, pageSize?: number }): calls GET /api/v2/sellerchat/get_message, returns ShopeeGetMessageListResponse
Throws ShopeeRateLimitError on HTTP 429 or Shopee error code 4002xxxx (rate limit)
B — omnichat-service: Fill ShopeePoller stub
Replace apps/omnichat-service/src/marketplace-polling/pollers/shopee-poller.ts — full implementation following TiktokPoller pattern:

Constructor: inject PrismaService, CredentialVaultService, ShopeeExternalService, PollingQueueService
resolveAccessToken(account) — same Prisma query as TikTok: ChannelCredentialRef → CredentialVersion → CredentialVaultService.decrypt()
poll():
Resolve access_token; skip if null
shopId = account.external_account_id; sinceUnix = Math.floor(context.since.getTime() / 1000); batchId = randomUUID()
Paginated getConversationList() — collect conversations where last_message_timestamp >= sinceUnix, break early when timestamp falls below window
For each conversation: paginated getMessageList() — collect messages where create_time >= sinceUnix
Build RawWebhookMessage: platform: 'SHOPEE', channelId: shopId, sourceUserId: msg.from_id, rawPayload: { conversation_id, message: msg }, source_category: 'chat', fetch_batch_id: batchId
Publish each via PollingQueueService.publish()
Track latestCreateTime for lastIngestedAt
Catch ShopeeRateLimitError → return { rateLimited: true, retryAfterMs, itemsIngested }
Update apps/omnichat-service/src/marketplace-polling/marketplace-polling.module.ts

Add ShopeeExternalService to providers array (already has TiktokExternalService as reference)
C — omnichat-normalizer-worker: ShopeeChannelMapper
Create apps/omnichat-normalizer-worker/src/worker/channel-mapper/mappers/shopee-channel-mapper.ts

implements ChannelMapper, readonly platform = PlatformType.SHOPEE
normalize(rawPayload, context):
Guard: if !rawPayload.message → return NormalizationError
msg = rawPayload.message
direction: if msg.from_id === context.channel_account_id → 'outbound', else 'inbound'
contentType: map message_type → ContentType ('text' / 'image' / 'file' etc.)
content: for text → msg.content.text; for image → msg.source_content.file_info?.url ?? ''
external_message_id: msg.message_id
external_user_id: msg.from_id
external_thread_id: msg.conversation_id
channel_timestamp: new Date(msg.create_time * 1000).toISOString()
metadata.shop_id: rawPayload.message?.to_id ?? null (seller's shop_id)
metadata.fetch_batch_id: from context (passed through RawWebhookMessage.fetch_batch_id)
Return NormalizationSuccess with built NormalizedEvent
Update apps/omnichat-normalizer-worker/src/worker/channel-mapper/index.ts

Export ShopeeChannelMapper
Update apps/omnichat-normalizer-worker/src/worker/worker.module.ts

Add ShopeeChannelMapper to the mapper list passed to ChannelMapperRegistry (alongside lineMapper, facebookMapper, instagramMapper)
Env Variables to Add
Add to .env.example and ConfigService:

SHOPEE_PARTNER_ID — Shopee app partner ID (numeric)
SHOPEE_PARTNER_KEY — Shopee app signing key (string)
Verification
Run pnpm --filter omnichat-service build and pnpm --filter omnichat-normalizer-worker build — must compile with no errors
Unit test ShopeeExternalService.buildSignature() (pure function, easy to test)
Unit test ShopeeChannelMapper.normalize() with fixture payloads (text message, image message, outbound echo)
End-to-end: enable POLLING_CRON_EXPRESSION, attach a Shopee sandbox account, observe [shopee] account=... ingested=N log in omnichat-service and normalized event TCP call in normalizer-worker
Decisions

Shopee auth: partner_id + partner_key from app-level env (not per-account), access_token per account from CredentialVault — aligns with Shopee Open Platform v2 design
ShopeeChannelMapper included in this task per user confirmation (not split to separate subtask)
source_category: 'chat' for all polled Shopee messages (same as TikTok)