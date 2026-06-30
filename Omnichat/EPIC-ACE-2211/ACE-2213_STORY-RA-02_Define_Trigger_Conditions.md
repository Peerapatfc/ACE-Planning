# STORY-RA-02: Define Trigger Conditions

**ClickUp ID:** ACE-2213
**Status:** In Progress
**Points:** 5 SP
**Assignees:** griangsak
**Parent Epic:** ACE-2211
**URL:** https://app.clickup.com/t/86d31160t

---

## User Story

As an Admin / Supervisor,
I want to กำหนด trigger conditions ได้ 3 types พร้อม AND/OR logic และ test panel,
so that Rule ทำงานตรงกับสถานการณ์ที่ต้องการ ไม่ trigger ผิดพลาด และ admin ทดสอบ condition ได้ก่อน activate.

---

## Detail / Description

- Trigger types ที่รองรับมี 3 ประเภท: **Keyword match**, **Channel**, **Business hours** (รวม Day of week)
- Keyword match รองรับ 2 operators: `contains` (partial match) และ `exact` (ต้องตรง message ทั้งหมด) — ทั้งคู่ case-insensitive รองรับภาษาไทยและอังกฤษ
- Business hours รวม Day of week เป็น field เดียวกัน เพราะ user คิดถึง 'เวลาทำการ' ไม่ได้แยกวันและเวลา — มี toggle 'ใช้ Workspace hours' เป็น default เพื่อลด friction (ใช้ ui เดิมได้)
- Conditions หลายอันเชื่อมด้วย **AND** (ทุกข้อตรง) หรือ **OR** (ตรงข้อใดข้อหนึ่ง)
- Evaluation เป็น **single-pass** — evaluate ทุก condition ณ เวลาที่ message เข้า แล้วจึง execute actions; ไม่ re-evaluate ระหว่าง execute
- ป้องกัน loop: evaluate เฉพาะ message ของลูกค้า (`sender_type = 'contact'`) ข้าม `'agent'`/`'system'` / message ซ้ำกันใน 5 วินาทีถูก deduplicate (background — guard ใหม่)

---

## Scope of This Story

- **Keyword:** contains, exact — case-insensitive ไทย-อังกฤษ
- **Channel:** LINE, Facebook, Instagram, Shopee, Lazada, TikTok — multi-select (matching ทำบน `conversation.channel_type` channel-agnostic — แต่ Shopee/TikTok inbound ยังไม่ integrate เต็ม จึงอาจยังไม่มี conversation จริงเข้ามาให้ match)
- **Business hours:** within/outside + day of week + timezone ในช่อง field เดียว (reuse `nextBhOpenAt` จาก `packages/shared`; config per-tenant จาก tenant-service)
- Toggle 'ใช้ Workspace hours' เป็น default on; ถ้าปิดแสดง custom picker (ใช้ ui เดิม)
- AND/OR toggle ระหว่าง condition cards
- **Test panel:** พิมพ์ข้อความ → match/no-match real-time + highlight condition ที่ match
- Non-customer sender skip (background): evaluate เฉพาะ `sender_type='contact'` ข้าม `agent`/`system`
- Message deduplication 5s window (background — guard ใหม่)

### Out of Scope

- starts with / ends with operator
- Regex / NLP / intent detection
- Wait time trigger
- Conversation status trigger
- Assigned to trigger
- Customer profile / segment

---

## Acceptance Criteria

**1. Keyword contains (partial, case-insensitive)**

Scenario 1
- Given Admin ตั้ง keyword: contains 'ยกเลิก'
- When message คือ 'อยากจะยกเลิก Order ครับ'
- Then Condition match: partial match, case-insensitive

Scenario 2
- Given Admin ตั้ง keyword: contains 'CANCEL'
- When message คือ 'i want to cancel this order'
- Then Condition match: uppercase keyword ทำงาน case-insensitive

