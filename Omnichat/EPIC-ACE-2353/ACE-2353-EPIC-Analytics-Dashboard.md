# EPIC-A5.1: Analytics Dashboard
**ClickUp:** ACE-2353 | **Status:** Backlog | **Product:** Omni

---

## 1.1 Objective

ให้ Admin และ Supervisor monitor performance ของทีม support และ automation feature ได้ใน 1 จอ เห็นปัญหาทันที (Live) และวิเคราะห์เทรนด์ย้อนหลังได้ (Analytics)

- วัดเฉพาะที่วัดได้จริง ไม่ใส่ metric ที่ระบบยังไม่รองรับ
- แยก Live vs Analytics ชัดเจน use case ต่างกัน (decision now vs trend analysis)
- Attribution ที่แม่นยำ ใช้ assignment_history แยก first responder, last assignee, time-held
- Tooltip glossary บนทุกศัพท์เทคนิค ช่วยให้ user ใหม่หรือ stakeholder เข้าใจได้เอง

---

## 1.2 Dashboard Structure

Dashboard มี 5 tabs แบ่งตาม use case:

| Tab | Use Case | Refresh / Data |
|-----|----------|----------------|
| Live | Supervisor คุมกะ เห็นปัญหาทันที | Near real-time (polling 30s), ข้อมูลปัจจุบัน |
| Analytics | Manager วิเคราะห์เทรนด์ | Historical, refresh on period change |
| Agents | ดู ranking + per-agent performance | Historical, period filter |
| Channels | เปรียบเทียบ channel + backlog | Historical + ปัจจุบัน (backlog) |
| Automation | พิสูจน์ ROI ของ rule | Historical, period filter |

---

## 1.3 Measurement Axes

Dashboard วัดผลใน 4 แกนหลัก:
- **Volume** - จำนวน conversation, message, tag, rule execution (เห็น throughput)
- **Speed** - FRT (response time), AHT (handle time) (เห็น responsiveness)
- **Quality** - Resolution Rate (เห็น effectiveness)
- **Distribution** - SLA bucket, Peak heatmap, Backlog age, Channel share (เห็น pattern)

และ 2 แกนเสริมที่ตอบโจทย์ Rule Automation:
- **Attribution** - bot vs human, rule vs manual (sender_type, tagged_by_type)
- **Efficiency** - FRT Reduction, Rule Success% (พิสูจน์ benefit ของ automation)

---

## 1.4 Attribution Rules

เพราะ conversation เปลี่ยนมือได้ (reassign) ต้องมีข้อตกลง attribution ให้ชัดก่อน implement:

| Metric | Attribute ให้ | เหตุผล / Logic |
|--------|--------------|----------------|
| Total Conversations | ไม่มี attribution | COUNT(DISTINCT conversation_id) reassign ไม่ double-count |
| Resolution | Last assignee (คนที่ปิด) | คนที่กดปิดคือคนที่รับผิดชอบผลสุดท้าย |
| Handled (per agent) | Last assignee | กัน double-count ระหว่าง team total กับ per-agent sum |
| FRT | First responder (คนตอบแรก) | ผูก first response, lock ไม่เปลี่ยนตาม reassign, ไม่นับ auto-reply |
| AHT (per agent) | แบ่งเวลาตาม assignment_history | sum(unassigned_at - assigned_at) per agent / count |
| AHT (conversation-level) | ไม่มี attribution | AVG(resolved_at - first_human_response_at) เวลาทั้ง conversation |
| Active / Waiting | Current assignee | ดูสถานะ ณ ปัจจุบัน - assigned_to ตอนนี้ |
| Reply Attribution | sender_type | human / rule / system แยกตาม source ของ message |
| Tag Attribution | tagged_by_type | human / rule แยกตาม source ของ tag event |

---

## 1.5 Permission Matrix

| การกระทำ | Admin | Supervisor | Agent |
|---------|-------|-----------|-------|
| ดู Live tab (Active, Waiting, Agent Workload) | Yes | Yes | No |
| ดู Analytics tab (metrics ทั้งทีม) | Yes | Yes | No |
| ดู Agents tab (ranking ทั้งทีม) | Yes | Yes | ดูเฉพาะของตัวเอง |
| ดู Channels tab | Yes | Yes | No |
| ดู Automation tab | Yes | Yes | No |
| Drill-in (เปิด conversation จาก dashboard) | Yes | Yes | No |
| เปลี่ยน period filter (Today / 7d / 30d) | Yes | Yes | ดูได้เฉพาะ Today (ของตัวเอง) |

**หมายเหตุ:**
- Agent role เห็นเฉพาะ Agents tab + ดูเฉพาะ row ของตัวเอง
- ทั้ง UI และ API ต้อง enforce permission, Agent call API agent อื่นได้รับ 403
- Period filter สำหรับ Agent ล็อคที่ Today (ไม่ให้ย้อน 30 วันดูตัวเอง)

---

## 1.6 Cross-cutting UX Requirements

### 1.6.1 Tooltip / Glossary System
ทุกศัพท์เทคนิคต้องมี tooltip อธิบาย:
- **Style A** - dotted underline บนหัวคอลัมน์ในตาราง (เนียน ไม่รก)
- **Style B** - info icon บน KPI card สำคัญ (สังเกตเห็นได้ชัด) — แนะนำ

เนื้อหา tooltip 3 ชั้น: ชื่อเต็ม + อธิบาย + เกณฑ์/หมายเหตุ

