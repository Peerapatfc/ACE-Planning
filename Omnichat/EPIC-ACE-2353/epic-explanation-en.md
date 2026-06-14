# EPIC ACE-2353: Analytics Dashboard — Simplified Explanation

## Overview

This Epic involves building an "Analytics Dashboard" that consolidates all team support performance data into a single screen, giving Admins and Supervisors instant visibility — both real-time (Live) and historical (Analytics).

The primary goal is to **let supervisors make faster decisions without asking the team** — see immediately which channel has a backlog, which agent is slow, and whether rule automation is actually reducing workload.

**Simple Analogy:**
Think of an airline control room — not the cockpit, but the operations center where supervisors see every flight on one screen, know which ones are delayed, which gates are congested, and can re-route traffic in real time.

---

## 1. Core Concepts

### 1.1 Dashboard with 5 Tabs, Each Answering a Different Question

The dashboard is not a single screen stuffed with everything — it's split into 5 tabs, each answering a distinct question:

| Tab | Question It Answers | Data Type |
|-----|---------------------|-----------|
| **Live** | "What does the queue look like right now? Who's been waiting?" | Near real-time, polling every 30s |
| **Analytics** | "Did FRT improve this week? When is peak hour?" | Historical, refreshes on period change |
| **Agents** | "Who resolved the most? Whose FRT is too slow and needs coaching?" | Historical, period filter |
| **Channels** | "Is Shopee's queue worse than LINE's? How old is the backlog?" | Historical + current backlog |
| **Automation** | "Are the rules I set up actually worth it? How much did FRT drop?" | Historical, period filter |

### 1.2 Two Measurement Modes: Live vs Historical

**Live (Tab 1):** Measures current state — "There are 84 open conversations right now, 14 with no agent assigned."

**Historical (Tabs 2-5):** Measures past performance — "Over the past 7 days, average FRT was 2.4 minutes."

> The two modes answer different needs: Live = decide now / Historical = trend analysis

### 1.3 Period Filter (3 Options)

All Historical tabs have a period filter in the top-right corner:
- **Today** — view today only
- **7 days** — view the last 7 days
- **30 days** — view the last 30 days

Changing the period → **all metrics in that tab update simultaneously.** No partial updates.

### 1.4 Attribution Rules (Who Gets Credit for What)

Because conversations can be reassigned, the system needs clear rules about which agent "owns" each metric:

| Metric | Attributed To | Reason |
|--------|--------------|--------|
| **Resolution** | Last assignee (who closed it) | The person who closed it is accountable for the outcome |
| **FRT** | First responder (who replied first) | Locked immediately on first reply — never changes on reassign |
| **AHT per agent** | Split by actual time held | Uses assignment_history — if A held 30m and B held 15m, A gets 30m and B gets 15m |
| **Total / Volume** | No attribution | Always COUNT DISTINCT — reassignment never causes double-counting |

**Iron rule:** FRT must never count auto-replies — the system uses `first_human_response_at` separately from `first_response_at`.

### 1.5 Permission Model

The dashboard has 3 permission levels:

| Action | Admin | Supervisor | Agent |
|--------|:-----:|:----------:|:-----:|
| Live tab | ✓ | ✓ | ✗ |
| Analytics tab | ✓ | ✓ | ✗ |
| Agents tab | ✓ | ✓ | Own row only |
| Channels tab | ✓ | ✓ | ✗ |
| Automation tab | ✓ | ✓ | ✗ |
| Period filter | Today / 7d / 30d | Today / 7d / 30d | Today only |

> Both UI hides the content AND the API returns 403 — an agent attempting to query another agent's data always gets a 403.

---

## 2. UI Components

### 2.1 Live Tab

```
┌─────────────────────────────────────────────────────┐
│  🟢 LIVE  (blinking)                                │
│                                                     │
│  [Active: 70]   [Waiting: 14]   [Agents: 8]         │
│   clickable→    clickable→      not clickable        │
│                                                     │
│  Volume Today (area chart — incoming vs resolved)   │
│                                                     │
│  Queue Now per channel:                             │
│  LINE: 2  Facebook: 1  Shopee: 🟠 7 (wait 4:35)    │
│                                                     │
│  Agent Workload:                                    │
│  [Nat 🟢 queue:3 done:12] [Pong 🟠 queue:5 done:8]  │
└─────────────────────────────────────────────────────┘
```

**Drill-in Drawer:** Clicking Active or Waiting slides a drawer in from the right, showing a list of real conversations with "Open conversation" and "Assign" buttons per row.

**LIVE Badge:** Blinks green while polling is healthy → turns 🟠 "connection lost" if the network drops.

### 2.2 Analytics Tab

