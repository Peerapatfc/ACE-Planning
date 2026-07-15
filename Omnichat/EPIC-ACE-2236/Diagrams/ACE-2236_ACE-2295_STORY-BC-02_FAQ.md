# STORY-BC-02: Audience Selection and Targeting — FAQ / คำถามที่คาดว่าจะเจอตอน review

**Epic:** [ACE-2236](https://app.clickup.com/t/86d318wjb) | **Story:** [ACE-2295](https://app.clickup.com/t/86d32c89v) | คู่กับ [Sequence Diagram](ACE-2236_ACE-2295_STORY-BC-02_Sequence_Diagram.md) · [ER Diagram](ACE-2236_ACE-2295_STORY-BC-02_ER_Diagram.md) · [API Reference](ACE-2236_ACE-2295_STORY-BC-02_API.md)

รวมคำถามที่คาดว่าจะโดนถามเกี่ยวกับดีไซน์ BC-02 — ข้อไหนมีคำตอบใน doc แล้วชี้ตำแหน่ง · ข้อไหนยังไม่เคาะ ระบุสถานะชัดๆ

---

## ส่วนที่ 1 — มีคำตอบใน doc แล้ว

### คำถามเชิง product / business

**Q1: ทำไมแยก targeting เป็น 3 โหมด ไม่รวม tag สองชนิดใน dropdown เดียว?**
ชื่อ tag ซ้ำข้าม library ได้ ("VIP" สองแถวหน้าตาเหมือนกันคนละ count), ความหมายต่างกัน (tag คน = "คนนี้เป็น X" / tag แชท = "เคยมีแชทติด X"), และ estimate ต้อง dedup ข้าม library — แยกโหมดตัดทั้งสามปัญหาพร้อมกัน → *Sequence: Decision #1*

**Q2: เลือก tag คนกับ tag แชทพร้อมกันใน broadcast เดียวได้มั้ย?**
ไม่ได้ — เป็น radio เลือกได้ทีละโหมด ราคาที่จ่ายของ Decision #1 ซึ่งตรงเจตนา business ("คนประเภทนี้" กับ "แชทเรื่องนี้" เป็นคนละแคมเปญ) · ถ้าอนาคตต้องการ mixed: schema รองรับอยู่แล้ว (tag_type ต่อแถว) แต่ต้องเปิด AC ใหม่ → *Sequence: Decision #1, #7*

**Q3: ทำไมเลข estimate ไม่ตรงกับ follower count ของ LINE OA?**
จงใจ — follower ที่ไม่เคยทักไม่มี LINE userId ใน DB = push หาไม่ได้จริง เลขที่ซื่อสัตย์คือ "คนที่เคยทัก + มี userId" (เช่น follower 12,450 แต่ส่งได้จริง 400) → *Sequence: Decision #4*

**Q4: เลขตอน compose กับจำนวนที่ส่งจริงต่างกันได้เหรอ?**
ได้ และเป็นเรื่องปกติ — ระบบ resolve รายชื่อสดตอน dispatch (ไม่ freeze ตอน schedule ตาม BC-01 AC2.1) คนทักใหม่/ถูกเปลี่ยน tag ระหว่างรอจึงทำให้เลขขยับ นี่คือความหมายของคำว่า "approximately" ใน UI → *Sequence: หมายเหตุ Audience freeze + BC-03 handoff*

**Q5: exclude tags ไม่มีใน AC ของ story แล้วทำไปทำไม?**
epic เขียน "tags (include/exclude)" ทั้งใน Scope และ DoD — confirm แล้วว่าอยู่ใน scope BC-02 · การบ้านคือ**เพิ่ม AC ฝั่ง exclude เข้า story** (พฤติกรรมช่อง exclude, ตัวอย่างเลข, error เมื่อ tag ซ้ำสอง mode) → *Sequence: หมายเหตุ Exclusion tags*

**Q6: "Send to everyone ยกเว้น tag X" ทำได้มั้ย?**
**ไม่ทำในเวอร์ชันนี้ — เคยเคาะทาง A (การ์ด everyone มีช่อง exclude 2 dropdown แยกชนิด) เมื่อ 2026-07-14 แล้วทีมตัดออกวันเดียวกัน** โหมด everyone จึงไม่มีช่อง tag เลย ซึ่งกลับมาตรงกับ AC3 เดิม ("ซ่อน tag input เมื่อเลือก everyone"):
- **Schema รองรับอยู่แล้ว**ถ้าอนาคตกลับมาทำ: เก็บ `targeting_type=all` + แถว `mode=exclude` ใน `broadcast_tags` ได้ทันที ไม่ต้อง migrate — ฝั่งโค้ดแค่เลิก reject tag ของโหมด all
- ทาง A ที่ถูกตัด: exclude (optional) 2 dropdown แยกชนิดบนการ์ด everyone = "ส่งทุกคนยกเว้น..." เช่น 400 − TEST GROUP(12) = 388 · ผลพวงที่หายไปด้วย: payload ไม่ต้องพก `type` แล้ว (ดู Q11) และ estimate ใช้ `excludeTagIds` ตัวเดียว
- ทางเลือก B ที่เคยพิจารณา (โหมด specific + ตัวเลือก "ทุกคน"): ตกไปตั้งแต่แรก — ต้องมี sentinel พิเศษ + กติกา exclusive กับ include อื่น และเสี่ยงตีความผิดเป็น "include ทุก tag" (ซึ่งพลาดคนไม่มี tag แบบเงียบๆ)
→ *Sequence: DECISION block + หมายเหตุ*

**Q7: Quota validation / plan-aware warning หายไปไหน?**
อยู่ใน feature list ของ story แต่**ไม่มี AC รองรับสักข้อ** — เลื่อนไป BC-03 (จุดที่ quota ถูกใช้จริง) รอ confirm PO → *Sequence: หมายเหตุ Quota*

**Q8: ทำไม BC-02 มีเรื่อง save/load draft ทั้งที่ AC ไม่ได้เขียน?**
BC-01 AC14 สั่งว่า draft ต้องเซฟ "Targeting setting" และ AC15 สั่ง restore — BC-02 เปลี่ยนเนื้อหาของ "Targeting setting" (โหมด + tags) จึงต้องขยาย flow เซฟ/โหลดเดิม ไม่งั้นเลือก tag ได้แต่กด save แล้วหาย · ตรวจโค้ดจริงแล้ว: BC-01 วางโครง `targeting_type`/`target_estimate` ไว้ครบทุกชั้นแต่ล็อกค่า `all` (Go: `validate:"oneof=all"` · web: hardcode 3 จุด) → *Sequence: diagram 3 (delta-only)*

### คำถามเชิง technical

**Q9: ทำไมไม่ reuse `GET /v1/contact-tags` / `GET /v1/tags` ที่มีอยู่แล้ว?**
(a) `/v1/tags` (chat) ไม่มี count เลย และ count ที่ต้องการคือจำนวน*คน*ผ่านห้องแชทของ OA — query ใหม่อยู่ดี (b) `/v1/contact-tags` มี usageCount แต่นับทั้ง workspace ไม่ scope OA — เลขจะขัดกับ estimate → *Sequence: Decision #2*

**Q10: ทำไม `tag_id` ไม่มี FK?**
ชี้ได้ 2 ตาราง (contact_tag_labels / tags) — FK ทำไม่ได้ ใช้ `tag_type` แยก + orphan ไม่มีพิษเพราะทุก read path JOIN + `deleted_at IS NULL` กรองเอง → *ER: constraints + Notes*

**Q11: ทำไมต้องเก็บ `tag_type` ต่อแถว ทั้งที่ derive จากโหมดได้?**
derive ได้จริง — tag ทุกแถวของ broadcast เป็นชนิดเดียวตาม targeting_type เสมอ (everyone ไม่มี tag เลยหลังตัด exclude ออก — Q6) server จึง**ใส่ tag_type ให้ทุกแถวเองตามโหมด payload ไม่ต้องส่ง `type`** (ไม่ต้องเชื่อค่าจาก client — ตัดเคส type ขัดโหมดตั้งแต่ต้นทาง) · แต่ยังเก็บลง DB ต่อแถวเพราะ (a) อยู่ใน UNIQUE key กัน id ชนข้าม 2 library (b) แถว self-describing: BC-03/BC-06 อ่านแล้วรู้ทาง JOIN โดยไม่ต้องย้อนดู targeting_type (c) requirement เปลี่ยน (เช่น everyone กลับมามี exclude) ไม่ต้อง migrate → *Sequence: Decision #7 · ER: Notes*

**Q12: ทำไม `mode` ไม่อยู่ใน UNIQUE key?**
จงใจ — `UNIQUE(broadcast_id, tag_id, tag_type)` ที่ไม่มี mode ทำให้ tag หนึ่งมีได้แถวเดียวต่อ broadcast = อยู่ทั้ง include และ exclude พร้อมกันไม่ได้ตั้งแต่ระดับ DB (ชั้นที่ 3 ต่อจาก UI + server validation) → *Sequence: Decision #12 · ER: constraints*

**Q13: ทำไม exclude ชนะ include?**
ความผิดพลาดไม่สมมาตร: exclude ชนะ → พลาดแบบ "ส่งขาด" (แก้รอบหน้าได้) / include ชนะ → พลาดแบบ "ส่งหาคนที่ห้ามส่ง" (irreversible, เปลือง quota, ลูกค้า block) · exclude คือกลไก opt-out เดียวที่มี (epic ตัด opt-out mechanism ออก) · ตรง convention ทุกเครื่องมือ marketing → *Sequence: Decision #12*

**Q14: ทำไมคำนวณใน DB ไม่บวกเลขฝั่ง FE?**
AC2 วางกับดักไว้: VIP(125) + New Customer(155) ต้องได้ 280 ไม่ใช่ 325 (คนถือสอง tag นับครั้งเดียว) — `COUNT(DISTINCT)` ได้ dedup ฟรี + AC4 บังคับเลขตรง query จริง · พิสูจน์กับ DB local แล้วทั้งสอง library (~6ms จาก budget 2s) → *Sequence: Decision #3 + SQL*

**Q15: เลขใน dropdown (VIP 125) ไม่ตรงกับหน้า Contact Tags (VIP 300)?**
จงใจ — dropdown scope ตาม OA ที่เลือก (คนที่ส่งถึงได้บน OA นี้) ส่วนหน้า Contact Tags นับทั้ง workspace เพื่อให้เลข dropdown/estimate/% เป็นจักรวาลเดียวกัน → *Sequence: Decision #13*

**Q16: GET สองตัวใหม่ทำไมไม่ gate permission?**
Pure read ตาม epic "Agent: read only permission for broadcast features" — pattern เดียวกับ `GET /v1/broadcasts` เดิม · ฝั่ง write มี `org:broadcast:manage` ครอบแล้ว → *Sequence: Decision #11 · API doc*

**Q17: resolve รายชื่อผู้รับต้องเป็น API มั้ย?**
ไม่ — เป็น method ที่ 3 บน `AudienceRepository` (BC-03 เพิ่ม) เรียกโดย dispatch worker ใน process เดียวกัน · ไม่มีผู้เรียกนอก process, เปิดเป็น HTTP = PII surface ฟรี · WHERE เดียวกับ estimate ต่างแค่ `SELECT external_id` → *Sequence: หมายเหตุ BC-03 handoff*

---

## ส่วนที่ 2 — คำตอบเตรียมไว้แล้ว แต่ยังไม่อยู่ใน design doc

**Q18: ต้องใส่ cache (Redis) ให้ tags/estimate มั้ย?**
**ไม่คุ้ม** — (1) เป็น path เย็นที่สุดในระบบ (admin เปิดหน้า compose วันละไม่กี่ครั้ง) (2) budget 2s เหลือเฟือ (~6ms จริง) (3) React Query ฝั่ง FE กินเคสเรียกซ้ำไปแล้ว (4) cache key ของ estimate = combination ของ tag set → hit rate ≈ 0 (5) invalidation ต้องผูกกับทุก write path ของ tag/conversation — พลาดจุดเดียว = เลขค้าง = **ละเมิด AC4 ตรงๆ** · จุดกลับมาคิดใหม่: วัดได้จริงว่า >1s บน workspace ระดับแสน contact — และตัวเลือกแรกตอนนั้นคือ index/denormalized count ไม่ใช่ Redis

**Q19: สอง admin แก้ broadcast เดียวกันพร้อมกันเกิดอะไรขึ้น?**
Last-write-wins — full-replace (delete + re-insert) ตาม pattern ของ broadcast_messages ที่รับมาจาก BC-01 ไม่มี optimistic lock · ยอมรับได้เพราะ broadcast มี editor เป็น admin/supervisor จำนวนน้อยและมี `updated_by` บอกว่าใครแก้ล่าสุด · ถ้าต้องการมากกว่านี้ (เช็ค updatedAt ก่อนเขียน → 409) เป็น scope ใหม่ระดับทั้ง compose form ไม่ใช่แค่ targeting

**Q20: Draft เก่าจาก BC-01 (targeting_type='all') เปิดในหน้าใหม่พังมั้ย?**
ไม่พัง — `all` ยังเป็นค่า default เดิม ไม่มีแถวใน broadcast_tags ก็คือไม่มี chip · ไม่ต้อง migrate data เก่า

**Q21: user คลิก chip รัวๆ estimate ยิงรัวตามมั้ย?**
การคลิกเป็น discrete event (ไม่ใช่การพิมพ์) — แต่ละคลิกเปลี่ยน queryKey แล้ว React Query จัดการเอง: request ของ key เก่าถูกทิ้ง (stale), key ซ้ำใช้ cache, `keepPreviousData` กันเลขกะพริบระหว่างรอ · ไม่ต้อง debounce เพิ่ม

**Q22: tags list ช้ามั้ยถ้า workspace มี tag หลายร้อยตัว? (count ต่อ tag scope OA เป็น GROUP BY)**
โครง query เดียวกับ estimate + index เดิมรองรับ (`ix_contact_tags_tag`, `ix_ctag_conv`) — คาดว่าอยู่หลัก ms แต่**ยังไม่ได้วัดจริง** (ต่างจาก estimate ที่วัดแล้ว) → **action: วัดตอน implement** ถ้าเกินงบค่อยปรับ

---

## ส่วนที่ 3 — ยังไม่เคาะ ต้องตัดสินใจก่อน implement

**Q23: สลับ LINE OA หลังเลือก tag ไปแล้ว — chips หายหรือคงอยู่?**
ยังไม่เคาะ (UX decision) · ข้อเท็จจริงเชิงเทคนิค: tag เป็น workspace-level → chips ยัง valid ข้าม OA, estimate ยิงใหม่เองอยู่แล้ว (queryKey มี oaId)
**ข้อเสนอ:** คง chips ไว้ + estimate refetch — เพราะ user ที่สลับ OA กลางทางมักแค่เลือก OA ผิด ไม่ได้อยากเริ่มเลือก tag ใหม่ · ถ้า UX เลือกทางเคลียร์ chips ก็ implement ง่ายเท่ากัน แค่ต้องเขียนลง AC

**Q24: (ผูกกับ Q5) AC ฝั่ง exclude จะเขียนเมื่อไหร่ ใครเขียน?**
ค้างที่ PO — ดีไซน์พร้อมแล้ว แต่ QA ไม่มี AC ให้ test · รายการที่ต้องครอบ: พฤติกรรมช่อง exclude, ตัวอย่างเลข estimate เมื่อมี exclude, error เมื่อเลือก tag ซ้ำสอง mode

**Q25: (ผูกกับ decision 3 โหมด) BC-01 AC3 + BC-02 AC1.1 + mockup จะแก้เมื่อไหร่?**
ค้างที่ PO/UX — ClickUp ล่าสุด (เช็คแล้ว) ยังเป็น radio 2 ตัว + list รวม · mockup ยังไม่มี radio ที่ 3 และช่อง exclude
