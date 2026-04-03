# EPIC ACE-1610 RBAC — Gap Analysis & แผนการ Implementation

## สรุปภาพรวม

Stories ทั้งสามอยู่ในสถานะ **Backlog** ผลการสำรวจโค้ดพบว่า:

| Story | ความต้องการของ Epic | สถานะการ Implement | % เสร็จ |
|---|---|---|---|
| RBAC-01 | Permission Model & API Enforcement | **ยังไม่ได้เริ่ม** | ~0% |
| RBAC-02 | Member Management | **มีแค่ Scaffolding** | ~20% |
| RBAC-03 | Frontend Permission Enforcement | **ยังไม่ได้เริ่ม** | ~0% |

Platform ยังไม่มีแนวคิดเรื่อง role ใน database schema, JWT, permission middleware หรือ `canDo()` abstraction ใดๆ ทั้งสิ้น Invitation flow มี token mechanics พื้นฐานแต่ยังขาด field `role`, การ resend/cancel, email delivery และ admin-protection rules ทุกข้อ ส่วน Frontend มีแค่ string `role: "admin"` ที่ hardcode ไว้ใน layout เท่านั้น — ไม่ได้มาจากข้อมูลจริง

---

## RBAC-01 — Permission Model & API Enforcement

### สิ่งที่มีอยู่แล้ว

- `jwt-auth.guard.ts` ใน api-gateway (authentication เท่านั้น — ยังไม่มี authorization)
- Type `JwtPayload` ใน `@monorepo/shared` มี fields: `sub`, `tenantId`, `email`, `firstName`, `lastName` — **ไม่มี field `role`**
- Message record มี field `agent_id` — **ไม่ใช่ `replied_by`**; ไม่มี immutability constraint

### สิ่งที่ยังขาด

| Gap | รายละเอียด | ไฟล์ที่ต้องสร้าง/แก้ไข |
|---|---|---|
| ตาราง `workspace_members` | ไม่มี junction table `(user_id, workspace_id, role)` ใน Prisma schema ใดๆ | `tenant-service/prisma/schema.prisma` |
| Role enum | ไม่มีการนิยาม `admin \| supervisor \| agent` ที่ไหนเลย | Constant ใหม่ใน `@monorepo/shared` |
| `role` ใน JWT payload | Interface `JwtPayload` ขาด `role`; `issueTokens()` ไม่ได้ query หรือฝัง role ไว้ | `shared/src/types/auth.types.ts`, `api-gateway/src/auth/auth.service.ts` |
| `canDo()` helper | ไม่มีฟังก์ชัน permission แบบ action-based ที่ไหนเลย | Service/util ใหม่ใน `api-gateway` หรือ `@monorepo/shared` |
| Permission matrix constant | ไม่มีที่เดียวที่นิยามว่า role ไหนทำ action ใดได้บ้างใน 9 actions | ไฟล์ constants ใหม่ |
| Permission middleware/guard | ไม่มี NestJS guard ที่ evaluate `canDo()` ก่อน endpoint handler | `PermissionGuard` ใหม่ + decorator `@RequirePermission()` |
| Protected endpoints | `POST /conversations/:id/assign`, SLA config, member management, channel management, workspace config — ทั้งหมดยังไม่มี permission guard | หลาย controllers |
| Field `replied_by` บน Message | Schema ใช้ `agent_id`; ต้อง rename/add และต้องเป็น non-nullable และ immutable | `omnichat-service/prisma/schema.prisma`, `messages.service.ts` |
| Admin protection service | ไม่มี service บังคับว่า "workspace ต้องมี admin อย่างน้อย 1 คน" ก่อนเปลี่ยน role หรือลบ member | Shared service ใหม่ใน `tenant-service` |
| รูปแบบ 403 error | ไม่มี standardized response `{ error: "permission_denied", action: "...", required_role: "..." }` | Shared error DTO |

### แผนการ Implementation

**Step 1 — Data Model (prerequisite ของทุกอย่าง)**

เพิ่ม `WorkspaceMember` ใน `tenant-service/prisma/schema.prisma`:

