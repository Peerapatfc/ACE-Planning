# ACE-701 — Commit Breakdown: Marketplace Channel Onboarding v1

**Story:** STORY-MKT-01: Connect Credentials and Account Mapping
**Epic:** EPIC-ACE-33
**Date:** 2026-03-11

---

## Commit Order

```
1 (schema) → 2 (vault integration) → 3 (tiktok auth) → 4 (shopee auth)
    → 5 (lazada auth) → 6 (channel service) → 7 (api endpoints)
    → 8 (tests)
```

> Commits 3–5 can be done in parallel (platform specific).
> Commit 6 depends on all of 2–5.

---

## Code Commits — 8 commits

### Commit 1
```text
chore(omnichat-service): add connection status and marketplace metadata to ChannelAccount schema
```
**Files:**
- `apps/omnichat-service/prisma/schema.prisma`
  - Update `channel_accounts` table: Add `connection_status` (`varchar` default `connected`), `last_error_message` (`varchar`), and `provider_metadata` (`jsonb` for `shop_id`, `seller_id`, `region`).
- `apps/omnichat-service/prisma/migrations/...`

---

### Commit 2
```text
feat(credentials): integrate FND-02 credential vault for marketplace tokens
```
**Files:**
- `libs/credentials/src/vault.service.ts` or `apps/omnichat-service/src/credentials/vault.service.ts`
**Methods:**
| Method | Description |
|--------|-------------|
| `storeOAuthTokens(tenantId, channelId, tokens)` | Encrypts and stores `access_token`, `refresh_token`, `expires_in` via FND-02 vault |
| `retrieveOAuthTokens(tenantId, channelId)` | Decrypts and fetches tokens |
| `revokeTokens(tenantId, channelId)` | Deletes credentials upon disconnect |

---

### Commit 3
```text
feat(marketplace-tiktok): implement TikTok OAuth connect and reconnect flow
```
**Files:**
- `apps/omnichat-service/src/marketplaces/tiktok/tiktok-auth.service.ts`
**Role:** Generates authorization URL, exchanges auth code for tokens, retrieves TikTok Shop ID and Seller ID.

---

### Commit 4
```text
feat(marketplace-shopee): implement Shopee Open Platform connect and reconnect flow
```
**Files:**
- `apps/omnichat-service/src/marketplaces/shopee/shopee-auth.service.ts`
**Role:** Generates Shopee partner signature, constructs auth URL, exchanges code for token, retrieves Shopee `shop_id`.

---

### Commit 5
```text
feat(marketplace-lazada): implement Lazada connect and reconnect flow
```
**Files:**
- `apps/omnichat-service/src/marketplaces/lazada/lazada-auth.service.ts`
**Role:** Handles Lazada OAuth flow, fetches tokens and seller account info (`seller_id`, region).

---

### Commit 6
```text
feat(omnichat-service): unify marketplace onboarding in ChannelAccountService
```
**Files:**
- `apps/omnichat-service/src/channels/channel-account.service.ts`
**Methods Added:**
- `connectMarketplace(tenantId, provider, code)`: Calls provider auth service, creates/updates `channel_accounts` record (multi-account per tenant allowed but exact `external_account_id` must be unique per provider), maps to Vault.
- `handleTokenRejection(tenantId, channelId)`: Sets `connection_status = 'error'`, flags for re-auth.

---

### Commit 7
```text
feat(omnichat-service): add API controllers for marketplace connecting
```
**Files:**
- `apps/omnichat-service/src/channels/controllers/marketplace-onboarding.controller.ts`
**Endpoints:**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/channels/marketplace/{provider}/auth-url` | GET | Returns the redirect URL for the frontend to open |
| `/api/v1/channels/marketplace/{provider}/callback` | GET/POST | Handles code exchange, saves account, returns success payload to UI |
| `/api/v1/channels/marketplace/{provider}/{id}/reconnect` | POST | Triggers the re-authentication sequence |

---

### Commit 8
```text
test(omnichat-service): add unit/integration tests for marketplace onboarding APIs
```
**Files:**
- `apps/omnichat-service/src/channels/marketplace-onboarding.spec.ts`
**Test cases to cover:**
- Vault encrypts standard payload successfully.
- Cross-tenant restriction: Cannot connect the same `shop_id` mapped to two different tenants without revoking the first one.
- Successful Shopee/TikTok/Lazada mocking sequence.
