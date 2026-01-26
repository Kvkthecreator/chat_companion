-- =============================================================================
-- Domain Layer - Thread Templates and Domain Classification
-- =============================================================================
-- Implements the domain layer for transition-focused companion experience.
-- Templates provide structure for thread classification and follow-up prompts.
--
-- See: docs/implementation/DOMAIN_LAYER_IMPLEMENTATION.md

-- =============================================================================
-- Thread Templates Table
-- =============================================================================
-- Templates define high-value thread types for people in transition.
-- Used for:
-- 1. Onboarding (user selects from transition options)
-- 2. Classification (LLM matches free-text to templates)
-- 3. Follow-up prompts (domain-specific check-in language)

CREATE TABLE IF NOT EXISTS thread_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Classification
    domain TEXT NOT NULL,           -- career, location, relationships, health, creative, life_stage, personal
    template_key TEXT NOT NULL,     -- job_search, new_city, breakup, etc.
    display_name TEXT NOT NULL,     -- "Looking for a job", "Moving to a New City"

    -- For LLM classification
    trigger_phrases TEXT[],         -- keywords that suggest this template
    description TEXT,               -- Helps LLM understand when to apply

    -- Phases (optional - not all transitions have clear phases)
    has_phases BOOLEAN DEFAULT FALSE,
    phases JSONB,                   -- ["exploring", "applying", "interviewing", "waiting", "decided"]

    -- Follow-up configuration
    follow_up_prompts JSONB NOT NULL,
    -- {
    --   "initial": "Tell me more about the job search",
    --   "check_in": "How's the job search going?",
    --   "phase_specific": { "waiting": "Did you hear back?" }
    -- }

    typical_duration TEXT,          -- days, weeks, months, varies
    default_follow_up_days INTEGER DEFAULT 3,

    -- Metadata
    is_active BOOLEAN DEFAULT TRUE,
    display_order INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_thread_templates_domain ON thread_templates(domain);
CREATE UNIQUE INDEX idx_thread_templates_key ON thread_templates(template_key);
CREATE INDEX idx_thread_templates_active ON thread_templates(is_active, display_order) WHERE is_active = TRUE;

-- =============================================================================
-- User Domain Preferences
-- =============================================================================
-- Store user's domain preferences (selected during onboarding)

ALTER TABLE users ADD COLUMN IF NOT EXISTS domain_preferences JSONB DEFAULT '{}';
-- Structure:
-- {
--   "primary_domains": ["career", "location"],
--   "domain_weights": { "career": 1.5, "location": 1.2 },
--   "onboarding_selections": ["job_search", "new_city"]
-- }

-- =============================================================================
-- User Context Extensions for Domain Layer
-- =============================================================================
-- Add domain-related fields to user_context for threads
-- Note: Threads are stored as category='thread' in user_context
-- The value JSON now includes domain/template_id/phase fields

-- Add tier column if not exists (for memory tiering: working/active/core)
ALTER TABLE user_context ADD COLUMN IF NOT EXISTS tier TEXT DEFAULT 'working';

-- Add domain field for thread classification (nullable for non-thread entries)
ALTER TABLE user_context ADD COLUMN IF NOT EXISTS domain TEXT;

-- Add template reference (nullable)
ALTER TABLE user_context ADD COLUMN IF NOT EXISTS template_id UUID REFERENCES thread_templates(id);

-- Add phase for phased transitions
ALTER TABLE user_context ADD COLUMN IF NOT EXISTS phase TEXT;

-- Add priority weight for ranking threads (default 1.0, primary domain gets 1.5)
ALTER TABLE user_context ADD COLUMN IF NOT EXISTS priority_weight NUMERIC(3,2) DEFAULT 1.0;

-- Index for priority-ranked thread queries
CREATE INDEX IF NOT EXISTS idx_user_context_thread_priority
ON user_context(user_id, priority_weight DESC, updated_at DESC)
WHERE category = 'thread';

-- Index for domain queries
CREATE INDEX IF NOT EXISTS idx_user_context_domain
ON user_context(user_id, domain)
WHERE domain IS NOT NULL;

-- =============================================================================
-- RLS Policies
-- =============================================================================

ALTER TABLE thread_templates ENABLE ROW LEVEL SECURITY;

-- Templates are readable by all authenticated users
CREATE POLICY "Templates are viewable by authenticated users"
ON thread_templates
FOR SELECT
TO authenticated
USING (is_active = TRUE);

-- Only service role can manage templates
CREATE POLICY "Service role can manage templates"
ON thread_templates
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- =============================================================================
-- Grants
-- =============================================================================

GRANT SELECT ON thread_templates TO authenticated;
GRANT ALL ON thread_templates TO service_role;

-- =============================================================================
-- Seed Data: Thread Templates
-- =============================================================================
-- 18 starter templates across 7 domains

