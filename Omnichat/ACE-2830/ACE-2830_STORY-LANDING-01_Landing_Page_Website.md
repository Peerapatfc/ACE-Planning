# ACE-2830: STORY-LANDING-01: Landing Page Website

- ClickUp: https://app.clickup.com/t/86d3q3nc8
- Status: backlog
- Folder: 📦 PO Backlog (no parent epic)
- Created: Thanyapong

## 1. User Story

### Primary
ในฐานะผู้ที่สนใจโซลูชัน omnichannel chat (เจ้าของธุรกิจหรือทีมการตลาดของธุรกิจไทย) ฉันต้องการหน้า landing page ที่อธิบายได้ชัดเจนว่า Zimple Omnichannel คืออะไรและช่วยธุรกิจอย่างไร พร้อมช่องทางให้เริ่มทดลองใช้หรือขอ demo ได้ง่าย เพื่อที่ฉันจะประเมินผลิตภัณฑ์และตัดสินใจดำเนินการขั้นต่อไปได้โดยไม่ติดขัด

### Secondary (Stakeholder)
ในฐานะทีมการตลาดของ Zimple ฉันต้องการหน้า landing page ที่เก็บรายชื่อผู้สนใจ (lead) ที่มีคุณภาพ ค้นเจอได้ทั้งบน search และ AI answer engine และวัดผลได้ เพื่อสร้างโอกาสทางการขายและติดตามประสิทธิภาพของแคมเปญ

## 2. Detail / Description

หน้า landing page นี้เป็นหน้าเว็บการตลาดของ Zimple Omnichannel เอง (ไม่ใช่ฟีเจอร์ภายในระบบสำหรับร้านค้า) มีเป้าหมายหลักเพื่อแนะนำผลิตภัณฑ์ให้กลุ่มธุรกิจไทย อธิบายคุณค่าหลัก แสดงช่องทางที่รองรับ (LINE, Facebook Messenger, Instagram, Shopee, Lazada, TikTok Shop) และนำผู้เข้าชมไปสู่การกระทำเป้าหมายหลัก (conversion action) ที่กำหนด เช่น เริ่มทดลองใช้งานฟรี หรือขอ demo

นอกจากทำงานได้ในเชิงฟังก์ชันแล้ว หน้านี้ต้องถูกออกแบบให้ค้นเจอและถูกอ้างอิงได้ทั้งบน search engine แบบดั้งเดิม (SEO), บน answer engine และ AI Overviews (AEO) และในคำตอบที่สร้างโดย AI เช่น ChatGPT, Perplexity, Gemini, Claude (AIO/GEO)

ข้อกำหนดหลักของหน้านี้:
- แสดงผลได้ทั้งบนมือถือและเดสก์ท็อป (responsive)
- ใช้ภาษาอังกฤษ/ไทยเป็นหลัก
- มีแบบฟอร์มเก็บข้อมูลผู้สนใจ (lead capture form) พร้อมการขอความยินยอมตาม PDPA
- เชื่อมโยงเอกสารกฎหมายที่มีอยู่แล้ว ได้แก่ นโยบายความเป็นส่วนตัว, ข้อกำหนดในการใช้งาน, นโยบายการใช้คุกกี้
- มีแบนเนอร์ขอความยินยอมคุกกี้ (cookie consent banner) ที่สอดคล้องกับนโยบายการใช้คุกกี้ของบริษัท
- รองรับการค้นเจอบน search และ AI answer engine (SEO / AEO / AIO)

หมายเหตุ: conversion action, การแสดงราคา, และปลายทางของ lead ยังเป็นข้อที่ต้องยืนยัน (ดู 3.4 Decisions)

## 3. Scope

