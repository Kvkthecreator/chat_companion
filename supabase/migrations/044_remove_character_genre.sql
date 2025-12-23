-- Migration: Remove genre from characters table
-- Date: 2024-12-23
-- Purpose: ADR-001 - Genre belongs to Story (Series/Episode), not Character
--
-- Decision: Characters define WHO someone is (personality, voice, boundaries).
-- Genre defines WHAT KIND OF STORY they're in. These are orthogonal concerns.
--
-- Genre is now:
-- - Stored on: series.genre, episode_templates.genre
-- - Injected by: DirectorGuidance.to_prompt_section() at runtime
--
-- See: docs/decisions/ADR-001-genre-architecture.md

-- Drop genre column from characters
ALTER TABLE characters DROP COLUMN IF EXISTS genre;

-- Log migration
DO $$
BEGIN
    RAISE NOTICE 'Migration 044: Removed genre column from characters table';
    RAISE NOTICE 'Genre is now on Series/Episode, injected by Director at runtime (ADR-001)';
END
$$;
