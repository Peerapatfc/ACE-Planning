# STORY-RBAC-01: Permission Model & API Enforcement — คำอธิบายแบบเข้าใจง่าย

## สรุปภาพรวม

RBAC-01 คือการวาง **ระบบตรวจสอบสิทธิ์** ที่ทุก endpoint ของ platform ต้องผ่านก่อนจะทำงานได้ ผลลัพธ์คือ "กำแพง" ที่บังคับว่า — role ไหนทำอะไรได้บ้าง และถ้าไม่มีสิทธิ์ระบบจะ block ทันทีก่อนที่ handler จะทำงาน

**เปรียบเทียบง่าย ๆ:**
เหมือนระบบรักษาความปลอดภัยในตึกออฟฟิศ — ก่อนเข้าห้องไหนก็ตาม ระบบจะสแกนบัตรก่อน ถ้าบัตรไม่มีสิทธิ์ประตูไม่เปิด ไม่ว่าจะขอร้องยังไงก็ตาม บัตรนั้นคือ role ของคุณ (admin / supervisor / agent)

> **สำคัญ:** Permission check ทำที่ backend เท่านั้น — frontend ที่ซ่อนเมนูเป็นแค่ UX ไม่ใช่ security จริง

---

## 1. ER Diagram — ตารางข้อมูล (เก็บอะไรบ้าง?)

### 10 ตาราง แบ่งเป็น 3 กลุ่ม

#### กลุ่ม A: Identity, Membership & Permissions (user-service DB)

| ตาราง | คืออะไร | สถานะ |
|---|---|---|
| **users** | คนที่ login เข้าระบบ — admin, supervisor, agent | เดิม |
| **refresh_tokens** | token สำหรับต่ออายุ JWT | เดิม |
| **workspace_members** | บันทึกว่า user คนนี้อยู่ใน workspace ไหน มี role อะไร | **ใหม่ — RBAC-02** |
| **permissions** | รายการ action ทั้งหมดที่มีในระบบ เช่น `assign_conversation` | **ใหม่ — RBAC-01** |
| **role_permissions** | matrix ว่า role ไหนทำ action ไหนได้ | **ใหม่ — RBAC-01** |
| **frontend_route_permissions** | map route URL → permission สำหรับ frontend route guard (RBAC-03) | **ใหม่ — RBAC-01** |

#### กลุ่ม B: Tenant Management (tenant-service DB)

| ตาราง | คืออะไร | สถานะ |
|---|---|---|
| **tenants** | บริษัทที่ใช้ platform | เดิม |
| **invitations** | คำเชิญสมาชิกใหม่ เพิ่ม field `role` และ `invited_by` | แก้ไข — RBAC-02 |

#### กลุ่ม C: Conversation Data (omnichat-service DB)

| ตาราง | คืออะไร | สถานะ |
|---|---|---|
| **conversations** | ห้องแชท | เดิม |
| **messages** | ข้อความ เพิ่ม field `replied_by` บันทึกว่าใครส่ง | แก้ไข — RBAC-01 |

### ความสัมพันธ์ — อ่านแบบนี้

```
ร้าน ABC Shop (tenant)
├── [user-service DB]
│   ├── User: นิด (users)
│   │   └── refresh_tokens (JWT session)
│   ├── workspace_members: นิด → role: admin     ← RBAC-01/02 ใช้ตรงนี้
│   ├── workspace_members: โอ๋ → role: supervisor
│   ├── workspace_members: แม็ค → role: agent
│   ├── permissions: assign_conversation, manage_members, ...  (9 actions)
│   └── role_permissions: admin → assign ✅, agent → assign ❌, ...
│
├── [tenant-service DB]
│   └── tenants: ABC Shop, invitations
│
└── [omnichat-service DB]
    ├── Conversation #1 (ลูกค้าทักมา)
    │   ├── Message: "สนใจสินค้า"       replied_by: null (ข้อความลูกค้า)
    │   └── Message: "สินค้ามีพร้อม"    replied_by: user_id ของ นิด ← RBAC-01 บังคับ NOT NULL
```

