# Subtask 3: Validate Outbound Mapping

**Status**: TO DO / DONE (Logic is currently present in codebase)

## Description
Validate outbound message mapping to the same `conversationId` in the `sendMessage` function. The process must guarantee that sending a message out does not duplicate or mistakenly create entirely new unlinked conversation records.

## Validation Details
1. **Target File**: `apps/omnichat-service/src/conversations/conversations.service.ts`
2. **Current Implementation**: The `sendMessage` function takes `conversationId` as the first actual argument. It then performs a DB check to find the conversation. The newly spawned `'outbound'` direction message gets explicitly tied to `conversation_id: conversationId`.
3. **Execution**: The database transaction logic updates `conversation` (bumping `last_message_at`) seamlessly while creating the message. Thus, the system is fundamentally architected right now to pin outbound traffic to the existing conversation context.
4. **Action Required**: Conduct minimal manual testing and QA to verify messages reflect properly inside the same thread when viewed by the client dashboard. Otherwise, engineering-wise this acts correctly out-of-the-box.
