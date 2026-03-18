# STORY-ICU-03: Reply Composer UI send text and show delivery state
**ID:** ACE-1101
**Status:** TO DO
**Sprint Points:** 7
**Assignee:** Tanawin(Toy)

**Description (User Story):**
> As a Support Agent
> I want to type and send messages to customers from the inbox
> so that I can provide support and resolve inquiries in real-time.

**Detail / Description:**
* การ์ดนี้คือ compose box และการส่งข้อความจาก inbox
* ต้องรองรับ text reply สำหรับทุกช่องทางที่ A1 รองรับ outbound ใน R1
* เมื่อกดส่ง ต้องเรียก send API แล้ว persist outbound message และแสดงสถานะ sending sent failed
* ต้องมี error message ที่อ่านง่าย เช่น auth_error permission_error rate_limit เพื่อให้ agent รู้ว่าต้องทำอะไรต่อ

**Scope:** 
Text input only for R1 pilot

**Acceptance Criteria:**
1. Composer renders at the bottom of the timeline properly.
2. Send action triggers backend API with correct conversation context and content.
3. UI feedback for delivery state:
   * When message is sent
   * Then bubble shows sending state
   * When API returns success
   * Then bubble shows sent state
   * When API returns error
   * Then bubble shows failed state with retry option
4. Validation:
   * Given the composer is empty
   * When the agent clicks send
   * Then the action is disabled or blocked

**Technical Notes:**
* **APIs:**
  * POST /send-message (or similar)
  * Payload: `conversation_id`, `content: { text: string }`
  * Response: `message_id`, `status`
* **Data:** Maintain optimistic UI state for bubbles during sending phase

**Subtasks (2):** 
- ACE-1105, ACE-1390

**Comments:**
* Attachai Saorangtoi: "Retry อาจจะต้องแยก Task @Thanyapong"
