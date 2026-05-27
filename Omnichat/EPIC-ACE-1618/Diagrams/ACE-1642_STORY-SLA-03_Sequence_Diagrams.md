# STORY-SLA-03: Sequence Diagrams

**Story:** ACE-1642 — Timer Display in Inbox
**Parent Epic:** ACE-1618

---

## SD-01: Initial Inbox Load with SLA Data

```mermaid
sequenceDiagram
    autonumber
    box Frontend
    actor Agent
    participant InboxUI
    participant ConversationList
    participant TimerBadge
    participant OverduePill
    end
    box Backend
    participant GW as api-gateway
    participant SVC as omnichat-service
    participant DB as Database
    end

    Note over Agent,DB: **Pre-conditions**<br/>Agent ยังไม่ได้เปิด inbox — ยังไม่มี conversations โหลด

    Note over SVC,DB: sla_status (stored): pending|disabled|active|due_soon|breached|met<br/>sla_due_soon_at = sla_due_at − due_soon_minutes (computed, not stored)<br/>FE badge color: green → amber (due_soon_at) → red (due_at)

    Agent->>InboxUI: เปิด Inbox
    InboxUI->>GW: GET /conversations?include_sla=true&limit=50&cursor=...
    GW->>SVC: forward
    SVC->>DB: SELECT sla_status, sla_due_at, waiting_since_at, ... FROM conversations
    DB-->>SVC: rows
    GW-->>InboxUI: conversations[] + {sla_status, sla_due_at, sla_due_soon_at} + next_cursor

    InboxUI->>ConversationList: render(conversations)

    loop ต่อ conversation
        alt sla_status = active | due_soon | breached
            ConversationList->>TimerBadge: render(sla_due_at, sla_due_soon_at)
            TimerBadge-->>ConversationList: badge (color computed from NOW vs timestamps)
        else sla_status = pending | met | disabled
            ConversationList->>ConversationList: ไม่ render badge
        end
    end

    alt SLA enabled channel ใดก็ได้
        InboxUI->>OverduePill: render()
        OverduePill-->>InboxUI: pill visible
    else SLA ปิดทุก channel
        InboxUI->>InboxUI: ไม่แสดง Overdue pill
    end

    Note over InboxUI,GW: Color transition — FE compute จาก NOW vs timestamps ตลอดเวลา<br/>Status changes (due_soon, breached, met) = WS push<br/>WS drop → reconnect → one-shot sync GET /conversations?ids=[visible_ids]&fields=sla_due_at,sla_due_soon_at,sla_status
```

---

## SD-02: Overdue Filter Pill Interaction

```mermaid
sequenceDiagram
    autonumber
    box Frontend
    actor Agent
    participant OverduePill
    participant ConversationList
    end
    box Backend
    participant GW as api-gateway
    participant SVC as omnichat-service
    participant DB as Database
    end

    Note over Agent,DB: **Pre-conditions**<br/>Inbox โหลดแล้ว — Overdue pill visible (SLA enabled อย่างน้อย 1 channel), filter ยังไม่ active

    Note over SVC,DB: DB index: @@index([tenant_id, status, sla_due_at(sort: Asc)])<br/>ORDER BY sla_due_at ASC = longest overdue first (lowest epoch = breach earliest)

    Agent->>OverduePill: click (activate filter)
    OverduePill->>OverduePill: set active state (highlighted)
    OverduePill->>GW: GET /conversations?is_overdue=true&sort_by=sla_due_soonest
    GW->>SVC: forward
    SVC->>DB: SELECT ... WHERE tenant_id=? AND sla_status='breached' ORDER BY sla_due_at ASC
    DB-->>SVC: rows (index scan, no filesort)
    GW-->>OverduePill: conversations[] (breached only, longest overdue first)
    OverduePill->>ConversationList: render(breached_conversations)
    ConversationList-->>Agent: เห็นเฉพาะ breached convs เรียง overdue นานที่สุดก่อน

    Agent->>OverduePill: click (deactivate filter)
    OverduePill->>OverduePill: clear active state
    OverduePill->>GW: GET /conversations (clear filter)
    GW->>SVC: forward
    SVC->>DB: SELECT sla_status, sla_due_at, ... FROM conversations WHERE tenant_id=? ORDER BY last_message_at DESC
    DB-->>SVC: rows
    GW-->>OverduePill: conversations[]
    OverduePill->>ConversationList: render(all_conversations)
    ConversationList-->>Agent: inbox กลับสู่ปกติ
```

