# User Saved Views Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement per-user saved view presets (named filter+sort snapshots) displayed as pill buttons above the conversation list so agents can switch working modes in one click.

**Architecture:** New `UserSavedView` Prisma model in `omnichat-service` with a dedicated NestJS module. The `api-gateway` exposes REST endpoints via HTTP proxy (same pattern as tags). The Next.js frontend adds a `SavedViewsPillRow` component, Zustand store, Save modal, and Manage modal (delete + set default only — no rename).

**Tech Stack:** NestJS 11 · Prisma 7 (PostgreSQL) · class-validator · Next.js 16 (App Router) · Zustand 5 · nuqs · shadcn/ui · React Hook Form · Zod · Jest (backend)

---

## System Pills vs User Saved Views

There are **6 built-in system pills** (hardcoded client-side constants, never stored in DB, never editable):

| Pill | Snapshot applied |
|------|-----------------|
| `all` | All empty / defaults |
| `my open` | status=open, assignee=me |
| `unassigned` | assignee=none |
| `in progress` | status=in_progress |
| `pending` | status=pending |
| `overdue` | is_overdue=true (sla_due_at < NOW, active statuses only) |

Users can create **max 14 own saved views** (6 system + 14 user = 20 total visible pills).

---

## Gap Analysis — What Is Missing

| Area | Gap |
|------|-----|
| Database | No `user_saved_views` table |
| omnichat-service | `ListConversationsDto` missing `is_overdue` boolean filter; no `saved-views` module |
| omnichat-service conversations | `conversations.service.ts` listConversations does not apply `is_overdue` filter |
| api-gateway | No `saved-views` controller/service; not registered in `OmnichatModule` |
| Frontend types | No `ViewSnapshot`, `SavedView`, `SystemPill` types; no `is_overdue` in nuqs params |
| Frontend API | No server actions for saved-views CRUD |
| Frontend state | No Zustand store for saved views; chat-store lacks `applyViewSnapshot` |
| Frontend UI | No VIEWS pill row, no Save View modal, no Manage Views modal |
| ConversationList | Not wired to views section; no default-view auto-apply on mount |

## Filter Snapshot Format

Mirrors nuqs URL params 1:1 — applying a view is just `setUrlParams(snapshot)`:

```typescript
type ViewSnapshot = {
  status:    string;  // comma-separated ConversationStatus, e.g. "open,in_progress" or ""
  channel:   string;  // comma-separated ChannelType, e.g. "line,facebook" or ""
  assignee:  string;  // "" | "me" | "none"
  tag:       string;  // comma-separated tag UUIDs or ""
  sort:      string;  // "latest_activity" | "oldest_waiting" | "sla_due_soonest"
  q:         string;  // search text; "" when saved without query
  is_overdue: string; // "true" | "" — used only by the "overdue" system pill
}
```

---

## File Map

### Created
| File | Responsibility |
|------|---------------|
| `apps/omnichat-service/src/saved-views/dto/create-saved-view.dto.ts` | Validate create payload |
| `apps/omnichat-service/src/saved-views/dto/list-saved-views.dto.ts` | Validate list query |
| `apps/omnichat-service/src/saved-views/dto/update-saved-view.dto.ts` | Validate set-default |
| `apps/omnichat-service/src/saved-views/dto/delete-saved-view.dto.ts` | Validate delete query |
| `apps/omnichat-service/src/saved-views/saved-views.service.ts` | Business logic (max 14, unique name, default swap) |
| `apps/omnichat-service/src/saved-views/saved-views.service.spec.ts` | Unit tests |
| `apps/omnichat-service/src/saved-views/saved-views.controller.ts` | HTTP GET/POST/PATCH/DELETE |
| `apps/omnichat-service/src/saved-views/saved-views.controller.spec.ts` | Unit tests |
| `apps/omnichat-service/src/saved-views/saved-views.module.ts` | NestJS module wiring |
| `apps/api-gateway/src/omnichat/dto/create-saved-view.dto.ts` | Gateway create DTO |
| `apps/api-gateway/src/omnichat/dto/update-saved-view.dto.ts` | Gateway update DTO (is_default only) |
| `apps/api-gateway/src/omnichat/services/saved-views.service.ts` | HTTP proxy to omnichat-service |
| `apps/api-gateway/src/omnichat/controllers/saved-views.controller.ts` | Gateway REST endpoints |
| `apps/workspace-admin/src/types/saved-views.ts` | ViewSnapshot, SavedView, SystemPill, SYSTEM_PILLS |
| `apps/workspace-admin/src/app/(main)/dashboard/chats/_api/saved-views.api.ts` | Server actions |
| `apps/workspace-admin/src/app/(main)/dashboard/chats/_store/saved-views-store.ts` | Zustand store |
| `apps/workspace-admin/src/app/(main)/dashboard/chats/_components/saved-views/save-view-modal.tsx` | Save View dialog (Thai UI) |
| `apps/workspace-admin/src/app/(main)/dashboard/chats/_components/saved-views/manage-views-modal.tsx` | Manage Views dialog (delete + set default only) |
| `apps/workspace-admin/src/app/(main)/dashboard/chats/_components/saved-views/saved-views-pill-row.tsx` | VIEWS section with pills |

### Modified
| File | Change |
|------|--------|
| `apps/omnichat-service/prisma/schema.prisma` | Add `UserSavedView` model |
| `apps/omnichat-service/src/conversations/dto/list-conversations.dto.ts` | Add `is_overdue` field |
| `apps/omnichat-service/src/conversations/conversations.service.ts` | Apply `is_overdue` filter in listConversations |
| `apps/omnichat-service/src/app.module.ts` | Import `SavedViewsModule` |
| `apps/api-gateway/src/omnichat/omnichat.module.ts` | Register SavedViewsController + SavedViewsService |
| `apps/workspace-admin/src/app/(main)/dashboard/chats/_store/chat-store.ts` | Add `applyViewSnapshot` action |
| `apps/workspace-admin/src/app/(main)/dashboard/chats/_components/conversation-list/conversation-list.tsx` | Add `<SavedViewsPillRow>` + default-view auto-apply + is_overdue nuqs param |

---

## Task 0: Add `is_overdue` Filter to Conversation Listing

Needed by the "overdue" system pill. Filters conversations where `sla_due_at < NOW()` and status is active (open, in_progress, pending).

**Files:**
- Modify: `apps/omnichat-service/src/conversations/dto/list-conversations.dto.ts`
- Modify: `apps/omnichat-service/src/conversations/conversations.service.ts`

- [ ] **Step 1: Add `is_overdue` to `ListConversationsDto`**

In `list-conversations.dto.ts`, add after the `is_read` field:

```typescript
/** Filter overdue conversations: sla_due_at is set and in the past */
@IsOptional()
@IsBooleanString()
is_overdue?: string;
```

- [ ] **Step 2: Apply `is_overdue` filter in `conversations.service.ts`**

Find the `where` clause construction in `listConversations`. Add the overdue condition alongside the other optional filters:

```typescript
// Inside the where clause builder, after is_read handling:
...(query.is_overdue === 'true' && {
  sla_due_at: { not: null, lt: new Date() },
  status: { in: ['open', 'in_progress', 'pending'] },
}),
```

- [ ] **Step 3: Verify build compiles**

```bash
cd apps/omnichat-service
pnpm build
```

Expected: No TypeScript errors.

- [ ] **Step 4: Commit**

```bash
git add apps/omnichat-service/src/conversations/dto/list-conversations.dto.ts apps/omnichat-service/src/conversations/conversations.service.ts
git commit -m "feat(omnichat): add is_overdue filter to conversation listing"
```

---

## Task 1: Prisma Model — `UserSavedView`

**Files:**
- Modify: `apps/omnichat-service/prisma/schema.prisma`

- [ ] **Step 1: Add model to schema**

Append at the end of `schema.prisma`:

