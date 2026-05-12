# STORY-NOTIF-02: Bell Icon & Unread Badge

**Status:** Backlog | **ClickUp:** [ACE-1945](https://app.clickup.com/t/86d2u4akj) | **Epic:** [ACE-1943](https://app.clickup.com/t/86d2u3v89)

## User Story

As a logged-in user
I want to see a notification bell with an unread count badge in the navigation bar
so that I always know at a glance whether I have unread notifications without opening anything.

## Detail / Description

Pure frontend story build bell icon บน top navigation ที่ update real-time ผ่าน WebSocket จาก NOTIF-01

**Scope of this story:**
- Bell icon: อยู่บน top navigation bar ฝั่งขวา เห็นทุกหน้า ข้างๆ profile icon
- Unread badge: แสดง count ของ notifications ที่ยังไม่อ่าน
- Badge format: ตัวเลข 1–99, "99+" ถ้าเกิน 99, ไม่แสดงเลยถ้า count = 0
- Real-time update: badge increment ทันทีเมื่อ notification ใหม่เข้าผ่าน WebSocket
- Click bell: เปิด/ปิด notification panel (implement ใน NOTIF-03)
- ไม่รวม notification panel content (อยู่ใน NOTIF-03)

## Acceptance Criteria

### Bell icon visible in navigation bar for all logged-in users
**Given** any logged-in user on any page  
**When** the top navigation renders  
**Then** the bell icon is visible on the right side of the navigation bar  
**And** it is accessible from every page without scrolling

### Unread badge shows correct count on initial load
**Given** a user logs in and has 5 unread notifications  
**When** the page first loads  
**Then** the bell shows a badge with number "5"  
**And** the count is fetched from `GET /notifications?unread=true` at page load

### Badge increments in real-time when new notification arrives
**Given** a user has 3 unread notifications and the badge shows "3"  
**When** a new notification arrives via WebSocket  
**Then** the badge increments to "4" immediately without page refresh

### Badge shows 99+ when unread count exceeds 99
**Given** a user has 120 unread notifications  
**When** the badge renders  
**Then** it shows "99+" not "120"

### Badge disappears when all notifications marked as read
**Given** a user has unread notifications  
**When** they mark all notifications as read  
**Then** the badge disappears from the bell icon  
**And** no count is shown (not even "0")

### Bell icon has active visual state when panel is open
**Given** the user clicks the bell icon to open the notification panel  
**When** the panel is open  
**Then** the bell icon shows a visual active state (e.g. filled or highlighted)  
**And** when the panel closes, the bell returns to its default state

## Technical Notes

**Dependencies:**
- NOTIF-01: WebSocket channel และ `GET /notifications?unread=true` API

**Special focus:**
- Badge count ต้อง sync กับ WebSocket อย่า rely on polling อย่างเดียว
- Optimistic update: mark all as read → badge หายทันที ก่อน API response กลับมา

## QA / Test Considerations

**Primary flows:**
- Login → badge แสดง unread count ถูกต้อง
- New notification via WebSocket → badge increment real-time

**Edge Cases:**
- 0 unread → no badge
- 120 unread → "99+"
- WebSocket disconnect → badge ไม่ stale หลัง reconnect

**Business-Critical Must Not Break:**
- Badge count ต้องไม่แสดงค่าผิด

**Test Types:**
- Unit tests: badge component
- Real-time tests: WebSocket event → badge update
- Boundary tests: 99 vs 100 vs 120
