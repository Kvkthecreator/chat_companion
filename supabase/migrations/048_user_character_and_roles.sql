-- Migration: 048_user_character_and_roles.sql
-- Purpose: Add support for user-created characters and explicit Role abstraction
-- Related: ADR-004 User Character & Role Abstraction
-- Created: 2025-01-01

-- ============================================================================
-- PART 1: ROLES TABLE
-- ============================================================================
-- Role is the bridge between episode and character.
-- It defines the archetype slot an episode requires, which can be filled by
-- any compatible character (canonical or user-created).

CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identity
    name TEXT NOT NULL,                           -- "The Barista", "The Stranger"
    slug TEXT UNIQUE NOT NULL,
    description TEXT,                             -- For content authoring UI

    -- Compatibility constraints
    archetype TEXT NOT NULL,                      -- Required archetype (warm_supportive, etc.)
    compatible_archetypes TEXT[] DEFAULT '{}',    -- Additional compatible archetypes
    required_traits JSONB DEFAULT '{}',           -- Minimum personality requirements (future)

    -- Scene motivation (moved from episode_template per ADR-002)
    -- These are the "director's notes" that the character internalizes
    scene_objective TEXT,                         -- What character wants from user
    scene_obstacle TEXT,                          -- What's stopping them
    scene_tactic TEXT,                            -- How they're playing it

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for archetype lookup (finding roles compatible with a character)
CREATE INDEX IF NOT EXISTS idx_roles_archetype ON roles(archetype);
CREATE INDEX IF NOT EXISTS idx_roles_slug ON roles(slug);

-- ============================================================================
-- PART 2: USER CHARACTER SUPPORT ON CHARACTERS TABLE
-- ============================================================================

-- Add is_user_created flag to distinguish platform vs user characters
ALTER TABLE characters
ADD COLUMN IF NOT EXISTS is_user_created BOOLEAN DEFAULT FALSE;

-- Add is_public flag for future shareable characters (Phase 3)
ALTER TABLE characters
ADD COLUMN IF NOT EXISTS is_public BOOLEAN DEFAULT FALSE;

-- Ensure created_by exists (may already exist from earlier migrations)
-- This column tracks who created the character
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'characters' AND column_name = 'created_by'
    ) THEN
        ALTER TABLE characters ADD COLUMN created_by UUID REFERENCES auth.users(id);
    END IF;
END $$;

-- Constraint: user-created characters must have created_by set
-- (canonical characters may or may not have created_by)
ALTER TABLE characters DROP CONSTRAINT IF EXISTS chk_user_created_has_owner;
ALTER TABLE characters ADD CONSTRAINT chk_user_created_has_owner
    CHECK (is_user_created = FALSE OR created_by IS NOT NULL);

-- Index for listing user's characters efficiently
CREATE INDEX IF NOT EXISTS idx_characters_user_created
ON characters(created_by, status)
WHERE is_user_created = TRUE;

-- Mark all existing characters as canonical (platform-created)
UPDATE characters SET is_user_created = FALSE WHERE is_user_created IS NULL;
UPDATE characters SET is_public = FALSE WHERE is_public IS NULL;

-- ============================================================================
-- PART 3: EPISODE TEMPLATE ROLE REFERENCE
-- ============================================================================

-- Add role_id to episode_templates
-- Existing episodes can have NULL role_id (backward compatibility)
-- New episodes should reference explicit roles
ALTER TABLE episode_templates
ADD COLUMN IF NOT EXISTS role_id UUID REFERENCES roles(id);

-- Index for finding episodes by role
CREATE INDEX IF NOT EXISTS idx_episode_templates_role ON episode_templates(role_id);

-- ============================================================================
-- PART 4: SESSION ROLE TRACKING
-- ============================================================================

-- Add role_id to sessions for explicit role tracking at runtime
-- This tracks "which role is this character playing in this session"
ALTER TABLE sessions
ADD COLUMN IF NOT EXISTS role_id UUID REFERENCES roles(id);

-- Index for role-based session queries
CREATE INDEX IF NOT EXISTS idx_sessions_role ON sessions(role_id);

-- ============================================================================
-- PART 5: RLS POLICIES FOR USER CHARACTERS
-- ============================================================================

-- Users can read all active canonical characters
-- Users can read their own user-created characters
DROP POLICY IF EXISTS "Users can view canonical characters" ON characters;
CREATE POLICY "Users can view canonical characters" ON characters
    FOR SELECT
    USING (
        is_user_created = FALSE
        OR created_by = auth.uid()
    );

-- Users can only insert their own characters
DROP POLICY IF EXISTS "Users can create own characters" ON characters;
CREATE POLICY "Users can create own characters" ON characters
    FOR INSERT
    WITH CHECK (
        created_by = auth.uid()
        AND is_user_created = TRUE
    );

-- Users can only update their own user-created characters
DROP POLICY IF EXISTS "Users can update own characters" ON characters;
CREATE POLICY "Users can update own characters" ON characters
    FOR UPDATE
    USING (
        created_by = auth.uid()
        AND is_user_created = TRUE
    );

-- Users can only delete their own user-created characters
DROP POLICY IF EXISTS "Users can delete own characters" ON characters;
CREATE POLICY "Users can delete own characters" ON characters
    FOR DELETE
    USING (
        created_by = auth.uid()
        AND is_user_created = TRUE
    );

-- ============================================================================
-- PART 6: RLS POLICIES FOR ROLES (read-only for users)
-- ============================================================================

-- Enable RLS on roles table
ALTER TABLE roles ENABLE ROW LEVEL SECURITY;

-- Everyone can read roles (they're platform content)
DROP POLICY IF EXISTS "Anyone can view roles" ON roles;
CREATE POLICY "Anyone can view roles" ON roles
    FOR SELECT
    USING (true);

-- Only service role can modify roles (content authoring)
DROP POLICY IF EXISTS "Service role can manage roles" ON roles;
CREATE POLICY "Service role can manage roles" ON roles
    FOR ALL
    USING (auth.role() = 'service_role');

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
DECLARE
    roles_exists BOOLEAN;
    is_user_created_exists BOOLEAN;
    role_id_in_episodes BOOLEAN;
    role_id_in_sessions BOOLEAN;
BEGIN
    -- Check roles table exists
    SELECT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'roles'
    ) INTO roles_exists;
    ASSERT roles_exists, 'roles table should exist';

    -- Check is_user_created column exists
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'characters' AND column_name = 'is_user_created'
    ) INTO is_user_created_exists;
    ASSERT is_user_created_exists, 'characters.is_user_created should exist';

    -- Check role_id in episode_templates
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'episode_templates' AND column_name = 'role_id'
    ) INTO role_id_in_episodes;
    ASSERT role_id_in_episodes, 'episode_templates.role_id should exist';

    -- Check role_id in sessions
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'sessions' AND column_name = 'role_id'
    ) INTO role_id_in_sessions;
    ASSERT role_id_in_sessions, 'sessions.role_id should exist';

    -- Check no NULL is_user_created values
    ASSERT (SELECT COUNT(*) FROM characters WHERE is_user_created IS NULL) = 0,
        'All characters should have is_user_created set';

    RAISE NOTICE '✓ Migration 048_user_character_and_roles completed successfully';
END $$;