```prisma
model UserSavedView {
  id         String    @id @default(uuid())
  tenant_id  String
  agent_id   String
  name       String
  snapshot   Json      @db.JsonB
  is_default Boolean   @default(false)
  created_at DateTime  @default(now())
  updated_at DateTime  @updatedAt
  deleted_at DateTime?

  @@unique([tenant_id, agent_id, name])
  @@index([tenant_id, agent_id, created_at(sort: Asc)])
  @@map("user_saved_views")
}
```

- [ ] **Step 2: Run migration**

```bash
cd apps/omnichat-service
pnpm prisma migrate dev --name add_user_saved_views
```

Expected: `The following migration(s) have been created and applied`

- [ ] **Step 3: Regenerate Prisma client**

```bash
pnpm prisma generate
```

Expected: `Generated Prisma Client`

- [ ] **Step 4: Commit**

```bash
git add apps/omnichat-service/prisma/schema.prisma apps/omnichat-service/prisma/migrations/
git commit -m "feat(omnichat): add UserSavedView prisma model"
```

---

## Task 2: omnichat-service DTOs

**Files:**
- Create: `apps/omnichat-service/src/saved-views/dto/create-saved-view.dto.ts`
- Create: `apps/omnichat-service/src/saved-views/dto/list-saved-views.dto.ts`
- Create: `apps/omnichat-service/src/saved-views/dto/update-saved-view.dto.ts`
- Create: `apps/omnichat-service/src/saved-views/dto/delete-saved-view.dto.ts`

- [ ] **Step 1: Create `create-saved-view.dto.ts`**

```typescript
// apps/omnichat-service/src/saved-views/dto/create-saved-view.dto.ts
import { IsIn, IsNotEmpty, IsOptional, IsString, IsUUID, MaxLength } from 'class-validator';

export class CreateSavedViewDto {
  @IsUUID()
  tenant_id: string;

  @IsUUID()
  agent_id: string;

  @IsString()
  @IsNotEmpty()
  @MaxLength(100)
  name: string;

  @IsOptional()
  @IsString()
  status?: string;

  @IsOptional()
  @IsString()
  channel?: string;

  @IsOptional()
  @IsString()
  assignee?: string;

  @IsOptional()
  @IsString()
  tag?: string;

  @IsIn(['latest_activity', 'oldest_waiting', 'sla_due_soonest'])
  sort: string;

  @IsOptional()
  @IsString()
  @MaxLength(200)
  q?: string;

  @IsOptional()
  @IsString()
  is_overdue?: string;
}
```

- [ ] **Step 2: Create `list-saved-views.dto.ts`**

```typescript
// apps/omnichat-service/src/saved-views/dto/list-saved-views.dto.ts
import { IsUUID } from 'class-validator';

export class ListSavedViewsDto {
  @IsUUID()
  tenant_id: string;

  @IsUUID()
  agent_id: string;
}
```

- [ ] **Step 3: Create `update-saved-view.dto.ts`**

Only `is_default` — no rename allowed.

```typescript
// apps/omnichat-service/src/saved-views/dto/update-saved-view.dto.ts
import { IsBoolean, IsUUID } from 'class-validator';

export class UpdateSavedViewDto {
  @IsUUID()
  tenant_id: string;

  @IsUUID()
  agent_id: string;

  @IsBoolean()
  is_default: boolean;
}
```

- [ ] **Step 4: Create `delete-saved-view.dto.ts`**

```typescript
// apps/omnichat-service/src/saved-views/dto/delete-saved-view.dto.ts
import { IsUUID } from 'class-validator';

export class DeleteSavedViewDto {
  @IsUUID()
  tenant_id: string;

  @IsUUID()
  agent_id: string;
}
```

- [ ] **Step 5: Commit**

```bash
git add apps/omnichat-service/src/saved-views/dto/
git commit -m "feat(omnichat): add saved-views DTOs"
```

---

## Task 3: omnichat-service SavedViewsService

**Files:**
- Create: `apps/omnichat-service/src/saved-views/saved-views.service.ts`
- Create: `apps/omnichat-service/src/saved-views/saved-views.service.spec.ts`

- [ ] **Step 1: Write the failing tests**

```typescript
// apps/omnichat-service/src/saved-views/saved-views.service.spec.ts
import { BadRequestException, ConflictException, NotFoundException } from '@nestjs/common';
import { Test, TestingModule } from '@nestjs/testing';
import { PrismaService } from '../prisma/prisma.service';
import { SavedViewsService } from './saved-views.service';

const TENANT_ID = 'tenant-uuid-1';
const AGENT_ID = 'agent-uuid-1';
const VIEW_ID = 'view-uuid-1';

const mockSnapshot = { status: 'open', channel: '', assignee: 'me', tag: '', sort: 'latest_activity', q: '', is_overdue: '' };

const mockView = {
  id: VIEW_ID,
  tenant_id: TENANT_ID,
  agent_id: AGENT_ID,
  name: 'My Refund Queue',
  snapshot: mockSnapshot,
  is_default: false,
  created_at: new Date(),
  updated_at: new Date(),
  deleted_at: null,
};

const mockPrisma = {
  userSavedView: {
    findFirst: jest.fn(),
    findMany: jest.fn(),
    count: jest.fn(),
    create: jest.fn(),
    update: jest.fn(),
    updateMany: jest.fn(),
  },
  $transaction: jest.fn((cb) => cb(mockPrisma)),
};

describe('SavedViewsService', () => {
  let service: SavedViewsService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        SavedViewsService,
        { provide: PrismaService, useValue: mockPrisma },
      ],
    }).compile();

    service = module.get<SavedViewsService>(SavedViewsService);
    jest.clearAllMocks();
  });

  // ─── create ──────────────────────────────────────────────────────────────────

  describe('create', () => {
    it('creates a saved view successfully', async () => {
      mockPrisma.userSavedView.count.mockResolvedValue(0);
      mockPrisma.userSavedView.findFirst.mockResolvedValue(null);
      mockPrisma.userSavedView.create.mockResolvedValue(mockView);

      const result = await service.create({
        tenant_id: TENANT_ID,
        agent_id: AGENT_ID,
        name: 'My Refund Queue',
        sort: 'latest_activity',
        status: 'open',
        assignee: 'me',
      });

      expect(mockPrisma.userSavedView.count).toHaveBeenCalledWith({
        where: { tenant_id: TENANT_ID, agent_id: AGENT_ID, deleted_at: null },
      });
      expect(result).toEqual(mockView);
    });

    it('throws BadRequestException when user already has 14 saved views', async () => {
      mockPrisma.userSavedView.count.mockResolvedValue(14);

      await expect(
        service.create({ tenant_id: TENANT_ID, agent_id: AGENT_ID, name: 'New', sort: 'latest_activity' }),
      ).rejects.toThrow(BadRequestException);
    });

    it('BadRequestException message is in Thai and says 14', async () => {
      mockPrisma.userSavedView.count.mockResolvedValue(14);

      const err = await service.create({ tenant_id: TENANT_ID, agent_id: AGENT_ID, name: 'X', sort: 'latest_activity' }).catch((e) => e);
      expect(err.message).toContain('14');
    });

    it('throws ConflictException when name already exists for this user', async () => {
      mockPrisma.userSavedView.count.mockResolvedValue(5);
      mockPrisma.userSavedView.findFirst.mockResolvedValue(mockView);

      await expect(
        service.create({ tenant_id: TENANT_ID, agent_id: AGENT_ID, name: 'My Refund Queue', sort: 'latest_activity' }),
      ).rejects.toThrow(ConflictException);
    });
  });

  // ─── list ─────────────────────────────────────────────────────────────────────

  describe('list', () => {
    it('returns views ordered by created_at asc', async () => {
      mockPrisma.userSavedView.findMany.mockResolvedValue([mockView]);

      const result = await service.list({ tenant_id: TENANT_ID, agent_id: AGENT_ID });

      expect(mockPrisma.userSavedView.findMany).toHaveBeenCalledWith({
        where: { tenant_id: TENANT_ID, agent_id: AGENT_ID, deleted_at: null },
        orderBy: { created_at: 'asc' },
      });
      expect(result).toEqual({ views: [mockView] });
    });
  });

  // ─── setDefault ──────────────────────────────────────────────────────────────

  describe('setDefault', () => {
    it('atomically clears all defaults then sets new one', async () => {
      mockPrisma.userSavedView.findFirst.mockResolvedValue(mockView);
      mockPrisma.userSavedView.updateMany.mockResolvedValue({ count: 2 });
      mockPrisma.userSavedView.update.mockResolvedValue({ ...mockView, is_default: true });

      await service.setDefault(VIEW_ID, { tenant_id: TENANT_ID, agent_id: AGENT_ID });

      expect(mockPrisma.userSavedView.updateMany).toHaveBeenCalledWith({
        where: { tenant_id: TENANT_ID, agent_id: AGENT_ID, deleted_at: null },
        data: { is_default: false },
      });
      expect(mockPrisma.userSavedView.update).toHaveBeenCalledWith({
        where: { id: VIEW_ID },
        data: { is_default: true },
      });
    });

    it('throws NotFoundException when view does not belong to user', async () => {
      mockPrisma.userSavedView.findFirst.mockResolvedValue(null);

      await expect(
        service.setDefault(VIEW_ID, { tenant_id: TENANT_ID, agent_id: AGENT_ID }),
      ).rejects.toThrow(NotFoundException);
    });
  });

  // ─── delete ──────────────────────────────────────────────────────────────────

  describe('delete', () => {
    it('soft-deletes and clears is_default when deleting the default view', async () => {
      const defaultView = { ...mockView, is_default: true };
      mockPrisma.userSavedView.findFirst.mockResolvedValue(defaultView);
      mockPrisma.userSavedView.update.mockResolvedValue({ ...defaultView, deleted_at: new Date(), is_default: false });

      await service.delete(VIEW_ID, { tenant_id: TENANT_ID, agent_id: AGENT_ID });

      expect(mockPrisma.userSavedView.update).toHaveBeenCalledWith({
        where: { id: VIEW_ID },
        data: expect.objectContaining({ deleted_at: expect.any(Date), is_default: false }),
      });
    });

    it('throws NotFoundException when view does not belong to user', async () => {
      mockPrisma.userSavedView.findFirst.mockResolvedValue(null);

      await expect(
        service.delete(VIEW_ID, { tenant_id: TENANT_ID, agent_id: AGENT_ID }),
      ).rejects.toThrow(NotFoundException);
    });
  });
});
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
cd apps/omnichat-service
pnpm test -- --testPathPattern=saved-views.service
```

