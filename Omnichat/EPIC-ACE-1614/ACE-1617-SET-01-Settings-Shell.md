# STORY-SET-01: Settings Shell & Sidebar Navigation

**ID:** ACE-1617 | **Status:** In Progress | **Points:** 6 | **Sprint:** Sprint 4 (4/13 - 4/26)  
**Assignee:** Peerapat | **URL:** https://app.clickup.com/t/86d2hd9gn  
**Parent:** [ACE-1614 EPIC](ACE-1614-EPIC-Settings-Configuration.md)

## User Story

> As a logged-in user  
> I want a dedicated Settings area with clear navigation that shows only sections I have access to  
> so that I can find and configure workspace settings without confusion or unauthorized access.

## Description

Pure frontend story — build layout shell และ navigation ของ Settings area ทั้งหมด ทำก่อน SET-02 และ SET-03  
Content ของแต่ละ section จะ build ใน stories ถัดไป — story นี้ทำแค่ shell, routing, และ access control ของ navigation

## Role Permission Matrix

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
- Content area ของแต่ละ section เป็น **placeholder** รอ stories ถัดไป
- ไม่รวม content ของแต่ละ section (อยู่ใน SET-02, SET-03, SLA-01, NOTIF-04, NOTIF-05)

## Acceptance Criteria

**Settings area accessible from main navigation**
- Given: any logged-in user
- When: click Settings icon/menu
- Then: taken to Settings area, sidebar auto-selects first accessible section, no blank screen

**Admin sees all sidebar sections**
- Given: Admin opens Settings
- Then: all sections visible — Business Information, Members & Roles, Channels, SLA Rules, Notification Rules, My Preferences

**Supervisor sees only permitted sections**
- Given: Supervisor opens Settings
- Then: only SLA Rules, Notification Rules, My Preferences shown — others **not present in DOM at all**

**Agent sees only My Preferences**
- Given: Agent opens Settings
- Then: only My Preferences shown, all others absent

**Route guard blocks direct URL access**
- Given: Agent types `/settings/business-information` directly
- Then: redirected to 403, no restricted content shown even briefly

**Active section highlighted with breadcrumb**
- Given: user navigates to any Settings section
- Then: active section has visual indicator in sidebar, breadcrumb shows correct path

**Navigation persists across section switches**
- When: user clicks different section
- Then: content area updates without full page reload, sidebar selection updates
- And: no unsaved data warning unless form has unsaved changes

**Layout responsive at desktop width**
- Then: sidebar and content area render side by side without overflow or overlap

## UI/UX Notes

- Layout: sidebar + content area, full viewport height minus top nav
- Sidebar: group labels, section links with left-border indicator when active
- Active section: left border solid primary color + subtle bg highlight (confirm with art)
- Breadcrumb: `"Settings > [Section name]"` — small text, muted, above content area
- Content area: placeholder that renders section component from route

## Technical Notes

**Dependencies**
- RBAC-01: role & permission system ต้องมีก่อนเพื่อ filter sidebar sections
- RBAC-03: route guard pattern — reuse guard hook เดียวกัน
- Frontend router ต้องรองรับ nested routes สำหรับ `/settings/*` pattern

**Special focus**
- Hidden sections ต้อง **not in DOM** ไม่ใช่แค่ hidden ด้วย CSS (dev tools จะเห็นได้)
- Route guard ต้อง run ก่อน component render — ห้ามมี flash of content
- First accessible section ควร determine ฝั่ง server หรือ guard เพื่อหลีกเลี่ยง redirect loop

## QA / Test Considerations

**Primary flows**
- Admin เข้า Settings → เห็นทุก section → click แต่ละ section → breadcrumb ถูกต้อง
- Supervisor เข้า Settings → เห็นแค่ SLA + Notifications + My Preferences
- Agent เข้า Settings → เห็นแค่ My Preferences → auto-select ทันที

**Edge cases**
- Agent พิมพ์ `/settings/business-information` โดยตรง → redirect
- User สลับ section โดยไม่ save form → warn ถ้ามี unsaved changes
- Role ถูกเปลี่ยนระหว่าง session → sidebar update ถูกต้องหลัง refresh

**Business-critical must not break**
- ห้ามมี section ที่ไม่มีสิทธิ์ปรากฏใน DOM ไม่ว่ากรณีใด
- Flash of unauthorized content = bug ที่ต้องแก้

**Test types**
- UI tests: sidebar rendering ต่อ role
- Route guard E2E: direct URL access ทุก restricted section
- Visual regression: sidebar highlight ถูก section

## Subtasks

| Task | Name | Status |
|------|------|--------|
| [ACE-1626](https://app.clickup.com/t/86d2jgtnu) | Show menu by permission | To Do |
| [ACE-1679](https://app.clickup.com/t/86d2qjmdc) | Create breadcrumb component | To Do |
