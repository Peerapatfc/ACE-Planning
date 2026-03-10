# ACE-703 STORY-MKT-03: TikTok Connector Baseline v1 Ingest Chat Order References Fetch History and Outbound Reply

> **Status:** `TO DO` &nbsp; | &nbsp; **Assignees:** `Unassigned`

## 📝 Description
- **Overview:** As a Connector Service, I want the TikTok baseline connector to ingest chat data and support outbound text replies for the R1 pilot.
- **Detail:** End-to-end TikTok integration including message/order reference ingestion, history backfill, and outbound text replies using TikTok messaging capabilities. Mapping must fit schema v1 via the normalization pipeline.
- **Scope:**
    - Implement TikTok poller for messages, order references, and history.
    - TikTok outbound text reply and persistence.
    - Basic threading key strategy for TikTok.
    - Clear auth/permission error handling.
- **Acceptance Criteria:**
    1. Poller fetches new messages and emits to normalization.
    2. 7-day history backfill on first connection.
    3. Order references fetched and linked as metadata.
    4. Successful outbound text replies and persistence.
    5. Consistent threading based on TikTok conversation IDs.

---

## 📋 Custom Fields
| Field | Value |
|---|---|
| Product | Omni |

## 🏗️ Subtasks
| Subtask | Status |
|---|---|
| None | N/A |

## 🔧 Technical Requirements
| Requirement | Needed? |
|---|---|
| Sequence Diagram | ❌ |
| ER Diagram | ✅ |
| API Spec | ✅ |
