# Plan: Commit 6 — Wire PollingModule and register ScheduleModule

## Context
Part of EPIC-ACE-33 ACE-702. This commit activates the polling framework by installing `@nestjs/schedule`, creating the `PollingModule` that wires all polling services, and registering it in `AppModule` alongside `ScheduleModule.forRoot()` which enables `@Cron` globally.

## Commit Message
`feat(omnichat-service): wire PollingModule and register ScheduleModule`

## Changes

### 1. Install package
```bash
pnpm add @nestjs/schedule --filter omnichat-service
```

### 2. Create `ace/apps/omnichat-service/src/polling/polling.module.ts`
```typescript
import { Module } from '@nestjs/common';
import { PrismaModule } from '../prisma/prisma.module';
import { BackoffService } from './backoff.service';
import { PollingOrchestratorService } from './polling-orchestrator.service';
import { PollingRegistry } from './polling.registry';
import { PollingStateService } from './polling-state.service';

@Module({
  imports: [PrismaModule],
  providers: [
    PollingOrchestratorService,
    PollingStateService,
    BackoffService,
    PollingRegistry,
  ],
})
export class PollingModule {}
```

### 3. Modify `ace/apps/omnichat-service/src/app.module.ts`
Add 2 import statements (lines 6-7 area):
```typescript
import { ScheduleModule } from '@nestjs/schedule';
import { PollingModule } from './polling/polling.module';
```
Add to imports array after `AppLoggerModule`:
```typescript
ScheduleModule.forRoot(),
```
And at end of imports array:
```typescript
PollingModule,
```

## Verification
* `pnpm --filter omnichat-service build` — TypeScript compiles without errors
* `pnpm --filter omnichat-service start:dev` — service starts, cron scheduler logs appear