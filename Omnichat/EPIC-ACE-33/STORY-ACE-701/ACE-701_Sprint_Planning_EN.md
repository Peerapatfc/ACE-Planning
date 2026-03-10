# Sprint Planning: ACE-701 - STORY-MKT-01: Marketplace Channel Onboarding v1

## 📋 Story Overview
**Goal:** Enable Tenant Admins to connect TikTok, Shopee, and Lazada accounts into the system for initial baseline usage (ingesting messages, orders, references, and outbound replies).
**Key Deliverables:** 
- Multi-account connection per tenant.
- Shop/Seller mapping (`external_account_id` -> `channel_account_id`).
- Secure credential storage (Vault).
- Connection status tracking and reconnect flow.

## 🛠️ Current Implementation Status
Based on the codebase analysis (`/Users/peerapatpongnipakorn/Work/AI-Knowledge/ace`):
- **Constants & Enums:** Basic `ChannelType` definitions for `tiktok`, `shopee`, and `lazada` are present in `packages/shared/src/constants/channel.constants.ts`.
- **Channel Accounts:** Models and controllers exist for `channel-accounts` (`apps/omnichat-service` and `apps/api-gateway`), allowing basic storage of account info.
- **Missing Pieces:**
  - Actual OAuth / API Key connection callback endpoints specifically handling TikTok, Shopee, and Lazada onboarding flows.
  - Integration with the designated Credential Vault (mentioned as FND-02) for securely storing marketplace access tokens.
  - Specific table structures or logic to map a tenant's multiple shops safely without overwriting.
  - Connection status handling (e.g., token expiration markers) and the corresponding UI fields.

## 📝 Subtask Breakdown
| ID | Subtask Name | Status | Description |
|---|---|---|---|
| MKT-01.1 | Implement Marketplace Connect Flows | TO DO | Create connect/callback endpoints handling auth flows for TikTok, Shopee, and Lazada APIs. |
| MKT-01.2 | Integrate Credential Vault | TO DO | Ensure access tokens are securely encrypted and saved via the Credential Vault system (FND-02). |
| MKT-01.3 | Develop Multi-Shop Data Mapping | TO DO | Map marketplace `external_account_id` (shop_id / seller_id) to `channel_account_id` ensuring a 1-to-many relationship under `tenant_id`. |
| MKT-01.4 | Implement Status Tracking & Reconnect | TO DO | Add `connection_status` field tracking (Active, Expired, Error) and logic to handle token rotation/re-authentication. |

## ⚠️ Recommendations & Edge Cases
1. **Token Refresh Lifecycles:** Understand the token expiration policies for TikTok, Shopee, and Lazada. Some require daily refreshes while others last longer. Implement proper background refresh jobs if supported, or clear status markers to force the user to reconnect.
2. **Shop Overrides:** Ensure the mapping logic explicitly checks if `external_account_id` already exists for *another* tenant to prevent hijacking, and handles re-connecting the *same* shop to the *same* tenant gracefully.
3. **Vault Security:** Mask credentials entirely in application logs during the onboarding handshake.
