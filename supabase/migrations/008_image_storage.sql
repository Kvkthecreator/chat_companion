-- Migration: 008_image_storage
-- Description: Image assets and episode images for scene cards and memories

-- ============================================================================
-- IMAGE_ASSETS table
-- Stores all images used in Fantazy (avatars, expressions, generated scenes)
-- ============================================================================
CREATE TABLE IF NOT EXISTS image_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Type classification
    type TEXT NOT NULL CHECK (type IN ('avatar', 'expression', 'scene')),

    -- Ownership (nullable for system/character assets)
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    character_id UUID REFERENCES characters(id) ON DELETE SET NULL,

    -- Storage
    storage_bucket TEXT NOT NULL DEFAULT 'scenes',
    storage_path TEXT NOT NULL,  -- e.g., "episodes/{episode_id}/{image_id}.png"

    -- Generation metadata (for scene images)
    prompt TEXT,                  -- The prompt used to generate this image
    model_used TEXT,              -- e.g., "gemini-2.0-flash-exp-image-generation"
    generation_params JSONB DEFAULT '{}',  -- width, height, etc.
    latency_ms INTEGER,

    -- Style tags for filtering/organization
    style_tags TEXT[] DEFAULT '{}',  -- e.g., ['anime', 'warm', 'cozy', 'evening']

    -- File metadata
    mime_type TEXT DEFAULT 'image/png',
    file_size_bytes INTEGER,
    width INTEGER,
    height INTEGER,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- EPISODE_IMAGES table (join table)
-- Links images to episodes for scene cards
-- ============================================================================
CREATE TABLE IF NOT EXISTS episode_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    episode_id UUID NOT NULL REFERENCES episodes(id) ON DELETE CASCADE,
    image_id UUID NOT NULL REFERENCES image_assets(id) ON DELETE CASCADE,

    -- Position in episode (for ordering multiple scene cards)
    sequence_index INTEGER NOT NULL DEFAULT 0,

    -- Caption for the scene card (LLM-generated)
    caption TEXT,

    -- Message context (which message triggered this image)
    triggered_by_message_id UUID REFERENCES messages(id) ON DELETE SET NULL,
    trigger_type TEXT CHECK (trigger_type IN ('milestone', 'user_request', 'stage_change', 'episode_start')),

    -- User interaction
    is_memory BOOLEAN DEFAULT FALSE,  -- User starred as a memory
    saved_at TIMESTAMPTZ,             -- When user saved it

    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Ensure unique image per position in episode
    UNIQUE(episode_id, sequence_index)
);

-- ============================================================================
-- CHARACTER_EXPRESSIONS table (future: Level 1 expression variants)
-- Links pre-made expression images to characters
-- ============================================================================
CREATE TABLE IF NOT EXISTS character_expressions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    image_id UUID NOT NULL REFERENCES image_assets(id) ON DELETE CASCADE,

    -- Expression type
    expression TEXT NOT NULL,  -- e.g., 'happy', 'thinking', 'flustered', 'default'

    -- For emotion detection mapping
    emotion_tags TEXT[] DEFAULT '{}',  -- e.g., ['joy', 'excitement'] maps to 'happy'

    is_default BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(character_id, expression)
);

-- ============================================================================
-- Enable RLS
-- ============================================================================
ALTER TABLE image_assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE episode_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE character_expressions ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- IMAGE_ASSETS Policies
-- ============================================================================

-- Users can see their own generated images
CREATE POLICY image_assets_select_own ON image_assets
    FOR SELECT USING (
        user_id IS NULL  -- System/character images are public
        OR auth.uid() = user_id
    );

-- Users can insert their own images (for generated scenes)
CREATE POLICY image_assets_insert_own ON image_assets
    FOR INSERT WITH CHECK (
        auth.uid() = user_id
    );

-- Service role can manage all images
CREATE POLICY image_assets_service ON image_assets
    FOR ALL TO service_role USING (TRUE);

-- ============================================================================
-- EPISODE_IMAGES Policies
-- ============================================================================

