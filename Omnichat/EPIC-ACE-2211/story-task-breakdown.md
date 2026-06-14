# EPIC-ACE-2211: Story Task Breakdown

Task แต่ละ story พร้อมคำอธิบายว่าทำอะไร — อิงจากสิ่งที่มีอยู่แล้วใน repo จริง (เฉพาะที่ยังต้องทำ)

> **Legend:** 🔧 มีโค้ดอยู่แล้วแต่ต้องแก้ | (ไม่มีไอคอน) สร้างใหม่ทั้งหมด

---

## สิ่งที่มีอยู่แล้วใน repo (อย่าทำซ้ำ)

| สิ่งที่มี | ไฟล์ | หมายเหตุ |
|----------|------|----------|
| BullMQ worker infrastructure | `apps/omnichat-gateway/` | ใช้แล้วใน SLA breach job — reuse pattern |
| Inbound message handler | `apps/omnichat-service/src/messages/` | hook จุดนี้สำหรับ rule evaluation trigger |
| Business hours logic | `apps/omnichat-service/src/` (SETTINGS-02) | reuse BH evaluation ใน rule engine |
| Tag CRUD + conversation tag update | `apps/omnichat-service/src/tags/` | reuse สำหรับ auto-tag executor |
| Channel send APIs | per-channel integration services | reuse สำหรับ auto-reply executor |
| `config_sla` RBAC permission pattern | `packages/shared/src/types/rbac.types.ts` | ใช้ pattern นี้สำหรับ `config_automation_rules` |
| Settings shell (SETTINGS-01) | `apps/workspace-admin/src/app/(main)/dashboard/settings/` | เพิ่ม Automation > Rules route ตรงนี้ |
| `sender_type` enum ใน messages | conversations/messages schema | ต้องเพิ่ม `'rule'` value เข้า enum |

---

## RA-01 — Rule Management (CRUD) (8 SP)

> **เป้าหมาย:** DB + API CRUD สำหรับ automation_rules + frontend shell ทั้งหมด (list, wizard, permission)

---

### Task 1.1 — DB migration: `automation_rules` table
**ทำอะไร:** สร้างตารางหลักสำหรับเก็บ rule configuration

**Location:** `apps/omnichat-service/prisma/schema.prisma`

```sql
-- automation_rules table
rule_id           UUID PRIMARY KEY DEFAULT gen_random_uuid()
workspace_id      UUID NOT NULL
name              VARCHAR(255) NOT NULL
conditions        JSONB NOT NULL  -- { logic: 'and'|'or', items: [...] }
action_type       ENUM('auto_reply', 'add_tag') NOT NULL
action_config     JSONB NOT NULL  -- per action_type
is_active         BOOLEAN DEFAULT true
fired_count       INTEGER DEFAULT 0
created_by        UUID NOT NULL
updated_by        UUID
created_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW()
updated_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW()
-- INDEX: (workspace_id, is_active, created_at) สำหรับ list + execution order
```

**conditions JSONB structure:**
```json
{
  "logic": "and",
  "items": [
    { "type": "keyword", "operator": "contains", "value": "ยกเลิก" },
    { "type": "channel", "value": ["shopee", "lazada"] },
    { "type": "business_hours", "operator": "outside", "use_workspace": true }
  ]
}
```

---

### Task 1.2 — API: CRUD endpoints สำหรับ automation rules
**ทำอะไร:** สร้าง REST endpoints ครบ CRUD + toggle

| Method | Path | ทำอะไร |
|--------|------|--------|
| `GET` | `/automation-rules` | list ทุก rule ของ workspace แยก active/inactive |
| `POST` | `/automation-rules` | สร้าง rule ใหม่ — block ถ้า active = 20 |
| `PATCH` | `/automation-rules/:id` | แก้ไข rule |
| `DELETE` | `/automation-rules/:id` | hard delete — Admin เท่านั้น |
| `PATCH` | `/automation-rules/:id/toggle` | enable/disable rule |

