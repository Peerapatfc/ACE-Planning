# EPIC-ACE-1970: Story Task Breakdown (With Repo Context)

Task แต่ละ story พร้อมคำอธิบายว่าทำอะไร — อิงจากสิ่งที่มีอยู่แล้วใน repo จริง (เฉพาะที่ยังต้องทำ)

> **Legend:** 🔧 มีโค้ดอยู่แล้วแต่ต้องแก้ | (ไม่มีไอคอน) สร้างใหม่ทั้งหมด

---

## สิ่งที่มีอยู่แล้วใน repo (อย่าทำซ้ำ)

| สิ่งที่มี | ไฟล์ | หมายเหตุ |
|----------|------|----------|
| `/auth/login`, `/auth/logout`, `/auth/refresh` | `api-gateway/src/auth/auth.service.ts` | JWT stateless — ยังไม่มี MFA gate |
| Invitation CRUD (create, resend, cancel, accept) | `tenant-service/src/invitations/` | status: pending/accepted/cancelled — ต่างจาก spec |
| Invite email template + SMTP delivery | `notification-service/src/email/` | template: invitation, register-success — ยังไม่มี MFA/lock templates |
| `is_email_verified` (Boolean) บน User | `user-service/prisma/schema.prisma` | มีแค่ boolean ไม่มี timestamp `email_verified_at` |
| bcrypt password hashing | `user-service/src/users/users.service.ts` | ใช้งานได้ปกติ |
| Redis blocklist (block user instantly) | `api-gateway/src/blocklist/` | TTL-based, ใช้ block user ที่ถูกลบออกจาก workspace |
| Global throttler (3-tier: 1s/10s/1min) | `api-gateway/src/app.module.ts` | fixed window ทั้ง workspace — ไม่ใช่ sliding window per-IP/per-account |
| SHA-256 token hashing (invitation) | `tenant-service/src/invitations/` | pattern นี้ reuse ได้กับ invite token |
| Frontend auth (cookies, silent refresh) | `workspace-admin/src/server/auth.ts` | httpOnly cookie, ace_access_token/ace_refresh_token |

---

## LOG-01 — Admin Invite Flow `8 SP`

> **เป้าหมาย:** เชื่อม invite flow เดิมที่มีอยู่ให้ครบ — เพิ่ม email verification logic, ออก temp password หลัง verify, block login ถ้ายังไม่ verify
> **SP เหตุผล:** cross 4 services (api-gateway + user-service + tenant-service + notification-service + frontend) + Task 1.2 แก้ status enum บน live invite system เสี่ยงสูง

---

### Task 1.1 🔧 — DB: เพิ่ม `email_verified_at` + `invite_expires_at` บน User
**ทำอะไร:** เพิ่ม timestamp fields บน User table ใน user-service  
**ทำไม:** มีแค่ `is_email_verified` (boolean) — ไม่มี timestamp ว่า verify เมื่อไหร่ และ invite หมดอายุเมื่อไหร่

**ไฟล์ที่แก้:** `apps/user-service/prisma/schema.prisma`
```sql
email_verified_at    TIMESTAMP WITH TIME ZONE  -- null = ยังไม่ verify
invite_expires_at    TIMESTAMP WITH TIME ZONE  -- null = ไม่มี invite pending
```

---

### Task 1.2 🔧 — แก้ invitation status ให้ตรงกับ spec
**ทำอะไร:** ปัจจุบัน status เป็น `pending/accepted/cancelled` — ต้องรองรับ `Invited/Expired/Active` ตาม story  
**ทำไม:** logic Expired (auto เมื่อ expires_at ผ่าน) และ Active (หลัง verify) ไม่มีอยู่เลย

**ไฟล์ที่แก้:** `apps/tenant-service/src/invitations/invitations.service.ts`  
**Logic เพิ่ม:** lazy evaluate Expired status ตอน login หรือ verify link (ไม่ต้องทำ cron)

---

### Task 1.3 — Email verification endpoint
**ทำอะไร:** สร้าง endpoint ที่รับ token จาก invite link → verify → เซ็ต `email_verified_at` → เปลี่ยน status เป็น Active  
**ทำไม:** ปัจจุบัน `GET /auth/invite/:token` แค่ accept invite สร้าง session — ไม่ได้ทำ verification flow แบบ spec

**ไฟล์ที่แก้:** `apps/api-gateway/src/auth/auth.controller.ts` + `auth.service.ts`  
**หลัง verify:** ต้อง trigger Task 1.4 (ออก temp password ทันที)

