# Meilisearch Integration — Technical Evaluation

> Date: 2026-03-31
> Project: ACE Omnichat / EPIC-ACE-1439 (Search/Filter/Sort/Saved Views)
> Scope: omnichat-service + workspace-admin

---

## 1. Executive Summary

The current search implementation uses Prisma `{ contains, mode: 'insensitive' }` — a simple PostgreSQL substring match with no full-text index. It returns conversation-level results only and has no message snippet extraction, no relevance ranking, and no typo tolerance. For the requirements in EPIC-ACE-1439 (grouped CONVERSATIONS + MESSAGES search, keyword-in-context snippets, <50ms latency), this implementation will not scale.

**Verdict:** Meilisearch integration is **technically beneficial** for the Messages search path but is **not required** for conversation-level filtering. A hybrid approach is recommended — keep PostgreSQL for filter/sort queries and use Meilisearch exclusively for full-text search on message `content` and contact `display_name`.

---

## 2. Current Architecture Baseline

```
workspace-admin (Next.js)
  └─ GET /v1/omnichat/conversations?search=keyword
       └─ omnichat-service (NestJS + Prisma)
            └─ PostgreSQL
                 WHERE contact.display_name ILIKE '%keyword%'
                 OR messages.content ILIKE '%keyword%'          ← full table scan on content
```

### Key Technical Constraints

| Item | Detail |
|------|--------|
| DB | PostgreSQL via Prisma ORM |
| Search | `{ contains: term, mode: 'insensitive' }` → translates to SQL `ILIKE '%term%'` |
| Message index | `(tenant_id, created_at)` and `(tenant_id, conversation_id, created_at DESC)` — **no FTS index** |
| Contact index | None on `display_name` |
| Pagination | Cursor-based on `(last_message_at, id)` for conversations; none for messages within search |
| Polling | Disabled when `searchQuery` is active |
| Result shape | Flat conversation list only — no message-level results, no snippet |

### Current Performance Characteristics

| Dataset Size | Estimated Search Latency (ILIKE) |
|---|---|
| 10,000 messages | ~20–50ms |
| 100,000 messages | ~200–800ms |
| 1,000,000 messages | ~2–10 seconds |
| 10,000,000 messages (production SaaS scale) | timeout / query killed |

> ILIKE with leading wildcard (`%term%`) **cannot use B-tree indexes** and forces a sequential scan. Multi-tenant workloads with tenant_id prefix reduce the scan set but do not eliminate it.

---

## 3. Meilisearch Capability Comparison

### 3.1 Feature Matrix

| Feature | Current (PostgreSQL ILIKE) | Meilisearch |
|---|---|---|
| Case-insensitive match | ✅ | ✅ |
| Substring match | ✅ | ✅ |
| Typo tolerance (1-2 char) | ❌ | ✅ (configurable per attribute) |
| Relevance ranking | ❌ (all results equal weight) | ✅ (9-tier ranking rules) |
| Keyword snippet / highlight | ❌ | ✅ (`_formatted` attribute with `<em>`) |
| Faceted filtering | ❌ | ✅ (filterable attributes with zero latency) |
| Grouped result sections | ❌ (requires two queries + code merging) | ✅ (multi-index federated search) |
| Prefix search (autocomplete) | ❌ | ✅ (real-time, first keystroke) |
| Multi-language support (Thai) | ⚠️ (byte-level ILIKE, no tokenization) | ✅ (CJK/Thai tokenizer via `charabia`) |
| Geo-search | ❌ | ✅ |
| Stop words | ❌ | ✅ |
| Synonyms | ❌ | ✅ |
| Real-time index | — | ✅ (async task queue, ~200ms lag) |
| Pagination | Cursor (custom) | Offset + cursor (both supported) |
| Tenant isolation (multi-tenant) | ✅ (WHERE tenant_id) | ✅ (filterable `tenant_id` attribute) |
| Federated multi-index search | ❌ | ✅ (`/multi-search` endpoint) |
| Search analytics | ❌ | ✅ (built-in analytics API) |

### 3.2 Thai Language Handling

PostgreSQL `ILIKE` performs **byte-level substring matching** on UTF-8 strings. Thai text searches work only for exact substrings — no word boundary awareness, no compound word splitting.

