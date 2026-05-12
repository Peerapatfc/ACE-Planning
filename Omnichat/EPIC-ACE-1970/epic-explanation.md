# EPIC ACE-1970: Login Security Enhancements — คำอธิบายแบบเข้าใจง่าย

## สรุปภาพรวม

Epic นี้คือการยกระดับความปลอดภัยของระบบ Login ทั้งหมด ครอบคลุมตั้งแต่การเชิญ User เข้าระบบ, การบังคับใช้ MFA ทุกครั้งที่ login, การจัดการ Temporary Password, ระบบล็อค Account เมื่อพยายาม login ผิดซ้ำ, ไปจนถึงการเข้ารหัสข้อมูลลูกค้าที่ sensitive

**เปรียบเทียบง่าย ๆ:**
เหมือนการเปลี่ยนระบบรักษาความปลอดภัยของอาคาร จากแค่มีกุญแจ เป็นต้องแสดงบัตร + กด OTP + มีระบบล็อคประตูอัตโนมัติเมื่อมีคนพยายามเข้าผิดหลายครั้ง และข้อมูลทุกอย่างในอาคารถูกล็อคในตู้นิรภัย

---

## 1. แนวคิดหลัก (Core Concepts)

### 1.1 Login Flow ใหม่ทั้งหมด

```
Email + Password
      ↓
ตรวจสอบ pre-conditions:
  - Email verified?
  - Account locked?
  - Password expired?
      ↓
Password ถูกต้อง → MFA Required
      ↓
ส่ง 6-digit code ทาง Email
      ↓
User กรอก code → Verified
      ↓
Session สร้าง → เข้าระบบได้
```

### 1.2 สถานะของ User Account

| สถานะ | ความหมาย | Login ได้? |
|---|---|---|
| Invited | ได้รับ invite แต่ยังไม่ verify email | ❌ |
| Expired | Invite link หมดอายุ (7 วัน) | ❌ |
| Active | Email verified แล้ว | ✅ |
| Soft locked | ผิดรหัส 5 ครั้ง (ล็อค 15 นาที) | ❌ (ชั่วคราว) |
| Hard locked | ผิดรหัส 10 ครั้ง (ล็อคถาวร) | ❌ (ต้อง reset password) |

### 1.3 Counter ที่ต้องแยกออกจากกัน (สำคัญมาก!)

- **`failed_login_attempts`** — นับจาก password ผิด ใช้ trigger soft/hard lock
- **MFA attempt counter (per challenge)** — นับจาก OTP code ผิด ไม่เกี่ยวกับ lock

ทั้งสองตัวนี้ **ห้ามปนกัน** — กรอก OTP ผิด 5 ครั้งทำให้ MFA challenge blocked แต่ไม่นับรวมกับ password fail counter

---

## 2. สรุปรายละเอียด (Scope)

| หมวดหมู่ | รายละเอียด |
|---|---|
| Stories ใน Epic นี้ | 9 Stories (STORY-LOG-01 ถึง 09) |
| MFA | Email-based TOTP 6 หลัก, หมดอายุใน 5 นาที |
| Session | Absolute TTL 8 ชั่วโมง, Idle timeout 30 นาที, max 3 sessions |
| Soft lock | 5 password fails → ล็อค 15 นาที (auto-expire) |
| Hard lock | 10 password fails → ล็อคถาวร (ต้อง reset password) |
| Password expiry | 90 วัน, ไม่ให้ใช้ 5 รหัสล่าสุดซ้ำ |
| Data encryption | AES-256-GCM + AWS KMS Envelope Encryption |

---

## 3. คำอธิบายแต่ละ Story (Story Breakdown)

---

### STORY-LOG-01: Admin Invite Flow (ACE-2045)

**เป้าหมาย:** Admin เชิญ User เข้าระบบผ่านอีเมล User ต้อง verify email ก่อนจึงจะ login ได้

**Scope:** Admin สร้าง account → ระบบส่ง invite email (one-time link หมดอายุ 7 วัน) → User click link → verified → ได้รับ Temporary Password ทางอีเมล → บังคับเปลี่ยนรหัสก่อนเข้าใช้งาน

