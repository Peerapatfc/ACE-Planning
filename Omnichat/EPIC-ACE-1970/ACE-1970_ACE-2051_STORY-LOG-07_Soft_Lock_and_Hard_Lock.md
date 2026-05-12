# STORY-LOG-07: Soft Lock (5 fails, 15 min auto-expire) + Hard Lock (10 fails, requires password reset)

**Status:** To Do | **Sprint:** Sprint 5 (5/5–5/15) | **Points:** 5 SP | **ClickUp:** [ACE-2051](https://app.clickup.com/t/86d2wav9n) | **Epic:** [ACE-1970](https://app.clickup.com/t/86d2u6vzv)

## User Story

As a user
I want failed login attempts to trigger an automatic temporary lock, and a permanent lock after repeated failures
so that brute-force attacks are blocked while legitimate users who mistype their password can recover without contacting support.

## Detail / Description

**Scope of this story:** Implement a two-tier lockout mechanism.

- **Tier 1 (Soft Lock):** after 5 consecutive failed attempts, the account is locked for 15 minutes and auto-expires. The user can wait or reset their password to unlock immediately.
- **Tier 2 (Hard Lock):** after 10 consecutive failed attempts total, the account is hard-locked and requires a password reset to regain access.

Both tiers are self-service via LOG-08 (Forgot Password).

## Acceptance Criteria

### Soft lock after 5 consecutive failed attempts
**Given** an active user account is not locked  
**When** the user enters an incorrect email or password 5 times consecutively  
**Then** the system sets `soft_locked_until = now() + 15 minutes`  
**And** prevents further login attempts until `soft_locked_until` has passed  
**And** sends a notification email: "Your account has been temporarily locked for 15 minutes."  
**And** must NOT proceed to MFA challenge while soft-locked

### Soft lock message guides user to self-service
**Given** the account is soft-locked and `soft_locked_until` has NOT yet passed  
**When** the user attempts to log in  
**Then** the system shows: "Account temporarily locked. Try again in X minutes, or reset your password to unlock immediately."  
**And** the login page must display a visible "Reset password" link (ties to LOG-08)

### Soft lock auto-expires after 15 minutes
**Given** the account is soft-locked and `soft_locked_until` has passed  
**When** the user attempts to log in  
**Then** the system allows the login attempt normally (soft lock is no longer active)  
**And** `failed_login_attempts` counter is NOT reset on expiry alone

### Hard lock after 10 consecutive failed attempts
**Given** the user continues to fail after soft lock expires and `failed_login_attempts` reaches 10  
**When** the 10th failed attempt occurs  
**Then** the system sets `hard_locked = true`  
**And** blocks all login attempts indefinitely (no auto-expire)  
**And** sends a notification email: "Your account has been locked. Please reset your password to regain access."  
**And** must NOT proceed to MFA challenge while hard-locked

### Hard lock message directs user to password reset
**Given** the account is hard-locked  
**When** the user attempts to log in  
**Then** the system shows: "Account locked. Please reset your password to regain access."  
**And** the login page must display a visible "Reset password" link (ties to LOG-08)

### Reset counter after successful authentication
**Given** a user has 1–4 failed attempts (not yet soft-locked)  
**When** the user successfully logs in (password + MFA complete)  
**Then** the system resets `failed_login_attempts` to 0 and ensures `soft_locked_until` is null

### Password reset clears both soft and hard lock
**Given** the account is soft-locked or hard-locked  
**When** the user completes a valid password reset (LOG-08)  
**Then** the system clears `soft_locked_until` (set to null)  
**And** clears `hard_locked` (set to false)  
**And** resets `failed_login_attempts` to 0  
**And** the user may log in immediately with the new password

### Consistent state across distributed instances
**Given** the application runs on multiple instances  
**When** failed attempt counts are updated concurrently  
**Then** updates must use transactional locking to prevent race conditions and ensure consistent counter state

### Show remaining attempts countdown before lockout
**Given** the user enters an incorrect password  
**When** a failed login attempt occurs (before soft lock or hard lock threshold)  
**Then** the UI must show how many attempts remain before the next lock tier triggers

## Technical Notes

**APIs:**
- `/auth/login` must check `soft_locked_until > now()` and `hard_locked` before processing credentials
- Returns stable error codes: `SOFT_LOCKED` (with `retry_after` timestamp) and `HARD_LOCKED`

**Data:**
- Fields: `failed_login_attempts (int)`, `soft_locked_until (nullable timestamp)`, `hard_locked (boolean, default false)`
- Remove legacy `locked_at` — replaced by `soft_locked_until` and `hard_locked`
- Track `last_failed_login_at` (optional, for auditing)
- `soft_locked_until`: set to `now()+15min` on 5th fail; cleared on successful login or password reset
- `hard_locked`: set true on 10th fail; cleared only by password reset (LOG-08)

**Integrations:**
- Email provider: "Account locked" notification template (hard and soft)

**Offer Logics:**
- Count only email/password failures (not MFA failures) toward lockout thresholds
- Soft lock threshold: 5 consecutive fails. Hard lock threshold: 10 consecutive fails
- Soft lock TTL: 15 minutes
- `failed_login_attempts` continues to accumulate across soft lock cycles — does NOT reset on soft lock expiry

**Dependencies:**
- Password reset flow (LOG-08) must clear both `soft_locked_until` and `hard_locked`

**Special focus:**
- Security: protect against enumeration — error messages must not reveal account existence
- Security: rate-limit `/auth/login` endpoint regardless of lock state
- UX: soft lock is intentionally self-service — no admin or dev intervention required
- Performance: transactional update on `failed_login_attempts` to prevent race conditions

## UI/UX Notes

- Soft lock message: "Account temporarily locked. Try again in X minutes, or reset your password to unlock immediately." — always show "Reset password" link
- Hard lock message: "Account locked. Please reset your password to regain access." — always show "Reset password" link
- Both messages must not reveal whether the email exists (non-enumerating at message level)
- Countdown timer (X minutes remaining) on soft lock screen

## QA / Test Considerations

**Primary flows:**
- 5 wrong passwords → soft lock → show retry timer + reset link → wait 15 min → login allowed
- 5 wrong passwords → soft lock → user clicks reset password → completes reset → login immediately
- 10 wrong passwords total → hard lock → show reset link → reset password → login allowed
- Successful login (before 5 fails) → counter resets to 0

**Edge Cases:**
- Concurrent login attempts from multiple devices → transactional counter
- User enters correct password on 5th attempt → should succeed and reset counter (not trigger soft lock)
- Soft lock expires but user continues failing → counter continues from 5 toward 10
- Multiple soft lock cycles before reaching 10 fails → counter never resets on expiry

**Business-Critical Must Not Break:**
- Soft lock must auto-expire reliably — no manual intervention required
- Hard lock must persist until password reset — no accidental unlock
- Must not lock accounts due to system errors or race conditions
- Password reset must always clear BOTH `soft_locked_until` AND `hard_locked`

## Subtasks

| ID | Name | Status |
|---|---|---|
| [ACE-2092](https://app.clickup.com/t/86d2wnz2c) | Lock State Validation | To Do |
| [ACE-2093](https://app.clickup.com/t/86d2wnz5b) | Failed Attempt Counter | To Do |
| [ACE-2094](https://app.clickup.com/t/86d2wnzfz) | Reset & Success Handling | To Do |
| [ACE-2095](https://app.clickup.com/t/86d2wnzx2) | Audit Logging | To Do |
| [ACE-2096](https://app.clickup.com/t/86d2wp0cy) | Email Delivery | To Do |
