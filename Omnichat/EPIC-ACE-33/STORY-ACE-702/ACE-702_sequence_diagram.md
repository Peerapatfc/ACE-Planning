# ACE-702 — Sequence Diagrams: Scheduled Polling Framework v1

**Story:** STORY-MKT-02: Scheduled Polling Framework v1 for Marketplace Ingest
**Epic:** EPIC-ACE-33
**Date:** 2026-03-10

---

## 1. Main Polling Cycle — Happy Path

```mermaid
sequenceDiagram
    autonumber
    participant Cron as @Cron Scheduler<br/>(ScheduleModule)
    participant Orch as PollingOrchestratorService<br/>(omnichat-service)
    participant DB as PostgreSQL<br/>(Prisma)
    participant Registry as PollingRegistry
    participant State as PollingStateService
    participant Poller as IMarketplacePoller<br/>(e.g. ShopeePoller)
    participant Creds as CredentialsService
    participant MktAPI as Marketplace API<br/>(Shopee/Lazada/TikTok)
    participant Gateway as omnichat-gateway<br/>(TCP → SQS)
    participant SQS as AWS SQS FIFO
    participant Worker as omnichat-normalizer-worker
    participant OmniSvc as omnichat-service<br/>(Messages)

    Note over Cron,Orch: Every 5 minutes (configurable via POLLING_CRON_EXPRESSION)

    Cron->>Orch: runCycle()

    %% Phase 1: Load active marketplace accounts
    Orch->>DB: findMany(ChannelAccount)<br/>WHERE status='active'<br/>AND connection_status='connected'<br/>AND channel_type IN (shopee, lazada, tiktok)
    DB-->>Orch: ChannelAccount[] (N accounts)

    Note over Orch: Split accounts into chunks<br/>based on POLLING_CONCURRENCY_LIMIT (default: 10)

    %% Phase 2: Process each account (per chunk, Promise.allSettled)
    loop Each chunk (concurrent via Promise.allSettled)
        loop Each account in chunk
            Orch->>Registry: get(account.channel_type)
            Registry-->>Orch: IMarketplacePoller instance

            loop Each pollType (chat, order)
                %% Phase 3: Check backoff
                Orch->>State: isInBackoff(accountId, pollType)
                State->>DB: findUnique(MarketplacePollingState)
                DB-->>State: state record
                State-->>Orch: false (not in backoff)

                %% Phase 4: Get last_fetch_at
                Orch->>State: getState(accountId, pollType)
                State-->>Orch: { last_fetch_at: timestamp }

                Note over Orch: Build PollingContext<br/>since = last_fetch_at ?? (now - 5min)

                %% Phase 5: Execute poll
                Orch->>Poller: poll(account, context)

                %% Phase 5a: Poller gets credentials
                Poller->>Creds: getDecryptedCredential(accountId, 'access_token')
                Creds-->>Poller: access_token (decrypted)

                %% Phase 5b: Call marketplace API
                Poller->>MktAPI: GET /chat/messages?since={timestamp}
                MktAPI-->>Poller: { messages: [...] }

                %% Phase 5c: Map to RawWebhookMessage format
                Note over Poller: Map API response →<br/>RawWebhookMessage[] format<br/>(source_category: 'fetch_history',<br/>fetch_batch_id: uuid)

                %% Phase 5d: Send to gateway for SQS enqueue
                Poller->>Gateway: TCP { cmd: 'enqueue_polled_messages' }<br/>payload: RawWebhookMessage[]
                Gateway->>SQS: sendMessage (FIFO)<br/>MessageGroupId: {platform}-{channelId}-{sourceUserId}
                SQS-->>Gateway: ack
                Gateway-->>Poller: success

                Poller-->>Orch: PollingOutcome { itemsIngested: N, rateLimited: false }

                %% Phase 6: Update state — mark success
                Orch->>State: markSuccess(accountId, pollType, lastEventAt)
                State->>DB: UPSERT MarketplacePollingState<br/>SET last_fetch_at, reset failures
                DB-->>State: updated
            end
        end
    end

    Note over Orch: Log summary:<br/>accounts: N, ingested: X, failures: Y, durationMs: Z

    %% Phase 7: Downstream processing (existing pipeline)
    Note over SQS,OmniSvc: ⬇️ Downstream — both paths share the same pipeline

    Worker->>SQS: ReceiveMessage (long-poll, WaitTimeSeconds=5)
    SQS-->>Worker: RawWebhookMessage batch

    Worker->>OmniSvc: POST /raw-events (store raw payload)
    OmniSvc-->>Worker: rawEventId

    Note over Worker: ChannelMapperRegistry.normalize()<br/>→ ShopeeChannelMapper / LazadaChannelMapper

    alt Normalization success
        Worker->>OmniSvc: POST /messages/inbound<br/>(NormalizedEvent with marketplace metadata)
        OmniSvc-->>Worker: messageId

        Note over OmniSvc: enrichContact → UPSERT Contact<br/>→ resolveConversation<br/>→ INSERT Message (idempotent)

        Worker->>SQS: DeleteMessage (ack)
    else Normalization failed
        Worker->>OmniSvc: PATCH /raw-events/:id<br/>{ normalization_status: 'failed', error_detail }
        OmniSvc-->>Worker: updated

        Worker->>SQS: DeleteMessage (ack)
    end
```

