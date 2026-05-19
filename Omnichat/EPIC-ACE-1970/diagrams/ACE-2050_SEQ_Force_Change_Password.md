# ACE-2050 · Sequence Diagrams: Force Change Password

**STORY-LOG-06** — 3 scenarios

| Scenario | Description |
|---|---|
| [01](#scenario-01-successful-password-change) | Happy path — step 1 exchanges reset token for scoped JWT; step 2 new password passes all rules → 200 OK, redirect to /login |
| [02](#scenario-02-history-reuse-failure) | New password matches one of last 5 → 422 inline error |
| [03](#scenario-03-invalid-or-expired-token) | Token not found / TTL elapsed / tampered → 401 + show error with link to /forgot-password |

> **Auth mechanism:** Two-step flow —  
> 1. `POST /auth/expired-reset/validate { token }` validates reset token and returns short-lived **scoped JWT** (`scope: password_change`, TTL 15 min).  
> 2. `POST /auth/expired-reset/complete { scoped_token, new_password }` verifies scoped JWT and finalizes the change, returning 200 OK — no token issued; FE redirects to /login.  
> Reset token stored in Redis (`expired_reset:{tokenHash}`, issued by LOG-05 / LOG-08, TTL 900 s).  
> `confirm_password` = frontend-only, not sent to API.

---

## Scenario 01: Successful Password Change

```mermaid
sequenceDiagram
    autonumber
    participant FE as browser
    participant GW as api-gateway
    participant AUTH as orches-auth-service
    participant SVC as user-service
    participant DB as user-db
    participant R as Redis

    Note over FE,R: Step 1 — Exchange reset token for scoped JWT

    FE->>GW: POST /auth/expired-reset/validate { token }
    Note over GW: @Public() — no JWT required, identity proven by reset token

    GW->>AUTH: auth.validate_expired_reset(rawToken)

    rect rgb(255,249,196)
    Note over AUTH,R: 1. Validate Reset Token

    AUTH->>AUTH: tokenHash = SHA-256(rawToken)
    AUTH->>R: GET expired_reset:{tokenHash}
    Note over R: key   → expired_reset:{tokenHash}<br/>value → userId (issued by LOG-05 / LOG-08)<br/>TTL   → 900s (15 min)
    R-->>AUTH: userId ✓

    AUTH->>AUTH: issue scopedJWT { sub: userId, scope: 'password_change', redis_key }
    Note over AUTH: scopedJWT TTL = 15 min
    AUTH-->>GW: scopedJWT
    end

    GW-->>FE: 200 OK { scoped_token: scopedJWT }

    Note over FE,R: Step 2 — Submit new password using scoped JWT

    FE->>GW: POST /auth/expired-reset/complete { scoped_token, new_password }
    Note over GW: @Public() — authenticated by scoped JWT, not bearer JWT

    GW->>AUTH: auth.complete_expired_reset(scopedToken, newPassword)

    rect rgb(255,249,196)
    Note over AUTH,R: 2. Verify Scoped JWT

    AUTH->>AUTH: JWT.verify(scopedToken) → { sub: userId, scope, redis_key }
    AUTH->>AUTH: assert scope === 'password_change'
    AUTH->>R: GET redis_key
    R-->>AUTH: userId ✓ (still valid)
    end

    rect rgb(255,243,224)
    Note over AUTH: 3. Complexity Validation (no DB required)

    AUTH->>AUTH: min 8 / max 64 chars — 1 uppercase, 1 number, 1 special char
    end

    rect rgb(227,242,253)
    Note over AUTH,DB: 4. History Check + Atomic Commit

    AUTH->>SVC: change_password(userId, newPassword)

    SVC->>DB: SELECT current hash + last 4 history hashes
    Note over DB: SELECT password_hash FROM users WHERE id = userId<br/>SELECT password_hash FROM user_password_history<br/>  WHERE user_id = userId ORDER BY created_at DESC LIMIT 4
    DB-->>SVC: currentHash + historyHashes[0..3]

    Note over SVC: bcrypt.verify(newPwd, currentHash) → false ✓<br/>bcrypt.verify(newPwd, each historyHash) → false ✓<br/>⚠ NEVER compare hash strings directly

    SVC->>SVC: newHash = bcrypt.hash(newPwd, 10)

    SVC->>DB: BEGIN TRANSACTION
    SVC->>DB: UPDATE users SET password_hash, password_changed_at, password_voided_at = NULL
    SVC->>DB: INSERT INTO user_password_history (userId, oldHash)
    SVC->>DB: DELETE oldest rows exceeding 5 per user
    SVC->>DB: REVOKE all active refresh_tokens for user
    SVC->>DB: COMMIT ✓
    DB-->>SVC: success
    SVC-->>AUTH: success
    end

    rect rgb(237,231,246)
    Note over AUTH,R: 5. Consume Token + Return Success

    AUTH->>R: DEL redis_key
    R-->>AUTH: OK
    AUTH-->>GW: success (userId)
    end

    GW-->>FE: 200 OK { message: "Password changed successfully" }
    Note over FE: Toast: Password changed successfully.<br/>Redirect to /login — user signs in manually with new password.

    AUTH-)SVC: emit insert_password_audit { action=password_change, result=success }
    SVC-)DB: INSERT INTO user_password_audits
```

---

## Scenario 02: History Reuse Failure

```mermaid
sequenceDiagram
    autonumber
    participant FE as browser
    participant GW as api-gateway
    participant AUTH as orches-auth-service
    participant SVC as user-service
    participant DB as user-db
    participant R as Redis

    Note over FE: Step 1 (validate) already succeeded — scoped_token in hand

    FE->>GW: POST /auth/expired-reset/complete { scoped_token, previously_used_password }
    GW->>AUTH: auth.complete_expired_reset(scopedToken, newPassword)

    rect rgb(255,249,196)
    Note over AUTH,R: 1. Verify Scoped JWT

    AUTH->>AUTH: JWT.verify(scopedToken) → { sub: userId, scope, redis_key }
    AUTH->>R: GET redis_key
    R-->>AUTH: userId ✓
    end

    rect rgb(255,243,224)
    Note over AUTH: 2. Complexity Validation ✓

    AUTH->>AUTH: complexity checks pass
    end

    rect rgb(227,242,253)
    Note over AUTH,DB: 3. History Check — REUSE DETECTED

    AUTH->>SVC: change_password(userId, newPassword)
    SVC->>DB: SELECT current hash + last 4 history hashes
    DB-->>SVC: currentHash + historyHashes

    SVC->>SVC: bcrypt.verify(newPwd, one of the hashes) → true ✗

    SVC-->>AUTH: 422 PASSWORD_HISTORY_REUSE
    AUTH-->>GW: 422 PASSWORD_HISTORY_REUSE
    GW-->>FE: 422 You can't reuse any of your last 5 passwords

    Note over FE: Inline error under New password field<br/>Token NOT consumed — user can retry with a different password
    end

    AUTH-)SVC: emit insert_password_audit { action=password_change_failed, reason=history_reuse }
    SVC-)DB: INSERT INTO user_password_audits
```

---

## Scenario 03: Invalid or Expired Token

```mermaid
sequenceDiagram
    autonumber
    participant FE as browser
    participant GW as api-gateway
    participant AUTH as orches-auth-service
    participant R as Redis

    Note over FE: Covers two cases:<br/>① forced-reset TTL elapsed (15-min window missed)<br/>② token tampered / never existed<br/>Backend path identical — Redis returns null for both

    FE->>GW: POST /auth/expired-reset/validate { invalid_or_expired_token }
    Note over GW: @Public() — no JWT required

    GW->>AUTH: auth.validate_expired_reset(rawToken)

    rect rgb(255,249,196)
    Note over AUTH,R: 1. Validate Reset Token — FAILED

    AUTH->>AUTH: tokenHash = SHA-256(rawToken)
    AUTH->>R: GET expired_reset:{tokenHash}
    R-->>AUTH: null (not found or TTL expired)

    AUTH-->>GW: 401 INVALID_OR_EXPIRED_TOKEN
    GW-->>FE: 401 Reset link is invalid or has expired
    end

    Note over FE: Your reset link has expired.<br/>Please use Forgot Password to request a new one.
    Note over GW: No DB access. No audit log.<br/>No userId available — token gone from Redis.
```

---

## Service Responsibility Split

| Responsibility | Service | Note |
|---|---|---|
| Token validation (Redis lookup) | `orches-auth-service` | SHA256(rawToken) → GET Redis |
| Scoped JWT issuance | `orches-auth-service` | `{ sub: userId, scope: 'password_change', redis_key }`, TTL 15 min |
| Scoped JWT verification | `orches-auth-service` | assert scope === 'password_change', re-verify redis_key still in Redis |
| Complexity validation | `orches-auth-service` | no DB/bcrypt needed |
| bcrypt.verify (history check) | `user-service` | bcrypt lib lives here |
| bcrypt.hash (new password) | `user-service` | all crypto in one place |
| Atomic DB commit | `user-service` | owns DB access |
| Session invalidation (DB) | `user-service` | within same transaction |
| Reset `password_voided_at` | `user-service` | SET NULL within same transaction |
| Token consumption (Redis DEL) | `orches-auth-service` | after user-service confirms success |
| Post-change response | `api-gateway` | 200 OK { message } — no token issued; FE redirects user to /login |
| Audit log write | `user-service` → `user_password_audits` | fire-and-forget via TCP from orches-auth-service |
