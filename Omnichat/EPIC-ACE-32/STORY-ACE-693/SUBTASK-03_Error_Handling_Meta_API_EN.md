# Subtask 3: Implement Advanced Error Handling for Meta API

**Status**: TO DO

## Description
Develop standard error handling behaviors intertwined with the outbound sending logic. The Facebook strategy must intelligently categorize different types of API failures so the global message state marks them appropriately.

## Implementation Details
1. **Target File**: `apps/omnichat-service/src/channel-accounts/strategies/facebook.strategy.ts` (inside `pushMessage` function catch block)
2. **Current State**: Neither the try nor the catch block exist.
3. **Action Required**: 
   - Detect whether an invalid API request occurs. Usually, Meta API replies with `OAuthException` or explicit error messages depicting an invalid token or missing permission scopes.
   - Map those scenarios back into a response object where `isSuccess = false` and append explicit text explaining the `errorMessage`. The system's existing orchestrator will take over and update the global table state (e.g. to `auth_error`).
   - Log observability metrics securely without exposing sensitive customer access bits.