INSERT INTO thread_templates (domain, template_key, display_name, trigger_phrases, description, has_phases, phases, follow_up_prompts, typical_duration, default_follow_up_days, display_order) VALUES

-- CAREER DOMAIN
('career', 'job_search', 'Looking for a job',
 ARRAY['job search', 'looking for work', 'applying', 'interview', 'resume', 'job hunt', 'unemployed', 'laid off'],
 'User is actively searching for employment',
 TRUE, '["exploring", "applying", "interviewing", "waiting", "decided"]'::jsonb,
 '{"initial": "Tell me about the job search — what kind of role are you looking for?", "check_in": "How''s the job search going?", "phase_specific": {"applying": "How are the applications going?", "interviewing": "How did the interview go?", "waiting": "Did you hear back yet?"}}'::jsonb,
 'weeks_to_months', 3, 1),

('career', 'new_job', 'Starting a new job',
 ARRAY['new job', 'started work', 'first day', 'new role', 'onboarding', 'just started'],
 'User recently started a new position',
 TRUE, '["preparing", "first_week", "settling_in", "established"]'::jsonb,
 '{"initial": "Congrats on the new role! How are you feeling about it?", "check_in": "How''s the new job going?", "phase_specific": {"first_week": "How was your first week?", "settling_in": "Starting to feel more settled?"}}'::jsonb,
 'months', 7, 2),

('career', 'leaving_job', 'Leaving a job',
 ARRAY['quitting', 'leaving job', 'last day', 'giving notice', 'resigned', 'fired'],
 'User is leaving or has left their job',
 FALSE, NULL,
 '{"initial": "That''s a big change. How are you feeling about leaving?", "check_in": "How are you doing with the job transition?"}'::jsonb,
 'weeks', 3, 3),

-- LOCATION DOMAIN
('location', 'moving', 'Moving to a new place',
 ARRAY['moving', 'relocating', 'new apartment', 'new house', 'packing', 'movers'],
 'User is in the process of moving',
 TRUE, '["planning", "packing", "moving_day", "unpacking", "settling"]'::jsonb,
 '{"initial": "Where are you moving to? What''s prompting the move?", "check_in": "How''s the move going?", "phase_specific": {"moving_day": "How did moving day go?", "settling": "Starting to feel at home?"}}'::jsonb,
 'weeks_to_months', 5, 4),

('location', 'new_city', 'Settling into a new city',
 ARRAY['new city', 'just moved', 'don''t know anyone', 'finding my way', 'exploring'],
 'User recently moved to a new city and is settling in',
 TRUE, '["arrival", "exploring", "building_routine", "feeling_home"]'::jsonb,
 '{"initial": "What brought you to the new city? How long have you been there?", "check_in": "How are you finding the new city?", "phase_specific": {"exploring": "Discovered any good spots yet?", "building_routine": "Starting to build a routine?"}}'::jsonb,
 'months', 7, 5),

-- RELATIONSHIPS DOMAIN
('relationships', 'breakup', 'Going through a breakup',
 ARRAY['breakup', 'broke up', 'ended relationship', 'ex', 'single again', 'split up'],
 'User is processing a relationship ending',
 FALSE, NULL,
 '{"initial": "I''m sorry to hear that. How are you holding up?", "check_in": "How are you doing with everything?"}'::jsonb,
 'weeks_to_months', 3, 6),

('relationships', 'new_relationship', 'Starting a new relationship',
 ARRAY['dating', 'new relationship', 'met someone', 'seeing someone', 'boyfriend', 'girlfriend'],
 'User has started a new romantic relationship',
 FALSE, NULL,
 '{"initial": "That''s exciting! How did you meet?", "check_in": "How are things going with them?"}'::jsonb,
 'months', 7, 7),

('relationships', 'relationship_tension', 'Working through relationship issues',
 ARRAY['fighting', 'argument', 'tension', 'not getting along', 'relationship problems', 'couples therapy'],
 'User is navigating difficulties in a relationship',
 FALSE, NULL,
 '{"initial": "That sounds stressful. What''s been going on?", "check_in": "How are things between you two?"}'::jsonb,
 'days_to_weeks', 2, 8),

-- HEALTH DOMAIN
('health', 'personal_health', 'Dealing with a health situation',
 ARRAY['health issue', 'diagnosis', 'doctor', 'treatment', 'symptoms', 'medical', 'surgery', 'hospital'],
 'User is managing a health concern',
 FALSE, NULL,
 '{"initial": "I hope you''re okay. What''s going on health-wise?", "check_in": "How are you feeling?"}'::jsonb,
 'varies', 3, 9),

('health', 'caregiver', 'Caring for someone',
 ARRAY['taking care of', 'caregiver', 'mom''s health', 'dad''s health', 'family member sick', 'elderly parent'],
 'User is caring for a sick family member',
 FALSE, NULL,
 '{"initial": "That''s a lot to carry. How is the person you''re caring for doing?", "check_in": "How are you holding up with everything?"}'::jsonb,
 'months', 5, 10),

