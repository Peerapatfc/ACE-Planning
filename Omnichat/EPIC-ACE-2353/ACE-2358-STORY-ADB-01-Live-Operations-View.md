# STORY-ADB-01: Live Operations View
**ClickUp:** ACE-2358 | **Epic:** ACE-2353 | **Status:** Backlog

---

## User Story

**As a** Admin / Supervisor,
**I want to** ดู conversation ที่กำลังดำเนินอยู่ตอนนี้ได้ทันที - Active, Waiting, Queue per channel, Agent workload,
**so that** Supervisor ที่คุมกะปัจจุบันมองเห็นปัญหาทันทีและตัดสินใจ assign / reassign ได้ใน 1 จอ.

---

## Detail / Description

- หน้า Live แสดงข้อมูล real-time ของ conversation และ agent ณ ปัจจุบัน อัปเดตอัตโนมัติ
- แยกชัดเจนระหว่าง **Active** (มี agent ดูแล) และ **Waiting** (ยังไม่มี agent รับ) — สองตัวเลขนี้นิยามไม่ทับกัน
- Queue Now แยก per channel พร้อมเวลารอนานสุด — supervisor เห็นได้ทันทีว่า channel ไหนกำลังบวม
- Agent Workload card แสดงจำนวนงานที่ assign ให้แต่ละ agent ตอนนี้ + จำนวนที่ดูแลวันนี้
- Drill-in: คลิก Active หรือ Waiting → drawer แสดง list conversation จริง พร้อมปุ่มเปิด conversation / Assign agent
- Refresh interval: 30 วินาที (polling) ถ้ามี WebSocket ก็ควรใช้

---

## Scope of this Story

- 3 Live KPIs: Active, Waiting, Agents Working (ตาม schedule shift)
- Volume Today chart: incoming vs resolved per ชั่วโมง (24 ชั่วโมงล่าสุด)
- Queue Now: จำนวนรอ + เวลารอนานสุด per channel (LINE, Facebook, IG, Shopee, Lazada, TikTok)
- Agent Workload: card per agent แสดง avatar, status, queue count, handled today
- Drill-in drawer: คลิก Active/Waiting card → list conversation พร้อมข้อมูล (id, ลูกค้า, channel, รอ/อายุ, agent)
- Refresh ทุก 30 วินาที พร้อม LIVE badge
- ถ้า queue ใด channel > 5 → แสดง warning หรือสีที่แตกต่าง

**Out of scope:**
- Supervisor whisper / takeover conversation (v2)
- Overloaded badge (ยังไม่มีหน้า config threshold)

---

## Metrics & Definitions

| Metric | Definition / Formula | Attribution / Notes |
|--------|---------------------|---------------------|
| Active | COUNT(conversation WHERE assigned_to IS NOT NULL AND status IN ('open', 'pending', 'in_progress')) | ณ วินาทีที่เรียก, refresh ทุก 30s, ไม่นับ resolved/closed |
| Waiting | COUNT(conversation WHERE assigned_to IS NULL AND status = 'open') | นิยามไม่ทับกับ Active, ตัวเลขสูง = ลูกค้ารอนาน |
| Agents Working | COUNT(agent WHERE schedule_status = 'working' ณ ตอนนี้) | ใช้ schedule ไม่ใช่ online tracking (ยังไม่มี) |
| Volume Today | GROUP BY hour(created_at), แยกนับ incoming และ resolved | incoming = conversation ใหม่ที่เปิด, resolved = ปิดในชั่วโมงนั้น |
| Queue per channel | COUNT(assigned_to IS NULL AND status='open') GROUP BY channel, MAX(NOW - created_at) | เวลารอนานสุด ไม่ใช่เฉลี่ย, สะท้อนเคสที่แย่ที่สุด |
| Agent Workload (queue) | COUNT(WHERE assigned_to = agent_id AND status='open') | นับเฉพาะ active ที่ assign คนนี้อยู่ตอนนี้ |
| Agent Handled Today | COUNT(DISTINCT conversation_id WHERE assigned_to ever included agent_id AND date = today) | เคยมีส่วนในการดูแลวันนี้ (touched today) |

---

## Acceptance Criteria

### 1. Active กับ Waiting นิยามไม่ทับกัน
- **Scenario 1:** มี conversation 84 อันยังเปิดอยู่, 70 มี agent assign และ 14 ยังไม่มี → Active แสดง 70, Waiting แสดง 14, รวมกันได้ 84
- **Scenario 2:** Agent A ถูก unassign ออกจาก conversation #100 → #100 ย้ายจาก Active count ไปเพิ่ม Waiting count อัตโนมัติ

### 2. Queue per channel + alert
- **Scenario 1:** Shopee มี waiting 7 อัน รอนานสุด 4:35 → แสดง Shopee: 7, wait 4:35 พร้อมไอคอนสีส้ม (เพราะ > 5)
- **Scenario 2:** ทุก channel waiting <= 5 → ไม่แสดง alert banner
- **Scenario 3:** channel ใด waiting > 5 → แสดง alert: 'Shopee queue สูง - assign เพิ่ม'

### 3. Drill-in drawer
- **Scenario 1:** Admin คลิก card Active → drawer เปิด แสดง list conversation ทั้ง 70 อัน พร้อม id, customer, channel, agent ที่ถืออยู่
- **Scenario 2:** Admin คลิก card Waiting → drawer เปิด แสดง list 14 อัน พร้อม id, customer, channel, เวลารอ
- **Scenario 3:** Admin คลิกปุ่ม 'Assign' บน row ใน drawer → เปิด assign modal