### Cross-Service — ทำไมบาง field ไม่มี FK?

```
user-service DB            tenant-service DB
───────────────            ─────────────────
workspace_members          tenants
  tenant_id ────────────▶  id
  (no DB FK)

user-service DB            omnichat-service DB
───────────────            ───────────────────
users                      messages
  id ───────────────────▶  replied_by
                           (no DB FK)
```

เพราะแต่ละ service มี database แยกกัน — PostgreSQL ไม่สามารถทำ FK ข้าม database ได้
แทน DB-level FK ด้วยการ validate ที่ application code แทน

หมายเหตุ: `workspace_members.user_id` → `users.id` อยู่ใน user-service DB เดียวกัน จึงมี FK จริงได้

### จุดสำคัญของ workspace_members

- อยู่ใน **user-service DB** (ไม่ใช่ omnichat-service หรือ tenant-service)
- `user_id` ชี้ไปหา `users.id` ในฐาน DB เดียวกัน — มี FK จริง
- `tenant_id` ชี้ไปหา `tenants.id` ใน tenant-service — cross-service, validate ที่ app code
- role ไม่ได้เก็บใน JWT — **ดึงจาก DB ทุก request** → role ที่เปลี่ยนมีผลทันทีบน request ถัดไป

---

## 2. Sequence Diagram — ลำดับการทำงาน (ทำอะไรก่อนหลัง?)

### Services ที่เกี่ยวข้อง

```
                         ┌─────────────────┐
Client (Browser/App) ──▶ │ OmnichatService │  ←── รับ request, ตรวจ JWT
                         └───────┬─────────┘
                                 │ ตรวจ permission ก่อนทำงาน
                                 ▼
                         ┌─────────────────┐
                         │  Permission     │  ←── "ยาม" — ตรวจก่อนเสมอ
                         │  Middleware     │
                         └───────┬─────────┘
                                 │ MessagePattern (ไม่ query DB ตรง)
                                 ▼
                         ┌─────────────────┐
                         │  UserService    │  ←── identity & auth hub
                         └───────┬─────────┘
                                 │
                         ┌───────┴──────────┐
                         ▼                  ▼
                    [user-service DB]    [omnichat-service DB]
                    workspace_members    conversations, messages
                    permissions
```

### 5 Flows

#### Flow 1: Permission Check ปกติ — สำคัญที่สุด

**สถานการณ์:** Agent (แม็ค) พยายาม assign conversation ซึ่งต้องการ Supervisor ขึ้นไป

```
ขั้นตอน:

1. แม็คส่ง POST /workspaces/:workspaceId/conversations/:id/assign
   → OmnichatService ตรวจ JWT → ได้ userId ของแม็ค

2. ถ้าไม่มี token → ตอบ 401 Unauthorized ทันที (ยังไม่ถึง permission check)

3. PermissionMiddleware รับ request (userId, tenantId, action="assign_conversation")
   → ส่ง MessagePattern ไปหา UserService:
     { cmd: 'get_workspace_member_role', payload: { userId, tenantId } }
   → UserService query workspace_members → ได้ role = "agent"

4. ถ้าไม่มี membership record → ตอบ 403 ทันที (ไม่ expose ว่า workspace มีอยู่จริงหรือไม่)

5. canDo("agent", "assign_conversation") → false (agent ไม่มีสิทธิ์)
   → ตอบ 403 Forbidden:
     { "error": "permission_denied", "action": "assign_conversation", "required_role": "supervisor" }
   → Handler ไม่ถูกเรียกเลย ✓
```

> **ทำไม middleware ไม่ query DB ตรง?** เพราะ omnichat-service กับ user-service มี DB แยกกัน — ถ้า query ตรงต้องเข้าถึง DB ของ service อื่น ซึ่งผิด architecture — ใช้ MessagePattern แทน

