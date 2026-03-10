# EPIC ACE-31: Normalized Data Platform v1 — Plain English Explanation

## Overview

The Normalized Data Platform (NDP) is a central system that receives messages from all channels (LINE, Facebook, Instagram, TikTok, Shopee, Lazada) and converts them into a unified format, so that Agents (customer service staff) can work without caring which channel the customer messaged from.

**Simple analogy:**
Think of it as a universal translator — customers speak 6 different languages (LINE, FB, IG, TikTok, Shopee, Lazada), the system translates everything into one common language and hands it to the Agent.

---

## 1. ER Diagram — Database Tables (What data do we store?)

The ER Diagram describes what data the system stores and how each piece relates to another.

### 7 Tables in 2 Groups

#### Group A: Business Tables (6 tables) — Core operational data

| Table | What is it? | Example |
|---|---|---|
| **tenant** | A company using the platform | "ABC Shop" — one tenant can have multiple channels |
| **channel_accounts** | Connected channel accounts | "ABC Shop's LINE OA", "ABC Shop's Facebook Page" |
| **contacts** | Customers who have messaged | "John messaged via LINE" (external_user_id = U1234) |
| **conversations** | Chat rooms (1 customer per channel = 1 conversation) | "Chat between John and ABC Shop's LINE OA" |
| **messages** | Individual messages | "Hello, I'm interested in your product" — 1 conversation has many messages |
| **attachments** | File attachments (images, videos, documents) | "photo.jpg that John sent along with a message" |

#### Group B: System Tables (1 table) — Behind-the-scenes data

| Table | What is it? | Example |
|---|---|---|
| **raw_events** | Raw webhook payloads (kept for debugging + normalization tracking) | Raw JSON from LINE before transformation — includes all fields LINE sent + `normalization_status` indicating success or failure |

### Relationships — Read it like this

```
ABC Shop (tenant)
├── LINE OA (channel_account)
│   ├── John (contact) — messaged via LINE
│   │   └── Conversation #1 (chat with LINE OA)
│   │       ├── Message: "Hello, I'm interested in your product"
│   │       ├── Message: "Can you send me a product photo?"
│   │       └── Message: [product photo]
│   │           └── Attachment: product.jpg (stored in S3)
│   └── Jane (contact) — messaged via LINE
│       └── Conversation #2
│
├── Facebook Page (channel_account)
│   └── John (contact) — same person, but messaged via FB = different contact record
│       └── Conversation #3
│
└── Shopee Shop (channel_account)
    └── ...
```

> **Key point:** The same customer messaging from different channels = separate contact records, because external_user_id differs (LINE uses U1234, FB uses PSIDxxxx)

### Tenant Isolation — Data separation between companies

Every table has `tenant_id` — Company A can never see Company B's data.

```
ABC Shop (tenant_id = aaa) → sees only its own data
XYZ Shop (tenant_id = bbb) → sees only its own data
```

### Soft Delete

All 6 business tables have `deleted_at` — deletion doesn't permanently remove data, it just hides it. Can be reversed.

```
DELETE channel_account → SET deleted_at = NOW()
Data remains in the database; normal queries filter with WHERE deleted_at IS NULL
```

System table (raw_events) has **no** `deleted_at` — kept permanently for audit purposes.

---

## 2. Sequence Diagram — Execution Order (What happens in what order?)

The Sequence Diagram describes how data flows through services when an event occurs, step by step.

### 5 Services in the System

```
                          ┌──────────────────┐
Customer sends message ──▶│ Omnichat Gateway │  ←── "Guard" — receives webhooks, validates signatures
                          └────────┬─────────┘
                                   │ Enqueue (SQS)
                                   ▼
                          ┌──────────────────┐
                          │ Normalizer Worker│  ←── "Translator" — normalizes data
                          └────────┬─────────┘
                                   │ HTTP calls
                                   ▼
                          ┌──────────────────┐
                          │ Omnichat Service │  ←── "Brain" — owns DB, sends outbound messages
                          └────────┬─────────┘
                                   │
                          ┌────────┴─────────┐
                          ▼                  ▼
                     ┌──────────┐     ┌──────────────┐
                     │PostgreSQL│     │ File Service  │──▶ S3
                     └──────────┘     └──────────────┘
```

### 5 Flows — Organized by use case

#### Flow 1: Customer sends inbound message — Most important

**Scenario:** John sends "I'm interested in your product" + photo.jpg via LINE

