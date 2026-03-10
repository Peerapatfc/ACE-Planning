# ACE-40 (NDP-04): Attachment Storage v1 — ER Diagram

## Context

Extends ACE-37 attachments table with fields for async download, retry logic, failure tracking, and validation. Size/type limits are managed via application config (env vars or config file).

---

## ER Diagram

```mermaid
erDiagram
    ATTACHMENTS {
        uuid id PK
        uuid tenant_id FK
        uuid message_id FK
        varchar type "image | video | audio | file | sticker"
        varchar content_type "MIME type, validated"
        bigint size "bytes, validated against max_size"
        varchar storage_key "S3 key: tenant_id/attachment_id/filename"
        varchar status "pending | uploading | uploaded | failed | rejected"
        varchar failure_reason "NEW: nullable, human-readable reason"
        boolean retryable "NEW: true if can be retried"
        integer retry_count "NEW: default 0, max 3"
        varchar checksum "SHA-256 of stored binary"
        varchar download_url "NEW: channel-specific content URL for async download"
        varchar file_url "NEW: public static URL after upload to S3"
        jsonb metadata "original_filename, channel-specific extras"
        timestamp created_at
        timestamp deleted_at "nullable, soft delete"
    }

    MESSAGES ||--o{ ATTACHMENTS : "has"
```

---

## New Fields on `attachments` (vs ACE-37)

| Field | Type | Purpose |
|---|---|---|
| `failure_reason` | varchar nullable | Why download/upload failed (e.g., `download_timeout`, `exceeds_size_limit`, `unsupported_content_type`) |
| `retryable` | boolean | Whether this failure can be retried |
| `retry_count` | integer | Current retry attempt count (max 3) |
| `download_url` | varchar nullable | Channel-specific URL to download binary (used by async worker) |
| `file_url` | varchar nullable | Public static URL after upload to S3 (e.g., `https://{bucket}.s3.amazonaws.com/{key}`) |

---

## Attachment Status Lifecycle

```
pending → uploading → uploaded     (happy path)
pending → uploading → failed       (download/upload error, retryable)
pending → rejected                 (validation: size/type exceeded)
failed  → uploading → uploaded     (manual retry success)
```

---

## Attachment Size/Type Validation (Application Config)

Size and type limits are managed via application config (not a DB table):

```yaml
# Example config
attachment_limits:
  image/*:  { max_size: 10485760, allowed: true }   # 10MB
  video/mp4: { max_size: 52428800, allowed: true }   # 50MB
  video/*:  { max_size: 52428800, allowed: true }    # 50MB
  audio/*:  { max_size: 26214400, allowed: true }    # 25MB
  application/pdf: { max_size: 10485760, allowed: true }
```

> Migrate to a DB table if runtime admin editing is needed in a future iteration.

---

## S3 Key Convention

```
Format:  {tenant_id}/{attachment_id}/{original_filename_or_hash}
Example: 550e8400-e29b/7c9e6679-f3b8/photo_2024.jpg
```
