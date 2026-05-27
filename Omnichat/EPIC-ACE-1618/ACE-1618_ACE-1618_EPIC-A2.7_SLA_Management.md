# EPIC-A2.7: SLA Management

**ClickUp ID:** ACE-1618
**Status:** To Do
**Product:** Omni
**Type:** Epic
**URL:** https://app.clickup.com/t/86d2hdp46
**Last Synced:** 2026-05-25

---

## Overview

SLA (Service Level Agreement) ใน OmniChat คือระบบที่ช่วยให้ทีม CS รู้ว่าต้องตอบ conversation ไหนภายในเวลาเท่าไหร่ และแจ้งเตือนเมื่อใกล้หรือเกิน deadline

**SLA v1 วัดแบบ First Response Time (FRT):** นับตั้งแต่ลูกค้าส่งข้อความครั้งแรก จนถึงตอนที่ agent ส่ง reply ครั้งแรก

---

## Stories

| Story | ชื่อ | สาระสำคัญ | Status | SP | URL |
|-------|------|-----------|--------|----|-----|
| ACE-1640 | STORY-SLA-01: SLA Configuration UI | Settings page: config target time per channel, due soon threshold, global toggle | 🔵 In Progress | 8 | https://app.clickup.com/t/86d2ptdux |
| ACE-1641 | STORY-SLA-02: SLA Timer Engine | คำนวณ sla_due_at, state machine, start/stop logic | 🔵 In Progress | 13 | https://app.clickup.com/t/86d2pte0x |
| ACE-1642 | STORY-SLA-03: Timer Display in Inbox | Badge ใน list, countdown ใน detail, Overdue filter pill | ⚪ To Do | 5 | https://app.clickup.com/t/86d2pte3q |
| ACE-1643 | STORY-SLA-04: Breach Detection & Auto-tag | Background job, system tags sla_breached / sla_met | ⚪ To Do | 5 | https://app.clickup.com/t/86d2pte6q |

**Total: 31 SP**

---

## Subtask Breakdown

### ACE-1640 — STORY-SLA-01: SLA Configuration UI (🔵 In Progress)

| Task | ชื่อ | Assignee | Status | URL |
|------|------|----------|--------|-----|
| ACE-2219 | FE — Implement Global SLA Toggle | Tanawin(Toy) | 🔵 In Progress | https://app.clickup.com/t/86d315hdt |
| ACE-2220 | BE — Create SLA Config Schema & Migration | Siraphob | 🟡 Reviewing | https://app.clickup.com/t/86d315hjy |
| ACE-2221 | BE — SLA Config APIs | Siraphob | 🔵 In Progress | https://app.clickup.com/t/86d315j6t |

### ACE-1641 — STORY-SLA-02: SLA Timer Engine (🔵 In Progress)

| Task | ชื่อ | Assignee | Status | URL |
|------|------|----------|--------|-----|
| ACE-1663 | BE — Add SLA fields to conversations | griangsak | 🔵 In Progress | https://app.clickup.com/t/86d2q9tkn |
| ACE-2223 | BE — Timer start logic | Tanawin(Toy) | ⚪ To Do | https://app.clickup.com/t/86d315md5 |
| ACE-2224 | BE — Timer stop logic | griangsak | ⚪ To Do | https://app.clickup.com/t/86d315p3v |
| ACE-2226 | BE — Implement Business Hours SLA Calculation | griangsak | ⚪ To Do | https://app.clickup.com/t/86d315pux |
| ACE-2227 | BE — Implement SLA Follow-up Cycle Logic | griangsak | ⚪ To Do | https://app.clickup.com/t/86d315q34 |
| ACE-2235 | BE — Implement Websocket | wetchayan | ⚪ To Do | https://app.clickup.com/t/86d315xjm |

### ACE-1642 — STORY-SLA-03: Timer Display in Inbox (⚪ To Do)

| Task | ชื่อ | Assignee | Status | URL |
|------|------|----------|--------|-----|
| ACE-2228 | FE — Add SLA Timer Badge in Conversation List | Siraphob | ⚪ To Do | https://app.clickup.com/t/86d315qfz |
| ACE-2229 | FE — Implement Overdue Filter Pill | Siraphob | ⚪ To Do | https://app.clickup.com/t/86d315r23 |
| ACE-2232 | FE — Implement sort by overdue | Tanawin(Toy) | ⚪ To Do | https://app.clickup.com/t/86d315t7u |
| ACE-2230 | BE — Add Inbox SLA Filter Support | Peerapat | ⚪ To Do | https://app.clickup.com/t/86d315rz8 |
| ACE-2231 | BE — Add SLA Sorting Support | Peerapat | ⚪ To Do | https://app.clickup.com/t/86d315t4b |

### ACE-1643 — STORY-SLA-04: Breach Detection & Auto-tag (⚪ To Do)

| Task | ชื่อ | Assignee | Status | URL |
|------|------|----------|--------|-----|
| ACE-2233 | BE — Create SLA Event & System Tag Schema | Peerapat | ⚪ To Do | https://app.clickup.com/t/86d315tu3 |
| ACE-2234 | BE — Create Breach Detection job | Peerapat | ⚪ To Do | https://app.clickup.com/t/86d315u2q |

---

## Dependency Chain

```
SLA-01 (config) → SLA-02 (engine reads config) → SLA-03 (display reads engine state) → SLA-04 (breach job uses engine state)
```

---

## Terminology Glossary

