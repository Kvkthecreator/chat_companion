-- Migration: 020_fresh_start_series_first.sql
-- Purpose: Fresh Start - Clear legacy content, align schema for Series-First architecture
-- Reference: docs/CONTENT_ARCHITECTURE_CANON.md
-- Date: 2025-12-17
--
-- WHAT THIS MIGRATION DOES:
-- 1. Clears ALL content data (messages, sessions, engagements, episode_templates, avatar_kits, characters, worlds, series)
-- 2. Adjusts schema for Series-First production model
-- 3. Prepares clean slate for Series-First scaffolding
--
-- CANON HIERARCHY (Production Flow):
--   World (universe/setting)
--     └── Series (narrative container) ← ENTRY POINT FOR CREATION
--           └── Episode Templates (ordered within series)
--                 └── Anchor Character (one per episode, but character can be in multiple episodes)
--                       └── Character (persona definition)

-- ============================================================================
-- PHASE 1: CLEAR ALL CONTENT DATA
-- ============================================================================
-- Order matters: child tables first, parent tables last

-- Runtime data
TRUNCATE TABLE messages CASCADE;
TRUNCATE TABLE sessions CASCADE;
TRUNCATE TABLE engagements CASCADE;

-- Content data
TRUNCATE TABLE episode_templates CASCADE;
TRUNCATE TABLE avatar_kits CASCADE;
TRUNCATE TABLE characters CASCADE;
TRUNCATE TABLE series CASCADE;
TRUNCATE TABLE worlds CASCADE;

-- Verify counts
DO $$
BEGIN
    RAISE NOTICE 'Content cleared:';
    RAISE NOTICE '  - messages: %', (SELECT COUNT(*) FROM messages);
    RAISE NOTICE '  - sessions: %', (SELECT COUNT(*) FROM sessions);
    RAISE NOTICE '  - engagements: %', (SELECT COUNT(*) FROM engagements);
    RAISE NOTICE '  - episode_templates: %', (SELECT COUNT(*) FROM episode_templates);
    RAISE NOTICE '  - avatar_kits: %', (SELECT COUNT(*) FROM avatar_kits);
    RAISE NOTICE '  - characters: %', (SELECT COUNT(*) FROM characters);
    RAISE NOTICE '  - series: %', (SELECT COUNT(*) FROM series);
    RAISE NOTICE '  - worlds: %', (SELECT COUNT(*) FROM worlds);
END $$;

-- ============================================================================
-- PHASE 2: SCHEMA ADJUSTMENTS FOR SERIES-FIRST
-- ============================================================================

-- 2A: Allow episode_templates.character_id to be NULL (for draft episodes)
-- Per Canon: "Every episode has ONE anchor character" but we allow drafts without anchor
ALTER TABLE episode_templates ALTER COLUMN character_id DROP NOT NULL;

-- 2B: featured_characters array DEFERRED
-- Per Canon: "crossover" series type may feature multiple characters
-- Deferring until crossover content is actually built (Genesis Stage = single anchor)

-- 2C: Ensure series_id is properly indexed (already done in 019, but verify)
CREATE INDEX IF NOT EXISTS idx_episode_templates_series ON episode_templates(series_id);

-- 2D: Add episode_order to series for explicit ordering
-- Already exists from 019, but ensure it's UUID[] not JSONB
-- (019 used UUID[] which is correct)

-- 2E: Add genre to series for filtering
ALTER TABLE series ADD COLUMN IF NOT EXISTS genre VARCHAR(50);
CREATE INDEX IF NOT EXISTS idx_series_genre ON series(genre);

-- ============================================================================
-- PHASE 3: VERIFY SCHEMA STATE
-- ============================================================================

DO $$
DECLARE
    char_id_nullable BOOLEAN;
    series_genre_exists BOOLEAN;
BEGIN
    -- Check character_id is nullable
    SELECT is_nullable = 'YES' INTO char_id_nullable
    FROM information_schema.columns
    WHERE table_name = 'episode_templates' AND column_name = 'character_id';

    -- Check series.genre exists
    SELECT EXISTS (
        SELECT FROM information_schema.columns
        WHERE table_name = 'series' AND column_name = 'genre'
    ) INTO series_genre_exists;

    IF NOT char_id_nullable THEN
        RAISE EXCEPTION 'Migration failed: episode_templates.character_id should be nullable';
    END IF;

    IF NOT series_genre_exists THEN
        RAISE EXCEPTION 'Migration failed: series.genre not added';
    END IF;

    RAISE NOTICE 'Migration 020_fresh_start_series_first completed successfully';
    RAISE NOTICE 'Schema ready for Series-First scaffolding';
END $$;

-- ============================================================================
-- NOTES FOR SCAFFOLD SCRIPT
-- ============================================================================
--
-- Production Flow (Series-First):
--
-- 1. CREATE WORLD
--    INSERT INTO worlds (name, slug, genre, tone, ...)
--
-- 2. CREATE SERIES (within world)
--    INSERT INTO series (title, slug, world_id, series_type, genre, ...)
--
-- 3. CREATE CHARACTERS (can be done alongside or after)
--    INSERT INTO characters (name, slug, world_id, archetype, ...)
--
-- 4. CREATE EPISODE TEMPLATES (within series, referencing character)
--    INSERT INTO episode_templates (
--        series_id,        -- REQUIRED: which series this belongs to
--        character_id,     -- REQUIRED for published: anchor character
--        episode_number,   -- Order within series
--        title, situation, opening_line, episode_frame,
--        dramatic_question, beat_guidance, resolution_types
--    )
--
-- 5. UPDATE series.episode_order with template IDs
--    UPDATE series SET episode_order = ARRAY[ep1_id, ep2_id, ...]
--
-- 6. CREATE AVATAR KITS for characters
--    INSERT INTO avatar_kits (character_id, ...)
--
-- 7. ACTIVATE content
--    UPDATE characters SET status = 'active' WHERE ...
--    UPDATE series SET status = 'active' WHERE ...