```
┌────────────────────────────────────────────────────────────────┐
│  [Total: 4,870]  [FRT: 2.4m]  [AHT: 8.2m]  [Res: 94%]  [30d ▾] │
│                                                                  │
│  [FRT bar: bot vs human]  [SLA Distribution]  [Weekly Trend]    │
│                                                                  │
│  [Peak Hours Heatmap — 7 days × 12 time slots]                   │
│                                                                  │
│  [Channel Breakdown]             [Top Auto-tags]                 │
└────────────────────────────────────────────────────────────────┘
```

### 2.3 Agents Tab

```
┌──────────────────────────────────────────────────────────┐
│  [Working: 8]  [Resolved: 142]  [FRT: 2.1m]  [AHT: 7.8m] │
│                                                          │
│  Sort: [Resolved ●] [FRT] [AHT]                          │
│                                                          │
│  Avatar  Name    Resolved  FRT      AHT     Status       │
│  🟢 Nat   120     1:24🟢   7:10🟢   🟢 online            │
│  🟠 Pong   87     3:15🔴   9:30🟠   🟠 busy              │
└──────────────────────────────────────────────────────────┘
```

### 2.4 Channels Tab

```
┌──────────────────────────────────────────────────────────┐
│  Channel    Volume      FRT      Resolution  Switch%     │
│  LINE       ████ 2,340  1:52🟢   96%🟢        5%🟢       │
│  Shopee     ██ 1,100    4:20🔴   88%🟠       18%🔴       │
│  Facebook   █ 890       2:10🟢   93%🟢        8%🟢       │
│                                                          │
│  Backlog Age:                                            │
│  [< 1h: 23]  [1-4h: 8]  [4-24h: 3]  [> 1 day: 5]      │
│  ⚠️ 5 conversations stuck over 1 day — escalation needed  │
└──────────────────────────────────────────────────────────┘
```

### 2.5 Automation Tab

```
┌──────────────────────────────────────────────────────────────┐
│  [Rules: 5/20]  [Auto-replied: 1,827]  [Auto-tagged: 1,419]  [FRT↓: 87%] │
│                                                                            │
│  Rule Performance:                                                         │
│  Auto-reply · Outside hours   Fired: 1,284  Handled: 1,201  ████ 94%🔵   │
│  Tag · Cancellation           Fired: 543    Handled: 540    ████ 99%🟢   │
│  Auto-reply · Welcome         Fired: 312    Handled: 272    ███░ 87%🟠   │
│                                                                            │
│  [Reply Attribution: 63% human / 37% rule]  [Tag: 71% auto / 29% manual] │
└──────────────────────────────────────────────────────────────┘
```

### 2.6 Cross-cutting UX

**Tooltip System:** Every technical KPI (FRT, AHT, Switch%) has an ⓘ icon — hover shows full name + explanation + threshold note.

**Loading Skeleton:** When changing the period — never shows stale data during the new fetch; shows a skeleton placeholder instead.

---

## 3. User Flows

### Scenario A: Supervisor spots a Shopee queue spike

Supervisor opens Live tab at 2:00 PM and sees Shopee queue showing 🟠 7 (wait 4:35).

1. **Clicks Waiting card** → drawer slides in from the right, showing 14 waiting conversations
2. **Filters to Shopee** → sees 7 items sorted by wait time
3. **Clicks Assign on the longest-waiting row** → assign modal opens → selects an available agent
4. **Drawer refreshes** on next polling cycle → that row moves to Active

### Scenario B: Manager analyzes weekly performance

1. **Opens Analytics tab**, selects period = 7 days
2. **Looks at FRT bar chart** — bot FRT 0.3m vs human FRT 2.4m
3. **Checks Peak Heatmap** — clear spike on Tuesday–Thursday 10:00–12:00
4. **Decides to** add shift coverage during peak → reduces FRT in that window

### Scenario C: Supervisor identifies who needs coaching

1. **Opens Agents tab**, sorts by FRT ascending
2. **Sees Pong's FRT = 3:15 in red** (threshold: > 3:00)
3. **Checks Pong's AHT** = 9:30, also high → likely a handling process issue
4. **Schedules a 1:1 coaching session** with Pong using dashboard data as evidence

### Scenario D: Admin proves Rule Automation ROI

1. **Opens Automation tab**, selects period = 30 days
2. **Sees FRT Reduction = 87%** → auto-reply cut response time from 2.4m to 0.3m for bot-handled conversations
3. **Reviews Rule Performance** → 'Auto-reply · Outside hours' at 94% success, working well
4. **Finds a rule with success < 90%** → clicks through to Rule Management to debug the condition

---

## Scope Summary

