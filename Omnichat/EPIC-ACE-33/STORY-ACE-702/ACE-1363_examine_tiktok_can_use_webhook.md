# ACE-1363: Examine TikTok Can Use Webhook — Research Findings

## Context

ACE-1363 is a subtask of "Scheduled Polling Framework v1 for Marketplace Ingest". The goal is to determine whether TikTok Shop supports webhooks for **chat/conversation messages**, which could replace the current polling-based approach.

---

## TL;DR

**Yes, TikTok Shop fully supports webhooks for chat messages.** Two key webhook events are available under the **"Customer Service"** category:

| Event | Type | Trigger | Key for ACE |
|-------|------|---------|-------------|
| **(13) New conversation** | 13 | Customer service agent joins/leaves a conversation | Useful for tracking conversation lifecycle |
| **(14) New message** | 14 | New message sent in a customer service conversation | **Primary event for chat ingestion** |

**Recommendation: Use webhooks (not polling) for TikTok chat message ingestion.** The ACE webhook infrastructure is already built — only payload extraction needs updating.

---

## Webhook Event Details (from Partner Center docs)

### (13) New Conversation
- **Trigger:** When a customer service agent joins or leaves a conversation
- **Payload:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `conversation_id` | string | The identification of the conversation |
| `create_time` | int | Unix timestamp (seconds) |

- **Example payload:**
```json
{
  "type": 13,
  "tts_notification_id": "73271123930573719l0",
  "shop_id": "7494049642642441621",
  "timestamp": 1644412885,
  "data": {
    "conversation_id": "576486316948490001",
    "create_time": 1627587506
  }
}
```

### (14) New Message — PRIMARY EVENT
- **Trigger:** When a new message is sent in a customer service conversation
- **Payload:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `message_id` | string | Message identification |
| `index` | string | Message index for sorting (newer = larger) |
| `conversation_id` | string | Conversation identification |
| `type` | string (enum) | Message type (see below) |
| `content` | string | JSON serialized content (format varies by type) |
| `create_time` | int | Unix timestamp (seconds) |
| `is_visible` | bool | Whether message should be displayed to customer |
| `sender` | object | `{ im_user_id, role }` — role can be "BUYER" etc. |

- **Message types:** `TEXT`, `IMAGE`, `ALLOCATED_SERVICE`, `NOTIFICATION`, `BUYER_ENTER_FROM_TRANSFER`, `BUYER_ENTER_FROM_PRODUCT`, `BUYER_ENTER_FROM_ORDER`, `PRODUCT_CARD`, `ORDER_CARD`, `EMOTICONS`, `VIDEO`, `LOGISTICS_CARD`, `COUPON_CARD`, `OTHER`

- **Content format examples:**
  - TEXT: `{"content": "simple text message"}`
  - IMAGE: `{"height": "290", "url": "https://...", "width": "304"}`
  - PRODUCT_CARD / BUYER_ENTER_FROM_PRODUCT: `{"product_id": "12345"}`
  - ORDER_CARD / BUYER_ENTER_FROM_ORDER: `{"order_id": "12345"}`
  - VIDEO: `{"url": "...", "width": 640, "height": 360, "duration": "20.504", ...}`
  - LOGISTICS_CARD: `{"order_id": "...", "package_id": "..."}`
  - COUPON_CARD: `{"coupon_id": "..."}`

- **Example payload:**
```json
{
  "type": 14,
  "tts_notification_id": "73271123930573719l0",
  "shop_id": "7494049642642441621",
  "timestamp": 1644412885,
  "data": {
    "content": "{\"content\":\"444\"}",
    "conversation_id": "7106888323922608l8",
    "create_time": 1681790246,
    "is_visible": true,
    "message_id": "7223234079263688l9",
    "index": "7494556010973233427",
    "type": "TEXT",
    "sender": {
      "im_user_id": "707885565181165594",
      "role": "BUYER"
    }
  }
}
```

### Common wrapper fields (all TikTok webhooks):
```json
{
  "type": "<event_type_number>",
  "tts_notification_id": "<notification_id>",
  "shop_id": "<shop_id>",
  "timestamp": "<unix_timestamp>",
  "data": { ... }
}
```

---

## All Available TikTok Shop Webhook Categories (from sidebar)

