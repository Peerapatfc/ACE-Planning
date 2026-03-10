# Subtask 2: Implement Outbound Sending Logic (Instagram Strategy)

**Status**: TO DO

## Description
Build the `InstagramStrategy` so our backend services know how to securely dispatch an outbound message text over the Instagram Direct Message platform.

## Implementation Details
1. **Target File**: Create `apps/omnichat-service/src/channel-accounts/strategies/instagram.strategy.ts`
2. **Current State**: `facebook` and `line` exist, but `instagram` is totally missing.
3. **Action Required**: 
   - Create a class implementing the `AccountChannelStrategy` interface.
   - Using the supplied access token fetched dynamically during the send flow, craft a request pointing towards the Meta Graph API `/me/messages` endpoint tailored for Instagram routing.
   - Successfully parse the responding `message_id` and format it safely back inside the `PushMessageResult` DTO object payload so admins can track message completion.