**Permission:** `config_automation_rules` (Admin/Supervisor สร้าง/แก้ไข, Admin เท่านั้นลบ, ทุก role GET)

**Location:** `apps/api-gateway/src/omnichat/automation-rules/` (ใหม่)

---

### Task 1.3 — RBAC: `config_automation_rules` permission
**ทำอะไร:** เพิ่ม permission ใหม่เข้า RBAC types และ seed default roles

**ไฟล์ที่แก้:**
- `packages/shared/src/types/rbac.types.ts` — เพิ่ม `config_automation_rules`
- seed/migration สำหรับ assign permission ให้ Admin + Supervisor

---

### Task 1.4 — UI: Rule list page
**ทำอะไร:** สร้างหน้า Settings > Automation > Rules แสดง Active / Inactive section

**Location:** `apps/workspace-admin/src/app/(main)/dashboard/settings/automation/rules/page.tsx` (ใหม่)

**Layout:**
- Header: "Automation Rules" + "Active (X/20)" counter + "+ New Rule" button + pills filter (All / Auto-reply / Add tag)
- Active section: rule cards sorted by created_at
- Inactive section: collapsed by default, แสดง "Inactive (X)" — click ขยาย

---

### Task 1.5 — UI: Rule card component
**ทำอะไร:** single rule card แสดง name, summaries, toggle, fired count, kebab

| Element | รายละเอียด |
|---------|----------|
| Rule name | ชื่อ + badge action type (Auto-reply / Add tag) |
| Trigger summary | เช่น "Keyword: ยกเลิก · Shopee, Lazada" |
| Action summary | เช่น "Auto-reply · cooldown 5 min" |
| Toggle | enable/disable inline — ไม่ reload |
| Fired count | "ทำงานแล้ว 87 ครั้ง" |
| created_by/updated_by | subtle text + relative time |
| Kebab menu (⋮) | Edit / Delete (Delete เฉพาะ Admin) |

**Location:** `apps/workspace-admin/src/app/(main)/dashboard/settings/automation/rules/_components/rule-card.tsx` (ใหม่)

---

### Task 1.6 — UI: Action-first entry modal
**ทำอะไร:** modal ที่เปิดเมื่อกด "+ New Rule" ถามก่อนว่าจะทำ action อะไร

**ทำไม:** ถ้าเปิด blank form ทันที admin ไม่รู้ว่าจะเริ่มจากตรงไหน

**Location:** `apps/workspace-admin/src/app/(main)/dashboard/settings/automation/rules/_components/action-first-modal.tsx` (ใหม่)

---

### Task 1.7 — UI: Rule wizard shell (2 steps) + step indicator
**ทำอะไร:** wizard container ที่ใช้ร่วมกันทั้ง create และ edit

**Step flow:**
```
[Step 1: Trigger Conditions] → [Step 2: Action Detail (ขึ้นกับ action)] → [Review/Save]
```

- Step indicator บนสุด — step ที่ผ่านแล้ว clickable
- Auto-generate rule name เมื่อถึง review: `Action · Trigger` เช่น "Auto-reply · Outside hours"
- Rule name field แก้ได้ก่อน save
- Wizard ใช้ pre-filled data เมื่อ edit (ดึงจาก GET /automation-rules/:id)

**Location:** `apps/workspace-admin/src/app/(main)/dashboard/settings/automation/rules/_components/rule-wizard.tsx` (ใหม่)

---

### Task 1.8 — UI: Hard delete confirmation dialog
**ทำอะไร:** dialog ยืนยันก่อน hard delete แสดงชื่อ rule + fired count + warning

**Content:**
```
ลบ rule "Auto-reply · Outside hours"?
Rule นี้ทำงานไปแล้ว 87 ครั้ง
⚠️ จะถูกลบถาวร ไม่สามารถกู้คืนได้

[ลบถาวร]  [Cancel]
```

**Location:** `apps/workspace-admin/src/app/(main)/dashboard/settings/automation/rules/_components/delete-rule-dialog.tsx` (ใหม่)

