# EPIC ACE-1365: Contact Profile and Commerce Context — Simplified Explanation

## Overview
This Epic involves building a "Unified Contact Profile" (Contact Profile) to give Agents a holistic view of the same customer interacting across multiple channels. It enables the system and the agents to securely recognize the same person and share contact-level history and notes in a single place.

**Simple Analogy:**
It's like a "Patient Medical Record". No matter which department (channel) the patient visits, the doctor sees their complete past history, identity details, and chronic notes all within one unified folder.

---

## 1. Core Concepts

### 1.1 Identity vs. Contact
- **Identity (Channel-Specific):** The customer's identity tied to a specific channel e.g., LINE user_id, Facebook PSID.
- **Contact (Unified Person):** The Omnichat-level entity (Contact ID) that acts as the umbrella grouping multiple channel identities into "the same person".

### 1.2 Merge Rules (v1)
1. **Deterministic Auto Link:** If the system detects the exact same channel identity (e.g., the same LINE user_id), it always maps it to the same Contact ID.
2. **Marketplace Shop Scoping:** Identities on Marketplaces (TikTok/Shopee/Lazada) are strictly scoped by `shop_id`. No cross-shop auto-merge is allowed.
3. **No Cross-Channel Auto-Merge:** Even if the phone number or email matches perfectly, the system will NOT automatically merge a LINE and a FB account in v1. Instead, it will display a suggestion for manual linking.
4. **Manual Link:** Agents can manually link identities together. This action is carefully recorded with an audit trail and provides an undo window.

---

## 2. UI Components

### Contact Profile Panel
When an agent opens a conversation, the side panel displays:
- **Overview:** Display image, name, tags, last seen timestamp, and total conversation count.
- **Identities:** A clear list of all joined channel identities (e.g., showing both a LINE badge and a Facebook badge).
- **Key Events:** A timeline of the 5 most recent activities (e.g., assignment changes, SLA events, note additions).
- **Recent Conversations:** A readily clickable list of past chats that seamlessly navigates into them.

### Customer Notes
- These are attached to the **Contact**, not an individual Conversation.
- Written once, visible to every agent in the tenant across any future conversation with that contact, regardless of the channel.
- Supports **Pinning** critical notes to the top (e.g., "VIP Customer" or "Refund pending").
- Includes an **Audit Trail** capturing exactly who wrote or updated the note and when.

---

## 3. User Flow Sequence

#### Scenario: Customer "Somchai" contacts via LINE, then later via Facebook.

1. **First Contact (LINE):**
   - System recognizes a new user, creating Identity 1 (LINE) and Contact A.
   - The Agent writes a Customer Note: "Customer prefers red color."
2. **Second Contact (Facebook):**
   - Somchai messages via Facebook. System creates Identity 2 (FB) and Contact B.
   - The system detects matching phone/email logic and shows a **"Suggested Link"** to the agent instead of auto-merging.
3. **Manual Linking:**
   - The Agent confirms and clicks "Link".
   - System manually merges them, placing Identity 2 securely under Contact A.
4. **Result:**
   - While still on the Facebook chat, the Agent instantly sees the old Customer Note "Customer prefers red color" that was written during the LINE chat.
   - The Contact Profile panel shows Somchai having 2 distinct channel identities (LINE + Facebook).

---

## Scope Summary (v1)

| Category | Details |
|---|---|
| In Scope Stories (Phase 1) | 3 (Contact Profile, Merge Rules, Customer Notes) |
| Backlog Stories | 3 (Last Purchase, Order Details, Order Actions) |
| Auto-Merge Rule | Strict to same identity type/shop. No cross-channel auto. |
| Cross-Channel Merge | Manual Link only (with Audit Log + Undo). |
| Customer Notes | Contact-level, pinnable, tenant-wide visibility. |

---

## 4. Story Breakdown

### STORY-CTX-01: Contact Profile 
**Goal:** Build a side panel giving agents immediate context about the customer without switching screens.
**Key Features:**
- **Overview:** Displays profile image, name, tags, last seen time, and primary contact info (phone/email).
- **Identities:** Lists badges for all channels this customer uses (e.g., LINE, Facebook).
- **Key Events:** Chronological display of the 5 most recent activity events (status changes, SLA updates, notes).
- **Recent Conversations:** A list of past interactions with the ability to click and navigate to older chats.

### STORY-CTX-02: Identity Model and Merge Rules v1 
**Goal:** Define strict rules for recognizing users to prevent accidental merging of different customers.
**Key Features:**
- **Auto-Merge Rules:** Only auto-merges within the same exact identity type (e.g., same LINE ID). For Marketplaces, it strictly scopes by Shop ID. 
- **Suggestions, Not Actions:** If a phone/email matches across different channels (e.g., LINE and FB), the system will **not** auto-merge it in v1. It will instead display a "Suggested Link" prompt.
- **Manual Control:** Agents can Manually Link or Unlink identities. All actions generate an Audit Log, and links feature an Undo option for safety.

### STORY-CTX-03: Customer Notes 
**Goal:** Allow agents to leave permanent, shared notes about a customer for the whole team to see.
**Key Features:**
- **Contact-Level Visibility:** Notes are tied to the Contact, meaning any agent in the tenant will see the note regardless of which channel the customer is currently using.
- **Pinning:** Important notes (like "VIP" or "Frustrated Customer") can be pinned to the top.
- **Audit Trail:** Transparently records the 'updated_by' and 'updated_at' to track who made modifications.
