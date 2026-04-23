# STORY-SET-01: Settings Shell & Sidebar Navigation

**ID:** ACE-1617 | **Status:** To Do | **Points:** 6  
**Assignee:** Peerapat Pongnipakorn | **Sprint:** Sprint 4 (4/13 - 4/26)  
**URL:** https://app.clickup.com/t/86d2hd9gn  
**Depends on:** RBAC-01

## User Story

As a logged-in user  
I want a dedicated Settings area with clear navigation that shows only sections I have access to  
so that I can find and configure workspace settings without confusion or unauthorized access.

## Description

Story นี้ build layout shell และ navigation ของ Settings area ทั้งหมด เป็น pure frontend story ที่ทำก่อน SET-02 และ SET-03  
Content ของแต่ละ section จะ build ใน stories ถัดไป — story นี้ทำแค่ shell, routing, และ access control ของ navigation

## Role Access Matrix

| Settings Section | Admin | Supervisor | Agent |
|-----------------|-------|-----------|-------|
| Business Information | ✅ | ❌ | ❌ |
| Members & Roles | ✅ | ❌ | ❌ |
| Channels (existing) | ✅ | ❌ | ❌ |
| SLA Rules (via SLA-01) | ✅ | ✅ | ❌ |
| Notification Rules (via NOTIF-04) | ✅ | ✅ | ❌ |
| My Preferences (via NOTIF-05) | ✅ | ✅ | ✅ |

## Scope

- Settings layout: sidebar navigation (left) + content area (right)
- Sidebar แสดงเฉพาะ section ที่ role มีสิทธิ์ — section ที่ไม่มีสิทธิ์ **hidden** ไม่ใช่ greyed out
- Active section highlighted ใน sidebar
- Breadcrumb ด้านบน content area: `Settings > Business Information`
- Auto-redirect ไป first accessible section เมื่อเข้า `/settings` โดยตรง
- Route guard: direct URL access ไป section ที่ไม่มีสิทธิ์ → redirect
- Content area ของแต่ละ section เป็น placeholder รอ stories ถัดไป
- ไม่รวม content ของแต่ละ section (อยู่ใน SET-02, SET-03, SLA-01, NOTIF-04, NOTIF-05)

## Acceptance Criteria

### Settings area is accessible from main navigation
- Given any logged-in user clicks the Settings icon/menu item
- Then they go to Settings area, sidebar auto-selects first accessible section, no blank screen shown

### Admin sees all sidebar sections
- Given Admin opens Settings → all sections visible

### Supervisor sees only permitted sections
- Given Supervisor opens Settings → only SLA Rules, Notification Rules, My Preferences shown (others not in DOM)

### Agent sees only My Preferences
- Given Agent opens Settings → only My Preferences shown

### Route guard blocks direct URL access to unauthorized sections
- Given Agent types `/settings/business-information` → redirected to 403, no flash of content

### Active section highlighted with breadcrumb
- Active section has visual indicator + breadcrumb shows `Settings > [Section name]`

### Navigation persists across section switches
- Click different section → content area updates without full page reload, no unsaved data warning unless form dirty

### Layout is responsive
- Sidebar + content area render side by side at standard desktop width

## UI/UX Notes

- Layout: sidebar + content area, full viewport height minus top nav
- Sidebar: group labels, section links with left-border indicator when active
- Active section: left border solid primary color + bg highlight subtle
- Breadcrumb: `Settings > [Section name]` ด้านบน content area, text เล็ก muted
- Content area: placeholder renders section component ตาม route

## Technical Notes

**Dependencies:**
- RBAC-01 role/permission system ต้องมีก่อน เพื่อ filter sidebar sections
- RBAC-03 route guard pattern — reuse guard hook เดิม
- Frontend router ต้องรองรับ nested routes `/settings/*`

**Special focus:**
- Hidden sections ต้อง **not in DOM** ไม่ใช่แค่ hidden ด้วย CSS (dev tools จะเห็นได้)
- Route guard ต้อง run ก่อน component render — ห้ามมี flash of content
- First accessible section ควร determine ฝั่ง server/guard เพื่อหลีกเลี่ยง redirect loop

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
- UI tests: sidebar rendering ต่อ role
- Route guard E2E tests: direct URL access ทุก restricted section
- Visual regression: sidebar highlight ถูก section

## Subtasks

| ID | Name | Points |
|----|------|--------|
| ACE-1626 | Show menu by permission | 1 |
| ACE-1679 | Create breadcrumb component | - |
