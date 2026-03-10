# EPIC ACE-31: Normalized Data Platform v1 — คำอธิบายแบบเข้าใจง่าย

## สรุปภาพรวม

Normalized Data Platform (NDP) คือระบบกลางที่รับข้อความจากทุกช่องทาง (LINE, Facebook, Instagram, TikTok, Shopee, Lazada) แล้วแปลงให้อยู่ในรูปแบบเดียวกัน เพื่อให้ Agent (คนตอบแชท) ทำงานได้โดยไม่ต้องสนว่าลูกค้าทักมาจากช่องทางไหน

**เปรียบเทียบง่าย ๆ:**
เหมือนล่ามแปลภาษา — ลูกค้าพูดมา 6 ภาษา (LINE, FB, IG, TikTok, Shopee, Lazada) ระบบแปลให้เป็นภาษาเดียวกันหมด แล้วส่งให้ Agent อ่านได้ทันที

---

## 1. ER Diagram — ตารางข้อมูล (เก็บอะไรบ้าง?)

ER Diagram อธิบายว่าระบบเก็บข้อมูลอะไรบ้าง และข้อมูลแต่ละส่วนเชื่อมกันยังไง

### 7 ตาราง แบ่งเป็น 2 กลุ่ม

#### กลุ่ม A: Business Tables (6 ตาราง) — ข้อมูลหลักที่ใช้ทำงาน

| ตาราง | คืออะไร | ตัวอย่าง |
|---|---|---|
| **tenant** | บริษัทที่ใช้ระบบ | "ร้าน ABC Shop" — tenant 1 ตัวมีได้หลาย channel |
| **channel_accounts** | บัญชีช่องทางที่เชื่อมต่อ | "LINE OA ของร้าน ABC", "Facebook Page ของร้าน ABC" |
| **contacts** | ลูกค้าที่เคยทักมา | "คุณสมชาย ทักมาทาง LINE" (external_user_id = U1234) |
| **conversations** | ห้องแชท (1 ลูกค้า ต่อ 1 ช่องทาง = 1 conversation) | "แชทระหว่าง คุณสมชาย กับ LINE OA ร้าน ABC" |
| **messages** | ข้อความแต่ละบับ | "สวัสดีครับ สนใจสินค้า" — 1 conversation มีได้หลาย messages |
| **attachments** | ไฟล์แนบ (รูป, วิดีโอ, เอกสาร) | "photo.jpg ที่คุณสมชายส่งมาพร้อมข้อความ" |

#### กลุ่ม B: System Tables (1 ตาราง) — ข้อมูลเบื้องหลัง

| ตาราง | คืออะไร | ตัวอย่าง |
|---|---|---|
| **raw_events** | Webhook ดิบที่รับมา (เก็บไว้ debug + track normalization result) | JSON ดิบจาก LINE ก่อนแปลง — มีครบทุก field ที่ LINE ส่งมา + มี `normalization_status` บอกว่าแปลงสำเร็จหรือ fail |

### ความสัมพันธ์ — อ่านแบบนี้

```
ร้าน ABC Shop (tenant)
├── LINE OA (channel_account)
│   ├── คุณสมชาย (contact) — ทักมาทาง LINE
│   │   └── Conversation #1 (แชทกับ LINE OA)
│   │       ├── Message: "สวัสดีครับ สนใจสินค้า"
│   │       ├── Message: "ส่งรูปสินค้าให้หน่อยครับ"
│   │       └── Message: [รูปสินค้า]
│   │           └── Attachment: product.jpg (เก็บใน S3)
│   └── คุณสมหญิง (contact) — ทักมาทาง LINE
│       └── Conversation #2
│
├── Facebook Page (channel_account)
│   └── คุณสมชาย (contact) — คนเดียวกัน แต่ทักมาทาง FB = contact คนละตัว
│       └── Conversation #3
│
└── Shopee Shop (channel_account)
    └── ...
```

