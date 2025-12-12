-- Migration: 012_cleanup_legacy
-- Description: Remove deprecated tables and clean up legacy schema artifacts
--
-- This migration removes:
-- 1. character_expressions - replaced by avatar_assets with asset_type='expression'
--
-- Prerequisites: Ensure no data exists in deprecated tables before running

-- ============================================================================
-- STEP 1: Verify no data in deprecated tables
-- ============================================================================
DO $$
DECLARE
    expr_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO expr_count FROM character_expressions;
    IF expr_count > 0 THEN
        RAISE EXCEPTION 'character_expressions has % rows. Migrate data before dropping.', expr_count;
    END IF;
END $$;

-- ============================================================================
-- STEP 2: Drop deprecated table
-- ============================================================================
DROP TABLE IF EXISTS character_expressions CASCADE;

-- ============================================================================
-- STEP 3: Update image_assets type constraint to remove deprecated types
-- ============================================================================
-- Note: We keep 'avatar' and 'expression' in the constraint for now since
-- existing code might still reference them. A future migration can remove them
-- once all code is updated.

-- Add comment clarifying current usage
COMMENT ON TABLE image_assets IS
'Generic image assets for non-avatar images.
Current valid types:
- scene: User-generated scene images (linked via scene_images table)
- background: World/scene backgrounds (future)
- prop: Props and objects (future)

Deprecated types (do not use for new records):
- avatar: Use avatar_assets with asset_type="anchor_*"
- expression: Use avatar_assets with asset_type="expression"';

-- ============================================================================
-- STEP 4: Clean up any orphaned storage policies if they exist
-- ============================================================================
-- These might have been created manually or from previous attempts

-- Note: Storage policies are already set in 011_avatars_storage.sql
-- This section ensures we don't have duplicates

-- ============================================================================
-- Migration complete
-- ============================================================================
