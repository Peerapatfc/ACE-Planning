# SEC-05 · Implementation Plan: Login — Expired Password Flow

**Scope:** Login flow only — POST `/auth/login` → expired password detection → token issuance → email notification.
**Skipped:** register, logout, refresh, invite, BlocklistService, JwtStrategy.

---

## Architecture

```
User → [api-gateway :3000] ──TCP──▶ [auth-orchestrator :4011] ──TCP──▶ [user-service :4005]
                                              │                  ──TCP──▶ [notification-service :4010]
                                              └──────────────────Redis──▶ [Redis]
```

**api-gateway** — HTTP layer only. `login()` becomes a thin TCP proxy.
**auth-orchestrator** — new NestJS hybrid service. Owns all login logic: credential validation, expiry check, JWT issuance, Redis token, email emit.

Port assignment: **HTTP 3011 / TCP 4011** (no conflict with existing services).

---

## Existing Code Reference

| What | Where |
|------|-------|
| Current `login()` to replace | `apps/api-gateway/src/auth/auth.service.ts:62–75` |
| `resolveTenantId()` to move | `apps/api-gateway/src/auth/auth.service.ts:196–204` |
| `issueTokens()` to move | `apps/api-gateway/src/auth/auth.service.ts:215–264` |
| Redis pattern reference | `apps/api-gateway/src/blocklist/blocklist.module.ts` |
| Notification emit pattern | `apps/user-service/src/users/users.service.ts:374–390` |
| TCP client registration pattern | `apps/api-gateway/src/auth/auth.module.ts:31–44` |
| Microservice main.ts pattern | `apps/user-service/src/main.ts` |

---

## Task Breakdown

### T1 — Register Config Keys

**File:** `packages/config/src/configuration.ts`

Add inside the exported object:

```typescript
authOrchestratorService: {
  http: {
    host: process.env.AUTH_ORCHESTRATOR_HTTP_HOST ?? '0.0.0.0',
    port: parseInt(process.env.AUTH_ORCHESTRATOR_HTTP_PORT ?? '3011'),
  },
  tcp: {
    host: process.env.AUTH_ORCHESTRATOR_TCP_HOST ?? '0.0.0.0',
    port: parseInt(process.env.AUTH_ORCHESTRATOR_TCP_PORT ?? '4011'),
  },
},
```

**Files:** `.env` + `.env.example` — add:

```env
AUTH_ORCHESTRATOR_HTTP_HOST=0.0.0.0
AUTH_ORCHESTRATOR_HTTP_PORT=3011
AUTH_ORCHESTRATOR_TCP_HOST=0.0.0.0
AUTH_ORCHESTRATOR_TCP_PORT=4011
```

> JWT secrets reuse existing keys (`shared.apiGateway.auth.jwt.*`) — no new env vars needed.
> Redis config key — verify against `blocklist.module.ts` before hardcoding (`apiGateway.redis.*`).

---

### T2 — Create `apps/auth-orchestrator/`

**Files to create:**

```
apps/auth-orchestrator/
  package.json
  tsconfig.json
  tsconfig.app.json
  src/
    main.ts
    app.module.ts
    auth/
      auth.module.ts
      auth.controller.ts
      auth.service.ts
      dto/
        login.dto.ts
```

#### `package.json`
Mirror `apps/user-service/package.json`. Change only `"name": "auth-orchestrator"`.

#### `src/main.ts`
```typescript
import { NestFactory } from '@nestjs/core';
import { ConfigService } from '@nestjs/config';
import { MicroserviceOptions, Transport } from '@nestjs/microservices';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  const config = app.get(ConfigService);

  const TCP_HOST = config.get<string>('shared.authOrchestratorService.tcp.host')!;
  const TCP_PORT = config.get<number>('shared.authOrchestratorService.tcp.port')!;
  const HTTP_HOST = config.get<string>('shared.authOrchestratorService.http.host')!;
  const HTTP_PORT = config.get<number>('shared.authOrchestratorService.http.port')!;

  app.connectMicroservice<MicroserviceOptions>({
    transport: Transport.TCP,
    options: { host: TCP_HOST, port: TCP_PORT },
  });

  await app.startAllMicroservices();
  await app.listen(HTTP_PORT, HTTP_HOST);
}
bootstrap();
```

