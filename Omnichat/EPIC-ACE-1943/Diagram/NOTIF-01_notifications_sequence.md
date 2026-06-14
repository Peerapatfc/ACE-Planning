## Sequence Diagrams

### 1 — Conversation Assigned / Reassigned / Unassigned

```mermaid
sequenceDiagram
  autonumber
  participant FE as workspace-admin
  participant API as api-gateway (HTTP)
  participant OmniSvc as omnichat-service
  participant NotiSvc as notification-service
  participant DB_N as notification-service DB
  participant Redis as Redis
  participant GW as api-gateway (WebSocket)

  FE->>API: HTTP PATCH /omnichat/conversations/:id/assign<br/>{ agent_id, agent_name, assigned_by_name }
  API->>OmniSvc: HTTP PATCH /conversations/:id/assign<br/>{ agent_id, agent_name, assigned_by_id, assigned_by_name }
  OmniSvc->>OmniSvc: findFirst conversation WHERE id + tenant_id<br/>SELECT { id, assigned_agent_id }
  alt not found
    OmniSvc-->>API: 404 NotFoundException
    API-->>FE: 404
  end

  OmniSvc->>OmniSvc: determine event_type<br/>null → agent_id     = conversation_assigned<br/>agent_id → other_id  = conversation_reassigned<br/>agent_id → null      = conversation_unassigned

  OmniSvc->>OmniSvc: $transaction<br/>  UPDATE conversation (assigned_agent_id, assigned_agent_name)<br/>  INSERT conversation_assignments
  OmniSvc->>OmniSvc: syncConversation() [meilisearch]
  OmniSvc->>Redis: PUBLISH omnichat:events<br/>{ type: conversation:updated, tenantId, conversationId,<br/>  payload: { assignedAgentId, assignedAgentName } }
  Note right of OmniSvc: fire-and-forget (existing)
  OmniSvc-->>API: 200 { conversation, assignment }
  API-->>FE: 200 OK

  alt event_type ≠ conversation_unassigned
    OmniSvc-)NotiSvc: TCP emit { cmd: 'create_notification' }<br/>{ workspace_id, user_id: new_agent_id,<br/>  event_type, conversation_id,<br/>  actor_id: assigned_by_id,<br/>  metadata: { customer_name, channel, assigned_by_name } }
    Note right of OmniSvc: fire-and-forget<br/>void .emit().subscribe({ error: ... })
    NotiSvc->>NotiSvc: checkGlobalRule(workspace_id, event_type)<br/>TODO (NOTIF-04): ตอนนี้ pass through เสมอ
    NotiSvc->>DB_N: INSERT notifications
    NotiSvc->>Redis: PUBLISH notifications:events<br/>{ userId: new_agent_id, tenantId, notification }
    Redis-->>GW: message event
    GW->>GW: JSON.parse(message)<br/>route to user:{userId} room
    GW->>FE: socket.to("user:{userId}").emit("notification:new", notification)
    FE->>FE: bell badge +1
  end
```

---

### 2 — New Conversation

```mermaid
sequenceDiagram
  autonumber
  participant Customer as Customer / Channel
  participant Normalizer as omnichat-normalizer-worker
  participant OmniSvc as omnichat-service
  participant UserSvc as user-service
  participant NotiSvc as notification-service
  participant DB_N as notification-service DB
  participant Redis as Redis
  participant GW as api-gateway (WebSocket)
  participant FE as workspace-admin

  Customer->>Normalizer: raw inbound event (first message)
  Normalizer->>OmniSvc: HTTP POST /messages/inbound
  OmniSvc->>OmniSvc: UPSERT contact<br/>INSERT conversation (new)<br/>INSERT message
  OmniSvc->>Redis: PUBLISH omnichat:events<br/>{ type: message:new, tenantId, conversationId,<br/>  payload: { message } }
  Note right of OmniSvc: fire-and-forget (existing)
  OmniSvc-->>Normalizer: 200 { conversation_id, message_id }

  OmniSvc->>UserSvc: TCP send { cmd: 'list_workspace_members' }<br/>{ tenant_id, roles: [admin, supervisor] }
  UserSvc-->>OmniSvc: members[] (admin + supervisor)

  loop per member
    OmniSvc-)NotiSvc: TCP emit { cmd: 'create_notification' }<br/>{ workspace_id, user_id: member.id,<br/>  event_type: new_conversation,<br/>  conversation_id, actor_id: null,<br/>  metadata: { customer_name, channel, message_preview } }
    NotiSvc->>NotiSvc: checkGlobalRule(workspace_id, event_type)<br/>TODO (NOTIF-04): ตอนนี้ pass through เสมอ
    NotiSvc->>DB_N: INSERT notifications<br/>{ event_type: new_conversation, message_count: 1, ... }
    NotiSvc->>Redis: PUBLISH notifications:events<br/>{ userId: member.id, tenantId, notification }
    Redis-->>GW: message event
    GW->>GW: route to user:{userId} room
    GW->>FE: socket.to("user:{userId}")<br/>.emit("notification:new", notification)
    FE->>FE: bell badge +1
  end
```

