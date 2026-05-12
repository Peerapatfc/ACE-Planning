# STORY-LOG-05 (Revised): Expired Password Reset via Token

**Status:** To Do | **Sprint:** Sprint 5 (5/5–5/15) | **Points:** 4 SP | **ClickUp:** [ACE-2049](https://app.clickup.com/t/86d2wav77) | **Epic:** [ACE-1970](https://app.clickup.com/t/86d2u6vzv)

> **Note:** This is a revised approach replacing the original "auto-generate temporary password" design. Instead of a temporary password the user must type, the system issues a one-time token delivered as a magic link in email. This flow does not include MFA — MFA is enforced on the subsequent fresh login after password change (standard flow, STORY-LOG-02 compliant).

---

## User Story

As a user  
I want the system to automatically send me a secure login link when my password has expired  
so that I can regain access securely without having to type a temporary password.

## Detail / Description

**Scope of this story:** When a user's password is expired (90-day policy), the system generates a one-time reset token, emails a magic link to the user, and invalidates the old password immediately. The user clicks the link and is directed to set a new password. After setting the new password, the user is redirected to login and must complete a fresh login (including MFA) to gain portal access. The token is single-use and expires in 15 minutes.

**Why token instead of temporary password:**
- No manual copy-paste of a random string — lower error rate
- Token stored hashed server-side — never appears in plaintext in logs
- Same security level — email is the trust boundary either way
- MFA enforced on fresh login after password change — STORY-LOG-02 "MFA always required" fully satisfied

---

## Login Flow (SEC-05 Token Path)

```
User enters email + password
  ↓
password_voided_at IS NOT NULL? → YES → 401 generic failure (skip bcrypt)
  ↓ NO
bcrypt compare → incorrect? → 401 generic failure
  ↓ correct
Password expired? (> 90 days) → NO → MFA step (STORY-LOG-02)
  ↓ YES
Generate token → hash + store in Redis (TTL 15 min)
SET password_voided_at = now()        ← blocks all future logins with old password
SET password_reset_issued_at = now()  ← cooldown anchor (used by resend endpoint)
Email magic link: /auth/expired-reset?token=<raw-uuid>
Return: "Your password has expired. We've sent a login link to your email."

  ↓ (subsequent login attempts with old/any password → void check → 401, never reach this path again)

User clicks magic link
  ↓
GETDEL expired_reset:{token_hash} → user_id (atomic, single-use)
Token valid → scoped session issued (password change only)
  ↓
Force password change screen (STORY-LOG-07)
  ← STORY-LOG-07: password_hash = new hash, password_voided_at = NULL on success
  ↓
New password set → redirect to login page
  ↓
User logs in with new password → MFA (STORY-LOG-02) → full session → portal access ✓
```

> **Note:** Cooldown (10-min anti-spam) is enforced on `POST /auth/expired-reset/resend` only —
> not on the login path. After first token issuance, `password_voided_at` blocks all login
> attempts, so the cooldown on login is unreachable.

---

## Acceptance Criteria

### Expired password triggers token issuance
**Given** the user's password is expired per configured policy (90 days)  
**When** the user attempts to log in with their (old) password  
**Then** the system must generate a one-time reset token, void the old password, email a magic link to the user, and display: "Your password has expired. We've sent a login link to your email."

### Old password becomes unusable immediately
**Given** the system has voided the old password due to expiry  
**When** the user attempts to log in again using the old password  
**Then** login must fail (generic failure) and must not allow MFA challenge creation

### Token link validates and leads directly to forced password change
**Given** the user received the magic link and the token is still valid (not used, not expired)  
**When** the user clicks the link  
**Then** the system must validate the token via `GETDEL` (atomic single-use), issue a scoped session, and redirect directly to the forced password change screen (STORY-LOG-07)  
**And** a full session must NOT be created — after password change, user is redirected to login  
**And** user must complete a fresh login with the new password (including MFA) to gain portal access

### Token expires in 15 minutes
**Given** the system has issued a reset token  
**When** the token has not been used within 15 minutes  
**Then** the token must be considered expired (Redis TTL auto-evicts the key)  
**And** clicking the link must return an error and redirect the user to the password reset request page

### Expired token forces user through reset flow
**Given** the user clicks a magic link whose token has expired  
**When** the system validates the token via `GETDEL` and receives `nil`  
**Then** the system must redirect the user to `/auth/expired-reset/request`  
**And** the user must enter their email to request a new link (subject to 10-min cooldown)  
**And** no session of any kind must be created — the redirect grants no access  
**And** `password_voided_at` remains set — user cannot bypass by retrying with old password

### Token is single-use
**Given** the user has already clicked the magic link once  
**When** the same link is clicked again  
**Then** the system must reject the request with a generic error and must not redirect to the password change screen

### Token issuance rate limit (anti-spam)
**Given** a user repeatedly attempts login while email is delayed  
**When** multiple login attempts with an expired password occur within 10 minutes  
**Then** the system must enforce a cooldown (one token issuance per 10 minutes per account) and must not send duplicate emails

---

## Technical Notes

**APIs:**
- `POST /auth/login` — detects password expiry, triggers token issuance workflow, returns generic expiry message
- `POST /auth/expired-reset/validate` — `GETDEL` token from Redis, validates user_id; returns a short-lived scoped session valid only for `POST /auth/password/change`
- `POST /auth/expired-reset/resend` — re-issues token if cooldown (10 min) has elapsed; **this is the only endpoint where cooldown is enforced**

**Data — new fields on User (DB):**

| Field | Type | Purpose |
|---|---|---|
| `password_reset_issued_at` | `DateTime?` | cooldown anchor (10-min anti-spam) — persists across Redis restarts, not cleared after password change |
| `password_voided_at` | `DateTime?` | blocks old password from login — set on token issuance, cleared by STORY-LOG-07 on successful password change |

> `must_change_password` — managed entirely by STORY-LOG-07, not this story

**Token storage — Redis:**

| Key | Value | TTL |
|---|---|---|
| `expired_reset:{token_hash}` | `{user_id}` | 900s (15 min, auto-expires) |

- Raw token: `crypto.randomBytes(32).toString('hex')` — matches project convention (see `invitations.service.ts`, `auth.service.ts`)
- Stored key: SHA-256 hash of raw token (never store plaintext)
- Link format: `https://<domain>/auth/expired-reset?token=<raw>`
- Single-use enforced via `GETDEL` (atomic get + delete) — no race condition, no separate "mark used" step
- Redis down during 15-min window → token lost → user must request new link (acceptable failure mode)

**Password voiding:**
- Set `password_voided_at = now()` on token issuance — `password_hash` is NOT modified
- Login check: if `password_voided_at IS NOT NULL` → reject immediately, skip bcrypt compare
- `password_voided_at` cleared by STORY-LOG-07 only after new password is successfully set
- Benefit: `password_hash` preserved throughout recovery — no broken state if user abandons flow mid-way

**Scoped session after token validation:**
- Token validation returns a short-lived scoped session (not a full portal session)
- Scoped session valid only for `POST /auth/password/change` — no other endpoint
- No full session created in this flow — password change completes then redirects to login
- User must do a fresh login with new password (goes through standard MFA flow) to gain portal access
- This preserves STORY-LOG-02 "MFA always required" — no exception needed

**Integrations:**
- Redis (already in stack via STORY-LOG-02 rate limiting)
- Email provider: new template "Password Expiry — Login Link" (distinct from MFA code email)

**Dependencies:**
- Password expiry evaluation (detect 90-day window) — prerequisite to this story
- Forced password change (STORY-LOG-07) — triggered directly after token validation
- Password history enforcement (STORY-LOG-08) — applied when user sets new password

**Security constraints:**
- Never log raw token — only log token hash or token ID
- Token must be validated in constant time (prevent timing attacks)
- Cooldown enforced on `POST /auth/expired-reset/resend` only — login path is blocked by `password_voided_at` after first issuance, making cooldown on login unreachable

---

## UI/UX Notes

- **Login page message (expired):** "Your password has expired. We've sent a login link to your email."
- **Token link landing page:** Show loading state → on success, redirect to forced password change screen (STORY-LOG-07); on failure show: "This link has expired or has already been used. Please log in again."
- Do not reveal whether an email address exists in the system — apply expiry message only after credential check passes (correct password + expired)

---

## QA / Test Considerations

**Primary flows:**
1. Expired user logs in → receives magic link email → clicks link → token validated → forced password change screen → new password set → redirect to login → user logs in with new password → MFA → full session → portal access

**Edge Cases:**
- User clicks link after 15 minutes → expired error, redirect back to login
- User clicks same link twice → second click rejected with generic error, no action taken
- User attempts login again with old (voided) password → generic login failure
- User attempts login 3 times while email is delayed → only first attempt triggers email; subsequent attempts within 10 min show: "A login link was recently sent. Please check your email."
- Email delivery failure → show: "We couldn't send the link. Please try again later." and log incident (no plaintext token in log)
- User attempts `/auth/expired-reset/validate` with tampered token → reject with generic error

**Business-Critical Must Not Break:**
- Must not void passwords for non-expired users
- Must not create full session at any point in this flow — portal access requires fresh login after password change
- Scoped session from token validation must not grant access to any endpoint other than password change
- Must not issue token if account is soft-locked or hard-locked

---

## Subtasks

| ID | Name | Status |
|---|---|---|
| [ACE-2085](https://app.clickup.com/t/86d2wnuz5) | Password Expiry Detection | To Do |
| [ACE-2086](https://app.clickup.com/t/86d2wnv2x) | Email Delivery (magic link template) | To Do |
| [ACE-2087](https://app.clickup.com/t/86d2wnveu) | Anti-Spam / Cooldown | To Do |
| *(new)* | Token generation, storage, and validation endpoint | To Do |
| *(new)* | Scoped session for password change after token validation | To Do |
