# EPIC-ACE-1365 Sprint Plan
**Focus Story**: ACE-1366 (Contact Profile)

## 1. Sprint Goals
- Deliver the core `Contact Profile` side panel containing the Overview, Identities, Key Events, and Recent Conversations to improve agent context switching.
- Implement the foundational `GET /contacts/:id/context` API that will serve the profile panel.
- Ensure the UI degrades gracefully and is performant for agents managing multiple conversations.

## 2. Scope of Stories
- **ACE-1366 (STORY-CTX-01)**: Contact Profile (Profile Panel + Key Events + History)

## 3. Technical Dependencies & Risk Assessment
- **Dependency 1**: Requires the `Contact` and `Conversation` entities to be populated effectively from the existing A1 data.
- **Dependency 2**: Key events rely on backend assignments and SLA logic representing discrete timeline updates.
- **Risk (Low)**: Querying the events feed dynamically could introduce minor delays if un-indexed. **Mitigation**: Limit the events to the last 5 records and ensure proper index use on timeline markers or `created_at`.
- **Risk (Medium)**: Navigating to older conversations might lose current message drafting state. **Mitigation**: Cache the draft state in local state/Redux before routing away.

## 4. Recommended Execution Sequence
1. **[Backend] Data Layer & API Definition**: Establish the Prisma queries and build the `GET /contacts/:id/context` API. Mock unimplemented sections (like Commerce/Notes).
2. **[Frontend] Mock Integration & Component Structure**: Build the main `ContactProfilePanel` with Skeleton placeholders and connect it to the new stubbed API.
3. **[Frontend] Detail Implementation**: Implement the mini-activity feed for Key Events, Identity Badges, and Missing data placeholders.
4. **[Frontend] Navigation Linkage**: Implement the router link interactions from "Recent Conversations" out to the corresponding conversation thread.
5. **[QA] End-to-End Delivery & Testing**: Run QA Test Cases (TC-01 through TC-05) focusing on load states, chronological correctness, and navigation state drops.