> **จุดสำคัญ:** ลูกค้าคนเดียวกัน ทักมาคนละช่องทาง = contact คนละตัว เพราะ external_user_id ต่างกัน (LINE ใช้ U1234, FB ใช้ PSIDxxxx)

### Tenant Isolation — แยกข้อมูลระหว่างบริษัท

ทุกตารางมี `tenant_id` — ร้าน A ดูข้อมูลร้าน B ไม่ได้เด็ดขาด

```
ร้าน ABC (tenant_id = aaa) → เห็นแค่ข้อมูลของตัวเอง
ร้าน XYZ (tenant_id = bbb) → เห็นแค่ข้อมูลของตัวเอง
```

### Soft Delete

Business tables ทั้ง 6 มี `deleted_at` — ลบแล้วไม่หายจริง แค่ซ่อน ย้อนกลับได้

```
DELETE channel_account → SET deleted_at = NOW()
ข้อมูลยังอยู่ในฐานข้อมูล แค่ query ปกติจะกรอง WHERE deleted_at IS NULL
```

System table (raw_events) **ไม่มี** `deleted_at` — เก็บไว้ตลอดเพื่อ audit

---

## 2. Sequence Diagram — ลำดับการทำงาน (ทำอะไรก่อนหลัง?)

Sequence Diagram อธิบายว่าเมื่อเกิด event ข้อมูลไหลผ่าน service ไหนบ้าง ตามลำดับ

### 5 Services ในระบบ

```
                        ┌──────────────────┐
ลูกค้าส่งข้อความ  ───▶ │ Omnichat Gateway │  ←── "ยาม" รับ webhook ตรวจลายเซ็น
                        └────────┬─────────┘
                                 │ ส่งเข้าคิว (SQS)
                                 ▼
                        ┌──────────────────┐
                        │ Normalizer Worker│  ←── "ล่ามแปลภาษา" แปลงข้อมูล
                        └────────┬─────────┘
                                 │ เรียก HTTP
                                 ▼
                        ┌──────────────────┐
                        │ Omnichat Service │  ←── "สมองกลาง" เก็บ DB ส่งข้อความออก
                        └────────┬─────────┘
                                 │
                        ┌────────┴─────────┐
                        ▼                  ▼
                   ┌──────────┐     ┌──────────────┐
                   │PostgreSQL│     │ File Service  │──▶ S3
                   └──────────┘     └──────────────┘
```

### 5 Flows — เรียงตาม use case

#### Flow 1: ลูกค้าส่งข้อความเข้า (Inbound) — สำคัญที่สุด

**สถานการณ์:** คุณสมชายส่งข้อความ "สนใจสินค้า" + รูป photo.jpg มาทาง LINE

```
ขั้นตอน:

1. LINE ส่ง webhook มาที่ Gateway
   → Gateway ตรวจลายเซ็น (HMAC-SHA256) ✓
   → ส่งเข้าคิว SQS → ตอบ LINE กลับ 200 OK ทันที (ไม่ต้องรอประมวลผล)

2. Worker หยิบจากคิว
   → ลบข้อมูลส่วนตัว (PII Redaction): ซ่อน userId, avatar
   → เก็บ payload ดิบลง raw_events (เผื่อ debug)

3. Worker แปลงข้อมูล (Normalize)
   → LINE format → Normalized format เดียวกันหมด

4. Omnichat Service เก็บข้อมูล
   → UPSERT contact (คุณสมชาย — ถ้ามีแล้วก็ update last_seen_at)
   → UPSERT conversation (ห้องแชทกับคุณสมชาย)
   → INSERT message ("สนใจสินค้า")
   → ack คิว SQS (เสร็จแล้ว ลบออกจากคิว)

5. Worker โหลด attachment (หลัง ack — ไม่ block คิว)
   → ดาวน์โหลด photo.jpg จาก LINE server
   → ตรวจขนาด/ประเภท → อัปโหลดขึ้น S3
   → update status: pending → uploaded
```

