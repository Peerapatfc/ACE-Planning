# ACE-1366 Frontend Implementation Plan

## Context
Backend (`feat/ace-1502-contact-context-api`) is fully implemented. Current branch `feat/ACE-1378-overview-identities-panel` contains all backend commits. All 5 contact-info components exist but use hardcoded mock data. Goal: wire them to the real `GET /v1/omnichat/contacts/:contactId/context` API without blocking the chat timeline.

---

## Step 1 — Add Types to `omnichat.ts`
**File:** `apps/workspace-admin/src/types/omnichat.ts`

Append these types:
```ts
export type ContactKeyEventType = 'assigned' | 'status_change' | 'tag_change';

export type ContactOverview = {
  id: string;
  display_name: string | null;
  avatar_url: string | null;
  last_seen_at: string;
  total_conversations: number;
  phone: string | null;
  email: string | null;
  address: string | null;
  language_preference: string | null;
  tags: string[];
};

export type ContactIdentity = {
  channel_type: string;
  channel_account_id: string;
  channel_account_name: string | null;
  external_user_id: string;
};

export type ContactKeyEvent = {
  type: ContactKeyEventType;
  description: string;
  actor_name: string | null;
  created_at: string;
};

export type RecentConversationItem = {
  id: string;
  status: string;
  last_message_preview: string | null;
  last_message_at: string | null;
  channel_type: string;
  channel_account_name: string | null;
};

export type ContactContext = {
  overview: ContactOverview;
  identities: ContactIdentity[];
  key_events: ContactKeyEvent[];
  recent_conversations: RecentConversationItem[];
  last_purchase_stub: null;
  customer_notes: [];
};

export type UpdateContactPayload = {
  display_name?: string;
  profile_metadata?: {
    phone?: string;
    email?: string;
    address?: string;
    language_preference?: string;
  };
};
```

---

## Step 2 — Create `contact.api.ts`
**File:** `apps/workspace-admin/src/app/(main)/dashboard/chats/_api/contact.api.ts`

Pattern: same as `conversations.api.ts` — `'use server'` + `httpClient`.

```ts
'use server';
import { httpClient } from '@/server/http.config';
import type { ContactContext, UpdateContactPayload } from '@/types/omnichat';

export async function getContactContext(contactId: string): Promise<ContactContext> {
  return httpClient.get<ContactContext>(`/v1/omnichat/contacts/${contactId}/context`);
}

export async function updateContactAction(contactId: string, payload: UpdateContactPayload): Promise<void> {
  await httpClient.patch(`/v1/omnichat/contacts/${contactId}`, payload);
}
```

---

## Step 3 — Update Chat Store
**File:** `apps/workspace-admin/src/app/(main)/dashboard/chats/_store/chat-store.ts`

### 3a. Add imports
```ts
import type { ContactContext } from '@/types/omnichat';
import { getContactContext } from '../_api/contact.api';
```

### 3b. Add to `ChatState` interface (after `nextCursor`)
```ts
contactContext: ContactContext | null;
isLoadingContactContext: boolean;
fetchContactContext: (contactId: string) => Promise<void>;
```

### 3c. Add initial state values
```ts
contactContext: null,
isLoadingContactContext: false,
```

### 3d. Add `fetchContactContext` action
```ts
fetchContactContext: async (contactId) => {
  set({ isLoadingContactContext: true });
  try {
    const ctx = await getContactContext(contactId);
    set({ contactContext: ctx });
  } catch {
    // silently ignore — panel stays in loading state
  } finally {
    set({ isLoadingContactContext: false });
  }
},
```

### 3e. Update `setActiveConversation`
```ts
setActiveConversation: (id) => {
  const conversation = get().conversations.find((c) => c.id === id);
  set({ activeConversationId: id, contactContext: null });
  get().markAsRead(id);
  get().fetchMessages(id);
  if (conversation?.contact.id) {
    void get().fetchContactContext(conversation.contact.id);  // non-blocking
  }
},
```

---

## Step 4 — Update `contact-info-panel.tsx`
**File:** `apps/workspace-admin/src/app/(main)/dashboard/chats/_components/contact-info/contact-info-panel.tsx`

- Read `contactContext` + `isLoadingContactContext` from store
- Pass both as props into `ContactTabContent` and down to all child sections

Key prop changes:
- `IdentitiesSection` receives `identities` + `isLoading`
- `KeyEventsSection` receives `keyEvents` + `isLoading`
- `RecentConversationsSection` receives `recentConversations`, `totalConversations`, `isLoading`
- `ContactHeaderSection` already receives `conversation`; add `overview` + `isLoading` props

---