---

### Task 1.4 — ออก temp password หลัง email verification
**ทำอะไร:** ทันทีที่ verify สำเร็จ → generate temp password → email → set `must_change_password = true`  
**ทำไม:** spec กำหนดว่า user ไม่ได้ set password เอง — ระบบออกให้แล้วบังคับเปลี่ยน (reuse LOG-05 mechanism)

**Dependency:** ต้องทำหลัง LOG-05 เสร็จ

---

### Task 1.5 🔧 — Block login ถ้า `email_verified_at` เป็น null
**ทำอะไร:** แก้ `/auth/login` ให้ check `email_verified_at` ก่อน validate password — block พร้อม message generic  
**ทำไม:** ปัจจุบัน login ไม่ check verification status — unverified user login ได้

**ไฟล์ที่แก้:** `apps/api-gateway/src/auth/auth.service.ts`  
**ข้อควรระวัง:** message ต้องไม่บอกว่า account อยู่สถานะ Invited vs Expired (non-enumerating)

---

### Task 1.6 — UI: Status column ใน User Management table
**ทำอะไร:** แสดง status ของ member แต่ละคน: Active / Invited / Expired / Soft locked / Hard locked  
**ทำไม:** Admin ต้องเห็นได้ว่า user ไหน pending invite หรือ lock อยู่

---

## LOG-02 — Enforce MFA Step for All Logins `8 SP`

> **เป้าหมาย:** เพิ่ม MFA gate ใน login flow, sliding window rate limit บน /auth/login, audit log ทุก attempt
> **SP เหตุผล:** Task 2.2 breaking change หลัก (login ไม่ออก JWT ทันทีอีกต่อไป) + Task 2.4 custom Redis sliding window ที่ต้องเขียนเอง (throttler เดิมใช้ไม่ได้)

---

### Task 2.1 — DB: สร้าง `audit_logs` table
**ทำอะไร:** สร้างตาราง INSERT-only สำหรับบันทึกทุก security event  
**ทำไม:** ไม่มี audit log อยู่เลย — compliance requirement

```sql
-- user-service หรือ api-gateway (ตาม architecture decision)
id           UUID PRIMARY KEY
timestamp    TIMESTAMP WITH TIME ZONE DEFAULT NOW()
event_type   VARCHAR   -- LOGIN_ATTEMPT, MFA_FAILED, SESSION_CREATED, etc.
user_id      UUID      -- nullable (กรณี email ไม่พบ)
email_at_event VARCHAR
ip_address   VARCHAR
user_agent   TEXT
outcome      VARCHAR   -- SUCCESS | FAILURE | BLOCKED
metadata     JSONB
-- ห้าม UPDATE/DELETE ที่ application DB user ระดับ DB
```

---

### Task 2.2 🔧 — แก้ `/auth/login` ให้ return MFA_REQUIRED แทน full session
**ทำอะไร:** เมื่อ password ถูก → ไม่ออก JWT ทันที → return `{ status: 'MFA_REQUIRED', mfa_challenge_id }` แทน  
**ทำไม:** ปัจจุบัน login ถูก password → ออก JWT เลย — ไม่มี MFA gate เลย

**ไฟล์ที่แก้:** `apps/api-gateway/src/auth/auth.service.ts`, `auth.controller.ts`

---

### Task 2.3 🔧 — เพิ่ม pre-condition check order ใน login
**ทำอะไร:** เรียง check ก่อน MFA: (1) email verified? (2) soft/hard locked? (3) password expired? (4) password correct? → MFA  
**ทำไม:** ปัจจุบัน login ข้าม check เหล่านี้ทั้งหมด — แต่ละ condition ต้องมา order ที่ถูกต้อง

---

### Task 2.4 — Sliding window rate limit บน `/auth/login`
**ทำอะไร:** rate limit เฉพาะ endpoint นี้ด้วย Redis ZADD/ZCOUNT (sliding window) — 20 req/min per IP + 10 req/min per account  
**ทำไม:** throttler ที่มีอยู่เป็น fixed window และ global ทุก endpoint — ไม่ใช่ sliding window และไม่ per-account

**Pattern:**
```typescript
// Redis sliding window
ZADD rate:ip:{ip} NX score=now() member=requestId
ZREMRANGEBYSCORE rate:ip:{ip} 0 (now - 60000)
ZCOUNT rate:ip:{ip} (now - 60000) now  // > 20 → 429
```

---

