# EPIC ACE-2211: Rule Automation — Simplified Explanation

## Overview

This Epic involves building a "Rule Automation" system that allows Admins and Supervisors to configure automated responses when specific conditions are met — for example, a customer typing "cancel" → system sends an auto-reply and tags the conversation as "cancellation-risk" instantly, without waiting for an agent.

The primary goal is to **reduce manual work for the support team**, create consistent customer experiences, and let agents focus on decisions that genuinely require human judgment.

**Simple Analogy:**
Think of it like setting up an email auto-responder, but smarter — you choose exactly when it triggers (keywords, channel, business hours) and what it does (reply, tag) without needing a developer to configure it.

---

## 1. Core Concepts

### 1.1 What is a Rule?

Each rule has two parts: **Conditions** (what must be true) and an **Action** (what the system does).

```
If [conditions match] → execute [action]
```

**Example Rules:**
- If keyword contains "cancel" AND channel = Shopee → send auto-reply "We've received your request" + tag "cancellation-risk"
- If business hours = outside AND channel = LINE → send auto-reply "We're currently outside business hours"

### 1.2 Trigger Conditions

| Type | Options | Notes |
|------|---------|-------|
| Keyword match | contains / exact | Case-insensitive Thai & English |
| Channel | LINE, Facebook, Instagram, Shopee, Lazada, TikTok | Multi-select |
| Business hours | within / outside | Includes day of week + timezone; toggle for Workspace hours |

Multiple conditions are joined by **AND** (all must match) or **OR** (any one must match).

### 1.3 Actions

| Action | Key Config | Behavior |
|--------|-----------|----------|
| Auto-reply | Message + template variables + cooldown | Sent via the same channel the customer used |
| Add tag | Multi-select + create inline | Append-only — never removes existing tags (soft-delete model) |

> **⚠️ Channel reality (verified against repo):** Auto-reply can only be **sent** on channels with an outbound integration today: **LINE, Facebook, Instagram, Lazada**. **TikTok** outbound is not yet implemented (`tiktok.strategy.ts` returns *"not yet supported"*) and **Shopee** has no send strategy at all (only a stub poller). On those two channels a rule will still **add tags** but **skips the auto-reply** (logged). The auto-tag action works on any channel.

### 1.4 Rule Execution Logic

When a message arrives, the system always follows these steps:

1. **Sender check:** Is `sender_type` a customer message (`'contact'`)? → Only `'contact'` is evaluated; `'agent'` and `'system'` messages are skipped (background)
2. **Dedup check:** Is this message a duplicate within 5 seconds? → If yes, skip (background) — *new guard to be built; the existing 24-hour dedup lives at the webhook gateway, not here*
3. **Evaluate:** Check all active rule conditions simultaneously (single-pass)
4. **Execute:** All matching rules execute in `created_at` order (oldest first):
   - **Add tag:** Every matching rule can tag (append-only)
   - **Auto-reply:** Sent only once from the oldest matching rule (only-first-wins) — other rules skip auto-reply, but their other actions still run

> **Key principle:** Single-pass means a tag added by Rule A cannot trigger Rule B within the same evaluation round.

### 1.5 Background Safety (Automatic — Not Exposed in UI)

| Mechanism | How It Works | What It Prevents |
|-----------|-------------|-----------------|
| `sender_type = 'rule'` | Message record identifies the rule as sender, not an agent. **Note:** `sender_type` is a plain string field (`contact \| agent \| system` today); `'rule'` is a new app-level value — not a DB enum. AI replies currently use `'agent'`. | Incorrect agent KPI |
| SLA state machine excludes rule replies | There is **no** `first_human_response_at` field — FRT is derived from `sla_first_inbound_at` + the SLA state machine + `ConversationSlaEvent.response_time_sec`. A `sender_type='rule'` message must not advance the "first agent response" state. | Inflated SLA / FRT metrics |
| Non-customer sender skip | Evaluates only `sender_type = 'contact'`; skips `agent`/`system` | Echoes & system messages triggering rules incorrectly |
| Message dedup 5s | Evaluates once per unique message (new guard) | Duplicate auto-replies from re-sent messages |