---

## RA-02 — Define Trigger Conditions (5 SP)

> **เป้าหมาย:** Rule evaluation engine (BE) + Wizard Step 1 UI + test panel

---

### Task 2.1 — Rule engine: message hook + evaluation orchestrator
**ทำอะไร:** hook `evaluateRules()` เข้าใน inbound message handler — trigger point หลักของระบบทั้งหมด

**Location:** `apps/omnichat-service/src/messages/messages.service.ts` 🔧

```typescript
// หลังจาก save inbound message
if (message.sender_type !== 'bot' && message.sender_type !== 'system') {
  await this.ruleEngine.evaluateAndExecute(conversation, message)
}
```

**Location (engine):** `apps/omnichat-service/src/automation-rules/rule-engine.service.ts` (ใหม่)

---

### Task 2.2 — Rule engine: bot sender skip + message deduplication
**ทำอะไร:** 2 background guards ที่รันก่อน evaluate ทุก rule

**Bot skip:**
```typescript
if (['bot', 'system'].includes(message.sender_type)) {
  logger.debug(`skipped: sender_type = ${message.sender_type}`)
  return
}
```

**Message dedup (5s window):**
```typescript
const dedupeKey = `rule_dedup:${conversationId}:${hash(message.content)}`
const exists = await redis.get(dedupeKey)
if (exists) return  // skip
await redis.set(dedupeKey, '1', 'EX', 5)  // TTL 5 วินาที
```

---

### Task 2.3 — Condition evaluator: Keyword (contains / exact)
**ทำอะไร:** evaluate keyword condition — case-insensitive ไทย-อังกฤษ

```typescript
function evaluateKeyword(condition: KeywordCondition, messageText: string): boolean {
  const normalized = messageText.toLowerCase()
  const keyword = condition.value.toLowerCase()
  if (condition.operator === 'contains') return normalized.includes(keyword)
  if (condition.operator === 'exact') return normalized === keyword
  return false
}
```

**Special chars:** escape ก่อน match — ไม่ treat เป็น regex

---

### Task 2.4 — Condition evaluator: Channel
**ทำอะไร:** ตรวจว่า conversation.channel อยู่ใน channel list ที่ rule กำหนด

```typescript
function evaluateChannel(condition: ChannelCondition, channel: string): boolean {
  return condition.value.includes(channel)  // multi-select OR logic
}
```

---

### Task 2.5 — Condition evaluator: Business hours (Workspace toggle + custom)
**ทำอะไร:** ตรวจว่าเวลาปัจจุบัน within/outside business hours ที่กำหนด

**Workspace toggle on:** ดึง BH config จาก workspace settings ทุกครั้ง (ไม่ cache)

**Custom:** ใช้ day of week + time range + timezone ที่ระบุใน condition

**Handle midnight-crossing:** ถ้า start > end (เช่น 22:00–06:00) → normalize เป็น 2 ranges

**ไฟล์ที่แก้:** reuse business hours calculation logic จาก SETTINGS-02

---

### Task 2.6 — Condition evaluator: AND/OR combinator
**ทำอะไร:** combine results จาก individual evaluators ด้วย logic ที่ rule กำหนด

```typescript
function evaluateConditions(conditions: RuleCondition[], logic: 'and' | 'or', context: EvalContext): boolean {
  const results = conditions.map(c => evaluateCondition(c, context))
  return logic === 'and' ? results.every(Boolean) : results.some(Boolean)
}
```

---

### Task 2.7 — UI: Wizard Step 1 — Condition builder
**ทำอะไร:** Step 1 ใน rule wizard — สร้าง/แก้ condition cards + AND/OR toggle

**Condition card anatomy:** `[Type dropdown] [Operator ถ้ามี] [Value input] [× ลบ]`

**Business hours card:** toggle "ใช้ Workspace hours" default on → ถ้าปิดแสดง custom day picker + time picker (ใช้ component เดิมจาก SETTINGS-02)

