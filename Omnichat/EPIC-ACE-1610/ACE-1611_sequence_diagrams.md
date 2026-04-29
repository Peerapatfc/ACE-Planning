# ACE-1611: RBAC-01 — Sequence Diagrams

Source: story `ACE-1611` + actual code in `apps/api-gateway` & `apps/user-service`.

---

## 1. Normal Protected Request (Permission Granted)

Flow for any authenticated user calling an endpoint that requires a permission they hold (e.g. Admin calling `manage_members`).

```mermaid
sequenceDiagram
    participant Client
    participant ApiGateway as API Gateway
    participant ThrottlerGuard
    participant JwtAuthGuard
    participant PermissionGuard
    participant PermissionMatrixSvc as PermissionMatrixService
    participant UserServiceTCP as user-service (TCP)
    participant Handler as Route Handler

    Client->>ApiGateway: HTTP Request + Bearer <token>

    ApiGateway->>ThrottlerGuard: canActivate()
    ThrottlerGuard-->>ApiGateway: true (rate limit OK)

    ApiGateway->>JwtAuthGuard: canActivate()
    JwtAuthGuard->>JwtAuthGuard: verify JWT signature + expiry
    JwtAuthGuard->>JwtAuthGuard: check Redis blocklist (isBlocked?)
    JwtAuthGuard-->>ApiGateway: req.user = { userId, tenantId, email }

    ApiGateway->>PermissionGuard: canActivate()
    PermissionGuard->>PermissionGuard: read @RequirePermission metadata → action
    PermissionGuard->>PermissionMatrixSvc: resolveRole(userId, tenantId)
    PermissionMatrixSvc->>UserServiceTCP: send({ cmd: 'get_workspace_member_role' }, { user_id, tenant_id })
    UserServiceTCP-->>PermissionMatrixSvc: role = 'admin'
    PermissionMatrixSvc-->>PermissionGuard: 'admin'

    PermissionGuard->>PermissionMatrixSvc: canDo('admin', 'manage_members')
    Note over PermissionMatrixSvc: Check in-memory matrix Map<action, Set<role>>
    PermissionMatrixSvc-->>PermissionGuard: true

    PermissionGuard-->>ApiGateway: true (pass)
    ApiGateway->>Handler: execute handler
    Handler-->>Client: 200 OK + response body
```

---

## 2. Permission Denied (403)

Agent calls `POST /conversations/:id/assign` which requires `assign_conversation` — Agent does not have it.

```mermaid
sequenceDiagram
    participant Client as Client (Agent)
    participant ApiGateway as API Gateway
    participant JwtAuthGuard
    participant PermissionGuard
    participant PermissionMatrixSvc as PermissionMatrixService
    participant UserServiceTCP as user-service (TCP)

    Client->>ApiGateway: POST /conversations/:id/assign + Bearer <token>

    ApiGateway->>JwtAuthGuard: canActivate()
    JwtAuthGuard-->>ApiGateway: req.user = { userId, tenantId }

    ApiGateway->>PermissionGuard: canActivate()
    PermissionGuard->>PermissionMatrixSvc: resolveRole(userId, tenantId)
    PermissionMatrixSvc->>UserServiceTCP: { cmd: 'get_workspace_member_role' }
    UserServiceTCP-->>PermissionMatrixSvc: role = 'agent'

    PermissionGuard->>PermissionMatrixSvc: canDo('agent', 'assign_conversation')
    PermissionMatrixSvc-->>PermissionGuard: false

    PermissionGuard->>PermissionGuard: getAllowedRoles('assign_conversation') → ['admin','supervisor']
    PermissionGuard-->>Client: 403 { error: "permission_denied", action: "assign_conversation", required_role: "admin | supervisor" }

    Note over Client,PermissionGuard: Handler is NEVER executed
```

---

## 3. Unauthenticated Request (401)

Request arrives without a valid JWT — rejected before permission check.

