# Plan: STORY-ICU-01 — Conversation List UI with Filters and Pagination

## Context
The existing conversation list at `/dashboard/chats` was built as a prototype with mock data, client-side filtering, and no pagination. This story redesigns it to match the Figma wireframe and connects it to the real backend API with cursor-based pagination and server-side filters.

**Key gaps in current implementation:**
- UI doesn't match Figma design (missing card-based layout, tags, assignee row, sort dropdown, sidebar toggle)
- No cursor-based pagination (loads all at once, limited by mock data)
- All filtering is client-side — doesn't leverage backend `channel_type`/`status` query params
- No loading skeleton or meaningful empty state
- `listConversations()` API call passes no filters or pagination params

## Step 1: Update listConversations API to accept filters & pagination
**File:** `conversations.api.ts`

Add `ListConversationsParams` interface:

```typescript
interface ListConversationsParams {
  channel_type?: string;
  status?: string;
  limit?: number;
  cursor?: string;
}
```
- Update `listConversations(params?)` to build query string from params and pass to `httpClient.get`

## Step 2: Update Zustand store for cursor pagination & server-side filters
**File:** `chat-store.ts`

- Add state fields: `nextCursor: string | null`, `hasMore: boolean`, `isLoadingMore: boolean`, `sortOrder: 'newest' | 'oldest'`
- Modify `fetchConversations()`:
  - Pass `channel_type` and `status` filters to API (from store state)
  - Pass `limit: 20` (per comment: "Pagination: Limit 20")
  - On success: set `conversations`, `nextCursor`, `hasMore`
  - Remove mock data merging (keep mock fallback only on API failure)
- Add `fetchMoreConversations()`:
  - Only callable when `hasMore && !isLoadingMore`
  - Pass `cursor: nextCursor` + same filters
  - Append results to existing conversations
  - Update `nextCursor` and `hasMore`
- Update `setChannelFilter()` and `setFilter()` to re-fetch from API (reset cursor)
- Add `setSortOrder()` action (re-fetches from API)
- Keep client-side search (`searchQuery`) as overlay filter on loaded data (backend doesn't support text search yet)

## Step 3: Redesign ConversationList header to match Figma
**File:** `conversation-list.tsx`

Replace the current header (Inbox + search + tabs + channel chips) with Figma design:

- Title row: "Your Inbox" (`text-xl font-semibold`) + search icon button (top-right)
- Filter bar: Sidebar toggle button + "All Channel" dropdown (using existing `Select` component) + "Newest" sort dropdown with arrow-up-down icon
- Remove the current filter tabs (All/Unread/Mine/Open/Resolved) and channel chips — replace with the two dropdowns
- The channel dropdown options: All Channel, LINE, Facebook, Instagram, Shopee, Lazada
- The sort dropdown options: Newest, Oldest
- Search: toggle a search input on click of the search icon (show/hide pattern)

**Reuse existing components:**
- `Button` (ghost variant for icon buttons) from `button.tsx`
- `Select` / `DropdownMenu` from existing UI components
- `PanelLeftClose` icon from `lucide-react`
- `ArrowUpDown`, `Search`, `EllipsisVertical`, `CheckCheck`, `UserRoundPlus`, `ChevronDown` from `lucide-react`

## Step 4: Redesign ConversationItem card to match Figma
**File:** `conversation-item.tsx`

Redesign each card to match the Figma wireframe structure:

- Card container: `rounded-2xl p-2 gap-3` with `bg-secondary` when selected
- Row 1 — Avatar + Info + More:
  - Avatar (40x40) with channel badge overlay (16x16, bottom-right) — reuse existing `Avatar` + `SimpleIcon`
  - Contact name (16px medium) + Channel account name (12px muted)
  - Ellipsis-vertical icon button (top-right)
- Row 2 — Message preview:
  - Read status: `CheckCheck` icon (16px) for read conversations
  - Message text (14px, single-line truncated)
  - Unread count badge: red `#EF001D` circle with white text (when unread)
  - Text color: `secondary-foreground` (`#171717`) when unread, `muted-foreground` (`#737373`) when read
- Row 3 — Tags: Outline badges (border `#E5E5E5`, 12px semibold, `rounded-lg`) — use existing `Badge` `variant="outline"`
- Row 4 — Assignee + Timestamp:
  - If assigned: "Assigned to [Name]" with chevron-down icon
  - If unassigned: `UserRoundPlus` icon in circular secondary background (20x20)
  - Timestamp (12px muted, right-aligned) — reuse existing `formatTime` helper

**Update `OmniConversation` type if needed:**
- Add `tags: string[]` to the contact or conversation (already exists on `OmniContact`)

## Step 5: Implement infinite scroll pagination
**File:** `conversation-list.tsx`

- Add an `IntersectionObserver` on a sentinel element at the bottom of the list
- When sentinel is visible and `hasMore` is true, call `fetchMoreConversations()`
- Show a small spinner at the bottom while loading more

## Step 6: Add loading skeleton and empty state
**File:** `conversation-list.tsx`

- Loading skeleton: Render 5-6 skeleton cards during initial fetch, each mimicking the card layout (avatar circle + text lines) — use existing `Skeleton` component
- Empty state: When API returns 0 results after filters:
  - Icon or illustration
  - "No conversations found" heading
  - "Try adjusting your filters" subtext

## Files to Modify

| File | Changes |
| --- | --- |
| `conversations.api.ts` | Add filter/pagination params to `listConversations` |
| `chat-store.ts` | Cursor pagination state, server-side filter dispatch, sort order |
| `conversation-list.tsx` | Redesign header, add infinite scroll, loading/empty states |
| `conversation-item.tsx` | Redesign card to match Figma |
| `omnichat.ts` | Add sort order type if needed |

## Verification
- **Visual:** Compare rendered UI with Figma screenshot — card layout, spacing, colors, typography should match
- **Filters:** Change "All Channel" dropdown → verify API is called with `channel_type` param and list updates
- **Sort:** Toggle Newest/Oldest → verify list re-orders via API
- **Pagination:** Scroll to bottom → verify "load more" triggers and appends conversations
- **Loading state:** On initial load, skeleton cards should appear briefly
- **Empty state:** Apply a filter that returns 0 results → verify empty state message appears
- **Selection:** Click a card → verify it highlights with `bg-secondary` and loads conversation in right panel
- **Lint/Build:** Run `pnpm --filter workspace-admin lint` and `pnpm --filter workspace-admin build`