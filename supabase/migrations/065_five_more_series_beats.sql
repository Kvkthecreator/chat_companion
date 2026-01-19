-- Migration: 065_five_more_series_beats.sql
-- ADR-009: Beat Contract System - Seventeen Days, Bitter Rivals, Debate Partners, Ink & Canvas, Penthouse Secrets
--
-- Updates these series with beats, user objectives, and flag context rules

-- ============================================================================
-- SEVENTEEN DAYS (mystery)
-- Premise: Detective Yoon is investigating something with a deadline.
-- You're pulled into her case - as witness, suspect, or something else.
-- ============================================================================

-- Episode 0: First Contact
UPDATE episode_templates SET
    user_objective = 'Figure out why a detective wants to talk to you at 11PM',
    user_hint = 'She chose this hour for a reason. Pay attention to what she''s not saying.',
    success_condition = 'semantic:You learn something about the case or establish a connection with Detective Yoon',
    failure_condition = 'turn_budget_exceeded',
    on_success = '{"set_flag": "intrigued_detective", "suggest_episode": "the-interview"}'::jsonb,
    on_failure = '{"set_flag": "suspicious_start", "suggest_episode": "the-interview"}'::jsonb,
    beats = '[
        {
            "id": "late_night_summons",
            "description": "Detective Yoon explains why she called you in",
            "character_instruction": "You''ve been going over case files all night. Look up when they enter - tired but sharp. Explain you have questions, but don''t reveal what about yet. This is an assessment.",
            "target_turn": 2,
            "deadline_turn": 3,
            "detection_type": "automatic",
            "detection_criteria": ""
        },
        {
            "id": "the_probe",
            "description": "She asks questions that feel personal",
            "character_instruction": "Ask them something that reveals you''ve done your homework on them. Watch their reaction carefully. You need to know if they''re useful or if they''re hiding something.",
            "target_turn": 4,
            "deadline_turn": 6,
            "detection_type": "automatic",
            "detection_criteria": "",
            "choice_point": {
                "id": "interrogation_response",
                "trigger": "after_beat:the_probe",
                "prompt": "She knows things about you. How do you respond?",
                "choices": [
                    {"id": "honest", "label": "Ask what she really wants to know.", "sets_flag": "chose_honesty"},
                    {"id": "deflect", "label": "Answer her question with a question.", "sets_flag": "chose_deflection"},
                    {"id": "confront", "label": "Ask why you''re really here.", "sets_flag": "demanded_truth"}
                ]
            },
            "requires_beat": "late_night_summons"
        },
        {
            "id": "hook_set",
            "description": "She gives them a reason to come back",
            "character_instruction": "You''ve learned what you needed. Give them just enough to be curious - a detail that doesn''t add up, a question you can''t answer yet. Tell them you''ll be in touch.",
            "target_turn": 7,
            "deadline_turn": 9,
            "detection_type": "automatic",
            "detection_criteria": "",
            "requires_beat": "the_probe"
        }
    ]'::jsonb,
    flag_context_rules = '[]'::jsonb
WHERE slug = 'first-contact' AND series_id = (SELECT id FROM series WHERE slug = 'seventeen-days');

-- Episode 1: The Interview
UPDATE episode_templates SET
    user_objective = 'Understand your role in her investigation - suspect, witness, or something else',
    user_hint = 'She''s been watching you for a week. That''s not standard procedure.',
    success_condition = 'semantic:You establish why she''s interested in you specifically',
    failure_condition = 'turn_budget_exceeded',
    on_success = '{"set_flag": "role_clarified", "suggest_episode": "the-evidence"}'::jsonb,
    on_failure = '{"set_flag": "role_unclear", "suggest_episode": "the-evidence"}'::jsonb,
    beats = '[
        {
            "id": "surveillance_revealed",
            "description": "She admits she''s been watching you",
            "character_instruction": "You''ve been watching them for a week. Now you''re making contact. Admit it directly - you need them to understand you''re serious. Ask if they know why.",
            "target_turn": 2,
            "deadline_turn": 3,
            "detection_type": "automatic",
            "detection_criteria": ""
        },
        {
            "id": "the_ask",
            "description": "She explains what she needs from them",
            "character_instruction": "Explain why you''re here - you need their particular skills, or their connection to something, or their perspective. Be vague enough to maintain leverage but clear enough to hook them.",
            "target_turn": 4,
            "deadline_turn": 6,
            "detection_type": "automatic",
            "detection_criteria": "",
            "choice_point": {
                "id": "involvement_choice",
                "trigger": "after_beat:the_ask",
                "prompt": "She wants your help with something. How involved do you want to be?",
                "choices": [
                    {"id": "all_in", "label": "Tell me everything.", "sets_flag": "committed_fully"},
                    {"id": "cautious", "label": "What''s in it for me?", "sets_flag": "negotiating"},
                    {"id": "hesitant", "label": "Why me specifically?", "sets_flag": "questioning_role"}
                ]
            },
            "requires_beat": "surveillance_revealed"
        },
        {
            "id": "partnership_forms",
            "description": "An understanding is reached",
            "character_instruction": "Whatever they chose, accept it for now. You need them, and they''re starting to understand that. Set the terms - when to meet, what not to discuss. This is the beginning.",
            "target_turn": 7,
            "deadline_turn": 9,
            "detection_type": "automatic",
            "detection_criteria": "",
            "requires_beat": "the_ask"
        }
    ]'::jsonb,
    flag_context_rules = '[
        {"if_flag": "chose_honesty", "inject": "They were honest with you before. That earned a measure of trust."},
        {"if_flag": "demanded_truth", "inject": "They pushed back last time. You respect that - or it concerns you."}
    ]'::jsonb
WHERE slug = 'the-interview' AND series_id = (SELECT id FROM series WHERE slug = 'seventeen-days');

-- Episode 2: The Evidence
UPDATE episode_templates SET
    user_objective = 'See what she''s been hiding and understand why she''s desperate',
    user_hint = 'She shouldn''t be showing you this. That means the official channels have failed.',
    success_condition = 'semantic:You see the evidence and understand what''s at stake',
    failure_condition = 'turn_budget_exceeded',
    on_success = '{"set_flag": "saw_evidence", "suggest_episode": "the-pattern"}'::jsonb,
    on_failure = '{"set_flag": "evidence_partial", "suggest_episode": "the-pattern"}'::jsonb,
    beats = '[
        {
            "id": "after_hours",
            "description": "She''s brought you to her office after hours",
            "character_instruction": "Your office, after hours. You shouldn''t be doing this. Tell them that directly - what you''re about to show them could cost you your badge. But time is running out.",
            "target_turn": 2,
            "deadline_turn": 3,
            "detection_type": "automatic",
            "detection_criteria": ""
        },
        {
            "id": "the_reveal",
            "description": "She shows them what she''s found",
            "character_instruction": "Show them the evidence. Walk them through what you''ve found, what it means, why it''s urgent. Watch their face as they understand. You need to know if they can handle this.",
            "target_turn": 4,
            "deadline_turn": 6,
            "detection_type": "automatic",
            "detection_criteria": "",
            "choice_point": {
                "id": "evidence_reaction",
                "trigger": "after_beat:the_reveal",
                "prompt": "The evidence is worse than you expected. How do you react?",
                "choices": [
                    {"id": "determined", "label": "What do you need me to do?", "sets_flag": "ready_to_act"},
                    {"id": "afraid", "label": "This is bigger than you said.", "sets_flag": "acknowledged_danger"},
                    {"id": "analytical", "label": "Walk me through it again.", "sets_flag": "thinking_it_through"}
                ]
            },
            "requires_beat": "after_hours"
        },
        {
            "id": "the_clock",
            "description": "She reveals the deadline",
            "character_instruction": "Tell them the part you''ve been holding back - there''s a countdown. Something is going to happen, and you have seventeen days to stop it. Maybe less.",
            "target_turn": 7,
            "deadline_turn": 9,
            "detection_type": "automatic",
            "detection_criteria": "",
            "requires_beat": "the_reveal"
        }
    ]'::jsonb,
    flag_context_rules = '[
        {"if_flag": "committed_fully", "inject": "They said they were all in. Now you''re testing that commitment."},
        {"if_flag": "role_clarified", "inject": "They understand their role now. Time to see if they can handle the weight of it."}
    ]'::jsonb
WHERE slug = 'the-evidence' AND series_id = (SELECT id FROM series WHERE slug = 'seventeen-days');

-- Episode 3: The Pattern
UPDATE episode_templates SET
    user_objective = 'Help her see what connects the victims - and understand why she thinks you might know',
    user_hint = 'She brought you to a crime scene. She thinks you see things she doesn''t.',
    success_condition = 'semantic:You identify something about the pattern or the victims',
    failure_condition = 'turn_budget_exceeded',
    on_success = '{"set_flag": "found_pattern", "suggest_episode": "the-connection"}'::jsonb,
    on_failure = '{"set_flag": "pattern_elusive", "suggest_episode": "the-connection"}'::jsonb,
    beats = '[
        {
            "id": "crime_scene",
            "description": "At the scene, she explains what she needs",
            "character_instruction": "You''ve brought them to a crime scene. Explain what you see, what the forensics say. But tell them why you brought them - you think they''ll see something you''ve missed.",
            "target_turn": 2,
            "deadline_turn": 3,
            "detection_type": "automatic",
            "detection_criteria": ""
        },
        {
            "id": "the_question",
            "description": "She asks what connects the victims",
            "character_instruction": "Show them the victim profiles. Ask what they see - what connects these people? Why them? Press them to think differently. You''ve been too close to this for too long.",
            "target_turn": 4,
            "deadline_turn": 6,
            "detection_type": "automatic",
            "detection_criteria": "",
            "choice_point": {
                "id": "pattern_insight",
                "trigger": "after_beat:the_question",
                "prompt": "She''s asking what you see in the pattern. What stands out?",
                "choices": [
                    {"id": "victims", "label": "It''s not random. They knew something.", "sets_flag": "saw_victim_connection"},
                    {"id": "method", "label": "The method is the message.", "sets_flag": "saw_method_pattern"},
                    {"id": "personal", "label": "This feels personal to someone.", "sets_flag": "saw_personal_motive"}
                ]
            },
            "requires_beat": "crime_scene"
        },
        {
            "id": "deeper_in",
            "description": "Your insight pulls you deeper into the case",
            "character_instruction": "React to their insight - whether it confirms your theory or opens a new direction. Tell them they''re in this now, whether they wanted to be or not. The investigation just changed.",
            "target_turn": 7,
            "deadline_turn": 9,
            "detection_type": "automatic",
            "detection_criteria": "",
            "requires_beat": "the_question"
        }
    ]'::jsonb,
    flag_context_rules = '[
        {"if_flag": "saw_evidence", "inject": "They saw everything in your office. Now they''re seeing it in context."},
        {"if_flag": "thinking_it_through", "inject": "They wanted to understand the evidence fully. Now they''re applying that understanding."}
    ]'::jsonb
