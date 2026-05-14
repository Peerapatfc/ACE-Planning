# ACE-2050 · Sequence Diagrams: Force Change Password

**STORY-LOG-06** — 3 scenarios

| Scenario | Description |
|---|---|
| [01](#scenario-01-successful-password-change) | Happy path — token valid, new password passes all rules → JWT issued |
| [02](#scenario-02-history-reuse-failure) | New password matches one of last 5 → 422 inline error |
| [03](#scenario-03-invalid-or-expired-token) | Token not found / TTL elapsed / tampered → 401 + show error with link to /forgot-password |

> **Auth mechanism:** `POST /auth/password/change` uses one-time **reset token** (Redis `expired_reset:{tokenHash}`, issued by LOG-05 / LOG-08) — not a bearer JWT.  
> `confirm_password` = frontend-only, not sent to API.

---

## Scenario 01: Successful Password Change

```mermaid
sequenceDiagram
    actor User as User (Browser)
    participant GW as API Gateway
    participant Auth as orches-auth-service
    participant SVC as user-service
    participant DB as User DB (PostgreSQL)
    participant Redis as Redis

    User->>GW: POST /auth/password/change<br/>body: token + new_password

    Note over GW: @Public() — no JWT required.<br/>Identity proven by reset token.

    GW->>Auth: TCP change_password(rawToken, newPassword)

    rect rgb(255, 249, 196)
        Note over Auth,Redis: Step 1 — Validate Reset Token
        Auth->>Auth: tokenHash = SHA256(rawToken)
        Auth->>Redis: GET expired_reset:{tokenHash}
        Redis-->>Auth: userId or null

        alt token not found or expired
            Auth-->>GW: RpcException 401 INVALID_OR_EXPIRED_TOKEN
            GW-->>User: 401 — Reset link is invalid or has expired
        end
    end

    rect rgb(255, 243, 224)
        Note over Auth: Step 2 — Complexity Validation (no DB)
        Auth->>Auth: min 8 / max 64 chars<br/>at least 1 uppercase, 1 number, 1 special char
    end

    rect rgb(227, 242, 253)
        Note over Auth,DB: Step 3 — History Check + Atomic Commit (user-service)
        Auth->>SVC: TCP force_change_password(userId, newPassword)

        SVC->>DB: SELECT password_hash FROM users WHERE id = userId
        SVC->>DB: SELECT password_hash FROM user_password_history<br/>WHERE user_id = userId ORDER BY created_at DESC LIMIT 4
        DB-->>SVC: currentHash + historyHashes[0..3]

        Note over SVC: bcrypt.verify(newPwd, currentHash) → false ✓
        Note over SVC: bcrypt.verify(newPwd, each historyHash) → false ✓
        Note over SVC: ⚠ NEVER compare hash strings directly

        SVC->>SVC: newHash = bcrypt.hash(newPwd, 10)

        SVC->>DB: BEGIN TRANSACTION
        SVC->>DB: UPDATE users SET password_hash = newHash,<br/>password_changed_at = NOW() WHERE id = userId
        SVC->>DB: INSERT INTO user_password_history(user_id, password_hash)<br/>VALUES (userId, oldHash)
        SVC->>DB: DELETE oldest rows exceeding 5 per user
        SVC->>DB: UPDATE refresh_tokens SET revoked_at = NOW()<br/>WHERE user_id = userId AND revoked_at IS NULL
        SVC->>DB: COMMIT ✓
        DB-->>SVC: success
        SVC-->>Auth: success
    end

    rect rgb(237, 231, 246)
        Note over Auth,Redis: Step 4 — Consume Token + Issue JWT
        Auth->>Redis: DEL expired_reset:{tokenHash}
        Redis-->>Auth: OK

        GW->>GW: issueTokens(userId, tenantId)<br/>access_token = JWT.sign(sub, sid, email, tenantId)<br/>rawRefresh = randomBytes(40).hex()<br/>refreshHash = SHA256(rawRefresh)
        GW->>SVC: TCP store_refresh_token(user_id, token_hash, expires_at)
        SVC->>DB: INSERT INTO refresh_tokens
        DB-->>SVC: OK
        SVC-->>GW: stored
    end

    GW-->>User: 200 OK — access_token + refresh_token

    Note over User: Toast: Password updated successfully.<br/>Redirect to portal.

    Auth-)SVC: fire-and-forget TCP insert_password_audit<br/>action=password_change, result=success, ip, userAgent
    SVC-)DB: INSERT INTO user_password_audits
```

---

## Scenario 02: History Reuse Failure

```mermaid
sequenceDiagram
    actor User as User (Browser)
    participant GW as API Gateway
    participant Auth as orches-auth-service
    participant SVC as user-service
    participant DB as User DB (PostgreSQL)
    participant Redis as Redis

    User->>GW: POST /auth/password/change<br/>body: token + previously_used_password
    GW->>Auth: TCP change_password(rawToken, newPassword)

    Auth->>Auth: tokenHash = SHA256(rawToken)
    Auth->>Redis: GET expired_reset:{tokenHash}
    Redis-->>Auth: userId ✓

    Auth->>Auth: complexity validation ✓

    Auth->>SVC: TCP force_change_password(userId, newPassword)
    SVC->>DB: SELECT current hash + last 4 history
    DB-->>SVC: currentHash + historyHashes
    SVC->>SVC: bcrypt.verify(newPwd, one of the hashes) → true ✗

    SVC-->>Auth: RpcException 422 PASSWORD_HISTORY_REUSE

    Auth-->>GW: RpcException 422 PASSWORD_HISTORY_REUSE
    GW-->>User: 422 — You cant reuse any of your last 5 passwords.

    Note over User: Inline error under New password field.<br/>Token NOT consumed. No DB write.

    Auth-)SVC: fire-and-forget TCP insert_password_audit<br/>action=password_change_failed, failure_reason=history_reuse
    SVC-)DB: INSERT INTO user_password_audits
```

---

## Scenario 03: Invalid or Expired Token

```mermaid
sequenceDiagram
    actor User as User (Browser)
    participant GW as API Gateway
    participant Auth as orches-auth-service
    participant Redis as Redis

    Note over User: Covers two cases:<br/>① forced-reset TTL elapsed (15-min window missed)<br/>② token tampered / never existed<br/>Backend path identical — Redis returns null for both.

    User->>GW: POST /auth/password/change<br/>body: invalid_or_expired_token + new_password

    Note over GW: @Public() — no JWT required.

    GW->>Auth: TCP change_password(rawToken, newPassword)

    Auth->>Auth: tokenHash = SHA256(rawToken)
    Auth->>Redis: GET expired_reset:{tokenHash}
    Redis-->>Auth: null (not found or TTL expired)

    Auth-->>GW: RpcException 401 INVALID_OR_EXPIRED_TOKEN
    GW-->>User: 401 — Reset link is invalid or has expired.

    Note over User: Page shows error message:<br/>Your reset link has expired.<br/>Please use Forgot Password to request a new one.<br/>(link/button to /forgot-password)

    Note over GW: No DB access. No audit log.<br/>No userId available — token gone from Redis.
```

---

## Service Responsibility Split

| Responsibility | Service | Note |
|---|---|---|
| Token validation (Redis lookup) | `orches-auth-service` | SHA256(rawToken) → GET Redis |
| Complexity validation | `orches-auth-service` | no DB/bcrypt needed |
| bcrypt.verify (history check) | `user-service` | bcrypt lib lives here |
| bcrypt.hash (new password) | `user-service` | all crypto in one place |
| Atomic DB commit | `user-service` | owns DB access |
| Session invalidation (DB) | `user-service` | within same transaction |
| Token consumption (Redis DEL) | `orches-auth-service` | after user-service confirms success |
| JWT + refresh token issuance | `api-gateway` | matches existing `issueTokens()` pattern |
| Audit log write | `user-service` → `user_password_audits` | fire-and-forget via TCP from orches-auth-service |