Scenario 3
- Given Admin ตั้ง keyword: contains 'refund'
- When message คือ 'ขอบคุณมากครับ'
- Then Condition ไม่ match

**2. Keyword exact (ต้องตรงทั้ง message)**

Scenario 1
- Given Admin ตั้ง keyword: exact 'ยกเลิก'
- When message คือ 'ยกเลิก'
- Then Condition match

Scenario 2
- Given Admin ตั้ง keyword: exact 'ยกเลิก'
- When message คือ 'อยากยกเลิก'
- Then Condition ไม่ match: เพราะ exact ต้องตรงทั้งหมด

**3. Channel multi-select**

Scenario 1
- Given Admin เลือก channel: Shopee และ Lazada
- When conversation เข้าจาก Lazada
- Then Condition match

Scenario 2
- Given Admin เลือก channel: LINE
- When conversation เข้าจาก Shopee
- Then Condition ไม่ match

Scenario 3
- Given Admin เลือกทุก channel (หมดทุกอัน)
- When conversation เข้าจาก channel ใดก็ได้
- Then Condition match เสมอ เทียบเท่า 'ไม่ filter channel'

**4. Business hours toggle Workspace hours**

Scenario 1
- Given Admin เปิด business hours condition, toggle 'ใช้ Workspace hours' = on, เลือก outside
- When conversation เข้าเวลา 20:00 (นอกเวลา Workspace 09:00–18:00)
- Then Condition match: ไม่ต้องกรอก timezone ซ้ำ ใช้ Workspace timezone อัตโนมัติ

Scenario 2
- Given Admin toggle 'ใช้ Workspace hours' = on, เลือก within
- When conversation เข้าเวลา 10:30
- Then Condition match: อยู่ในเวลาทำการ

**5. Business hours custom settings**

Scenario 1
- Given Admin ปิด Workspace toggle, กำหนด custom: outside, เสาร์–อาทิตย์, 00:00–23:59, Asia/Bangkok
- When conversation เข้าวันเสาร์เวลา 15:00
- Then Condition match

Scenario 2
- Given Admin กำหนด custom time range ข้าม midnight: outside 22:00–06:00
- When conversation เข้าเวลา 23:30
- Then Condition match

**6. AND logic ทุกข้อต้องตรง**

Scenario 1
- Given Rule มี: keyword contains 'ยกเลิก' AND channel = LINE
- When message 'ยกเลิก' มาจาก Shopee
- Then Rule ไม่ทำงาน: channel ไม่ตรง

Scenario 2
- Given Rule มี: keyword contains 'ยกเลิก' AND channel = LINE
- When message 'ยกเลิก' มาจาก LINE
- Then Rule ทำงาน: ทั้งสองข้อตรง

**7. OR logic ตรงข้อใดข้อหนึ่ง**

Scenario 1
- Given Rule มี: keyword contains 'ยกเลิก' OR channel = LINE
- When message 'สวัสดี' มาจาก LINE
- Then Rule ทำงาน: channel ตรง แม้ keyword ไม่ตรง

Scenario 2
- Given Rule มี: keyword contains 'ยกเลิก' OR channel = LINE
- When message 'สวัสดี' มาจาก Shopee
- Then Rule ไม่ทำงาน: ไม่มีข้อใดตรงเลย

**8. Test panel real-time**

Scenario 1
- Given Admin อยู่ใน Step 1 และมี keyword condition: contains 'ยกเลิก'
- When พิมพ์ 'อยากยกเลิก' ใน test panel
- Then แสดง 'Match' ทันที พร้อม highlight condition card สีเขียว

Scenario 2
- Given Admin มี 2 conditions: AND keyword + channel ที่ยังไม่เลือก channel
- When พิมพ์ข้อความใน test panel
- Then Keyword card highlight สีเขียว, Channel card highlight สีแดง; แสดง 'No match (AND ต้องตรงทุกข้อ)' (ถาม art ให้ art design ให้)