```
Steps:

1. LINE sends webhook to Gateway
   → Gateway validates signature (HMAC-SHA256) ✓
   → Enqueue to SQS → Respond 200 OK to LINE immediately (no waiting for processing)

2. Worker picks from queue
   → PII Redaction: mask userId, avatar (message content is NOT redacted)
   → Store raw payload in raw_events (for debugging)

3. Worker normalizes data
   → LINE format → Unified normalized format

4. Omnichat Service persists data
   → UPSERT contact (John — if exists, update last_seen_at)
   → UPSERT conversation (chat room with John, set is_read=false)
   → INSERT message ("I'm interested in your product")
   → Acknowledge SQS (done — remove from queue)

5. Worker downloads attachment (after ack — doesn't block the queue)
   → Download photo.jpg from LINE server
   → Validate size/type → Upload to S3
   → Update status: pending → uploaded
```

> **Why use a queue (SQS)?** If LINE sends 1,000 webhooks simultaneously, we must respond 200 OK quickly, then process later. If we respond too slowly, LINE will retry.

#### Flow 2: Agent sends outbound message

**Scenario:** Agent replies to John with "Product is ready to ship" + image attachment

```
1. Agent clicks Send in Inbox UI
   → API Gateway validates auth + tenant_id

2. Omnichat Service:
   → Upload image to S3 (if attachment exists)
   → INSERT message (direction='outbound', status='pending')
   → UPDATE conversation (last_message_at, last_message_preview)

3. Send to LINE API (Reply/Push Message)
   → Success → UPDATE message status='sent'
   → Failure → UPDATE message status='failed' → Notify Agent
```

#### Flow 3: Agent opens Inbox (Conversation List)

**Scenario:** Agent opens Inbox and sees conversation list sorted by most recent

```
GET /api/v1/conversations?status=open&channel_type=LINE&limit=20

Response:
[
  { "contact": "John", "preview": "I'm interested", "last_message_at": "10:30", "is_read": false },
  { "contact": "Jane", "preview": "Order placed", "last_message_at": "10:25", "is_read": true },
  ...20 items
]
Cursor-based pagination — click Load More = fetch next 20 items
```

> **Pagination consistency:** Cursor-based pagination on `last_message_at` ensures no duplicates or skips even when new messages arrive while scrolling.

#### Flow 4: Agent opens a chat (Message Timeline)

**Scenario:** Agent clicks into John's chat and sees messages ordered by time

```
GET /api/v1/conversations/{id}/messages?limit=20

Response:
[
  { "sender": "John", "content": "Hello", "type": "text" },
  { "sender": "John", "content": "", "type": "image",
    "attachments": [{ "id": "att-1", "type": "image", "size": 245678, "status": "uploaded",
      "file_url": "https://{bucket}.s3.amazonaws.com/{tenant_id}/att-1/photo.jpg" }]
  },
  { "sender": "Agent Nid", "content": "Product is ready to ship", "type": "text" },
]

Note: attachment includes file_url (static public URL, no expiry) — browser can load image immediately
```

> **Why include `file_url` in the Timeline?** S3 bucket is public, so `file_url` is a permanent static URL (no expiry). Including it directly in the timeline avoids an extra API call per image. Endpoint `GET /api/v1/attachments/:id/download` is still available for checking pending/failed status.

> **Pagination consistency:** Cursor-based pagination on `created_at` ensures no duplicates or skips even when new messages arrive. New messages are delivered via real-time push (WebSocket/SSE), not via pagination.

#### Flow 5: Marketplace (Shopee/Lazada) — 3 event types

```
1. Chat Message (customer chats in Shopee Chat)
   → Normalized the same way as LINE/FB

2. Order Reference (customer places order → creates a reference message)
   → Stores metadata: { order_id: "SHP-001", shop_id: "shop-abc" }
   → Agent sees in chat: "Customer placed order SHP-001"

3. Fetch History (pull historical chat messages)
   → Pulled in batches → stored one message at a time
   → Idempotency key prevents duplicates (if message overlaps with live = skip)
```

---

## 3. API Table — All Endpoints (What can you call?)

The API Table describes all available endpoints, who can call them, what to send, and what comes back.

### Organized by Caller

#### Group 1: Channel Platforms call these (6 endpoints)

```
LINE, Facebook, Instagram, TikTok, Shopee, Lazada
  ──▶ POST /webhooks/{channel_type}

Example: LINE sends a webhook
POST /webhooks/line
Header: X-Line-Signature: abc123...
Body: { "events": [{ "type": "message", "message": { "text": "Hello" } }] }

→ Gateway validates signature → Enqueue → Respond 200 OK
```

#### Group 2: Agent / Inbox UI calls these (16 endpoints)

**Channel Accounts (5)** — Manage connected channels