('health', 'lifestyle_change', 'Making a lifestyle change',
 ARRAY['diet', 'exercise', 'quit smoking', 'sobriety', 'sleep', 'habit', 'working out', 'eating better'],
 'User is making a significant lifestyle change',
 TRUE, '["starting", "first_week", "building_habit", "maintaining"]'::jsonb,
 '{"initial": "What motivated this change?", "check_in": "How''s the lifestyle change going?", "phase_specific": {"first_week": "How''s the first week going?", "building_habit": "Starting to feel like a habit?"}}'::jsonb,
 'weeks_to_months', 3, 11),

-- CREATIVE DOMAIN
('creative', 'launching', 'Launching something',
 ARRAY['launching', 'shipping', 'release', 'going live', 'product launch', 'launch day'],
 'User is launching a product, project, or business',
 TRUE, '["preparing", "launch_day", "post_launch"]'::jsonb,
 '{"initial": "Exciting! What are you launching?", "check_in": "How''s the launch prep going?", "phase_specific": {"launch_day": "How did the launch go?", "post_launch": "How''s the reception been?"}}'::jsonb,
 'weeks', 2, 12),

('creative', 'building', 'Building a project',
 ARRAY['building', 'working on', 'side project', 'creating', 'making', 'developing'],
 'User is working on a creative or technical project',
 FALSE, NULL,
 '{"initial": "What are you building?", "check_in": "How''s the project coming along?"}'::jsonb,
 'months', 7, 13),

-- LIFE STAGE DOMAIN
('life_stage', 'graduation', 'Graduating / finishing school',
 ARRAY['graduating', 'finished school', 'degree', 'diploma', 'college', 'university'],
 'User is completing education',
 FALSE, NULL,
 '{"initial": "Congratulations! What''s next for you?", "check_in": "How are you feeling about the transition?"}'::jsonb,
 'months', 7, 14),

('life_stage', 'parenthood', 'Becoming a parent',
 ARRAY['pregnant', 'expecting', 'baby', 'new parent', 'newborn', 'having a baby'],
 'User is expecting or has recently become a parent',
 FALSE, NULL,
 '{"initial": "That''s huge! How are you feeling about it?", "check_in": "How''s everything going with the little one?"}'::jsonb,
 'months', 7, 15),

-- PERSONAL DOMAIN (catch-all for important but uncategorized)
('personal', 'grief', 'Processing a loss',
 ARRAY['loss', 'died', 'passed away', 'grieving', 'funeral', 'death'],
 'User is grieving a loss',
 FALSE, NULL,
 '{"initial": "I''m so sorry for your loss. I''m here if you want to talk.", "check_in": "How are you doing?"}'::jsonb,
 'months', 5, 16),

('personal', 'finances', 'Financial situation',
 ARRAY['money', 'debt', 'budget', 'saving', 'financial stress', 'bills', 'broke'],
 'User is dealing with financial challenges',
 FALSE, NULL,
 '{"initial": "Money stuff can be stressful. What''s going on?", "check_in": "How''s the financial situation?"}'::jsonb,
 'months', 7, 17),

('personal', 'open', 'Something else',
 ARRAY[]::TEXT[],
 'Catch-all for situations that don''t match other templates',
 FALSE, NULL,
 '{"initial": "Tell me more about what''s going on.", "check_in": "How are things going?"}'::jsonb,
 'varies', 5, 99);

-- =============================================================================
-- Comments
-- =============================================================================

COMMENT ON TABLE thread_templates IS
'Thread templates for the domain layer. Defines high-value transitions to track.';

COMMENT ON COLUMN thread_templates.domain IS
'Domain category: career, location, relationships, health, creative, life_stage, personal';

COMMENT ON COLUMN thread_templates.template_key IS
'Unique key for this template, used in code references';

COMMENT ON COLUMN thread_templates.trigger_phrases IS
'Keywords that suggest this template during classification';

COMMENT ON COLUMN thread_templates.follow_up_prompts IS
'JSON with initial, check_in, and optional phase_specific prompts';

COMMENT ON COLUMN users.domain_preferences IS
'User''s domain preferences from onboarding: primary_domains, domain_weights, onboarding_selections';

COMMENT ON COLUMN user_context.domain IS
'Domain classification for thread entries (career, location, etc.)';

COMMENT ON COLUMN user_context.template_id IS
'Reference to thread_templates for typed threads';

COMMENT ON COLUMN user_context.phase IS
'Current phase within a phased transition (e.g., interviewing, settling_in)';

COMMENT ON COLUMN user_context.priority_weight IS
'Priority weight for ranking threads. Primary domain threads get 1.5, others 1.0';
