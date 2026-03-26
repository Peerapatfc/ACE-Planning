# EPIC-ACE-1365 / ACE-1366 Task Breakdown
**Story**: STORY-CTX-01_Contact_Profile (Profile Panel + Key Events + History)

## 1. Backend / API Tasks
### 1.1 Create Contact Context API
- **Task**: `GET /api/v1/contacts/:contact_id/context`
- **Description**: Implement a new API endpoint to retrieve the full context of a contact for the profile panel.
- **Endpoint Data**:
  - `overview`: Contact details from the `Contact` model (name, avatar, first/last seen).
  - `identities`: Connected identities representing external channel accounts (from `ChannelAccount`).
  - `key_events`: Chronological list of the last 5 key events (e.g. assignments from `ConversationAssignment` or specific SLA status changes).
  - `recent_conversations`: List of up to 5-10 recent conversations related to the `contact_id` from the `Conversation` model, ordered by `last_message_at DESC`.
  - `last_purchase_stub`: Placeholder for future implementation.
  - `customer_notes`: Placeholder for future implementation.

### 1.2 Conversation Context Enhancements
- **Task**: Data Layer Queries for Context
- **Description**: Implement Prisma queries to aggregate contact identities, event feeds, and recent conversations efficiently. Create a unified response mapping.

## 2. Database Tasks
### 2.1 Schema Adjustments
- **Task**: Review SLA event data sources
- **Description**: Ensure we have the proper event structures. As per notes, `ConversationAssignment` is available, but SLA events might need preliminary fields in `Message` or `Conversation`.

## 3. Frontend (UI) Tasks
### 3.1 Contact Profile Panel Component
- **Task**: Build the `ContactProfilePanel` UI
- **Description**: Create a collapsible side panel for the contact profile conforming to the UI/UX notes (Overview -> Identities -> Last Purchase -> Customer Notes -> Key Events -> Recent Conversations).

### 3.2 Key Events Mini Activity Feed
- **Task**: Build Key Events Feed
- **Description**: Implement a mini activity feed within the panel or conversation header showing the recent chronological events (last 5) with author and timestamps.

### 3.3 Identities & Graceful Degradation
- **Task**: Edge Cases & Placeholders
- **Description**: Handle missing data (e.g., missing last_seen) gracefully using placeholders and skeleton loaders during the initial API fetch. Render badges for each identity/channel.

### 3.4 Recent Conversations Navigation
- **Task**: Inbox Navigation
- **Description**: Wire up the recent conversations list to predictably navigate the agent to the selected historical conversation, while preserving the inbox view state.

## 4. QA & Testing
### 4.1 Test Cases (Manual & Automated)
- **TC-01 (Identities)**: 
  - *Given* contact has multiple channel identities. 
  - *When* panel renders. 
  - *Then* it shows each identity with a channel badge and masked ID.
- **TC-02 (Key Events)**: 
  - *Given* assignment and SLA events exist. 
  - *When* panel renders. 
  - *Then* chronological list of 5 key events displays with author/time.
- **TC-03 (Recent Conversations Nav)**: 
  - *Given* contact has multiple conversations. 
  - *When* agent clicks a recent conversation. 
  - *Then* inbox navigates to that thread.
- **TC-04 (Missing Data)**: 
  - *Given* missing fields (e.g. no last seen). 
  - *When* panel renders. 
  - *Then* layout does not break and placeholders are shown.
- **TC-05 (Performance)**: Verify the panel renders skeleton loaders during API latency and is lightweight/responsive.