Meilisearch uses the **`charabia` tokenizer** which supports Thai segmentation. For example, searching `"สลิปโอน"` will also match `"สลิป"` and `"โอน"` as separate tokens. This is critical for the `tags`, `contact.display_name`, and `messages.content` search paths.

### 3.3 Performance Benchmarks (Published — Meilisearch v1.x)

| Operation | Meilisearch | PostgreSQL FTS (tsvector) | PostgreSQL ILIKE |
|---|---|---|---|
| Search (1M docs) | 1–10ms | 10–50ms | 500ms–5s |
| Facet count (10 facets) | <5ms | 50–200ms | N/A |
| Indexing throughput | ~10K–50K docs/s | ~5K docs/s | — |
| Index size overhead | ~2× raw data | ~0.3× raw data | — |
| RAM usage (1M docs) | ~500MB–2GB | shared with PG | — |

> Source: Meilisearch official benchmarks and community reports. Figures vary by hardware and document structure.

### 3.4 Scalability Requirements (ACE-specific)

Estimated message volume for a mid-size SaaS omnichat tenant:
- 500 conversations/day × 20 messages = **10,000 messages/day**
- 1 year × 100 tenants = **365,000,000 messages** (full SaaS scale)

For a single production tenant searching across 6 months of messages (~1.8M messages), ILIKE will be unusable. Meilisearch handles this comfortably at <10ms.

---

## 4. Where Meilisearch Adds Maximum Value

### Priority 1 — HIGH IMPACT (Direct EPIC-ACE-1439 requirement)

| Subtask | Current Problem | Meilisearch Benefit |
|---|---|---|
| SFS-01-BE-1: Grouped search endpoint | Two separate ILIKE queries merged in code; slow at scale | Single `/multi-search` call across `conversations` + `messages` indexes; returns both sections in one round-trip |
| SFS-01-BE-2: Message snippet extraction | No snippet API — would require fetching full `content` and slicing in code | Native `attributesToHighlight` returns `_formatted.content` with `<em>keyword</em>` wrapped matches |
| SFS-01-FE-3: Search debounce 300ms | 300ms debounce masks slow ILIKE; still fires heavy queries | 300ms safe because Meilisearch responds in 1–10ms; debounce is UX preference, not a performance mask |
| ACE-1443: Thai language support | ILIKE matches byte substrings only; searching `"รอสลิป"` won't match message containing `"รอการตรวจสอบสลิปโอนเงิน"` | `charabia` tokenizer splits Thai correctly; partial word matches work |

### Priority 2 — MEDIUM IMPACT (Future stories / R2)

| Subtask | Current Problem | Meilisearch Benefit |
|---|---|---|
| Contact search (autocomplete) | No autocomplete — user must type exact prefix | Prefix search on first keystroke; typo tolerance for name misspellings |
| Tag-based message search | `tag_id` filters conversations but can't search tag names in message content | Index `tag_names` as attribute; searchable facet |
| Search analytics (R2) | Zero visibility into what agents search for | Built-in search analytics API; track zero-result queries |
| Saved view "smart suggestions" (R2) | No search query suggestions | Query suggestions API |

### Priority 3 — LOW IMPACT (No benefit from Meilisearch)

| Area | Reason |
|---|---|
| Conversation list filters (status, channel, assignee) | These are structured filters — SQL WHERE is optimal; Meilisearch filterable attributes add overhead without gain |
| Sort (latest_activity, oldest_waiting) | Sort by datetime columns — SQL ORDER BY with indexes is faster and more precise |
| Cursor-based pagination of the main conversation list | Meilisearch offset pagination does not support stable cursor; cursor must stay in PostgreSQL |
| Saved views storage + retrieval | Relational data — PostgreSQL is correct choice |
| Real-time conversation updates (polling) | Event-driven update via webhook/polling — Meilisearch indexing has ~200ms lag, not suitable for live status changes |

---

## 5. Implementation Phases

### Phase 0 — Infrastructure Setup (0.5 SP)

**Goal:** Add Meilisearch to the development and production environment.

```yaml
# docker-compose.yml addition
meilisearch:
  image: getmeili/meilisearch:v1.11
  ports:
    - "7700:7700"
  environment:
    - MEILI_MASTER_KEY=${MEILI_MASTER_KEY}
    - MEILI_ENV=development
  volumes:
    - meilisearch_data:/meili_data
```