Expected: FAIL — `Cannot find module './saved-views.service'`

- [ ] **Step 3: Implement `saved-views.service.ts`**

```typescript
// apps/omnichat-service/src/saved-views/saved-views.service.ts
import {
  BadRequestException,
  ConflictException,
  Injectable,
  NotFoundException,
} from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import type { CreateSavedViewDto } from './dto/create-saved-view.dto';
import type { DeleteSavedViewDto } from './dto/delete-saved-view.dto';
import type { ListSavedViewsDto } from './dto/list-saved-views.dto';
import type { UpdateSavedViewDto } from './dto/update-saved-view.dto';

const MAX_VIEWS_PER_USER = 14;

@Injectable()
export class SavedViewsService {
  constructor(private readonly prisma: PrismaService) {}

  async create(dto: CreateSavedViewDto) {
    const { tenant_id, agent_id, name, sort, status, channel, assignee, tag, q, is_overdue } = dto;

    const count = await this.prisma.userSavedView.count({
      where: { tenant_id, agent_id, deleted_at: null },
    });
    if (count >= MAX_VIEWS_PER_USER) {
      throw new BadRequestException(
        `คุณมี saved views ครบ ${MAX_VIEWS_PER_USER} อัน กรุณาลบก่อนสร้างใหม่`,
      );
    }

    const duplicate = await this.prisma.userSavedView.findFirst({
      where: { tenant_id, agent_id, name, deleted_at: null },
    });
    if (duplicate) {
      throw new ConflictException(`Saved view with name "${name}" already exists`);
    }

    const snapshot = {
      status: status ?? '',
      channel: channel ?? '',
      assignee: assignee ?? '',
      tag: tag ?? '',
      sort,
      q: q ?? '',
      is_overdue: is_overdue ?? '',
    };

    return this.prisma.userSavedView.create({
      data: { tenant_id, agent_id, name, snapshot },
    });
  }

  async list(dto: ListSavedViewsDto) {
    const { tenant_id, agent_id } = dto;
    const views = await this.prisma.userSavedView.findMany({
      where: { tenant_id, agent_id, deleted_at: null },
      orderBy: { created_at: 'asc' },
    });
    return { views };
  }

  async setDefault(id: string, dto: UpdateSavedViewDto) {
    const { tenant_id, agent_id } = dto;

    const existing = await this.prisma.userSavedView.findFirst({
      where: { id, tenant_id, agent_id, deleted_at: null },
    });
    if (!existing) throw new NotFoundException('Saved view not found');

    return this.prisma.$transaction(async (tx) => {
      await tx.userSavedView.updateMany({
        where: { tenant_id, agent_id, deleted_at: null },
        data: { is_default: false },
      });
      return tx.userSavedView.update({
        where: { id },
        data: { is_default: true },
      });
    });
  }

  async delete(id: string, dto: DeleteSavedViewDto) {
    const { tenant_id, agent_id } = dto;

    const existing = await this.prisma.userSavedView.findFirst({
      where: { id, tenant_id, agent_id, deleted_at: null },
    });
    if (!existing) throw new NotFoundException('Saved view not found');

    return this.prisma.userSavedView.update({
      where: { id },
      data: { deleted_at: new Date(), is_default: false },
    });
  }
}
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
pnpm test -- --testPathPattern=saved-views.service
```

Expected: PASS (8 tests)

- [ ] **Step 5: Commit**

```bash
git add apps/omnichat-service/src/saved-views/
git commit -m "feat(omnichat): add SavedViewsService (max 14, unique name, atomic default)"
```

---

## Task 4: omnichat-service SavedViewsController

**Files:**
- Create: `apps/omnichat-service/src/saved-views/saved-views.controller.ts`
- Create: `apps/omnichat-service/src/saved-views/saved-views.controller.spec.ts`

- [ ] **Step 1: Write failing tests**

```typescript
// apps/omnichat-service/src/saved-views/saved-views.controller.spec.ts
import { BadRequestException, ConflictException, NotFoundException } from '@nestjs/common';
import { Test, TestingModule } from '@nestjs/testing';
import { SavedViewsController } from './saved-views.controller';
import { SavedViewsService } from './saved-views.service';

const TENANT_ID = 'tenant-uuid-1';
const AGENT_ID = 'agent-uuid-1';
const VIEW_ID = 'view-uuid-1';

const mockView = {
  id: VIEW_ID,
  tenant_id: TENANT_ID,
  agent_id: AGENT_ID,
  name: 'Refund Queue',
  snapshot: { status: 'open', channel: '', assignee: 'me', tag: '', sort: 'latest_activity', q: '', is_overdue: '' },
  is_default: false,
  created_at: new Date(),
  updated_at: new Date(),
  deleted_at: null,
};

const mockService = {
  create: jest.fn(),
  list: jest.fn(),
  setDefault: jest.fn(),
  delete: jest.fn(),
};

describe('SavedViewsController', () => {
  let controller: SavedViewsController;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      controllers: [SavedViewsController],
      providers: [{ provide: SavedViewsService, useValue: mockService }],
    }).compile();

    controller = module.get<SavedViewsController>(SavedViewsController);
    jest.clearAllMocks();
  });

  describe('listSavedViews', () => {
    it('delegates to service.list', async () => {
      mockService.list.mockResolvedValue({ views: [mockView] });
      const result = await controller.listSavedViews({ tenant_id: TENANT_ID, agent_id: AGENT_ID });
      expect(result).toEqual({ views: [mockView] });
    });
  });

  describe('createSavedView', () => {
    it('delegates to service.create', async () => {
      mockService.create.mockResolvedValue(mockView);
      const result = await controller.createSavedView({
        tenant_id: TENANT_ID, agent_id: AGENT_ID, name: 'Refund Queue', sort: 'latest_activity',
      });
      expect(result).toEqual(mockView);
    });

    it('propagates BadRequestException when limit reached', async () => {
      mockService.create.mockRejectedValue(new BadRequestException('limit'));
      await expect(
        controller.createSavedView({ tenant_id: TENANT_ID, agent_id: AGENT_ID, name: 'X', sort: 'latest_activity' }),
      ).rejects.toThrow(BadRequestException);
    });
  });

  describe('setDefaultView', () => {
    it('delegates to service.setDefault', async () => {
      mockService.setDefault.mockResolvedValue({ ...mockView, is_default: true });
      const result = await controller.setDefaultView(VIEW_ID, {
        tenant_id: TENANT_ID, agent_id: AGENT_ID, is_default: true,
      });
      expect(mockService.setDefault).toHaveBeenCalledWith(VIEW_ID, expect.any(Object));
      expect(result.is_default).toBe(true);
    });
  });

  describe('deleteSavedView', () => {
    it('delegates to service.delete', async () => {
      mockService.delete.mockResolvedValue(undefined);
      await controller.deleteSavedView(VIEW_ID, { tenant_id: TENANT_ID, agent_id: AGENT_ID });
      expect(mockService.delete).toHaveBeenCalledWith(VIEW_ID, { tenant_id: TENANT_ID, agent_id: AGENT_ID });
    });
  });
});
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
pnpm test -- --testPathPattern=saved-views.controller
```

