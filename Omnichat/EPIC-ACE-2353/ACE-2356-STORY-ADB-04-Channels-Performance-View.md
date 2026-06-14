# STORY-ADB-04: Channels Performance View
**ClickUp:** ACE-2356 | **Epic:** ACE-2353 | **Status:** Backlog

---

## User Story

**As a** Admin / Supervisor,
**I want to** เปรียบเทียบ performance ทุก channel + ดู backlog age,
**so that** Manager เห็นว่า channel ไหนมีปัญหา (FRT ช้า / Switch% สูง) และจัดสรร resource ใหม่.

---

## Detail / Description

- หน้า Channels เปรียบเทียบ 6 channels: LINE, Facebook, Instagram, Shopee, Lazada, TikTok
- ตารางเดียวรวม metrics สำคัญ: Volume, FRT, Resolution Rate, Switch%
- **Switch%** = % ลูกค้าที่ใช้มากกว่า 1 channel ในการสนทนา (signal ว่าลูกค้าต้องเปลี่ยน channel เพื่อหาคำตอบ)
- Backlog Age: conversation ที่ยังเปิดอยู่ แบ่งเป็น 4 buckets ตามอายุ
- Alert: ถ้ามี conversation ค้างเกิน 1 วัน > 3 อัน → escalation warning

---

## Scope of this Story

- Comparison Table per channel: Channel, Volume + share bar, FRT, Resolution Rate, Switch%
- Color coding: FRT (เขียว/ส้ม/แดง), Resolution (เขียว/ส้ม/แดง), Switch% (เขียว/ส้ม/แดง)
- Backlog Age cards: < 1 ชม / 1-4 ชม / 4-24 ชม / > 1 วัน + จำนวน + %
- Alert banner ถ้ามี backlog > 1 วันมากกว่า threshold
- Note อธิบาย FRT, Switch% และ Resolution

**Out of scope:**
- Channel-level CSAT (v2)
- Channel deflection rate (v2)
- Channel-level cost analysis (v2)
- Drill-in per channel (ใช้ filter ใน Analytics tab แทน)

---

## Metrics & Definitions

| Metric | Definition / Formula | Attribution / Notes |
|--------|---------------------|---------------------|
| Channel Volume | COUNT(DISTINCT conversation_id) GROUP BY channel | นับ unique conversation |
| Channel % share | channel_volume / total x 100 | ใน period ที่เลือก |
| Channel FRT | AVG(first_human_response_at - created_at) GROUP BY channel | ไม่นับ auto-reply |
| Channel Resolution Rate | (resolved per channel / total per channel) x 100 | นับ unique |
| Channel Switch% | COUNT(conversation ที่ลูกค้าใช้ > 1 channel) / total x 100 | ระบุลูกค้าด้วย customer_id ข้าม channel, สูง = ลูกค้าต้องเปลี่ยน channel |
| Backlog Age | WHERE status = open, GROUP BY (NOW - created_at) bucket | buckets: <1h, 1-4h, 4-24h, >1d |

---

## Acceptance Criteria

### 1. Switch% calculation
- **Scenario 1:** Customer ID #555 เริ่ม conversation ที่ LINE แล้วต่อใน Facebook ภายในวันเดียวกัน → นับเป็น switching event 1 ครั้งสำหรับทั้ง LINE และ Facebook
- **Scenario 2:** Customer ID #555 ใช้แค่ LINE → ไม่นับ switching

### 2. Backlog Age buckets
- **Scenario 1:** Conversation #100 เปิดมา 45 นาที → นับเข้า bucket '< 1 ชั่วโมง'
- **Scenario 2:** Conversation #100 เปิดมา 26 ชั่วโมง → นับเข้า bucket '> 1 วัน'

### 3. Escalation alert
- **Scenario 1:** มี conversation > 1 วัน 5 อัน → แสดง alert: 'มี 5 conversations ค้างเกิน 1 วัน - ต้องการ escalation'
- **Scenario 2:** มี conversation > 1 วัน 0-3 อัน → ไม่แสดง alert

### 4. Color coding
- **Scenario 1:** Channel Switch% = 18% → แสดงสีแดง (> 15%)
- **Scenario 2:** Channel Switch% = 8% → แสดงสีเขียว (< 10%)

### 5. Period filter apply
- Admin เปลี่ยน period = 30 days → ทุก metric ใน channel comparison + backlog update

### 6. Channel ไม่มี conversation ใน period
- TikTok ไม่มี conversation ใน period ที่เลือก → TikTok ยังแสดงใน row, ค่าทั้งหมด = 0 หรือ ' - ', ไม่ซ่อน row

### 7. Customer ไม่ identify ได้ข้าม channel
- **Scenario 1:** Customer ใช้ LINE (login) และ Facebook (guest ไม่ login) → ไม่ count เป็น switching เพราะ customer_id ไม่ match (Switch% เป็น lower bound)
- **Scenario 2:** Customer ใช้ LINE 2 ครั้งต่างเวลา → ไม่นับ — same channel

### 8. Empty state Backlog
- **Scenario 1:** ไม่มี conversation ใดยังเปิดอยู่ → แสดง 'ไม่มี backlog' แทน cards ทั้ง 4, ไม่แสดง alert
- **Scenario 2:** มี backlog แต่ทุก bucket > 1 วัน = 0 → แสดง cards 4 ใบปกติ (3 แรกมีค่า, สุดท้าย = 0), ไม่แสดง escalation alert

### 9. Permission - Agent ไม่เห็น Channels
- User role = Agent เปิด URL Channels tab → redirect ไป Agents tab, Channels tab ไม่อยู่ใน sidebar

### 10. Consistency - channel sum = total
- Period = 7 days, Total = 4,870 → sum Volume ของทุก 6 channels ต้องเท่ากับ 4,870

---

## UI/UX Notes

- Single table แทนการแยกหลาย panel ลด cognitive load
- Volume column = bar chart inline + ตัวเลข right-aligned
- Switch% และ Resolution% มี mini progress bar ใต้ตัวเลข สีตาม threshold
- Backlog cards 4 ใบ ด้านล่างตาราง — สีเข้มตาม severity
- Footer note สีอ่อนอธิบาย Switch% / Resolution definitions
- Tooltip info icon บน FRT, Resolution, Switch% column headers

---

## QA / Test Considerations

**Primary flows:**
1. Manager เปิด Channels → เห็น Shopee Switch% 18% สีแดง → คลิก info ดู definition → เข้าใจว่าลูกค้าต้องเปลี่ยน channel
2. Manager ดู Backlog Age → เห็นมี 5 อันค้างเกินวัน → escalation alert → escalate ทีม

**Edge Cases:**
- Channel ที่ไม่มี volume — แสดง row + ค่า 0 ทั้งหมด ไม่ซ่อน
- Switch% มีเฉพาะตอน customer_id matching ได้ — ถ้า customer ไม่ login ทุก channel อาจ identify ไม่ได้
- Backlog ทั้งหมด = 0 — แสดง 'ไม่มี backlog' แทน cards
- Customer ใช้ channel เดียวกัน 2 ครั้งใน period — ไม่นับเป็น switching

**Business-Critical "Must Not Break":**
- Volume sum across channels = Total Conversations ของ Analytics
- Switch% ต้องไม่นับ same-channel switching
- Backlog buckets ไม่ overlap — conversation นึงต้องอยู่ bucket เดียว

**Test Types:**
- Unit: channel volume aggregation
- Unit: Switch% logic (cross-channel customer_id)
- Unit: Backlog bucket assignment by age
- Integration: period filter propagation
- E2E: backlog > 1d threshold → alert appear
