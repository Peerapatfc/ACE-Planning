# STORY-MKT-03: TikTok Connector Baseline v1 (ACE-703)

**Title:** STORY-MKT-03: TikTok Connector Baseline v1 Ingest Chat Order References Fetch History and Outbound Reply

**User Story:**
As a Tenant Admin
I want to sync TikTok conversations and reply to messages from the Omni dashboard
so that we can manage TikTok customers alongside other channels.

**Detail / Description:**
Implement TikTok specific API integration using the framework from MKT-01 and MKT-02. Focus on Chat messages and basic order context.

**Scope:**
1. TikTok API integration (Chat, Get Order)
2. Normalization of TikTok messages to Omni format
3. Send text and image outbound replies via TikTok API
4. Sync historical messages (History Fetch)

**Acceptance Criteria:**
1. Message Ingestion: New text messages from TikTok appear in the Omni conversation list.
2. Outbound Reply: Replies sent from Omni are received by the customer on the TikTok app.
3. Order Context: Basic order information attached to the conversation if the buyer initiated the chat from an order page.
4. Image Support: Ability to receive and send images.

**Subtasks:**
- ACE-1259: API TikTok Inbound
- ACE-1260: API TikTok Outbound
- ACE-1261: Normalization TikTok
- ACE-1262: History Fetch TikTok
