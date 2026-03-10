# Subtask 1: Define Polling Schedules & Architecture

**Status**: TO DO

## Description
Set up the core polling architecture: a cron-based scheduler that drops jobs into a queue (e.g. SQS, BullMQ) and a worker pool to execute API polling requests per `channel_account`.

## Implementation Details
1. **Target Files**: 
   - `apps/omnichat-service/src/polling/` (New module structure)
   - `infrastructure/` (Queue definitions)
2. **Current State**: The system lacks a centralized, scheduled polling worker and the associated cron scheduler for `channel_accounts`.
3. **Action Required**: 
   - Define a cron job (e.g., via `@nestjs/schedule`) that periodically scans `channel_accounts` where `channel_type` requires polling (TikTok, Shopee, Lazada) and `status` is ACTIVE.
   - For each valid account, push a `PollJob` message into a message broker (SQS/BullMQ).
   - Create a worker service listening to this queue to pick up the `PollJob`.
   - Ensure the worker strictly enforces concurrency controls (e.g. Redis locks or FIFO queues) so only *one* poll job runs per `channel_account` at a time.
