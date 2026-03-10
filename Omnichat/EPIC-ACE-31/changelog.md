# Changelog

All notable changes to the **Inbound Flow for EPIC-ACE-31** will be documented in this file.

## [Unreleased]

### Added (Planned / In Progress)
- **Normalizer Worker:** Channel Mappers using Strategy Pattern for mapping raw payloads to normalized events. *(Currently working on `feat/ACE-81-channel-mappers-strategy-pattern`)*
- **Normalizer Worker:** Worker orchestration for integrating raw event saving, normalization, and persistence workflows.
- **File Service:** Internal Upload API (`POST /files/upload`) for async attachment processing.
- **Omnichat Service:** Attachment tracking APIs for creating and updating attachment status.
- **Normalizer Worker:** Async downloader to process media attachments and forward to file service.
- **API Gateway:** Conversations List API (`GET /api/v1/conversations`) with cursor-based pagination.
- **API Gateway:** Message Timeline API (`GET /api/v1/conversations/:id/messages`) for fetching chat history.

---

## [Done]

### Added
- **Omnichat Service:** NDP Database schema for `Contacts`, `Conversations`, `Messages`, `Attachments`, and `RawEvents` tables.
- **Omnichat Service:** Raw Events API for persisting webhook payloads and updating normalization status.
- **Omnichat Service:** Inbound Persistence API (`POST /messages/inbound`) for idempotent message UPSERT/INSERT.
- **Omnichat Gateway:** Webhook Controller with HMAC-SHA256 signature validation and rate limiting.
- **Omnichat Gateway:** SQS Producer for publishing deduplicated webhook payloads to FIFO queues.
- **Normalizer Worker:** SQS Consumer setup with long-polling and initial PII redaction layer.
