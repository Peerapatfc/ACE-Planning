# Implementation Plan: ACE-1257 - Lazada Scheduled Polling fetch Chat Message

## Context

This task implements scheduled polling for Lazada seller chat messages as part of the marketplace polling framework (ACE-702). The system already has working implementations for Shopee (ACE-1256) and TikTok (ACE-1258), which provide proven patterns to follow.

**Why this is needed:**
- Lazada may not provide reliable webhooks for real-time message notifications
- Periodic polling ensures we don't miss customer messages
- Maintains consistency with other marketplace integrations (Shopee, TikTok)

**Current state:**
- ✅ Polling framework exists and is operational
- ✅ LazadaPoller stub is registered but returns zero items
- ✅ LazadaExternalService exists with OAuth token exchange
- ⚠️ No Lazada conversation/message API methods yet
- ⚠️ No Lazada types for messages/conversations
- ❌ No LazadaChannelMapper for normalization

**Expected outcome:**
- Lazada messages are polled every 5 minutes (configurable via POLLING_CRON_EXPRESSION)
- Messages are published to SQS and normalized like other marketplaces
- Rate limiting and error handling work correctly
- No duplicate message ingestion

---

## API Documentation (Confirmed from Lazada Open Platform)

✅ **Lazada IM API Endpoints** (specs obtained):

### 1. GetSessionList (GET `/im/session/list`)
Query seller session (conversation) list

**Parameters:**
- `last_session_id` (String, Optional) - For pagination, null for first page
- `start_time` (String, **Required**) - Current timestamp for first page, use `next_start_time` from response for next page
- `page_size` (String, **Required**) - Page size

**Response:**
- `session_list` - Array of sessions
- `next_start_time` - Use for next page
- `has_more` - Boolean indicating more pages
- `last_session_id` - Last session ID in current page

### 2. GetMessages (GET `/im/message/list`)
Get message list for a session

**Parameters:**
- `session_id` (String, **Required**) - Session/conversation ID
- `start_time` (Number, **Required**) - Current timestamp for first page, use `next_start_time` for pagination
- `page_size` (Number, **Required**) - Page size
- `last_message_id` (String, Optional) - For pagination, null for first page

**Response:**
- `message_list` - Array of messages with fields: last_message_id, message_id, type, content, from_account_id, from_account_type, process_msg, session_id, auto_reply, site_id, template_id, from_account_id, status
- `next_start_time` - Timestamp for next page
- `has_more` - Boolean

### 3. Common Authentication Parameters
All endpoints require:
- `app_key` (String, Required) - App ID from Lazada Open Platform
- `timestamp` (String, Required) - Unix timestamp in milliseconds
- `access_token` (String, Required) - OAuth access token
- `sign_method` (String, Required) - "sha256"
- `sign` (String, Required) - HMAC signature

**Base URL:** Region-specific
- Vietnam: `https://api.lazada.vn/rest`
- Singapore: `https://api.lazada.sg/rest`
- Thailand: `https://api.lazada.co.th/rest`
- Philippines: `https://api.lazada.com.ph/rest`
- Malaysia: `https://api.lazada.com.my/rest`
- Indonesia: `https://api.lazada.co.id/rest`

---

## Implementation Plan

### 1. Define Lazada Types (NEW FILE)

**File:** `apps/omnichat-service/src/external/types/lazada.ts`

**Create type definitions based on actual Lazada IM API:**

