# ACE-1617: Settings Shell — Implementation Plan

**Story:** [ACE-1617-SET-01-Settings-Shell.md](ACE-1617-SET-01-Settings-Shell.md)  
**Repo:** `apps/workspace-admin` (Next.js 16, App Router)

---

## Architecture Overview

Settings area currently reuses the dashboard AppShell via `settings/layout.tsx` re-export. This plan adds a **settings-specific sub-sidebar** nested inside the existing AppShell content area, with permission-filtered navigation, breadcrumb, auto-redirect, and per-section route guards.

```
AppShell (SidebarProvider + AppSidebar + SidebarInset)   ← settings/layout.tsx (modified)
└── flex h-full overflow-hidden
    ├── SettingsSidebar (w-56, border-r)                 ← client, filtered by permissions
    └── div flex-1 overflow-auto p-4 md:p-6
        ├── SettingsBreadcrumb                           ← client, usePathname()
        └── {children}                                   ← section page content
```

---

## Permission Matrix

| Section | Route | Permission | Admin | Supervisor | Agent |
|---|---|---|---|---|---|
| Business Information | `/settings/business-information` | `MANAGE_WORKSPACE` | ✅ | ❌ | ❌ |
| Members & Roles | `/settings/members` | `MANAGE_MEMBERS` | ✅ | ❌ | ❌ |
| Channels | `/settings/channels` | `MANAGE_CHANNELS` | ✅ | ❌ | ❌ |
| SLA Rules | `/settings/sla` | `CONFIG_SLA` | ✅ | ✅ | ❌ |
| Notification Rules | `/settings/notification-rules` | `CONFIG_NOTIFICATION` | ✅ | ✅ | ❌ |
| My Preferences | `/settings/my-preferences` | _(none)_ | ✅ | ✅ | ✅ |

All permissions exist in `src/lib/permissions.ts`. Route guard pattern exists in `settings/members/layout.tsx` and `settings/sla/layout.tsx`.

---

## Files to Modify

### `src/app/(main)/settings/layout.tsx`

**Current:** `export { default } from "@/app/(main)/dashboard/layout"`

**Change to:** Standalone layout (copy of `dashboard/layout.tsx`) with modified content area:

```tsx
// Replace this in dashboard layout copy:
// <div className="h-full p-4 md:p-6">{children}</div>

// With:
<div className="flex h-full overflow-hidden">
  <SettingsSidebar permissions={permissions} />
  <div className="flex-1 overflow-auto p-4 md:p-6">
    <SettingsBreadcrumb />
    {children}
  </div>
</div>
```

---

## Files to Create

### 1. `src/app/(main)/settings/_config/settings-nav.ts`

Navigation items config — single source of truth for sidebar + auto-redirect logic.

```ts
import type { LucideIcon } from 'lucide-react';
import { Bell, Building2, PlugZap, Timer, User, UsersRound } from 'lucide-react';
import { Permission } from '@/lib/permissions';

export interface SettingsNavItem {
  title: string;
  url: string;
  icon: LucideIcon;
  permissions: Permission[];
}

export const SETTINGS_NAV_ITEMS: SettingsNavItem[] = [
  { title: 'Business Information', url: '/settings/business-information', icon: Building2,  permissions: [Permission.MANAGE_WORKSPACE]   },
  { title: 'Members & Roles',      url: '/settings/members',              icon: UsersRound, permissions: [Permission.MANAGE_MEMBERS]     },
  { title: 'Channels',             url: '/settings/channels',             icon: PlugZap,    permissions: [Permission.MANAGE_CHANNELS]    },
  { title: 'SLA Rules',            url: '/settings/sla',                  icon: Timer,      permissions: [Permission.CONFIG_SLA]         },
  { title: 'Notification Rules',   url: '/settings/notification-rules',   icon: Bell,       permissions: [Permission.CONFIG_NOTIFICATION] },
  { title: 'My Preferences',       url: '/settings/my-preferences',       icon: User,       permissions: []                              },
];
```

---

### 2. `src/app/(main)/settings/_components/settings-sidebar.tsx`

**Subtask ACE-1626 — Show menu by permission**

```tsx
'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

import { cn } from '@/lib/utils';
import type { Permission } from '@/lib/permissions';
import { SETTINGS_NAV_ITEMS } from '../_config/settings-nav';

export function SettingsSidebar({ permissions }: { permissions: Permission[] }) {
  const pathname = usePathname();

  const visibleItems = SETTINGS_NAV_ITEMS.filter(
    (item) => !item.permissions.length || item.permissions.some((p) => permissions.includes(p)),
  );

  return (
    <aside className="w-56 shrink-0 border-r overflow-y-auto">
      <nav className="p-2 pt-4">
        <p className="px-3 pb-2 text-xs font-medium text-muted-foreground uppercase tracking-wider">
          Settings
        </p>
        {visibleItems.map((item) => {
          const isActive = pathname === item.url;
          return (
            <Link
              key={item.url}
              href={item.url}
              className={cn(
                'flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-colors',
                isActive
                  ? 'border-l-2 border-primary bg-accent text-accent-foreground font-medium pl-[10px]'
                  : 'text-muted-foreground hover:text-foreground hover:bg-accent/50',
              )}
            >
              <item.icon className="size-4 shrink-0" />
              {item.title}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
```

