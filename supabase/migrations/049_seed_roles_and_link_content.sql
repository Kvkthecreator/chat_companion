-- Migration: 049_seed_roles_and_link_content.sql
-- Purpose: Seed roles for existing series and link episode_templates to roles
-- Related: ADR-004 User Character & Role Abstraction
-- Created: 2025-01-01
--
-- This migration completes the Role architecture by:
-- 1. Creating roles for each series (one role per series, matching its canonical character)
-- 2. Linking all episode_templates to their series' role
-- 3. Mapping canonical character archetypes to user character archetypes for compatibility
--
-- Architecture:
--   Series → has one → Role (the archetype slot)
--   Role → defines → required archetype + compatible archetypes
--   EpisodeTemplate → references → Role (via role_id)
--   Character (canonical or user-created) → can fill → Role (if archetype compatible)

-- ============================================================================
-- PART 1: ARCHETYPE MAPPING
-- ============================================================================
-- Canonical characters have legacy archetypes (rebel, golden_girl, mysterious, etc.)
-- User characters use simplified archetypes (warm_supportive, playful_teasing, etc.)
--
-- This mapping defines which user archetypes can play roles designed for each
-- canonical character archetype.

-- Create a temporary mapping table for the migration
CREATE TEMP TABLE archetype_mapping (
    canonical_archetype TEXT PRIMARY KEY,
    user_archetype TEXT NOT NULL,
    compatible_user_archetypes TEXT[] DEFAULT '{}'
);

INSERT INTO archetype_mapping (canonical_archetype, user_archetype, compatible_user_archetypes) VALUES
    -- Warm/nurturing archetypes
    ('caregiver', 'warm_supportive', ARRAY['playful_teasing']),
    ('soft_intellectual', 'warm_supportive', ARRAY['mysterious_reserved']),
    ('golden_girl', 'playful_teasing', ARRAY['warm_supportive', 'confident_assertive']),

    -- Intense/mysterious archetypes
    ('mysterious', 'mysterious_reserved', ARRAY['intense_passionate']),
    ('brooding', 'mysterious_reserved', ARRAY['intense_passionate']),
    ('cold_exterior_warm_heart', 'mysterious_reserved', ARRAY['intense_passionate', 'warm_supportive']),
    ('wounded_star', 'intense_passionate', ARRAY['mysterious_reserved']),
    ('the_one_who_left', 'intense_passionate', ARRAY['mysterious_reserved']),

    -- Confident/assertive archetypes
    ('rebel', 'confident_assertive', ARRAY['intense_passionate', 'playful_teasing']),
    ('fierce_competitor', 'confident_assertive', ARRAY['intense_passionate']),
    ('returned_protector', 'confident_assertive', ARRAY['intense_passionate', 'warm_supportive']),
    ('charming_deflector', 'playful_teasing', ARRAY['confident_assertive']),
    ('idol_leader', 'confident_assertive', ARRAY['playful_teasing']),

    -- Special/hybrid archetypes (more permissive compatibility)
    ('hometown protector', 'warm_supportive', ARRAY['confident_assertive', 'playful_teasing']),
    ('The One Who Sees You', 'warm_supportive', ARRAY['mysterious_reserved', 'playful_teasing']),
    ('The One You Can''t Read', 'mysterious_reserved', ARRAY['intense_passionate', 'confident_assertive']),
    ('intellectual', 'mysterious_reserved', ARRAY['warm_supportive', 'confident_assertive']),
    ('flirty', 'playful_teasing', ARRAY['confident_assertive', 'warm_supportive']);

-- ============================================================================
-- PART 2: CREATE ROLES FOR EACH SERIES
-- ============================================================================
-- Each series gets one role, named after its canonical character's archetype slot.
-- The role defines what type of character can play in this series.

INSERT INTO roles (id, name, slug, description, archetype, compatible_archetypes, scene_objective, scene_obstacle, scene_tactic)
SELECT
    gen_random_uuid() as id,
    -- Role name based on series context
    CASE
        WHEN s.slug = 'coffee-shop-crush' THEN 'The Barista'
        WHEN s.slug = 'study-partners' THEN 'The Study Partner'
        WHEN s.slug = 'cheerleader-crush' THEN 'The Popular One'
        WHEN s.slug = 'after-class' THEN 'The Teacher''s Pet'
        WHEN s.slug = 'corner-office' THEN 'The Executive'
        WHEN s.slug = 'the-arrangement' THEN 'The Arranged Match'
        WHEN s.slug = 'the-dare' THEN 'The Daring One'
        WHEN s.slug = 'off-limits' THEN 'The Forbidden One'
        WHEN s.slug = 'the-competition' THEN 'The Rival'
        WHEN s.slug = 'room-404' THEN 'The Healer'
        WHEN s.slug = 'second-chance' THEN 'The One Who Left'
        WHEN s.slug = 'academy-secrets' THEN 'The Transfer Student'
        WHEN s.slug = 'penthouse-secrets' THEN 'The Mysterious Neighbor'
        WHEN s.slug = 'k-pop-boy-idol' THEN 'The Idol'
        WHEN s.slug = 'k-campus-encounter' THEN 'The Campus Star'
        WHEN s.slug = 'meeting-k-pop-idol-crush' THEN 'The Star'
        WHEN s.slug = 'fashion-empire-ceo' THEN 'The Designer'
        WHEN s.slug = 'hometown-crush' THEN 'The Hometown Friend'
        WHEN s.slug = 'hometown-crush-m' THEN 'The Hometown Friend'
        WHEN s.slug = 'hometown-crush-f' THEN 'The Hometown Friend'
        ELSE 'The Interest'
    END as name,
    s.slug || '-role' as slug,
    'Primary character role for ' || s.title as description,
    -- Map canonical archetype to user archetype
    COALESCE(am.user_archetype, 'warm_supportive') as archetype,
    -- Compatible archetypes
    COALESCE(am.compatible_user_archetypes, ARRAY['playful_teasing']) as compatible_archetypes,
    -- Scene motivation from first episode (if available)
    (SELECT scene_objective FROM episode_templates WHERE series_id = s.id AND episode_number = 0 LIMIT 1) as scene_objective,
    (SELECT scene_obstacle FROM episode_templates WHERE series_id = s.id AND episode_number = 0 LIMIT 1) as scene_obstacle,
    (SELECT scene_tactic FROM episode_templates WHERE series_id = s.id AND episode_number = 0 LIMIT 1) as scene_tactic