```typescript
// API Response wrapper (confirmed from docs)
export interface LazadaApiResponse<T> {
  code: string;           // '0' = success
  success: boolean;
  err_code: string;
  err_message: string;
  data: T;
  request_id: string;
}

// Session (Conversation) types
export interface LazadaSession {
  session_id: string;              // Unique session/conversation ID
  summary: string;                 // Conversation summary/title
  unread_count: number;            // Number of unread messages
  last_message_id: string;         // ID of the most recent message
  last_message_time: string;       // Timestamp of last message
  buyer_id: string;                // Buyer's ID
  buyer_url: string;               // Buyer profile URL
  site_id: string;                 // Site/marketplace ID
  title: string;                   // Conversation title
  self_position: string;           // Seller position/role
  to_position: string;             // Buyer position/role
  tags?: string[];                 // Optional tags
}

export interface LazadaSessionListData {
  session_list: LazadaSession[];   // Array of sessions (not "conversations")
  has_more: boolean;               // More pages available
  next_start_time: string;         // Timestamp for next page
  last_session_id: string;         // Last session ID for pagination
}

// Message types
export interface LazadaMessage {
  message_id: string;              // Unique message ID
  session_id: string;              // Parent session/conversation ID
  type: string;                    // Message type (1=text, 2=image, etc.)
  content: string;                 // Message content (JSON string or text)
  from_account_id: string;         // Sender account ID
  from_account_type: string;       // "buyer" or "seller"
  status: string;                  // Message status
  auto_reply: boolean;             // Is auto-reply message
  process_msg: string;             // Processing message info
  template_id?: string;            // Template ID if applicable
  site_id: string;                 // Site/marketplace ID
}

export interface LazadaMessageListData {
  message_list: LazadaMessage[];   // Array of messages (not just "messages")
  has_more: boolean;               // More pages available
  next_start_time: string;         // Timestamp for next page
  last_message_id: string;         // Last message ID for pagination
}

// Error types (following Shopee/TikTok pattern)
export const LAZADA_RATE_LIMIT_CODE = 'RateLimitExceeded';

export class LazadaRateLimitError extends Error {
  constructor(
    readonly retryAfterMs: number,
    message = 'Lazada rate limit exceeded',
  ) {
    super(message);
    this.name = 'LazadaRateLimitError';
  }
}

export class LazadaApiError extends Error {
  constructor(
    readonly code: string,
    message: string,
    readonly requestId: string,
  ) {
    super(`Lazada API error ${code}: ${message} (request_id=${requestId})`);
    this.name = 'LazadaApiError';
  }
}
```

**Note:** Types are based on actual API documentation from Lazada Open Platform.

---

### 2. Extend LazadaExternalService

**File:** `apps/omnichat-service/src/external/services/lazada-external.service.ts`

**Add new methods following the existing `generateSignature` and `exchangeAuthCode` pattern:**

