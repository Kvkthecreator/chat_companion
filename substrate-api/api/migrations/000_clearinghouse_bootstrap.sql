-- =============================================================================
-- CLEARINGHOUSE: Bootstrap Migration
-- Purpose: Add Clearinghouse tables to existing YARNNN database
-- Note: Works with existing workspaces and workspace_memberships tables
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- =============================================================================
-- 1. ADD CATALOGS TABLE (if not exists)
-- =============================================================================

CREATE TABLE IF NOT EXISTS catalogs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    default_ai_permissions JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_by TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_catalogs_workspace ON catalogs(workspace_id);

-- =============================================================================
-- 2. ADD RIGHTS SCHEMAS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS rights_schemas (
    id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL,
    field_schema JSONB NOT NULL,
    ai_permission_fields JSONB,
    identifier_fields TEXT[] DEFAULT '{}',
    display_field TEXT DEFAULT 'title',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- =============================================================================
-- 3. ADD RIGHTS ENTITIES TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS rights_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    catalog_id UUID NOT NULL REFERENCES catalogs(id) ON DELETE CASCADE,

    rights_type TEXT NOT NULL REFERENCES rights_schemas(id),
    entity_key TEXT,

    title TEXT NOT NULL,
    content JSONB NOT NULL DEFAULT '{}',
    ai_permissions JSONB DEFAULT '{}',

    rights_holder_info JSONB,
    ownership_chain JSONB DEFAULT '[]',

    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'archived', 'pending', 'disputed', 'draft')),
    verification_status TEXT DEFAULT 'unverified' CHECK (verification_status IN ('unverified', 'pending_verification', 'verified', 'disputed', 'expired')),

    -- Data Architecture fields
    embedding_status TEXT DEFAULT 'pending' CHECK (embedding_status IN ('pending', 'processing', 'ready', 'failed', 'skipped')),
    processing_error TEXT,
    semantic_metadata JSONB DEFAULT '{
        "primary_tags": [],
        "mood": [],
        "energy": null,
        "language": null,
        "explicit_content": false,
        "type_fields": {},
        "custom_tags": [],
        "ai_analysis": null
    }'::jsonb,
    extensions JSONB DEFAULT '{}',

    version INTEGER DEFAULT 1,
    previous_version_id UUID REFERENCES rights_entities(id),

    created_by TEXT NOT NULL,
    updated_by TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),

    UNIQUE(catalog_id, rights_type, entity_key)
);

CREATE INDEX IF NOT EXISTS idx_rights_entities_catalog ON rights_entities(catalog_id);
CREATE INDEX IF NOT EXISTS idx_rights_entities_type ON rights_entities(rights_type);
CREATE INDEX IF NOT EXISTS idx_rights_entities_status ON rights_entities(status) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_rights_entities_embedding_status ON rights_entities(embedding_status);
CREATE INDEX IF NOT EXISTS idx_entities_semantic_tags ON rights_entities USING gin ((semantic_metadata->'primary_tags'));
CREATE INDEX IF NOT EXISTS idx_entities_mood ON rights_entities USING gin ((semantic_metadata->'mood'));

-- =============================================================================
-- 4. ADD GOVERNANCE RULES TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS governance_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    catalog_id UUID NOT NULL REFERENCES catalogs(id) ON DELETE CASCADE,

    name TEXT NOT NULL,
    description TEXT,

    -- Auto-approval settings
    auto_approve_types TEXT[] DEFAULT '{}',
    require_approval_for TEXT[] DEFAULT '{"CREATE", "UPDATE", "DELETE"}',

    -- Voting/review settings
    min_approvals INTEGER DEFAULT 1,
    approval_timeout_hours INTEGER DEFAULT 168,

    is_active BOOLEAN DEFAULT true,

    created_by TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),

    UNIQUE(catalog_id, name)
);

CREATE INDEX IF NOT EXISTS idx_governance_rules_catalog ON governance_rules(catalog_id);

-- =============================================================================
-- 5. ADD PROPOSALS TABLE (for governance workflow)
-- =============================================================================