**Key:** `visibleItems` = filtered list → hidden items never rendered to DOM.

---

### 3. `src/app/(main)/settings/_components/settings-breadcrumb.tsx`

**Subtask ACE-1679 — Create breadcrumb component**

Uses existing shadcn `Breadcrumb` component (`src/components/ui/breadcrumb.tsx`).

```tsx
'use client';

import { usePathname } from 'next/navigation';

import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb';
import { SETTINGS_NAV_ITEMS } from '../_config/settings-nav';

export function SettingsBreadcrumb() {
  const pathname = usePathname();
  const currentSection = SETTINGS_NAV_ITEMS.find((item) => item.url === pathname);

  if (!currentSection) return null;

  return (
    <Breadcrumb className="mb-4">
      <BreadcrumbList>
        <BreadcrumbItem>
          <BreadcrumbLink href="/settings">Settings</BreadcrumbLink>
        </BreadcrumbItem>
        <BreadcrumbSeparator />
        <BreadcrumbItem>
          <BreadcrumbPage>{currentSection.title}</BreadcrumbPage>
        </BreadcrumbItem>
      </BreadcrumbList>
    </Breadcrumb>
  );
}
```

---

### 4. `src/app/(main)/settings/page.tsx`

Auto-redirect to first accessible section. No content rendered — pure server-side redirect.

```tsx
import { redirect } from 'next/navigation';

import { getMyPermissionsAction } from '@/server/permissions';
import { SETTINGS_NAV_ITEMS } from './_config/settings-nav';

export default async function SettingsPage() {
  const permissions = await getMyPermissionsAction();
  const first = SETTINGS_NAV_ITEMS.find(
    (item) => !item.permissions.length || item.permissions.some((p) => permissions.includes(p)),
  );
  redirect(first?.url ?? '/unauthorized');
}
```

---

### 5. New Section Layouts (Route Guards)

Pattern from `settings/members/layout.tsx` — redirect to `/unauthorized` before render.

**`settings/business-information/layout.tsx`**
```tsx
import type { ReactNode } from 'react';
import { redirect } from 'next/navigation';
import { Permission } from '@/lib/permissions';
import { checkPermission } from '@/server/permissions';

export default async function BusinessInformationLayout({ children }: { children: ReactNode }) {
  const allowed = await checkPermission({ some: [Permission.MANAGE_WORKSPACE] });
  if (!allowed) redirect('/unauthorized');
  return <>{children}</>;
}
```

**`settings/channels/layout.tsx`** → `Permission.MANAGE_CHANNELS`

**`settings/notification-rules/layout.tsx`** → `Permission.CONFIG_NOTIFICATION`

**`settings/my-preferences/`** → no layout guard (all roles)

---

### 6. Placeholder Pages

Each section page that doesn't have content yet renders a minimal placeholder.

```tsx
// Example: settings/business-information/page.tsx
import type { Metadata } from 'next';

export const metadata: Metadata = { title: 'Business Information' };

export default function BusinessInformationPage() {
  return (
    <div className="flex flex-col gap-2">
      <h1 className="text-xl font-semibold">Business Information</h1>
      <p className="text-sm text-muted-foreground">Coming soon.</p>
    </div>
  );
}
```

Apply same pattern to: `channels/page.tsx`, `notification-rules/page.tsx`, `my-preferences/page.tsx`.

---

## Files Unchanged

| File | Reason |
|---|---|
| `settings/members/layout.tsx` | Already has `MANAGE_MEMBERS` guard → `/unauthorized` |
| `settings/members/page.tsx` | Full content — keep as-is |
| `settings/sla/layout.tsx` | Already has `CONFIG_SLA` guard → `/unauthorized` |
| `settings/sla/page.tsx` | ComingSoon placeholder — keep as-is |
| `src/lib/permissions.ts` | All needed permissions exist |
| `src/navigation/sidebar/sidebar-items.ts` | Keep existing Settings group items |

---

## Build Sequence

```
1. _config/settings-nav.ts              (no deps)
2. _components/settings-sidebar.tsx     (depends on config)
3. _components/settings-breadcrumb.tsx  (depends on config + shadcn Breadcrumb)
4. settings/layout.tsx                  (depends on sidebar + breadcrumb)
5. settings/page.tsx                    (depends on config)
6. business-information/layout.tsx + page.tsx
7. channels/layout.tsx + page.tsx
8. notification-rules/layout.tsx + page.tsx
9. my-preferences/page.tsx
```

---

## Verification Checklist

| Scenario | Expected |
|---|---|
| Admin → `/settings` | Redirect → `/settings/business-information`, all 6 items in sidebar |
| Supervisor → `/settings` | Redirect → `/settings/sla`, SLA + Notification Rules + My Preferences (3 items) |
| Agent → `/settings` | Redirect → `/settings/my-preferences`, 1 item only |
| Agent → `/settings/business-information` (direct URL) | Redirect → `/unauthorized`, no content flash |
| Click between sections | Content updates, sidebar highlight updates, no full reload |
| DOM inspection as Supervisor | `Members & Roles`, `Business Information`, `Channels` nodes absent from DOM entirely |
| Breadcrumb | Shows `Settings / [Section Name]` for all sections |
| Active sidebar item | Left border primary + accent bg on current section |
