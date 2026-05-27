# STORY-SLA-02: sla_status State Diagram

**Story:** ACE-1641 — SLA Timer Engine
**Parent Epic:** ACE-1618

> Referenced by: SLA-03 (display), SLA-04 (breach detection)

---

```mermaid
stateDiagram-v2
    [*] --> pending : conversation created

    pending --> disabled : SLA off on channel / outbound-first
    pending --> active : first inbound + SLA enabled (sla_due_at calculated)

    active --> due_soon : remaining time <= due_soon_minutes
    due_soon --> breached : sla_due_at <= NOW()
    active --> breached : sla_due_at <= NOW() (ถ้าไม่มี due_soon_threshold)

    active --> met : agent sends first outbound reply
    due_soon --> met : agent sends first outbound reply
    breached --> met : agent sends first outbound reply

    met --> active : customer follow-up (new SLA cycle, same bh_aware snapshot)

    note right of pending : รอ SLA config resolve — ไม่แสดง badge
    note right of disabled : ไม่แสดง badge
    note right of active : badge เขียว — countdown
    note right of due_soon : badge เหลือง — countdown
    note right of breached : badge แดง — "Overdue +Xm"
    note right of met : ไม่แสดง badge
```