**Environment variables to add:**
```env
MEILISEARCH_HOST=http://meilisearch:7700
MEILISEARCH_API_KEY=your-master-key
MEILISEARCH_SEARCH_KEY=search-only-api-key  # for FE if needed
```

**NestJS dependency:**
```bash
npm install meilisearch   # official JS SDK
```

### Phase 1 — Index Design & Data Modeling (1 SP)

**Two indexes required:**

#### Index: `conversations`

```typescript
// Document shape in Meilisearch
interface ConversationDocument {
  id: string;                    // PK
  tenant_id: string;             // filterable
  contact_display_name: string;  // searchable
  status: string;                // filterable
  channel_type: string;          // filterable
  assigned_agent_id: string | null; // filterable
  tag_ids: string[];             // filterable
  tag_names: string[];           // searchable
  last_message_preview: string | null; // searchable
  last_message_at: number;       // sortable (unix timestamp)
  created_at: number;            // sortable
}
```

#### Index: `messages`

```typescript
interface MessageDocument {
  id: string;
  tenant_id: string;             // filterable
  conversation_id: string;       // filterable + returnable for navigation
  content: string | null;        // searchable (primary)
  sender_display_name: string | null; // searchable
  content_type: string;          // filterable ('text' only for search)
  channel_type: string;          // filterable
  created_at: number;            // sortable
  deleted_at: number | null;     // filterable (exclude deleted)
}
```

**Index settings:**

```typescript
// conversations index settings
await meili.index('conversations').updateSettings({
  searchableAttributes: ['contact_display_name', 'tag_names', 'last_message_preview'],
  filterableAttributes: ['tenant_id', 'status', 'channel_type', 'assigned_agent_id', 'tag_ids'],
  sortableAttributes: ['last_message_at', 'created_at'],
  typoTolerance: {
    enabled: true,
    minWordSizeForTypos: { oneTypo: 4, twoTypos: 8 },
  },
});

// messages index settings
await meili.index('messages').updateSettings({
  searchableAttributes: ['content', 'sender_display_name'],
  filterableAttributes: ['tenant_id', 'conversation_id', 'content_type', 'channel_type', 'deleted_at'],
  sortableAttributes: ['created_at'],
  typoTolerance: { enabled: false },  // Exact match preferred for message content
  pagination: { maxTotalHits: 1000 },
});
```

### Phase 2 — Indexing Pipeline (1.5 SP)

**Strategy: Event-driven sync via existing message/conversation create events**

The omnichat-service already has message creation and update flows. Add Meilisearch sync as a side-effect using NestJS event emitter or BullMQ (Redis already in docker-compose).

```typescript
// apps/omnichat-service/src/search/search.service.ts (NEW)
@Injectable()
export class SearchService {
  private readonly meili: MeiliSearch;

  constructor(private readonly configService: ConfigService) {
    this.meili = new MeiliSearch({
      host: configService.get('MEILISEARCH_HOST'),
      apiKey: configService.get('MEILISEARCH_API_KEY'),
    });
  }

  async indexMessage(message: Message & { conversation: Conversation & { contact: Contact } }) {
    if (message.content_type !== 'text' || !message.content) return; // index text only
    await this.meili.index('messages').addDocuments([{
      id: message.id,
      tenant_id: message.tenant_id,
      conversation_id: message.conversation_id,
      content: message.content,
      sender_display_name: message.sender_display_name,
      content_type: message.content_type,
      channel_type: message.channel_type,
      created_at: message.created_at.getTime(),
      deleted_at: message.deleted_at ? message.deleted_at.getTime() : null,
    }]);
  }

  async deleteMessage(messageId: string) {
    await this.meili.index('messages').deleteDocument(messageId);
  }

  async indexConversation(conversation: Conversation & { contact: Contact; tags: Tag[] }) {
    await this.meili.index('conversations').addDocuments([{
      id: conversation.id,
      tenant_id: conversation.tenant_id,
      contact_display_name: conversation.contact.display_name ?? '',
      status: conversation.status,
      channel_type: conversation.channel_type,
      assigned_agent_id: conversation.assigned_agent_id ?? null,
      tag_ids: conversation.tags.map(t => t.tag_id),
      tag_names: conversation.tags.map(t => t.tag.name),
      last_message_preview: conversation.last_message_preview ?? null,
      last_message_at: conversation.last_message_at?.getTime() ?? 0,
      created_at: conversation.created_at.getTime(),
    }]);
  }
}
```