| Category | Events |
|----------|--------|
| **Affiliate Creator** | (17) Shoppable content posting, (20) Creator deauthorization, (55) Video Precheck Result, (59) Shoppable Video Precheck Tasks Result |
| **Affiliate Seller** | (33) New message listener, (56) Sample Application Status Change |
| **Customer Service** | **(13) New conversation**, **(14) New message** |
| **Fulfillment** | (36) Invoice status change |
| **Fulfilled by TikTok** | (21) Inbound FBT order status change, (22) FBT merchant onboarding, (23) Goods match, (24) FBT inventory update |
| **Logistics** | (3) Recipient address update, (4) Package update |

---

## Current ACE Codebase State

### Webhook infrastructure (ALREADY IMPLEMENTED)

| Component | File | Status |
|-----------|------|--------|
| Webhook endpoint | `apps/omnichat-gateway/src/webhook/controllers/webhook.controller.ts` | Done — `POST /webhooks/tiktok` |
| Signature validation | `apps/omnichat-gateway/src/webhook/services/webhook-validation.service.ts` | Done — HMAC-SHA256 via `x-tiktok-signature` |
| Payload extraction | `apps/omnichat-gateway/src/webhook/services/channel-extractor.service.ts` | **Needs update** — currently generic, needs TikTok message-specific mapping |
| Deduplication | `apps/omnichat-gateway/src/webhook/controllers/webhook.controller.ts` | Done |
| SQS publishing | `apps/omnichat-gateway/src/webhook/controllers/webhook.controller.ts` | Done |

### Polling infrastructure (STUB — may not be needed for chat)

| Component | File | Status |
|-----------|------|--------|
| TikTok poller | `apps/omnichat-service/src/marketplace-polling/pollers/tiktok-poller.ts` | Stub — can be deprioritized if webhooks work |

---

## BLOCKER: Customer Service API Scope ยังไม่ได้รับอนุมัติ

จากหน้า "จัดการ API ของ ACE OmniChat" ใน Partner Center:

- **Scope:** `seller.customer_service` (Scope ID: 480004)
- **Status:** อยู่ระหว่างการตรวจสอบ (Under Review)
- **Tag:** ข้อมูลที่ละเอียดอ่อน (Sensitive Data)

**ทั้ง Webhook และ Polling ใช้งานไม่ได้จนกว่า scope นี้จะได้รับอนุมัติ** เพราะ:
- Webhook events (13) New conversation และ (14) New message อยู่ภายใต้ Customer Service
- Polling APIs (Get Conversation Messages, Create Conversation, etc.) อยู่ภายใต้ scope เดียวกัน

---

## Conclusion & Recommended Next Steps

**TikTok Shop webhooks fully support chat message ingestion.** No need for polling for chat messages. **But the Customer Service scope must be approved first.**

### What needs to be done:

0. **[BLOCKER] รอ scope `seller.customer_service` ได้รับอนุมัติ** — ก่อนที่จะทำอะไรได้ทั้งหมด

1. **Configure webhook URL in TikTok Partner Center** (หลัง scope approved)
   - Point to `https://<your-domain>/webhooks/tiktok`
   - Subscribe to events (13) and (14) at minimum

2. **Update `extractTiktok()` in `channel-extractor.service.ts`**
   - Map `data.conversation_id`, `data.message_id`, `data.sender`, `data.type`, `data.content` from the event 14 payload
   - Use `data.sender.im_user_id` as `sourceUserId`
   - Use `data.sender.role` to identify buyer vs. seller messages
   - Handle the `type` field to route different content types (TEXT, IMAGE, VIDEO, etc.)

3. **Deduplication key** — Use `data.message_id` for event 14 deduplication

4. **Polling can be deprioritized** — The TikTok poller stub can remain as-is; webhooks cover the chat use case

---

## Sources
- [TikTok Shop Partner Center — (13) New Conversation](https://partner.tiktokshop.com/docv2/page/13-new-conversation)
- [TikTok Shop Partner Center — (14) New Message](https://partner.tiktokshop.com/docv2/page/14-new-message)
- [Webhook Configuration Guide](https://partner.tiktokshop.com/docv2/page/configuration-guide)
- [Get Conversation Messages API (polling fallback)](https://partner.tiktokshop.com/docv2/page/get-conversation-messages-202309)
