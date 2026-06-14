# SLA-04: Breach Detection & Auto-tag — State Diagram

**Story:** ACE-1643  
**Epic:** ACE-1618 SLA Management

---

## Diagram 1: SLA Conversation Status States

**ว่าด้วย:** `sla_status` บน conversation เปลี่ยนยังไงตลอด lifecycle

| State | ความหมาย |
|-------|----------|
| `active` | SLA กำลังนับอยู่ ยังไม่มีใครตอบ |
| `due_soon` | ใกล้หมดเวลา (warning zone) |
| `met` | Agent ตอบทัน ✓ |
| `breached` | หมดเวลาแล้ว ไม่มีใครตอบ ✗ |

```mermaid
stateDiagram-v2
    [*] --> active : customer sends message\n(new cycle starts)

    active --> due_soon : sla_due_at - threshold <= NOW()\n(SLA-02 warning job)

    active --> met : agent replies before sla_due_at\n→ tag: sla_met [is_system]\n→ record: sla_event { type=met }

    due_soon --> met : agent replies before sla_due_at\n→ tag: sla_met [is_system]\n→ record: sla_event { type=met }

    active --> breached : breach job detects sla_due_at <= NOW()\n→ tag: sla_breached [is_system]\n→ record: sla_event { type=breached }

    due_soon --> breached : breach job detects sla_due_at <= NOW()\n→ tag: sla_breached [is_system]\n→ record: sla_event { type=breached }

    breached --> breached : agent replies late\n(sla_breached tag stays — immutable)\nno SLA action

    met --> active : customer sends new message\n(new cycle — cycle_number++)

    breached --> active : customer sends new message\n(new cycle — cycle_number++)

    met --> [*] : conversation resolved
    breached --> [*] : conversation resolved
```

**ตัวอย่าง Happy Path:**
```
10:00  ลูกค้าทัก        → active
10:50  ใกล้หมดเวลา      → due_soon
10:55  Agent ตอบ        → met ✓
```

**ตัวอย่าง Breach Path:**
```
10:00  ลูกค้าทัก        → active
10:50  ใกล้หมดเวลา      → due_soon
11:01  job วิ่ง ไม่มีใครตอบ → breached ✗
11:30  Agent ตอบสาย     → ยังคง breached (ไม่เปลี่ยน)
```

> `met` และ `breached` ไม่ใช่ terminal — ถ้าลูกค้าทักใหม่จะวนกลับ `active` (cycle ใหม่)

---

## Diagram 2: System Tag Lifecycle

**ว่าด้วย:** tag `sla_met` / `sla_breached` ถูก add ได้ยังไง และลบไม่ได้เพราะอะไร

```mermaid
stateDiagram-v2
    [*] --> no_tag : conversation created

    no_tag --> sla_met_tagged : agent replies before deadline\n(real-time, from Message Service)

    no_tag --> sla_breached_tagged : breach job runs\n(within 1 min of deadline)

    sla_met_tagged --> sla_met_tagged : DELETE attempt\n→ 403 Forbidden (immutable)

    sla_breached_tagged --> sla_breached_tagged : DELETE attempt\n→ 403 Forbidden (immutable)

    sla_breached_tagged --> both_tagged : next cycle → agent replies on time\n→ sla_met added for new cycle

    both_tagged --> both_tagged : any DELETE attempt\n→ 403 Forbidden
```

**ตัวอย่าง:**
```
Cycle 1: agent ตอบทัน
  → tags: [sla_met]

Cycle 2: ไม่มีใครตอบ
  → tags: [sla_met, sla_breached]

Admin พยายามลบ sla_breached → 403 "system tag ไม่สามารถลบได้"
```

> ล็อคไว้เป็น audit trail — supervisor ต้องรู้ว่า conversation เคย breach แม้ agent จะตอบทีหลัง

---

## Diagram 3: Multi-cycle State Transitions

**ว่าด้วย:** 1 conversation มีหลาย SLA cycle และแต่ละ cycle independent กัน — ผลของ cycle หนึ่งไม่ทับอีก cycle

```mermaid
stateDiagram-v2
    state "Cycle 1" as c1 {
        [*] --> c1_active
        c1_active --> c1_met : agent replies on time\n→ sla_met [cycle=1]
        c1_met --> [*]
    }

    state "Cycle 2" as c2 {
        [*] --> c2_active
        c2_active --> c2_due_soon : warning threshold hit
        c2_due_soon --> c2_breached : deadline passed\n→ sla_breached [cycle=2]
        c2_breached --> [*]
    }

    c1 --> c2 : customer sends new message\n(cycle_number = 2, sla resets)

    note right of c1
        sla_met tag: immutable
        sla_event cycle=1: preserved
    end note

    note right of c2
        sla_breached tag: immutable
        sla_event cycle=2: independent record
        UI badge: shows cycle 2 status
    end note
```

**ตัวอย่าง:**
```
Cycle 1 (เช้า):
  10:00  ลูกค้าทัก → sla_due_at 11:00
  10:45  Agent ตอบ → sla_met [cycle=1]

Cycle 2 (บ่าย):
  14:00  ลูกค้าทักใหม่ → sla_due_at 15:00
  (ไม่มีใครตอบ)     → sla_breached [cycle=2]

Inbox badge แสดง:  "Overdue +1m"         ← cycle 2 (latest)
History เก็บ:      cycle 1 met ✓          ← ยังอยู่ครบ
                   cycle 2 breached ✗     ← ยังอยู่ครบ
```

> แยก record ต่อ cycle เพื่อ analytics — รู้ได้ว่าแต่ละครั้งที่ลูกค้าทัก team ตอบทันหรือเปล่า

---

## Diagram 4: Breach Job Decision Flow

**ว่าด้วย:** job ที่วิ่งทุก 1 นาทีทำอะไรบ้าง step by step

```mermaid
stateDiagram-v2
    [*] --> scan : cron triggers (every 1 min)

    scan --> no_breach : 0 rows found\n(sla_due_at <= NOW AND status IN active/due_soon)

    scan --> process : N rows found

    no_breach --> log_zero : log "0 processed"
    log_zero --> [*]

    process --> update_status : UPDATE sla_status → breached

    update_status --> insert_tag : INSERT sla_breached tag\n(ON CONFLICT DO NOTHING)

    insert_tag --> insert_event : INSERT sla_event { breached }\n(ON CONFLICT DO NOTHING)

    insert_event --> emit_event : EMIT breach_detected\n→ Epic 2.8 notification

    emit_event --> next_row : log conversation_id + cycle

    next_row --> process : more rows
    next_row --> log_total : all rows done

    log_total --> [*] : log total count processed
```

**ตัวอย่าง job run ตอน 15:01:**
```
Scan พบ 3 conversations ที่ deadline ผ่านแล้ว

conv A: update breached → add tag → emit event  ✓  (new breach)
conv B: update breached → add tag → emit event  ✓  (new breach)
conv C: tag มีอยู่แล้ว (job รอบก่อน insert ไป)
        ON CONFLICT DO NOTHING → ข้ามไป ไม่ duplicate ✓

Log: "processed 3 conversations"
```

> `ON CONFLICT DO NOTHING` คือ idempotency guard — job crash แล้ว restart ก็ไม่สร้าง tag ซ้ำ
