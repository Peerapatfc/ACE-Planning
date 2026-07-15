# STORY-CTX-07: Contact Tags

**Status:** In Progress | **ClickUp:** [ACE-2714](https://app.clickup.com/t/86d3knuen) | **Epic:** [ACE-1472](https://app.clickup.com/t/ACE-1472)

## User Story

**AS** a Support Agent
**I WANT TO** ติด tag ให้กับ contact (โปรไฟล์ลูกค้า) ได้โดยตรง
**SO THAT** ทีมสามารถ segment ลูกค้า เห็น context ของลูกค้าคนเดิมได้ในทุก conversation และ filter งานตามประเภทลูกค้าได้

## Description

ปัจจุบันระบบมี tag เฉพาะระดับ conversation (tag ติดกับเรื่อง) story นี้เพิ่ม tag ระดับ contact (tag ติดกับคน) ซึ่งเป็นคนละชั้นกันและตอบคำถามคนละแบบ

Contact tag ติดที่ตัว contact ครั้งเดียว แล้วมีผลกับทุก conversation ของ contact นั้นโดยอัตโนมัติ ทั้ง conversation ที่มีอยู่แล้วและที่จะเกิดใหม่ในอนาคต เช่น ติด tag "VIP" ให้ลูกค้าหนึ่งราย ทุกเรื่องที่ลูกค้ารายนี้ทักเข้ามาจะถูกมองเป็นเรื่องของลูกค้า VIP ทันที และอยู่ในฝั่งของ contact

ตัวอย่าง use case ที่ contact tag ตอบโจทย์: ดูทุก conversation ของลูกค้า VIP, segment ลูกค้ากลุ่ม wholesale ทั้งหมด, agent เห็นทันทีว่ากำลังคุยกับลูกค้ากลุ่มไหนโดยไม่ต้องเปิดประวัติ

Tag library ของ contact tag ให้แยกจาก conversation tag library เพื่อไม่ให้ชื่อ tag สองชั้นปนกันตอนเลือกและตอน filter

## Scope of this story

- เพิ่มและลบ contact tag ได้จาก contact info panel ในหน้า conversation
- สร้าง tag ใหม่แบบ inline ระหว่างพิมพ์ได้ โดย typeahead จะแสดง tag ที่มีอยู่แล้วให้เลือกก่อน
- แสดง contact tag ในทุก conversation ของ contact นั้น โดยรูปแบบการแสดงผลแยกจาก conversation tag ชัดเจน
- เพิ่ม filter ใหม่ให้ conversation list สามารถ filter ด้วย contact tag ได้ แยกจาก filter ของ conversation tag
- Panel จัดการ contact tag library (rename, delete, ดูจำนวน contact ที่ใช้แต่ละ tag)
- บันทึก audit ว่าใครติดหรือลบ tag และเมื่อไหร่

**Out of scope:**
- Auto-tagging ผ่าน automation rules
- Bulk tagging หลาย contact พร้อมกัน
- SLA หรือ routing ตาม tag
- รายงานและ analytics ตาม contact tag

## Acceptance Criteria

### AC1: การติด tag ให้ contact

**Scenario 1**
**GIVEN** agent เปิด conversation และเห็น contact info panel ของลูกค้า
**WHEN** agent พิมพ์ชื่อ tag ที่มีอยู่แล้วใน library และกดเลือก
**THEN** ระบบบันทึก tag ที่ระดับ contact ทันที tag ปรากฏใน contact info panel ของทุก conversation ของ contact นั้นโดยไม่ต้อง refresh พร้อมบันทึก audit (ผู้ทำและเวลา)

**Scenario 2**
**GIVEN** agent พิมพ์ชื่อ tag ที่ยังไม่มีในระบบ
**WHEN** agent กดสร้าง tag ใหม่
**THEN** ระบบสร้าง tag เข้า contact tag library และติดให้ contact นั้นทันที โดย validate ชื่อ tag ตามข้อกำหนด (ยาวไม่เกิน 30 ตัวอักษร ตัดช่องว่างหัวท้าย convert ให้เป็น uppercase ทั้งหมด ในการแสดงผล)

### AC2: การลบ tag ออกจาก contact

**GIVEN** contact มี tag "VIP" ติดอยู่
**WHEN** agent กดลบ tag ออกจาก contact
**THEN** tag หายจาก contact นั้นในทุก conversation ทันที โดยตัว tag ยังคงอยู่ใน library และ contact อื่นที่ติด tag เดียวกันไม่ได้รับผลกระทบ

### AC3: การแสดงผลข้ามทุก conversation ของ contact

**GIVEN** contact มี tag "VIP" และมี conversation อยู่ 3 เรื่อง
**WHEN** agent เปิด conversation เรื่องใดก็ตามของ contact นี้ รวมถึงเรื่องใหม่ที่เพิ่งทักเข้ามาหลังติด tag
**THEN** เห็น tag "VIP" ใน contact info panel ครบทุกเรื่อง และรูปแบบการแสดงผลของ contact tag แยกจาก conversation tag อย่างชัดเจน

### AC4: Filter ด้วย contact tag

**Scenario 1**
**GIVEN** มี contact 2 รายที่ติด tag "VIP" และแต่ละรายมีหลาย conversation
**WHEN** agent เลือก filter contact tag = VIP
**THEN** รายการแสดงทุก conversation ของ contact ที่ติด tag VIP ไม่ว่า conversation นั้นจะมี conversation tag อะไรหรือไม่ก็ตาม

**Scenario 2**
**GIVEN** agent เลือก filter contact tag = VIP ร่วมกับ filter อื่น เช่น status = Open
**WHEN** apply filter
**THEN** ผลลัพธ์เป็นการ AND ของทุกเงื่อนไข และ filter ถูกเก็บใน URL parameter ตามพฤติกรรมเดียวกับ filter อื่นของระบบ

### AC5: การจัดการ tag library (Admin)

**Scenario 1**
**GIVEN** Admin เปิด panel จัดการ contact tag library
**WHEN** rename tag "VIP" เป็น "VIP Gold"
**THEN** ชื่อใหม่มีผลกับทุก contact ที่ติด tag นี้ทันที โดยไม่ต้องติด tag ใหม่

**Scenario 2**
**GIVEN** tag "wholesale" ถูกใช้กับ contact อยู่ 25 ราย
**WHEN** Admin กดลบ tag ออกจาก library
**THEN** ระบบแสดง confirmation พร้อมจำนวน contact ที่จะได้รับผลกระทบ และเมื่อยืนยัน tag ถูกถอดออกจากทุก contact และหายจาก library

### AC6: ข้อจำกัดและ validation

**GIVEN** contact มี tag ครบ 10 tag แล้ว
**WHEN** agent พยายามติด tag ที่ 11
**THEN** ระบบไม่บันทึกและแสดงข้อความแจ้งว่าเกินจำนวน tag สูงสุดต่อ contact

### AC7: สิทธิ์การใช้งาน (อิงตาม RBAC)

**GIVEN** ผู้ใช้ role Agent, Supervisor หรือ Admin
**WHEN** ใช้งานฟีเจอร์ contact tag
**THEN** ทุก role ติดและลบ tag บน contact ได้ ส่วนการจัดการ library (rename และ delete tag) ทำได้เฉพาะ Admin ส่วน Supervisor rename ได้อย่างเดียว ใน library

### AC8: Data isolation

**GIVEN** workspace A และ workspace B ตั้งชื่อ tag เหมือนกัน
**WHEN** ผู้ใช้ workspace A เรียกดู tag library หรือใช้ filter
**THEN** เห็นเฉพาะ tag และข้อมูลของ workspace ตัวเองเท่านั้น ไม่มีข้อมูลข้าม tenant ในทุกกรณี

## UI/UX Notes

- แสดง contact tag ใน contact info panel ส่วนบนใกล้ชื่อลูกค้า เป็น chip พร้อมปุ่มลบเมื่อ hover
- รูปแบบ chip ของ contact tag ต้องต่างจาก conversation tag เช่น outline style กับ filled style คนละแบบ (รอ design กำหนด token จาก art)
- ช่อง add tag เป็น typeahead แสดง tag ที่มีอยู่ก่อน ถ้าไม่พบจึงแสดงตัวเลือกสร้าง tag ใหม่
- ใน filter panel แยก section "Contact tag" ออกจาก "Conversation tag" พร้อม label กำกับชัดเจนเพื่อกันความสับสน
- Panel tag library แสดง ชื่อ tag, จำนวน contact ที่ใช้

## QA / Test Considerations

### Primary flows
- ติด tag ที่มีอยู่, สร้าง tag ใหม่, ลบ tag ออกจาก contact
- เปิด conversation หลายเรื่องของ contact เดียวกัน ตรวจว่า tag แสดงครบทุกเรื่อง
- Filter ด้วย contact tag ทั้งแบบเดี่ยวและร่วมกับ filter อื่น
- Admin rename และ delete tag จาก library

### Edge Cases
- Agent สองคนติด tag เดียวกันให้ contact เดียวกันพร้อมกัน ต้องไม่เกิด tag ซ้ำ
- ลบ tag จาก library ขณะที่หน้าจออื่นกำลังแสดง tag นั้นอยู่
- ชื่อ contact tag ตรงกับชื่อ conversation tag ต้องไม่ปนกันทั้งการแสดงผลและการ filter
- ชื่อ tag ภาษาไทย ภาษาอังกฤษ ตัวเลข และอักขระพิเศษ ตาม validation ที่กำหนด
- ติด tag ให้ contact ที่ conversation ทั้งหมดถูก resolve ไปแล้ว

### Business-Critical "Must Not Break"
- ข้อมูล tag ต้องไม่ข้าม tenant ในทุกกรณี
- พฤติกรรมของ conversation tag เดิมและ system tag (เช่น sla_breached) ต้องไม่เปลี่ยน
- Filter และ saved view เดิมที่ไม่เกี่ยวกับ contact tag ต้องทำงานเหมือนเดิม

### Test Types
- Unit test: validation, limit, duplicate check
- Integration test: tag CRUD, filter query, audit log
- Permission test ครบทั้ง 3 role
- UI test: การแสดงผลข้าม conversation และการแยกรูปแบบจาก conversation tag
