# STORY-LOG-03: Generate & Email 6-digit TOTP Code with Resend Controls

**Status:** Backlog | **ClickUp:** [ACE-2047](https://app.clickup.com/t/86d2wav3j) | **Epic:** [ACE-1970](https://app.clickup.com/t/86d2u6vzv)

## User Story

As a user
I want the system to email me a 6-digit time-limited verification code
so that I can complete MFA during login.

## Detail / Description

**Scope of this story:** Create the MFA by generating a 6-digit code (time-limited) and delivering it to the user's email. Includes resend behavior and anti-spam controls.

## Acceptance Criteria

### Code generation & email delivery
**Given** a user has passed email and password validation and is in `MFA_REQUIRED` state  
**When** the system creates an MFA challenge  
**Then** it must generate a 6-digit numeric code, set an expiry time (5 minutes), and send the code to the user's registered email address

### Resend control
**Given** an MFA challenge exists and is not yet verified  
**When** the user clicks "Resend code"  
**Then** the system must send a new code (invalidating the previous code) and enforce a resend cooldown (cannot resend more than once per 30 seconds)  
**And** the system must limit max resend attempts (5 resends per hour)

### Delivery failure handling
**Given** the email provider fails or times out  
**When** the system attempts to send the MFA email  
**Then** the user must see a generic failure message with a safe retry option  
**And** the system must log the failure event for support investigation

### Code stored securely
**Given** the system generates an MFA code  
**When** storing the challenge record  
**Then** the system must store only the hashed value of the code (never plaintext)

## Technical Notes

**APIs:**
- `POST /auth/mfa/challenge` (optional if not created during `/auth/login`) → returns `mfa_challenge_id`
- `POST /auth/mfa/resend` → invalidates old code and issues a new one

**Data:**
- `mfa_challenges` table: `id, user_id, code_hash, expires_at, status (PENDING/VERIFIED/EXPIRED), resend_count, last_sent_at`
- Store hash of code only (never store plaintext)

**Integrations:**
- Email service/provider (SMTP/SendGrid/etc.) + templating for "Login verification code"

**Dependencies:**
- Verified email availability (LOG-04 uses this challenge)

**Special focus:**
- Security: rate-limit resend and avoid email enumeration leaks

## UI/UX Notes

- MFA screen แสดง: email แบบ masked (e.g., `t***@domain.com`) และปุ่ม "Resend code" พร้อม cooldown timer
- แสดงข้อความ "Code expires in X minutes."
- ห้ามแสดง email address แบบ full

## QA / Test Considerations

**Primary flows:**
- MFA challenge created → email received with 6-digit code
- Resend → new email received; old code no longer works

**Edge Cases:**
- Email delayed beyond TTL → user enters expired code → must fail cleanly
- Multiple resends quickly → cooldown enforced

**Business-Critical Must Not Break:**
- Do not email codes for incorrect-password attempts
- Codes must not be reusable after verification/expiry/resend
