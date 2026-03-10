# ACE-701 STORY-MKT-01: Marketplace Channel Onboarding v1 Connect Credentials and Account Mapping

> **Status:** `TO DO` &nbsp; | &nbsp; **Assignees:** `Unassigned`

## 📝 Description
- **Overview:** As a Tenant Admin, I want to connect TikTok, Shopee, and Lazada accounts into our system so that we can ingest messages, orders, references, and enable outbound replies for baseline pilot usage.
- **Detail:** This story focuses on onboarding for marketplaces (TikTok, Shopee, Lazada) enabling multi-account connections per tenant. Key elements include mapping between tenants and marketplace shops (shop_id, seller_id) and securely storing credentials via Vault with status tracking (connected/error).
- **Scope:** 
    - Connect flow spec and backend support for TikTok, Shopee, Lazada.
    - Secure credential storage via Credential Vault (from FND-02).
    - Mapping marketplace `external_account_id` to `channel_account_id` and `tenant_id`.
    - Visible connection status fields.
    - Support for reconnect and token rotation flow (minimal).
    - *Excluded:* Polling ingest logic (covered in MKT-02).
- **Acceptance Criteria:**
    1. Correct multi-tenant connect mapping.
    2. Secure credential storage (encrypted at rest, masked in logs).
    3. Support for multiple shops per tenant without overwriting.
    4. Visible connection status with initial validation.
    5. Reconnect flow for expired credentials.

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