### Task 2.5 — Write `LOGIN_ATTEMPT` ไปยัง audit_log
**ทำอะไร:** หลังทุก login attempt → บันทึก event พร้อม outcome (SUCCESS/FAILURE/BLOCKED)  
**ทำไม:** ไม่มี audit trail ของ login เลย — ต้องมีสำหรับ security monitoring

---

## LOG-03 — Generate & Email 6-digit OTP `5 SP`

> **เป้าหมาย:** สร้าง MFA challenge system — generate OTP, hash เก็บ, email ส่ง, resend controls
> **SP เหตุผล:** contained — DB table + generate + email + resend controls อยู่ใน scope เดียว ไม่ cross service ซับซ้อน

---

### Task 3.1 — DB: สร้าง `mfa_challenges` table
**ทำอะไร:** ตารางเก็บ OTP challenge แต่ละ login attempt  
**ทำไม:** ไม่มีอยู่เลย — MFA ทั้งระบบต้องการตารางนี้

```sql
id           UUID PRIMARY KEY
user_id      UUID NOT NULL
code_hash    VARCHAR NOT NULL     -- hash ของ OTP ห้ามเก็บ plaintext
expires_at   TIMESTAMP            -- 5 นาที
status       VARCHAR              -- PENDING | VERIFIED | EXPIRED | BLOCKED
resend_count INT DEFAULT 0
last_sent_at TIMESTAMP
attempt_count INT DEFAULT 0      -- จำนวน verify ที่ผิด (max 5)
created_at   TIMESTAMP
```

---

### Task 3.2 — 6-digit OTP generation + hash storage
**ทำอะไร:** generate random 6-digit code → bcrypt hash → เก็บแค่ hash  
**ทำไม:** ห้ามเก็บ OTP plaintext — ถ้า DB leak จะได้ไม่เจอ code จริง

---

### Task 3.3 — POST `/auth/mfa/challenge` endpoint
**ทำอะไร:** สร้าง challenge record + generate OTP + ส่ง email  
**ทำไม:** ไม่มีอยู่ — เป็น entry point ของ MFA flow ทั้งหมด

---

### Task 3.4 — POST `/auth/mfa/resend` endpoint + cooldown
**ทำอะไร:** invalidate code เดิม → generate ใหม่ → email ใหม่ → enforce 30s cooldown + max 5 resend/hr  
**ทำไม:** ป้องกัน user spam resend และป้องกันคนนอก request OTP ซ้ำ

---

### Task 3.5 — Email template: MFA verification code
**ทำอะไร:** สร้าง email template ใหม่สำหรับส่ง OTP code  
**ทำไม:** มีแค่ invitation + register-success templates — ไม่มี MFA template

**ไฟล์ที่แก้:** `apps/notification-service/src/email/email.service.ts` + template ใหม่

---

## LOG-04 — Verify MFA Code `13 SP`

> **เป้าหมาย:** validate OTP → สร้าง session → enforce TTL rules — session management ทั้งหมดต้องสร้างใหม่
> **SP เหตุผล:** 10 tasks: idle TTL ต้อง hook ทุก authenticated request (DB write ทุก call), concurrent session eviction ต้อง atomic transaction, UI idle warning modal — underestimated ใน round แรก (8 → 13)

---

### Task 4.1 — DB: สร้าง `sessions` table
**ทำอะไร:** ตารางเก็บ session ทุก active login  
**ทำไม:** ปัจจุบัน stateless JWT ล้วนๆ — ไม่มี server-side session tracking เลย → ไม่รู้ว่ามี session กี่อัน ไม่สามารถ enforce idle/absolute TTL ได้

```sql
session_id     UUID PRIMARY KEY
user_id        UUID NOT NULL
created_at     TIMESTAMP         -- absolute TTL: created_at + 8h
last_active_at TIMESTAMP         -- idle TTL: last_active_at + 30min
invalidated_at TIMESTAMP         -- null = still active
ip_address     VARCHAR
user_agent     TEXT
```

---

### Task 4.2 — POST `/auth/mfa/verify` endpoint
**ทำอะไร:** รับ OTP → constant-time hash compare → ถ้าถูก: create session + ออก JWT  
**ทำไม:** ไม่มีอยู่ — เป็นขั้นตอนสุดท้ายของ login flow

**ข้อควรระวัง:** MFA attempt counter อยู่บน challenge (max 5) — ห้ามนับรวมกับ `failed_login_attempts`

---

### Task 4.3 — MFA attempt counter + BLOCKED state
**ทำอะไร:** นับจำนวน verify ที่ผิดบน challenge record — ครบ 5 → mark BLOCKED + force re-login  
**ทำไม:** ต้องแยก counter นี้ออกจาก `failed_login_attempts` ของ LOG-07 อย่างเด็ดขาด

