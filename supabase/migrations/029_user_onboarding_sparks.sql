-- =============================================================================
-- Migration 029: Hardened Free Tier Economics
-- =============================================================================
-- This migration ensures spark_balance defaults to 0 for new users.
--
-- RATIONALE (Bootstrap-Friendly Economics):
-- Free content is already generous - no need to give away Sparks:
-- - Episode 0 = Full intro experience with auto-gen images (~$0.20 cost)
-- - Play Mode = Multiple trope episodes with auto-gen images (~$0.20 cost)
-- - Free Chat = Unlimited chat (no images)
--
-- Users who want Episode 1+ must purchase Sparks or subscribe.
-- This keeps free tier burn close to zero while providing enough value
-- for users to understand the product before converting.
--
-- Reference: docs/monetization/CREDITS_SYSTEM_PROPOSAL.md Section 2
-- =============================================================================

-- Ensure default is 0 (no free onboarding Sparks)
ALTER TABLE users ALTER COLUMN spark_balance SET DEFAULT 0;

COMMENT ON COLUMN users.spark_balance IS
'Current Spark balance. New users start with 0. Free content (Episode 0, Play Mode) requires no Sparks. Episode 1+ costs 3 Sparks each.';
