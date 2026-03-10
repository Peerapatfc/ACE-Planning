# Subtask 1: Implement Marketplace Connect Flows

**Status**: TO DO

## Description
Create the connection and callback endpoints required to handle the OAuth and API Key authentication flows for TikTok, Shopee, and Lazada APIs.

## Implementation Details
1. **Target Files**: 
   - `apps/omnichat-service/src/channel-accounts/controllers/marketplace-auth.controller.ts` (New)
   - `apps/omnichat-service/src/channel-accounts/services/marketplace-auth.service.ts` (New)
2. **Current State**: The system handles basic LINE and Meta connections, but specific auth callback flows for the three marketplaces do not exist.
3. **Action Required**: 
   - Setup OAuth2.0 callbacks for TikTok and Shopee where users are redirected back to the system with an authorization code.
   - Setup the appropriate API Key handshakes for Lazada.
   - Exchange the authorization codes for access and refresh tokens.
   - Ensure the callback URL securely identifies the Tenant ID initiating the connection.