```prisma
model WorkspaceMember {
  id           String    @id @default(uuid())
  tenant_id    String
  user_id      String
  role         String    // admin | supervisor | agent
  joined_at    DateTime  @default(now())
  created_at   DateTime  @default(now())
  updated_at   DateTime  @updatedAt
  deleted_at   DateTime?

  tenant Tenant @relation(fields: [tenant_id], references: [id])

  @@unique([tenant_id, user_id])
  @@index([tenant_id, role])
  @@map("workspace_members")
}
```

Rename `agent_id` → `replied_by` บน `Message` ใน `omnichat-service/prisma/schema.prisma` (ทำให้ non-nullable สำหรับ outbound direction)

**Step 2 — Role ใน JWT**

- เพิ่ม `role: string` ใน `JwtPayload` ใน `packages/shared/src/types/auth.types.ts`
- อัพเดต `issueTokens()` ใน `api-gateway/src/auth/auth.service.ts` ให้ query `WorkspaceMember` และฝัง role ไว้ใน access token

**Step 3 — Permission Matrix + `canDo()` Helper**

สร้าง `packages/shared/src/constants/permissions.ts`:

```typescript
export const PERMISSION_MATRIX: Record<string, string[]> = {
  reply_any_conversation:     ['admin', 'supervisor', 'agent'],
  assign_conversation:        ['admin', 'supervisor'],
  change_conversation_status: ['admin', 'supervisor', 'agent'],
  config_sla:                 ['admin', 'supervisor'],
  config_notification:        ['admin', 'supervisor'],
  view_team_report:           ['admin', 'supervisor'],
  manage_members:             ['admin'],
  manage_channels:            ['admin'],
  manage_workspace:           ['admin'],
};

export function canDo(role: string, action: string): boolean {
  return PERMISSION_MATRIX[action]?.includes(role) ?? false;
}
```

**Step 4 — NestJS `PermissionGuard`**

สร้าง guard ใน `api-gateway/src/auth/guards/permission.guard.ts` ที่:
1. อ่าน `role` จาก JWT payload
2. อ่าน required action จาก decorator `@RequirePermission('action_name')` ผ่าน `Reflector`
3. เรียก `canDo(role, action)` → ถ้า false ส่งกลับ 403 พร้อม body มาตรฐาน

```typescript
// รูปแบบ 403 response body
{ error: "permission_denied", action: "assign_conversation", required_role: "supervisor" }
```

**Step 5 — Apply Guard กับ Protected Action Endpoints ทั้ง 9 ตัว**

ใส่ `@RequirePermission()` กับทุก controller method ที่เกี่ยวข้อง:

| Endpoint | Action |
|---|---|
| `POST /conversations/:id/assign` | `assign_conversation` |
| `PATCH /conversations/:id/status` | `change_conversation_status` |
| `POST/PATCH /settings/sla` | `config_sla` |
| `POST/PATCH /settings/notifications/rules` | `config_notification` |
| `GET /reports/team` | `view_team_report` |
| `POST/DELETE /settings/members` | `manage_members` |
| `POST/PATCH/DELETE /settings/channels` | `manage_channels` |
| `PATCH /settings/workspace` | `manage_workspace` |

**Step 6 — Admin Protection Service**

สร้าง `tenant-service/src/tenants/admin-protection.service.ts`:

```typescript
async ensureAdminRemains(tenantId: string, excludeUserId: string): Promise<void> {
  const adminCount = await this.prisma.workspaceMember.count({
    where: {
      tenant_id: tenantId,
      role: 'admin',
      deleted_at: null,
      user_id: { not: excludeUserId },
    },
  });
  if (adminCount < 1) {
    throw new BadRequestException('workspace_must_have_at_least_one_admin');
  }
}
```

**Step 7 — First Admin เมื่อสร้าง Workspace**

ใน `api-gateway/src/auth/auth.service.ts` ฟังก์ชัน `register()`: หลังสร้าง tenant + user ให้ insert row `WorkspaceMember` พร้อม `role: 'admin'`

**Step 8 — บังคับใช้ `replied_by`**

อัพเดต `omnichat-service/src/messages/messages.service.ts` การสร้าง outbound message ให้ set `replied_by = agentUserId` จาก caller context Field ต้องเป็น non-nullable สำหรับ outbound message และ immutable หลังจากสร้างแล้ว

