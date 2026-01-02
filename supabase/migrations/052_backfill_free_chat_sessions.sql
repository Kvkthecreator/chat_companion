-- Migration: Backfill free chat templates for existing sessions
-- Purpose: Create free chat templates for characters that have free chat sessions
-- and update those sessions to use the new templates

-- Step 1: Create free chat templates for characters that have free chat sessions
-- but don't yet have a free chat template
WITH chars_needing_templates AS (
    SELECT DISTINCT s.character_id, c.name, c.archetype
    FROM sessions s
    JOIN characters c ON c.id = s.character_id
    WHERE s.episode_template_id IS NULL
    AND NOT EXISTS (
        SELECT 1 FROM episode_templates et
        WHERE et.character_id = s.character_id AND et.is_free_chat = TRUE
    )
)
INSERT INTO episode_templates (
    id, character_id, title, slug, situation, opening_line,
    genre, visual_mode, generation_budget, turn_budget,
    episode_cost, is_free_chat, is_default, status, episode_number
)
SELECT
    gen_random_uuid(),
    character_id,
    'Chat with ' || name,
    'free-chat-' || character_id::text,
    'An open conversation with ' || name || '.',
    '',
    'romantic_tension',
    'none',
    0,
    0,  -- turn_budget 0 means open-ended
    0,
    TRUE,
    FALSE,
    'active',
    -1  -- Use -1 to avoid conflict with episode_number unique constraint
FROM chars_needing_templates;

-- Step 2: Update existing free chat sessions to use their character's free chat template
UPDATE sessions s
SET episode_template_id = et.id
FROM episode_templates et
WHERE s.episode_template_id IS NULL
AND et.character_id = s.character_id
AND et.is_free_chat = TRUE;

-- Log results
DO $$
DECLARE
    templates_created INTEGER;
    sessions_updated INTEGER;
BEGIN
    SELECT COUNT(*) INTO templates_created FROM episode_templates WHERE is_free_chat = TRUE;
    SELECT COUNT(*) INTO sessions_updated FROM sessions WHERE episode_template_id IN (
        SELECT id FROM episode_templates WHERE is_free_chat = TRUE
    );
    RAISE NOTICE 'Free chat templates: %, Sessions migrated: %', templates_created, sessions_updated;
END $$;
