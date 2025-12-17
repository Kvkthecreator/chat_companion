-- Migration: 023_seed_kworld.sql
-- Purpose: Add K-World as a foundational world for K-Drama/K-Culture content
-- Date: 2025-12-17
--
-- K-WORLD PHILOSOPHY:
-- Not just "Korean characters" — the specific storytelling grammar of K-drama.
-- Heightened emotion, visual beauty, fate-driven encounters, and the tension
-- between duty and desire. Distinct tropes (wrist grab, contract love, back hug)
-- and social dynamics (sunbae/hoobae, agency control, chaebol expectations).

-- ============================================================================
-- K-WORLD: K-Drama / K-Culture
-- ============================================================================

INSERT INTO worlds (
    id,
    name,
    slug,
    description,
    default_scenes,
    tone,
    ambient_details,
    metadata,
    visual_style,
    is_active
) VALUES (
    'a0000000-0000-0000-0000-000000000006'::uuid,
    'K-World',
    'k-world',
    'The aesthetic and emotional language of Korean drama and culture. Idols, actors, chaebols, contract relationships, fate-driven encounters. Heightened emotion, visual beauty, and the tension between duty and desire.',
    ARRAY[
        'rooftop of entertainment company building',
        'convenience store at 3am',
        'practice room after hours',
        'han river at night',
        'pojangmacha (tent bar)',
        'airport departure gate',
        'recording studio',
        'quiet cafe in Bukchon',
        'hospital corridor',
        'penthouse apartment'
    ],
    'heightened-romantic',
    '{
        "setting_type": "transparent",
        "time_period": "present_day",
        "technology_level": "modern",
        "magic_level": "none",
        "tropes": [
            "wrist_grab",
            "piggyback_ride",
            "umbrella_sharing",
            "contract_relationship",
            "rich_heir_ordinary_person",
            "childhood_connection",
            "near_kiss_interrupted",
            "back_hug",
            "protective_declaration",
            "watching_sleep"
        ],
        "social_dynamics": [
            "sunbae_hoobae_hierarchy",
            "agency_control",
            "chaebol_family_expectations",
            "public_vs_private_self",
            "scandal_culture",
            "netizen_surveillance"
        ],
        "notes": "K-drama storytelling grammar. Heightened melodrama, fate-driven romance, visual beauty. Characters often navigate duty vs desire, public image vs authentic self."
    }'::jsonb,
    '{
        "genesis_stage": true,
        "priority": 3,
        "sub_types": ["idol_romance", "chaebol_drama", "slice_of_life_korean", "historical_sageuk"]
    }'::jsonb,
    '{
        "base_style": "cinematic K-drama photography, soft glamour",
        "color_palette": "soft pastels with romantic lighting, cherry blossom pinks, night city neons, warm indoor amber",
        "rendering": "beauty lighting, soft focus backgrounds, rain on windows, autumn leaves",
        "character_framing": "idol-grade beauty, expressive close-ups, longing gazes, fashion-forward styling",
        "negative_prompt": "harsh unflattering lighting, western casual style, gritty realism, anime, cartoon"
    }'::jsonb,
    TRUE
)
ON CONFLICT (slug) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    default_scenes = EXCLUDED.default_scenes,
    tone = EXCLUDED.tone,
    ambient_details = EXCLUDED.ambient_details,
    metadata = EXCLUDED.metadata,
    visual_style = EXCLUDED.visual_style;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
DECLARE
    kworld_exists BOOLEAN;
    world_count INTEGER;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM worlds WHERE slug = 'k-world'
    ) INTO kworld_exists;

    SELECT COUNT(*) INTO world_count FROM worlds;

    IF NOT kworld_exists THEN
        RAISE EXCEPTION 'Migration failed: K-World not created';
    END IF;

    RAISE NOTICE 'Migration 023_seed_kworld completed successfully';
    RAISE NOTICE 'Total worlds: %', world_count;
    RAISE NOTICE '';
    RAISE NOTICE 'K-World added with:';
    RAISE NOTICE '  - 10 default scenes (convenience store, han river, etc.)';
    RAISE NOTICE '  - K-drama tropes (wrist grab, back hug, contract love)';
    RAISE NOTICE '  - Social dynamics (sunbae/hoobae, agency control)';
    RAISE NOTICE '  - Visual style: soft glamour, cherry blossom pinks';
END $$;