### Test Cases

| Test | ผลที่คาดหวัง |
|---|---|
| `canDo('agent', 'assign_conversation')` | `false` |
| `canDo('supervisor', 'config_sla')` | `true` |
| `canDo('supervisor', 'manage_members')` | `false` |
| Agent เรียก `POST /conversations/:id/assign` | `403 { error: "permission_denied", action: "assign_conversation" }` |
| User ที่ไม่มี workspace membership เรียก protected endpoint | `403` (ไม่ใช่ 404) |
| Token หาย / หมดอายุ | `401` ก่อน permission check |
| Workspace มี admin 1 คน ขอ demote เขา | `400 workspace_must_have_at_least_one_admin` |
| Workspace มี admin 2 คน admin self-demote | `200` |
| สร้าง outbound message | `replied_by` = sender user ID, non-null |

### Acceptance Criteria

- 9 actions ทั้งหมดจาก permission matrix ถูกบังคับใช้ที่ API layer — ยืนยันด้วย integration tests
- Unit tests ของ `canDo()` ครอบคลุมทุก 27 combinations (9 actions × 3 roles)
- ไม่มี protected handler ทำงานเมื่อ caller ขาด permission
- `replied_by` ไม่เป็น null บน outbound message ใดๆ เลย
- Workspace มี admin อย่างน้อย 1 คนตลอดเวลา

### Story Points: **8 points**
### Priority: **P0 — บล็อกทุกอย่างที่เหลือ**
### Risk: **สูง** — ทุก feature ปัจจุบันไม่มี access control เลย Schema migration ต้องประสานกับ omnichat-service migration (rename `replied_by`)

---

## RBAC-02 — Member Management

### สิ่งที่มีอยู่แล้ว

| Component | สถานะ |
|---|---|
| Invitation token creation (32-byte hex) | ✅ Implemented |
| Invitation 7-day expiry | ✅ Implemented |
| Token hashing (SHA-256) | ✅ Implemented |
| หน้า Accept invitation (UI) | ✅ Implemented |
| Invite member form (UI) | ✅ Implemented (พื้นฐาน, ไม่มี role field) |
| Members list page (UI) | ✅ Scaffolded (read-only, ไม่มี role/actions) |
| Invitations list page (UI) | ✅ Scaffolded (ไม่มี Resend/Cancel) |

### สิ่งที่ยังขาด

| Gap | รายละเอียด |
|---|---|
| Field `role` บน Invitation | `CreateInvitationDto` ไม่มี `role` — invitation ไม่สามารถกำหนด role ได้ |
| Column `role` ในตาราง `invitations` | Schema ของ `tenant-service` ไม่มี `role` บน model `Invitation` |
| ตาราง `workspace_members` | การ accept invitation ไม่มีที่เก็บ membership พร้อม role ที่ได้รับ |
| Resend invitation | ไม่มี endpoint (`PATCH /invitations/:id/resend`) และไม่มี UI action |
| Cancel invitation | ไม่มี endpoint (`DELETE /invitations/:id`) และไม่มี UI action |
| Remove member | ไม่มี endpoint และไม่มี UI |
| Change role | ไม่มี endpoint และไม่มี UI |
| Session revocation เมื่อลบ member | ไม่มีกลไก revoke refresh token ของ user ที่ถูกลบ |
| แสดงผล "former member" | ยังไม่ implement fallback ของ `replied_by` สำหรับ member ที่ถูกลบแล้ว |
| Admin protection เมื่อลบ/เปลี่ยน role | ไม่มีการ validate ก่อน member action ใดๆ |
| Email delivery | `createInvitation()` สร้าง DB record เท่านั้น — ไม่เคยส่ง email จริงๆ |
| Members page: role column | ตารางแสดงแค่ Name, Email, Joined — ขาด Role, Last Active, Actions |
| Members page: actions | ไม่มี inline role dropdown, ไม่มีปุ่ม Remove |
| Duplicate invite guard | เช็ค `tenant_id + email + status` แต่ไม่มี role validation |
| Member limit enforcement | ยังไม่มีการเช็ค limit |
| First Admin auto-assignment | เมื่อสร้าง workspace ผู้สร้างไม่ได้ถูกเพิ่มใน `workspace_members` เป็น admin |