**9. Non-customer sender skip (background)**

- Given Rule มี keyword contains 'ยกเลิก'
- When มี message ที่ `sender_type='system'` หรือ `'agent'` (เช่น echo/automated message) ที่มีคำว่า 'ยกเลิก' เข้า conversation
- Then Rule ไม่ evaluate — log: `skipped: sender_type = system` (evaluate เฉพาะ `'contact'`)

**10. Message deduplication (background)**

- Given Customer ส่ง message เดิมซ้ำ 5 ครั้งใน 3 วินาที
- When messages เข้า system
- Then Rule evaluate ครั้งเดียว; 4 ครั้งที่เหลือถูก deduplicate (background log: `deduplicated: 4 messages`)

**11. ไม่มี condition validate ก่อน save**

- Given Admin ไม่ได้เพิ่ม condition ใดเลย
- When กด Next หรือ Save
- Then Validation error: 'ต้องมีอย่างน้อย 1 เงื่อนไข' ไม่อนุญาตให้ proceed

---

## UI/UX Notes

- Condition card: `[Type dropdown] [Operator ถ้ามี] [Value input] [× ลบ]`
- Business hours card: toggle 'ใช้ Workspace hours' เป็น default on; เมื่อปิดแสดง day picker + time picker (ใช้ ui อันเดิมได้เลย)
- Day picker ใน Business hours: ใช้ ui อันเดิมได้เลย
- AND/OR toggle อยู่ระหว่าง condition cards แบบ inline
- Test panel: text input + result badge (Match/No match) + highlight card
- Info box: 'เฉพาะข้อความจากลูกค้าเท่านั้นที่ trigger rule (ข้อความจาก agent/ระบบจะไม่ trigger)'
- ปุ่ม '+ เพิ่มเงื่อนไข' ด้านล่าง card list

---

## QA / Test Considerations

### Primary Flows
- Admin เลือก type → กรอก value → test panel → เพิ่ม condition ที่ 2 → AND/OR → Next
- Admin เลือก Business hours → Workspace toggle on → เลือก within/outside → Next
- Admin เลือก Business hours → ปิด Workspace toggle → เลือกวัน + เวลา → Next

### Edge Cases
- Keyword ว่าง → validate error 'กรุณากรอก keyword' ก่อน save
- Keyword ที่มี special characters เช่น '(cancel)' → notify ก่อน match ว่าไม่ treat เป็น regex
- Business hours: start time = end time → validate error 'เวลาเริ่มต้นและสิ้นสุดต้องไม่เท่ากัน'
- ไม่เลือก channel ใดเลยใน Channel condition → validate error 'เลือกอย่างน้อย 1 channel'
- AND logic มี 3 conditions แต่ test message match แค่ 2 ใน 3 → แสดง No match + highlight 2 สีเขียว 1 สีแดง

### Business-Critical "Must Not Break"
- Case-insensitive ต้องทำงานถูกต้องทั้งภาษาไทยและอังกฤษ
- Business hours ต้อง evaluate ด้วย Workspace timezone เมื่อ toggle = on
- Non-customer sender (`sender_type ≠ 'contact'`) ต้องไม่ trigger rule ไม่ว่า keyword จะ match หรือไม่
- Single-pass evaluation: tag ที่ rule A เพิ่งเพิ่มต้องไม่ trigger rule B ในรอบเดียวกัน

### Test Types
- Unit: keyword contains (partial, case-insensitive Thai/EN)
- Unit: keyword exact (whole message match)
- Unit: special character escape
- Unit: business hours evaluation ทั้ง Workspace และ custom
- Unit: midnight-crossing time range
- Unit: AND / OR evaluation logic
- Unit: non-customer sender skip (`sender_type ≠ 'contact'`)
- Unit: message deduplication (5s window)
- Integration: condition evaluation pipeline
- E2E: test panel → match/no-match + highlight