---

### 3 — Customer Replied

```mermaid
sequenceDiagram
  autonumber
  participant Customer as Customer / Channel
  participant Normalizer as omnichat-normalizer-worker
  participant OmniSvc as omnichat-service
  participant NotiSvc as notification-service
  participant DB_N as notification-service DB
  participant Redis as Redis
  participant GW as api-gateway (WebSocket)
  participant FE as workspace-admin

  Customer->>Normalizer: inbound message
  Normalizer->>OmniSvc: HTTP POST /messages/inbound
  OmniSvc->>OmniSvc: UPSERT contact<br/>UPSERT conversation (existing)<br/>INSERT message<br/>UPDATE conversation (last_message_at, unread_count)
  OmniSvc->>Redis: PUBLISH omnichat:events<br/>{ type: message:new, tenantId, conversationId,<br/>  payload: { message } }
  Note right of OmniSvc: fire-and-forget (existing)
  OmniSvc-->>Normalizer: 200 { conversation_id, message_id }

  OmniSvc->>OmniSvc: is_new_conversation = false → emit customer_replied<br/>SELECT assigned_agent_id

  alt assigned_agent_id exists
    OmniSvc->>OmniSvc: truncate message body → message_preview (80 chars)
    OmniSvc-)NotiSvc: TCP emit { cmd: 'create_notification' }<br/>{ workspace_id, user_id: assigned_agent_id,<br/>  event_type: customer_replied,<br/>  conversation_id, actor_id: null,<br/>  metadata: { customer_name, channel, message_preview } }
    NotiSvc->>NotiSvc: checkGlobalRule(workspace_id, event_type)<br/>TODO (NOTIF-04): ตอนนี้ pass through เสมอ
    NotiSvc->>DB_N: SELECT notifications<br/>WHERE user_id + conversation_id + is_read = false<br/>AND event_type IN (new_conversation, customer_replied)
    alt unread noti EXISTS
      NotiSvc->>DB_N: UPDATE notifications SET<br/>metadata.message_count++<br/>metadata.message_preview = new preview<br/>updated_at = NOW()
    else no unread noti
      NotiSvc->>DB_N: INSERT notifications<br/>{ event_type: customer_replied, message_count: 1, ... }
    end
    NotiSvc->>Redis: PUBLISH notifications:events<br/>{ userId: assigned_agent_id, tenantId, notification }
    Redis-->>GW: message event
    GW->>GW: route to user:{userId} room
    GW->>FE: socket.to("user:{userId}")<br/>.emit("notification:new", notification)
    FE->>FE: upsert noti row by notification_id<br/>(insert ใหม่ หรือ update message_count + preview)
  else no assigned agent
    OmniSvc->>OmniSvc: skip
  end
```

---

### 4 — Mention in Conversation Note

```mermaid
sequenceDiagram
  autonumber
  participant FE as workspace-admin
  participant API as api-gateway (HTTP)
  participant OmniSvc as omnichat-service
  participant NotiSvc as notification-service
  participant DB_N as notification-service DB
  participant Redis as Redis
  participant GW as api-gateway (WebSocket)

  FE->>API: HTTP POST /omnichat/conversations/:id/conversation-notes<br/>{ content, created_by_agent_id, mentioned_agent_ids[] }
  API->>OmniSvc: HTTP POST /conversations/:id/conversation-notes
  OmniSvc->>OmniSvc: INSERT conversation_notes<br/>{ content, created_by_agent_id, mentioned_agent_ids[] }
  OmniSvc-->>API: 201 { note }
  API-->>FE: 201 Created

  OmniSvc->>OmniSvc: truncate content → note_preview (80 chars + "...")

  loop per mentioned user_id in mentioned_agent_ids[]
    OmniSvc-)NotiSvc: TCP emit { cmd: 'create_notification' }<br/>{ workspace_id, user_id: mentioned_id,<br/>  event_type: mention,<br/>  conversation_id, actor_id: created_by_agent_id,<br/>  metadata: { conversation_id, note_id,<br/>    actor_name, channel, note_preview } }
    NotiSvc->>NotiSvc: checkGlobalRule(workspace_id, event_type)<br/>TODO (NOTIF-04): ตอนนี้ pass through เสมอ
    NotiSvc->>DB_N: INSERT notifications
    NotiSvc->>Redis: PUBLISH notifications:events<br/>{ userId: mentioned_id, tenantId, notification }
    Redis-->>GW: message event
    GW->>GW: route to user:{userId} room
    GW->>FE: socket.to("user:{userId}").emit("notification:new", notification)
    FE->>FE: bell badge +1
  end
```

