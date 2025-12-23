-- Migration: Drop deprecated backstory columns
-- Date: 2024-12-23
-- Purpose: Complete the consolidation by removing old columns
-- Prerequisite: 039_consolidate_backstory_fields.sql must have run first

-- Drop deprecated columns
ALTER TABLE characters DROP COLUMN IF EXISTS short_backstory;
ALTER TABLE characters DROP COLUMN IF EXISTS full_backstory;
ALTER TABLE characters DROP COLUMN IF EXISTS current_stressor;
ALTER TABLE characters DROP COLUMN IF EXISTS life_arc;

-- Log migration
DO $$
BEGIN
    RAISE NOTICE 'Migration 040: Dropped deprecated columns (short_backstory, full_backstory, current_stressor, life_arc)';
END
$$;
