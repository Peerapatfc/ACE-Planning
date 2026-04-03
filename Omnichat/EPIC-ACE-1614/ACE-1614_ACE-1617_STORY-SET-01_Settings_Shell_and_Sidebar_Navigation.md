# STORY-SET-01: Settings Shell & Sidebar Navigation

**Status:** Backlog

**Depends On:** RBAC-01

## User Story

As a logged-in user
I want a dedicated Settings area with clear navigation that shows only sections I have access to
so that I can find and configure workspace settings without confusion or unauthorized access.

## Detail / Description

Story นี้ build layout shell และ navigation ของ Settings area ทั้งหมด เป็น pure frontend story ที่ทำก่อน SET-02 และ SET-03
Content ของแต่ละ section จะ build ใน stories ถัดไป story นี้ทำแค่ shell, routing, และ access control ของ navigation

## Settings Sections และ Role ที่เข้าได้

| Settings Section | Admin | Supervisor | Agent |
|---|---|---|---|
| Business Information | ✅ | ❌ | ❌ |
| Members & Roles | ✅ | ❌ | ❌ |
| Channels (existing) | ✅ | ❌ | ❌ |
| SLA Rules (via SLA-01) | ✅ | ✅ | ❌ |
| Notification Rules (via NOTIF-04) | ✅ | ✅ | ❌ |
| My Preferences (via NOTIF-05) | ✅ | ✅ | ✅ |

## Scope of this story

- Settings layout: sidebar navigation (left) + content area (right)
- Sidebar แสดงเฉพาะ section ที่ role มีสิทธิ์ — section ที่ไม่มีสิทธิ์ **hidden** ไม่ใช่ greyed out
- Active section highlighted ใน sidebar
- Breadcrumb ด้านบน content area: `Settings > Business Information`
- Auto-redirect ไป first accessible section เมื่อเข้า `/settings` โดยตรง
- Route guard: direct URL access ไป section ที่ไม่มีสิทธิ์ → redirect
- Content area ของแต่ละ section เป็น placeholder รอ stories ถัดไป
- ไม่รวม content ของแต่ละ section (อยู่ใน SET-02, SET-03, SLA-01, NOTIF-04, NOTIF-05)

## Acceptance Criteria

### Settings area is accessible from the main navigation
- Given any logged-in user clicks the Settings icon
- Then they are taken to Settings area and sidebar auto-selects the first accessible section
- And no blank or empty screen is shown

### Admin sees all sidebar sections
- Business Information, Members & Roles, Channels, SLA Rules, Notification Rules, My Preferences

### Supervisor sees only permitted sections
- Only SLA Rules, Notification Rules, and My Preferences are shown
- Business Information, Members & Roles, and Channels are **not present in UI at all**

### Agent sees only My Preferences
- All other sections are absent from the UI

### Route guard blocks direct URL access to unauthorized sections
- Given an Agent types `/settings/business-information` directly
- Then they are redirected to 403 and no restricted content is shown even briefly

### Active section is highlighted with breadcrumb
- Active section has visual indicator in sidebar
- Breadcrumb shows correct path e.g. "Settings > Business Information"

### Settings navigation persists across section switches
- Content area updates without full page reload
- No unsaved data warning unless a form has unsaved changes

### Settings layout renders correctly at standard desktop width
- Sidebar and content area render side by side without overflow or overlap

## UI/UX Notes

- Layout: sidebar + content area, full viewport height minus top nav
- Sidebar: group labels, section links with left-border indicator when active
- Active section: left border solid primary color + subtle bg highlight
- Breadcrumb: "Settings > [Section name]" ด้านบน content area — text เล็ก muted
- Content area: placeholder ที่ render section component ที่ถูก route มา

## Technical Notes

**Dependencies:**
- RBAC-01 role และ permission system ต้องมีก่อนเพื่อ filter sidebar sections
- RBAC-03 route guard pattern — ควร reuse guard hook เดียวกัน
- Frontend router ต้องรองรับ nested routes สำหรับ `/settings/*` pattern

**Special focus:**
- Hidden sections ต้อง **not in DOM** ไม่ใช่แค่ hidden ด้วย CSS (dev tools จะเห็นได้)
- Route guard ต้อง run ก่อน component render ห้ามมี flash of content
- First accessible section ควร determine ฝั่ง server หรือ guard เพื่อหลีกเลี่ยง redirect loop

## QA / Test Considerations

**Primary flows:**
- Admin เข้า Settings → เห็นทุก section → click แต่ละ section → breadcrumb ถูกต้อง
- Supervisor เข้า Settings → เห็นแค่ SLA + Notifications + My Preferences
- Agent เข้า Settings → เห็นแค่ My Preferences → auto-select ทันที

**Edge Cases:**
- Agent พิมพ์ `/settings/business-information` โดยตรง → redirect
- User สลับ section โดยไม่ save form → warn ถ้ามี unsaved changes
- Role ถูกเปลี่ยนระหว่าง session → sidebar update ถูกต้องหลัง refresh

**Business-Critical Must Not Break:**
- ห้ามมี section ที่ไม่มีสิทธิ์ปรากฏใน DOM ไม่ว่ากรณีใด
- Flash of unauthorized content ถือเป็น bug

**Test Types:**
- UI tests สำหรับ sidebar rendering ต่อ role
- Route guard E2E tests: direct URL access ทุก restricted section
- Visual regression: sidebar highlight ถูก section
