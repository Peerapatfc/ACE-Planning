# EPIC ACE-1439: Search / Filter / Sort / Saved Views — คำอธิบายแบบเข้าใจง่าย

## สรุปภาพรวม

Search/Filter/Sort/Saved Views คือชุด story ที่ทำให้ Agent ค้นหาและจัดการ conversation ใน Unified Inbox ได้อย่างมีประสิทธิภาพ — ตั้งแต่พิมพ์คำค้น → กรองตามเงื่อนไข → เรียงลำดับ → บันทึก preset ไว้ใช้ซ้ำ

**เปรียบเทียบง่าย ๆ:**
Inbox ที่ไม่มี search/filter เหมือนกล่องจดหมายที่กองรวมกันหมด — ต้องไล่อ่านทีละบรรทัด EPIC นี้คือการสร้าง "ช่องค้นหา + ฟิลเตอร์ + ปุ่มจัดเรียง + bookmark" ให้ Agent หา conversation ที่ต้องการได้ภายในไม่กี่วินาที

---

## 5 Stories ในนี้ทำอะไรบ้าง?

| Story | ชื่อ | ทำอะไร |
|---|---|---|
| **ACE-1440** | Unified Search with Results | search bar ที่ค้นทุก field พร้อมกัน + แสดงผลแบบ grouped |
| **ACE-1441** | Filter System | กรอง conversation ด้วย channel, status, assignee, overdue |
| **ACE-1442** | Sort Options | เรียงรายการด้วย 3 โหมด (latest, oldest waiting, SLA) |
| **ACE-1450** | User Saved Views | บันทึก preset filter+sort เป็น pill สำหรับสลับด่วน |
| **ACE-1443** | Combined Query Semantics & State Management | "กติกากลาง" ว่า search+filter+sort+saved view ทำงานร่วมกันยังไง |

### ลำดับการพึ่งพากัน

```
ACE-1441 (Filter System)  ←── ต้องมี filter ก่อน
ACE-1442 (Sort Options)   ←── ต้องมี sort ก่อน
    │
    ├──▶ ACE-1440 (Search)       ← search ต้องเข้าใจ filter state
    └──▶ ACE-1450 (Saved Views)  ← saved view บันทึก filter+sort
              │
              ▼
        ACE-1443 (Semantics)  ←── cross-cutting: กำหนดว่าทุกอย่างรวมกันยังไง
```

> ACE-1443 ไม่ได้ทำ UI เพิ่ม แต่เป็น "spec" ที่ทุก story ต้องปฏิบัติตาม — implement ไปพร้อมกับ story อื่น

---

## 1. ภาพรวม Architecture — Query Pipeline

ทุก interaction ในหน้า Inbox (search / filter / sort / saved view) ผ่าน pipeline เดียวกัน:

```
Agent พิมพ์ / กดปุ่ม
        │
        ▼
  Query State (client)
  ┌─────────────────────────────────────┐
  │  search_query: "refund"             │
  │  filters: { channel: ["LINE"],      │
  │             status:  ["open"] }     │
  │  sort:    "latest_activity"         │
  │  view:    "My Open" (pill)          │
  └─────────────────────────────────────┘
        │
        ▼ (debounce 300ms สำหรับ search)
  API Request
  GET /api/v1/conversations
       ?q=refund
       &channel=LINE
       &status=open
       &sort=last_message_at:desc
        │
        ▼
  Backend: Final Result Set = Search AND Filters
        │
        ├──▶ Sort applied
        └──▶ Paginated response
                │
                ▼
          Inbox List  +  Search Sections
          (CONVERSATIONS / MESSAGES)
```

**กฎหลัก (ACE-1443):**
- Result set = **Search AND Filter** (ไม่ใช่ OR)
- Sort ใช้ **หลัง** filter แล้วเสมอ
- Saved view **แทนที่** state ทั้งหมด (ไม่ merge)
- Pagination cursor ผูกกับ query state — เปลี่ยน query → reset หน้า 1

---

## 2. ACE-1440: Unified Search — search แล้วเห็นอะไร?

### ผลลัพธ์ 2 sections ในที่เดียว

