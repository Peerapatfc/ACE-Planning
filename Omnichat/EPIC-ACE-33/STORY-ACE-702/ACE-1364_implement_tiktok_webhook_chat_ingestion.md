# ACE-1364: Implement TikTok Webhook Chat Ingestion — Subtask Plan

> **Parent:** ACE-702 (Scheduled Polling Framework v1 for Marketplace Ingest)
> **Based on:** ACE-1363 Research Findings
> **Blocker:** `seller.customer_service` scope (ID: 480004) ต้องได้รับอนุมัติก่อน

---

## สรุป

จาก research ACE-1363 พบว่า TikTok Shop รองรับ webhook สำหรับ chat messages ได้เต็มรูปแบบ (event 13: New Conversation, event 14: New Message) ดังนั้น **ไม่จำเป็นต้องใช้ polling สำหรับ chat** — ใช้ webhook แทนได้เลย

โครงสร้าง webhook infrastructure (endpoint, signature validation, dedup, SQS) ทำเสร็จแล้ว แต่ยังขาด:
1. **Payload extraction** — `extractTiktok()` ยังเป็น generic ไม่ได้ map field จาก event 14 อย่างถูกต้อง
2. **Normalizer mapper** — ไม่มี `TikTokChannelMapper` ใน normalizer-worker (messages จะไปตกที่ DLQ)
3. **Webhook subscription** — ยังไม่ได้ configure ใน TikTok Partner Center

---

## Proposed Subtasks

### Subtask 1: Update `extractTiktok()` Payload Mapping

**Objective:** ปรับ `extractTiktok()` ให้ map field จาก TikTok event 14 (New Message) อย่างถูกต้อง

**File:** `apps/omnichat-gateway/src/webhook/services/channel-extractor.service.ts`

**Current State (ปัญหา):**
```typescript
// ❌ ใช้ body.open_id ซึ่งไม่มีใน event 14 payload
sourceUserId: body.open_id || 'unknown',
// ❌ ใช้ new Date() แทนที่จะใช้ timestamp จาก payload
timestamp: new Date(),
```

**Target State:**
```typescript
private extractTiktok(body: any, headers: Record<string, string>, { channelAccountId, tenantId }: ResolvedChannelAccount): ExtractedEvents {
  const eventType = body.type; // 13 = New Conversation, 14 = New Message
  const channelId = String(body.shop_id || '');

  // Event 14: New Message — primary chat ingestion event
  if (eventType === 14) {
    const data = body.data || {};
    return {
      messages: [{
        platform: PlatformType.TIKTOK,
        channelId,
        tenantId,
        channelAccountId,
        sourceUserId: data.sender?.im_user_id || 'unknown',
        rawPayload: body,
        timestamp: data.create_time ? new Date(data.create_time * 1000) : new Date(),
        headers,
        source_category: 'chat',
      }],
    };
  }

  // Event 13: New Conversation — conversation lifecycle
  if (eventType === 13) {
    const data = body.data || {};
    return {
      messages: [{
        platform: PlatformType.TIKTOK,
        channelId,
        tenantId,
        channelAccountId,
        sourceUserId: 'system', // ไม่มี sender ใน event 13
        rawPayload: body,
        timestamp: data.create_time ? new Date(data.create_time * 1000) : new Date(),
        headers,
        source_category: 'chat',
      }],
    };
  }

  // Other TikTok events (order, logistics, etc.) — pass through
  return {
    messages: [{
      platform: PlatformType.TIKTOK,
      channelId,
      tenantId,
      channelAccountId,
      sourceUserId: 'unknown',
      rawPayload: body,
      timestamp: new Date(body.timestamp * 1000),
      headers,
    }],
  };
}
```

**Key Mapping (Event 14 → RawWebhookMessage):**

| TikTok Field | → | RawWebhookMessage Field |
|---|---|---|
| `body.shop_id` | → | `channelId` |
| `body.data.sender.im_user_id` | → | `sourceUserId` |
| `body.data.create_time` (unix sec) | → | `timestamp` (Date, ×1000) |
| `body.data.message_id` | → | (อยู่ใน rawPayload, dedup ใช้อยู่แล้ว) |
| `body.data.conversation_id` | → | (อยู่ใน rawPayload, normalizer จะใช้) |
| `body.data.sender.role` | → | (อยู่ใน rawPayload, ใช้แยก BUYER/SELLER) |
| `body.data.type` | → | (อยู่ใน rawPayload, ใช้แยก TEXT/IMAGE/VIDEO) |

**Unit Tests ที่ต้องเพิ่ม:**
- Test event 14 extraction: sourceUserId = `data.sender.im_user_id`
- Test event 14 timestamp conversion: unix seconds → Date
- Test event 13 extraction: sourceUserId = 'system'
- Test unknown event type: fallback behavior
- Test missing data fields: graceful defaults

**Deduplication:** ใช้ `data.message_id` อยู่แล้ว ✅ (ไม่ต้องแก้)

---

### Subtask 2: Create TikTok Channel Mapper in Normalizer Worker

**Objective:** สร้าง `TikTokChannelMapper` เพื่อ normalize TikTok messages เข้าสู่ Omni format

**Files:**
- CREATE: `apps/omnichat-normalizer-worker/src/worker/channel-mappers/tiktok-channel-mapper.ts`
- MODIFY: `apps/omnichat-normalizer-worker/src/worker/worker.module.ts` — register mapper