### 4. Refresh interval
- **Scenario 1:** เปิดหน้า Live ทิ้งไว้ → ผ่านไป 30 วินาที → ข้อมูลทุก KPI และ chart อัปเดตอัตโนมัติ, LIVE badge ยังกะพริบ
- **Scenario 2:** เปิดหน้า Live แล้วเปลี่ยน tab ไป Analytics → หยุด polling เพื่อประหยัด resource, กลับมา Live ค่อย resume

### 5. Permission - Agent ไม่เห็น Live tab
- User role = Agent เปิด URL ของ Live tab โดยตรง → redirect ไปหน้า Agents tab, Live tab ไม่แสดงใน sidebar

### 6. Empty state - ไม่มี conversation เลย
- **Scenario 1:** เปิด Workspace ใหม่ ยังไม่มี conversation → แสดง Active=0, Waiting=0, Agents Working=0, Volume chart แสดง empty state
- **Scenario 2:** คลิก Active card ที่เป็น 0 → drawer ไม่เปิด หรือ เปิดแล้วแสดง 'ไม่มี conversation' ไม่ error

### 7. Polling fail / network error
- **Scenario 1:** Polling request fail → แสดง badge 'connection lost' สีส้มแทน LIVE, retry ทุก 30 วินาที
- **Scenario 2:** Network กลับมา → badge กลับเป็น LIVE, data update ทันที

### 8. Drawer refresh ขณะเปิดอยู่
- **Scenario 1:** Admin เปิด drawer Waiting อยู่ มี 14 รายการ → polling 30s รอบใหม่ + มี conversation ใหม่เข้ามา → drawer update เป็น 15 รายการ, scroll position คงอยู่
- **Scenario 2:** Conversation ใน drawer ถูก assign ขณะ drawer เปิด → polling รอบถัดไป → รายการนั้นหายจาก Waiting drawer, ไม่ flash หรือ jump

### 9. Agents Working = 0
- เวลาตี 3 ไม่มี agent ใด schedule = working → Agents Working แสดง 0, Agent Workload section แสดง empty state

### 10. หน้าเปิดทิ้งไว้นานเกิน
- Admin เปิด Live tab ทิ้งไว้ > 1 ชั่วโมงโดยไม่ interact → แสดง prompt 'หน้าเปิดมานานแล้ว - กดเพื่อ reload เพื่อความถูกต้อง'

---

## UI/UX Notes

- KPI cards ใหญ่ 3 ใบเรียงแถวบน: Active, Waiting, Agents Working
- Active และ Waiting cards คลิกได้ (cursor pointer + hover state) Agents Working ไม่คลิก
- LIVE badge สีเขียวกะพริบมุมขวาบนของแต่ละ chart/section
- Volume Today: area chart 2 เส้น (Incoming coral, Resolved teal) 24 ชั่วโมงล่าสุด
- Queue Now: list per channel + dot สีเขียว/ส้มตาม threshold + ตัวเลข queue ตัวใหญ่ขวาสุด
- Agent Workload: 5 cards, avatar + status dot + queue/handled ตัวเลข
- Drill-in drawer: เลื่อนเข้ามาจากขวา + backdrop + close button
- Tooltip glossary บน Active, Waiting (info icon)

---

## QA / Test Considerations

**Primary flows:**
1. Supervisor เปิด Live tab → ดูภาพรวม → เห็น Shopee queue สูง → คลิก Waiting card → drawer แสดง list → กด Assign
2. Supervisor monitor 30 วินาที → ข้อมูลอัปเดตอัตโนมัติ

**Edge Cases:**
- ไม่มี conversation เลย (off-peak ตี 3) — แสดง 0 ทุก KPI ไม่ error
- Agent ทั้งหมด offline — Agents Working แสดง 0 + empty state
- Polling fail — แสดง 'connection lost' badge + retry ทุก 30s
- Conversation reassign ระหว่าง drawer เปิด — refresh drawer พร้อม 'data updated'
- เปิดหน้าทิ้งไว้นาน (> 1 ชั่วโมง) — prompt 'reload เพื่อความถูกต้อง'

**Business-Critical "Must Not Break":**
- Active + Waiting ต้องไม่ทับกัน — ตัวเลขรวมต้องเท่ากับจำนวน open ทั้งหมด
- Refresh ต้องไม่ทำให้ scroll position หาย หรือ drawer ปิด
- ถ้า drawer เปิดอยู่ ข้อมูลใน drawer ต้องไม่ stale
- Agent role ห้ามเข้า Live tab ได้ ไม่ว่าทาง UI หรือ URL ตรง

**Test Types:**
- Unit: query Active/Waiting แยกกันถูกต้อง (assigned_to IS/NOT NULL)
- Unit: queue count + max wait per channel
- Integration: polling 30s + visibility change pause/resume
- E2E: assignment เปลี่ยน → dashboard reflect ภายใน 30s
- E2E: drill-in drawer → assign action → handover
- Security: Agent role ห้ามเข้า Live tab
- Performance: polling ไม่ทำให้ memory leak (เปิดทิ้งไว้ 1 ชั่วโมง)