| Term | ความหมาย | ขยายความ |
|------|-----------|----------|
| FRT | First Response Time | เวลาที่ agent ใช้ในการตอบ conversation ครั้งแรก — SLA v1 วัดค่านี้อย่างเดียว |
| SLA Target | เวลาเป้าหมาย | เวลาที่กำหนดว่าต้องตอบภายในเท่าไหร่ — config ได้ต่อ channel |
| sla_due_at | Deadline ของ conversation | timestamp = first_inbound_at + target_minutes — คำนวณและบันทึกตอน message เข้า |
| Active | กำลังนับเวลา | sla_status = active → timer กำลังนับ ยังไม่มีใครตอบ ยังไม่ถึง due soon threshold |
| Due Soon | ใกล้ถึง deadline | sla_status = due_soon → เหลือเวลาน้อยกว่าหรือเท่ากับ due_soon_threshold |
| Overdue / SLA Breached | เกิน deadline | Overdue = label ใน UI / SLA Breached = system term — เกิดขึ้นเมื่อ sla_due_at <= NOW() และยังไม่มีใครตอบ |
| SLA Met | ตอบทันก่อน deadline | sla_status = met → agent ส่ง first reply ก่อน sla_due_at — บันทึก sla_met_at ด้วย |
| Disabled | SLA ปิดอยู่ | SLA ไม่ได้เปิดสำหรับ channel นั้น หรือ conversation ไม่ถูก track |

---

## SLA Status Machine

**Flow:**
```
Message เข้า → [active] → เหลือน้อยกว่า threshold → [due_soon] → deadline ผ่าน → [breached/overdue]
หรือ:
Message เข้า → [active] หรือ [due_soon] → agent reply → [met]
```

| Status | เงื่อนไข | สีที่แสดง |
|--------|----------|----------|
| `disabled` | SLA ปิดอยู่ หรือ outbound-first conversation | ไม่แสดง timer |
| `active` | มี first inbound + SLA enabled + เหลือเวลา > due_soon_threshold | เขียว |
| `due_soon` | เหลือเวลา <= due_soon_threshold นาที | เหลือง/amber |
| `breached` | sla_due_at <= NOW() และยังไม่มีใครตอบ → แสดง "Overdue +Xm" | แดง |
| `met` | agent ส่ง first outbound reply ก่อน sla_due_at | ไม่แสดง timer |

---

## Business Hours Aware

**Simple BH-aware (v1):**
- Message เข้าในช่วง Business Hours → นับตามปกติ
- Message เข้านอก BH → sla_due_at เริ่มนับจากตอนที่ BH เปิดครั้งถัดไป

| | Simple (v1) | Full (R2) |
|-|-------------|-----------|
| Logic | message นอก BH → deadline เลื่อนไปเริ่มตอน BH เปิด | timer หยุดนับทุกช่วงนอก BH รวม break กลางวัน |
| Edge cases | น้อย | มาก → break กลางวัน, ข้ามหลายวัน, วันหยุด |
| Platform ตัวอย่าง | Chatwoot | Freshdesk Enterprise |
| Pain point | แก้ "message เข้าตี 3 breach ตอนเช้า" ได้ครบ | Overkill สำหรับ MVP |

**3 กรณีหลักที่ Simple Logic handle:**

| กรณี | ตัวอย่าง | sla_due_at คือ |
|------|----------|----------------|
| Message เข้าระหว่าง BH | BH = 09-18, message เข้า 10:00, target = 1h | 10:00 + 1h = 11:00 (วันเดียวกัน) |
| Message เข้านอก BH (กลางคืน) | BH = 09-18, message เข้า 23:00, target = 1h | 09:00 วันถัดไป + 1h = 10:00 วันถัดไป |
| Message เข้านอก BH (หลัง BH ปิด) | BH = 09-18, message เข้า 19:00, target = 1h | 09:00 วันถัดไป + 1h = 10:00 วันถัดไป |

> ⚠️ ถ้า BH toggle ปิดอยู่ → ใช้ 24/7 เหมือนเดิม (backward compatible)

---

## Platform Messaging Window

| Channel | Hard Limit | ผลถ้าไม่ตอบ | แนะนำ SLA Target |
|---------|-----------|------------|-----------------|
| Facebook | 24h window | เกิน 24h: ส่ง promotional ไม่ได้ / เกิน 7 วัน: ส่งได้แค่ Message Tags | 1 ชั่วโมง — ถ้าตั้ง > 24h จะมี warning ใน UI |
| Instagram | 24h window | เกิน 24h: human agent เท่านั้น / เกิน 7 วัน: ส่งไม่ได้เลย | 1 ชั่วโมง — strict กว่า Facebook เพราะหลัง 7 วันปิดสนิท |
| LINE | ไม่มี | ส่งได้ตลอด (ยกเว้น user block) — มีแค่ monthly message limit | 1 ชั่วโมง — business expectation ทั่วไป |
| Shopee | ไม่มี messaging window | กระทบ seller score / chat response rate ต่ำ | 12 ชั่วโมง — marketplace ลูกค้ารอได้นานกว่า |
| Lazada | ไม่มี messaging window | กระทบ seller rating | 12 ชั่วโมง — best practice marketplace |
| TikTok Shop | ไม่มี messaging window | กระทบ Shop Performance Score / After-Sales Handling Time metric | 12 ชั่วโมง — TikTok วัด after-sales response ทุกวัน |

> ⚠️ Default values เหล่านี้คือ recommended guideline ไม่ใช่ platform mandate โดยตรง
