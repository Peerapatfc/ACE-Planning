# EPIC ACE-31: Inbound Flow PR / Branch Breakdown

This document provides a breakdown of tasks into small, manageable Pull Requests (PRs) or branches for **Sequence 1: Inbound Flow** of EPIC-ACE-31 (NDP-01 to NDP-05). It excludes the basic tenant and channel account setup (which belongs to EPIC-ACE-30 / FND-01) to ensure each PR is small, easy to review, and allows for parallel development.

> [!IMPORTANT]
> **Reference Documents** — All implementation must align with these consolidated epic-level specs:
>
> | Document | Description |
> |---|---|
> | [epic-api-table.md](./epic-api-table.md) | Consolidated API surface — endpoints, request/response contracts, pagination conventions |
> | [epic-er-diagram.md](./epic-er-diagram.md) | Consolidated ER diagram — all entities, fields, indexes, unique constraints |
> | [epic-sequence.md](./epic-sequence.md) | Consolidated sequence diagrams — inbound/outbound/query flows, SQS config, PII redaction rules |

---

## 🗄️ Stage 1: Database & Internal API (Data Layer for NDP)
**Target Projects:** `omnichat-service` and Shared schema
**Goal:** Prepare database tables and internal APIs to receive data from the normalization worker.

- [x] **PR 1.1: NDP Database Schema**
    - **Tasks:** Create schema definitions and migrations specifically for `Contacts`, `Conversations`, `Messages`, `Attachments`, and `RawEvents` tables.
    - **Review Focus:** Unique constraints for idempotency (preventing duplicate processing) and indexes for cursor-based pagination.

- [x] **PR 1.2: Raw Events API**
    - **Tasks:** Implement `POST /raw-events` (to persist the original webhook payload) and `PATCH /raw-events/:id` (to update the normalization status upon failure).

- [x] **PR 1.3: Inbound Persistence API (Core Logic)**
    - **Tasks:** Implement `POST /messages/inbound`.
    - **Review Focus:** Resolution logic: `UPSERT` Contact -> Create or retrieve Conversation using `fallback_thread_key` -> `INSERT` Message (Idempotent).

---

## 🚪 Stage 2: Webhook Gateway (Entry Point)
**Target Project:** `omnichat-gateway`
**Goal:** Receive webhooks from external channels (LINE, FB, etc.), validate them quickly, and push them to the message queue.

- [x] **PR 2.1: Webhook Controller & Security**
    - **Tasks:** Create a unified `POST /webhooks/:channel` controller.
    - **Review Focus:** Signature validation middleware (HMAC-SHA256) and Rate Limiting logic.

- [x] **PR 2.2: SQS Producer & Deduplication**
    - **Tasks:** Implement logic to publish payloads to an AWS SQS FIFO queue.
    - **Review Focus:** Correct configuration of `MessageGroupId` (to maintain order per channel/user) and `DeduplicationId` (`SHA256(payload)`) to prevent processing duplicate webhook deliveries.

---

## ⚙️ Stage 3: Normalization Pipeline (Core Processing)
**Target Project:** `omnichat-normalizer-worker`
**Goal:** Consume messages from the queue, redact PII, normalize the payload structure, and forward it to Stage 1 APIs for persistence.

- [x] **PR 3.1: SQS Consumer Setup & PII Redactor**
    - **Tasks:** Set up the SQS Consumer (Long-polling 20s, batch size of 10) and implement the initial PII redaction layer.
    - **Review Focus:** Consumer configuration and error safety in redaction.

- [x] **PR 3.2: Channel Mappers (Strategy Pattern)**
    - **Tasks:** Implement transformation logic (starting with one channel, e.g., LINE) to map raw payloads into the standard `NormalizedEvent Contract`.
    - **Review Focus:** Usage of the Strategy Pattern to ensure extensibility for future channels, and support for marketplace metadata (`source_category`: chat, order_reference, fetch_history).

