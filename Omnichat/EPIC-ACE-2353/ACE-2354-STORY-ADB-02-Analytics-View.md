# STORY-ADB-02: Analytics View
**ClickUp:** ACE-2354 | **Epic:** ACE-2353 | **Status:** Backlog

---

## User Story

**As a** Admin / Supervisor,
**I want to** ดู historical metrics ของทีม - volume, FRT, AHT, Resolution Rate และ trend ย้อนหลังได้,
**so that** Manager วิเคราะห์ performance ทีมเพื่อตัดสินใจปรับ process หรือเพิ่ม resource.

---

## Detail / Description

- หน้า Analytics เป็น historical view ไม่ใช่ real-time, refresh เฉพาะตอนเปลี่ยน period filter
- 4 Primary KPIs ที่ supervisor ดูทุกวัน: Total Conversations, Avg FRT (Human), Avg AHT, Resolution Rate
- Charts ที่เห็นเทรนด์: FRT bot vs human, SLA Distribution, Weekly Trend (volume + FRT)
- Peak Hours Heatmap: วัน x ชั่วโมง สำหรับวางแผน shift agent
- Channel Breakdown + Top Auto-tags ช่วยให้เห็นว่าปัญหาประเภทไหนเข้ามาเยอะ
- Period filter: Today / 7 days / 30 days — ทุก metric เปลี่ยนตาม period

---

## Scope of this Story

- 4 Primary KPI cards: Total Conversations, Avg FRT (Human), Avg AHT, Resolution Rate
- FRT bar chart: bot vs human รายวัน (7 วันล่าสุด)
- SLA Distribution: % conversation ในแต่ละ FRT bucket (< 1m, 1-5m, 5-30m, > 30m)
- Weekly Trend line chart: volume + FRT 4 สัปดาห์
- Peak Hours Heatmap: 7 วัน x 12 ช่วงเวลา (ทุก 2 ชั่วโมง)
- Channel Breakdown: list per channel พร้อม % share
- Top Auto-tags: tag cloud จาก tagged_by_type='rule'
- Period filter: Today / 7 days / 30 days

**Out of scope:**
- Custom date range picker (v2)
- Custom report builder (v2)
- Export to CSV/Excel (v2)
- Schedule email report (v2)
- CSAT / FCR / Reopen / Abandoned / Deflection (ยังไม่มีระบบที่วัดได้ใน v1)

---

## Metrics & Definitions

| Metric | Definition / Formula | Attribution / Notes |
|--------|---------------------|---------------------|
| Total Conversations | COUNT(DISTINCT conversation_id WHERE created_at IN period) | นับ unique, reassign ไม่ทำให้ double-count |
| Avg FRT (Human) | AVG(first_human_response_at - created_at) | ไม่นับ auto-reply, ผูกกับ response แรก ไม่เปลี่ยนตาม reassign |
| Avg AHT | AVG(resolved_at - first_human_response_at) per conversation | เวลาตั้งแต่ human ตอบแรกจนปิด, conversation-level |
| Resolution Rate | (COUNT(DISTINCT resolved) / COUNT(DISTINCT total)) x 100 | นับ unique, กดปิด 2 รอบไม่ double, attribute ปิดให้ last assignee |
| FRT Bot | AVG(first_response_at - created_at) WHERE sender_type='rule' | เฉพาะ auto-reply |
| FRT Human | AVG(first_human_response_at - created_at) | เฉพาะ human response, เปรียบเทียบ benefit ของ automation |
| SLA Bucket | COUNT(FRT IN bucket) / total x 100 — bucket: <1m, 1-5m, 5-30m, >30m | ใช้ human FRT |
| Peak Heatmap | COUNT(conversation_id) GROUP BY day_of_week, hour_bucket(2h) | เฉลี่ยข้าม period, สะท้อนความหนาแน่นปกติ |
| Channel % share | COUNT per channel / total x 100 | นับ conversation ไม่ใช่ message |
| Top Auto-tags | COUNT(tag) WHERE tagged_by_type='rule' GROUP BY tag | เฉพาะ tag จาก rule ไม่นับ agent tag |

---

## Acceptance Criteria

### 1. Period filter เปลี่ยนทุก metric
- **Scenario 1:** Admin เลือก period = 7 days → ทุก KPI, chart, heatmap, channel, tag ปรับ scope เป็น 7 วันย้อนหลังทันที
- **Scenario 2:** Admin เลือก period = Today → Trend chart (รายสัปดาห์) ยังคงแสดง 4 สัปดาห์ (weekly trend ไม่มี Today scope)

### 2. Total นับ unique ไม่ double-count
- **Scenario 1:** Conversation #100 ถูก reassign 3 ครั้ง (A → B → C → ปิด) → นับ 1 (ไม่ใช่ 4)
- **Scenario 2:** Conversation #100 ถูกปิด 2 รอบ (เปิดใหม่อัตโนมัติแล้วปิดอีก) → นับ 1 unique conversation ที่ปิด

### 3. FRT ไม่นับ auto-reply
- **Scenario 1:** Conversation เข้า 14:00, auto-reply 14:00:30, human ตอบ 14:03 → FRT = 3 นาที (ไม่ใช่ 30 วินาที)
- **Scenario 2:** แสดง FRT bot vs human chart → bot bar = 0.5m, human bar = 3m แยกชัดเจน

### 4. FRT lock ไม่เปลี่ยนตาม reassign
- Agent A ตอบครั้งแรก FRT = 2m แล้ว reassign ไป B → B ตอบช้า 5 นาที → FRT ของ conversation = 2m (ของ A), ไม่เปลี่ยนเป็น 7m

