# ACE-37 (NDP-01): Define Normalized Schema v1 — คำอธิบาย API Table

## ภาพรวม

API นี้จะยังไม่ implement ใน story นี้ (ACE-37) แต่ schema ต้องรองรับ API ที่วางแผนไว้ใน story NDP-05 — ดังนั้นนี่คือ API surface ที่ schema ต้อง support

---

## กลุ่ม API

### 1. Channel Accounts (บัญชีช่องทาง)

| Endpoint | ทำอะไร |
|---|---|
| `POST /api/v1/channel-accounts` | **เพิ่มบัญชีช่องทางใหม่** — เช่น เชื่อม LINE OA, Facebook Page หรือ Instagram Business ใหม่ เข้ากับ tenant |
| `GET /api/v1/channel-accounts` | **ดูรายการบัญชีช่องทางทั้งหมด** ของ tenant — filter ด้วย `?channel_type=` (LINE, FACEBOOK, ฯลฯ) หรือ `?status=` (active/inactive) |
| `GET /api/v1/channel-accounts/:id` | **ดูรายละเอียดบัญชีช่องทาง** 1 บัญชี — เช่น display_name, connection_status, last_error_summary |
| `PATCH /api/v1/channel-accounts/:id` | **แก้ไขบัญชีช่องทาง** — เปลี่ยน display_name, credential_ref_id, หรือตั้ง status=inactive |
| `DELETE /api/v1/channel-accounts/:id` | **ปิดการใช้งานบัญชีช่องทาง** — soft delete (ตั้ง status=inactive หรือ deleted_at) |

**Key Params:**
- `tenant_id`, `channel_type`, `external_account_id` — ระบุว่าบัญชีช่องทางนี้เป็นของ tenant ไหน, channel อะไร, ID จาก channel คืออะไร
- `credential_ref_id` — อ้างอิง FK ไปยัง credential_store (FND-02) ไม่เก็บ token ตรงนี้

---

### 2. Contacts (ผู้ติดต่อ/ลูกค้า)

| Endpoint | ทำอะไร |
|---|---|
| `GET /api/v1/contacts` | **ดูรายการผู้ติดต่อ** — filter ด้วย `?channel_type=`, search ด้วย `?search=` (ชื่อ), pagination ด้วย `?cursor=`, `?limit=` |
| `GET /api/v1/contacts/:id` | **ดูรายละเอียดผู้ติดต่อ** — เช่น display_name, avatar_url, profile_metadata, first_seen_at |
| `PATCH /api/v1/contacts/:id` | **แก้ไขข้อมูลผู้ติดต่อ** — เปลี่ยน display_name หรือ profile_metadata (tags, notes, custom fields) |

**Key Params:**
- `?search=` — ค้นหาจากชื่อผู้ติดต่อ
- `profile_metadata` — JSONB ใส่ข้อมูลเพิ่มเติมได้ตามต้องการ

---

### 3. Conversations (บทสนทนา/Inbox)

| Endpoint | ทำอะไร |
|---|---|
| `GET /api/v1/conversations` | **ดูรายการบทสนทนา (Inbox)** — filter ด้วย `?status=` (open/closed/snoozed), `?channel_type=`, sort ด้วย `?sort=last_message_at` (ล่าสุดก่อน) |
| `GET /api/v1/conversations/:id` | **ดูรายละเอียดบทสนทนา** — contact, channel_account, last_message_preview, status |
| `PATCH /api/v1/conversations/:id` | **เปลี่ยนสถานะบทสนทนา** — ตั้ง `status=open` (กำลังดูแล), `closed` (ปิดแล้ว), `snoozed` (เลื่อนไว้) |
| `GET /api/v1/conversations/:id/messages` | **ดู timeline ข้อความ** ในบทสนทนา — pagination ด้วย `?cursor=`, `?limit=` |

**Key Params:**
- `?status=` — filter inbox ตาม open/closed/snoozed
- `?sort=last_message_at` — เรียงตามข้อความล่าสุด (default DESC)

---

### 4. Messages (ข้อความ)

| Endpoint | ทำอะไร |
|---|---|
| `POST /api/v1/messages` | **ส่งข้อความออก** — Agent หรือระบบส่งข้อความไปหาลูกค้าผ่าน channel ที่เชื่อมไว้ |
| `GET /api/v1/messages/:id` | **ดูรายละเอียดข้อความ** — content, attachments, status, channel_timestamp |

