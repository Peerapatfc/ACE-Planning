# STORY-BC-06: Broadcast Detail

**Status:** Backlog | **ClickUp:** [ACE-2504](https://app.clickup.com/t/86d3dhk9h) | **Epic:** [ACE-2236](https://app.clickup.com/t/86d318wjb)

## User Story

**AS** Admin/Supervisor
**I WANT TO** ดูรายละเอียด broadcast เมื่อกดจากหน้า list
**SO THAT** สามารถดูข้อมูล message content และ settings ได้

## Acceptance Criteria

### AC1: Topbar
**GIVEN** กด broadcast row จากหน้า Broadcast List
**WHEN** เข้า detail page
**THEN** แสดง:
- ปุ่มกลับ (←) → กลับไปหน้า Broadcast List
- ชื่อ broadcast (เช่น "New Year Sale 2026")

### AC2: ข้อมูล Broadcast
**GIVEN** หน้า Broadcast Detail
**THEN** แสดง:
- Status badge: (Scheduled/Sent/Error/Sent with error/Draft)
- ชื่อ LINE OA
- เป้าหมาย (Target audience)
- จำนวนผู้รับ

### AC3: Status: Scheduled
**GIVEN** broadcast status = "Scheduled"
**THEN** แสดง:
- วันและเวลาตั้งเวลาส่ง
- ปุ่ม "Edit" → ไปหน้า form สามารถแก้ไขได้
- ปุ่ม "Cancel Schedule" → ยกเลิกการตั้งเวลา → broadcast เปลี่ยนเป็น "Draft"
- ปุ่ม "Delete" → ลบ broadcast → กลับไปหน้า list

### AC4: Status: Sent
**GIVEN** broadcast status = "Sent"
**THEN** แสดง:
- วันและเวลาที่ส่ง
- จำนวนผู้รับ (เช่น "3,200 คน")
- ปุ่ม "Delete" → ลบ broadcast → กลับไปหน้า list

### AC5: Status: Error
**GIVEN** broadcast status = "Error"
**THEN** แสดง:
- ข้อความ error: เหตุผลที่ล้มเหลว (เช่น "Network timeout", "Quota exceeded")
- จำนวนผู้รับ: "0 / 3,200"
- ปุ่ม "Delete" → ลบ broadcast → กลับไปหน้า list

### AC6: Status: Sent with error
**GIVEN** broadcast status = "Sent with error"
**THEN** แสดง:
- วันและเวลาที่ส่ง
- จำนวนผู้รับ: "ส่งสำเร็จ: 3,125 / 3,200"
- ปุ่ม "Delete" → ลบ broadcast → กลับไปหน้า list

### AC7: Status: Draft
**GIVEN** broadcast status = "Draft"
**THEN** แสดง:
- เป้าหมาย (estimated count)
- จำนวนผู้รับ: "~400 คน"
- ปุ่ม "Continue Edit" → ไปหน้า Create/Edit form สามารถแก้ไขต่อได้
- ปุ่ม "Delete" → ลบ broadcast → กลับไปหน้า list

### AC8: Status: Sending
**GIVEN** broadcast status = "Sending"
**WHEN** user กดเข้า detail page
**THEN** แสดง:
- Status badge: "กำลังส่ง"
- ชื่อ LINE OA, Target audience, Message content (read-only)
- ไม่มีปุ่ม action ใดๆ (Edit, Delete, Retry ซ่อนทั้งหมด)

AND status badge อัปเดตอัตโนมัติเมื่อส่งเสร็จโดยไม่ต้อง refresh หน้า

### AC9: ปุ่มกลับ
**GIVEN** user กด ปุ่มกลับ (←)
**THEN**:
- กลับไปหน้า Broadcast List
- เก็บ filter/tab state (ถ้า user อยู่ tab "Sent" จะกลับไปที่ tab "Sent")

### AC10: Message content
**GIVEN** หน้า Broadcast Detail (ทุก status)
**WHEN** แสดง
**THEN** แสดง section "ข้อความ" พร้อม message bubbles ที่ถูกส่ง/ตั้งค่าไว้ทั้งหมด ตามลำดับ:
- Text message → แสดงข้อความ
- Image message → แสดง image preview

AND message bubbles เป็น read-only (ไม่สามารถแก้ไขได้)

### AC11: Agent role - read-only mode
**GIVEN** user role = Agent
**WHEN** Agent in broadcast detail
**THEN** all actions are disabled — Agent can only view the detail