---

### Task 4.4 — Session absolute TTL enforcement (8h)
**ทำอะไร:** JWT guard ต้อง check `session.created_at + 8h > now()` — ถ้าเกิน → invalidate + 401  
**ทำไม:** ปัจจุบัน JWT แค่ check signature — ไม่มี absolute TTL จาก session table

---

### Task 4.5 — Session idle TTL enforcement (30min)
**ทำอะไร:** ทุก authenticated request → อัปเดต `last_active_at` + check ว่าเกิน 30min ไหม  
**ทำไม:** ไม่มี idle timeout เลย — session ปัจจุบันอยู่ได้ตลอดตาม JWT expiry (1d)

---

### Task 4.6 — Concurrent session limit: max 3 per user
**ทำอะไร:** ก่อนสร้าง session ใหม่ → count active sessions → ถ้า >= 3 → evict oldest (by `created_at`) atomically  
**ทำไม:** ป้องกัน account sharing และ session hijack

---

### Task 4.7 — Audit log: MFA events
**ทำอะไร:** write `MFA_FAILED`, `MFA_CHALLENGE_BLOCKED` พร้อม attempt_count + ip_address  
**ทำไม:** MFA failure ต้องบันทึกแยกจาก login attempt

---

### Task 4.8 — Audit log: Session events
**ทำอะไร:** write `SESSION_CREATED`, `SESSION_EXPIRED`, `SESSION_INVALIDATED` พร้อม session_id + user_id  
**ทำไม:** compliance requirement — ต้องรู้ว่า session ใครหมดอายุเมื่อไหร่

---

### Task 4.9 🔧 — อัปเดต `/auth/logout` ให้ invalidate session + audit
**ทำอะไร:** แก้ logout endpoint ให้ mark session เป็น `invalidated_at = now()` + write `SESSION_INVALIDATED` ด้วย  
**ทำไม:** logout มีอยู่แล้วแต่แค่ revoke refresh token — ยังไม่ invalidate session table

**ไฟล์ที่แก้:** `apps/api-gateway/src/auth/auth.service.ts`

---

### Task 4.10 — UI: Idle warning modal (25min)
**ทำอะไร:** แสดง modal "เซสชันจะหมดอายุใน 5 นาที" เมื่อ idle ถึง 25min — ปุ่ม "Stay logged in" reset idle เท่านั้น  
**ทำไม:** UX requirement — ไม่ควรให้ session หมดอายุโดยไม่แจ้ง

---

## LOG-05 — Auto-generate Temporary Password `5 SP`

> **เป้าหมาย:** detect รหัสผ่านหมดอายุ (90 วัน) → ออก temp password อัตโนมัติ → email → force change
> **SP เหตุผล:** foundation story ที่ LOG-01, LOG-06, LOG-08 depend — Task 5.3 temp password generator ต้องทำดี reusable + testable มาก เดิมให้ 3 SP ต่ำเกินไป

---

### Task 5.1 — DB: เพิ่ม fields บน User
**ทำอะไร:** เพิ่ม fields ที่จำเป็นสำหรับ password expiry + temp password flow  
**ทำไม:** ไม่มีสักตัวเลย — ปัจจุบันไม่มี password expiry concept

**ไฟล์ที่แก้:** `apps/user-service/prisma/schema.prisma`
```sql
must_change_password       BOOLEAN DEFAULT false
password_last_changed_at   TIMESTAMP WITH TIME ZONE
temporary_password_issued_at TIMESTAMP WITH TIME ZONE  -- cooldown check
```

---

### Task 5.2 🔧 — `/auth/login`: detect 90-day password expiry
**ทำอะไร:** เพิ่ม check ใน login flow — ถ้า `password_last_changed_at + 90d < now()` → trigger temp password  
**ทำไม:** ไม่มี expiry logic เลย ใน login flow

**ไฟล์ที่แก้:** `apps/api-gateway/src/auth/auth.service.ts`

---

### Task 5.3 — Temp password generator
**ทำอะไร:** generate random 12-16 char string ที่ผ่าน complexity rules + ไม่ซ้ำ 5 รหัสผ่านล่าสุด  
**ทำไม:** ต้องเป็น function ที่ reuse ได้โดย LOG-08 (Forgot Password) ด้วย

---

