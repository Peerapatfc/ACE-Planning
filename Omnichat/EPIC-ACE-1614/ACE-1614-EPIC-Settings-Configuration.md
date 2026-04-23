# EPIC-A2.6: Settings & Configuration

**ID:** ACE-1614 | **Status:** To Do | **Product:** Omni  
**URL:** https://app.clickup.com/t/86d2hd9ef

## Overview

Settings คือ area ที่รวม config ทั้งหมดที่ตั้งครั้งเดียวแล้วมีผลกับทั้ง workspace

## Stories

| Story | Name | Depends on | Points |
|-------|------|-----------|--------|
| SETTINGS-01 (ACE-1617) | Settings Shell & Sidebar Navigation | RBAC-01 | 6 |
| SETTINGS-02 (ACE-1615) | Business Information & Business Hours | SET-01 | 6 |
| SETTINGS-03 (ACE-1616) | Members & Roles Page + Edit User + Work Shift | SET-01, SET-02, RBAC-02 | 6 |

## Dependency Chain

```
SETTINGS-01 → SETTINGS-02 → SETTINGS-03
```

SETTINGS-02 (Business Hours) ต้องเสร็จก่อน SETTINGS-03 เพราะ "User's work shift" มี toggle "Same as business hours" ที่อ่านค่าจาก SETTINGS-02 โดยตรง
