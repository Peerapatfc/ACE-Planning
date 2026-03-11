# EPIC ACE-33: Marketplace Connectivity Baseline — คำอธิบายแบบเข้าใจง่าย

## สรุปภาพรวม

Marketplace Connectivity Baseline คือชุด story ที่ทำให้ ACE รองรับ marketplace 3 เจ้า (TikTok, Shopee, Lazada) ได้ครบวงจร — ตั้งแต่ต่อบัญชี → ดึงข้อความ → แปลงข้อมูล → เก็บลง DB → Agent ตอบกลับได้

**เปรียบเทียบง่าย ๆ:**
LINE/Facebook ส่ง webhook มาหาเราตลอด (เหมือนลูกค้า "โทรหา") แต่ Shopee/Lazada/TikTok ไม่มี webhook ที่เชื่อถือได้ เราต้องเป็นฝ่าย "โทรไปหา" ตามเวลาแทน — EPIC นี้คือการสร้างระบบ "โทรออกหา marketplace" นั้น

---

## 6 Stories ในนี้ทำอะไรบ้าง?

| Story | ชื่อ | ทำอะไร |
|---|---|---|
| **ACE-701** | Marketplace Channel Onboarding | ต่อบัญชี marketplace + เก็บ credentials |
| **ACE-702** | Scheduled Polling Framework | วงล้อ cron ที่ดึงข้อมูลตามเวลา (infrastructure) |
| **ACE-703** | TikTok Connector Baseline | integration เฉพาะของ TikTok |
| **ACE-704** | Shopee Connector Baseline | integration เฉพาะของ Shopee |
| **ACE-705** | Lazada Connector Baseline | integration เฉพาะของ Lazada |
| **ACE-706** | Marketplace Threading Rules | กฎการจัดกลุ่มข้อความให้ถูกห้อง |

### ลำดับการพึ่งพากัน

```
ACE-701 (ต่อบัญชี)
    │
    ▼
ACE-702 (Polling Framework)  ←── infrastructure ที่ 703/704/705 ใช้
    │
    ├──▶ ACE-703 (TikTok Connector)
    ├──▶ ACE-704 (Shopee Connector)
    └──▶ ACE-705 (Lazada Connector)

ACE-706 (Threading Rules)  ←── cross-cutting ใช้ได้ตั้งแต่ 703/704/705
```

> ต้องทำ 701 และ 702 ก่อน ถึงจะทำ 703–705 ได้

---

## 1. ภาพรวม Architecture — Webhook vs Polling

ก่อน EPIC นี้ ACE รับข้อมูลแบบเดียวคือ **Webhook** (ช่องทาง push ข้อมูลมาหาเรา) หลัง EPIC นี้ ACE มีทั้ง 2 เส้นทาง:

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

**สำคัญ:** ทั้ง 2 path ใช้ pipeline เดิมร่วมกันหลังจากเข้า SQS แล้ว — ไม่ต้องสร้าง normalization หรือ DB logic ใหม่

---

## 2. ACE-701: Marketplace Channel Onboarding — ต่อบัญชียังไง?

### สิ่งที่เก็บในระบบ

เมื่อ Admin ต่อ Shopee Shop เข้า ACE จะสร้าง record ใน `ChannelAccount`:

```
ChannelAccount {
  id:                  "ca-uuid-001"
  tenant_id:           "tenant-abc"
  channel_type:        "shopee"
  external_account_id: "shop-12345"     ← Shopee shop_id
  status:              "active"
  connection_status:   "connected"
  credential_ref_id:   "vault-ref-xyz"  ← ชี้ไปที่ encrypted vault (ไม่เก็บ token ตรง)
}
```

### Credential เก็บยังไง?

Token จาก marketplace **ไม่เก็บตรง ๆ** ใน DB — เก็บไว้ใน Credential Vault (เข้ารหัส) แล้วเก็บแค่ `credential_ref_id` ไว้อ้างอิง

```
❌ ห้ามทำ:  channel_account.access_token = "eyJhbGci..."
✅ ที่ถูก:   channel_account.credential_ref_id = "vault-ref-xyz"
            vault["vault-ref-xyz"] = encrypt("eyJhbGci...")
```

### Support กี่บัญชีต่อ tenant?

Multi-account ได้ — ร้าน ABC เชื่อม Shopee ได้ 2 shop, Lazada ได้ 1 shop ฯลฯ

```
ร้าน ABC (tenant_id = abc)
├── Shopee Shop ไทย    (channel_type=shopee, external_account_id=shop-001)
├── Shopee Shop มาเลย์ (channel_type=shopee, external_account_id=shop-002)
└── Lazada TH          (channel_type=lazada, external_account_id=seller-999)
```

---

