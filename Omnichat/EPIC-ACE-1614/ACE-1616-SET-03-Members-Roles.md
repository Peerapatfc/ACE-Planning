# STORY-SET-03: Members & Roles Page + Edit User + Work Shift

**ID:** ACE-1616 | **Status:** In Progress | **Points:** 6 | **Sprint:** Sprint 4 (4/13 - 4/26)  
**Assignee:** griangsak | **URL:** https://app.clickup.com/t/86d2hd9kp  
**Parent:** [ACE-1614 EPIC](ACE-1614-EPIC-Settings-Configuration.md)

## User Story

> As a Workspace Admin  
> I want a complete Members & Roles management page with the ability to edit user details and configure individual work shifts  
> so that I can see who is on my team, what hours they work, and manage their access and schedules from one place.

## Description

Build หน้า `Settings > Members & Roles` ที่สมบูรณ์ โดยใช้ API จาก RBAC-02  
เพิ่ม Edit User modal ที่มีข้อมูลครบถ้วน รวมถึง Work Shift config ของแต่ละ user

## Member List Columns

| Column | ข้อมูลที่แสดง | Editable | Note |
|--------|-------------|---------|------|
| ชื่อ | Full name + avatar | ผ่าน Edit modal | |
| Email | Email address | ไม่ได้ (read-only) | |
| Role | Badge (Admin/Supervisor/Agent) | ผ่าน Edit modal | ไม่มี inline dropdown |
| Work shift | "จ-ศ 09-18" หรือ "Same as BH" | ผ่าน Edit modal | summary แบบ read-only |
| Last active | relative time เช่น "2h ที่แล้ว" | ไม่ได้ | |
| Actions | Edit button | | Remove อยู่ใน Edit modal |

## Edit User Modal Sections

**Section A: User Information**
- Full Name (editable)
- Email (read-only — แสดงแต่ไม่ให้แก้ไข)
- Role (dropdown Admin/Supervisor/Agent — ต้องผ่าน Admin protection rules)

**Section B: User's Work Shift**
- "Same as business hours" toggle
  - เปิด: ใช้ค่าจาก SET-02 เลย ไม่ต้อง config เพิ่ม
  - ปิด: แสดง per-day schedule เหมือน SET-02 Business Hours (toggle วัน + time range + add shift)
- "Copy times to all" shortcut
- Remove member button ด้านล่าง modal (มี confirm dialog)

> **Note:** `team_id` field บน `workspace_members` table ต้องมีตั้งแต่ตอนนี้ (nullable) เพื่อรองรับ Teams ใน R2  
> `user_work_shifts` table ควรรองรับ team assignment ได้ในอนาคต

## Scope

- Member list page: columns ตาม table ด้านบน
- Pending invitations section (ใช้ data จาก RBAC-02)
- Invite member button: เปิด invite modal (อยู่ใน RBAC-02 แล้ว)
- Edit User modal: Section A (name, email read-only, role) + Section B (work shift)
- Work shift toggle + per-day schedule
- Remove member จาก Edit modal พร้อม confirm dialog
- ไม่รวม Teams feature (R2)

## Acceptance Criteria

**Member list shows all active members**
- Then: list shows Name (with avatar), Email, Role, Work shift summary, Last active, Edit button
- And: Role shows as read-only badge — no inline dropdown

**Work shift summary reflects current setting**
- "Same as business hours" → shows "Same as BH"
- Custom (Mon-Fri 09:00-18:00) → shows readable summary "จ-ศ 09:00-18:00"

**Edit User modal opens with pre-filled data**
- When: Admin clicks Edit on member row
- Then: modal shows current Full Name (editable), Email (read-only), Role (dropdown)
- And: Work shift section shows current config, no fields blank

**Admin can update Full Name and Role**
- When: change Full Name + select new Role → Save
- Then: member record updated, list reflects new name and role badge immediately
- And: if role change violates Admin protection rules → blocking error shown

**Email is read-only in Edit modal**
- Then: field visually distinct as read-only (disabled styling or lock icon)
- And: clicking/typing has no effect, Save never updates email

**"Same as business hours" toggle**
- When: toggle on
- Then: per-day inputs hidden, preview summary shows current business hours from SET-02
- When saved: user's work shift marked as `same_as_business_hours`
- And: if Business Hours change later, this user's effective shift updates automatically

**Custom work shift per user**
- When: toggle off
- Then: per-day schedule inputs appear, Admin can toggle days and set time ranges independently
- "Copy times to all" applies current row's time to all active days
- When saved: custom shift independent of Business Hours changes

**Remove member requires confirmation**
- When: click Remove member → confirmation dialog with warning appears
- When confirmed: member removed, access revoked immediately, disappears from list
- When cancelled: nothing changes, Edit modal remains open