```mermaid
sequenceDiagram
    participant Client
    participant ApiGateway as API Gateway
    participant JwtAuthGuard
    participant PermissionGuard

    Client->>ApiGateway: HTTP Request (no token / expired token)
    ApiGateway->>JwtAuthGuard: canActivate()
    JwtAuthGuard->>JwtAuthGuard: JWT verify fails (missing / expired / invalid)
    JwtAuthGuard-->>Client: 401 Unauthorized

    Note over PermissionGuard: Never reached
```

---

## 4. Non-Member Authenticated User (403, not 404)

User has valid JWT but has no `WorkspaceMember` record for the requested workspace.

```mermaid
sequenceDiagram
    participant Client as Client (valid token, wrong workspace)
    participant ApiGateway as API Gateway
    participant JwtAuthGuard
    participant PermissionGuard
    participant PermissionMatrixSvc as PermissionMatrixService
    participant UserServiceTCP as user-service (TCP)

    Client->>ApiGateway: GET /members + Bearer <token>
    ApiGateway->>JwtAuthGuard: canActivate()
    JwtAuthGuard-->>ApiGateway: req.user = { userId, tenantId }

    ApiGateway->>PermissionGuard: canActivate()
    PermissionGuard->>PermissionMatrixSvc: resolveRole(userId, tenantId)
    PermissionMatrixSvc->>UserServiceTCP: { cmd: 'get_workspace_member_role' }

    Note over UserServiceTCP: No WorkspaceMember row found (or status='removed')
    UserServiceTCP-->>PermissionMatrixSvc: null

    PermissionGuard->>PermissionGuard: role is null → deny
    PermissionGuard-->>Client: 403 Forbidden { error: "permission_denied" }

    Note over Client,PermissionGuard: Workspace existence NOT revealed (no 404)
```

---

## 5. Permission Matrix Load at Startup

`PermissionMatrixService` loads the full permission matrix from user-service on module init, and caches it in memory.

```mermaid
sequenceDiagram
    participant NestApp as NestJS App (startup)
    participant PermissionMatrixSvc as PermissionMatrixService
    participant UserServiceTCP as user-service (TCP)
    participant InMemory as In-Memory Map<action, Set<role>>

    NestApp->>PermissionMatrixSvc: onModuleInit()
    PermissionMatrixSvc->>UserServiceTCP: send({ cmd: 'get_all_role_permissions' }, {})
    UserServiceTCP->>UserServiceTCP: SELECT from role_permissions JOIN permissions
    UserServiceTCP-->>PermissionMatrixSvc: Array<{ action, role, allowed }>

    loop For each row where allowed = true
        PermissionMatrixSvc->>InMemory: matrix.get(action).add(role)
    end

    PermissionMatrixSvc-->>NestApp: Matrix ready (11 actions × 3 roles)

    Note over NestApp,InMemory: canDo() reads InMemory only — no DB per request
```

---

## 6. Change Member Role (Admin Protection)

Admin A attempts to downgrade their own role when they are the last admin in the workspace.

```mermaid
sequenceDiagram
    participant Client as Client (Admin A)
    participant ApiGateway as API Gateway
    participant PermissionGuard
    participant MembersCtrl as MembersController
    participant MembersSvc as MembersService (API-GW)
    participant UserServiceTCP as user-service (TCP)
    participant UserSvcService as WorkspaceMembersService
    participant DB as PostgreSQL (user-service DB)

    Client->>ApiGateway: PATCH /members/:userId/role { role: "supervisor" }

    ApiGateway->>PermissionGuard: canActivate() — resolveRole → 'admin', canDo('admin','manage_members') → true
    PermissionGuard-->>ApiGateway: pass

    ApiGateway->>MembersCtrl: changeRole(tenantId, userId, 'supervisor')
    MembersCtrl->>MembersSvc: changeRole(tenantId, userId, 'supervisor')
    MembersSvc->>UserServiceTCP: send({ cmd: 'change_member_role' }, { tenant_id, user_id, role: 'supervisor' })

    UserServiceTCP->>UserSvcService: changeRole(tenant_id, user_id, 'supervisor')
    UserSvcService->>DB: BEGIN TRANSACTION

    UserSvcService->>DB: SELECT ... FROM workspace_members WHERE role='admin' FOR UPDATE
    Note over DB: Row-level lock prevents concurrent last-admin removal

    UserSvcService->>DB: COUNT active admins in workspace (excluding this user)
    DB-->>UserSvcService: adminCount = 0

    UserSvcService->>DB: ROLLBACK
    UserSvcService-->>UserServiceTCP: RpcException { statusCode: 409, message: "workspace_must_have_at_least_one_admin" }
    UserServiceTCP-->>MembersSvc: error
    MembersSvc-->>Client: 400 Bad Request { error: "workspace_must_have_at_least_one_admin" }
```