---

### 5 — SLA Due Soon

```mermaid
sequenceDiagram
  autonumber
  participant Cron as BullMQ Cron (every 1 min)
  participant OmniSvc as omnichat-service
  participant NotiSvc as notification-service
  participant DB_N as notification-service DB
  participant Redis as Redis
  participant GW as api-gateway (WebSocket)
  participant FE as workspace-admin

  Cron->>OmniSvc: SLACronService.runCycle()
  OmniSvc->>Redis: acquireLock(sla_breach_lock, TTL=300s)
  alt lock not acquired
    OmniSvc->>OmniSvc: skip cycle
  else lock acquired
    OmniSvc->>OmniSvc: clearDisabled()
    OmniSvc->>OmniSvc: markDueSoon()
    OmniSvc->>OmniSvc: UPDATE conversations SET sla_status = due_soon<br/>WHERE sla_due_at <= NOW() + due_soon_minutes<br/>AND sla_status NOT IN (due_soon, breached)

    loop per updated conversation
      OmniSvc->>Redis: PUBLISH omnichat:events<br/>{ type: sla:warning, tenantId, conversationId }
      Note right of OmniSvc: fire-and-forget (existing)
      OmniSvc->>OmniSvc: SELECT assigned_agent_id

      alt assigned_agent_id exists
        OmniSvc-)NotiSvc: TCP emit { cmd: create_notification }<br/>{ workspace_id, user_id: assigned_agent_id,<br/>  event_type: sla_due_soon, conversation_id,<br/>  metadata: { customer_name, channel, remaining_minutes } }
        NotiSvc->>DB_N: INSERT notifications
        NotiSvc->>Redis: PUBLISH notifications:events<br/>{ userId: assigned_agent_id, tenantId, notification }
        Redis-->>GW: message event
        GW->>GW: route to user:{userId} room
        GW->>FE: socket.to("user:{userId}")<br/>.emit("notification:new", notification)
        FE->>FE: bell badge +1
      end
    end

    OmniSvc->>OmniSvc: markBreached()
    OmniSvc->>Redis: releaseLock(sla_breach_lock)
  end
```

---

### 6 — SLA Breached (Dual Recipients)

