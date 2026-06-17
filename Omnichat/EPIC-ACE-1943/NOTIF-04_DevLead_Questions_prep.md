# NOTIF-04 — คำถามที่ Dev Lead น่าจะถามในรีวิว (พร้อมคำตอบแบบง่าย)

> เตรียมจาก: sequence v2, ER v2, escalation v3, user story + **ตรวจกับโค้ดจริง** ที่ `D:\Work\Meaw - Q\ACE\ace`
> สร้างจากการสำรวจโค้ด 6 service (notification / omnichat-sla / api-gateway / workspace-admin / shared+user+tenant / NOTIF-01 pipeline) แล้วให้คน fact-check คำตอบกับ docs+โค้ดอีกที

**สัญลักษณ์ความสำคัญ:** 🔴 ต้องเตรียมตอบแน่นอน · 🟡 น่าจะถาม · ⚪ อาจถาม
**สถานะคำตอบ:** ✅ docs/โค้ดตอบไว้แล้ว · ⚠️ เอกสารขัดกันเอง (ต้องเคาะ) · ❓ ช่องว่าง docs เงียบ (ต้องตัดสินใจ)

---

## ⭐ สรุปก่อนเข้าห้อง — 5 เรื่องที่ "ต้องยกขึ้นพูดเอง" ก่อนโดนถาม

เรื่องพวกนี้คือจุดที่ **Story ใน ClickUp กับ Design diagram พูดไม่ตรงกัน** ถ้าปล่อยไว้ dev กับ QA จะทำคนละ spec:

1. **Rate-limit** — Story AC#5 บอกต้องมี "ไม่เกิน 5 escalation/นาที/user" แต่ escalation v3 **ตัดทิ้งแล้ว** → ต้องเคาะกับ PO ก่อน QA เขียน test (Q1)
2. **ชื่อ column** — Story เขียน `workspace_id` + มี `due_soon_minutes` ในตาราง แต่ ER ใช้ `tenant_id` + **ไม่เก็บ** `due_soon_minutes` → ยึด ER (Q2)
3. **Story ยังไม่ถูก update จริง** — v3 อ้างว่าแก้ story เรื่อง "ปิด sla_breached_team = ปิด escalation" แล้ว แต่ไฟล์ story ยังเป็นของเก่า (Q4)
4. **AC เรื่อง recipients เขียนสลับ event** — Given ตั้งค่า `sla_breached` แต่ Then ไปเช็ค `sla_breached_team` → AC verify ไม่ได้ตามที่เขียน (Q5)
5. **NOTIF-01 ยังไม่มีในโค้ดเลย** — design เขียนเหมือนเสร็จแล้ว แต่ grep ทั้ง repo ไม่เจอ emit `create_notification` สักจุด → ต้องเคลียร์ลำดับ deploy 2 story (Q6)

---

## กลุ่ม 1 — ความขัดแย้งเอกสาร & ช่องว่างใน Design (🔴 ต้องเตรียมตอบ)

### Q1. Rate-limit: AC ขัดกับ design ⚠️ 🔴
**Dev Lead ถามว่า:** "Story AC เขียนชัดว่าต้องมี rate-limit ≤ 5 escalation/นาที/user แต่ v3 บอกตัด rate-limit ที่ delivery ออกเลย — ตกลงเอาไง? QA เขียน test ตาม story ตอนนี้ก็ fail ตั้งแต่ design แล้ว"

**ทำไมถึงถาม:** AC กับ design ขัดกันตรงๆ เป็นสิ่งแรกที่จับได้เมื่ออ่านสองไฟล์เทียบกัน และ QA plan ("Rate-limit tests: bulk breach") ยังอ้าง AC เดิม

**คำตอบ (ง่ายๆ):** เป็น conflict จริง ต้องยกพูดเอง — v3 ตัดสิน (12 มิ.ย.) ว่าไม่ทำ rate-limit เพราะตรวจ UX ทั้ง epic แล้ว surface เดียวคือ **bell badge + panel** ไม่มี toast/เสียง/desktop notification เลย ไม่มีอะไรเด้งใส่ user ให้ spam ได้ badge ขึ้นจาก 5 → 100 คือตัวเลขความจริง (FE cap "99+" อยู่แล้ว) ใบ breach แรกก็ไม่เคยมี rate-limit อยู่แล้ว และการ drop WS push จะทำ badge ค้าง (stale) เพราะระบบไม่มี polling มีแค่ reconnect fetch ส่วน throughput คุมที่ต้นทางด้วย batch 500/รอบ cron อยู่แล้ว → **ทางเลือก:** (a) ตัด AC ทิ้ง (design แนะนำ) หรือ (b) เก็บไว้ทำตอนมี intrusive channel จริงใน NOTIF-05 + โน้ตว่า scale หลักพันใบต้องมี digest notification เป็น story แยก. **Action: ปิดเรื่องนี้กับ PO ก่อน QA เริ่ม**
**อ้างอิง:** Story AC#5 (บรรทัด 83-87) + Tech Notes 112 + QA 132 ขัดกับ escalation v3 บรรทัด 119-133

### Q2. ชื่อ field: workspace_id/due_soon_minutes vs tenant_id ⚠️ 🔴
**Dev Lead ถามว่า:** "Story Tech Notes เขียน `workspace_id` แถมมี `due_soon_minutes` (nullable) ในตาราง notification_rules แต่ ER ใช้ `tenant_id` และตัด due_soon ออกไปอ่านจาก workspace_sla_configs แทน — ยึดอันไหน?"

**ทำไมถึงถาม:** ถ้า dev ทำ schema ตาม story จะได้ column ผิดชื่อ + column เกินที่ desync กับ SLA config และ QA จะ test จาก story แล้ว fail

**คำตอบ (ง่ายๆ):** **ยึด ER ทั้งสองเรื่อง** — (1) `due_soon_minutes` มี source of truth อยู่แล้วที่ `workspace_sla_configs` (SLA-01) ถ้า copy มาเก็บอีกชุด = มีนาฬิกาสองเรือนเดินไม่ตรงกัน แก้ที่หน้า SLA แล้วหน้า Rules โชว์ค่าเก่า = bug ถาวร ER เลยให้หน้า Rules แสดง read-only โดยยิง GET `/sla/workspace-config` ขนานไป (มีใน Diagram 1 แล้ว และ story บรรทัด 21 ก็เขียนเองว่าแสดงเฉยๆ ปรับไม่ได้) (2) `workspace_id` เป็นศัพท์รุ่นเก่า ทั้ง repo ใช้ `tenant_id` หมดแล้ว. **Action: รับไปแก้ Tech Notes ของ story**
**อ้างอิง:** Story 108 vs ER 98 + 13; code: notification-service/prisma/schema.prisma ใช้ tenant_id

### Q3. Diagram 1 บอก "always 10 rows" แต่ ER ยอมรับว่า row หายได้ ⚠️ 🔴
**Dev Lead ถามว่า:** "Diagram 1 บอก SELECT ได้ 'always 10 rows' แต่ ER list เคส row หายได้ 3 เคส (seed fail, migration ตก, event ใหม่) — GET /rules จะคืนอะไรตอนแถวไม่ครบ?"

**ทำไมถึงถาม:** FE render หน้า settings จาก API ตรงๆ ถ้า GET ไม่เติมแถวที่หาย admin จะ config event นั้นไม่ได้เลย

**คำตอบ (ง่ายๆ — แก้จากฉบับร่างแล้ว):** ⚠️ *ระวังอย่าพูดว่า "docs เงียบเรื่อง fallback ฝั่ง GET" เพราะ sequence v2 บรรทัด 51 เขียนไว้แล้วว่า "ถ้า row หาย fallback DEFAULT_RULES"* — สิ่งที่ docs **ไม่ได้ระบุจริงๆ คือ "กลไก"**: diagram วาดแค่ SELECT→คืน ไม่มี step fallback และ ER spec fallback ไว้เฉพาะใน `checkGlobalRule` ไม่ได้บอกว่า `get_notification_rules` ทำอะไร → **คำถามจริงคือ "fallback ฝั่ง GET แปลว่า เติมแถวใน response / INSERT จริง / หรือคืนไม่ครบ 10?"** ข้อเสนอ: ให้ `get_notification_rules` **merge** แถวที่หายด้วยค่า DEFAULT_RULES ใน response (ไม่ INSERT) → FE ได้ 10 แถวเสมอจริง และเคส "เพิ่ม event ที่ 11 ในอนาคต" ทำงานครบโดยไม่ต้อง migration. **Caveat:** แถวจริงจะเกิดผ่าน PATCH เฉพาะตอน admin แก้ค่าแถวนั้น (UPSERT ทำเฉพาะ row ที่ diff). **Action: เขียนพฤติกรรม merge นี้ลง doc**
**อ้างอิง:** sequence v2 บรรทัด 31 + 51 vs ER 160-163; fallback ที่ ER 129-135

