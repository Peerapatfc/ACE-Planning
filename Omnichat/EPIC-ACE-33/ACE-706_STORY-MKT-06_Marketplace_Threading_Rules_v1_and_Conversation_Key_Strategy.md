# STORY-MKT-06: Marketplace Threading Rules v1 (ACE-706)

**Title:** STORY-MKT-06: Marketplace Threading Rules v1 and Conversation Key Strategy

**User Story:**
As a System
I want a consistent strategy to map marketplace buyers to conversations
so that messages from the same person in the same shop are grouped correctly.

**Detail / Description:**
Marketplace threading ต่างจาก social เพราะบางครั้ง thread id ไม่ชัดหรือมี buyer/seller identifiers และ shop contexts ไม่ครบ Story นี้กำหนด rule v1 ที่ simple testable เช่น conversation key based on tenant_id + channel_account_id + external_buyer_id and optional external_thread_id when available เพื่อกันหลุดห้องและกัน mixing ข้าม shop

**Scope:**
1. Define threading strategy for TikTok, Shopee, Lazada
2. Apply rule in normalization for inbound and outbound mapping
3. Store external identifiers for audit and debug
4. Document limitations such as merged buyer identity across marketplaces not supported in R1

**Acceptance Criteria:**
1. Deterministic conversation mapping for same buyer and shop: Given multiple messages from the same buyer under the same marketplace shop, When processed, Then they map to the same conversation_id consistently.
2. Different shops never share a conversation: Given two shops under the same tenant, When messages arrive from the same buyer id value in different shops, Then the system creates separate conversations and does not mix them.
3. Outbound replies map to existing conversation: Replies use the correct external identifiers to post back to the right external thread.
