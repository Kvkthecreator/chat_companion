-- Migration: Consolidate backstory fields and remove deprecated fields
-- Date: 2024-12-23
-- Purpose:
--   - Merge short_backstory and full_backstory into single "backstory" field
--   - Remove current_stressor (episode situation now conveys emotional state)
--   - Remove life_arc (backstory + archetype + genre doctrine provide character depth)
--
-- Rationale:
--   EP-01 Episode-First Pivot simplifies character data model:
--   - Characters define WHO (persona, backstory, preferences)
--   - Episodes define WHAT (situation, emotional context)
--   - This reduces redundancy and makes data influence on prompts more transparent

-- Step 1: Add new backstory column (nullable initially)
ALTER TABLE characters ADD COLUMN IF NOT EXISTS backstory TEXT;

-- Step 2: Migrate data - prefer full_backstory, fall back to short_backstory
-- If both exist, concatenate with full_backstory taking precedence
UPDATE characters
SET backstory = COALESCE(
    CASE
        WHEN full_backstory IS NOT NULL AND short_backstory IS NOT NULL
        THEN full_backstory
        WHEN full_backstory IS NOT NULL
        THEN full_backstory
        WHEN short_backstory IS NOT NULL
        THEN short_backstory
        ELSE NULL
    END
);

-- Step 3: Drop deprecated columns
-- Note: We drop these columns after data migration to avoid data loss
-- Keeping these commented out initially for safety - uncomment after verifying migration
-- ALTER TABLE characters DROP COLUMN IF EXISTS short_backstory;
-- ALTER TABLE characters DROP COLUMN IF EXISTS full_backstory;
-- ALTER TABLE characters DROP COLUMN IF EXISTS current_stressor;
-- ALTER TABLE characters DROP COLUMN IF EXISTS life_arc;

-- Add comments for documentation
COMMENT ON COLUMN characters.backstory IS 'Merged from short_backstory and full_backstory. Character history and context used in system prompt.';

-- Log migration
DO $$
BEGIN
    RAISE NOTICE 'Migration 039_consolidate_backstory_fields completed.';
    RAISE NOTICE 'Data has been migrated from short_backstory/full_backstory to backstory.';
    RAISE NOTICE 'Deprecated columns (short_backstory, full_backstory, current_stressor, life_arc) are preserved for rollback safety.';
    RAISE NOTICE 'After verifying the migration, run a follow-up migration to drop the deprecated columns.';
END
$$;
