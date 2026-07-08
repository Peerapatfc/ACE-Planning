# STORY-BC-05: Broadcast List

**Status:** To Do | **ClickUp:** [ACE-2503](https://app.clickup.com/t/86d3dhcrm) | **Epic:** [ACE-2236](https://app.clickup.com/t/86d318wjb)

## User Story

**AS** Admin/Supervisor
**I WANT TO** ดูรายการ broadcasts ทั้งหมด
**SO THAT** สามารถจัดการและติดตาม status ของ broadcast

## Acceptance Criteria

### AC1: Topbar
**GIVEN** หน้า Broadcast List
**THEN** มี:
- Title: "บรอดแคสต์"
- "สร้างใหม่" button → ไปหน้า Create broadcast

### AC2: Search & Info Section
**GIVEN** หน้า Broadcast List
**THEN** มี:
- Search input: ค้นหา broadcast name
- Filter: เมนู filter broadcast

### AC3: Tabs
**THEN** มี 6 tabs:
- **ทั้งหมด (All)** — แสดง broadcasts ทั้งหมด (รวม Sending ด้วย, ไม่มี tab Sending แยก)
- **ตั้งเวลาส่ง (Scheduled)** — broadcasts ที่ตั้งเวลาส่ง แต่ยังไม่ส่ง
- **ส่งแล้ว (Sent)** — broadcasts ที่ส่งแล้ว สำเร็จ
- **ผิดพลาด (Error)** — broadcasts ที่มีข้อผิดพลาด
- **ส่งแล้วแต่มีข้อผิดพลาด (Sent with error)**
- **แบบร่าง (Draft)**

### AC4: Data Table columns (in order)
- ID - Broadcast ID
- ชื่อข้อความ - Broadcast name
- LINE OA name - Which LINE account
- status - sent, scheduled, error, sent with error, draft
- เป้าหมาย - Target audience (e.g. "All", "VIP Tag", "New Customer")
- จำนวนผู้รับ - "Total recipients count" / "Total Target audience"
- วันบรอดแคสต์ - Send date (sortable ↑↓)
- วันที่อัพเดต - Update date (sortable ↑↓)

### AC5: Default Sorting & Ordering
**WHEN** page load หรือ clear filter
**THEN**:
- Default sort: วันที่อัพเดต (newest first)
- Broadcasts ที่อัพเดตล่าสุด pin ไว้ด้านบนสุด
- Show sort icon: ↓ (descending)

### AC6: Table Row Interaction
**WHEN** hover on row → Row highlight
**WHEN** click → go to broadcast detail page

### AC7: Search Functionality
**WHEN** type broadcast name
**THEN**:
- Real-time search (auto-filter)
- Show results matching broadcast name
- If no results → "ไม่พบข้อมูล"
- Clear button (X) to reset

### AC8: Filter Modal
**WHEN** user click Filter button
**THEN** can filter by:
- Updated Date picker 1: DD/MM/YYYY (from date)
- Updated Date picker 2: DD/MM/YYYY (to date)
- Dropdown: SELECT LINE OA name
- Buttons: "ค้นหา" (apply filter) | "รีเซ็ต" (reset)

### AC9: After Filter Applied
**WHEN** filter apply → table shows filtered results, sorted by วันที่อัพเดต newest first

> **Note (comment, griangsak):** search/filter/sorting/pagination ควรอยู่ tab เดิม (ไม่ reset กลับไปที่ tab "ทั้งหมด")

### AC10: Pagination
**WHEN** more than 10 items
**THEN**:
- Display 10 broadcasts per page
- Show pagination controls: 1, 2, 3... Next/Previous
- Show total count: "Showing 1-20 of 100"

### AC11: Empty State

| Tab | Empty state text |
|---|---|
| ทั้งหมด (All) | "ยังไม่มี broadcast" |
| ตั้งเวลาส่ง (Scheduled) | "ยังไม่มี broadcast ที่ตั้งเวลาส่ง" |
| ส่งแล้ว (Sent) | "ยังไม่มี broadcast ที่ส่งสำเร็จ" |
| ผิดพลาด (Error) | "ไม่มี broadcast ที่เกิดข้อผิดพลาด" |
| ส่งแล้วแต่มีข้อผิดพลาด (Sent with error) | "ไม่มี broadcast ที่ส่งแล้วแต่มีข้อผิดพลาด" |
| แบบร่าง (Draft) | "ยังไม่มีแบบร่าง" |

### AC12: Sorting
**GIVEN** sortable columns (วันบรอดแคสต์, วันที่อัพเดต)
**WHEN** click column header → Sort ascending (↑) | Click again → sort descending (↓) | Only one column sorted at a time

### AC13: Action menu (3-dot)
**WHEN** user กดปุ่ม `⋮` บน row
**THEN** แสดง dropdown menu ตาม status:

| Status | Actions |
|---|---|
| Draft | View, Edit, Delete |
| Scheduled | View, Cancel Scheduled |
| Sent | View |
| Sent with error | View |
| Error | View |

- "View" → ไปหน้า Broadcast Detail
- "Edit" → ไปหน้า Create/Edit form
- "Delete" → แสดง confirmation modal ก่อนลบ
- คลิกนอก dropdown → ปิด menu

### AC14: Agent role - read-only mode
**GIVEN** user role = Agent
**WHEN** Agent in broadcast list page
**THEN** Create button is disabled AND Three dot menu is disabled AND Agent can only click to see detail
