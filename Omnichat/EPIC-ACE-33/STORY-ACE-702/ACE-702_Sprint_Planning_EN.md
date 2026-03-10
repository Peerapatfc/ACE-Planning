# Sprint Planning: ACE-702 - STORY-MKT-02: Scheduled Polling Framework v1

## 📋 Story Overview
**Goal:** Create a centralized, scheduled polling engine to automatically fetch data (messages, orders, etc.) from marketplace APIs (TikTok, Shopee, Lazada) per `channel_account`.
**Key Deliverables:** 
- Polling job scheduling and queue runner.
- Watermark tracking per account/event to prevent data duplication.
- Rate limits and concurrency controls.
- Push raw valid events to the Normalization Pipeline (NDP-03).

## 🛠️ Current Implementation Status
Based on the codebase analysis (`/Users/peerapatpongnipakorn/Work/AI-Knowledge/ace`):
- **Missing Infrastructure:** There are currently no pre-existing watermark systems (`watermarks` table) or centralized polling engines built specifically for the `omnichat-service`.
- **Existing Patterns:** The system has standalone workers (like `ai-extractor-worker` or `omnichat-normalizer-worker`), implying that queue-based processing (e.g., SQS or BullMQ) is the standard architectural pattern.
- **Action Needed:** This means the framework must be built from the ground up, requiring database schema updates (for watermarks) and a new worker/scheduler architecture.

## 📝 Subtask Breakdown
| ID | Subtask Name | Status | Description |
|---|---|---|---|
| MKT-02.1 | Define Polling Architecture & Queue | TO DO | Set up the cron-based scheduler, job queue (e.g. SQS/Bull), and worker infrastructure to trigger API polling per `channel_account`. |
| MKT-02.2 | Implement Watermark State Check | TO DO | Create database schemas and logic to track the last fetched timestamp (watermark) per channel to prevent duplicates. |
| MKT-02.3 | Implement Rate Limiting & Backoff | TO DO | Add safety guards to respect marketplace API limits, including exponential backoff for transient failures. |

## ⚠️ Recommendations & Edge Cases
1. **Clock Skew & Watermark Overlap:** When polling, always subtract a short overlap buffer (e.g., 5 minutes) from the last watermark to ensure edge-case messages generated during previous poll cycles aren't permanently missed. Use external message IDs to de-duplicate any overlapping messages fetched in that buffer window.
2. **Concurrency Control:** Ensure that only *one* poll job runs per `channel_account` at any given time. If a poll takes longer than the interval (e.g. backfilling history), the next scheduled run should skip or wait until the lock is released.
3. **Queue Resilience:** If a marketplace API goes down completely, the polling framework should pause or massively backoff polling for *that specific channel type* to prevent queue starvation for healthy channels.
