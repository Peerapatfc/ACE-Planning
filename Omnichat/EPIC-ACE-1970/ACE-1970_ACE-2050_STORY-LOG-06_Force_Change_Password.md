# STORY-LOG-06: Force User to Change Password After Temporary Password Login

**Status:** To Do | **Sprint:** Sprint 5 (5/5–5/15) | **Points:** 5 SP | **ClickUp:** [ACE-2050](https://app.clickup.com/t/86d2wav7z) | **Epic:** [ACE-1970](https://app.clickup.com/t/86d2u6vzv)

## User Story

As a user
I want to be forced to set a new password after using a temporary password, and for the system to reject any password I have used before
so that my account returns to a secure user-known password and old passwords cannot be recycled.

## Detail / Description

**Scope of this story:** When a user logs in with a system-issued temporary password (from expiry or forgot-password reset), they must set a new permanent password before accessing the portal.

The new password is validated against:
- Complexity rules
- The last 5 passwords (no reuse)

This story merges the password history check as an inline validation within this form — it is not a separate story or screen.

## Acceptance Criteria

### Forced change gate blocks all portal access
**Given** the user is authenticated (including MFA) and `must_change_password = true`  
**When** they navigate to any portal page  
**Then** the system must redirect them to a "Change Password" page  
**And** block all other access until the password change is completed

### New password must pass complexity rules
**Given** the user submits a new password  
**When** the password does not meet the minimum complexity requirements  
**Then** the system must reject the change with a clear inline error  
**And** must NOT update the stored password

### New password must not match any of the last 5 passwords
**Given** the user submits a new password  
**When** the new password matches any of the last 5 previously used passwords (checked via bcrypt verify against each stored hash)  
**Then** the system must reject the change with message: "You can't reuse any of your last 5 passwords."  
**And** must NOT update the stored password

### Successful change grants access and stores history
**Given** the user submits a new valid password that passes all rules  
**When** the change is committed  
**Then** the system updates the password hash and sets `password_last_changed_at` to `now()`  
**And** stores the previous hash in `user_password_history` (retain only the 5 most recent)  
**And** clears `must_change_password`  
**And** grants the user full access to the portal

### Cannot bypass via direct URL or API
**Given** `must_change_password = true`  
**When** the user calls any protected portal API directly  
**Then** the API must return an authorization error indicating password change is required

### All other sessions invalidated after password change
**Given** the user successfully changes their password  
**When** the change is committed  
**Then** all other active sessions for that user must be invalidated immediately

## Technical Notes

**APIs:**
- `POST /auth/password/change` with `{ current_password, new_password }` → validates complexity + history before committing

**Data:**
- User fields: `must_change_password`, `password_last_changed_at`, `password_hash`
- `user_password_history` table: `id, user_id, password_hash, created_at` — retain only 5 most recent per user
- History check: `bcrypt.verify(newPassword, eachHistoryHash)` — NOT direct string equality

**Offer Logics:**
- Password complexity: minimum 8 characters, at least 1 uppercase, 1 number, 1 special character
- Password must not exceed 64 characters
- History check: compare against current password hash + up to 4 previous hashes (total 5)
- Password expiry: fixed at 90 days (backend config `password_expiry_days = 90`) — no UI to change this value
- Deny all portal access until forced change is completed (`must_change_password` gate applies to all routes)

**Dependencies:**
- Temp password issuance (LOG-05) and forgot password reset (LOG-08)
- `user_password_history` table must exist

**Special focus:**
- Security: history check via bcrypt verify — never compare hashes directly as strings
- Security: invalidate other active sessions after password change
- Performance/UX: history check = max 5 bcrypt comparisons

## UI/UX Notes

- หน้าเปลี่ยนรหัส: new password + confirm new password (use token to verify — ไม่ต้องกรอก temporary password)
- แสดง inline password requirements checklist — update real-time ขณะพิมพ์
- History error inline under "New password": "You can't reuse any of your last 5 passwords."
- Complexity error inline under "New password" per failed rule
- Success toast: "Password updated successfully." แล้ว redirect ไป portal

## QA / Test Considerations

**Primary flows:**
- Login with temp password → MFA → forced change → new password passes all rules → access granted
- Submit password matching one of last 5 → rejected with correct inline error → submit new unique password → success

**Edge Cases:**
- User submits current (temporary) password as new password → rejected (counts as reuse)
- User with fewer than 5 prior passwords → check against all available history entries
- User opens portal in second tab during change → blocked

**Business-Critical Must Not Break:**
- No portal access possible before completing forced change
- Password change must be atomic — no partial update
- Must not corrupt `password_history` causing lockout

## Subtasks

| ID | Name | Status |
|---|---|---|
| [ACE-2088](https://app.clickup.com/t/86d2wnxgy) | Password History Check (Last 5) | To Do |
| [ACE-2089](https://app.clickup.com/t/86d2wnxvq) | Change Password Endpoint & Validation | To Do |
| [ACE-2090](https://app.clickup.com/t/86d2wnyaj) | Session Invalidation | To Do |
| [ACE-2091](https://app.clickup.com/t/86d2wnyj8) | Audit Logging | To Do |