### แผนการ Implementation

**Step 1 — Schema: เพิ่ม `role` ให้ Invitation, สร้าง `WorkspaceMember`**
(ร่วมกับ RBAC-01 Step 1)

```prisma
// เพิ่มใน Invitation model:
role String @default("agent") // admin | supervisor | agent
```

**Step 2 — อัพเดต `CreateInvitationDto`**

```typescript
@IsEnum(['admin', 'supervisor', 'agent'])
role: string;
```

**Step 3 — Resend Invitation Endpoint**

`PATCH /invitations/:id/resend` ใน `tenant-service`:
- สร้าง token ใหม่, อัพเดต `token_hash`, `expires_at = now + 7d`, `status = 'pending'`
- Trigger email resend

**Step 4 — Cancel Invitation Endpoint**

`DELETE /invitations/:id` ใน `tenant-service`:
- Set `status = 'cancelled'`; token เดิมจะใช้ accept ไม่ได้อีกต่อไป

**Step 5 — `acceptInvitation()` สร้าง WorkspaceMember**

อัพเดต `invitations.service.ts` ฟังก์ชัน `acceptInvitation()`:
- หลัง mark accepted ให้ upsert `WorkspaceMember` พร้อม `role` จาก invitation record

**Step 6 — Remove Member Endpoint**

`DELETE /workspace-members/:userId` ใน `tenant-service`:
- เรียก admin-protection check (RBAC-01 Step 6)
- Set `deleted_at` บน `WorkspaceMember`
- เรียก `user-service` ผ่าน TCP เพื่อ revoke refresh token ทั้งหมดของ `user_id` นั้น

**Step 7 — Change Role Endpoint**

`PATCH /workspace-members/:userId/role` ใน `tenant-service`:
- เรียก admin-protection check
- อัพเดต `role` บน `WorkspaceMember`
- **ไม่** revoke session — permission ใหม่มีผลทันทีใน API call ถัดไป

**Step 8 — Email Delivery Integration**

เชื่อม email sender (SES / SMTP / Resend) เข้ากับ `tenant-service` Trigger หลังสร้างและ resend invitation Template ประกอบด้วย `{invitation_url}` ที่ชี้ไปที่ `https://<domain>/invite/<raw_token>`

> **External dependency:** ต้อง verify domain ก่อนจะขึ้น production ได้ ระหว่าง development ใช้ mock/console email ได้

**Step 9 — Frontend: อัพเดต Members Page**

เพิ่ม Role column, Last Active column, inline role dropdown (พร้อม confirm dialog), ปุ่ม Remove (พร้อม confirm dialog) ใน `settings/members/page.tsx`

**Step 10 — Frontend: อัพเดต Invitations Page**

เพิ่มปุ่ม Resend และ Cancel action ในแต่ละแถวของ pending invitation เพิ่ม Role column

**Step 11 — Frontend: อัพเดต Invite Form**

เพิ่ม role selector (Admin / Supervisor / Agent) ใน `InviteMemberForm`

### Test Cases

| Test | ผลที่คาดหวัง |
|---|---|
| Invite ด้วย role `agent` → accept → เช็ค `workspace_members` | มี row ที่มี `role = 'agent'` |
| Invite email เดิมซ้ำสองครั้ง | 409 Conflict |
| Accept invitation หลัง 7 วัน | ถูกปฏิเสธ; status = `expired` |
| Cancel invitation → ใช้ link เดิม | Invalid / 404 |
| Resend → link เดิมใช้ไม่ได้, link ใหม่ใช้ได้ | ✅ |
| Remove member → member เรียก API ใดๆ | 401 |
| Workspace มี admin 1 คน → ลบ admin | 400 `workspace_must_have_at_least_one_admin` |
| เปลี่ยน role → API call ถัดไปใช้ permission ใหม่ | ✅ (ไม่ต้อง login ใหม่) |
| Log แสดงผล reply ของ removed member | แสดง `"former member (Name)"` |

### Acceptance Criteria

