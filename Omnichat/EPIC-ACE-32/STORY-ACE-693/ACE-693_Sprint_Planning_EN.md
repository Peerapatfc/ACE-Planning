# Sprint Planning: ACE-693 Meta Connector v1 Facebook Messenger Inbound and Outbound Text

## 1. Subtask Breakdown & Current Status
Based on the codebase analysis in `omnichat-service`, `omnichat-gateway`, and `omnichat-normalizer-worker`, here is the actionable sprint plan:

- **[ ] Subtask 1: Implement Inbound Webhook Normalization (Mapper)**:
  - **Status**: TO DO. The `RawWebhookMessage` is correctly extracted via `ChannelExtractorService.extractFacebook`. However, the normalization step in `omnichat-normalizer-worker` currently lacks a `facebook-channel-mapper.ts`.
  - **Action**: Implement `FacebookChannelMapper` to translate the raw Facebook payload into the internal schema v1 `InboundEvent` DTO. Ensure `external_message_id` is mapped correctly from the payload (e.g., `entry.messaging.message.mid`) to guarantee idempotency on retries.

- **[ ] Subtask 2: Implement Outbound Sending Logic**:
  - **Status**: TO DO. The `FacebookStrategy` in `omnichat-service/src/channel-accounts/strategies/facebook.strategy.ts` has a placeholder for `pushMessage` that throws a `NotImplementedException`.
  - **Action**: Use the Meta Graph API inside `pushMessage` to fire `/me/messages` events. Map outbound text messages correctly and return the provider's `message_id` within the `PushMessageResult`.

- **[ ] Subtask 3: Implement Advanced Error Handling for Meta API**:
  - **Status**: TO DO. While `pushMessage` is being implemented, it needs to capture and categorize Facebook error codes.
  - **Action**: Check for conditions like `OAuthException` or token invalidation. Make sure the error is returned with `isSuccess: false` and `errorMessage` properly populated so `MessagesService` flags the message status as `failed` with `auth_error` metadata. 

- **[ ] Subtask 4: Verify Webhook Setup Integrity**:
  - **Status**: DONE/REVIEW. The codebase already implements the `GET /webhooks/facebook` endpoint checking `hub.challenge` and `validateFacebookSignature` correctly hashes the payload using HMAC SHA-256. 
  - **Action**: Run integration tests to assure this piece does not break when full text-message payloads start streaming in.

## 2. Recommendations & Edge Cases to Watch Out For

1. **Non-Message Events (Read, Delivery, Postback)**:
   - **Risk**: Facebook webhooks frequently trigger `read` and `delivery` receipts as well as `postback` events along with standard text. If the new mapper doesn't filter them out, it might inadvertently create empty messages or crash.
   - **Recommendation**: Ensure `facebook-channel-mapper.ts` either safely drops these events (returning `null`) or accurately parses them out of the `entry.messaging` array since v1 is strictly text focused.

2. **Wait, Threads in Facebook?**:
   - **Risk**: Facebook provides a Page-Scoped ID (PSID) as `sender.id`. `MessagesService` automatically creates a thread based on `external_user_id` + `channel_account_id`.
   - **Recommendation**: This native hashing approach is completely sufficient for Facebook threading v1. Just ensure `sourceUserId` from the payload continues to extract the `sender.id`. 

3. **Inbound Attachments**:
   - **Risk**: A user sends an image, which Facebook delivers via `message.attachments`. Even though the scope says "Not include attachments", the payload could still arrive.
   - **Recommendation**: Have the mapper safely ignore the attachments array and map the `content` as `[Attachment unsupported in v1]` or an empty string, avoiding unhandled errors during schema conversion.
