# Subtask 2: Implement Watermark & Duplicate Check

**Status**: TO DO

## Description
Create a resilient tracking system to store the last successfully fetched timestamp ("watermark") per `channel_account` and `event_type` to prevent continuous data duplication while avoiding missed messages.

## Implementation Details
1. **Target Files**: 
   - `apps/omnichat-service/src/polling/entities/watermark.entity.ts` (New)
   - `apps/omnichat-service/src/polling/services/watermark.service.ts` (New)
2. **Current State**: No watermark tracking mechanism exists.
3. **Action Required**: 
   - Create a `watermarks` database table (e.g., `id`, `tenant_id`, `channel_account_id`, `event_type`, `last_polled_cursor_or_timestamp`).
   - Before executing a poll, the worker must read the watermark.
   - During the API call, fetch data starting from `[watermark - OVERLAP_BUFFER]`. The overlap buffer (e.g. 5 minutes) ensures messages stuck in transit during the last poll aren't ignored forever.
   - De-duplicate any messages fetched within that overlap buffer using the external message ID.
   - After a successful fetch and publish to the Normalizer, update the watermark to the newest timestamp received.
