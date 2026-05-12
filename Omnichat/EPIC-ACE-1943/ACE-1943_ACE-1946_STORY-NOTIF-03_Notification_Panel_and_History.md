# STORY-NOTIF-03: Notification Panel & History

**Status:** Backlog | **ClickUp:** [ACE-1946](https://app.clickup.com/t/86d2u4au8) | **Epic:** [ACE-1943](https://app.clickup.com/t/86d2u3v89)

## User Story

As a logged-in user
I want to open a notification panel and browse notification history, mark items as read, and navigate to the relevant conversation
so that I can see what happened, act on it, and clear my backlog efficiently.

## Detail / Description

Frontend story build notification panel ที่เปิดเมื่อ click bell (NOTIF-02) ทุก notification item ใช้ design pattern จาก Epic Overview

**Panel anatomy:**
- Header: "การแจ้งเตือน" + "อ่านทั้งหมด" button
- List: notification items เรียงจากใหม่ไปเก่า
- Empty state: icon + "ไม่มีการแจ้งเตือน"
- Footer / Infinite scroll: load more เมื่อ scroll ถึงด้านล่าง

**Notification item components (ตาม pattern ใน Overview):**
- Event icon (วงกลม colored ตาม event group)
- Text: actor + verb + object + channel badge
- Time: relative time
- Unread dot: จุดแดง ถ้า `is_read = false`
- Background: unread = พื้นแดงอ่อน? | read = ขาว (ถาม Art)
- SLA notifications: border-left สีแดง

**Mention deletion graceful handling:**
- ลบ @mention ออก → click notification → ไปที่ note (ไม่มี mention แล้วแต่ไม่ error)
- ลบ note ทั้งอัน → click → toast "โน้ตนี้ถูกลบแล้ว" อยู่ที่เดิม
- ลบ conversation → click → toast "Conversation นี้ไม่พบ" อยู่ที่ inbox (edge case)

**Scope of this story:**
- Panel เปิด/ปิดเมื่อ click bell
- Notification list: items ตาม design pattern พร้อม read/unread state
- Click notification item → navigate ไป conversation + mark as read
- "อ่านทั้งหมด" button → mark all as read → badge หาย
- Infinite scroll / load more (max 50 items ต่อ page, history 30 วัน)
- Empty state
- Close panel เมื่อ click นอก panel
- Graceful handling เมื่อ destination (note/conversation) ไม่มีแล้ว

## Acceptance Criteria

### Notification panel opens and closes when bell is clicked
**Given** the user clicks the bell icon  
**When** the click is registered  
**Then** the notification panel opens below the bell icon  
**And** clicking anywhere outside the panel closes it  
**And** clicking the bell again also toggles the panel closed

### Notification items display correct information per design pattern
**When** the panel renders notification items  
**Then** each item shows: event icon, actor name, verb + object, channel badge, relative time  
**And** unread items have a visual distinction: unread dot and highlighted background  
**And** SLA notifications (`sla_due_soon`, `sla_breached`) have a red left border  
**And** read items show plain white background with no dot

### Clicking a notification navigates to conversation and marks it as read
**Given** the panel is open and there are unread notifications  
**When** the user clicks a notification item  
**Then** the app navigates to the relevant conversation  
**And** the notification is immediately marked as read (`is_read = true`)  
**And** the unread badge count decrements by 1  
**And** the panel closes

### "อ่านทั้งหมด" marks all notifications as read at once
**Given** the panel has multiple unread notifications  
**When** the user clicks "อ่านทั้งหมด"  
**Then** all notifications change to read state  
**And** the unread dot disappears from all items  
**And** the bell badge disappears

### Older notifications load when scrolling to bottom
**Given** the panel is open and the user has more than 50 notifications  
**When** the user scrolls to the bottom of the panel  
**Then** the next page of older notifications loads  
**And** a loading indicator appears briefly during the fetch  
**And** older notifications append below the current list

### Empty state shown when there are no notifications
**Given** the user has no notifications at all  
**When** the panel opens  
**Then** an empty state with an icon and "ไม่มีการแจ้งเตือน" is shown

### Graceful handling when notification destination is deleted
**Given** a mention notification exists but the original note has been deleted  
**When** the user clicks the mention notification  
**Then** a toast message appears: "โน้ตนี้ถูกลบแล้ว"  
**And** the user stays on the current page (no navigation occurs)  
**And** the notification is still marked as read

**Given** a conversation notification exists but the conversation has been deleted  
**When** the user clicks the notification  
**Then** a toast message appears: "Conversation นี้ไม่พบ"  
**And** the user stays on the inbox

### Relative time displays correctly per format table
**Given** a notification was created 30 seconds ago → shows "เมื่อสักครู่"  
**Given** a notification was created 5 minutes ago → shows "5 นาทีที่ผ่านมา"  
**Given** a notification was created yesterday at 14:22 → shows "เมื่อวาน 14:22 น."

## Technical Notes

**Dependencies:**
- NOTIF-01: `GET /notifications` API (paginated, sorted by `created_at` desc)
- NOTIF-01: `PATCH /notifications/:id/read` และ `PATCH /notifications/read-all`
- NOTIF-02: bell icon ต้องมีก่อนเพื่อ hook panel open/close
- Router: navigate ไป conversation ต้องไม่ full page reload

**Special focus:**
- Panel position: dropdown anchored ใต้ bell icon, z-index สูงกว่า content
- Infinite scroll: ใช้ Intersection Observer บน sentinel element ด้านล่าง
- Optimistic mark-as-read: update `is_read` ใน local state ก่อน API return
- Destination check: ก่อน navigate ไม่ต้อง pre-check, handle error หลัง navigate แล้ว 404
- Panel ต้อง re-fetch ทุกครั้งที่เปิด หรือ sync กับ WebSocket events ที่เกิดขณะ panel ปิด

## QA / Test Considerations

**Primary flows:**
- Click bell → panel open → items ถูกต้อง
- Click notification → navigate → mark read → badge -1
- Mark all → badge หาย
- Scroll bottom → load more

**Edge Cases:**
- Note deleted → click → toast ไม่ crash
- Conversation deleted → toast
- 0 notifications → empty state
- Panel เปิดระหว่าง WebSocket push → item ใหม่ปรากฏทันที

**Business-Critical Must Not Break:**
- Navigation ต้องทำงานทุก notification type
- Graceful handling ห้าม crash
- Mark read ต้อง sync badge ถูกต้อง

**Test Types:**
- UI tests: panel open/close, item rendering
- Navigation tests: ทุก event type
- Graceful tests: deleted destination
- Infinite scroll tests
- Mark read / mark all read tests
