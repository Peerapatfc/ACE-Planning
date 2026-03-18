# STORY-ICU-02: Conversation Timeline UI with message bubbles attachments and ordering
**ID:** ACE-1100
**Status:** TO DO
**Sprint Points:** 10
**Assignee:** griangsak

**Description (User Story):**
> As a Support Agent
> I want to open a conversation and view the full timeline with inbound outbound messages and attachments
> so that I can understand context quickly and respond accurately.

**Acceptance Criteria:**
1. Timeline loading:
   * When the timeline view opens
   * Then the system loads the latest messages from the timeline API and renders them in chronological order
2. Inbound and outbound display rules:
   * Given messages include direction inbound and outbound
   * When rendering message bubbles
   * Then inbound messages display as customer side and outbound messages display as agent side consistently
3. Attachment rendering for images:
   * Given a message has one or more image attachments with secure link references
   * When the timeline renders
   * Then image thumbnails are shown and clicking opens the image using a secure retrieval method without exposing raw storage keys
4. Source labels are visible:
   * Given messages have source values such as platform, external_native, imported
   * When the message bubble is rendered
   * Then a small label or icon is shown to indicate the source and imported messages are visually distinguishable
5. Timeline pagination loads older messages safely:
   * Given a conversation has more messages than the initial page size
   * When the agent clicks Load older or scrolls to top to load more
   * Then older messages are appended at the top without duplicates and ordering remains correct
6. Error handling is user friendly:
   * Given the timeline API fails temporarily
   * When the UI attempts to load messages
   * Then the UI shows a retry action and does not clear the existing timeline content if already loaded
7. Time display and timezone consistency:
   * Given messages have channel timestamp and created_at
   * When rendering timestamps
   * Then the UI displays consistent time in tenant timezone and ordering uses the correct timestamp policy

**UI/UX Notes:**
* Right pane layout: header section, message list, composer at bottom
* Message bubble design: clear contrast between inbound/outbound, sender name for group chats if applicable, timestamp visible on hover or persistent
* Loading skeletons for smoothness

**Technical Notes:**
* **APIs:**
  * GET messages
  * Parameters: conversation_id, before_cursor (for older messages), limit
  * Response: items with direction, sender_type, content (text/rich), attachments, external_id, source, timestamps
* **Data:**
  * Secure retrieval for attachments (e.g. signed URLs from backend)
  * Ensure message ordering uses stable sort on timestamp + ID to prevent flickering

**Subtasks (4):** 
- ACE-1104, ACE-1389, ACE-1387, ACE-1388

**Comments:**
* Attachai Saorangtoi: "Pagination: Limit: 30 (able to change)"