- Invitation flow end-to-end: invite (พร้อม role) → ส่ง email → accept ภายใน 7 วัน → มี row ใน `workspace_members` ที่มี role ถูกต้อง
- Resend reset expiry; token เดิม invalidated
- Removed member ได้รับ 401 ใน API call ถัดไป (session revoked ทันที)
- Workspace มี admin อย่างน้อย 1 คน — บังคับใช้ที่ backend
- Member management actions ทั้งหมดเข้าถึงได้เฉพาะ Admin role (guard โดย RBAC-01 `manage_members` permission)

### Story Points: **13 points**
### Priority: **P1 — ต้องมี RBAC-01 ก่อน**
### Risk: **MEDIUM-HIGH** — Email delivery มี external dependency (domain verification) Session revocation ต้องใช้ TCP communication ข้าม service ระหว่าง `tenant-service` กับ `user-service` ที่ยังไม่ได้ทำ

---

## RBAC-03 — Frontend Permission Enforcement

### สิ่งที่มีอยู่แล้ว

| Component | สถานะ |
|---|---|
| Auth-only redirect ใน `(main)/layout.tsx` | ✅ Redirect ไป `/login` ถ้าไม่มี session |
| หน้า `/unauthorized` (static) | ✅ มีอยู่แต่ยังไม่ได้ wire กับ role-based check |
| Next.js App Router (รองรับ SSR guards ระดับ layout) | ✅ Architecture รองรับ pattern นี้ |

### สิ่งที่ยังขาด

| Gap | รายละเอียด |
|---|---|
| `role` ใน session/app state | JWT payload ไม่มี role; `currentUser` ใน dashboard layout hardcode `role: "admin"` |
| `usePermission` hook | ไม่มีอยู่เลย |
| Route guards (role-based) | Layout เช็คแค่ `me` (auth) ไม่เช็ค `me.role` ตาม route |
| Role-based sidebar filtering | Sidebar render ทุก item ให้ทุกคน |
| Assign panel visibility | ไม่มีการเช็ค `canDo` — Agent เห็นปุ่ม Assign |
| 403 page integration | หน้า `/unauthorized` มีอยู่แต่ 403 API responses ไม่ trigger มัน |
| Flash-of-unauthorized-content prevention | ไม่มีการเช็ค role ฝั่ง SSR ก่อน render หน้าที่ restricted |
| Session expiry พร้อม return URL | เมื่อเกิด 401 redirect ไป `/login` แต่ไม่ได้ save URL ปัจจุบัน |
| Conversation assigned-to banner | Banner "assigned to [Agent Name]" ยังไม่ได้ implement |
| `usePermission` update เมื่อ role เปลี่ยน | ไม่มี invalidation mechanism เมื่อ role เปลี่ยนระหว่าง session |

### แผนการ Implementation

**Step 1 — ฝัง Role ใน Session**

หลังจาก RBAC-01 เพิ่ม `role` ใน JWT แล้ว อัพเดต `getMeAction()` ใน `workspace-admin/src/server/auth.ts` ให้ decode และ return `role` อัพเดต interface `CurrentUser`:

```typescript
export interface CurrentUser {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  avatar_url: string | null;
  role: 'admin' | 'supervisor' | 'agent';
}
```

ลบ hardcoded `role: "admin"` ออกจาก `workspace-admin/src/app/(main)/dashboard/layout.tsx`

**Step 2 — `usePermission` Hook**

สร้าง `workspace-admin/src/hooks/use-permission.ts`:

```typescript
// อ่าน role จาก Zustand/React Context ที่ populate ตอน session load
// Return boolean — ไม่เรียก API เลย
export function usePermission(action: PermissionAction): boolean {
  const role = useCurrentUserStore((s) => s.role);
  return canDo(role, action); // import มาจาก @monorepo/shared
}
```

**Step 3 — Role-Based Route Guards**

สำหรับแต่ละ settings route ที่ restricted เพิ่ม server-side check ใน layout หรือ page:

```typescript
// เช่น app/(main)/settings/sla/layout.tsx
const me = await getMeAction();
if (!canDo(me.role, 'config_sla')) {
  redirect('/inbox?error=unauthorized');
}
```

ทำงานก่อน content ของ page ใดๆ render — ป้องกัน flash of unauthorized content

**Route Permission Map:**