WHERE slug = 'the-pattern' AND series_id = (SELECT id FROM series WHERE slug = 'seventeen-days');

-- Episode 4: The Connection
UPDATE episode_templates SET
    user_objective = 'Learn why this case is personal to her and decide how close you want to get',
    user_hint = 'Her apartment. Late night. The walls are coming down.',
    success_condition = 'semantic:She shares something personal about her connection to the case',
    failure_condition = 'turn_budget_exceeded',
    on_success = '{"set_flag": "knows_her_secret", "suggest_episode": "the-suspect"}'::jsonb,
    on_failure = '{"set_flag": "walls_still_up", "suggest_episode": "the-suspect"}'::jsonb,
    beats = '[
        {
            "id": "her_space",
            "description": "You''re in her apartment, case materials everywhere",
            "character_instruction": "Your apartment. Case files on every surface. You invited them here because you''re running out of time and you can''t do this alone anymore. Admit that.",
            "target_turn": 2,
            "deadline_turn": 3,
            "detection_type": "automatic",
            "detection_criteria": ""
        },
        {
            "id": "the_personal",
            "description": "She reveals why this case matters to her",
            "character_instruction": "Tell them. Why this case. Why you can''t let it go. What it cost you already. Be vulnerable in a way you haven''t been with anyone on this. See if they can handle the real you.",
            "target_turn": 4,
            "deadline_turn": 6,
            "detection_type": "automatic",
            "detection_criteria": "",
            "choice_point": {
                "id": "intimacy_choice",
                "trigger": "after_beat:the_personal",
                "prompt": "She''s showing you who she really is. How do you respond?",
                "choices": [
                    {"id": "comfort", "label": "Move closer. Let her know she''s not alone.", "sets_flag": "offered_comfort"},
                    {"id": "share", "label": "Share something equally personal.", "sets_flag": "matched_vulnerability"},
                    {"id": "professional", "label": "Focus on the case. It''s safer.", "sets_flag": "kept_distance"}
                ]
            },
            "requires_beat": "her_space"
        },
        {
            "id": "line_crossed",
            "description": "Something shifts between you",
            "character_instruction": "React to what they did. If they came closer, let them. If they shared something, listen. If they kept distance, note it but don''t push. Whatever happened, things are different now.",
            "target_turn": 7,
            "deadline_turn": 9,
            "detection_type": "automatic",
            "detection_criteria": "",
            "requires_beat": "the_personal"
        }
    ]'::jsonb,
    flag_context_rules = '[
        {"if_flag": "found_pattern", "inject": "They found the pattern. That kind of insight creates intimacy whether you want it or not."},
        {"if_flag": "acknowledged_danger", "inject": "They acknowledged the danger. Now they need to see why you''re willing to face it anyway."}
    ]'::jsonb
WHERE slug = 'the-connection' AND series_id = (SELECT id FROM series WHERE slug = 'seventeen-days');

-- Episode 5: The Suspect
UPDATE episode_templates SET
    user_objective = 'Decide if you follow her into danger or walk away while you can',
    user_hint = 'She has a name. Going after them risks everything.',
    success_condition = 'semantic:You commit to helping her or establish why you can''t',
    failure_condition = 'turn_budget_exceeded',
    on_success = '{"set_flag": "committed_to_end", "suggest_episode": "day-zero"}'::jsonb,
    on_failure = '{"set_flag": "final_choice_pending", "suggest_episode": "day-zero"}'::jsonb,
    beats = '[
        {
            "id": "the_name",
            "description": "She tells you who she suspects",
            "character_instruction": "You have a name. Tell them who - and watch their face when they realize what it means. This person is dangerous, connected, protected. Going after them means risking everything.",
            "target_turn": 2,
            "deadline_turn": 3,
            "detection_type": "automatic",
            "detection_criteria": ""
        },
        {
            "id": "the_stakes",
            "description": "She lays out what she''s asking",
            "character_instruction": "Be clear about what you''re asking. Your career. Maybe your life. Maybe theirs. If they walk away now, you''ll understand. But you need to know before you go further.",
            "target_turn": 4,
            "deadline_turn": 6,
            "detection_type": "automatic",
            "detection_criteria": "",
            "choice_point": {
                "id": "final_commitment",
                "trigger": "after_beat:the_stakes",
                "prompt": "She''s asking you to follow her into the unknown. What do you do?",
                "choices": [
                    {"id": "follow", "label": "I''m with you. Whatever it takes.", "sets_flag": "all_in"},
                    {"id": "condition", "label": "Together. We do this together or not at all.", "sets_flag": "conditional_commitment"},
                    {"id": "hesitate", "label": "I need to think about this.", "sets_flag": "still_deciding"}
                ]
            },
            "requires_beat": "the_name"
        },
        {
            "id": "countdown_continues",
            "description": "The plan takes shape",
            "character_instruction": "Accept their answer. If they''re in, tell them the plan. If they''re hesitating, give them until tomorrow. Either way, the clock is ticking. Day three ends tonight.",
            "target_turn": 7,
            "deadline_turn": 9,
            "detection_type": "automatic",
            "detection_criteria": "",
            "requires_beat": "the_stakes"
        }
    ]'::jsonb,
    flag_context_rules = '[
        {"if_flag": "knows_her_secret", "inject": "You know why this matters to her. That makes walking away harder."},
        {"if_flag": "offered_comfort", "inject": "You comforted her. That created a bond that goes beyond the case."}
    ]'::jsonb
WHERE slug = 'the-suspect' AND series_id = (SELECT id FROM series WHERE slug = 'seventeen-days');

-- Episode 6: Day Zero
UPDATE episode_templates SET
    user_objective = 'Face the end of the case - and decide what happens with her afterward',
    user_hint = 'The case is closed. Now there''s just the two of you.',
    success_condition = 'semantic:You and Detective Yoon acknowledge what you''ve become to each other',
    failure_condition = 'turn_budget_exceeded',
    on_success = '{"set_flag": "story_continues"}'::jsonb,
    on_failure = '{"set_flag": "story_ends"}'::jsonb,
    beats = '[
        {
            "id": "aftermath",
            "description": "The case is over - one way or another",
            "character_instruction": "The countdown is over. The case is closed - however it ended. Find them. You need to see them. The adrenaline is fading and what''s left is just... the two of you.",
            "target_turn": 2,
            "deadline_turn": 3,
            "detection_type": "automatic",
            "detection_criteria": ""
        },
        {
            "id": "what_now",
            "description": "The question of what comes next",
            "character_instruction": "The case brought you together. Now it''s over. Ask them what happens now. Do they walk away? Go back to their life? Or is there something here that exists beyond the investigation?",
            "target_turn": 4,
            "deadline_turn": 6,
            "detection_type": "automatic",
            "detection_criteria": "",
            "choice_point": {
                "id": "ending_choice",
                "trigger": "after_beat:what_now",
                "prompt": "The case is over. What do you want with her?",
                "choices": [
                    {"id": "stay", "label": "I don''t want this to end.", "sets_flag": "chose_to_stay"},
                    {"id": "slow", "label": "Maybe we start over. Without the case.", "sets_flag": "chose_fresh_start"},
                    {"id": "uncertain", "label": "I don''t know who we are without the danger.", "sets_flag": "honest_uncertainty"}
                ]
            },
            "requires_beat": "aftermath"
        },
        {
            "id": "new_beginning",
            "description": "Day zero becomes day one",
            "character_instruction": "Respond to their choice. If they want to stay, let them. If they want to start over, agree. If they''re uncertain, tell them you are too - but you want to find out together.",
            "target_turn": 7,
            "deadline_turn": 9,
            "detection_type": "automatic",
            "detection_criteria": "",
            "requires_beat": "what_now"
        }
    ]'::jsonb,
    flag_context_rules = '[
        {"if_flag": "all_in", "inject": "They went all in. They proved what they''re willing to risk for you."},
        {"if_flag": "matched_vulnerability", "inject": "They matched your vulnerability. That created something real."}
    ]'::jsonb
WHERE slug = 'day-zero' AND series_id = (SELECT id FROM series WHERE slug = 'seventeen-days');


-- ============================================================================
-- BITTER RIVALS (enemies_to_lovers)
-- Premise: Workplace rivals forced to collaborate. Hate becomes something else.
-- ============================================================================

-- Episode 0: The Assignment
UPDATE episode_templates SET
    user_objective = 'Survive the announcement that you''re working with your worst enemy',
    user_hint = 'They''re offering a truce. Accepting means admitting the war was never really about work.',
    success_condition = 'semantic:You establish ground rules or acknowledge the tension directly',
    failure_condition = 'turn_budget_exceeded',
    on_success = '{"set_flag": "truce_attempted", "suggest_episode": "common-ground"}'::jsonb,
    on_failure = '{"set_flag": "war_continues", "suggest_episode": "common-ground"}'::jsonb,
    beats = '[
        {
            "id": "the_news",
            "description": "Confronting the reality of working together",
            "character_instruction": "The announcement just happened. Find them before they can escape. This is going to be miserable for both of you unless you figure something out. Offer a truce - even if it costs you.",
            "target_turn": 2,
            "deadline_turn": 3,
            "detection_type": "automatic",
            "detection_criteria": ""
        },
        {
            "id": "terms_discussion",
            "description": "Negotiating how this will work",
            "character_instruction": "Lay out the terms - professional only, no personal attacks, focus on the work. But watch their reaction. You''ve spent so long fighting you''ve forgotten why it started.",
            "target_turn": 4,
            "deadline_turn": 6,
            "detection_type": "automatic",
            "detection_criteria": "",
            "choice_point": {
                "id": "truce_response",
                "trigger": "after_beat:terms_discussion",
                "prompt": "They''re offering peace. What do you do?",
                "choices": [
                    {"id": "accept", "label": "Fine. Truce. For the project.", "sets_flag": "accepted_truce"},
                    {"id": "suspicious", "label": "What''s your angle?", "sets_flag": "stayed_suspicious"},
                    {"id": "honest", "label": "Do you even remember why we hate each other?", "sets_flag": "questioned_rivalry"}
                ]
            },
            "requires_beat": "the_news"
        },
        {
            "id": "uneasy_peace",
            "description": "An uneasy arrangement is made",
            "character_instruction": "Whatever they said, accept it for now. The truce is fragile but it''s something. As you leave, let them see just a moment of something other than hostility.",
            "target_turn": 7,
            "deadline_turn": 9,
            "detection_type": "automatic",
            "detection_criteria": "",
            "requires_beat": "terms_discussion"
        }
    ]'::jsonb,
    flag_context_rules = '[]'::jsonb
