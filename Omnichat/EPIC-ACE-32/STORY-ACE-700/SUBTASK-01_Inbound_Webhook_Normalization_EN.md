# Subtask 1: Implement Inbound Webhook Normalization (Mapper)

**Status**: TO DO

## Description
The `RawWebhookMessage` for Instagram is already recognized and extracted via `ChannelExtractorService.extractInstagram` inside `omnichat-gateway`. However, the `omnichat-normalizer-worker` service needs a corresponding channel mapper to transform this raw payload into our normalized schema v1 `InboundEvent` DTO.

## Implementation Details
1. **Target File**: Create `apps/omnichat-normalizer-worker/src/worker/channel-mapper/mappers/instagram-channel-mapper.ts`
2. **Action Required**: 
   - Write the translation logic for `InstagramChannelMapper`.
   - Ensure `external_message_id` is carefully mapped (typically located inside the `entry.messaging.message.mid` path for Instagram Meta payloads) to ensure idempotency functions properly during webhook retries.
   - Extract the text content safely. Any unsupported payload segments like IG stories or media attachments should be cast to a string placeholder or dropped gracefully to protect the normalization worker from crashing.
   - Register the class correctly in `channel-mapper-registry.ts` associating it to `PlatformType.INSTAGRAM`.
