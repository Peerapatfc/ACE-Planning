# STORY-SET-03: Members & Roles Page + Edit User + Work Shift

**Status:** Backlog

**Depends On:** SET-01, SET-02, RBAC-02

## User Story

As a Workspace Admin
I want a complete Members & Roles management page with the ability to edit user details and configure individual work shifts
so that I can see who is on my team, what hours they work, and manage their access and schedules from one place.

## Detail / Description

Story นี้ build หน้า Settings > Members & Roles ที่สมบูรณ์ โดยใช้ API จาก RBAC-02
เพิ่ม Edit User modal ที่มีข้อมูลครบถ้วน รวมถึง Work Shift config ของแต่ละ user

## Member List Columns

| Column | ข้อมูลที่แสดง | Editable | Note |
|---|---|---|---|
| ชื่อ | Full name + avatar | ผ่าน Edit modal | |
| Email | Email address | ไม่ได้ (read-only) | แสดงใน Edit modal เท่านั้น |
| Role | Badge (Admin/Supervisor/Agent) | ผ่าน Edit modal | ไม่มี inline dropdown |
| Work shift | "จ-ศ 09-18" หรือ "Same as BH" | ผ่าน Edit modal | summary แบบ read-only |
| Last active | relative time เช่น "2h ที่แล้ว" | ไม่ได้ | |
| Actions | Edit button | | Remove อยู่ใน Edit modal |

## Edit User Modal

**Section A: User Information**
- Full Name (editable)
- Email (read-only)
- Role (dropdown Admin / Supervisor / Agent — ผ่าน Admin protection rules)

**Section B: User's Work Shift**
- "Same as business hours" toggle
  - เปิด: ใช้ค่าจาก SET-02 เลย ไม่ต้อง config เพิ่ม
  - ปิด: แสดง per-day schedule (toggle วัน + time range + add shift)
- "Copy times to all" shortcut
- Remove member button ด้านล่าง modal (มี confirm dialog)

> **Note:** `team_id` field บน `workspace_members` table ต้องมีตั้งแต่ตอนนี้ (nullable) เพื่อรองรับ Teams ใน R2

## Scope of this story

- Member list page: columns ตาม table ด้านบน
- Pending invitations section (ใช้ data จาก RBAC-02)
- Invite member button: เปิด invite modal (อยู่ใน RBAC-02 แล้ว)
- Edit User modal: Section A (name, email read-only, role) + Section B (work shift)
- Work shift toggle + per-day schedule
- Remove member จาก Edit modal พร้อม confirm dialog
- ไม่รวม Teams feature (R2)

## Acceptance Criteria

### Member list shows all active members with required columns
- Name (with avatar), Email, Role badge, Work shift summary, Last active, Edit button
- Role shows as read-only badge — ไม่มี inline dropdown

### Work shift summary reflects current setting
- "Same as business hours" → แสดง "Same as BH"
- Custom shift Mon-Fri 09:00-18:00 → แสดง "จ-ศ 09:00-18:00"

### Edit User modal opens with pre-filled data
- Shows current Full Name (editable), Email (read-only), Role (dropdown)
- Work shift section shows current configuration
- No fields are blank or mis-populated

### Admin can update Full Name and Role from Edit modal
- Changes saved → member list reflects new name and role badge immediately
- Role change that violates Admin protection rules → blocking error shown

### Email in Edit User modal is read-only and cannot be changed
- Field is visually distinct as read-only (disabled styling or lock icon)
- Save action never updates the email (enforced at API layer too)

### "Same as business hours" toggle
- On → per-day schedule inputs hidden, preview shows current BH schedule from SET-02
- Saved as `same_as_business_hours = true` → if BH changes, effective shift updates automatically
- Off → per-day schedule inputs appear, independent of Business Hours changes

### Custom work shift can be set independently per user
- Toggle each day on/off, set time ranges, "Copy times to all" works per row

### Remove member from Edit modal requires confirmation
- Confirm → member removed, access revoked immediately, disappears from list
- Cancel → nothing changes, Edit modal remains open

