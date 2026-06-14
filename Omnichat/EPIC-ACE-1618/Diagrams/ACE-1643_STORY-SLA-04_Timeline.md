# SLA-04: Multi-cycle Timeline Example

**Story:** ACE-1643 — Breach Detection & Auto-tag  
**Service:** `omnichat-service`

> Concrete walkthrough — cycle 1 (met ✓) → cycle 2 (breached ✗)  
> Infrastructure details (cache, lock, error paths) → [ACE-1643_STORY-SLA-04_Sequence_Diagram.md](ACE-1643_STORY-SLA-04_Sequence_Diagram.md)

---

```mermaid
sequenceDiagram
    autonumber
    actor Customer
    actor Agent
    participant Conv as ConversationsService<br/>(omnichat-service)
    participant Job as BreachDetectionJob<br/>@Cron('*/1 * * * *')<br/>(omnichat-service)
    participant DB as Database
    participant WS as WebSocket Server

    Note over Customer,WS: **Pre-conditions**<br/>SLA เปิดอยู่สำหรับ channel นี้ — first_response_minutes กำหนดไว้ใน ChannelSlaConfig<br/>แสดง 2 cycle: cycle 1 met ✓, cycle 2 breached ✗

    Note over Customer,WS: ── Cycle 1 (10:00–10:45) ──────────────────────────────

    Customer->>Conv: inbound message (10:00)
    Conv->>DB: INSERT conversations { sla_status='pending', ... }

    Note over Conv: GET omnichat:sla:config → bh_aware=true, first_response_minutes=60<br/>GET omnichat:bh:schedule → timezone, days[]<br/>bh_aware=true → next_bh_open(10:00, days) + 60min = 11:00

    Note over Conv,DB: BEGIN TRANSACTION
    Conv->>DB: INSERT message (inbound)
    Conv->>DB: UPDATE conversations SET<br/>sla_status='active', sla_due_at=11:00, sla_bh_aware=true,<br/>cycle_number=1, sla_first_inbound_at=10:00, sla_met_at=null
    Note over Conv,DB: COMMIT

    Conv->>WS: conversation:updated { conv_id, sla_status: "active", sla_due_at: "11:00" }
    Note over WS: FE เริ่ม countdown timer ทันที

    Agent->>Conv: outbound reply (10:45)
    Note over Conv: reply_at(10:45) < sla_due_at(11:00) → SLA met ✓

    Note over Conv,DB: BEGIN TRANSACTION
    Conv->>DB: UPDATE conversations SET sla_status='met', sla_met_at=10:45, sla_due_at=null
    Conv->>DB: INSERT conversation_sla_events<br/>{ cycle=1, type='met', inbound_at=10:00, sla_due_at=11:00,<br/>resolved_at=10:45, response_time_sec=2700 } ON CONFLICT DO NOTHING
    Conv->>DB: INSERT conversation_tags { tag_id=SLA_MET_TAG, is_system=true } ON CONFLICT DO NOTHING
    Note over Conv,DB: COMMIT

    Conv->>WS: conversation:updated { conv_id, sla_status: "met", sla_due_at: null }
    Note over WS: badge หาย + ออกจาก Overdue list ทันที

    Note over Customer,WS: ── Cycle 2 (14:00 — no reply) ─────────────────────────

    Customer->>Conv: new inbound message (14:00)

    Note over Conv: GET omnichat:sla:config → bh_aware=true, first_response_minutes=60<br/>bh_aware อ่านจาก config ทุก cycle — admin เปลี่ยน → DEL+SET cache ทันที → cycle ใหม่ได้ค่าใหม่<br/>GET omnichat:bh:schedule → timezone, days[]<br/>bh_aware=true → next_bh_open(14:00, days) + 60min = 15:00

    Note over Conv,DB: BEGIN TRANSACTION
    Conv->>DB: INSERT message (inbound)
    Conv->>DB: UPDATE conversations SET<br/>sla_status='active', sla_due_at=15:00, sla_bh_aware=true,<br/>cycle_number=cycle_number+1, sla_first_inbound_at=14:00, sla_met_at=null
    Note over Conv,DB: COMMIT

    Conv->>WS: conversation:updated { conv_id, sla_status: "active", sla_due_at: "15:00" }
    Note over WS: FE restart countdown timer จาก sla_due_at ใหม่

    Note over Job: 15:01 — cron fires

    Job->>DB: SELECT id, cycle_number, sla_due_at, sla_first_inbound_at FROM conversations<br/>WHERE sla_due_at <= NOW() AND sla_status IN ('active','due_soon')
    Note over Job: พบ conv นี้ — sla_due_at(15:00) <= NOW(15:01) ✓

    Note over Job,DB: BEGIN TRANSACTION
    Job->>DB: UPDATE conversations SET sla_status='breached'
    Job->>DB: INSERT conversation_tags { tag_id=SLA_BREACHED_TAG, is_system=true } ON CONFLICT DO NOTHING
    Job->>DB: INSERT conversation_sla_events<br/>{ cycle=2, type='breached', inbound_at=sla_first_inbound_at,<br/>sla_due_at=15:00, resolved_at=15:01 } ON CONFLICT DO NOTHING
    Note over Job,DB: COMMIT

    Job->>WS: conversation:sla_breached { conversation_id }
    Note over WS: badge เปลี่ยนเป็นสีแดง + ขึ้น Overdue list

    Note over DB,WS: DB audit trail: cycle 1 → sla_met ✓ / cycle 2 → sla_breached ✗<br/>sla_met tag + sla_breached tag ทั้งคู่ immutable (is_system=true)
```
