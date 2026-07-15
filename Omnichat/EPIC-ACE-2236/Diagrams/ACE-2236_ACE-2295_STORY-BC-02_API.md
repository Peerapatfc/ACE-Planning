# STORY-BC-02: Audience Selection and Targeting — API Reference

**Epic:** [ACE-2236](https://app.clickup.com/t/86d318wjb) | **Story:** [ACE-2295](https://app.clickup.com/t/86d32c89v) | คู่กับ [Sequence Diagram](ACE-2236_ACE-2295_STORY-BC-02_Sequence_Diagram.md) · [ER Diagram](ACE-2236_ACE-2295_STORY-BC-02_ER_Diagram.md)

**Convention (ตาม BC-01):** ทุก endpoint ต้องมี Bearer JWT (Clerk) · response envelope = `{code, message, data}` โดย success `code = "1000"` · business error → HTTP 200 + error code (`CodeBroadcastValidation` ฯลฯ) · infra error → 5xx (log ก่อนเสมอ) · JSON field เป็น camelCase

## สรุป API ทั้งหมดของ BC-02

| Method / Path | สถานะ | ใช้ทำอะไร | Orch method | Permission → Role |
|---|---|---|---|---|
| `GET /v1/broadcasts/audience/tags` | **ใหม่** | tag list ของชนิดตามโหมด + จำนวนคนต่อ tag (dropdown) | `ListAudienceTags` | ไม่ gate → ทุก role |
| `GET /v1/broadcasts/audience/estimate` | **ใหม่** | นับ recipients + total (estimated reach) | `EstimateAudience` | ไม่ gate → ทุก role |
| `POST /v1/broadcasts` | ขยาย | create broadcast + targeting | `Create` | `org:broadcast:manage` → Admin·Sup |
| `PATCH /v1/broadcasts/:id` | ขยาย | update broadcast + targeting (full resubmit) | `Update` | `org:broadcast:manage` → Admin·Sup |
| `GET /v1/broadcasts/:id` | ขยาย response | โหลด broadcast + targetTags (restore chips) | `GetByID` | ไม่ gate → ทุก role |

> GET ไม่ gate permission ตาม epic "Agent: read only permission for broadcast features" — pattern เดียวกับ `GET /v1/broadcasts` เดิม
> **BC-03 (send) ไม่มี endpoint ใหม่** — ใช้ POST/PATCH เดิมด้วย `action=send` แล้ว dispatch ทำงานเป็น background ภายใน server

---

## 1. GET /v1/broadcasts/audience/tags (ใหม่)

ดึง tag list ของชนิดที่ตรงกับโหมด targeting พร้อมจำนวนคนที่ส่งถึงได้บน OA นั้นต่อ tag — FE โหลด lazy ครั้งแรกที่เข้าโหมด แล้ว cache แยกตาม (OA, type)

**Query params**

| param | type | required | ความหมาย |
|---|---|---|---|
| `channelAccountId` | uuid | ✓ | LINE OA ที่เลือกใน BC-01 — count จะ scope ตาม OA นี้ |
| `type` | `contact` \| `chat` | ✓ | ชนิด tag: `contact` = tag ระดับบุคคล (โหมด specific_people) · `chat` = tag ระดับแชท (โหมด specific_chat) |

**Response 200**

```json
{
  "code": "1000",
  "message": "ok",
  "data": [
    { "id": "uuid", "name": "NEW CUSTOMER", "contactCount": 82 },
    { "id": "uuid", "name": "PREMIUM", "contactCount": 98 },
    { "id": "uuid", "name": "VIP", "contactCount": 125 }
  ]
}
```

- เรียงชื่อ A-Z · เอาเฉพาะ tag ที่ยังไม่ถูกลบ (soft delete แล้วไม่โผล่)
- `contactCount` = จำนวนคนใน base set ของ OA นี้ (เคยทัก + มี LINE userId) ที่ถือ tag นั้น — จักรวาลเดียวกับ estimate เสมอ

**Errors:** 401 ไม่มี/JWT ผิด · 400 param ขาดหรือ type ไม่ใช่ contact|chat · workspace ไม่พบ → 200 + error code (convention เดิม)

---

## 2. GET /v1/broadcasts/audience/estimate (ใหม่)

นับยอดผู้รับตามเงื่อนไข targeting ปัจจุบัน — FE ยิงใหม่อัตโนมัติทุกครั้งที่ chips เปลี่ยน (React Query key: `[oaId, targetingType, includeIds, excludeIds]`)

**Query params**

| param | type | required | ความหมาย |
|---|---|---|---|
| `channelAccountId` | uuid | ✓ | LINE OA ที่เลือก |
| `targetingType` | `all` \| `specific_people` \| `specific_chat` | ✓ | โหมด — บอกด้วยว่า tag ids ชี้ library ไหน |
| `includeTagIds` | csv ของ uuid | เมื่อโหมด specific | tag ฝั่ง include (ชนิดตามโหมด · โหมด all ห้ามส่ง) |
| `excludeTagIds` | csv ของ uuid | — (optional) | tag ฝั่ง exclude (ชนิดตามโหมด · เฉพาะโหมด specific — โหมด all ห้ามส่ง) |

**Response 200**

```json
{
  "code": "1000",
  "message": "ok",
  "data": { "recipients": 280, "total": 400 }
}
```

- `recipients` = คนใน base set ที่ผ่านเงื่อนไข include ของโหมด (โหมด all = ทุกคน) และไม่มี exclude tag เลย — dedup แล้ว (คนถือหลาย tag นับครั้งเดียว)
- `total` = ทุกคนใน base set · FE คิด % badge = recipients/total เอง
- โหมด `all` ไม่มี tag → `recipients == total` (100%) เสมอ
- โหมด specific + `includeTagIds` ว่าง → `recipients = 0` (ปกติ FE ไม่ยิงเคสนี้ โชว์ 0 เองเลย)
- ยิง `channelAccountId` ของ workspace อื่น → ได้ 0 เฉยๆ (query scope workspace ใน WHERE — ไม่รั่ว)
- AC4: ต้องตอบภายใน 2 วินาที (implement จริงเป็น query เดียว ~ms)

**Errors:** 401 · 400 param ผิดรูป (targetingType นอกลิสต์, uuid ผิด format)

---

## 3. POST /v1/broadcasts · PATCH /v1/broadcasts/:id (ขยายของเดิม)

Multipart form เดิมของ BC-01 ทุก field — BC-02 เพิ่ม 3 field:

| field ใหม่ | type | ความหมาย |
|---|---|---|
| `targetingType` | `all` \| `specific_people` \| `specific_chat` | โหมด targeting (เดิมมีแต่ `all`) |
| `targetTags` | JSON string: `[{"id": "uuid", "mode": "include" \| "exclude"}]` | tag ที่เลือก — ชนิดเดียวตามโหมดเสมอ server จึง**ใส่ `tag_type` ให้ทุกแถวเองจาก `targetingType`** (payload ไม่ส่ง type) |
| `targetEstimate` | int | ยอดจากผล estimate ล่าสุด (snapshot เก็บโชว์ใน list/detail — เลิกใช้ followerCount) |

**Validation เพิ่มจาก BC-01 (เฉพาะ `action=send|schedule` — draft เป็น soft validation):**

| เคส | ผล |
|---|---|
| โหมด specific + ไม่มี include tag | 200 + `CodeBroadcastValidation` — "กรุณาเลือกอย่างน้อย 1 tag" (AC1.5) |
| โหมด all + มี tag ใดๆ | 200 + `CodeBroadcastValidation` (everyone ไม่มีช่อง tag) |
| tag เดียวกันอยู่ทั้ง include และ exclude | 200 + `CodeBroadcastValidation` (DB `UNIQUE(broadcast_id, tag_id, tag_type)` กันซ้ำอีกชั้น) |

**Response:** เดิมของ BC-01 — `{id, code, status, updatedAt}` (201 สำหรับ POST, 200 สำหรับ PATCH)
**การเก็บ:** targeting เขียนลง `broadcasts.targeting_type/target_estimate` + `messaging.broadcast_tags` แบบ full-replace ใน transaction เดียวกับ messages

---

## 4. GET /v1/broadcasts/:id (ขยาย response)

ของเดิมทุกอย่าง + เพิ่ม field ใน `data` สำหรับ restore หน้า edit:

```json
{
  "targetingType": "specific_people",
  "targetTags": [
    { "id": "uuid", "name": "VIP", "mode": "include" },
    { "id": "uuid", "name": "NEW CUSTOMER", "mode": "include" },
    { "id": "uuid", "name": "TEST GROUP", "mode": "exclude" }
  ],
  "targetEstimate": 271
}
```

- `name` = ชื่อ*ปัจจุบัน*จาก library (JOIN ตอนอ่าน) — tag ถูก rename แล้วได้ชื่อใหม่, tag ถูกลบแล้วไม่โผล่มา (ไม่เหลือ chip ค้างของ tag ที่ถูกลบ)
- FE ใช้ `targetingType` ติ๊ก radio, `targetTags` restore chips แยกช่องตาม `mode` แล้วยิง estimate ใหม่ทันที (โชว์เลขสด ไม่ใช่ `targetEstimate` ที่เซฟไว้)

---

## Standard test cases (ตาม CLAUDE.md — ใช้กับทุก endpoint ข้างบน)

| เคส | คาดหวัง |
|---|---|
| JWT ขาด/ผิด | 401 |
| JWT ถูกแต่คนละ workspace | ไม่พบ/ผลว่าง/0 — ห้าม 500 |
| Request ถูกต้อง | 200/201 + JSON shape ตาม doc นี้ (field camelCase ครบ) |
| Body/param ผิดรูป | 400 พร้อม message |
| DB/infra error | 500 + log ฝั่ง server (ห้าม silent) |
