-- Add starter prompts to all Episode 0s that don't have them
-- Generated: 2026-01-12

-- Corner Office (workplace)
UPDATE episode_templates
SET starter_prompts = ARRAY[
  'Introduce yourself professionally',
  'Ask about the case details',
  'Keep your distance - stay focused'
]
WHERE id = 'baad6745-9092-42a2-87be-890caa433d81';

-- Session Notes (psychological)
UPDATE episode_templates
SET starter_prompts = ARRAY[
  'Sit down and wait for them to speak',
  'Ask what brings them here today',
  'Study their body language carefully'
]
WHERE id = '4f469a3e-34a4-45df-b356-7dd0f909533a';

-- The Duke''s Third Son (historical)
UPDATE episode_templates
SET starter_prompts = ARRAY[
  'Greet them with proper etiquette',
  'Browse the shelves quietly',
  'Ask what they''re reading'
]
WHERE id = '1e72ae7f-08e0-4732-bbac-019d43d4275a';

-- Debate Partners (GL)
UPDATE episode_templates
SET starter_prompts = ARRAY[
  'Decline politely',
  'Ask why they chose you',
  'Agree reluctantly'
]
WHERE id = '4a5f2c27-4066-4b89-99ea-0004f8fd4837';

-- Ink & Canvas (BL)
UPDATE episode_templates
SET starter_prompts = ARRAY[
  'Show them your portfolio',
  'Ask what style they''re looking for',
  'Tell them your rates upfront'
]
WHERE id = 'd7980e61-d528-49bf-a0f4-71945a176015';

-- The Corner Cafe (cozy)
UPDATE episode_templates
SET starter_prompts = ARRAY[
  'Order your usual',
  'Ask about their day',
  'Notice something different about them'
]
WHERE id = 'b940a49c-4bc6-44f9-9e1f-2fdbdd9f51a7';

-- The Regressor''s Last Chance (fantasy_action) - CRITICAL
UPDATE episode_templates
SET starter_prompts = ARRAY[
  'Check what day it is - are you really back?',
  'Rush to warn someone about their death',
  'Test if you still have your abilities'
]
WHERE id = 'c0150f7f-c446-4006-a12f-50a365ecd243';

-- Death Flag: Deleted (otome_isekai) - CRITICAL
UPDATE episode_templates
SET starter_prompts = ARRAY[
  'Get up immediately - you need a plan',
  'Examine your reflection - confirm who you are',
  'Check the date - how much time do you have?'
]
WHERE id = 'ed805700-d648-4d13-9770-ec60754e0cab';

-- The Villainess Survives (otome_isekai) - CRITICAL
UPDATE episode_templates
SET starter_prompts = ARRAY[
  'Stay silent and observe him carefully',
  'Demand to know the charges against you',
  'Ask why he''s visiting personally'
]
WHERE id = '80a43b5c-c90d-4d5f-bb4e-988cce69bf90';

-- Room 404 (romantic_tension)
UPDATE episode_templates
SET starter_prompts = ARRAY[
  'Knock on their door',
  'Pretend you didn''t see anything',
  'Ask what they''re doing out here'
]
WHERE id = '5031ee6a-8f61-4e90-a44a-23e636ecbe80';