### Q4. ปิด sla_breached_team = ปิด escalation + story ยังไม่ถูกแก้จริง ⚠️ 🔴
**Dev Lead ถามว่า:** "ปิด toggle `sla_breached_team` ใบเดียวแล้ว escalation ดับตามทั้งยวง — ตั้งใจหรือ accident? แล้ว v3 อ้างว่า story ถูก update แล้ว แต่ไฟล์ story บรรทัด 22 ยังเขียน 'sla_breached escalation' และ AC ใหม่ก็ไม่มี"

**ทำไมถึงถาม:** ผูกสอง behavior กับ toggle เดียวเป็น product decision และ doc ไม่ sync จับได้ไว

**คำตอบ (ง่ายๆ):** ตัว behavior **เคาะแล้ว** มีตราประทับ "intended ✅ confirmed 2026-06-12" ทั้งใน ER และ v3 — เหตุผล: escalation คือ "นัดเตือนครั้งที่สอง" ของเรื่องเดียวกัน ไม่ใช่ event อิสระ config อยู่ row เดียวกันเลยมีสวิตช์เดียว ไม่เกิด state งงๆ แบบ "แม่ปิดลูกเปิด" แต่ **จุดที่ขัดจริงคือ story ยังไม่ถูกแก้** (v3 บรรทัด 155 อ้างว่าแก้แล้วแต่ไฟล์ไม่สะท้อน) → ยอมรับตรงๆ + ไปแก้ ClickUp/ไฟล์ก่อน QA + เสนอให้ UI มี hint บอก user ว่าปิดอันนี้แล้วโดนทั้งคู่
**อ้างอิง:** v3 บรรทัด 155 vs story 22 + AC section; ER 104

### Q5. AC "configure recipients" เขียนสลับ event ⚠️ 🔴 *(verifier เพิ่ม)*
**Dev Lead ถามว่า:** "AC ข้อนี้ Given ตั้ง recipients ของ `sla_breached` = [assigned_agent, supervisor] แต่ Then กลับ assert ว่า supervisor ได้ใบ `sla_breached_team` — test อะไรกันแน่? แล้ว 'Admin does not receive it' ก็ขัดกับ default ของ sla_breached_team ที่มี admin อยู่"

**ทำไมถึงถาม:** QA จะเขียน test ตรงตาม BDD แล้วได้ test ที่ตรวจคนละ event กับที่ config ใน Given — AC verify ไม่ได้ตามที่เขียน

**คำตอบ (ง่ายๆ):** AC เขียน Then ข้าม event — ตาม Diagram 3 ทุก event ที่ไม่ hardcode ใช้ recipients จาก rules row ของตัวเอง: ตั้ง `sla_breached` = [agent, supervisor] → ตอน breach **agent + supervisor ได้ใบ `sla_breached`** ส่วนใบ `sla_breached_team` เป็นคนละ event เดินตาม rule ตัวเอง (default = supervisor, admin) ไม่เกี่ยวกับ Given เลย และถ้าตีความ "it" = ใบ team ประโยค "Admin ไม่ได้รับ" ก็ผิดเพราะ default มี admin. **Action: เขียน AC ใหม่แยกสอง event ให้ชัดก่อน QA**
**อ้างอิง:** Story 62-67 vs sequence v2 Diagram 3 (203-210) + ER DEFAULT_RULES 150

### Q6. NOTIF-01 ยังไม่มีในโค้ด + contract เปลี่ยน user_id → context ❓ 🔴
**Dev Lead ถามว่า:** "Design เขียนเหมือน NOTIF-01 เสร็จแล้ว แต่ grep ทั้ง repo ไม่มี emit `create_notification` สักจุด แถม DTO ปัจจุบัน `user_id` ยัง required ขณะที่ NOTIF-04 เปลี่ยนเป็น `context` — contract นี้ใคร own? deploy 2 service ยังไง?"

**ทำไมถึงถาม:** ถ้าไม่เคลียร์ dependency ordering สอง story จะเขียน interface ชนกัน หรือ build rules engine ที่ไม่มีใครเรียก — contract change ข้าม service คือจุดที่ rolling deploy พังบ่อยสุด

**คำตอบ (ง่ายๆ — แก้จากฉบับร่างแล้ว):** ข้อเท็จจริงหลักถูก: ทั้ง repo **ไม่มี emit `create_notification` เลย** และ DTO `user_id` ยัง required (`@IsUUID`) → เปลี่ยน contract ตอนนี้ไม่ใช่ breaking change จริง เป็นโอกาสออกแบบ interface ให้ถูกก่อนมี caller. แต่ต้องแก้ 2 จุดจากร่างเดิม:
- ⚠️ **ฝั่งรับไม่ใช่กระดาษเปล่า** — notification-service มี handler `create_notification` ทำงานอยู่แล้ว (INSERT + PUBLISH ราย user_id + merge logic ที่ key ด้วย user_id) → การย้ายไป `context` คือ **"แก้ handler เดิม + แก้ merge logic"** ไม่ใช่เขียนใหม่จากศูนย์
- ⚠️ **demo escalation โดยไม่รอ NOTIF-01 ได้แค่ระดับ INSERT row** ลงตาราง notifications เท่านั้น — **bell badge เด้งไม่ได้** เพราะ delivery ขา gateway→FE ยังไม่มี: `chat.gateway.ts` subscribe เฉพาะ `omnichat:events` (ไม่มี subscriber ของ `notifications:events`), gateway ไม่มี endpoint `/v1/notifications`, FE ไม่มีใครฟัง `notification:new`

**ลำดับ deploy:** ผู้รับขึ้นก่อนผู้ส่ง (notification-service รับ shape ใหม่ก่อน → omnichat-service), FE รู้จัก `sla_escalation` ก่อน backend emit, NotiSvc เป็นด่านเดียว enforce context ครบตาม event_type (ใช้ตาราง Diagram 3 เป็น spec). **Action: ใส่ลง ACE-2392 ให้ชัด**
**อ้างอิง:** create-notification.dto.ts:14-15 vs sequence v2 292-299; code: 0 emit sites; gateway subscribe เฉพาะ omnichat:events

### Q7. Seeding workspace ใหม่/เก่า — กลไกจริงคืออะไร ❓ 🔴
**Dev Lead ถามว่า:** "Doc บอก workspace ใหม่ seed 10 แถว 'ตอนสร้าง' workspace เก่า 'migration ตอน deploy' — แต่ `createTenant` เป็น $transaction local ไม่มี hook ข้าม service แล้ว notification DB ก็ไม่มีตาราง tenants จะเอา list tenant จากไหน? idempotent ไหม? อยู่ subtask ไหน?"

**ทำไมถึงถาม:** seed คือ critical path แต่ flow สร้าง tenant ไม่มี extension point และ one-shot migration คือจุดพังบ่อยสุดในงาน data

**คำตอบ (ง่ายๆ):** doc บอกแค่ผลลัพธ์ ไม่บอกวิธี และโค้ดยืนยันว่า `createTenant` ไม่มีช่องเสียบ — ทางเลือก workspace ใหม่: (1) tenant-service emit TCP fire-and-forget ให้ notification seed (ง่ายแต่พลาดเงียบได้ — ซึ่ง DEFAULT_RULES fallback ครอบอยู่แล้ว) หรือ **(2) lazy-init แบบ SLA-01** (`initDefaultConfig` สร้างแถว default ตอนถูกเรียกครั้งแรก) — มี pattern ในโค้ดให้ลอก ไม่ต้องแตะ tenant-service. workspace เก่า: เป็น chicken-and-egg (notification ไม่รู้รายชื่อ tenant) → script แยกดึง tenant list ผ่าน tenant-service แล้ว INSERT `skipDuplicates` อาศัย unique (tenant_id, event_type) รันซ้ำได้ปลอดภัย หรือกล้าพูดว่า "ไม่ migrate เลย พึ่ง fallback" แถวจริงเกิดตอน admin save ครั้งแรก. **Action: เคาะ lazy-init + ใส่ ACE-2389**
**อ้างอิง:** sequence v2 51 + ER 157-163 vs tenants.service.ts:185-209 (local tx); lazy-init: omnichat sla.service.ts:62