```typescript
// Add configuration - region-specific base URLs
private getApiUrl(region: string = 'sg'): string {
  const urls: Record<string, string> = {
    vn: 'https://api.lazada.vn/rest',
    sg: 'https://api.lazada.sg/rest',
    th: 'https://api.lazada.co.th/rest',
    ph: 'https://api.lazada.com.ph/rest',
    my: 'https://api.lazada.com.my/rest',
    id: 'https://api.lazada.co.id/rest',
  };
  return urls[region] || urls.sg;
}

/**
 * List sessions (conversations) for a seller account with pagination.
 * GET /im/session/list
 */
async listSessions(params: {
  accessToken: string;
  appKey: string;
  appSecret: string;
  region?: string;              // Default 'sg'
  lastSessionId?: string;       // For pagination (null for first page)
  startTime: string;            // Current timestamp for first page, next_start_time for next page
  pageSize: number;             // Page size
}): Promise<LazadaSessionListData> {
  const path = '/im/session/list';
  const timestamp = Date.now().toString();
  const apiUrl = this.getApiUrl(params.region);

  const apiParams: Record<string, string> = {
    app_key: params.appKey,
    access_token: params.accessToken,
    timestamp,
    sign_method: 'sha256',
    start_time: params.startTime,
    page_size: params.pageSize.toString(),
  };

  // Add optional pagination parameter
  if (params.lastSessionId) {
    apiParams.last_session_id = params.lastSessionId;
  }

  const sign = this.generateSignature(params.appSecret, path, apiParams);
  const queryParams = new URLSearchParams({ ...apiParams, sign }).toString();
  const url = `${apiUrl}${path}?${queryParams}`;

  try {
    const response = await firstValueFrom(
      this.httpService.get<LazadaApiResponse<LazadaSessionListData>>(url),
    );

    // Check for HTTP 429
    if (response.status === 429) {
      const retryAfter = Number(response.headers['retry-after'] ?? 60) * 1000;
      throw new LazadaRateLimitError(retryAfter);
    }

    return this.handleApiResponse(response.data, path);
  } catch (error) {
    if (error instanceof LazadaRateLimitError || error instanceof LazadaApiError) {
      throw error;
    }
    this.logger.error(`Lazada API ${path} failed: ${error.message}`);
    throw error;
  }
}

/**
 * List messages for a specific session with pagination.
 * GET /im/message/list
 */
async listMessages(params: {
  accessToken: string;
  appKey: string;
  appSecret: string;
  region?: string;              // Default 'sg'
  sessionId: string;            // Session/conversation ID (required)
  startTime: number;            // Current timestamp for first page, next_start_time for next page
  pageSize: number;             // Page size
  lastMessageId?: string;       // For pagination (null for first page)
}): Promise<LazadaMessageListData> {
  const path = '/im/message/list';
  const timestamp = Date.now().toString();
  const apiUrl = this.getApiUrl(params.region);

  const apiParams: Record<string, string> = {
    app_key: params.appKey,
    access_token: params.accessToken,
    timestamp,
    sign_method: 'sha256',
    session_id: params.sessionId,
    start_time: params.startTime.toString(),
    page_size: params.pageSize.toString(),
  };

  // Add optional pagination parameter
  if (params.lastMessageId) {
    apiParams.last_message_id = params.lastMessageId;
  }

  const sign = this.generateSignature(params.appSecret, path, apiParams);
  const queryParams = new URLSearchParams({ ...apiParams, sign }).toString();
  const url = `${apiUrl}${path}?${queryParams}`;

  try {
    const response = await firstValueFrom(
      this.httpService.get<LazadaApiResponse<LazadaMessageListData>>(url),
    );

    // Check for HTTP 429
    if (response.status === 429) {
      const retryAfter = Number(response.headers['retry-after'] ?? 60) * 1000;
      throw new LazadaRateLimitError(retryAfter);
    }

    return this.handleApiResponse(response.data, path);
  } catch (error) {
    if (error instanceof LazadaRateLimitError || error instanceof LazadaApiError) {
      throw error;
    }
    this.logger.error(`Lazada API ${path} failed: ${error.message}`);
    throw error;
  }
}

/**
 * Handle Lazada API response and throw appropriate errors.
 * Response structure: { code, success, err_code, err_message, data, request_id }
 */
private handleApiResponse<T>(
  response: LazadaApiResponse<T>,
  path: string,
): T {
  // Success: code = '0' or success = true
  if (response.code === '0' || response.success === true) {
    return response.data;
  }

  // Rate limiting - check for common rate limit error codes
  const isRateLimit =
    response.err_code === LAZADA_RATE_LIMIT_CODE ||
    response.code === '429' ||
    response.err_message?.toLowerCase().includes('rate limit') ||
    response.err_message?.toLowerCase().includes('too many requests');

  if (isRateLimit) {
    throw new LazadaRateLimitError(60_000, response.err_message); // Default 60s
  }

  // Other errors
  throw new LazadaApiError(
    response.err_code || response.code,
    response.err_message || 'Unknown error',
    response.request_id,
  );
}
```

**Add imports:**
```typescript
import type {
  LazadaApiResponse,
  LazadaSessionListData,
  LazadaMessageListData,
} from '../types/lazada';
import { LazadaRateLimitError, LazadaApiError, LAZADA_RATE_LIMIT_CODE } from '../types/lazada';
```

---

### 3. Implement LazadaPoller

**File:** `apps/omnichat-service/src/marketplace-polling/pollers/lazada-poller.ts`

**Replace stub with full implementation following ShopeePoller pattern:**

