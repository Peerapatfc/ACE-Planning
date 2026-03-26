# ACE-1366 — Implementation Plan
**Story:** STORY-CTX-01: Contact Profile (Profile Panel + Key Events + History)
**Last updated:** 2026-03-26

---

## Subtask Mapping

| ClickUp | Name | Status |
|---|---|---|
| ACE-1502 | API: GET /contact-context | to do |
| ACE-1378 | Overview & Identities Panel | to do |
| ACE-1477 | Activity Tab (Key event) | to do |
| ACE-1478 | Conversations list | to do |
| ACE-1479 | Edit name, email, tel, address | to do |
| ACE-1504 | Internal Notes (Mock Up) | **in progress — skip** |

---

## [ACE-1502] Backend: GET /contact-context

### New module: `apps/omnichat-service/src/contacts/`

**Files to create:**
- `contacts.module.ts`
- `contacts.service.ts`
- `contacts.controller.ts`

**Endpoint:** `GET /v1/omnichat/contacts/:contactId/context`

Tenant ID extracted from JWT (same pattern as other services in the app).

**Response shape:**
```typescript
{
  overview: {
    id: string,
    display_name: string | null,
    avatar_url: string | null,
    last_seen_at: string,
    total_conversations: number,
    phone: string | null,              // from profile_metadata.phone
    email: string | null,              // from profile_metadata.email
    address: string | null,            // from profile_metadata.address
    language_preference: string | null,
    tags: string[],                    // distinct from ConversationTag
  },
  identities: Array<{
    channel_type: string,
    channel_account_id: string,
    channel_account_name: string | null,
    external_user_id: string,          // masked: "Xxxx•••xxxx"
  }>,
  key_events: Array<{
    type: 'assigned' | 'status_change' | 'tag_change',
    description: string,               // human-readable, built in service
    actor_name: string | null,
    created_at: string,
  }>,                                  // last 5, sorted DESC
  recent_conversations: Array<{
    id: string,
    status: string,
    last_message_preview: string | null,
    last_message_at: string | null,
    channel_type: string,
    channel_account_name: string | null,
  }>,                                  // last 5, sorted by updated_at DESC
  last_purchase_stub: null,            // placeholder for A2-CTX-05
  customer_notes: [],                  // placeholder for CTX-03
}
```

**Query logic in `ContactsService`:**
```
total_conversations:  prisma.conversation.count({ where: { contact_id, tenant_id } })
tags:                 prisma.conversationTag.findMany grouped by conversation.contact_id → distinct values
identities:           prisma.conversation.findMany({ distinct: ['channel_account_id'], include: channel_account })
key_events:           union ConversationAssignment + ConversationStatusHistory + ConversationTag
                      filtered by conversations.contact_id, sort DESC, take 5
recent_conversations: prisma.conversation.findMany({ orderBy: updated_at DESC, take: 5, include: channel_account })
```

**PATCH endpoint (for ACE-1479 edit form):**
- `PATCH /v1/omnichat/contacts/:contactId` — updates `display_name` + `profile_metadata`
- Add to same controller/service

### api-gateway proxy

**Files to create:**
- `apps/api-gateway/src/omnichat/controllers/contacts.controller.ts`
- `apps/api-gateway/src/omnichat/services/contacts.service.ts`

**Files to modify:**
- `apps/api-gateway/src/omnichat/omnichat.module.ts` — register ContactsModule
- `apps/omnichat-service/src/app.module.ts` — register ContactsModule

---

## Frontend: Shared Infrastructure

### New server action file
**Create:** `apps/workspace-admin/src/app/(main)/dashboard/chats/_api/contact.api.ts`
```typescript
'use server';
export async function getContactContext(contactId: string): Promise<ContactContext>
export async function updateContactAction(contactId: string, payload: UpdateContactPayload): Promise<void>
```

### New types
**Modify:** `apps/workspace-admin/src/types/omnichat.ts`
- Add: `ContactContext`, `ContactOverview`, `ContactIdentity`, `ContactKeyEvent`, `RecentConversationItem`

### Chat store slice
**Modify:** `apps/workspace-admin/src/app/(main)/dashboard/chats/_store/chat-store.ts`
- Add state: `contactContext: ContactContext | null`, `isLoadingContactContext: boolean`
- Add action: `fetchContactContext(contactId: string)` — calls `getContactContext`, sets state
- In `setActiveConversation`: reset `contactContext = null` immediately, then fire `fetchContactContext` **without await** (non-blocking)

### contact-info-panel.tsx
**Modify:** `apps/workspace-admin/src/app/(main)/dashboard/chats/_components/contact-info/contact-info-panel.tsx`
- Read `contactContext` + `isLoadingContactContext` from store
- Pass both as props to all child sections

---

## [ACE-1378] Frontend: Overview & Identities Panel