ตัวอย่าง:
- **FRT** → 'First Response Time, เวลาตั้งแต่ลูกค้าทักจนได้รับการตอบครั้งแรกจากเจ้าหน้าที่, ยิ่งน้อยยิ่งดี, ไม่นับ auto-reply'
- **AHT** → 'Average Handle Time, เวลาเฉลี่ยที่เจ้าหน้าที่ใช้ดูแลหนึ่งการสนทนา ตั้งแต่เริ่มจนปิด, สะท้อนภาระงาน'

### 1.6.2 Period Filter
- 3 options: **Today / 7 days / 30 days** — มุมขวาบนของ tab (ยกเว้น Live)
- เปลี่ยน period → apply ทุก section ใน tab พร้อมกัน (ไม่ partial update)
- Loading skeleton ตอน fetch ใหม่
- Live tab ไม่มี period filter เพราะเป็น current state

### 1.6.3 Drill-in Drawer
- คลิก KPI card (เช่น Active, Waiting) → drawer เลื่อนเข้ามาจากขวา
- List conversation จริง พร้อมข้อมูล: conversation_id, customer, channel, อายุ/wait time, agent
- Actions per row: 'เปิด conversation' + 'Assign' (assign modal)
- Drawer refresh ตามรอบ polling ถ้าเปิดทิ้งไว้

---

## 1.7 Business Edge Cases

### 1.7.1 Reassign & Attribution

| Scenario / เคส | ปัญหา / Risk | Business Decision / Solution |
|---------------|-------------|------------------------------|
| A ดูแล → B รับต่อ → B ปิด | นับ Resolved ให้ใคร? double-count ทั้งสองคนได้ไหม | Resolved attribute ให้ last assignee (B) เท่านั้น, team total = 1 ไม่ใช่ 2 |
| A ตอบครั้งแรก → reassign ไป B → B ตอบช้า | FRT ของ conversation ควรเป็นของใคร | FRT ผูก first responder (A) lock ไม่เปลี่ยน |
| A ถือ 30m, B ถือ 15m รวม 45m | ใครได้ AHT 45m? โยนทั้งก้อนให้ B? | แบ่งเวลาตามจริง: A = 30m, B = 15m, ใช้ assignment_history |
| Conversation ปิด 2 รอบ (reopen แล้วปิดอีก) | Resolution count นับ 2 ไหม | COUNT(DISTINCT conversation_id) นับ 1 ครั้งเสมอ |

### 1.7.2 Auto-reply & FRT

| Scenario / เคส | ปัญหา / Risk | Business Decision / Solution |
|---------------|-------------|------------------------------|
| Bot ตอบ 30 วินาทีก่อน human | FRT คำนวณจาก bot หรือ human | ใช้ human FRT เสมอ, bot reply ไม่นับ, first_human_response_at แยกจาก first_response_at |
| หลาย rule match พร้อมกัน | ส่ง auto-reply กี่ครั้ง | Only-first-wins, เกี่ยวกับ rule logic ไม่กระทบ dashboard |
| Auto-reply นับเข้า agent KPI ผิด | Agent FRT จะ inflate | sender_type = 'rule' ใน message, exclude จาก agent FRT calculation |

### 1.7.3 Time Boundary & Period

| Scenario / เคส | ปัญหา / Risk | Business Decision / Solution |
|---------------|-------------|------------------------------|
| Conversation เริ่มเมื่อวาน 23:50 ปิดวันนี้ 00:15 | นับเข้า period ไหน | Volume นับเข้าวันที่ created, Resolution นับเข้าวันที่ resolved |
| Period = Today ตอน 6 โมง | data น้อยมาก trend ไม่มีความหมาย | แสดง data ที่มี + note 'ข้อมูลยังไม่พอ' บน trend chart |
| Period เปลี่ยนตอน chart loading | ข้อมูลผสม period เก่ากับใหม่ | Loading skeleton + abort request เก่า, แสดงเฉพาะ period ใหม่ |

### 1.7.4 Permission & Privacy

| Scenario / เคส | ปัญหา / Risk | Business Decision / Solution |
|---------------|-------------|------------------------------|
| Agent เปิด URL ของ agent อื่น | Agent อาจดู KPI เพื่อนได้ | UI hide + API enforce 403, ตรวจ permission ทั้ง UI และ API |
| Supervisor ดู data ของ Admin | ข้อมูล sensitive เช่นเงินเดือน | Dashboard ไม่มี data sensitive, ทั้ง Admin/Supervisor ดูได้เหมือนกัน |
| Agent role เปลี่ยน period เป็น 30 วัน | ใช้ดู performance ตัวเองย้อนหลัง | อนุญาตเฉพาะ Today สำหรับ Agent, 7/30 วันสำหรับ Admin/Supervisor |

### 1.7.5 Data Freshness

| Scenario / เคส | ปัญหา / Risk | Business Decision / Solution |
|---------------|-------------|------------------------------|
| Live tab เปิดทิ้งไว้นาน | data stale ลูกค้ารอแต่ supervisor ไม่รู้ | Polling 30s + LIVE badge กะพริบ, ถ้า idle เกิน 1 ชั่วโมง prompt reload |
| Network ขาดช่วง refresh | แสดง data เก่าแต่ user คิดว่าใหม่ | แสดง 'connection lost' badge + retry, ไม่ใช่ silent fail |
| Conversation เปลี่ยน status ระหว่าง drawer เปิด | data ใน drawer ไม่ตรง | Drawer refresh ตามรอบ polling พร้อม subtle indicator 'data updated' |

---

## User Stories

| Story | Title | ClickUp |
|-------|-------|---------|
| ADB-01 | Live Operations View | ACE-2358 |
| ADB-02 | Analytics View | ACE-2354 |
| ADB-03 | Agents Performance View | ACE-2355 |
| ADB-04 | Channels Performance View | ACE-2356 |
| ADB-05 | Automation Performance View | ACE-2357 |
