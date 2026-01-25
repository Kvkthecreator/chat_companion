# Extraction Observability - Implementation Plan

> Tracking memory and thread extraction health without blocking user experience

**Created:** 2026-01-25
**Status:** Implementation In Progress

---

## Problem Statement

After decoupling memory/thread extraction from the streaming response (using `asyncio.create_task()`), we lost visibility into extraction failures. The system now:
- Returns responses immediately (good UX)
- Extracts context/threads in background (fire-and-forget)
- Logs warnings on failure (but logs have limited retention/queryability)

**Risk:** If extraction silently fails, users will experience "Kiko forgot what I told her" without any way for admins to detect or diagnose the issue.

---

## Solution: DB-Based Extraction Logging

### Why This Approach?

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| **Just logging** | Zero effort | Not queryable, limited retention | ❌ |
| **DB logging** | Queryable, uses existing infra, no new services | Extra DB writes | ✅ Chosen |
| **Prometheus/Datadog** | Rich dashboards, alerting | New infra, cost, overkill for scale | ❌ Later |

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Background Extraction                     │
│  _background_extraction() in conversation.py                │
├─────────────────────────────────────────────────────────────┤
│  1. Extract context (LLM call)                              │
│  2. Save context items                                       │
│  3. Extract threads (LLM call)                              │
│  4. Log result to extraction_logs table  ← NEW              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    extraction_logs table                     │
│  - user_id, conversation_id                                 │
│  - extraction_type (context | thread)                       │
│  - status (success | failed)                                │
│  - error_message, items_extracted, duration_ms              │
│  - created_at                                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Admin Dashboard                           │
│  /admin/extraction page (restricted by email allowlist)     │
│  - Failure rate (24h, 7d)                                   │
│  - Recent failures with error messages                      │
│  - Extraction volume trends                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation

### 1. Database Migration

**File:** `supabase/migrations/104_extraction_logs.sql`

```sql
CREATE TABLE extraction_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    conversation_id UUID NOT NULL,
    extraction_type TEXT NOT NULL CHECK (extraction_type IN ('context', 'thread')),
    status TEXT NOT NULL CHECK (status IN ('success', 'failed')),
    error_message TEXT,
    items_extracted INTEGER DEFAULT 0,
    duration_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX idx_extraction_logs_created ON extraction_logs(created_at DESC);
CREATE INDEX idx_extraction_logs_status ON extraction_logs(status, created_at DESC);
CREATE INDEX idx_extraction_logs_user ON extraction_logs(user_id, created_at DESC);

-- Cleanup: Auto-delete logs older than 30 days (optional, via cron)
-- Or rely on manual cleanup query
```

### 2. Backend Changes

**File:** `api/api/src/app/services/conversation.py`

Update `_background_extraction()` to log results:
- Record start time
- Try extraction, catch errors
- Insert log record with status, duration, item count

### 3. API Endpoint

**File:** `api/api/src/app/routes/admin.py`

New endpoint: `GET /admin/extraction-stats`
- Returns failure rates, recent failures, volume trends
- Protected by existing `is_admin_email()` check

### 4. Frontend Page

**File:** `web/src/app/admin/extraction/page.tsx`

Simple dashboard showing:
- Success/failure rates (24h, 7d)
- Recent failures table with error messages
- Volume chart (extractions per day)

Access controlled by same mechanism as `/admin` page (API returns 403 for non-admins).

---

## Queries for Observability

### Failure Rate (Last 7 Days)
```sql
SELECT
    DATE(created_at) as date,
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE status = 'failed') as failed,
    ROUND(COUNT(*) FILTER (WHERE status = 'failed') * 100.0 / COUNT(*), 1) as failure_pct
FROM extraction_logs
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY 1
ORDER BY 1 DESC;
```

### Recent Failures
```sql
SELECT
    el.created_at,
    el.extraction_type,
    el.error_message,
    el.duration_ms,
    u.display_name
FROM extraction_logs el
JOIN users u ON u.id = el.user_id
WHERE el.status = 'failed'
ORDER BY el.created_at DESC
LIMIT 20;
```

### Extraction Volume by Type
```sql
SELECT
    DATE(created_at) as date,
    extraction_type,
    COUNT(*) as count,
    AVG(items_extracted) as avg_items,
    AVG(duration_ms) as avg_duration_ms
FROM extraction_logs
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY 1, 2
ORDER BY 1 DESC, 2;
```

---

## Future Enhancements

If extraction failures become a significant issue:

1. **Alerting**: Query failure rate in scheduler job, send Slack/email if > threshold
2. **Retry Queue**: On failure, insert into `jobs` table for retry (uses existing worker)
3. **User Impact**: Track "messages since last successful extraction" to identify affected users

---

## Files Changed

- `supabase/migrations/104_extraction_logs.sql` - New table
- `api/api/src/app/services/conversation.py` - Log extraction results
- `api/api/src/app/routes/admin.py` - New stats endpoint
- `web/src/app/admin/extraction/page.tsx` - New dashboard page
- `web/src/lib/api/client.ts` - API client for new endpoint
- `web/src/types/index.ts` - TypeScript types
