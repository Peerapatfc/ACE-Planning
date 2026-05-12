# STORY-LOG-05 (Original): Auto-generate a New Temporary Password and Email It

**Status:** To Do | **Sprint:** Sprint 5 (5/5–5/15) | **Points:** 4 SP | **ClickUp:** [ACE-2049](https://app.clickup.com/t/86d2wav77) | **Epic:** [ACE-1970](https://app.clickup.com/t/86d2u6vzv)

> **Note:** This is the original temporary-password approach as defined in ClickUp ACE-2049. Superseded by the token/magic-link approach — see `ACE-1970_ACE-2049_STORY-LOG-05_Expired_Password_Reset_Via_Token.md`.

## User Story

As a user
I want the system to automatically issue me a new password when mine has expired
so that I can regain access securely without using an outdated password.

## Detail / Description

**Scope of this story:** When a user's password is expired (90-day policy), the system generates a new temporary password, emails it to the user, and invalidates the old password immediately. The new password becomes the only valid password for the next login.

## Acceptance Criteria

### Expired password triggers new password issuance
**Given** the user's password is expired per configured policy (90 days)  
**When** the user attempts to log in with their (old) password  
**Then** the system must generate a new temporary password, invalidate the old password, email the temporary password, and show a message instructing the user to check email

### Old password becomes unusable immediately
**Given** the system has generated a temporary password due to expiry  
**When** the user attempts to log in again using the old password  
**Then** login must fail (generic failure) and must not allow MFA challenge creation

### Temporary password works for next login
**Given** the user received the temporary password and it is still valid  
**When** the user logs in using the temporary password  
**Then** the login flow proceeds to MFA (since MFA is required) and, after MFA success, the user is forced to change the password (STORY-LOG-07)

### Temporary password issuance rate limit
**Given** a user repeatedly attempts login while the email is delayed  
**When** multiple issuance attempts occur within a short window  
**Then** the system must enforce a cooldown (one issuance per 10 minutes) and must not spam the user's inbox

### Temporary password expires in 15 minutes
**Given** the system has issued a temporary password  
**When** the temporary password has not been used within 15 minutes  
**Then** the temporary password must be considered expired  
**And** the user must be forced to request a new password reset flow

## Technical Notes

**APIs:**
- `/auth/login` must detect expiry and trigger password regeneration workflow
- Optionally `POST /auth/password/issue-temporary` internal service endpoint

**Data:**
- User fields updated: `password_hash` (new hash), `password_last_changed_at = now()`, `must_change_password = true`
- Store `temporary_password_issued_at` (recommended) — cooldown anchor (10-min anti-spam)
- Store `temporary_password_expires_at` (optional) — explicit expiry timestamp if not computing from `issued_at + 15 min`

**Integrations:**
- Email provider: "Temporary password issued" template

**Offer Logics:**
- Temporary password generation: strong random (12–16 chars), meets complexity, not easily guessable
- Temporary password must not match any of last 5 passwords (check against history using bcrypt verify)

**Dependencies:**
- Password expiry evaluation (STORY-LOG-05)
- Password history enforcement (STORY-LOG-08) if applied at issuance

**Special focus:**
- Security: never log plaintext temp passwords
- Performance/UX: cooldown — one issuance per 10 minutes per account

## UI/UX Notes

- Login message for expired passwords: "Your password has expired. We've emailed you a new temporary password."
- Do not reveal whether an email exists — apply message only after valid email + expired status is confirmed

## QA / Test Considerations

**Primary flows:**
- Expired user logs in → receives temp password email → logs in with temp password → MFA → forced change → success

**Edge Cases:**
- User repeatedly attempts login while email is delayed → cooldown prevents spamming
- Email delivery failure → show retry guidance and log incident

**Business-Critical Must Not Break:**
- Must not accidentally reset passwords for non-expired users
- Must not allow old password after temp password issuance

## Subtasks

| ID | Name | Status |
|---|---|---|
| [ACE-2085](https://app.clickup.com/t/86d2wnuz5) | Password Expiry Detection | To Do |
| [ACE-2086](https://app.clickup.com/t/86d2wnv2x) | Email Delivery | To Do |
| [ACE-2087](https://app.clickup.com/t/86d2wnveu) | Anti-Spam | To Do |
