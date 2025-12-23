-- Migration: Drop legacy visual generation columns
-- Date: 2024-12-23
-- Purpose: Complete hardening to Ticket + Moments model
--
-- Removed fields (superseded by visual_mode + generation_budget + episode_cost):
-- - auto_scene_mode: replaced by visual_mode
-- - scene_interval: rhythmic mode removed (semantic triggers only)
-- - spark_cost_per_scene: costs now included in episode_cost
-- - arc_hints: never used in prompt generation
-- - beat_guidance: never used in prompt generation
--
-- Reference: docs/monetization/MONETIZATION_v2.0.md

-- Drop legacy visual generation columns from episode_templates
ALTER TABLE episode_templates DROP COLUMN IF EXISTS auto_scene_mode;
ALTER TABLE episode_templates DROP COLUMN IF EXISTS scene_interval;
ALTER TABLE episode_templates DROP COLUMN IF EXISTS spark_cost_per_scene;

-- Drop unused episode dynamics columns
ALTER TABLE episode_templates DROP COLUMN IF EXISTS arc_hints;
ALTER TABLE episode_templates DROP COLUMN IF EXISTS beat_guidance;
ALTER TABLE episode_templates DROP COLUMN IF EXISTS fade_hints;

-- Log migration
DO $$
BEGIN
    RAISE NOTICE 'Migration 041: Dropped legacy visual columns (auto_scene_mode, scene_interval, spark_cost_per_scene) and unused dynamics columns (arc_hints, beat_guidance, fade_hints)';
    RAISE NOTICE 'Visual generation now uses: visual_mode, generation_budget, episode_cost (Ticket + Moments model)';
END
$$;
