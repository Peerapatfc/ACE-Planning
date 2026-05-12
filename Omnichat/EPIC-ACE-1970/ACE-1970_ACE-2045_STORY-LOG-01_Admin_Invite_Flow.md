# STORY-LOG-01: Admin Invite Flow

**Status:** Backlog | **ClickUp:** [ACE-2045](https://app.clickup.com/t/86d2wauu7) | **Epic:** [ACE-1970](https://app.clickup.com/t/86d2u6vzv)

## User Story

As a System Admin
I want to invite users by email so they can verify their account and access the portal
so that only users with a verified email can log in, and MFA codes are always deliverable to a confirmed inbox.

## Detail / Description

**Scope of this story:** Admin creates user accounts and the system sends an invitation email containing a one-time verification link. The link expires after 7 days. If the user does not verify within 7 days, only the Admin can resend the invite — there is no self-service resend for the user. Until email is verified, login is blocked at the password stage with a clear message.

This story covers: invite email send, status tracking (Invited / Expired / Active), login block behavior, and Admin resend flow.

## Acceptance Criteria

### Invite email sent automatically when Admin creates a user
**Given** System Admin creates a new user account with an email address  
**When** the account is saved  
**Then** the system generates a one-time verification token, sets `invite_expires_at = now() + 7 days`, and sends an invite email to the provided address  
**And** the user status is set to "Invited"  
**And** the user cannot log in until the invite is accepted

### User verifies email within 7 days
**Given** the user receives an invite email and the link has not expired  
**When** the user clicks the verification link  
**Then** the system sets `email_verified_at` to the current timestamp  
**And** the user status changes to "Active"  
**And** the user may now log in and complete MFA

### Invite link expires after 7 days
**Given** the user clicks a verification link after `invite_expires_at` has passed  
**When** the link is submitted  
**Then** the system must reject the link with an error: "This invite link has expired. Please contact your administrator."  
**And** the user status changes to "Expired"  
**And** the user cannot log in until Admin resends the invite

### Login blocked if email not verified
**Given** a user account has status Invited or Expired (`email_verified_at` is null)  
**When** the user attempts to log in with correct email and password  
**Then** the system must block login immediately after password validation  
**And** the system must show: "Your account is not yet verified. Please check your email for an invite link, or contact your administrator."  
**And** the system must NOT send an MFA code  
**And** the system must NOT reveal the exact account status (Invited vs Expired) in the message

### Admin can resend invite for Invited or Expired users
**Given** the user status is Invited or Expired  
**When** System Admin clicks "Resend invite" in User Management  
**Then** the system invalidates the previous token and generates a new one  
**And** the system sets `invite_expires_at = now() + 7 days`  
**And** the system sends a new invite email to the user  
**And** the user status resets to "Invited"

### Invite token is secure and single-use
**Given** an invite token is generated  
**When** it is stored and sent  
**Then** the token must be cryptographically random, hashed at rest, single-use, and expire after 7 days  
**And** clicking a used or superseded token must be rejected gracefully

### Temporary password issued after email verification
**Given** a user clicks a valid invite link and email verification completes successfully  
**When** the system sets `email_verified_at` and changes status to Active  
**Then** the system must immediately generate a temporary password using the same mechanism as LOG-05  
**And** the system must send the temporary password to the verified email address  
**And** `must_change_password` must be set to true  
**And** the user must log in with this temporary password and will be forced to set a new permanent password via LOG-06  
**And** the invite token must be invalidated at this point and cannot be reused

## Technical Notes

**Data:**
- User fields: `email`, `email_verified_at (nullable)`, `invite_token_hash (nullable)`, `invite_expires_at (nullable)`, `status (Invited / Expired / Active / Soft locked / Hard locked)`
- Status transitions: Invited → Active (on verify), Invited → Expired, Expired → Invited (on resend), Active → Invited (on email change)

**APIs:** ตรวจสอบว่ามีอยู่แล้ว

**Integrations:**
- Email provider: single "invite" template ใช้ทั้ง initial invite และ resend
- Cron job หรือ DB check: mark Invited → Expired เมื่อ `invite_expires_at < now()` (หรือ evaluate lazily at login/verify time)

**Dependencies:**
- Admin User Management module with role-based access
- Email provider + invite template
- Cron หรือ lazy-evaluation mechanism for Expired status

**Special focus:**
- Security: invite tokens must be hashed at rest, never stored in plaintext
- UX: Admin must clearly see which users are Invited / Expired

## UI/UX Notes

- User Management table: แสดง status column — Active / Invited / Expired / Soft locked / Hard locked

## QA / Test Considerations

**Primary flows:**
- Admin creates user → invite email sent → user clicks link within 7 days → verified → login works
- Admin creates user → 7 days pass → status = Expired → Admin resends → new link → verified → login works

**Edge Cases:**
- User clicks expired link (must show clear error, not generic 404)
- User clicks old token after Admin has resent → must reject
- Admin resends to Invited user before 7 days → old token invalidated

**Business-Critical Must Not Break:**
- Unverified users must never receive an MFA code
- Login block message must not reveal whether token is Invited vs Expired
- Active users must not be affected by invite flow changes