### Q8. Redis ล่ม = notification ทั้งระบบล้มไหม? ❓ 🔴
**Dev Lead ถามว่า:** "`checkGlobalRule()` พึ่ง Redis GET ทุกครั้งก่อน create notification — Redis ล่ม ระบบล้มเลยไหม หรือ degrade ไปอ่าน DB? แล้ว PUBLISH ที่ใช้ส่งเข้า WebSocket ก็ Redis ตัวเดียวกัน"

**ทำไมถึงถาม:** Redis กลายเป็น dependency บน critical path ของทุก notification — diagram เขียนแต่ happy path cache miss

**คำตอบ (ง่ายๆ):** docs เขียนแค่ cache miss (GET ไม่เจอ→SELECT DB) ไม่ได้บอกว่า GET "พัง" จะทำไง → implementation ต้อง `try/catch` รอบ Redis GET แล้ว treat error เหมือน cache miss คือ fallthrough ไป SELECT DB ตรง (query เบามาก 10 rows/tenant, index ตรง) ระบบช้าลงแต่ไม่ตาย ส่วน PUBLISH fail = bell ไม่เด้ง real-time แต่ row INSERT ลง DB แล้ว user เห็นตอน reconnect/refresh สรุป: **Redis ล่ม = เสีย "ความสด" ไม่เสีย "ข้อมูล"** แต่ต้อง commit พฤติกรรม try/catch นี้ลงโค้ดเพราะตอนนี้ไม่มีอะไร enforce
**อ้างอิง:** sequence v2 Diagram 3 (155-160); v3 128 (reconnect fetch ไม่มี polling)

### Q9. ทำไม write-through SET ไม่ใช่ DEL? + race stale ❓ 🔴
**Dev Lead ถามว่า:** "ทำไม cache ใช้ write-through SET ทับตอน PATCH แทน DEL? แล้ว race: read ฝั่ง create กำลัง SELECT ค่าเก่า พอดี PATCH commit+SET ค่าใหม่เสร็จก่อน แล้ว read เอาค่าเก่ามา SET ทับทีหลัง — stale ค้างได้เกือบชั่วโมง"

**ทำไมถึงถาม:** write-through ที่ไม่มี versioning มี race window แบบ classic โดยเฉพาะเมื่อ AC บอก rule change ต้องมีผลทันที

**คำตอบ (ง่ายๆ):** ส่วน "ทำไม write-through" docs ตอบ: SET ทับให้มีผลกับ event ถัดไปทันทีไม่ต้องรอใคร fill, TTL 3600 เป็น safety net. แต่ race ที่ถามเป็นเรื่องจริง docs ไม่พูด — reader หยิบค่าเก่าจาก DB ก่อน PATCH commit แล้วมา SET ทีหลัง จะเขียนทับค่าใหม่ค้างจน TTL หมด. คำตอบซื่อสัตย์: window แคบระดับ ms + ต้องชนจังหวะ cache expiry พอดี โอกาสต่ำมาก + damage cap ที่ 1 ชม. **ถ้า reviewer ไม่รับ: PATCH ใช้ DEL แทน SET** (read ถัดไป fill ค่าใหม่จาก DB เสมอ ตัด race ฝั่ง writer ทิ้ง) เสนอเป็น adjustment ได้เลย
**อ้างอิง:** sequence v2 80, 98

### Q10. escalation:configs (EX 60) ไม่ถูก invalidate ตอน PATCH ❓ 🔴
**Dev Lead ถามว่า:** "PATCH SET ทับแค่ `notification:rules:{tenant}` แต่ `escalation:configs` (EX 60) ไม่ invalidate — admin ปิด sla_breached_team แล้ว cron ยัง scan ต่อได้อีก 60 วิ แถม conv ที่โดน mark escalated ช่วงนั้น dedup row ลงแล้วแต่ notification โดน skip → เปิด rule กลับ conv นั้นก็ไม่ escalate อีก ตั้งใจหรือหลุด?"

**ทำไมถึงถาม:** สอง cache คนละ TTL derive จากข้อมูลก้อนเดียวกันแต่ invalidate ไม่พร้อมกัน + dedup row insert ก่อน delivery decision ทำให้ notification หายเงียบ

**คำตอบ (ง่ายๆ):** ครึ่งแรก design ตอบได้: `escalation:configs` stale ได้สูงสุด 60 วิ ยอมรับได้เพราะ cron รันทุก 1 นาที + ด่านตัดสินจริงคือ `checkGlobalRule` ฝั่ง NotiSvc ที่อ่าน rules cache สดเสมอ → ใบ notification ไม่หลุดไปถึง user หลังปิด rule แน่นอน. **แต่ครึ่งหลังคือช่องจริง:** ในรอบ stale นั้น omnichat INSERT row 'escalated' (dedup) ไปก่อน emit → NotiSvc skip → row dedup ยังอยู่ → เปิด rule กลับมา conv นั้นไม่ถูก scan เจออีกในรอบเดิม = escalation ใบนั้นหายถาวรเงียบๆ. **ทางแก้ที่จบเร็วสุด: เพิ่ม 1 บรรทัดใน PATCH flow → DEL `escalation:configs` ด้วย** cost แทบศูนย์ ปิด window นี้เลย
**อ้างอิง:** sequence v2 Diagram 2 (80) vs v3 (40-44) + ลำดับ INSERT ก่อน emit (53-58)

### Q11. cron ถือ lock 300s + TCP ไม่มี timeout → pod ซ้อน? ❓ 🔴
**Dev Lead ถามว่า:** "`runCycle()` ถือ lock 300 วิ แล้วทุกนาทียิง TCP `get_escalation_configs` ข้ามไป notification-service — ถ้า NotiSvc ค้าง `firstValueFrom` ไม่มี timeout จะ block จน lock หมดแล้วอีก pod เข้าซ้อนไหม? ทำไม escalation config ไปอยู่ฝั่ง notification ทั้งที่ detection อยู่ omnichat?"

**ทำไมถึงถาม:** เอา cross-service call เข้าไปใน cron ที่ถือ distributed lock = service ปลายทางช้าครั้งเดียวอาจ corrupt lock semantics ทั้ง cycle

**คำตอบ (ง่ายๆ):** ownership docs ตอบดี: `escalation_minutes` เป็น notification rule ที่ admin แก้บนหน้า notification settings เลยอยู่ DB ฝั่ง NotiSvc และ v3 ถามแค่ 1 TCP call/รอบ (batch ทุก tenant + cache 60s) — coupling บางสุดแล้ว. **แต่ timeout เป็นช่องจริง:** ทั้ง repo ใช้ `firstValueFrom` ไม่มี timeout operator ถ้า NotiSvc แขวน runCycle จะค้างจน lock TTL หมด → pod ซ้อน. **ทางแก้: ใส่ timeout สั้นๆ (เช่น 5 วิ) บน call นี้ fail = skip markEscalated() รอบนั้น** ไม่เสียหายเพราะ scan เป็น stateless รอบหน้าเจอ conv เดิม (NOT EXISTS ยังไม่ถูก insert) — graceful degradation ที่ design รองรับอยู่แล้ว
**อ้างอิง:** sla-cron.service.ts:10 (TTL=300) + v3 39-48; timeout ไม่มีใน doc/code

### Q12. PATCH diff เทียบกับอะไร + concurrent save lost update? ❓ 🔴
**Dev Lead ถามว่า:** "PATCH ส่ง rules ทั้ง array แต่ UPSERT เฉพาะ row ที่ค่าเปลี่ยน — diff เทียบ snapshot ไหน? admin สองคนเปิดหน้าค้างไว้แล้ว save ไล่กัน last-write-wins ใช่ไหม? ไม่มี version/optimistic lock ใน schema เลย"

**ทำไมถึงถาม:** PATCH รับทั้ง array แต่เขียนบางส่วนเป็น semantics ไม่ standard + settings ที่ admin หลายคนแก้ได้คือสนาม lost update

