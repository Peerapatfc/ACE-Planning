# Subtask 2: Integrate Credential Vault

**Status**: TO DO

## Description
Ensure that the access and refresh tokens retrieved from the marketplace connection flows are securely encrypted and saved via the designated Credential Vault system (FND-02).

## Implementation Details
1. **Target Files**: 
   - `apps/omnichat-service/src/channel-accounts/services/marketplace-auth.service.ts` (New)
   - `apps/omnichat-service/src/vault/vault.service.ts` (Assuming FND-02 implementation)
2. **Current State**: Basic channel token storage exists, but must integrate fully with the highly secure FND-02 Credential Vault.
3. **Action Required**: 
   - After successfully exchanging tokens from Subtask 1, invoke the Vault Service to encrypt the credentials at rest.
   - Avoid storing raw access tokens in the main `channel_accounts` database table. Store a reference/ID to the Vault instead.
   - Ensure to mask or redact all token inputs/outputs from application observability logs to prevent credential leakage.
