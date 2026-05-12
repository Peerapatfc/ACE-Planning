# EPIC ACE-1943: Notification Center — Simplified Explanation

## Overview

This Epic involves building a real-time "Notification Center" that instantly alerts agents when important events occur — such as being assigned a conversation, a customer replying, being @mentioned in a note, or an SLA deadline approaching.

The primary goal is to ensure agents **never miss critical conversations** without needing to constantly refresh their screen, while keeping notification noise low enough to avoid disrupting their work.

**Simple Analogy:**
Think of it like a desk bell that only rings when something important lands on your specific desk — not every time anything happens anywhere in the office.

---

## 1. Core Concepts

### 1.1 Who Receives What

The system categorizes events into 4 groups. Who receives each notification depends on their role and their relationship to the relevant conversation.

**Group 1 — Conversation Events (assignment changes):**
- A conversation was assigned to me → I receive it
- My conversation was reassigned to someone else → I (the original agent) receive it
- A conversation was unassigned and now has no owner → Supervisors and Admins receive it
- A new conversation arrived with no assignee → Supervisors and Admins receive it

**Group 2 — Message Events:**
- A customer replies in my assigned conversation → I receive it
- Someone @mentions me in an internal note → only the mentioned person receives it

**Group 3 — SLA Events:**
- SLA deadline approaching for my conversation → I and Supervisors receive it
- SLA breached for my specific conversation (personal alert) → I receive it
- SLA breached, team-wide alert → Supervisors and Admins receive it

**Group 4 — System Events:**
- A channel has an error (token expired, disconnected) → only Admins receive it

### 1.2 The Delivery Pipeline

Every notification must pass 5 checks before it reaches anyone:

1. An event occurs in the system
2. Check whether the Admin has enabled this event type at the workspace level (if disabled, nobody gets it)
3. Check the recipient list — who should receive this event
4. Check each recipient's personal preference — have they muted this event themselves?
5. If all checks pass → create the notification and push it in real-time via WebSocket

> **Key principle:** Admin authority is absolute. If an Admin disables an event at the workspace level, nobody receives it regardless of personal settings.

---

## 2. UI Components

### Bell Icon
- Sits in the top-right of the navigation bar on every page
- Shows the count of unread notifications (1–99, or "99+" when over 99)
- Disappears completely when all notifications are read — never shows "0"
- The count increments in real-time via WebSocket — no page refresh needed

### Notification Panel
Opens when the bell is clicked, showing notifications sorted newest-first. Each item includes:

- **Icon:** Color-coded by event group (assignment=blue, message=green, SLA=red/amber, system=gray)
- **Content:** Actor name + action description + channel badge (LINE, FB, etc.) + relative timestamp
- **Unread indicator:** Red dot on the left side; highlighted background
- **SLA notifications:** Red left border to signal urgency
- **Click item:** Navigate to conversation and automatically mark as read
- **"อ่านทั้งหมด" (Mark all):** Marks everything as read in one click
- **Infinite scroll:** Loads 50 more items when scrolling to the bottom; 30-day history retained

### Notification Rules Page (Admin/Supervisor only)
Located at Settings > Notifications > Rules. Configurable per event:
- Toggle events on/off at the workspace level
- Set who receives each event (assigned_agent / supervisor / admin)
- SLA: view the due_soon threshold value (read-only here; edit at SLA settings), configure escalation (re-notify supervisors if X minutes pass after breach with no reply)

### My Preferences Page (All roles)
Located at Settings > Notifications > My Preferences. Personal controls:
- Mute or unmute individual events for yourself only — teammates are completely unaffected
- Events disabled by Admin at the workspace level appear greyed out and cannot be toggled

---

## 3. User Flow

#### Scenario: A customer messages on LINE in a conversation assigned to Agent Min

1. **Customer sends a message:**
   - System checks → `customer_replied` event is enabled globally (passes)
   - Checks recipient list → `assigned_agent` = Min
   - Checks personal preference → Min has not muted this event
   - Notification is pushed to Min immediately via WebSocket

2. **Min sees the badge on her bell icon change to "4"**

3. **Min clicks the bell:**
   - Panel opens showing notifications newest-first
   - She sees: "Somchai sent a new message in 'Product Inquiry' · LINE"

4. **Min clicks the item:**
   - App navigates to the conversation
   - Notification is marked as read → badge decrements to "3"
   - Panel closes automatically

#### Scenario: SLA approaching but Min has muted it

- System reaches check step 4 → Min has muted `sla_due_soon`
- Min does not receive that notification
- Supervisors still receive it normally — the scopes are completely separate

---

## Scope Summary

| Category | Details |
|---|---|
| Stories in this Epic | 5 Stories (NOTIF-01 through NOTIF-05) |
| Event types | 10 events across 4 groups |
| Real-time delivery | Per-user scoped WebSocket channel |
| SLA deduplication | One `sla_due_soon` per conversation per SLA cycle |
| Authority hierarchy | Admin rules > Workspace recipient rules > Personal preference |
| Retention | 30 days |

