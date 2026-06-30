# EPIC-ACE-2211: Sprint Planning Prep

เอกสารเตรียม sprint planning สำหรับ Epic Rule Automation (18 SP, 4 stories)
อิง dependency + reality check จาก `story-task-breakdown.md` — **ช่องที่เป็น `___` ให้ทีมเติมตอน planning**

> Related: [Epic](ACE-2211_EPIC-A4.1_Rule_Automation.md) · [Task breakdown](story-task-breakdown.md) · Stories: [RA-01](ACE-2212_STORY-RA-01_Rule_Management_CRUD.md) [RA-02](ACE-2213_STORY-RA-02_Define_Trigger_Conditions.md) [RA-03](ACE-2214_STORY-RA-03_Send_Auto_reply_Message.md) [RA-04](ACE-2215_STORY-RA-04_Auto_Tag_Conversation.md)

---

## 0. Capacity (ทีมเติม)

| รายการ | ค่า |
|--------|-----|
| Sprint length | `___` (เช่น 2 สัปดาห์) |
| ทีม BE (คน) | `___` |
| ทีม FE (คน) | `___` |
| Velocity ต่อ sprint (SP) | `___` |
| จำนวน sprint ที่คาดว่าใช้ | `___` (ถ้า velocity ~6–7 SP → 3 sprints) |

---

## 1. Sprint Goal (ทีมเติม / draft)

- **Sprint 1:** วาง foundation — สร้าง/แก้ rule ได้ครบ CRUD + permission (ยังไม่ trigger จริง)
- **Sprint 2:** rule trigger ได้จริง — engine + conditions + test panel
- **Sprint 3:** action ทำงานครบ — auto-reply + auto-tag + attribution ถูกต้อง

---

## 2. Proposed Sprint Allocation (อิง dependency — ห้ามสลับลำดับ story)

ลำดับบังคับ: **RA-01 → RA-02 → (RA-03 ∥ RA-04)**
เหตุผล: RA-02 engine ต้องมี `automation_rules` table (1.1) ก่อน; RA-03/04 executor เสียบเข้า engine (2.1); FE ทุก step ต้องมี wizard shell (1.7)

| Sprint | Stories | SP | งานหลัก |
|--------|---------|----|---------|
| **Sprint 1** | RA-01 Rule Management | 8 | DB table + CRUD API + RBAC + FE shell (list, card, modal, wizard shell, delete dialog) |
| **Sprint 2** | RA-02 Trigger Conditions | 5 | message hook + rule engine + 3 evaluators + AND/OR + Step 1 UI + test panel |
| **Sprint 3** | RA-03 Auto-reply + RA-04 Auto-tag | 2 + 3 | 2 executors + sender_type/migration + Step 2 UI (auto-reply + add-tag) + tooltip |

**Parallel tracks ในแต่ละ sprint (BE ∥ FE):**
- Sprint 1: BE ทำ 1.1→1.2→1.3 // FE ทำ 1.4–1.8 (FE เริ่มด้วย mock จนกว่า API จะพร้อม)
- Sprint 2: BE ทำ 2.1–2.6 // FE ทำ 2.7–2.8 (test panel ใช้ logic เดียวกับ BE รัน client-side)
- Sprint 3: BE ทำ 3.1/3.3/3.4 + 4.1/4.2 // FE ทำ 3.5 + 4.3 + 4.4

> **Early-start option:** เมื่อ 1.1 (table) merge แล้ว BE เริ่ม 2.1 (engine) ได้เลยภายใน Sprint 1 ถ้ามี capacity เหลือ

---

## 3. 🔑 Open Decisions — ต้องเคลียร์ก่อน/ต้นวง (ไม่ตอบ = estimate ไม่ได้)

