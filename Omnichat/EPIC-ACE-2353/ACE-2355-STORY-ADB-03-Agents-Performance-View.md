# STORY-ADB-03: Agents Performance View
**ClickUp:** ACE-2355 | **Epic:** ACE-2353 | **Status:** Backlog

---

## User Story

**As a** Admin / Supervisor / Agent,
**I want to** ดู performance ของ agent ทั้งทีมและ ranking - Resolved, FRT, AHT, Status,
**so that** Supervisor หา top performer ที่ควรชม และคนที่ต้อง coaching ส่วน Agent เห็นของตัวเอง.

---

## Detail / Description

- หน้า Agents แสดง 4 Team KPIs + ตาราง performance per agent ที่ sort ได้
- ใช้ assignment_history attribution: Resolved นับให้คนที่ปิด, FRT ของคนที่ตอบแรก, AHT แบ่งตามเวลาถือจริง
- **Permission พิเศษ:** Agent role เห็นได้ แต่เฉพาะ row ของตัวเอง, ไม่เห็นชื่อหรือตัวเลขของเพื่อน
- Sort ตาราง: Resolved (default), FRT, AHT
- Status: online / offline ตาม schedule shift

---

## Scope of this Story

- 4 Team KPIs: Working Now, Total Resolved (วันนี้), Avg FRT, Avg AHT
- Performance Table per agent: Agent (avatar + ชื่อ), Resolved, FRT, AHT, Status
- Sort buttons: Resolved (default), FRT, AHT
- Color coding ตามค่า: FRT/AHT เขียว/ส้ม/แดง ตาม threshold
- Status dot: online (เขียว), offline (เทา)
- Permission: Agent role เห็นเฉพาะ row ของตัวเอง + KPI ที่อิงตัวเอง

**Out of scope:**
- Agent profile detail page (v2)
- Coaching notes (v2)
- Per-agent CSAT (v2)
- Per-agent Reopen rate (v2)

---

## Metrics & Definitions

| Metric | Definition / Formula | Attribution / Notes |
|--------|---------------------|---------------------|
| Working Now | COUNT(agent WHERE schedule = working AND status != offline) | ตาม schedule + ไม่ใช่ offline |
| Total Resolved (team) | COUNT(DISTINCT conversation_id WHERE resolved_at IN period) | นับ unique conversation ที่ปิดในช่วง |
| Avg FRT (team) | AVG(first_human_response_at - created_at) ข้ามทุก agent | ไม่นับ auto-reply |
| Avg AHT (team) | AVG(time_held per conversation) ข้ามทุก agent | เฉลี่ยจาก assignment_history |
| Agent Resolved | COUNT(DISTINCT conversation_id WHERE last_assignee = agent_id AND resolved_at IN period) | นับให้คนที่ปิด (last assignee) เท่านั้น |
| Agent FRT | AVG(FRT WHERE first_responder = agent_id) | ผูก first response, ไม่เปลี่ยนตาม reassign |
| Agent AHT | sum(unassigned_at - assigned_at) per agent / COUNT(conversation ที่ดูแล) | แบ่งเวลาตามจริง — ถ้า A ถือ 30m, B ถือ 15m → A ได้ 30m, B ได้ 15m |
| Agent Status | online / offline จาก schedule + last activity | schedule-based เพราะยังไม่มี real-time online tracking |

---

## Acceptance Criteria

### 1. Resolved attribute ให้ last assignee (คนที่ปิด)
- Conversation #100: A ดูแล → reassign ไป B → B ปิด → นับเข้า B (last assignee), ไม่นับเข้า A, team total = 1 (ไม่ double)

### 2. FRT ผูก first responder ไม่ตาม reassign
- A ตอบครั้งแรก FRT = 1:30 แล้ว reassign ไป B → #100 ไม่นับเข้า FRT ของ B, ของ A คือ 1:30

### 3. AHT แบ่งเวลาจริงตาม assignment_history
- Conversation #100 ใช้เวลา 45 นาที — A ถือ 30 นาที, B ถือ 15 นาที → A ได้ 30m เข้า total, B ได้ 15m (ไม่ใช่ B ได้ 45m ทั้งก้อน)

### 4. Permission - Agent เห็นเฉพาะของตัวเอง
- **Scenario 1:** User role = Agent (Nat) เปิด Agents tab → แสดงเฉพาะ row ของ Nat + KPIs ที่อิง Nat, ไม่เห็นชื่อหรือตัวเลขของเพื่อน
- **Scenario 2:** Agent (Nat) call API /agents/list → return เฉพาะ Nat, 403 ถ้าพยายาม query agent อื่น

### 5. Sort ทำงานถูกต้อง
- **Scenario 1:** กด sort = FRT → agent เรียงจาก FRT น้อยไปมาก (เร็วที่สุดก่อน)
- **Scenario 2:** กด sort = Resolved → เรียงจากมากไปน้อย (top performer ก่อน)

