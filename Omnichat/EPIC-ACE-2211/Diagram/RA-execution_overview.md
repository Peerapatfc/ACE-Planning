## Rule Execution Engine — Overview (EPIC ACE-2211)

> **Scope:** ภาพรวมการ "execute" rule ตอน message เข้า — **ไม่ใช่ STORY RA-01** (RA-01 = CRUD เท่านั้น)
> รายละเอียด design ลงในสตอรี่ย่อย: **RA-02** (conditions) · **RA-03** (auto-reply) · **RA-04** (auto-tag)
> EPIC: [ACE-2211](../ACE-2211_EPIC-A4.1_Rule_Automation.md) · ER: [RA-01_rule_automation_er.md](./RA-01_rule_automation_er.md) · CRUD: [RA-01_rule_automation_sequence.md](./RA-01_rule_automation_sequence.md)
> ไฟล์นี้ให้บริบทว่า field ที่ RA-01 สร้าง (`fired_count`, cooldown, `sender_type='rule'`, `tagged_by_type`) ถูกใช้ตอน execute อย่างไร

---

### Rule Execution Engine (inbound message → evaluate → execute)

ภาพรวม EPIC "Rule Execution Logic" — hook เพิ่มใน `createInbound()` ของ omnichat-service (ต่อจาก persist + SLA + publish `message:new` เดิม) แบบ **fire-and-forget** (void, ไม่ block inbound ingestion เหมือน AI auto-assign เดิม)

```mermaid
sequenceDiagram
  autonumber
  participant Norm as omnichat-normalizer-worker
  participant OmniSvc as omnichat-service (createInbound + RuleEngine)
  participant Redis as Redis
  participant DB_O as omnichat-service DB
  participant Strategy as Channel Strategy (pushMessage)
  participant GW as api-gateway (WebSocket)
  participant FE as workspace-admin

  Norm->>OmniSvc: POST /messages/inbound (existing)
  OmniSvc->>DB_O: INSERT messages { sender_type:'contact', direction:'inbound' }<br/>+ update conversation + SLA active + publish message:new (existing)
  OmniSvc-)OmniSvc: RuleEngine.evaluate(message, conversation) — async void

  Note over OmniSvc: Background guard #1 — bot/system skip
  alt message.sender_type != 'contact' OR direction != 'inbound'
    OmniSvc->>OmniSvc: skip ทั้งหมด (bot/platform/agent/rule message ไม่ trigger)
  else customer inbound
    Note over OmniSvc,Redis: Background guard #2 — dedup 5s window
    OmniSvc->>Redis: SET automation:dedup:{tenant}:{conv}:{hash(content)} NX EX 5
    alt key มีอยู่แล้ว (message ซ้ำใน 5s)
      OmniSvc->>OmniSvc: skip evaluate (กัน trigger ซ้ำ)
    else acquired
      OmniSvc->>Redis: GET automation:rules:{tenant_id}
      opt cache miss
        OmniSvc->>DB_O: SELECT automation_rules WHERE tenant_id AND enabled = true<br/>ORDER BY created_at ASC, id ASC
        DB_O-->>OmniSvc: activeRules[]
        OmniSvc->>Redis: SET automation:rules:{tenant_id} EX 3600
      end

      OmniSvc->>OmniSvc: evaluate conditions ทุก rule (single-pass ณ เวลานี้)<br/>keyword / channel / business_hours + AND|OR<br/>business_hours(use_workspace_hours) → ดึง workspace tz ทุกครั้ง (ไม่ cache)
      Note over OmniSvc: matched[] = rules ที่ผ่าน — เรียง created_at ASC, id ASC (เก่าสุดก่อน = priority สูงสุด)

      alt matched ว่าง
        OmniSvc->>OmniSvc: จบ — ไม่มี action
      else มี rule match
        loop ทุก add_tag rule ที่ match (ทุกอันติดได้)
          OmniSvc->>Redis: GET automation:cooldown:{rule.id}:{conv}
          alt cooldown ยังไม่หมด
            OmniSvc->>OmniSvc: skip rule นี้ — ไม่ติด tag ซ้ำ<br/>(tag ที่ agent ลบไป stay ลบจนกว่า cooldown หมด)
          else ไม่มี cooldown
            OmniSvc->>DB_O: resolve tag_ids → skip tag ที่ deleted_at != null (warn ไม่ error)<br/>dedup กับ conversation_tags ที่ยัง active
            opt มี tag ใหม่ต้องติด
              OmniSvc->>DB_O: INSERT conversation_tags { tagged_by_type:'rule', created_by_id: rule_id }
              OmniSvc->>DB_O: UPDATE automation_rules SET fired_count = fired_count + 1
              OmniSvc->>Redis: PUBLISH omnichat:events { type:'conversation:updated', tenantId, conversationId }
            end
            OmniSvc->>Redis: SET automation:cooldown:{rule.id}:{conv}<br/>EX RULE_TAG_COOLDOWN_MINUTES×60 (default ระบบ — wizard ไม่ให้ตั้ง)
          end
        end

        Note over OmniSvc: Auto-reply — only-first-wins (rule เก่าสุดที่ action_type=auto_reply)
        opt มี auto_reply rule ใน matched
          OmniSvc->>Redis: GET automation:cooldown:{firstRule.id}:{conv}
          alt cooldown ยังไม่หมด
            OmniSvc->>OmniSvc: skip auto-reply (กัน loop reply→trigger→reply)
          else ไม่มี cooldown
            alt channel ∈ {LINE,FACEBOOK,INSTAGRAM,LAZADA}
              OmniSvc->>OmniSvc: render template variables ({{contact_name}} ...)
              OmniSvc->>DB_O: INSERT messages { direction:'outbound', sender_type:'rule',<br/>status:'sending', metadata:{ rule_id } }
              OmniSvc->>Strategy: pushMessage({ channelAccountId, to, content })
              alt isSuccess
                Strategy-->>OmniSvc: { isSuccess: true }
                OmniSvc->>DB_O: UPDATE messages SET status='sent'<br/>⚠️ ข้าม sla_met update (sender_type != 'agent' → ไม่ advance first human response)
                OmniSvc->>DB_O: UPDATE automation_rules SET fired_count = fired_count + 1
                OmniSvc->>Redis: SET automation:cooldown:{firstRule.id}:{conv} EX cooldown_minutes×60
                OmniSvc->>Redis: PUBLISH omnichat:events { type:'message:new', payload:{ message, attachments:[] } }
                Redis-->>GW: message event
                GW->>FE: socket.emit("message:new") → room tenant:{tenantId}
              else send failed
                Strategy-->>OmniSvc: { isSuccess:false, errorMessage }
                OmniSvc->>DB_O: UPDATE messages SET status='failed', delivery_message=errorMessage
              end
            else TIKTOK / SHOPEE (ส่งไม่ได้)
              OmniSvc->>OmniSvc: skip auto-reply (tag ติดไปแล้วด้านบน) — log info ไม่ error
            end
          end
        end
      end
    end
  end
```

