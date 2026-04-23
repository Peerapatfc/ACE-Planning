# STORY-SET-03: Members & Roles Page + Edit User + Work Shift

**ID:** ACE-1616 | **Status:** To Do | **Points:** 6  
**Sprint:** Sprint 4 (4/13 - 4/26)  
**URL:** https://app.clickup.com/t/86d2hd9kp  
**Depends on:** SET-01, SET-02, RBAC-02, RBAC-01

## User Story

As a Workspace Admin  
I want a complete Members & Roles management page with the ability to edit user details and configure individual work shifts  
so that I can see who is on my team, what hours they work, and manage their access and schedules from one place.

## Description

Build หน้า `Settings > Members & Roles` ที่สมบูรณ์ โดยใช้ API จาก RBAC-02  
เพิ่ม Edit User modal ที่มีข้อมูลครบถ้วน รวมถึง Work Shift config ของแต่ละ user

### Member List Columns

| Column | ข้อมูล | Editable | Note |
|--------|--------|----------|------|
| ชื่อ | Full name + avatar | ผ่าน Edit modal | |
| Email | Email address | ❌ read-only | |
| Role | Badge (Admin/Supervisor/Agent) | ผ่าน Edit modal | ไม่มี inline dropdown |
| Work shift | "จ-ศ 09-18" หรือ "Same as BH" | ผ่าน Edit modal | summary read-only |
| Last active | relative time เช่น "2h ที่แล้ว" | ❌ | |
| Actions | Edit button | | Remove อยู่ใน Edit modal |

### Edit User Modal — Section A: User Information
- Full Name (editable)
- Email (read-only — แสดงแต่ไม่ให้แก้ไข)
- Role (dropdown Admin/Supervisor/Agent — ต้องผ่าน Admin protection rules)

### Edit User Modal — Section B: User's Work Shift
- "Same as business hours" toggle:
  - ON: ใช้ค่าจาก SET-02 เลย ไม่ต้อง config เพิ่ม
  - OFF: แสดง per-day schedule เหมือน SET-02 (toggle วัน + time range + add shift)
- "Copy times to all" shortcut
- Remove member button ด้านล่าง modal (มี confirm dialog)

> **Note:** `team_id` field บน `workspace_members` table ต้องมีตั้งแต่ตอนนี้ (nullable) เพื่อรองรับ Teams ใน R2

## Scope

- Member list page: columns ตาม table ด้านบน
- Pending invitations section (ใช้ data จาก RBAC-02)
- Invite member button → invite modal (อยู่ใน RBAC-02 แล้ว)
- Edit User modal: Section A + Section B
- Work shift toggle + per-day schedule
- Remove member จาก Edit modal พร้อม confirm dialog
- **ไม่รวม:** Teams feature (R2)

## Acceptance Criteria

### Member list shows all active members with required columns
- Name (avatar), Email, Role, Work shift summary, Last active, Edit button
- Role: read-only badge — no inline dropdown

### Work shift summary reflects current setting
- "Same as BH" → shows "Same as BH" label
- Custom shift Mon-Fri 09:00–18:00 → shows "จ-ศ 09:00-18:00"

### Edit User modal opens with pre-filled data
- Shows current Full Name (editable), Email (read-only), Role (dropdown)
- Work shift shows current config — no blank fields

### Admin can update Full Name and Role
- Change name + role → Save → list updates immediately
- Role change violates Admin protection → blocking error shown

### Email in Edit modal is read-only
- Visually distinct (disabled/lock icon)
- Typing has no effect
- Save never updates email

### "Same as business hours" toggle
- ON → per-day inputs hidden, preview shows BH schedule from SET-02
- Saved as `same_as_business_hours` flag — if BH changes, user's effective shift updates automatically

### Custom work shift per user
- OFF → per-day inputs appear
- Set independently per day
- "Copy times to all" applies current row's time to all active days
- Saved independently from BH changes

### Remove member requires confirmation
- Click Remove → confirm dialog with warning
- Confirm → member removed, access revoked, disappears from list
- Cancel → nothing changes, modal stays open

### Pending invitations section
- Shows Email, Role, Sent date, Expiry status, Resend/Cancel buttons
- Expired invitations visually distinct

### Schema includes team_id for R2 readiness
- `workspace_members` record includes `team_id` (nullable, defaults null)
- UI does not display `team_id` in MVP

### Non-Admin roles cannot access Members & Roles
- Supervisor/Agent → route guard redirects, page does not render

## UI/UX Notes

- Member list: table layout
- Work shift column: short text — "Same as BH", "จ-ศ 09-18", "จ-อา 08-20", "ไม่ได้ตั้ง"
- Edit User modal: 2 sections with clear divider
- Email field: disabled styling or lock icon (confirm with Art)
- "Same as BH" toggle ON → show preview schedule below toggle
- Remove member: ด้านล่างสุดของ modal แยกจาก Save ชัดเจน
- Confirm dialog: mention ผลกระทบของ removal

## Technical Notes

**Dependencies:**
- SET-01 Settings shell
- SET-02 Business Hours API (for "Same as BH" toggle)
- RBAC-02 member management APIs (invite, change role, remove)
- RBAC-01 Admin protection rules (enforced at backend)

**Special focus:**
- `workspace_members` table: must have `team_id` column (nullable FK to teams) from MVP
- `user_work_shifts` table: `user_id, workspace_id, same_as_business_hours (boolean), shifts (JSON array), created_at, updated_at`
- "Same as BH": store `same_as_business_hours=true` flag — do NOT copy values (auto-updates when BH changes)
- Email read-only: enforced at API layer — `PATCH /members/:id` must not accept `email` field
- Role change → call RBAC-02 API (no new API)

## QA / Test Considerations

**Primary flows:**
- Edit modal → แก้ชื่อ + เปลี่ยน role → save → list update ถูกต้อง
- Enable "Same as BH" → save → work shift column shows "Same as BH"
- Set custom work shift Mon-Fri 09-18 → save → summary แสดงถูกต้อง
- Remove member → confirm → member หายจาก list
- BH update ใน SET-02 → member ที่ใช้ Same as BH → effective shift updates

**Edge Cases:**
- Email field: พยายาม type → ไม่มีผล
- Change role ของ Admin คนเดียว → Admin protection error
- BH ไม่ได้ตั้งค่าใน SET-02 → "Same as BH" toggle should show warning or default
- Member ถูก remove → sessions revoke
- Custom shift overlap (shift 1: 09-13, shift 2: 12-18) → validate

**Business-Critical Must Not Break:**
- Email ต้องไม่แก้ไขได้ทั้ง frontend และ API
- `team_id` field ต้องมีใน schema ตั้งแต่ MVP
- Admin protection ต้องทำงานใน Edit modal เช่นเดียวกับ direct API call

**Test Types:**
- UI tests: member list columns, Edit modal open/close/save
- API tests: `PATCH /members/:id` verify email ไม่เปลี่ยน
- Schema test: `team_id` field มีอยู่ใน `workspace_members`
- Work shift tests: same_as_BH vs custom, reads BH correctly
- Admin protection: role change last admin → error

## Subtasks

| ID | Name | Points |
|----|------|--------|
| ACE-1628 | Modify member list page | 1 |
| ACE-1690 | Build edit member role and business hours | - |
| ACE-1686 | Design/build api | - |
| ACE-1687 | Diagrams | - |
| ACE-1688 | API Table | - |