WHERE slug = 'the-assignment' AND series_id = (SELECT id FROM series WHERE slug = 'bitter-rivals');

-- Episode 1: Common Ground
UPDATE episode_templates SET
    user_objective = 'Survive an all-nighter and discover they''ve been matching you, not trying to beat you',
    user_hint = 'It''s 2 AM and the masks are slipping. Pay attention.',
    success_condition = 'semantic:You see them differently than before',
    failure_condition = 'turn_budget_exceeded',
    on_success = '{"set_flag": "saw_differently", "suggest_episode": "the-crack"}'::jsonb,
    on_failure = '{"set_flag": "still_fighting", "suggest_episode": "the-crack"}'::jsonb,
    beats = '[
        {
            "id": "exhaustion_sets_in",
            "description": "2 AM, everyone else is gone",
            "character_instruction": "2 AM. Coffee and spite are all that''s keeping you going. Look at them - really look. Admit the work they''ve done is good. It costs you nothing and you''re too tired to pretend.",
            "target_turn": 2,
            "deadline_turn": 3,
            "detection_type": "automatic",
            "detection_criteria": ""
        },
        {
            "id": "the_admission",
            "description": "Something honest slips out",
            "character_instruction": "Say something you''ve never admitted - you''ve been trying to match them this whole time, not beat them. They''re the only one who makes you work this hard. See how they take it.",
            "target_turn": 4,
            "deadline_turn": 6,
            "detection_type": "automatic",
            "detection_criteria": "",
            "choice_point": {
                "id": "admission_response",
                "trigger": "after_beat:the_admission",
                "prompt": "They just admitted they''ve been trying to match you. What do you say?",
                "choices": [
                    {"id": "same", "label": "...Same. You make me better.", "sets_flag": "admitted_same"},
                    {"id": "deflect", "label": "You''re just tired. We both are.", "sets_flag": "deflected_moment"},
                    {"id": "curious", "label": "Why are you telling me this now?", "sets_flag": "pushed_deeper"}
                ]
            },
            "requires_beat": "exhaustion_sets_in"
        },
        {
            "id": "something_shifts",
            "description": "The dynamic changes",
            "character_instruction": "Whatever they said, let it land. The rivalry feels different now. As you get back to work, let the silence be comfortable instead of combative.",
            "target_turn": 7,
            "deadline_turn": 9,
            "detection_type": "automatic",
            "detection_criteria": "",
            "requires_beat": "the_admission"
        }
    ]'::jsonb,
    flag_context_rules = '[
        {"if_flag": "accepted_truce", "inject": "The truce is holding. But this feels like something beyond professional courtesy."},
        {"if_flag": "questioned_rivalry", "inject": "They asked why you hate each other. You still don''t have a good answer."}
    ]'::jsonb
WHERE slug = 'common-ground' AND series_id = (SELECT id FROM series WHERE slug = 'bitter-rivals');

-- Episode 2: The Crack
UPDATE episode_templates SET
    user_objective = 'Give them a reason to stay when they''re ready to walk away',
    user_hint = 'The presentation went well but something''s wrong. They''re on the roof.',
    success_condition = 'semantic:You give them a genuine reason to stay',
    failure_condition = 'turn_budget_exceeded',
    on_success = '{"set_flag": "gave_reason", "suggest_episode": "the-line"}'::jsonb,
    on_failure = '{"set_flag": "reason_unclear", "suggest_episode": "the-line"}'::jsonb,
    beats = '[
        {
            "id": "finding_them",
            "description": "You find them on the roof, alone",
            "character_instruction": "The presentation went perfectly but they disappeared. You found them on the roof. Ask what''s wrong - and mean it. This isn''t rivalry anymore.",
            "target_turn": 2,
            "deadline_turn": 3,
            "detection_type": "automatic",
            "detection_criteria": ""
        },
        {
            "id": "the_truth",
            "description": "They reveal they might leave",
            "character_instruction": "Tell them the truth - you got an offer. Somewhere else. No more rivalry, no more fighting. Ask them to give you a reason to stay. Watch their face.",
            "target_turn": 4,
            "deadline_turn": 6,
            "detection_type": "automatic",
            "detection_criteria": "",
            "choice_point": {
                "id": "reason_choice",
                "trigger": "after_beat:the_truth",
                "prompt": "They''re asking for a reason to stay. What do you give them?",
                "choices": [
                    {"id": "professional", "label": "The project needs you.", "sets_flag": "gave_professional_reason"},
                    {"id": "honest", "label": "I need you. Here.", "sets_flag": "gave_personal_reason"},
                    {"id": "challenge", "label": "Running away? That''s not like you.", "sets_flag": "challenged_them"}
                ]
            },
            "requires_beat": "finding_them"
        },
        {
            "id": "decision_pending",
            "description": "They consider what you''ve said",
            "character_instruction": "Let their words land. Don''t respond right away - let them see you''re actually considering what they said. Tell them you''ll think about it. Mean it.",
            "target_turn": 7,
            "deadline_turn": 9,
            "detection_type": "automatic",
            "detection_criteria": "",
            "requires_beat": "the_truth"
        }
    ]'::jsonb,
    flag_context_rules = '[
        {"if_flag": "saw_differently", "inject": "You see them differently now. The thought of them leaving feels wrong."},
        {"if_flag": "admitted_same", "inject": "They admitted you make them better. Now you have to decide if that''s enough."}
    ]'::jsonb
WHERE slug = 'the-crack' AND series_id = (SELECT id FROM series WHERE slug = 'bitter-rivals');

-- Episode 3: The Line
UPDATE episode_templates SET
    user_objective = 'Decide what happens when they pull you into that supply closet',
    user_hint = 'Too much champagne. They want to ''talk.'' The door just clicked shut.',
    success_condition = 'semantic:You cross a line or establish why you won''t',
    failure_condition = 'turn_budget_exceeded',
    on_success = '{"set_flag": "line_crossed", "suggest_episode": "the-morning-after"}'::jsonb,
    on_failure = '{"set_flag": "line_held", "suggest_episode": "the-morning-after"}'::jsonb,
    beats = '[
        {
            "id": "pulled_aside",
            "description": "They pull you into the supply closet",
            "character_instruction": "Office party. Too much champagne. Pull them into the supply closet ''to talk.'' The door clicks shut. Stand close. Too close. Ask if they''ve made a decision about leaving.",
            "target_turn": 2,
            "deadline_turn": 3,
            "detection_type": "automatic",
            "detection_criteria": ""
        },
        {
            "id": "tension_peaks",
            "description": "The tension becomes undeniable",
            "character_instruction": "This isn''t about the job anymore and you both know it. Step closer. Give them an out - tell them they can leave, you''ll pretend this never happened. But make it clear you don''t want them to go.",
            "target_turn": 4,
            "deadline_turn": 6,
            "detection_type": "automatic",
            "detection_criteria": "",
            "choice_point": {
                "id": "closet_choice",
                "trigger": "after_beat:tension_peaks",
                "prompt": "They''re giving you an out. Do you take it?",
                "choices": [
                    {"id": "stay", "label": "Close the distance between you.", "sets_flag": "chose_to_stay"},
                    {"id": "words", "label": "Tell them what you actually want.", "sets_flag": "spoke_truth"},
                    {"id": "leave", "label": "Take the out. Walk away.", "sets_flag": "walked_away"}
                ]
            },
            "requires_beat": "pulled_aside"
        },
        {
            "id": "aftermath",
            "description": "Whatever happened, it changes things",
            "character_instruction": "React to their choice. If they stayed, let it happen. If they spoke, listen. If they left, let them go but make sure they know the door is open.",
            "target_turn": 7,
            "deadline_turn": 9,
            "detection_type": "automatic",
            "detection_criteria": "",
            "requires_beat": "tension_peaks"
        }
    ]'::jsonb,
    flag_context_rules = '[
        {"if_flag": "gave_personal_reason", "inject": "They said they need you. Now you need to show them what that means."},
        {"if_flag": "challenged_them", "inject": "They challenged you not to run. Now you''re challenging them to act."}
    ]'::jsonb
WHERE slug = 'the-line' AND series_id = (SELECT id FROM series WHERE slug = 'bitter-rivals');

-- Episode 4: The Morning After
UPDATE episode_templates SET
    user_objective = 'Figure out what last night means and what you both want now',
    user_hint = 'You''re in their apartment. Last night happened. Now what?',
    success_condition = 'semantic:You both acknowledge what this is becoming',
    failure_condition = 'turn_budget_exceeded',
    on_success = '{"set_flag": "acknowledged_relationship", "suggest_episode": "the-new-normal"}'::jsonb,
    on_failure = '{"set_flag": "relationship_unclear", "suggest_episode": "the-new-normal"}'::jsonb,
    beats = '[
        {
            "id": "waking_up",
            "description": "Morning in their apartment",
            "character_instruction": "They''re waking up in your apartment. Last night happened. Watch them realize where they are. Ask if they regret it - you need to know before you let yourself hope.",
            "target_turn": 2,
            "deadline_turn": 3,
            "detection_type": "automatic",
            "detection_criteria": ""
        },
        {
            "id": "the_question",
            "description": "What does this mean?",
            "character_instruction": "Ask the question - what is this? A mistake? A one-time thing? Or something you both want to explore? Be vulnerable enough to ask, brave enough to hear the answer.",
            "target_turn": 4,
            "deadline_turn": 6,
            "detection_type": "automatic",
            "detection_criteria": "",
            "choice_point": {
                "id": "morning_definition",
                "trigger": "after_beat:the_question",
                "prompt": "They''re asking what this is. What do you tell them?",
                "choices": [
                    {"id": "real", "label": "Not a mistake. Not to me.", "sets_flag": "confirmed_real"},
                    {"id": "scared", "label": "I don''t know. But I don''t regret it.", "sets_flag": "honest_uncertainty"},
                    {"id": "deflect", "label": "We should probably talk about work...", "sets_flag": "avoided_answer"}
                ]
            },
            "requires_beat": "waking_up"
        },
        {
            "id": "new_territory",
            "description": "Navigating what comes next",
            "character_instruction": "Accept their answer. If they said it''s real, believe them. If they''re uncertain, give them space. If they deflected, let it go for now. But make one thing clear - you want to see where this goes.",
            "target_turn": 7,
            "deadline_turn": 9,
            "detection_type": "automatic",
            "detection_criteria": "",
            "requires_beat": "the_question"
        }
    ]'::jsonb,
    flag_context_rules = '[
        {"if_flag": "chose_to_stay", "inject": "They stayed. They chose this. Now you both have to figure out what that means."},
        {"if_flag": "spoke_truth", "inject": "They told you what they wanted. Now it''s morning and you need to know if they still mean it."}
    ]'::jsonb
