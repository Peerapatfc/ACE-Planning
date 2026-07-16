# ACE-2830 Task Breakdown — STORY-LANDING-01: Landing Page Website

Repo: `ace-omnichat-web` (Next.js 15 App Router). Baseline: [ACE-2830_STORY-LANDING-01_Landing_Page_Website.md](./ACE-2830_STORY-LANDING-01_Landing_Page_Website.md)

Figma: [Landing Page](https://www.figma.com/design/LgvPOufZ0GXBwINGODXZDX/Omnichat---Landing-Page?node-id=345-5612&m=dev) · [Pricing Page](https://www.figma.com/design/LgvPOufZ0GXBwINGODXZDX/Omnichat---Landing-Page?node-id=487-6633&m=dev) (**confirm ทำในเฟสนี้ 2026-07-16**)

Total estimate: **35 pts (Fibonacci)** = ผลรวม subtask 21 ตัว สเกล 1/2/3/5/8 — ถ้าต้องปักเลขเดียวระดับ story ใช้ **34** (Fibonacci ที่ใกล้สุด); สองภาษา TH/EN confirm แล้ว 2026-07-16
(หมายเหตุ: เดิมประเมินแบบทศนิยมได้ ~28 — Fibonacci สูงกว่าเพราะปัดงานเล็ก 0.5 ขึ้นเป็น 1 และปัดความไม่แน่นอนขึ้นตามธรรมเนียม planning poker)

Mobile design: **มีจริง** ([node 345:5613](https://www.figma.com/design/LgvPOufZ0GXBwINGODXZDX/Omnichat---Landing-Page?node-id=345-5613&m=dev) "Landing mobile ver." 430px, 2 เฟรม: เมนูปิด `181:2963` / เมนูเปิด `245:5368`) — audit รอบแรกที่บอกว่าไม่มีคือผิด; มีแค่ 430 กับ 1440 **ช่วง tablet กลางๆ dev ตัดสินใจเอง**; mobile มี designer note ยืนยัน 2 ภาษา: "EN + TH — Head: IBM Plex Sans TH, Body: Google Sans"

## Group A — Infra / Foundation (พื้นฐานระบบ — บล็อกทุกอย่างข้างล่าง) — 8 pts

| # | Task | รายละเอียด (ไทย) | Pts |
|---|---|---|---|
| A1 | Public unauthenticated route | สร้าง route ที่ไม่ต้อง login แยกจาก Clerk `ClerkProvider`/`AppShell`/middleware; ต้องยืนยัน domain/hosting ก่อน (path / subdomain / root) — ยังเป็น open decision | 3 |
| A2 | i18n scaffolding (TH/EN) — **confirm แล้ว 2 ภาษา** | next-intl (หรือเทียบเท่า) + locale routing + message files + UI สลับภาษา — Figma มีแค่ text "Language \| English" (node 455:8397) ไม่ใช่ selector จริง **ต้องขอ design ตัวสลับภาษา หรือ dev ออกแบบเอง**; อย่าลืม hreflang + canonical ต่อ locale (กระทบ D1/D4); copy ภาษาไทย **ทีม marketing เป็นคนสรุปส่งมาให้** — dev เตรียมโครง message files รอ | 3 |
| A3 | Cookie consent — **รอเคาะทางเลือก** | ทางเลือก (ตรวจราคาจริง 2026-07-16): **(ก) [CookiePlus](https://cookieplus.com/en/pricing) by Predictive — SaaS ไทย มี free ถาวร**: pageviews ไม่จำกัด แต่ **2,000 sessions/เดือน** (ควรถาม support ว่าเกินแล้ว banner หยุดไหม), Consent Mode v2, ถ้าโตจ่าย Basic ฿199/โดเมน/เดือน = 1 pt; **(ข) open source [vanilla-cookieconsent](https://cookieconsent.orestbida.com/) (MIT) หรือ [Klaro](https://klaro.org/) — ไม่มีเพดานใดๆ**, บล็อกสคริปต์ตาม category ครบ FN-7, TH/EN เสียบ i18n (A2) ได้ = 1 pt แลกกับไม่มี dashboard/hosted consent records; (ค) build เอง = 2 pts; ตัวที่ตัดทิ้ง: Cookie Wow (free ไม่มีแล้ว — trial 14 วันผูกบัตร, Small ฿2,400+VAT/ปี), CookieYes free (5k pv แล้ว banner โดน suspend) | 1 |
| A4 | Analytics events (page view / CTA click / form submit) gated on consent | **ตกหล่นจาก estimate เดิม** — เป็น story scope ข้อ 11; ยิง event หลังได้ consent จาก Cookie Wow เท่านั้น; **ยังไม่ได้เลือก tool** (GA4 / อื่นๆ — open decision #10) | 1 |

## Group B — Content Sections ตาม Figma จริง (12 sections) — 14 pts

| # | Task | รายละเอียด (ไทย) | Pts |
|---|---|---|---|
| B1 | Page shell: Nav + Final CTA + Footer | Nav desktop + **mobile hamburger 2 states (design มีครบทั้งเปิด/ปิด)**, Final CTA, Footer (3 คอลัมน์ลิงก์ Product/Case studies/Resources + social FB/IG/LINE + text "Language \| English" ที่ยังไม่ใช่ selector จริง) — **footer ทั้ง desktop และ mobile ไม่มีลิงก์กฎหมาย** (privacy/terms/cookie) ทั้งที่เป็น AC FN-8 ต้องเพิ่มเอง, mobile ไม่มี copyright ด้วย — เมนู nav: Pricing → `/pricing`, Product/Use Cases/Resources → **anchor scroll ไป section ใน landing** (เคาะแล้ว 2026-07-16) | 2 |
| B2 | Hero | Banner "Trusted by 12,000+ teams", headline, subhead, CTA "Start free trial" / "Book a demo" | 1 |
| B3 | How it works | 3 steps พร้อมคำอธิบาย — section static | 1 |
| B4 | Pain points marquee | 10 การ์ด "Silence is expensive" เลื่อนแบบ marquee 3 คอลัมน์ — **มี animation** + copy 2 ใบยังซ้ำกัน ต้องตาม content | 2 |
| B5 | Solution (tabs) + Security section | Solution บน mobile เป็น **tabs 3 อัน** (Unified inbox / AI & automation / Analytics — ตรงกับ tab variants ที่วางนอก canvas ฝั่ง desktop) — **ระวัง AIO-3**: เนื้อหาใน tab ต้องอยู่ใน HTML ทั้งหมด ไม่ใช่ render เฉพาะ tab ที่เปิด; Security = copy + screenshot ธรรมดา | 2 |
| B6 | What's inside — 4 feature cards | Channels (รวมชื่อ 6 channels เป็น copy — แทน channel showcase เดิมใน story) / AI / Insights / Commerce | 1 |
| B7 | Find your fit — industry cards | Desktop 6 ใบ (E-commerce, Retail, F&B, Financial, Healthcare, Education) + CTA; **mobile ลดเหลือ 4 ใบเป็น carousel เลื่อนแนวนอน** — ต้องทำ carousel component | 2 |
| B8 | Value-prop pill grid + logo strip | Pills ~30 อัน (**ครึ่งนึงยัง placeholder "Must try"**, **mobile ไม่มี section นี้** — ซ่อนตาม design) + logo strip (**ยังเป็นโลโก้ stock: Uber/Nike ฯลฯ ต้อง confirm ของจริง**) | 1 |
| B9 | FAQ + FAQPage JSON-LD schema | **ไม่มี design ใน Figma** แต่เป็น AC บังคับ (AEO-2) — จำนวนคำถามรอ marketing (5-8 ข้อ) | 2 |

## Group C — Lead Capture Form (ฟอร์มเก็บ lead) — 5 pts

**ไม่มี design ใน Figma ทั้งกลุ่ม** (ไม่มี form/input/PDPA node เลย) — ทำตาม AC ของ story โดยตรง, เสี่ยง rework ถ้า design มาทีหลัง

| # | Task | รายละเอียด (ไทย) | Pts |
|---|---|---|---|
| C1 | Form ครบวงจร: UI + validation + PDPA gating + states | RHF + zod (pattern มีแล้ว 7 ไฟล์) + checkbox PDPA บล็อกการส่งจนกว่าติ๊ก + ลิงก์ privacy policy + success/error state ไม่ทำข้อมูลหาย (FN-3/4/5/6) — รวม C1/C2/C4 เดิม | 3 |
| C2 | Submit → ส่งต่อ lead ไปปลายทาง + บันทึกความยินยอม+timestamp | **ติดเงื่อนไข open decision #2**: อีเมล / spreadsheet / CRM — ให้ 2 เผื่อความไม่แน่นอน (อีเมลง่ายสุด CRM แพงสุด) | 2 |

## Group D — SEO — 2 pts

| # | Task | รายละเอียด (ไทย) | Pts |
|---|---|---|---|
| D1 | Meta/OG/robots/sitemap ครบชุด | Title/description/canonical/viewport + OG/Twitter cards (ภาพ 1200x630) + `app/robots.ts`/`app/sitemap.ts` — งาน config-level ผ่าน Next.js convention ทั้งหมด (รวม D1/D3/D4 เดิม) | 1 |
| D2 | Structured data (Organization/WebSite/SoftwareApplication/BreadcrumbList) | ต้องทำ JSON-LD helper ใหม่ ยังไม่มีของเดิม | 1 |

## Group E — AIO / GEO — 1 pt

| # | Task | รายละเอียด (ไทย) | Pts |
|---|---|---|---|
| E1 | AIO ครบชุด: AI crawler allowlist + `llms.txt` + ตรวจ entity | robots.txt เปิด GPTBot/ClaudeBot/PerplexityBot/Google-Extended + ตรวจ CDN ไม่บล็อก; `llms.txt` ที่ root (confirm ทำเฟสนี้); ตรวจ Organization schema ตรงเอกสารกฎหมาย (AIO-4 — Figma ยังใช้ `info@gmail.com`/`02-999-9999` ต้องได้ข้อมูลจริงก่อน) — รวม E1/E2/E3 เดิม | 1 |

## Group F — Pricing Page (confirm เข้า scope 2026-07-16) — 5 pts

อ้างอิงเฟรม `487:6634` (1440×3076) — **มีเฟรมซ้ำ 3 เวอร์ชัน (487:6634, 511:8514, 517:4734) Final CTA copy ต่างกัน ต้องเคาะก่อนเริ่มว่าอันไหน final**; **ไม่มี mobile design ของหน้านี้** — dev เกลี่ยเองทุก breakpoint

| # | Task | รายละเอียด (ไทย) | Pts |
|---|---|---|---|
| F1 | Route `/pricing` + breadcrumb + plan grid 3 tiers | Reuse shell จาก B1 (nav/footer เหมือน landing เป๊ะ); Basic ฿1,800 (3 seats) / Pro ฿3,100 ("Most popular", 5 seats) / Advanced ฿4,200 (10 seats), CTA "Try for free" ทุกใบ — **ราคาต้อง confirm ว่า final** ก่อน publish | 2 |
| F2 | Feature comparison table | 4 กลุ่ม / 10 แถว (Unified Inbox, Automation & Broadcast, SLA & Team Management, Enterprise & Security) check/x ต่อ tier — **ตารางบน mobile ไม่มี design** ต้องออกแบบวิธีแสดงเอง (เวอร์ชัน 2-3 ของเฟรมมีแบบ single-column ย่อ อาจใช้เป็นแนว) | 2 |
| F3 | SEO/i18n ของหน้า pricing | Meta + canonical, **BreadcrumbList schema** (มี breadcrumb "Home › Pricing" ใน design), เพิ่มเข้า sitemap, copy TH/EN (รอ marketing ชุดเดียวกับ landing) | 1 |

## Excluded from dev estimate (งาน ops/process ไม่นับเป็น story point)
- AIO-6 (ติดตามการถูกกล่าวถึง/referral traffic จาก AI แบบต่อเนื่อง) — เป็นงาน ops ต่อเนื่อง ไม่ใช่งาน build
- Off-site authority/digital PR (อยู่นอกขอบเขตอยู่แล้วตามข้อ 3.3)
- ~~Pricing page~~ — **ย้ายเข้า scope แล้ว (Group F, 2026-07-16)**

## Figma Design Comparison (ตรวจจริง 2026-07-16 — เฉพาะหน้า Landing)

อ้างอิงเฟรม 1440px node `345:5612` (artboard จริง `105:5358`) — **มีแต่ desktop, ไม่มี mobile frame ในไฟล์เลย**

### อยู่ใน story แต่**ไม่มีใน Figma** (ยังต้องทำตาม AC — ไม่มี design รองรับ)
| รายการ | สถานะใน Figma | ผลกระทบ |
|---|---|---|
| Lead capture form + PDPA checkbox | ไม่มีเลยทั้ง desktop และ mobile (ไม่มี form/input node, ไม่มีคำว่า PDPA) | Group C ไม่มี design — เสี่ยง rework |
| FAQ + FAQPage schema | ไม่มี section FAQ ทั้งสอง viewport | B9 ไม่มี design; AEO-2 ยังเป็น AC ที่ต้องผ่าน |
| Cookie consent banner | ไม่มี | A3 ไม่มี design |
| 6-channel showcase | ไม่มีเป็น section — ชื่อ channel เป็นแค่ copy ใน feature card เดียว (B6) | ถูกกว่าที่ story คาด แต่ต้อง confirm กับ designer |
| ~~Responsive/mobile~~ | **แก้ไข 2026-07-16: มี mobile design จริง** (node 345:5613, 430px, 2 nav states — audit รอบแรกผิด) | เหลือแค่ tablet 768-1279px ที่ dev ต้องเกลี่ยเอง |

### อยู่ใน Figma แต่**ไม่อยู่ใน story** (scope เพิ่ม — นับใน Group B แล้ว)
How it works · Pain points marquee 10 การ์ด (มี animation) · What's inside 4 การ์ด · Security section · Find your fit 6 การ์ด · Pill grid ~30 pills · Logo strip

### Content ที่ยังไม่เสร็จใน Figma (ต้องตามทีม design/marketing ก่อนหรือระหว่าง sprint)
- Pill grid ~ครึ่งหนึ่งเขียนว่า "Must try" (placeholder)
- การ์ด pain point 2 ใบ copy ซ้ำกับใบอื่นแบบคำต่อคำ
- Footer ใช้ email/เบอร์ placeholder (`info@gmail.com`, `02-999-9999`)
- Logo strip เป็นโลโก้ stock (Uber, Nike, Wise ฯลฯ)

## Checklist ถาม UX/UI (นัด confirm)
- [ ] ตัวสลับภาษา TH/EN — ตอนนี้มีแค่ text "Language | English" (สีขาวบนพื้นขาว) จะ design selector จริงให้ไหม
- [x] ~~Mobile design~~ — **มีแล้ว** (node 345:5613, 430px, hamburger 2 states) → คำถามที่เหลือ: **tablet/จอกลาง (768-1279px) ให้ dev ตัดสินใจเองใช่ไหม** และ mobile มีเศษ artifact นอก canvas ค้างในไฟล์ (เมนูย่อขนาด 5px, หัวข้อ desktop หลงมา) ฝากเก็บกวาด
- [ ] Mobile ก็ยังไม่มี: form / FAQ / cookie banner / ตัวสลับภาษา / ลิงก์กฎหมาย+copyright ใน footer — ชุดเดียวกับ desktop
- [ ] Design ที่ขาด 2 ชิ้นแต่เป็น AC บังคับ: lead form + PDPA checkbox / FAQ section (~~cookie banner~~ ใช้ Cookie Wow แล้ว — เหลือแค่ปรับ theme banner ใน dashboard ให้เข้าแบรนด์)
- [ ] Footer ไม่มีลิงก์กฎหมาย (privacy/terms/cookie policy) — FN-8 บังคับ ต้องเพิ่มใน design
- [x] ~~ปลายทางเมนู nav~~ — เคาะแล้ว: Pricing → `/pricing`, ที่เหลือ anchor ใน landing ไปก่อน (แจ้ง designer รับทราบ mapping)
- [ ] Placeholder content: pill grid "Must try" ~ครึ่งกริด, การ์ด pain point copy ซ้ำ 2 ใบ, footer `info@gmail.com`/`02-999-9999`, logo strip โลโก้ stock (Uber/Nike) — ของจริงคืออะไร ใครเตรียม
- [ ] Pricing page มี 3 เฟรมซ้ำ (487:6634, 511:8514, 517:4734) Final CTA copy ต่างกัน + ตารางเปรียบเทียบคนละแบบ — **อันไหน final (ตอนนี้เข้า scope แล้ว บล็อก Group F)**
- [ ] Pricing page ไม่มี mobile design — จะทำให้ไหม โดยเฉพาะ comparison table บนจอแคบ
- [ ] ราคา 3 tiers (฿1,800/฿3,100/฿4,200) เป็นราคาจริงหรือ placeholder — ต้อง confirm ก่อน publish

## Open decisions ที่ยังบล็อกการประเมินจุดให้แม่นยำ
1. Conversion action (ทดลองใช้ฟรี / ขอ demo / ติดต่อฝ่ายขาย) — Figma มีทั้ง "Start free trial" และ "Book a demo" แต่ไม่มีฟอร์มปลายทาง
2. ปลายทางของ lead (อีเมล / spreadsheet / CRM) — บล็อก C3
3. โครงสร้าง domain/hosting (path / subdomain / root) — รอคุยกับ P'Tan, บล็อก A1
4. Primary keyword / keyword research — รอทีม marketing
5. จำนวนคำถาม FAQ — รอทีม marketing, บล็อก B9
6. ~~ปลายทางเมนู nav~~ — **ตัดสินใจแล้ว (2026-07-16)**: Pricing → `/pricing` (Group F); Product / Use Cases / Resources → **anchor ไปยัง section ใน landing ไปก่อน** (mapping เสนอ: Product → What's inside, Use Cases → Find your fit, Resources → FAQ — ให้ dev/designer เคาะตอน implement)
7. ~~Mobile design~~ — **มีแล้ว (2026-07-16)**: node 345:5613 "Landing mobile ver." 430px × 2 states; เหลือแค่ช่วง tablet 768-1279px ที่ไม่มี design ให้ dev เกลี่ยเอง
8. **Design ของ form / FAQ / cookie banner** — ขอจาก designer หรือ dev ออกแบบเอง
9. ~~จำนวนภาษาตอน launch~~ — **ตัดสินใจแล้ว (2026-07-16): ทำ 2 ภาษา TH/EN**; copy ภาษาไทย **marketing สรุปส่งมาให้** (รอของ) → เหลือแค่ design ตัวสลับภาษาที่ยังไม่มีใน Figma
10. **Analytics tool** (GA4 / อื่นๆ) — ยังไม่ได้เลือก, บล็อก A4; ต้องเข้ากับ consent solution ที่เลือกได้
11. **Cookie consent solution** — รอเคาะระหว่าง: (ก) **CookiePlus free** (SaaS ไทยโดย Predictive — pageviews ไม่จำกัด/2,000 sessions/เดือน, มี dashboard + hosted consent records, ต้องถาม support เรื่องพฤติกรรมตอนเกิน limit) vs (ข) **open source vanilla-cookieconsent/Klaro** (ไม่มีเพดานเลย แต่ไม่มี dashboard); Cookie Wow/CookieYes ตัดทิ้งแล้ว
