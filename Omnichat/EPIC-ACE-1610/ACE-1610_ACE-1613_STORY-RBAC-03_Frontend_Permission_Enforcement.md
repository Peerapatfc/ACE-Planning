# STORY-RBAC-03: Frontend Permission Enforcement

**Status:** Backlog

## User Story

As a Frontend Engineer
I want to implement route guards, role-based UI visibility, and correct reply behavior based on user role
so that users see and can interact with only what their role permits, and the experience is clear and consistent.

## Detail / Description

Story นี้ build permission enforcement ฝั่ง frontend ซึ่งทำหน้าที่ 2 อย่าง:
- **Route guard:** ป้องกัน user ที่ไม่มีสิทธิ์จากการ navigate ไป route ที่ไม่ควรเข้า (เช่น เมื่อ Supervisor ส่ง link ให้ Agent)
- **UI visibility:** ซ่อน หรือ adjust elements ที่ไม่มีสิทธิ์ เพื่อให้ UX ชัดเจน

## Scope of this story

- Route guard: redirect เมื่อ user navigate ไป route ที่ไม่มีสิทธิ์ (direct URL หรือ shared link)
- 403 page: แสดงเมื่อ server return 403 บอก role ที่ต้องการ และ link กลับหน้าหลัก
- Settings sidebar: แสดงเฉพาะ section ที่ role มีสิทธิ์ section ที่ไม่มีสิทธิ์ hidden ไม่ใช่ greyed out
- Assign button: ซ่อนสำหรับ Agent แต่ Supervisor และ Admin เห็นและกดได้
- Reply behavior: ทุก role ตอบได้ทุก conversation แต่ถ้า conversation assigned ให้คนอื่น แสดง "assigned to [ชื่อ]" ให้ชัดเจน
- `usePermission` hook: helper ที่ทุก component ใช้ check permission ได้โดยไม่ต้อง hardcode role
- ไม่รวม Settings page content อยู่ใน SETTINGS EPIC

## Route Permission Map

| Route | Admin | Supervisor | Agent |
|---|---|---|---|
| /inbox | ✅ | ✅ | ✅ |
| /settings/workspace/* | ✅ | ❌ | ❌ |
| /settings/channels | ✅ | ❌ | ❌ |
| /settings/sla | ✅ | ✅ | ❌ |
| /settings/notifications/rules | ✅ | ✅ | ❌ |
| /settings/notifications/preferences | ✅ | ✅ | ✅ |
| /settings/members | ✅ | ❌ | ❌ |

## Acceptance Criteria

### Route guard redirects unauthorized users accessing restricted pages
- Given an Agent navigates to `/settings/sla`
- Then they are redirected to `/inbox` immediately before any page content renders
- And a toast notification appears: "คุณไม่มีสิทธิ์เข้าถึงหน้านี้"
- And no Settings content or data is visible even briefly

### 403 page displays when server returns 403 Forbidden
- Then a 403 page is shown with a message explaining access is denied
- And a "กลับหน้าหลัก" button is displayed
- And the page does not expose which resource was being accessed

### Settings sidebar shows only permitted sections per role
- Admin → all sections visible: Workspace, Channels, SLA, Notifications
- Supervisor → only SLA and Notifications visible (Workspace and Channels not present in UI at all)
- Agent → only Notifications > My Preferences visible

### Assign button is hidden for Agent role
- Agent viewing any conversation → Assign / Reassign panel is not present in UI (no disabled/greyed-out version)
- Supervisor or Admin → Assign panel visible and functional

### All roles can reply to any conversation
- Given an Agent opens a conversation assigned to another agent
- Then the reply input is fully enabled and functional
- When Agent sends a reply → `replied_by` is recorded as this Agent's `user_id`

### usePermission hook returns correct value and updates on role change
- `usePermission("assign_conversation")` with Supervisor → `true`
- `usePermission("assign_conversation")` with Agent → `false`
- When role changes and session refreshes → hook returns updated value without full page reload

### Permission state is derived from session (no extra API calls)
- `usePermission` check is evaluated locally from cached session data
- No additional API request made to verify role
- Frontend still relies on backend 403 as actual security enforcement

### No flash of unauthorized content
- Restricted elements are never shown even momentarily before being hidden
- No layout shift caused by elements appearing then disappearing

### Graceful handling when session token expires mid-session
- Redirect to login page with current URL saved for return
- Message: "กรุณา login ใหม่ session หมดอายุแล้ว"

## UI/UX Notes

- Route guard ต้อง run ก่อน component render ทั้งหมด ห้ามให้ page content โผล่
- 403 page: icon lock + หัวข้อ "ไม่มีสิทธิ์เข้าถึง" + อธิบาย + ปุ่ม "กลับหน้าหลัก"
- Settings sidebar: hidden section ของแต่ละ role

## Technical Notes

**Dependencies:**
- RBAC-01 action list และ permission definitions ต้องถูก finalize ก่อน
- Authentication system ต้อง expose role ใน session/token เพื่อให้ `usePermission` hook อ่านได้
- Router system ของ frontend framework ต้องรองรับ guard hooks

**Special focus:**
- `usePermission` hook ต้อง derive จาก role ที่อยู่ใน app state (Redux, Zustand, Context) ไม่ใช่ call API ใหม่ทุกครั้ง
- Route guard ต้อง check ทั้ง initial load และ navigation ระหว่าง session
- Frontend hide = UX เท่านั้น ไม่ถือว่า secure จนกว่า backend 403 จะ enforce ด้วย (RBAC-01)
- Assignment banner ต้องดึงชื่อ assignee จาก conversation object ที่มีอยู่แล้ว ไม่ต้อง API call ใหม่
- ถ้า role change เกิดขึ้น ระบบควร invalidate permission cache เมื่อ token refresh หรือ next page load

## QA / Test Considerations

**Primary flows:**
- Supervisor เปิด Settings → เห็นแค่ SLA + Notifications
- Agent เปิด conversation ที่ assigned ให้คนอื่น → reply ได้
- Agent เปิด conversation ที่ assigned ให้ตัวเอง → reply ได้
- Agent เปิด conversation → Assign panel ไม่อยู่ใน UI

**Edge Cases:**
- User paste URL `/settings/workspace` ใน browser โดยตรง → route guard ทำงานก่อน render
- Role ถูกเปลี่ยนระหว่าง session → refresh → permission update ถูกต้อง
- Session หมดอายุ → redirect login พร้อม return URL
- Server return 403 → 403 page แสดง (ไม่ crash หรือ blank page)

**Business-Critical Must Not Break:**
- ห้ามมี restricted content โผล่ (flash of unauthorized content ถือเป็น bug)
- Agent ต้องไม่เห็น Assign panel ไม่ว่ากรณีใด
- Reply ต้อง work สำหรับทุก role ทุก conversation

**Test Types:**
- Unit tests สำหรับ `usePermission` hook ทุก role × action
- E2E tests สำหรับ route guard: direct URL access ทุก restricted route
- Visual regression tests สำหรับ sidebar ต่อ role
