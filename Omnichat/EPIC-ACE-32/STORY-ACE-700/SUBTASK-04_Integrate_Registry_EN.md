# Subtask 4: Integrate Strategy into Registry

**Status**: TO DO

## Description
For the `InstagramStrategy` class to actively receive execution commands from the orchestrating webhook engine or outbound API layer, it requires manual registration inside the application's global strategy directory index.

## Verification Details
1. **Target Area**: `apps/omnichat-service/src/channel-accounts/strategies/strategy.registry.ts`
2. **Current State**: Facebook and Line share connections here, but Instagram is excluded.
3. **Action Required**: 
   - Inside the registry provider, inject the newly crafted `InstagramStrategy` class from Subtask 2.
   - Configure the internal map to reliably translate `ChannelType.INSTAGRAM` enum targets to immediately load this specific provider class. Ensure syntax aligns properly to resolve provider dependency injections cleanly upon NextJS/NestJS boots.