| Category | Details |
|---------|---------|
| Stories in this Epic | 5 Stories (ADB-01 through ADB-05) |
| Tabs | 5 tabs: Live, Analytics, Agents, Channels, Automation |
| Period filter options | Today / 7 days / 30 days (except Live tab) |
| Attribution model | Last assignee (Resolution), First responder (FRT), Time-split via assignment_history (AHT per agent) |
| FRT rule | Never counts auto-reply — always uses first_human_response_at |
| Live refresh | Polling every 30s + blinking LIVE badge |
| Permission enforcement | Both UI hide and API 403 |
| Agent role restriction | Agents tab only + own row only + period locked to Today |

---

## 4. Story Breakdown

### STORY-ADB-01: Live Operations View — See Problems Instantly

**Goal:** Give the shift supervisor instant visibility into the current state of conversations and agents — enough to make assign/reassign decisions without picking up the phone.

**Key Features:**
- **3 KPI cards:** Active (conversations with an assigned agent), Waiting (no agent yet), Agents Working (by schedule)
- **Volume Today chart:** area chart showing incoming vs resolved per hour over 24h
- **Queue Now per channel:** queue depth + longest wait time + warning when > 5
- **Agent Workload cards:** avatar, status dot, current queue, handled today
- **Drill-in drawer:** click Active/Waiting → real conversation list → assign / open conversation
- **Polling 30s + LIVE badge + connection-lost handling**

**Why it matters:** A supervisor who can't see the queue in real time reacts slowly — customers wait unnecessarily.

---

### STORY-ADB-02: Analytics View — Analyze Historical Trends

**Goal:** Give managers a complete historical view of team performance, with charts and a heatmap for workforce planning.

**Key Features:**
- **4 KPI cards:** Total Conversations, Avg FRT (Human), Avg AHT, Resolution Rate
- **FRT bar chart:** bot vs human side-by-side by day
- **SLA Distribution:** % of conversations in 4 FRT buckets (< 1m, 1-5m, 5-30m, > 30m)
- **Weekly Trend line chart:** volume + FRT across 4 weeks
- **Peak Hours Heatmap:** 7 days × 12 two-hour slots — normalized per period (not raw sum)
- **Channel Breakdown + Top Auto-tags:** understand which channels and tag types dominate

**Why it matters:** A single-day FRT average tells you nothing. You need 7–30 day trends and peak-hour patterns before making staffing decisions.

---

### STORY-ADB-03: Agents Performance View — Ranking and Coaching

**Goal:** Let supervisors see a performance ranking of the whole team, while agents can only see their own row.

**Key Features:**
- **4 Team KPIs:** Working Now, Total Resolved, Avg FRT, Avg AHT
- **Sortable performance table:** sort by Resolved / FRT / AHT
- **Color-coded thresholds:** FRT/AHT shown in green/orange/red
- **Fair AHT via time-split:** uses assignment_history — doesn't dump the full conversation time on the last person
- **Permission:** agent role sees only their own row + period locked to Today

**Why it matters:** If AHT is dumped entirely onto the last assignee, an agent who took over for just 5 minutes looks terrible on paper. Metric fairness is critical for performance reviews.

---

### STORY-ADB-04: Channels Performance View — Compare Channels

**Goal:** Let managers see which channels have problems — slow FRT, high Switch%, aging backlog.

**Key Features:**
- **Comparison Table:** 6 channels side-by-side — Volume, FRT, Resolution Rate, Switch%
- **Switch%:** % of customers who had to use more than one channel to resolve their issue — identified via customer_id cross-channel matching
- **Backlog Age cards:** 4 buckets (< 1h, 1-4h, 4-24h, > 1d) with escalation alert when > 3 conversations exceed 1 day
- **Color coding:** each metric has threshold-based colors

**Why it matters:** Shopee might have acceptable FRT but a high Switch% — meaning customers have to go to LINE to actually get answers. That's a broken process, not just a speed problem.

---

### STORY-ADB-05: Automation Performance View — Prove Rule ROI

**Goal:** Let admins see whether their automation rules are actually working and worth keeping — fired/handled/skip per rule plus overall FRT reduction.

**Key Features:**
- **4 KPI cards:** Rules Active (X/20), Auto-replied, Auto-tagged, FRT Reduction %
- **Rule Performance Table:** per-rule Fired, Handled, Skip, Success% with a color-coded progress bar
- **Reply Attribution:** human vs rule message breakdown + Bot FRT / Human FRT / Reduction stats
- **Tag Attribution:** auto vs manual tag breakdown + top 4 auto-tags
- **Edge cases:** deleted rule with remaining logs → shows '(deleted)'; no bot data → shows ' - ' not 0% or infinity

**Why it matters:** Without this page, admins have no way to know whether the rules they configured are firing correctly — and no data to justify keeping (or improving) the Rule Automation feature.
