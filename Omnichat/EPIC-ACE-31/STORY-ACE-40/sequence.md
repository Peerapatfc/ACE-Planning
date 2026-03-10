# ACE-40 (NDP-04): Attachment Storage v1 — Sequence Diagram

## Context

Sequence diagrams for the attachment pipeline: async download from channel APIs, upload to S3 (public bucket), retry with backoff, and retrieval via static URLs. R1 must-have is LINE images end-to-end.

---

## 1. Async Attachment Download & Store (LINE Image)

```mermaid
sequenceDiagram
    participant Normalizer as Normalization Pipeline<br/>(NDP-03)
    participant Persist as Persistence Service<br/>(NDP-02)
    participant Queue as Job Queue
    participant Worker as Attachment Worker
    participant LINE as LINE Content API
    participant S3 as Object Storage (S3)
    participant DB as PostgreSQL

    Normalizer->>Persist: persistInboundMessage(normalizedEvent)
    Persist->>DB: INSERT messages (content_type='image', status='received')
    DB-->>Persist: message_id
    Persist->>DB: INSERT attachments (message_id, status='pending', type='image')
    DB-->>Persist: attachment_id
    Persist-->>Normalizer: { message_id, attachment_id }

    Note over Normalizer: Webhook returns 200 OK immediately<br/>Attachment download is async

    Persist->>Queue: enqueue(DownloadAttachment, { attachment_id, download_url, tenant_id })

    Queue->>Worker: dequeue job
    Worker->>LINE: GET content/{messageId} (with channel access token)

    alt Download Success
        LINE-->>Worker: binary data (image)
        Worker->>Worker: Validate size (<10MB) & content_type

        alt Validation OK
            Worker->>Worker: Calculate SHA-256 checksum
            Worker->>S3: PUT {tenant_id}/{attachment_id}/{filename} (public bucket)
            S3-->>Worker: storage_key, file_url
            Worker->>DB: UPDATE attachments SET<br/>storage_key=?, file_url=?, size=?, checksum=?,<br/>content_type=?, status='uploaded'
        else Validation Failed
            Worker->>DB: UPDATE attachments SET<br/>status='rejected', failure_reason='exceeds_size_limit'
        end

    else Download Failed (temporary)
        LINE-->>Worker: 500 / timeout
        Worker->>DB: UPDATE attachments SET retry_count+=1

        alt retry_count < max_retries (3)
            Worker->>Queue: re-enqueue with backoff<br/>(delay: 2^retry_count * 1000ms)
        else retry_count >= max_retries
            Worker->>DB: UPDATE attachments SET<br/>status='failed', failure_reason='download_timeout_after_retries'
        end
    end
```

---

## 2. Static URL Retrieval

```mermaid
sequenceDiagram
    participant Client as Inbox UI
    participant API as Omni API
    participant DB as PostgreSQL

    Client->>API: GET /api/v1/attachments/{id}/download
    API->>API: Extract tenant_id from auth context

    API->>DB: SELECT attachment WHERE id=? AND tenant_id=?
    DB-->>API: attachment record

    alt Attachment Not Found or Wrong Tenant
        API-->>Client: 404 Not Found
    else Status = 'pending'
        API-->>Client: 202 Accepted { status: 'pending', message: 'Processing' }
    else Status = 'failed'
        API-->>Client: 200 OK { status: 'failed', failure_reason }
    else Status = 'uploaded'
        API-->>Client: 200 OK { url: file_url }
        Note over Client: Static public URL from DB — no expiry,<br/>no S3 presigned URL needed
    end
```

> **Note:** S3 bucket is public. `file_url` is stored in DB at upload time. No presigned download URL generation needed.

---

## 3. Retry with Backoff

```mermaid
sequenceDiagram
    participant Queue as Job Queue
    participant Worker as Attachment Worker
    participant Source as Channel Content API
    participant DB as PostgreSQL

    Note over Worker: Retry policy: max 3 attempts<br/>Backoff: 1s, 2s, 4s (exponential)

    Queue->>Worker: Attempt 1
    Worker->>Source: Download binary
    Source-->>Worker: 500 Error
    Worker->>DB: UPDATE attachments SET retry_count=1
    Worker->>Queue: re-enqueue (delay: 1s)

    Queue->>Worker: Attempt 2 (after 1s)
    Worker->>Source: Download binary
    Source-->>Worker: Timeout
    Worker->>DB: UPDATE attachments SET retry_count=2
    Worker->>Queue: re-enqueue (delay: 2s)

    Queue->>Worker: Attempt 3 (after 2s)
    Worker->>Source: Download binary
    Source-->>Worker: 500 Error
    Worker->>DB: UPDATE attachments SET retry_count=3, status='failed',<br/>failure_reason='max_retries_exceeded'

    Note over Worker: Final state: failed<br/>Message still persisted,<br/>attachment shows error placeholder in UI
```