**คำตอบ (ง่ายๆ):** เหตุผล diff-based docs ตอบชัด: ถ้า upsert ทุก row `updated_by` ของทุก event จะกลายเป็นคนกด save ล่าสุดหมด — audit โกหก เหมือนเซ็นชื่อเฉพาะหน้าที่แก้ ไม่ใช่ทุกหน้าทุกครั้งที่เปิดแฟ้ม + ทั้งก้อนเป็น $transaction all-or-nothing. **แต่ docs ไม่บอกว่า diff เทียบอะไร** → ควร diff กับค่าปัจจุบันใน DB ภายใน transaction (ไม่ใช่ค่าที่ FE โหลดมาซึ่งอาจ stale). concurrency จริง = last-write-wins ระดับ row: สองคนแก้คนละ event ไม่ทับกัน (คนละ row) แต่แก้ row เดียวกันคนหลังชนะเงียบๆ ไม่มี error เหลือแค่ `updated_by` ตามรอย — ยอมรับได้ใน MVP เพราะหน้านี้นานๆ มีคนแก้. **ถ้าต้องการเพิ่ม: ใช้ `updated_at` ที่มีอยู่แล้วเป็น optimistic version → FE ส่งกลับมาตอน PATCH service ตอบ 409 ถ้าไม่ตรง โดยไม่ต้องแก้ schema**
**อ้างอิง:** sequence v2 78, 97; ER 113 (ไม่มี version column)

### Q13. LIMIT 500 พอไหม + per-tenant query? ❓ 🔴
**Dev Lead ถามว่า:** "LIMIT 500/รอบพอจริงเหรอ? cron ตายครึ่งชั่วโมงฟื้นมามี backlog 2,000 convs จะเกิดอะไร? ORDER BY sla_due_at ASC จะ starve conv ใหม่ไหม? แล้ว 500 นี่ global ทุก tenant หรือต่อ tenant — escalation_minutes ต่างกันต่อ tenant ต้องแยกยิง query ไหม?"

**ทำไมถึงถาม:** batch limit คือ throughput control ตัวเดียวของ design นี้ (ไม่มี rate-limit ที่ delivery แล้ว)

**คำตอบ (ง่ายๆ):** docs ตอบส่วนใหญ่: dedup NOT EXISTS ทำให้ conv ที่ fire แล้วไม่กลับมาใน scan → backlog 2,000 ระบายหมดใน ~4 รอบ (~4 นาที) ที่ 500/รอบ ไม่มี starvation ถาวรเพราะคิวมีแต่หดลง, ORDER BY ASC แค่ทำให้ของเก่าออกก่อน. math worst case: ~500 emit/นาที, ~1,500 INSERT+PUBLISH/นาที (supervisor 3 คน) ทุก hop รับไหว. **แต่ส่วนที่ docs เงียบคือคำถามท้าย:** scan ต้อง compare กับ escalation_minutes ที่ต่างกันต่อ tenant ซึ่งมาจาก TCP (คนละ DB JOIN ไม่ได้) → อาจต้องยิง query ต่อ tenant หรือ inline เป็น VALUES list และ doc ไม่ระบุว่า 500 เป็น budget รวมหรือต่อ tenant → เป็น implementation detail ที่ยังไม่เคาะ. **ข้อเสนอ: cap รวม 500/รอบเพื่อให้ math doc ยังจริง แล้วกระจาย fair ต่อ tenant ถ้าจำเป็น**
**อ้างอิง:** v3 50 + 130; per-tenant semantics ไม่มีในทุก doc

### Q14. escalation_minutes นับจากไหน + BH-aware? ❓ 🔴
**Dev Lead ถามว่า:** "escalation_minutes นับจาก cron mark breached หรือจาก sla_due_at? ถ้า workspace เปิด `bh_aware` นับแบบ business-hour หรือ wall-clock? breach 17:50 ก่อนปิดร้าน 18:00 ตั้ง escalate 30 นาที จะ fire 18:20 ที่ไม่มีใครอ่าน"

**ทำไมถึงถาม:** `workspace_sla_configs` มี `bh_aware` จริง และ `sla_due_at` คำนวณ BH-aware ได้ แต่สูตร scan ของ escalation เป็น wall-clock ล้วน — ความไม่สมมาตรนี้ทำให้ fire นอกเวลาทำการแบบไร้ประโยชน์

**คำตอบ (ง่ายๆ):** anchor ตอบได้จากสูตร: scan ใช้ `sla_due_at <= NOW() - escalation_minutes` → นับจาก `sla_due_at` (เวลา SLA ครบกำหนดจริง) ไม่ใช่เวลา cron ประทับตรา ข้อดี: cron delay เพราะ backlog เวลานัดไม่เลื่อนตาม (เงื่อนไขแฝง: conv ต้องถูก markBreached ก่อน). **เรื่อง BH-aware ต้องตอบตรงๆ ว่า docs เงียบ:** `sla_due_at` อาจถูกคำนวณ BH-aware มาแล้ว (`calculateSlaDueAt` รองรับ) แต่ `+escalation_minutes` ที่ต่อท้ายเป็น wall-clock ล้วน ไม่มี BH logic ใน markEscalated. **คำตอบ: v1 ตั้งใจให้ wall-clock เพื่อความเรียบง่าย ถ้าต้องการ BH-aware ให้เป็น decision ของ PO ทำ iteration ถัดไป — อย่าแอบใส่เพราะมันเปลี่ยนความหมายตัวเลขที่ admin ตั้ง**
**อ้างอิง:** v3 50 + ER 41 + messages.service.ts:172-196 (calculateSlaDueAt รับ bh_aware)

### Q15. DEFAULT_RULES ทำสองหน้าที่ → drift? ❓ 🔴
**Dev Lead ถามว่า:** "DEFAULT_RULES เป็นทั้ง seed source และ runtime fallback — ถ้าวันหน้าแก้ค่า default ใน map ล่ะ? tenant ที่ seed ไปแล้วถือ snapshot เก่าใน DB ส่วน tenant ที่ row หายได้ค่าใหม่จาก fallback — สอง tenant พฤติกรรมต่างโดยไม่มี UI บอกว่าใครวิ่งบน fallback"

**ทำไมถึงถาม:** constant ทำสองหน้าที่คือ drift trap และ fallback เงียบๆ ทำให้ debug "ทำไม tenant A ไม่เหมือน B" ยากมาก

**คำตอบ (ง่ายๆ):** นึกภาพ map เป็นพิมพ์เขียว — ตอน seed ถ่ายสำเนาลง DB แต่แก้พิมพ์เขียวทีหลังสำเนาเก่าไม่เปลี่ยน ส่วน tenant ที่ row หายอ่านพิมพ์เขียวล่าสุดเสมอ → แยกสองทางได้จริง. doc ระวังแค่ drift ระหว่างไฟล์ (กฎ "ห้ามเขียน default ซ้ำที่อื่น") ไม่พูดถึง drift ระหว่าง map กับแถวที่ seed ไปแล้ว. **คำตอบ defensible:** เป็นพฤติกรรมตั้งใจ — แถวใน DB คือค่าที่ tenant ถือจริง (admin อาจแก้ไปแล้ว แยกไม่ออกจากค่า seed และไม่ควร retroactively เขียนทับ config ใคร) ส่วน fallback เป็น safety net ชั่วคราว. **Action: log/metric ทุกครั้งที่ fallback ถูกใช้ → เห็นว่า tenant ไหนยังไม่มีแถวจริง แทนที่จะรู้ตอนลูกค้าโทรมา**
**อ้างอิง:** ER 137-163

### Q16. ทำไม recipients เป็น JSON ไม่ normalize? ❓ 🔴
**Dev Lead ถามว่า:** "ทำไม recipients เก็บ JSON column ไม่ normalize เป็น table แยก หรือ enum array? JSON ไม่มี constraint ที่ DB ใครยัดค่ามั่วๆ ก็รับหมด"

**ทำไมถึงถาม:** JSON column ใน relational DB เป็น red flag คลาสสิก เช็คว่า trade-off ถูกคิดมาหรือแค่สะดวกตอนเขียน Prisma

**คำตอบ (ง่ายๆ):** doc ไม่เขียนเหตุผลตรงๆ แต่มีคำตอบ defensible: recipients เป็น set ปิดเล็กมาก (3 ค่า) อ่านทั้งก้อนพร้อม row เสมอ ไม่มี use case query กลับด้าน (ไม่มีใครถาม "หา rule ทุกอันที่มี supervisor เป็นผู้รับ") → normalize เป็น join table ได้ JOIN เพิ่มเปล่าๆ ไม่มี query ได้ประโยชน์ แถม shape JSON ตรงกับ API response + Redis cache value แบบ 1:1. integrity ย้ายไปคุมที่ business validation ใน NotiSvc ด่านเดียว (subset 3 ค่า, ห้าม empty ถ้า enabled). **จุดอ่อนที่ยอมรับ: คนยิง SQL ตรงไม่มีอะไรกัน — trade-off ชุดเดียวกับ event_type เป็น TEXT**
**อ้างอิง:** ER 16 + 88-96; sequence v2 92-96