### 3.1 In Scope (MVP) - Functional
1. หน้า landing page เดียว รองรับ responsive (มือถือและเดสก์ท็อป)
2. Hero section: headline, sub-headline, ปุ่ม CTA หลัก และภาพประกอบหลัก
3. ส่วนคุณค่าหลัก (value proposition / key benefits)
4. ส่วนแสดงช่องทางที่รองรับ 6 ช่องทาง: LINE, Facebook Messenger, Instagram, Shopee, Lazada, TikTok Shop
5. ส่วนไฮไลต์ฟีเจอร์หลัก เช่น unified inbox
6. ส่วน social proof (โลโก้ลูกค้า/คำรับรอง, placeholder หากยังไม่มีเนื้อหาจริง)
7. แบบฟอร์มเก็บ lead: ชื่อ, ชื่อธุรกิจ, อีเมล, เบอร์โทรศัพท์ พร้อม checkbox ยินยอม PDPA ลิงก์ privacy policy
8. FAQ
9. Footer: ข้อมูลบริษัท, ลิงก์ privacy policy / terms / cookie policy, ช่องทางติดต่อ
10. Cookie consent banner แสดงครั้งแรกที่เข้าชม รองรับปุ่มยอมรับและตั้งค่า
11. เก็บ event พื้นฐาน (page view, CTA click, form submit) ยิงหลังได้รับความยินยอมคุกกี้ที่ไม่จำเป็น

### 3.2 Search & AI Visibility Scope (SEO / AEO / AIO)

**SEO**
1. Title tag ไม่ซ้ำ ~50-60 ตัวอักษร มี primary keyword + ชื่อแบรนด์
2. Meta description ~150-160 ตัวอักษร
3. โครงสร้างหัวข้อ: H1 เดียว, H2/H3 ตามลำดับตรรกะ
4. Semantic HTML + slug ที่สื่อความหมาย
5. Canonical tag
6. Image alt text ครบ
7. robots.txt / sitemap.xml ถูกต้อง, index (ไม่ noindex)
8. Structured data: Organization, WebSite, SoftwareApplication (หรือ Product), BreadcrumbList
9. Open Graph + Twitter Card
10. HTTPS, mobile-friendly, Core Web Vitals (LCP, INP, CLS)
11. เนื้อหาหลัก server-side rendered

**AEO**
1. Answer-first content ต่อแต่ละส่วน
2. หัวข้อในรูปแบบคำถาม (H2/H3)
3. FAQ พร้อม FAQPage schema (JSON-LD) ตรงกับเนื้อหาจริง
4. แต่ละส่วน self-contained
5. คำตอบกระชับ ระบุตัวเลข/หน่วย
6. คำถามหลักใน title/meta description
7. แสดงวันที่เผยแพร่/อัปเดตล่าสุด
8. ใช้ตาราง/รายการ/คำนิยาม

**AIO / GEO**
1. เปิดให้ AI crawler เข้าถึงใน robots.txt (GPTBot, OAI-SearchBot, ClaudeBot, Claude-SearchBot, PerplexityBot, Google-Extended); CDN/Cloudflare ไม่บล็อก
2. เนื้อหาหลัก server-side rendered HTML (AI crawler ส่วนใหญ่ไม่รัน JS)
3. ไม่ซ่อนเนื้อหาสำคัญหลัง tab/accordion/dropdown
4. Entity clarity: Organization schema + ข้อเท็จจริงตรงกับเอกสารบริษัท
5. อ้างอิงข้อมูลที่ตรวจสอบได้ (สถิติ/แหล่งอ้างอิงจริง)
6. llms.txt ที่ root (Markdown) — infrastructure สำหรับอนาคต ไม่ใช่ ranking factor ที่การันตี
7. เสริม authority นอกเว็บ (นอกขอบเขตหน้านี้)
8. รองรับการวัดผลการปรากฏของแบรนด์ใน AI answer engines + AI referral traffic

### 3.3 Out of Scope (เลื่อนไปเวอร์ชันถัดไป)
1. A/B testing
2. Blog / resource center
3. ฝัง Zimple chat widget (ขึ้นกับ STORY Website Chat Widget)
4. Personalization
5. เชื่อมต่อ lead เข้า CRM/marketing automation อัตโนมัติ
6. Pricing calculator
7. Off-site authority / digital PR / ongoing AI-mention monitoring