### Pending invitations section shows correct status and actions
- Each invitation shows: Email, Role, Sent date, Expiry status, Resend/Cancel buttons
- Expired invitations are visually distinct from active pending ones

### Schema includes team_id field for future R2 readiness
- `workspace_members` table has `team_id` field (nullable, defaults to null)
- UI does not display `team_id` in MVP — schema-only preparation

### Member list and Edit modal inaccessible to non-Admin roles
- Supervisor or Agent attempting to navigate to Settings > Members & Roles → redirected by route guard

## UI/UX Notes

- Member list: table layout
- Work shift column: short summary เช่น "Same as BH", "จ-ศ 09-18", "ไม่ได้ตั้ง"
- Edit button: text button หรือ icon ด้านขวาของ row
- Edit User modal: 2 sections ชัดเจน "User information" และ "User's work shift" แยก divider
- Email field: disabled styling หรือ lock icon (รอ Art confirm)
- Role dropdown: แสดง role ปัจจุบัน + allow change (enforce admin protection)
- "Same as business hours" toggle on → show preview schedule ย่อๆ ด้านล่าง toggle
- Remove member: อยู่ด้านล่างสุดของ modal แยกออกจาก Save อย่างชัดเจน
- Confirm dialog สำหรับ Remove: mention ผลกระทบ

## Technical Notes

**Dependencies:**
- SET-01 Settings shell และ navigation
- SET-02 Business Hours API ต้องพร้อมเพื่อ populate "Same as business hours" toggle
- RBAC-02 member management APIs (invite, change role, remove) ต้องมีก่อน
- RBAC-01 admin protection rules enforce ที่ backend ตอน role change

**Special focus:**
- `workspace_members` table ต้องมี `team_id` column (nullable) ตั้งแต่ MVP นี้
- `user_work_shifts` table: `user_id`, `workspace_id`, `same_as_business_hours` (boolean), `shifts` (JSON array), `created_at`, `updated_at`
- Work shift "Same as BH": เก็บ flag `same_as_business_hours=true` ไม่ copy ค่า — ถ้า BH เปลี่ยน ค่าอัปเดตอัตโนมัติ
- Email read-only: enforce ที่ API layer ด้วย — `PATCH /members/:id` ต้องไม่รับ `email` field
- Role change ผ่าน Edit modal → call RBAC-02 API เหมือนเดิม ไม่มี API ใหม่

## QA / Test Considerations

**Primary flows:**
- เปิด Edit modal → แก้ชื่อ + เปลี่ยน role → save → list update ถูกต้อง
- Enable "Same as BH" → save → work shift column แสดง "Same as BH"
- Set custom work shift Mon-Fri 09-18 → save → summary แสดงถูกต้องใน list
- Remove member → confirm → member หายจาก list
- Business hours update ใน SET-02 → member ที่ใช้ Same as BH → effective shift update

**Edge Cases:**
- Email field ใน modal: พยายาม type → ไม่มีผล
- Change role ของ Admin คนเดียว → Admin protection error
- Business hours ไม่ได้ตั้งค่าใน SET-02 → "Same as BH" toggle ควร show warning หรือ default
- Member ที่ถูก remove: sessions revoke
- Work shift ที่ custom มีวันทับซ้อน (shift 1: 09-13, shift 2: 12-18) → validate overlap

**Business-Critical Must Not Break:**
- Email ต้องไม่สามารถแก้ไขได้ทั้ง frontend และ API
- `team_id` field ต้องมีใน schema ตั้งแต่ MVP แรก
- Admin protection ต้องทำงานใน Edit modal เช่นเดียวกับ direct API call

**Test Types:**
- UI tests: member list columns, Edit modal open/close/save
- API tests: `PATCH member` (name, role) verify email ไม่เปลี่ยน
- Schema test: `team_id` field มีอยู่ใน `workspace_members`
- Work shift tests: same_as_BH vs custom, read business hours correctly
- Admin protection: role change last admin → error
