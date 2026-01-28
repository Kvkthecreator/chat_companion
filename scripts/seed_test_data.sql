-- =============================================================================
-- Seed Test Data for Chat Companion
-- Run this against your database to populate test data for kvkthecreator@gmail.com
--
-- PREREQUISITES:
-- 1. Run migration 108_fix_messages_table.sql first (adds conversation_id to messages)
-- 2. User kvkthecreator@gmail.com must exist in the database
--
-- THRESHOLDS MET:
-- - Relationship: 14+ days, 10+ conversations
-- - Communication: 20+ user messages, 5+ conversations
-- - Domain Health: 1+ threads per domain
-- - Thread Journey: 7+ days per thread
-- =============================================================================

-- Get the user ID for the test user
DO $$
DECLARE
    test_user_id UUID;
    conv_id UUID;
    thread_job_id UUID := gen_random_uuid();
    thread_move_id UUID := gen_random_uuid();
    thread_health_id UUID := gen_random_uuid();
    job_template_id UUID;
    move_template_id UUID;
BEGIN
    -- Find the test user
    SELECT id INTO test_user_id FROM users WHERE email = 'kvkthecreator@gmail.com';

    IF test_user_id IS NULL THEN
        RAISE EXCEPTION 'Test user kvkthecreator@gmail.com not found. Please create the user first.';
    END IF;

    -- Get template IDs (may be null if domain layer not seeded)
    SELECT id INTO job_template_id FROM thread_templates WHERE template_key = 'job_search';
    SELECT id INTO move_template_id FROM thread_templates WHERE template_key = 'new_city';

    -- =============================================================================
    -- 1. CONVERSATIONS & MESSAGES (need 10+ convos, 20+ user messages, 14+ days)
    -- =============================================================================

    -- Conversation 1: 20 days ago (first contact)
    conv_id := gen_random_uuid();
    INSERT INTO conversations (id, user_id, channel, started_at, message_count, initiated_by)
    VALUES (conv_id, test_user_id, 'web', NOW() - INTERVAL '20 days', 4, 'companion')
    ON CONFLICT DO NOTHING;
    INSERT INTO messages (conversation_id, role, content, created_at) VALUES
    (conv_id, 'assistant', 'Hi there! I''m so glad to meet you. What brings you here today?', NOW() - INTERVAL '20 days' + INTERVAL '10 hours'),
    (conv_id, 'user', 'Hey! I''ve been feeling a bit lost with my career lately. Thinking about making some changes.', NOW() - INTERVAL '20 days' + INTERVAL '10 hours 5 minutes'),
    (conv_id, 'assistant', 'That''s a really common feeling. What kind of changes are you considering?', NOW() - INTERVAL '20 days' + INTERVAL '10 hours 6 minutes'),
    (conv_id, 'user', 'Maybe looking for a new job. I''ve been at my current company for 3 years and feel stuck.', NOW() - INTERVAL '20 days' + INTERVAL '10 hours 10 minutes')
    ON CONFLICT DO NOTHING;

    -- Conversation 2: 18 days ago
    conv_id := gen_random_uuid();
    INSERT INTO conversations (id, user_id, channel, started_at, message_count, initiated_by)
    VALUES (conv_id, test_user_id, 'web', NOW() - INTERVAL '18 days', 4, 'companion')
    ON CONFLICT DO NOTHING;
    INSERT INTO messages (conversation_id, role, content, created_at) VALUES
    (conv_id, 'assistant', 'How are you doing today? Been thinking about our last chat about your career.', NOW() - INTERVAL '18 days' + INTERVAL '9 hours'),
    (conv_id, 'user', 'Yeah, I started updating my resume actually. It feels good to take action.', NOW() - INTERVAL '18 days' + INTERVAL '9 hours 5 minutes'),
    (conv_id, 'assistant', 'That''s awesome! What kind of roles are you looking at?', NOW() - INTERVAL '18 days' + INTERVAL '9 hours 6 minutes'),
    (conv_id, 'user', 'Senior product roles at startups. I want more ownership and impact.', NOW() - INTERVAL '18 days' + INTERVAL '9 hours 10 minutes')
    ON CONFLICT DO NOTHING;

    -- Conversation 3: 15 days ago
    conv_id := gen_random_uuid();
    INSERT INTO conversations (id, user_id, channel, started_at, message_count, initiated_by)
    VALUES (conv_id, test_user_id, 'web', NOW() - INTERVAL '15 days', 4, 'user')
    ON CONFLICT DO NOTHING;
    INSERT INTO messages (conversation_id, role, content, created_at) VALUES
    (conv_id, 'user', 'Got a call from a recruiter today! There''s a startup in Austin looking for a senior PM.', NOW() - INTERVAL '15 days' + INTERVAL '14 hours'),
    (conv_id, 'assistant', 'That''s exciting! Tell me more about the opportunity.', NOW() - INTERVAL '15 days' + INTERVAL '14 hours 1 minute'),
    (conv_id, 'user', 'It''s in the fintech space. They''re building something really interesting with payments.', NOW() - INTERVAL '15 days' + INTERVAL '14 hours 5 minutes'),
    (conv_id, 'assistant', 'And Austin - that would be a big move from SF. How do you feel about that?', NOW() - INTERVAL '15 days' + INTERVAL '14 hours 6 minutes')
    ON CONFLICT DO NOTHING;

    -- Conversation 4: 12 days ago
    conv_id := gen_random_uuid();
    INSERT INTO conversations (id, user_id, channel, started_at, message_count, initiated_by)
    VALUES (conv_id, test_user_id, 'web', NOW() - INTERVAL '12 days', 4, 'companion')
    ON CONFLICT DO NOTHING;
    INSERT INTO messages (conversation_id, role, content, created_at) VALUES
    (conv_id, 'assistant', 'How did the recruiter call go? Have you thought more about Austin?', NOW() - INTERVAL '12 days' + INTERVAL '9 hours'),
    (conv_id, 'user', 'Actually really excited about it. The cost of living is way lower than SF.', NOW() - INTERVAL '12 days' + INTERVAL '9 hours 5 minutes'),
    (conv_id, 'assistant', 'That''s a practical consideration. What else draws you to making a move?', NOW() - INTERVAL '12 days' + INTERVAL '9 hours 6 minutes'),
    (conv_id, 'user', 'I''ve been in SF for 7 years. I think I need a fresh start. New city, new energy.', NOW() - INTERVAL '12 days' + INTERVAL '9 hours 10 minutes')
    ON CONFLICT DO NOTHING;

    -- Conversation 5: 10 days ago
    conv_id := gen_random_uuid();
    INSERT INTO conversations (id, user_id, channel, started_at, message_count, initiated_by)
    VALUES (conv_id, test_user_id, 'web', NOW() - INTERVAL '10 days', 4, 'user')
    ON CONFLICT DO NOTHING;
    INSERT INTO messages (conversation_id, role, content, created_at) VALUES
    (conv_id, 'user', 'First round interview scheduled for next week! Getting nervous already.', NOW() - INTERVAL '10 days' + INTERVAL '18 hours'),
    (conv_id, 'assistant', 'That''s wonderful! What''s making you nervous about it?', NOW() - INTERVAL '10 days' + INTERVAL '18 hours 1 minute'),
    (conv_id, 'user', 'It''s been a while since I interviewed. What if I mess up the product case?', NOW() - INTERVAL '10 days' + INTERVAL '18 hours 5 minutes'),
    (conv_id, 'assistant', 'That''s totally normal to feel. Would it help to practice together?', NOW() - INTERVAL '10 days' + INTERVAL '18 hours 6 minutes')
    ON CONFLICT DO NOTHING;

    -- Conversation 6: 8 days ago
    conv_id := gen_random_uuid();
    INSERT INTO conversations (id, user_id, channel, started_at, message_count, initiated_by)
    VALUES (conv_id, test_user_id, 'web', NOW() - INTERVAL '8 days', 4, 'companion')
    ON CONFLICT DO NOTHING;
    INSERT INTO messages (conversation_id, role, content, created_at) VALUES
    (conv_id, 'assistant', 'Your interview is coming up soon! How are you preparing?', NOW() - INTERVAL '8 days' + INTERVAL '9 hours'),
    (conv_id, 'user', 'Been researching the company like crazy. Also started running again to manage stress.', NOW() - INTERVAL '8 days' + INTERVAL '9 hours 5 minutes'),
    (conv_id, 'assistant', 'That''s great that you''re taking care of yourself too. Running is such a good outlet.', NOW() - INTERVAL '8 days' + INTERVAL '9 hours 6 minutes'),
    (conv_id, 'user', 'Yeah, I used to run a lot but stopped when work got busy. Feels good to be back.', NOW() - INTERVAL '8 days' + INTERVAL '9 hours 10 minutes')
    ON CONFLICT DO NOTHING;

    -- Conversation 7: 5 days ago (interview prep)
    conv_id := gen_random_uuid();
    INSERT INTO conversations (id, user_id, channel, started_at, message_count, initiated_by)
    VALUES (conv_id, test_user_id, 'web', NOW() - INTERVAL '5 days', 4, 'companion')
    ON CONFLICT DO NOTHING;
    INSERT INTO messages (conversation_id, role, content, created_at) VALUES
    (conv_id, 'assistant', 'Good morning! How are you feeling about the week ahead?', NOW() - INTERVAL '5 days' + INTERVAL '9 hours'),
    (conv_id, 'user', 'Pretty anxious actually. Interview is Thursday.', NOW() - INTERVAL '5 days' + INTERVAL '9 hours 5 minutes'),
    (conv_id, 'assistant', 'That''s understandable! You''ve prepared well though. What''s your game plan?', NOW() - INTERVAL '5 days' + INTERVAL '9 hours 6 minutes'),
    (conv_id, 'user', 'Go through their product one more time. Research the founders. Get a good night''s sleep.', NOW() - INTERVAL '5 days' + INTERVAL '9 hours 10 minutes')
    ON CONFLICT DO NOTHING;

    -- Conversation 8: 3 days ago (pre-interview)
    conv_id := gen_random_uuid();
    INSERT INTO conversations (id, user_id, channel, started_at, message_count, initiated_by)
    VALUES (conv_id, test_user_id, 'web', NOW() - INTERVAL '3 days', 6, 'companion')
    ON CONFLICT DO NOTHING;
    INSERT INTO messages (conversation_id, role, content, created_at) VALUES
    (conv_id, 'assistant', 'Tomorrow''s the big day! How are you feeling?', NOW() - INTERVAL '3 days' + INTERVAL '18 hours'),
    (conv_id, 'user', 'Nervous but ready. I''ve done everything I can to prepare.', NOW() - INTERVAL '3 days' + INTERVAL '18 hours 3 minutes'),
    (conv_id, 'assistant', 'You''ve put in the work. What draws you most to this opportunity?', NOW() - INTERVAL '3 days' + INTERVAL '18 hours 4 minutes'),
    (conv_id, 'user', 'They''re building in a space I really care about. And the Austin move excites me more than I expected.', NOW() - INTERVAL '3 days' + INTERVAL '18 hours 8 minutes'),
    (conv_id, 'assistant', 'That excitement is a good sign. It sounds like more than just a job opportunity.', NOW() - INTERVAL '3 days' + INTERVAL '18 hours 9 minutes'),
    (conv_id, 'user', 'Yeah, it feels like a whole life change. New city, new challenge, new chapter.', NOW() - INTERVAL '3 days' + INTERVAL '18 hours 15 minutes')
    ON CONFLICT DO NOTHING;

    -- Conversation 9: Yesterday (post-interview)
    conv_id := gen_random_uuid();
    INSERT INTO conversations (id, user_id, channel, started_at, message_count, initiated_by)
    VALUES (conv_id, test_user_id, 'web', NOW() - INTERVAL '1 day', 4, 'user')
    ON CONFLICT DO NOTHING;
    INSERT INTO messages (conversation_id, role, content, created_at) VALUES
    (conv_id, 'user', 'The interview went really well! They want me to come back for a final round.', NOW() - INTERVAL '1 day' + INTERVAL '14 hours'),
    (conv_id, 'assistant', 'That''s fantastic news! What made it feel like it went well?', NOW() - INTERVAL '1 day' + INTERVAL '14 hours 1 minute'),
    (conv_id, 'user', 'The product discussion was really energizing. We got into the weeds on their roadmap and I had a lot of ideas.', NOW() - INTERVAL '1 day' + INTERVAL '14 hours 5 minutes'),
    (conv_id, 'assistant', 'That sounds like great chemistry. When''s the final round?', NOW() - INTERVAL '1 day' + INTERVAL '14 hours 6 minutes')
    ON CONFLICT DO NOTHING;

    -- Conversation 10: Today
    conv_id := gen_random_uuid();
    INSERT INTO conversations (id, user_id, channel, started_at, message_count, initiated_by)
    VALUES (conv_id, test_user_id, 'web', NOW(), 4, 'companion')
    ON CONFLICT DO NOTHING;
    INSERT INTO messages (conversation_id, role, content, created_at) VALUES
    (conv_id, 'assistant', 'Good morning! Still riding high from yesterday''s interview?', NOW() + INTERVAL '9 hours'),
    (conv_id, 'user', 'Yeah! Just found out the final round is next Tuesday. It''s feeling real now.', NOW() + INTERVAL '9 hours 2 minutes'),
    (conv_id, 'assistant', 'This is really coming together. How are you feeling about all of it?', NOW() + INTERVAL '9 hours 3 minutes'),
    (conv_id, 'user', 'Excited and terrified. But mostly excited. I think this could really be it.', NOW() + INTERVAL '9 hours 5 minutes')
    ON CONFLICT DO NOTHING;

    -- =============================================================================
    -- 2. USER CONTEXT (facts, threads, follow-ups)
    -- =============================================================================

    -- Facts about the user
    INSERT INTO user_context (user_id, category, key, value, importance_score, emotional_valence, source, tier) VALUES
    (test_user_id, 'fact', 'current_location', 'San Francisco', 0.8, 0, 'extracted', 'core'),
    (test_user_id, 'fact', 'years_in_sf', '7 years', 0.6, 0, 'extracted', 'core'),
    (test_user_id, 'fact', 'profession', 'Product Manager', 0.9, 0, 'extracted', 'core'),
    (test_user_id, 'preference', 'work_style', 'Prefers early mornings for deep work', 0.5, 1, 'extracted', 'core'),
    (test_user_id, 'relationship', 'support_network', 'Has close friends in SF tech community', 0.7, 1, 'extracted', 'core')
    ON CONFLICT (user_id, category, key) DO UPDATE SET value = EXCLUDED.value;

    -- Active thread: Job Search (Career domain, 20 days old)
    INSERT INTO user_context (
        id, user_id, category, key, value,
        importance_score, emotional_valence,
        tier, domain, template_id, phase, priority_weight, created_at
    ) VALUES (
        thread_job_id, test_user_id, 'thread', 'job_search',
        '{"summary": "Looking for senior product role at startups. Had successful interview, advancing to final round at Austin company.", "status": "active", "key_details": ["Senior PM role at fintech startup", "Based in Austin (potential relocation)", "Strong product discussion chemistry", "Final round scheduled for Tuesday"]}',
        0.95, 1,
        'thread', 'career', job_template_id, 'interviewing', 1.5, NOW() - INTERVAL '20 days'
    ) ON CONFLICT (user_id, category, key) DO UPDATE SET
        value = EXCLUDED.value,
        phase = EXCLUDED.phase,
        updated_at = NOW();

    -- Active thread: Potential Move (Location domain, 15 days old)
    INSERT INTO user_context (
        id, user_id, category, key, value,
        importance_score, emotional_valence,
        tier, domain, template_id, phase, priority_weight, created_at
    ) VALUES (
        thread_move_id, test_user_id, 'thread', 'considering_austin',
        '{"summary": "Considering moving to Austin if job works out. Has been in SF for 7 years, feeling ready for change.", "status": "active", "key_details": ["Lower cost of living than SF", "Fresh start energy", "New chapter in life"]}',
        0.8, 0,
        'thread', 'location', move_template_id, 'exploring', 1.2, NOW() - INTERVAL '15 days'
    ) ON CONFLICT (user_id, category, key) DO UPDATE SET
        value = EXCLUDED.value,
        updated_at = NOW();

    -- Active thread: Health/Running (Health domain, 8 days old)
    INSERT INTO user_context (
        id, user_id, category, key, value,
        importance_score, emotional_valence,
        tier, domain, template_id, phase, priority_weight, created_at
    ) VALUES (
        thread_health_id, test_user_id, 'thread', 'getting_back_to_running',
        '{"summary": "Started running again after taking a break when work got busy. Using it to manage interview stress.", "status": "active", "key_details": ["Running for stress management", "Had stopped when work got busy", "Feels good to be back at it"]}',
        0.6, 1,
        'thread', 'health', NULL, 'ongoing', 1.0, NOW() - INTERVAL '8 days'
    ) ON CONFLICT (user_id, category, key) DO UPDATE SET
        value = EXCLUDED.value,
        updated_at = NOW();

    -- Follow-up items
    INSERT INTO user_context (user_id, category, key, value, importance_score, expires_at, tier) VALUES
    (test_user_id, 'follow_up', 'final_interview_tuesday', 'Final round interview scheduled for Tuesday', 0.95, NOW() + INTERVAL '7 days', 'core'),
    (test_user_id, 'follow_up', 'austin_research', 'User is researching Austin neighborhoods', 0.6, NOW() + INTERVAL '14 days', 'core')
    ON CONFLICT (user_id, category, key) DO UPDATE SET value = EXCLUDED.value;

    -- Patterns/Observations (derived tier)
    INSERT INTO user_context (user_id, category, key, value, importance_score, emotional_valence, tier) VALUES
    (test_user_id, 'pattern', 'interview_anxiety', '{"pattern_type": "emotional", "message_hint": "Gets anxious before big moments but channels it into preparation", "trend_direction": "stable"}', 0.7, 0, 'derived'),
    (test_user_id, 'pattern', 'action_oriented', '{"pattern_type": "behavioral", "message_hint": "Responds to uncertainty by taking action - updating resume, researching, preparing", "trend_direction": "positive"}', 0.8, 1, 'derived'),
    (test_user_id, 'pattern', 'seeking_change', '{"pattern_type": "life_stage", "message_hint": "At an inflection point - career and location both in flux, open to big changes", "trend_direction": "emerging"}', 0.8, 0, 'derived')
    ON CONFLICT (user_id, category, key) DO UPDATE SET value = EXCLUDED.value;

    -- =============================================================================
    -- 3. ARTIFACTS (thread journey, domain health)
    -- =============================================================================

    -- Thread Journey artifact for job search
    INSERT INTO artifacts (
        user_id, artifact_type, thread_id, title,
        sections, companion_voice, data_sources,
        is_meaningful, generated_at
    ) VALUES (
        test_user_id, 'thread_journey', thread_job_id, 'Your Job Search Journey',
        '[
            {
                "type": "header",
                "content": {
                    "title": "Looking for Senior Product Role",
                    "subtitle": "Started 20 days ago",
                    "status": "Interviewing"
                }
            },
            {
                "type": "timeline",
                "content": [
                    {"date": "20 days ago", "description": "Started thinking about career change", "type": "start"},
                    {"date": "18 days ago", "description": "Updated resume, targeting senior PM roles", "type": "milestone"},
                    {"date": "15 days ago", "description": "Recruiter reached out about Austin opportunity", "type": "milestone"},
                    {"date": "10 days ago", "description": "First round interview scheduled", "type": "milestone"},
                    {"date": "Yesterday", "description": "Interview went well - advancing to final round!", "type": "milestone"}
                ]
            },
            {
                "type": "observations",
                "content": "You seem energized by product discussions and strategic work. The Austin opportunity combines your career goals with a fresh start you''ve been thinking about."
            },
            {
                "type": "key_details",
                "content": [
                    "Senior product role at fintech startup",
                    "Role would be in Austin (potential relocation)",
                    "Strong product discussion chemistry in interview",
                    "Final round scheduled for Tuesday"
                ]
            }
        ]'::jsonb,
        'I can see how much thought you''ve put into this transition. The fact that the interview felt energizing is a really good sign - that chemistry is hard to fake.',
        '["thread:job_search", "messages:20", "patterns:3"]'::jsonb,
        true,
        NOW()
    ) ON CONFLICT DO NOTHING;

    -- Domain Health artifact for Career
    INSERT INTO artifacts (
        user_id, artifact_type, domain, title,
        sections, companion_voice, data_sources,
        is_meaningful, generated_at
    ) VALUES (
        test_user_id, 'domain_health', 'career', 'Career Health',
        '[
            {
                "type": "header",
                "content": {
                    "domain": "Career",
                    "active_threads": 1,
                    "overall_sentiment": "positive"
                }
            },
            {
                "type": "stats",
                "content": {
                    "threads_tracked": 1,
                    "current_phase": "Interviewing",
                    "days_active": 20
                }
            },
            {
                "type": "summary",
                "content": "Your job search is progressing well. After feeling stuck at your current company, you''ve taken action and found an opportunity that genuinely excites you - both the role itself and the potential for a fresh start in Austin."
            }
        ]'::jsonb,
        'It takes courage to pursue something that matters to you. I''m rooting for you.',
        '["thread:job_search", "domain:career"]'::jsonb,
        true,
        NOW()
    ) ON CONFLICT DO NOTHING;

    -- Communication Profile artifact
    INSERT INTO artifacts (
        user_id, artifact_type, title,
        sections, companion_voice, data_sources,
        is_meaningful, generated_at
    ) VALUES (
        test_user_id, 'communication', 'How You Communicate',
        '[
            {
                "type": "stats",
                "content": {
                    "total_conversations": 10,
                    "total_messages": 42,
                    "avg_messages_per_conversation": 4.2,
                    "initiation_rate": 30
                }
            },
            {
                "type": "patterns",
                "content": [
                    "You tend to share news and updates proactively when excited",
                    "You express vulnerability about anxiety and uncertainty",
                    "You appreciate when conversations flow naturally rather than feeling structured"
                ]
            }
        ]'::jsonb,
        'I''ve noticed you''re really thoughtful in how you share what''s going on. You don''t just tell me the facts - you let me in on how you''re actually feeling about things.',
        '["conversations:10", "patterns:3"]'::jsonb,
        true,
        NOW()
    ) ON CONFLICT DO NOTHING;

    -- Relationship Summary artifact
    INSERT INTO artifacts (
        user_id, artifact_type, title,
        sections, companion_voice, data_sources,
        is_meaningful, generated_at
    ) VALUES (
        test_user_id, 'relationship', 'Our Relationship',
        '[
            {
                "type": "header",
                "content": {
                    "started": "20 days ago",
                    "days_together": 20,
                    "conversation_count": 10
                }
            },
            {
                "type": "learned",
                "content": {
                    "facts_count": 5,
                    "patterns_count": 3,
                    "threads_count": 3,
                    "sample_facts": ["You''ve been in SF for 7 years", "You''re a Product Manager", "You prefer early mornings"]
                }
            },
            {
                "type": "following",
                "content": [
                    {"topic": "Job Search", "domain": "career", "phase": "interviewing"},
                    {"topic": "Austin Move", "domain": "location", "phase": "exploring"},
                    {"topic": "Getting Back to Running", "domain": "health", "phase": "ongoing"}
                ]
            }
        ]'::jsonb,
        'In just 20 days, I feel like I''ve gotten to know you during a really meaningful time in your life. You''re standing at a crossroads - career, location, lifestyle - and I''m honored to be part of figuring it out with you.',
        '["conversations:10", "facts:5", "threads:3"]'::jsonb,
        true,
        NOW()
    ) ON CONFLICT DO NOTHING;

    -- =============================================================================
    -- 4. ARTIFACT EVENTS (for timeline building)
    -- =============================================================================

    INSERT INTO artifact_events (user_id, thread_id, event_type, event_date, description) VALUES
    (test_user_id, thread_job_id, 'start', CURRENT_DATE - INTERVAL '20 days', 'Started thinking about career change'),
    (test_user_id, thread_job_id, 'milestone', CURRENT_DATE - INTERVAL '18 days', 'Updated resume, targeting senior PM roles'),
    (test_user_id, thread_job_id, 'milestone', CURRENT_DATE - INTERVAL '15 days', 'Recruiter reached out about Austin opportunity'),
    (test_user_id, thread_job_id, 'milestone', CURRENT_DATE - INTERVAL '10 days', 'First round interview scheduled'),
    (test_user_id, thread_job_id, 'milestone', CURRENT_DATE - INTERVAL '1 day', 'Interview went well - advancing to final round'),
    (test_user_id, thread_move_id, 'start', CURRENT_DATE - INTERVAL '15 days', 'Started considering Austin as destination'),
    (test_user_id, thread_move_id, 'mention', CURRENT_DATE - INTERVAL '12 days', 'Excited about lower cost of living'),
    (test_user_id, thread_health_id, 'start', CURRENT_DATE - INTERVAL '8 days', 'Started running again for stress management')
    ON CONFLICT DO NOTHING;

    RAISE NOTICE 'Successfully seeded test data for user %', test_user_id;
END $$;
