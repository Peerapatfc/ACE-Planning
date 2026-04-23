# ACE-1617: Settings Shell — Implementation Plan

**Story:** ACE-1617 Settings Shell & Sidebar Navigation  
**Sprint:** Sprint 4 (4/13 – 4/26) | **Points:** 6  
**Depends on:** RBAC-01 (role field on CurrentUser), RBAC-03 (guard pattern)

---

## Context

Currently `/settings/*` routes re-export the main dashboard layout — no dedicated shell exists. This plan builds the Settings-specific layout shell: role-filtered sidebar, server-side route guards, breadcrumb, and placeholder content pages per section.

**Architecture:** Next.js App Router server components handle all role checks before render, eliminating flash-of-unauthorized-content entirely.

---

## Role Access Matrix

| Section | Admin | Supervisor | Agent |
|---------|-------|-----------|-------|
| Business Information | ✅ | ❌ | ❌ |
| Members & Roles | ✅ | ❌ | ❌ |
| Channels | ✅ | ❌ | ❌ |
| SLA Rules | ✅ | ✅ | ❌ |
| Notification Rules | ✅ | ✅ | ❌ |
| My Preferences | ✅ | ✅ | ✅ |

---

## File Map

### Files to Create

```
src/app/(main)/settings/
├── layout.tsx                              REPLACE current re-export
├── page.tsx                                NEW — auto-redirect to first accessible section
├── _config/
│   └── settings-nav.ts                    NEW — nav config + role access matrix
├── _lib/
│   └── settings-access.ts                 NEW — requireSettingsAccess() server utility
├── _components/
│   ├── settings-sidebar.tsx               NEW — client component, role-filtered nav
│   └── settings-breadcrumb.tsx            NEW — wraps existing breadcrumb UI component
├── business-information/page.tsx          NEW — placeholder (Admin)
├── channels/page.tsx                      NEW — placeholder (Admin)
├── sla-rules/page.tsx                     NEW — placeholder (Admin + Supervisor)
├── notification-rules/page.tsx            NEW — placeholder (Admin + Supervisor)
└── my-preferences/page.tsx               NEW — placeholder (all roles)

src/app/(main)/
└── 403/page.tsx                           NEW — unauthorized access page
```

### Files to Modify