#### Flow 2: Fail-Closed — action ที่ไม่รู้จัก

**สถานการณ์:** มี request เข้ามาพร้อม action ที่ไม่อยู่ใน permission matrix

```
1. PermissionMiddleware ได้รับ action = "unknown_action"
2. ดึง role จาก UserService → role = "admin"
3. canDo("admin", "unknown_action") → action ไม่อยู่ใน matrix → DENY
4. ตอบ 403 Forbidden

สังเกต: ไม่ throw 500 — ออกแบบให้ "ปิดก่อนเสมอ" เมื่อไม่แน่ใจ
```

> **Fail-Closed หมายความว่า:** ถ้าระบบไม่รู้ว่าอนุญาตไหม — ตอบว่าไม่อนุญาตก่อนเสมอ ดีกว่าเปิดแล้วค่อยมาแก้ที่หลัง

#### Flow 3: Admin Protection — เปลี่ยน role

**สถานการณ์:** Admin พยายาม downgrade ตัวเองเป็น Supervisor แต่เป็น Admin คนเดียวที่เหลือ

```
1. PATCH /workspaces/:workspaceId/members/:memberId { role: "supervisor" }
   → PermissionMiddleware ผ่านแล้ว (caller มีสิทธิ์ manage_members)

2. AdminProtectionService เช็คก่อน:
   SELECT COUNT(*) FROM workspace_members WHERE tenant_id = ? AND role = 'admin'
   → adminCount = 1

3. target คือ Admin คนเดียวที่เหลือ → BLOCK
   → ตอบ 400 Bad Request:
     { "error": "workspace_must_have_at_least_one_admin" }

ถ้า adminCount >= 2 → อนุญาต → UPDATE role ได้ปกติ
```

#### Flow 4: Admin Protection — ลบสมาชิก

**สถานการณ์:** Admin A พยายามลบ Admin B ซึ่งเป็น Admin คนสุดท้าย

```
1. DELETE /workspaces/:workspaceId/members/:memberId
2. AdminProtectionService เช็ค role ของ target ก่อน → "admin"
3. เพราะ target เป็น admin → เช็คจำนวน admin ที่เหลือ
   → adminCount = 1 → BLOCK → 400

ถ้า target ไม่ใช่ admin หรือ adminCount >= 2 → ลบได้ปกติ
   → หลังลบ: revoke token ทั้งหมดของ user ที่ถูกลบ (ผ่าน user-service)
```

> **ทำไมต้อง revoke token ด้วย?** เพราะถ้าไม่ revoke คนที่ถูกลบออกจาก workspace ยังใช้ JWT เดิมเข้าระบบได้จนกว่า token จะหมดอายุเอง

#### Flow 5: Reply — บันทึกว่าใครส่ง

**สถานการณ์:** Agent ส่งข้อความตอบลูกค้า

```
1. POST /workspaces/:workspaceId/conversations/:id/reply { content: "..." }
   → PermissionMiddleware ผ่าน (reply_any_conversation — ทุก role ทำได้)

2. MessageHandler:
   → ดึง userId จาก JWT (ไม่รับ replied_by จาก client)
   → INSERT INTO messages (conversation_id, content, replied_by)
     VALUES (?, ?, userId)
   → replied_by = NOT NULL เสมอ ← DB constraint บังคับ

3. ตอบ 201 Created: { id, content, replied_by: userId, created_at }

ถ้าพยายาม update replied_by ทีหลัง → 400 field is immutable
```

---

## 3. Permission Matrix — role ไหนทำอะไรได้บ้าง

