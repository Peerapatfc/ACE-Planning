# Subtask 1: Verify Inbound Mapping

**Status**: TO DO / DONE (Logic is currently present in codebase)

## Description
Verify `MessagesService` uses `fallback_thread_key` as a hash of `external_user_id` + `channel_account_id` for LINE inbound mapping. This ensures deterministic conversation mapping where users without a native `thread_id` are grouped correctly.

## Verification Details
1. **Target File**: `apps/omnichat-service/src/messages/messages.service.ts`
2. **Current Implementation**: The method `resolveConversation` checks if `external_thread_id` exists. If not, it falls back to calling `computeFallbackThreadKey(external_user_id, channel_account_id)`, which generates a deterministic SHA256 hash.
3. **Execution**: The implemented logic is currently correct and matches the acceptance criteria for the pilot phase.
4. **Action Required**: The developer simply needs to verify the existing implementation against the business requirement, confirm it with the QA team, and move the ticket status to DONE. No extra code changes are required for this subtask to function normally, assuming edge cases (like group chats) are handled elsewhere.