```
POST   /api/v1/channel-accounts          Create new account (e.g. connect a new LINE OA)
GET    /api/v1/channel-accounts          List all accounts
GET    /api/v1/channel-accounts/:id      Get account details
PATCH  /api/v1/channel-accounts/:id      Update account (rename, change credential)
DELETE /api/v1/channel-accounts/:id      Delete account (soft delete)
```

**Contacts (3)** — Customer data

```
GET    /api/v1/contacts                  Search contacts
GET    /api/v1/contacts/:id              Get contact details
PATCH  /api/v1/contacts/:id              Update contact metadata

Example: Search for contact named "John" on LINE
GET /api/v1/contacts?channel_type=LINE&search=John

→ { "data": [{ "display_name": "John", "external_user_id": "U1234", "last_seen_at": "..." }] }
```

**Conversations (4)** — Chat rooms

```
GET    /api/v1/conversations             List chats (Inbox view)
GET    /api/v1/conversations/:id         Get chat details
PATCH  /api/v1/conversations/:id         Update status (open/closed/snoozed) or mark as read
GET    /api/v1/conversations/:id/messages View messages in chat (Timeline)

Example: Agent opens Inbox showing open LINE chats
GET /api/v1/conversations?status=open&channel_type=LINE&limit=20&sort=last_message_at&order=desc

→ Returns 20 chats sorted by most recent, with last message preview
```

**Messages (2)** — Messages

```
POST   /api/v1/messages                  Send outbound message (Agent replies to customer)
GET    /api/v1/messages/:id              Get message details + attachments

Example: Agent sends a message to customer
POST /api/v1/messages
{
  "conversation_id": "conv-uuid",
  "content": "Product is ready to ship",
  "content_type": "text",
  "sender_display_name": "Agent Nid"
}

→ { "data": { "id": "msg-uuid", "status": "sent" } }
```

**Attachments (2)** — File attachments

```
GET    /api/v1/attachments/:id           Get file metadata
GET    /api/v1/attachments/:id/download  Get static URL for download

Example: Agent clicks to view an image the customer sent
GET /api/v1/attachments/att-uuid/download

→ { "data": { "url": "https://{bucket}.s3.../tenant-id/att-id/photo.jpg" } }
→ Browser loads image from this permanent URL (no expiry)
```

#### Group 3: Service-to-Service — Internal (7 endpoints)

```
Not accessible externally — API Gateway blocks these

Worker → Omnichat Service:
  POST  /internal/raw-events                    Store raw webhook payload
  POST  /internal/messages/inbound              Store normalized data
  POST  /internal/attachments                   Create attachment record
  PATCH /internal/attachments/:id               Update attachment status
  PATCH /internal/raw-events/:id                Update normalization status (on failure)

Omnichat Service / Worker → File Service:
  POST  /files/presigned-url                    Get presigned upload URL (returns upload_url + static file_url)
  POST  /files/upload                           Upload file to S3 (returns storage_key + static file_url)
```

---

## Summary Numbers

| Category | Count |
|---|---|
| Database tables | 7 tables |
| HTTP Endpoints (NDP) | 24 endpoints (6 webhook + 11 public + 5 internal + 2 file service) |
| Sequence Flows | 5 flows |
| Supported channels | 6 channels (LINE, Facebook, Instagram, TikTok, Shopee, Lazada) |

---

## End-to-End Example: Customer sends message → Agent replies

```
1. John sends "I'm interested in your product" + photo.jpg via LINE

2. LINE → POST /webhooks/line → Gateway validates signature → SQS

3. Worker picks from queue:
   - PII Redaction (mask userId, avatar in raw payload; message content NOT redacted)
   - Store raw event → POST /internal/raw-events
   - Normalize LINE format → Normalized format
   - Success → UPDATE raw_events SET normalization_status='success'
   - Failure → UPDATE raw_events SET normalization_status='failed' + error_detail
   - Persist data → POST /internal/messages/inbound
     → UPSERT contact (John)
     → UPSERT conversation (chat room with John, is_read=false)
     → INSERT message ("I'm interested in your product")
   - Acknowledge SQS (done)
   - Download photo.jpg from LINE → Upload to S3 → PATCH /internal/attachments/:id

4. Agent Nid opens Inbox:
   - GET /api/v1/conversations?status=open → sees John's chat (bold = unread)

5. Agent Nid clicks into the chat:
   - GET /api/v1/conversations/{id}/messages → sees messages + attachment metadata (includes file_url)
   - PATCH /api/v1/conversations/{id} { is_read: true } → mark as read

6. Agent Nid replies "Product is ready to ship":
   - POST /api/v1/messages → INSERT message → Send to LINE API → status='sent'

7. John sees the reply in LINE
```
