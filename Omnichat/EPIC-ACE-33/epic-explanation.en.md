# EPIC ACE-33: Marketplace Connectivity Baseline — Plain English Guide

## Overview

Marketplace Connectivity Baseline is the set of stories that enables ACE to support 3 marketplaces (TikTok, Shopee, Lazada) end-to-end — from connecting an account → fetching messages → normalizing data → storing in DB → allowing agents to reply.

**Simple analogy:**
LINE/Facebook push webhooks to us whenever something happens (like a customer "calling us"). But Shopee/Lazada/TikTok don't have fully reliable webhooks — we have to be the one to "call them" on a schedule instead. This EPIC is about building that outbound calling system.

---

## What do the 6 Stories do?

| Story | Name | Purpose |
|---|---|---|
| **ACE-701** | Marketplace Channel Onboarding | Connect marketplace accounts + store credentials |
| **ACE-702** | Scheduled Polling Framework | The cron loop that fetches data on a schedule (infrastructure) |
| **ACE-703** | TikTok Connector Baseline | TikTok-specific API integration |
| **ACE-704** | Shopee Connector Baseline | Shopee-specific API integration |
| **ACE-705** | Lazada Connector Baseline | Lazada-specific API integration |
| **ACE-706** | Marketplace Threading Rules | Rules for grouping messages into the correct conversation |

### Dependency Order

```
ACE-701 (connect accounts)
    │
    ▼
ACE-702 (Polling Framework)  ←── shared infrastructure used by 703/704/705
    │
    ├──▶ ACE-703 (TikTok Connector)
    ├──▶ ACE-704 (Shopee Connector)
    └──▶ ACE-705 (Lazada Connector)

ACE-706 (Threading Rules)  ←── cross-cutting, applied inside 703/704/705
```

> ACE-701 and ACE-702 must be completed before work on ACE-703–705 can begin.

---

## 1. Architecture Overview — Webhook vs Polling

Before this EPIC, ACE only received data via **Webhook** (channels push data to us). After this EPIC, ACE supports both paths:

```
                        ┌────────────────────────────────┐
PATH A: Webhook         │                                │
(LINE, Facebook, IG)    │  External Channel              │
                        │  POST /webhooks/:channel ──▶   │
                        │                                │
PATH B: Polling ← NEW   │  Marketplace API               │
(Shopee, Lazada, TikTok)│  ◀── GET /chat/messages?since= │
                        └────────────────────────────────┘
                                        │
                                        ▼
                               omnichat-gateway
                                        │
                                        ▼
                                 AWS SQS FIFO
                                        │
                                        ▼
                           omnichat-normalizer-worker
                                        │
                                        ▼
                              omnichat-service (DB)
```

**Key point:** Both paths share the same pipeline after entering SQS — no new normalization or DB logic is needed downstream.

---

## 2. ACE-701: Marketplace Channel Onboarding — How does connecting an account work?

### What gets stored in the system

When an admin connects a Shopee shop to ACE, a record is created in `ChannelAccount`:

```
ChannelAccount {
  id:                  "ca-uuid-001"
  tenant_id:           "tenant-abc"
  channel_type:        "shopee"
  external_account_id: "shop-12345"     ← Shopee shop_id
  status:              "active"
  connection_status:   "connected"
  credential_ref_id:   "vault-ref-xyz"  ← pointer to encrypted vault (no raw token stored)
}
```

### How are credentials stored?

Marketplace tokens are **never stored directly** in the DB — they are stored in an encrypted Credential Vault, and only the `credential_ref_id` is kept as a reference.

```
❌ Wrong:  channel_account.access_token = "eyJhbGci..."
✅ Correct: channel_account.credential_ref_id = "vault-ref-xyz"
            vault["vault-ref-xyz"] = encrypt("eyJhbGci...")
```

### How many accounts per tenant?

Multi-account is supported — store ABC can connect 2 Shopee shops, 1 Lazada shop, etc.

```
Store ABC (tenant_id = abc)
├── Shopee Thailand    (channel_type=shopee, external_account_id=shop-001)
├── Shopee Malaysia    (channel_type=shopee, external_account_id=shop-002)
└── Lazada TH          (channel_type=lazada, external_account_id=seller-999)
```

---

## 3. ACE-702: Scheduled Polling Framework — How does the cron loop work?

### Why do we need Polling?

Shopee/Lazada/TikTok don't provide fully reliable real-time webhooks, so we proactively ask their APIs every X minutes: "Are there any new messages?"

### Main Flow

```
Every 5 minutes:
1. Load all marketplace accounts where status=active
2. Split into chunks of 10 accounts (concurrency limit)
3. For each account × each pollType (chat, order):
   - If account is in backoff → skip
   - Get last_fetch_at (timestamp of last successful fetch)
   - Call Marketplace API: GET /messages?since=last_fetch_at
   - Send results into SQS → normal pipeline
   - Update last_fetch_at to the latest event timestamp
```

### New Table: MarketplacePollingState

Stores a "bookmark" for how far each account has been fetched.

| Field | Meaning | Example |
|---|---|---|
| `channel_account_id` | Which account | "ca-uuid-001" (Shopee Shop A) |
| `poll_type` | What type of data is being fetched | "chat" or "order" |
| `last_fetch_at` | Timestamp of last successful fetch | 2026-03-10 10:00:00 |
| `backoff_until` | Do not poll until this time | 2026-03-10 10:01:00 (after rate limit) |
| `consecutive_failures` | How many failures in a row | 2 |
| `last_error` | Most recent error message | "rate_limited" |

### Why is last_fetch_at important?