-- Users can see episode images for their episodes
CREATE POLICY episode_images_select_own ON episode_images
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM episodes
            WHERE episodes.id = episode_images.episode_id
            AND episodes.user_id = auth.uid()
        )
    );

-- Users can insert episode images for their episodes
CREATE POLICY episode_images_insert_own ON episode_images
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM episodes
            WHERE episodes.id = episode_images.episode_id
            AND episodes.user_id = auth.uid()
        )
    );

-- Users can update their own episode images (for starring as memory)
CREATE POLICY episode_images_update_own ON episode_images
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM episodes
            WHERE episodes.id = episode_images.episode_id
            AND episodes.user_id = auth.uid()
        )
    );

-- ============================================================================
-- CHARACTER_EXPRESSIONS Policies
-- ============================================================================

-- Everyone can see character expressions (they're public character assets)
CREATE POLICY character_expressions_select_all ON character_expressions
    FOR SELECT TO authenticated USING (TRUE);

-- ============================================================================
-- Indexes
-- ============================================================================

-- Image assets
CREATE INDEX IF NOT EXISTS idx_image_assets_user ON image_assets(user_id);
CREATE INDEX IF NOT EXISTS idx_image_assets_character ON image_assets(character_id);
CREATE INDEX IF NOT EXISTS idx_image_assets_type ON image_assets(type);
CREATE INDEX IF NOT EXISTS idx_image_assets_active ON image_assets(is_active) WHERE is_active = TRUE;

-- Episode images
CREATE INDEX IF NOT EXISTS idx_episode_images_episode ON episode_images(episode_id);
CREATE INDEX IF NOT EXISTS idx_episode_images_image ON episode_images(image_id);
CREATE INDEX IF NOT EXISTS idx_episode_images_memories ON episode_images(is_memory) WHERE is_memory = TRUE;

-- Character expressions
CREATE INDEX IF NOT EXISTS idx_character_expressions_character ON character_expressions(character_id);

-- ============================================================================
-- Grants
-- ============================================================================
GRANT SELECT, INSERT ON image_assets TO authenticated;
GRANT ALL ON image_assets TO service_role;

GRANT SELECT, INSERT, UPDATE ON episode_images TO authenticated;
GRANT ALL ON episode_images TO service_role;

GRANT SELECT ON character_expressions TO authenticated;
GRANT ALL ON character_expressions TO service_role;

-- ============================================================================
-- Helper function: Get user's memory images (saved scene cards)
-- ============================================================================
CREATE OR REPLACE FUNCTION get_user_memories(
    p_user_id UUID,
    p_character_id UUID DEFAULT NULL,
    p_limit INTEGER DEFAULT 50
)
RETURNS TABLE (
    image_id UUID,
    episode_id UUID,
    character_id UUID,
    character_name TEXT,
    caption TEXT,
    storage_path TEXT,
    style_tags TEXT[],
    saved_at TIMESTAMPTZ,
    episode_started_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ia.id as image_id,
        ei.episode_id,
        e.character_id,
        c.name as character_name,
        ei.caption,
        ia.storage_path,
        ia.style_tags,
        ei.saved_at,
        e.started_at as episode_started_at
    FROM episode_images ei
    JOIN image_assets ia ON ia.id = ei.image_id
    JOIN episodes e ON e.id = ei.episode_id
    JOIN characters c ON c.id = e.character_id
    WHERE e.user_id = p_user_id
        AND ei.is_memory = TRUE
        AND (p_character_id IS NULL OR e.character_id = p_character_id)
    ORDER BY ei.saved_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION get_user_memories(UUID, UUID, INTEGER) TO authenticated, service_role;

-- ============================================================================
-- Helper function: Get next sequence index for episode images
-- ============================================================================
CREATE OR REPLACE FUNCTION get_next_episode_image_index(p_episode_id UUID)
RETURNS INTEGER AS $$
DECLARE
    next_index INTEGER;
BEGIN
    SELECT COALESCE(MAX(sequence_index) + 1, 0)
    INTO next_index
    FROM episode_images
    WHERE episode_id = p_episode_id;

    RETURN next_index;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION get_next_episode_image_index(UUID) TO authenticated, service_role;