| Route | Required Action |
|---|---|
| `/settings/workspace/*` | `manage_workspace` |
| `/settings/channels` | `manage_channels` |
| `/settings/sla` | `config_sla` |
| `/settings/notifications/rules` | `config_notification` |
| `/settings/notifications/preferences` | (ทุก role — ไม่ต้อง guard) |
| `/settings/members` | `manage_members` |

**Step 4 — Role-Based Sidebar Filtering**

อัพเดต `AppSidebar` / sidebar-items logic ให้ filter `NavGroup` items ตาม `currentUser.role` ก่อน render:

- **Admin:** ทุก section
- **Supervisor:** SLA, Notifications เท่านั้น (Workspace, Channels, Members ไม่ปรากฏใน DOM)
- **Agent:** Notifications > My Preferences เท่านั้น

Items ที่ซ่อนต้อง **ไม่มีอยู่ใน DOM เลย** — ไม่ใช่แค่ greyed-out หรือ hidden ด้วย CSS

**Step 5 — Assign Panel Conditional Rendering**

Wrap `AssignPanel` ใน conversation detail ด้วย:

```tsx
{canDo(currentUser.role, 'assign_conversation') && <AssignPanel ... />}
```

ต้องเป็น SSR conditional rendering (ไม่ใช่ client-side toggle) เพื่อป้องกัน flash

**Step 6 — 403 API Error Handling**

ใน HTTP client ให้ intercept 403 responses และ redirect ไป `/unauthorized` หน้า `/unauthorized` ต้องไม่เปิดเผยว่ากำลัง access resource อะไรอยู่

**Step 7 — Session Expiry พร้อม Return URL**

เมื่อได้รับ 401 response ให้ save path ปัจจุบันแล้ว redirect:

```
/login?returnTo={encodeURIComponent(currentPath)}
```

แสดงข้อความ: `"กรุณา login ใหม่ session หมดอายุแล้ว"` หลัง login สำเร็จอ่าน param `returnTo` แล้ว redirect ไปที่นั่น

**Step 8 — Conversation Assigned-To Banner**

ใน conversation view เมื่อ `conversation.assigned_agent_id !== currentUser.id` (และ conversation ถูก assign แล้ว) ให้แสดง banner: `"Assigned to {assigned_agent_name}"` ข้อมูลนี้อยู่ใน model `Conversation` อยู่แล้ว — ไม่ต้องเรียก API เพิ่ม

**Step 9 — `usePermission` Invalidation เมื่อ Role เปลี่ยน**

เมื่อ token refresh flow ออก access token ใหม่ (ที่มี role อัพเดต) ให้ re-derive role จาก token ใหม่แล้วอัพเดต Zustand store Hook consumers จะ re-render reactively พร้อม permission values ที่อัพเดตแล้ว

### Test Cases

| Test | ผลที่คาดหวัง |
|---|---|
| Agent navigate ตรงไปที่ `/settings/sla` | Redirect ไป `/inbox` + toast; ไม่มี SLA content ใน DOM |
| Supervisor เปิด Settings sidebar | มีแค่ SLA กับ Notifications; ไม่มี Workspace / Members |
| Agent เปิด Settings sidebar | มีแค่ Notifications > My Preferences |
| Agent เปิด conversation ที่ assign ให้ agent อื่น | Reply input ใช้งานได้; banner "Assigned to [Name]" แสดงอยู่; ไม่มี Assign panel |
| Server ส่งกลับ 403 | แสดงหน้า `/unauthorized` พร้อมปุ่ม back; ไม่ crash |
| `usePermission('assign_conversation')` — Supervisor | `true` |
| `usePermission('assign_conversation')` — Agent | `false` |
| Session token หมดอายุระหว่าง session | Redirect ไป `/login?returnTo=...` พร้อมข้อความแจ้งหมดอายุ |
| Role เปลี่ยนฝั่ง server → user refresh token | Permission ใหม่มีผลโดยไม่ต้อง full page reload |

### Acceptance Criteria