**Acceptance Criteria หลัก:**
- Admin สร้าง user → invite email ส่งอัตโนมัติ, status = "Invited"
- User click link ภายใน 7 วัน → status = "Active", ระบบส่ง Temporary Password ทันที
- User click link หลัง 7 วัน → ขึ้น error "This invite link has expired. Please contact your administrator.", status = "Expired"
- Login blocked หาก email ยังไม่ verified → ไม่ส่ง MFA code เด็ดขาด
- Admin resend invite ได้ (ทั้ง Invited และ Expired) → token เดิมถูก invalidate ทันที
- Invite token ต้องเป็น cryptographically random, hashed at rest, single-use เท่านั้น

**Technical Notes:**
- User fields เพิ่ม: `email_verified_at`, `invite_token_hash`, `invite_expires_at`, `status`
- Status transitions: Invited → Active, Invited → Expired, Expired → Invited (resend), Active → Invited (email change)
- Email: ใช้ template เดียวสำหรับทั้ง initial invite และ resend

**UI:**
- User Management table ต้องแสดง status column: Active / Invited / Expired / Soft locked / Hard locked

---

### STORY-LOG-02: Enforce MFA Step for All Logins (ACE-2046)

**เป้าหมาย:** บังคับให้ทุก login ต้องผ่าน MFA หลังจาก password validation ทุกครั้ง

**Scope:** ตรวจ pre-conditions ทั้งหมดก่อน trigger MFA, rate-limit API endpoint, บันทึก audit log ทุก login attempt

**Acceptance Criteria หลัก:**
- Password ถูก → ต้องไป MFA step เสมอ ห้ามสร้าง session ก่อน
- Password ผิด → generic error, ไม่ส่ง MFA code
- ผ่าน password แต่ยังไม่ผ่าน MFA → ทุก API ต้องคืน 401/403
- Rate limit: 20 req/min per IP, 10 req/min per account → HTTP 429 + Retry-After header
- ทุก login attempt บันทึก audit log: timestamp, event_type, user_id, ip_address, user_agent, outcome

**Technical Notes:**
- `POST /auth/login` → คืน `MFA_REQUIRED + mfa_challenge_id` (ยังไม่มี full session)
- Rate limit counter เก็บใน Redis (sliding window TTL)
- `audit_logs` table: INSERT-only (ห้าม UPDATE หรือ DELETE ที่ application DB level)

**UI:**
- หลัง password success → แสดงหน้า "Verify your sign-in" พร้อม 6-digit code input

---

### STORY-LOG-03: Generate & Email 6-digit TOTP Code with Resend Controls (ACE-2047)

**เป้าหมาย:** สร้าง OTP 6 หลัก ส่งทางอีเมล พร้อม resend control และ anti-spam

**Scope:** Generate 6-digit code (time-limited 5 นาที), deliver ทาง email, รองรับ resend พร้อม cooldown

**Acceptance Criteria หลัก:**
- MFA challenge สร้าง → 6-digit code, expires_at = now() + 5 นาที, ส่งทาง email
- Resend: new code (ล้าง code เดิม) + cooldown 30 วินาที, max 5 resend ต่อ 1 ชั่วโมง
- Email provider fail → แสดง generic error พร้อม retry option, log incident
- เก็บเฉพาะ hash ของ code เท่านั้น (ห้ามเก็บ plaintext)

**Technical Notes:**
- `POST /auth/mfa/resend` → invalidate old code, issue new
- `mfa_challenges` table: `id, user_id, code_hash, expires_at, status (PENDING/VERIFIED/EXPIRED), resend_count, last_sent_at`

**UI:**
- แสดง email แบบ masked (e.g., t***@domain.com)
- ปุ่ม "Resend code" พร้อม countdown timer
- แสดง "Code expires in X minutes."

---

### STORY-LOG-04: Verify MFA Code (ACE-2048)

**เป้าหมาย:** Validate OTP code, สร้าง session หลัง verify สำเร็จ, บังคับ session management rules ทั้งหมด