---

## SD-03: Agent Reply → SLA Met → Remove from Overdue List

```mermaid
sequenceDiagram
    autonumber
    box Frontend
    actor Agent
    participant ConversationDetail
    participant InboxUI
    participant TimerBadge
    participant OverduePill
    participant ConversationList
    end
    box Backend
    participant GW as api-gateway
    participant SVC as omnichat-service
    participant WSServer as WebSocket Server
    end

    Note over Agent,WSServer: **Pre-conditions:** Agent เปิด conversation ที่ sla_status = active | due_soon | breached, Overdue filter อาจ active หรือไม่ก็ได้<br/>Agent ที่ส่ง reply update UI ทันทีจาก response body — ไม่รอ WS<br/>WS notify agents อื่นที่ watch inbox เดียวกัน

    Agent->>ConversationDetail: ส่ง reply
    ConversationDetail->>GW: POST /conversations/{id}/messages {type: outbound}
    GW->>SVC: forward
    SVC->>SVC: sla_status = met, sla_met_at = NOW(), waiting_since_at = null
    SVC->>WSServer: conversation:updated {conv_id, sla_status: "met", sla_due_at: null}
    GW-->>ConversationDetail: 201 Created + {sla_status: "met"}

    ConversationDetail->>InboxUI: sla_status = met (from response)
    InboxUI->>TimerBadge: hide()
    TimerBadge-->>InboxUI: badge หาย

    alt Overdue filter กำลัง active
        InboxUI->>OverduePill: removeConversation(conv_id)
        OverduePill->>ConversationList: re-render (ลบ conv ออก)
        ConversationList-->>Agent: conversation หายออกจาก Overdue list ทันที
    end

    Note over WSServer,InboxUI: Other agents watching same inbox
    WSServer->>InboxUI: WS event: conversation:updated {conv_id, sla_status: "met", sla_due_at: null}
    InboxUI->>TimerBadge: hide()
    alt Overdue filter active
        InboxUI->>OverduePill: removeConversation(conv_id)
        OverduePill->>ConversationList: re-render (ลบ conv ออก)
        ConversationList-->>Agent: conversation หายออกจาก Overdue list
    end
```

---

## SD-04: Sort by SLA Due Soonest

```mermaid
sequenceDiagram
    autonumber
    box Frontend
    actor Agent
    participant SortDropdown
    participant ConversationList
    end
    box Backend
    participant GW as api-gateway
    participant SVC as omnichat-service
    participant DB as Database
    end

    Note over Agent,DB: **Pre-conditions:** Inbox โหลดแล้ว — sort = default (last_message_at DESC)<br/>sort_by=sla_due_soonest = ORDER BY sla_due_at ASC NULLS LAST<br/>NULL sla_due_at (met/disabled) จมล่าง — breached ขึ้นก่อน (epoch ต่ำสุด)

    Agent->>SortDropdown: เลือก "SLA due soonest"
    SortDropdown->>GW: GET /conversations?sort_by=sla_due_soonest
    GW->>SVC: forward
    SVC->>DB: SELECT ... ORDER BY sla_due_at ASC NULLS LAST
    DB-->>SVC: rows (index scan via @@index([tenant_id, sla_due_at(sort: Asc)]))
    GW-->>SortDropdown: conversations[] sorted
    SortDropdown->>ConversationList: render(sorted_conversations)
    ConversationList-->>Agent: inbox เรียงตาม deadline ใกล้ที่สุดก่อน
```

---

> **sla_status state transitions** → see [ACE-1641_STORY-SLA-02_State_Diagram.md](ACE-1641_STORY-SLA-02_State_Diagram.md)