## 3. ACE-702: Scheduled Polling Framework — วงล้อ cron ทำงานยังไง?

### ทำไมต้องมี Polling?

Shopee/Lazada/TikTok ไม่มี webhook แบบ real-time ที่เชื่อถือได้ทั้งหมด เราเลยต้องวิ่งไปถามเองทุก X นาทีว่า "มีข้อความใหม่ไหม?"

### Flow หลัก

```
ทุก 5 นาที:
1. โหลด marketplace accounts ทั้งหมดที่ status=active
2. แบ่งเป็นกลุ่ม ๆ ละ 10 accounts (concurrency limit)
3. แต่ละ account × แต่ละ pollType (chat, order):
   - ถ้า account อยู่ใน backoff → ข้าม
   - ดึง last_fetch_at (timestamp ล่าสุดที่เคยดึงสำเร็จ)
   - เรียก Marketplace API: GET /messages?since=last_fetch_at
   - ส่งผลลัพธ์เข้า SQS → pipeline ปกติ
   - อัปเดต last_fetch_at = ใหม่
```

### ตารางใหม่: MarketplacePollingState

เก็บ "bookmark" ว่า account นี้ดึงข้อมูลถึงไหนแล้ว

| Field | ความหมาย | ตัวอย่าง |
|---|---|---|
| `channel_account_id` | account ไหน | "ca-uuid-001" (Shopee Shop A) |
| `poll_type` | ดึงข้อมูลประเภทอะไร | "chat" หรือ "order" |
| `last_fetch_at` | ดึงสำเร็จล่าสุดเมื่อไหร่ | 2026-03-10 10:00:00 |
| `backoff_until` | ห้าม poll จนถึงเวลานี้ | 2026-03-10 10:01:00 (ถ้าโดน rate limit) |
| `consecutive_failures` | fail ติดต่อกันกี่ครั้ง | 2 |
| `last_error` | error ล่าสุดคืออะไร | "rate_limited" |

### ทำไม last_fetch_at ถึงสำคัญ?

```
รอบแรก (10:00):  since = 09:55  →  ดึงข้อความ 09:55–10:00  →  last_fetch_at = 10:00
รอบสอง (10:05):  since = 10:00  →  ดึงข้อความ 10:00–10:05  →  ไม่ซ้ำ ✓
```

ถ้าไม่มี last_fetch_at ทุกรอบจะดึงข้อมูลทั้งหมดซ้ำ

### Backoff — ป้องกัน rate limit

```
fail ครั้งที่ 1  →  รอ 1 นาที
fail ครั้งที่ 2  →  รอ 2 นาที
fail ครั้งที่ 3  →  รอ 4 นาที
fail ครั้งที่ 4  →  รอ 8 นาที
fail ครั้งที่ 5+ →  รอ 16 นาที (สูงสุด)

ถ้า API ตอบ 429 พร้อม Retry-After: 60 → รอตาม header นั้นเลย
```

---

## 4. ACE-703/704/705: Platform Connectors — แต่ละเจ้าต่างกันยังไง?

ทุก connector ทำงานผ่าน interface เดียวกัน `IMarketplacePoller` แต่ implement logic เฉพาะของ API ตัวเอง

```typescript
interface IMarketplacePoller {
  poll(account: ChannelAccount, context: PollingContext): Promise<PollingOutcome>
}
```

| Connector | API | ความแตกต่างหลัก |
|---|---|---|
| **TikTok** (ACE-703) | TikTok Shop API | มี order context เมื่อลูกค้าเริ่มแชทจาก order page |
| **Shopee** (ACE-704) | Shopee Open API v2 | rate limit per shop, ต้องจัดการต่อร้านค้า |
| **Lazada** (ACE-705) | Lazada Seller API | มี region-specific endpoints (TH, MY, SG...) |

### แต่ละ Connector ทำ 4 อย่าง

```
1. Inbound    — รับข้อความใหม่จาก API (ผ่าน polling)
2. Outbound   — ส่งข้อความตอบกลับจาก Agent
3. Normalize  — แปลง platform format → Omni format เดียวกัน
4. History    — ดึงประวัติแชทย้อนหลัง (รอบแรกที่เชื่อมต่อ)
```

### ตัวอย่าง: Shopee message → Omni format

```
Shopee raw:                          Omni normalized:
{                                    {
  "conversation_id": "conv-001",       "external_message_id": "conv-001-msg-001",
  "message_id": "msg-001",             "channel_type": "shopee",
  "from_user": { "uid": "B456" },      "external_user_id": "B456",
  "content": {                         "content_type": "text",
    "type": "text",                    "content": "สนใจสินค้าครับ",
    "text": "สนใจสินค้าครับ"           "source_category": "fetch_history",
  },                                   "fetch_batch_id": "batch-uuid"
  "create_time": 1710000000           }
}
```