### 6. Color coding
- **Scenario 1:** Agent FRT = 1:24 → แสดงสีเขียว (เร็วกว่า 2:30)
- **Scenario 2:** Agent FRT = 3:15 → แสดงสีแดง (ช้ากว่า 3:00)

### 7. Status
- **Scenario 1:** Agent มี schedule = working, last activity 30 วินาทีก่อน → status = online (เขียว)
- **Scenario 2:** Agent schedule = working แต่ last activity > 10 นาทีก่อน → status = busy (ส้ม)
- **Scenario 3:** Agent schedule = off → status = offline (เทา)

### 8. Consistency - sum per agent = team total
- **Scenario 1:** Period = 7 days, Team Total Resolved = 614 → sum Agent Resolved ของทุก agent ต้องเท่ากับ 614 พอดี
- **Scenario 2:** Period = 7 days, Team Avg FRT = 2.1m → weighted avg ของ Agent FRT (ตาม volume) ต้องตรงกับ 2.1m

### 9. Agent ใหม่ยังไม่มี history
- **Scenario 1:** Agent (Pong) เพิ่งเข้าทำงานวันนี้ ยังไม่มี conversation → Resolved = 0, FRT = ' - ', AHT = ' - ', Status ตาม schedule, ไม่ error
- **Scenario 2:** Period = 30 days แต่ Pong เพิ่งเข้า 5 วัน → แสดง data 5 วันที่มี, footer note 'agent ใหม่ - data 5 วัน'

### 10. Agent ถูก terminated
- **Scenario 1:** Agent (Vino) ถูก terminate วันที่ 15, Period รวมก่อน 15 → Vino ไม่แสดงใน table (filter active agents), แต่ data historical ยังอยู่ใน team totals
- **Scenario 2:** Period สิ้นสุดก่อน 15 → Vino ยังแสดงปกติ

### 11. Permission - UI hide + API enforce
- **Scenario 1:** Agent (Nat) เปิด direct URL /agents/profile/another_id → 403 + redirect ไปหน้า Agents tab ของตัวเอง
- **Scenario 2:** Agent call API GET /agents/team/performance → 403 Forbidden
- **Scenario 3:** Agent (Nat) เปลี่ยน period เป็น 30 days ผ่าน URL ?period=30d → server force ลงเป็น Today

---

## UI/UX Notes

- 4 KPI cards บน — หน้านี้เน้นตาราง
- Sort pills (Resolved / FRT / AHT) เป็น chip ที่ active
- Avatar circle + ตัวอักษรชื่อ
- Status dot มี hover tooltip 'online, last active 2 min ago'
- Tooltip info icon บน FRT, AHT, Resolved column headers
- Agent role: หน้านี้ไม่มี Sort button (เพราะมี row เดียว) + ซ่อน KPI ทีม

---

## QA / Test Considerations

**Primary flows:**
1. Supervisor เปิด Agents → sort by Resolved → เห็น top → sort by FRT ascending → คนช้าสุด → schedule 1:1 coaching
2. Agent (Nat) เปิด Agents → เห็นแถวตัวเอง + KPI ของตัวเอง

**Edge Cases:**
- Agent ที่ไม่มี conversation ในช่วง period — แสดง row แต่ค่า 0 / N/A
- Agent ใหม่เพิ่งเข้า — ไม่มี history → แสดง N/A สำหรับ FRT/AHT
- Agent ถูกลบ (terminated) — ไม่แสดงใน table แต่ data ใน historical ยังอยู่
- Agent role เปิด direct URL ของ agent อื่น (/agents/123) — 403 + redirect to own
- Period = 30 days แต่ Agent เพิ่งเข้าทำงาน 5 วัน — แสดงเฉพาะ data 5 วัน + note

**Business-Critical "Must Not Break":**
- Resolved ของแต่ละ agent รวมกัน = Team Total Resolved (ไม่ over/under)
- FRT lock first responder — ห้ามเปลี่ยนตาม reassign
- AHT แบ่งเวลาจริง — ผลรวมเวลาทุก agent = เวลา conversation จริง
- Agent role ห้ามเห็นข้อมูล agent อื่นไม่ว่ากรณีใด (UI + API)

**Test Types:**
- Unit: Resolved attribution = last assignee only
- Unit: FRT attribution = first responder, locked
- Unit: AHT time-split per agent via assignment_history
- Unit: Sort logic (asc/desc per column)
- Unit: Status calculation (schedule + activity)
- Security: Agent ดู agent อื่นไม่ได้ (UI hide + API 403)
- E2E: reassign → Resolved ย้ายไปคนใหม่, FRT ของคนเก่า
- Integration: time-split AHT ตรงกับเวลาจริงใน assignment_history