### Task 5.4 — Email template: Temporary password
**ทำอะไร:** สร้าง email template สำหรับส่ง temp password ให้ user  
**ทำไม:** ไม่มี template นี้ใน notification-service

---

### Task 5.5 — 10-minute cooldown per account
**ทำอะไร:** check `temporary_password_issued_at` — ถ้าน้อยกว่า 10 นาที → ไม่ออกใหม่ → ไม่ spam inbox  
**ทำไม:** ป้องกัน user กด login ซ้ำๆ แล้วได้ email หลายฉบับ

---

## LOG-06 — Force Change Password `8 SP`

> **เป้าหมาย:** block portal ทั้งหมดถ้า must_change_password=true, validate complexity + history 5 รหัสผ่านล่าสุด
> **SP เหตุผล:** Task 6.3 ต้อง enforce ทั้งสองชั้น (backend middleware + Next.js frontend route guard) + UI force change screen มี inline real-time requirements checklist

---

### Task 6.1 — DB: สร้าง `user_password_history` table
**ทำอะไร:** เก็บ hash ของ 5 รหัสผ่านล่าสุดต่อ user  
**ทำไม:** ไม่มีอยู่เลย — ต้องมีเพื่อ check reuse

```sql
id           UUID PRIMARY KEY
user_id      UUID NOT NULL
password_hash VARCHAR NOT NULL
created_at   TIMESTAMP
-- KEEP only 5 most recent per user (delete oldest on insert)
```

---

### Task 6.2 — POST `/auth/password/change` endpoint
**ทำอะไร:** validate complexity + check 5 history via bcrypt.verify → update hash → clear `must_change_password` → invalidate other sessions  
**ทำไม:** ไม่มี endpoint นี้อยู่เลย

**ข้อควรระวัง:** ต้องใช้ `bcrypt.verify(newPwd, eachHistoryHash)` — ห้าม compare hash โดยตรง

---

### Task 6.3 — Route guard: block portal ถ้า `must_change_password = true`
**ทำอะไร:** ทุก protected route → check flag นี้ → ถ้า true → redirect ไปหน้า change password  
**ทำไม:** ป้องกัน user ข้าม force change ด้วย direct URL หรือ API call

**ต้องทำทั้ง:** backend middleware + frontend route guard ใน Next.js

---

### Task 6.4 — Session invalidation หลัง password change
**ทำอะไร:** หลัง change password สำเร็จ → invalidate sessions ทั้งหมด ยกเว้น current session  
**ทำไม:** ป้องกัน session ที่ขโมยไปยังใช้ได้หลังเปลี่ยนรหัสผ่าน

---

### Task 6.5 — UI: Force change password screen
**ทำอะไร:** หน้าบังคับเปลี่ยนรหัสผ่าน — temp pw + new pw + confirm + inline requirements checklist  
**ทำไม:** ไม่มีหน้านี้อยู่เลยใน workspace-admin

---

## LOG-07 — Soft Lock + Hard Lock `8 SP`

> **เป้าหมาย:** 5 fail → soft lock 15min, 10 fail → hard lock ถาวร — ทั้งคู่ unlock ได้ด้วย LOG-08
> **SP เหตุผล:** Task 7.3 counter increment ต้องใช้ SELECT FOR UPDATE กัน race condition, 2 email templates + 2 UI screens (countdown timer) — งาน frontend เยอะกว่าที่เห็น

---

### Task 7.1 — DB: เพิ่ม lock fields บน User
**ทำอะไร:** เพิ่ม 3 fields สำหรับ lock state tracking  
**ทำไม:** ไม่มีอยู่เลย ใน User table

**ไฟล์ที่แก้:** `apps/user-service/prisma/schema.prisma`
```sql
failed_login_attempts INT DEFAULT 0
soft_locked_until     TIMESTAMP WITH TIME ZONE  -- null = ไม่ locked
hard_locked           BOOLEAN DEFAULT false
```

---

### Task 7.2 🔧 — `/auth/login`: check lock state ก่อน validate password
**ทำอะไร:** ก่อน bcrypt compare → check soft lock (expired?) + hard lock → ถ้า locked → return error ทันที  
**ทำไม:** ปัจจุบัน login ไม่ check lock เลย

**Error codes:**
- Soft locked: `SOFT_LOCKED` + `retry_after` timestamp
- Hard locked: `HARD_LOCKED`

---

### Task 7.3 🔧 — `/auth/login`: increment counter บน fail, reset บน success
**ทำอะไร:** password ผิด → `failed_login_attempts += 1` (transactional) → ถ้าถึง threshold → trigger lock  
**ทำไม:** counter logic ไม่มี — ปัจจุบัน login fail แค่ return error ไม่ track