-- Check if proposals table exists and drop/recreate if schema differs
DO $$
BEGIN
    -- Only create if doesn't exist or has wrong schema
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'proposals' AND column_name = 'catalog_id'
    ) THEN
        -- Create new proposals table for Clearinghouse governance
        CREATE TABLE IF NOT EXISTS clearinghouse_proposals (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            catalog_id UUID NOT NULL REFERENCES catalogs(id) ON DELETE CASCADE,

            proposal_type TEXT NOT NULL CHECK (proposal_type IN ('CREATE', 'UPDATE', 'TRANSFER', 'VERIFY', 'DISPUTE', 'ARCHIVE', 'RESTORE')),
            target_entity_id UUID REFERENCES rights_entities(id) ON DELETE CASCADE,

            payload JSONB DEFAULT '{}',
            proposed_changes JSONB DEFAULT '{}',
            reasoning TEXT,
            priority TEXT DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),

            status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'under_review', 'approved', 'rejected', 'cancelled')),
            auto_approved BOOLEAN DEFAULT false,
            auto_approval_reason TEXT,

            created_by TEXT NOT NULL,
            reviewed_by TEXT,
            review_notes TEXT,

            created_at TIMESTAMPTZ DEFAULT now(),
            reviewed_at TIMESTAMPTZ,
            updated_at TIMESTAMPTZ DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS idx_ch_proposals_catalog ON clearinghouse_proposals(catalog_id);
        CREATE INDEX IF NOT EXISTS idx_ch_proposals_status ON clearinghouse_proposals(status);
        CREATE INDEX IF NOT EXISTS idx_ch_proposals_entity ON clearinghouse_proposals(target_entity_id);
    END IF;
END $$;

-- =============================================================================
-- 6. ADD PROPOSAL COMMENTS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS proposal_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id UUID NOT NULL,

    content TEXT NOT NULL,
    comment_type TEXT DEFAULT 'comment' CHECK (comment_type IN ('comment', 'question', 'concern', 'approval', 'rejection')),

    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_proposal_comments_proposal ON proposal_comments(proposal_id);

-- =============================================================================
-- 7. ADD LICENSES TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS licenses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    rights_entity_id UUID NOT NULL REFERENCES rights_entities(id) ON DELETE CASCADE,
    licensee_workspace_id UUID REFERENCES workspaces(id),
    licensee_external_id TEXT,

    license_type TEXT NOT NULL CHECK (license_type IN ('exclusive', 'non_exclusive', 'sublicensable')),

    terms JSONB NOT NULL DEFAULT '{}',
    territories TEXT[] DEFAULT '{"WORLDWIDE"}',

    start_date DATE NOT NULL,
    end_date DATE,

    status TEXT DEFAULT 'active' CHECK (status IN ('draft', 'pending', 'active', 'expired', 'terminated', 'disputed')),

    usage_limits JSONB,
    usage_count INTEGER DEFAULT 0,

    price_cents INTEGER,
    currency TEXT DEFAULT 'USD',
    billing_type TEXT CHECK (billing_type IN ('one_time', 'subscription', 'usage_based', 'revenue_share')),

    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_licenses_entity ON licenses(rights_entity_id);
CREATE INDEX IF NOT EXISTS idx_licenses_licensee ON licenses(licensee_workspace_id);
CREATE INDEX IF NOT EXISTS idx_licenses_status ON licenses(status);