**Pending invitations section**
- Shows: Email, Role, Sent date, Expiry status, Resend/Cancel buttons
- Expired invitations visually distinct from active pending ones

**Schema includes team_id for R2 readiness**
- `workspace_members` table includes `team_id` field (nullable, defaults to null)
- UI does not display `team_id` in MVP — schema-only preparation

**Members & Roles inaccessible to non-Admin**
- Supervisor or Agent attempts to navigate to `Settings > Members & Roles` → redirected by route guard

## UI/UX Notes

- Member list: table layout
- Work shift column: short summary text — "Same as BH", "จ-ศ 09-18", "จ-อา 08-20", "ไม่ได้ตั้ง"
- Edit button: text button หรือ icon ด้านขวาของ row
- Edit User modal: 2 sections ชัดเจน "User information" + "User's work shift" แยก divider
- Email field: disabled styling หรือ background สีต่าง หรือ lock icon (waiting for Art confirm)
- Role dropdown ใน modal: แสดง role ปัจจุบัน + allow change (enforce admin protection)
- "Same as business hours" toggle on → show preview schedule ย่อๆ ด้านล่าง toggle
- Remove member: ด้านล่างสุดของ modal แยกออกจาก Save อย่างชัดเจน
- Confirm dialog for Remove: mention ผลกระทบ

## Technical Notes

**Dependencies**
- SET-01: Settings shell และ navigation
- SET-02: Business Hours API ต้องพร้อมเพื่อ populate "Same as business hours" toggle
- RBAC-02: member management APIs (invite, change role, remove) ต้องมีก่อน
- RBAC-01: admin protection rules enforce ที่ backend ตอน role change

**Special focus**
- `workspace_members` table ต้องมี `team_id` column (nullable, FK to teams table เมื่อ R2 มา) ตั้งแต่ MVP นี้
- `user_work_shifts` table schema: `user_id`, `workspace_id`, `same_as_business_hours` (boolean), `shifts` (JSON array), `created_at`, `updated_at`
- Work shift "Same as business hours": เก็บ flag `same_as_business_hours=true` ไม่ copy ค่ามา — ถ้า business hours เปลี่ยน ค่าต้องอัปเดตตามอัตโนมัติ
- Email read-only: enforce ที่ API layer — `PATCH /members/:id` ต้องไม่รับ email field
- Role change ผ่าน Edit modal → call RBAC-02 API เหมือนเดิม ไม่มี API ใหม่

## QA / Test Considerations

**Primary flows**
- เปิด Edit modal → แก้ชื่อ + เปลี่ยน role → save → list update ถูกต้อง
- Enable "Same as BH" → save → work shift column แสดง "Same as BH"
- Set custom work shift Mon-Fri 09-18 → save → summary แสดงถูกต้องใน list
- Remove member → confirm → member หายจาก list
- Business hours update ใน SET-02 → member ที่ใช้ Same as BH → effective shift update

**Edge cases**
- Email field ใน modal: พยายาม type → ไม่มีผล
- Change role ของ Admin คนเดียว → Admin protection error
- Business hours ไม่ได้ตั้งค่าใน SET-02 → "Same as BH" toggle ควร show warning หรือ default
- Member ที่ถูก remove: sessions revoke
- Work shift custom มีวันทับซ้อน (shift 1: 09-13, shift 2: 12-18) → validate overlap

**Business-critical must not break**
- Email ต้องไม่สามารถแก้ไขได้ทั้ง frontend และ API
- `team_id` field ต้องมีใน schema ตั้งแต่ MVP แรก ไม่ต้องมา alter ทีหลัง
- Admin protection ต้องทำงานใน Edit modal เช่นเดียวกับ direct API call

**Test types**
- UI tests: member list columns, Edit modal open/close/save
- API tests: `PATCH member` (name, role) — verify email ไม่เปลี่ยน
- Schema test: `team_id` field มีอยู่ใน `workspace_members`
- Work shift tests: same_as_BH vs custom, read business hours correctly
- Admin protection: role change last admin → error

## Subtasks

| Task | Name | Status |
|------|------|--------|
| [ACE-1628](https://app.clickup.com/t/86d2jhdf8) | Modify member list page | To Do |
| [ACE-1690](https://app.clickup.com/t/86d2qk8ej) | Build edit member role and business hours | To Do |
| [ACE-1686](https://app.clickup.com/t/86d2qk8k9) | Design/build api | To Do |
| [ACE-1687](https://app.clickup.com/t/86d2qk8pp) | Diagrams | In Progress |
| [ACE-1688](https://app.clickup.com/t/86d2qk8tm) | API Table | To Do |