---

## 2. UI Components

### Rule List Page (Settings > Automation > Rules)

- **Active section:** Enabled rules with counter X/20 (max 20 active rules per workspace)
- **Inactive section:** Collapsed by default — click to expand
- **Each rule card:** Rule name, trigger summary, action summary, toggle, fired count, created_by/updated_by + relative time, kebab menu (⋮)
- **Pills filter:** All / Auto-reply / Add tag
- **+ New Rule:** Opens a modal asking "What would you like the system to do?" (action-first)

### Action-First Modal

Starts by selecting an Action — not a blank form — to reduce decision fatigue.

```
"What would you like the system to do?"
┌─────────────────────────┐  ┌──────────────────────────┐
│  Send auto-reply message │  │  Add label to conversation│
└─────────────────────────┘  └──────────────────────────┘
```

### Rule Wizard (2 Steps)

- **Step 1 — Trigger Conditions:** Add condition cards + choose AND/OR + test panel for real-time testing
- **Step 2 — Action Detail:** Depends on the chosen action (Auto-reply or Add tag)
- Step indicator at the top — completed steps are clickable to go back
- Rule name auto-generated from action + trigger (e.g. `'Auto-reply · Outside hours'`) — editable before saving

### Step 2A: Auto-reply Configuration

- Multi-line text editor with character count
- Variable toolbar: `{{customer_name}}` `{{channel}}` `{{current_time}}` — click to insert at cursor
- Fallback value per variable (when the variable cannot resolve)
- Preview panel: live resolved message using dummy data
- Cooldown field (required, must be > 0): "Send at most 1 time per [5] [minutes] per conversation"

### Step 2B: Add Tag Configuration

- Tag picker: search + multi-select + create inline (type → Enter → creates and selects immediately)
- Preview chip list: "Will add these labels: [chip list]"

---

## 3. User Flow

#### Scenario: Customer types "cancel" on LINE outside business hours

Two rules are configured:
- Rule A: keyword contains "cancel" AND channel = LINE → auto-reply "Noted!" + tag "cancellation-risk"
- Rule B: business hours = outside → auto-reply "Outside business hours" + tag "off-hours"

1. **Customer sends "cancel my order" via LINE at 10:00 PM:**
   - Sender check passes (`sender_type = 'contact'`)
   - Dedup check passes (new message)
   - Evaluate: Rule A matches (keyword + LINE ✓), Rule B matches (outside hours ✓)
   - Execute (sorted by created_at):
     - Rule A: auto-reply "Noted!" → **Sent ✓** / tag "cancellation-risk" → **Applied ✓**
     - Rule B: auto-reply "Outside business hours" → **Skipped ✗** (Rule A already sent — only-first-wins) / tag "off-hours" → **Applied ✓**

2. **Customer receives 1 message** ("Noted!"), not 2

3. **Conversation has 2 tags:** "cancellation-risk" + "off-hours"

4. **FRT continues counting** — the `sender_type = 'rule'` message does not advance the SLA "first agent response" state

> *On a channel without send support (TikTok/Shopee), Rule A's auto-reply would be **skipped**, but both tags would still be applied.*

#### Scenario: Admin deletes a rule

1. Clicks the kebab menu (⋮) on the rule
2. Confirmation dialog appears: rule name + "This rule has run 87 times" + "Will be permanently deleted"
3. Admin clicks "Delete permanently" → rule is removed from DB, no undo

---

## Scope Summary

| Category | Details |
|---|---|
| Stories in this Epic | 4 Stories (RA-01 through RA-04) |
| Trigger types | 3: Keyword, Channel, Business hours |
| Actions | 2: Auto-reply, Add tag |
| Active rule limit | Max 20 active rules per workspace (`tenant_id` in DB) |
| Rule execution | Single-pass evaluate, oldest-first execute |
| Auto-reply dedup | Only-first-wins + cooldown per-conversation-per-rule (Redis) |
| Auto-reply channels | LINE / Facebook / Instagram / Lazada only — TikTok & Shopee send not yet supported |
| SLA attribution | `sender_type = 'rule'` must not advance the SLA first-agent-response state |
| Tag integrity | Append-only (soft-delete), new `tagged_by_type`/`tagged_by_rule_id` columns, graceful skip if tag deleted |

