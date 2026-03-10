# ACE-706 STORY-MKT-06: Marketplace Threading Rules v1 and Conversation Key Strategy

> **Status:** `TO DO` &nbsp; | &nbsp; **Assignees:** `Unassigned`

## 📝 Description
- **Overview:** As a Platform Engineer, I want a consistent threading key strategy for marketplaces to map messages and replies to the correct conversations.
- **Detail:** Marketplace threading differs from social channels as thread IDs may be unclear or include multiple identifiers. This story defines a "v1 rule" for generating conversation keys (e.g., `tenant_id + channel_account_id + external_buyer_id`).
- **Scope:**
    - Define conversation_key generation service.
    - Support mapping for TikTok (platform ID), Shopee (buyer + order ID), and Lazada (buyer ID).
    - Unit tests for key consistency.
- **Acceptance Criteria:**
    1. Identical keys for the same TikTok conversation.
    2. Identical keys for Shopee buyers across sessions.
    3. Identical keys for Lazada buyers.
    4. Key strategy service reachable by all connectors.

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
