# ACE-702 STORY-MKT-02: Scheduled Polling Framework v1 for Marketplace Ingest

> **Status:** `TO DO` &nbsp; | &nbsp; **Assignees:** `Unassigned`

## 📝 Description
- **Overview:** As a Platform Service, I want a scheduled polling framework for marketplace channels so that we can automatically fetch content without manual triggers in R1.
- **Detail:** Since webhooks may be limited or delayed, R1 will rely on a centralized polling engine. This engine runs per `channel_account`, sending raw events to the normalization pipeline (NDP-03). It must include rate limits, backoff retries, and watermarks to prevent data loss or duplicates.
- **Scope:**
    - Define polling schedules per channel/account.
    - Implement poll job runner with queue and concurrency controls.
    - Maintain watermark checkpoints per account/event type.
    - Publish raw events to the normalization pipeline.
    - Basic retry backoff and error categorization.
- **Acceptance Criteria:**
    1. Automated scheduled runs per account.
    2. Watermarked polling to prevent duplicates.
    3. Rate limits and concurrency controls to protect providers.
    4. Transient failure retries with backoff.
    5. Raw event emission with traceability (trace_id, tenant_id).

---

## 📋 Custom Fields
| Field | Value |
|---|---|
| Product | Omni |

## 🏗️ Subtasks
| Subtask | Status |
|---|---|
| ACE-708: task | TO DO |

## 🔧 Technical Requirements
| Requirement | Needed? |
|---|---|
| Sequence Diagram | ❌ |
| ER Diagram | ✅ |
| API Spec | ✅ |
