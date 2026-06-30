# API Table — RA-01: Rule Automation / Rule Management (CRUD)

> EPIC: [ACE-2211](../ACE-2211_EPIC-A4.1_Rule_Automation.md) · STORY: [ACE-2212](../ACE-2212_STORY-RA-01_Rule_Management_CRUD.md)
> Diagrams: [ER](./RA-01_rule_automation_er.md) · [Sequence](./RA-01_rule_automation_sequence.md)
> Mock ทั้งหมดอิง schema ใน ER doc — shape ของ `conditions` / `action_config` ดูหัวข้อ [Shared shapes](#shared-shapes) ท้ายไฟล์

---

## Conventions

| หัวข้อ | รายละเอียด |
| --- | --- |
| Base path | `/v1/omnichat/automation/rules` (api-gateway global prefix `/v1` + domain `/omnichat`) |
| Transport | FE → **api-gateway (HTTP)** → **omnichat-service (HTTP proxy `axiosRef`)** → DB (pattern เดียวกับ saved-views/credentials) |
| Auth | JWT (httpOnly cookie) — `tenant_id`, `user_id` (`created_by`/`updated_by`), role ดึงจาก JWT/`get_member_role` ที่ gateway |
| Body ที่ FE ส่ง | **ไม่มี** `tenant_id` / `created_by` / `created_by_name` — gateway เติมจาก JWT ตอน proxy |
| Permission guard | global `APP_GUARD` ที่ api-gateway (`@RequirePermission`) — เช็คทั้ง UI และ API (Agent ยิงตรง = 403) · controller ใน omnichat-service ไม่มี guard เอง |
| Error format | omnichat-service **throw NestJS exception** → body `{ "statusCode", "message", "error" }`; gateway proxy คง status เดิม, FE Server Action map เป็น `{ "error": "<message>" }` · **message ด้านล่างคือ string จริงจาก service (อังกฤษ)** |
| Response rule object | = raw record จาก Prisma — รวม `tenant_id`, `created_by`, `updated_by` (mock ด้านล่างย่อบาง field เพื่ออ่านง่าย) |
| Date | ISO 8601 string (UTC) — relative time ("2 วันที่แล้ว") FE format จาก `updated_at` |

---

## Endpoint summary

| # | Method | Path | Permission | Role ที่เข้าได้ | Purpose | Success | Errors |
| - | ------ | ---- | ---------- | --------------- | ------- | ------- | ------ |
| 1 | `GET`    | `/v1/omnichat/automation/rules`            | `view_automation_rules`   | Admin · Supervisor · Agent | List แยก `active`/`inactive` + counters (รองรับ `?status` `?limit` `?offset`) | `200` | `403` |
| 2 | `GET`    | `/v1/omnichat/automation/rules/:id`        | `manage_automation_rules` | Admin · Supervisor | อ่าน rule เดียว (edit pre-fill) | `200` | `403` `404` |
| 3 | `POST`   | `/v1/omnichat/automation/rules`            | `manage_automation_rules` | Admin · Supervisor | สร้าง rule (active เต็ม 20 → บันทึกเป็น inactive) | `201` | `400` `403` |
| 4 | `PATCH`  | `/v1/omnichat/automation/rules/:id`        | `manage_automation_rules` | Admin · Supervisor | แก้ไข rule (ไม่ retroactive) | `200` | `400` `403` `404` |
| 5 | `PATCH`  | `/v1/omnichat/automation/rules/:id/enabled`| `manage_automation_rules` | Admin · Supervisor | Enable / Disable | `200` | `403` `404` `409` |
| 6 | `DELETE` | `/v1/omnichat/automation/rules/:id`        | `delete_automation_rules` | **Admin เท่านั้น** | Hard delete | `200` | `403` `404` |

---

## 1) `GET /v1/omnichat/automation/rules` — List rules

ทุก role เข้าได้ · response แยกเป็น 2 array `active` / `inactive` (ไม่ใช่ array เดียว) · counts คืนเสมอสำหรับ tab badge · `fired_count`: active = query สด override cache, inactive = จาก cache (frozen) · เรียง `enabled DESC, created_at DESC` · cache TTL 3600s

**Query params** (ทั้งหมด optional ยกเว้น `tenant_id` ที่ gateway เติมจาก JWT)

| param | type | constraint | หมายเหตุ |
| --- | --- | --- | --- |
| `tenant_id` | uuid | — | gateway เติมจาก JWT (FE ไม่ส่ง) |
| `status` | `active` \| `inactive` | enum | เลือก array ไหนถูก paginate — ไม่ส่ง = `active` เต็ม (≤20) + `inactive` paginate |
| `limit` | int | 1–100 (default 20, clamp) | pagination page size |
| `offset` | int | ≥ 0 | pagination offset |

**Response `200`**

```json
{
  "active": [
    {
      "id": "9f1c2e7a-4b8d-4c1a-9e2f-7a3b1c0d5e6f",
      "name": "Auto-reply · Outside hours",
      "action_type": "auto_reply",
      "trigger_logic": "AND",
      "conditions": [
        { "type": "business_hours", "operator": "outside", "value": { "use_workspace_hours": true } }
      ],
      "action_config": {
        "message": "สวัสดี {{customer_name}} ขณะนี้อยู่นอกเวลาทำการ ทีมงานจะติดต่อกลับโดยเร็วที่สุดค่ะ",
        "cooldown_minutes": 60
      },
      "trigger_summary": "Business hours: outside",
      "action_summary": "Auto-reply: 'สวัสดี {{customer_name}}…'",
      "enabled": true,
      "fired_count": 342,
      "created_by_name": "Admin",
      "updated_by_name": "Admin",
      "created_at": "2026-05-30T03:20:00.000Z",
      "updated_at": "2026-06-21T07:45:10.000Z"
    },
    {
      "id": "1a2b3c4d-5e6f-4071-8a9b-0c1d2e3f4a5b",
      "name": "Tag · ยกเลิก keywords",
      "action_type": "add_tag",
      "trigger_logic": "AND",
      "conditions": [
        { "type": "keyword", "operator": "contains", "value": ["ยกเลิก", "cancel"] },
        { "type": "channel", "operator": "in", "value": ["LINE", "SHOPEE"] }
      ],
      "action_config": { "tag_ids": ["c9d0e1f2-3a4b-4c5d-9e6f-7a8b9c0d1e2f"] },
      "trigger_summary": "Keyword: contains 'ยกเลิก', 'cancel' · Channel: LINE, Shopee",
      "action_summary": "Tag: cancellation-risk",
      "enabled": true,
      "fired_count": 87,
      "created_by_name": "สมศักดิ์ ว.",
      "updated_by_name": "สมศักดิ์ ว.",
      "created_at": "2026-05-12T05:00:00.000Z",
      "updated_at": "2026-06-18T11:02:33.000Z"
    },
    {
      "id": "2b3c4d5e-6f70-4182-9b0c-1d2e3f4a5b6c",
      "name": "Auto-reply · Shopee new",
      "action_type": "auto_reply",
      "trigger_logic": "AND",
      "conditions": [
        { "type": "channel", "operator": "in", "value": ["SHOPEE"] },
        { "type": "business_hours", "operator": "outside", "value": { "use_workspace_hours": true } }
      ],
      "action_config": {
        "message": "ขอบคุณที่ติดต่อเข้ามาค่ะ ทีมงานจะตอบกลับในเวลาทำการ",
        "cooldown_minutes": 120
      },
      "trigger_summary": "Channel: Shopee · Business hours: outside",
      "action_summary": "Auto-reply: 'ขอบคุณที่ติดต่อ…'",
      "enabled": true,
      "fired_count": 201,
      "created_by_name": "นัทธิดา พ.",
      "updated_by_name": "นัทธิดา พ.",
      "created_at": "2026-05-01T02:10:00.000Z",
      "updated_at": "2026-06-16T08:30:00.000Z"
    }
  ],
  "inactive": [
    {
      "id": "3c4d5e6f-7081-4293-ac1d-2e3f4a5b6c7d",
      "name": "Tag · Facebook new conv",
      "action_type": "add_tag",
      "trigger_logic": "AND",
      "conditions": [
        { "type": "channel", "operator": "in", "value": ["FACEBOOK"] }
      ],
      "action_config": { "tag_ids": ["d0e1f2a3-4b5c-4d6e-8f70-1a2b3c4d5e6f"] },
      "trigger_summary": "Channel: Facebook",
      "action_summary": "Tag: facebook-lead",
      "enabled": false,
      "fired_count": 56,
      "created_by_name": "Admin",
      "updated_by_name": "Admin",
      "created_at": "2026-04-20T04:00:00.000Z",
      "updated_at": "2026-06-09T09:00:00.000Z"
    }
  ],
  "active_count": 3,
  "inactive_count": 1,
  "limit": 20,
  "offset": 0
}
```

> Rule `Auto-reply · Shopee new`: สร้าง/แสดงได้ แต่ตอน execute auto-reply ถูก **skip** เพราะ Shopee ส่งไม่ได้ (tag ยังทำงาน) — ดู Sequence Diagram 6

**Error `403`** — role ไม่มี (เช่นยิง API ตรงโดยไม่มีสิทธิ์)

```json
{ "error": "permission_denied" }
```

---

## 2) `GET /v1/omnichat/automation/rules/:id` — Get one rule (edit pre-fill)

ใช้ตอนเปิด wizard แก้ไข / deep-link `/rules/:id/edit` · Agent ไม่มี edit จึงไม่เรียกเส้นนี้ · `:id` ผ่าน `ParseUUIDPipe` (ไม่ใช่ uuid → `400`) · `tenant_id` ส่งเป็น query param (gateway เติมจาก JWT)

**Response `200`**

```json
{
  "rule": {
    "id": "9f1c2e7a-4b8d-4c1a-9e2f-7a3b1c0d5e6f",
    "name": "Auto-reply · Outside hours",
    "action_type": "auto_reply",
    "trigger_logic": "AND",
    "conditions": [
      { "type": "business_hours", "operator": "outside", "value": { "use_workspace_hours": true } }
    ],
    "action_config": {
      "message": "สวัสดี {{customer_name}} ขณะนี้อยู่นอกเวลาทำการ ทีมงานจะติดต่อกลับโดยเร็วที่สุดค่ะ",
      "cooldown_minutes": 60
    },
    "enabled": true,
    "fired_count": 342,
    "created_by": "8c2a1f3e-1d4b-4a9c-bb12-3e5f7a9c1d2b",
    "created_by_name": "Admin",
    "updated_by": "8c2a1f3e-1d4b-4a9c-bb12-3e5f7a9c1d2b",
    "updated_by_name": "Admin",
    "created_at": "2026-05-30T03:20:00.000Z",
    "updated_at": "2026-06-21T07:45:10.000Z"
  }
}
```

**Error `404`** — ไม่พบ / ไม่ใช่ของ tenant นี้

```json
{ "error": "Automation rule not found" }
```

---

## 3) `POST /v1/omnichat/automation/rules` — Create rule

Validation (DTO): `name` ≥ 1 ตัว, ≤ **150** ตัวอักษร · `action_type` ∈ `auto_reply` \| `add_tag` · `trigger_logic` optional (default `AND`) ∈ `AND` \| `OR` · `conditions` = array · `action_config` = object · gateway เติม `tenant_id`/`created_by`/`created_by_name` (uuid + non-empty) จาก JWT
Service-level check (400): `conditions` ≥ 1 → `"At least 1 condition is required"` · `auto_reply` ต้องมี `message` (non-empty) + `cooldown_minutes` (number) → `"auto_reply requires message and cooldown_minutes"` · `add_tag` ต้องมี `tag_ids` ≥ 1 → `"add_tag requires at least 1 tag"`

**Request body**

```json
{
  "name": "Auto-reply · Outside hours",
  "action_type": "auto_reply",
  "trigger_logic": "AND",
  "conditions": [
    { "type": "business_hours", "operator": "outside", "value": { "use_workspace_hours": true } }
  ],
  "action_config": {
    "message": "สวัสดี {{customer_name}} ขณะนี้อยู่นอกเวลาทำการ ทีมงานจะติดต่อกลับโดยเร็วที่สุดค่ะ",
    "cooldown_minutes": 60
  }
}
```

**Response `201`**

```json
{
  "rule": {
    "id": "9f1c2e7a-4b8d-4c1a-9e2f-7a3b1c0d5e6f",
    "name": "Auto-reply · Outside hours",
    "action_type": "auto_reply",
    "trigger_logic": "AND",
    "conditions": [
      { "type": "business_hours", "operator": "outside", "value": { "use_workspace_hours": true } }
    ],
    "action_config": {
      "message": "สวัสดี {{customer_name}} ขณะนี้อยู่นอกเวลาทำการ ทีมงานจะติดต่อกลับโดยเร็วที่สุดค่ะ",
      "cooldown_minutes": 60
    },
    "enabled": true,
    "fired_count": 0,
    "created_by": "8c2a1f3e-1d4b-4a9c-bb12-3e5f7a9c1d2b",
    "created_by_name": "Admin",
    "updated_by": null,
    "updated_by_name": null,
    "created_at": "2026-06-23T09:14:22.000Z",
    "updated_at": "2026-06-23T09:14:22.000Z"
  }
}
```

**`201` (active เต็ม 20)** — **ไม่ block** การสร้าง; rule ถูกบันทึกเป็น **inactive** (`enabled=false`) + flag `forced_inactive` — เปิดใช้ไม่ได้จนกว่าจะ disable rule active ตัวอื่น (เปลี่ยนจากเดิมที่ตอบ 409 — product decision 2026-06-24, **supersede** STORY AC#1 Sc.2 / EPIC)

```json
{
  "rule": {
    "id": "4d5e6f70-8192-43a4-bd2e-3f4a5b6c7d8e",
    "name": "Tag · refund",
    "action_type": "add_tag",
    "enabled": false,
    "fired_count": 0,
    "created_by_name": "Admin",
    "created_at": "2026-06-24T04:00:00.000Z",
    "updated_at": "2026-06-24T04:00:00.000Z"
  },
  "forced_inactive": true
}
```

**Error `400`** — validation (ต้องมี ≥ 1 condition / action_config ไม่ครบ)

```json
{ "error": "At least 1 condition is required" }
```

ตัวอย่าง create แบบ `add_tag`:

```json
{
  "name": "Tag · ยกเลิก keywords",
  "action_type": "add_tag",
  "trigger_logic": "AND",
  "conditions": [
    { "type": "keyword", "operator": "contains", "value": ["ยกเลิก", "cancel"] },
    { "type": "channel", "operator": "in", "value": ["LINE", "SHOPEE"] }
  ],
  "action_config": { "tag_ids": ["c9d0e1f2-3a4b-4c5d-9e6f-7a8b9c0d1e2f"] }
}
```

---

## 4) `PATCH /v1/omnichat/automation/rules/:id` — Edit rule

`action_type` **แก้ไม่ได้** (fix ตั้งแต่ entry — เปลี่ยน action = สร้างใหม่ · ไม่มีใน DTO) · มีผลกับ message ที่เข้า "หลัง" save เท่านั้น (ไม่ retroactive) · ทุก field optional (PATCH partial) — `name` ≤ 150 ตัวเหมือน create

**Request body** (ส่งเฉพาะ field ที่แก้)

```json
{
  "name": "Auto-reply · นอกเวลาทำการ",
  "trigger_logic": "AND",
  "conditions": [
    { "type": "business_hours", "operator": "outside", "value": { "use_workspace_hours": true } }
  ],
  "action_config": {
    "message": "สวัสดีค่ะ {{customer_name}} ขณะนี้นอกเวลาทำการ ทีมงานจะรีบติดต่อกลับนะคะ",
    "cooldown_minutes": 90
  }
}
```

**Response `200`** — `updated_by` / `updated_at` เปลี่ยนเป็นคนกด save ล่าสุด

```json
{
  "rule": {
    "id": "9f1c2e7a-4b8d-4c1a-9e2f-7a3b1c0d5e6f",
    "name": "Auto-reply · นอกเวลาทำการ",
    "action_type": "auto_reply",
    "trigger_logic": "AND",
    "conditions": [
      { "type": "business_hours", "operator": "outside", "value": { "use_workspace_hours": true } }
    ],
    "action_config": {
      "message": "สวัสดีค่ะ {{customer_name}} ขณะนี้นอกเวลาทำการ ทีมงานจะรีบติดต่อกลับนะคะ",
      "cooldown_minutes": 90
    },
    "enabled": true,
    "fired_count": 342,
    "created_by": "8c2a1f3e-1d4b-4a9c-bb12-3e5f7a9c1d2b",
    "created_by_name": "Admin",
    "updated_by": "b1d2c3e4-5a6f-4708-9c1a-2b3d4e5f6a7b",
    "updated_by_name": "สมศักดิ์ ว.",
    "created_at": "2026-05-30T03:20:00.000Z",
    "updated_at": "2026-06-23T10:05:00.000Z"
  }
}
```

**Error `400`** — validation · **`404`** — ไม่พบ rule

```json
{ "error": "At least 1 condition is required" }
```

---

## 5) `PATCH /v1/omnichat/automation/rules/:id/enabled` — Enable / Disable

`fired_count` ไม่แตะ · enable เช็ค limit 20 ซ้ำ · มีผลกับ engine ทันที (DEL cache)

**Request body**

```json
{ "enabled": false }
```

**Response `200`**

```json
{
  "rule": {
    "id": "9f1c2e7a-4b8d-4c1a-9e2f-7a3b1c0d5e6f",
    "name": "Auto-reply · Outside hours",
    "enabled": false,
    "fired_count": 342,
    "updated_by": "8c2a1f3e-1d4b-4a9c-bb12-3e5f7a9c1d2b",
    "updated_by_name": "Admin",
    "updated_at": "2026-06-23T10:10:00.000Z"
  }
}
```

**Error `409`** — enable (`{ "enabled": true }`) ขณะ active เต็ม 20 (เช็คใน serializable transaction)

```json
{ "error": "Active rule limit reached (20). Disable a rule first." }
```

**Error `404`**

```json
{ "error": "Automation rule not found" }
```

---

## 6) `DELETE /v1/omnichat/automation/rules/:id` — Hard delete

**Admin เท่านั้น** · ลบจริงจาก DB ถาวร (ไม่มี soft flag) · FE แสดง confirmation dialog (ชื่อ rule + fired_count + warning) ก่อนเรียก · `:id` ผ่าน `ParseUUIDPipe` · `tenant_id` ส่งเป็น query param (gateway เติมจาก JWT)

**Response `200`**

```json
{ "success": true }
```

**Error `403`** — Supervisor / Agent (รวมยิง API ตรงเพื่อ bypass UI)

```json
{ "error": "permission_denied" }
```

**Error `404`**

```json
{ "error": "Automation rule not found" }
```

---

## Shared shapes

`conditions[]` — array, อ่านเทียบ `trigger_logic` (`AND` = ทุกข้อต้องผ่าน / `OR` = ผ่าน ≥ 1)

| `type` | operator | value | หมายเหตุ |
| --- | --- | --- | --- |
| `keyword` | `contains` / `exact` | `string[]` | case-insensitive ไทย-อังกฤษ — match `message.content` |
| `channel` | `in` | `ChannelType[]` | `LINE` `FACEBOOK` `INSTAGRAM` `SHOPEE` `LAZADA` `TIKTOK` |
| `business_hours` | `within` / `outside` | `{ use_workspace_hours, timezone?, days?, ranges? }` | `use_workspace_hours=true` → ดึง workspace tz ทุกครั้ง (ไม่ cache) |

`action_config` — ขึ้นกับ `action_type`

| `action_type` | shape | required |
| --- | --- | --- |
| `auto_reply` | `{ message, cooldown_minutes }` | ทั้งคู่ — `message` รองรับ `{{customer_name}}` ฯลฯ; `cooldown_minutes` กัน loop |
| `add_tag` | `{ tag_ids: string[] }` | `tag_ids` ≥ 1 (uuid ของ tag) — append-only, skip tag ที่ถูกลบ · cooldown = default ระบบ `RULE_TAG_COOLDOWN_MINUTES` (ไม่อยู่ใน config, กัน tag เด้งกลับหลัง agent ลบ) |

> รายละเอียด field + index + Redis keys เต็ม ดู [ER doc](./RA-01_rule_automation_er.md) · flow แต่ละเส้น ดู [Sequence doc](./RA-01_rule_automation_sequence.md)

---

## Permission matrix

| การกระทำ | endpoint | `view_*` | `manage_*` | `delete_*` | Admin | Supervisor | Agent |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: |
| ดู list | #1 | ✓ | | | ✓ | ✓ | ✓ |
| ดู rule เดียว (edit) | #2 | | ✓ | | ✓ | ✓ | ✗ |
| สร้าง | #3 | | ✓ | | ✓ | ✓ | ✗ |
| แก้ไข | #4 | | ✓ | | ✓ | ✓ | ✗ |
| Enable/Disable | #5 | | ✓ | | ✓ | ✓ | ✗ |
| ลบ (hard) | #6 | | | ✓ | ✓ | ✗ | ✗ |

`*` = `automation_rules` · permission ใหม่ 3 ตัวเพิ่มใน `packages/shared/src/types/rbac.types.ts` (ดู ER doc)
