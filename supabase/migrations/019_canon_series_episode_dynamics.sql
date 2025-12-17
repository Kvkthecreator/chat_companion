-- Migration: 019_canon_series_episode_dynamics.sql
-- Purpose: Implement Canon Content Architecture - Series and Episode Dynamics
-- Reference: docs/implementation/CANON_IMPLEMENTATION_PLAN.md
-- Date: 2025-12-17

-- ============================================================================
-- PHASE 1A: Create Series Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS series (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Core identity
    title TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    description TEXT,
    tagline TEXT,  -- Short hook for discovery UI

    -- Relationships
    world_id UUID REFERENCES worlds(id) ON DELETE SET NULL,

    -- Series taxonomy (per GLOSSARY.md)
    series_type VARCHAR(20) DEFAULT 'standalone'
        CHECK (series_type IN ('standalone', 'serial', 'anthology', 'crossover')),

    -- Content organization
    featured_characters UUID[] DEFAULT '{}',  -- Array of character IDs for crossover series
    episode_order UUID[] DEFAULT '{}',        -- Ordered array of episode_template IDs
    total_episodes INTEGER DEFAULT 0,

    -- Visual assets
    cover_image_url TEXT,
    thumbnail_url TEXT,

    -- Publishing state
    status VARCHAR(20) DEFAULT 'draft'
        CHECK (status IN ('draft', 'active', 'archived', 'featured')),
    is_featured BOOLEAN DEFAULT false,
    featured_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for series
CREATE INDEX IF NOT EXISTS idx_series_world ON series(world_id);
CREATE INDEX IF NOT EXISTS idx_series_status ON series(status);
CREATE INDEX IF NOT EXISTS idx_series_featured ON series(is_featured, featured_at DESC) WHERE is_featured = true;
CREATE INDEX IF NOT EXISTS idx_series_type ON series(series_type);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_series_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS series_updated_at ON series;
CREATE TRIGGER series_updated_at
    BEFORE UPDATE ON series
    FOR EACH ROW
    EXECUTE FUNCTION update_series_updated_at();

-- RLS policies for series (public read, authenticated manage)
ALTER TABLE series ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS series_select_public ON series;
CREATE POLICY series_select_public ON series
    FOR SELECT
    TO authenticated
    USING (status IN ('active', 'featured'));

-- ============================================================================
-- PHASE 1B: Add Episode Dynamics Columns to episode_templates
-- ============================================================================

-- Add series relationship
ALTER TABLE episode_templates
    ADD COLUMN IF NOT EXISTS series_id UUID REFERENCES series(id) ON DELETE SET NULL;

-- Add episode dynamics (per EPISODE_DYNAMICS_CANON.md)
ALTER TABLE episode_templates
    ADD COLUMN IF NOT EXISTS dramatic_question TEXT;

ALTER TABLE episode_templates
    ADD COLUMN IF NOT EXISTS beat_guidance JSONB DEFAULT '{}';

-- Resolution types array (per Ring Model)
ALTER TABLE episode_templates
    ADD COLUMN IF NOT EXISTS resolution_types TEXT[] DEFAULT ARRAY['positive', 'neutral', 'negative'];

-- Episode fade hints
ALTER TABLE episode_templates
    ADD COLUMN IF NOT EXISTS fade_hints JSONB DEFAULT '{}';

-- Indexes for new columns
CREATE INDEX IF NOT EXISTS idx_episode_templates_series ON episode_templates(series_id);
CREATE INDEX IF NOT EXISTS idx_episode_templates_beat_guidance ON episode_templates USING GIN(beat_guidance);

-- ============================================================================
-- PHASE 1C: Add Session State Tracking
-- ============================================================================

-- Add session state (per GLOSSARY.md Session States)
ALTER TABLE sessions
    ADD COLUMN IF NOT EXISTS session_state VARCHAR(20) DEFAULT 'active'
    CHECK (session_state IN ('active', 'paused', 'faded', 'complete'));

-- Add resolution tracking
ALTER TABLE sessions
    ADD COLUMN IF NOT EXISTS resolution_type VARCHAR(20)
    CHECK (resolution_type IS NULL OR resolution_type IN ('positive', 'neutral', 'negative', 'surprise', 'faded'));

-- Add fade metadata
ALTER TABLE sessions
    ADD COLUMN IF NOT EXISTS fade_metadata JSONB DEFAULT '{}';

-- Index for session state queries
CREATE INDEX IF NOT EXISTS idx_sessions_state ON sessions(session_state);
CREATE INDEX IF NOT EXISTS idx_sessions_user_state ON sessions(user_id, session_state);

-- ============================================================================
-- PHASE 1D: Update characters table for primary_series
-- ============================================================================

ALTER TABLE characters
    ADD COLUMN IF NOT EXISTS primary_series_id UUID REFERENCES series(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_characters_primary_series ON characters(primary_series_id);

-- ============================================================================
-- PHASE 1E: Function to update series episode count
-- ============================================================================

CREATE OR REPLACE FUNCTION update_series_episode_count()
RETURNS TRIGGER AS $$
BEGIN
    -- Update count when episode is added/removed from series
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        IF NEW.series_id IS NOT NULL THEN
            UPDATE series
            SET total_episodes = (
                SELECT COUNT(*) FROM episode_templates
                WHERE series_id = NEW.series_id AND status = 'active'
            ),
            updated_at = NOW()
            WHERE id = NEW.series_id;
        END IF;

        -- Handle case where series_id changed
        IF TG_OP = 'UPDATE' AND OLD.series_id IS NOT NULL AND OLD.series_id != NEW.series_id THEN
            UPDATE series
            SET total_episodes = (
                SELECT COUNT(*) FROM episode_templates
                WHERE series_id = OLD.series_id AND status = 'active'
            ),
            updated_at = NOW()
            WHERE id = OLD.series_id;
        END IF;
    END IF;

    IF TG_OP = 'DELETE' THEN
        IF OLD.series_id IS NOT NULL THEN
            UPDATE series
            SET total_episodes = (
                SELECT COUNT(*) FROM episode_templates
                WHERE series_id = OLD.series_id AND status = 'active'
            ),
            updated_at = NOW()
            WHERE id = OLD.series_id;
        END IF;
    END IF;

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS episode_templates_series_count ON episode_templates;
CREATE TRIGGER episode_templates_series_count
    AFTER INSERT OR UPDATE OR DELETE ON episode_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_series_episode_count();

-- ============================================================================
-- VERIFICATION: Check migration success
-- ============================================================================

DO $$
DECLARE
    series_exists BOOLEAN;
    series_id_col BOOLEAN;
    dramatic_q_col BOOLEAN;
    session_state_col BOOLEAN;
BEGIN
    -- Check series table
    SELECT EXISTS (
        SELECT FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'series'
    ) INTO series_exists;

    -- Check episode_templates columns
    SELECT EXISTS (
        SELECT FROM information_schema.columns
        WHERE table_name = 'episode_templates' AND column_name = 'series_id'
    ) INTO series_id_col;

    SELECT EXISTS (
        SELECT FROM information_schema.columns
        WHERE table_name = 'episode_templates' AND column_name = 'dramatic_question'
    ) INTO dramatic_q_col;

    -- Check sessions columns
    SELECT EXISTS (
        SELECT FROM information_schema.columns
        WHERE table_name = 'sessions' AND column_name = 'session_state'
    ) INTO session_state_col;

    IF NOT series_exists THEN
        RAISE EXCEPTION 'Migration failed: series table not created';
    END IF;

    IF NOT series_id_col THEN
        RAISE EXCEPTION 'Migration failed: series_id column not added to episode_templates';
    END IF;

    IF NOT dramatic_q_col THEN
        RAISE EXCEPTION 'Migration failed: dramatic_question column not added to episode_templates';
    END IF;

    IF NOT session_state_col THEN
        RAISE EXCEPTION 'Migration failed: session_state column not added to sessions';
    END IF;

    RAISE NOTICE 'Migration 019_canon_series_episode_dynamics completed successfully';
END $$;