```mermaid
sequenceDiagram
  autonumber
  participant Cron as BullMQ Cron (every 1 min)
  participant OmniSvc as omnichat-service
  participant UserSvc as user-service
  participant NotiSvc as notification-service
  participant DB_N as notification-service DB
  participant Redis as Redis
  participant GW as api-gateway (WebSocket)
  participant FE as workspace-admin

  Note over Cron,OmniSvc: ต่อจาก Diagram 5 — ภายใน runCycle() เดียวกัน
  OmniSvc->>OmniSvc: markBreached()
  OmniSvc->>OmniSvc: SELECT conversations<br/>WHERE sla_due_at < NOW()<br/>AND sla_status IN (active, due_soon, pending)

  loop per conversation
    OmniSvc->>OmniSvc: $transaction<br/>  UPDATE sla_status = breached (optimistic lock)<br/>  INSERT conversationTag (SLA Breached, is_system=true)<br/>  UPSERT conversationSlaEvent<br/>  WHERE conversation_id + event_type=breached + cycle_number

    alt didUpdate = false
      OmniSvc->>OmniSvc: skip — race condition, another pod breached first
    else didUpdate = true
      OmniSvc->>Redis: PUBLISH omnichat:events<br/>{ type: sla:overdue, tenantId, conversationId }
      Note right of OmniSvc: fire-and-forget (existing)
      OmniSvc->>OmniSvc: SELECT assigned_agent_id

      alt assigned_agent_id exists
        OmniSvc-)NotiSvc: TCP emit { cmd: 'create_notification' }<br/>{ workspace_id, user_id: assigned_agent_id,<br/>  event_type: sla_breached, conversation_id,<br/>  actor_id: null,<br/>  metadata: { customer_name, channel, elapsed_minutes } }
        NotiSvc->>DB_N: INSERT notifications (agent only)
        NotiSvc->>Redis: PUBLISH notifications:events<br/>{ userId: assigned_agent_id, tenantId, notification }
        Redis-->>GW: message event
        GW->>GW: route to user:{userId} room
        GW->>FE: socket.to("user:{userId}")<br/>.emit("notification:new", notification)
        FE->>FE: bell badge +1
      end

      OmniSvc->>UserSvc: TCP send { cmd: 'list_workspace_members' }<br/>{ tenant_id, roles: [admin, supervisor] }
      UserSvc-->>OmniSvc: members[] (admin + supervisor)

      loop per supervisor / admin
        OmniSvc-)NotiSvc: TCP emit { cmd: 'create_notification' }<br/>{ workspace_id, user_id: member.id,<br/>  event_type: sla_breached_team, conversation_id,<br/>  actor_id: null,<br/>  metadata: { customer_name, channel, elapsed_minutes } }
        NotiSvc->>DB_N: INSERT notifications
        NotiSvc->>Redis: PUBLISH notifications:events<br/>{ userId: member.id, tenantId, notification }
        Redis-->>GW: message event
        GW->>GW: route to user:{userId} room
        GW->>FE: socket.to("user:{userId}")<br/>.emit("notification:new", notification)
        FE->>FE: bell badge +1
      end
    end
  end
```

---

### 7 — Channel Error

```mermaid
sequenceDiagram
  autonumber
  participant OmniSvc as omnichat-service
  participant TenantSvc as tenant-service
  participant UserSvc as user-service
  participant NotiSvc as notification-service
  participant DB_N as notification-service DB
  participant Redis as Redis
  participant GW as api-gateway (WebSocket)
  participant FE as workspace-admin

  OmniSvc->>OmniSvc: LazadaTokenMonitorTask.runCycle()<br/>detect token expiring / expired
  OmniSvc->>TenantSvc: TCP send { cmd: 'get_tenant_by_id' }<br/>{ id: tenant_id }
  TenantSvc-->>OmniSvc: { tenant_name }

  OmniSvc->>UserSvc: TCP send { cmd: 'list_workspace_members' }<br/>{ tenant_id, roles: [admin] }
  UserSvc-->>OmniSvc: members[] (admin)

  loop per admin
    OmniSvc-)NotiSvc: TCP emit { cmd: 'create_notification' }<br/>{ workspace_id, user_id: admin.id,<br/>  event_type: channel_error,<br/>  conversation_id: null, actor_id: null,<br/>  metadata: { channel_type, error_description } }
    NotiSvc->>NotiSvc: checkGlobalRule(workspace_id, event_type)<br/>TODO (NOTIF-04): ตอนนี้ pass through เสมอ
    NotiSvc->>DB_N: INSERT notifications
    NotiSvc->>Redis: PUBLISH notifications:events<br/>{ userId: admin.id, tenantId, notification }
    Redis-->>GW: message event
    GW->>GW: route to user:{userId} room
    GW->>FE: socket.to("user:{userId}")<br/>.emit("notification:new", notification)
    FE->>FE: bell badge +1
  end

  Note over OmniSvc: email ยังส่งแยกผ่าน<br/>TCP emit { cmd: 'send_lazada_token_expiry_email' }<br/>เหมือนเดิม — ไม่เปลี่ยน
```

---

### 8 — Mark Notifications Read (FE เปิด Conversation)