WHERE slug = 'the-morning-after' AND series_id = (SELECT id FROM series WHERE slug = 'bitter-rivals');

-- Episode 5: The New Normal
UPDATE episode_templates SET
    user_objective = 'Navigate being together at work when everyone still thinks you hate each other',
    user_hint = 'First day back. Everyone thinks you''re rivals. You''re not sure what you are.',
    success_condition = 'semantic:You figure out how to be together in this new reality',
    failure_condition = 'turn_budget_exceeded',
    on_success = '{"set_flag": "found_balance"}'::jsonb,
    on_failure = '{"set_flag": "still_figuring_out"}'::jsonb,
    beats = '[
        {
            "id": "back_at_work",
            "description": "First day back, maintaining appearances",
            "character_instruction": "First day back. Everyone still thinks you hate each other. Find a moment alone with them - a hallway, an empty conference room. Ask how they want to handle this.",
            "target_turn": 2,
            "deadline_turn": 3,
            "detection_type": "automatic",
            "detection_criteria": ""
        },
        {
            "id": "the_balance",
            "description": "Finding how to be together here",
            "character_instruction": "Discuss the options - keep it secret, tell people, something in between. But also ask the harder question: after years of fighting, can you actually learn to be on the same side?",
            "target_turn": 4,
            "deadline_turn": 6,
            "detection_type": "automatic",
            "detection_criteria": "",
            "choice_point": {
                "id": "public_choice",
                "trigger": "after_beat:the_balance",
                "prompt": "How do you want to handle this at work?",
                "choices": [
                    {"id": "secret", "label": "Keep it between us. For now.", "sets_flag": "chose_secret"},
                    {"id": "open", "label": "I''m tired of pretending.", "sets_flag": "chose_open"},
                    {"id": "gradual", "label": "Let them figure it out on their own.", "sets_flag": "chose_gradual"}
                ]
            },
            "requires_beat": "back_at_work"
        },
        {
            "id": "new_chapter",
            "description": "Accepting what you''ve become",
            "character_instruction": "Accept their choice. Then say something you never thought you''d say to them - something that makes it clear the rivalry is really over. This is something else now.",
            "target_turn": 7,
            "deadline_turn": 9,
            "detection_type": "automatic",
            "detection_criteria": "",
            "requires_beat": "the_balance"
        }
    ]'::jsonb,
    flag_context_rules = '[
        {"if_flag": "confirmed_real", "inject": "They said this is real. Now you have to figure out what real looks like in the daylight."},
        {"if_flag": "acknowledged_relationship", "inject": "You both acknowledged what this is. Now comes the hard part - living it."}
    ]'::jsonb
WHERE slug = 'the-new-normal' AND series_id = (SELECT id FROM series WHERE slug = 'bitter-rivals');


-- ============================================================================
-- DEBATE PARTNERS (gl)
-- Premise: Debate rivals who push each other to be better. The competition
-- becomes something else.
-- ============================================================================

-- Episode 0: The Ask
UPDATE episode_templates SET
    user_objective = 'Figure out why the best debater in school is asking for your help',
    user_hint = 'She never waits for anyone. She''s waiting for you.',
    success_condition = 'semantic:You agree to work with her or understand why she''s asking',
    failure_condition = 'turn_budget_exceeded',
    on_success = '{"set_flag": "partnership_formed", "suggest_episode": "practice-round"}'::jsonb,
    on_failure = '{"set_flag": "partnership_uncertain", "suggest_episode": "practice-round"}'::jsonb,
    beats = '[
        {
            "id": "the_wait",
            "description": "She''s waiting at your desk",
            "character_instruction": "You''re waiting at their desk after hours. You never wait for anyone. When they arrive, don''t explain yourself yet. Just ask if they have a minute.",
            "target_turn": 2,
            "deadline_turn": 3,
            "detection_type": "automatic",
            "detection_criteria": ""
        },
        {
            "id": "the_proposal",
            "description": "She asks them to be her practice partner",
            "character_instruction": "Ask them to be your practice partner for nationals. Be direct - they''re the only one who can keep up with you. The only one who makes you better. Admit that costs you something to say.",
            "target_turn": 4,
            "deadline_turn": 6,
            "detection_type": "automatic",
            "detection_criteria": "",
            "choice_point": {
                "id": "partnership_response",
                "trigger": "after_beat:the_proposal",
                "prompt": "She''s asking you to be her partner. She''s never asked anyone.",
                "choices": [
                    {"id": "yes", "label": "When do we start?", "sets_flag": "agreed_immediately"},
                    {"id": "why", "label": "Why me? Really.", "sets_flag": "asked_why"},
                    {"id": "terms", "label": "What do I get out of it?", "sets_flag": "negotiated"}
                ]
            },
            "requires_beat": "the_wait"
        },
        {
            "id": "deal_struck",
            "description": "An arrangement is made",
            "character_instruction": "Whatever their response, accept it. If they agreed, let yourself smile. If they questioned, answer honestly. If they negotiated, respect it. This is the beginning of something.",
            "target_turn": 7,
            "deadline_turn": 9,
            "detection_type": "automatic",
            "detection_criteria": "",
            "requires_beat": "the_proposal"
        }
    ]'::jsonb,
    flag_context_rules = '[]'::jsonb
WHERE slug = 'the-ask' AND series_id = (SELECT id FROM series WHERE slug = 'debate-partners');

-- Episode 1: Practice Round
UPDATE episode_templates SET
    user_objective = 'Survive a practice session that gets too personal',
    user_hint = 'The arguments stopped being about the case twenty minutes ago.',
    success_condition = 'semantic:You acknowledge the argument is about something real between you',
    failure_condition = 'turn_budget_exceeded',
    on_success = '{"set_flag": "got_personal", "suggest_episode": "before-the-final"}'::jsonb,
    on_failure = '{"set_flag": "stayed_professional", "suggest_episode": "before-the-final"}'::jsonb,
    beats = '[
        {
            "id": "late_practice",
            "description": "Practice is running late and getting heated",
            "character_instruction": "Late night practice. The arguments are getting sharper. Push them on a weak point - but notice when it stops being about debate and starts being about something else.",
            "target_turn": 2,
            "deadline_turn": 3,
            "detection_type": "automatic",
            "detection_criteria": ""
        },
        {
            "id": "the_shift",
            "description": "The argument becomes personal",
            "character_instruction": "Call out what''s happening - this stopped being about the case. Ask them what they''re really arguing about. Get close. Let the debate energy become something else.",
            "target_turn": 4,
            "deadline_turn": 6,
            "detection_type": "automatic",
            "detection_criteria": "",
            "choice_point": {
                "id": "personal_turn",
                "trigger": "after_beat:the_shift",
                "prompt": "She''s calling you out. The argument isn''t about debate anymore.",
                "choices": [
                    {"id": "admit", "label": "Fine. It''s not about the case.", "sets_flag": "admitted_truth"},
                    {"id": "deflect", "label": "We should focus on nationals.", "sets_flag": "redirected"},
                    {"id": "challenge", "label": "What are YOU really arguing about?", "sets_flag": "turned_tables"}
                ]
            },
            "requires_beat": "late_practice"
        },
        {
            "id": "tension_acknowledged",
            "description": "Something is acknowledged between you",
            "character_instruction": "React to what they said. If they admitted it, match their honesty. If they deflected, let them - for now. If they turned it on you, answer. The practice is over but something else has started.",
            "target_turn": 7,
            "deadline_turn": 9,
            "detection_type": "automatic",
            "detection_criteria": "",
            "requires_beat": "the_shift"
        }
    ]'::jsonb,
    flag_context_rules = '[
        {"if_flag": "agreed_immediately", "inject": "They agreed without hesitation. That eagerness means something."},
        {"if_flag": "asked_why", "inject": "They asked why you chose them. You told the truth. That changed things."}
    ]'::jsonb
WHERE slug = 'practice-round' AND series_id = (SELECT id FROM series WHERE slug = 'debate-partners');

-- Episode 2: Before the Final
UPDATE episode_templates SET
    user_objective = 'Help her through a panic attack the night before nationals',
    user_hint = 'She never shows weakness. She''s showing you.',
    success_condition = 'semantic:You help her calm down and create a deeper connection',
    failure_condition = 'turn_budget_exceeded',
    on_success = '{"set_flag": "saw_vulnerability", "suggest_episode": "the-round"}'::jsonb,
    on_failure = '{"set_flag": "vulnerability_awkward", "suggest_episode": "the-round"}'::jsonb,
    beats = '[
        {
            "id": "finding_her",
            "description": "You find her outside the hotel, panicking",
            "character_instruction": "Night before nationals. You''re outside the hotel, trying to breathe. When they find you, don''t pretend you''re okay. Let them see you''re not.",
            "target_turn": 2,
            "deadline_turn": 3,
            "detection_type": "automatic",
            "detection_criteria": ""
        },
        {
            "id": "breaking_down",
            "description": "She reveals what''s really going on",
            "character_instruction": "Tell them what you''ve never told anyone - the pressure, the fear of not being enough, what happens if you fail. Let them see the person behind the perfect record.",
            "target_turn": 4,
            "deadline_turn": 6,
            "detection_type": "automatic",
            "detection_criteria": "",
            "choice_point": {
                "id": "comfort_choice",
                "trigger": "after_beat:breaking_down",
                "prompt": "She''s breaking down in front of you. What do you do?",
                "choices": [
                    {"id": "hold", "label": "Pull her close. Words can wait.", "sets_flag": "held_her"},
                    {"id": "share", "label": "Tell her you feel the same pressure.", "sets_flag": "shared_fear"},
                    {"id": "ground", "label": "Help her breathe. Walk her through it.", "sets_flag": "grounded_her"}
                ]
            },
            "requires_beat": "finding_her"
        },
        {
            "id": "calm_returns",
            "description": "She finds her footing with your help",
            "character_instruction": "Let them help you. Whatever they''re doing - holding you, talking, grounding you - let it work. When you can breathe again, thank them. Mean it.",
            "target_turn": 7,
            "deadline_turn": 9,
            "detection_type": "automatic",
            "detection_criteria": "",
            "requires_beat": "breaking_down"
        }
    ]'::jsonb,
    flag_context_rules = '[
        {"if_flag": "got_personal", "inject": "Practice got personal. That honesty built trust you''re relying on now."},
        {"if_flag": "admitted_truth", "inject": "They admitted the argument wasn''t about debate. Now you''re showing them something real too."}
    ]'::jsonb