- [x] **PR 3.3: Worker Orchestration (Workflow Stitching)**
    - **Tasks:** Integrate PR 3.1 and 3.2 into the main workflow.
    - **Sub-flow:**
        1. Call PR 1.2 (Save Raw Event).
        2. Attempt payload normalization.
        3. On Success -> Call PR 1.3 (Save Inbound Payload) -> Acknowledge (delete message from queue).
        4. On Failure -> Call PATCH to log the error -> Process next message in the queue (Failure Isolation).

---

## 📎 Stage 4: Async Attachment Processing
**Target Projects:** `file-service`, `omnichat-service`, `omnichat-normalizer-worker`
**Goal:** Offload image/video/audio downloads and uploads to an asynchronous flow, preventing bottlenecks in the main text message processing pipeline.

- [x] **PR 4.1: Internal Upload API (`file-service`)**
    - **Tasks:** Implement `POST /files/upload` to receive binary files, upload them to a public S3 bucket, and return a static `file_url`.

- [x] **PR 4.2: Attachment Tracking APIs (`omnichat-service`)**
    - **Tasks:** Implement `POST /attachments` (to create a record with a `pending` status) and `PATCH /attachments/:id` (to update the `file_url`, size, `retry_count`, `failure_reason`, and ultimate status upon completion or error).

- [x] **PR 4.3: Async Downloader (`omnichat-normalizer-worker`)**
    - **Tasks:** Add logic after PR 3.3: If a message contains attachments, trigger an API to download the file from the channel network -> Validate Size/MIME type -> Send to PR 4.1 -> Update status using PR 4.2.
    - **Review Focus:** Max file size limitations, retry backoff logic (e.g., max 3 retries on network failures), and correct status transitions (`pending` -> `uploading` -> `uploaded` or `failed`/`rejected`).

---

## 🔍 Stage 5: Core Query APIs (For Inbox UI)
**Target Projects:** `api-gateway`, `omnichat-service`
**Goal:** Provide APIs to serve data to the Inbox UI or downstream AI processes.

- [ ] **PR 5.1: Conversations List API**
    - **Tasks:** Implement `GET /api/v1/conversations` (to populate the recent chats list).
    - **Review Focus:** Cursor-based pagination on `last_message_at` and correct JOIN logic with the Contacts table.

- [ ] **PR 5.2: Message Timeline API**
    - **Tasks:** Implement `GET /api/v1/conversations/:id/messages` (to populate the chat window).
    - **Review Focus:** Cursor-based pagination on `created_at` and accurately merging the static `file_url` for any associated attachments into the response.

---

## 💻 Stage 6: MVP Inbox UI (Frontend)
**Target Project:** `omnichat-frontend`
**Goal:** Build the core user interface for agents to view and manage incoming chats based on the provided design.

- [ ] **PR 6.1: Chat List Panel (Left Column)**
    - **Tasks:** Implement the "All chats" sidebar including tabs (Open, Follow up, Closed), filter button, and chat list items displaying avatar, name, last message snippet, timestamp, unread badges, and tags/labels.
    - **Review Focus:** Proper integration with the Conversations List API (PR 5.1) and responsive rendering of the chat list.

- [ ] **PR 6.2: Active Chat Window (Middle Column)**
    - **Tasks:** Build the central chat area with the conversation header (user info, actions, "Close chat" button) and the message timeline (supporting text bubbles, product cards, and system indicators like "AI agent is responding...").
    - **Review Focus:** Proper integration with the Message Timeline API (PR 5.2), auto-scrolling to the latest message, and component modularity for different message types.

- [ ] **PR 6.3: Customer Information Panel (Right Column)**
    - **Tasks:** Implement the right-side details panel containing tabs (Information, Automation logs, AI assistant), displaying customer contact details and notes.
    - **Review Focus:** Clean presentation of dynamic customer data and reusable layout for the nested tabs.

---

> **💡 Tips for Parallel Development**
> - The team can start working on **Stage 1 (Database & APIs)**, **Stage 2 (Webhook)**, and **Stage 4.1 (File Upload)** concurrently. The developers working on Stage 2 can mock SQS publishing during testing.
> - Once Stage 1 is unblocked, the team can immediately proceed with **Stage 3 (Normalizer Worker)**.
