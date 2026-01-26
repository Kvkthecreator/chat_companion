-- =============================================================================
-- Artifacts - Memory Output Modality
-- =============================================================================
-- Artifacts are structured syntheses of memory data, rendered in companion voice.
-- They are STORED (first-class citizens) and regenerated on meaningful updates.
--
-- See: docs/analysis/ARTIFACT_LAYER_ANALYSIS.md

-- =============================================================================
-- Artifact Types Enum
-- =============================================================================

CREATE TYPE artifact_type AS ENUM (
    'thread_journey',      -- Timeline + insights for a specific thread
    'domain_health',       -- Overview of threads in a domain
    'communication',       -- How the user communicates
    'relationship'         -- Overall companion relationship summary
);

-- =============================================================================
-- Artifacts Table
-- =============================================================================
-- Stores generated artifacts. Regenerated when underlying data changes meaningfully.

CREATE TABLE artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Type and reference
    artifact_type artifact_type NOT NULL,

    -- For thread_journey: references a specific thread
    thread_id UUID REFERENCES user_context(id) ON DELETE CASCADE,

    -- For domain_health: references a domain
    domain TEXT,

    -- Generated content
    title TEXT NOT NULL,
    sections JSONB NOT NULL,
    -- sections structure:
    -- [
    --   {"type": "header", "content": {...}},
    --   {"type": "timeline", "events": [...]},
    --   {"type": "observations", "content": "..."},
    --   {"type": "key_details", "items": [...]}
    -- ]

    companion_voice TEXT,  -- Overall companion reflection

    -- Data provenance (for transparency and cache invalidation)
    data_sources JSONB NOT NULL DEFAULT '[]',
    -- ["thread:job_search", "messages:34", "patterns:2"]

    data_snapshot_hash TEXT,  -- Hash of source data for change detection

    -- Availability/validity
    is_meaningful BOOLEAN NOT NULL DEFAULT TRUE,  -- False if insufficient data
    min_data_reason TEXT,  -- Why not meaningful (if applicable)

    -- Timestamps
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,  -- Optional: when artifact should be regenerated
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- Indexes
-- =============================================================================

-- Fast lookup of user's artifacts by type
CREATE INDEX idx_artifacts_user_type ON artifacts(user_id, artifact_type);

-- For thread journey artifacts
CREATE INDEX idx_artifacts_thread ON artifacts(thread_id) WHERE thread_id IS NOT NULL;

-- For domain health artifacts
CREATE INDEX idx_artifacts_domain ON artifacts(user_id, domain) WHERE domain IS NOT NULL;

-- For finding stale artifacts
CREATE INDEX idx_artifacts_generated ON artifacts(generated_at);

-- Unique constraints for artifact types
-- Only one artifact per thread
CREATE UNIQUE INDEX idx_artifacts_unique_thread
ON artifacts(user_id, artifact_type, thread_id)
WHERE artifact_type = 'thread_journey' AND thread_id IS NOT NULL;

-- Only one artifact per domain
CREATE UNIQUE INDEX idx_artifacts_unique_domain
ON artifacts(user_id, artifact_type, domain)
WHERE artifact_type = 'domain_health' AND domain IS NOT NULL;

-- Only one communication profile per user
CREATE UNIQUE INDEX idx_artifacts_unique_communication
ON artifacts(user_id, artifact_type)
WHERE artifact_type = 'communication';

-- Only one relationship summary per user
CREATE UNIQUE INDEX idx_artifacts_unique_relationship
ON artifacts(user_id, artifact_type)
WHERE artifact_type = 'relationship';

-- =============================================================================
-- Artifact Events Table (for Thread Journey timeline)
-- =============================================================================
-- Tracks significant events/moments for threads to build journey artifacts.
-- Events are created during extraction when notable things happen.

CREATE TABLE artifact_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    thread_id UUID REFERENCES user_context(id) ON DELETE CASCADE,

    -- Event details
    event_type TEXT NOT NULL,  -- 'phase_change', 'milestone', 'mention', 'update'
    event_date DATE NOT NULL,
    description TEXT NOT NULL,

    -- Source tracking
    source_message_id UUID REFERENCES messages(id) ON DELETE SET NULL,
    source_scheduled_id UUID REFERENCES scheduled_messages(id) ON DELETE SET NULL,

    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_artifact_events_thread ON artifact_events(thread_id, event_date DESC);
CREATE INDEX idx_artifact_events_user ON artifact_events(user_id, event_date DESC);

-- =============================================================================
-- Thread Templates: Add artifact_config column
-- =============================================================================
-- Template-specific artifact configuration

ALTER TABLE thread_templates
ADD COLUMN IF NOT EXISTS artifact_config JSONB DEFAULT '{}';
-- Structure:
-- {
--   "journey_enabled": true,
--   "journey_milestones": ["first_application", "first_interview", "offer_received"],
--   "domain_health_weight": 1.0,
--   "custom_sections": []
-- }

COMMENT ON COLUMN thread_templates.artifact_config IS
'Template-specific artifact configuration: journey milestones, domain weights, custom sections';

-- =============================================================================
-- RLS Policies
-- =============================================================================

ALTER TABLE artifacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE artifact_events ENABLE ROW LEVEL SECURITY;

-- Users can only see their own artifacts
CREATE POLICY "Users can view own artifacts"
ON artifacts FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

-- Service role can manage artifacts
CREATE POLICY "Service role manages artifacts"
ON artifacts FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Users can only see their own events
CREATE POLICY "Users can view own artifact events"
ON artifact_events FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

-- Service role can manage events
CREATE POLICY "Service role manages artifact events"
ON artifact_events FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- =============================================================================
-- Grants
-- =============================================================================

GRANT SELECT ON artifacts TO authenticated;
GRANT ALL ON artifacts TO service_role;

GRANT SELECT ON artifact_events TO authenticated;
GRANT ALL ON artifact_events TO service_role;

-- =============================================================================
-- Trigger for updated_at
-- =============================================================================

CREATE TRIGGER update_artifacts_updated_at
    BEFORE UPDATE ON artifacts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- =============================================================================
-- Comments
-- =============================================================================

COMMENT ON TABLE artifacts IS
'Stored artifacts - structured memory syntheses in companion voice. First-class citizens.';

COMMENT ON COLUMN artifacts.artifact_type IS
'Type: thread_journey, domain_health, communication, relationship';

COMMENT ON COLUMN artifacts.sections IS
'JSON array of artifact sections (header, timeline, observations, key_details, etc.)';

COMMENT ON COLUMN artifacts.companion_voice IS
'Overall companion reflection text for the artifact';

COMMENT ON COLUMN artifacts.data_sources IS
'Array of source references for transparency (e.g., ["thread:job_search", "messages:34"])';

COMMENT ON COLUMN artifacts.data_snapshot_hash IS
'Hash of source data at generation time - used for cache invalidation';

COMMENT ON COLUMN artifacts.is_meaningful IS
'False if insufficient data exists for a meaningful artifact';

COMMENT ON TABLE artifact_events IS
'Timeline events for threads - used to build journey artifacts';

COMMENT ON COLUMN artifact_events.event_type IS
'Event type: phase_change, milestone, mention, update';