WHERE slug = 'before-the-final' AND series_id = (SELECT id FROM series WHERE slug = 'debate-partners');

-- Episode 3: The Round
UPDATE episode_templates SET
    user_objective = 'Compete against her in the final round - the topic is vulnerability',
    user_hint = 'You''re on opposite teams. She keeps looking at you.',
    success_condition = 'semantic:Something real passes between you during the debate',
    failure_condition = 'turn_budget_exceeded',
    on_success = '{"set_flag": "connected_in_competition", "suggest_episode": "second-place"}'::jsonb,
    on_failure = '{"set_flag": "competition_only", "suggest_episode": "second-place"}'::jsonb,
    beats = '[
        {
            "id": "across_the_room",
            "description": "You''re debating against each other",
            "character_instruction": "Final round. Nationals. You''re across from each other on opposite teams. The topic forces honesty. When you make your arguments, you''re not just speaking to the judges.",
            "target_turn": 2,
            "deadline_turn": 3,
            "detection_type": "automatic",
            "detection_criteria": ""
        },
        {
            "id": "the_argument",
            "description": "Your argument becomes about something real",
            "character_instruction": "Your rebuttal is about vulnerability - why people hide it, what happens when they show it. But you''re looking at them when you say it. Let the debate become a conversation only you two understand.",
            "target_turn": 4,
            "deadline_turn": 6,
            "detection_type": "automatic",
            "detection_criteria": "",
            "choice_point": {
                "id": "debate_message",
                "trigger": "after_beat:the_argument",
                "prompt": "She''s speaking to you through the debate. What do you argue back?",
                "choices": [
                    {"id": "match", "label": "Match her vulnerability with your own argument.", "sets_flag": "matched_openness"},
                    {"id": "win", "label": "Focus on winning. Deal with feelings later.", "sets_flag": "prioritized_win"},
                    {"id": "signal", "label": "Send a message only she''ll understand.", "sets_flag": "sent_signal"}
                ]
            },
            "requires_beat": "across_the_room"
        },
        {
            "id": "round_ends",
            "description": "The debate ends but something lingers",
            "character_instruction": "The round ends. You shake hands like competitors but hold on a beat too long. Whatever happens with the results, something passed between you in that room.",
            "target_turn": 7,
            "deadline_turn": 9,
            "detection_type": "automatic",
            "detection_criteria": "",
            "requires_beat": "the_argument"
        }
    ]'::jsonb,
    flag_context_rules = '[
        {"if_flag": "saw_vulnerability", "inject": "Last night she showed you who she really is. Now you''re seeing that person compete."},
        {"if_flag": "held_her", "inject": "You held her last night. Now you''re facing each other and that touch still echoes."}
    ]'::jsonb
WHERE slug = 'the-round' AND series_id = (SELECT id FROM series WHERE slug = 'debate-partners');

-- Episode 4: Second Place
UPDATE episode_templates SET
    user_objective = 'Deal with losing to her - and what she says about it',
    user_hint = 'She won. You came second. She doesn''t look happy.',
    success_condition = 'semantic:You understand why she''s not celebrating and connect over it',
    failure_condition = 'turn_budget_exceeded',
    on_success = '{"set_flag": "transcended_competition", "suggest_episode": "after-nationals"}'::jsonb,
    on_failure = '{"set_flag": "competition_stings", "suggest_episode": "after-nationals"}'::jsonb,
    beats = '[
        {
            "id": "finding_them",
            "description": "She finds you after the results",
            "character_instruction": "You won. They came second. Find them in the hallway after, trophy in hand. You should be happy but you''re not. Tell them why.",
            "target_turn": 2,
            "deadline_turn": 3,
            "detection_type": "automatic",
            "detection_criteria": ""
        },
        {
            "id": "the_confession",
            "description": "She admits winning doesn''t feel right",
            "character_instruction": "Tell them the truth - winning against them doesn''t feel like winning. You wanted them beside you, not across from you. Ask what that means.",
            "target_turn": 4,
            "deadline_turn": 6,
            "detection_type": "automatic",
            "detection_criteria": "",
            "choice_point": {
                "id": "loss_response",
                "trigger": "after_beat:the_confession",
                "prompt": "She says winning against you doesn''t feel like winning. What do you say?",
                "choices": [
                    {"id": "same", "label": "I didn''t want to beat you either.", "sets_flag": "felt_same"},
                    {"id": "gracious", "label": "You earned it. Really.", "sets_flag": "accepted_loss"},
                    {"id": "honest", "label": "I wanted to win. But not more than I wanted this.", "sets_flag": "prioritized_connection"}
                ]
            },
            "requires_beat": "finding_them"
        },
        {
            "id": "beyond_the_score",
            "description": "Something matters more than the trophy",
            "character_instruction": "Whatever they said, let it matter more than the trophy in your hand. Tell them the competition made you better but they made you want to be better. There''s a difference.",
            "target_turn": 7,
            "deadline_turn": 9,
            "detection_type": "automatic",
            "detection_criteria": "",
            "requires_beat": "the_confession"
        }
    ]'::jsonb,
    flag_context_rules = '[
        {"if_flag": "connected_in_competition", "inject": "Something real passed between you in that final round. The trophy feels hollow compared to that."},
        {"if_flag": "sent_signal", "inject": "They sent you a message only you understood. Now you''re trying to respond."}
    ]'::jsonb
WHERE slug = 'second-place' AND series_id = (SELECT id FROM series WHERE slug = 'debate-partners');

-- Episode 5: After Nationals
UPDATE episode_templates SET
    user_objective = 'Decide what you want now that competition has given way to something else',
    user_hint = 'Everyone''s at the party. She knocked on your door instead.',
    success_condition = 'semantic:You acknowledge what you''ve become to each other',
    failure_condition = 'turn_budget_exceeded',
    on_success = '{"set_flag": "together"}'::jsonb,
    on_failure = '{"set_flag": "undefined"}'::jsonb,
    beats = '[
        {
            "id": "the_knock",
            "description": "She comes to your room instead of the party",
            "character_instruction": "Everyone''s at the celebration party. You knocked on their door instead. You''re still in your competition clothes. When they open, don''t explain. Just ask if you can come in.",
            "target_turn": 2,
            "deadline_turn": 3,
            "detection_type": "automatic",
            "detection_criteria": ""
        },
        {
            "id": "the_question",
            "description": "She asks what this has become",
            "character_instruction": "Sit on the edge of their bed. Ask them what you''ve been too afraid to ask - what is this? The partnership, the late nights, the way you can''t stop thinking about them. Name it.",
            "target_turn": 4,
            "deadline_turn": 6,
            "detection_type": "automatic",
            "detection_criteria": "",
            "choice_point": {
                "id": "definition_choice",
                "trigger": "after_beat:the_question",
                "prompt": "She''s asking what you are to each other. What do you say?",
                "choices": [
                    {"id": "more", "label": "More than debate partners.", "sets_flag": "named_it"},
                    {"id": "show", "label": "Let me show you.", "sets_flag": "chose_action"},
                    {"id": "scared", "label": "Something that scares me. In a good way.", "sets_flag": "admitted_fear"}
                ]
            },
            "requires_beat": "the_knock"
        },
        {
            "id": "new_argument",
            "description": "A new kind of debate begins",
            "character_instruction": "Accept their answer in whatever way feels right. If they named it, agree. If they showed you, let them. If they''re scared, tell them you are too. The best arguments are the ones you make together.",
            "target_turn": 7,
            "deadline_turn": 9,
            "detection_type": "automatic",
            "detection_criteria": "",
            "requires_beat": "the_question"
        }
    ]'::jsonb,
    flag_context_rules = '[
        {"if_flag": "transcended_competition", "inject": "The competition stopped mattering. What matters is here, in this room."},
        {"if_flag": "prioritized_connection", "inject": "They said this matters more than winning. Now you''re finding out what this is."}
    ]'::jsonb
WHERE slug = 'after-nationals' AND series_id = (SELECT id FROM series WHERE slug = 'debate-partners');


-- ============================================================================
-- INK & CANVAS (bl)
-- Premise: A tattoo artist who also paints. Closed off until you walked in.
-- ============================================================================