**Scope:** Validate code, สร้าง session, idle timeout 30 นาที, absolute TTL 8 ชั่วโมง, max 3 concurrent sessions, explicit logout

**Acceptance Criteria หลัก:**
- Code ถูก + ไม่หมดอายุ → สร้าง full authenticated session
- Code ผิด (1-4 ครั้ง) → ขึ้น "The code is incorrect. X attempts remaining." (X = 5 - attempt count)
- Code ผิด 5 ครั้ง → challenge BLOCKED → "Too many attempts. Please re-enter email and password." → ต้อง re-login ใหม่ทั้งหมด
- Code หมดอายุ → ขึ้น "This code has expired. Please request a new code." → Resend ได้ (preserve password-verified state)
- Session absolute TTL: 8 ชั่วโมง
- Session idle timeout: 30 นาที (warning 5 นาทีก่อน expire)
- Max concurrent sessions: 3 per user (session เก่าสุดถูก evict อัตโนมัติ)
- Logout → session invalid ทันที ใช้ token ซ้ำไม่ได้
- Session events บันทึก audit log ทั้งหมด

**Technical Notes:**
- `POST /auth/mfa/verify` → success: JWT; failure: increment attempt count
- `sessions` table: `session_id, user_id, created_at, last_active_at, invalidated_at`
- Concurrent session eviction ต้องเป็น atomic transaction
- MFA failure counter ≠ `failed_login_attempts` (สองตัวแยกกันอย่างเด็ดขาด)

**UI:**
- Input auto-advance, รองรับ paste 6 ตัว
- ปุ่ม "Back to login" รีสตาร์ท flow ได้อย่างปลอดภัย
- Idle warning modal ที่ 25 นาที: "Your session will expire in 5 minutes. Stay logged in?"

---

### STORY-LOG-05: Auto-generate a New Temporary Password and Email It (ACE-2049)

**เป้าหมาย:** เมื่อรหัสผ่านหมดอายุ (90 วัน) ระบบออก Temporary Password ใหม่ทาง email อัตโนมัติ

**Scope:** ตรวจ password expiry ตอน login → generate temp password → invalidate รหัสเดิม → email ส่ง → `must_change_password = true`

**Acceptance Criteria หลัก:**
- Password expired → generate temp password ใหม่, invalidate รหัสเดิม, email ส่ง, แสดง "Your password has expired. We've emailed you a new temporary password."
- รหัสเดิม login ไม่ได้อีกหลังจาก temp password ออก
- Temp password → login ปกติ (MFA required) → บังคับเปลี่ยน password (STORY-LOG-06)
- Cooldown: ออก temp password ได้ครั้งเดียวต่อ 10 นาที (กัน spam)

**Technical Notes:**
- User fields: `must_change_password = true`, `password_last_changed_at = now()`, `temporary_password_issued_at`
- Temp password: strong random 12-16 chars, ตรวจไม่ให้ซ้ำกับ 5 รหัสล่าสุด
- ห้าม log plaintext temp password เด็ดขาด

---

### STORY-LOG-06: Force User to Change Password After Temporary Password Login (ACE-2050)

**เป้าหมาย:** บังคับให้ User เปลี่ยนรหัสใหม่หลัง login ด้วย Temporary Password ก่อนเข้าใช้ portal

**Scope:** `must_change_password = true` → redirect ทุก route ไปหน้า Change Password → validate complexity + history ก่อน commit

**Acceptance Criteria หลัก:**
- `must_change_password = true` → redirect ทุก portal page ไปหน้าเปลี่ยนรหัส, block ทุก protected API
- รหัสใหม่ต้องผ่าน: min 8 chars, uppercase, number, special char
- รหัสใหม่ห้ามซ้ำกับ 5 รหัสล่าสุด → ขึ้น "You can't reuse any of your last 5 passwords."
- เปลี่ยนสำเร็จ → อัปเดต hash, เก็บ history, clear `must_change_password`, grant full access
- หลัง password change → invalidate session อื่นทั้งหมดทันที

