# SLA-04: Breach Detection & Auto-tag — High Level Flow

**Story:** ACE-1643  
**Epic:** ACE-1618 SLA Management

---

## Flow 1: `sla_met` — Real-time (Agent Reply Path)

```
Agent sends outbound message
        │
        ▼
SLA-02 logic: agent reply handler
        │
        ├─ Has sla_status = active / due_soon?
        │         │
        │        YES
        │         ▼
        │   reply_at < sla_due_at?
        │    ├── YES → insert sla_event { cycle_N, type=met, response_time_sec }
        │    │         insert conversation_tag { sla_met, is_system=true }  ← idempotent
        │    │         update sla_status → met  (latest cycle)
        │    │         [emit event for analytics]
        │    │
        │    └── NO  → agent replied late — no SLA action (breach recorded by job)
        │
        └─ sla_status already breached? → skip — no SLA action
```

---

## Flow 2: `sla_breached` — Background Job (Every 1 min)

```
Cron Job triggers (every 1 min)
        │
        ▼
Query: conversations WHERE
  sla_due_at <= NOW()
  AND sla_status IN ('active', 'due_soon')
        │
        ├── 0 rows → log "0 processed", exit
        │
        └── N rows → for each conversation:
                │
                ▼
         UPDATE sla_status → 'breached'
                │
                ▼
         INSERT conversation_tag
           (sla_breached, is_system=true)
           ON CONFLICT DO NOTHING   ← idempotency
                │
                ▼
         INSERT conversation_sla_events
           (cycle_N, type=breached, resolved_at=NOW())
           ON CONFLICT DO NOTHING
           -- elapsed_breach_time = resolved_at - sla_due_at  ← for AC13 analytics
                │
                ▼
         EMIT breach_detected event
           → notification handler (Epic 2.8, out of scope here)
                │
                ▼
         Log: processed conversation_id + cycle_number

        After loop → log total count processed
```

---

## Flow 3: System Tag Protection

```
User/API calls DELETE /tags/{tag_id}
        │
        ▼
Lookup tag → is_system = true?
        │
       YES → return 403 "system tag ไม่สามารถลบได้"
        │
       NO  → delete allowed (user tag)
```

---

## Flow 4: Multi-cycle Timeline

```
t=10:00  Customer sends message
          → sla_first_inbound_at = 10:00
          → sla_due_at = 11:00
          → sla_status = active
          → cycle_number = 1

t=10:45  Agent replies
          → reply_at < sla_due_at ✓
          → tag: sla_met [cycle=1]
          → sla_event: { cycle=1, met, response_time=45min }
          → sla_status = met

t=14:00  Customer sends new message
          → NEW cycle triggered (SLA-02 logic)
          → sla_due_at = 15:00
          → sla_status = active
          → cycle_number = 2

t=15:01  Breach job runs
          → sla_due_at(15:00) <= NOW(15:01) ✓
          → sla_status → breached
          → tag: sla_breached [cycle=2]
          → sla_event: { cycle=2, breached, resolved_at=15:01 }
          → emit breach event

t=15:30  Agent replies (late)
          → sla_breached tag stays (immutable)
          → no SLA action
```

---

## Component Interaction Map

```
┌─────────────────┐      agent reply      ┌──────────────────┐
│  Agent Client   │ ─────────────────────▶│  Message Service │
└─────────────────┘                        │  (SLA-02 logic)  │
                                           └────────┬─────────┘
                                                    │ real-time
                                                    ▼
                                           ┌──────────────────┐
                                           │  SLA Tag Service  │
                                           │  - add sla_met   │
                                           │  - record event   │
                                           └────────┬─────────┘
                                                    │
                                                    ▼
                                           ┌──────────────────┐
┌─────────────────┐    every 1 min        │   PostgreSQL DB   │
│  Breach Job     │ ─────────────────────▶│  conversations    │
│  (Cron/Worker)  │                        │  conversation_tags│
└─────────────────┘                        │  sla_events       │
        │                                  └──────────────────┘
        │ emit
        ▼
┌─────────────────┐
│  Breach Event   │ ──── (Epic 2.8) ──── Notification Handler
└─────────────────┘
```

---

## Key Rules Summary

| Rule | Where enforced |
|------|---------------|
| `sla_met` = real-time on agent reply | Message Service (SLA-02 hook) |
| `sla_breached` = job within 1 min | Cron job |
| Idempotent insert | `ON CONFLICT DO NOTHING` |
| System tag immutable | API layer 403 + DB constraint |
| Multi-cycle independent records | `cycle_number` FK on sla_events |
| Breach tag survives late reply | tag immutable — agent reply ไม่แตะ tag |
| `response_time_sec` formula | `reply_at - sla_first_inbound_at` (recorded on `sla_met` only) |
| `elapsed_breach_time` formula | `resolved_at - sla_due_at` (from sla_event, for breach-rate analytics) |
