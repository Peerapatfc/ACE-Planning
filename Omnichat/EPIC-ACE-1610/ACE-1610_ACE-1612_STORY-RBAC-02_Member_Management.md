# STORY-RBAC-02: Member Management

**Status:** Backlog

## User Story

As a Workspace Admin
I want to invite team members, assign their roles, change roles, and remove members
so that I can control who has access to the workspace and ensure the right people have the right permissions.

## Detail / Description

Story นี้ build ระบบจัดการ members ภายใน workspace ทั้งหมด ครอบคลุม invitation flow, role management, และ member removal
เฉพาะ Admin เท่านั้นที่ทำ action เหล่านี้ได้

**First Admin คือใคร:**
คนที่สร้าง workspace ใหม่ได้รับ Admin role โดยอัตโนมัติ โดยไม่ต้องถูก invite เป็น onboarding flow
(RBAC-02 ต้องทำให้รองรับ state นี้ รวมถึงต้องไปเซ็ต no-reply@domain ด้วย [รอชื่อโดเมนว่าจะใช้อันไหนดี])

**Invitation Flow:**
1. Admin กรอก email ปลายทาง + เลือก role → ระบบส่ง invitation email ด้วย no-reply email
2. Email มี link ที่มี token ที่มีอายุ 7 วัน
3. ผู้รับ click link → ลงทะเบียน (ถ้าไม่มี account) หรือ login → ได้รับ role ที่กำหนด
4. ถ้าไม่ accept ภายใน 7 วัน invitation หมดอายุ Admin ต้อง Resend เพื่อออก link ใหม่

## Admin Protection Rules

| Scenario | Behavior |
|---|---|
| Admin down role ตัวเอง | ได้ ถ้ายังมี Admin อื่นอย่างน้อย 1 คน |
| Admin down role Admin อีกคน | ได้ ถ้ายังมี Admin เหลืออย่างน้อย 1 คนหลังเปลี่ยน |
| Admin remove Admin อีกคน | ได้ ถ้ายังมี Admin เหลืออย่างน้อย 1 คนหลัง remove |
| Workspace มี Admin 1 คน | ไม่สามารถ down role หรือ remove Admin คนนั้นได้เลย |

## Scope of this story

- Invite member: กรอก email + เลือก role + ส่ง invitation email ด้วย no-reply email
- Pending invitation: แสดงรายการ, Resend (reset expiry 7 วัน), Cancel invitation
- Active member list: แสดง name, email, role, joined date, last active
- Change role: Admin เปลี่ยน role ของ member คนใดก็ได้ (ยกเว้นกรณีที่ละเมิด Admin protection)
- Remove member: Admin ลบ member ออกจาก workspace (ยกเว้นกรณีที่ละเมิด Admin protection)
- ไม่รวม UI shell ของ Settings page อยู่ใน SETTINGS-03

## Acceptance Criteria

### Admin can invite a new member with a specified role
- Given an Admin is on the Member Management page
- When they enter a valid email address and select a role (Admin, Supervisor, or Agent) and click Send invitation
- Then an invitation email is sent to that address from no-reply@domain
- And a pending invitation record is created with expiry = 7 days from now
- And the pending invitation appears in the "Pending Invitations" section

### Invited user becomes a member upon accepting the invitation
- Given a pending invitation exists for email X with role Agent
- When the recipient clicks the invitation link within 7 days and completes login or registration
- Then they are added to the workspace with role Agent
- And the pending invitation record is marked as accepted

### Invitation expires after 7 days and cannot be accepted
- Given a pending invitation was sent 7 days ago and has not been accepted
- When the recipient clicks the invitation link
- Then they see "Invitation link has expired"
- And the invitation status updates to "Expired" in the pending list

### Admin can resend or cancel a pending invitation
- When Admin clicks Resend → new email sent with fresh token, expiry resets to 7 days
- When Admin clicks Cancel → invitation voided, original link no longer works

### Admin cannot invite an email that is already an active member
- Then the system shows an error "email นี้เป็นสมาชิกอยู่แล้ว"

### Admin can change the role of any member (subject to Admin protection rules)
- Given workspace has 2+ Admins → Admin A can change Admin B's role to Supervisor → updated immediately
- Given workspace has 1 Admin left → that Admin cannot change own role → error "ต้องมี Admin อย่างน้อย 1 คนใน workspace"

### Admin can remove a member
- When Admin removes a member → member loses all access immediately
- Conversation history and messages are preserved intact
- Removed member's name appears in historical reply logs as "former member"

### Admin cannot remove the last Admin
- Error: "ไม่สามารถลบ Admin คนสุดท้ายได้ กรุณา assign Admin คนใหม่ก่อน"

### Role change takes effect immediately without requiring re-login
- New permissions applied on member's next action/API call

### Admin cannot invite beyond workspace member limit
- System shows error when member limit is reached (limit TBD per plan)

## UI/UX Notes

- Page แบ่งเป็น 2 sections: "Active Members" และ "Pending Invitations"
- Active Members table: Name, Email, Role, Joined date, Last active, Actions
- เปลี่ยน role ผ่าน dropdown inline ใน row (มี confirm dialog ก่อนทำ)
- Remove button มี confirm dialog พร้อม warning
- Pending Invitations table: Email, Role, Sent date, Expires, Status, Actions (Resend / Cancel)
- Invite modal: email input, role dropdown, Send button
- Error state ชัดเจนเมื่อ Admin protection rule ถูก trigger

## Technical Notes

**Dependencies:**
- RBAC-01 Admin protection logic และ permission middleware ต้องมีก่อน
- domain email ต้องถูก verify ก่อน RBAC-02 dev เสร็จ
- Authentication system user account creation flow ต้องรองรับ invitation token

**Special focus:**
- Invitation token ควรเป็น cryptographically random string (32-byte hex) ไม่ใช่ sequential ID
- เมื่อ member ถูก remove → revoke session token ที่ active ทั้งหมดทันที ไม่รอ expiry
- Role change → ไม่ต้อง revoke session แต่ permission check จะ re-evaluate บน next request
- `replied_by` ใน message ของ member ที่ถูก remove → fallback display เป็น "former member (name)"

## QA / Test Considerations

**Primary flows:**
- Invite → email ส่ง → accept ภายใน 7 วัน → เป็น member มี permission ถูกต้อง
- Invite → ไม่ accept 7 วัน → expired → Resend → link ใหม่ใช้ได้
- Change role Agent → Supervisor → verify permission เปลี่ยนทันที
- Remove member → member เข้า workspace ไม่ได้

**Edge Cases:**
- Invite email ซ้ำที่มีอยู่แล้ว → error message ชัดเจน
- Accept invitation หลัง cancel → link invalid
- Accept invitation หลัง 7 วัน → expired page
- Remove last Admin → error ไม่ให้ทำ
- Down role Admin คนสุดท้าย → error ไม่ให้ทำ
- Admin remove ตัวเอง ขณะที่มี Admin อื่น → ได้

**Business-Critical Must Not Break:**
- Workspace ต้องมี Admin อย่างน้อย 1 คนตลอดเวลา ห้ามเป็น 0
- Invitation token ต้อง expire จริงที่ backend ไม่ใช่แค่ UI
- Session ของ removed member ต้องถูก revoke ทันที

**Test Types:**
- API tests สำหรับ invite, accept, expire, resend, cancel
- Admin protection tests: edge cases ทุก scenario
- Email delivery tests
- Session revocation tests: removed member call API → 401
