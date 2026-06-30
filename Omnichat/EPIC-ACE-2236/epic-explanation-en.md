# EPIC ACE-2236: Broadcast — Simplified Explanation (grounded in real code)

**Status:** Backlog | **ClickUp:** [ACE-2236](https://app.clickup.com/t/86d318wjb) | **Product:** Omni
**Stories:** BC-01..BC-06 (ACE-2294, 2295, 2457, 2297, 2503, 2504)

> This doc explains the Broadcast epic in plain language **and** maps it onto the real `ace` repo (NestJS microservices + the Next.js `workspace-admin` frontend), so it's clear what already exists to reuse vs. what is net-new. Broadcast is **not yet in the code** (greenfield) — everything here builds on existing infrastructure.

---

## Overview

Today, sending a one-to-many message to customers over LINE (promos/announcements) forces businesses out to the separate **LINE OA Manager**, away from the unified inbox the team already uses.

This epic builds **Broadcast** natively inside Omnichat: pick a LINE OA → target an audience with tags → compose text/image messages → send now or schedule → the system sends in batches and tracks status in real time, with full history.

**Simple analogy:**
It's a **mail merge**. Write one letter, choose who gets it (by customer tag), and the built-in post office splits it into stacks and sends them out. Anything undeliverable is logged with a reason, and you can see the delivery status of every letter from one place.

**Phase 1 = LINE only** (Facebook/IG/others are later phases).

---

## 1. Core Concepts

### 1.1 Status Lifecycle
A broadcast moves through these statuses (status drives which buttons the List/Detail pages show):

| Status | Meaning | Available actions |
|---|---|---|
| **Draft** | Saved, not sent | Continue Edit, Delete |
| **Scheduled** | Will send at a future time | Edit, Cancel Schedule (→ Draft), Delete |
| **Sending** | Batches in flight | None (read-only) |
| **Sent** | All sent, no failures | Delete |
| **Sent with error** | Partially delivered | Delete |
| **Error** | Nothing delivered / quota failed | Delete |

### 1.2 Targeting
Two modes: **"Send to everyone"** (all contacts on that LINE OA) or **"Send to specific people"** (selected by tags). The system then computes **estimated reach** = count of unique (deduped) contacts that have a valid LINE user id for the chosen LINE OA.

> ⚠️ **Key gap to resolve:** the current code only has **conversation-level tags** (`Tag` + `ConversationTag`) — there are **no person-level tags** as BC-02 describes, and no API to count contacts by tag. See [Open Questions](#8-open-questions-resolve-before-building).

### 1.3 Batch Send
Not sent all at once — split into **batches of 500**, up to **3 batches in parallel**. Every recipient gets an idempotency key to prevent duplicate sends. Failed batches retry 3× with backoff (2s → 4s); rate-limited recipients (429) retry per-recipient, and each failure reason is recorded (e.g. `user_blocked`, `rate_limited`).

### 1.4 Plan-based Quota
Before the real send, quota is checked by plan: **Free/Basic = blocked** if insufficient, **Pro = allowed (overage)**. If it fails, the broadcast becomes **Error** with reason `quota_exceeded`.

> ⚠️ **Key gap:** the plan/quota system (Free/Basic/Pro) **does not exist anywhere in the code** — it must be built from scratch.

### 1.5 Roles
Three roles: **admin / supervisor / agent**. Admin/Supervisor manage broadcasts fully; **agent is read-only** (create/edit/delete buttons disabled).

---

## 2. UI Components

### Broadcast List page (BC-05)
A table of all broadcasts + **6 tabs** (All / Scheduled / Sent / Error / Sent with error / Draft) + name search + filter (updated-date range + LINE OA) + sortable columns + pagination (10/page) + 3-dot action menu (actions by status). Click a row to open Detail.

### Broadcast Detail page (BC-06)
Title + status badge + info (LINE OA, target, recipient count) + a "Messages" section showing message bubbles **read-only** + status-conditional actions. When status is **Sending**, the badge updates automatically on completion **without a refresh**. The back (←) button restores the List's prior filter/tab.

### Create/Edit page (BC-01)
Single-page form: pick LINE OA → schedule (now/future) → choose targeting → name (≤20 chars) → message composer (text/image bubbles, max 5, drag to reorder) + a **real-time LINE-style preview** on the right + Save Draft / Send Test / Send.

### Audience Picker (BC-02)
Searchable tag dropdown + selected tags shown as chips + real-time reach recalculated on every add/remove.

### Test Broadcast Dialog (BC-04)
Pick yourself/teammates who have a LINE connection (max 5) and send a test — **does not count quota, not saved to history**.

---

## 3. User Flow

#### Scenario: an Admin sends a New Year promo to VIP customers

1. **Create (BC-01):** Open Create → pick LINE OA "Shop A" → choose "Schedule" Jan 1, 09:00 → name it "New Year Sale 2026".
2. **Target (BC-02):** Choose "specific people" → select tags `VIP` + `New Customer` → system shows "≈ 280 recipients (70%)" (deduped).
3. **Compose (BC-01):** Add a text bubble + an image bubble → preview on the right shows how it'll look in LINE.
4. **Test (BC-04):** Send Test → pick yourself → verify in your own LINE (no quota cost).
5. **Send (BC-03):** Click Send → confirm in dialog → redirect to List; the broadcast shows **"Sending"** immediately.
6. **Background (BC-03):** Check quota → split the 280 into batches → push via LINE → record each recipient's result/reason.
7. **Track (BC-03/06):** On completion the status flips to **"Sent"** automatically + a **toast appears only for the sender** ("Broadcast id: ... send successfully"), wherever they are in the app.
8. **Detail (BC-06):** The admin opens Detail to see the sent messages, timestamp, and recipient count.

---

## 4. How it sits on the real codebase (`ace`)

Broadcast follows ACE's **3-tier vertical-feature convention** (use `tags` as the clean template, `contact-notes` as the audit template):

```
workspace-admin (Next.js)  →  api-gateway (proxy + auth/permission)  →  omnichat-service (logic + Prisma + LINE)
        UI / pages                pulls tenantId/userId from JWT          models + real LINE send + batching
```

- **omnichat-service** owns all logic: new Prisma models + a `BroadcastModule` (service + HTTP/TCP controller + migration).
- **api-gateway** is a thin proxy: pulls `@CurrentUser` from JWT, applies `@RequirePermission`, forwards on (exactly like `tags.controller.ts`).
- **workspace-admin** adds routes `(main)/dashboard/broadcast/{page.tsx, create/page.tsx, [id]/page.tsx}` + `_api/broadcast.api.ts` (server actions calling `httpClient` → `/v1/omnichat/broadcast*`).

### What already exists — reuse ✅

| Concern | Real code | Use in Broadcast |
|---|---|---|
| Send to LINE | `LineStrategy.pushMessage()` → `LineExternalService.pushTextMessage(token, to, content, retryKey)` (`@line/bot-sdk`) | core of every send (BC-03/04) |
| LINE OA credential | `CredentialsService.getCredential()` decrypts the token on use | fetch the OA access token (pre-fetch once per OA) |
| Idempotency / retry | `Message.retry_key` (unique) + `retryPushMessage()` | safe per-recipient retries |
| Backoff (incl. 429) | `BackoffService` (exp backoff + Retry-After) in marketplace-polling | per-batch / per-recipient retry timing (BC-03 AC9/10) |
| Parallel processing | `PollingOrchestratorService` chunk + `Promise.allSettled`; worker uses `pLimit` | template for "500/batch × 3 parallel" |
| Queue / worker | SQS FIFO (`omnichat-gateway` `QueueService`) + consumer (`omnichat-normalizer-worker`) | (optional) run batches in background |
| Audience data | `Conversation`(channel_account_id, contact_id) + `ConversationTag` + `Contact.external_user_id` | join to resolve audience + dedupe by LINE user id |
| LINE OA entity | `ChannelAccount` (channel_type=`line`) | the "LINE OA" being sent from |
| Per-message status/reason | `Message.status / delivery_status / delivery_message / delivery_metadata` | per-message result (when a conversation exists) |
| Realtime | `chat.gateway.ts` → Redis `notifications:events` → `user:{id}` room → Socket.IO; FE `SocketManager`/`useSocket` + ws-token | sender-only toast + live Sending status |
| Toast | `Sonner` mounted at root | sender-only toast (BC-03 AC8) |
| Permissions | `@RequirePermission` + `PermissionGuard` + matrix; FE `getMyPermissionsAction()` | agent read-only (BC-05/06) |
| UI kit | DataTable (TanStack v8) + `useDataTableInstance`, Tabs, Dialog/AlertDialog, DropdownMenu, Badge, RadioGroup, Select | List/Detail/Form/Confirm |
| Multi-select chips | `RecipientMultiSelect` (notification-rules) | tag picker (BC-02) |
| Forms | react-hook-form + Zod (e.g. `edit-user-modal`) | BC-01 form |
| list+detail+form template | the `documents` feature (`page.tsx` / `[id]/page.tsx` / `create/page.tsx`) | broadcast page scaffolding |
| Server actions | `listChannelAccounts(channelType='line')`, `listMembers()` | LINE OA dropdown + team list for test |

### What is net-new — build 🔨

- **New models:** `Broadcast` (name, status, message_json bubbles, schedule, channel_account_id, target_tag_ids, estimated_reach, tenant_id, created_by, soft delete), `BroadcastRecipient` (per-recipient: contact_id, external_user_id, status, failure_reason, retry_count), `BroadcastAudit` (modeled on `ContactNoteAudit`).
- **BroadcastOrchestratorService:** chunk into 500, run 3 parallel, retry per batch, pre-fetch token once.
- **LINE error parser:** map HTTP status/body → reason (`user_blocked` 403 / `rate_limited` 429 / `invalid_user` 400) — today only `error.message` is logged.
- **The entire plan/quota subsystem:** `Tenant.plan` enum + `BroadcastUsage` (or Redis counter) + a `canSend()` guard — **nothing exists today**.
- **Person-level tags** (if BC-02 is confirmed) + a **reach-estimation endpoint** (distinct contact_id).
- **A WorkspaceMember ↔ LINE Contact join** for BC-04 (today User/WorkspaceMember has no line_user_id at all).
- **New permission actions:** `view_broadcast / create_broadcast / send_broadcast / edit_broadcast / delete_broadcast` + matrix seeds (agent = view only).
- **A new realtime event** for broadcast status (must be added to the **user-scoped** `NotificationEvent` only, per the security comment in the gateway file — never `OmnichatEvent`, which is tenant-wide).
- **All the frontend:** routes + form + bubble editor (drag reorder) + LINE preview + list (tabs/filters) + detail (status-conditional actions) + a `broadcastStore` (Zustand) + socket listeners.

---

## 5. Scope Summary

| Category | Details |
|---|---|
| Phase 1 channel | LINE OA only |
| Stories | 6 (BC-01 create/edit, BC-02 targeting, BC-03 send, BC-04 test, BC-05 list, BC-06 detail) |
| Batching | 500/batch, max 3 parallel, 3× retry with backoff |
| Messages | text + image, max 5 bubbles/broadcast |
| Quota | Free/Basic blocked, Pro overage (overage = tracked-only in Phase 1) |
| Permissions | admin/supervisor manage, agent read-only |
| Out of scope | quick reply, personalization vars, template library, analytics, other channels, recurring, Narrowcast API, video/carousel |

---

## 6. Story Breakdown

### BC-01 — Create and Edit Broadcast (ACE-2294)
**Goal:** single-page create/edit with a live LINE preview and draft save.
**Reuse:** 3-tier convention, `listChannelAccounts`, react-hook-form+Zod, Dialog/Select, soft-delete + tenant scoping.
**Net-new:** `Broadcast` model+migration, CRUD service, the `message_json` shape, the **bubble editor + drag reorder**, the **LINE preview renderer**, ≤20-char name validation, draft semantics.

### BC-02 — Audience Selection and Targeting (ACE-2295)
**Goal:** everyone vs specific-people via tags + real-time deduped reach.
**Reuse:** the `ConversationTag → Conversation → Contact` distinct-contact join, `TagsService.listTags`, `RecipientMultiSelect` chips, `Contact.external_user_id` as the dedupe/validity key.
**Net-new:** the **reach-estimation endpoint**; **person-level tags don't exist** (only conversation-level today — design must be resolved); "send to everyone" = all contacts on the OA with a conversation + valid external_user_id.

### BC-03 — Send Broadcast (ACE-2457)
**Goal:** confirm → quota check → batch send + retry → completion summary + sender-only toast + live status.
**Reuse:** `pushMessage` + `retry_key`, `BackoffService`, the chunk/`Promise.allSettled` pattern, Redis → `user:{id}` room (sender-only), Sonner, AlertDialog.
**Net-new:** the **batch orchestrator (chunk/parallel/retry)**, the **LINE error parser**, the `BroadcastRecipient` model, the **entire quota subsystem**, a broadcast status event, and handling recipients without a `Conversation` (because `Message.conversation_id` is NOT NULL).

### BC-04 — Test Broadcast (ACE-2297)
**Goal:** test-send to self/team (≤5), no quota, no history.
**Reuse:** `GET /api/members` (`listMembers`), Dialog + multi-select, `pushMessage`, Sonner.
**Net-new:** the **WorkspaceMember ↔ LINE Contact match** (no link exists today), a max-5 cap, a quota-bypassing + no-history test path.

### BC-05 — Broadcast List (ACE-2503)
**Goal:** table + status tabs + search/filter + sort + paginate + 3-dot menu + agent read-only.
**Reuse:** DataTable + `useDataTableInstance`, Tabs, `DataTablePagination`, the DropdownMenu action column (`documents` template), Badge, `listChannelAccounts`, permission gating.
**Net-new:** the list endpoint + filters (tab→status, date range, OA), status-specific action items, query indexes, the `view_broadcast` permission.

### BC-06 — Broadcast Detail (ACE-2504)
**Goal:** status-specific detail, read-only bubbles, status-conditional actions, live Sending status, back preserves filter/tab, agent read-only.
**Reuse:** the `[id]/page.tsx` pattern, AlertDialog, socket/`useSocket`+Sonner, permission gating, soft-delete+audit tx.
**Net-new:** the detail endpoint, the status-conditional action set, the `BroadcastAudit` model, live Sending updates (reuses BC-03's event), filter/tab preservation on Back.

---

## 7. Risk / Blast radius

- **High-volume LINE pushes** hit the real LINE OA rate limits — the orchestrator + backoff must be tested before launch.
- **Quota miscalculation** could over-bill customers on overage — lock the calculation against the AC7 race condition.
- Several new models/migrations on a multi-tenant schema — every query must scope `tenant_id` (per the existing convention).
- Realtime: do **not** put the broadcast event on `OmnichatEvent` (tenant room) or it leaks across users — it must ride `NotificationEvent` (user room) per the gateway file's comment.

---

## 8. Open Questions (resolve before building)

All of these come from reading the real code — they're the gap between "what the stories say" and "what the system has today":

1. **Person-level tags (BC-02):** only conversation-level tags exist. Does "person-level" mean (a) tags rolled up from all of a contact's conversations, (b) tags on a `ContactGroup`, or (c) a genuinely new contact-tag model? This changes both schema and the reach query.
2. **Recipients without a Conversation:** `Message.conversation_id` is NOT NULL (required FK). For "send to everyone" or anyone with a LINE id but no existing conversation on this OA, can we push at all (LINE push only needs the user id)? If so, create a Conversation, skip Message persistence and rely on `BroadcastRecipient`, or exclude them from reach?
3. **Plan/Quota:** plan tiers and quota tracking **don't exist** — where should plan live (`Tenant.plan`?), where is usage counted (a table vs Redis), what's the billing-period boundary, and is "Pro overage" tracked-only or enforced?
4. **Realtime event:** reuse the existing `notification:new` carrying a broadcast payload, or add a new `broadcast:status` to `NotificationEvent` (never to `OmnichatEvent`)? Confirm the event name + payload shape.
5. **BC-04 member↔LINE match:** there's no link between WorkspaceMember and a LINE Contact — match by email, a manual mapping, or is "self/team test" actually sending to the member's own LINE follower identity? The mechanism is undefined.
6. **Permission grants:** confirm the 5 actions and each role's grants (does supervisor get full rights; do read endpoints need a guard?).
7. **Message bubble shape + images:** confirm the `message_json` schema and how images are pushed — today `LineExternalService` only exposes `pushTextMessage` (image/multi-message push is net-new).
8. **Scheduled send:** there's no broadcast scheduler today (only `SlaCronService`) — will future-scheduled broadcasts run via a new cron/ScheduleModule job polling for due rows?
9. **Image upload (BC-01):** is S3/asset upload available (`Attachment.file_url` implies S3), or do image bubbles reference external URLs only? The compose-time upload path is unconfirmed.
