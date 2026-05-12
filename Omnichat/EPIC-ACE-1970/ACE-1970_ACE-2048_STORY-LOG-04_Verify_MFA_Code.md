# STORY-LOG-04: Verify MFA Code

**Status:** Backlog | **ClickUp:** [ACE-2048](https://app.clickup.com/t/86d2wav5z) | **Epic:** [ACE-1970](https://app.clickup.com/t/86d2u6vzv)

## User Story

As a user
I want my MFA code to be validated before I gain access, and for my session to expire automatically when I am inactive or after a maximum duration
so that only verified users access the portal and unattended sessions cannot be exploited.

## Detail / Description

**Scope of this story:** Validate the 6-digit MFA code, create the authenticated session on success, and enforce all session management rules — idle timeout (30 minutes), concurrent session limit (max 3 per user), and explicit logout. All session events are written to the audit log.

## Acceptance Criteria

### Successful verification grants access
**Given** a valid, unexpired MFA challenge exists for the user  
**When** the user enters the correct 6-digit code  
**Then** the system marks it as VERIFIED and creates a fully authenticated session/token allowing access to the portal

### Invalid or expired code is rejected
**Given** an MFA challenge is pending  
**When** the user enters an incorrect code or a code after `expires_at`  
**Then** the system must reject it with a generic message and must not authenticate the session

### MFA code failure — incorrect code (attempts 1–4)
**Given** an MFA challenge is pending and the user has fewer than 5 failed attempts on it  
**When** the user enters an incorrect code  
**Then** the system must reject the code and increment the attempt counter  
**And** display: "The code is incorrect. X attempts remaining." (where X = 5 minus attempt count)  
**And** the session is NOT created  
**And** `failed_login_attempts` (the password counter used for soft/hard lock in LOG-07) is NOT incremented — MFA failures are tracked separately  
**And** write `MFA_FAILED` to the audit log with `attempt_count` and `ip_address`

### MFA attempt limit — blocked after 5 failures
**Given** the user has entered an incorrect code on the same challenge 5 times  
**When** the 5th failure is recorded  
**Then** the system must mark the challenge as BLOCKED  
**And** display: "Too many attempts. Please re-enter email and password."  
**And** the user must click a button to re-enter email and password as a new login flow  
**And** the pre-authenticated login state (password verified) is NOT preserved — user must re-enter email and password  
**And** `MFA_CHALLENGE_BLOCKED` must be written to the audit log

### MFA code expired — user must resend
**Given** a valid challenge exists but `expires_at` has passed  
**When** the user submits a code (correct or not)  
**Then** the system must reject it with: "This code has expired. Please request a new code."  
**And** the challenge is marked EXPIRED  
**And** the user must click Resend — the pre-authenticated state (password verified) is preserved

### Session has absolute TTL of 8 hours
**Given** a session is created on successful MFA verification  
**When** 8 hours have passed since session creation (`created_at`)  
**Then** the session must be invalidated server-side regardless of activity  
**And** the next API call must return 401 and redirect the user to login

### Session has idle timeout of 30 minutes
**Given** an authenticated user makes no API calls for 30 consecutive minutes  
**When** the idle threshold is exceeded (`last_active_at + 30 min < now`)  
**Then** the session must be invalidated server-side  
**And** the next API call or page load must return 401 and redirect to login  
**And** idle warning must be shown in the portal UI 5 minutes before expiry

### Concurrent session limit: max 3 per user
**Given** a user already has 3 active sessions (e.g., 3 different browsers)  
**When** they complete a new successful MFA verification  
**Then** the system must identify the oldest session by `created_at` and invalidate it before creating the new session  
**And** the total active session count must never exceed 3  
**And** the evicted session receives 401 on next use

### Explicit logout invalidates session immediately
**Given** a user clicks logout  
**When** the logout request is processed  
**Then** the session is deleted or marked invalid server-side immediately  
**And** the session token cannot be reused even if intercepted  
**And** `SESSION_INVALIDATED` is written to the audit log

### All session events are audit logged
**Given** any session lifecycle event occurs  
**When** the event completes  
**Then** `SESSION_CREATED`, `SESSION_EXPIRED` (idle or absolute), `SESSION_INVALIDATED` (logout or eviction) must all be written to the audit log with `timestamp`, `user_id`, `ip_address`, and `session_id`

## Technical Notes

**APIs:**
- `POST /auth/mfa/verify` → success: session/JWT issued; failure: attempt count incremented
- `POST /auth/session/extend` → resets `last_active_at` (idle timer only)
- `POST /auth/logout` → server-side session invalidation
- All protected endpoints: validate `mfa_verified=true` AND session not expired before processing

**Data:**
- `sessions` table: `session_id, user_id, created_at, last_active_at, invalidated_at`
- Absolute TTL: 8 hours from `created_at`. Idle TTL: 30 minutes from `last_active_at`
- `last_active_at` updated on every authenticated API call (lightweight)
- Concurrent session eviction: SELECT oldest WHERE `user_id = ? AND invalidated_at IS NULL`, then invalidate in same transaction as new session creation
- audit_logs events: `MFA_FAILED`, `MFA_CHALLENGE_BLOCKED`, `SESSION_CREATED`, `SESSION_EXPIRED`, `SESSION_INVALIDATED`

**Offer Logics:**
- MFA verify: constant-time hash comparison (bcrypt/argon2). Challenge single-use on success
- Session absolute TTL: 8 hours (backend config). Idle TTL: 30 minutes (backend config)
- Max concurrent sessions: 3 (backend config). Eviction: oldest by `created_at`

**Dependencies:**
- MFA challenge from LOG-03
- `audit_logs` table (INSERT-only for application DB user)

**Special focus:**
- Security: both TTLs enforced server-side — client-side idle timers are UX only, must not be trusted
- Security: concurrent session eviction must be atomic (same DB transaction as new session insert)
- Security: explicit logout must make token non-reusable immediately

## UI/UX Notes

- Input should auto-advance and accept paste of 6 digits
- "Back to login" link to restart flow safely
- Idle warning modal at 25 minutes idle: "Your session will expire in 5 minutes. Stay logged in?"
- "Stay logged in" resets idle timer only — absolute TTL continues from session creation

## QA / Test Considerations

**Primary flows:**
- Correct code on first attempt → session created → `SESSION_CREATED` logged → portal accessible
- Wrong code (attempt 1–4) → error with attempts remaining → eventual success
- Wrong code 5 times → challenge BLOCKED → "Too many attempts" → user re-login
- Code expired → "Code expired" → user resends → new code → success
- Session idle 30 min → invalidated → 401
- Session 8h → invalidated → 401
- 3 active sessions → new login → oldest evicted → still max 3
- Logout → token unusable immediately

**Edge Cases:**
- Two browser tabs submit code simultaneously → only first succeeds
- Code arrives late, user enters after 5 min TTL → "Code expired" even if correct digits
- Two concurrent logins at session limit → DB transaction prevents 4 sessions
- Absolute TTL expires during 5-min idle warning → absolute takes priority

**Business-Critical Must Not Break:**
- MFA failure counter (per challenge) must NOT increment `failed_login_attempts` — two separate counters
- After challenge BLOCKED, user must re-enter email and password
- No portal API accessible without MFA verification
- Session count must never exceed 3
- Logout must prevent token reuse even if intercepted