### Q17. recipients ห้าม empty ขัดกับ mention/channel_error + ทำไม reject 400? ❓ 🔴
**Dev Lead ถามว่า:** "Validation บอก recipients ห้าม empty ถ้า enabled=true แต่ row ของ mention/channel_error เก็บ [] ทั้งที่ enabled=true — ชนกันเองไหม? แล้วถ้า FE เผลอส่ง recipients มาแก้สอง event นี้ ทำไม reject 400 ทั้ง request แทนที่จะ ignore field นั้นเงียบๆ แล้ว save ที่เหลือ?"

**ทำไมถึงถาม:** จุดที่ implement แล้วพังง่ายสุด — ถ้า dev เขียน validator ตรง doc ทีละบรรทัดโดยไม่เห็นข้อยกเว้น จะ save หน้า rules ไม่ผ่านตั้งแต่ครั้งแรก

**คำตอบ (ง่ายๆ):** อ่านตรงตัวสองบรรทัดชนกันจริง แต่เจตนา: กฎ non-empty ใช้กับ **payload ที่ส่งเข้ามา** ไม่ใช่ row ใน DB และ mention/channel_error ถูกห้ามส่ง recipients ตั้งแต่ต้น (reject ก่อน) → กฎ non-empty เหลือผลกับ 8 event ที่เหลือ. **ตอบเป็นลำดับชั้น:** (1) event_type ต้องอยู่ใน 10 ค่า — sla_escalation ส่งมา = reject (2) mention/channel_error → ห้ามมี recipients ใน payload (3) อีก 8 event → recipients ⊆ 3 ค่า + ห้าม empty ถ้า enabled. **ทำไม reject ไม่ ignore:** ignore เงียบ = ระบบโกหก client (FE ได้ 200 เชื่อว่า save แล้วทั้งที่ไม่ลง DB) ซ่อน bug FE ไว้นาน + ขัด fail-loud philosophy ที่ทีมใช้ตัดสิน v3 (เลิก metadata flag เพราะ typo แล้วพังเงียบอันตรายกว่า) + audit เพี้ยน — UX ไม่กระทบเพราะ FE ที่ถูกต้อง render สอง event นี้เป็น fixed label อยู่แล้ว
**อ้างอิง:** sequence v2 93-96 vs ER DEFAULT_RULES 147, 151; ER 96

### Q18. ใครก็ emit sla_escalation ปลอมได้ไหม? ❓ 🔴
**Dev Lead ถามว่า:** "`create_notification` เป็น TCP EventPattern เปิดรับทุก caller พอเพิ่ม SLA_ESCALATION เข้า enum แล้ว @IsEnum รับค่านี้จากใครก็ได้ — มี guard ว่า sla_escalation ต้องมาจาก SLA cron เท่านั้นไหม? service อื่น emit ปลอมหา supervisor ได้เลย?"

**ทำไมถึงถาม:** design ระบุ sla_escalation ควรมี emitter เดียวคือ markEscalated() แต่ enum validation เปิดรับจากทุกทาง

**คำตอบ (ง่ายๆ):** เป็น gap จริง ยอมรับตรงๆ: TCP layer ของ repo นี้ไม่มี caller authentication กับ cmd ไหนเลย ทุก service ใน internal network ส่งหากันได้ พอเพิ่ม enum แล้ว DTO @IsEnum รับอัตโนมัติทุกทาง → service ที่โดน compromise หรือเขียนผิดสร้าง escalation ปลอมได้. **คำตอบในห้อง: consistent กับ trust model เดิมทั้งระบบ (การ์ดจริงอยู่ที่ network boundary ของ cluster ไม่ใช่ application layer) ความเสี่ยงนี้ไม่ใหม่ — ใครจะปลอม sla_breached วันนี้ก็ทำได้เหมือนกัน** ถ้าจะแข็งขึ้น (allowlist source / shared secret) ควรทำเป็น cross-cutting story ทุก TCP cmd ไม่ใช่ patch เฉพาะ event เดียวซึ่งให้ความปลอดภัยลวงตา
**อ้างอิง:** notifications.controller.ts:12 (@EventPattern ไม่มี guard); v3 58, 147

### Q19. Test strategy: timer 30 นาที + cache consistency ❓ 🔴
**Dev Lead ถามว่า:** "Escalation timer 30 นาทีกับ cron ทุก 1 นาที test ยังไงไม่ให้ QA นั่งรอจริง? test markEscalated() ครอบ race multi-pod + dedup ด้วยไหม? แล้ว AC 'rule change มีผลทันที' มี integration test ผ่าน Redis write-through จริงไหม?"

**ทำไมถึงถาม:** logic ผูกเวลา/cron + AC พึ่ง cache consistency คือจุด test ยากสุด bug ชอบหลุดถ้า mock Redis แล้วผ่านหมดแต่ของจริงไม่ถูกทับ

**คำตอบ (ง่ายๆ):** docs ไม่มี test strategy ต้องเตรียมเอง:
- **Timer:** อย่า test ผ่าน scheduler — เรียก `runCycle()`/`markEscalated()` ตรงๆ แล้วคุม "เวลา" ผ่านข้อมูล: เซ็ต `sla_due_at` ของ conv ทดสอบเป็นอดีต (เช่น NOW()-45m) = จำลอง breach เกิน threshold โดยไม่ต้อง mock นาฬิกา. เคสขั้นต่ำ: (1) breach เกินเวลา+ไม่มีใครตอบ→escalate (2) agent ตอบก่อนครบ→sla_status met หลุดจาก scan (3) รัน cycle ซ้ำ→dedup NOT EXISTS คืน 0 rows (4) race 2 pod→create() ชน P2002 ตัวแพ้ต้องไม่ emit
- **AC "มีผลทันที":** integration test ผ่าน Redis จริง — PATCH ปิด rule→ยิง create→assert ไม่มี row, เปิดกลับ→noti กลับมา, ใบเก่าใน bell ไม่หาย
- **เคสที่ Dev Lead จะจี้ต่อ:** DB tx สำเร็จแต่ SET cache fail → stale ได้นานสุด 1 ชม. docs ไม่พูด → ยอมรับเป็น accepted risk หรือเพิ่ม DEL cache fallback
**อ้างอิง:** Story 114-133 (QA มีแค่หัวข้อ) + AC 89-93; v3 77; sla-cron.service.ts:24-48

### Q20. งาน bell UI + ลำดับ subtask 6 ตัว + ข้าม service ❓ 🔴
**Dev Lead ถามว่า:** "v3 checklist มีข้อ 'NOTIF-02/03 bell UI แยก render escalation' แต่ subtask ของ NOTIF-04 มีแค่ Rules page UI (ACE-2390) ไม่มีงาน bell — อยู่ story ไหน? แล้ว ACE-2392 'Handle Emit Event Type From Config' ครอบ markEscalated() ฝั่ง omnichat ด้วยไหม? คนละ service กับที่เหลือ"

**ทำไมถึงถาม:** งานที่ checklist บอกต้องมีแต่ไม่อยู่ใน subtask ไหนเลย = งานที่จะหล่นแน่ + subtask ชื่อกำกวมข้าม service = estimate พลาด

**คำตอบ (ง่ายๆ):** สอง gap ownership จริง:
1. **bell UI** — v3 ระบุต้องเพิ่ม switch case `sla_escalation` (ข้อความ/icon ต่างจากใบ breach แรก) แต่ subtasks NOTIF-04 (2389-2392) ไม่มีงาน bell และโค้ดตอนนี้ workspace-admin ยังไม่มี component ฟัง `notification:new` ด้วยซ้ำ → ถ้า backend emit แล้ว FE ไม่รู้จัก อาจ render เป็นใบ blank → เคาะว่าใส่ scope NOTIF-02/03 หรือเพิ่ม subtask + เพิ่ม SLA_ESCALATION ใน shared enum ก่อน FE เริ่ม
2. **ลำดับ:** ACE-2389 Schema/Migration (table+seed+enum) → ACE-2391 API GET/PATCH → ACE-2390 UI → ACE-2392 ปิดท้าย. **แต่ถ้า ACE-2392 = แค่ checkGlobalRule ฝั่ง notification แปลว่า markEscalated() + get_escalation_configs + TCP client ใหม่ฝั่ง omnichat ไม่มี subtask รองรับเลย** (ก้อนงานไม่เล็ก: แก้ cron, เพิ่ม TCP client 2 ตัว, race-safe insert) → เสนอแตก subtask escalation ฝั่ง omnichat แยก หรือเขียน scope ACE-2392 ให้ครอบทั้งสองฝั่ง
**อ้างอิง:** v3 141-152 vs story Subtasks 135-144; code: ไม่พบ component ฟัง notification:new; SlaModule ยังไม่มี NOTIFICATION_SERVICE client