**ข้อสำคัญ:** ต้อง SELECT FOR UPDATE หรือ atomic increment ป้องกัน race condition บน concurrent request

---

### Task 7.4 — Soft lock trigger (5 fails)
**ทำอะไร:** `failed_login_attempts = 5` → set `soft_locked_until = now() + 15min` → send lock email  
**ทำไม:** เป็น logic ใหม่ทั้งหมด

---

### Task 7.5 — Hard lock trigger (10 fails)
**ทำอะไร:** `failed_login_attempts = 10` → set `hard_locked = true` → send hard lock email  
**ทำไม:** soft lock expire แล้ว fail ต่อ counter ยังนับต่อ — ไม่ reset ตอน soft lock expire

---

### Task 7.6 — Email templates: Soft lock + Hard lock notification
**ทำอะไร:** สร้าง 2 email templates ใน notification-service  
**ทำไม:** ไม่มี templates เหล่านี้เลย

---

### Task 7.7 — UI: Soft lock screen (countdown + reset link)
**ทำอะไร:** หน้า error แสดง countdown กี่นาทีที่เหลือ + link ไป forgot password  
**ทำไม:** UX requirement — user ต้องรู้ว่าต้องรอเท่าไหร่

---

### Task 7.8 — UI: Hard lock screen (reset link เท่านั้น)
**ทำอะไร:** หน้า error บอกว่า locked ถาวร + link ไป forgot password  
**ทำไม:** hard lock ไม่มี timer — ต้อง reset password เท่านั้น

---

## LOG-08 — Forgot Password `5 SP`

> **เป้าหมาย:** self-service recovery — ออก temp password ใหม่ + clear lock ทั้งคู่ แบบ atomic
> **SP เหตุผล:** mostly reuse จาก stories อื่น แต่ Task 8.4 atomic lock clear ใน transaction + Task 8.2 rate limiting ใหม่ — เดิม 3 SP ต่ำเกินไปสำหรับ new endpoint + atomic DB

---

### Task 8.1 — POST `/auth/password/forgot` endpoint
**ทำอะไร:** รับ email → ไม่ว่า account จะมีหรือไม่ → return message เดิมเสมอ → ถ้ามี account valid → trigger temp password  
**ทำไม:** ไม่มีอยู่เลย — non-enumeration mandatory

---

### Task 8.2 — Rate limit 5 req/hr per IP + 10min cooldown per account
**ทำอะไร:** sliding window 5 requests/hr per IP → 429 + Retry-After; cooldown 10min per account (reuse `temporary_password_issued_at`)  
**ทำไม:** ป้องกัน abuse กดขอรหัสผ่านใหม่ต่อเนื่อง

---

### Task 8.3 — Reuse LOG-05 temp password mechanism
**ทำอะไร:** เรียก temp password generator เดิม → email → `must_change_password = true`  
**ทำไม:** ไม่ต้องสร้าง mechanism ใหม่ — reuse function จาก Task 5.3

---

### Task 8.4 — Atomic lock clear
**ทำอะไร:** ใน transaction เดียว: `soft_locked_until = null`, `hard_locked = false`, `failed_login_attempts = 0`  
**ทำไม:** ถ้าไม่ atomic อาจเกิด partial state — hard_locked clear แต่ counter ยังอยู่

---

### Task 8.5 — Session invalidation บน temp password issuance
**ทำอะไร:** หลังออก temp password → invalidate sessions ทุกอันของ user นั้น  
**ทำไม:** ถ้า session เดิมยังใช้ได้อยู่ แปลว่า attacker ที่ขอ reset password อาจ hijack session เดิมได้

---

## LOG-09 — Encrypt Sensitive Customer Data `13 SP`

> **เป้าหมาย:** AES-256-GCM field encryption บน sensitive fields ด้วย AWS KMS Envelope Encryption
> **SP เหตุผล:** KMS external dependency (infra ต้องพร้อมก่อน) + Task 9.5 envelope encryption pattern ซับซ้อน + Task 9.7 cross-cutting data layer hook + Task 9.10 migration script risk สูง (ต้องมี rollback plan)

---

### Task 9.1 — [Infra] AWS KMS CMK provisioning + IAM roles
**ทำอะไร:** สร้าง Customer Managed Key ใน AWS KMS + กำหนด IAM policy ว่า service ไหน Decrypt ได้  
**ทำไม:** Pre-implementation dependency — ต้องทำก่อนเขียนโค้ดทั้งหมดใน LOG-09