> **ทำไมต้องมีคิว (SQS)?** เพราะถ้า LINE ส่ง webhook มา 1,000 ข้อความพร้อมกัน เราต้องตอบ 200 OK ให้เร็ว แล้วค่อยประมวลผลทีหลัง ถ้าตอบช้า LINE จะ retry ซ้ำ

#### Flow 2: Agent ส่งข้อความออก (Outbound)

**สถานการณ์:** Agent ตอบคุณสมชายว่า "สินค้ามีพร้อมส่งค่ะ" + แนบรูป

```
1. Agent กด Send ใน Inbox UI
   → API Gateway ตรวจ auth + tenant_id

2. Omnichat Service:
   → อัปโหลดรูปไป S3 (ถ้ามี attachment)
   → INSERT message (direction='outbound', status='pending')
   → UPDATE conversation (last_message_at, last_message_preview)

3. ส่งไปหา LINE API (Reply/Push Message)
   → สำเร็จ → UPDATE message status='sent'
   → ล้มเหลว → UPDATE message status='failed' → แจ้ง Agent
```

#### Flow 3: Agent เปิดหน้า Inbox (Conversation List)

**สถานการณ์:** Agent เปิด Inbox เห็นรายการแชท เรียงตามล่าสุด

```
GET /api/v1/conversations?status=open&channel_type=LINE&limit=20

ตอบกลับ:
[
  { "contact": "คุณสมชาย", "preview": "สนใจสินค้า", "last_message_at": "10:30" },
  { "contact": "คุณสมหญิง", "preview": "สั่งซื้อแล้วค่ะ", "last_message_at": "10:25" },
  ...20 รายการ
]
cursor-based pagination — กด Load More = ดึง 20 รายการถัดไป
```

> **Pagination consistency:** ใช้ cursor-based pagination บน `last_message_at` — แม้มีข้อความใหม่เข้ามาระหว่าง scroll ก็ไม่มีข้อมูลซ้ำหรือหาย

#### Flow 4: Agent กดเข้าดูแชท (Message Timeline)

**สถานการณ์:** Agent กดเข้าดูแชทของคุณสมชาย เห็นข้อความเรียงตามเวลา

```
GET /api/v1/conversations/{id}/messages?limit=20

ตอบกลับ:
[
  { "sender": "คุณสมชาย", "content": "สวัสดีครับ", "type": "text" },
  { "sender": "คุณสมชาย", "content": "", "type": "image",
    "attachments": [{ "id": "att-1", "type": "image", "size": 245678, "status": "uploaded",
      "file_url": "https://{bucket}.s3.amazonaws.com/{tenant_id}/att-1/photo.jpg" }]
  },
  { "sender": "Agent นิด", "content": "สินค้ามีพร้อมส่งค่ะ", "type": "text" },
]

สังเกต: attachment มี file_url (static URL ถาวร ไม่หมดอายุ) — Browser โหลดรูปได้เลย
```

> **ทำไมส่ง `file_url` มาใน Timeline ด้วย?** S3 bucket เป็น public ดังนั้น `file_url` เป็น URL ถาวร (ไม่หมดอายุ) — ส่งมาตรงนี้เลยจะได้ไม่ต้องเรียก API เพิ่มทีละรูป Endpoint `GET /api/v1/attachments/:id/download` ยังใช้ได้สำหรับเช็คสถานะ pending/failed

> **Pagination consistency:** ใช้ cursor-based pagination บน `created_at` — แม้มีข้อความใหม่เข้ามาระหว่าง scroll ก็ไม่มีข้อมูลซ้ำหรือหาย ข้อความใหม่จะแสดงผ่าน real-time push (WebSocket/SSE) แทน

#### Flow 5: Marketplace (Shopee/Lazada) — มี 3 ประเภท event

