# Subtask 3: Implement Rate Limiting & Backoff Retries

**Status**: TO DO

## Description
Develop protective logic limiting the frequency of marketplace API requests (rate limits) and apply exponential backoff when dealing with temporary errors to maintain system health and avoid vendor lockouts.

## Implementation Details
1. **Target Files**: 
   - `apps/omnichat-service/src/polling/services/polling-worker.service.ts`
   - Worker retry policies.
2. **Current State**: N/A (New polling infrastructure).
3. **Action Required**: 
   - Observe and enforce the rate limit boundaries for TikTok, Shopee, and Lazada APIs locally so that the worker does not flood their servers.
   - If an API responds with `429 Too Many Requests` or `5xx Server Error`, categorize it as a transient failure.
   - For transient failures, do *not* drop the job. Instead, re-queue the `PollJob` with an exponential backoff strategy.
   - For constant failures on a specific channel type, enable a circuit breaker that pauses queue jobs for that provider until it recovers, preventing exhaustion of our internal worker pool.
