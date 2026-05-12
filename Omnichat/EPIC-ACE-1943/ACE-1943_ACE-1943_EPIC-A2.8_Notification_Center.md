# EPIC-A2.8: Notification Center

**Status:** Backlog | **ClickUp:** [ACE-1943](https://app.clickup.com/t/86d2u3v89) | **Product:** Omni

## Epic Overview

Notification Center คือระบบที่แจ้งเตือน user แบบ real-time เมื่อมี event สำคัญเกิดขึ้นใน workspace เช่น มี conversation ใหม่, ถูก assign งาน, ถูก mention, หรือ SLA ใกล้ breach

เป้าหมายหลักคือให้แน่ใจว่า agent ไม่พลาด conversation สำคัญ โดยไม่ถูก noise รบกวนจนเกินไป

## Associated Stories

| Story | Name | Content |
|---|---|---|
| NOTIF-01 | Notification Infrastructure (Backend) | Data model, delivery service, WebSocket, event triggers |
| NOTIF-02 | Bell Icon & Unread Badge | Bell icon, unread count, real-time update |
| NOTIF-03 | Notification Panel & History | Dropdown panel, notification list, mark read, navigate |
| NOTIF-04 | Notification Rules Config | Settings page: workspace-level rules, recipients, thresholds |
| NOTIF-05 | Personal Notification Preferences | Personal mute/unmute per event ไม่กระทบ user คนอื่น |

**ACE IDs:**
1. ACE-1944: STORY-NOTIF-01 (Backlog)
2. ACE-1945: STORY-NOTIF-02 (Backlog)
3. ACE-1946: STORY-NOTIF-03 (Backlog)
4. ACE-1947: STORY-NOTIF-04 (Backlog)
5. ACE-1948: STORY-NOTIF-05 (Backlog)

## Dependency Chain

NOTIF-01 (backend infra) → NOTIF-02 (bell) → NOTIF-03 (panel) → NOTIF-04 (rules) → NOTIF-05 (personal prefs)

NOTIF-01 depends on: RBAC-01 (user role), SLA-02 (sla_due_at), SLA-04 (breach event)

## Event Catalog

### กลุ่มที่ 1: Conversation Events

| event_type | เกิดขึ้นเมื่อ | ใครได้รับ (default) |
|---|---|---|
| conversation_assigned | conversation ถูก assign ให้ฉัน (โดย agent/supervisor อื่น หรือ auto-assign) | Agent ที่ถูก assign |
| conversation_reassigned | conversation ที่เคย assigned ฉัน ถูก reassign ให้คนอื่น | Agent เดิมที่ถูก reassign ออก |
| conversation_unassigned | conversation ถูก unassign กลับมาเป็น "ไม่มีผู้รับ" | Supervisor, Admin |
| new_conversation | มี conversation ใหม่เข้ามาและยังไม่มีใคร assign | Supervisor, Admin |

### กลุ่มที่ 2: Message Events

| event_type | เกิดขึ้นเมื่อ | ใครได้รับ (default) |
|---|---|---|
| customer_replied | ลูกค้าส่งข้อความใน conversation ที่ assigned ฉัน | Agent ที่ assigned |
| mention | ถูก @mention ใน internal note ของ conversation | User ที่ถูก mention (เฉพาะคนนั้น) |

### กลุ่มที่ 3: SLA Events

| event_type | เกิดขึ้นเมื่อ | ใครได้รับ (default) |
|---|---|---|
| sla_due_soon | remaining time <= due_soon_threshold ของ conv ที่ assigned ฉัน | Agent ที่ assigned, Supervisor |
| sla_breached | sla_due_at ผ่านแล้วใน conv ที่ assigned ฉัน (personal) | Agent ที่ assigned |
| sla_breached_team | sla_due_at ผ่านแล้ว team-wide alert สำหรับทุก conv | Supervisor, Admin |

### กลุ่มที่ 4: System Events

| event_type | เกิดขึ้นเมื่อ | ใครได้รับ (default) |
|---|---|---|
| channel_error | Channel disconnect หรือ token หมดอายุ ทำให้รับ message ไม่ได้ | Admin เท่านั้น |

## Delivery Pipeline

ทุก notification ต้องผ่านขั้นตอนนี้ตามลำดับ:

1. Event เกิดขึ้น → NotificationService รับ event
2. ตรวจสอบว่า event type นี้ enabled ใน global rules (NOTIF-04) ไหม
3. ตรวจสอบ recipients list ของ event นั้น (NOTIF-04) ว่าใครควรได้รับ
4. สำหรับแต่ละ recipient → ตรวจสอบว่า user mute event นี้ไหม (NOTIF-05)
5. ถ้าผ่านทุก step → สร้าง notification record และ push ผ่าน WebSocket

> Note: ถ้า global rule disable event → ทุกคนไม่ได้รับ ไม่ว่า personal preference จะเป็นอย่างไร

## Notification Item Design Pattern

| Component | รายละเอียด |
|---|---|
| Event Icon | วงกลม colored ตาม event group: Assignment=น้ำเงิน, Message=เขียว, SLA=แดง/amber, System=เทา (confirm กับ art) |
| Actor Name | ชื่อคนที่ทำ action (bold) ถ้าเป็น system event ไม่มี actor |
| Verb + Object | คำกริยา + object ตาม event type |
| Channel Badge | pill เล็กบอก channel ต้นทางของ conversation (LINE, Shopee ฯลฯ) |
| Time | relative time right-align |
| Unread Dot | จุดแดง ด้านซ้าย แสดงเฉพาะ is_read = false |
| Background | Unread: พื้นหลังอ่อนกว่า / Read: พื้นขาวปกติ |
| Urgency border | SLA notifications: border-left สีแดง เพื่อบ่ง urgency |

## Text Templates

| event_type | Text ที่แสดงใน notification item |
|---|---|
| conversation_assigned | [ชื่อ actor] ได้ assign conversation "[ชื่อลูกค้า]" ให้คุณ · [channel badge] |
| conversation_reassigned | [ชื่อ actor] ได้ reassign conversation "[ชื่อลูกค้า]" ของคุณให้ [ชื่อ agent ใหม่] · [channel badge] |
| conversation_unassigned | Conversation "[ชื่อลูกค้า]" ถูก unassign ยังไม่มีผู้รับ · [channel badge] |
| new_conversation | Conversation "[ชื่อลูกค้า]" ใหม่เข้ามา ยังไม่มีผู้รับ · [channel badge] |
| customer_replied | "[ชื่อลูกค้า]" ส่งข้อความใหม่ใน "[preview text ย่อ]" · [channel badge] |
| mention | [ชื่อ actor] mention คุณใน note: "[preview text ย่อ]" · [channel badge] |
| sla_due_soon | SLA ใกล้ครบกำหนด "[ชื่อลูกค้า]" เหลือ [X] นาที · [channel badge] |
| sla_breached | SLA เกินกำหนด "[ชื่อลูกค้า]" เลยมา [X] นาทีแล้ว · [channel badge] |
| sla_breached_team | SLA เกินกำหนด [ชื่อ agent] มี [X] conversations รอการตอบกลับ |
| channel_error | Channel [channel name] มีปัญหา [error description ย่อ] |

## Relative Time Format

| ช่วงเวลา | Format | ตัวอย่าง |
|---|---|---|
| < 1 นาที | เมื่อสักครู่ | เมื่อสักครู่ |
| 1–59 นาที | X นาทีที่ผ่านมา | 5 นาทีที่ผ่านมา |
| 1–23 ชั่วโมง | X ชั่วโมงที่ผ่านมา | 2 ชั่วโมงที่ผ่านมา |
| วันนี้ (> 23h) | วันนี้ HH:MM น. | วันนี้ 09:30 น. |
| เมื่อวาน | เมื่อวาน HH:MM น. | เมื่อวาน 14:22 น. |
| 2–6 วันที่แล้ว | วัน DD MMM | อังคาร 25 มี.ค. |
| > 1 สัปดาห์ | DD MMM YYYY | 15 ก.พ. 2568 |

## Mention Deletion State Management

| กรณี | Behavior |
|---|---|
| ลบ @mention ออกจาก note (note ยังอยู่) | Notification ยังอยู่ใน bell: click ไปที่ note แต่ mention หายแล้ว แสดง note ตามปกติ ไม่มี error |
| ลบ note ทั้งอัน | Notification ยังอยู่ใน bell: click แล้วแสดง toast "โน้ตนี้ถูกลบแล้ว" ไม่ redirect หรือ crash |
| ลบ conversation ทั้งอัน (edge case) | Notification ยังอยู่ใน bell: click แล้วแสดง toast "Conversation นี้ไม่พบ" อยู่ที่ inbox |

> Note: Notification ไม่ถูกลบ retroactive เนื่องจากเป็น audit trail เบื้องต้นว่าเหตุการณ์เกิดขึ้น ระบบแค่ handle gracefully เมื่อ destination ไม่มีแล้ว