| # | Decision | ตัวเลือก | กระทบ | Owner | ต้องตอบก่อน |
|---|----------|---------|-------|-------|-------------|
| D1 | Auto-reply retry pattern (Task 3.1) | inline `executeWithRetry` (omnichat-gateway) **vs** BullMQ queue (ai-ingestion pattern) | SP + infra (queue ใหม่?) | `___` | Sprint 3 |
| D2 | Cooldown store (Task 3.3) | Redis key (แนะนำ) **vs** DB table | SP เล็กน้อย + audit | `___` | Sprint 3 |
| D3 | RBAC "Supervisor แก้ได้แต่ลบไม่ได้" (Task 1.3) | hard-check `role==='admin'` ใน DELETE controller **vs** เพิ่ม action `delete_automation_rules` แยก | AC + permission seed | `___` | **Sprint 1** |
| D4 | `sender_type='rule'` threading (Task 3.4) | ร้อยผ่าน `sendMessage` + กัน SLA state machine ไม่ให้ advance "first agent response" — ต้อง BE owner sign-off (แตะ flow หลัก) | risk สูง (กระทบ SLA/KPI) | `___` | **Sprint 1** (ตัดสินใจ design ก่อน) |
| D5 | Shopee/TikTok ส่ง auto-reply ไม่ได้ | ซ่อน/disable 2 channel ใน picker ของ auto-reply rule **vs** allow+skip ตอน execute **vs** โชว์ warning — **mockup ปัจจุบัน = เลือกได้ ไม่มี warning** (มี AC #1 Scenario 3 รองรับ allow+skip) | AC + UX | `___` | Sprint 2 (ก่อน FE Step 2) |
| D6 | Design/Figma สำหรับ wizard | ✅ **mockup ส่งแล้ว** (7 จอ) ครอบ list/action-first/2-step/auto-reply/add-tag/saved — **ยังขาด: BH condition card, delete dialog (1.8), add-tag preview** | FE estimate | `___` | ปิดส่วนใหญ่; เหลือ BH card ก่อน Sprint 2, delete dialog ก่อน Sprint 1 |
| D7 | Keyword หลายคำต่อ condition | ✅ ยืนยันจาก mockup (`'ยกเลิก', 'cancel'`) → `value: string[]`, match คำใดคำหนึ่ง (แก้ใน 1.1/2.3 แล้ว) | schema + evaluator | — | ตัดสินแล้ว |
| D8 | Fallback value ต่อ variable | mockup Step 2 **ไม่มี** fallback UI → เก็บ (เพิ่ม design + 3.2/3.5) **vs** ตัด (YAGNI) | scope 3.2/3.5 + AC | `___` | ก่อน Sprint 3 |
| D9 | Pills filter (All/Auto-reply/Tag) | mockup **ไม่มี** → ตัด (≤20 rules ไม่จำเป็น) **vs** เพิ่ม (1.4) | scope 1.4 | `___` | ก่อน Sprint 1 |

---

## 4. Cross-Service Ownership — งานนี้แตะ 5 service + FE

| Service / Repo | Tasks ที่เกี่ยวข้อง | Owner (TBD) |
|----------------|---------------------|-------------|
| `omnichat-service` | 1.1 schema, backend CRUD, 2.1 engine, 2.2–2.6 evaluators, 3.1 executor, 3.4, 4.1 executor, 4.2 migration | `___` |
| `api-gateway` | 1.2 controllers/services (proxy) | `___` |
| `user-service` | 1.3 RBAC seed (`PERMISSION_MATRIX`) | `___` |
| `tenant-service` | 2.5 อ่าน business-hours config ข้าม service | `___` |
| `packages/shared` | 1.3 `rbac.types.ts`, 2.5 import `business-hours.utils` | `___` |
| `workspace-admin` (FE) | 1.4–1.8, 2.7, 2.8, 3.5, 4.3, 4.4 | `___` |

> **ผลต่อ planning:** ต้องมีคน BE ที่เข้าถึง/รีวิวได้หลาย service โดยเฉพาะ `user-service` (RBAC) + `tenant-service` (BH) — ถ้าคนละทีมดูแล ให้เพิ่ม cross-team dependency เข้า board

---

## 5. Re-estimate Check (scope เปลี่ยนหลัง reconcile กับ code)

| Task | SP เดิม (โดยรวมใน story) | ทิศทาง | เหตุผล |
|------|------------------------|--------|--------|
| 3.4 sender_type | — | 🔽 เบาลง | ไม่ใช่ enum migration — เป็น app-level convention |
| 3.1 auto-reply executor | — | 🔼 หนักขึ้น | เพิ่ม channel-support guard + ต้องเลือก retry (D1) + กัน SLA state (D4) |
| 2.5 business hours evaluator | — | 🔼 หนักขึ้น | ดึง config ข้าม service (tenant-service) ไม่ใช่ local |
| 1.4–1.8 FE shell | — | 🔼 ระวัง | wizard + list หนักกว่า settings เดิม (single-form) — ขึ้นกับ D6 |

**Action:** ยืนยัน RA-02 (5) และ RA-03 (2) ระหว่าง planning — net SP น่าจะใกล้เดิม 18 แต่ RA-03 ที่ตั้งไว้ 2 SP อาจตึงหลัง D1/D4

---

## 6. Risks (จาก edge cases + reconcile)

| Risk | กระทบ | Mitigation |
|------|-------|-----------|
| `sender_type='rule'` ทำ SLA/KPI เพี้ยน (D4) | report agent ผิด | design review + unit test กัน state machine ก่อน merge |
| ส่ง auto-reply ซ้ำ/loop | customer รำคาญ | cooldown (Redis) + only-first-wins + dedup 5s (guard ใหม่) |
| 5s dedup guard ยังไม่มีในระบบ (เดิม 24 ชม. ที่ webhook) | trigger ซ้ำ | สร้าง guard ใหม่ใน rule engine (Task 2.2) |
| FE wizard ไม่มี design (D6) | estimate ลม / rework | ปิด D6 ก่อน Sprint 1 |

---

## 7. Definition of Ready / Done

ใช้ DoR/DoD ระดับทีม (ไม่ผูกกับ epic นี้) — ก่อนดึง story เข้า sprint ให้เช็ค: AC ชัด ✓ (มีใน ACE-2212–2215), dependency unblocked ✓ (ดู §2), open decision ที่เกี่ยวข้องปิดแล้ว ✓ (ดู §3)