**Bulk backfill job** (one-time migration):
```typescript
// apps/omnichat-service/src/search/search-backfill.command.ts
async backfillMessages(tenantId: string) {
  const batchSize = 500;
  let cursor: string | undefined;

  do {
    const messages = await this.prisma.message.findMany({
      where: { tenant_id: tenantId, content_type: 'text', deleted_at: null },
      take: batchSize,
      skip: cursor ? 1 : 0,
      cursor: cursor ? { id: cursor } : undefined,
      orderBy: { created_at: 'asc' },
    });
    if (messages.length === 0) break;
    await this.meili.index('messages').addDocuments(
      messages.map(m => ({ ...m, created_at: m.created_at.getTime() }))
    );
    cursor = messages[messages.length - 1].id;
  } while (true);
}
```

### Phase 3 — Grouped Search API (2 SP)

**New endpoint: `GET /v1/omnichat/conversations/search`**

Uses Meilisearch `/multi-search` to query both indexes simultaneously:

```typescript
// apps/omnichat-service/src/conversations/conversations.controller.ts
@Get('search')
async groupedSearch(@Query() dto: GroupedSearchDto, @TenantId() tenantId: string) {
  return this.searchService.groupedSearch({
    query: dto.q,
    tenantId,
    filters: { status: dto.status, channel_type: dto.channel_type },
    limit: dto.limit ?? 5,
  });
}
```

```typescript
// search.service.ts
async groupedSearch({ query, tenantId, filters, limit }) {
  const tenantFilter = `tenant_id = "${tenantId}"`;
  const statusFilter = filters.status ? ` AND status IN [${filters.status.split(',').map(s => `"${s}"`).join(',')}]` : '';
  const channelFilter = filters.channel_type ? ` AND channel_type IN [${filters.channel_type.split(',').map(c => `"${c}"`).join(',')}]` : '';
  const baseFilter = `${tenantFilter}${statusFilter}${channelFilter}`;

  const results = await this.meili.multiSearch({
    queries: [
      {
        indexUid: 'conversations',
        q: query,
        filter: baseFilter,
        limit,
        attributesToHighlight: ['contact_display_name'],
        highlightPreTag: '<mark>',
        highlightPostTag: '</mark>',
      },
      {
        indexUid: 'messages',
        q: query,
        filter: `${tenantFilter} AND deleted_at IS NULL AND content_type = "text"`,
        limit,
        attributesToHighlight: ['content'],
        attributesToCrop: ['content'],
        cropLength: 80,
        highlightPreTag: '<mark>',
        highlightPostTag: '</mark>',
      },
    ],
  });

  return {
    conversations: {
      items: results.results[0].hits,
      total: results.results[0].estimatedTotalHits,
    },
    messages: {
      items: results.results[1].hits,
      total: results.results[1].estimatedTotalHits,
    },
  };
}
```

### Phase 4 — Frontend Integration (1 SP)

**No change required** to the chat-store search state. Only the API function changes:

```typescript
// conversations.api.ts — new search function
export async function groupedSearch(params: GroupedSearchParams): Promise<GroupedSearchResponse> {
  const query = new URLSearchParams({ q: params.q, limit: String(params.limit ?? 5) });
  if (params.status) query.set('status', params.status);
  if (params.channel_type) query.set('channel_type', params.channel_type);
  return httpClient.get(`/v1/omnichat/conversations/search?${query}`);
}
```

`search-results-view.tsx` (new component from SFS-01-FE-1) calls `groupedSearch()` when `searchQuery.length >= 2`, replacing the current `listConversations({ search: query })` call.

### Phase 5 — Fallback Mechanism

If Meilisearch is unavailable (service down, indexing lag), fall back to PostgreSQL ILIKE:

```typescript
async groupedSearch(params) {
  try {
    return await this.meilisearchGroupedSearch(params);
  } catch (err) {
    this.logger.warn('Meilisearch unavailable, falling back to PostgreSQL search', err.message);
    return await this.postgresGroupedSearch(params);  // existing listConversations() logic
  }
}
```

---

## 6. Success Criteria

### 6.1 Search Latency