```
Cycle 1 (10:00):  since = 09:55  →  fetch messages 09:55–10:00  →  last_fetch_at = 10:00
Cycle 2 (10:05):  since = 10:00  →  fetch messages 10:00–10:05  →  no duplicates ✓
```

Without `last_fetch_at`, every cycle would re-fetch everything from the beginning.

### Backoff — preventing rate limit issues

```
1st failure  →  wait 1 minute
2nd failure  →  wait 2 minutes
3rd failure  →  wait 4 minutes
4th failure  →  wait 8 minutes
5th+ failure →  wait 16 minutes (cap)

If the API responds 429 with Retry-After: 60 → use that header value directly
```

---

## 4. ACE-703/704/705: Platform Connectors — How are they different?

All connectors implement the same `IMarketplacePoller` interface but handle platform-specific API logic.

```typescript
interface IMarketplacePoller {
  poll(account: ChannelAccount, context: PollingContext): Promise<PollingOutcome>
}
```

| Connector | API | Key Difference |
|---|---|---|
| **TikTok** (ACE-703) | TikTok Shop API | Includes order context when a buyer initiates chat from an order page |
| **Shopee** (ACE-704) | Shopee Open API v2 | Rate limit is per shop; must be managed per account |
| **Lazada** (ACE-705) | Lazada Seller API | Region-specific endpoints (TH, MY, SG, etc.) |

### Each Connector does 4 things

```
1. Inbound    — receive new messages from the API (via polling)
2. Outbound   — send reply messages from the Agent back to the platform
3. Normalize  — convert platform-specific format → unified Omni format
4. History    — fetch historical chat messages (on first connection)
```

### Example: Shopee message → Omni format

```
Shopee raw:                          Omni normalized:
{                                    {
  "conversation_id": "conv-001",       "external_message_id": "conv-001-msg-001",
  "message_id": "msg-001",             "channel_type": "shopee",
  "from_user": { "uid": "B456" },      "external_user_id": "B456",
  "content": {                         "content_type": "text",
    "type": "text",                    "content": "Is this item still available?",
    "text": "Is this item available?"  "source_category": "fetch_history",
  },                                   "fetch_batch_id": "batch-uuid"
  "create_time": 1710000000           }
}
```

`source_category: "fetch_history"` indicates this data came from polling, not a live webhook.

---

## 5. ACE-706: Threading Rules — How are messages grouped into the right conversation?

### The Problem: marketplace conversation keys differ from social channels

LINE/Facebook provide a clear `reply_token` or `thread_id`. But some marketplace platforms identify buyers with a `uid` that may appear across multiple shops. Without careful handling, messages from a buyer in Shop A could be mixed into Shop B's conversation.

### Rule v1: Conversation Key

```
conversation_key = tenant_id + channel_account_id + external_buyer_id

If external_thread_id is available:
conversation_key = tenant_id + channel_account_id + external_buyer_id + external_thread_id
```

### Example: Why is channel_account_id required?

```
Store ABC has 2 shops:

Shopee Shop A (ca-001):
  Buyer uid=B456 → conversation key: abc + ca-001 + B456 → Conversation #100

Shopee Shop B (ca-002):
  Buyer uid=B456 → conversation key: abc + ca-002 + B456 → Conversation #101

Same uid, but different shops → separate conversations ✓
```

> R1 Limitation: If the same buyer contacts both Shopee Shop A and Shopee Shop B, the system treats them as two separate contacts in separate conversations. Cross-shop identity merging is not supported in this version.

---

## 6. Shared Pipeline — the existing pipeline handles marketplaces out of the box

The normalizer-worker and omnichat-service require minimal changes — marketplaces reuse the same pipeline:

```
[SQS Message]
      │
      ▼
omnichat-normalizer-worker
  ├── ChannelMapperRegistry.normalize()
  │     ├── ShopeeChannelMapper  ← new
  │     ├── LazadaChannelMapper  ← new
  │     └── TikTokChannelMapper  ← new
  └── POST /internal/messages/inbound
            │
            ▼
      omnichat-service
        ├── UPSERT Contact
        ├── UPSERT Conversation  ← uses threading key from MKT-06
        └── INSERT Message (idempotency check to prevent duplicates)
```

---

## Summary by the numbers

| Category | Count |
|---|---|
| Stories | 6 stories (ACE-701 to ACE-706) |
| Marketplaces supported | 3 (TikTok, Shopee, Lazada) |
| New tables | 1 (MarketplacePollingState) |
| Updated tables | 1 (ChannelAccount — added relation) |
| New connectors | 3 (IMarketplacePoller per platform) |
| Total subtasks | 23 subtasks |

---

## End-to-End Example: Shopee buyer sends a message → Agent replies

```
1. Admin connects Shopee Shop A to ACE (MKT-01)
   → Creates ChannelAccount + stores access_token in credential vault

2. Cron fires every 5 minutes (MKT-02)
   → Loads Shop A → not in backoff
   → Gets last_fetch_at = 10:00

3. ShopeePoller calls Shopee API (MKT-04)
   → GET /chat/messages?since=10:00
   → Receives message "Is this item still available?" from buyer uid=B456

4. Maps to RawWebhookMessage → sends into SQS via Gateway TCP

5. Normalizer Worker picks up from queue
   → ShopeeChannelMapper.normalize()
   → POST /internal/messages/inbound
   → UPSERT Contact (B456), UPSERT Conversation (key: tenant+ca-001+B456)
   → INSERT Message

6. Agent sees it in Inbox
   → Opens the conversation → replies "Yes, ready to ship!"
   → POST /api/v1/messages
   → Shopee Outbound API → buyer sees reply in Shopee Chat ✓

7. Next polling cycle
   → markSuccess: last_fetch_at = 10:05
   → Next cycle fetches from 10:05 onwards (no duplicates ✓)
```