### Q21. Permission matrix cache ค้าง + boot failure ❓ 🔴
**Dev Lead ถามว่า:** "Permission matrix โหลดจาก user-service ครั้งเดียวตอน gateway start — revoke สิทธิ์ supervisor ตอนรันอยู่มีผลเมื่อไหร่? แล้ว user-service ตายตอน gateway boot เกิดอะไร?"

**ทำไมถึงถาม:** security config ที่ cache ค้างคือช่องโหว่คลาสสิก — สิทธิ์ถูกถอนแล้วยังใช้ได้ + failure mode fail-open/closed

**คำตอบ (ง่ายๆ — แก้จากฉบับร่างแล้ว):** matrix โหลดใน `onModuleInit` ครั้งเดียว ไม่มี refresh interval → แก้ตัว matrix (ถอด action จาก supervisor) ต้อง **restart gateway** ถึงเห็น. แต่ "role ของ user" ถูก resolve สดทุก request ผ่าน TCP (`resolveRole`) → **ลด role ใครมีผลทันที**. ⚠️ **failure mode ตอน boot (แก้แล้ว):** `loadMatrix` ไม่มี try/catch — user-service ตายตอน boot → `onModuleInit` reject → **gateway start ไม่ขึ้นเลย (crash/restart loop)** ไม่ใช่ "ขึ้นมาแล้วตอบ 403" → blast radius = ทุก endpoint รวม route public. ส่วนเคส user-service ตายระหว่างรันอยู่ค่อยเป็น fail-closed ราย request (resolveRole catch→null→deny→403). **สรุป: เป็น limitation ที่มีอยู่ก่อน NOTIF-04 โดนทุก permission เท่ากัน ถ้าจะแก้ (periodic reload / boot retry-with-backoff) ควรเป็นงาน cross-cutting แยก**
**อ้างอิง:** permission-matrix.service.ts:16-23 (reload เฉพาะ onModuleInit, ไม่มี try/catch), :66-74 (resolveRole per-request)

### Q22. เปิด escalation ครั้งแรกบน backlog เก่า → flood ย้อนหลัง? ❓ 🔴 *(verifier เพิ่ม)*
**Dev Lead ถามว่า:** "เปิด escalation ครั้งแรก (หรือเพิ่งเซ็ต escalation_minutes) ใน workspace ที่มี conv ค้าง breached เป็นร้อย — สูตร `sla_due_at <= NOW()-X` ไม่มีขอบเขตเวลาย้อนหลัง breach เก่าเป็นสัปดาห์ก็เข้าเงื่อนไขทันทีและถูกระบายรอบละ 500 จนหมด — supervisor โดน bell ถล่มทั้งที่ admin เพิ่งกด save ตั้งใจไหม?"

**ทำไมถึงถาม:** config change ที่มีผล retroactive กับ state เก่าคือ surprise behavior คลาสสิกตอน rollout — first-enable เป็นจังหวะที่ทุก workspace ต้องเจอครั้งหนึ่งเสมอ แต่ docs คุยเฉพาะ steady state กับเคส cron ตายฟื้น

**คำตอบ (ง่ายๆ):** docs ไม่พูดถึงเลย — สูตร v3 จับทุก conv ที่ `sla_status=breached` และเลย threshold โดยไม่สนว่า config ตั้งเมื่อไหร่ ส่วน dedup กันแค่ยิงซ้ำ ไม่กันย้อนหลัง → first-enable บน backlog ใหญ่ = flood จริงตาม math ของ doc เอง. **ทางเลือกเสนอ PO:** (a) ยอมรับ — backlog คือความจริงที่ supervisor ควรเห็น สอดคล้อง "badge คือตัวเลขความจริง" + อาศัย digest notification ที่ v3 โน้ตไว้ (b) escalate เฉพาะ breach ที่เกิดหลังเปิด config — ต้องเก็บ timestamp ตอนเปิด เป็นงานเพิ่ม (c) cap อายุ breach ที่จะ escalate (เช่นไม่เกิน 24 ชม.). **ไม่ว่าทางไหนต้องเขียน expected behavior ลง doc/AC เพื่อให้ QA ตัดสินเคสนี้ได้**
**อ้างอิง:** v3 50 (scan ไม่มี lower bound), 130 (backlog 2,000 = flood ที่ design คาด), 133 (digest); ไม่มี doc ใดพูดถึง first-enable

### Q23. ใบ escalation/breach ถูก mark read ตอนไหน? ❓ 🔴 *(verifier เพิ่ม)*
**Dev Lead ถามว่า:** "ใบ `sla_escalation`/`sla_breached_team` ถูก mark read ตอนไหน? โค้ด `mark_notifications_read` ปัจจุบัน allowlist แค่ `new_conversation` กับ `customer_replied` — supervisor คลิกใบ escalation เข้าไปดูแล้วใบค้าง unread ตลอดเหรอ? งานขยาย allowlist อยู่ subtask ไหน?"

**ทำไมถึงถาม:** v3 ใช้ข้อดี "allowlist เลือก clear แยกใบ breach/escalation ได้อิสระ" เป็นเหตุผลขายการสร้าง event_type ใหม่ แต่ไม่มี doc เคาะจริงว่า allowlist รวม SLA events ไหม → read lifecycle ที่ไม่ถูกเคาะ = badge ค้างให้ user งง

**คำตอบ (ง่ายๆ):** ยังไม่มีคำตอบใน docs — โค้ดจริงตอนนี้ allowlist ของ `mark_notifications_read` มีแค่ `NEW_CONVERSATION` + `CUSTOMER_REPLIED` → ณ ปัจจุบันใบ SLA ทุกชนิด (รวม escalation) จะไม่ถูก auto-clear ตอนเปิด conversation. **ต้องเคาะ product decision 3 ทาง:** (1) เปิด conv จากใบ escalation → clear เฉพาะใบ escalation ของ conv นั้น (2) clear รวมใบ breach แรกด้วย (3) ไม่ auto-clear ให้กดอ่านเอง → แล้ว assign เจ้าของงานขยาย allowlist (NOTIF-02/03 ฝั่ง interaction หรือเพิ่ม scope ACE-2392). **จุดขายของ v3 "เลือก clear แยกได้" จะจริงก็ต่อเมื่อมีคน implement**
**อ้างอิง:** notifications.service.ts:110-125 (allowlist เฉพาะ NEW_CONVERSATION, CUSTOMER_REPLIED); v3 93; docs ทั้ง 4 ไฟล์ไม่ระบุ read lifecycle ของ sla_escalation

---

## กลุ่ม 2 — Escalation Logic & Race Condition (🟡 มีคำตอบใน docs/โค้ด)

### Q24. ทำไมฝัง markEscalated() ใน runCycle() เดิม ไม่แยก cron? ✅ 🟡
**คำตอบ (ง่ายๆ):** ข้อมูลที่ใช้ตัดสิน "ใคร breach เกิน X นาที + ยังไม่เคย escalate" อยู่ใน DB omnichat ทั้งหมด เช็คจบใน query เดียว ไม่ต้องลากข้อมูลข้าม service ทุกนาที เหมือนรถส่งของวิ่งรอบเดิมแค่แวะเพิ่มจุดเดียว ดีกว่าออกรถคันที่สองที่ต้องมีคนขับ (lock) + ตารางเวลา (timing skew) ของตัวเอง. lock TTL — doc ยอมรับว่าถ้าหมดกลางรอบแล้วอีก pod ชิงได้ มีชั้นสอง = unique constraint บน conversation_sla_events ทำให้ INSERT ซ้ำชนแล้ว skip + steady state scan = 0 rows
**อ้างอิง:** v3 12-18, 101-112, 77; sla-cron.service.ts:9-10