```
┌─────────────────────────────────────────┐
│  🔍 refund                           ✕  │   ← search bar (debounce 300ms, min 2 chars)
└─────────────────────────────────────────┘

CONVERSATIONS (3)                           ← match จาก contact name, identifier, order ID, tag
┌─────────────────────────────────────────┐
│ 👤 คุณสมชาย  LINE 🟢 open  10:32       │
│ 🏷 VIP  | "...ขอ refund ออเดอร์..."    │
├─────────────────────────────────────────┤
│ 👤 ORD-8823  Shopee 🟡 pending  09:15  │
│ ...                                     │
├─────────────────────────────────────────┤
│              ดูทั้งหมด (3)              │   ← แสดงเมื่อผลมากกว่า 5
└─────────────────────────────────────────┘

MESSAGES (12)                               ← match จาก message text
┌─────────────────────────────────────────┐
│ 👤 คุณมานี  LINE  09:00                │
│ "ต้องการขอ **refund** สินค้าครับ"      │   ← keyword highlighted
├─────────────────────────────────────────┤
│ ...                                     │
├─────────────────────────────────────────┤
│              ดูทั้งหมด (12)             │
└─────────────────────────────────────────┘
```

- Section ไหนไม่มีผล → **ซ่อน** section นั้น
- คลิก CONVERSATIONS → เปิด conversation
- คลิก MESSAGES → เปิด conversation + scroll ไปยัง message ที่ match + highlight

### Search ค้นจาก Field อะไรบ้าง?

```
ทุก channel (common fields):
  ✅ Contact display name
  ✅ Contact identifiers (masked — ค้นด้วยค่าจริงได้)
  ✅ Message text
  ✅ Tag บน conversation (text match: พิมพ์ "VIP" → เจอ conversation ที่มี tag "VIP")
  ✅ Conversation ID
  ✅ Order ID ที่ลูกค้าพิมพ์ในข้อความ

Per-channel identifiers:
  LINE     → LINE User ID, display name
  Facebook → PSID, display name / page name
  Instagram→ IG User ID, username (@handle)
  Shopee   → Buyer ID, Shop Buyer ID, Shopee Order ID  ← สำคัญสุด
  Lazada   → Buyer ID, Lazada Order ID
  TikTok   → TikTok User ID, display name, TikTok Order ID
  Shopify  → Customer name, Order #1234, email (masked, partial OK)

Phase 1 ยังไม่รองรับ:
  ❌ Product name / SKU
  ❌ Phone number
  ❌ System event text
```

### Known Limitation: Tag Search

```
✅ พิมพ์ "VIP" → เจอ conversation ที่มี tag ชื่อ "VIP"   (Phase 1: text match)
⚠️ ถ้า tag "VIP" ถูก rename → saved view ที่บันทึก query "VIP" จะหาไม่เจอ
🔧 R2: เปลี่ยนไปใช้ tag_id filter แทน text match
```

---

## 3. ACE-1441: Filter System — กรองด้วยอะไรได้บ้าง?

### 4 Filters ใน MVP

```
┌──────────────────────────────────────────────────────────────┐
│  Channel ▼  │  Status ▼  │  Assignee ▼  │  Overdue ▼ (SLA)  │
│  LINE ✓     │  open ✓    │  mine        │  (hidden ถ้า SLA   │
│  Shopee ✓   │  in prog.  │  unassigned  │   ปิดอยู่)         │
│  ...        │  pending   │  all         │                    │
│             │  completed │  ชื่อ agent  │                    │
└─────────────────────────┬────────────────────────────────────┘
                          │
              Active Filter Chips:
              [LINE ✕] [Shopee ✕] [open ✕]    ← กด ✕ เพื่อลบทีละตัว
              [Reset all]
```

| Filter | ประเภท | หมายเหตุ |
|---|---|---|
| Channel | Multi-select (OR ภายใน) | LINE OR Shopee AND filter อื่น |
| Status | Multi-select | ไม่เลือก = แสดงทุก status (4 อย่าง) |
| Assignee | Single-select | mine / unassigned / all / ชื่อ agent |
| Overdue | Toggle | ซ่อนทั้งหมดเมื่อ SLA feature ปิด |

### Filter + Search = AND เสมอ

```
filter: channel=LINE, status=open
search: "refund"

Result = (channel=LINE AND status=open AND message contains "refund")

                  ┌──────────────┐
  All convs ──▶   │ Filter (AND) │──▶ Filtered set ──▶ Sort ──▶ List
                  └──────────────┘
                        ▲
                    search query
                    เป็นเงื่อนไข
                    หนึ่งใน AND
```

### URL Params — Filter state เก็บใน URL

```
?channel=LINE,Facebook&status=open,in_progress

→ กด Refresh / แชร์ลิงก์ → filter ยังอยู่ครบ
```

---

## 4. ACE-1442: Sort Options — เรียงแบบไหน ใช้เมื่อไหร่?

### 3 Sort Modes

