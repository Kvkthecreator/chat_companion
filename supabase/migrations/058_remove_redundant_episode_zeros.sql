-- Migration: Remove Redundant Episode 0s
-- Date: 2026-01-12
-- Purpose: Delete redundant Episode 0s from 3 series and renumber remaining episodes
--
-- Affected series:
-- 1. download-complete: Episode 0 "Boot Sequence" is redundant with Episode 1 "Activation Day"
-- 2. first-snow: Episode 0 "The Studio" is redundant with Episode 1 "The Art Room"
-- 3. summers-end: Episode 0 "Seven Years" is redundant with Episode 1 "The Return"
--
-- Strategy: Delete Episode 0, renumber episodes 1-6 to become 0-5

BEGIN;

-- Step 1: Migrate existing user sessions from old Episode 0 to new Episode 0 (current Episode 1)
-- download-complete: Boot Sequence -> Activation Day
UPDATE sessions
SET episode_template_id = '32b40cf8-172b-4613-9651-7159353ad51f'  -- Activation Day
WHERE episode_template_id = '48af01cd-62ae-4757-b12d-112389df0aee';  -- Boot Sequence

-- first-snow: The Studio -> The Art Room
UPDATE sessions
SET episode_template_id = '14322d9a-2bdd-4d39-bf67-78f64f654995'  -- The Art Room
WHERE episode_template_id = 'd0f4856a-9031-46db-b128-72d56c7d03bd';  -- The Studio

-- summers-end: Seven Years -> The Return
UPDATE sessions
SET episode_template_id = '6a04dbea-6b76-48af-adff-eca254359392'  -- The Return
WHERE episode_template_id = 'd902f478-45d8-4855-a552-382de3db8aaf';  -- Seven Years

-- Step 2: Copy role_id from old Episode 0 to Episode 1 (which will become new Episode 0)
-- download-complete
UPDATE episode_templates
SET role_id = '5124dc73-7b0a-4b2e-bd2f-5f2f2e7fe29b'  -- Role from Boot Sequence
WHERE id = '32b40cf8-172b-4613-9651-7159353ad51f';  -- Activation Day

-- first-snow
UPDATE episode_templates
SET role_id = '051e3879-a4b1-4fbf-8499-47eb6f11d5da'  -- Role from The Studio
WHERE id = '14322d9a-2bdd-4d39-bf67-78f64f654995';  -- The Art Room

-- summers-end
UPDATE episode_templates
SET role_id = '0a695c39-714e-45d7-a21b-795917adf884'  -- Role from Seven Years
WHERE id = '6a04dbea-6b76-48af-adff-eca254359392';  -- The Return

-- Step 3: Delete the redundant Episode 0s
DELETE FROM episode_templates
WHERE id IN (
    '48af01cd-62ae-4757-b12d-112389df0aee',  -- download-complete: Boot Sequence
    'd0f4856a-9031-46db-b128-72d56c7d03bd',  -- first-snow: The Studio
    'd902f478-45d8-4855-a552-382de3db8aaf'   -- summers-end: Seven Years
);

-- Step 4: Renumber remaining episodes (1-6 -> 0-5)
-- Use a temporary offset to avoid unique constraint conflicts, then shift back
-- First, shift all to 100+ range
UPDATE episode_templates
SET episode_number = episode_number + 100
WHERE series_id IN (
    SELECT id FROM series WHERE slug IN ('download-complete', 'first-snow', 'summers-end')
)
AND episode_number BETWEEN 1 AND 6;

-- Now shift back to final positions (101-106 -> 0-5)
UPDATE episode_templates
SET episode_number = episode_number - 101
WHERE series_id IN (
    SELECT id FROM series WHERE slug IN ('download-complete', 'first-snow', 'summers-end')
)
AND episode_number BETWEEN 101 AND 106;

COMMIT;

-- Verification query (run separately after migration):
-- SELECT s.slug, et.episode_number, et.title
-- FROM series s
-- JOIN episode_templates et ON s.id = et.series_id
-- WHERE s.slug IN ('download-complete', 'first-snow', 'summers-end')
-- ORDER BY s.slug, et.episode_number;