**AND/OR toggle:** อยู่ระหว่าง condition cards แบบ inline badge

**Info box:** "Message จาก bot หรือ system อัตโนมัติจะไม่ trigger rule"

**Location:** `apps/workspace-admin/src/app/(main)/dashboard/settings/automation/rules/_components/step-conditions.tsx` (ใหม่)

---

### Task 2.8 — UI: Test panel (real-time match + highlight)
**ทำอะไร:** text input ด้านล่าง condition cards — พิมพ์ข้อความ → highlight card ที่ match/ไม่ match ทันที

**Logic:** evaluate conditions ใน browser ด้วย logic เดียวกับ backend (keyword + channel + BH) โดยไม่ต้อง call API

**Result badge:** Match (สีเขียว) / No match + เหตุผล (สีแดง)

**Location:** `apps/workspace-admin/src/app/(main)/dashboard/settings/automation/rules/_components/condition-test-panel.tsx` (ใหม่)

---

## RA-03 — Send Auto-reply Message (2 SP)

> **เป้าหมาย:** Auto-reply executor (BE) + variable resolver + Wizard Step 2 UI (Auto-reply)

---

### Task 3.1 — Auto-reply executor
**ทำอะไร:** execute auto-reply action — ส่งผ่าน channel เดียวกัน พร้อม guards ครบ

**Location:** `apps/omnichat-service/src/automation-rules/actions/auto-reply.executor.ts` (ใหม่)

**Guards ตามลำดับ:**
1. Skip ถ้า `conversation.status = 'completed'`
2. Check cooldown: query `rule_cooldowns` table หรือ Redis key `cooldown:{ruleId}:{conversationId}` → skip ถ้า active
3. Only-first-wins: รับ flag `autoreply_sent` จาก rule engine — ถ้า true skip
4. Resolve variables → send ผ่าน channel API → retry 3 ครั้ง exponential backoff ถ้า fail
5. บันทึก message ด้วย `sender_type = 'rule'` + update `rule_cooldowns` + set `autoreply_sent = true`

**SLA attribution:**
```typescript
// ไม่ update first_human_response_at เมื่อ sender_type = 'rule'
// first_human_response_at นับเฉพาะ sender_type = 'human'
```

---

### Task 3.2 — Variable resolver + fallback
**ทำอะไร:** resolve template variables ใน message ก่อนส่ง

```typescript
function resolveVariables(template: string, context: ResolveContext, fallbacks: Record<string, string>): string {
  return template
    .replace(/\{\{customer_name\}\}/g, context.customerName ?? fallbacks['customer_name'] ?? '')
    .replace(/\{\{channel\}\}/g, context.channel ?? fallbacks['channel'] ?? '')
    .replace(/\{\{current_time\}\}/g, formatTime(context.now) ?? fallbacks['current_time'] ?? '')
}
```

**Error case:** syntax ผิด เช่น `{{customer name}}` มีช่องว่าง → skip resolve, log warning, ส่ง literal ไป

---

### Task 3.3 — DB: `rule_cooldowns` table (หรือ Redis key pattern)
**ทำอะไร:** เก็บ cooldown state per conversation per rule

**Option A — Redis (แนะนำ):**
```
key: rule_cooldown:{ruleId}:{conversationId}
value: 1
TTL: cooldown_minutes * 60 วินาที
```

**Option B — DB table:**
```sql
rule_id         UUID NOT NULL
conversation_id UUID NOT NULL
last_sent_at    TIMESTAMP WITH TIME ZONE
PRIMARY KEY (rule_id, conversation_id)
```

---

### Task 3.4 — 🔧 เพิ่ม `'rule'` เข้า `sender_type` enum ใน messages
**ทำอะไร:** เพิ่ม value ใหม่เข้า enum ที่มีอยู่แล้ว

**ไฟล์ที่แก้:** `apps/omnichat-service/prisma/schema.prisma` — `MessageSenderType` enum