| Metric | Target | Measurement Method |
|---|---|---|
| Meilisearch search response time (p50) | < 10ms | Meilisearch stats API (`GET /stats`) |
| Meilisearch search response time (p99) | < 50ms | Application-level timer in groupedSearch() |
| End-to-end API response (p50) | < 100ms | NestJS interceptor timing |
| End-to-end API response (p99) | < 300ms | Application monitoring (Datadog/Prometheus) |
| PostgreSQL fallback (p50) | < 500ms | Fallback path logging |

### 6.2 Relevance

| Metric | Target | Measurement |
|---|---|---|
| Top result is expected conversation | ≥ 90% for exact phrase queries | Manual QA with 50 pre-defined test queries |
| Zero-result rate for valid queries | < 5% | Meilisearch analytics API |
| Typo tolerance hit rate (1-char error) | ≥ 80% | Test suite with intentional typos |

### 6.3 Indexing

| Metric | Target | Measurement |
|---|---|---|
| Index lag (message created → searchable) | < 500ms | Compare `created_at` to Meilisearch task `finishedAt` |
| Backfill throughput | ≥ 5,000 docs/batch | Backfill job timing log |
| Index consistency (PG vs Meili) | < 0.1% divergence | Daily reconciliation job counting discrepancies |

### 6.4 System Resources

| Resource | Limit | Action if Exceeded |
|---|---|---|
| Meilisearch RAM | < 2GB per environment | Tune `MEILI_MAX_INDEXING_MEMORY`, reduce attribute count |
| Meilisearch disk | < 10GB | Archive old tenant data, reduce stored attributes |
| Indexing CPU spike | < 50% for 5s | Rate-limit BullMQ indexing queue |

---

## 7. Risk Assessment Matrix

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **Data consistency gap** — message indexed in Meili but updated/deleted in PG | Medium | High | Soft-delete sync: on `deleted_at` set, update Meili document immediately; daily reconciliation job |
| **Indexing lag during high traffic** | Medium | Medium | BullMQ queue with priority; messages still searchable via PG fallback during lag |
| **Meilisearch service outage** | Low | Medium | Circuit breaker + PostgreSQL fallback (Phase 5); Meilisearch is stateless — restart recovers from disk |
| **Multi-tenant data leakage** | Low | Critical | All queries MUST include `filter: tenant_id = "X"`; unit test asserting filter presence on every search call |
| **Index rebuilds on schema change** | Medium | Medium | Index rebuilds are async and non-blocking; run during off-peak with BullMQ batch job |
| **Thai tokenization quality** | Low | Medium | Charabia Thai support is alpha-quality in v1.x — test with real agent message corpus before enabling typo tolerance on Thai |
| **Memory pressure (large tenant)** | Low | High | Configure `MEILI_MAX_INDEXING_MEMORY=512mb`; monitor with Prometheus; scale Meilisearch to dedicated node if needed |
| **Migration complexity** | Low | Low | Backfill is additive; PG is still source of truth; rollback = disable Meili route, no data loss |
| **Long-term maintenance** | Low | Medium | Meilisearch is self-hosted — team must own upgrades; plan quarterly version bumps; consider Meilisearch Cloud for zero-ops |
| **Cursor pagination incompatibility** | Low | Low | Conversation list pagination stays in PostgreSQL; Meilisearch only used for search endpoint (offset pagination, max 1000 results acceptable for search use case) |

---

## 8. Proof-of-Concept Plan

### PoC Scope

Build a working grouped search endpoint using real production data (or anonymized copy) and validate all 6 success criteria.

**Duration:** 2–3 days engineering time.

### PoC Test Scenarios

| Scenario | Input | Expected Output | Pass Condition |
|---|---|---|---|
| Exact phrase match | `q=refund` | Conversations with "refund" in contact name + messages with "refund" in content | Both sections populated, correct highlight |
| Thai text search | `q=สลิป` | Messages containing "สลิป" (slip) | Charabia tokenizer returns results |
| Typo tolerance | `q=refudn` (1-char swap) | Same result as `q=refund` | Meilisearch typo tolerance fires |
| Filter + search combined | `q=order&status=open&channel_type=LINE` | Only open LINE conversations | tenant_id + status + channel filter all present in Meili filter string |
| Empty result | `q=xyznonexistent` | `{ conversations: { total: 0 }, messages: { total: 0 } }` | No crash, empty state handled in UI |
| Tenant isolation | Tenant A searches `q=hello` | No results from Tenant B | Verified by cross-tenant query in test |
| Deleted message excluded | `q=deleted_keyword` | Message with `deleted_at != null` NOT in results | `deleted_at IS NULL` filter applied |
| Fallback on Meili down | Stop Meilisearch container | Search degrades to PG ILIKE | Fallback log emitted, result still returns |

