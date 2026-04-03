# EPIC ACE-1610 RBAC — สรุป Gap Analysis ระดับภาพรวม

## สถานะรวม

| Story | ชื่อ | สถานะ | เสร็จแล้ว |
|---|---|---|---|
| ACE-1611 (RBAC-01) | Permission Model & API Enforcement | Backlog | 0% |
| ACE-1612 (RBAC-02) | Member Management | Backlog | ~20% |
| ACE-1613 (RBAC-03) | Frontend Permission Enforcement | Backlog | 0% |

**สาเหตุหลัก:** Platform ยังไม่มีระบบ role ในทุกระดับ ทั้ง database, API, และ UI ผู้ใช้ที่ login สำเร็จทุกคนถูกมองว่ามีสิทธิ์เต็มเหมือนกันหมด Invitation scaffolding มีอยู่บ้างแต่ยังไม่สมบูรณ์และไม่มี role field เลย

---

## สิ่งที่สร้างไว้แล้ว

| ส่วน | สิ่งที่มี |
|---|---|
| Authentication | JWT login/register, refresh token, session cookies |
| Invitation พื้นฐาน | สร้าง token (32-byte hex), expiry 7 วัน, SHA-256 hash, accept flow |
| Members UI | ตารางแบบ read-only (ชื่อ, email, วันที่เข้าร่วม — ไม่มี role, ไม่มี actions) |
| Invitations UI | หน้ารายการพร้อม invite form (ไม่มี role selector, ไม่มี Resend/Cancel) |
| หน้า Unauthorized | หน้า `/unauthorized` แบบ static — ยังไม่ได้เชื่อมกับ permission check ใดๆ |

---

## สิ่งที่ยังขาดอยู่ — สรุป

### RBAC-01: Permission Model & API Enforcement

> **ยังไม่ได้เริ่มเลย — นี่คือ security foundation ของทั้งระบบ**

- ไม่มีตาราง `workspace_members` — role ไม่มีอยู่ใน database ใดๆ เลย
- ไม่มี `role` ใน JWT — token ไม่มีข้อมูล authorization
- ไม่มีฟังก์ชัน `canDo()` — ไม่มี permission abstraction
- ไม่มี permission middleware — ทุก API endpoint เปิดกว้างสำหรับทุกคนที่ login แล้ว
- ไม่มี field `replied_by` บน message — ไม่มี audit trail ว่าใครเป็นคนตอบ
- ไม่มี admin protection — ไม่มีอะไรป้องกันไม่ให้ workspace ไม่มี Admin เหลือเลย

### RBAC-02: Member Management

> **มี invitation scaffolding อยู่บ้าง แต่ไม่รู้จัก role และยังไม่สมบูรณ์**

- Invitation ไม่มี field `role` — invite คนได้แต่กำหนด role ไม่ได้
- ไม่มี Resend invitation (ทั้ง endpoint และ UI)
- ไม่มี Cancel invitation (ทั้ง endpoint และ UI)
- ไม่มี Remove member (ทั้ง endpoint และ UI)
- ไม่มี Change role (ทั้ง endpoint และ UI)
- ไม่มีการ revoke session เมื่อ remove member
- ไม่มีการส่ง email — สร้าง record ใน DB แต่ไม่เคยส่ง email จริง
- ไม่มีการ enforce admin protection rules

### RBAC-03: Frontend Permission Enforcement

> **ยังไม่ได้เริ่มเลย — ตอนนี้ role ถูก hardcode เป็น `"admin"` สำหรับทุกคน**

- `role: "admin"` เป็น string ที่ hardcode อยู่ใน layout — ไม่ได้มาจากข้อมูลจริง
- ไม่มี hook `usePermission`
- ไม่มี route guard ตาม role — ทุกคนที่ login แล้วเข้าหน้า settings ได้หมด
- ไม่มีการกรอง sidebar ตาม role — ทุก menu item แสดงให้ทุกคนเห็น
- ไม่มีการจัดการ error 403 — API error ทำให้หน้าจอขาวหรือ crash
- ไม่มีการบันทึก URL ปัจจุบันเมื่อ session หมดอายุ

---

## ลำดับความสำคัญและ Effort

| ลำดับ | งาน | Points |
|---|---|---|
| P0 | ตาราง workspace_members + role enum | 5 |
| P0 | Permission matrix + ฟังก์ชัน `canDo()` | 3 |
| P0 | Permission middleware ครอบทุก protected endpoint | 5 |
| P0 | Admin protection service | 2 |
| P0 | Role ฝังอยู่ใน JWT | 2 |
| P0 | Hook `usePermission` + route guards (ฝั่ง Frontend) | 8 |
| P1 | Field `replied_by` บน message (audit trail) | 3 |
| P1 | Member Management API ครบ (resend, cancel, เปลี่ยน role, remove) | 8 |
| P1 | เชื่อมต่อ email delivery | 5 |
| P1 | Members UI ครบ (role, actions) + กรอง sidebar | 8 |
| P1 | จัดการ 403 + session expiry + assign panel | 5 |
| **รวม** | | **54 pts** |

---

## Dependencies & สิ่งที่บล็อกอยู่

```
RBAC-01 (Backend)  ──► RBAC-02 (Member Mgmt)  ──► RBAC-03 (Frontend)
     │                        │
     │                   ต้อง verify email
     └── Role ใน JWT          domain ก่อน
         ต้องมีก่อน
         RBAC-03 เริ่มได้
```

| สิ่งที่บล็อก | เจ้าของ | ผลกระทบ |
|---|---|---|
| Email domain ยังไม่ได้ verify (ระบุไว้ใน story) | Ops/Infra | RBAC-02 ไม่สามารถขึ้น production ได้ |
| ยังไม่มีตาราง `workspace_members` | Backend | บล็อก RBAC-01, RBAC-02 และ RBAC-03 ทั้งหมด |
| Role ไม่มีอยู่ใน JWT | Backend | บล็อก frontend permission check ทุกอย่าง |

---

## Risk Snapshot

| Risk | ระดับ |
|---|---|
| ไม่มี access control เลย — API endpoint ทุกตัวเปิดกว้าง | 🔴 วิกฤต |
| ยังไม่ยืนยัน email domain — ส่ง invite email ไม่ได้ | 🔴 วิกฤต |
| การ revoke session เมื่อ remove member ต้องใช้ pattern ข้าม service ที่ยังไม่เคยทำ | 🟡 ปานกลาง |
| `role: "admin"` ถูก hardcode ใน UI — demo ใดๆ ที่เกี่ยวกับ role จะผิดพลาด | 🟡 ปานกลาง |
| Flash of unauthorized content ถ้า FE guard ทำฝั่ง client เท่านั้น | 🟡 ปานกลาง |

---

## แนวทางที่แนะนำ

**Sprint 1 — สร้าง Foundation (RBAC-01)**
วาง database, permission logic และ API enforcement ให้เรียบร้อย สิ่งอื่นใน RBAC epic ทำถูกต้องไม่ได้ถ้าไม่มีสิ่งนี้

**Sprint 2 — Member Management + UI Enforcement (RBAC-02 + RBAC-03 คู่ขนานกัน)**
ทีม Backend ทำ invitation role support, resend/cancel, เปลี่ยน role และ remove member ให้เสร็จ ทีม Frontend implement `usePermission`, route guards และกรอง sidebar โดยใช้ role ที่มีอยู่ใน JWT แล้ว

**Gate ก่อน release:** ต้อง verify email domain และทดสอบ email delivery แบบ end-to-end ก่อน feature นี้จะขึ้น production ได้
