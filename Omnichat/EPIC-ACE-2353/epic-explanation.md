# EPIC ACE-2353: Analytics Dashboard — คำอธิบายแบบเข้าใจง่าย

## สรุปภาพรวม

Epic นี้คือการสร้าง "Analytics Dashboard" ที่รวมข้อมูล performance ของทีม support ทั้งหมดไว้ใน 1 หน้า ให้ Admin และ Supervisor มองเห็นภาพรวมได้ทันที ทั้งแบบ real-time (Live) และแบบวิเคราะห์ย้อนหลัง (Analytics)

เป้าหมายหลักคือ **ให้ supervisor ตัดสินใจได้เร็วขึ้นโดยไม่ต้องถามทีม** — เห็นทันทีว่า queue บวมที่ channel ไหน, agent คนไหน FRT ช้า, rule automation ช่วยลด workload ได้จริงแค่ไหน

**เปรียบเทียบง่าย ๆ:**
เหมือน control room ของสายการบิน — ไม่ใช่ที่นั่งขับเครื่องบิน แต่เป็นที่ที่ supervisor เห็นทุก flight บนจอเดียว รู้ว่าเครื่องไหนช้า, gate ไหนติดขัด, และตัดสินใจ re-route ได้ทันที

---

## 1. แนวคิดหลัก (Core Concepts)

### 1.1 Dashboard 5 Tabs แบ่งตาม Use Case

Dashboard ไม่ใช่หน้าเดียวที่ยัดทุกอย่าง — แต่แบ่งเป็น 5 tabs ที่ตอบคำถามต่างกัน:

| Tab | คำถามที่ตอบ | ข้อมูลประเภทไหน |
|-----|------------|----------------|
| **Live** | "ตอนนี้ queue เป็นยังไง? ใครรอนาน?" | Near real-time, polling 30s |
| **Analytics** | "สัปดาห์นี้ FRT ดีขึ้นไหม? peak hour อยู่เมื่อไหร่?" | Historical, refresh ตอนเปลี่ยน period |
| **Agents** | "ใคร resolve เยอะสุด? ใคร FRT ช้าต้อง coaching?" | Historical, period filter |
| **Channels** | "Shopee queue บวมกว่า LINE ไหม? backlog ค้างนานแค่ไหน?" | Historical + current backlog |
| **Automation** | "Rule ที่ตั้งไว้ทำงานคุ้มไหม? FRT ลดได้กี่ %?" | Historical, period filter |

### 1.2 สองโหมดการวัด: Live vs Historical

**Live (Tab 1):** วัดสถานะ ณ ปัจจุบัน — "กำลังมี 84 conversation เปิดอยู่, 14 ยังไม่มี agent รับ"

**Historical (Tab 2-5):** วัดผลย้อนหลัง — "7 วันที่ผ่านมา FRT เฉลี่ย 2.4 นาที"

> ทั้งสองโหมดตอบโจทย์ต่างกัน: Live = decision now / Historical = trend analysis

### 1.3 Period Filter (3 ตัวเลือก)

Tab ที่เป็น Historical ทั้งหมดมี period filter มุมขวาบน:
- **Today** — ดูวันนี้
- **7 days** — ดู 7 วันย้อนหลัง
- **30 days** — ดู 30 วันย้อนหลัง

เปลี่ยน period → **ทุก metric ใน tab นั้นเปลี่ยนพร้อมกัน** ไม่มี partial update

### 1.4 Attribution Rules (ข้อตกลงว่าผลลัพธ์นับให้ใคร)

เพราะ conversation เปลี่ยนมือได้ (reassign) ต้องตกลงกันก่อนว่า "KPI ชิ้นนี้นับให้ใคร":

| Metric | นับให้ใคร | เหตุผล |
|--------|----------|--------|
| **Resolution** | Last assignee (คนที่กดปิด) | คนปิดคือคนรับผิดชอบผลสุดท้าย |
| **FRT** | First responder (คนตอบแรก) | Lock ทันทีที่ตอบแรก ไม่เปลี่ยนตาม reassign |
| **AHT per agent** | แบ่งตามเวลาที่ถือจริง | ใช้ assignment_history — A ถือ 30m ได้ 30m, B ถือ 15m ได้ 15m |
| **Total / Volume** | ไม่มี attribution | COUNT DISTINCT เสมอ reassign ไม่ทำให้ double-count |

**กฎเหล็ก:** FRT ต้องไม่นับ auto-reply ของ bot — ใช้ `first_human_response_at` แยกจาก `first_response_at`

### 1.5 Permission Model

Dashboard มี permission 3 ระดับ:

