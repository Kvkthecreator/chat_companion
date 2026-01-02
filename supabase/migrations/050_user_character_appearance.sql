-- Migration: 050_user_character_appearance.sql
-- Purpose: Add appearance_prompt and style_preset columns to characters table
--          for user-created characters (ADR-004)
-- Created: 2025-01-02

-- ============================================================================
-- Add appearance columns to characters table
-- ============================================================================
-- These columns store user-defined appearance settings for user-created characters.
-- Canonical characters use avatar_kits.appearance_prompt instead.

ALTER TABLE characters
ADD COLUMN IF NOT EXISTS appearance_prompt TEXT;

ALTER TABLE characters
ADD COLUMN IF NOT EXISTS style_preset TEXT DEFAULT 'manhwa';

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
DECLARE
    appearance_prompt_exists BOOLEAN;
    style_preset_exists BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'characters' AND column_name = 'appearance_prompt'
    ) INTO appearance_prompt_exists;
    ASSERT appearance_prompt_exists, 'characters.appearance_prompt should exist';

    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'characters' AND column_name = 'style_preset'
    ) INTO style_preset_exists;
    ASSERT style_preset_exists, 'characters.style_preset should exist';

    RAISE NOTICE '✓ Migration 050_user_character_appearance completed successfully';
END $$;