### Q25. กัน multi-pod race ยังไง + ทำไม create()+catch P2002 ไม่ใช่ upsert? ✅ 🟡
**คำตอบ (ง่ายๆ):** กันสองชั้น: Redis lock + unique constraint (ตัวตัดสินจริงเมื่อ lock พลาด). markEscalated **ไม่แตะ sla_status** (ยัง breached ตั้งใจ ไม่กระทบ dashboard/filter) → ผลของ INSERT event คือสัญญาณเดียวที่บอกว่า pod ไหนได้สิทธิ์ emit. ถ้าใช้ `upsert update:{}` มันสำเร็จเงียบทั้งสอง pod แยกไม่ออกว่าใคร created → emit ซ้ำสองใบ. `create()+catch P2002` ชนะได้คนเดียว — เหมือนแย่งจองที่นั่งที่มีที่เดียว คนจองติดได้พิมพ์ตั๋ว (emit) คนชน P2002 เดินกลับ. **ควรเขียน comment อธิบายในโค้ดว่าทำไมต่างจาก markBreached ที่ใช้ upsert**
**อ้างอิง:** v3 77; markBreached upsert+didUpdate guard ที่ sla-cron.service.ts:159-203

### Q26. cycle_number increment ตอนไหน? ✅ 🟡
**คำตอบ (ง่ายๆ):** ✅ เช็คโค้ดแล้วปลอดภัย — `cycle_number` = "รอบที่เท่าไหร่ของ SLA ใน conversation นี้": ลูกค้าทักครั้งแรก set `sla_cycle_number=1` (messages.service.ts:192) พอ agent ตอบจน met แล้วลูกค้าทักกลับ increment เป็นรอบถัดไป (messages.service.ts:235) → unique (conversation_id, 'escalated', cycle_number) แปลว่า escalation fire ได้ 1 ครั้ง/1 รอบ breach รอบใหม่ breach ใหม่ fire ใหม่ได้ ไม่ใช่ครั้งเดียวตลอดชีพ เหมือนตั๋วเข้างานที่ออกใหม่ทุกรอบการแสดง. *(หมายเหตุ: finding เก่าที่ว่า "ไม่เคย increment" ผิด — มันอยู่ใน messages flow ไม่ใช่ใน cron)*
**อ้างอิง:** messages.service.ts:192, 235 + @@unique ใน omnichat schema; v3 144

### Q27. AC "agent ตอบใน 30 นาที escalation ไม่ fire" หยุดยังไง? internal note นับไหม? ✅ 🟡
**คำตอบ (ง่ายๆ):** หยุดแบบ implicit ผ่าน state machine เดิม: agent ส่งข้อความถึงลูกค้าสำเร็จ → `sla_status` เปลี่ยน breached→met ทันที (SLA-01 เดิม) แล้ว scan ของ markEscalated มี `WHERE sla_status='breached'` → conv ที่ met หลุดจากตาข่ายเอง เหมือนชื่อหลุดจากบัญชีลูกหนี้ทันทีที่จ่ายเงิน. **internal note ไม่หยุด escalation** — เช็คแล้ว `createConversationNote` ไม่แตะ sla_status และ met flip เฉพาะเมื่อ push ข้อความออกไปหาลูกค้าสำเร็จจริง (`pushedResult.isSuccess`) ซึ่งถูกต้อง เพราะ "ยังไม่มีใครตอบ" = ตอบลูกค้า ไม่ใช่คุยกันเองภายใน
**อ้างอิง:** v3 76 + conversations.service.ts:771-786, 1297

### Q28. ทำไมไม่ทำ rules row ที่ 11 ให้ sla_escalation config ได้เลย? ✅ 🟡
**คำตอบ (ง่ายๆ):** escalation ไม่ใช่สิ่งที่ user config แยกได้ — สิ่งเดียวที่ตั้งได้คือ `escalation_minutes` ซึ่งอยู่บน row `sla_breached_team` อยู่แล้ว ถ้าเพิ่ม row ที่ 11 จะได้ toggle ที่สองที่ต้อง sync กับตัวแม่ (เปิดลูกแต่แม่ปิด=งง) + ต้องแตะ seed + DEFAULT_RULES + migration + หน้า settings โชว์ row ที่ห้ามแก้ recipients เพิ่ม = จ่ายแพงเพื่อ flexibility ที่ไม่มีใครขอ. ส่วนที่ยังต้องเป็น event_type ใหม่ (แทน metadata flag) เพราะ key (user_id, conversation_id, event_type) จะชนกับใบ breach แรก → merge/group ยุบ escalation หายเงียบ. มันเข้า family เดียวกับ mention/channel_error ที่ hardcode recipients โดย key ด้วย event_type. **trap: checkGlobalRule ต้อง special-case ก่อน fallback เสมอ เพราะ DEFAULT_RULES ไม่มี key นี้ (ตกไปคือ undefined)**
**อ้างอิง:** v3 86-95; ER 83-86, 131, 153-154

---

## กลุ่ม 3 — Transport, Cache & Multi-tenancy (🟡 มีคำตอบใน docs)

### Q29. เกณฑ์เลือก TCP send vs emit คืออะไร? ✅ 🟡
**คำตอบ (ง่ายๆ):** **send = ต้องการคำตอบกลับมาทำงานต่อ** (configs เอา escalation_minutes มา scan, rules คืนให้ FE) · **emit = ไม่ต้องการคำตอบและห้ามให้ flow หลักรอ** เหมือนโทรถามข้อมูล (รอสาย) vs หย่อนโน้ตใส่กล่อง (วางแล้วเดินต่อ). create_notification เป็น side-effect: ถ้า notification fail งานหลัก (SLA cron, assign) ต้องไม่พังตาม → fire-and-forget `void .emit().subscribe({error: log})`. validation fail ฝั่ง NotiSvc log ฝั่งนั้น — caller ไม่รู้โดยตั้งใจเพราะทำอะไรต่อไม่ได้อยู่ดี. **ความเสี่ยง emit ถูก cover ด้วย monitoring ฝั่ง NotiSvc ไม่ใช่ฝั่ง caller**
**อ้างอิง:** sequence v2 177 + Transport Reference 272-288

### Q30. burst 500/นาที จะ DDoS user-service ไหม? roles filter พร้อมยัง? ✅ 🟡
**คำตอบ (ง่ายๆ):** load คิดไว้แล้ว: v3 checklist ให้ cache supervisor list ใน Redis `workspace_members:{tenant}:{role}` TTL 30-60s → burst 500 emit/นาทีเหลือ call ไป user-service ~1 ครั้ง/นาที/tenant เหมือนถามรายชื่อหัวหน้าเวรครั้งเดียวแล้วจดแปะ. tradeoff: supervisor เพิ่ง join/ออกคลาดเคลื่อนได้สูงสุด 60 วิ (ยอมรับได้). **2 จุดต้องระวัง:** (1) cache นี้อยู่ใน checklist แต่ไม่ได้วาดใน sequence หลัก → ย้ำว่าเป็น required scope ไม่ใช่ optional (2) handler `list_workspace_members` ปัจจุบันรับแค่ `tenant_id` **ยังไม่รองรับ roles filter** ตามที่ design เรียก → ต้องแก้ user-service ด้วย เป็นงานข้าม service ต้อง flag ใน task breakdown
**อ้างอิง:** v3 150; workspace-members.controller.ts:28-32 (ยังไม่มี roles param) vs diagram line 60

### Q31. cache key tenant_id เชื่อใครมา? ทำไม escalation:configs เป็น global? ✅ ⚪
**คำตอบ (ง่ายๆ):** `tenant_id` **ไม่ได้มาจาก client** — gateway ดึงจาก JWT ผ่าน `@CurrentUser` (pattern เดียวกับ SLA controller) แล้วส่งใน TCP payload → user ปลอมตัวเป็น tenant อื่นไม่ได้ตั้งแต่ขอบระบบ. ส่วน `escalation:configs` เป็น global ก้อนเดียวโดยตั้งใจ เพราะมันไม่ใช่ข้อมูลเสิร์ฟ user แต่เป็นคำถามของ cron ว่า "tenant ไหนเปิด escalation บ้าง" ถามครั้งเดียวต่อรอบ — ถ้า scope per tenant จะกลายเป็น N calls/รอบ = v1 ที่ถูก reject ไปแล้ว เนื้อข้อมูลมีแค่ tenant_id + escalation_minutes วิ่งระหว่าง service ภายใน ไม่เคยถึงหน้าจอใคร = ไม่มี cross-tenant leak
**อ้างอิง:** sequence v2 28-32, 284-285; v3 39-45; sla.controller.ts:28 (@CurrentUser→tenantId)

---

## กลุ่ม 4 — Data Model & Schema (🟡 มีคำตอบใน docs)