### contact-header-section.tsx
- Replace `MOCK_CONTACT_STATS` → `overview.total_conversations` + `overview.last_seen_at`
- Replace `MOCK_CONTACT_INFO` → `overview.phone` / `overview.email`
- Replace `MOCK_CONNECTED_CHANNELS` → unique channel_type values from `identities[]`
- Replace `contact.tags` → `overview.tags`
- Add `<Skeleton>` rows during loading
- Fallback: show `—` for null phone/email

### identities-section.tsx
- Replace `MOCK_IDENTITIES` with `identities[]` from context
- `external_user_id` already masked from API
- Map `channel_type` → existing `CHANNEL_ICONS` / `CHANNEL_COLORS` constants
- Add skeleton rows while loading
- Empty state: "No linked identities"

---

## [ACE-1477] Frontend: Key Events

### key-events-section.tsx
- Replace `MOCK_KEY_EVENTS` with `key_events[]` from context
- Dot color mapping (extend existing map):
  - `assigned` → orange
  - `status_change` → gray
  - `tag_change` → blue
- Add skeleton while loading
- Empty state: "No events yet"

> Key events stay in the Contact tab accordion — no tab restructuring needed.

---

## [ACE-1478] Frontend: Conversations List

### recent-conversations-section.tsx
- Replace `MOCK_RECENT_CONVERSATIONS` with `recent_conversations[]` from context
  - Title: `last_message_preview` or fallback `#${id.slice(0, 8)}`
  - Date: formatted `last_message_at`
  - "New" badge: when `status === 'open'`
- Replace `MOCK_TOTAL_CONVERSATIONS` with `overview.total_conversations`
- On click: call `setActiveConversation(conv.id)` from chat store
- Add skeleton while loading
- Empty state: "No previous conversations"

---

## [ACE-1479] Frontend: Edit Contact Profile Form

### New component
**Create:** `apps/workspace-admin/src/app/(main)/dashboard/chats/_components/contact-info/edit-contact-dialog.tsx`

- Shadcn `Dialog` triggered by pencil button in `contact-header-section.tsx`
- Form fields: Display name, Phone, Email, Address, Language preference
- On save: call `updateContactAction`, then `fetchContactContext` to refresh panel
- Validation: display name required, others optional

---

## Files Summary

| File | Task | Action |
|---|---|---|
| `apps/omnichat-service/src/contacts/contacts.service.ts` | ACE-1502 | Create |
| `apps/omnichat-service/src/contacts/contacts.controller.ts` | ACE-1502 | Create |
| `apps/omnichat-service/src/contacts/contacts.module.ts` | ACE-1502 | Create |
| `apps/omnichat-service/src/app.module.ts` | ACE-1502 | Modify |
| `apps/api-gateway/src/omnichat/controllers/contacts.controller.ts` | ACE-1502 | Create |
| `apps/api-gateway/src/omnichat/services/contacts.service.ts` | ACE-1502 | Create |
| `apps/api-gateway/src/omnichat/omnichat.module.ts` | ACE-1502 | Modify |
| `apps/workspace-admin/src/app/(main)/dashboard/chats/_api/contact.api.ts` | ACE-1502/1479 | Create |
| `apps/workspace-admin/src/types/omnichat.ts` | ACE-1502 | Modify |
| `apps/workspace-admin/src/app/(main)/dashboard/chats/_store/chat-store.ts` | ACE-1502 | Modify |
| `apps/workspace-admin/src/app/(main)/dashboard/chats/_components/contact-info/contact-info-panel.tsx` | ACE-1378 | Modify |
| `apps/workspace-admin/src/app/(main)/dashboard/chats/_components/contact-info/contact-header-section.tsx` | ACE-1378 | Modify |
| `apps/workspace-admin/src/app/(main)/dashboard/chats/_components/contact-info/identities-section.tsx` | ACE-1378 | Modify |
| `apps/workspace-admin/src/app/(main)/dashboard/chats/_components/contact-info/key-events-section.tsx` | ACE-1477 | Modify |
| `apps/workspace-admin/src/app/(main)/dashboard/chats/_components/contact-info/recent-conversations-section.tsx` | ACE-1478 | Modify |
| `apps/workspace-admin/src/app/(main)/dashboard/chats/_components/contact-info/edit-contact-dialog.tsx` | ACE-1479 | Create |

---

## Out of Scope
- `conversation-notes-tab-content.tsx` — ACE-1504 in progress, do not touch
- Order history → A2-CTX-05
- Customer notes API → ACE-1368/CTX-03 (return empty stub only)
- Identity merge/unmerge → ACE-1367/CTX-02
- SLA events in key_events (schema supports it, populated later)

---

## Verification Checklist

- [ ] Contact panel loads without blocking chat timeline (skeleton visible)
- [ ] Header shows real name, avatar, phone/email, conversation count, last seen
- [ ] Identities shows real channels with masked IDs
- [ ] Key events shows last 5 real events
- [ ] Recent conversations shows last 5, clicking navigates correctly
- [ ] Edit dialog saves and panel refreshes
- [ ] Switching conversations resets and re-fetches panel
- [ ] No data leakage across tenants (tenant_id always applied)
- [ ] Missing/null fields show graceful fallbacks