**Current State (ปัญหา):**
- ไม่มี TikTok mapper → messages ที่เข้า SQS จะ fail normalization → ไปตกที่ DLQ

**Scope:**
- Map TikTok message types เป็น Omni format:
  - `TEXT` → text message
  - `IMAGE` → image attachment (url, width, height)
  - `VIDEO` → video attachment (url, width, height, duration)
  - `PRODUCT_CARD` / `BUYER_ENTER_FROM_PRODUCT` → product reference card
  - `ORDER_CARD` / `BUYER_ENTER_FROM_ORDER` → order reference card
  - `EMOTICONS` → sticker/emoji
  - `LOGISTICS_CARD` → logistics info card
  - `COUPON_CARD` → coupon info card
  - `ALLOCATED_SERVICE`, `NOTIFICATION`, `BUYER_ENTER_FROM_TRANSFER` → system notifications
  - `OTHER` → fallback
- ใช้ `data.sender.role` เพื่อระบุ direction (BUYER = inbound, อื่นๆ = outbound)
- ใช้ `data.conversation_id` เป็น thread key
- ใช้ `data.is_visible` เพื่อกรอง messages ที่ไม่ควรแสดง

> **Note:** Subtask นี้อาจ overlap กับ ACE-1261 (Normalization TikTok) ภายใต้ ACE-703 — ต้องตกลงกันว่าจะรวมหรือแยก

---

### Subtask 3: Configure TikTok Webhook Subscription (Manual/Ops)

**Objective:** ตั้งค่า webhook URL ใน TikTok Partner Center

**Type:** Manual configuration (ไม่ใช่ coding task)

**Steps:**
1. เข้า TikTok Shop Partner Center → App Management → ACE OmniChat
2. ไปที่ Webhook Configuration
3. ตั้ง Webhook URL: `https://<production-domain>/webhooks/tiktok`
4. Subscribe to events:
   - ✅ (14) New Message — **required**
   - ✅ (13) New Conversation — recommended
5. ทดสอบ webhook delivery ด้วย TikTok test tools

**Prerequisites:**
- ❗ `seller.customer_service` scope ต้อง approved แล้ว
- Production domain ต้อง accessible จาก TikTok servers
- SSL certificate ต้อง valid

---

### Subtask 4: Deprioritize TikTok Poller (Cleanup)

**Objective:** ปรับ TikTok poller stub ให้ชัดเจนว่าไม่ใช้สำหรับ chat (webhook ทำแทน)

**File:** `apps/omnichat-service/src/marketplace-polling/pollers/tiktok-poller.ts`

**Action:**
- เพิ่ม comment ว่า chat ใช้ webhook (event 14) แทน polling
- Poller อาจยังจำเป็นสำหรับ use case อื่น (เช่น order sync) ในอนาคต — เก็บ stub ไว้

**Priority:** Low — ทำได้เลยไม่ต้องรอ scope approved

---

## Dependency & Priority Order

```
[BLOCKER] seller.customer_service scope approved
         │
         ├── Subtask 1: Update extractTiktok() ──→ Subtask 2: TikTok Mapper
         │                                                │
         └── Subtask 3: Configure webhook ────────────────┘
                                                          │
                                              ✅ End-to-end working

Subtask 4: Deprioritize poller (independent, low priority)
```

| Priority | Subtask | Dependency |
|----------|---------|------------|
| 🔴 Blocked | All | `seller.customer_service` scope |
| 1 (High) | Subtask 1: Update extractTiktok() | Scope approved |
| 2 (High) | Subtask 2: TikTok Channel Mapper | Subtask 1 |
| 3 (High) | Subtask 3: Configure webhook | Scope approved |
| 4 (Low) | Subtask 4: Deprioritize poller | None |

---

## Overlap กับ ACE-703 (TikTok Connector Baseline)

ACE-703 มี subtasks ที่เกี่ยวข้อง:
- **ACE-1259:** API TikTok Inbound — อาจ overlap กับ Subtask 1 (webhook extraction)
- **ACE-1261:** Normalization TikTok — อาจ overlap กับ Subtask 2 (channel mapper)

**Recommendation:** หารือกับทีมว่า:
- ถ้า ACE-1259/1261 ยังไม่เริ่ม → รวม Subtask 1-2 เข้าไปใน ACE-1259/1261 เลย
- ถ้าแยก → Subtask 1-2 อยู่ใน ACE-702, ACE-1259/1261 ต่อยอดเพิ่มเติม

---

## Data Flow (After Implementation)

```
TikTok Shop → POST /webhooks/tiktok (event type 14)
    │
    ├─ WebhookSignatureGuard (HMAC-SHA256) ✅ done
    ├─ extractTiktok() maps: sourceUserId, timestamp, source_category ← Subtask 1
    ├─ Dedup via data.message_id (Redis 24h) ✅ done
    ├─ SQS FIFO (group: TIKTOK-{shop_id}-{im_user_id}) ✅ done
    │
    └─ omnichat-normalizer-worker
         └─ TikTokChannelMapper ← Subtask 2
              ├─ TEXT → text message
              ├─ IMAGE → image attachment
              ├─ VIDEO → video attachment
              ├─ *_CARD → reference cards
              └─ → Omni conversation + message records
```
