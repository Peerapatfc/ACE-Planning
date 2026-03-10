# ACE-37 (NDP-01): Define Normalized Schema v1 — คำอธิบาย Sequence Diagram

## ภาพรวม

Sequence diagram นี้แสดง 3 flow หลัก: (1) รับข้อความเข้า (2) ส่งข้อความออก (3) query timeline ของบทสนทนา

---

## 1. Inbound Message Flow (รับข้อความจาก Channel เข้าระบบ)

### กระบวนการ

1. **Channel Platform ส่ง webhook มา**
   - เช่น LINE/Facebook/Instagram/TikTok/Shopee/Lazada ส่ง POST มาที่ `/webhook/{channel_type}`

2. **Webhook Receiver รับ request**
   - Validate signature (ตรวจสอบว่ามาจาก channel จริง ไม่ใช่ปลอม)
   - Extract `tenant_id` จาก mapping ภายใน (เช่น LINE OA ID → tenant_id)

3. **Normalization Pipeline ประมวลผล**
   - ส่ง payload ไปผ่าน **PII Redactor** เพื่อลบข้อมูลส่วนบุคคลออก (เช่น เบอร์โทร, อีเมล, ที่อยู่)
   - บันทึก **raw_events** ลง DB เป็น JSON redacted payload พร้อม flag `pii_safe=true`
   - แปลง (normalize) payload ของแต่ละ channel ให้เป็นรูปแบบเดียวกัน

4. **Persistence Service บันทึกข้อมูล**
   - **UPSERT contacts** — ถ้ามี contact นี้อยู่แล้ว (ตาม `external_user_id`) ก็ update `display_name` และ `last_seen_at`, ถ้ายังไม่มีก็สร้างใหม่
   - **UPSERT conversations** — ถ้ามี conversation นี้อยู่แล้ว (ตาม `external_thread_id`) ก็ update `last_message_at` และ `last_message_preview`, ถ้ายังไม่มีก็สร้างใหม่
   - **INSERT messages** — เพิ่มข้อความใหม่ (ใช้ `ON CONFLICT DO NOTHING` ป้องกันการ insert ซ้ำถ้า `external_message_id` ซ้ำ)

5. **Attachment แบบ async (ถ้ามี)**
   - เพิ่ม record ใน `attachments` table ด้วยสถานะ `status='pending'`
   - ส่ง job ไป **Job Queue** เพื่อ download ไฟล์ binary ไปเก็บใน S3 แบบ async (ไม่รอ webhook response)

6. **ตอบกลับ Channel**
   - ส่ง `200 OK` กลับไปทันทีหลังจากบันทึกข้อมูลเสร็จ (ไม่รอ download attachment)

### จุดสำคัญ
- **Idempotency**: `ON CONFLICT DO NOTHING` ทำให้ webhook ซ้ำไม่ทำให้ข้อมูลซ้ำ
- **Async attachment**: ไม่ block webhook response, download ทีหลัง
- **PII redaction**: ลบข้อมูลส่วนบุคคลก่อนเก็บ raw_events

---

## 2. Outbound Message Flow (Agent/ระบบส่งข้อความออกไปยัง Channel)

### กระบวนการ

1. **Agent หรือระบบเรียก API**
   - `POST /api/v1/messages` พร้อม `conversation_id`, `content`, `attachments` (ถ้ามี)

2. **Omni API ตรวจสอบสิทธิ์**
   - Validate `tenant_id` และ ownership ของ conversation (ตรวจว่า tenant นี้เป็นเจ้าของ conversation นี้จริง)

3. **Upload attachment ก่อน (ถ้ามี)**
   - Upload ไฟล์ binary ไป S3 ได้ `storage_key` กลับมา

4. **Persistence Service บันทึกข้อความ**
   - **INSERT messages** ด้วย `direction='outbound'`, `status='pending'`
   - **INSERT attachments** (ถ้ามี) ด้วย `status='uploaded'`
   - **UPDATE conversations** ตั้ง `last_message_at` และ `last_message_preview`

5. **ส่งข้อความไปยัง Channel API**
   - เรียก Channel API (เช่น LINE Messaging API, Facebook Send API)
   - ได้ `external_message_id` กลับมาจาก channel

6. **Update status**
   - `UPDATE messages` ตั้ง `external_message_id` และ `status='sent'`

7. **ตอบกลับ Agent**
   - `200 OK` พร้อม `message_id` และ `status: 'sent'`

### จุดสำคัญ
- **Upload ก่อนบันทึก**: attachment binary อยู่ใน S3 แล้วก่อนจะสร้าง message record
- **Status tracking**: `pending` → `sent` (อาจมี `delivered`, `read`, `failed` ตาม channel รองรับ)
- **Sync send**: ต่างจาก inbound ที่ async, outbound ต้องรอส่งเสร็จก่อนตอบ API

---

## 3. Query Conversation Timeline (ดึงข้อความย้อนหลังในบทสนทนา)

### กระบวนการ

1. **Inbox UI หรือ AI เรียก API**
   - `GET /api/v1/conversations/{id}/messages?cursor=&limit=20`

2. **Omni API ตรวจสอบสิทธิ์**
   - Extract `tenant_id` และ validate ownership

3. **Query messages**
   - `SELECT messages WHERE tenant_id=? AND conversation_id=? AND deleted_at IS NULL AND created_at < cursor ORDER BY created_at DESC LIMIT 21`
   - ดึง LIMIT+1 (21 แทน 20) เพื่อรู้ว่ามี page ถัดไปไหม (`has_more`)

4. **Query attachments**
   - `SELECT attachments WHERE message_id IN (...)` — ดึงไฟล์แนบของข้อความที่ได้มา

5. **Build response**
   - Merge attachments เข้ากับ messages
   - สร้าง `next_cursor` จาก `created_at` ของ item สุดท้าย
   - ส่ง `has_more=true` ถ้าได้ 21 items (แสดงว่ามีอีก)

6. **ตอบกลับ Client**
   - `200 OK { data: messages[], meta: { cursor, has_more } }`

### จุดสำคัญ
- **Cursor-based pagination**: ไม่ใช่ offset/page แต่ใช้ `created_at` เป็น cursor (stable, รองรับ realtime insert)
- **LIMIT+1 trick**: ดึงมา 21 items แต่ส่งกลับ 20, ใช้ item ที่ 21 เพื่อรู้ว่ามี page ถัดไป
- **Soft delete filter**: `deleted_at IS NULL` — ไม่แสดงข้อความที่ถูกลบแบบ soft delete

---

## สรุปความต่างระหว่าง 3 Flows

| Flow | Direction | Sync/Async | Key Point |
|---|---|---|---|
| **Inbound** | Channel → System | Async attachment download | Fast webhook response, idempotency |
| **Outbound** | System → Channel | Sync send | Upload S3 first, then send to channel |
| **Query** | Client ← System | Sync read | Cursor pagination, LIMIT+1 trick |