| สิ่งที่ทำ | Admin | Supervisor | Agent |
|---------|:-----:|:----------:|:-----:|
| Live tab | ✓ | ✓ | ✗ |
| Analytics tab | ✓ | ✓ | ✗ |
| Agents tab | ✓ | ✓ | เฉพาะ row ตัวเอง |
| Channels tab | ✓ | ✓ | ✗ |
| Automation tab | ✓ | ✓ | ✗ |
| Period filter | Today / 7d / 30d | Today / 7d / 30d | Today เท่านั้น |

> ทั้ง UI ซ่อนและ API enforce 403 — Agent ที่พยายาม query ข้อมูล agent อื่นได้รับ 403 เสมอ

---

## 2. ส่วนประกอบบนหน้าจอ (UI Components)

### 2.1 Live Tab

```
┌─────────────────────────────────────────────────────┐
│  🟢 LIVE  (กะพริบ)                                   │
│                                                     │
│  [Active: 70]   [Waiting: 14]   [Agents: 8]         │
│   คลิกได้→      คลิกได้→        ไม่คลิก             │
│                                                     │
│  Volume Today (area chart — incoming vs resolved)   │
│                                                     │
│  Queue Now per channel:                             │
│  LINE: 2  Facebook: 1  Shopee: 🟠 7 (wait 4:35)    │
│                                                     │
│  Agent Workload:                                    │
│  [Nat 🟢 queue:3 done:12] [Pong 🟠 queue:5 done:8]  │
└─────────────────────────────────────────────────────┘
```

**Drill-in Drawer:** คลิก Active หรือ Waiting → drawer เลื่อนจากขวา แสดง list conversation จริง พร้อมปุ่ม "เปิด conversation" และ "Assign"

**LIVE Badge:** กะพริบตราบใดที่ polling ปกติ → เปลี่ยนเป็น 🟠 "connection lost" เมื่อ network ขาด

### 2.2 Analytics Tab

```
┌────────────────────────────────────────────────────┐
│  [Total: 4,870]  [FRT: 2.4m]  [AHT: 8.2m]  [Res%: 94%]   Period: [30d ▾] │
│                                                                             │
│  [FRT bar: bot vs human]  [SLA Distribution]  [Weekly Trend]               │
│                                                                             │
│  [Peak Hours Heatmap - 7 วัน x 12 ช่วงเวลา]                                │
│                                                                             │
│  [Channel Breakdown]        [Top Auto-tags]                                 │
└────────────────────────────────────────────────────┘
```

### 2.3 Agents Tab

```
┌──────────────────────────────────────────────────────────┐
│  [Working: 8]  [Resolved today: 142]  [FRT: 2.1m]  [AHT: 7.8m]           │
│                                                                            │
│  Sort: [Resolved ●] [FRT] [AHT]                                           │
│                                                                            │
│  Avatar  Name      Resolved  FRT       AHT       Status                   │
│  🟢 Nat   120       1:24🟢    7:10🟢    🟢 online                          │
│  🟠 Pong   87       3:15🔴    9:30🟠    🟠 busy                            │
└──────────────────────────────────────────────────────────┘
```

### 2.4 Channels Tab

```
┌──────────────────────────────────────────────────────────┐
│  Channel    Volume      FRT      Resolution  Switch%     │
│  LINE       ████ 2,340  1:52🟢   96%🟢        5%🟢       │
│  Shopee     ██ 1,100    4:20🔴   88%🟠       18%🔴       │
│  Facebook   █ 890       2:10🟢   93%🟢        8%🟢       │
│  ...                                                     │
│                                                          │
│  Backlog Age:                                            │
│  [< 1h: 23]  [1-4h: 8]  [4-24h: 3]  [> 1 วัน: 5]      │
│  ⚠️ มี 5 conversations ค้างเกิน 1 วัน — ต้องการ escalation │
└──────────────────────────────────────────────────────────┘
```

### 2.5 Automation Tab

```
┌──────────────────────────────────────────────────────────┐
│  [Rules: 5/20]  [Auto-replied: 1,827]  [Auto-tagged: 1,419]  [FRT↓: 87%] │
│                                                                            │
│  Rule Performance:                                                         │
│  Auto-reply · Outside hours   Fired: 1,284  Handled: 1,201  ████ 94%🔵   │
│  Tag · ยกเลิก                  Fired: 543    Handled: 540   ████ 99%🟢   │
│  Auto-reply · Welcome          Fired: 312    Handled: 272   ███░ 87%🟠   │
│                                                                            │
│  [Reply Attribution: 63% human / 37% rule]  [Tag Attribution: 71% auto]  │
└──────────────────────────────────────────────────────────┘
```

