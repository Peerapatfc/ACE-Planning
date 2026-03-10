# Subtask 3: Develop Multi-Shop Data Mapping

**Status**: TO DO

## Description
Establish a data mapping logic that associates a single workspace tenant with potentially multiple marketplace shops (1-to-many relationship) safely without overwriting previous connections.

## Implementation Details
1. **Target Files**: 
   - `apps/omnichat-service/src/channel-accounts/channel-accounts.service.ts`
   - `packages/shared/src/types/` (Updates to payload requirements)
2. **Current State**: The `channel_accounts` logic allows storing external accounts, but specific overrides and duplication prevention for multi-shop needs tightening.
3. **Action Required**: 
   - Implement logic to map a marketplace's `external_account_id` (shop_id or seller_id) to the internal `channel_account_id`.
   - Before inserting, explicitly check if the `external_account_id` belongs to a *different* tenant. Reject or flag the request to prevent account hijacking.
   - If the same tenant reconnects the same `external_account_id`, gracefully update the existing record (and Vault references) instead of creating duplicate rows.