FROM (
    -- Get distinct series with their canonical characters
    SELECT DISTINCT ON (s.id)
        s.id, s.slug, s.title, c.archetype as canonical_archetype
    FROM series s
    JOIN episode_templates et ON et.series_id = s.id
    JOIN characters c ON et.character_id = c.id
    WHERE s.status = 'active'
    ORDER BY s.id, et.episode_number
) s
LEFT JOIN archetype_mapping am ON s.canonical_archetype = am.canonical_archetype
ON CONFLICT (slug) DO UPDATE SET
    archetype = EXCLUDED.archetype,
    compatible_archetypes = EXCLUDED.compatible_archetypes,
    updated_at = NOW();

-- ============================================================================
-- PART 3: LINK EPISODE_TEMPLATES TO ROLES
-- ============================================================================
-- Set role_id on all episode_templates based on their series

UPDATE episode_templates et
SET role_id = r.id
FROM series s
JOIN roles r ON r.slug = s.slug || '-role'
WHERE et.series_id = s.id
  AND et.role_id IS NULL;

-- ============================================================================
-- PART 4: ADD SERIES-ROLE RELATIONSHIP
-- ============================================================================
-- Add role_id to series table for direct reference (optional but cleaner)

ALTER TABLE series
ADD COLUMN IF NOT EXISTS default_role_id UUID REFERENCES roles(id);

-- Link series to their roles
UPDATE series s
SET default_role_id = r.id
FROM roles r
WHERE r.slug = s.slug || '-role'
  AND s.default_role_id IS NULL;

-- Index for role lookup
CREATE INDEX IF NOT EXISTS idx_series_default_role ON series(default_role_id);

-- ============================================================================
-- PART 5: UPDATE CANONICAL CHARACTERS WITH USER-COMPATIBLE ARCHETYPES
-- ============================================================================
-- For canonical characters, ensure their archetype field can be matched
-- against the user archetype system. We add a new field for this mapping.

-- Add mapped_archetype column for compatibility matching
ALTER TABLE characters
ADD COLUMN IF NOT EXISTS mapped_archetype TEXT;

-- Update canonical characters with their mapped archetypes
UPDATE characters c
SET mapped_archetype = am.user_archetype
FROM archetype_mapping am
WHERE c.archetype = am.canonical_archetype
  AND c.is_user_created = FALSE
  AND c.mapped_archetype IS NULL;

-- For user-created characters, mapped_archetype equals archetype
UPDATE characters
SET mapped_archetype = archetype
WHERE is_user_created = TRUE
  AND mapped_archetype IS NULL;

-- Index for archetype-based character queries
CREATE INDEX IF NOT EXISTS idx_characters_mapped_archetype ON characters(mapped_archetype);

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
DECLARE
    roles_count INTEGER;
    episodes_with_role INTEGER;
    episodes_without_role INTEGER;
    series_with_role INTEGER;
BEGIN
    -- Count roles created
    SELECT COUNT(*) INTO roles_count FROM roles;
    RAISE NOTICE 'Roles created: %', roles_count;

    -- Count episodes with role_id set
    SELECT COUNT(*) INTO episodes_with_role
    FROM episode_templates
    WHERE role_id IS NOT NULL;
    RAISE NOTICE 'Episodes with role_id: %', episodes_with_role;

    -- Count episodes still missing role_id
    SELECT COUNT(*) INTO episodes_without_role
    FROM episode_templates et
    JOIN series s ON et.series_id = s.id
    WHERE et.role_id IS NULL AND s.status = 'active';
    RAISE NOTICE 'Active episodes without role_id: %', episodes_without_role;

    -- Count series with default_role_id
    SELECT COUNT(*) INTO series_with_role
    FROM series
    WHERE default_role_id IS NOT NULL;
    RAISE NOTICE 'Series with default_role_id: %', series_with_role;

    -- Assertions
    ASSERT roles_count > 0, 'Should have created at least one role';
    ASSERT episodes_with_role > 0, 'Should have linked episodes to roles';

    RAISE NOTICE '✓ Migration 049_seed_roles_and_link_content completed successfully';
END $$;