### 2.6 Cross-cutting UX

**Tooltip System:** ทุก KPI ที่เป็นศัพท์เทคนิค (FRT, AHT, Switch%) มี ⓘ icon — hover แสดง ชื่อเต็ม + คำอธิบาย + เกณฑ์

**Loading Skeleton:** ตอนเปลี่ยน period — ไม่แสดง data เก่าระหว่าง fetch ใหม่ แต่แสดง skeleton แทน

---

## 3. ลำดับการทำงาน (User Flow)

### สถานการณ์ A: Supervisor เห็น Shopee queue บวม

Supervisor เปิด Live tab เวลา 14:00 เห็นว่า Shopee queue แสดง 🟠 7 (wait 4:35)

1. **คลิก Waiting card** → drawer เลื่อนเข้ามาจากขวา แสดง 14 conversation ที่รอ
2. **Filter ดู Shopee** → เห็น 7 รายการรอนาน เรียงตามเวลารอ
3. **คลิก Assign บนรายการที่รอนานสุด** → เปิด assign modal → เลือก agent ที่ว่าง
4. **Drawer refresh** ตาม polling รอบถัดไป → รายการนั้นย้ายไป Active

### สถานการณ์ B: Manager วิเคราะห์ performance รายสัปดาห์

1. **เปิด Analytics tab** เลือก period = 7 days
2. **ดู FRT bar chart** เห็นว่า bot FRT 0.3m แต่ human FRT 2.4m
3. **ดู Peak Heatmap** เห็น peak ชัดช่วง อังคาร-พฤหัส 10:00-12:00
4. **ตัดสินใจ** เพิ่ม shift coverage ช่วง peak → ลด FRT ตรงนั้น

### สถานการณ์ C: Supervisor หา agent ที่ต้อง coaching

1. **เปิด Agents tab** กด sort = FRT ascending
2. **เห็น Pong FRT = 3:15 สีแดง** (threshold > 3:00)
3. **ตรวจ AHT ของ Pong** = 9:30 ก็สูงด้วย → น่าจะมีปัญหาเรื่องกระบวนการดูแล
4. **Schedule coaching** กับ Pong โดยอ้างข้อมูลจาก dashboard

### สถานการณ์ D: Admin พิสูจน์ ROI ของ Rule Automation

1. **เปิด Automation tab** เลือก period = 30 days
2. **เห็น FRT Reduction = 87%** → auto-reply ลด response time จาก 2.4m เหลือ 0.3m สำหรับ bot
3. **ดู Rule Performance** → 'Auto-reply · Outside hours' success 94% ทำงานดี
4. **เห็น rule ที่ success < 90%** → คลิกไป Rule Management เพื่อ debug condition

---

## สรุปรายละเอียด (Scope)

| หมวดหมู่ | รายละเอียด |
|---------|-----------|
| Stories ที่พัฒนาใน Epic นี้ | 5 Stories (ADB-01 ถึง ADB-05) |
| Tabs | 5 tabs: Live, Analytics, Agents, Channels, Automation |
| Period filter options | Today / 7 days / 30 days (ยกเว้น Live tab) |
| Attribution model | Last assignee (Resolution), First responder (FRT), Time-split (AHT per agent) |
| FRT rule | ไม่นับ auto-reply — ใช้ first_human_response_at เสมอ |
| Refresh (Live) | Polling 30s + LIVE badge กะพริบ |
| Permission enforcement | UI hide + API 403 ทั้งคู่ |
| Agent role restriction | เห็นเฉพาะ Agents tab + row ตัวเอง + period = Today เท่านั้น |

---

## 4. คำอธิบายแต่ละ Story (Story Breakdown)

### STORY-ADB-01: Live Operations View — มองเห็นปัญหาทันที

**เป้าหมาย:** Supervisor ที่คุมกะเห็นสถานะ conversation และ agent ณ ปัจจุบันได้ใน 1 หน้า ตัดสินใจ assign/reassign ได้เลย

**สิ่งที่จะทำ:**
- **3 KPI cards:** Active (conversation ที่มี agent), Waiting (ยังไม่มี agent รับ), Agents Working (ตาม schedule)
- **Volume Today chart:** area chart incoming vs resolved รายชั่วโมง 24h
- **Queue Now per channel:** จำนวนรอ + เวลารอนานสุด + warning เมื่อ > 5
- **Agent Workload cards:** avatar, status dot, queue count, handled today
- **Drill-in drawer:** คลิก Active/Waiting → list conversation จริง → assign/เปิด conversation
- **Polling 30s + LIVE badge + connection lost handling**