**Happy path** (2+ admins exist): `adminCount ≥ 1` → UPDATE role → COMMIT → 200 OK.

---

## 7. Remove Member (with Token Revocation)

Admin removes a member: soft-delete + Redis blocklist + refresh token revocation.

```mermaid
sequenceDiagram
    participant Client as Client (Admin)
    participant ApiGateway as API Gateway
    participant PermissionGuard
    participant MembersSvc as MembersService (API-GW)
    participant UserServiceTCP as user-service (TCP)
    participant UserSvcService as WorkspaceMembersService
    participant DB as PostgreSQL
    participant Redis as Redis (blocklist)

    Client->>ApiGateway: DELETE /members/:targetUserId

    ApiGateway->>PermissionGuard: canActivate() → pass (admin has manage_members)
    ApiGateway->>MembersSvc: removeMember(tenantId, targetUserId)

    MembersSvc->>UserServiceTCP: send({ cmd: 'remove_member' }, { tenant_id, user_id })
    UserServiceTCP->>UserSvcService: removeMember(tenant_id, user_id)

    UserSvcService->>DB: BEGIN TRANSACTION
    UserSvcService->>DB: SELECT admins FOR UPDATE (if target is admin)
    DB-->>UserSvcService: adminCount check
    UserSvcService->>DB: UPDATE workspace_members SET status='removed'
    DB-->>UserSvcService: updated member
    UserSvcService->>DB: COMMIT
    UserSvcService-->>MembersSvc: success

    MembersSvc->>Redis: SETEX blocklist:<userId> <ttl> 1
    Note over Redis: Immediately invalidates current session

    MembersSvc->>UserServiceTCP: send({ cmd: 'revoke_all_refresh_tokens' }, { user_id })
    Note over MembersSvc: Fire-and-forget — errors ignored

    MembersSvc-->>Client: 200 OK
```

---

## 8. Workspace-Scoped Permission Check

User is Admin in Workspace A but Agent in Workspace B — calls `manage_members` with Workspace B context.

```mermaid
sequenceDiagram
    participant Client as Client (Admin-A, Agent-B)
    participant ApiGateway as API Gateway
    participant JwtAuthGuard
    participant PermissionGuard
    participant PermissionMatrixSvc as PermissionMatrixService
    participant UserServiceTCP as user-service (TCP)

    Note over Client: JWT contains tenantId = workspaceB_id

    Client->>ApiGateway: GET /members + Bearer <token with tenantId=workspaceB>
    ApiGateway->>JwtAuthGuard: canActivate()
    JwtAuthGuard-->>ApiGateway: req.user = { userId, tenantId: "workspaceB" }

    ApiGateway->>PermissionGuard: canActivate()
    PermissionGuard->>PermissionMatrixSvc: resolveRole(userId, "workspaceB")
    PermissionMatrixSvc->>UserServiceTCP: { cmd: 'get_workspace_member_role', user_id, tenant_id: "workspaceB" }
    UserServiceTCP-->>PermissionMatrixSvc: role = 'agent'

    PermissionGuard->>PermissionMatrixSvc: canDo('agent', 'manage_members')
    PermissionMatrixSvc-->>PermissionGuard: false

    PermissionGuard-->>Client: 403 Forbidden
    Note over Client: Admin role in Workspace A has NO effect here
```
