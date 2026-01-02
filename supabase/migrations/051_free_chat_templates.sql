-- Migration: Add is_free_chat flag to episode_templates
-- Purpose: Enable unified template model where free chat uses auto-generated templates
-- instead of having episode_template_id = NULL

-- Add flag to distinguish free chat templates
ALTER TABLE episode_templates
ADD COLUMN IF NOT EXISTS is_free_chat BOOLEAN NOT NULL DEFAULT FALSE;

-- Index for efficient lookup of free chat templates by character
CREATE INDEX IF NOT EXISTS idx_episode_templates_free_chat
ON episode_templates(character_id, is_free_chat)
WHERE is_free_chat = TRUE;

-- Add comment for documentation
COMMENT ON COLUMN episode_templates.is_free_chat IS
'System-generated template for free chat mode. Hidden from episode discovery. One per character.';
