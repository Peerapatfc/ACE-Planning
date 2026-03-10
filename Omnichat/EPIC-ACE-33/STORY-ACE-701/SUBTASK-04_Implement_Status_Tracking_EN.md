# Subtask 4: Implement Status Tracking & Reconnect Flow

**Status**: TO DO

## Description
Introduce connection state visibility. Store statuses such as Active, Expired, or Error, and supply a mechanism allowing users to refresh or re-authenticate their expired tokens gracefully.

## Implementation Details
1. **Target Files**: 
   - `apps/omnichat-service/src/channel-accounts/channel-accounts.service.ts`
2. **Current State**: A connection might fail silently without the platform updating its internal state visually for the tenant admins.
3. **Action Required**: 
   - Add status tracking fields to the DB entity if not fully utilized: `connection_status` (Enum: `ACTIVE`, `EXPIRED`, `ERROR`).
   - Create a background refresh checker if the marketplaces support long-lived token rotation via APIs.
   - Expose the status to the frontend. If a token goes `EXPIRED`, prompt the Frontend state to force a "Reconnect" via the OAuth flows established in Subtask 1, seamlessly updating the existing `channel_account_id`.
