# EPIC-A2.5: RBAC

## Epic Overview

RBAC คือ foundation ที่ทุก feature บน platform อ้างอิง ก่อนหน้านี้ platform มีแค่ single user ไม่มีระบบ role เพราะมีแค่ tenant เดียว เมื่อ team เริ่มขยาย จำเป็นต้องมีระบบควบคุมว่า "ใครทำอะไรได้บ้าง" เพื่อ:
- ป้องกันการ access ข้อมูลที่ไม่ควร เช่น Agent เห็น config ทั้งหมดของระบบ
- Audit trail ที่ชัดเจน รู้ว่าใครตอบ conversation ไหน ใคร config อะไร
- รองรับ team ที่มีหลายคน Admin, Supervisor, Agent มีหน้าที่ต่างกัน

## Associated Stories

| Story | Name | Content |
|---|---|---|
| RBAC-01 | Permission Model & API Enforcement | Backend foundation: role enum, permission rules, API 403 |
| RBAC-02 | Member Management | Invite, เปลี่ยน role, remove member, Admin protection rules |
| RBAC-03 | Frontend Permission Enforcement | Route guard, UI visibility, reply permission, 403 page |

**ACE IDs:**
1. ACE-1611: STORY-RBAC-01 (Backlog)
2. ACE-1612: STORY-RBAC-02 (Backlog)
3. ACE-1613: STORY-RBAC-03 (Backlog)

## Roles ทั้ง 3 ที่ MVP รองรับ

| Role | Description | Responsibility & Scope |
|---|---|---|
| Admin | เจ้าของ / ผู้ดูแลระบบ | Config ทุกอย่าง, manage members, manage channels, ดูได้ทุกอย่าง (สร้างโดยอัตโนมัติเมื่อ workspace ถูกสร้าง) |
| Supervisor | หัวหน้าทีม CS | ดู inbox ทั้งหมด, assign/reassign conversation, config SLA และ notification, ดู report ของทีม |
| Agent | CS staff | ดู inbox ทั้งหมด, ตอบ conversation ได้ทุก conversation, เปลี่ยน status |

> **Note:** First Admin = คนที่สร้าง workspace จะได้รับ Admin role อัตโนมัติ ไม่ต้องถูก invite

## Permission Matrix

| Permission | Admin | Supervisor | Agent |
|---|---|---|---|
| ดู conversation ทั้งหมด | ✅ | ✅ | ✅ |
| ตอบ conversation ทุก conversation | ✅ | ✅ | ✅ |
| Assign / Reassign conversation | ✅ | ✅ | ❌ |
| เปลี่ยน status conversation | ✅ | ✅ | ✅ |
| Config SLA rules | ✅ | ✅ | ❌ |
| Config notification rules | ✅ | ✅ | ❌ |
| ตั้งค่า personal notification preferences | ✅ | ✅ | ✅ |
| ดู team report / analytics (later) | ✅ | ✅ | ❌ |
| Invite / Remove member | ✅ | ❌ | ❌ |
| เปลี่ยน role ของ member | ✅ | ❌ | ❌ |
| Manage channels | ✅ | ❌ | ❌ |
| Access Settings > Workspace | ✅ | ❌ | ❌ |
| Access Settings > Channels | ✅ | ❌ | ❌ |
| Access Settings > SLA | ✅ | ✅ | ❌ |
| Access Settings > Notification Rules | ✅ | ✅ | ❌ |
| Access Settings > My Preferences | ✅ | ✅ | ✅ |

## Admin Protection Rules

| Scenario | Decision |
|---|---|
| Admin down role ตัวเอง | ได้ ถ้ามี Admin คนอื่นที่ active อยู่อย่างน้อย 1 คน |
| Admin down role Admin อีกคน | ได้ ถ้ายังมี Admin เหลืออย่างน้อย 1 คนหลังเปลี่ยน |
| Admin remove Admin อีกคน | ได้ ถ้ายังมี Admin เหลืออย่างน้อย 1 คนหลัง remove |
| Workspace มี Admin เหลือ 1 คน | Admin คนนั้นไม่สามารถ down role ตัวเองหรือถูก remove ได้ |
| First Admin | คนที่สร้าง workspace ได้ Admin role อัตโนมัติ handle ใน onboarding flow |
| Invitation expiry | 7 วัน นับจากวันที่ส่ง invitation ต้อง Resend ออก link ใหม่และ reset expiry |