---

## 4. Story Breakdown

### STORY-NOTIF-01: Notification Infrastructure (Backend Foundation)

**Goal:** Build all the backend infrastructure that every other notification story depends on. No UI is involved in this story.

**Key Features:**
- **Database:** `notifications` table stores every notification record. `notification_dedup` table prevents duplicate SLA alerts for the same conversation in the same cycle.
- **NotificationService:** A single centralized function `createNotification(userId, eventType, payload)`. Every feature must call this — nobody creates notifications directly.
- **Event triggers:** Wire the service into conversation assignment, inbound message handling, SLA timer checks, and channel error detection.
- **WebSocket delivery:** Push notifications to each user's private channel `user:{id}:notifications` in real-time.
- **Reconnect handling:** When a browser comes back online, the client sends its `last_seen_at` timestamp and the server returns all missed notifications from that point — no gaps.
- **SLA deduplication:** `sla_due_soon` fires at most once per conversation per SLA cycle. Resets when a customer replies and a new SLA cycle begins.
- **30-day retention:** Notifications are soft-deleted after 30 days to control data growth.

**Why it matters:** Without this story, every other notification story has no data to read from or write to.

---

### STORY-NOTIF-02: Bell Icon & Unread Badge

**Goal:** Build the bell icon in the navigation bar that shows a live unread notification count.

**Key Features:**
- **Badge format:** Displays 1–99 as a number, "99+" when count exceeds 99, hidden entirely when count is 0.
- **Initial load:** Fetches the correct unread count from the API when the page first loads.
- **Real-time update:** Badge increments immediately when a new notification arrives via WebSocket — no page refresh.
- **Optimistic mark-as-read:** Badge disappears the instant "mark all as read" is triggered, before the API response returns (reverts only if the API call fails).
- **Active state:** Bell shows a filled/highlighted visual when the notification panel is open; returns to default when it closes.

---

### STORY-NOTIF-03: Notification Panel & History

**Goal:** Build the dropdown panel that opens when the bell is clicked, displaying the full notification list with read/unread management.

**Key Features:**
- **Panel layout:** Header with "การแจ้งเตือน" title + "อ่านทั้งหมด" button + notification list + empty state ("ไม่มีการแจ้งเตือน")
- **Each item:** Event icon, actor name, action description, channel badge, relative timestamp, unread dot when unread
- **SLA urgency:** SLA notification items have a red left border
- **Infinite scroll:** Loads the next 50 notifications when scrolling to the bottom; 30-day history
- **Graceful error handling:** If a linked destination no longer exists, shows a toast instead of crashing

**Graceful errors:**
- Entire note deleted → toast: "โน้ตนี้ถูกลบแล้ว" — stay on current page, still mark as read
- Conversation deleted → toast: "Conversation นี้ไม่พบ" — stay at inbox
- Mention removed but note still exists → navigate to note normally, no error shown

---

### STORY-NOTIF-04: Notification Rules Configuration

**Goal:** Give Admins and Supervisors workspace-level control over which events are active and who receives them, at Settings > Notifications > Rules.

**Key Features:**
- **Toggle per event:** Enable or disable an event globally. Disabled events produce zero notifications for anyone in the workspace.
- **Recipients:** Multi-select who gets each event: assigned_agent, supervisor, admin.
- **SLA config:** View the `sla_due_soon` threshold pulled from SLA settings (read-only here). Configure escalation: re-notify supervisors X minutes after SLA breach if no agent has replied.
- **Fixed recipients:** `mention` is always the mentioned user. `channel_error` is always Admins only. Neither can be changed.
- **Escalation rate-limit:** Max 5 escalation notifications per user per minute — prevents supervisor inbox flood when many conversations breach simultaneously.
- **Agents cannot access this page:** They are redirected to an Access Denied page.

---

### STORY-NOTIF-05: Personal Notification Preferences

**Goal:** Let every user mute or unmute specific event types for themselves only, at Settings > Notifications > My Preferences.

**Key Features:**
- **Personal mute:** Toggle individual events on/off for yourself only. Your teammates are completely unaffected.
- **Role-filtered view:** Agents only see the events they are eligible to receive — events like `new_conversation` or `sla_breached_team` are not shown to Agents at all.
- **Greyed out when globally disabled:** If an Admin disabled an event at the workspace level, it appears greyed out in My Preferences with a tooltip: "ปิดโดย Admin ของ workspace กรุณาติดต่อ Admin เพื่อเปิดใช้งาน" — the user cannot override it.
- **Default state:** All events are unmuted for new users. Nothing is muted unless the user explicitly does it themselves.
- **Immediate effect:** Preference changes apply to the next new event immediately. Notifications already in the bell are not removed retroactively.
