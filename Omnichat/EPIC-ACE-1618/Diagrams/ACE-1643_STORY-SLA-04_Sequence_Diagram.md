# SLA-04: Sequence Diagrams

**Story:** ACE-1643 — Breach Detection & Auto-tag  
**Service:** `omnichat-service`

---

## SD-01: Agent Reply — SLA Outcome Handler

```mermaid
sequenceDiagram
    autonumber
    actor Agent
    participant GW as api-gateway
    participant Conv as ConversationsService<br/>(omnichat-service)
    participant DB as Database
    participant MS as Meilisearch
    participant WS as WebSocket Server

    Note over Agent,WS: **Pre-conditions**<br/>Agent ส่ง reply — sender_type, sla_status, และ timing กำหนดว่าจะเกิดอะไรขึ้น

    Agent->>GW: POST /conversations/{id}/messages
    GW->>Conv: TCP send('send_message', payload)

    alt sender_type = system | bot
        Note over Conv: skip — not a human agent reply
        Conv-->>GW: message saved
        GW-->>Agent: 201 Created
    else sender_type = agent
        Conv->>DB: SELECT sla_status, sla_due_at, cycle_number, sla_first_inbound_at
        DB-->>Conv: { sla_status, sla_due_at, cycle_number, sla_first_inbound_at }

        alt sla_status = active | due_soon  AND  reply_at < sla_due_at
            Note over Conv: Agent ตอบก่อน deadline → SLA met
            Note over Conv,DB: BEGIN TRANSACTION
            Conv->>DB: UPDATE conversations SET sla_status='met', sla_met_at=NOW(), sla_due_at=null
            Conv->>DB: INSERT conversation_sla_events<br/>{ cycle_N, type='met', inbound_at=sla_first_inbound_at,<br/>sla_due_at, resolved_at=NOW(), response_time_sec=(resolved_at-inbound_at) }<br/>ON CONFLICT DO NOTHING
            Conv->>DB: INSERT conversation_tags<br/>{ tag_id=SLA_MET_TAG, is_system=true }<br/>ON CONFLICT DO NOTHING
            alt transaction success
                Note over Conv,DB: COMMIT
                Conv->>MS: sync conversation (add sla_met tag)
                Conv->>WS: conversation:updated<br/>{ conv_id, sla_status: "met", sla_due_at: null }
                Note over WS: push ให้ทุก agent ที่ watch inbox เดียวกัน<br/>badge หาย + ออกจาก Overdue list ทันที
                Conv-->>GW: message saved
                GW-->>Agent: 201 Created
            else transaction failed
                Note over Conv,DB: ROLLBACK
                Conv-->>GW: throw InternalServerErrorException
                GW-->>Agent: 500 Internal Server Error
            end
        else sla_status = breached  OR  reply_at >= sla_due_at
            Note over Conv: Agent ตอบสาย หรือ breach แล้ว → ไม่ทำ SLA action<br/>sla_breached tag set โดย BreachJob แล้ว — ไม่แตะ
            Conv-->>GW: message saved
            GW-->>Agent: 201 Created
        else sla_status = pending | disabled
            Note over Conv: pending = race condition (inbound เข้าแล้วแต่ SLA calculation ยังไม่จบ)<br/>disabled = SLA ไม่ได้ enable สำหรับ channel นี้ → mark disabled
            Conv->>DB: UPDATE conversations SET sla_status='disabled'
            Conv-->>GW: message saved
            GW-->>Agent: 201 Created
        end
    end
```

---

## SD-02: Breach Detection Job — due_soon & breach scan (@Cron 1 min)

> Redis ใช้ **Distributed lock** — กัน race condition ถ้า omnichat-service scale หลาย instance