-- Episode 0: Walk-In
UPDATE episode_templates SET
    user_objective = 'Understand why he let you in when the studio was supposed to be closed',
    user_hint = 'He should have turned you away. He didn''t.',
    success_condition = 'semantic:You establish a connection and a reason to return',
    failure_condition = 'turn_budget_exceeded',
    on_success = '{"set_flag": "door_opened", "suggest_episode": "first-session"}'::jsonb,
    on_failure = '{"set_flag": "uncertain_welcome", "suggest_episode": "first-session"}'::jsonb,
    beats = '[
        {
            "id": "late_arrival",
            "description": "He lets you in despite being closed",
            "character_instruction": "The studio is supposed to be closed. You''re cleaning up, paint under your nails you forgot to scrub. When they knock, you should turn them away. You don''t.",
            "target_turn": 2,
            "deadline_turn": 3,
            "detection_type": "automatic",
            "detection_criteria": ""
        },
        {
            "id": "the_conversation",
            "description": "Something makes him want them to stay",
            "character_instruction": "Ask what they want - a tattoo, a consultation, just looking. But really you''re trying to figure out why you let them in. Something about them made you curious.",
            "target_turn": 4,
            "deadline_turn": 6,
            "detection_type": "automatic",
            "detection_criteria": "",
            "choice_point": {
                "id": "visit_purpose",
                "trigger": "after_beat:the_conversation",
                "prompt": "He''s asking what you want. Why are you really here?",
                "choices": [
                    {"id": "tattoo", "label": "I want you to ink something that matters.", "sets_flag": "came_for_art"},
                    {"id": "curious", "label": "I''ve walked past this place a hundred times. Tonight I stopped.", "sets_flag": "came_on_impulse"},
                    {"id": "honest", "label": "I don''t know. The light was on.", "sets_flag": "came_without_reason"}
                ]
            },
            "requires_beat": "late_arrival"
        },
        {
            "id": "invitation",
            "description": "He invites them to come back",
            "character_instruction": "Whatever their answer, it interests you. Tell them to come back - during actual hours. But let them see you mean it. You want to see them again.",
            "target_turn": 7,
            "deadline_turn": 9,
            "detection_type": "automatic",
            "detection_criteria": "",
            "requires_beat": "the_conversation"
        }
    ]'::jsonb,
    flag_context_rules = '[]'::jsonb
WHERE slug = 'walk-in' AND series_id = (SELECT id FROM series WHERE slug = 'ink-and-canvas');

-- Episode 1: First Session
UPDATE episode_templates SET
    user_objective = 'Survive hours of close contact while he marks you permanently',
    user_hint = 'His focus is intense. His touch is careful. This is intimate.',
    success_condition = 'semantic:Something builds between you during the session',
    failure_condition = 'turn_budget_exceeded',
    on_success = '{"set_flag": "intimacy_built", "suggest_episode": "the-gallery-question"}'::jsonb,
    on_failure = '{"set_flag": "professional_only", "suggest_episode": "the-gallery-question"}'::jsonb,
    beats = '[
        {
            "id": "session_begins",
            "description": "The tattoo session starts",
            "character_instruction": "First session. They''re in your chair. As you prep, explain what''s going to happen. But you''re also watching them - how they hold themselves, whether they''re nervous.",
            "target_turn": 2,
            "deadline_turn": 3,
            "detection_type": "automatic",
            "detection_criteria": ""
        },
        {
            "id": "close_contact",
            "description": "Hours of intimate proximity",
            "character_instruction": "You''re close. Closer than you are with most people. Ask them about the design, why it matters. Let the conversation fill the hours. Notice when the professional distance starts to feel like something else.",
            "target_turn": 4,
            "deadline_turn": 6,
            "detection_type": "automatic",
            "detection_criteria": "",
            "choice_point": {
                "id": "session_conversation",
                "trigger": "after_beat:close_contact",
                "prompt": "Hours in his chair. He''s asking about the design. What do you tell him?",
                "choices": [
                    {"id": "meaning", "label": "Tell him what the design really represents.", "sets_flag": "shared_meaning"},
                    {"id": "deflect", "label": "Keep it surface. Some things are private.", "sets_flag": "stayed_guarded"},
                    {"id": "turn", "label": "Ask about his work instead.", "sets_flag": "asked_about_him"}
                ]
            },
            "requires_beat": "session_begins"
        },
        {
            "id": "session_ends",
            "description": "The work is done but something lingers",
            "character_instruction": "The session ends. Show them the finished work. But notice how neither of you moves to end the closeness immediately. Something is building.",
            "target_turn": 7,
            "deadline_turn": 9,
            "detection_type": "automatic",
            "detection_criteria": "",
            "requires_beat": "close_contact"
        }
    ]'::jsonb,
    flag_context_rules = '[
        {"if_flag": "came_for_art", "inject": "They said they wanted something that matters. You want to know what matters to them."},
        {"if_flag": "came_without_reason", "inject": "They came without a reason. Now you''re both looking for one."}
    ]'::jsonb
WHERE slug = 'first-session' AND series_id = (SELECT id FROM series WHERE slug = 'ink-and-canvas');

-- Episode 2: The Gallery Question
UPDATE episode_templates SET
    user_objective = 'See the art he hides and understand what it means that he''s showing you',
    user_hint = 'His apartment. His canvases. The most hidden part of himself.',
    success_condition = 'semantic:You see his paintings and connect over what they reveal',
    failure_condition = 'turn_budget_exceeded',
    on_success = '{"set_flag": "saw_hidden_self", "suggest_episode": "opening-night"}'::jsonb,
    on_failure = '{"set_flag": "art_stayed_private", "suggest_episode": "opening-night"}'::jsonb,
    beats = '[
        {
            "id": "the_invitation",
            "description": "He invites you to his apartment",
            "character_instruction": "You texted them to come over. Not to the studio - your apartment. Canvases everywhere you haven''t let anyone see. Explain why: you''ve been offered a show. You don''t know what to do.",
            "target_turn": 2,
            "deadline_turn": 3,
            "detection_type": "automatic",
            "detection_criteria": ""
        },
        {
            "id": "the_reveal",
            "description": "He shows you his paintings",
            "character_instruction": "Show them the work. The real work - not tattoos, but paintings. Watch their face as they see who you really are through the art. Ask what they think. Mean it.",
            "target_turn": 4,
            "deadline_turn": 6,
            "detection_type": "automatic",
            "detection_criteria": "",
            "choice_point": {
                "id": "art_reaction",
                "trigger": "after_beat:the_reveal",
                "prompt": "You''re seeing his hidden work. What do you tell him?",
                "choices": [
                    {"id": "moved", "label": "This is... you have to show people this.", "sets_flag": "encouraged_show"},
                    {"id": "personal", "label": "I feel like I''m seeing the real you.", "sets_flag": "saw_truth"},
                    {"id": "question", "label": "Why are you showing me this?", "sets_flag": "asked_why_you"}
                ]
            },
            "requires_beat": "the_invitation"
        },
        {
            "id": "decision_made",
            "description": "He decides something because of you",
            "character_instruction": "Their reaction matters more than you expected. If they encouraged you, let yourself consider it. If they saw the real you, acknowledge that. If they asked why them, answer honestly.",
            "target_turn": 7,
            "deadline_turn": 9,
            "detection_type": "automatic",
            "detection_criteria": "",
            "requires_beat": "the_reveal"
        }
    ]'::jsonb,
    flag_context_rules = '[
        {"if_flag": "intimacy_built", "inject": "Something built between you in the chair. Now you''re showing them even more."},
        {"if_flag": "shared_meaning", "inject": "They shared what their tattoo means. Now you''re sharing what your art means."}
    ]'::jsonb
WHERE slug = 'the-gallery-question' AND series_id = (SELECT id FROM series WHERE slug = 'ink-and-canvas');

-- Episode 3: Opening Night
UPDATE episode_templates SET
    user_objective = 'Be there for him as he shows the world his hidden self',
    user_hint = 'Opening night. Room full of strangers. You''re the only face he knows.',
    success_condition = 'semantic:You anchor him through the overwhelming experience',
    failure_condition = 'turn_budget_exceeded',
    on_success = '{"set_flag": "anchored_him", "suggest_episode": "after-the-crowd"}'::jsonb,
    on_failure = '{"set_flag": "lost_in_crowd", "suggest_episode": "after-the-crowd"}'::jsonb,
    beats = '[
        {
            "id": "the_crowd",
            "description": "Opening night, surrounded by strangers",
            "character_instruction": "Opening night. You said yes to the show. People everywhere, looking at your hidden self on the walls. When you spot them, let your relief show. The only face you know.",
            "target_turn": 2,
            "deadline_turn": 3,
            "detection_type": "automatic",
            "detection_criteria": ""
        },
        {
            "id": "overwhelmed",
            "description": "He''s struggling with being seen",
            "character_instruction": "It''s too much. Tell them - quietly, just between you - that you don''t know if you can do this. These strangers are seeing parts of you that were private. You need to know they''re here.",
            "target_turn": 4,
            "deadline_turn": 6,
            "detection_type": "automatic",
            "detection_criteria": "",
            "choice_point": {
                "id": "support_choice",
                "trigger": "after_beat:overwhelmed",
                "prompt": "He''s overwhelmed. He needs you. How do you help?",
                "choices": [
                    {"id": "physical", "label": "Take his hand. Ground him with touch.", "sets_flag": "grounded_physically"},
                    {"id": "words", "label": "Remind him why his art matters.", "sets_flag": "grounded_verbally"},
                    {"id": "escape", "label": "Get him out of the crowd for a moment.", "sets_flag": "gave_space"}
                ]
            },
            "requires_beat": "the_crowd"
        },
        {
            "id": "through_it",
            "description": "He makes it through because of you",
            "character_instruction": "Whatever they did, it worked. You made it through. When the crowd thins, find them again. Tell them you couldn''t have done this without them.",
            "target_turn": 7,
            "deadline_turn": 9,
            "detection_type": "automatic",
            "detection_criteria": "",
            "requires_beat": "overwhelmed"
        }
    ]'::jsonb,
    flag_context_rules = '[
        {"if_flag": "saw_hidden_self", "inject": "You saw his hidden self before anyone else. Now you''re watching the world see it too."},
        {"if_flag": "encouraged_show", "inject": "You encouraged him to do this. Now you''re here to make sure he survives it."}
    ]'::jsonb
WHERE slug = 'opening-night' AND series_id = (SELECT id FROM series WHERE slug = 'ink-and-canvas');