```
1. Chat Message (คุยกับลูกค้าใน Shopee Chat)
   → แปลงเหมือน LINE/FB ปกติ

2. Order Reference (ลูกค้าสั่งซื้อ → สร้าง message อ้างอิง)
   → เก็บ metadata: { order_id: "SHP-001", shop_id: "shop-abc" }
   → Agent เห็นในแชทว่า "ลูกค้าสั่งซื้อ order SHP-001"

3. Fetch History (ดึงประวัติแชทย้อนหลัง)
   → ดึงเป็น batch → เก็บทีละข้อความ
   → มี idempotency key กัน duplicate (ถ้าข้อความซ้ำกับ live = ข้าม)
```

---

## 3. API Table — Endpoint ทั้งหมด (เรียกอะไรได้บ้าง?)

API Table อธิบายว่าระบบมี endpoint อะไรบ้าง ใครเรียกได้ ส่งอะไรไป ได้อะไรกลับ

### แบ่งตามผู้เรียก

#### กลุ่ม 1: Channel Platforms เรียก (6 endpoints)

```
LINE, Facebook, Instagram, TikTok, Shopee, Lazada
  ──▶ POST /webhooks/{channel_type}

ตัวอย่าง: LINE ส่ง webhook มา
POST /webhooks/line
Header: X-Line-Signature: abc123...
Body: { "events": [{ "type": "message", "message": { "text": "สวัสดี" } }] }

→ Gateway ตรวจลายเซ็น → ส่งเข้าคิว → ตอบ 200 OK
```

#### กลุ่ม 2: Agent / Inbox UI เรียก (16 endpoints)

**Channel Accounts (5)** — จัดการบัญชีช่องทาง

```
POST   /api/v1/channel-accounts          สร้างบัญชีใหม่ (เช่น เชื่อม LINE OA ใหม่)
GET    /api/v1/channel-accounts          ดูรายการบัญชีทั้งหมด
GET    /api/v1/channel-accounts/:id      ดูรายละเอียดบัญชี
PATCH  /api/v1/channel-accounts/:id      แก้ไขบัญชี (เปลี่ยนชื่อ, เปลี่ยน credential)
DELETE /api/v1/channel-accounts/:id      ลบบัญชี (soft delete)
```

**Contacts (3)** — ข้อมูลลูกค้า

```
GET    /api/v1/contacts                  ค้นหาลูกค้า
GET    /api/v1/contacts/:id              ดูรายละเอียดลูกค้า
PATCH  /api/v1/contacts/:id              แก้ไขข้อมูลลูกค้า

ตัวอย่าง: ค้นหาลูกค้าชื่อ "สมชาย" ทาง LINE
GET /api/v1/contacts?channel_type=LINE&search=สมชาย

→ { "data": [{ "display_name": "สมชาย", "external_user_id": "U1234", "last_seen_at": "..." }] }
```

**Conversations (4)** — ห้องแชท

```
GET    /api/v1/conversations             ดูรายการแชท (หน้า Inbox)
GET    /api/v1/conversations/:id         ดูรายละเอียดห้องแชท
PATCH  /api/v1/conversations/:id         เปลี่ยนสถานะ (open → closed → snoozed)
GET    /api/v1/conversations/:id/messages ดูข้อความในห้องแชท (Timeline)

ตัวอย่าง: Agent เปิด Inbox ดูแชทที่เปิดอยู่ เฉพาะ LINE
GET /api/v1/conversations?status=open&channel_type=LINE&limit=20&sort=last_message_at&order=desc

→ ได้รายการแชท 20 ห้อง เรียงจากล่าสุด พร้อม preview ข้อความสุดท้าย
```

**Messages (2)** — ข้อความ

```
POST   /api/v1/messages                  ส่งข้อความออก (Agent ตอบลูกค้า)
GET    /api/v1/messages/:id              ดูรายละเอียดข้อความ + attachments

ตัวอย่าง: Agent ส่งข้อความหาลูกค้า
POST /api/v1/messages
{
  "conversation_id": "conv-uuid",
  "content": "สินค้ามีพร้อมส่งค่ะ",
  "content_type": "text",
  "sender_display_name": "Agent นิด"
}

→ { "data": { "id": "msg-uuid", "status": "sent" } }
```