#### `src/app.module.ts`
```typescript
import { configuration } from '@monorepo/config';
import { AppLoggerModule } from '@monorepo/logger';
import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { AuthModule } from './auth/auth.module';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      load: [configuration],
      envFilePath: ['.env', '../../.env'],
    }),
    AppLoggerModule,
    AuthModule,
  ],
})
export class AppModule {}
```

#### `src/auth/auth.module.ts`
```typescript
import { Module } from '@nestjs/common';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { JwtModule } from '@nestjs/jwt';
import { ClientsModule, Transport } from '@nestjs/microservices';
import Redis from 'ioredis';
import { AuthController } from './auth.controller';
import { AuthService } from './auth.service';

@Module({
  imports: [
    JwtModule.registerAsync({
      imports: [ConfigModule],
      useFactory: (config: ConfigService) => ({
        secret: config.get('shared.apiGateway.auth.jwt.accessSecret'),
      }),
      inject: [ConfigService],
    }),
    ClientsModule.registerAsync([
      {
        name: 'USER_SERVICE',
        imports: [ConfigModule],
        useFactory: (config: ConfigService) => ({
          transport: Transport.TCP,
          options: {
            host: config.get('shared.userService.tcp.host'),
            port: config.get('shared.userService.tcp.port'),
          },
        }),
        inject: [ConfigService],
      },
      {
        name: 'NOTIFICATION_SERVICE',
        imports: [ConfigModule],
        useFactory: (config: ConfigService) => ({
          transport: Transport.TCP,
          options: {
            host: config.get('shared.notificationService.tcp.host'),
            port: config.get('shared.notificationService.tcp.port'),
          },
        }),
        inject: [ConfigService],
      },
    ]),
  ],
  controllers: [AuthController],
  providers: [
    AuthService,
    {
      provide: 'REDIS_CLIENT',
      useFactory: (config: ConfigService) =>
        new Redis({
          host: config.get('shared.apiGateway.redis.host'),  // ← verify key
          port: config.get('shared.apiGateway.redis.port'),
          lazyConnect: true,
        }),
      inject: [ConfigService],
    },
  ],
})
export class AuthModule {}
```

#### `src/auth/auth.controller.ts`
```typescript
import { Controller } from '@nestjs/common';
import { MessagePattern, Payload } from '@nestjs/microservices';
import { LoginDto } from './dto/login.dto';
import { AuthService } from './auth.service';

@Controller()
export class AuthController {
  constructor(private readonly authService: AuthService) {}

  @MessagePattern({ cmd: 'auth_login' })
  async login(@Payload() dto: LoginDto) {
    return this.authService.login(dto);
  }
}
```

#### `src/auth/auth.service.ts`
```typescript
import { Inject, Injectable, UnauthorizedException } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { JwtService } from '@nestjs/jwt';
import { ClientProxy } from '@nestjs/microservices';
import * as crypto from 'crypto';
import { differenceInDays } from 'date-fns';
import Redis from 'ioredis';
import { firstValueFrom } from 'rxjs';
import { LoginDto } from './dto/login.dto';

@Injectable()
export class AuthService {
  constructor(
    @Inject('USER_SERVICE') private readonly userClient: ClientProxy,
    @Inject('NOTIFICATION_SERVICE') private readonly notifClient: ClientProxy,
    @Inject('REDIS_CLIENT') private readonly redis: Redis,
    private readonly jwtService: JwtService,
    private readonly config: ConfigService,
  ) {}

  async login(dto: LoginDto) {
    // validate_credentials throws RpcException on: not found | not verified | voided | wrong password
    const user = await firstValueFrom(
      this.userClient.send({ cmd: 'validate_credentials' }, dto),
    );

    if (user.password_changed_at) {
      const days = differenceInDays(new Date(), new Date(user.password_changed_at));
      if (days > 90) {
        return this.handleExpiredPassword(user);
      }
    }

    const tenantId = await this.resolveTenantId(user.id);
    return this.issueTokens(user.id, tenantId, user.email, user.first_name, user.last_name);
  }

  private async handleExpiredPassword(user: { id: string; email: string }) {
    const rawToken = crypto.randomBytes(32).toString('hex');
    const tokenHash = crypto.createHash('sha256').update(rawToken).digest('hex');

    await this.redis.set(`expired_reset:${tokenHash}`, user.id, 'EX', 900);

    await firstValueFrom(
      this.userClient.send({ cmd: 'void_password' }, { userId: user.id }),
    );

    const frontendUrl = this.config.get<string>('shared.frontendUrl');
    this.notifClient.emit(
      { cmd: 'send_password_expiry_email' },
      { to: user.email, reset_url: `${frontendUrl}/auth/expired-reset?token=${rawToken}` },
    );

    return {
      expired: true,
      message: "Your password has expired. We've sent a login link to your email.",
    };
  }

  private async resolveTenantId(userId: string): Promise<string> {
    const members = await firstValueFrom<{ tenant_id: string }[]>(
      this.userClient.send({ cmd: 'get_user_workspace_members' }, { user_id: userId }),
    );
    if (!members.length) throw new UnauthorizedException('User has no active workspace');
    return members[0].tenant_id;
  }

  private async issueTokens(
    userId: string,
    tenantId: string,
    email: string,
    firstName?: string,
    lastName?: string,
  ) {
    // Move from api-gateway/src/auth/auth.service.ts:215–264 verbatim
    // (JwtService.sign, crypto.randomBytes refresh token, store_refresh_token RPC)
  }

  private hashToken(token: string): string {
    return crypto.createHash('sha256').update(token).digest('hex');
  }
}
```