**Technical Notes:**
- `POST /auth/password/change { current_password, new_password }`
- `user_password_history` table: เก็บ 5 รหัสล่าสุด
- History check ใช้ `bcrypt.verify()` ห้าม compare hash string ตรงๆ
- Password expiry: 90 วัน (backend config, ไม่มี UI ให้แก้)

**UI:**
- หน้าเปลี่ยนรหัส: Temporary password + New password + Confirm
- Inline checklist requirement แบบ real-time ขณะพิมพ์
- Success toast: "Password updated successfully."

---

### STORY-LOG-07: Soft Lock (5 fails, 15 min auto-expire) + Hard Lock (10 fails, requires password reset) (ACE-2051)

**เป้าหมาย:** ป้องกัน brute-force ด้วยระบบล็อค 2 ระดับ

**Scope:** Tier 1 (Soft Lock) 5 fails → ล็อค 15 นาที auto-expire; Tier 2 (Hard Lock) 10 fails → ล็อคถาวรจนกว่าจะ reset password

**Acceptance Criteria หลัก:**

**Soft Lock:**
- Password ผิด 5 ครั้ง → `soft_locked_until = now() + 15 min`, ส่งอีเมลแจ้ง, ห้าม MFA
- ขณะ soft locked → "Account temporarily locked. Try again in X minutes, or reset your password to unlock immediately."
- ครบ 15 นาที → login ได้ปกติ (แต่ `failed_login_attempts` ไม่ reset)

**Hard Lock:**
- Password ผิดรวม 10 ครั้ง → `hard_locked = true`, ส่งอีเมลแจ้ง, ล็อคถาวร
- "Account locked. Please reset your password to regain access."

**Reset:**
- Login สำเร็จ (ก่อนครบ 5) → `failed_login_attempts = 0`
- Reset password (STORY-LOG-08) → clear `soft_locked_until`, `hard_locked`, `failed_login_attempts` ทั้งหมด

**Technical Notes:**
- User fields: `failed_login_attempts (int)`, `soft_locked_until (nullable timestamp)`, `hard_locked (boolean)`
- นับเฉพาะ password fails เท่านั้น (MFA fails ไม่นับ)
- `failed_login_attempts` สะสมต่อเนื่องข้าม soft lock cycles (ไม่ reset ตอน soft lock expire)
- Counter update ต้องใช้ transactional locking (กัน race condition distributed)
- Error messages ห้ามเปิดเผยว่า account exist หรือไม่

**UI:**
- Soft lock: ขึ้น countdown timer, แสดง "Reset password" link
- Hard lock: แสดง "Reset password" link เสมอ

---

### STORY-LOG-08: Forgot Password (ACE-2052)

**เป้าหมาย:** User reset รหัสได้เอง ผ่านอีเมล ไม่ต้องติดต่อ support — flow เดียวกับ STORY-LOG-05

**Scope:** Forgot Password ออก Temporary Password ผ่าน mechanism เดียวกับ STORY-LOG-05, clear lock state ทั้งหมดใน transaction เดียว

**Acceptance Criteria หลัก:**
- Submit email → response เดิมเสมอ ไม่ว่า account จะ exist หรือไม่ (non-enumerating)
- ถ้า account exist → generate temp password, invalidate รหัสเดิม, `must_change_password = true`, email ส่ง
- ล้าง lock state ใน transaction เดียว: `soft_locked_until = null`, `hard_locked = false`, `failed_login_attempts = 0`
- Rate limit: 5 requests/hr per IP → HTTP 429 + Retry-After
- Cooldown per account: 1 temp password per 10 นาที
- Temp password ออก → invalidate ทุก active session ทันที
- Login ด้วย temp password → MFA required → force change (STORY-LOG-06)

**Technical Notes:**
- `POST /auth/password/forgot { email }` — rate-limited, non-enumerating
- ไม่ต้องมี `password_reset_tokens` table แยก (ใช้ temp password mechanism แทน)
- Atomic lock clearing ต้องอยู่ใน DB transaction เดียวกัน