**Key Params:**
- `conversation_id` — ระบุว่าจะส่งข้อความไปในบทสนทนาไหน
- `content` — เนื้อหาข้อความ
- `content_type` — text/image/video/audio/file/sticker/template
- `sender_display_name` — ชื่อ agent ที่ส่ง (แสดงใน UI)
- `attachments[]` — array ของไฟล์แนบ (ถ้ามี)

---

### 5. Attachments (ไฟล์แนบ)

| Endpoint | ทำอะไร |
|---|---|
| `GET /api/v1/attachments/:id` | **ดู metadata ของไฟล์แนบ** — type, content_type, size, status, checksum |
| `GET /api/v1/attachments/:id/download` | **ดึง pre-signed URL สำหรับ download** — สร้าง URL ชั่วคราวจาก S3 (หมดอายุ เช่น 15 นาที) |

**Key Params:**
- ไม่มี params — ดึงตาม `attachment_id` เท่านั้น

**เหตุผลที่แยก endpoint download:**
- ไฟล์อยู่ใน S3 ไม่ผ่าน API server
- Pre-signed URL ปลอดภัยกว่า (expire ได้, ไม่เปิดเผย storage key)

---

### 6. Webhooks (Inbound) (รับ webhook จาก Channel)

| Endpoint | ทำอะไร |
|---|---|
| `POST /webhook/line` | รับ webhook events จาก LINE (ต้องมี signature ใน header เพื่อ validate) |
| `POST /webhook/facebook` | รับ webhook events จาก Facebook Messenger |
| `POST /webhook/instagram` | รับ webhook events จาก Instagram Messaging |
| `POST /webhook/tiktok` | รับ webhook events จาก TikTok |
| `POST /webhook/shopee` | รับ webhook events จาก Shopee |
| `POST /webhook/lazada` | รับ webhook events จาก Lazada |

**Key Params:**
- Signature ใน header — แต่ละ channel มีวิธี sign ต่างกัน (X-Line-Signature, X-Hub-Signature-256 ฯลฯ)

---

## Common Headers (ทุก API call ต้องมี)

| Header | คำอธิบาย |
|---|---|
| `X-Tenant-Id` | **ระบุ tenant_id** — ต้องส่งทุก API call เพื่อแยกข้อมูลระหว่าง tenant (tenant isolation) |
| `Authorization` | **Bearer token** — สำหรับ authentication (JWT หรือ API key) |

---

## Conventions (ข้อตกลงทั่วไป)

### Pagination (การแบ่งหน้า)
- **Cursor-based** — ใช้ `?cursor=` และ `?limit=` (ไม่ใช่ page/offset)
- Default: `limit=20`, Max: `limit=100`
- เหตุผล: cursor ทำงานได้ดีกับ real-time data (ไม่เพี้ยนเมื่อมีข้อมูลใหม่แทรกเข้ามา)

### Sorting (การเรียงลำดับ)
- `?sort=field` — เรียงตาม field ไหน (เช่น `last_message_at`)
- `?order=asc|desc` — เรียงจากน้อยไปมาก หรือ มากไปน้อย

### Response Envelope (รูปแบบ response)
```json
{
  "data": { ... },  // หรือ [ ... ] สำหรับ array
  "meta": {
    "cursor": "2024-01-01T00:00:00Z",
    "has_more": true
  }
}
```

### Error Format (รูปแบบ error)
```json
{
  "error": {
    "code": "INVALID_TENANT",
    "message": "Tenant not found",
    "details": { ... }  // optional
  }
}
```

### Timestamps
- **ISO 8601 UTC** — เช่น `2024-01-15T10:30:00Z`
- ไม่ใช้ Unix timestamp เพื่อความชัดเจน

### IDs
- **UUID v4** — ทุก ID ใช้ UUID (เช่น `550e8400-e29b-41d4-a716-446655440000`)
- ไม่ใช้ auto-increment integer เพื่อ security และ distributed system

---

## สรุป Design Pattern

| Pattern | เหตุผล |
|---|---|
| **Tenant isolation ด้วย header** | แยกข้อมูลระหว่าง tenant ชัดเจน, ไม่ต้องใส่ใน path |
| **Cursor pagination** | รองรับ real-time, stable กว่า offset |
| **Pre-signed URL สำหรับ attachment** | ไม่ผ่าน API server, ลด load และปลอดภัย |
| **Separate webhook endpoints** | แต่ละ channel ตรวจสอบ signature ต่างกัน, แยกเพื่อความชัดเจน |
| **UUID v4 IDs** | ไม่เปิดเผยจำนวนข้อมูล, รองรับ distributed system |
| **ISO 8601 timestamps** | มาตรฐานสากล, อ่านง่าย, มี timezone ชัดเจน |
