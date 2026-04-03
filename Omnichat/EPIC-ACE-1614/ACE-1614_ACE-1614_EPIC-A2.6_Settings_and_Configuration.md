# EPIC-A2.6: Settings & Configuration

## Epic Overview

Settings คือ area ที่รวม config ทั้งหมดที่ตั้งครั้งเดียวแล้วมีผลกับทั้ง workspace โดยแบ่งออกเป็น 3 stories ตาม dependency chain ดังนี้

## Associated Stories

| Story | Name | Depends On |
|---|---|---|
| SETTINGS-01 | Settings Shell & Sidebar Navigation | RBAC-01 |
| SETTINGS-02 | Business Information & Business Hours | SET-01 |
| SETTINGS-03 | Members & Roles Page + Edit User + Work Shift | SET-01, SET-02, RBAC-02 |

**ACE IDs:**
1. ACE-1617: STORY-SET-01 (Backlog)
2. ACE-1615: STORY-SET-02 (Backlog)
3. ACE-1616: STORY-SET-03 (Backlog)

## Dependency Chain

SETTINGS-02 (Business Hours) ต้องเสร็จก่อน SETTINGS-03 เพราะ "User's work shift" มี toggle "Same as business hours" ที่อ่านค่าจาก SETTINGS-02 โดยตรง