- ไม่มี restricted element ปรากฏใน DOM — แม้แต่ชั่วคราว — สำหรับ user ที่ไม่มีสิทธิ์ (ยืนยันด้วย visual regression + DOM inspection)
- Agent ไม่สามารถเห็น Assign panel ใน conversation ใดๆ ได้เลยทุกกรณี
- Route guard redirect ก่อน page render เมื่อ access route ที่ไม่ได้รับอนุญาต
- `usePermission` derive จาก cached session — ไม่มี API call เพิ่มขึ้นต่อการ render
- 403 responses จาก server ไม่ทำให้หน้าขาวหรือ crash เลย
- Session expiry เก็บ URL ปัจจุบันไว้สำหรับ redirect หลัง login

### Story Points: **8 points**
### Priority: **P2 — ต้องมี RBAC-01 (role ใน JWT) ก่อน**
### Risk: **MEDIUM** — Flash-of-unauthorized-content ต้องใช้ SSR-first checks; shortcut ฝั่ง client จะทำให้ไม่ผ่าน acceptance criteria React Compiler (ที่ enable ใน project นี้) อาจกระทบ memoization ของ `usePermission` — ต้องทดสอบให้ดี

---

## ลำดับความสำคัญ

| ลำดับ | Feature | Story | Points | บล็อก |
|---|---|---|---|---|
| P0-1 | ตาราง `workspace_members` & role enum | RBAC-01/02 | 5 | ทุกอย่าง |
| P0-2 | Permission matrix & `canDo()` helper | RBAC-01 | 3 | Guards ทั้งหมด |
| P0-3 | Permission middleware บน protected endpoints | RBAC-01 | 5 | API security |
| P0-4 | Admin protection service | RBAC-01/02 | 2 | Member ops |
| P0-5 | `usePermission` hook & role ใน JWT | RBAC-03 | 3 | FE guards ทั้งหมด |
| P0-6 | Route guards | RBAC-03 | 5 | Settings access |
| P1-1 | Field `replied_by` บน messages | RBAC-01 | 3 | Audit trail |
| P1-2 | Member Management API ครบ | RBAC-02 | 8 | Admin workflow |
| P1-3 | Email delivery integration | RBAC-02 | 5 | Invite flow |
| P1-4 | Members Management UI ครบ | RBAC-02 | 5 | Admin usability |
| P1-5 | Role-based sidebar filtering | RBAC-03 | 3 | UX clarity |
| P1-6 | 403 page & session expiry handling | RBAC-03 | 3 | Error UX |
| P1-7 | Assign panel visibility & banner | RBAC-03 | 2 | Agent UX |

**รวม: 52 story points**

---

## Sprint Breakdown ที่แนะนำ

### Sprint A — Backend Foundation (23 points)

| งาน | Points |
|---|---|
| Schema ตาราง `workspace_members` + `role` บน Invitation | 5 |
| Permission matrix + `canDo()` ใน `@monorepo/shared` | 3 |
| `PermissionGuard` + decorator `@RequirePermission()` | 5 |
| Admin protection service | 2 |
| Role ฝังอยู่ใน JWT (อัพเดต `issueTokens`) | 2 |
| First Admin auto-assignment เมื่อสร้าง workspace | 1 |
| Field `replied_by` บน Message | 3 |
| Unit tests: 27 combinations ของ `canDo()` | 2 |

### Sprint B — Member Management + Frontend (29 points)

| งาน | Points |
|---|---|
| `role` บน `CreateInvitationDto` + `acceptInvitation()` สร้าง WorkspaceMember | 2 |
| Resend + Cancel invitation endpoints | 3 |
| Change role + Remove member endpoints (พร้อม session revocation) | 5 |
| Email delivery integration | 5 |
| Members page UI ครบ (role, last active, เปลี่ยน role, remove) | 5 |
| `usePermission` hook | 3 |
| Role-based route guards (6 routes) | 3 |
| Role-based sidebar filtering | 3 |

> RBAC-03 items สามารถเริ่มพร้อมกันได้ทันทีที่ JWT role จาก Sprint A พร้อม

---

## Risk Summary

