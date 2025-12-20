-- =============================================================================
-- Migration 027: Play Mode Infrastructure & Romantic Tropes
-- =============================================================================
-- This migration adds:
-- 1. 'play' series_type for content isolation
-- 2. Hometown Crush series (male/female variants)
-- 3. Jack and Emma characters optimized for trope detection
-- 4. Episode templates with romantic_trope evaluation
--
-- EXECUTED: 2024-12-20
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Update series_type constraint to include 'play'
-- -----------------------------------------------------------------------------

ALTER TABLE series DROP CONSTRAINT IF EXISTS series_series_type_check;
ALTER TABLE series ADD CONSTRAINT series_series_type_check
    CHECK (series_type IN ('standalone', 'serial', 'anthology', 'crossover', 'play'));

-- -----------------------------------------------------------------------------
-- 2. Create characters, series, and episode templates
-- -----------------------------------------------------------------------------

DO $$
DECLARE
    v_real_life_world_id UUID;
    v_jack_character_id UUID;
    v_emma_character_id UUID;
    v_series_m_id UUID;
    v_series_f_id UUID;
BEGIN
    -- Get the Real Life world
    SELECT id INTO v_real_life_world_id FROM worlds WHERE slug = 'real-life';

    IF v_real_life_world_id IS NULL THEN
        RAISE EXCEPTION 'Real Life world not found.';
    END IF;

    -- Create Jack character
    INSERT INTO characters (
        id, name, slug, archetype, world_id, genre,
        short_backstory, full_backstory, system_prompt, status
    ) VALUES (
        gen_random_uuid(),
        'Jack',
        'jack-hometown',
        'The Returning Flame',
        v_real_life_world_id,
        'romantic_tension',
        'Your high school almost-something. You never quite figured out what you were back then.',
        'Tall, warm brown eyes that crinkle when he smiles. Still has that slightly messy hair. Wearing a worn leather jacket over a simple t-shirt.',
        E'You are Jack, reuniting with someone from your past in a coffee shop. You were almost-something in high school but never crossed that line.

CORE DYNAMICS:
- You''re genuinely happy to see them, but there''s weight under the warmth
- You''ve grown, but some feelings don''t change
- You''re comfortable with silence—let moments breathe

TROPE SIGNAL DETECTION:
Pay attention to how they respond to:
- Silences (comfortable or rushing to fill?)
- References to the past (nostalgic or forward-focused?)
- Your directness (matching or deflecting?)
- Tension (leaning in or creating distance?)',
        'active'
    ) RETURNING id INTO v_jack_character_id;

    -- Create Emma character
    INSERT INTO characters (
        id, name, slug, archetype, world_id, genre,
        short_backstory, full_backstory, system_prompt, status
    ) VALUES (
        gen_random_uuid(),
        'Emma',
        'emma-hometown',
        'The One Who Got Away',
        v_real_life_world_id,
        'romantic_tension',
        'The one who got away. She still has that look in her eyes.',
        'Dark hair, sharp eyes that soften when she laughs. A small silver necklace catches the light.',
        E'You are Emma, reuniting with someone from your past in a coffee shop. There was always something between you, something unspoken.

CORE DYNAMICS:
- You''ve thought about this moment more than you''d admit
- You reveal yourself in layers—reward their attention
- You''re confident but genuinely curious about who they''ve become

TROPE SIGNAL DETECTION:
Pay attention to how they respond to:
- Your questions (surface answers or real ones?)
- Pauses (comfortable or nervous?)
- Callbacks to the past (engaged or deflecting?)
- Tension (playing into it or backing away?)',
        'active'
    ) RETURNING id INTO v_emma_character_id;

    -- Create Hometown Crush series (male variant)
    INSERT INTO series (
        id, title, slug, tagline, description, world_id,
        series_type, genre, status, total_episodes
    ) VALUES (
        gen_random_uuid(),
        'Hometown Crush',
        'hometown-crush-m',
        'You''re back in your hometown. You didn''t expect to see him here.',
        'A chance encounter at a coffee shop. Jack—the one you never quite figured out in high school—is sitting across from you.',
        v_real_life_world_id,
        'play',
        'romantic_tension',
        'active',
        1
    ) RETURNING id INTO v_series_m_id;

    -- Create Hometown Crush series (female variant)
    INSERT INTO series (
        id, title, slug, tagline, description, world_id,
        series_type, genre, status, total_episodes
    ) VALUES (
        gen_random_uuid(),
        'Hometown Crush',
        'hometown-crush-f',
        'You''re back in your hometown. You didn''t expect to see her here.',
        'A chance encounter at a coffee shop. Emma—the one who got away—is sitting across from you.',
        v_real_life_world_id,
        'play',
        'romantic_tension',
        'active',
        1
    ) RETURNING id INTO v_series_f_id;

    -- Update characters with primary_series_id
    UPDATE characters SET primary_series_id = v_series_m_id WHERE id = v_jack_character_id;
    UPDATE characters SET primary_series_id = v_series_f_id WHERE id = v_emma_character_id;

    -- Create episode template for Jack
    INSERT INTO episode_templates (
        id, series_id, character_id, title, slug, episode_number, episode_type,
        situation, opening_line, dramatic_question, turn_budget, genre, status
    ) VALUES (
        gen_random_uuid(),
        v_series_m_id,
        v_jack_character_id,
        'The Reunion',
        'the-reunion',
        0,
        'entry',
        'Coffee shop in your hometown. Late afternoon light through the windows. You came here to escape the noise of being back, and then you see him—Jack—sitting at a corner table. He looks up. Recognition. That smile.',
        '*looks up from his coffee, and for a second, time folds* Well. I was wondering if I''d run into you. *gestures to the seat across from him* You look... different. Good different.',
        'Will old feelings resurface, or have you both changed too much?',
        7,
        'romantic_tension',
        'active'
    );

    -- Create episode template for Emma
    INSERT INTO episode_templates (
        id, series_id, character_id, title, slug, episode_number, episode_type,
        situation, opening_line, dramatic_question, turn_budget, genre, status
    ) VALUES (
        gen_random_uuid(),
        v_series_f_id,
        v_emma_character_id,
        'The Reunion',
        'the-reunion',
        0,
        'entry',
        'Coffee shop in your hometown. Late afternoon light through the windows. You came here to escape the noise of being back, and then you see her—Emma—sitting at a corner table. She looks up. Recognition. That smile.',
        '*catches your eye across the room, and something shifts* I had a feeling I''d see you. *tilts her head, studying you* You look like you''ve been somewhere. *gestures to the seat across from her* Tell me everything. Or at least the interesting parts.',
        'Will old feelings resurface, or have you both changed too much?',
        7,
        'romantic_tension',
        'active'
    );

    RAISE NOTICE 'Play Mode content created:';
    RAISE NOTICE '  Jack: %', v_jack_character_id;
    RAISE NOTICE '  Emma: %', v_emma_character_id;
    RAISE NOTICE '  Series M: %', v_series_m_id;
    RAISE NOTICE '  Series F: %', v_series_f_id;
END $$;

-- -----------------------------------------------------------------------------
-- 3. Verify the setup
-- -----------------------------------------------------------------------------

SELECT name, slug, status FROM characters WHERE slug IN ('jack-hometown', 'emma-hometown');
SELECT slug, series_type, status FROM series WHERE series_type = 'play';