---

## 2. Rate Limit Handling Flow

```mermaid
sequenceDiagram
    autonumber
    participant Orch as PollingOrchestratorService
    participant State as PollingStateService
    participant Backoff as BackoffService
    participant Poller as IMarketplacePoller
    participant MktAPI as Marketplace API
    participant DB as PostgreSQL

    Orch->>State: isInBackoff(accountId, 'chat')
    State-->>Orch: false

    Orch->>Poller: poll(account, context)
    Poller->>MktAPI: GET /chat/messages
    MktAPI-->>Poller: HTTP 429 Too Many Requests<br/>Retry-After: 60

    Note over Poller: Catch 429 — do not throw<br/>return outcome { rateLimited: true,<br/>retryAfterMs: 60000 }

    Poller-->>Orch: PollingOutcome { rateLimited: true, retryAfterMs: 60000 }

    Orch->>Backoff: calculateRateLimitBackoffMs(60, consecutiveFailures)
    Backoff-->>Orch: 60000ms (using value from Retry-After header)

    Orch->>Backoff: getBackoffUntil(60000)
    Backoff-->>Orch: backoffUntil = now + 60s

    Orch->>State: markFailure(accountId, 'chat', 'rate_limited', backoffUntil)
    State->>DB: UPSERT MarketplacePollingState<br/>SET consecutive_failures++,<br/>backoff_until = now + 60s
    DB-->>State: updated

    Note over Orch: ⚠️ Log warning:<br/>"[rate-limit] shopee/shop123 — backoff until ..."

    Note over Orch,State: ⏭️ Next cycle (5 min later)...

    Orch->>State: isInBackoff(accountId, 'chat')
    State->>DB: findUnique(MarketplacePollingState)
    DB-->>State: { backoff_until: now + 60s }

    alt backoff_until > now
        State-->>Orch: true (still in backoff)
        Note over Orch: ⏭️ SKIP — do not poll this account in this cycle
    else backoff_until <= now (backoff expired)
        State-->>Orch: false
        Note over Orch: ✅ Resume polling normally
    end
```

---

## 3. Error Handling with Exponential Backoff

```mermaid
sequenceDiagram
    autonumber
    participant Orch as PollingOrchestratorService
    participant State as PollingStateService
    participant Backoff as BackoffService
    participant Poller as IMarketplacePoller
    participant MktAPI as Marketplace API
    participant DB as PostgreSQL

    Note over Orch: Cycle N — first failure

    Orch->>Poller: poll(account, context)
    Poller->>MktAPI: GET /chat/messages
    MktAPI-->>Poller: ❌ HTTP 500 Internal Server Error

    Note over Poller: Catch error, return outcome<br/>or throw (Orchestrator will catch)

    Poller-->>Orch: ❌ throws Error("API returned 500")

    Note over Orch: try/catch catches the error

    Orch->>State: getState(accountId, 'chat')
    State-->>Orch: { consecutive_failures: 0 }

    Orch->>Backoff: calculateBackoffMs(1)
    Note over Backoff: 60,000 × 2^(1-1) = 60,000ms (1 min)
    Backoff-->>Orch: 60000ms

    Orch->>Backoff: getBackoffUntil(60000)
    Backoff-->>Orch: now + 1 min

    Orch->>State: markFailure(accountId, 'chat', "API returned 500", backoffUntil)
    State->>DB: UPSERT SET consecutive_failures=1,<br/>backoff_until=now+1min
    DB-->>State: updated

    Note over Orch: 🔴 Log error:<br/>"[error] shopee/shop123 — API returned 500<br/>(failures=1, backoff=60000ms)"

    Note over Orch,Backoff: ⏭️ Next failed cycle — consecutive_failures = 2

    Orch->>Backoff: calculateBackoffMs(2)
    Note over Backoff: 60,000 × 2^(2-1) = 120,000ms (2 min)
    Backoff-->>Orch: 120000ms

    Note over Orch,Backoff: ⏭️ consecutive_failures = 3 → 4 min
    Note over Orch,Backoff: ⏭️ consecutive_failures = 4 → 8 min
    Note over Orch,Backoff: ⏭️ consecutive_failures = 5+ → 16 min (cap)

    Note over Orch,DB: ✅ On successful poll — reset everything

    Orch->>State: markSuccess(accountId, 'chat', lastEventAt)
    State->>DB: UPSERT SET consecutive_failures=0,<br/>backoff_until=NULL,<br/>last_fetch_at=lastEventAt
```