#### `src/auth/dto/login.dto.ts`
```typescript
export class LoginDto {
  email: string;
  password: string;
}
```

---

### T3 — api-gateway: Proxy Login to Orchestrator

**File:** `apps/api-gateway/src/auth/auth.module.ts`

Add `AUTH_ORCHESTRATOR` client alongside existing `USER_SERVICE`:

```typescript
{
  name: 'AUTH_ORCHESTRATOR',
  imports: [ConfigModule],
  useFactory: (config: ConfigService) => ({
    transport: Transport.TCP,
    options: {
      host: config.get('shared.authOrchestratorService.tcp.host'),
      port: config.get('shared.authOrchestratorService.tcp.port'),
    },
  }),
  inject: [ConfigService],
},
```

**File:** `apps/api-gateway/src/auth/auth.service.ts`

Inject orchestrator client, replace `login()` (lines 62–75):

```typescript
// Add to constructor:
@Inject('AUTH_ORCHESTRATOR') private readonly orchestrator: ClientProxy,

// Replace login():
async login(dto: LoginDto) {
  return firstValueFrom(this.orchestrator.send({ cmd: 'auth_login' }, dto));
}
```

Remove `issueTokens()` and `resolveTenantId()` from this file — they move to auth-orchestrator.

> `register()`, `refresh()`, `logout()`, `getMe()`, `acceptInvitation()` — **untouched**.

---

### T4 — User Service: New Fields + `void_password` RPC

#### Migration

New file: `apps/user-service/prisma/migrations/YYYYMMDD_add_password_expiry_fields/migration.sql`

```sql
ALTER TABLE "users"
  ADD COLUMN "password_changed_at"      TIMESTAMPTZ,
  ADD COLUMN "password_voided_at"       TIMESTAMPTZ,
  ADD COLUMN "password_reset_issued_at" TIMESTAMPTZ;

-- Backfill: existing users default to account creation date
UPDATE "users" SET "password_changed_at" = "created_at" WHERE "password_changed_at" IS NULL;
```

**File:** `apps/user-service/prisma/schema.prisma` — add to `User` model:

```prisma
password_changed_at      DateTime?
password_voided_at       DateTime?
password_reset_issued_at DateTime?
```

#### `users.controller.ts` — add:

```typescript
@MessagePattern({ cmd: 'void_password' })
async voidPassword(@Payload() { userId }: { userId: string }) {
  return this.usersService.voidPassword(userId);
}
```

#### `users.service.ts` — add method + extend `validateCredentials` select:

```typescript
async voidPassword(userId: string) {
  return this.prisma.user.update({
    where: { id: userId },
    data: {
      password_voided_at: new Date(),
      password_reset_issued_at: new Date(),
    },
  });
}
```

In `validateCredentials` Prisma select — add `password_changed_at` and `password_voided_at` to returned fields.

> Diagram WHERE clause already filters `AND password_voided_at IS NULL` — so voided users return null → 401 before expiry check runs.

---

### T5 — Notification Service: Password Expiry Email