`source_category: "fetch_history"` บอกว่าข้อมูลชุดนี้มาจาก polling ไม่ใช่ webhook live

---

## 5. ACE-706: Threading Rules — จัดกลุ่มข้อความยังไงให้ถูกห้อง?

### ปัญหา: marketplace conversation key ต่างจาก social

LINE/Facebook มี `reply_token` หรือ `thread_id` ที่ชัดเจน แต่ marketplace บางเจ้าระบุตัวตนผู้ซื้อด้วย uid ที่ซ้ำกันข้าม shop ได้ ถ้าไม่ระวังข้อความของลูกค้าจาก shop A อาจไปรวมกับ shop B

### กฎ v1: Conversation Key

```
conversation_key = tenant_id + channel_account_id + external_buyer_id

ถ้ามี external_thread_id:
conversation_key = tenant_id + channel_account_id + external_buyer_id + external_thread_id
```

### ตัวอย่าง: ทำไมต้องมี channel_account_id ด้วย?

```
ร้าน ABC มี 2 shop:

Shopee Shop A (ca-001):
  ลูกค้า uid=B456 → conversation key: abc + ca-001 + B456 → Conversation #100

Shopee Shop B (ca-002):
  ลูกค้า uid=B456 → conversation key: abc + ca-002 + B456 → Conversation #101

ถึงแม้ uid เดียวกัน แต่คนละ shop → คนละห้องแชท ✓
```

> Limitation ใน R1: ถ้าลูกค้าคนเดียวทักทั้ง Shopee Shop A และ Shopee Shop B ระบบจะเห็นเป็น 2 คนคนละห้อง ไม่ merge identity ข้าม shop ในเวอร์ชันนี้

---

## 6. Shared Pipeline — pipeline เดิมรองรับ marketplace ได้เลย

สิ่งที่ดีคือ normalizer-worker และ omnichat-service ไม่ต้องแก้มาก — marketplace ใช้ pipeline เดิม:

```
[SQS Message]
      │
      ▼
omnichat-normalizer-worker
  ├── ChannelMapperRegistry.normalize()
  │     ├── ShopeeChannelMapper  ← เพิ่มใหม่
  │     ├── LazadaChannelMapper  ← เพิ่มใหม่
  │     └── TikTokChannelMapper  ← เพิ่มใหม่
  └── POST /internal/messages/inbound
            │
            ▼
      omnichat-service
        ├── UPSERT Contact
        ├── UPSERT Conversation  ← ใช้ threading key จาก MKT-06
        └── INSERT Message (idempotency check กัน duplicate)
```

---

## สรุปตัวเลข

| หมวด | จำนวน |
|---|---|
| Stories | 6 stories (ACE-701 ถึง ACE-706) |
| Marketplace ที่รองรับ | 3 (TikTok, Shopee, Lazada) |
| ตารางใหม่ | 1 (MarketplacePollingState) |
| ตารางที่แก้ | 1 (ChannelAccount เพิ่ม relation) |
| Connector ใหม่ | 3 (IMarketplacePoller per platform) |
| Subtasks ทั้งหมด | 23 subtasks |

---

## ตัวอย่าง End-to-End: ลูกค้า Shopee ส่งข้อความ → Agent ตอบ

```
1. Admin ต่อ Shopee Shop A เข้า ACE (MKT-01)
   → สร้าง ChannelAccount + เก็บ access_token ใน vault

2. Cron วิ่งทุก 5 นาที (MKT-02)
   → โหลด Shop A → ไม่อยู่ใน backoff
   → ดึง last_fetch_at = 10:00

3. ShopeePoller เรียก Shopee API (MKT-04)
   → GET /chat/messages?since=10:00
   → ได้ข้อความ "สินค้ายังมีไหมครับ" จาก buyer uid=B456

4. Map → RawWebhookMessage → ส่งเข้า SQS via Gateway TCP

5. Normalizer Worker หยิบจากคิว
   → ShopeeChannelMapper.normalize()
   → POST /internal/messages/inbound
   → UPSERT Contact (B456), UPSERT Conversation (key: tenant+ca-001+B456)
   → INSERT Message

6. Agent เห็นใน Inbox
   → เปิดแชท → ตอบ "มีพร้อมส่งครับ"
   → POST /api/v1/messages
   → Shopee Outbound API → ลูกค้าเห็นใน Shopee Chat ✓

7. Polling รอบถัดไป
   → markSuccess: last_fetch_at = 10:05
   → รอบต่อไปดึงตั้งแต่ 10:05 เป็นต้นไป (ไม่ซ้ำ ✓)
```