**Notes:**
- **hook point:** `RuleEngine.evaluate()` เรียกต่อท้าย `createInbound()` แบบ async void (fire-and-forget) เหมือน AI auto-assign เดิม (`messages.service.ts:307-317`) — ไม่ block การ ingest message
- **guard #1 (bot skip):** trigger เฉพาะ `sender_type='contact'` + `direction='inbound'` → bot/system/agent/rule message ไม่ fire (กันเคส Shopee notification มีคำว่า 'ยกเลิก')
- **guard #2 (dedup 5s):** `SET NX EX 5` keyed by content hash — ต่างจาก dedup 24h เดิมที่ webhook gateway (กันคนละชั้น)
- **only-first-wins:** auto-reply ส่งจาก rule เก่าสุด (created_at ASC) ที่ match — rule auto-reply อื่น skip แต่ **add_tag ของทุก rule ยังทำงาน** (ตาม EPIC: Rule B auto-reply skip แต่ tag shopee ติด)
- **SLA attribution (สำคัญ):** ปัจจุบัน `sendMessage()` set `sla_status='met'` ตอน push success โดยไม่เช็ค sender_type (`conversations.service.ts:765-795`) — auto-reply path ที่นี่ **ไม่เรียก** logic นั้น (sender_type='rule') → FRT/first-human-response ไม่ถูก advance โดย bot
- **cooldown per-conversation-per-rule (ครอบทั้ง 2 action):** key `automation:cooldown:{rule_id}:{conv}` SET หลัง action ทำงาน — **auto-reply** ใช้ `cooldown_minutes` ที่ตั้งใน wizard (กัน loop reply→trigger) · **add_tag** ใช้ default ระบบ `RULE_TAG_COOLDOWN_MINUTES` (wizard ไม่ให้ตั้ง — ค่าเริ่มต้นรอ PO เคาะ, เสนอ 60 นาที)
- **tag integrity (EPIC):** agent ลบ tag ที่ rule ติด → ในช่วง cooldown rule **ไม่ติดกลับ** (tag stay ลบ) จนกว่า cooldown หมด + มี message match ใหม่ — กันเคส "tag เด้งกลับทำให้ agent งง" ✅ · ปกติ (tag ยังอยู่) dedup-on-active กันซ้ำอยู่แล้ว, cooldown คุมเฉพาะเคส re-add หลังถูกลบ
- **channel capability:** เช็คก่อนส่งจาก `strategy.registry.ts` — TikTok `pushMessage` คืน not-supported, Shopee ไม่มี strategy → skip auto-reply เงียบ (tag ยังติด)
- **fired_count** เพิ่มเมื่อ action execute จริง (tag ติด / auto-reply ส่งสำเร็จ) — atomic `increment`
- **engine cache** `automation:rules:{tenant_id}` (active-only, created_at ASC) — อ่านที่นี่, **invalidate (DEL) โดย CRUD ทุกครั้งที่ save/toggle/delete** (ดู [RA-01 CRUD](./RA-01_rule_automation_sequence.md))

