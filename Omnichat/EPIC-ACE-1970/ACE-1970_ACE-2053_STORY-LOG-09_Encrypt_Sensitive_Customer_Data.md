# STORY-LOG-09: Encrypt Sensitive Customer Data

**Status:** Backlog | **ClickUp:** [ACE-2053](https://app.clickup.com/t/86d2wavct) | **Epic:** [ACE-1970](https://app.clickup.com/t/86d2u6vzv)

## User Story

As a System / Platform Engineer
I want all sensitive customer fields to be encrypted at rest with a properly managed key
so that customer data is protected against unauthorized access even if the database is compromised, and the application meets Lazada DataMoat Requirement No.13.

## Detail / Description

**Scope of this story:** Implement field-level encryption for sensitive customer data stored in PostgreSQL (AWS RDS) using AES-256-GCM. Encryption keys are managed via AWS KMS using the Envelope Encryption pattern. Secret keys must never be stored on the client side or in application code.

## Acceptance Criteria

### Sensitive fields must be encrypted before storage
**Given** the application writes a customer record containing sensitive fields (e.g., phone, email, name, address)  
**When** the record is persisted to the database  
**Then** each sensitive field must be encrypted using AES-256-GCM before insert/update  
**And** the plaintext value must never appear in the database, logs, or API responses (unless authorized)

### Encryption uses AES-256-GCM mode
**Given** the encryption algorithm is configured  
**When** a field is encrypted  
**Then** the algorithm used must be AES-256-GCM (key size: 256-bit, mode: GCM)  
**And** a unique random IV (96-bit / 12 bytes) must be generated for every encryption operation  
**And** the 128-bit Auth Tag must be stored alongside the ciphertext  
**And** the stored value must contain: `Base64(IV [12B] + AuthTag [16B] + Ciphertext)`

### Auth Tag must be verified on every decryption
**Given** encrypted data is retrieved from the database  
**When** the system decrypts the field  
**Then** the Auth Tag must be validated before returning the plaintext  
**And** if Auth Tag validation fails (tampered data), the system must throw an error and NOT return any plaintext

### Keys managed via AWS KMS (Envelope Encryption)
**Given** data needs to be encrypted  
**When** the system requests an encryption key  
**Then** a Data Encryption Key (DEK) is requested from AWS KMS via `GenerateDataKey (AES_256)`  
**And** the plaintext DEK is used only in memory for encryption, then immediately zeroed/discarded  
**And** only the KMS-encrypted DEK (CiphertextBlob) is stored in the database alongside the record  
**And** the Master Key (CMK) resides in AWS KMS only — never in application code, environment variables, or client storage

### Secret key must not be stored on client side
**Given** the application architecture is inspected  
**When** reviewing all key storage locations  
**Then** no encryption key, DEK, or CMK reference must exist in browser localStorage, sessionStorage, cookies, frontend JavaScript bundles, or any client-accessible storage  
**And** all key operations must be performed server-side only

### Access control on sensitive data
**Given** sensitive fields are stored encrypted  
**When** a request to read decrypted data is made  
**Then** the system must validate that the requesting service/user has the appropriate IAM role or permission to call AWS KMS Decrypt  
**And** unauthorized decryption attempts must be logged and rejected

### Data in transit encrypted via TLS
**Given** data flows between client and server, or between services  
**When** any sensitive data is transmitted  
**Then** the connection must use HTTPS/TLS 1.2 or higher at all times  
**And** unencrypted (HTTP) transport of sensitive data is strictly prohibited

### Key rotation support
**Given** AWS KMS CMK rotation is enabled  
**When** a key rotation event occurs  
**Then** existing data encrypted with the old DEK remains decryptable (KMS handles CMK rotation transparently)  
**And** new records use the latest DEK issued by the rotated CMK

## Technical Notes

**APIs:**
- ไม่มี public API ใหม่ — encryption/decryption handled internally within the data access layer
- AWS KMS APIs used: `GenerateDataKey`, `Decrypt` (via AWS SDK server-side only)

**Data:**
- Sensitive fields stored as: `Base64(IV [12B] + AuthTag [16B] + Ciphertext)`
- Encrypted DEK (CiphertextBlob) stored per record in the database
- Plaintext DEK: memory only, never persisted
- Sensitive field classification matrix must be defined before implementation (e.g., phone, email, name, address)

**Integrations:**
- AWS KMS: CMK (Customer Managed Key) must be provisioned with appropriate IAM policies
- AWS RDS PostgreSQL: storage-level encryption at rest must also be enabled (separate layer)

**Offer Logics:**
- Algorithm: AES-256-GCM. IV: 12 bytes random per operation. Auth Tag: 16 bytes (128-bit)
- Format: `Base64(IV + AuthTag + Ciphertext)`
- Envelope Encryption pattern: CMK in KMS → generates DEK → DEK encrypts data → only encrypted DEK stored in DB
- DEK caching strategy may be considered for read-heavy paths (with TTL and secure in-memory handling)

**Dependencies:**
- AWS KMS CMK provisioned and IAM roles configured before implementation
- Sensitive field classification matrix approved by product/security team
- Data migration plan for existing unencrypted records

**Special focus:**
- Security: Master Key never leaves KMS. No keys in code, .env, or client
- Security: Auth Tag must always be verified — failure to verify means decryption must be rejected
- Security: Plaintext DEK must be zeroed from memory immediately after use
- Compliance: Directly addresses Lazada DataMoat Requirement No.13 (AES ≥ 128-bit, GCM mode, Key Vault, no client-side keys)

**Additional Implementation Notes:**
- **Performance:** ถ้าต้อง decrypt ทีละหลาย records (list ลูกค้า 1,000 คน) จะช้ากว่า query ปกติ — ควร cache DEK ใน memory (พร้อม TTL) และ paginate ข้อมูลแทนการ load ทีเดียวหมด
- **Search/Filter:** ค้นหาด้วย encrypted field ตรงๆ ไม่ได้ (`WHERE phone = '0812345678'` ใช้ไม่ได้ เพราะ DB เก็บเป็น ciphertext) — ต้องทำ searchable hash แยก (เก็บ HMAC ของ plaintext ไว้ search) หรือ search ผ่าน field ที่ไม่ได้ encrypt แทน
- **Logging:** plaintext ห้ามหลุดไปใน application log — ห้าม log request/response body ที่มีข้อมูลลูกค้า

## UI/UX Notes

- ไม่มี UI changes สำหรับ end-users — encryption/decryption transparent ที่ service layer
- Admin portal ต้องไม่แสดง raw encrypted values — แสดง decrypted values เมื่อ authorized เท่านั้น
- Audit log ต้องบันทึกเมื่อ sensitive fields ถูก access (read) และโดย service/user ใด

## QA / Test Considerations

**Primary flows:**
- Write customer record → fields encrypted with AES-256-GCM → `IV+AuthTag+Ciphertext` stored in DB → encrypted DEK stored alongside
- Read customer record → fetch encrypted DEK → KMS Decrypt → plaintext DEK → AES-256-GCM decrypt → Auth Tag verified → plaintext returned to authorized caller

**Edge Cases:**
- Tamper with ciphertext in DB → Auth Tag validation fails → decryption rejected, error logged
- KMS unavailable → system must handle gracefully (fail-safe, no plaintext leak)
- Unauthorized role attempts KMS Decrypt → access denied, event logged

**Business-Critical Must Not Break:**
- Existing records must be migrated/re-encrypted during deployment (migration plan required)
- Decryption failure must never return partial plaintext
- Encryption must not degrade login or data read performance beyond acceptable thresholds
