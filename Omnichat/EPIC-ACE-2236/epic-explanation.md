# EPIC ACE-2236: Broadcast — คำอธิบายแบบเข้าใจง่าย (อ้างอิงโค้ดจริง)

**Status:** Backlog | **ClickUp:** [ACE-2236](https://app.clickup.com/t/86d318wjb) | **Product:** Omni
**Stories:** BC-01..BC-06 (ACE-2294, 2295, 2457, 2297, 2503, 2504)

> เอกสารนี้สรุป Epic Broadcast ให้เข้าใจง่าย **และ** แมปลงโค้ดจริงในรีโป `ace` (NestJS microservices + Next.js `workspace-admin`) เพื่อให้รู้ว่าอะไร "มีอยู่แล้วเอามาใช้ได้" และอะไร "ต้องสร้างใหม่" ฟีเจอร์ Broadcast **ยังไม่มีในโค้ด** (greenfield) — ทุกอย่างในนี้คือการต่อยอดจากระบบที่มีอยู่

---

## สรุปภาพรวม

วันนี้ถ้าธุรกิจอยากส่งข้อความหาลูกค้าจำนวนมากผ่าน LINE (โปรโมชั่น/ประกาศ) ต้องไปใช้ **LINE OA Manager** แยกต่างหาก ทำให้หลุดออกจาก unified inbox ที่ทีมใช้คุยกับลูกค้าอยู่แล้ว

Epic นี้สร้างระบบ **Broadcast** ในตัว Omnichat เอง: เลือก LINE OA → เลือกกลุ่มเป้าหมายด้วย tags → เขียนข้อความ (text/รูป) → ตั้งเวลาหรือส่งทันที → ระบบทยอยส่งเป็น batch แล้วติดตามสถานะแบบเรียลไทม์ พร้อมประวัติย้อนหลังครบ

**เปรียบเทียบง่าย ๆ:**
เหมือน "การส่งจดหมายเวียน (mail merge)" — เขียนจดหมายฉบับเดียว เลือกว่าจะส่งถึงใคร (ตามป้ายกำกับลูกค้า) แล้วระบบไปรษณีย์ในตัวก็แบ่งกองทยอยส่งให้ ใครส่งไม่ถึงก็จดไว้ว่าเพราะอะไร และเราดูสถานะการส่งของจดหมายทุกฉบับได้จากที่เดียว

**Phase 1 = LINE เท่านั้น** (Facebook/IG/อื่น ๆ เป็น Phase ถัดไป)

---

## 1. แนวคิดหลัก (Core Concepts)

### 1.1 วงจรสถานะของ Broadcast (Status Lifecycle)
Broadcast หนึ่งอันจะเดินผ่านสถานะเหล่านี้ (สถานะคุมว่าหน้า List/Detail แสดงปุ่มอะไร):

| สถานะ | ความหมาย | ปุ่มที่ทำได้ |
|---|---|---|
| **Draft** (แบบร่าง) | สร้างค้างไว้ ยังไม่ส่ง | Continue Edit, Delete |
| **Scheduled** (ตั้งเวลา) | ตั้งเวลาส่งในอนาคต | Edit, Cancel Schedule (→ Draft), Delete |
| **Sending** (กำลังส่ง) | กำลังทยอยส่ง batch | ไม่มีปุ่ม (read-only) |
| **Sent** (ส่งสำเร็จ) | ส่งครบ ไม่มี fail | Delete |
| **Sent with error** | ส่งบางส่วนสำเร็จ | Delete |
| **Error** (ผิดพลาด) | ส่งไม่สำเร็จเลย / quota ไม่พอ | Delete |

### 1.2 การเลือกกลุ่มเป้าหมาย (Targeting)
2 โหมด: **"ส่งทุกคน"** (ทุก contact ที่ผูกกับ LINE OA นั้น) หรือ **"ส่งเฉพาะกลุ่ม"** (เลือกด้วย tags) แล้วระบบคำนวณ **estimated reach** = จำนวน contact ที่ไม่ซ้ำกัน (dedupe) ที่มี LINE user id ใช้ได้ของ LINE OA ที่เลือก

> ⚠️ **จุดสำคัญที่ต้องเคลียร์:** โค้ดปัจจุบันมี tag แค่ **ระดับห้องแชท (conversation-level)** เท่านั้น (`Tag` + `ConversationTag`) — **ยังไม่มี tag ระดับบุคคล (person-level)** ตามที่ BC-02 เขียนไว้ และยังไม่มี API นับ contact ตาม tag ดูหัวข้อ [ประเด็นที่ต้องเคลียร์](#8-ประเด็นที่ต้องเคลียร์ก่อนพัฒนา-open-questions)

### 1.3 การส่งแบบ Batch (Batch Send)
ไม่ส่งทีเดียวรวด แต่แบ่งเป็น **batch ละ 500 คน** ส่งพร้อมกันสูงสุด **3 batch** ทุก recipient มี idempotency key กันส่งซ้ำ ถ้า batch ล้มเหลว retry 3 ครั้งแบบ backoff (2s → 4s) ถ้า recipient โดน rate limit (429) ก็ retry รายคน แล้วบันทึกเหตุผลที่ส่งไม่สำเร็จ (เช่น `user_blocked`, `rate_limited`)

### 1.4 Quota ตาม Plan
ก่อนส่งจริง เช็ก quota ตาม plan: **Free/Basic = บล็อก** ถ้าไม่พอ, **Pro = ส่งได้ (overage)** ถ้าไม่ผ่าน broadcast จะกลายเป็นสถานะ Error เหตุผล `quota_exceeded`

> ⚠️ **จุดสำคัญ:** ระบบ plan/quota (Free/Basic/Pro) **ยังไม่มีอยู่เลยในโค้ด** ต้องสร้างทั้งระบบใหม่

### 1.5 สิทธิ์การใช้งาน (Roles)
3 บทบาท: **admin / supervisor / agent** — Admin/Supervisor จัดการ broadcast ได้ทั้งหมด ส่วน **agent = ดูได้อย่างเดียว (read-only)** ปุ่มสร้าง/แก้/ลบถูก disable

---

## 2. ส่วนประกอบบนหน้าจอ (UI Components)

### หน้า Broadcast List (BC-05)
ตาราง broadcasts ทั้งหมด + **6 tabs** (ทั้งหมด / ตั้งเวลา / ส่งแล้ว / ผิดพลาด / ส่งแล้วแต่มีข้อผิดพลาด / แบบร่าง) + ค้นหาชื่อ + filter (ช่วงวันที่อัปเดต + LINE OA) + จัดเรียงคอลัมน์ + แบ่งหน้า (10/หน้า) + เมนู 3 จุด (action ตามสถานะ) คลิกแถวเพื่อเข้า Detail

### หน้า Broadcast Detail (BC-06)
หัวข้อ + status badge + ข้อมูล (LINE OA, เป้าหมาย, จำนวนผู้รับ) + section "ข้อความ" แสดง message bubbles **แบบอ่านอย่างเดียว** + ปุ่ม action ตามสถานะ ถ้าสถานะ **Sending** จะอัปเดต badge อัตโนมัติเมื่อส่งเสร็จ **โดยไม่ต้อง refresh** ปุ่มกลับ (←) คืนค่า filter/tab เดิมของหน้า List

### หน้า Create/Edit Broadcast (BC-01)
ฟอร์มหน้าเดียว: เลือก LINE OA → ตั้งเวลา (ส่งทันที/ตั้งเวลา) → เลือกเป้าหมาย → ตั้งชื่อ (≤20 ตัว) → message composer (bubble text/รูป, สูงสุด 5, ลากจัดลำดับได้) + **preview แบบ LINE เรียลไทม์** ทางขวา + ปุ่ม Save Draft / Send Test / Send

### Audience Picker (BC-02)
Dropdown ค้นหา tag ได้ + แสดง tag ที่เลือกเป็น chips + คำนวณ reach เรียลไทม์ทุกครั้งที่เพิ่ม/ลบ tag

### Test Broadcast Dialog (BC-04)
เลือกตัวเอง/เพื่อนร่วมทีมที่มี LINE connection (สูงสุด 5 คน) ส่งทดสอบ — **ไม่นับ quota, ไม่บันทึกใน history**

---

## 3. ลำดับการทำงาน (User Flow)

#### สถานการณ์: Admin ส่งโปรโมชั่นปีใหม่หาลูกค้า VIP

1. **สร้าง (BC-01):** Admin เปิดหน้า Create → เลือก LINE OA "ร้าน A" → เลือก "ตั้งเวลา" 1 ม.ค. 09:00 → ตั้งชื่อ "New Year Sale 2026"
2. **เลือกเป้าหมาย (BC-02):** เลือก "ส่งเฉพาะกลุ่ม" → เลือก tag `VIP` และ `New Customer` → ระบบโชว์ "ส่งถึงประมาณ 280 คน (70%)" (นับแบบไม่ซ้ำ)
3. **เขียนข้อความ (BC-01):** เพิ่ม bubble ข้อความ + bubble รูป → ดู preview ฝั่งขวาว่าจะออกมาหน้าตาแบบไหนใน LINE
4. **ทดสอบ (BC-04):** กด Send Test → เลือกตัวเอง → เช็กใน LINE ตัวเองว่าข้อความถูกต้อง (ไม่กิน quota)
5. **ส่ง (BC-03):** กด Send → ยืนยันใน dialog → redirect ไปหน้า List, broadcast ขึ้นสถานะ **"กำลังส่ง"** ทันที
6. **ระบบทำงานเบื้องหลัง (BC-03):** เช็ก quota → แบ่ง 280 คนเป็น batch → ทยอย push ผ่าน LINE → จดผล/เหตุผลของแต่ละคน
7. **ติดตามผล (BC-03/06):** เมื่อเสร็จ สถานะเด้งเป็น **"Sent"** อัตโนมัติ + **toast เด้งเฉพาะคนที่กดส่ง** ("Broadcast id: ... send successfully") ไม่ว่าจะอยู่หน้าไหน
8. **ดูรายละเอียด (BC-06):** Admin คลิกเข้า Detail เห็นข้อความที่ส่ง วันเวลา และจำนวนผู้รับ

---

## 4. การวางบนระบบจริง (Grounding บนโค้ด `ace`)

Broadcast ลงร่องเดียวกับฟีเจอร์เดิม ๆ ตาม **3-tier convention** ของ ACE (ใช้ `tags` เป็นแม่แบบที่สะอาดที่สุด, `contact-notes` เป็นแม่แบบ audit):

```
workspace-admin (Next.js)  →  api-gateway (proxy + auth/permission)  →  omnichat-service (logic + Prisma + LINE)
        UI/หน้าจอ                  ดึง tenantId/userId จาก JWT             โมเดล + ส่ง LINE จริง + batch
```

- **omnichat-service** = เจ้าของ logic ทั้งหมด: โมเดล Prisma ใหม่ + `BroadcastModule` (service + controller HTTP/TCP + migration)
- **api-gateway** = proxy บาง ๆ ดึง `@CurrentUser` จาก JWT + ใส่ `@RequirePermission` แล้ว forward ต่อ (เหมือน `tags.controller.ts` เป๊ะ)
- **workspace-admin** = route `(main)/dashboard/broadcast/{page.tsx, create/page.tsx, [id]/page.tsx}` + `_api/broadcast.api.ts` (server actions เรียก `httpClient` → `/v1/omnichat/broadcast*`)

### สิ่งที่ "มีอยู่แล้ว" เอามาใช้ซ้ำได้ (Reuse) ✅

| ส่วน | ของจริงในโค้ด | ใช้ทำอะไรใน Broadcast |
|---|---|---|
| ส่งข้อความเข้า LINE | `LineStrategy.pushMessage()` → `LineExternalService.pushTextMessage(token, to, content, retryKey)` (`@line/bot-sdk`) | core ของการส่งทุก recipient (BC-03/04) |
| Credential LINE OA | `CredentialsService.getCredential()` ถอดรหัส token ตอนใช้ | ดึง access token ของ OA (ควร pre-fetch ครั้งเดียวต่อ OA) |
| Idempotency / retry | `Message.retry_key` (unique) + `retryPushMessage()` | กันส่งซ้ำตอน retry รายคน |
| Backoff (รวม 429) | `BackoffService` (exp backoff + Retry-After) ใน marketplace-polling | จังหวะ retry ต่อ batch/รายคน (BC-03 AC9/10) |
| ประมวลผลขนาน | `PollingOrchestratorService` chunk + `Promise.allSettled`; worker ใช้ `pLimit` | แม่แบบ "500/batch × 3 ขนาน" |
| คิว/Worker | SQS FIFO (`omnichat-gateway` `QueueService`) + consumer (`omnichat-normalizer-worker`) | (ทางเลือก) รัน batch เบื้องหลัง |
| ฐานข้อมูลกลุ่มเป้าหมาย | `Conversation`(channel_account_id, contact_id) + `ConversationTag` + `Contact.external_user_id` | join หา audience + dedupe ด้วย LINE user id |
| LINE OA | `ChannelAccount` (channel_type=`line`) | เอนทิตีของ "LINE OA" ที่เลือกส่ง |
| สถานะ/เหตุผลส่งไม่สำเร็จ | `Message.status / delivery_status / delivery_message / delivery_metadata` | เก็บผลรายข้อความ (เมื่อมี conversation) |
| เรียลไทม์ | `chat.gateway.ts` → Redis `notifications:events` → ห้อง `user:{id}` → Socket.IO; FE `SocketManager`/`useSocket` + ws-token | toast เฉพาะคนส่ง + สถานะ Sending สด |
| Toast | `Sonner` mount ที่ root | toast เฉพาะผู้ส่ง (BC-03 AC8) |
| สิทธิ์ | `@RequirePermission` + `PermissionGuard` + matrix; FE `getMyPermissionsAction()` | agent read-only (BC-05/06) |
| UI kit | DataTable (TanStack v8) + `useDataTableInstance`, Tabs, Dialog/AlertDialog, DropdownMenu, Badge, RadioGroup, Select | List/Detail/Form/Confirm |
| Multi-select chips | `RecipientMultiSelect` (notification-rules) | tag picker (BC-02) |
| ฟอร์ม | react-hook-form + Zod (เช่น `edit-user-modal`) | ฟอร์ม BC-01 |
| แม่แบบหน้า list+detail+form | feature `documents` (`page.tsx` / `[id]/page.tsx` / `create/page.tsx`) | โครงหน้า Broadcast |
| Server action | `listChannelAccounts(channelType='line')`, `listMembers()` | dropdown LINE OA + รายชื่อทีม test |

### สิ่งที่ "ต้องสร้างใหม่" (Net-new) 🔨

- **โมเดลใหม่:** `Broadcast` (ชื่อ, สถานะ, message_json bubbles, schedule, channel_account_id, target_tag_ids, estimated_reach, tenant_id, created_by, soft delete), `BroadcastRecipient` (per-recipient: contact_id, external_user_id, status, failure_reason, retry_count), `BroadcastAudit` (เลียนแบบ `ContactNoteAudit`)
- **BroadcastOrchestratorService:** ตัด batch 500, ขนาน 3, retry per batch, pre-fetch token ครั้งเดียว
- **LINE error parser:** แปลง HTTP status/body → เหตุผล (`user_blocked` 403 / `rate_limited` 429 / `invalid_user` 400) — ปัจจุบันแค่ log `error.message`
- **ระบบ Plan/Quota ทั้งระบบ:** `Tenant.plan` enum + `BroadcastUsage` (หรือ Redis counter) + guard `canSend()` — **ไม่มีอะไรเลยวันนี้**
- **Person-level tags** (ถ้ายืนยันตาม BC-02) + **endpoint คำนวณ reach** (distinct contact_id)
- **การ join WorkspaceMember ↔ LINE Contact** สำหรับ BC-04 (วันนี้ User/WorkspaceMember ไม่มี line_user_id เลย)
- **Permission actions ใหม่:** `view_broadcast / create_broadcast / send_broadcast / edit_broadcast / delete_broadcast` + seed matrix (agent = view เท่านั้น)
- **Realtime event ใหม่** สำหรับสถานะ broadcast (ต้องเพิ่มใน `NotificationEvent` ฝั่ง user-scoped เท่านั้น ตาม comment ความปลอดภัยในไฟล์ — ห้ามใส่ใน `OmnichatEvent` ที่เป็น tenant-wide)
- **FE ทั้งหมด:** routes + ฟอร์ม + bubble editor (ลากจัดลำดับ) + LINE preview + list (tabs/filter) + detail (action ตามสถานะ) + `broadcastStore` (Zustand) + socket listeners

---

## 5. สรุป Scope

| หมวด | รายละเอียด |
|---|---|
| ช่องทาง Phase 1 | LINE OA เท่านั้น |
| Stories | 6 (BC-01 สร้าง/แก้, BC-02 เป้าหมาย, BC-03 ส่ง, BC-04 ทดสอบ, BC-05 list, BC-06 detail) |
| Batch | 500 คน/batch, ขนานสูงสุด 3, retry 3 ครั้ง backoff |
| ข้อความ | text + รูป, สูงสุด 5 bubble/broadcast |
| Quota | Free/Basic บล็อก, Pro overage (overage = tracked-only ใน Phase 1) |
| สิทธิ์ | admin/supervisor จัดการได้, agent อ่านอย่างเดียว |
| Out of scope | quick reply, personalization vars, template library, analytics, ช่องทางอื่น, recurring, Narrowcast API, video/carousel |

---

## 6. คำอธิบายแต่ละ Story (Story Breakdown)

### BC-01 — Create and Edit Broadcast (ACE-2294)
**เป้าหมาย:** ฟอร์มหน้าเดียวสร้าง/แก้ broadcast พร้อม preview แบบ LINE สด และ save draft
**Reuse:** 3-tier convention, `listChannelAccounts`, react-hook-form+Zod, Dialog/Select, soft-delete+tenant scoping
**Net-new:** โมเดล `Broadcast`+migration, CRUD service, รูปแบบ `message_json`, **bubble editor + ลากจัดลำดับ**, **ตัว render preview LINE**, validate ชื่อ ≤20, draft semantics

### BC-02 — Audience Selection and Targeting (ACE-2295)
**เป้าหมาย:** เลือกทุกคน/เฉพาะกลุ่มด้วย tags + คำนวณ reach แบบไม่ซ้ำ เรียลไทม์
**Reuse:** join `ConversationTag → Conversation → Contact` (distinct contact_id), `TagsService.listTags`, `RecipientMultiSelect` chips, `Contact.external_user_id` เป็น key dedupe/ความถูกต้อง
**Net-new:** **endpoint คำนวณ reach**, **person-level tags ไม่มีในระบบ** (วันนี้มีแค่ conversation-level — ต้องเคลียร์ดีไซน์), นิยาม "ส่งทุกคน" = ทุก contact บน OA ที่มี conversation + external_user_id ใช้ได้

### BC-03 — Send Broadcast (ACE-2457)
**เป้าหมาย:** ยืนยัน → เช็ก quota → batch send + retry → สรุปผล + toast เฉพาะผู้ส่ง + สถานะอัปเดตสด
**Reuse:** `pushMessage` + `retry_key`, `BackoffService`, แพตเทิร์น chunk/`Promise.allSettled`, Redis → ห้อง `user:{id}` (เฉพาะผู้ส่ง), Sonner, AlertDialog
**Net-new:** **orchestrator ตัด batch/ขนาน/retry**, **LINE error parser**, โมเดล `BroadcastRecipient`, **ระบบ quota ทั้งระบบ**, event สถานะ broadcast, การจัดการ recipient ที่ยังไม่มี `Conversation` (เพราะ `Message.conversation_id` เป็น NOT NULL)

### BC-04 — Test Broadcast (ACE-2297)
**เป้าหมาย:** ส่งทดสอบหาตัวเอง/ทีม (≤5) ไม่กิน quota ไม่เก็บ history
**Reuse:** `GET /api/members` (`listMembers`), Dialog + multi-select, `pushMessage`, Sonner
**Net-new:** **การจับคู่ WorkspaceMember ↔ LINE Contact** (วันนี้ไม่มี link), cap 5, เส้นทางทดสอบที่ bypass quota + ไม่บันทึก

### BC-05 — Broadcast List (ACE-2503)
**เป้าหมาย:** ตาราง + tabs ตามสถานะ + ค้นหา/filter + sort + paginate + เมนู 3 จุด + agent read-only
**Reuse:** DataTable + `useDataTableInstance`, Tabs, `DataTablePagination`, DropdownMenu action column (แม่แบบ `documents`), Badge, `listChannelAccounts`, permission gating
**Net-new:** endpoint list + filter (tab→status, ช่วงวันที่, OA), เมนู action ตามสถานะ, index ของ query, permission `view_broadcast`

### BC-06 — Broadcast Detail (ACE-2504)
**เป้าหมาย:** หน้า detail ตามสถานะ, bubble read-only, action ตามสถานะ, สถานะ Sending สด, back คืน filter/tab, agent read-only
**Reuse:** แพตเทิร์น `[id]/page.tsx`, AlertDialog, socket/`useSocket`+Sonner, permission gating, soft-delete+audit tx
**Net-new:** endpoint detail, ชุด action ตามสถานะ, โมเดล `BroadcastAudit`, อัปเดต Sending สด (ใช้ event เดียวกับ BC-03), เก็บ filter/tab ตอนกดกลับ

---

## 7. ความเสี่ยง / Blast radius

- การ **push LINE จำนวนมาก** กระทบ rate limit ของ LINE OA จริง — ต้องเทสต์ orchestrator + backoff ให้ดีก่อนเปิด
- **Quota ผิดพลาด** อาจทำให้ลูกค้าโดนคิดเงิน overage เกิน — ต้อง lock การคำนวณให้แน่ (race condition AC7)
- โมเดล/migration ใหม่หลายตัวบน schema ที่มี multi-tenancy — ต้องคุม `tenant_id` ทุก query (ตาม convention เดิม)
- เรียลไทม์: ระวังอย่าใส่ event broadcast ลง `OmnichatEvent` (tenant room) เพราะจะรั่วข้ามผู้ใช้ — ต้องใช้ `NotificationEvent` (user room) ตาม comment ในไฟล์ gateway

---

## 8. ประเด็นที่ต้องเคลียร์ก่อนพัฒนา (Open Questions)

ทั้งหมดนี้มาจากการตรวจโค้ดจริง — เป็นช่องว่างระหว่าง "สิ่งที่ story เขียน" กับ "สิ่งที่ระบบมีตอนนี้":

1. **Person-level tags (BC-02):** ระบบมีแค่ tag ระดับห้องแชท — "person-level" หมายถึง (ก) tag ที่ roll-up จากทุก conversation ของ contact, (ข) tag ผูกกับ `ContactGroup`, หรือ (ค) โมเดล tag บุคคลใหม่จริง ๆ? เปลี่ยนทั้ง schema และ query คำนวณ reach
2. **Recipient ที่ไม่มี Conversation:** `Message.conversation_id` เป็น NOT NULL (FK บังคับ) — สำหรับ "ส่งทุกคน" หรือคนที่มี LINE id แต่ยังไม่เคยมีห้องแชทบน OA นี้ จะส่งได้ไหม (LINE push ใช้แค่ user id)? ถ้าได้ ควรสร้าง Conversation, หรือไม่เก็บ Message แล้วพึ่ง `BroadcastRecipient` อย่างเดียว, หรือไม่นับใน reach?
3. **Plan/Quota:** plan tiers และระบบ quota **ไม่มีในโค้ดเลย** — plan ควรอยู่ที่ไหน (`Tenant.plan`?), นับ usage ที่ไหน (ตาราง vs Redis), รอบบิลคิดยังไง, "Pro overage" คือ track-only หรือ enforce?
4. **Realtime event:** ใช้ `notification:new` เดิมแนบ payload broadcast หรือเพิ่มชื่อ event ใหม่ `broadcast:status` ใน `NotificationEvent` (ห้ามใส่ใน `OmnichatEvent`)? สรุปชื่อ event + รูปแบบ payload
5. **BC-04 จับคู่สมาชิก↔LINE:** ไม่มี link ระหว่าง WorkspaceMember กับ LINE Contact — จับคู่ด้วยอีเมล, mapping มือ, หรือจริง ๆ คือส่งหา LINE id ของสมาชิกเองในฐานะ follower? กลไกยังไม่นิยาม
6. **Permission grants:** ยืนยัน action ทั้ง 5 และสิทธิ์แต่ละ role (supervisor ได้เต็มไหม, read endpoint ต้องมี guard ไหม)
7. **รูปแบบ message bubble + รูป:** ยืนยัน schema `message_json` และวิธี push รูป — ปัจจุบัน `LineExternalService` มีแค่ `pushTextMessage` (push รูป/หลายข้อความเป็น net-new)
8. **Scheduled send:** ยังไม่มี scheduler สำหรับ broadcast (มีแค่ `SlaCronService`) — จะใช้ cron/ScheduleModule ใหม่ poll หา broadcast ที่ถึงเวลาไหม
9. **อัปโหลดรูป (BC-01):** มี S3/asset upload พร้อมไหม (`Attachment.file_url` บ่งชี้ว่ามี S3) หรือรูป bubble อ้าง URL ภายนอกอย่างเดียว — เส้นทางอัปโหลดตอน compose ยังไม่ยืนยัน
