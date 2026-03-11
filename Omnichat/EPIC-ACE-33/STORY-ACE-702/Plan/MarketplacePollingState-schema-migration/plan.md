# Plan: Commit 1 — Add MarketplacePollingState Schema and Migration

## Context
EPIC-ACE-33 enables marketplace (TikTok, Shopee, Lazada) polling support. Unlike LINE/Facebook (push webhooks), marketplaces require a pull-based polling loop. Commit 1 lays the DB foundation: a `MarketplacePollingState` table that tracks per-account, per-type (chat/order) polling cursors and backoff state.

## Commit Message
```text
chore(omnichat-service): add MarketplacePollingState schema and migration
```

## Changes

### 1. `ace/apps/omnichat-service/prisma/schema.prisma`
Add relation to `ChannelAccount` model (after `raw_events` line):
```prisma
  polling_states MarketplacePollingState[]
```

Add new model (at end of file):
```prisma
model MarketplacePollingState {
  id                   String    @id @default(uuid())
  channel_account_id   String
  poll_type            String    // "chat" | "order"
  last_fetch_at        DateTime?
  backoff_until        DateTime?
  consecutive_failures Int       @default(0)
  last_error           String?
  created_at           DateTime  @default(now())
  updated_at           DateTime  @updatedAt

  channel_account ChannelAccount @relation(fields: [channel_account_id], references: [id])

  @@unique([channel_account_id, poll_type])
  @@index([backoff_until])
  @@map("marketplace_polling_states")
}
```

### 2. New migration folder + SQL
Path: `ace/apps/omnichat-service/prisma/migrations/20260311000000_add_marketplace_polling_state/migration.sql`

```sql
-- CreateTable
CREATE TABLE "marketplace_polling_states" (
    "id" TEXT NOT NULL,
    "channel_account_id" TEXT NOT NULL,
    "poll_type" TEXT NOT NULL,
    "last_fetch_at" TIMESTAMP(3),
    "backoff_until" TIMESTAMP(3),
    "consecutive_failures" INTEGER NOT NULL DEFAULT 0,
    "last_error" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "marketplace_polling_states_pkey" PRIMARY KEY ("id")
);

-- CreateIndex (unique)
CREATE UNIQUE INDEX "marketplace_polling_states_channel_account_id_poll_type_key"
    ON "marketplace_polling_states"("channel_account_id", "poll_type");

-- CreateIndex (backoff lookup)
CREATE INDEX "marketplace_polling_states_backoff_until_idx"
    ON "marketplace_polling_states"("backoff_until");

-- AddForeignKey
ALTER TABLE "marketplace_polling_states"
    ADD CONSTRAINT "marketplace_polling_states_channel_account_id_fkey"
    FOREIGN KEY ("channel_account_id") REFERENCES "channel_accounts"("id")
    ON DELETE RESTRICT ON UPDATE CASCADE;
```

**Note:** FK references `channel_accounts` (the `@@map` name of `ChannelAccount`), and uses PostgreSQL `TIMESTAMP(3)` (not SQLite `DATETIME`).

## Verification
- `cd ace && pnpm --filter omnichat-service build` — confirms Prisma schema compiles
- `npx prisma migrate dev --name add_marketplace_polling_state --schema apps/omnichat-service/prisma/schema.prisma` — runs migration against dev DB
- Confirm `marketplace_polling_states` table exists with correct columns, unique index on `(channel_account_id, poll_type)`, and index on `backoff_until`