-- =============================================================================
-- 8. ADD ENTITY TIMELINE TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS entity_timeline (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    rights_entity_id UUID NOT NULL REFERENCES rights_entities(id) ON DELETE CASCADE,

    event_type TEXT NOT NULL,
    event_data JSONB DEFAULT '{}',

    actor TEXT NOT NULL,

    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_entity_timeline_entity ON entity_timeline(rights_entity_id);
CREATE INDEX IF NOT EXISTS idx_entity_timeline_type ON entity_timeline(event_type);

-- =============================================================================
-- 9. ADD REFERENCE ASSETS TABLE (enhanced for Data Architecture)
-- =============================================================================

-- Drop existing reference_assets if it has wrong schema
DROP TABLE IF EXISTS reference_assets CASCADE;

CREATE TABLE reference_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rights_entity_id UUID NOT NULL REFERENCES rights_entities(id) ON DELETE CASCADE,

    asset_type TEXT NOT NULL CHECK (asset_type IN (
        'audio_master', 'audio_preview', 'audio_stem',
        'lyrics', 'sheet_music', 'artwork', 'photo',
        'contract', 'certificate', 'other'
    )),
    filename TEXT NOT NULL,
    mime_type TEXT,
    file_size_bytes BIGINT,

    storage_bucket TEXT NOT NULL DEFAULT 'reference-assets',
    storage_path TEXT NOT NULL,
    is_public BOOLEAN DEFAULT false,

    duration_seconds NUMERIC,
    sample_rate INTEGER,
    channels INTEGER,
    bit_depth INTEGER,

    processing_status TEXT DEFAULT 'uploaded' CHECK (processing_status IN ('uploaded', 'processing', 'ready', 'failed')),
    processing_error TEXT,
    extracted_metadata JSONB DEFAULT '{}',

    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_assets_entity ON reference_assets(rights_entity_id);
CREATE INDEX IF NOT EXISTS idx_assets_type ON reference_assets(asset_type);
CREATE INDEX IF NOT EXISTS idx_assets_status ON reference_assets(processing_status);

-- =============================================================================
-- 10. ADD ENTITY EMBEDDINGS TABLE (pgvector)
-- =============================================================================

CREATE TABLE IF NOT EXISTS entity_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rights_entity_id UUID NOT NULL REFERENCES rights_entities(id) ON DELETE CASCADE,

    embedding_type TEXT NOT NULL CHECK (embedding_type IN (
        'text_description', 'text_lyrics', 'audio_full', 'audio_segment',
        'visual', 'combined'
    )),
    source_asset_id UUID REFERENCES reference_assets(id) ON DELETE SET NULL,

    model_id TEXT NOT NULL,
    model_version TEXT,

    embedding vector(1536),

    segment_index INTEGER DEFAULT 0,
    segment_start_ms INTEGER,
    segment_end_ms INTEGER,

    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_embeddings_entity ON entity_embeddings(rights_entity_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_type ON entity_embeddings(embedding_type);
CREATE INDEX IF NOT EXISTS idx_embeddings_vector_hnsw ON entity_embeddings USING hnsw (embedding vector_cosine_ops);

-- =============================================================================
-- 11. ADD PROCESSING JOBS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS processing_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    job_type TEXT NOT NULL CHECK (job_type IN (
        'embedding_generation', 'asset_analysis', 'metadata_extraction',
        'fingerprint_generation', 'batch_import'
    )),
    rights_entity_id UUID REFERENCES rights_entities(id) ON DELETE CASCADE,
    asset_id UUID REFERENCES reference_assets(id) ON DELETE CASCADE,

    status TEXT DEFAULT 'queued' CHECK (status IN ('queued', 'processing', 'completed', 'failed', 'cancelled')),
    priority INTEGER DEFAULT 0,

    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,

    config JSONB DEFAULT '{}',
    result JSONB,

    created_by TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_jobs_status ON processing_jobs(status, priority DESC, created_at);
CREATE INDEX IF NOT EXISTS idx_jobs_entity ON processing_jobs(rights_entity_id);
CREATE INDEX IF NOT EXISTS idx_jobs_type ON processing_jobs(job_type);

-- =============================================================================
-- 12. HELPER FUNCTIONS
-- =============================================================================

-- Find similar entities by embedding
CREATE OR REPLACE FUNCTION find_similar_entities(
    query_embedding vector(1536),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 10,
    filter_catalog_ids UUID[] DEFAULT NULL,
    filter_rights_types TEXT[] DEFAULT NULL
)
RETURNS TABLE (
    entity_id UUID,
    title TEXT,
    rights_type TEXT,
    catalog_id UUID,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        re.id as entity_id,
        re.title,
        re.rights_type,
        re.catalog_id,
        1 - (ee.embedding <=> query_embedding) as similarity
    FROM entity_embeddings ee
    JOIN rights_entities re ON re.id = ee.rights_entity_id
    WHERE
        re.status = 'active'
        AND re.embedding_status = 'ready'
        AND (filter_catalog_ids IS NULL OR re.catalog_id = ANY(filter_catalog_ids))
        AND (filter_rights_types IS NULL OR re.rights_type = ANY(filter_rights_types))
        AND 1 - (ee.embedding <=> query_embedding) > match_threshold
    ORDER BY ee.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Update embedding status trigger
CREATE OR REPLACE FUNCTION update_entity_embedding_status()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'completed' AND NEW.rights_entity_id IS NOT NULL THEN
        IF NOT EXISTS (
            SELECT 1 FROM processing_jobs
            WHERE rights_entity_id = NEW.rights_entity_id
            AND status IN ('queued', 'processing')
            AND id != NEW.id
        ) THEN
            IF EXISTS (
                SELECT 1 FROM entity_embeddings
                WHERE rights_entity_id = NEW.rights_entity_id
            ) THEN
                UPDATE rights_entities
                SET embedding_status = 'ready', updated_at = now()
                WHERE id = NEW.rights_entity_id;
            END IF;
        END IF;
    ELSIF NEW.status = 'failed' AND NEW.rights_entity_id IS NOT NULL THEN
        IF NEW.retry_count >= NEW.max_retries THEN
            UPDATE rights_entities
            SET embedding_status = 'failed',
                processing_error = NEW.error_message,
                updated_at = now()
            WHERE id = NEW.rights_entity_id;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_embedding_status ON processing_jobs;
CREATE TRIGGER trigger_update_embedding_status
    AFTER UPDATE OF status ON processing_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_entity_embedding_status();

-- =============================================================================
-- 13. SEED RIGHTS SCHEMAS
-- =============================================================================

INSERT INTO rights_schemas (id, display_name, description, category, field_schema, ai_permission_fields, identifier_fields) VALUES
('musical_work', 'Musical Work', 'A musical composition (melody, harmony, lyrics)', 'music',
 '{"type":"object","properties":{"composers":{"type":"array","items":{"type":"string"}},"lyricists":{"type":"array","items":{"type":"string"}},"publishers":{"type":"array","items":{"type":"string"}},"iswc":{"type":"string"},"genres":{"type":"array","items":{"type":"string"}}}}',
 '{"training":{"type":"object"},"generation":{"type":"object"},"commercial":{"type":"object"}}',
 ARRAY['iswc']),

('sound_recording', 'Sound Recording', 'A specific recorded performance of a musical work', 'music',
 '{"type":"object","properties":{"performers":{"type":"array","items":{"type":"string"}},"producer":{"type":"string"},"label":{"type":"string"},"isrc":{"type":"string"},"release_date":{"type":"string","format":"date"},"duration_seconds":{"type":"number"}}}',
 '{"training":{"type":"object"},"generation":{"type":"object"},"commercial":{"type":"object"}}',
 ARRAY['isrc']),

('voice_likeness', 'Voice Likeness', 'The distinctive voice characteristics of an individual', 'voice',
 '{"type":"object","properties":{"individual_name":{"type":"string"},"voice_characteristics":{"type":"array","items":{"type":"string"}},"sample_recordings":{"type":"array","items":{"type":"string"}}}}',
 '{"training":{"type":"object"},"generation":{"type":"object"},"voice":{"type":"object","properties":{"cloning_allowed":{"type":"boolean"},"synthesis_allowed":{"type":"boolean"}}},"commercial":{"type":"object"}}',
 ARRAY[]),

('character_ip', 'Character/Persona', 'A fictional character or public persona', 'character',
 '{"type":"object","properties":{"character_name":{"type":"string"},"franchise":{"type":"string"},"character_traits":{"type":"array","items":{"type":"string"}},"visual_description":{"type":"string"}}}',
 '{"training":{"type":"object"},"generation":{"type":"object"},"commercial":{"type":"object"}}',
 ARRAY[]),

('visual_work', 'Visual Work', 'Artwork, photography, or other visual creative works', 'visual',
 '{"type":"object","properties":{"artist":{"type":"string"},"medium":{"type":"string"},"dimensions":{"type":"string"},"year_created":{"type":"integer"}}}',
 '{"training":{"type":"object"},"generation":{"type":"object"},"commercial":{"type":"object"}}',
 ARRAY[]),

('literary_work', 'Literary Work', 'Written creative works including books, articles, scripts', 'literary',
 '{"type":"object","properties":{"author":{"type":"string"},"isbn":{"type":"string"},"word_count":{"type":"integer"},"genre":{"type":"string"}}}',
 '{"training":{"type":"object"},"generation":{"type":"object"},"commercial":{"type":"object"}}',
 ARRAY['isbn']),

('video_content', 'Video Content', 'Video recordings, films, and multimedia content', 'video',
 '{"type":"object","properties":{"director":{"type":"string"},"duration_seconds":{"type":"number"},"resolution":{"type":"string"},"isan":{"type":"string"}}}',
 '{"training":{"type":"object"},"generation":{"type":"object"},"commercial":{"type":"object"}}',
 ARRAY['isan'])

ON CONFLICT (id) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    field_schema = EXCLUDED.field_schema,
    ai_permission_fields = EXCLUDED.ai_permission_fields,
    updated_at = now();

-- =============================================================================
-- 14. GRANTS
-- =============================================================================

GRANT ALL ON catalogs TO authenticated;
GRANT ALL ON catalogs TO service_role;
GRANT SELECT ON rights_schemas TO authenticated;
GRANT ALL ON rights_schemas TO service_role;
GRANT ALL ON rights_entities TO authenticated;
GRANT ALL ON rights_entities TO service_role;
GRANT ALL ON governance_rules TO authenticated;
GRANT ALL ON governance_rules TO service_role;
GRANT ALL ON clearinghouse_proposals TO authenticated;
GRANT ALL ON clearinghouse_proposals TO service_role;
GRANT ALL ON proposal_comments TO authenticated;
GRANT ALL ON proposal_comments TO service_role;
GRANT ALL ON licenses TO authenticated;
GRANT ALL ON licenses TO service_role;
GRANT ALL ON entity_timeline TO authenticated;
GRANT ALL ON entity_timeline TO service_role;
GRANT ALL ON reference_assets TO authenticated;
GRANT ALL ON reference_assets TO service_role;
GRANT ALL ON entity_embeddings TO authenticated;
GRANT ALL ON entity_embeddings TO service_role;
GRANT ALL ON processing_jobs TO authenticated;
GRANT ALL ON processing_jobs TO service_role;

-- =============================================================================
-- MIGRATION COMPLETE
-- =============================================================================