| File | Change |
|------|--------|
| `src/app/(main)/settings/members/page.tsx` | Add server-side Admin-only guard |
| `src/server/auth.ts` | Add `role` to `CurrentUser` interface (if RBAC-01 hasn't) |
| `src/app/(main)/dashboard/layout.tsx:32` | Replace hardcoded `role: "admin"` with `me?.role` |

### Existing Code to Reuse

| Resource | Path |
|----------|------|
| Breadcrumb component | `src/components/ui/breadcrumb.tsx` |
| `getMeAction()` | `src/server/auth.ts` |
| `cn()` utility | `src/lib/utils.ts` |
| `redirect()` | `next/navigation` |

---

## Implementation Phases

### Phase 1 — Nav Config & Access Utility

**`src/app/(main)/settings/_config/settings-nav.ts`**

```ts
import type { LucideIcon } from "lucide-react";
import { Bell, Building2, Sliders, Timer, Users2, Wifi } from "lucide-react";

export type SettingsRole = "admin" | "supervisor" | "agent";

export interface SettingsNavItem {
  key: string;
  label: string;
  url: string;
  icon: LucideIcon;
  allowedRoles: SettingsRole[];
}

export const SETTINGS_NAV: SettingsNavItem[] = [
  {
    key: "business-information",
    label: "Business Information",
    url: "/settings/business-information",
    icon: Building2,
    allowedRoles: ["admin"],
  },
  {
    key: "members",
    label: "Members & Roles",
    url: "/settings/members",
    icon: Users2,
    allowedRoles: ["admin"],
  },
  {
    key: "channels",
    label: "Channels",
    url: "/settings/channels",
    icon: Wifi,
    allowedRoles: ["admin"],
  },
  {
    key: "sla-rules",
    label: "SLA Rules",
    url: "/settings/sla-rules",
    icon: Timer,
    allowedRoles: ["admin", "supervisor"],
  },
  {
    key: "notification-rules",
    label: "Notification Rules",
    url: "/settings/notification-rules",
    icon: Bell,
    allowedRoles: ["admin", "supervisor"],
  },
  {
    key: "my-preferences",
    label: "My Preferences",
    url: "/settings/my-preferences",
    icon: Sliders,
    allowedRoles: ["admin", "supervisor", "agent"],
  },
];

export function getAccessibleSections(role: SettingsRole): SettingsNavItem[] {
  return SETTINGS_NAV.filter((item) => item.allowedRoles.includes(role));
}

export function canAccessSection(role: SettingsRole, key: string): boolean {
  const item = SETTINGS_NAV.find((n) => n.key === key);
  return item ? item.allowedRoles.includes(role) : false;
}
```

**`src/app/(main)/settings/_lib/settings-access.ts`**

```ts
import { redirect } from "next/navigation";
import type { SettingsRole } from "../_config/settings-nav";
import { canAccessSection, getAccessibleSections } from "../_config/settings-nav";

export function requireSettingsAccess(role: SettingsRole, sectionKey: string): void {
  if (!canAccessSection(role, sectionKey)) {
    redirect("/403");
  }
}

export function getFirstAccessibleUrl(role: SettingsRole): string {
  const sections = getAccessibleSections(role);
  if (sections.length === 0) redirect("/403");
  return sections[0].url;
}
```

---

### Phase 2 — Settings Shell Layout

**`src/app/(main)/settings/layout.tsx`** (replaces current 1-line re-export)

```tsx
import type { ReactNode } from "react";
import { getMeAction } from "@/server/auth";
import type { SettingsRole } from "./_config/settings-nav";
import { getAccessibleSections } from "./_config/settings-nav";
import { SettingsSidebar } from "./_components/settings-sidebar";

export default async function SettingsLayout({ children }: { children: ReactNode }) {
  const me = await getMeAction();
  const role = (me?.role ?? "agent") as SettingsRole;
  const navItems = getAccessibleSections(role);

  return (
    <div className="flex h-full">
      <SettingsSidebar items={navItems} />
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
}
```

> Note: This layout nests inside `(main)/layout` which already provides the top nav bar and auth session check. No need to re-wrap `SidebarProvider`.

---

### Phase 3 — Settings Sidebar Component

**`src/app/(main)/settings/_components/settings-sidebar.tsx`**

Client component. Receives already-filtered items from server layout — zero role logic here, satisfying the "not in DOM" requirement.

```tsx
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import type { SettingsNavItem } from "../_config/settings-nav";

export function SettingsSidebar({ items }: { items: SettingsNavItem[] }) {
  const pathname = usePathname();

  return (
    <aside className="w-56 shrink-0 border-r h-full py-4">
      <div className="px-3 mb-3">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-2">
          Settings
        </p>
      </div>
      <nav className="space-y-0.5 px-3">
        {items.map((item) => {
          const active = pathname.startsWith(item.url);
          return (
            <Link
              key={item.key}
              href={item.url}
              className={cn(
                "flex items-center gap-2.5 rounded-md px-3 py-2 text-sm transition-colors",
                "hover:bg-accent hover:text-accent-foreground",
                active
                  ? "border-l-2 border-primary bg-accent/60 font-medium text-foreground"
                  : "text-muted-foreground border-l-2 border-transparent",
              )}
            >
              <item.icon className="size-4 shrink-0" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
```

---

### Phase 4 — Breadcrumb Component

**`src/app/(main)/settings/_components/settings-breadcrumb.tsx`**

Wraps existing `src/components/ui/breadcrumb.tsx` — no new UI code.

```tsx
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";

export function SettingsBreadcrumb({ section }: { section: string }) {
  return (
    <Breadcrumb>
      <BreadcrumbList>
        <BreadcrumbItem>
          <span className="text-muted-foreground text-sm">Settings</span>
        </BreadcrumbItem>
        <BreadcrumbSeparator />
        <BreadcrumbItem>
          <BreadcrumbPage>{section}</BreadcrumbPage>
        </BreadcrumbItem>
      </BreadcrumbList>
    </Breadcrumb>
  );
}
```

Each section page imports and renders `<SettingsBreadcrumb section="[Section Name]" />` at top.

---

### Phase 5 — Auto-Redirect Index Page

**`src/app/(main)/settings/page.tsx`**

Server component. No render — pure server-side redirect to first accessible section.

```tsx
import { redirect } from "next/navigation";
import { getMeAction } from "@/server/auth";
import type { SettingsRole } from "./_config/settings-nav";
import { getFirstAccessibleUrl } from "./_lib/settings-access";

export default async function SettingsIndexPage() {
  const me = await getMeAction();
  const role = (me?.role ?? "agent") as SettingsRole;
  redirect(getFirstAccessibleUrl(role));
}
```

---

### Phase 6 — Section Pages with Route Guards

Each section page runs `requireSettingsAccess()` server-side before any render. This is the RBAC-03 guard pattern applied to App Router.

**Pattern template:**

```tsx
import { getMeAction } from "@/server/auth";
import type { SettingsRole } from "../_config/settings-nav";
import { requireSettingsAccess } from "../_lib/settings-access";
import { SettingsBreadcrumb } from "../_components/settings-breadcrumb";

export default async function BusinessInformationPage() {
  const me = await getMeAction();
  const role = (me?.role ?? "agent") as SettingsRole;
  requireSettingsAccess(role, "business-information");  // redirects to /403 if denied

  return (
    <div className="p-6 space-y-4">
      <SettingsBreadcrumb section="Business Information" />
      <div className="rounded-lg border border-dashed p-12 text-center text-muted-foreground text-sm">
        Business Information — content coming in SET-02
      </div>
    </div>
  );
}
```

Apply this pattern to all 6 sections:

| Section key | Section label | Page path |
|-------------|--------------|-----------|
| `business-information` | Business Information | `business-information/page.tsx` |
| `members` | Members & Roles | `members/page.tsx` (modify existing) |
| `channels` | Channels | `channels/page.tsx` |
| `sla-rules` | SLA Rules | `sla-rules/page.tsx` |
| `notification-rules` | Notification Rules | `notification-rules/page.tsx` |
| `my-preferences` | My Preferences | `my-preferences/page.tsx` |

---

### Phase 7 — 403 Forbidden Page

**`src/app/(main)/403/page.tsx`**

```tsx
import Link from "next/link";

export default function ForbiddenPage() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-3">
      <p className="text-5xl font-bold text-foreground">403</p>
      <p className="text-muted-foreground">You don't have access to this section.</p>
      <Link href="/settings" className="text-sm text-primary underline-offset-4 hover:underline">
        Go to Settings
      </Link>
    </div>
  );
}
```

---

### Phase 8 — CurrentUser Role Field (if RBAC-01 pending)

**`src/server/auth.ts`** — add `role` field:

```ts
export interface CurrentUser {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  avatar_url: string | null;
  role: "admin" | "supervisor" | "agent";  // ← add this
}
```

**`src/app/(main)/dashboard/layout.tsx` line 32** — use dynamic role:

```ts
// Before
role: "admin",

// After
role: me?.role ?? "agent",
```

---

## Implementation Order

```
Phase 1 (config + access util)
    └─► Phase 2 (shell layout)
            └─► Phase 3 (sidebar component)
            └─► Phase 4 (breadcrumb component)
            └─► Phase 5 (index redirect)
            └─► Phase 6 (section pages with guards)
Phase 7 (403 page)          ← independent, do first
Phase 8 (role field)        ← do first if RBAC-01 not yet merged
```

Recommended order: **8 → 7 → 1 → 2 → 3 → 4 → 5 → 6**

---

## Security Requirements (Critical)

| Requirement | Implementation |
|-------------|----------------|
| Hidden sections not in DOM | Server component filters `navItems` before passing to client — client renders only what it receives |
| No flash of unauthorized content | `requireSettingsAccess()` calls `redirect()` server-side; Next.js never sends page HTML to client |
| No redirect loops | `getFirstAccessibleUrl()` redirects to `/403` if zero accessible sections (not back to `/settings`) |
| Role change mid-session | Server components re-fetch `getMeAction()` on each navigation; sidebar re-filters on next request |

---

## QA / Verification

### Manual Test Matrix

| Scenario | Steps | Expected |
|---------|-------|---------|
| Admin sees all sections | Login as admin → `/settings` | Auto-selects Business Information; all 6 sections in sidebar |
| Supervisor filtered nav | Login as supervisor → `/settings` | Only SLA Rules, Notification Rules, My Preferences in sidebar |
| Agent single section | Login as agent → `/settings` | Redirects immediately to My Preferences; only that item in sidebar |
| Admin navigate sections | Click each sidebar item | Content area updates; breadcrumb shows correct section; no reload |
| Agent blocked URL | Agent types `/settings/business-information` | Redirects to `/403`; no content visible |
| Active highlight | Navigate to any section | Left-border highlight on active item |
| Breadcrumb | On any section page | Shows `Settings > [Section Name]` |

### DOM Check

Open DevTools on Supervisor session → inspect sidebar HTML → confirm `business-information`, `members`, `channels` links **do not exist** in DOM.

### Test Types (as spec requires)

- **Unit:** `getAccessibleSections()` and `canAccessSection()` per role — pure functions, easy to test
- **E2E (Playwright):** Direct URL guard for each restricted section per role
- **Visual regression:** Sidebar active state per section; breadcrumb rendering

---

## Out of Scope

- Section content (SET-02, SET-03, SLA-01, NOTIF-04, NOTIF-05)
- Mobile sidebar (desktop side-by-side only per spec)
- Unsaved-changes warning (wire up later when section forms exist)
- Settings entry point in top-level navigation (assumed to exist or covered by another story)
