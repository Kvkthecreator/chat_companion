-- Migration: Move starter_prompts from characters to episode_templates
-- Part of EP-01 Episode-First Pivot cleanup
--
-- This migration:
-- 1. Adds starter_prompts column to episode_templates
-- 2. Migrates existing starter_prompts from characters to their default episode_templates
-- 3. Removes starter_prompts and example_messages from characters table

-- Step 1: Add starter_prompts to episode_templates if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'episode_templates' AND column_name = 'starter_prompts'
    ) THEN
        ALTER TABLE episode_templates ADD COLUMN starter_prompts TEXT[] DEFAULT '{}';
    END IF;
END $$;

-- Step 2: Migrate existing starter_prompts from characters to their default episode_templates
-- Only update episode_templates where the character has starter_prompts
UPDATE episode_templates et
SET starter_prompts = c.starter_prompts
FROM characters c
WHERE et.character_id = c.id
  AND et.is_default = TRUE
  AND c.starter_prompts IS NOT NULL
  AND array_length(c.starter_prompts, 1) > 0
  AND (et.starter_prompts IS NULL OR array_length(et.starter_prompts, 1) = 0);

-- Step 3: For episode_templates without starter_prompts, use opening_line as default
UPDATE episode_templates
SET starter_prompts = ARRAY[opening_line]
WHERE (starter_prompts IS NULL OR array_length(starter_prompts, 1) = 0)
  AND opening_line IS NOT NULL
  AND opening_line != '';

-- Step 4: Drop starter_prompts and example_messages from characters table
-- These fields are no longer used - all conversation ignition data lives on episode_templates
ALTER TABLE characters DROP COLUMN IF EXISTS starter_prompts;
ALTER TABLE characters DROP COLUMN IF EXISTS example_messages;

-- Add comment explaining the change
COMMENT ON COLUMN episode_templates.starter_prompts IS 'Alternative opening line suggestions for UI. Moved from characters table as part of EP-01 Episode-First Pivot.';
