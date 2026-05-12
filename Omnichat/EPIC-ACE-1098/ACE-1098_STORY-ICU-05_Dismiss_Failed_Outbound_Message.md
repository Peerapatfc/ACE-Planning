# STORY-ICU-05: Dismiss Failed Outbound Message
**ID:** ACE-1935
**Status:** To Do
**ClickUp:** [ACE-1935](https://app.clickup.com/t/86d2tp3zy)
**Epic:** [ACE-1098 EPIC-A2.1: Inbox core UI](https://app.clickup.com/t/86d23yw04)

**Description (User Story):**
> As a Support Agent
> I want to dismiss (delete) a failed outbound message from the inbox timeline
> so that I can clean up noise from failed attempts I no longer intend to retry,
> without affecting the customer's conversation on the platform.

## Detail / Description

การ์ดนี้คือการลบ outbound message ที่อยู่ในสถานะ failed เท่านั้น ออกจาก timeline ใน inbox

- ขอบเขตของ delete ในการ์ดนี้คือ **local delete เท่านั้น** เนื่องจาก message ที่ failed ไม่เคยถูกส่งถึงลูกค้า จึงไม่มีความจำเป็นต้องเรียก platform API เพื่อลบฝั่งลูกค้า
- การลบควรทำให้ timeline สะอาดขึ้น โดยไม่กระทบ message อื่นใน conversation และต้องมี confirmation ก่อนลบเพื่อป้องกัน accidental delete

> **หมายเหตุ:** ไม่รองรับ delete message ที่ sent หรือ delivered เพราะต้องใช้ platform-level delete API ซึ่งแต่ละ channel มี policy และ time window ต่างกัน (LINE ไม่รองรับ unsend จาก business, Meta มี time limit)

## Scope

| In Scope | Out of Scope |
|---|---|
| Dismiss / Delete action บน failed outbound message เท่านั้น | Platform-side delete (LINE, Meta, WhatsApp) |
| Local delete: ลบ record ออกจาก timeline ใน system ของเรา | Delete message ที่ status เป็น sent / delivered / sending / retrying |
| Confirmation dialog ก่อนลบเพื่อป้องกัน accidental delete | Bulk delete หลาย failed messages พร้อมกัน |
| ลบแล้ว message bubble หายออกจาก timeline ทันที | Restore / undo หลังจากลบแล้ว |
| Audit log บันทึก agent_id, message_id, deleted_at | Auto-delete failed messages ตาม policy |
| | Delete message ที่ไม่ใช่ outbound (inbound messages) |

## Acceptance Criteria

### Delete action appears only on failed outbound messages
**Given** an outbound message has status "failed" in the timeline  
**When** the agent views the conversation  
**Then** a "Delete" action appears on that message bubble  
**And** messages with status sending / sent / delivered do NOT show the Delete action

### Confirmation required before delete
**Given** the agent clicks Delete on a failed outbound message  
**When** the delete action is triggered  
**Then** a confirmation dialog appears: "Remove this failed message from the timeline? This cannot be undone."  
**And** Cancel returns to the timeline without any change  
**And** Confirm proceeds with the deletion

### Delete is only local soft-delete
**Given** the agent confirms deletion of a failed outbound message  
**When** the delete operation executes  
**Then** the message is soft-deleted from the agent's timeline view  
**And** NO call is made to LINE / Meta / Marketplace platform API  
**And** the outbound message record is marked as `dismissed` in our database  
**And** the message does not reappear after page refresh

### Timeline robustness after delete
**Given** a failed outbound message is deleted  
**When** the agent views the conversation  
**Then** the deleted message no longer appears in the timeline  
**And** all other messages in the conversation are unaffected  
**And** conversation context and reply history remain intact  
**And** no "deleted message" placeholder is shown (unlike sent messages)

### Only delete failed message with no provider_message_id
**Given** a failed outbound message has no `provider_message_id` (never reached platform)  
**When** the agent confirms deletion  
**Then** the system allows the deletion  
**And** if a failed message somehow has a `provider_message_id` (partial failure edge case)  
**Then** the system blocks delete or requires elevated confirmation and logs for review

### Audit trail always recorded
**Given** an agent deletes a failed outbound message  
**When** the deletion succeeds  
**Then** the system logs: `agent_id`, `message_id`, `conversation_id`, `deleted_at`, `reason="agent_dismiss"`  
**And** this log is accessible to admins for audit purposes  
**And** the log is NOT shown in the agent-facing timeline

## UI/UX Notes

- แสดง trash icon / "Remove" ใน context menu (3 dots) ของ failed outbound bubble เท่านั้น (ถาม art ดูว่าจะให้แสดงแบบไหน)
- ไม่แสดง delete action บน sent/delivered messages เพื่อป้องกัน confusion
- Confirmation dialog ควรระบุชัดว่า: "นี่คือการลบออกจาก timeline ของเราเท่านั้น ลูกค้าไม่ได้รับข้อความนี้อยู่แล้วเพราะการส่งล้มเหลว"
- หลังลบ ไม่ต้องมี "deleted message" placeholder ให้ลบออกไปเลยเพราะลูกค้าไม่เคยเห็น
- Retry และ Delete action ควรอยู่ใน context menu เดียวกัน ให้ agent ตัดสินใจได้ว่าจะ retry หรือ dismiss
- ไม่ควรมี loading state ที่ยาวนาน

## Technical Notes

**Data:**
- Soft delete: เพิ่ม `deleted_at` และ `deleted_by` column บน `outbound_messages` table
- Status จะเปลี่ยนเป็น `dismissed` แทนที่จะ hard delete เพื่อ audit trail
- Timeline query ต้อง filter out `dismissed` status
- Audit log: บันทึก `agent_id`, `message_id`, `conversation_id`, `deleted_at`

**Integrations:** ไม่มี integration กับ LINE / Meta / WhatsApp สำหรับ story นี้ (local delete only)

**Dependencies:**
- STORY-ICU-04 (Retry failed outbound message): Retry และ Delete share UX บน failed message bubble
- `outbound_messages` table ต้องรองรับ `deleted_at`, `deleted_by`, `status = dismissed`

**Special Focus:**
- ต้องไม่แสดง Delete บน message ที่ไม่ใช่ status `failed`
- ต้องไม่เรียก platform API โดยไม่จำเป็น
- ต้องใช้ tenant isolation: agent ลบได้เฉพาะ message ใน tenant ของตัวเอง
- UX ต้องสื่อสารชัดเจนว่า local delete ≠ unsend บน platform

## QA / Test Considerations

**Primary Flows:**
- Delete failed message บน LINE, FB, IG และตรวจสอบว่า message หายจาก timeline ของเราเอง
- ยืนยันว่าไม่มี API call ไปหา platform (network log should be clean)
- Delete แล้วถ้า refresh page message ต้องไม่กลับมา
- Audit log ถูก record ถูกต้อง (agent_id, message_id, timestamp)
- Retry และ Delete action แสดงร่วมกันใน context menu อย่างถูกต้อง

**Edge Cases:**
- ลบ failed message ที่ conversation ถูก archive/close แล้ว
- Rapid double click Confirm ต้องไม่ delete สองครั้ง (monkey test)
- ถ้าส่งข้อความไปแล้วโชว์ในฝั่ง platform แต่ฝั่งเราขึ้นว่า fail to sent message ต้องจัดการ gracefully
- Delete แล้ว agent อีกคนเปิด conversation เดิม ต้องไม่เห็น message นั้น

**Business-Critical Must Not Break:**
- ต้องไม่ลบ message ที่ส่งสำเร็จออกจาก timeline
- ต้องไม่เรียก platform API โดยไม่จำเป็น
- ต้องไม่ซ่อน error context จาก audit trail
- ต้องไม่อนุญาตให้ลบ message ของ tenant อื่น

**Test Types:**
- Unit tests: delete permission guard and status validation
- Integration tests: soft delete updates database correctly
- UI tests: delete button visibility, confirmation dialog, timeline update
- Security tests: tenant isolation, permission enforcement
- Network tests: no platform API calls during local delete
