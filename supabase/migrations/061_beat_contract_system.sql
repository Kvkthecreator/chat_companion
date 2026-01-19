-- Migration: 061_beat_contract_system.sql
-- ADR-009: Beat Contract System
--
-- Adds beats column to episode_templates for defining narrative beats
-- that characters must deliver, with integrated choice points.

-- Add beats JSONB column to episode_templates
-- This replaces the turn-based choice_points with a more sophisticated
-- beat contract system where characters are instructed to deliver specific
-- narrative moments, and choices surface when beats are detected.
ALTER TABLE episode_templates
ADD COLUMN IF NOT EXISTS beats JSONB DEFAULT '[]'::jsonb;

-- Add comment explaining the structure
COMMENT ON COLUMN episode_templates.beats IS 'ADR-009: Beat definitions with character instructions and optional choice points. Structure: [{id, description, character_instruction, target_turn, deadline_turn, detection_type, detection_criteria, choice_point?, requires_beat?, requires_flag?}]';

-- Add beat tracking to sessions.director_state
-- This is handled in application code since director_state is already JSONB
-- Structure will include: director_state.beats.{beat_id}.{status, delivered_at_turn, detected_at_turn, choice_pending}

-- Create index for querying episodes with beats
CREATE INDEX IF NOT EXISTS idx_episode_templates_has_beats
ON episode_templates ((beats != '[]'::jsonb))
WHERE beats IS NOT NULL AND beats != '[]'::jsonb;

-- Helper function to check if an episode has active beats
CREATE OR REPLACE FUNCTION has_beats(episode_template_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM episode_templates
        WHERE id = episode_template_id
        AND beats IS NOT NULL
        AND beats != '[]'::jsonb
        AND jsonb_array_length(beats) > 0
    );
END;
$$ LANGUAGE plpgsql STABLE;

-- Migrate existing choice_points to beats format (optional, for existing data)
-- This creates corresponding beats for any existing choice_points
-- Run this manually for specific series after review:
--
-- UPDATE episode_templates
-- SET beats = (
--     SELECT jsonb_agg(
--         jsonb_build_object(
--             'id', cp->>'id' || '_beat',
--             'description', 'Character delivers the ' || (cp->>'id') || ' moment',
--             'character_instruction', 'Work toward this moment: ' || (cp->>'prompt'),
--             'target_turn', (regexp_replace(cp->>'trigger', 'turn:', ''))::int,
--             'deadline_turn', (regexp_replace(cp->>'trigger', 'turn:', ''))::int + 2,
--             'detection_type', 'automatic',
--             'detection_criteria', '',
--             'choice_point', cp
--         )
--     )
--     FROM jsonb_array_elements(choice_points) cp
-- )
-- WHERE choice_points IS NOT NULL
-- AND choice_points != '[]'::jsonb
-- AND series_id = 'YOUR_SERIES_ID';