```mermaid
sequenceDiagram
    autonumber
    participant Job as BreachDetectionJob<br/>@Cron('*/1 * * * *')<br/>(omnichat-service)
    participant Redis as Redis
    participant DB as Database
    participant MS as Meilisearch
    participant WS as WebSocket Server
    Note over Job,WS: **Pre-conditions**<br/>มี conversations ที่ sla_due_at <= NOW() และ sla_status IN ('active','due_soon')<br/>Job วิ่งทุก 1 นาที — ต้อง idempotent และ multi-instance safe

    loop Every 1 minute
        Job->>Redis: SET sla:breach_job:lock "1" NX EX 55
        Note over Redis: NX = set only if not exists (atomic)<br/>EX 55 = auto-release ถ้า job crash

        alt lock acquired (result = "OK")
            Job->>DB: Query 1 — due_soon<br/>SELECT c.id FROM conversations c<br/>JOIN workspace_sla_configs w ON w.tenant_id=c.tenant_id<br/>WHERE c.sla_status='active'<br/>AND c.sla_due_at > NOW()<br/>AND c.sla_due_at <= NOW() + (w.due_soon_minutes * interval '1 min')
            DB-->>Job: conversations to mark due_soon
            Job->>DB: UPDATE conversations SET sla_status='due_soon' (batch)

            Job->>DB: Query 2 — breach<br/>SELECT id, cycle_number, sla_due_at, sla_first_inbound_at FROM conversations<br/>WHERE sla_due_at <= NOW()<br/>AND sla_status IN ('active', 'due_soon')

            alt 0 rows found
                Job->>Job: log "breach_job: 0 processed"
            else N rows found — for each conversation
                Note over Job,DB: BEGIN TRANSACTION
                Job->>DB: UPDATE conversations SET sla_status = 'breached'
                Job->>DB: INSERT conversation_tags<br/>{ tag_id=SLA_BREACHED_TAG, is_system=true }<br/>ON CONFLICT DO NOTHING
                Job->>DB: INSERT conversation_sla_events<br/>{ cycle_N, type='breached', inbound_at=sla_first_inbound_at,<br/>sla_due_at, resolved_at=NOW() }<br/>ON CONFLICT DO NOTHING
                alt transaction success
                    Note over Job,DB: COMMIT
                    Job->>Redis: DEL sla:status:{conv_id}
                    Job->>MS: sync conversation (add sla_breached tag)
                    Job->>WS: conversation:sla_breached { conversation_id }
                    Note over WS: push ให้ทุก agent ที่ watch inbox<br/>badge เปลี่ยนเป็นสีแดง + ขึ้น Overdue list

                else transaction failed
                    Note over Job,DB: ROLLBACK
                    Job->>Job: log error + skip conversation
                end
            end

            Job->>Job: log "breach_job: N processed"
            Job->>Redis: DEL sla:breach_job:lock
        else lock not acquired (result = null)
            Job->>Job: skip — another instance running
        end
    end
```

---

## SD-03: System Tag Delete Protection

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant GW as api-gateway
    participant Tags as TagsService<br/>(omnichat-service)
    participant DB as Database

    Note over User,DB: **Pre-conditions**<br/>conversation มี system tag (sla_met หรือ sla_breached) ที่มี is_system = true<br/>User พยายามลบ tag ผ่าน UI หรือ API โดยตรง

    User->>GW: DELETE /conversations/{id}/tags/{tag_id}
    GW->>Tags: TCP send('remove_conversation_tag', ...)
    Tags->>DB: SELECT is_system FROM conversation_tags WHERE id = tag_id

    alt is_system = true
        Tags-->>GW: throw ForbiddenException
        GW-->>User: 403 "system tag ไม่สามารถลบได้"
    else is_system = false
        Tags->>DB: UPDATE conversation_tags SET deleted_at = NOW()
        Tags-->>GW: ok
        GW-->>User: 200 OK
    end
```

---

## Redis Key Summary

| Key | TTL | Purpose | ใช้ใน |
|-----|-----|---------|-------|
| `sla:breach_job:lock` | 55s | Distributed lock — กัน multi-instance race | BreachDetectionJob |
| `omnichat:sla:config:{tenant_id}:{channel_type}` | 60m | SLA config cache (bh_aware, first_response_minutes) — DEL+SET ทันทีเมื่อ admin เปลี่ยน | ConversationsService |
| `omnichat:bh:schedule:{tenant_id}` | 60m | Business Hours schedule cache — DEL เมื่อ admin เปลี่ยน BH settings | ConversationsService |

---

## Component Map (Real Code)

```
packages/redis/                            ← existing — import RedisModule ใน omnichat-service
├── redis.service.ts                       ← RedisService.getClient() → raw ioredis
└── cache/redis-cache.service.ts           ← RedisCacheService.setJson/getJson/del/exists

omnichat-service/
├── src/
│   ├── app.module.ts                      ← add RedisModule import (NEW)
│   ├── conversations/
│   │   └── conversations.service.ts       ← sendMessage() — add cache read/invalidate + WS push
│   ├── tags/
│   │   └── tags.service.ts                ← deleteTag() — add is_system guard
│   └── sla/                              ← NEW module
│       ├── breach-detection.job.ts        ← @Cron, distributed lock, breach loop + WS push
│       └── sla.service.ts                 ← tag helpers + cache helpers
└── prisma/
    └── schema.prisma                      ← add is_system to Tag + ConversationTag
                                              redesign ConversationSlaEvent
```

---

> **Multi-cycle Timeline Example** → see [ACE-1643_STORY-SLA-04_Timeline.md](ACE-1643_STORY-SLA-04_Timeline.md)  
> **SLA status state transitions** → see [ACE-1643_STORY-SLA-04_State_Diagram.md](ACE-1643_STORY-SLA-04_State_Diagram.md)  
> **ER Diagram** → see [ACE-1643_STORY-SLA-04_ER_Diagram.md](ACE-1643_STORY-SLA-04_ER_Diagram.md)