| Mode | เรียงด้วย | Use Case |
|---|---|---|
| **Latest activity** _(default)_ | `last_message_at DESC` | monitoring ทั่วไป — ดูที่มีความเคลื่อนไหวล่าสุด |
| **Oldest waiting** | `last_inbound_at ASC` (NULLS LAST) | triage — หา conversation ที่รอนานสุดยังไม่ตอบ |
| **SLA due soonest** | `sla_due_at ASC` (NULLS LAST) | deadline — เน้น conversation ที่ใกล้หมดเวลาตอบ |

### Sort ใช้กับ Conversation list เท่านั้น

```
Sort dropdown เปลี่ยน
        │
        ├──▶ CONVERSATIONS section  ← จัดเรียงใหม่ ✓
        └──▶ MESSAGES section       ← ไม่ได้รับผล (ใช้ relevance ordering ตลอด)
```

### Pagination Stability

```
Sort: Oldest waiting
Page 1: conv A (รอ 2ชม), conv B (รอ 1.5ชม), conv C (รอ 1ชม) ...
        │
        │ ระหว่างนี้: ลูกค้าส่งข้อความเข้า conv X ใหม่
        │
Page 2: ต่อจาก page 1 ตาม cursor เดิม  ← ไม่กระโดดไปอยู่หน้า 1

[New conversations available]  ← banner แจ้ง ให้กด refresh เอง
```

> ถ้า sort เปลี่ยน → pagination cursor reset → เริ่มหน้า 1 ใหม่

---

## 5. ACE-1450: User Saved Views — บันทึก preset ยังไง?

### Saved View เก็บอะไร?

```typescript
interface SavedView {
  id:            string
  user_id:       string       // per-user, ไม่แชร์ข้าม agent (Phase 1)
  name:          string       // ตั้งชื่อเอง, ห้ามซ้ำ
  filters:       FilterState  // channel, status, assignee, overdue
  sort:          SortMode     // latest / oldest_waiting / sla_due_soonest
  include_query: boolean      // บันทึก search query ด้วยไหม?
  query_text?:   string       // ถ้า include_query=true
  is_default:    boolean      // โหลดอัตโนมัติตอนเปิด inbox
}
```

### Pills Row — หน้าตา UI

```
[All] [My Open] [Unassigned] [In Progress] [Pending] [Overdue]  ← System pills (ลบไม่ได้)
[LINE Only ✕] [VIP Cases ✕] [My SLA ✕]  [+ Save view]          ← User saved views
```

### Apply View = แทนที่ State ทั้งหมด

```
ก่อนกด:  query="refund", filter=LINE, sort=latest
กด pill "My SLA" (ที่บันทึกไว้: filter=all, sort=sla_due_soonest)

หลังกด:  query=""        ← ถูก replace (ถ้า include_query=false)
          filter=all      ← ถูก replace
          sort=sla_due    ← ถูก replace
          pagination      ← reset → page 1
```

### กฎที่ต้องรู้

```
✅ Max 20 saved views per user
   → เกิน: "คุณมี saved views ครบ 20 อัน กรุณาลบก่อนสร้างใหม่"

✅ ชื่อซ้ำไม่ได้
   → warning + บันทึกไม่ผ่าน

✅ ลบ default view → ระบบ fallback ไปที่ System Default View

✅ R2: shared team views, pill reorder
```

### System Default View (Ground Zero)

```
Sort:    last_message_at DESC (Latest activity)
Filter:  ALL status + ALL channels + ALL assignees
Search:  empty

คือ state ที่ "Reset all" จะพากลับมาเสมอ
```

---

## 6. ACE-1443: Query Semantics — กติกากลางที่ทุก story ต้องปฏิบัติตาม

### State Actions Table

| Action | ผลที่เกิด | หมายเหตุ |
|---|---|---|
| พิมพ์ใน search bar | เปิด search mode, filter ยังอยู่ | AND semantics ยังคง |
| กด ✕ บน search bar (Clear search) | ล้างแค่ query text, filter+sort ยังอยู่ | กลับเป็น inbox list view |
| กด ✕ บน filter chip | ลบ filter นั้น, query+sort ยังอยู่ | |
| กด pill (saved view) | replace filter+sort+query ทั้งหมด | pagination reset |
| กด "Reset all" | ล้างทุกอย่าง → System Default View | ground zero |
| เปลี่ยน sort mode | reorder list เดิม, ไม่แตะ filter/query | pagination reset |

### Clear Search ≠ Reset All

```
Clear Search (✕ บน search bar):
  query     → ลบ ✓
  filters   → คงอยู่
  sort      → คงอยู่
  saved view→ ยังแสดง pill active

Reset All (ปุ่มแยกต่างหาก):
  query     → ลบ ✓
  filters   → ล้าง ✓
  sort      → reset → latest activity ✓
  saved view→ ไม่มี pill active ✓
  → กลับไป System Default View
```