---

## 4. Full System Overview — Polling vs Webhook Paths

```mermaid
sequenceDiagram
    autonumber
    participant ExtChannel as External Channel<br/>(LINE / Facebook)
    participant MktAPI as Marketplace API<br/>(Shopee / Lazada / TikTok)
    participant CronSched as @Cron Scheduler
    participant Orch as PollingOrchestratorService<br/>(omnichat-service)
    participant Poller as IMarketplacePoller
    participant Gateway as omnichat-gateway
    participant SQS as AWS SQS FIFO
    participant Worker as omnichat-normalizer-worker
    participant OmniSvc as omnichat-service

    Note over ExtChannel,Gateway: ========== PATH A: Webhook (LINE, Facebook, Instagram) ==========

    ExtChannel->>Gateway: POST /webhooks/:channel (HTTP)
    Note over Gateway: WebhookSignatureGuard<br/>→ ChannelExtractorService.extract()<br/>→ WebhookDeduplicationService<br/>→ QueueService.sendMessage()
    Gateway->>SQS: sendMessage (FIFO)

    Note over CronSched,Poller: ========== PATH B: Polling (Shopee, Lazada, TikTok) ==========

    CronSched->>Orch: runCycle() (every 5 min)
    Orch->>Orch: loadActiveMarketplaceAccounts()
    Orch->>Poller: poll(account, context)
    Poller->>MktAPI: GET /chat/messages?since=...
    MktAPI-->>Poller: messages data
    Note over Poller: Map → RawWebhookMessage format
    Poller->>Gateway: TCP: enqueue polled messages
    Gateway->>SQS: sendMessage (FIFO)

    Note over SQS,OmniSvc: ========== SHARED PIPELINE (used by both paths) ==========

    Worker->>SQS: ReceiveMessage (long-poll)
    SQS-->>Worker: message batch

    Worker->>OmniSvc: POST /raw-events
    Worker->>Worker: ChannelMapper.normalize()
    Worker->>OmniSvc: POST /messages/inbound
    Worker->>SQS: DeleteMessage (ack)

    Note over OmniSvc: Contact UPSERT → Conversation resolve → Message INSERT
```

---

## 5. Polling State Machine — per (account × pollType)

> Each marketplace account runs **2 independent state machines** in parallel:
> one for `poll_type = chat` and one for `poll_type = order`.
> A backoff or failure on `chat` does **not** affect the `order` state, and vice versa.
>
> Example — Shopee Shop A:
> - `(ca-001, chat)` → InBackoff (rate limited)
> - `(ca-001, order)` → Polling normally ✓

```mermaid
stateDiagram-v2
    [*] --> NeverPolled: Account connected<br/>(no MarketplacePollingState record yet)

    NeverPolled --> Polling: Cron triggers<br/>(since = now - 5min)

    Polling --> Success: poll() returns<br/>rateLimited=false
    Polling --> RateLimited: poll() returns<br/>rateLimited=true
    Polling --> Failed: poll() throws<br/>or returns error

    Success --> Polling: Next cron cycle<br/>(since = last_fetch_at)

    RateLimited --> InBackoff: markFailure()<br/>backoff_until = now + Retry-After
    Failed --> InBackoff: markFailure()<br/>backoff_until = exponential

    InBackoff --> Skipped: Cron triggers but<br/>backoff_until > now
    Skipped --> InBackoff: Stay in backoff

    InBackoff --> Polling: Cron triggers and<br/>backoff_until <= now

    note right of Success
        consecutive_failures = 0
        backoff_until = NULL
        last_fetch_at = updated
    end note

    note right of InBackoff
        Exponential backoff:
        1 fail → 1 min
        2 fail → 2 min
        3 fail → 4 min
        4 fail → 8 min
        5+ fail → 16 min (cap)
    end note
```

---

## 6. Data Model — MarketplacePollingState

```mermaid
erDiagram
    ChannelAccount ||--o{ MarketplacePollingState : "has many"

    ChannelAccount {
        string id PK
        string tenant_id FK
        string channel_type "shopee | lazada | tiktok | line | ..."
        string external_account_id "shop_id / seller_id"
        string status "active | inactive"
        string connection_status "connected | disconnected | ..."
        datetime deleted_at
    }

    MarketplacePollingState {
        string id PK
        string channel_account_id FK
        string poll_type "chat | order"
        datetime last_fetch_at "nullable — cursor for next fetch"
        datetime backoff_until "nullable — skip if > now"
        int consecutive_failures "default 0"
        string last_error "nullable"
        datetime created_at
        datetime updated_at
    }
```

---

## Legend

| Symbol | Meaning |
|--------|---------|
| `→` (solid arrow) | Synchronous call / request |
| `-->>` (dashed arrow) | Response / return |
| `loop` | Iteration over collection |
| `alt` | Conditional branching |
| `Note` | Explanation or context |
