# STORY-ADB-05: Automation Performance View
**ClickUp:** ACE-2357 | **Epic:** ACE-2353 | **Status:** Backlog

---

## User Story

**As a** Admin / Supervisor,
**I want to** ดูว่า automation rules ที่ตั้งไว้ทำงานคุ้มไหม - fired, handled, skip + attribution,
**so that** Admin พิสูจน์ ROI ของ Rule Automation feature และ identify rule ที่ควรปรับ.

---

## Detail / Description

- หน้า Automation เป็นหน้า valuable ที่สุดสำหรับ v1 — ตอบคำถาม 'rule ที่ตั้งทำงานคุ้มหรือเปล่า'
- ทุก metric ในหน้านี้วัดได้จริงจาก execution log, sender_type, tagged_by_type ที่เก็บอยู่แล้ว
- 4 KPIs: Rules Active, Auto-replied, Auto-tagged, FRT Reduction
- Rule Performance Table: fired/handled/skip/success% per rule
- Reply Attribution: human vs rule message %
- Tag Attribution: human vs rule tag %

---

## Scope of this Story

- 4 KPI cards: Rules Active (X/20), Auto-replied วันนี้, Auto-tagged วันนี้, FRT Reduction %
- Rule Performance table per rule: name + type icon, Fired, Handled, Skip, Success%
- Reply Attribution: bar comparison human vs rule + 3 stats (Bot FRT, Human FRT, Reduction)
- Tag Attribution: bar comparison auto vs manual + top 4 tags list
- Period filter apply

**Out of scope:**
- A/B testing rules (v2)
- Suggested rule improvements (v2 — ต้องมี AI ก่อน)
- Cost saving estimation (v2)

---

## Metrics & Definitions

| Metric | Definition / Formula | Attribution / Notes |
|--------|---------------------|---------------------|
| Rules Active | COUNT(rule WHERE active = true) | max 20 ตาม spec ของ Rule Automation |
| Auto-replied | COUNT(message WHERE sender_type='rule' AND type='auto_reply' AND date IN period) | จำนวน message ที่ rule ส่ง |
| Auto-tagged | COUNT(tag_event WHERE tagged_by_type='rule' AND date IN period) | จำนวน tag ที่ rule ติด |
| FRT Reduction | ((human_FRT - bot_FRT) / human_FRT) x 100 | วัดว่า auto-reply ลดเวลา response ได้กี่ % |
| Rule Fired | COUNT(execution_log WHERE rule_id = X) | trigger ทุกครั้งไม่ว่าผลลัพธ์ |
| Rule Handled | COUNT(execution_log WHERE rule_id = X AND status = 'success') | action ทำงานสำเร็จ |
| Rule Skip | COUNT(execution_log WHERE rule_id = X AND status = 'skipped') | ข้าม (cooldown, conversation closed, ฯลฯ) |
| Rule Success% | (Handled / Fired) x 100 | เทียบ success rate, ต่ำ = rule มีปัญหา |
| Reply Attribution % | GROUP BY sender_type (human\|rule) - COUNT(message) per group | แยก message ที่มาจากคน vs ระบบ |
| Tag Attribution % | GROUP BY tagged_by_type (human\|rule) - COUNT(tag) per group | แยก tag ที่มาจากคน vs ระบบ |

---

## Acceptance Criteria

### 1. Rules Active ตรงกับ X/20
- มี rules ที่ active = 5 ตัว → แสดง '5 of 20 limit' ตาม spec Rule Automation

### 2. Auto-replied แยกจาก human message
- วันนี้มี message 5000 อัน: 3000 จาก agent, 1827 จาก rule, 173 จาก system → แสดง 1,827 (เฉพาะ sender_type='rule')

### 3. FRT Reduction calculation
- Human FRT = 2.4m, Bot FRT = 0.3m → แสดง 87% — ((2.4 - 0.3) / 2.4) x 100

### 4. Rule Performance per rule
- **Scenario 1:** Rule 'Auto-reply, Outside hours' fired 1284 ครั้ง, handled 1201, skip 83 → Fired 1,284, Handled 1,201, Skip 83, Success 94% (progress bar สีน้ำเงิน)
- **Scenario 2:** Rule success% < 90% → progress bar สีส้ม (signal ว่า rule ต้องดู)

### 5. Reply Attribution
- **Scenario 1:** Human 3051, Rule 1827 → human 63%, rule 37% — bar 2 สี
- **Scenario 2:** แสดง stats ใต้ bar → Bot FRT 0.3m, Human FRT 2.4m, FRT Reduction 87%

### 6. Tag Attribution
- Auto 1419, Manual 581 → auto 71%, manual 29% — bar 2 สี + top 4 auto-tags ด้านล่าง

