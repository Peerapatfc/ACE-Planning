# STORY-BC-01: Create and Edit Broadcast

**Status:** To Do | **ClickUp:** [ACE-2294](https://app.clickup.com/t/86d32c7k4) | **Epic:** [ACE-2236](https://app.clickup.com/t/86d318wjb)

## Overview

การทำงาน:
- สร้างทุกอย่างในหน้าเดียว (single page form)
- เลือก LINE OA → กำหนดเวลาส่ง → เลือก audience → เขียนข้อความ
- แสดง preview แบบ LINE ด้านขวา (real-time)
- กด + เพื่อเพิ่ม message (สูงสุด 5)
- Required fields ขึ้นสีแดงเมื่อพยายามส่งแต่กรอกไม่ครบ

## Acceptance Criteria

### AC1: Select LINE OA account (Required)
**GIVEN** Admin opens "Create Broadcast" page
**WHEN** page loads
**THEN** shows dropdown section "Select which LINE account to send from*" (with red asterisk)
AND shows option with all connected LINE OAs:
- LINE OA avatar
- LINE OA name
- Friend count (if available)
- A-Z sorted

**WHEN** Admin selects LINE OA → selection is saved

**WHEN** no LINE OA connected → shows empty state

### AC2: Broadcast time (Send now or Schedule)
**GIVEN** Admin is creating broadcast
**WHEN** they see "Broadcast time" section
**THEN** shows 2 options:
- Send now (default selected)
- Set schedule

**WHEN** "Send now" selected → broadcast will send immediately upon clicking "Send"

**WHEN** "Set schedule" selected
**THEN** shows date/time picker:
- Date selector
- Time selector (HH:MM)
- Timezone display: Asia/Bangkok (GMT+7)
- UI ไม่อนุญาตให้เลือกวันและเวลาที่น้อยกว่าปัจจุบัน (disable past dates/times ใน picker)
- Note: การ validate เวลาขั้นสุดท้ายเกิดขึ้นตอนกด Send (server-side)

### AC2.1: Scheduled Auto-execution
**GIVEN** broadcast status = "Scheduled" AND ถึงวันเวลาที่ตั้งไว้แล้ว
**WHEN** ระบบตรวจสอบเวลา (server-side)
**THEN** trigger การส่งอัตโนมัติ AND ดำเนินการตาม flow เดียวกับ "Send now" ทุกขั้นตอน

Note: Scheduled execution เป็น background process — ไม่มี confirmation dialog และไม่มี UI progress สำหรับ scheduled broadcast ใน Phase 1 user จะเห็น status update ใน broadcast list เท่านั้น

### AC3: Choose broadcast targeting
**GIVEN** Admin sees "Choose broadcast targeting" section
**WHEN** section loads
**THEN** shows 2 radio options:
- Send to everyone (default)
- Send to specific people

**WHEN** "Send to everyone" selected → shows target estimate: "100%" badge + "Send to approximately 18 recipients"

**WHEN** "Send to specific people" selected → enables tag selection (from BC-02) AND updates target estimate based on selected tags

### AC4: Broadcast name
**GIVEN** Admin sees broadcast name input
**WHEN** they type name
**THEN** accepts up to 20 characters AND shows character counter: "15 / 20"

**WHEN** name exceeds 20 characters → prevents typing more AND shows "20 / 20"

**WHEN** Admin clicks to proceed AND name is empty → name field border turns RED AND shows error: "กรุณาใส่ชื่อ Broadcast"

Note: can be duplicate with other broadcast

### AC5: Empty state on load
**GIVEN** Admin creates new broadcast
**WHEN** message section loads
**THEN** [+] button (enabled), no message bubbles displayed

**WHEN** Admin clicks [+] for the first time
**THEN** shows message type selector: [ข้อความ] Text | [รูปภาพ] Image
**WHEN** Admin selects type → creates first message bubble AND updates header: "ข้อความ (1/1)"

### AC6: Add new message bubble
**GIVEN** Admin has 0-4 message bubbles
**WHEN** they click [+ เพิ่มข้อความ] button
**THEN** shows message type selector popup: [ข้อความ] Text | [รูปภาพ] Image
**WHEN** Admin selects type → adds new empty bubble AND increments counter: "ข้อความ (2/5)" AND [+ เพิ่มข้อความ] remains visible if < 5 messages

### AC8: Hide add button at maximum
**GIVEN** Admin has added messages
**WHEN** message count reaches 5 → [+] button is HIDDEN AND counter shows "ข้อความ (5/5)"
**WHEN** Admin removes a message AND count becomes < 5 → [+ เพิ่มข้อความ] button appears again

### AC9: Text message type
**GIVEN** text message bubble is active
**WHEN** Admin types message → character counter updates: "245/500"
AND allows emoji input (emoji counts toward character limit)
**WHEN** text reaches 500 characters → prevents typing more

**WHEN** Admin clicks emoji button → shows emoji picker popup

**WHEN** Admin clicks to proceed AND text is empty → text area border turns RED AND shows error: "กรุณากรอกข้อความ"

### AC10: Image message type
**GIVEN** image message bubble is active
**WHEN** bubble loads → shows image upload area:
- Dashed border box
- "Click to upload" or drag-and-drop
- "JPEG or PNG, max 10MB"

**WHEN** Admin uploads valid image (JPEG/PNG < 10MB)
**THEN** shows image preview AND displays image size: "2.3 MB" AND shows [Change Image] button

**WHEN** Admin uploads file > 10MB → shows error: "ไฟล์ใหญ่เกินไป (สูงสุด 10MB)"
**WHEN** Admin uploads unsupported format → shows error: "รองรับเฉพาะ JPEG และ PNG"
**WHEN** Admin clicks to proceed AND image not uploaded → upload area border RED AND error: "กรุณาอัปโหลดรูปภาพ"

### AC11: Remove message bubble
**GIVEN** Admin has messages (1-5)
**WHEN** they click [x] on a message bubble
**THEN** shows confirmation modal: "ลบข้อความนี้?"
- Message: "คุณต้องการลบข้อความนี้ใช่หรือไม่"
- Actions: [ยกเลิก] [ลบ]

**WHEN** Admin clicks [ลบ] → removes that bubble AND updates counter AND re-enables [+ เพิ่มข้อความ] if was hidden

Note: ไม่มี minimum message count — Admin สามารถลบจนเหลือ 0 messages ได้ ระบบจะ validate ตอนกด Send แทน

### AC12: Message order and arrangement
**GIVEN** Admin has multiple messages
**WHEN** Admin wants to reorder → can drag-and-drop OR use up/down arrow buttons
**WHEN** order changes → counter updates to reflect new positions

### AC13: Live preview (RIGHT SIDE)
**GIVEN** Admin is creating/editing broadcast
**WHEN** making any changes
**THEN** right panel shows:
- Header: "Preview"
- LINE-style message preview (real-time updates)
- All messages rendered as they will appear in LINE

### AC14: Save as draft
**GIVEN** Admin is creating broadcast
**WHEN** they click "save draft" button
**THEN** saves broadcast with status = "draft" AND saves all current data:
- LINE OA selection, Schedule setting, Targeting setting, Broadcast name, All messages (text, images), Message order
- ผู้สร้าง, ผู้แก้ไขล่าสุด, วันที่แก้ไขล่าสุด

**WHEN** draft saved successfully → shows toast: "บันทึกแบบร่างแล้ว" AND redirects to broadcast list

Note: Draft save does soft validation (allows incomplete data)

### AC15: Load and edit draft
**GIVEN** Admin opens existing draft
**WHEN** draft loads → restores all saved data
**WHEN** Admin makes changes → can save again or proceed
