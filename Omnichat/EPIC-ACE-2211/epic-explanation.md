# EPIC ACE-2211: Rule Automation — คำอธิบายแบบเข้าใจง่าย

## สรุปภาพรวม

Epic นี้คือการสร้าง "ระบบ Rule Automation" ที่ให้ Admin และ Supervisor ตั้งค่าให้ระบบทำงานอัตโนมัติเมื่อมีเงื่อนไขตรง เช่น ลูกค้าพิมพ์คำว่า "ยกเลิก" → ระบบส่งข้อความตอบกลับอัตโนมัติ และติด tag "cancellation-risk" ให้การสนทนาทันที โดยไม่ต้องรอ agent

เป้าหมายหลักคือ **ลด manual work ของทีม support** สร้าง consistent experience ให้ลูกค้า และปล่อยให้ agent โฟกัสกับงานที่ต้องใช้การตัดสินใจจริงๆ

**เปรียบเทียบง่าย ๆ:**
เหมือนเซ็ตระบบ auto-responder อีเมล แต่ฉลาดกว่า — เลือกได้ว่าจะ trigger เมื่อไหร่ (คำ, ช่องทาง, เวลาทำการ) และทำอะไร (ตอบกลับ, ติด label) โดยไม่ต้องให้ developer ช่วยเซ็ต

---

## 1. แนวคิดหลัก (Core Concepts)

### 1.1 Rule คืออะไร

Rule แต่ละตัวประกอบด้วย 2 ส่วน: **Conditions** (เงื่อนไขที่ต้องตรง) และ **Action** (สิ่งที่ระบบทำ)

```
ถ้า [conditions ตรง] → ทำ [action]
```

**ตัวอย่าง Rule:**
- ถ้า keyword contains "ยกเลิก" AND channel = Shopee → ส่ง auto-reply "รับเรื่องแล้วครับ" + ติด tag "cancellation-risk"
- ถ้า business hours = outside AND channel = LINE → ส่ง auto-reply "ขณะนี้นอกเวลาทำการ"

### 1.2 Trigger Conditions (เงื่อนไขที่รองรับ)

| ประเภท | ตัวเลือก | หมายเหตุ |
|--------|---------|----------|
| Keyword match | contains / exact | Case-insensitive ไทย-อังกฤษ |
| Channel | LINE, Facebook, Instagram, Shopee, Lazada, TikTok | Multi-select |
| Business hours | within / outside | รวม day of week + timezone; toggle Workspace hours |

Conditions หลายอันเชื่อมด้วย **AND** (ทุกข้อต้องตรง) หรือ **OR** (ตรงข้อใดข้อหนึ่งก็พอ)

### 1.3 Actions (สิ่งที่ระบบทำ)

| Action | Key config | พฤติกรรม |
|--------|-----------|----------|
| Auto-reply | ข้อความ + template variables + cooldown | ส่งผ่าน channel เดิมที่ลูกค้าส่งมา |
| Add tag | เลือก tag หลายอัน + สร้าง inline ได้ | Append-only ไม่ลบ tag เดิม |

### 1.4 Rule Execution Logic

เมื่อ message เข้า ระบบทำตามขั้นตอนนี้ทุกครั้ง:

1. **Bot check:** message มาจาก bot/system หรือไม่ → ถ้าใช่ skip ทั้งหมด (background)
2. **Dedup check:** message ซ้ำกับ message เดิมใน 5 วินาทีหรือไม่ → ถ้าใช่ skip (background)
3. **Evaluate:** ตรวจ conditions ของทุก active rule พร้อมกัน (single-pass)
4. **Execute:** rules ที่ match ทั้งหมด execute เรียงตาม `created_at` (เก่าสุดก่อน)
   - **Add tag:** ทุก rule ที่ match ติด tag ได้ (append-only)
   - **Auto-reply:** ส่งเพียงครั้งเดียวจาก rule เก่าสุด (only-first-wins) — rule อื่น skip auto-reply แต่ actions อื่นยังทำงาน

> **สิ่งสำคัญ:** single-pass หมายความว่า tag ที่ Rule A เพิ่งเพิ่มจะไม่ trigger Rule B ในรอบเดียวกัน

### 1.5 Background Safety (ทำงานเองไม่ expose ใน UI)

| กลไก | ทำงานยังไง | ป้องกันอะไร |
|------|-----------|------------|
| `sender_type = 'rule'` | message record บอกว่า rule ตอบ ไม่ใช่ agent | KPI agent ผิดพลาด |
| `first_human_response_at` แยก | SLA ไม่นับ auto-reply เป็น FRT | SLA metric บวมเกินจริง |
| Bot sender skip | ตรวจ sender_type ก่อน evaluate | Notification จาก Shopee trigger rule ผิดพลาด |
| Message dedup 5s | evaluate ครั้งเดียวต่อ message เดิม | ส่ง auto-reply ซ้ำจาก double-send |