**ข้อสำคัญ:** CMK ต้องไม่อยู่ใน .env หรือ code เด็ดขาด — อยู่ใน KMS เท่านั้น

---

### Task 9.2 — กำหนด Sensitive Field Classification Matrix
**ทำอะไร:** list ว่า field ไหนบ้างต้อง encrypt — phone, email, name, address (ตรวจสอบกับ product/security team)  
**ทำไม:** ถ้าไม่มี matrix ก่อน implement จะเดาเอง → encrypt ผิด field หรือขาด field

---

### Task 9.3 — AES-256-GCM encrypt utility
**ทำอะไร:** pure function รับ plaintext + DEK → return `Base64(IV[12B] + AuthTag[16B] + Ciphertext)`  
**ทำไม:** building block ของทุก field encryption

```typescript
// IV: 12 bytes random per operation (ไม่ใช้ IV ซ้ำ)
encrypt(plaintext: string, dek: Buffer): string  // Base64 output
```

---

### Task 9.4 — AES-256-GCM decrypt utility + Auth Tag verification
**ทำอะไร:** parse Base64 → extract IV + AuthTag + Ciphertext → decrypt → verify Auth Tag  
**ทำไม:** ถ้า Auth Tag fail ต้อง throw error ทันที — ห้าม return plaintext บางส่วน

---

### Task 9.5 — Envelope Encryption: KMS GenerateDataKey → encrypt fields → store encrypted DEK
**ทำอะไร:** ขอ DEK จาก KMS → ใช้ DEK encrypt fields → zero DEK จาก memory → เก็บ encrypted DEK ใน DB  
**ทำไม:** CMK ต้องอยู่ใน KMS เท่านั้น — DEK plaintext ต้องไม่ persist

```typescript
// Pattern:
// 1. KMS.generateDataKey() → { plaintext_dek, encrypted_dek }
// 2. encrypt all fields with plaintext_dek
// 3. memzero(plaintext_dek)
// 4. store: encrypted_fields + encrypted_dek in DB
```

---

### Task 9.6 — DEK caching (in-memory, TTL) สำหรับ read-heavy path
**ทำอะไร:** cache DEK plaintext ใน memory พร้อม TTL — ไม่ต้อง call KMS Decrypt ทุก request  
**ทำไม:** list ลูกค้า 1,000 คน = 1,000 KMS calls → ช้ามาก + ค่า KMS แพง

**ข้อระวัง:** DEK ที่ cache ต้องอยู่แค่ใน server memory — ห้าม persist ลง Redis หรือ disk

---

### Task 9.7 — Data access layer: auto-encrypt on write, auto-decrypt on authorized read
**ทำอะไร:** เพิ่ม hook ใน repository/service layer ให้ encrypt ก่อน insert/update, decrypt หลัง fetch  
**ทำไม:** transparent to business logic — ไม่ต้องทุก service รู้เรื่อง encryption

---

### Task 9.8 — Searchable HMAC hash สำหรับ encrypted fields
**ทำอะไร:** เก็บ `HMAC(plaintext, search_key)` แยกต่างหาก สำหรับใช้ใน `WHERE phone_hash = HMAC(input)`  
**ทำไม:** `WHERE phone = '0812345678'` ไม่ได้ผล — DB เก็บ ciphertext, query ต้องใช้ hash แทน

---

### Task 9.9 — Audit log: sensitive field access
**ทำอะไร:** บันทึกเมื่อ sensitive field ถูก read — โดย service/user ใด, เมื่อไหร่  
**ทำไม:** compliance requirement — ต้องมี trail ว่าใครเข้าถึงข้อมูลลูกค้า

---

### Task 9.10 — Data migration: encrypt existing unencrypted records
**ทำอะไร:** script แบบ batched ที่อ่าน records เดิม → encrypt → update กลับ → verify  
**ทำไม:** records ที่มีอยู่แล้วยัง plaintext — ต้อง migrate ก่อน go-live

**ข้อระวัง:** ต้องทำ batched + verify แต่ละ batch ก่อน commit — ถ้า fail กลางทาง ต้องมี rollback plan

---

## Summary