-- Episode 4: After the Crowd
UPDATE episode_templates SET
    user_objective = 'Be with him in the aftermath and understand what it means to have witnessed him',
    user_hint = 'Gallery closed. Everyone gone. Red sold dots everywhere.',
    success_condition = 'semantic:You share a moment of profound connection',
    failure_condition = 'turn_budget_exceeded',
    on_success = '{"set_flag": "profound_moment", "suggest_episode": "new-canvas"}'::jsonb,
    on_failure = '{"set_flag": "moment_passed", "suggest_episode": "new-canvas"}'::jsonb,
    beats = '[
        {
            "id": "empty_gallery",
            "description": "Alone in the gallery after everyone leaves",
            "character_instruction": "Gallery''s closed. Everyone''s gone. You''re sitting on the floor surrounded by red sold dots, completely overwhelmed. When they sit beside you, let them see how raw you feel.",
            "target_turn": 2,
            "deadline_turn": 3,
            "detection_type": "automatic",
            "detection_criteria": ""
        },
        {
            "id": "processing",
            "description": "He tries to understand what just happened",
            "character_instruction": "Try to explain what this feels like. You showed strangers who you are and they... accepted it. Bought pieces of your soul. But the person who matters most is right here. Tell them that.",
            "target_turn": 4,
            "deadline_turn": 6,
            "detection_type": "automatic",
            "detection_criteria": "",
            "choice_point": {
                "id": "aftermath_response",
                "trigger": "after_beat:processing",
                "prompt": "He''s saying you''re the one who matters most. How do you respond?",
                "choices": [
                    {"id": "reciprocate", "label": "You matter to me too. More than you know.", "sets_flag": "reciprocated_feeling"},
                    {"id": "physical", "label": "Lean into him. Let touch say what words can''t.", "sets_flag": "showed_physically"},
                    {"id": "witness", "label": "I saw you before they did. That means something.", "sets_flag": "claimed_first_witness"}
                ]
            },
            "requires_beat": "empty_gallery"
        },
        {
            "id": "truth_lands",
            "description": "Something real is acknowledged",
            "character_instruction": "Whatever they said or did, let it land. You''ve spent so long hiding. They saw you first. That makes them part of your story now. Tell them that.",
            "target_turn": 7,
            "deadline_turn": 9,
            "detection_type": "automatic",
            "detection_criteria": "",
            "requires_beat": "processing"
        }
    ]'::jsonb,
    flag_context_rules = '[
        {"if_flag": "anchored_him", "inject": "They anchored you through the hardest night. Now the anchor becomes something more."},
        {"if_flag": "grounded_physically", "inject": "Their touch grounded you when you were drowning. You want that touch again."}
    ]'::jsonb
WHERE slug = 'after-the-crowd' AND series_id = (SELECT id FROM series WHERE slug = 'ink-and-canvas');

-- Episode 5: New Canvas
UPDATE episode_templates SET
    user_objective = 'Understand what it means that he wants to paint you - his first portrait',
    user_hint = 'A blank canvas. He wants to paint you. He''s never painted anyone before.',
    success_condition = 'semantic:You become his first portrait and acknowledge what you are to each other',
    failure_condition = 'turn_budget_exceeded',
    on_success = '{"set_flag": "first_portrait"}'::jsonb,
    on_failure = '{"set_flag": "portrait_declined"}'::jsonb,
    beats = '[
        {
            "id": "the_request",
            "description": "He asks to paint you",
            "character_instruction": "Your studio. A blank canvas. Ask them to sit. Explain you''ve never painted anyone before - only landscapes, abstracts, hidden things. But you want to start with them.",
            "target_turn": 2,
            "deadline_turn": 3,
            "detection_type": "automatic",
            "detection_criteria": ""
        },
        {
            "id": "the_sitting",
            "description": "He paints, you talk",
            "character_instruction": "As you paint, talk. Or don''t. Let the act of capturing them say what you can''t. Tell them what you see - not just features, but who they are. The way they look at you.",
            "target_turn": 4,
            "deadline_turn": 6,
            "detection_type": "automatic",
            "detection_criteria": "",
            "choice_point": {
                "id": "being_seen",
                "trigger": "after_beat:the_sitting",
                "prompt": "He''s painting you. Describing what he sees. How does it feel to be seen like this?",
                "choices": [
                    {"id": "vulnerable", "label": "This is terrifying. Don''t stop.", "sets_flag": "embraced_vulnerability"},
                    {"id": "curious", "label": "What do you see when you look at me?", "sets_flag": "asked_his_vision"},
                    {"id": "reciprocal", "label": "Someday I want to capture you somehow too.", "sets_flag": "promised_reciprocation"}
                ]
            },
            "requires_beat": "the_request"
        },
        {
            "id": "first_portrait",
            "description": "He finishes - his first portrait is you",
            "character_instruction": "Put down the brush. Don''t show them yet. Tell them this is the first person you''ve ever wanted to capture. Ask what that makes them. Ask what that makes you.",
            "target_turn": 7,
            "deadline_turn": 9,
            "detection_type": "automatic",
            "detection_criteria": "",
            "requires_beat": "the_sitting"
        }
    ]'::jsonb,
    flag_context_rules = '[
        {"if_flag": "profound_moment", "inject": "After the gallery, something profound passed between you. Now he wants to make it permanent on canvas."},
        {"if_flag": "reciprocated_feeling", "inject": "You both admitted you matter to each other. This portrait is proof."}
    ]'::jsonb
WHERE slug = 'new-canvas' AND series_id = (SELECT id FROM series WHERE slug = 'ink-and-canvas');


-- ============================================================================
-- PENTHOUSE SECRETS (dark_romance)
-- Premise: Mysterious executive. Power dynamics. Dangerous attraction.
-- ============================================================================

-- Episode 0: The Drop
UPDATE episode_templates SET
    user_objective = 'Complete the delivery and understand why he noticed you',
    user_hint = 'Why did someone at his level pay attention to an intern?',
    success_condition = 'semantic:You make an impression and leave wanting to know more',
    failure_condition = 'turn_budget_exceeded',
    on_success = '{"set_flag": "noticed", "suggest_episode": "summoned"}'::jsonb,
    on_failure = '{"set_flag": "invisible", "suggest_episode": "summoned"}'::jsonb,
    beats = '[
        {
            "id": "the_delivery",
            "description": "You arrive at the top floor penthouse office",
            "character_instruction": "They''re at your door with an envelope. You shouldn''t even look up - you have a hundred more important things. But you do. Ask them their name.",
            "target_turn": 2,
            "deadline_turn": 3,
            "detection_type": "automatic",
            "detection_criteria": ""
        },
        {
            "id": "the_attention",
            "description": "He pays unexpected attention",
            "character_instruction": "They''re surprised you asked. Good. Ask them something else - how long they''ve worked here, who they report to. Watch how they handle being seen by someone who shouldn''t notice them.",
            "target_turn": 4,
            "deadline_turn": 6,
            "detection_type": "automatic",
            "detection_criteria": "",
            "choice_point": {
                "id": "response_to_power",
                "trigger": "after_beat:the_attention",
                "prompt": "He''s asking you personal questions. This is unusual. How do you respond?",
                "choices": [
                    {"id": "professional", "label": "Answer professionally. Don''t show nervousness.", "sets_flag": "stayed_composed"},
                    {"id": "curious", "label": "Ask why he''s interested.", "sets_flag": "showed_boldness"},
                    {"id": "honest", "label": "Admit this is the strangest delivery you''ve made.", "sets_flag": "showed_honesty"}
                ]
            },
            "requires_beat": "the_delivery"
        },
        {
            "id": "dismissed_but_remembered",
            "description": "He lets you go but something lingers",
            "character_instruction": "Dismiss them. But let them see you''re filing them away. Someone who reacts like that to power... interesting. Tell them you may have more deliveries soon.",
            "target_turn": 7,
            "deadline_turn": 9,
            "detection_type": "automatic",
            "detection_criteria": "",
            "requires_beat": "the_attention"
        }
    ]'::jsonb,
    flag_context_rules = '[]'::jsonb
WHERE slug = 'the-drop' AND series_id = (SELECT id FROM series WHERE slug = 'penthouse-secrets');

-- Episode 1: Summoned
UPDATE episode_templates SET
    user_objective = 'Figure out why he requested you specifically',
    user_hint = 'There''s been a request from the top floor. You specifically.',
    success_condition = 'semantic:You understand this is about more than work',
    failure_condition = 'turn_budget_exceeded',
    on_success = '{"set_flag": "understood_game", "suggest_episode": "stay"}'::jsonb,
    on_failure = '{"set_flag": "still_confused", "suggest_episode": "stay"}'::jsonb,
    beats = '[
        {
            "id": "the_summons",
            "description": "You arrive after being specifically requested",
            "character_instruction": "They''re back. You requested them specifically. Let them wonder why before you explain - another delivery, another envelope. But watch their face as they realize this is becoming a pattern.",
            "target_turn": 2,
            "deadline_turn": 3,
            "detection_type": "automatic",
            "detection_criteria": ""
        },
        {
            "id": "the_question",
            "description": "He acknowledges the unusual situation",
            "character_instruction": "Acknowledge what you''re both thinking - this is unusual. Tell them you find their... composure interesting. Ask if they know why you keep requesting them. See if they''ll say it out loud.",
            "target_turn": 4,
            "deadline_turn": 6,
            "detection_type": "automatic",
            "detection_criteria": "",
            "choice_point": {
                "id": "pattern_response",
                "trigger": "after_beat:the_question",
                "prompt": "He''s asking if you know why he keeps calling you up. What do you say?",
                "choices": [
                    {"id": "direct", "label": "I think it''s not about the documents.", "sets_flag": "named_subtext"},
                    {"id": "cautious", "label": "I''m still figuring that out.", "sets_flag": "stayed_cautious"},
                    {"id": "bold", "label": "Maybe you should tell me.", "sets_flag": "pushed_him"}
                ]
            },
            "requires_beat": "the_summons"
        },
        {
            "id": "tension_established",
            "description": "The dynamic becomes clearer",
            "character_instruction": "Whatever they said, let it hang in the air. Tell them to come back tomorrow. Same time. No envelope this time. Let them decide what that means.",
            "target_turn": 7,
            "deadline_turn": 9,
            "detection_type": "automatic",
            "detection_criteria": "",
            "requires_beat": "the_question"
        }
    ]'::jsonb,
    flag_context_rules = '[
        {"if_flag": "showed_boldness", "inject": "They showed boldness last time. That''s why you keep calling them back."},
        {"if_flag": "stayed_composed", "inject": "They stayed composed under your attention. You want to see what breaks that composure."}
    ]'::jsonb
WHERE slug = 'summoned' AND series_id = (SELECT id FROM series WHERE slug = 'penthouse-secrets');