---

## 2. ส่วนประกอบบนหน้าจอ (UI Components)

### หน้า Rule List (Settings > Automation > Rules)

- **Active section:** rules ที่เปิดอยู่ แสดง counter X/20 (สูงสุด 20 active rules)
- **Inactive section:** collapsed by default — click ขยายเพื่อดู
- **แต่ละ rule card:** ชื่อ rule, trigger summary, action summary, toggle, fired count, created_by/updated_by + relative time, kebab menu (⋮)
- **Pills filter:** แยก All / Auto-reply / Add tag
- **+ New Rule:** เปิด modal ถามก่อนว่า "คุณอยากให้ระบบทำอะไร?" (action-first)

### Action-first Modal

เริ่มจากเลือก Action ก่อน ไม่ใช่ blank form — ลด decision fatigue

```
"คุณอยากให้ระบบทำอะไร?"
┌─────────────────────────┐  ┌──────────────────────────┐
│  ส่งข้อความตอบอัตโนมัติ  │  │  ติด label ให้การสนทนา   │
└─────────────────────────┘  └──────────────────────────┘
```

### Rule Wizard (2 Steps)

- **Step 1 — Trigger Conditions:** เพิ่ม condition cards + เลือก AND/OR + test panel ทดสอบ real-time
- **Step 2 — Action Detail:** ขึ้นอยู่กับ action ที่เลือก (Auto-reply หรือ Add tag)
- Step indicator บน wizard — step ที่ผ่านแล้ว click กลับได้
- Rule name auto-generate จาก action + trigger เช่น `'Auto-reply · Outside hours'` — แก้ได้ก่อน save

### Step 2A: Auto-reply Config

- Text editor multi-line + character count
- Variable toolbar: `{{customer_name}}` `{{channel}}` `{{current_time}}` — click แทรกที่ cursor
- Fallback value per variable (กรณีค่า resolve ไม่ได้)
- Preview panel: resolved message ด้วย dummy data real-time
- Cooldown field (required, min > 0): "ส่งได้สูงสุด 1 ครั้ง ต่อ [5] [นาที] ต่อการสนทนา"

### Step 2B: Add Tag Config

- Tag picker: search + multi-select + create inline (พิมพ์ → Enter → สร้างและเลือกทันที)
- Preview chip list: "จะติด label เหล่านี้: [chip list]"

---

## 3. ลำดับการทำงาน (User Flow)

#### สถานการณ์: ลูกค้าพิมพ์ "ยกเลิก" มาใน Shopee นอกเวลาทำการ

มี rule ตั้งไว้ว่า: keyword contains "ยกเลิก" AND channel = Shopee → auto-reply "รับเรื่องแล้ว" + tag "cancellation-risk"
มี rule อีกตัว: business hours = outside → auto-reply "นอกเวลาทำการ" + tag "off-hours"

1. **ลูกค้าส่งข้อความ "ยกเลิก order ครับ" ผ่าน Shopee เวลา 22:00:**
   - Bot check ผ่าน (ลูกค้าส่งเอง)
   - Dedup check ผ่าน (message ใหม่)
   - Evaluate: Rule A match (keyword + Shopee ✓), Rule B match (outside hours ✓)
   - Execute (เรียงตาม created_at):
     - Rule A: auto-reply "รับเรื่องแล้ว" → **ส่ง ✓** / tag "cancellation-risk" → **ติด ✓**
     - Rule B: auto-reply "นอกเวลาทำการ" → **skip ✗** (Rule A ส่งไปแล้ว — only-first-wins) / tag "off-hours" → **ติด ✓**

2. **ลูกค้าได้รับ 1 ข้อความ** ("รับเรื่องแล้ว") ไม่ใช่ 2 ข้อความ

3. **Conversation มี 2 tags:** "cancellation-risk" + "off-hours"

4. **FRT ยังนับต่อ** เพราะ `sender_type = 'rule'` ไม่กระทบ `first_human_response_at`

#### สถานการณ์: Admin ต้องการลบ rule

1. กด kebab menu (⋮) บน rule
2. ระบบแสดง confirmation dialog: ชื่อ rule + "Rule นี้ทำงานไปแล้ว 87 ครั้ง" + warning "จะถูกลบถาวร"
3. Admin กด "ลบถาวร" → rule หายจาก DB จริง ไม่มี undo

---

## สรุปรายละเอียด (Scope)