```prisma
enum MessageSenderType {
  human
  bot
  system
  rule   // ← เพิ่มใหม่
}
```

---

### Task 3.5 — UI: Wizard Step 2 — Auto-reply config
**ทำอะไร:** Step 2 ใน wizard สำหรับ action = auto_reply

**Elements:**
- Multi-line text editor (max 2,000 chars) + character count
- Variable toolbar: `{{customer_name}}` `{{channel}}` `{{current_time}}` — click insert at cursor
- Fallback value inputs (per variable ที่ใช้ใน message)
- Preview panel: resolved real-time ด้วย dummy data (ชื่อ: สมปอง, channel: Shopee, เวลา: 14:30)
- Cooldown field: required, default 5, unit selector (นาที/ชั่วโมง), asterisk
- Info box: "Auto-reply ไม่นับเป็น First Response Time ของ agent"

**Location:** `apps/workspace-admin/src/app/(main)/dashboard/settings/automation/rules/_components/step-action-autoreply.tsx` (ใหม่)

---

## RA-04 — Auto-Tag Conversation (3 SP)

> **เป้าหมาย:** Auto-tag executor (BE) + Wizard Step 2 UI (Add tag) + tooltip บน conversation

---

### Task 4.1 — Auto-tag executor
**ทำอะไร:** execute add_tag action — append-only, dedup, skip gracefully ถ้า tag หาย

**Location:** `apps/omnichat-service/src/automation-rules/actions/auto-tag.executor.ts` (ใหม่)

```typescript
async executeAddTag(conversation: Conversation, tagIds: string[], ruleId: string): Promise<void> {
  const existingTagIds = new Set(conversation.tags.map(t => t.tag_id))
  
  for (const tagId of tagIds) {
    const tag = await this.tagRepo.findById(tagId)
    if (!tag) {
      logger.warn(`tag not found: ${tagId} — skipping`)
      continue  // ไม่ throw ไม่หยุด actions อื่น
    }
    if (existingTagIds.has(tagId)) continue  // dedup — ไม่ duplicate
    
    await this.conversationTagRepo.create({
      conversation_id: conversation.conversation_id,
      tag_id: tagId,
      tagged_by_type: 'rule',
      tagged_by_rule_id: ruleId,
    })
  }
}
```

---

### Task 4.2 — 🔧 เพิ่ม `tagged_by_type` + `tagged_by_rule_id` ใน conversation_tags
**ทำอะไร:** เพิ่ม metadata columns เข้าตาราง conversation_tags ที่มีอยู่แล้ว

**ไฟล์ที่แก้:** `apps/omnichat-service/prisma/schema.prisma`

```sql
tagged_by_type    ENUM('human', 'rule') DEFAULT 'human'
tagged_by_rule_id UUID NULLABLE REFERENCES automation_rules(rule_id) ON DELETE SET NULL
```

---

### Task 4.3 — UI: Wizard Step 2 — Add tag config
**ทำอะไร:** Step 2 ใน wizard สำหรับ action = add_tag

**Elements:**
- Tag picker: search input + scrollable list + checkbox multi-select
- "Create new" option: เมื่อ search ไม่เจอ → แสดง "+ Create tag: [ชื่อ]" → Enter → สร้างและเลือกทันที
- Selected tags: chips พร้อม × ลบออก
- Preview: "จะติด label เหล่านี้: [chip list]"

**Location:** `apps/workspace-admin/src/app/(main)/dashboard/settings/automation/rules/_components/step-action-addtag.tsx` (ใหม่)

---

### Task 4.4 — UI: Tooltip "tagged by rule" บน conversation view
**ทำอะไร:** tag chip ใน conversation ที่ `tagged_by_type = 'rule'` แสดง tooltip เมื่อ hover

**Tooltip text:** "tagged by rule: [ชื่อ rule]"

**ไฟล์ที่แก้:** conversation tag component ที่ render tag chips ใน conversation detail

---

## Summary