| Action | Admin | Supervisor | Agent | ใช้ที่ endpoint |
|---|---|---|---|---|
| `reply_any_conversation` | ✅ | ✅ | ✅ | POST .../reply |
| `assign_conversation` | ✅ | ✅ | ❌ | POST .../assign |
| `change_conversation_status` | ✅ | ✅ | ✅ | PATCH .../status |
| `config_sla` | ✅ | ✅ | ❌ | PATCH .../sla |
| `config_notification` | ✅ | ✅ | ❌ | PATCH .../notifications |
| `view_team_report` | ✅ | ✅ | ❌ | GET .../reports/team |
| `manage_members` | ✅ | ❌ | ❌ | GET/PATCH/DELETE .../members |
| `manage_channels` | ✅ | ❌ | ❌ | POST/PATCH/DELETE .../channels |
| `manage_workspace` | ✅ | ❌ | ❌ | PATCH /workspaces/:id |

Matrix นี้เก็บใน DB (`role_permissions` table) — ไม่ใช่ hardcoded ใน code
โหลดเข้า memory ตอน startup และ `canDo(role, action)` check จาก in-memory แทนการ query DB ทุก request

---

## 4. Error Response — format มาตรฐาน

```
401 Unauthorized       → ไม่มี token หรือ token หมดอายุ
                         { "error": "unauthorized" }

403 Forbidden          → มี token แต่ไม่มีสิทธิ์ หรือไม่ได้เป็นสมาชิก workspace นี้
                         { "error": "permission_denied",
                           "action": "assign_conversation",
                           "required_role": "supervisor" }

400 Bad Request        → Admin protection — จะเหลือ Admin 0 คน
                         { "error": "workspace_must_have_at_least_one_admin" }
```

---

## สรุปตัวเลข

| หมวด | จำนวน |
|---|---|
| ตารางใหม่/แก้ไข | 5 ตาราง (workspace_members, invitations, permissions, role_permissions, frontend_route_permissions) |
| Sequence Flows | 5 flows |
| Protected actions | 9 actions |
| Roles | 3 roles (admin, supervisor, agent) |
| Role × Action combinations | 27 combinations (ทดสอบครบทุกตัว) |

---

## ตัวอย่าง End-to-End: User พยายามทำ action ต่าง ๆ

```
สมมติ:
  นิด  → role: Admin   ใน Workspace A
  โอ๋  → role: Supervisor ใน Workspace A
  แม็ค → role: Agent   ใน Workspace A
  นิด  → role: Agent   ใน Workspace B  ← คนเดียวกัน คนละ workspace คนละ role

────────────────────────────────────────────────────

สถานการณ์ 1: แม็ค (Agent) พยายาม assign conversation ใน Workspace A
→ Permission check: resolveRole(แม็ค, workspaceA) → "agent"
→ canDo("agent", "assign_conversation") → false
→ 403 Forbidden ✓

สถานการณ์ 2: นิด (Admin ใน A) พยายาม assign ใน Workspace B
→ Permission check: resolveRole(นิด, workspaceB) → "agent"
→ canDo("agent", "assign_conversation") → false
→ 403 Forbidden ✓  ← สิทธิ์ scope ต่อ workspace ไม่ข้ามกัน

สถานการณ์ 3: โอ๋ (Supervisor) ส่งข้อความตอบลูกค้า
→ Permission check: resolveRole(โอ๋, workspaceA) → "supervisor"
→ canDo("supervisor", "reply_any_conversation") → true
→ Handler ทำงาน → INSERT message (replied_by = โอ๋'s userId) ✓

สถานการณ์ 4: นิด (Admin เดียว) พยายาม downgrade role ตัวเอง
→ Permission check ผ่าน (manage_members)
→ AdminProtectionService: adminCount = 1 → BLOCK
→ 400 workspace_must_have_at_least_one_admin ✓

สถานการณ์ 5: JWT ของแม็คยังไม่หมดอายุ แต่ role เพิ่งถูกเปลี่ยนเป็น Supervisor
→ resolveRole ดึงจาก DB ทุกครั้ง → ได้ "supervisor" ทันที
→ สิทธิ์ใหม่มีผลทันทีโดยไม่ต้อง logout/login ✓
```
