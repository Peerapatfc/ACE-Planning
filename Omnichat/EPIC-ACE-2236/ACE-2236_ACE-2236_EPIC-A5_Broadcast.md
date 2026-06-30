# EPIC-A5: Broadcast

**Status:** Backlog | **ClickUp:** [ACE-2236](https://app.clickup.com/t/86d318wjb) | **Product:** Omni

## Epic Overview

ปัจจุบันธุรกิจต้องการสื่อสารกับลูกค้าผ่าน LINE Official Account แบบ one-to-many เพื่อส่งโปรโมชั่น ประกาศข่าวสาร และ engagement campaigns แต่ยังไม่มีระบบ broadcast ที่ integrate กับ unified inbox ทำให้ต้องใช้ LINE Official Account Manager (OA Manager) แยกต่างหาก

EPIC-A5 จะสร้างระบบ broadcast ที่ integrate เต็มรูปแบบกับ unified inbox โดย Phase 1 focus ที่ LINE OA เป็นหลัก พร้อม targeting ด้วย tags, scheduling

## Goals

| Goal | Outcome/User Goal |
|---|---|
| Enable targeted mass communication | Admin/Supervisor สามารถส่ง broadcast messages หากลุ่มเป้าหมายที่เลือกผ่าน tags ได้อย่างรวดเร็ว |
| Provide operational visibility | Admin เห็น broadcast history และดู status ได้ |

## Associated Stories

| Story | ACE ID | Name |
|---|---|---|
| BC-01 | ACE-2294 | Create and Edit Broadcast |
| BC-02 | ACE-2295 | Audience Selection and Targeting |
| BC-03 | ACE-2457 | Send Broadcast |
| BC-04 | ACE-2297 | Test Broadcast |
| BC-05 | ACE-2503 | Broadcast list |
| BC-06 | ACE-2504 | Broadcast Detail |

## Scope

### In Scope (Phase 1)

**Broadcast Core Features:**
- Create, schedule, send broadcast campaigns (LINE only)
- Target audience selection ด้วย tags (include/exclude)
- Message composer รองรับ text + image
- Test broadcast (send to self/team)

**Scheduling & Execution:**
- Send immediately or schedule for future datetime
- Batch processing (500 recipients/batch, parallel 3 batches)

**History & Observability:**
- Broadcast history list

### Phase 2 (Out of Phase 1)
- Quick reply buttons
- Personalization variables: `{{customer_name}}`, `{{first_name}}`
- Template library (save, reuse, customize)
- Analytics & Reporting: delivery metrics, engagement metrics, response time tracking, failed recipients list
- Tab sending status (pending feedback from Phase 1)

### Out of Scope
- Opt-out/Opt-in mechanism
- Broadcast ไปช่องทางอื่นนอกจาก LINE (Facebook, Instagram, WhatsApp)
- Recurring/automated broadcasts (schedule once only)
- Conversion tracking (reply → order)
- Advanced audience segmentation (demographic, behavior filters นอกจาก tags)
- LINE Narrowcast API integration
- Rich media messages (video, audio, carousels)
- Broadcast templates sharing across workspaces
- Broadcast approval workflow
- Overage cost calculation and billing integration

## Success Metrics

| Metric | Definition | Target |
|---|---|---|
| Broadcast adoption rate | % of marketing campaigns ส่งผ่าน platform vs LINE OA Manager | 80%+ ภายใน 3 เดือน |
| Broadcast creation time | เวลาเฉลี่ยในการสร้างและส่ง broadcast | < 5 นาที |
| System uptime | Broadcast service availability | 99.5%+ |

## Dependencies

| Dependency | Why It Is Needed | Owner | Status | Needed By |
|---|---|---|---|---|
| Contact Model with Tags (ACE-1366) | Broadcast ต้องใช้ contact data และ tags สำหรับ targeting | Dev | ✅ Dev Testing | Start of BC |
| Tagging System (RA-05) | Broadcast ใช้ tags ในการ segment audience | Dev | ✅ Backlog | Start of BC |
| LINE Messaging Infrastructure | ส่ง broadcast messages ผ่าน LINE API | Dev | ✅ Production | Start of BC |

## Definition of Done

### Functionality
- Admin/Supervisor สามารถสร้าง broadcast (text + image) ได้
- Target audience ด้วย tags (include/exclude) แสดง estimated reach ถูกต้อง
- Test broadcast ส่งได้ (ไม่นับ quota)
- Schedule broadcast สำหรับ future datetime ได้
- Broadcast ส่งเป็น batches (500 recipients/batch) พร้อม progress tracking

### Permissions
- Agent: read only permission for broadcast features
- Admin/Supervisor เห็นและจัดการ broadcasts ทั้งหมดได้