**File:** `apps/notification-service/src/email/email.controller.ts` — add:

```typescript
@EventPattern({ cmd: 'send_password_expiry_email' })
async sendPasswordExpiryEmail(@Payload() payload: SendPasswordExpiryEmailPayload): Promise<void> {
  await this.emailService.sendPasswordExpiryEmail(payload);
}
```

**New DTO** (add to `email.service.ts` top or separate file):

```typescript
export interface SendPasswordExpiryEmailPayload {
  to: string;
  reset_url: string;
}
```

**File:** `apps/notification-service/src/email/email.service.ts` — add method mirroring `sendInvitationEmail`.

**File:** `apps/notification-service/src/email/templates/password-expiry/index.ts` — new template:

```typescript
export function passwordExpiryTemplate({ reset_url, year }: { reset_url: string; year: number }) {
  return {
    subject: 'Your password has expired — login link inside',
    html: `...`,  // mirror invitation template structure
    text: `Your password has expired. Click the link below to log in and set a new password.\n\n${reset_url}\n\nThis link expires in 15 minutes.`,
  };
}
```

---

## Build Sequence

```
T1  (config keys + env vars)
 │
 ▼
T4  (migration → prisma generate → void_password RPC)   ← unblocks T2
 │
 ▼
T2  (auth-orchestrator: main.ts, app.module, auth module/controller/service)
 │
 ▼
T3  (api-gateway: add AUTH_ORCHESTRATOR client, replace login())
 │
 ▼
T5  (notification: EventPattern + template)             ← independent, can parallel with T2
```

---

## File Touch Summary

| # | File | Action |
|---|------|--------|
| 1 | `packages/config/src/configuration.ts` | Add authOrchestratorService block |
| 2 | `.env` / `.env.example` | Add 4 env vars |
| 3 | `apps/auth-orchestrator/package.json` | CREATE |
| 4 | `apps/auth-orchestrator/tsconfig.json` | CREATE |
| 5 | `apps/auth-orchestrator/tsconfig.app.json` | CREATE |
| 6 | `apps/auth-orchestrator/src/main.ts` | CREATE |
| 7 | `apps/auth-orchestrator/src/app.module.ts` | CREATE |
| 8 | `apps/auth-orchestrator/src/auth/auth.module.ts` | CREATE |
| 9 | `apps/auth-orchestrator/src/auth/auth.controller.ts` | CREATE |
| 10 | `apps/auth-orchestrator/src/auth/auth.service.ts` | CREATE |
| 11 | `apps/auth-orchestrator/src/auth/dto/login.dto.ts` | CREATE |
| 12 | `apps/api-gateway/src/auth/auth.module.ts` | Add AUTH_ORCHESTRATOR client |
| 13 | `apps/api-gateway/src/auth/auth.service.ts` | Replace login(), remove issueTokens/resolveTenantId |
| 14 | `apps/user-service/prisma/schema.prisma` | 3 new fields on User |
| 15 | `apps/user-service/prisma/migrations/*/migration.sql` | CREATE + backfill |
| 16 | `apps/user-service/src/users/users.service.ts` | voidPassword() + extend select |
| 17 | `apps/user-service/src/users/users.controller.ts` | void_password MessagePattern |
| 18 | `apps/notification-service/src/email/email.controller.ts` | send_password_expiry_email EventPattern |
| 19 | `apps/notification-service/src/email/email.service.ts` | sendPasswordExpiryEmail() method |
| 20 | `apps/notification-service/src/email/templates/password-expiry/index.ts` | CREATE template |

---

## Risk Flags

| Risk | Detail |
|------|--------|
| **Backfill blast** | All users older than 90 days trigger expired flow on first login after deploy. Confirm intended or add grace period. |
| **Redis config key** | Verify `shared.apiGateway.redis.*` matches what `blocklist.module.ts` uses — do not assume. |
| **issueTokens move** | `store_refresh_token` RPC stays on user-service. Auth-orchestrator needs USER_SERVICE client — already registered. |
| **`shared.frontendUrl` key** | Verify this config key exists in `configuration.ts` — may need to add it. |
| **`date-fns` dependency** | Confirm `date-fns` in auth-orchestrator `package.json` — or use native `Date` math instead. |
| **raw_token in reset_url** | Never log `reset_url` — fire-and-forget emit only. Token in URL param, never in logs. |
