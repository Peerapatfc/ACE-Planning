# ACE-37 (NDP-01): Define Normalized Schema v1 — คำอธิบาย ER Diagram

## ภาพรวม

Schema นี้ออกแบบมาให้ทุก channel (LINE, Facebook, Instagram, TikTok, Shopee, Lazada) เก็บข้อมูลในรูปแบบเดียวกัน โดยแยกข้อมูลตาม tenant (ผู้ใช้งานระบบ/องค์กร) ตั้งแต่แรก

---

## ตาราง (Tables)

### TENANT
เจ้าของระบบ/องค์กรที่ใช้งาน Omnichannel — ทุกตารางอื่นจะอ้างอิง `tenant_id` กลับมาที่นี่เสมอ เพื่อแยกข้อมูลระหว่าง tenant ไม่ให้ปนกัน

### CHANNEL_ACCOUNTS
บัญชีช่องทางที่ tenant เชื่อมต่อไว้ เช่น LINE OA, Facebook Page, Instagram Business, TikTok Shop เป็นต้น — แต่ละ record คือ 1 บัญชีของ 1 channel
- `external_account_id` — ID ของบัญชีฝั่ง channel (เช่น LINE OA ID)
- `credential_ref_id` — อ้างอิงไปยัง credential_store (FND-02) สำหรับเก็บ token/secret แยกต่างหาก ไม่เก็บ credential ตรงในตารางนี้
- `connection_status` — สถานะการเชื่อมต่อปัจจุบัน (connected หรือ error)
- `last_error_summary`, `error_code_category` — ข้อมูล error ล่าสุด สำหรับแสดงใน Admin UI

### CONTACTS
ผู้ติดต่อ/ลูกค้าที่ส่งข้อความเข้ามา — ระบบสร้างอัตโนมัติเมื่อได้รับข้อความครั้งแรกจากแต่ละ channel
- `external_user_id` — ID ของผู้ใช้ฝั่ง channel (เช่น LINE User ID)
- `profile_metadata` — ข้อมูลเพิ่มเติมจาก channel เป็น JSON (เช่น language, tags)
- `first_seen_at`, `last_seen_at` — เวลาที่เห็นผู้ติดต่อครั้งแรกและล่าสุด

### CONVERSATIONS
บทสนทนาระหว่าง contact กับ channel account — 1 conversation = 1 thread ของข้อความ
- `contact_id` — ผู้ติดต่อที่เกี่ยวข้อง
- `channel_account_id` — บัญชีช่องทางที่รับ/ส่งข้อความ
- `external_thread_id` — ID ของ thread ฝั่ง channel (บาง channel ไม่มี จึง nullable)
- `status` — สถานะบทสนทนา (open/closed/snoozed) สำหรับ Inbox UI
- `last_message_preview`, `last_message_at` — ข้อความล่าสุดและเวลา สำหรับแสดงในรายการ Inbox

### MESSAGES
ข้อความแต่ละข้อความในบทสนทนา ทั้งขาเข้า (inbound) และขาออก (outbound)
- `direction` — ทิศทางข้อความ (inbound = ลูกค้าส่งมา, outbound = agent/ระบบส่งออก)
- `external_message_id` — ID ของข้อความฝั่ง channel สำหรับ traceability
- `content_type` — ประเภทเนื้อหา (text, image, video, sticker ฯลฯ)
- `event_type` — ประเภท event (v1 รองรับ `message` เท่านั้น; edit/delete/reaction จะเพิ่มในอนาคต)
- `metadata` — ข้อมูลเพิ่มเติมเฉพาะ channel เป็น JSON รวมถึง marketplace_order_id, shop_id สำหรับ Shopee/Lazada
- `channel_timestamp` — เวลาจริงจากฝั่ง channel (อาจต่างจาก created_at ของระบบ)
- `raw_event_id` — เชื่อมไปยัง raw event ต้นทาง สำหรับ debug

### ATTACHMENTS
ไฟล์แนบของข้อความ (รูป, วิดีโอ, เสียง, ไฟล์, สติกเกอร์) — เก็บแค่ metadata ใน DB ส่วน binary เก็บใน S3
- `storage_key` — path/key ใน S3 สำหรับดึงไฟล์
- `content_type` — MIME type (เช่น image/jpeg, video/mp4)
- `status` — สถานะการ upload (pending → uploaded หรือ failed)
- `checksum` — SHA-256 สำหรับตรวจสอบความถูกต้องของไฟล์

### RAW_EVENTS
payload ดิบจาก webhook ของแต่ละ channel — เก็บไว้เพื่อ debug และ replay
- `payload` — JSON body ดิบที่ผ่านการ redact PII แล้ว (ลบข้อมูลส่วนบุคคลออก)
- `pii_safe` — flag ยืนยันว่าผ่านการ redact แล้ว
- `external_event_id` — idempotency key ป้องกันการประมวลผลซ้ำ

---

## ความสัมพันธ์ (Relationships)

```
TENANT
  ├── has many → CHANNEL_ACCOUNTS   (1 tenant มีหลายบัญชีช่องทาง)
  ├── has many → CONTACTS            (1 tenant มีหลายผู้ติดต่อ)
  ├── has many → CONVERSATIONS       (1 tenant มีหลายบทสนทนา)
  ├── has many → MESSAGES            (1 tenant มีหลายข้อความ)
  ├── has many → ATTACHMENTS         (1 tenant มีหลายไฟล์แนบ)
  └── has many → RAW_EVENTS          (1 tenant มีหลาย raw events)

CHANNEL_ACCOUNTS
  └── receives many → CONVERSATIONS  (1 บัญชีช่องทาง รับหลายบทสนทนา)

CONTACTS
  └── participates in many → CONVERSATIONS  (1 ผู้ติดต่อ มีหลายบทสนทนา)

CONVERSATIONS
  └── contains many → MESSAGES       (1 บทสนทนา มีหลายข้อความ)

MESSAGES
  ├── has many → ATTACHMENTS         (1 ข้อความ มีหลายไฟล์แนบ)
  └── linked to one → RAW_EVENTS     (1 ข้อความ เชื่อมกับ 1 raw event)
```

---

## การแยกข้อมูลระหว่าง Tenant (Tenant Isolation)

ทุกตารางมี `tenant_id` เป็น FK — ทุก query ต้องระบุ `tenant_id` เสมอ เพื่อให้แน่ใจว่าข้อมูลของแต่ละ tenant ไม่รั่วไหลข้ามกัน index ทุกตัวจึงขึ้นต้นด้วย `tenant_id` เป็น column แรก

## Soft Delete

ทุกตารางหลักมี `deleted_at` (nullable) — เมื่อลบข้อมูลจะไม่ลบจริง แต่ใส่ timestamp ไว้แทน เพื่อรองรับการกู้คืนและ audit trail
