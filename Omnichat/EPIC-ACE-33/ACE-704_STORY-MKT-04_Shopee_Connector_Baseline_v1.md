# ACE-704 STORY-MKT-04: Shopee Connector Baseline v1 Ingest Chat Order References Fetch History and Outbound Reply

> **Status:** `TO DO` &nbsp; | &nbsp; **Assignees:** `Unassigned`

## 📝 Description
- **Overview:** As a Connector Service, I want the Shopee baseline connector to ingest chat data and support outbound text replies for the R1 baseline.
- **Detail:** Similar to TikTok, this story covers end-to-end Shopee integration. It emphasizes error categorization and rate limit handling due to strict marketplace API requirements.
- **Scope:**
    - Shopee poller for chat, orders, and history.
    - Outbound text replies.
    - Basic Shopee-specific threading rules.
    - De-duplication by external message ID.
- **Acceptance Criteria:**
    1. Scheduled poll ingests data since last watermark.
    2. 7-day history backfill on connection.
    3. Order references linked as metadata.
    4. Outbound text reply success and persistence.
    5. Consistent threading based on Shopee conversation IDs.

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
