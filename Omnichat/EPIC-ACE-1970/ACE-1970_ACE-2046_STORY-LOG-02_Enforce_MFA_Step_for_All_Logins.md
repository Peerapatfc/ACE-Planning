# STORY-LOG-02: Enforce MFA Step for All Logins

**Status:** Backlog | **ClickUp:** [ACE-2046](https://app.clickup.com/t/86d2wav10) | **Epic:** [ACE-1970](https://app.clickup.com/t/86d2u6vzv)

## User Story

As a user (admin / supervisor / agent)
I want MFA to be required after I enter my email and password, with all pre-conditions checked before MFA proceeds
so that unauthorized access is prevented and every login attempt is recorded for security auditing.

## Detail / Description

**Scope of this story:** Enforce MFA for all users after password validation. All pre-conditions (lock state, email verification, password expiry) are checked before MFA is triggered. The `/auth/login` endpoint is rate-limited at API level. Every login attempt is written to the audit log.

## Acceptance Criteria

### MFA is always required
**Given** an active user account with a verified email  
**When** the user submits correct email and password  
**Then** the system must not create a fully authenticated session yet  
**And** must redirect to an MFA verification step

### MFA is not triggered when password is incorrect
**Given** an active user account  
**When** the user submits an incorrect email or password  
**Then** the system must return a generic login failure response  
**And** must not send an MFA code

### No partial session grants access
**Given** a user who has passed password validation but has not yet completed MFA  
**When** they attempt to access any portal page or protected API  
**Then** the system must return 401/403 and deny access until MFA is verified

### Login endpoint is rate-limited at API layer
**Given** requests arrive at `POST /auth/login`  
**When** the rate exceeds 20 requests per minute from a single IP, or 10 requests per minute targeting the same account  
**Then** the system must return HTTP 429 with a `Retry-After` header  
**And** rate limiting is enforced at API gateway or middleware level, independent of application-layer lockout  
**And** rate limit counters are stored in Redis with a sliding window TTL

### Every login attempt is written to the audit log
**Given** a login attempt completes (success or failure)  
**When** the response is returned to the client  
**Then** the system must write an audit log entry with: `timestamp (UTC)`, `event_type (LOGIN_ATTEMPT)`, `user_id or email`, `ip_address`, `user_agent`, `outcome (SUCCESS / FAILURE / BLOCKED)`  
**And** MFA-stage events (`MFA_CODE_SENT`, `MFA_VERIFIED`, `MFA_FAILED`, `MFA_CHALLENGE_BLOCKED`) are written by LOG-04; the `audit_logs` table is shared  
**And** audit log entries are append-only, no update or delete is permitted

## Technical Notes

**APIs:**
- `POST /auth/login` → returns `MFA_REQUIRED + mfa_challenge_id` (no full session yet)
- Rate limit: 20 req/min per IP, 10 req/min per account → HTTP 429 + `Retry-After` + `X-RateLimit-*` headers

**Data:**
- User fields: `role`, `email`, `email_verified_at`, `status`
- Auth state: `mfa_challenge_id` and status until verified/expired
- `audit_logs` table: `id, timestamp, event_type, user_id, email_at_event, ip_address, user_agent, outcome, metadata (JSONB)` — INSERT-only, application DB user has no UPDATE or DELETE on this table

**Integrations:**
- Redis (or equivalent) for rate limit counters

**Dependencies:**
- Redis infrastructure
- User/role model

**Special focus:**
- Security: rate limiting is a second layer on top of lockout (LOG-07), both must be active
- Security: audit log INSERT-only enforced at DB level, not just application level
- Performance: rate limit Redis operations are sub-millisecond; audit log writes must not block the response

## UI/UX Notes

- After password success → แสดงหน้า "Verify your sign-in" พร้อม 6-digit code input

## QA / Test Considerations

**Primary flows:**
- Correct password → redirected to MFA step; `LOGIN_ATTEMPT(SUCCESS)` logged
- Incorrect password → generic error; `LOGIN_ATTEMPT(FAILURE)` logged
- 21 rapid requests from same IP → 21st returns 429

**Edge Cases:**
- Rate limit Redis unavailable → fail-open with monitoring alert (do not break login entirely)
- Audit log write fails → log to error monitoring but do not block the login response

**Business-Critical Must Not Break:**
- No partial session grants portal access
- Rate limit headers must always be present on 429 responses