### 3.4 Open Decisions
1. Conversion action หลัก: free trial, ขอ demo, ติดต่อฝ่ายขาย หรือมากกว่าหนึ่งอย่าง
2. การแสดงราคา: **แสดงราคาบนหน้าเลย** (ตัดสินใจแล้ว)
3. ปลายทางของ lead: อีเมล, spreadsheet, หรือ CRM — รอ marketing ops
4. ฝัง Zimple chat widget — ขึ้นกับ timeline ของ STORY Website Chat Widget
5. ความพร้อมเนื้อหา (testimonials, โลโก้ลูกค้า, ภาพจริง) — UX/UI จัดเตรียม
6. โครงสร้าง domain/hosting (path/subdomain/root) — คุยกับ P'Tan
7. Primary keyword / keyword research — รอทีม marketing
8. จำนวนคำถาม FAQ (เช่น 5-8 ข้อ) — รอทีม marketing
9. llms.txt: **ทำในเฟสนี้** (ตัดสินใจแล้ว)

## 4. Acceptance Criteria (Given/When/Then)

### 4.1 Functional
- **FN-1 Responsive**: viewport มือถือ 360-430px / แท็บเล็ต 768px / เดสก์ท็อป 1280px+ → จัดวางถูกต้อง ไม่มี horizontal scroll ที่ไม่ตั้งใจ, value prop + CTA เห็นตั้งแต่ต้นหน้า
- **FN-2 CTA หลัก**: กดแล้วนำไปปลายทางที่กำหนด, มี hover/focus state, touch target ≥44x44px
- **FN-3 Form validation**: ฟิลด์บังคับไม่ครบ/ผิดรูปแบบ → error inline, focus ฟิลด์แรกที่ผิด, ไม่ส่งจนกว่าจะแก้ (ชื่อ/ชื่อธุรกิจ บังคับ, อีเมล ตรวจรูปแบบ, เบอร์โทรไทย ตรวจรูปแบบ 0+9 หลัก)
- **FN-4 PDPA consent**: ไม่ติ๊ก checkbox → ปุ่มส่งไม่ทำงาน/error, ลิงก์ privacy policy เปิดได้ (แท็บใหม่)
- **FN-5 ส่งสำเร็จ**: บันทึก/ส่งต่อ lead, แสดงข้อความยืนยัน, บันทึกความยินยอม+timestamp
- **FN-6 ส่งไม่สำเร็จ**: แสดง error ที่เข้าใจได้, ไม่สูญเสียข้อมูลที่กรอกไว้, ลองใหม่ได้
- **FN-7 Cookie consent**: แสดง banner ครั้งแรก, คุกกี้ที่ไม่จำเป็นไม่ทำงานก่อนยินยอม, ปุ่มยอมรับ/ตั้งค่า, ปฏิเสธแล้วไม่ตั้งค่าคุกกี้ไม่จำเป็น, จำการเลือกไว้
- **FN-8 Footer legal links**: ลิงก์ privacy/terms/cookie policy ใช้งานได้ ไม่เป็นลิงก์เสีย

### 4.2 SEO
- **SEO-1** Title (~50-60 chars) + meta description (~150-160 chars) + canonical ถูกต้อง
- **SEO-2** H1 เดียว, H2/H3 ไม่ข้ามระดับ
- **SEO-3** Structured data (Organization, WebSite, SoftwareApplication/Product, FAQPage) validate ผ่าน
- **SEO-4** อยู่ใน sitemap, ไม่ถูกบล็อก robots.txt, HTTP 200, index
- **SEO-5** Open Graph + Twitter Card ครบ, preview ถูกต้อง
- **SEO-6** Lighthouse: LCP ≤2.5s, INP ≤200ms, CLS ≤0.1, HTTPS, mobile-friendly
- **SEO-7** Alt text ครบ, WebP, lazy-load, ระบุขนาดภาพ