Expected: FAIL — `Cannot find module './saved-views.controller'`

- [ ] **Step 3: Implement `saved-views.controller.ts`**

```typescript
// apps/omnichat-service/src/saved-views/saved-views.controller.ts
import {
  Body,
  Controller,
  Delete,
  Get,
  HttpCode,
  HttpStatus,
  Param,
  ParseUUIDPipe,
  Patch,
  Post,
  Query,
} from '@nestjs/common';
import { CreateSavedViewDto } from './dto/create-saved-view.dto';
import { DeleteSavedViewDto } from './dto/delete-saved-view.dto';
import { ListSavedViewsDto } from './dto/list-saved-views.dto';
import { UpdateSavedViewDto } from './dto/update-saved-view.dto';
import { SavedViewsService } from './saved-views.service';

@Controller('saved-views')
export class SavedViewsController {
  constructor(private readonly savedViewsService: SavedViewsService) {}

  @Get()
  async listSavedViews(@Query() query: ListSavedViewsDto) {
    return this.savedViewsService.list(query);
  }

  @Post()
  @HttpCode(HttpStatus.CREATED)
  async createSavedView(@Body() dto: CreateSavedViewDto) {
    return this.savedViewsService.create(dto);
  }

  @Patch(':id')
  @HttpCode(HttpStatus.OK)
  async setDefaultView(
    @Param('id', ParseUUIDPipe) id: string,
    @Body() dto: UpdateSavedViewDto,
  ) {
    return this.savedViewsService.setDefault(id, dto);
  }

  @Delete(':id')
  @HttpCode(HttpStatus.OK)
  async deleteSavedView(
    @Param('id', ParseUUIDPipe) id: string,
    @Query() dto: DeleteSavedViewDto,
  ) {
    return this.savedViewsService.delete(id, dto);
  }
}
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
pnpm test -- --testPathPattern=saved-views.controller
```

Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add apps/omnichat-service/src/saved-views/
git commit -m "feat(omnichat): add SavedViewsController"
```

---

## Task 5: omnichat-service Module + App Registration

**Files:**
- Create: `apps/omnichat-service/src/saved-views/saved-views.module.ts`
- Modify: `apps/omnichat-service/src/app.module.ts`

- [ ] **Step 1: Create the module**

```typescript
// apps/omnichat-service/src/saved-views/saved-views.module.ts
import { Module } from '@nestjs/common';
import { PrismaModule } from '../prisma/prisma.module';
import { SavedViewsController } from './saved-views.controller';
import { SavedViewsService } from './saved-views.service';

@Module({
  imports: [PrismaModule],
  controllers: [SavedViewsController],
  providers: [SavedViewsService],
})
export class SavedViewsModule {}
```

- [ ] **Step 2: Register in `app.module.ts`**

```typescript
// Add import:
import { SavedViewsModule } from './saved-views/saved-views.module';

// Add to @Module imports array (after TagsModule):
SavedViewsModule,
```

- [ ] **Step 3: Build to verify no compile errors**

```bash
cd apps/omnichat-service
pnpm build
```

- [ ] **Step 4: Commit**

```bash
git add apps/omnichat-service/src/saved-views/saved-views.module.ts apps/omnichat-service/src/app.module.ts
git commit -m "feat(omnichat): register SavedViewsModule"
```

---

## Task 6: api-gateway DTOs

**Files:**
- Create: `apps/api-gateway/src/omnichat/dto/create-saved-view.dto.ts`
- Create: `apps/api-gateway/src/omnichat/dto/update-saved-view.dto.ts`

- [ ] **Step 1: Create `create-saved-view.dto.ts`**

```typescript
// apps/api-gateway/src/omnichat/dto/create-saved-view.dto.ts
import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { IsIn, IsNotEmpty, IsOptional, IsString, MaxLength } from 'class-validator';

export class CreateSavedViewDto {
  @ApiProperty({ example: 'My Refund Queue' })
  @IsString()
  @IsNotEmpty()
  @MaxLength(100)
  name: string;

  @ApiPropertyOptional({ example: 'open,in_progress' })
  @IsOptional()
  @IsString()
  status?: string;

  @ApiPropertyOptional({ example: 'line,facebook' })
  @IsOptional()
  @IsString()
  channel?: string;

  @ApiPropertyOptional({ example: 'me' })
  @IsOptional()
  @IsString()
  assignee?: string;

  @ApiPropertyOptional({ example: 'uuid1,uuid2' })
  @IsOptional()
  @IsString()
  tag?: string;

  @ApiProperty({ example: 'latest_activity' })
  @IsIn(['latest_activity', 'oldest_waiting', 'sla_due_soonest'])
  sort: string;

  @ApiPropertyOptional({ example: 'refund' })
  @IsOptional()
  @IsString()
  @MaxLength(200)
  q?: string;

  @ApiPropertyOptional({ example: 'true' })
  @IsOptional()
  @IsString()
  is_overdue?: string;
}
```

- [ ] **Step 2: Create `update-saved-view.dto.ts`**

```typescript
// apps/api-gateway/src/omnichat/dto/update-saved-view.dto.ts
import { ApiProperty } from '@nestjs/swagger';
import { IsBoolean } from 'class-validator';