### Performance Validation Procedure

```bash
# 1. Start Meilisearch locally
docker run -p 7700:7700 getmeili/meilisearch:v1.11

# 2. Backfill 100,000 messages from dev DB
npx ts-node scripts/backfill-search.ts --tenant=dev-tenant-id --limit=100000

# 3. Run latency benchmark (k6 or autocannon)
autocannon -c 10 -d 30 "http://localhost:3000/v1/omnichat/conversations/search?q=order&tenant_id=dev"

# 4. Check Meilisearch stats
curl http://localhost:7700/indexes/messages/stats -H "Authorization: Bearer MASTER_KEY"
# Inspect: numberOfDocuments, isIndexing, fieldDistribution

# 5. Compare results to PostgreSQL baseline
curl "http://localhost:3000/v1/omnichat/conversations?search=order" > pg_results.json
curl "http://localhost:3000/v1/omnichat/conversations/search?q=order" > meili_results.json
# Manual diff: verify Meilisearch returns superset of PostgreSQL results (richer, not fewer)
```

### Rollback Strategy

| Phase | Rollback Action | Data Loss |
|---|---|---|
| Phase 0 (infra) | Remove docker-compose entry | None |
| Phase 1–2 (indexing) | Delete Meilisearch indexes; remove SearchService wiring | None — PG is source of truth |
| Phase 3 (API) | Route `GET /conversations/search` → 404 or redirect to `/conversations?search=` | None |
| Phase 4 (FE) | Revert `search-results-view.tsx` to call `listConversations({ search: q })` | None |

All phases are **fully reversible**. Meilisearch indexes are derived data — they can be rebuilt from PostgreSQL at any time.

---

## 9. Recommended Subtask Additions to EPIC-ACE-1439

The following subtasks should be added to the existing breakdown in `subtasks.md`:

| New Subtask | Parent Story | Layer | SP |
|---|---|---|---|
| [INFRA] Add Meilisearch to docker-compose + env vars | ACE-1440 | INFRA | 0.5 |
| [BE] SearchModule + SearchService (index/delete wrappers) | ACE-1440 | BE | 1 |
| [BE] Index design + settings for `conversations` + `messages` indexes | ACE-1440 | BE | 0.5 |
| [BE] Event hooks: sync message create/update/delete → Meilisearch | ACE-1440 | BE | 1 |
| [BE] Backfill CLI command for existing messages per tenant | ACE-1440 | BE | 1 |
| [BE] Grouped search endpoint using Meilisearch /multi-search | ACE-1440 | BE | 1.5 |
| [BE] PostgreSQL fallback for grouped search (circuit breaker) | ACE-1440 | BE | 0.5 |
| [BE] Daily reconciliation job (PG vs Meili doc count per tenant) | ACE-1443 | BE | 1 |

**Estimated additional SP: 7 SP**
**Revised total for EPIC-ACE-1439: 33 + 7 = 40 SP**

---

## 10. Decision Summary

| Question | Answer |
|---|---|
| Is Meilisearch technically superior for this use case? | **Yes** — for message full-text search at scale |
| Is it required for the MVP (EPIC-ACE-1439)? | **Yes for SFS-01** (grouped search + snippet); not required for SFS-02/03/04/05 |
| Should it replace PostgreSQL entirely? | **No** — hybrid: Meili for search, PG for filters/sort/pagination |
| What is the operational cost? | Low — single Docker container, ~500MB RAM for 1M messages, minimal ops |
| Is Thai language support adequate? | **Acceptable** — charabia handles Thai segmentation; recommend disabling typo tolerance for Thai until further testing |
| What is the migration risk? | **Low** — fully additive, PostgreSQL remains source of truth, rollback is trivial |
| When should PoC be run? | Before implementing SFS-01-BE-1 (Grouped search endpoint) |

---

_Generated: 2026-03-31 | ACE Omnichat Engineering_
