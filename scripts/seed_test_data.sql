-- =============================================================================
-- Seed Test Data for Chat Companion
-- Run this against your database to populate test data for kvkthecreator@gmail.com
--
-- PREREQUISITES:
-- 1. Run migration 108_fix_messages_table.sql first (adds conversation_id to messages)
-- 2. User kvkthecreator@gmail.com must exist in the database
-- =============================================================================

-- Get the user ID for the test user
DO $$
DECLARE
    test_user_id UUID;
    conv_1_id UUID := gen_random_uuid();
    conv_2_id UUID := gen_random_uuid();
    conv_3_id UUID := gen_random_uuid();
    conv_today_id UUID := gen_random_uuid();
    thread_job_id UUID := gen_random_uuid();
    thread_move_id UUID := gen_random_uuid();
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
    -- 1. CONVERSATIONS & MESSAGES (for unified chat history)
    -- =============================================================================

    -- Conversation from 5 days ago
    INSERT INTO conversations (id, user_id, channel, started_at, message_count, initiated_by)
    VALUES (conv_1_id, test_user_id, 'web', NOW() - INTERVAL '5 days', 4, 'companion')
    ON CONFLICT DO NOTHING;

    -- Messages use conversation_id (requires migration 108)
    INSERT INTO messages (conversation_id, role, content, created_at) VALUES
    (conv_1_id, 'assistant', 'Good morning! How are you feeling about the week ahead?', NOW() - INTERVAL '5 days' + INTERVAL '9 hours'),
    (conv_1_id, 'user', 'Pretty anxious actually. I have a big interview on Thursday.', NOW() - INTERVAL '5 days' + INTERVAL '9 hours 5 minutes'),
    (conv_1_id, 'assistant', 'That''s understandable! What''s the interview for? I''d love to hear about it.', NOW() - INTERVAL '5 days' + INTERVAL '9 hours 6 minutes'),
    (conv_1_id, 'user', 'It''s for a senior product role at a startup. Been job searching for about 2 months now.', NOW() - INTERVAL '5 days' + INTERVAL '9 hours 10 minutes')
    ON CONFLICT DO NOTHING;

    -- Conversation from 3 days ago
    INSERT INTO conversations (id, user_id, channel, started_at, message_count, initiated_by)
    VALUES (conv_2_id, test_user_id, 'web', NOW() - INTERVAL '3 days', 6, 'companion')
    ON CONFLICT DO NOTHING;

    INSERT INTO messages (conversation_id, role, content, created_at) VALUES
    (conv_2_id, 'assistant', 'Tomorrow''s the big day! How are you preparing for the interview?', NOW() - INTERVAL '3 days' + INTERVAL '18 hours'),
    (conv_2_id, 'user', 'Going through their product one more time. Also researching the founders.', NOW() - INTERVAL '3 days' + INTERVAL '18 hours 3 minutes'),
    (conv_2_id, 'assistant', 'That''s smart prep work. What draws you to this particular company?', NOW() - INTERVAL '3 days' + INTERVAL '18 hours 4 minutes'),
    (conv_2_id, 'user', 'They''re building in a space I really care about. And it would mean moving to Austin, which I''ve been thinking about anyway.', NOW() - INTERVAL '3 days' + INTERVAL '18 hours 8 minutes'),
    (conv_2_id, 'assistant', 'Oh interesting! Austin is a big change. Is that exciting or scary or both?', NOW() - INTERVAL '3 days' + INTERVAL '18 hours 9 minutes'),
    (conv_2_id, 'user', 'Definitely both. I''ve been in SF for 7 years. But I think I need a change.', NOW() - INTERVAL '3 days' + INTERVAL '18 hours 15 minutes')
    ON CONFLICT DO NOTHING;

    -- Conversation from yesterday
    INSERT INTO conversations (id, user_id, channel, started_at, message_count, initiated_by)
    VALUES (conv_3_id, test_user_id, 'web', NOW() - INTERVAL '1 day', 4, 'user')
    ON CONFLICT DO NOTHING;

    INSERT INTO messages (conversation_id, role, content, created_at) VALUES
    (conv_3_id, 'user', 'The interview went really well! They want me to come back for a final round.', NOW() - INTERVAL '1 day' + INTERVAL '14 hours'),
    (conv_3_id, 'assistant', 'That''s fantastic news! What made it feel like it went well?', NOW() - INTERVAL '1 day' + INTERVAL '14 hours 1 minute'),
    (conv_3_id, 'user', 'The product discussion was really energizing. We got into the weeds on their roadmap and I had a lot of ideas.', NOW() - INTERVAL '1 day' + INTERVAL '14 hours 5 minutes'),
    (conv_3_id, 'assistant', 'That sounds like great chemistry. When''s the final round?', NOW() - INTERVAL '1 day' + INTERVAL '14 hours 6 minutes')
    ON CONFLICT DO NOTHING;

    -- Today's conversation (current)
    INSERT INTO conversations (id, user_id, channel, started_at, message_count, initiated_by)
    VALUES (conv_today_id, test_user_id, 'web', NOW(), 2, 'companion')
    ON CONFLICT DO NOTHING;

    INSERT INTO messages (conversation_id, role, content, created_at) VALUES
    (conv_today_id, 'assistant', 'Good morning! Still riding high from yesterday''s interview? How are you feeling today?', NOW() + INTERVAL '9 hours'),
    (conv_today_id, 'user', 'Yeah! Just found out the final round is next Tuesday. Starting to feel real.', NOW() + INTERVAL '9 hours 2 minutes')
    ON CONFLICT DO NOTHING;

    -- =============================================================================
    -- 2. USER CONTEXT (facts, threads, follow-ups)
    -- =============================================================================

    -- Facts about the user
    INSERT INTO user_context (user_id, category, key, value, importance_score, emotional_valence, source) VALUES
    (test_user_id, 'fact', 'current_location', 'San Francisco', 0.8, 0, 'extracted'),
    (test_user_id, 'fact', 'years_in_sf', '7 years', 0.6, 0, 'extracted'),
    (test_user_id, 'fact', 'profession', 'Product Manager', 0.9, 0, 'extracted'),
    (test_user_id, 'preference', 'work_style', 'Prefers early mornings for deep work', 0.5, 1, 'extracted'),
    (test_user_id, 'relationship', 'support_network', 'Has close friends in SF tech community', 0.7, 1, 'extracted')
    ON CONFLICT (user_id, category, key) DO UPDATE SET value = EXCLUDED.value;

    -- Active thread: Job Search
    INSERT INTO user_context (
        id, user_id, category, key, value,
        importance_score, emotional_valence,
        tier, domain, template_id, phase, priority_weight
    ) VALUES (
        thread_job_id, test_user_id, 'thread', 'job_search',
        'Looking for senior product role at startups. Had successful interview, advancing to final round at Austin company.',
        0.95, 1,
        'active', 'career', job_template_id, 'interviewing', 1.5
    ) ON CONFLICT (user_id, category, key) DO UPDATE SET
        value = EXCLUDED.value,
        phase = EXCLUDED.phase,
        updated_at = NOW();

    -- Active thread: Potential Move
    INSERT INTO user_context (
        id, user_id, category, key, value,
        importance_score, emotional_valence,
        tier, domain, template_id, phase, priority_weight
    ) VALUES (
        thread_move_id, test_user_id, 'thread', 'considering_austin',
        'Considering moving to Austin if job works out. Has been in SF for 7 years, feeling ready for change.',
        0.8, 0,
        'active', 'location', move_template_id, 'exploring', 1.2
    ) ON CONFLICT (user_id, category, key) DO UPDATE SET
        value = EXCLUDED.value,
        updated_at = NOW();

    -- Follow-up items
    INSERT INTO user_context (user_id, category, key, value, importance_score, expires_at) VALUES
    (test_user_id, 'follow_up', 'final_interview_tuesday', 'Final round interview scheduled for Tuesday', 0.95, NOW() + INTERVAL '7 days'),
    (test_user_id, 'follow_up', 'austin_research', 'User is researching Austin neighborhoods', 0.6, NOW() + INTERVAL '14 days')
    ON CONFLICT (user_id, category, key) DO UPDATE SET value = EXCLUDED.value;

    -- Patterns/Observations
    INSERT INTO user_context (user_id, category, key, value, importance_score, emotional_valence) VALUES
    (test_user_id, 'emotion', 'current_mood', 'Cautiously optimistic about career transition', 0.7, 1),
    (test_user_id, 'situation', 'life_transition', 'At an inflection point - career and location both in flux', 0.8, 0)
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
                    "subtitle": "Started 2 months ago",
                    "status": "Interviewing"
                }
            },
            {
                "type": "timeline",
                "events": [
                    {"date": "2 months ago", "description": "Started job search", "type": "start"},
                    {"date": "5 days ago", "description": "Mentioned big interview coming up", "type": "milestone"},
                    {"date": "Yesterday", "description": "Interview went well - advancing to final round!", "type": "milestone"}
                ]
            },
            {
                "type": "observations",
                "content": "You seem energized by product discussions and strategic work. The Austin opportunity combines your career goals with a fresh start you''ve been thinking about."
            },
            {
                "type": "key_details",
                "items": [
                    "Senior product role at startup",
                    "Role would be in Austin (potential relocation)",
                    "Strong product discussion chemistry in interview",
                    "Final round scheduled for Tuesday"
                ]
            }
        ]'::jsonb,
        'I can see how much thought you''ve put into this transition. The fact that the interview felt energizing is a really good sign.',
        '["thread:job_search", "messages:10", "patterns:2"]'::jsonb,
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
                    "days_active": 60
                }
            },
            {
                "type": "summary",
                "content": "Your job search is progressing well. After 2 months of searching, you''ve found an opportunity that genuinely excites you - both the role itself and the potential for a fresh start in Austin."
            }
        ]'::jsonb,
        'It takes courage to pursue something that matters to you. I''m rooting for you.',
        '["thread:job_search", "domain:career"]'::jsonb,
        true,
        NOW()
    ) ON CONFLICT DO NOTHING;

    -- =============================================================================
    -- 4. ARTIFACT EVENTS (for timeline building)
    -- =============================================================================

    INSERT INTO artifact_events (user_id, thread_id, event_type, event_date, description) VALUES
    (test_user_id, thread_job_id, 'start', CURRENT_DATE - INTERVAL '60 days', 'Started looking for senior product role'),
    (test_user_id, thread_job_id, 'mention', CURRENT_DATE - INTERVAL '5 days', 'Feeling anxious about upcoming interview'),
    (test_user_id, thread_job_id, 'milestone', CURRENT_DATE - INTERVAL '1 day', 'Interview went really well - advancing to final round')
    ON CONFLICT DO NOTHING;

    RAISE NOTICE 'Successfully seeded test data for user %', test_user_id;
END $$;