| หมวดหมู่ | รายละเอียด |
|---|---|
| Stories ที่พัฒนาใน Epic นี้ | 4 Stories (RA-01 ถึง RA-04) |
| Trigger types | 3 types: Keyword, Channel, Business hours |
| Actions | 2 types: Auto-reply, Add tag |
| Active rule limit | สูงสุด 20 active rules ต่อ Workspace |
| Rule execution | Single-pass evaluate, oldest-first execute |
| Auto-reply dedup | Only-first-wins + cooldown per-conversation-per-rule |
| SLA attribution | `sender_type = 'rule'` ไม่นับ FRT |
| Tag integrity | Append-only, tagged_by_type = rule, graceful skip ถ้า tag ลบ |

---

## 4. คำอธิบายแต่ละ Story (Story Breakdown)

### STORY-RA-01: Rule Management (CRUD) — ระบบจัดการ Rule

**เป้าหมาย:** สร้าง UI และ API สำหรับสร้าง แก้ไข ลบ enable/disable Automation Rule ตาม permission ของแต่ละ role

**สิ่งที่จะทำ:**
- **Rule list page:** แสดง Active / Inactive section, rule card, counter, pills filter
- **Action-first wizard:** เริ่มจากเลือก action ก่อน → wizard 2 steps → auto-generate rule name → save
- **CRUD operations:** สร้าง, แก้ไข (pre-filled wizard), enable/disable toggle, hard delete พร้อม confirmation
- **Permission enforcement:** Admin = full CRUD, Supervisor = สร้าง/แก้ไข, Agent = ดูอย่างเดียว — check ทั้ง UI และ API
- **Active rule limit:** block create เมื่อ active rules = 20

**ทำไมสำคัญ:** Story นี้คือ shell ทั้งหมด ถ้าไม่มีนี้ RA-02/03/04 ไม่มีที่ให้ rule ไปอยู่

---

### STORY-RA-02: Define Trigger Conditions — กำหนดเงื่อนไข Trigger

**เป้าหมาย:** ให้ admin กำหนด trigger conditions ได้ 3 types พร้อม AND/OR logic และ test panel ทดสอบก่อน activate

**สิ่งที่จะทำ:**
- **Evaluator:** Keyword (contains/exact, case-insensitive ไทย-EN), Channel, Business hours (Workspace toggle + custom)
- **AND/OR logic:** evaluate ทุก condition แบบ single-pass ด้วย logic ที่เลือก
- **Background guards:** bot sender skip, message dedup 5s window
- **Wizard Step 1 UI:** condition cards + AND/OR toggle + test panel real-time highlight

**ทำไมสำคัญ:** ถ้า evaluation ผิด rule fire ผิดเวลา — การ test ก่อน save ลด misconfiguration

---

### STORY-RA-03: Send Auto-reply Message — ส่งข้อความอัตโนมัติ

**เป้าหมาย:** เมื่อ rule match ให้ระบบส่งข้อความตอบกลับผ่าน channel เดิม พร้อม template variables และ cooldown บังคับ

**สิ่งที่จะทำ:**
- **Auto-reply executor:** ส่งผ่าน channel เดียวกัน, only-first-wins, skip ถ้า conversation completed
- **Variable resolver:** resolve `{{customer_name}}`, `{{channel}}`, `{{current_time}}` พร้อม fallback
- **Cooldown:** required field, per-conversation-per-rule, default 5 นาที
- **Background:** `sender_type = 'rule'`, ไม่ update `first_human_response_at`, retry 3 ครั้ง
- **Wizard Step 2 (Auto-reply) UI:** text editor + variable toolbar + fallback inputs + preview + cooldown field

**ทำไมสำคัญ:** ถ้า `sender_type` ผิดหรือ cooldown ไม่ทำงาน FRT metric และ customer experience พัง

---

### STORY-RA-04: Auto-Tag Conversation — ติด Tag อัตโนมัติ

**เป้าหมาย:** ให้ rule ติด tag ให้ conversation อัตโนมัติแบบ append-only พร้อม metadata สำหรับแยก KPI

**สิ่งที่จะทำ:**
- **Auto-tag executor:** append-only (ไม่ลบ tag เดิม), dedup (ไม่ duplicate), skip + log ถ้า tag หายจาก system
- **Metadata:** `tagged_by_type = 'rule'` สำหรับ KPI report filter แยก manual / automated
- **Wizard Step 2 (Add tag) UI:** tag picker searchable + multi-select + create inline + preview chip list
- **Tooltip:** tag ที่ rule ติดแสดง "tagged by rule: [ชื่อ]" เมื่อ hover

**ทำไมสำคัญ:** tag ที่ผิดประเภท (rule vs human) ทำให้ KPI report ไม่น่าเชื่อถือ