```mermaid
sequenceDiagram
  autonumber
  participant FE as workspace-admin
  participant API as api-gateway (HTTP)
  participant OmniSvc as omnichat-service
  participant NotiSvc as notification-service
  participant DB_N as notification-service DB
  participant Redis as Redis
  participant GW as api-gateway (WebSocket)

  FE->>API: HTTP GET /omnichat/conversations/:id
  API->>OmniSvc: HTTP GET /conversations/:id
  OmniSvc-->>API: 200 { conversation }
  API-->>FE: 200 OK

  OmniSvc-)NotiSvc: TCP emit { cmd: 'mark_notifications_read' }<br/>{ workspace_id, user_id, conversation_id,<br/>  event_types: [new_conversation, customer_replied] }
  Note right of OmniSvc: fire-and-forget<br/>void .emit().subscribe({ error: ... })
  NotiSvc->>DB_N: UPDATE notifications SET<br/>is_read = true, read_at = NOW()<br/>WHERE user_id + conversation_id + is_read = false<br/>AND event_type IN (new_conversation, customer_replied)
  NotiSvc->>Redis: PUBLISH notifications:events<br/>{ userId, tenantId, type: 'notifications:read',<br/>  conversation_id }
  Redis-->>GW: message event
  GW->>GW: route to user:{userId} room
  GW->>FE: socket.to("user:{userId}")<br/>.emit("notifications:read", { conversation_id })
  FE->>FE: mark noti rows read + update bell badge
```

---

### 9 — WebSocket Reconnected

```mermaid
sequenceDiagram
  autonumber
  participant FE as workspace-admin
  participant API as api-gateway (HTTP)
  participant NotiSvc as notification-service
  participant DB_N as notification-service DB

  FE->>FE: WebSocket reconnect สำเร็จ
  FE->>API: HTTP GET /notifications?since=last_seen_at
  API->>NotiSvc: TCP send { cmd: 'get_missed_notifications' }<br/>{ user_id, last_seen_at }

  alt last_seen_at exists
    NotiSvc->>DB_N: SELECT notifications<br/>WHERE user_id = X<br/>AND created_at > last_seen_at<br/>ORDER BY created_at ASC
  else last_seen_at = null (first load)
    NotiSvc->>DB_N: SELECT notifications<br/>WHERE user_id = X AND is_read = false<br/>ORDER BY created_at ASC
  end

  DB_N-->>NotiSvc: notifications[]
  NotiSvc-->>API: notifications[]
  API-->>FE: 200 { notifications }
  FE->>FE: merge into noti list + update bell badge
```

---

## Transport Reference

| From | To | Protocol | Key |
| --- | --- | --- | --- |
| workspace-admin | api-gateway (HTTP) | HTTP | `PATCH /omnichat/conversations/:id/assign` |
| workspace-admin | api-gateway (HTTP) | HTTP | `POST /omnichat/conversations/:id/conversation-notes` |
| workspace-admin | api-gateway (HTTP) | HTTP | `GET /omnichat/conversations/:id` |
| api-gateway (HTTP) | omnichat-service | HTTP | `PATCH /conversations/:id/assign` |
| api-gateway (HTTP) | omnichat-service | HTTP | `POST /conversations/:id/conversation-notes` |
| api-gateway (HTTP) | omnichat-service | HTTP | `GET /conversations/:id` |
| omnichat-normalizer-worker | omnichat-service | HTTP | `POST /messages/inbound` |
| omnichat-service | user-service | TCP send | `{ cmd: 'list_workspace_members' }` |
| omnichat-service | tenant-service | TCP send | `{ cmd: 'get_tenant_by_id' }` |
| omnichat-service | notification-service | TCP emit | `{ cmd: 'create_notification' }` |
| omnichat-service | notification-service | TCP emit | `{ cmd: 'mark_notifications_read' }` |
| notification-service | Redis | PUBLISH | `notifications:events` |
| Redis | api-gateway (WebSocket) | SUB message | `notifications:events` |
| api-gateway (WebSocket) | workspace-admin | Socket.io emit | `notification:new` → room `user:{userId}` |
| api-gateway (WebSocket) | workspace-admin | Socket.io emit | `notifications:read` → room `user:{userId}` |

---

## ACE-2382 — สิ่งที่ต้องเพิ่มใน ChatGateway

| ไฟล์ | การเปลี่ยนแปลง |
| --- | --- |
| `chat.gateway.ts` `handleConnection()` | เพิ่ม `client.join(user:${data.userId})` |
| `chat.gateway.ts` `onModuleInit()` | subscribe `notifications:events` channel + route to `user:{userId}` room |
| `notification-service` | เพิ่ม RedisModule + `PUBLISH notifications:events` หลัง INSERT notifications |

---

## TODO Tracker

| ref | งาน | blocked by |
| --- | --- | --- |
| `TODO (NOTIF-04)` | `checkGlobalRule()` ใน notification-service | ACE NOTIF-04 |