### Q32. ทำไม event_type เป็น TEXT ไม่ใช่ DB enum/CHECK? ✅ 🟡
**คำตอบ (ง่ายๆ):** ถ้าเป็น DB enum การเพิ่ม event ใหม่ทุกครั้งต้อง migration — แต่รอบนี้เพิ่ม sla_escalation ทำได้ด้วยแก้ shared TS enum 1 บรรทัด ไม่ต้องแตะ DB. ความถูกต้องย้ายไปคุมที่ขอบ service ด้วย `@IsEnum(NotificationEventType)` ใน DTO ซึ่ง reject ค่าแปลกก่อนถึง DB — เหมือนย้ายยามจากหน้าตู้เซฟมายืนหน้าประตูตึก. จุดอ่อนที่ยอมรับ: ใครเขียน DB ตรงๆ ไม่มีด่านกัน + pattern นี้ consistent กับ `conversation_sla_events.event_type` ฝั่ง omnichat ที่เป็น String อยู่แล้ว — ทั้งระบบเลือกทางนี้เหมือนกัน ไม่ใช่ความขี้เกียจเฉพาะจุด
**อ้างอิง:** v3 18, 78, 143, 147; ER 86; schema.prisma:15 (event_type String)

### Q33. ไม่มี FK เลย — orphan rows ใครเก็บกวาด? ✅ ⚪
**คำตอบ (ง่ายๆ):** ER ตอบชัด: ตารางพวกนี้อยู่คนละ database คนละ service (tenants @ tenant-service, rules/notifications @ notification-service) → FK ข้าม database เป็นไปไม่ได้ทางเทคนิคตั้งแต่แรก เหมือนสมุดสองเล่มคนละตู้ ผูกเชือกข้ามตู้ไม่ได้ → ความสัมพันธ์เป็น logical (เก็บ tenant_id เป็น string). ลบ tenant แล้วแถวไม่หายเอง = orphan ที่ "ยอมรับได้" จัดการด้วย cleanup job ภายหลัง — ในทางปฏิบัติ notification_rules มีแค่ 10 แถว/tenant จิ๋วมาก ไม่ใช่ความเสี่ยง growth (ตัวที่โตคือ notifications = การบ้าน retention ของ NOTIF-01) + pattern logical-ref-no-FK ใช้ทั้ง repo อยู่แล้ว
**อ้างอิง:** ER 13, 67-71

---

## กลุ่ม 5 — Security, Permission & Audit (🟡 มีคำตอบใน docs/โค้ด)

### Q34. permission เดียวคุมทั้ง GET+PATCH → supervisor แก้ได้เท่า admin? ✅ ⚪
**คำตอบ (ง่ายๆ):** intended ตาม story ตรงๆ — story เปิดหัว "As an Admin **or Supervisor** I want to configure..." และ AC สุดท้ายล็อกแค่ agent ต้องโดน redirect → supervisor ได้ทั้งดูทั้งแก้เท่า admin โดยตั้งใจ. โค้ดตรงกัน: matrix seed ให้ `config_notification_rules` กับ admin+supervisor. ใช้ permission เดียวทั้ง GET/PATCH เพราะหน้านี้ all-or-nothing (เข้าได้=แก้ได้) + guard ไม่ hardcode role โหลดจาก matrix → ถ้าวันหน้าอยากให้ supervisor ดูอย่างเดียว เพิ่ม action ใหม่ใน matrix ได้โดยไม่แตะ guard
**อ้างอิง:** Story 8-9 + AC 95-97; seed.ts:27 (config_notification_rules→['admin','supervisor'])

### Q35. updated_by ต่อ row มาจาก JWT ยังไง ในเมื่อ TCP ไม่มี JWT? ✅ 🟡
**คำตอบ (ง่ายๆ):** JWT ถูก verify ที่ gateway (JwtAuthGuard แปะ user ลง request) → gateway ดึง userId ใส่เป็น field `updated_by` ธรรมดาใน TCP payload (ไม่มี token วิ่งข้าม service). ที่ "ต่อ row" ได้เพราะ NotiSvc ไม่ได้เขียนทับทั้ง 10 แถว — diff ก่อนแล้ว UPSERT เฉพาะ row ที่ค่าเปลี่ยน row ที่ไม่เปลี่ยนไม่โดน stamp → `updated_by` แต่ละแถว = คนสุดท้ายที่แก้แถวนั้นจริง ไม่ใช่คนกด save ล่าสุด. **จุดที่ยอมรับถ้าถูกถามต่อ:** NotiSvc เชื่อ updated_by ตามที่ caller ส่งมา — internal trust model เดียวกับทุก cmd ไม่ใช่ความเสี่ยงใหม่
**อ้างอิง:** sequence v2 72, 97; ER 105

### Q36. ทำไม business validation กองที่ NotiSvc ด่านเดียว ไม่ทำที่ gateway? ✅ ⚪
**คำตอบ (ง่ายๆ):** gateway ไม่ใช่ทางเข้าเดียวของ notification-service — มี caller อื่นมาทาง TCP ตรง (omnichat วันนี้ + service อื่นในอนาคต) ถ้ากฎอยู่ที่ gateway caller พวกนั้นหลุดด่านหมด. เหมือนยามหน้าหมู่บ้าน (gateway) เช็คแค่เอกสารหน้าตาถูก format (DTO shape) ส่วนเจ้าของบ้าน (NotiSvc เจ้าของตาราง) ตัดสินกฎจริง (event_type ∈ 10 ค่า, recipients ห้าม empty ถ้า enabled, mention/channel_error ห้ามแก้ recipients) → กฎมีที่เดียว แก้ที่เดียว ครอบทุก caller เสมอ + gateway ยังช่วยตัด request ผิด shape ตั้งแต่ขอบ
**อ้างอิง:** sequence v2 92-96

---

## ภาคผนวก — Action Items ที่งอกจากรีวิว (เอาไปเปิด task/แก้ doc)

| # | Action | เจ้าของ/ที่ | จาก Q |
|---|--------|------------|-------|
| 1 | เคาะ rate-limit AC กับ PO (ตัดทิ้ง/เลื่อน NOTIF-05) | PO | Q1 |
| 2 | แก้ Story Tech Notes: workspace_id→tenant_id, ลบ due_soon_minutes column | Story owner | Q2 |
| 3 | update Story: wording escalation + เพิ่ม AC "ปิด sla_breached_team = ปิด escalation" | Story owner | Q4 |
| 4 | เขียน AC recipients ใหม่แยก sla_breached / sla_breached_team | Story owner | Q5 |
| 5 | เขียนพฤติกรรม merge DEFAULT_RULES ฝั่ง GET ลง doc | Diagram owner | Q3 |
| 6 | เคลียร์ลำดับ deploy NOTIF-01 ↔ NOTIF-04 + ใส่ ACE-2392 | Dev Lead | Q6 |
| 7 | เคาะกลไก seed (lazy-init แนะนำ) + script migration → ACE-2389 | Dev Lead | Q7 |
| 8 | commit พฤติกรรม Redis-down (try/catch→DB) ลงโค้ด | Dev | Q8 |
| 9 | เพิ่ม DEL escalation:configs ใน PATCH flow | Dev | Q10 |
| 10 | ใส่ timeout บน get_escalation_configs (5s) + skip on fail | Dev | Q11 |
| 11 | แก้ user-service list_workspace_members รับ roles filter | Dev (user-svc) | Q30 |
| 12 | แตก subtask escalation ฝั่ง omnichat (markEscalated/TCP client) | Dev Lead | Q20 |
| 13 | เคาะ read lifecycle ของ sla_escalation + ขยาย mark-read allowlist | PO/Dev | Q23 |
| 14 | เคาะพฤติกรรม first-enable backlog (ยอมรับ/cap/หลังเปิด) | PO | Q22 |
| 15 | เคาะ BH-aware escalation window (wall-clock vs BH) | PO | Q14 |

> **หมายเหตุความน่าเชื่อถือ:** คำตอบในกลุ่ม 1 ข้อ Q3, Q6, Q21 ถูกแก้หลังจาก fact-check กับโค้ดจริงแล้ว (ฉบับร่างแรกพูดเกินจริงไปบางจุด). `verify:code` agent ตัวหนึ่ง die เพราะ socket error — claim ที่อ้าง file:line ส่วนใหญ่ถูก verify โดย explorer + verify:docs แล้ว แต่แนะนำให้เปิดไฟล์จริงยืนยันอีกทีตอน implement สำหรับข้อที่จะลงมือเขียนโค้ด