| Story | Task ใหม่ | Task 🔧 | SP | เหตุผลที่ให้ SP เท่านี้ |
|-------|-----------|--------|----|------------------------|
| LOG-01 Invite Flow | 4 | 3 | **8** | cross 4 services (api-gateway + user-service + tenant-service + notification-service + frontend) + Task 1.2 แก้ status enum บน live invite system เสี่ยงสูง |
| LOG-02 MFA Enforce | 3 | 2 | **8** | Task 2.2 breaking change หลัก (login ไม่ออก JWT ทันทีอีกต่อไป) + Task 2.4 custom Redis sliding window ที่ต้องเขียนเอง (throttler เดิมใช้ไม่ได้) |
| LOG-03 OTP Generate | 5 | 0 | **5** | contained — DB table + generate + email + resend controls ทั้งหมดอยู่ใน scope เดียว ไม่ cross service ซับซ้อน |
| LOG-04 OTP Verify + Session | 9 | 1 | **13** | 10 tasks: idle TTL ต้อง hook ทุก request (DB write ทุก call), concurrent session eviction ต้อง atomic transaction, UI idle warning modal — underestimated ใน round แรก |
| LOG-05 Temp Password | 4 | 1 | **5** | foundation story ที่ LOG-01, LOG-06, LOG-08 depend — Task 5.3 temp password generator ต้องทำดี reusable + testable มาก เดิมให้ 3 SP ต่ำเกินไป |
| LOG-06 Force Change | 5 | 0 | **8** | Task 6.3 ต้อง enforce ทั้งสองชั้น (backend middleware + Next.js frontend route guard) + UI force change screen มี inline real-time requirements checklist |
| LOG-07 Soft/Hard Lock | 6 | 2 | **8** | Task 7.3 counter increment ต้องใช้ SELECT FOR UPDATE กัน race condition, 2 email templates + 2 UI screens (countdown timer) = งาน frontend เยอะกว่าที่เห็น |
| LOG-08 Forgot Password | 5 | 0 | **5** | mostly reuse จาก stories อื่น แต่ Task 8.4 atomic lock clear ใน transaction + Task 8.2 rate limiting ใหม่ — เดิม 3 SP ต่ำเกินไปสำหรับ new endpoint + atomic DB |
| LOG-09 Encryption | 10 | 0 | **13** | KMS external dependency + Task 9.5 envelope encryption ซับซ้อน + Task 9.7 cross-cutting data layer hook + Task 9.10 migration script risk สูง (ต้องมี rollback plan) |
| **รวม** | **51** | **6** | **73 SP** | เพิ่มจาก 55 → 73 เพราะ LOG-04 + LOG-06 + LOG-07 underestimated ใน round แรก |

---

## Dependency ระหว่าง Story

```
LOG-01 (Invite) ← ต้องมี LOG-05 ก่อน (Task 1.4 ออก temp password หลัง verify)

LOG-02 (MFA Enforce) ← ต้องมี LOG-03 + LOG-04 (สร้าง + verify challenge)
LOG-02 ← ต้องมี LOG-07 บางส่วน (pre-condition: check lock state ใน login)

LOG-03 (OTP Generate) ← ต้องมี Task 2.2 (login return MFA_REQUIRED)
LOG-04 (OTP Verify) ← ต้องมี LOG-03 (challenge table + OTP)

LOG-05 (Temp Password) — standalone, reused by LOG-01, LOG-08
LOG-06 (Force Change) ← ต้องมี LOG-05 (must_change_password flag)

LOG-07 (Lock) ← เขียนได้ parallel กับ LOG-02 บางส่วน (user fields)
LOG-08 (Forgot Password) ← ต้องมี LOG-05 + LOG-07 (reuse mechanism + clear lock)

LOG-09 (Encryption) — standalone (ไม่ขึ้นกับ story อื่น)
```

---

## ไฟล์หลักที่ต้องแก้ (จาก repo จริง)

| ไฟล์ | แก้เพราะ |
|------|----------|
| `apps/user-service/prisma/schema.prisma` | เพิ่ม fields: email_verified_at, must_change_password, password_last_changed_at, failed_login_attempts, soft_locked_until, hard_locked |
| `apps/api-gateway/src/auth/auth.service.ts` | แก้ login flow: MFA gate, pre-condition order, lock check, expiry check |
| `apps/api-gateway/src/auth/auth.controller.ts` | เพิ่ม endpoints: /auth/mfa/*, /auth/password/*, /auth/session/* |
| `apps/tenant-service/src/invitations/invitations.service.ts` | แก้ status logic ให้รองรับ Invited/Expired/Active |
| `apps/notification-service/src/email/email.service.ts` | เพิ่ม templates: MFA code, soft lock, hard lock, temp password |
| `apps/workspace-admin/src/server/auth.ts` | เพิ่ม idle warning, session extend, must_change_password gate |
