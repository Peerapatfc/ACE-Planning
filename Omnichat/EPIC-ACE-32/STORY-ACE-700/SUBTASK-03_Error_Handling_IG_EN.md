# Subtask 3: Implement Instagram Error Handling

**Status**: TO DO

## Description
Extend the `InstagramStrategy` outbound framework to detect standard and Instagram-specific exceptions derived from the Meta API interactions.

## Implementation Details
1. **Target File**: `apps/omnichat-service/src/channel-accounts/strategies/instagram.strategy.ts` (Inside Catch Blocks)
2. **Current State**: Completely unwritten, as it relies on Subtask 2's creation.
3. **Action Required**: 
   - Parse Meta JSON exceptions correctly. 
   - Identify whether an exception relates to an Invalid Token, Permissions Scope mismatch, or the infamous "Outside 24-hours window" response. 
   - Funnel those errors securely back with `isSuccess = false` and append explicit text mapping explaining the failure inside the `errorMessage`. The centralized `MessagesService` uses this flag to visibly label the UI element as marked 'failed' for administrators.
