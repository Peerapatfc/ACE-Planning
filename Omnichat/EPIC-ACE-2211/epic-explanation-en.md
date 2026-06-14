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
| Add tag | Multi-select + create inline | Append-only — never removes existing tags |

### 1.4 Rule Execution Logic

When a message arrives, the system always follows these steps:

1. **Bot check:** Did this message come from a bot/system? → If yes, skip everything (background)
2. **Dedup check:** Is this message a duplicate within 5 seconds? → If yes, skip (background)
3. **Evaluate:** Check all active rule conditions simultaneously (single-pass)
4. **Execute:** All matching rules execute in `created_at` order (oldest first):
   - **Add tag:** Every matching rule can tag (append-only)
   - **Auto-reply:** Sent only once from the oldest matching rule (only-first-wins) — other rules skip auto-reply, but their other actions still run

> **Key principle:** Single-pass means a tag added by Rule A cannot trigger Rule B within the same evaluation round.

### 1.5 Background Safety (Automatic — Not Exposed in UI)

| Mechanism | How It Works | What It Prevents |
|-----------|-------------|-----------------|
| `sender_type = 'rule'` | Message record identifies the rule as sender, not an agent | Incorrect agent KPI |
| Separate `first_human_response_at` | SLA does not count auto-replies as FRT | Inflated SLA metrics |
| Bot sender skip | Checks sender_type before evaluating | Platform notifications triggering rules incorrectly |
| Message dedup 5s | Evaluates once per unique message | Duplicate auto-replies from re-sent messages |

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

#### Scenario: Customer types "cancel" on Shopee outside business hours

Two rules are configured:
- Rule A: keyword contains "cancel" AND channel = Shopee → auto-reply "Noted!" + tag "cancellation-risk"
- Rule B: business hours = outside → auto-reply "Outside business hours" + tag "off-hours"

1. **Customer sends "cancel my order" via Shopee at 10:00 PM:**
   - Bot check passes (customer sent it)
   - Dedup check passes (new message)
   - Evaluate: Rule A matches (keyword + Shopee ✓), Rule B matches (outside hours ✓)
   - Execute (sorted by created_at):
     - Rule A: auto-reply "Noted!" → **Sent ✓** / tag "cancellation-risk" → **Applied ✓**
     - Rule B: auto-reply "Outside business hours" → **Skipped ✗** (Rule A already sent — only-first-wins) / tag "off-hours" → **Applied ✓**

2. **Customer receives 1 message** ("Noted!"), not 2

3. **Conversation has 2 tags:** "cancellation-risk" + "off-hours"

4. **FRT continues counting** — `sender_type = 'rule'` does not affect `first_human_response_at`

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
| Active rule limit | Max 20 active rules per workspace |
| Rule execution | Single-pass evaluate, oldest-first execute |
| Auto-reply dedup | Only-first-wins + cooldown per-conversation-per-rule |
| SLA attribution | `sender_type = 'rule'` does not count as FRT |
| Tag integrity | Append-only, tagged_by_type = rule, graceful skip if tag deleted |

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
- **Background guards:** Bot sender skip, 5-second message deduplication window
- **Wizard Step 1 UI:** Condition cards + AND/OR toggle + real-time test panel with highlight

**Why it matters:** Incorrect evaluation means rules fire at the wrong time — the test panel reduces misconfiguration before it reaches production.

---

### STORY-RA-03: Send Auto-reply Message

**Goal:** When a rule matches, send an automated reply via the same channel the customer used, with template variables and mandatory cooldown.

**Key Features:**
- **Auto-reply executor:** Sends via same channel, only-first-wins, skips if conversation is completed
- **Variable resolver:** Resolves `{{customer_name}}`, `{{channel}}`, `{{current_time}}` with fallback values
- **Cooldown:** Required field, per-conversation-per-rule, default 5 minutes
- **Background:** Sets `sender_type = 'rule'`, does not update `first_human_response_at`, retries 3 times with exponential backoff
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
