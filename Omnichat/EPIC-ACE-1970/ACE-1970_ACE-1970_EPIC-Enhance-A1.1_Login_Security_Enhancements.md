# EPIC-Enhance-A1.1: Login Security Enhancements

**Status:** Backlog | **ClickUp:** [ACE-1970](https://app.clickup.com/t/86d2u6vzv) | **Product:** Omni

## Epic Overview

เพิ่มความปลอดภัยของระบบ Login ทั้งหมด ครอบคลุม invite flow, MFA enforcement, temporary password, account lockout, และ field-level encryption สำหรับข้อมูลลูกค้า

## Associated Stories

| Story | ACE ID | Name | Content |
|---|---|---|---|
| LOG-01 | ACE-2045 | Admin invite flow | Invite email, email verification, status tracking |
| LOG-02 | ACE-2046 | Enforce MFA step for all logins | MFA gate, rate limiting, audit log |
| LOG-03 | ACE-2047 | Generate & email 6-digit TOTP code with resend controls | OTP generation, email delivery, resend cooldown |
| LOG-04 | ACE-2048 | Verify MFA code | OTP validation, session management, idle/absolute TTL |
| LOG-05 | ACE-2049 | Auto-generate a new temporary password and email it | Password expiry, temp password issuance |
| LOG-06 | ACE-2050 | Force user to change password after temporary password login | Forced change gate, complexity, history check |
| LOG-07 | ACE-2051 | Soft lock + Hard lock | 5-fail soft lock (15 min), 10-fail hard lock |
| LOG-08 | ACE-2052 | Forgot password | Self-service recovery, atomic lock clear |
| LOG-09 | ACE-2053 | Encrypt sensitive customer data | AES-256-GCM, AWS KMS Envelope Encryption |

## Dependency Chain

```
LOG-01 (Invite) → ใช้ temp password mechanism ของ LOG-05
LOG-02 (MFA Enforce) → trigger LOG-03 challenge → verify ด้วย LOG-04
LOG-05 (Temp Password) → set must_change_password → trigger LOG-06
LOG-07 (Lock) → unlock โดย LOG-08
LOG-08 (Forgot Password) → reuse LOG-05 mechanism → trigger LOG-06
LOG-09 (Encryption) → standalone
```

## User Status Lifecycle

| สถานะ | Login ได้? | เปลี่ยนจาก/ไป |
|---|---|---|
| Invited | ❌ | → Active (verify), → Expired (7d) |
| Expired | ❌ | → Invited (admin resend) |
| Active | ✅ | → Invited (email change), → Soft locked, → Hard locked |
| Soft locked | ❌ (15 min) | → Active (auto-expire / reset password) |
| Hard locked | ❌ (permanent) | → Active (reset password only) |

## Counter Separation (Critical)

| Counter | นับอะไร | ใช้ทำอะไร |
|---|---|---|
| `failed_login_attempts` | Password fails | Trigger soft lock (≥5) / hard lock (≥10) |
| MFA attempt (per challenge) | OTP code fails | Block challenge หลัง 5 ครั้ง (ไม่เกี่ยวกับ lock) |

ห้ามปนกัน — MFA fail ≠ password fail

## Session Rules

| Rule | Value |
|---|---|
| Absolute TTL | 8 hours from created_at |
| Idle timeout | 30 minutes from last_active_at |
| Idle warning | 5 minutes before idle expiry |
| Max concurrent sessions | 3 per user (oldest evicted) |

## Email Templates Required

| Template | Trigger | Story |
|---|---|---|
| Invitation email | Admin creates user | LOG-01 |
| Temporary password email | Password expired / forgot password | LOG-05, LOG-08 |
| MFA code email | Every successful password login | LOG-03 |
| Soft lock notification | 5 password fails | LOG-07 |
| Hard lock notification | 10 password fails | LOG-07 |
