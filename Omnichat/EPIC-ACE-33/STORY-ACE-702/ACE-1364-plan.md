ACE-1364: Implement TikTok Webhook Chat Ingestion
Context
TikTok Shop supports webhooks for chat messages (event 13: New Conversation, event 14: New Message). The webhook infrastructure (endpoint, signature validation, dedup, SQS) is already in place, but two key pieces are missing:

extractTiktok() uses body.open_id (incorrect for event 14) and new Date() instead of payload timestamp
No TikTok channel mapper in normalizer-worker — messages go to DLQ
This plan covers Subtask 1 (extractor update) and Subtask 2 (channel mapper creation). Subtask 3 (webhook subscription) is manual ops. Subtask 4 (poller comment) is trivial low-priority.

Subtask 1: Update extractTiktok() Payload Mapping
File to modify
channel-extractor.service.ts (lines 142-166)
Changes
Replace the current generic extractTiktok() with event-type-aware mapping:

Event 14 (New Message): sourceUserId = data.sender.im_user_id, timestamp = data.create_time * 1000, source_category = 'chat'
Event 13 (New Conversation): sourceUserId = 'system', timestamp = data.create_time * 1000, source_category = 'chat'
Other events: fallback with body.timestamp * 1000, no source_category
channelId: always String(body.shop_id || '')
Tests to update
channel-extractor.service.spec.ts (lines 256-283)
Add tests for:

Event 14: correct sourceUserId, timestamp conversion (unix sec → Date), source_category: 'chat'
Event 13: sourceUserId = 'system'
Unknown event type: fallback behavior
Missing data fields: graceful defaults
Subtask 2: Create TikTok Channel Mapper
File to create
apps/omnichat-normalizer-worker/src/worker/channel-mapper/mappers/tiktok-channel-mapper.ts
Files to modify
worker.module.ts — register TiktokChannelMapper in providers + factory
index.ts — export new mapper
Implementation pattern
Follow line-channel-mapper.ts pattern:

Implement ChannelMapper interface (platform, normalize())
Return NormalizationResult discriminated union
Mapping logic
TikTok data.type	→ content_type	Content extraction
TEXT	text	data.content.text
IMAGE	image	attachment from data.content.image_info.image_url
VIDEO	video	attachment from data.content.video_info.video_url
EMOTICONS	sticker	[sticker]
PRODUCT_CARD, BUYER_ENTER_FROM_PRODUCT	text	[product card] with structured_content
ORDER_CARD, BUYER_ENTER_FROM_ORDER	text	[order card] with structured_content
LOGISTICS_CARD	text	[logistics card] with structured_content
COUPON_CARD	text	[coupon card] with structured_content
ALLOCATED_SERVICE, NOTIFICATION, BUYER_ENTER_FROM_TRANSFER	text	system notification text
OTHER / unknown	text	fallback
Key field mappings
external_message_id = data.message_id
external_user_id = data.sender.im_user_id
external_thread_id = data.conversation_id
direction = data.sender.role === 'BUYER' ? 'inbound' : 'outbound' (outbound → source: 'external_native')
channel_timestamp = new Date(data.create_time * 1000).toISOString()
source_category = 'chat'
shop_id in metadata = from rawPayload context
Filter data.is_visible === false → return unsupported_event
Reuse existing utilities
url-utils.ts — for URL detection in text content
normalized-event.ts — all types
channel-mapper.interface.ts — ChannelMapper interface
Tests to create
apps/omnichat-normalizer-worker/src/worker/channel-mapper/mappers/tiktok-channel-mapper.spec.ts
Test each message type mapping
Test direction detection (BUYER vs SELLER)
Test is_visible === false filtering
Test missing/invalid fields
Subtask 4: Deprioritize TikTok Poller (Low Priority)
File to modify
tiktok-poller.ts
Change
Add a comment clarifying that chat uses webhook (event 14) instead of polling. Keep the stub for future order sync use cases.

Verification
Unit tests:


pnpm --filter omnichat-gateway test -- --testPathPattern=channel-extractor
pnpm --filter omnichat-normalizer-worker test -- --testPathPattern=tiktok-channel-mapper
Lint & format:


pnpm --filter omnichat-gateway lint
pnpm --filter omnichat-normalizer-worker lint
pnpm format
Build:


pnpm --filter omnichat-gateway build
pnpm --filter omnichat-normalizer-worker build