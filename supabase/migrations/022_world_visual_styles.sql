-- Migration: 022_world_visual_styles.sql
-- Purpose: Add visual style system at world level for image generation consistency
-- Date: 2025-12-17
--
-- VISUAL ARCHITECTURE:
--   World Visual Style (per world) - defines aesthetic baseline
--     └── Character Style (inherits from world, optional overrides)
--
-- This approach provides:
-- - Consistency within context (all Real Life characters share grounded aesthetic)
-- - Meaningful differentiation (Fantasy feels different from Celebrity Sphere)
-- - Expandability (new worlds can have new visual identities)
-- - User expectation alignment (visual style reinforces the world)

-- ============================================================================
-- PHASE 1: ADD VISUAL_STYLE COLUMN TO WORLDS
-- ============================================================================

ALTER TABLE worlds ADD COLUMN IF NOT EXISTS visual_style JSONB DEFAULT '{}'::jsonb;

COMMENT ON COLUMN worlds.visual_style IS 'Visual generation style for this world: base_style, color_palette, rendering, negative_prompts';

-- ============================================================================
-- PHASE 2: UPDATE FOUNDATIONAL WORLDS WITH VISUAL STYLES
-- ============================================================================

-- Real Life: Soft realistic, natural colors, grounded
UPDATE worlds SET visual_style = '{
    "base_style": "soft realistic photography style",
    "color_palette": "natural warm tones, soft earth colors",
    "rendering": "soft natural lighting, shallow depth of field",
    "character_framing": "intimate portrait, eye-level, genuine expression",
    "negative_prompt": "anime, cartoon, fantasy elements, supernatural, oversaturated, harsh lighting"
}'::jsonb
WHERE slug = 'real-life';

-- Celebrity Sphere: Polished realistic, glamorous but vulnerable
UPDATE worlds SET visual_style = '{
    "base_style": "editorial photography style, fashion magazine quality",
    "color_palette": "rich contrast, moody undertones, selective color pop",
    "rendering": "dramatic lighting, bokeh backgrounds, high production value",
    "character_framing": "celebrity portrait, candid backstage moment, real vulnerability beneath polish",
    "negative_prompt": "anime, cartoon, amateur quality, harsh flash, unflattering angles"
}'::jsonb
WHERE slug = 'celebrity-sphere';

-- Historical: Painterly, era-appropriate palette
UPDATE worlds SET visual_style = '{
    "base_style": "painterly illustration, classical portraiture influence",
    "color_palette": "muted period-appropriate colors, sepia undertones available",
    "rendering": "soft diffused lighting, canvas texture subtle, romantic atmosphere",
    "character_framing": "formal portrait composition, period-appropriate pose and expression",
    "negative_prompt": "modern elements, bright neon colors, contemporary clothing, digital artifacts"
}'::jsonb
WHERE slug = 'historical';

-- Near Future: Cinematic sci-fi, neon and chrome
UPDATE worlds SET visual_style = '{
    "base_style": "cinematic sci-fi concept art, blade runner influence",
    "color_palette": "neon accents on dark backgrounds, cyan and magenta highlights, chrome reflections",
    "rendering": "volumetric lighting, atmospheric haze, holographic elements",
    "character_framing": "cinematic portrait, environmental storytelling, technology integration",
    "negative_prompt": "fantasy magic, medieval elements, pastoral scenes, warm cozy lighting"
}'::jsonb
WHERE slug = 'near-future';

-- Fantasy Realms: Anime/illustration style, vibrant and magical
UPDATE worlds SET visual_style = '{
    "base_style": "anime illustration style, fantasy art influence",
    "color_palette": "vibrant saturated colors, magical glow effects, ethereal highlights",
    "rendering": "cel shading optional, dramatic magical lighting, sparkle and particle effects",
    "character_framing": "dynamic anime portrait, expressive eyes, fantasy costume detail",
    "negative_prompt": "photorealistic, mundane settings, modern technology, gritty realism"
}'::jsonb
WHERE slug = 'fantasy-realms';

-- ============================================================================
-- PHASE 3: ADD STYLE_OVERRIDE TO CHARACTERS (for exceptional cases)
-- ============================================================================

ALTER TABLE characters ADD COLUMN IF NOT EXISTS style_override JSONB;

COMMENT ON COLUMN characters.style_override IS 'Optional visual style override when character needs to break world style (e.g., time traveler, crossover character)';

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
DECLARE
    worlds_with_style INTEGER;
BEGIN
    SELECT COUNT(*) INTO worlds_with_style
    FROM worlds
    WHERE visual_style IS NOT NULL AND visual_style != '{}'::jsonb;

    IF worlds_with_style < 5 THEN
        RAISE EXCEPTION 'Migration failed: Expected 5 worlds with visual_style, found %', worlds_with_style;
    END IF;

    RAISE NOTICE 'Migration 022_world_visual_styles completed successfully';
    RAISE NOTICE 'Worlds with visual styles: %', worlds_with_style;
    RAISE NOTICE '';
    RAISE NOTICE 'Visual Style Architecture:';
    RAISE NOTICE '  - Real Life: soft realistic photography';
    RAISE NOTICE '  - Celebrity Sphere: editorial/fashion photography';
    RAISE NOTICE '  - Historical: painterly classical portraiture';
    RAISE NOTICE '  - Near Future: cinematic sci-fi concept art';
    RAISE NOTICE '  - Fantasy Realms: anime/fantasy illustration';
END $$;
