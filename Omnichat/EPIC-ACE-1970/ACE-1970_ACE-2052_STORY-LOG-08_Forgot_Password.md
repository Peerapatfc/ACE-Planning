# STORY-LOG-08: Forgot Password

**Status:** Backlog | **ClickUp:** [ACE-2052](https://app.clickup.com/t/86d2wavbw) | **Epic:** [ACE-1970](https://app.clickup.com/t/86d2u6vzv)

## User Story

As a user
I want to regain access by requesting a temporary password via email when I forget my password or my account is locked
so that I can self-service both password recovery and account unlock without contacting support or engineering.

## Detail / Description

**Scope of this story:** Forgot Password issues a temporary password using the same mechanism as LOG-05 (password expiry). This eliminates the need for a separate reset-link token and endpoint. After the temp password is emailed, the user logs in with it, passes MFA, then is forced to set a new password via LOG-06. The same flow also atomically clears any soft lock or hard lock state.

There is no reset link, no separate verification token, and no separate password-setting page outside of the existing force-change flow.

## Acceptance Criteria

### Request is non-enumerating
**Given** a user submits their email on the Forgot Password page  
**When** the form is submitted  
**Then** the system must always respond with the same generic message regardless of whether the account exists  
**And** if the account exists and is eligible, the system generates a temporary password and emails it  
**And** if the account does not exist, no email is sent and no indication is given

### System generates and emails a temporary password
**Given** a valid account exists for the submitted email  
**When** the forgot password request is processed  
**Then** the system generates a new strong random temporary password (same mechanism as LOG-05)  
**And** the current password is invalidated immediately  
**And** `must_change_password` is set to true  
**And** the temporary password is emailed to the user

### Temporary password clears all lock states atomically
**Given** the account is soft-locked, hard-locked, or both  
**When** the temporary password is issued  
**Then** `soft_locked_until` is set to null in the same database transaction  
**And** `hard_locked` is set to false in the same database transaction  
**And** `failed_login_attempts` is reset to 0 in the same database transaction  
**And** the user may log in immediately with the temporary password

### User login with temp password leads to force change
**Given** the user receives the temporary password  
**When** they log in with it and pass MFA  
**Then** the system enforces `must_change_password = true`  
**And** all portal access is blocked until the user sets a new permanent password via LOG-06

### Rate limiting prevents abuse
**Given** a user or attacker submits multiple forgot password requests  
**When** the rate limit threshold is reached (5 requests per hour per IP)  
**Then** the system must return HTTP 429 with a `Retry-After` header  
**And** no temporary password is generated for rate-limited requests

### Session invalidation on temp password issuance
**Given** a temporary password is issued successfully  
**When** the process completes  
**Then** all existing active sessions for that user must be invalidated immediately

## Technical Notes

**APIs:**
- `POST /auth/password/forgot { email }` — rate-limited, non-enumerating, triggers temp password generation and email

**Data:**
- Reuses temp password mechanism from LOG-05: update `password_hash`, set `must_change_password = true`
- Atomic update: `soft_locked_until = null, hard_locked = false, failed_login_attempts = 0`
- No separate `password_reset_tokens` table needed — eliminates a token/endpoint entirely

**Integrations:**
- Email provider: "temporary password" template — same template as LOG-05 with different subject line

**Offer Logics:**
- Rate limit: 5 requests per hour per IP → 429 with `Retry-After`
- Cooldown per account: one temp password issued per 10 minutes (prevent inbox spam)
- Temp password must not match any of last 5 passwords (history check at generation time)

**Dependencies:**
- LOG-05 temp password generation mechanism (reused directly)
- LOG-06 force change flow (user must pass through after login with temp password)

**Special focus:**
- Security: non-enumeration is mandatory — identical response for existing and non-existing accounts
- Security: atomic lock clear — `soft_locked_until`, `hard_locked`, and `failed_login_attempts` must update in one transaction
- UX: significantly simpler than a reset-link flow — no TTL countdown, no "link expired" edge case

## UI/UX Notes

- "Forgot password?" link on login screen — visible at all times including during lockout
- Request page: email input only. Submit shows generic success message regardless of outcome
- No reset-link page, no token-confirmation page — user goes directly to login with temp password
- Hard lock screen must also show "Forgot password?" link prominently

## QA / Test Considerations

**Primary flows:**
- Submit email → temp password emailed → login with temp password → MFA → force change → portal access
- Hard-locked user submits email → temp password issued → lock cleared atomically → login works immediately after
- Soft-locked user submits email → lock cleared → can log in without waiting 15 minutes

**Edge Cases:**
- Non-existent email submitted → same response, no email sent, no timing difference
- Multiple requests within cooldown → only latest temp password valid, inbox not spammed
- Rate limit hit → 429 returned, no temp password generated

**Business-Critical Must Not Break:**
- Response must never indicate whether the email exists
- Lock clearing must be atomic — no partial state where `hard_locked` is cleared but counter is not
- MFA must still be required after logging in with the temporary password