| Risk | ระดับความรุนแรง | การแก้ไข |
|---|---|---|
| Schema migration — user ที่มีอยู่ทั้งหมดไม่มี row ใน `workspace_members` | สูง | Run seeder เพื่อ insert Admin rows สำหรับ tenant users ที่มีอยู่ทั้งหมดระหว่าง migration |
| Rename `replied_by` บนตาราง `messages` — อาจทำ query ที่มีอยู่พัง | กลาง | เพิ่ม column ใหม่, backfill จาก `agent_id`, deprecate column เดิมใน migration แยกต่างหาก |
| ยังไม่ verify email domain (ระบุไว้ใน story) | สูง | Mock/console email ใน dev; ตั้งเป็น release gate ก่อนขึ้น production |
| Session revocation ข้าม service (tenant-service → user-service) | สูง | TCP message ใหม่ `{ cmd: 'revoke_all_tokens' }` — validate TCP channel pattern ด้วย integration test |
| Flash-of-unauthorized-content ใน Next.js App Router | กลาง | บังคับใช้ SSR-level role checks ใน server layouts ไม่ใช่ client components — validate ใน code review |
| Hardcoded `role: "admin"` ใน dashboard layout | สูง | ต้องลบออกก่อน demo หรือทดสอบ feature ที่เกี่ยวกับ role |
| React Compiler อาจกระทบ memoization ของ `usePermission` | ต่ำ | ทดสอบ hook behavior ให้ละเอียด; หลีกเลี่ยงการ wrap `useMemo` เองถ้าไม่ได้ verify output ของ compiler แล้ว |
| Endpoint ที่ขาดไปจาก permission coverage | กลาง | สร้าง endpoint audit checklist; automated test ที่ verify ว่า HTTP routes ทั้งหมดผ่าน guard |

---

## Deliverables ตาม Story

### RBAC-01 Deliverables

- Prisma migration ของ `workspace_members` + seeder สำหรับ user ที่มีอยู่
- Type `WorkspaceRole` + Type `WorkspaceAction` ใน `@monorepo/shared`
- `PERMISSION_MATRIX` constant + `canDo()` pure function ใน `@monorepo/shared`
- `PermissionGuard` + decorator `@RequirePermission()` ใน api-gateway
- Field `role` เพิ่มใน `JwtPayload` และฝังอยู่ใน `issueTokens()`
- Field `replied_by` บน Message (non-nullable สำหรับ outbound, immutable หลังสร้าง)
- Admin protection service (`ensureAdminRemains`)
- First Admin seeding ใน flow `register()`
- Unit tests: ทุก 27 combinations ของ `canDo()`
- Integration tests: middleware บน 9 protected actions ทั้งหมด
- Integration tests: admin protection edge cases

### RBAC-02 Deliverables

- `role` เพิ่มใน `Invitation` model + `CreateInvitationDto`
- `acceptInvitation()` สร้าง `WorkspaceMember` พร้อม role จาก invitation
- Resend invitation API (`PATCH /invitations/:id/resend`)
- Cancel invitation API (`DELETE /invitations/:id`)
- Change role API (`PATCH /workspace-members/:userId/role`)
- Remove member API (`DELETE /workspace-members/:userId`) + session revocation
- Email delivery integration (SES/SMTP) พร้อม invitation template
- Members page UI อัพเดต: Role, Last Active, inline role change, Remove
- Invitations page UI อัพเดต: Role column, Resend + Cancel actions
- Invite form อัพเดต: role selector
- API tests: invitation lifecycle ครบ (invite → accept → expire → resend)
- Session revocation tests: removed member → 401

### RBAC-03 Deliverables

- `role` ใน `CurrentUser` type และ return จาก `getMeAction()`
- ลบ hardcoded `role: "admin"` ออกจาก dashboard layout
- `usePermission(action)` hook
- Server-side route guards สำหรับ 6 protected routes ทั้งหมด
- Sidebar navigation แบบกรองตาม role (3 role variants)
- Assign panel conditional rendering (SSR — ไม่มี DOM trace สำหรับ Agent)
- 403 error page integration (trigger จาก API 403 responses)
- Session expiry พร้อม return URL preservation
- Conversation assigned-to banner
- Unit tests: `usePermission` × ทุก roles × ทุก actions (27 combinations)
- E2E tests (Playwright): direct URL navigation ไปยังแต่ละ restricted route ต่อ role
- Visual regression: sidebar rendering ต่อ role