**UI:**
- "Forgot password?" link ต้องแสดงตลอดเวลา รวมถึงตอน locked
- Hard lock screen ต้องแสดง link นี้ชัดเจน

---

### STORY-LOG-09: Encrypt Sensitive Customer Data (ACE-2053)

**เป้าหมาย:** เข้ารหัสข้อมูล sensitive ของลูกค้าใน DB ด้วย AES-256-GCM + AWS KMS รองรับ Lazada DataMoat Requirement No.13

**Scope:** Field-level encryption บน PostgreSQL (AWS RDS) ใช้ Envelope Encryption Pattern ผ่าน AWS KMS

**Acceptance Criteria หลัก:**
- Sensitive fields (phone, email, name, address) ต้องถูก encrypt ก่อน persist
- Algorithm: AES-256-GCM, IV: 96-bit random per operation, Auth Tag: 128-bit
- Format stored: `Base64(IV [12B] + AuthTag [16B] + Ciphertext)`
- Auth Tag ต้อง verify ทุกครั้งที่ decrypt — ถ้า fail ห้าม return plaintext
- Envelope Encryption: CMK ใน AWS KMS → generate DEK → DEK เข้ารหัส data → เก็บ encrypted DEK ใน DB
- Plaintext DEK: memory only, zero out ทันทีหลังใช้
- ห้าม store key ใดๆ บน client (localStorage, sessionStorage, cookies, JS bundle)
- ทุก request decrypt ต้อง validate IAM role ก่อน — unauthorized → log + reject
- Data in transit ต้อง HTTPS/TLS 1.2+

**Technical Notes:**
- ไม่มี public API ใหม่ — encryption/decryption อยู่ใน data access layer
- DEK caching ใน memory แบบมี TTL ทำได้ (สำหรับ read-heavy paths)
- Search บน encrypted field ไม่ได้ตรง → ต้องใช้ HMAC searchable hash แยก หรือ search ผ่าน field ที่ไม่ encrypt
- ต้องทำ data migration plan สำหรับ existing records
- ไม่ log request/response body ที่มีข้อมูลลูกค้า

**Dependencies:**
- AWS KMS CMK provisioned + IAM roles configured ก่อน implement
- Sensitive field classification matrix อนุมัติจาก product/security team ก่อน
- Data migration plan สำหรับ existing unencrypted records

---

## 4. Dependency Map ระหว่าง Stories

```
STORY-LOG-01 (Invite)
    └─→ ออก Temp Password ผ่าน mechanism ของ STORY-LOG-05

STORY-LOG-02 (MFA Enforcement)
    └─→ เรียกใช้ challenge จาก STORY-LOG-03
    └─→ ตรวจ lock state จาก STORY-LOG-07

STORY-LOG-03 (Generate OTP)
    └─→ ถูก verify โดย STORY-LOG-04

STORY-LOG-04 (Verify MFA)
    └─→ สร้าง session หลัง verify

STORY-LOG-05 (Temp Password Issuance)
    └─→ set must_change_password → trigger STORY-LOG-06

STORY-LOG-06 (Force Change)
    └─→ เช็ค password history (last 5)
    └─→ ถูก trigger โดย STORY-LOG-05 และ STORY-LOG-08

STORY-LOG-07 (Soft/Hard Lock)
    └─→ clear lock โดย STORY-LOG-08

STORY-LOG-08 (Forgot Password)
    └─→ reuse mechanism ของ STORY-LOG-05
    └─→ trigger STORY-LOG-06

STORY-LOG-09 (Encryption)
    └─→ standalone, ไม่ depend กับ story อื่น
```

---

## 5. Email Templates ที่ต้องมี

| Template | ใช้เมื่อ | Story |
|---|---|---|
| Invitation email | Admin invite user ใหม่ | LOG-01 |
| Temporary password email | Password expired หรือ Forgot password | LOG-05, LOG-08 |
| MFA code email | ทุก login ที่ผ่าน password | LOG-03 |
| Soft lock notification | ผิดรหัส 5 ครั้ง | LOG-07 |
| Hard lock notification | ผิดรหัส 10 ครั้ง | LOG-07 |
