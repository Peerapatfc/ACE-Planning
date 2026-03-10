# ACE-40 (NDP-04): Attachment Storage v1 — API Table

## Context

Public API for attachment metadata and download (static URL from public S3 bucket), plus internal worker interface for async download/upload.

---

## Public API

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/attachments/:id` | Get attachment metadata |
| GET | `/api/v1/attachments/:id/download` | Get download URL (static public URL) |

---

### GET `/api/v1/attachments/:id`

**Response:**

```json
{
  "data": {
    "id": "uuid",
    "message_id": "uuid",
    "type": "image",
    "content_type": "image/jpeg",
    "size": 245678,
    "status": "uploaded",
    "failure_reason": null,
    "checksum": "sha256:abc123...",
    "metadata": { "original_filename": "photo.jpg" },
    "created_at": "2025-01-15T10:30:00Z"
  }
}
```

---

### GET `/api/v1/attachments/:id/download`

**Response (status = uploaded):**

```json
{
  "data": {
    "url": "https://{bucket}.s3.amazonaws.com/{tenant_id}/{attachment_id}/photo.jpg"
  }
}
```

> Static public URL — no expiry, no presigned URL needed. S3 bucket is public.

**Response (status = pending):**

```json
{
  "data": {
    "status": "pending",
    "message": "Attachment is still being processed"
  }
}
```

**Response (status = failed):**

```json
{
  "data": {
    "status": "failed",
    "failure_reason": "download_timeout_after_retries",
    "retryable": true
  }
}
```

---

## Internal Worker Interface

| Method | Interface | Description | Key Params |
|---|---|---|---|
| `downloadAndStore` | Queue Job | Async download from channel, upload to S3, update DB | `{ attachment_id, download_url, tenant_id, channel_type }` |
| `retryFailedAttachment` | Admin/Internal | Re-enqueue failed retryable attachment | `{ attachment_id }` |

---

## Security Headers

| Header | Description |
|---|---|
| `X-Tenant-Id` | Required — attachment access scoped to tenant |
| `Authorization` | Bearer token |
| `Cache-Control` | Standard caching — static URLs are permanent |