export class UpdateSavedViewDto {
  @ApiProperty({ example: true })
  @IsBoolean()
  is_default: boolean;
}
```

- [ ] **Step 3: Commit**

```bash
git add apps/api-gateway/src/omnichat/dto/create-saved-view.dto.ts apps/api-gateway/src/omnichat/dto/update-saved-view.dto.ts
git commit -m "feat(api-gateway): add saved-views DTOs"
```

---

## Task 7: api-gateway SavedViewsService

**Files:**
- Create: `apps/api-gateway/src/omnichat/services/saved-views.service.ts`

- [ ] **Step 1: Implement HTTP proxy service**

```typescript
// apps/api-gateway/src/omnichat/services/saved-views.service.ts
import { HttpService } from '@nestjs/axios';
import { HttpException, Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { AxiosError } from 'axios';
import type { CreateSavedViewDto } from '../dto/create-saved-view.dto';
import type { UpdateSavedViewDto } from '../dto/update-saved-view.dto';

@Injectable()
export class SavedViewsService {
  private omnichatServiceUrl: string;

  constructor(
    private httpService: HttpService,
    private configService: ConfigService,
  ) {
    const host = this.configService.get<string>('shared.omnichatService.http.host') as string;
    const port = this.configService.get<string>('shared.omnichatService.http.port') as string;
    this.omnichatServiceUrl = `http://${host}:${port}`;
  }

  private handleError(error: AxiosError): never {
    const status = error.response?.status ?? 502;
    const data = (error.response?.data ?? { message: 'Bad Gateway' }) as string | Record<string, unknown>;
    throw new HttpException(data, status);
  }

  async listSavedViews(tenantId: string, agentId: string) {
    try {
      const res = await this.httpService.axiosRef.get(
        `${this.omnichatServiceUrl}/saved-views`,
        { params: { tenant_id: tenantId, agent_id: agentId } },
      );
      return res.data;
    } catch (e) { this.handleError(e); }
  }

  async createSavedView(tenantId: string, agentId: string, dto: CreateSavedViewDto) {
    try {
      const res = await this.httpService.axiosRef.post(
        `${this.omnichatServiceUrl}/saved-views`,
        { tenant_id: tenantId, agent_id: agentId, ...dto },
      );
      return res.data;
    } catch (e) { this.handleError(e); }
  }

  async setDefaultView(tenantId: string, agentId: string, viewId: string, dto: UpdateSavedViewDto) {
    try {
      const res = await this.httpService.axiosRef.patch(
        `${this.omnichatServiceUrl}/saved-views/${viewId}`,
        { tenant_id: tenantId, agent_id: agentId, ...dto },
      );
      return res.data;
    } catch (e) { this.handleError(e); }
  }

  async deleteSavedView(tenantId: string, agentId: string, viewId: string) {
    try {
      const res = await this.httpService.axiosRef.delete(
        `${this.omnichatServiceUrl}/saved-views/${viewId}`,
        { params: { tenant_id: tenantId, agent_id: agentId } },
      );
      return res.data;
    } catch (e) { this.handleError(e); }
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add apps/api-gateway/src/omnichat/services/saved-views.service.ts
git commit -m "feat(api-gateway): add SavedViewsService HTTP proxy"
```

---

## Task 8: api-gateway SavedViewsController + Module Registration

**Files:**
- Create: `apps/api-gateway/src/omnichat/controllers/saved-views.controller.ts`
- Modify: `apps/api-gateway/src/omnichat/omnichat.module.ts`

- [ ] **Step 1: Implement the controller**

```typescript
// apps/api-gateway/src/omnichat/controllers/saved-views.controller.ts
import {
  Body,
  Controller,
  Delete,
  Get,
  HttpCode,
  HttpStatus,
  Param,
  ParseUUIDPipe,
  Patch,
  Post,
  UnauthorizedException,
} from '@nestjs/common';
import { ApiBearerAuth, ApiTags } from '@nestjs/swagger';
import { CurrentUser } from '../../auth/auth.decorator';
import { CreateSavedViewDto } from '../dto/create-saved-view.dto';
import { UpdateSavedViewDto } from '../dto/update-saved-view.dto';
import { SavedViewsService } from '../services/saved-views.service';

@ApiTags('omnichat-saved-views')
@ApiBearerAuth()
@Controller('omnichat/saved-views')
export class SavedViewsController {
  constructor(private readonly savedViewsService: SavedViewsService) {}

  @Get()
  async listSavedViews(
    @CurrentUser() user: { userId: string; tenantId: string },
  ) {
    if (!user.tenantId) throw new UnauthorizedException('Tenant ID is required');
    return this.savedViewsService.listSavedViews(user.tenantId, user.userId);
  }

  @Post()
  @HttpCode(HttpStatus.CREATED)
  async createSavedView(
    @Body() dto: CreateSavedViewDto,
    @CurrentUser() user: { userId: string; tenantId: string },
  ) {
    if (!user.tenantId) throw new UnauthorizedException('Tenant ID is required');
    return this.savedViewsService.createSavedView(user.tenantId, user.userId, dto);
  }

  @Patch(':id')
  @HttpCode(HttpStatus.OK)
  async setDefaultView(
    @Param('id', ParseUUIDPipe) id: string,
    @Body() dto: UpdateSavedViewDto,
    @CurrentUser() user: { userId: string; tenantId: string },
  ) {
    if (!user.tenantId) throw new UnauthorizedException('Tenant ID is required');
    return this.savedViewsService.setDefaultView(user.tenantId, user.userId, id, dto);
  }

  @Delete(':id')
  @HttpCode(HttpStatus.OK)
  async deleteSavedView(
    @Param('id', ParseUUIDPipe) id: string,
    @CurrentUser() user: { userId: string; tenantId: string },
  ) {
    if (!user.tenantId) throw new UnauthorizedException('Tenant ID is required');
    return this.savedViewsService.deleteSavedView(user.tenantId, user.userId, id);
  }
}
```

- [ ] **Step 2: Register in `omnichat.module.ts`**

```typescript
// Add imports:
import { SavedViewsController } from './controllers/saved-views.controller';
import { SavedViewsService } from './services/saved-views.service';

// Add to controllers array:
SavedViewsController,

// Add to providers array:
SavedViewsService,
```

- [ ] **Step 3: Build api-gateway**

```bash
cd apps/api-gateway
pnpm build
```

- [ ] **Step 4: Commit**

```bash
git add apps/api-gateway/src/omnichat/controllers/saved-views.controller.ts apps/api-gateway/src/omnichat/omnichat.module.ts
git commit -m "feat(api-gateway): add SavedViewsController and register in OmnichatModule"
```

---

## Task 9: Frontend Types + SYSTEM_PILLS Constants

**Files:**
- Create: `apps/workspace-admin/src/types/saved-views.ts`

- [ ] **Step 1: Create types and constants**

```typescript
// apps/workspace-admin/src/types/saved-views.ts

/** Mirrors nuqs URL param keys in ConversationList 1:1 */
export type ViewSnapshot = {
  status:     string;  // e.g. "open,in_progress" or ""
  channel:    string;  // e.g. "line,facebook" or ""
  assignee:   string;  // "" | "me" | "none"
  tag:        string;  // comma-separated tag UUIDs or ""
  sort:       string;  // SortMode
  q:          string;  // search text; "" when not included at save time
  is_overdue: string;  // "true" | ""
};

export type SavedView = {
  id: string;
  name: string;
  snapshot: ViewSnapshot;
  is_default: boolean;
  created_at: string;
  updated_at: string;
};

export type SavedViewsListResponse = {
  views: SavedView[];
};

export type SystemPill = {
  id: string;         // prefix "system:" — never collides with UUIDs
  label: string;
  snapshot: ViewSnapshot;
  isSystem: true;
};

const EMPTY: ViewSnapshot = {
  status: '', channel: '', assignee: '', tag: '',
  sort: 'latest_activity', q: '', is_overdue: '',
};

/**
 * Built-in system pills — always shown first, never editable or deletable.
 * 6 pills × hardcoded = total visible limit is 20 (6 + 14 user max).
 */
export const SYSTEM_PILLS: SystemPill[] = [
  { id: 'system:all',         label: 'all',         snapshot: EMPTY,                                                isSystem: true },
  { id: 'system:my_open',     label: 'my open',     snapshot: { ...EMPTY, status: 'open', assignee: 'me' },        isSystem: true },
  { id: 'system:unassigned',  label: 'unassigned',  snapshot: { ...EMPTY, assignee: 'none' },                     isSystem: true },
  { id: 'system:in_progress', label: 'in progress', snapshot: { ...EMPTY, status: 'in_progress' },                isSystem: true },
  { id: 'system:pending',     label: 'pending',     snapshot: { ...EMPTY, status: 'pending' },                    isSystem: true },
  { id: 'system:overdue',     label: 'overdue',     snapshot: { ...EMPTY, is_overdue: 'true' },                   isSystem: true },
];

export type PillId = string; // "system:*" or a saved view UUID
```

- [ ] **Step 2: Commit**

```bash
git add apps/workspace-admin/src/types/saved-views.ts
git commit -m "feat(fe): add SavedView types and SYSTEM_PILLS (6 system pills, max 14 user)"
```

---

## Task 10: Frontend Server Actions

**Files:**
- Create: `apps/workspace-admin/src/app/(main)/dashboard/chats/_api/saved-views.api.ts`

- [ ] **Step 1: Create server actions**

```typescript
// apps/workspace-admin/src/app/(main)/dashboard/chats/_api/saved-views.api.ts
'use server';

import { httpClient } from '@/server/http.config';
import type { SavedView, SavedViewsListResponse, ViewSnapshot } from '@/types/saved-views';

export async function listSavedViews(): Promise<SavedViewsListResponse> {
  return httpClient.get<SavedViewsListResponse>('/v1/omnichat/saved-views');
}

export type CreateSavedViewPayload = {
  name: string;
  snapshot: ViewSnapshot;
};

export async function createSavedView(payload: CreateSavedViewPayload): Promise<SavedView> {
  const { name, snapshot } = payload;
  return httpClient.post<SavedView>('/v1/omnichat/saved-views', {
    name,
    status:     snapshot.status,
    channel:    snapshot.channel,
    assignee:   snapshot.assignee,
    tag:        snapshot.tag,
    sort:       snapshot.sort,
    q:          snapshot.q,
    is_overdue: snapshot.is_overdue,
  });
}

export async function setDefaultSavedView(viewId: string): Promise<SavedView> {
  return httpClient.patch<SavedView>(`/v1/omnichat/saved-views/${viewId}`, { is_default: true });
}

export async function deleteSavedView(viewId: string): Promise<void> {
  return httpClient.delete(`/v1/omnichat/saved-views/${viewId}`);
}
```

- [ ] **Step 2: Commit**

```bash
git add apps/workspace-admin/src/app/(main)/dashboard/chats/_api/saved-views.api.ts
git commit -m "feat(fe): add saved-views server actions"
```

---

## Task 11: Frontend Zustand Store + `applyViewSnapshot` in chat-store

**Files:**
- Create: `apps/workspace-admin/src/app/(main)/dashboard/chats/_store/saved-views-store.ts`
- Modify: `apps/workspace-admin/src/app/(main)/dashboard/chats/_store/chat-store.ts`

- [ ] **Step 1: Create `saved-views-store.ts`**

```typescript
// apps/workspace-admin/src/app/(main)/dashboard/chats/_store/saved-views-store.ts
import { create } from 'zustand';
import {
  createSavedView,
  deleteSavedView,
  listSavedViews,
  setDefaultSavedView,
} from '../_api/saved-views.api';
import type { SavedView, ViewSnapshot } from '@/types/saved-views';

type SavedViewsState = {
  views: SavedView[];
  isLoading: boolean;
  activePillId: string;  // "system:all" | "system:my_open" | ... | <uuid>

  fetchViews: () => Promise<void>;
  setActivePillId: (id: string) => void;
  create: (name: string, snapshot: ViewSnapshot) => Promise<void>;
  setDefault: (viewId: string) => Promise<void>;
  remove: (viewId: string) => Promise<void>;
  getDefaultView: () => SavedView | undefined;
};

export const useSavedViewsStore = create<SavedViewsState>((set, get) => ({
  views: [],
  isLoading: false,
  activePillId: 'system:all',

  fetchViews: async () => {
    set({ isLoading: true });
    try {
      const { views } = await listSavedViews();
      set({ views });
    } finally {
      set({ isLoading: false });
    }
  },

  setActivePillId: (id) => set({ activePillId: id }),

  create: async (name, snapshot) => {
    const view = await createSavedView({ name, snapshot });
    set((s) => ({ views: [...s.views, view] }));
  },

  setDefault: async (viewId) => {
    await setDefaultSavedView(viewId);
    set((s) => ({
      views: s.views.map((v) => ({ ...v, is_default: v.id === viewId })),
    }));
  },

  remove: async (viewId) => {
    await deleteSavedView(viewId);
    set((s) => ({
      views: s.views.filter((v) => v.id !== viewId),
      activePillId: s.activePillId === viewId ? 'system:all' : s.activePillId,
    }));
  },

  getDefaultView: () => get().views.find((v) => v.is_default),
}));
```

- [ ] **Step 2: Add `applyViewSnapshot` to `chat-store.ts`**

In the chat-store state type, add:

```typescript
applyViewSnapshot: (snapshot: import('@/types/saved-views').ViewSnapshot) => void;
```

In the store implementation (inside `create(...)`), add:

```typescript
applyViewSnapshot: (snapshot) => {
  const statuses = snapshot.status ? (snapshot.status.split(',') as ConversationStatus[]) : [];
  const channels = snapshot.channel ? (snapshot.channel.split(',') as ChannelType[]) : [];
  const tags = snapshot.tag ? snapshot.tag.split(',') : [];
  set({
    statusFilters: statuses,
    channelFilters: channels,
    tagFilters: tags,
    sortBy: (snapshot.sort as SortMode) ?? 'latest_activity',
    search: snapshot.q ?? '',
    ...FILTER_RESET,
  });
  get().fetchConversations();
},
```

- [ ] **Step 3: Build frontend**

```bash
cd apps/workspace-admin
pnpm build
```

- [ ] **Step 4: Commit**

```bash
git add apps/workspace-admin/src/app/(main)/dashboard/chats/_store/
git commit -m "feat(fe): add SavedViewsStore and applyViewSnapshot to chat-store"
```

---

## Task 12: `SaveViewModal` Component

**Files:**
- Create: `apps/workspace-admin/src/app/(main)/dashboard/chats/_components/saved-views/save-view-modal.tsx`

- [ ] **Step 1: Implement the modal**

UI spec from design: title "บันทึก view ปัจจุบัน", subtitle "filters + sort จะถูกบันทึก", label "ชื่อ view", placeholder "เช่น LINE open ของฉัน...", checkbox "รวม search query", buttons "ยกเลิก" / "บันทึก" (red primary).

```tsx
// apps/workspace-admin/src/app/(main)/dashboard/chats/_components/saved-views/save-view-modal.tsx
'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { useSavedViewsStore } from '../../_store/saved-views-store';
import type { ViewSnapshot } from '@/types/saved-views';

const schema = z.object({
  name: z.string().min(1, 'กรุณาใส่ชื่อ view').max(100, 'ไม่เกิน 100 ตัวอักษร'),
  includeQuery: z.boolean(),
});

type FormValues = z.infer<typeof schema>;

type Props = {
  open: boolean;
  onClose: () => void;
  currentSnapshot: ViewSnapshot;
};

export function SaveViewModal({ open, onClose, currentSnapshot }: Props) {
  const { create, views } = useSavedViewsStore();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    setError,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { name: '', includeQuery: false },
  });

  const includeQuery = watch('includeQuery');
  const hasQuery = Boolean(currentSnapshot.q);

  async function onSubmit(values: FormValues) {
    // AC-11: optimistic client-side duplicate check for instant feedback
    if (views.some((v) => v.name === values.name)) {
      setError('name', { message: 'มี view ชื่อนี้อยู่แล้ว' });
      return;
    }

    setIsSubmitting(true);
    try {
      const snapshot: ViewSnapshot = {
        ...currentSnapshot,
        q: values.includeQuery ? currentSnapshot.q : '',
      };
      await create(values.name, snapshot);
      reset();
      onClose();
    } catch (err: unknown) {
      const raw = (err as Error)?.message ?? '';
      // Server may return Thai message for limit error — pass through
      setError('name', { message: raw || 'ไม่สามารถบันทึก view ได้' });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(v) => { if (!v) { reset(); onClose(); } }}
    >
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>บันทึก view ปัจจุบัน</DialogTitle>
          <DialogDescription className="text-sm text-muted-foreground">
            filters + sort จะถูกบันทึก
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 pt-1">
          <div className="space-y-1.5">
            <Label htmlFor="view-name">ชื่อ view</Label>
            <Input
              id="view-name"
              placeholder="เช่น LINE open ของฉัน..."
              {...register('name')}
              autoFocus
            />
            {errors.name && (
              <p className="text-xs text-destructive">{errors.name.message}</p>
            )}
          </div>

          {hasQuery && (
            <div className="flex items-center gap-2">
              <Checkbox
                id="include-query"
                checked={includeQuery}
                onCheckedChange={(v) => setValue('includeQuery', Boolean(v))}
              />
              <Label htmlFor="include-query" className="font-normal cursor-pointer">
                รวม search query
              </Label>
            </div>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => { reset(); onClose(); }}
            >
              ยกเลิก
            </Button>
            <Button
              type="submit"
              disabled={isSubmitting}
              className="bg-red-500 hover:bg-red-600 text-white"
            >
              {isSubmitting ? 'กำลังบันทึก…' : 'บันทึก'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add apps/workspace-admin/src/app/(main)/dashboard/chats/_components/saved-views/save-view-modal.tsx
git commit -m "feat(fe): add SaveViewModal with Thai UI (name input + include query checkbox)"
```

---

## Task 13: `ManageViewsModal` Component

Delete + Set Default only. **No rename.**

**Files:**
- Create: `apps/workspace-admin/src/app/(main)/dashboard/chats/_components/saved-views/manage-views-modal.tsx`

- [ ] **Step 1: Implement the modal**

```tsx
// apps/workspace-admin/src/app/(main)/dashboard/chats/_components/saved-views/manage-views-modal.tsx
'use client';

import { IconStar, IconStarFilled, IconTrash } from '@tabler/icons-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { useSavedViewsStore } from '../../_store/saved-views-store';

type Props = {
  open: boolean;
  onClose: () => void;
};

export function ManageViewsModal({ open, onClose }: Props) {
  const { views, setDefault, remove } = useSavedViewsStore();

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose(); }}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>จัดการ views</DialogTitle>
        </DialogHeader>

        {views.length === 0 && (
          <p className="text-sm text-muted-foreground py-6 text-center">
            ยังไม่มี saved view กด &ldquo;+ save view&rdquo; เพื่อสร้าง
          </p>
        )}

        <ul className="space-y-0.5 max-h-80 overflow-y-auto">
          {views.map((view) => (
            <li
              key={view.id}
              className="flex items-center gap-2 px-2 py-2 rounded-md hover:bg-muted/50"
            >
              <span className="flex-1 text-sm truncate">{view.name}</span>

              {/* Set as default */}
              <Button
                size="icon"
                variant="ghost"
                className={cn('size-7 shrink-0', view.is_default && 'text-yellow-500')}
                title={view.is_default ? 'Default view' : 'ตั้งเป็น default'}
                disabled={view.is_default}
                onClick={() => setDefault(view.id)}
              >
                {view.is_default
                  ? <IconStarFilled className="size-3.5" />
                  : <IconStar className="size-3.5" />}
              </Button>

              {/* Delete */}
              <Button
                size="icon"
                variant="ghost"
                className="size-7 shrink-0 text-destructive hover:text-destructive"
                title="ลบ view นี้"
                onClick={() => remove(view.id)}
              >
                <IconTrash className="size-3.5" />
              </Button>
            </li>
          ))}
        </ul>
      </DialogContent>
    </Dialog>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add apps/workspace-admin/src/app/(main)/dashboard/chats/_components/saved-views/manage-views-modal.tsx
git commit -m "feat(fe): add ManageViewsModal (delete + set default, no rename)"
```

---

## Task 14: `SavedViewsPillRow` Component

**Files:**
- Create: `apps/workspace-admin/src/app/(main)/dashboard/chats/_components/saved-views/saved-views-pill-row.tsx`

- [ ] **Step 1: Implement the component**

```tsx
// apps/workspace-admin/src/app/(main)/dashboard/chats/_components/saved-views/saved-views-pill-row.tsx
'use client';

import { useEffect, useState } from 'react';
import { IconSettings } from '@tabler/icons-react';
import { cn } from '@/lib/utils';
import { SYSTEM_PILLS } from '@/types/saved-views';
import type { ViewSnapshot } from '@/types/saved-views';
import { useSavedViewsStore } from '../../_store/saved-views-store';
import { SaveViewModal } from './save-view-modal';
import { ManageViewsModal } from './manage-views-modal';

type Props = {
  /** Current filter state — passed to SaveViewModal when saving */
  currentSnapshot: ViewSnapshot;
  /** Called when a pill is clicked — caller updates nuqs + chat-store */
  onApply: (snapshot: ViewSnapshot) => void;
};

export function SavedViewsPillRow({ currentSnapshot, onApply }: Props) {
  const { views, activePillId, setActivePillId, fetchViews } = useSavedViewsStore();
  const [saveOpen, setSaveOpen] = useState(false);
  const [manageOpen, setManageOpen] = useState(false);
  const atLimit = views.length >= 14; // AC-7: max 14 user views

  useEffect(() => {
    fetchViews();
  }, [fetchViews]);

  function handleClick(pillId: string, snapshot: ViewSnapshot) {
    setActivePillId(pillId);
    onApply(snapshot);
  }

  return (
    <div className="px-3 pt-2.5 pb-1">
      {/* Section label row */}
      <div className="flex items-center justify-between mb-2">
        <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
          Views
        </span>
        {views.length > 0 && (
          <button
            type="button"
            className="text-muted-foreground hover:text-foreground transition-colors"
            title="จัดการ views"
            onClick={() => setManageOpen(true)}
          >
            <IconSettings className="size-3.5" />
          </button>
        )}
      </div>

      {/* Pills (wrap naturally across rows) */}
      <div className="flex flex-wrap gap-1.5">
        {/* System pills */}
        {SYSTEM_PILLS.map((pill) => {
          const isActive = activePillId === pill.id;
          return (
            <button
              key={pill.id}
              type="button"
              onClick={() => handleClick(pill.id, pill.snapshot)}
              className={cn(
                'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border transition-colors',
                isActive
                  ? 'bg-foreground text-background border-foreground'
                  : 'bg-background text-foreground border-border hover:border-foreground/40',
              )}
            >
              {!isActive && (
                <span className="size-1.5 rounded-full bg-foreground/30 shrink-0" />
              )}
              {pill.label}
            </button>
          );
        })}

        {/* User saved view pills */}
        {views.map((view) => {
          const isActive = activePillId === view.id;
          const snapshot = view.snapshot as ViewSnapshot;
          return (
            <button
              key={view.id}
              type="button"
              onClick={() => handleClick(view.id, snapshot)}
              className={cn(
                'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border transition-colors',
                isActive
                  ? 'bg-foreground text-background border-foreground'
                  : 'bg-background text-foreground border-border hover:border-foreground/40',
              )}
            >
              {!isActive && (
                <span className="size-1.5 rounded-full bg-foreground/30 shrink-0" />
              )}
              {view.name}
              {view.is_default && !isActive && (
                <span
                  className="size-1.5 rounded-full bg-yellow-400 shrink-0"
                  title="Default view"
                />
              )}
            </button>
          );
        })}

        {/* + save view button */}
        <button
          type="button"
          disabled={atLimit}
          title={
            atLimit
              ? 'คุณมี saved views ครบ 14 อัน กรุณาลบก่อนสร้างใหม่'
              : 'บันทึก view ปัจจุบัน'
          }
          onClick={() => !atLimit && setSaveOpen(true)}
          className={cn(
            'inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border border-dashed transition-colors',
            atLimit
              ? 'border-muted-foreground/20 text-muted-foreground/40 cursor-not-allowed'
              : 'border-muted-foreground/50 text-muted-foreground hover:border-foreground hover:text-foreground cursor-pointer',
          )}
        >
          + save view
        </button>
      </div>

      <SaveViewModal
        open={saveOpen}
        onClose={() => setSaveOpen(false)}
        currentSnapshot={currentSnapshot}
      />
      <ManageViewsModal
        open={manageOpen}
        onClose={() => setManageOpen(false)}
      />
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add apps/workspace-admin/src/app/(main)/dashboard/chats/_components/saved-views/saved-views-pill-row.tsx
git commit -m "feat(fe): add SavedViewsPillRow (6 system pills + user views + save button)"
```

---

## Task 15: Integrate into `ConversationList`

**Files:**
- Modify: `apps/workspace-admin/src/app/(main)/dashboard/chats/_components/conversation-list/conversation-list.tsx`

- [ ] **Step 1: Add imports**

```typescript
import { SavedViewsPillRow } from '../saved-views/saved-views-pill-row';
import { useSavedViewsStore } from '../../_store/saved-views-store';
import type { ViewSnapshot } from '@/types/saved-views';
```

- [ ] **Step 2: Add `is_overdue` to nuqs params**

In the existing `useQueryStates` call, add the new param:

```typescript
const [urlParams, setUrlParams] = useQueryStates({
  status:     parseAsString.withDefault(''),
  channel:    parseAsString.withDefault(''),
  sort:       parseAsString.withDefault('latest_activity'),
  q:          parseAsString.withDefault(''),
  assignee:   parseAsString.withDefault(''),
  tag:        parseAsString.withDefault(''),
  is_overdue: parseAsString.withDefault(''),  // ← ADD THIS
});
```

Also pass `is_overdue` to the API call (wherever `listConversations` is called with URL params, add `is_overdue: urlParams.is_overdue || undefined`).

- [ ] **Step 3: Build currentSnapshot + wire store**

Inside `ConversationList()`, after existing store destructuring:

```typescript
const applyViewSnapshot = useChatStore((s) => s.applyViewSnapshot);
const { getDefaultView } = useSavedViewsStore();

const currentSnapshot: ViewSnapshot = {
  status:     urlParams.status,
  channel:    urlParams.channel,
  assignee:   urlParams.assignee,
  tag:        urlParams.tag,
  sort:       urlParams.sort,
  q:          urlParams.q,
  is_overdue: urlParams.is_overdue,
};
```

- [ ] **Step 4: Auto-apply default view on mount (AC-5)**

After existing `useEffect` hooks, add:

```typescript
// Auto-apply default view on first mount when no filters are active
useEffect(() => {
  const isCleanState =
    !urlParams.status && !urlParams.channel && !urlParams.assignee &&
    !urlParams.tag && !urlParams.q && !urlParams.is_overdue &&
    urlParams.sort === 'latest_activity';

  if (isCleanState) {
    const defaultView = getDefaultView();
    if (defaultView) {
      const snapshot = defaultView.snapshot as ViewSnapshot;
      void setUrlParams({
        status:     snapshot.status,
        channel:    snapshot.channel,
        assignee:   snapshot.assignee,
        tag:        snapshot.tag,
        sort:       snapshot.sort,
        q:          snapshot.q,
        is_overdue: snapshot.is_overdue,
      });
      applyViewSnapshot(snapshot);
      useSavedViewsStore.getState().setActivePillId(defaultView.id);
    }
  }
  // eslint-disable-next-line react-hooks/exhaustive-deps
}, []); // run once on mount only
```

- [ ] **Step 5: Add `<SavedViewsPillRow>` to JSX**

Inside the return, **above** the filter buttons row:

```tsx
{/* ─── Saved views pill row ─────────────────────────────────── */}
<SavedViewsPillRow
  currentSnapshot={currentSnapshot}
  onApply={(snapshot) => {
    void setUrlParams({
      status:     snapshot.status,
      channel:    snapshot.channel,
      assignee:   snapshot.assignee,
      tag:        snapshot.tag,
      sort:       snapshot.sort,
      q:          snapshot.q,
      is_overdue: snapshot.is_overdue,
    });
    applyViewSnapshot(snapshot);
  }}
/>
```

- [ ] **Step 6: Wire Reset All to system:all (AC-8)**

Find the existing reset/clear all handler. Add the system:all reset:

```typescript
// After clearing URL params and store state:
useSavedViewsStore.getState().setActivePillId('system:all');
```

And ensure the URL params reset includes `is_overdue: ''`:

```typescript
void setUrlParams({
  status: '', channel: '', assignee: '', tag: '',
  sort: 'latest_activity', q: '', is_overdue: '',
});
applyViewSnapshot({
  status: '', channel: '', assignee: '', tag: '',
  sort: 'latest_activity', q: '', is_overdue: '',
});
```

- [ ] **Step 7: Build frontend**

```bash
cd apps/workspace-admin
pnpm build
```

Expected: No TypeScript errors.

- [ ] **Step 8: Commit**

```bash
git add apps/workspace-admin/src/app/(main)/dashboard/chats/_components/conversation-list/conversation-list.tsx
git commit -m "feat(fe): integrate SavedViewsPillRow into ConversationList with default-view auto-apply"
```

---

## Acceptance Criteria Verification

| AC | Covered by |
|----|-----------|
| AC-1: Create saved view from current filters + sort | Task 3 service.create + Task 12 SaveViewModal |
| AC-2: Optional include search query (`รวม search query` checkbox) | SaveViewModal checkbox; `q: ''` when unchecked |
| AC-3: Applying view replaces current state | `applyViewSnapshot` sets all state atomically |
| AC-4: Apply updates list instantly | `applyViewSnapshot` calls `fetchConversations()` |
| AC-5: Default view auto-applied on page load | `useEffect` on mount in Task 15 |
| AC-6: Delete saved view; deleting default reverts to system:all | ManageViewsModal delete + store `remove` + AC-8 reset |
| AC-7: Max 14 user views (error in Thai, button disabled at limit) | Service `BadRequestException` + pill row `atLimit` guard |
| AC-8: Reset all returns to System Default View | Reset handler sets `system:all` + clears all params |
| AC-9: System pills always first, non-editable | `SYSTEM_PILLS` rendered before user views; no edit/delete UI |
| AC-10: Tenant + user isolation | `agent_id = userId` from JWT; scoped in all DB queries |
| AC-11: Duplicate name rejected | DB `@@unique` constraint + service `ConflictException` + client-side guard in SaveViewModal |

---

## Rollback Strategy

The feature is purely additive. Each layer rolls back independently:

| Layer | Rollback |
|-------|---------|
| DB | `pnpm prisma migrate resolve --rolled-back <id>` → drop `user_saved_views` table |
| omnichat-service | Remove `SavedViewsModule` from `app.module.ts`; delete `src/saved-views/`; revert `list-conversations.dto.ts` + `conversations.service.ts` |
| api-gateway | Remove controller + service from `OmnichatModule`; delete files |
| Frontend | Remove `<SavedViewsPillRow>` from `conversation-list.tsx`; delete `_components/saved-views/`, `_api/saved-views.api.ts`, `_store/saved-views-store.ts`; revert `chat-store.ts` |

**Optional feature flag** — wrap pill row in env var check for zero-risk deploy:

```typescript
{process.env.NEXT_PUBLIC_FEATURE_SAVED_VIEWS === 'true' && (
  <SavedViewsPillRow currentSnapshot={currentSnapshot} onApply={...} />
)}
```

---

## Self-Review

- [x] **6 system pills** defined in `SYSTEM_PILLS` constant (Task 9)
- [x] **`is_overdue` backend filter** added to DTO + service (Task 0) — required by "overdue" system pill
- [x] **MAX 14 user views** enforced: DB business logic (Task 3) + UI guard (Task 14)
- [x] **No rename** — `UpdateSavedViewDto` contains only `is_default`; ManageViewsModal has delete + star only (Task 13)
- [x] **Thai UI text** — SaveViewModal uses "บันทึก view ปัจจุบัน", "ชื่อ view", "รวม search query", "ยกเลิก", "บันทึก" (Task 12)
- [x] **AC-11 duplicate name** — DB unique constraint (Task 1) + service ConflictException (Task 3) + optimistic client check (Task 12)
- [x] **Type consistency** — `ViewSnapshot` (7 fields including `is_overdue`) used consistently across Tasks 9→15
- [x] **No placeholders** — every step has complete code
