# Subtask 2: Update Unit Tests

**Status**: TO DO / IN PROGRESS

## Description
Add/Update unit tests in `messages.service.spec.ts` for deterministic conversation mapping. Ensure unit tests adequately cover the SHA256 creation function to prevent regressions during future refactors.

## Implementation Details
1. **Target File**: `apps/omnichat-service/src/messages/messages.service.spec.ts`
2. **Current State**: The unit test file already contains descriptions block for `fallback_thread_key determinism` and asserts if it's used when `external_thread_id` is missing.
3. **Action Required**: 
   - Execute the current test suite: `pnpm test` (or scoped test run).
   - Ensure the coverage properly validates that the same `external_user_id` and `channel_account_id` inputs correctly hit the `PrismaService` find/transaction layers with identical fallback representations.
   - If acceptable, this task is complete. If logic for Group chats or custom null fallbacks is added, tests should be updated to verify those newly handled edge cases.