> **Implementation grounding:** Every technical claim in this Epic was verified against the `ace` repo (branch `dev`). Key realities: `sender_type` and `status` are plain string fields, not DB enums; the new automation-rules engine hooks into `omnichat-service` `messages.service.ts` (post-save); business-hours logic is reused from `packages/shared` with config stored per-tenant in `tenant-service`; outbound sending reuses the per-channel `StrategyRegistry`. See `story-task-breakdown.md` for file-level detail.

---

## 4. Story Breakdown

### STORY-RA-01: Rule Management (CRUD)

**Goal:** Build the UI and API for creating, editing, deleting, and enabling/disabling Automation Rules according to each role's permissions.

**Key Features:**
- **Rule list page:** Active/Inactive sections, rule cards, counter, pills filter
- **Action-first wizard:** Select action first → 2-step wizard → auto-generated rule name → save
- **CRUD operations:** Create, edit (pre-filled wizard), enable/disable toggle, hard delete with confirmation dialog
- **Permission enforcement:** Admin = full CRUD, Supervisor = create/edit only, Agent = read-only — enforced in both UI and API
- **Active rule limit:** Blocks creation when active rules reach 20

**Why it matters:** This story is the complete shell — without it, RA-02/03/04 have no structure to attach to.

---

### STORY-RA-02: Define Trigger Conditions

**Goal:** Let admins define trigger conditions across 3 types with AND/OR logic and a real-time test panel to validate before activating.

**Key Features:**
- **Evaluators:** Keyword (contains/exact, case-insensitive Thai/EN), Channel, Business hours (Workspace toggle + custom)
- **AND/OR logic:** Single-pass evaluation with the selected logic combinator
- **Background guards:** Non-customer sender skip (`sender_type ≠ 'contact'`), 5-second message deduplication window (new guard)
- **Wizard Step 1 UI:** Condition cards + AND/OR toggle + real-time test panel with highlight

**Why it matters:** Incorrect evaluation means rules fire at the wrong time — the test panel reduces misconfiguration before it reaches production.

---

### STORY-RA-03: Send Auto-reply Message

**Goal:** When a rule matches, send an automated reply via the same channel the customer used, with template variables and mandatory cooldown.

**Key Features:**
- **Auto-reply executor:** Sends via same channel, only-first-wins, skips if conversation is completed
- **Variable resolver:** Resolves `{{customer_name}}`, `{{channel}}`, `{{current_time}}` with fallback values
- **Cooldown:** Required field, per-conversation-per-rule, default 5 minutes
- **Background:** Sets `sender_type = 'rule'`, does not advance the SLA first-agent-response state, retries 3 times with exponential backoff; skips channels without send support (TikTok/Shopee)
- **Wizard Step 2 (Auto-reply) UI:** Text editor + variable toolbar + fallback inputs + live preview + cooldown field

**Why it matters:** If `sender_type` is wrong or cooldown doesn't work, FRT metrics break and customers receive duplicate messages.

---

### STORY-RA-04: Auto-Tag Conversation

**Goal:** Let rules automatically tag conversations as append-only, with metadata to distinguish automated from manual tagging in KPI reports.

**Key Features:**
- **Auto-tag executor:** Append-only (never removes existing tags), deduplication, graceful skip + log if tag is deleted from system
- **Metadata:** `tagged_by_type = 'rule'` for KPI report filtering (separates automated vs manual tagging)
- **Wizard Step 2 (Add tag) UI:** Searchable tag picker + multi-select + inline create + preview chip list
- **Tooltip:** Tags applied by rules show "tagged by rule: [rule name]" on hover

**Why it matters:** Incorrectly attributed tags (rule vs human) make KPI reports unreliable for measuring agent performance.
