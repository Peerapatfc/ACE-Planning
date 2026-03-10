# Subtask 4: Ensure Webhook Normalization

**Status**: TO DO

## Description
Ensure the `omnichat-gateway` webhook normalization sequence correctly extracts and passes required logic and identifiers downstream to the service payload.

## Implementation Details
1. **Target File**: `apps/omnichat-gateway/src/webhook/services/channel-extractor.service.ts`
2. **Current State**: `extractLine` maps `sourceUserId: event.source?.userId || 'unknown'`.
3. **Identified Risks**:
   - If `userId` is missing (for instance, when receiving messages from LINE Group chats and Rooms where `source.type` implies no specific user without special consent scopes), defaulting to `'unknown'` will hash everything into one global broken thread for that tenant channel.
4. **Action Required**: 
   - We must review if we want to extract the `groupId` / `roomId` instead when `userId` is absent.
   - Alternatively, throw a proper Bad Request exception or skip the event payload securely so that junk `'unknown'` identifiers do not poison our conversation threading process.
   - Make small codebase alterations reflecting the desired fix directly into `extractLine`.
