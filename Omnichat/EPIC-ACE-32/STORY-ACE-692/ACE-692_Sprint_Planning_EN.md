# Sprint Planning: ACE-692 LINE OA Threading Rules v1 Conversation Mapping

## 1. Subtask Breakdown & Current Status
Based on the codebase analysis in `omnichat-service` and `omnichat-gateway`, most of the core logic has already been implemented. Here is the actionable sprint plan:

- **[x] Verify `MessagesService` uses `fallback_thread_key`**:
  - **Status**: Implemented. The `resolveConversation` method in `MessagesService` correctly computes a SHA256 hash using `external_user_id` and `channel_account_id`.
  - **Action**: Mark as done in ClickUp.
- **[x] Validate outbound message mapping to same `conversationId` in `sendMessage`**:
  - **Status**: Implemented. `ConversationsService.sendMessage` naturally enforces this by taking `conversationId` as a parameter and persisting the new outbound message directly under that same ID. 
  - **Action**: Mark as done.
- **[x] Add/Update unit tests in `messages.service.spec.ts`**:
  - **Status**: Almost complete. Existing tests already cover the determinism of `fallback_thread_key`.
  - **Action**: Briefly run and verify the test suite. Add any edge case tests if necessary.
- **[ ] Ensure `omnichat-gateway` webhook normalization passes required fields to service**:
  - **Status**: Partially complete. `ChannelExtractorService.extractLine` extracts `sourceUserId: event.source?.userId || 'unknown'`.
  - **Action**: Need to ensure this logic gracefully drops or handles events where `userId` is missing without pooling everything into the `'unknown'` bucket.
- **[ ] Document known limitations for LINE**:
  - **Status**: To Do.
  - **Action**: Create a markdown file or Wiki page listing limitations (e.g., group chats, unsend events, etc.).

## 2. Recommendations & Edge Cases to Watch Out For

1. **Group Chat / Room Event Bubbling**:
   - **Risk**: In LINE, messages can come from a group or a room. In these cases, `event.source.type` will be `group` or `room`, and `event.source.groupId` will be present. If we strictly look for `event.source.userId`, it might fallback to `'unknown'` and group *all* unknown users globally into a single conversation.
   - **Recommendation**: Update `ChannelExtractorService.extractLine` to check `event.source.type`. If it is a group/room, we should extract the `groupId` or `roomId` as the `external_user_id` (or reject the payload if group chats are strictly unsupported in v1).

2. **Handling Non-Message Events**:
   - **Risk**: Webhooks contain `follow`, `unfollow`, and `postback` events. 
   - **Recommendation**: Ensure that creating a conversation purely from a `follow` event does not crash if we don't handle the messaging flow properly. 

3. **Collision of `unknown` Users**:
   - **Risk**: If the hashing function hashes `'unknown'` + `channel_account_id`, all users with missing IDs will share the exact same thread. 
   - **Recommendation**: Filter out or return a 400 Bad Request for LINE events that critically lack an identifier, rather than defaulting to `'unknown'`.
