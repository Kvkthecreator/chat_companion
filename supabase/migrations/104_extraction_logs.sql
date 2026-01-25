-- =============================================================================
-- Extraction Logs - Observability for Background Memory/Thread Extraction
-- =============================================================================
-- Tracks success/failure of context and thread extraction that runs
-- asynchronously after each conversation message.
--
-- See: docs/implementation/EXTRACTION_OBSERVABILITY.md

CREATE TABLE IF NOT EXISTS extraction_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    conversation_id UUID NOT NULL,

    -- What was extracted
    extraction_type TEXT NOT NULL CHECK (extraction_type IN ('context', 'thread')),

    -- Result
    status TEXT NOT NULL CHECK (status IN ('success', 'failed')),
    error_message TEXT,
    items_extracted INTEGER DEFAULT 0,

    -- Performance
    duration_ms INTEGER,

    -- Timestamp
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for dashboard queries (recent logs, failure lookups)
CREATE INDEX idx_extraction_logs_created ON extraction_logs(created_at DESC);

-- Index for filtering by status (failure analysis)
CREATE INDEX idx_extraction_logs_status ON extraction_logs(status, created_at DESC);

-- Index for per-user debugging
CREATE INDEX idx_extraction_logs_user ON extraction_logs(user_id, created_at DESC);

-- =============================================================================
-- RLS Policies
-- =============================================================================
ALTER TABLE extraction_logs ENABLE ROW LEVEL SECURITY;

-- Service role has full access (for API backend)
CREATE POLICY "Service role can manage extraction_logs"
ON extraction_logs
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Users cannot directly access extraction logs (admin only via API)
-- No authenticated user policy needed

-- =============================================================================
-- Grants
-- =============================================================================
GRANT ALL ON extraction_logs TO service_role;

-- =============================================================================
-- Comments
-- =============================================================================
COMMENT ON TABLE extraction_logs IS
'Observability logs for background memory/thread extraction. Used by admin dashboard to monitor extraction health.';

COMMENT ON COLUMN extraction_logs.extraction_type IS
'Type of extraction: context (memory facts) or thread (ongoing situations)';

COMMENT ON COLUMN extraction_logs.items_extracted IS
'Number of context items or threads extracted (0 if failed or nothing found)';