See full implementation in the plan file (too long to include here - includes poll(), resolveCredentials(), fetchSessionsSince(), fetchMessagesSince() methods)

**Update module to inject LazadaExternalService:**

**File:** `apps/omnichat-service/src/marketplace-polling/marketplace-polling.module.ts`

Add import and injection:
```typescript
import { LazadaExternalService } from '../external/services/lazada-external.service';

// In providers array, add LazadaExternalService before LazadaPoller
```

---

### 4. Create LazadaChannelMapper for Normalization

**File:** `apps/omnichat-normalizer-worker/src/worker/mappers/lazada-channel-mapper.ts`

See full implementation in the plan file (handles type-based content parsing: "1"=text, "2"=image, "3"=product, "4"=order, "6"=file)

**Register mapper in module:**

**File:** `apps/omnichat-normalizer-worker/src/worker/worker.module.ts`

```typescript
import { LazadaChannelMapper } from './mappers/lazada-channel-mapper';

// Add to ChannelMapperRegistry factory and providers
```

---

## Critical Files to Modify

1. **NEW:** `apps/omnichat-service/src/external/types/lazada.ts` - Type definitions
2. **EDIT:** `apps/omnichat-service/src/external/services/lazada-external.service.ts` - Add listSessions, listMessages methods
3. **EDIT:** `apps/omnichat-service/src/marketplace-polling/pollers/lazada-poller.ts` - Replace stub with full implementation
4. **EDIT:** `apps/omnichat-service/src/marketplace-polling/marketplace-polling.module.ts` - Inject LazadaExternalService
5. **NEW:** `apps/omnichat-normalizer-worker/src/worker/mappers/lazada-channel-mapper.ts` - Normalization logic
6. **EDIT:** `apps/omnichat-normalizer-worker/src/worker/worker.module.ts` - Register LazadaChannelMapper

---

## Testing & Verification

### Integration Testing

1. **Setup Lazada test account:**
   - Create Lazada seller account
   - Register app on Lazada Open Platform
   - Complete OAuth flow to get access_token

2. **Test polling manually:**
   ```bash
   LOG_LEVEL=debug pnpm --filter omnichat-service start:dev
   ```

3. **Verify outcomes:**
   - Messages appear in SQS queue with platform='LAZADA'
   - Normalizer processes messages without errors
   - No duplicate messages ingested
   - Rate limiting triggers backoff correctly

---

## Risks & Assumptions

### ✅ Confirmed from API Documentation

1. **API Endpoints:** `/im/session/list` and `/im/message/list` confirmed
2. **Pagination:** Uses `start_time` + `last_session_id`/`last_message_id`
3. **Message Content:** `type` field ("1"=text, "2"=image), `content` is string
4. ⚠️ **No `create_time` field** - must use current time

### ⚠️ Remaining Assumptions

1. **Rate Limiting:** Unknown specific error codes
2. **Region Configuration:** Currently hardcoded to 'sg'
3. **Pagination Performance:** Cannot filter messages by timestamp at API level

---

## Summary

This plan implements Lazada scheduled polling based on **actual Lazada IM API documentation** from Lazada Open Platform.

**Key Deliverables:**
- ✅ Lazada types and error classes (based on actual API response)
- ✅ API methods in LazadaExternalService (`listSessions`, `listMessages`)
- ✅ Full LazadaPoller implementation with correct pagination
- ✅ LazadaChannelMapper for normalization (handles type-based content parsing)

**Key Differences from Shopee/TikTok:**
- Uses `/im/session/list` (not `conversation/list`)
- Pagination via `start_time` + `last_session_id`/`last_message_id`
- Message `content` is string (may be JSON-encoded)
- Message `type` is numeric string ("1"=text, "2"=image)
- No `create_time` field in messages
- Region-specific API base URLs

**Post-Implementation TODO:**
1. Add region configuration per account (currently hardcoded 'sg')
2. Test with actual Lazada seller account
3. Validate message timestamp handling
4. Monitor for rate limit errors and adjust codes if needed