**Attachments (2)** — ไฟล์แนบ

```
GET    /api/v1/attachments/:id           ดู metadata ของไฟล์
GET    /api/v1/attachments/:id/download  ขอ static URL เพื่อดาวน์โหลด

ตัวอย่าง: Agent กดดูรูปที่ลูกค้าส่งมา
GET /api/v1/attachments/att-uuid/download

→ { "data": { "url": "https://{bucket}.s3.../tenant-id/att-id/photo.jpg" } }
→ Browser ใช้ URL นี้โหลดรูปได้เลย (ไม่หมดอายุ)
```

#### กลุ่ม 3: Service-to-Service — Internal (7 endpoints)

```
คนนอกเรียกไม่ได้ — API Gateway บล็อกไว้

Worker → Omnichat Service:
  POST  /internal/raw-events                    เก็บ webhook ดิบ
  POST  /internal/messages/inbound              เก็บข้อมูลที่แปลงแล้ว
  POST  /internal/attachments                   สร้าง record attachment
  PATCH /internal/attachments/:id               อัปเดตสถานะ attachment
  PATCH /internal/raw-events/:id                อัปเดตสถานะ normalization (เมื่อ fail)

Omnichat Service / Worker → File Service:
  POST  /files/presigned-url                    ขอ presigned URL สำหรับ upload (ได้ upload_url + static file_url)
  POST  /files/upload                           อัปโหลดไฟล์ขึ้น S3 (ได้ storage_key + static file_url)
```

---

## สรุปตัวเลข

| หมวด | จำนวน |
|---|---|
| ตารางในฐานข้อมูล | 7 ตาราง |
| HTTP Endpoints (NDP) | 24 เส้น (6 webhook + 11 public + 5 internal + 2 file service) |
| Sequence Flows | 5 flows |
| รองรับช่องทาง | 6 ช่องทาง (LINE, Facebook, Instagram, TikTok, Shopee, Lazada) |

---

## ตัวอย่าง End-to-End: ลูกค้าส่งข้อความ → Agent ตอบกลับ

```
1. คุณสมชายส่ง "สนใจสินค้า" + รูป photo.jpg ทาง LINE

2. LINE → POST /webhooks/line → Gateway ตรวจลายเซ็น → SQS

3. Worker หยิบจากคิว:
   - ลบ PII (ซ่อน userId, avatar ใน raw payload)
   - เก็บ raw event → POST /internal/raw-events
   - แปลง LINE format → Normalized format
   - สำเร็จ → UPDATE raw_events SET normalization_status='success'
   - fail → UPDATE raw_events SET normalization_status='failed' + error_detail
   - เก็บข้อมูล → POST /internal/messages/inbound
     → UPSERT contact (คุณสมชาย)
     → UPSERT conversation (ห้องแชทกับคุณสมชาย)
     → INSERT message ("สนใจสินค้า")
   - ack SQS (เสร็จแล้ว)
   - โหลด photo.jpg จาก LINE → อัปโหลด S3 → PATCH /internal/attachments/:id

4. Agent นิดเปิด Inbox:
   - GET /api/v1/conversations?status=open → เห็นแชทของคุณสมชาย

5. Agent นิดกดเข้าดูแชท:
   - GET /api/v1/conversations/{id}/messages → เห็นข้อความ + attachment metadata (รวม file_url)
   - PATCH /api/v1/conversations/{id} { is_read: true } → อ่านแล้ว

6. Agent นิดตอบ "สินค้ามีพร้อมส่งค่ะ":
   - POST /api/v1/messages → INSERT message → ส่งไป LINE API → status='sent'

7. คุณสมชายเห็นข้อความตอบกลับใน LINE
```