### 5. SLA Distribution
- มี 1000 conversation: 580 ตอบใน 1 นาที, 280 ใน 5 นาที, 90 ใน 30 นาที, 50 เกิน 30 นาที → bucket แสดง 58%, 28%, 9%, 5%

### 6. Peak Heatmap
- **Scenario 1:** Period = 30 days → คำนวณค่าเฉลี่ยจำนวน conversation per (วัน, ชั่วโมง 2h bucket) ข้าม 30 วัน, แสดงเป็นสีเข้ม/อ่อนตาม density
- **Scenario 2:** Hover ที่ cell → แสดง tooltip 'อังคาร 10:00 - 78 conversations'

### 7. Top Auto-tags แยกจาก manual
- มี tag 'cancellation-risk' 312 ครั้งจาก rule และ 45 ครั้งจาก agent → แสดงเฉพาะ 312 (จาก rule)

### 8. Loading state ตอนเปลี่ยน period
- **Scenario 1:** Admin เปลี่ยน period จาก Today เป็น 30 days → แสดง loading skeleton บนทุก KPI/chart, abort request เก่าถ้ายังไม่เสร็จ
- **Scenario 2:** Fetch สำเร็จ → skeleton หาย, data update พร้อมกันทุก section (ไม่มี partial update)

### 9. Empty state - period สั้น data น้อย
- **Scenario 1:** Period = Today ตอน 6 โมง มีเพียง 3 conversation → แสดง KPIs ตามจริง, Trend chart แสดง note 'ข้อมูลยังไม่พอ'
- **Scenario 2:** Period = Today และไม่มี conversation เลย → ทุก KPI = 0, Heatmap แสดง empty cells

### 10. Empty state - ไม่มี bot rule active
- **Scenario 1:** ไม่มี auto-reply rule ใด active → แสดงเฉพาะ bar human, bot bar = 0 หรือซ่อน, legend คงไว้ทั้ง 2 สี
- **Scenario 2:** คำนวณ KPI FRT Reduction → ถ้าไม่มี bot data, แสดง ' - ' ไม่ใช่ 0% หรือ infinity

### 11. Consistency check - channel sum = total
- Total = 4,870 ใน period → sum ของทุก channel ใน Channel Breakdown ต้องเท่ากับ 4,870 พอดี

### 12. Heatmap period boundary
- **Scenario 1:** Period = Today → แสดงเฉพาะวันนี้ (1 row) + note 'ดูภาพรวมหลายวันที่ 7d/30d'
- **Scenario 2:** Period = 30 days → normalize เป็นค่าเฉลี่ยต่อช่อง (เฉลี่ย 30 วัน), ไม่ใช่ raw sum

### 13. Permission - Agent ไม่เห็น Analytics
- **Scenario 1:** User role = Agent เปิด URL Analytics tab → redirect ไป Agents tab, Analytics tab ไม่แสดงใน sidebar
- **Scenario 2:** Agent call API GET /analytics/summary → 403 Forbidden

---

## UI/UX Notes

- 4 KPI cards แถวเดียว เรียงตามความสำคัญ: Total → FRT → AHT → Resolution Rate
- Period filter มุมขวาบน, apply ทันที (ไม่ต้องกด Apply)
- Charts row 3 ใบ: FRT bar / SLA distribution / Weekly trend
- Heatmap row เต็มกว้าง, มี legend สีและ note ว่า peak ช่วงไหน
- Channel Breakdown + Auto-tags ด้านล่างเรียงเป็น 2 columns
- Tooltip info icon บนทุก KPI ที่เป็นศัพท์เทคนิค (FRT, AHT, Resolution Rate)
- Loading skeleton ตอนเปลี่ยน period แทนการกระพริบ data เก่า

---

## QA / Test Considerations

**Primary flows:**
1. Manager เปิด Analytics → ดู KPIs 4 ตัว → ดู FRT chart เห็นเทรนด์ → ดู heatmap → วาง shift schedule
2. Manager เปลี่ยน period จาก Today เป็น 7 days → ทุกอย่าง update
3. Manager hover บน cell heatmap → tooltip บอกตัวเลข + ช่วงเวลา

**Edge Cases:**
- Period = Today แต่ยังเช้ามาก (6 โมง) — data น้อยมาก แสดง 'ข้อมูลยังไม่พอ' บน trend chart
- ไม่มี auto-reply rule ใด active — FRT Bot bar เป็น 0 / empty
- Channel ใดไม่มี conversation ใน period — แสดงในตารางแต่ค่า 0 (ไม่ซ่อน)
- Tag ที่ rule ติดแต่ rule ถูกลบไปแล้ว — ยังนับใน Top Auto-tags เพราะ tag history ยังอยู่

**Business-Critical "Must Not Break":**
- Total ต้องเป็น COUNT DISTINCT เสมอ — ห้าม double-count จาก reassign
- FRT ต้องไม่นับ auto-reply ไม่ว่ากรณีใด
- Period filter ต้อง apply ทุก section ใน tab พร้อมกัน — ห้าม partial update
- Heatmap ต้อง normalize ตาม period — ไม่ใช่ raw count

**Test Types:**
- Unit: COUNT DISTINCT logic (reassign + reopen scenarios)
- Unit: FRT calculation excluding auto-reply (sender_type='rule')
- Unit: FRT lock to first responder, not last assignee
- Unit: SLA bucket calculation
- Unit: Heatmap aggregation per (day, hour_bucket)
- Integration: Period filter changes propagate to all sections
- E2E: เปลี่ยน period → ทุก metric update ภายใน 2 วินาที
- Performance: heatmap query ใน 30-day scope ต้องเสร็จใน < 3 วินาที