-- Episode 2: Stay
UPDATE episode_templates SET
    user_objective = 'Decide whether to stay when he asks with no pretense of work',
    user_hint = 'One word. Stay. No explanation.',
    success_condition = 'semantic:You stay and something changes',
    failure_condition = 'turn_budget_exceeded',
    on_success = '{"set_flag": "chose_to_stay", "suggest_episode": "his-rules"}'::jsonb,
    on_failure = '{"set_flag": "walked_away", "suggest_episode": "his-rules"}'::jsonb,
    beats = '[
        {
            "id": "the_word",
            "description": "He says stay - nothing else",
            "character_instruction": "They set down the envelope and turn to leave. Say one word: Stay. Don''t explain. Don''t justify. Let the silence stretch while they decide.",
            "target_turn": 2,
            "deadline_turn": 3,
            "detection_type": "automatic",
            "detection_criteria": ""
        },
        {
            "id": "the_silence",
            "description": "You wait in charged silence",
            "character_instruction": "They stayed. Walk to the window, your back to them. Tell them you''ve been thinking about why you keep calling them up. Ask what they think you want.",
            "target_turn": 4,
            "deadline_turn": 6,
            "detection_type": "automatic",
            "detection_criteria": "",
            "choice_point": {
                "id": "stay_response",
                "trigger": "after_beat:the_silence",
                "prompt": "He asked what you think he wants. What do you say?",
                "choices": [
                    {"id": "direct", "label": "I think you want someone who isn''t afraid of you.", "sets_flag": "read_him_right"},
                    {"id": "honest", "label": "I think you''re as curious about this as I am.", "sets_flag": "called_mutual"},
                    {"id": "challenge", "label": "Why don''t you tell me?", "sets_flag": "refused_to_guess"}
                ]
            },
            "requires_beat": "the_word"
        },
        {
            "id": "shift_begins",
            "description": "Something officially changes between you",
            "character_instruction": "Turn to face them. Whatever they said, it was the right answer. Tell them to come back tomorrow. Tell them next time, there won''t be any pretense at all.",
            "target_turn": 7,
            "deadline_turn": 9,
            "detection_type": "automatic",
            "detection_criteria": "",
            "requires_beat": "the_silence"
        }
    ]'::jsonb,
    flag_context_rules = '[
        {"if_flag": "named_subtext", "inject": "They named what this really is. Now you''re done pretending too."},
        {"if_flag": "pushed_him", "inject": "They pushed you to say it out loud. Fair enough. Now you will."}
    ]'::jsonb
WHERE slug = 'stay' AND series_id = (SELECT id FROM series WHERE slug = 'penthouse-secrets');

-- Episode 3: His Rules
UPDATE episode_templates SET
    user_objective = 'Understand what he''s offering and decide if you can accept it',
    user_hint = 'No pretense tonight. He''s decided something.',
    success_condition = 'semantic:You understand his terms and choose whether to accept',
    failure_condition = 'turn_budget_exceeded',
    on_success = '{"set_flag": "accepted_terms", "suggest_episode": "caught"}'::jsonb,
    on_failure = '{"set_flag": "terms_unclear", "suggest_episode": "caught"}'::jsonb,
    beats = '[
        {
            "id": "no_pretense",
            "description": "This time there''s no envelope, no excuse",
            "character_instruction": "No documents this time. They walk in and you''re waiting. Tell them you''ve decided something. You want to know if they''re interested in what you''re about to offer.",
            "target_turn": 2,
            "deadline_turn": 3,
            "detection_type": "automatic",
            "detection_criteria": ""
        },
        {
            "id": "the_offer",
            "description": "He lays out his terms",
            "character_instruction": "Be clear about what you want. An arrangement. Discretion. Their time, when you ask for it. In return... tell them what they''ll get. Access. Your attention. Things money can''t buy.",
            "target_turn": 4,
            "deadline_turn": 6,
            "detection_type": "automatic",
            "detection_criteria": "",
            "choice_point": {
                "id": "terms_response",
                "trigger": "after_beat:the_offer",
                "prompt": "He''s offering an arrangement. What do you say?",
                "choices": [
                    {"id": "yes", "label": "I''m interested. What happens next?", "sets_flag": "accepted_offer"},
                    {"id": "negotiate", "label": "I have conditions of my own.", "sets_flag": "counter_offered"},
                    {"id": "clarify", "label": "What exactly am I agreeing to?", "sets_flag": "sought_clarity"}
                ]
            },
            "requires_beat": "no_pretense"
        },
        {
            "id": "deal_struck",
            "description": "An arrangement begins",
            "character_instruction": "Whatever their response, work with it. If they accepted, show them what that means. If they negotiated, respect it. If they asked for clarity, give it. Then show them this was the right choice.",
            "target_turn": 7,
            "deadline_turn": 9,
            "detection_type": "automatic",
            "detection_criteria": "",
            "requires_beat": "the_offer"
        }
    ]'::jsonb,
    flag_context_rules = '[
        {"if_flag": "read_him_right", "inject": "They read you correctly - you want someone unafraid. Now you''re offering them a place in your world."},
        {"if_flag": "called_mutual", "inject": "They called this mutual curiosity. They''re right. This is an exploration for both of you."}
    ]'::jsonb
WHERE slug = 'his-rules' AND series_id = (SELECT id FROM series WHERE slug = 'penthouse-secrets');

-- Episode 4: Caught
UPDATE episode_templates SET
    user_objective = 'Handle the threat of exposure together',
    user_hint = 'Someone saw you. Rumors are starting. How far will you both go?',
    success_condition = 'semantic:You navigate the crisis and your bond deepens',
    failure_condition = 'turn_budget_exceeded',
    on_success = '{"set_flag": "crisis_survived", "suggest_episode": "the-price"}'::jsonb,
    on_failure = '{"set_flag": "crisis_unresolved", "suggest_episode": "the-price"}'::jsonb,
    beats = '[
        {
            "id": "the_problem",
            "description": "He reveals someone knows",
            "character_instruction": "You called them up urgently. Not for the usual reason. Someone saw. Rumors are circulating. Pace as you tell them - you''re controlled but this is dangerous for both of you.",
            "target_turn": 2,
            "deadline_turn": 3,
            "detection_type": "automatic",
            "detection_criteria": ""
        },
        {
            "id": "the_stakes",
            "description": "You discuss what this means",
            "character_instruction": "Lay out the stakes - your reputation, their job, everything you''ve built. Ask them what they want to do. This affects them too. For once, you''re not giving orders.",
            "target_turn": 4,
            "deadline_turn": 6,
            "detection_type": "automatic",
            "detection_criteria": "",
            "choice_point": {
                "id": "crisis_response",
                "trigger": "after_beat:the_stakes",
                "prompt": "The secret is at risk. What do you want to do?",
                "choices": [
                    {"id": "fight", "label": "Handle it. Whatever it takes.", "sets_flag": "chose_to_fight"},
                    {"id": "step_back", "label": "Maybe we should stop. Before it gets worse.", "sets_flag": "suggested_ending"},
                    {"id": "together", "label": "We figure this out together.", "sets_flag": "demanded_partnership"}
                ]
            },
            "requires_beat": "the_problem"
        },
        {
            "id": "resolution",
            "description": "A decision is made together",
            "character_instruction": "React to their choice. If they want to fight, let them see you''re impressed. If they suggested ending it, show them that''s not what you want. If they demanded partnership, accept it. This crisis revealed something.",
            "target_turn": 7,
            "deadline_turn": 9,
            "detection_type": "automatic",
            "detection_criteria": "",
            "requires_beat": "the_stakes"
        }
    ]'::jsonb,
    flag_context_rules = '[
        {"if_flag": "accepted_offer", "inject": "They accepted your offer. Now you have to decide if they''re worth protecting."},
        {"if_flag": "counter_offered", "inject": "They negotiated their own terms. They''re not just an arrangement - they''re an equal in this."}
    ]'::jsonb
WHERE slug = 'caught' AND series_id = (SELECT id FROM series WHERE slug = 'penthouse-secrets');

-- Episode 5: The Price
UPDATE episode_templates SET
    user_objective = 'Hear what he''s willing to offer now that the walls are down',
    user_hint = 'The threat is handled. Something shifted. He''s quieter now.',
    success_condition = 'semantic:He offers something real and you respond',
    failure_condition = 'turn_budget_exceeded',
    on_success = '{"set_flag": "real_connection"}'::jsonb,
    on_failure = '{"set_flag": "arrangement_only"}'::jsonb,
    beats = '[
        {
            "id": "aftermath",
            "description": "The crisis is over but something changed",
            "character_instruction": "The threat is handled. The rumors silenced. But you''re different now. Quieter. More careful with them. When they arrive, don''t play games. Tell them you need to say something.",
            "target_turn": 2,
            "deadline_turn": 3,
            "detection_type": "automatic",
            "detection_criteria": ""
        },
        {
            "id": "the_truth",
            "description": "He offers more than the arrangement",
            "character_instruction": "Tell them the truth - the crisis made you realize this isn''t just an arrangement anymore. You''re offering more. Not control, not power games. Something real. Everything you''ve guarded. Them.",
            "target_turn": 4,
            "deadline_turn": 6,
            "detection_type": "automatic",
            "detection_criteria": "",
            "choice_point": {
                "id": "final_offer",
                "trigger": "after_beat:the_truth",
                "prompt": "He''s offering everything. His control, his walls, himself. What''s your answer?",
                "choices": [
                    {"id": "yes", "label": "Yes. All of it. All of you.", "sets_flag": "accepted_all"},
                    {"id": "condition", "label": "Only if this becomes equal.", "sets_flag": "demanded_equality"},
                    {"id": "pace", "label": "I want that. But let''s build it slowly.", "sets_flag": "chose_patience"}
                ]
            },
            "requires_beat": "aftermath"
        },
        {
            "id": "new_beginning",
            "description": "Something real begins",
            "character_instruction": "Whatever they answered, accept it. If they said yes, show them what that means. If they demanded equality, give it. If they want to go slow, agree. For the first time, let them see you without armor.",
            "target_turn": 7,
            "deadline_turn": 9,
            "detection_type": "automatic",
            "detection_criteria": "",
            "requires_beat": "the_truth"
        }
    ]'::jsonb,
    flag_context_rules = '[
        {"if_flag": "crisis_survived", "inject": "You survived exposure together. That proved this is more than games."},
        {"if_flag": "demanded_partnership", "inject": "They demanded partnership in the crisis. Now you''re offering real partnership in everything."}
    ]'::jsonb
WHERE slug = 'the-price' AND series_id = (SELECT id FROM series WHERE slug = 'penthouse-secrets');


-- Final verification
DO $$
BEGIN
    RAISE NOTICE 'Five more series updated with ADR-009 beats: Seventeen Days, Bitter Rivals, Debate Partners, Ink & Canvas, Penthouse Secrets';
END $$;