### 7. Empty state - ไม่มี rule active
- **Scenario 1:** Workspace ยังไม่มี rule ใด active → Rules Active = 0/20, ทุก KPI = 0 หรือ ' - ', Rule Performance table แสดง empty state พร้อม CTA 'สร้าง rule แรก' link ไป Rule Management
- **Scenario 2:** มี rule แต่ inactive ทั้งหมด → Rules Active = 0/20, execution data ของ rule ที่เคย active ยังแสดงใน performance table

### 8. Rule ถูกลบ แต่ execution_log ยังอยู่
- Rule 'Old promotion' ถูกลบไปแล้ว แต่ใน period มี execution log → แสดงใน table พร้อม label '(deleted)' หลังชื่อ, ตัวเลขปกติ, ไม่คลิกไปแก้ rule ได้

### 9. FRT Reduction edge case
- **Scenario 1:** Period นี้ไม่มี bot reply เลย → แสดง ' - ' ไม่ใช่ 0% หรือ infinity
- **Scenario 2:** Bot FRT ช้ากว่า Human FRT (เคสแปลก เช่น bot retry 3 ครั้ง) → แสดง 0% (ไม่แสดงค่าลบ) + tooltip 'bot ไม่ได้ลด FRT ใน period นี้'

### 10. Consistency กับ Rule Management
- **Scenario 1:** Rules Active = 5 ในหน้า Rule Management → ต้องตรงกัน = 5 ใน Automation dashboard
- **Scenario 2:** Admin disable rule ในหน้า Rule Management → refresh Automation tab → Rules Active ลดลง 1, execution log ของ rule นั้นยังอยู่ใน table

### 11. Period filter apply
- Admin เปลี่ยน period = 30 days → Auto-replied, Auto-tagged, Rule Performance, Attribution update
- **Rules Active ไม่เปลี่ยน** (เป็น current state ไม่ขึ้นกับ period)

### 12. Permission - Agent ไม่เห็น Automation
- **Scenario 1:** User role = Agent เปิด URL Automation tab → redirect ไป Agents tab, Automation tab ไม่อยู่ใน sidebar
- **Scenario 2:** Agent call API GET /automation/rules/performance → 403 Forbidden

---

## UI/UX Notes

- 4 KPIs ใช้ icon ที่สื่อ: Rules, Reply, Tag, FRT
- Rule table: icon (reply) หรือ (tag) นำหน้าชื่อ rule
- Success% bar สีเปลี่ยนตาม threshold: >= 95% เขียว, 90-95% น้ำเงิน, < 90% ส้ม
- Reply / Tag Attribution: 2 panels เคียงกัน แบบเดียวกัน เพื่อ visual consistency
- Tooltip info icon บน FRT Reduction, Reply Attribution, Tag Attribution, Fired, Handled, Skip
- Period filter ทำงานเหมือน Analytics

---

## QA / Test Considerations

**Primary flows:**
1. Admin เปิด Automation → เห็น Auto-replied 1,827 + FRT Reduction 87% → พิสูจน์คุ้ม
2. Admin ดู rule table → เห็น 'Auto-reply, Outside hours' success 94% → rule ทำงานดี
3. Admin เห็น rule ใด success < 90% → คลิกไปดูที่ Rule Management → debug หรือปรับ condition

**Edge Cases:**
- ไม่มี rule ใด active — แสดง 0/20 + empty state 'สร้าง rule แรก' พร้อม link ไป Rule Management
- Rule ถูกลบไปแล้ว แต่มี execution_log อยู่ — แสดงในตารางพร้อม note '(deleted)'
- FRT Reduction คำนวณไม่ได้ (ไม่มี bot reply ใน period) — แสดง ' - ' ไม่ใช่ 0
- Auto-tagged แต่ tag ถูกลบไปแล้ว — ยังนับเพราะ tag event ยังอยู่

**Business-Critical "Must Not Break":**
- sender_type='rule' ต้องแยกชัดเจน — ห้ามนับเข้า human attribution
- tagged_by_type='rule' ต้องแยกชัดเจน — ห้ามนับเข้า manual attribution
- Rules Active count ต้องตรงกับ Rule Management view (consistency)
- FRT Reduction ต้องไม่ลบ (negative) — ถ้า bot ช้ากว่า human แสดง ' - ' หรือ 0%

**Test Types:**
- Unit: sender_type / tagged_by_type filter logic
- Unit: FRT Reduction formula + edge case (no bot data)
- Unit: Rule success% calculation
- Integration: rule execution log → dashboard
- E2E: สร้าง rule + trigger → dashboard reflect ภายใน next refresh
- Performance: rule attribution query ใน 30-day scope < 2 วินาที
