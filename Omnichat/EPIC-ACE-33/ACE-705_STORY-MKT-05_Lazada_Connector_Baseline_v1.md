# ACE-705 STORY-MKT-05: Lazada Connector Baseline v1 Ingest Chat Order References Fetch History and Outbound Reply

> **Status:** `TO DO` &nbsp; | &nbsp; **Assignees:** `Unassigned`

## 📝 Description
- **Overview:** As a Connector Service, I want the Lazada baseline connector to ingest chat data and support outbound text replies for the R1 pilot.
- **Detail:** End-to-end Lazada baseline integration following the same pattern as TikTok and Shopee.
- **Scope:**
    - Lazada poller for chat, orders, and history.
    - Outbound text replies.
    - Basic Lazada threading rules and de-duplication.
- **Acceptance Criteria:**
    1. Scheduled poll ingests data since watermark.
    2. 7-day history backfill on connection.
    3. Order references linked as metadata.
    4. Outbound text reply success and persistence.
    5. Consistent threading based on Lazada conversation IDs.

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