### 4.3 AEO
- **AEO-1** แต่ละส่วนตอบก่อนใน 1-2 ประโยค
- **AEO-2** FAQ ตามจำนวนที่ตกลง + FAQPage schema ตรงกับเนื้อหาจริง (ไม่ mismatch)
- **AEO-3** หัวข้อสำคัญเป็นคำถามที่ค้นจริง
- **AEO-4** แสดงวันที่เผยแพร่/อัปเดต + dateModified ใน structured data
- **AEO-5** ใช้รายการ/ตาราง/คำนิยาม, แต่ละส่วน self-contained

### 4.4 AIO / GEO
- **AIO-1** AI crawlers (GPTBot, OAI-SearchBot, ClaudeBot, Claude-SearchBot, PerplexityBot, Google-Extended) ไม่ถูกบล็อก, HTTP 200
- **AIO-2** เนื้อหาหลักอยู่ใน HTML โดยไม่ต้องรัน JS
- **AIO-3** เนื้อหาสำคัญไม่ถูกซ่อนหลัง interaction ที่ต้องคลิก
- **AIO-4** Entity clarity + Organization schema (ZIMPLIGITAL LTD., ที่อยู่, ช่องทางติดต่อ) ตรงกับเอกสารกฎหมาย
- **AIO-5** llms.txt ที่ root ถูกต้อง (H1 แบรนด์, blockquote สรุป, ลิงก์หน้าสำคัญ) — forward-looking, ไม่การันตี ranking
- **AIO-6** มีวิธีติดตามการปรากฏของแบรนด์ใน AI answers + AI referral traffic (ongoing process)

## 5. UI/UX Notes
- Above-the-fold: value prop + CTA หลักต้องเห็นทันที
- โลโก้ช่องทาง (LINE, FB Messenger, IG, Shopee, Lazada, TikTok Shop) ตาม brand guideline แต่ละแพลตฟอร์ม
- Lead form สั้น เก็บเฉพาะฟิลด์จำเป็น
- Trust signal (โลโก้ลูกค้า/security message) ใกล้ฟอร์ม
- โทนแบรนด์/ฟอนต์ตามมาตรฐาน Zimple
- Question-based headings ต้องอ่านลื่นสำหรับคนด้วย ไม่ใช่เขียนเพื่อเครื่องอย่างเดียว
- Hero/og:image ขนาดเหมาะกับ social preview (1200x630)
- แสดงวันที่อัปเดตล่าสุด (เช่น footer)
- (รอยืนยัน) Sticky CTA บนมือถือ

## 6. QA / Test Considerations
- Cross-browser (Chrome, Safari, Firefox, Edge) + มือถือ (Safari, Chrome)
- Responsive ทุก breakpoint
- Form validation edge cases: ช่องว่าง, อีเมลผิดรูปแบบ, เบอร์โทรผิดรูปแบบ, ข้อความยาวผิดปกติ, อักขระพิเศษ, script injection ต้อง sanitize
- Cookie consent: ปฏิเสธ → ไม่มีคุกกี้ไม่จำเป็น; ยอมรับ → ตั้งค่าได้
- ยืนยันการส่งต่อ lead ถึงปลายทางจริง + ทดสอบกรณีส่งไม่สำเร็จ
- ตรวจลิงก์เสีย (legal links + CTA)
- Rich Results Test / Schema Markup Validator ทุก schema
- Lighthouse (mobile + desktop): Performance, SEO, Accessibility, Best Practices, Core Web Vitals
- ปิด JS แล้วยืนยันเนื้อหาหลักยังปรากฏใน HTML
- ตรวจ robots.txt ไม่บล็อก AI crawler + CDN/Cloudflare settings
- ตรวจ Open Graph/Twitter Card ด้วย debug tools
- ตรวจ FAQPage schema ตรงกับ FAQ ที่แสดงจริง
- ตรวจ canonical (+ hreflang ถ้ามีหลายภาษาในอนาคต)
- validate รูปแบบ llms.txt ถ้าทำในเฟสนี้
- PDPA: ตรวจบันทึกความยินยอม+timestamp ตาม Privacy Notice
