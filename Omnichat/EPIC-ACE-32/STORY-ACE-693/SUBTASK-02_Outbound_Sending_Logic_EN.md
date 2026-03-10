# Subtask 2: Implement Outbound Sending Logic

**Status**: TO DO

## Description
Develop the core capability for our application to act as a proper Meta API client and fire textual conversation replies directly to Facebook Messenger users via the `/me/messages` endpoint. 

## Implementation Details
1. **Target File**: `apps/omnichat-service/src/channel-accounts/strategies/facebook.strategy.ts`
2. **Current State**: The `pushMessage` method is currently throwing a `NotImplementedException`.
3. **Action Required**: 
   - Integrate with the Graph API `https://graph.facebook.com/v25.0/me/messages` utilizing the target channel account's assigned access token.
   - Format the request payload securely so that `recipient.id` receives the text from the UI.
   - Successfully capture the returning `message_id` and format it neatly inside the standard `PushMessageResult` object to trace deliveries on the dashboard.
