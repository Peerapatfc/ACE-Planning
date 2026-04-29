# EPIC-A2.6: Settings & Configuration

**ID:** ACE-1614 | **Status:** To Do | **Product:** Omni  
**URL:** https://app.clickup.com/t/86d2hd9ef

## Overview

Settings คือ area ที่รวม config ทั้งหมดที่ตั้งครั้งเดียวแล้วมีผลกับทั้ง workspace

## Stories

| Story | Name | Depends on | Points | Status | Assignee |
|-------|------|-----------|--------|--------|----------|
| [SETTINGS-01 (ACE-1617)](ACE-1617-SET-01-Settings-Shell.md) | Settings Shell & Sidebar Navigation | RBAC-01 | 6 | In Progress | Peerapat |
| [SETTINGS-02 (ACE-1615)](ACE-1615-SET-02-Business-Information.md) | Business Information & Business Hours | SET-01 | 6 | In Progress | Tanawin (Toy) |
| [SETTINGS-03 (ACE-1616)](ACE-1616-SET-03-Members-Roles.md) | Members & Roles Page + Edit User + Work Shift | SET-01, SET-02, RBAC-02 | 6 | In Progress | griangsak |

## Subtasks

### SETTINGS-01 (ACE-1617) — Settings Shell & Sidebar Navigation

| Task | Name | Status |
|------|------|--------|
| ACE-1626 | Show menu by permission | To Do |
| ACE-1679 | Create breadcrumb component | To Do |

### SETTINGS-02 (ACE-1615) — Business Information & Business Hours

| Task | Name | Status |
|------|------|--------|
| ACE-1627 | Design/Create config db business hours | To Do |
| ACE-1685 | Generate Store ID when Create Tenant | In Progress |
| ACE-1680 | Create business information component | In Progress |
| ACE-1681 | Create business hours component | To Do |
| ACE-1682 | Build api | In Progress |
| ACE-1683 | Design diagrams | In Progress |
| ACE-1684 | API Table | To Do |

### SETTINGS-03 (ACE-1616) — Members & Roles Page + Edit User + Work Shift

| Task | Name | Status |
|------|------|--------|
| ACE-1628 | Modify member list page | To Do |
| ACE-1690 | Build edit member role and business hours | To Do |
| ACE-1686 | Design/build api | To Do |
| ACE-1687 | Diagrams | To Do |
| ACE-1688 | API Table | To Do |

## Dependency Chain

```
SETTINGS-01 → SETTINGS-02 → SETTINGS-03
```

SETTINGS-02 (Business Hours) ต้องเสร็จก่อน SETTINGS-03 เพราะ "User's work shift" มี toggle "Same as business hours" ที่อ่านค่าจาก SETTINGS-02 โดยตรง
