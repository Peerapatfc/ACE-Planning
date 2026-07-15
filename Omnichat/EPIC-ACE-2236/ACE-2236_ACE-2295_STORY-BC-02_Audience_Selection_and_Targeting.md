# STORY-BC-02: Audience Selection and Targeting

**Status:** In Progress | **ClickUp:** [ACE-2295](https://app.clickup.com/t/86d32c89v) | **Epic:** [ACE-2236](https://app.clickup.com/t/86d318wjb) | **Assignee:** Peerapat

> **Blocker (comment, griangsak):** ~~Hold ไว้ก่อน ยังไม่มี Contact Tags~~ — **Resolved** (comment, Pornparawee): ทำได้หลังจากพี่คิว @Peerapat Pongnipakorn ทำ Contact tag เสร็จ

> ⚠️ **AC ใน ClickUp ยังไม่ถูกแก้ตาม team decision 2026-07-13** (targeting แยก 3 โหมด + exclude tags) — AC1.1 ยังเขียน "list รวมทั้ง 2 ชนิด" และยังไม่มี AC ฝั่ง exclude · ดีไซน์ล่าสุดยึดตาม [Diagrams/](Diagrams/ACE-2236_ACE-2295_STORY-BC-02_Sequence_Diagram.md)

## User Story

**AS** an Admin/Supervisor
**I WANT TO** select target audience for broadcast using tags
**SO THAT** I can send relevant messages to specific customer segments

## Description

Story นี้ focus ที่การเลือก audience สำหรับ broadcast โดยใช้ tags ที่มีอยู่ในระบบ (จาก Contact Profile และ Rule Automation)

**Features:**
- Searchable tag dropdown with chip display
- "Send to everyone" option (broadcast ทุกคนที่เชื่อมกับ LINE OA นี้)
- "Send to specific people" option with tag selection
- Real-time estimated reach calculation
- Filter โดย LINE OA ที่เลือกใน BC-01
- Quota validation with plan-aware warnings

## Acceptance Criteria

### AC1: Tag selection with searchable dropdown
**GIVEN** Admin selects "Send to specific people"
**WHEN** tag selector appears
**THEN** shows:
- Search input field with placeholder: "ค้นหา tag..."
- Dropdown icon (▼)
- Selected tags displayed as chips below input

### AC1.1: Search and filter tags
**GIVEN** Admin clicks on tag search input
**WHEN** dropdown opens
**THEN** shows list of all available tags (ทั้ง tag ระดับ chat และ tag ระดับบุคคล):
- Tag name
- Contact count (e.g., "VIP (125)")
- Sorted A-Z

**WHEN** Admin types in search input
**THEN** filters tag list in real-time:
- Matches tag name (case-insensitive)
- Shows only matching tags

**WHEN** no tags match search → shows: "ไม่พบ tag ที่ค้นหา"

### AC1.2: Select tag from dropdown
**GIVEN** dropdown is open with tag list
**WHEN** Admin clicks on a tag
**THEN**:
- Tag is selected
- Tag appears as chip below search input:
  - Tag name in chip
  - remove button on chip
  - Tag color/style (if applicable)
- **Selected tag is REMOVED from dropdown list**
- Dropdown remains open for multi-select
- Target estimate updates immediately

**WHEN** Admin selects multiple tags
**THEN** chips display in horizontal row:
- Wrap to next line if needed
- Each chip shows tag name + [X]

### AC1.3: Remove selected tag
**GIVEN** Admin has selected tags (shown as chips)
**WHEN** they click [X] on a chip
**THEN**:
- Tag chip is removed
- **Tag reappears in dropdown list (alphabetically sorted)**
- Target estimate updates
- Dropdown list updates (tag becomes available again)

### AC1.4: Close dropdown
**GIVEN** dropdown is open
**WHEN** Admin clicks outside dropdown area OR presses Escape key
**THEN** dropdown closes AND search input clears AND selected tags remain as chips

### AC1.5: Validation for tag selection
**GIVEN** Admin selects "Send to specific people"
**WHEN** they click to proceed to next step AND no tags selected
**THEN** shows validation error:
- Tag selector border turns RED
- Error message: "กรุณาเลือกอย่างน้อย 1 tag"
- Prevents proceeding

### AC2: Target estimate with multiple tags
**GIVEN** Admin selects multiple tags
**WHEN** tags are selected
**THEN** target estimate shows:
- Combined **unique** contact count (no duplicates)
- Example: Tag chips show: [VIP] [New Customer]
- Estimate below: "Send to approximately **280 recipients**" (unique contacts)
- Percentage badge: "70%" (if 280 out of 400 total contacts)

**WHEN** tags are added or removed → estimate recalculates in real-time

### AC3: All contacts option works
**GIVEN** Admin clicks "Send to everyone" radio button
**WHEN** selected
**THEN**:
- Tag search input is HIDE
- Any selected tag chips are cleared
- Estimated reach shows all contacts count of selected LINE OA
- Shows: "Send to approximately **400 recipients** (100%)"

**WHEN** Admin switches back to "Send to specific people"
**THEN** tag search input re-enables AND chips area is empty (ready for selection)

### AC4: Estimated reach calculation is accurate
**GIVEN** Admin has configured audience
**WHEN** system calculates reach
**THEN** count matches actual contacts query:
- Has valid line_user_id for the selected LINE OA
- Has at least one included tag (if "specific people" selected)
- **Deduplicates contacts** (if contact has multiple selected tags, count once)

AND calculation completes within 2 seconds