## Step 5 — Update `contact-header-section.tsx` (ACE-1378)
**File:** `apps/workspace-admin/src/app/(main)/dashboard/chats/_components/contact-info/contact-header-section.tsx`

Replace:
- `MOCK_CONTACT_STATS.conversationCount` → `overview?.total_conversations`
- `MOCK_CONTACT_STATS.lastSeen` → formatted `overview?.last_seen_at`
- `MOCK_CONTACT_INFO.phone/email` → `overview?.phone`, `overview?.email`
- `MOCK_CONNECTED_CHANNELS` → derive unique `channel_type` values from `identities[]`
- `contact.tags` → `overview?.tags` (already available from context, fallback to `contact.tags`)
- Remove all 3 `MOCK_*` constants
- Add skeleton rows while `isLoading` (use `<Skeleton>` from shadcn/ui)
- Null fallback: show `—` for phone/email when null

---

## Step 6 — Update `identities-section.tsx` (ACE-1378)
**File:** `apps/workspace-admin/src/app/(main)/dashboard/chats/_components/contact-info/identities-section.tsx`

- Replace `MOCK_IDENTITIES` with `identities[]` prop
- Map `channel_type` (string) → `ChannelType` for `CHANNEL_ICONS` / `CHANNEL_COLORS`
- `external_user_id` already masked from API — use directly
- `channel_account_name` as label (fallback to `channel_type`)
- Remove `method` badge (not in API) and `LinkMethod` type
- Add skeleton rows while loading
- Add empty state: "No linked identities"

---

## Step 7 — Update `key-events-section.tsx` (ACE-1477)
**File:** `apps/workspace-admin/src/app/(main)/dashboard/chats/_components/contact-info/key-events-section.tsx`

- Replace `MOCK_KEY_EVENTS` with `keyEvents[]` prop
- Update `KEY_EVENT_DOT` map: `assigned` → orange, `status_change` → gray, `tag_change` → blue
- Use `event.description` as text, `event.created_at` as date (format: `MMM D · h:mm A`)
- Remove `message`, `sla`, `note` dot entries (not in API)
- Add skeleton while loading
- Add empty state: "No events yet"

---

## Step 8 — Update `recent-conversations-section.tsx` (ACE-1478)
**File:** `apps/workspace-admin/src/app/(main)/dashboard/chats/_components/contact-info/recent-conversations-section.tsx`

- Replace `MOCK_RECENT_CONVERSATIONS` with `recentConversations[]` prop
- Title: `last_message_preview` or fallback `#${id.slice(0, 8)}`
- Date: formatted `last_message_at`
- "New" badge: when `status === 'open'`
- Replace `MOCK_TOTAL_CONVERSATIONS` with `overview.total_conversations` passed from panel
- On click: call `setActiveConversation(conv.id)` from store
- Add skeleton while loading
- Add empty state: "No previous conversations"

---

## Step 9 — Create `edit-contact-dialog.tsx` (ACE-1479)
**File:** `apps/workspace-admin/src/app/(main)/dashboard/chats/_components/contact-info/edit-contact-dialog.tsx`

- Shadcn `Dialog` triggered by the existing pencil button in `contact-header-section.tsx`
- Form fields: Display name (required), Phone, Email, Address, Language preference (all optional)
- On save: call `updateContactAction`, then `fetchContactContext` to refresh panel
- Use `useState` for form state, simple validation (display name not empty)

---

## Files Summary

| File | Action |
|---|---|
| `src/types/omnichat.ts` | Modify — add 7 new types |
| `chats/_api/contact.api.ts` | Create |
| `chats/_store/chat-store.ts` | Modify — add contactContext state + action |
| `contact-info/contact-info-panel.tsx` | Modify — read store, pass props |
| `contact-info/contact-header-section.tsx` | Modify — replace mocks |
| `contact-info/identities-section.tsx` | Modify — replace mocks |
| `contact-info/key-events-section.tsx` | Modify — replace mocks |
| `contact-info/recent-conversations-section.tsx` | Modify — replace mocks |
| `contact-info/edit-contact-dialog.tsx` | Create |

**Do NOT touch:** `conversation-notes-tab-content.tsx` (ACE-1504 in progress)

---

## Verification
1. Open a conversation → contact panel loads with skeleton → real data appears
2. Switch conversations → panel resets to skeleton → new data loads
3. Header shows real name, phone/email (or `—`), total conversations, last seen
4. Identities shows real channels with masked IDs; empty state if none
5. Key events shows last 5 real events; empty state if none
6. Recent conversations shows last 5; clicking navigates to that conversation
7. Pencil icon opens edit dialog; save updates panel without page reload
8. No data from contact A shows in contact B after switching