---

## Transport Reference (Execution)

| From                    | To                      | Protocol       | Key                                                          |
| ----------------------- | ----------------------- | -------------- | ------------------------------------------------------------ |
| omnichat-normalizer     | omnichat-service        | HTTP           | `POST /messages/inbound` (existing — trigger ของ engine)     |
| omnichat-service        | Channel Strategy        | in-process     | `StrategyRegistry.get(channel).pushMessage()` (auto-reply send) |
| omnichat-service        | Redis                   | GET/SET        | `automation:rules:{tenant_id}` (EX 3600 — engine active-rules cache; DEL โดย CRUD) |
| omnichat-service        | Redis                   | SET NX         | `automation:dedup:{tenant}:{conv}:{hash}` (EX 5)             |
| omnichat-service        | Redis                   | GET/SET        | `automation:cooldown:{rule_id}:{conv}` — auto_reply: `cooldown_minutes`×60 · add_tag: `RULE_TAG_COOLDOWN_MINUTES`×60 |
| omnichat-service        | Redis                   | PUBLISH        | `omnichat:events` (`message:new` / `conversation:updated`)   |
| Redis                   | api-gateway (WebSocket) | SUB message    | `omnichat:events`                                            |
| api-gateway (WebSocket) | workspace-admin         | Socket.io emit | `message:new` / `conversation:updated` → room `tenant:{tenantId}` |

---

## Changes to Existing Code (Execution)

| File / Layer                                                  | Change                                                                                         |
| ------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `omnichat-service/src/automation/rule-engine.service.ts` (new) | `evaluate()` — guards (bot skip, dedup 5s), load active rules, evaluate conditions, execute actions (auto-reply + auto-tag) |
| `omnichat-service/src/messages/messages.service.ts`           | hook `RuleEngine.evaluate()` ต่อท้าย `createInbound()` (async void, fire-and-forget)            |
| `omnichat-service/src/conversations/conversations.service.ts` | `sendMessage()` SLA-met guard: skip เมื่อ `sender_type !== 'agent'` (auto-reply ของ rule ไม่ advance FRT) |
| `omnichat-service` channel strategies                          | ใช้ `StrategyRegistry.get(channel).pushMessage()` เดิม — เพิ่ม path ส่งจาก rule (sender_type='rule') |

> migration (`AutomationRule`, `tagged_by_type`, `sender_type` 'rule' value) ทำใน **RA-01** — execution แค่ "ใช้" field เหล่านั้น

---

## TODO Tracker (Execution — RA-02/03/04)

| ref     | งาน                                                              | story    | blocked by         |
| ------- | ---------------------------------------------------------------- | -------- | ------------------ |
| RA-02   | condition evaluation (keyword / channel / business_hours + AND/OR) | RA-02 | RA-01 engine skeleton |
| RA-02   | RuleEngine guards (bot skip, dedup 5s) + load/eval active rules  | RA-02    | RA-01              |
| RA-03   | auto-reply execute (template vars, cooldown, only-first-wins)    | RA-03    | RA-02              |
| RA-03   | SLA-met guard (skip `sender_type='rule'`) — ใน conversations.service | RA-03 | RA-03              |
| RA-04   | auto-tag execute (append-only, `tagged_by_type`, dedup, cooldown) | RA-04  | RA-02              |
