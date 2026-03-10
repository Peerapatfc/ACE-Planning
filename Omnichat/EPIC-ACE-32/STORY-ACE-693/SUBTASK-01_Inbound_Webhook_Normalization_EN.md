# Subtask 1: Implement Inbound Webhook Normalization (Mapper)

**Status**: TO DO

## Description
The `RawWebhookMessage` for Facebook is already extracted via `ChannelExtractorService.extractFacebook`. However, the `omnichat-normalizer-worker` service needs a corresponding channel mapper to transform this raw payload into our normalized schema v1 `InboundEvent` DTO.

## Implementation Details
1. **Target File**: Create `apps/omnichat-normalizer-worker/src/worker/channel-mapper/mappers/facebook-channel-mapper.ts`
2. **Action Required**: 
   - Implement the translation logic for `FacebookChannelMapper`.
   - Ensure `external_message_id` is meticulously mapped (usually found under `entry.messaging.message.mid`) to guarantee that the idempotency safeguards in `MessagesService` function properly during webhook retries.
   - Extract the text content and safely ignore or gracefully stringify attachment/fallback payloads so the system does not crash when unexpected non-text media arrives.
   - Register it correctly in the `channel-mapper-registry.ts`.