### UI State ที่ต้องแสดงให้เห็นตลอด

```
┌──────────────────────────────────────────────────────────────┐
│ Active View: My Open              ← ชื่อ saved view ที่ active│
├──────────────────────────────────────────────────────────────┤
│ [LINE ✕] [open ✕]                ← filter chips              │
├──────────────────────────────────────────────────────────────┤
│ 🔍 refund  ✕   [Sort: Oldest ▼]  ← query + sort label        │
├──────────────────────────────────────────────────────────────┤
│                                  [Reset all]                 │
└──────────────────────────────────────────────────────────────┘
```

> ทุก element ข้างบนต้องอ่านได้ + ทดสอบได้ (QA ใช้ตรวจสอบ state)

### Pagination Rules

```
เปลี่ยน query state (search / filter / sort / view):
  → cursor reset → โหลดหน้า 1 ใหม่

pagination ระหว่างอยู่ในหน้าเดิม:
  → cursor คงอยู่กับ sort key เดิม
  → ข้อความเข้าใหม่ไม่กระโดดขึ้นหน้า 1 เอง
  → แสดง "New conversations available" banner แทน
```

---

## สรุปตัวเลข

| หมวด | จำนวน |
|---|---|
| Stories | 5 stories (ACE-1440 ถึง ACE-1443, ACE-1450) |
| Story Points รวม | 33 SP |
| Filter fields (MVP) | 4 (channel, status, assignee, overdue) |
| Sort modes | 3 (latest activity, oldest waiting, SLA due soonest) |
| System pills (hardcoded) | 5 (All, My Open, Unassigned, In Progress, Pending / Overdue) |
| Max saved views per user | 20 |
| Search sections | 2 (CONVERSATIONS + MESSAGES) |

---

## ตัวอย่าง End-to-End: Agent ค้นหา conversation และบันทึก preset

```
1. Agent เปิด Inbox (default state)
   → Sort: latest activity, no filter, no search
   → Pill active: "All" (System Default View)

2. Agent กรอง channel=LINE + status=open
   → Filter chips: [LINE ✕] [open ✕]
   → List แสดงเฉพาะ LINE + open conversations

3. Agent พิมพ์ "refund" ใน search bar
   → Debounce 300ms → API call
   → Result: Search AND (channel=LINE AND status=open)
   → แสดง CONVERSATIONS(2) + MESSAGES(5) grouped sections

4. Agent คลิก message result ของ "สนใจขอ refund ออเดอร์ ORD-8823"
   → เปิด conversation ของ คุณสมชาย
   → Timeline scroll ไปหา message นั้น + highlight

5. Agent กลับ Inbox → กด ✕ บน search bar (Clear search)
   → query ล้าง, filter LINE+open ยังอยู่
   → กลับเป็น Inbox list แสดง LINE open ทั้งหมด

6. Agent บันทึก preset นี้ → กด "+ Save view"
   → ตั้งชื่อ "LINE Open"
   → include_query: OFF (ไม่เก็บ query text)
   → บันทึก → pill "LINE Open" ปรากฏใน row

7. Agent เปิด Inbox ครั้งใหม่
   → State กลับ System Default View (ยังไม่ set default)
   → กดปุ่ม pill "LINE Open" → filter LINE+open + sort latest apply ทันที

8. Agent set "LINE Open" เป็น default view
   → ครั้งถัดไปเปิด Inbox → "LINE Open" โหลดอัตโนมัติ

9. Agent ต้องการดู conversation รอนานสุด
   → เปลี่ยน sort → "Oldest waiting"
   → List reorder: conversation ที่ลูกค้ารอตอบนานสุดขึ้นบน
   → Pill "LINE Open" ยัง active แต่ sort override

10. Agent กด "Reset all"
    → ทุกอย่างล้าง → กลับ System Default View
    → Sort: latest activity, no filter, no search, pill "All" active ✓
```

---

## Quick Reference: ปุ่มต่าง ๆ ทำอะไร?

| ปุ่ม / Action | ผล |
|---|---|
| ✕ บน search bar | ล้าง query เท่านั้น |
| ✕ บน filter chip | ลบ filter นั้น |
| กด pill | แทนที่ filter+sort+query ทั้งหมดด้วย preset ของ pill นั้น |
| กด pill ซ้ำ | reset กลับ System Default View |
| Reset all | ล้างทุกอย่าง → System Default View |
| + Save view | บันทึก filter+sort (+ optional query) เป็น pill ใหม่ |