**ทำไมสำคัญ:** Supervisor ที่ไม่เห็น queue real-time ตัดสินใจช้า — ลูกค้ารอนานโดยไม่จำเป็น

---

### STORY-ADB-02: Analytics View — วิเคราะห์เทรนด์ย้อนหลัง

**เป้าหมาย:** Manager ดู historical performance ของทีมได้ครบ พร้อม chart และ heatmap สำหรับวางแผน

**สิ่งที่จะทำ:**
- **4 KPI cards:** Total Conversations, Avg FRT (Human), Avg AHT, Resolution Rate
- **FRT bar chart:** bot vs human เปรียบเทียบรายวัน
- **SLA Distribution:** % conversation ใน 4 FRT buckets (< 1m, 1-5m, 5-30m, > 30m)
- **Weekly Trend line chart:** volume + FRT 4 สัปดาห์
- **Peak Hours Heatmap:** 7 วัน x 12 ช่วงเวลา (ทุก 2h) — normalize ตาม period
- **Channel Breakdown + Top Auto-tags:** เห็น mix ของ channel และ tag ที่ rule ติด

**ทำไมสำคัญ:** FRT เฉลี่ยวันเดียวบอกอะไรไม่ได้ — ต้องดูเทรนด์ 7/30 วัน และ peak hour ก่อนจะตัดสินใจเพิ่ม resource

---

### STORY-ADB-03: Agents Performance View — ranking และ coaching

**เป้าหมาย:** Supervisor เห็น performance ranking ของ agent ทุกคน ส่วน Agent เห็นของตัวเอง

**สิ่งที่จะทำ:**
- **4 Team KPIs:** Working Now, Total Resolved, Avg FRT, Avg AHT
- **Performance Table:** per agent พร้อม sort (Resolved / FRT / AHT)
- **Color coding:** FRT/AHT ตาม threshold เขียว/ส้ม/แดง
- **AHT attribution แบบ time-split:** ใช้ assignment_history — ไม่โยนเวลาทั้งก้อนให้คนสุดท้าย
- **Permission:** Agent role เห็นเฉพาะ row ตัวเอง + period ล็อค Today

**ทำไมสำคัญ:** ถ้า AHT โยนให้คนสุดท้ายทั้งหมด คนที่ reassign มาแค่ 5 นาทีจะดู AHT สูงผิดจริง — fairness ของ metric สำคัญมากสำหรับ performance review

---

### STORY-ADB-04: Channels Performance View — เปรียบเทียบ channel

**เป้าหมาย:** Manager เห็นว่า channel ไหนมีปัญหา (FRT ช้า, Switch% สูง, backlog ค้าง)

**สิ่งที่จะทำ:**
- **Comparison Table:** 6 channels เรียงคู่ — Volume, FRT, Resolution Rate, Switch%
- **Switch%:** % ลูกค้าที่ต้องเปลี่ยน channel เพื่อหาคำตอบ — ใช้ customer_id matching ข้าม channel
- **Backlog Age cards:** 4 buckets (< 1h, 1-4h, 4-24h, > 1d) พร้อม escalation alert
- **Color coding:** แต่ละ metric มีสี threshold

**ทำไมสำคัญ:** Shopee อาจมี FRT ดีแต่ Switch% สูง — หมายความว่าลูกค้าต้องไปหาคำตอบที่ LINE แทน นั่นคือ process ที่พัง ไม่ใช่แค่ speed

---

### STORY-ADB-05: Automation Performance View — พิสูจน์ ROI ของ Rule

**เป้าหมาย:** Admin เห็นว่า automation rules ทำงานได้จริงและคุ้มแค่ไหน — fired/handled/skip per rule + FRT reduction

**สิ่งที่จะทำ:**
- **4 KPI cards:** Rules Active (X/20), Auto-replied, Auto-tagged, FRT Reduction %
- **Rule Performance Table:** per rule — Fired, Handled, Skip, Success% + progress bar สีตาม threshold
- **Reply Attribution:** human vs rule message % + Bot FRT / Human FRT / Reduction stats
- **Tag Attribution:** auto vs manual tag % + top 4 auto-tags
- **Edge cases:** rule ถูกลบแต่ log ยังอยู่ → แสดง '(deleted)', FRT Reduction ไม่มีข้อมูล → แสดง ' - ' ไม่ใช่ 0% หรือ infinity

**ทำไมสำคัญ:** ถ้าไม่มีหน้านี้ Admin ไม่รู้ว่า rule ที่ตั้งทำงานจริงหรือเปล่า และ justify ไม่ได้ว่า Rule Automation feature มีมูลค่า