| Story | Task ใหม่ | Task แก้ 🔧 | SP |
|-------|-----------|----------|----|
| RA-01 Rule Management | 8 | 0 | 8 |
| RA-02 Trigger Conditions | 7 | 1 | 5 |
| RA-03 Auto-reply | 4 | 1 | 2 |
| RA-04 Auto-tag | 3 | 1 | 3 |
| **รวม** | **22** | **3** | **18 SP** |

---

## Dependency ระหว่าง Task

```
[1.1] automation_rules table
    → [1.2] CRUD APIs
        → [1.3] RBAC permission
        → [1.4–1.8] Frontend (list + wizard + delete dialog)

[2.1] Message hook + rule engine orchestrator ← ต้องมี [1.1] table ก่อน
    → [2.2] Bot skip + dedup guards
    → [2.3–2.6] Condition evaluators (ทำ parallel ได้)
    → (ส่งผล) [3.1] Auto-reply executor
    → (ส่งผล) [4.1] Auto-tag executor

[3.4] sender_type enum migration ← ทำก่อน [3.1]
[4.2] tagged_by_type migration ← ทำก่อน [4.1]

[2.7] Step 1 Conditions UI ← ต้องมี [1.7] wizard shell ก่อน
[2.8] Test panel ← ต้องมี [2.7] ก่อน

[3.5] Step 2 Auto-reply UI ← ต้องมี [1.7] wizard shell ก่อน
[4.3] Step 2 Add tag UI ← ต้องมี [1.7] wizard shell ก่อน
[4.4] Tooltip ← ต้องมี [4.2] migration ก่อน
```

---

## ไฟล์หลักที่ต้องสร้าง/แก้ (จาก repo จริง)

| ไฟล์ | สร้าง/แก้เพราะ |
|------|---------------|
| `apps/omnichat-service/prisma/schema.prisma` | Task 1.1, 3.4, 4.2 — tables + enum ใหม่ |
| `apps/omnichat-service/src/automation-rules/rule-engine.service.ts` | Task 2.1 — orchestrator ใหม่ |
| `apps/omnichat-service/src/automation-rules/actions/auto-reply.executor.ts` | Task 3.1 — executor ใหม่ |
| `apps/omnichat-service/src/automation-rules/actions/auto-tag.executor.ts` | Task 4.1 — executor ใหม่ |
| `apps/omnichat-service/src/messages/messages.service.ts` | Task 2.1 🔧 — hook rule engine เข้า inbound handler |
| `apps/api-gateway/src/omnichat/automation-rules/` | Task 1.2 — CRUD APIs ใหม่ |
| `packages/shared/src/types/rbac.types.ts` | Task 1.3 🔧 — เพิ่ม permission |
| `apps/workspace-admin/src/app/(main)/dashboard/settings/automation/rules/page.tsx` | Task 1.4 — rule list page ใหม่ |
| `apps/workspace-admin/src/app/(main)/dashboard/settings/automation/rules/_components/rule-card.tsx` | Task 1.5 — ใหม่ |
| `apps/workspace-admin/src/app/(main)/dashboard/settings/automation/rules/_components/action-first-modal.tsx` | Task 1.6 — ใหม่ |
| `apps/workspace-admin/src/app/(main)/dashboard/settings/automation/rules/_components/rule-wizard.tsx` | Task 1.7 — ใหม่ |
| `apps/workspace-admin/src/app/(main)/dashboard/settings/automation/rules/_components/step-conditions.tsx` | Task 2.7 — ใหม่ |
| `apps/workspace-admin/src/app/(main)/dashboard/settings/automation/rules/_components/condition-test-panel.tsx` | Task 2.8 — ใหม่ |
| `apps/workspace-admin/src/app/(main)/dashboard/settings/automation/rules/_components/step-action-autoreply.tsx` | Task 3.5 — ใหม่ |
| `apps/workspace-admin/src/app/(main)/dashboard/settings/automation/rules/_components/step-action-addtag.tsx` | Task 4.3 — ใหม่ |
