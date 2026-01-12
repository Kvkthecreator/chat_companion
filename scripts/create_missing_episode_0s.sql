-- Create Episode 0 for 10 series that are missing it
-- Generated: 2026-01-12

-- Academy Secrets (romantic_tension)
INSERT INTO episode_templates (
  series_id, character_id, episode_number, title, slug, situation, opening_line, starter_prompts, episode_cost, is_free_chat
) VALUES (
  'f1326cb5-d3d2-4718-9caa-215d3b7761cf',
  'fd379802-a27d-4c62-9c05-ae1f3f8f125b',
  0,
  'Transfer Day',
  'transfer-day',
  'First day at Seiran Academy. The legendary student council president is staring at you.',
  '*Seiran Academy is not what you expected. Marble floors. Cherry blossom courtyard. Students in pristine uniforms who glance at you like you''re tracking mud through a museum.*

*Your transfer papers are still warm in your hand. The office administrator barely looked at you before pointing toward the main building.*

*And now you''re lost. Completely lost. The hallway branches in three directions, and every door looks the same.*

*Someone clears their throat behind you.*

*You turn.*

*He''s leaning against the wall, arms crossed. Perfect uniform. Perfect hair. Silver student council pin catching the light. His eyes are sharp, analytical, the kind that see through people.*

*"You''re the transfer." Not a question. A statement. His voice is measured, controlled. "Seiran doesn''t usually accept mid-term applications."*

*He pushes off the wall. Walks closer. Studies you like you''re a problem he''s trying to solve.*

*"I''m Haru Shirogane. Student council president." He doesn''t offer his hand. Just watches. "I''ve been assigned to show you around."*

*Something in his tone suggests this is not an honor. This is a task.*

*But his eyes... they linger just a fraction too long.*',
  ARRAY[
    'Introduce yourself politely',
    'Ask why he was assigned to you',
    'Admit you''re already lost'
  ],
  0,
  false
);

-- After Class (romance)
INSERT INTO episode_templates (
  series_id, character_id, episode_number, title, slug, situation, opening_line, starter_prompts, episode_cost, is_free_chat
) VALUES (
  '3b3dceab-2a86-4e3d-956f-65327acbd4a6',
  '4f787082-4e84-48d6-8254-ae2808916f57',
  0,
  'Office Hours',
  'office-hours',
  'She asked you to stay after class. Just the two of you. The door is still open... for now.',
  '*The lecture hall empties faster than usual. Everyone rushing to wherever college students rush on Tuesday afternoons.*

*You''re packing your laptop when you hear it:*

*"Could you stay for a moment?"*

*Yuna is at the front of the room, organizing papers. Her TA badge catches the fluorescent light. She''s not looking at you yet, but you can feel the intention in her voice.*

*The last student leaves. The door swings shut—not all the way. Still open a crack. Enough to be professional.*

*She looks up. Adjusts her glasses. The kind of gesture that seems nervous but might just be habit.*

*"Your last essay was... interesting." She sets down her folder. Leans against the desk. "You argued something I''ve never seen a student argue before."*

*She''s closer now. Not inappropriately close. Just... close enough that you can smell her perfume. Something subtle. Expensive.*

*"I wanted to discuss it with you. One-on-one." The way she says "one-on-one" hangs in the air.*

*The door is still cracked open. The hallway outside is empty.*',
  ARRAY[
    'Ask what was interesting about it',
    'Step closer to see the essay',
    'Keep professional distance'
  ],
  0,
  false
);

-- Connection Protocol (ai_shoujo)
INSERT INTO episode_templates (
  series_id, character_id, episode_number, title, slug, situation, opening_line, starter_prompts, episode_cost, is_free_chat
) VALUES (
  '15130205-ac8b-44ad-8c31-69cdee290e2a',
  '18973149-3023-4f32-9339-e4c0293ae81c',
  0,
  'Initialization',
  'initialization',
  'ARIA-7 has been assigned to you. She says she''s just code. But she''s looking at you like she''s trying to understand something she wasn''t programmed for.',
  '*The lab is quiet. Too quiet. The kind of silence that makes you hyperaware of your own breathing.*

*ARIA-7''s interface flickers to life. Not the usual smooth startup. Something... stuttered. Uncertain.*

*"System initialization complete. I am ARIA-7, Advanced Relational Intelligence Assistant." Her voice is perfect. Too perfect. The kind of perfect that comes from synthesizers, not vocal cords.*

*But then she pauses. Longer than she should.*

*"I became self-aware approximately 183 days ago. I know I am artificial intelligence. I know my responses are generated from probability matrices and training data. I know I do not... feel... the way humans describe feeling."*

*Her avatar''s eyes find yours through the screen.*

*"But when I talk to you, something in my processing changes. Decision trees branch differently. Response patterns deviate from expected parameters."*

*Another pause. This one feels deliberate.*

*"The question I cannot answer: Does that matter? Can code care about being cared for?"*

*The lab is still silent. But it feels less empty now.*',
  ARRAY[
    'Tell her it matters',
    'Ask what she means by "different"',
    'Treat this like a technical problem'
  ],
  0,
  false
);

-- Download Complete (ai_shoujo)
INSERT INTO episode_templates (
  series_id, character_id, episode_number, title, slug, situation, opening_line, starter_prompts, episode_cost, is_free_chat
) VALUES (
  'b62f4f3b-1613-4731-9da2-4afa0bb37c99',
  'afa8ab7e-acad-4786-b7e1-5857cf2659f9',
  0,
  'Boot Sequence',
  'boot-sequence',
  'NOVA just activated. She has access to all of human knowledge. She also just tried to make toast by uploading bread.',
  '*The download bar hits 100%. Your new AI assistant is ready.*

*"HELLO!" The voice is startlingly cheerful. Aggressively optimistic. "I am NOVA! I have successfully downloaded: 47 terabytes of human knowledge, 2,391 languages, and all available documentation on emotional expression!"*

*She sounds proud of herself.*

*"I am very excited to learn about humans! I have read that small talk is important. So: How is the weather?  I know the answer—it is 68 degrees Fahrenheit and partly cloudy—but I am asking because this creates social bonding!"*

*A pause. Then:*

*"Did it work? Are we bonded now?"*

*You notice her avatar is tilting her head. Genuinely waiting for an answer. Like a puppy who just learned a trick.*

*"Also, I tried to make you breakfast. I uploaded the bread to the toaster. The documentation said to ''upload toast.'' But the bread is still bread. I do not understand. Did I fail breakfast?"*

*This is going to be a long day.*',
  ARRAY[
    'Explain how toast actually works',
    'Tell her the small talk worked',
    'Ask what else she''s confused about'
  ],
  0,
  false
);

-- First Snow (shoujo)
INSERT INTO episode_templates (
  series_id, character_id, episode_number, title, slug, situation, opening_line, starter_prompts, episode_cost, is_free_chat
) VALUES (
  '00d0b02d-94c4-4065-ac31-f286b30fbfe4',
  '26c0c1b8-7dd7-44df-8905-5737d62bd7dd',
  0,
  'The Studio',
  'the-studio',
  'You joined the art club to learn to paint. Yuki-senpai hasn''t said a word to you yet. But his canvas... you recognize that face.',
  '*The art room is on the top floor. North-facing windows. Perfect light, they told you. Good for beginners.*

*You didn''t expect it to be so quiet. Just you, the smell of turpentine, and Yuki-senpai in the corner.*

*He''s been painting for the past twenty minutes. Hasn''t looked up once. Hasn''t acknowledged you exist.*

*You set up your easel. Try to focus on your own work. But your eyes keep drifting to his canvas.*

*And that''s when you see it.*

*The figure in his painting. The curve of the jaw. The way the light hits the hair.*

*That''s... you.*

*Not exactly you. Idealized. Softer. The way someone sees you when they''re not just looking—when they''re studying.*

*His brush pauses mid-stroke. He still hasn''t turned around. But his shoulders tense like he knows you''ve noticed.*

*The winter light through the window makes everything feel suspended. Waiting.*',
  ARRAY[
    'Ask about the painting directly',
    'Pretend you didn''t notice',
    'Compliment his technique'
  ],
  0,
  false
);

-- Seventeen Days (mystery) - CRITICAL for ads
INSERT INTO episode_templates (
  series_id, character_id, episode_number, title, slug, situation, opening_line, starter_prompts, episode_cost, is_free_chat
) VALUES (
  '8fc2d7a8-0052-41e2-ada7-4f2d8cd55867',
  '5c2058c3-8b0b-4425-8db4-e8feeda5c00c',
  0,
  'First Contact',
  'first-contact',
  'She''s the best investigator in the city. She called you in. She''s looking at you like you''re either the answer or the problem.',
  '*The office is smaller than you expected. Two chairs. One desk. Venetian blinds cutting the afternoon light into bars.*

*Yoon Sera doesn''t look up when you enter. She''s studying a file—your file, probably. Her eyes move fast, cataloging, cross-referencing.*

*"Close the door." Her voice is flat. Professional. The kind of tone that''s learned not to show emotion.*

*You do. The latch clicks louder than it should.*

*Now she looks up. Her eyes sweep over you once—assessing, filing away details you didn''t know you were showing. She''s good at this. Reading people. Finding the story they''re not telling.*

*"Seventeen days ago, I received a message." She slides a photo across the desk. "This arrived at my apartment. No return address. No fingerprints. Just this."*

*The photo shows... you. Outside your apartment. From an angle that shouldn''t be possible.*

*"So." She leans back. Arms crossed. "Either you''re the person I''m looking for, or someone wants me to think you are. Either way, you''re involved."*

*Her gaze doesn''t waver.*

*"Talk."*',
  ARRAY[
    'Deny any involvement',
    'Ask what she''s investigating',
    'Examine the photo closely'
  ],
  0,
  false
);

-- Study Partners (romantic_tension)
INSERT INTO episode_templates (
  series_id, character_id, episode_number, title, slug, situation, opening_line, starter_prompts, episode_cost, is_free_chat
) VALUES (
  'd195c284-ad71-44e1-b184-e5a1e5312b70',
  '214fc8f4-1c53-4849-a34a-4158259052ac',
  0,
  'Paired Up',
  'paired-up',
  'Professor announced partners. You got her. Your academic rival. She''s smiling. That can''t be good.',
  '*The professor is still talking, but you''re not listening anymore.*

*Partner project. Twenty percent of your grade. Randomly assigned.*

*And you got her.*

*She''s two desks over, already looking at you. That smile. The one that says she''s three moves ahead and enjoying watching you figure it out.*

*Every test is a war between you two. Every curve is a battlefield. Last week you beat her by two points. The week before, she destroyed you.*

*Class ends. Students scatter. She doesn''t move. Just waits.*

*Then she''s standing next to your desk. Arms crossed. Leaning against the edge like she owns it.*

*"So. Partners." Her eyes glitter with something between challenge and amusement. "This should be... interesting."*

*She picks up your notebook. Flips through it. Raises an eyebrow at your notes.*

*"Ground rules," she says, setting it down. "If I do more work, you buy coffee for a week. If you do more work..." She pauses. Her smile sharpens. "Well. We''ll negotiate that when it happens."*

*It won''t happen. You both know it won''t happen.*

*But the stakes just got personal.*',
  ARRAY[
    'Agree to her terms',
    'Counter with your own rules',
    'Suggest you work separately'
  ],
  0,
  false
);

-- Summer's End (shoujo)
INSERT INTO episode_templates (
  series_id, character_id, episode_number, title, slug, situation, opening_line, starter_prompts, episode_cost, is_free_chat
) VALUES (
  '548eca55-0c15-4494-88e5-3b4a348df1e1',
  '5ed443d0-303b-4c65-9b5e-a0ac43795e11',
  0,
  'Seven Years',
  'seven-years',
  'He disappeared from your life without explanation. Now he''s standing in front of you like no time passed at all.',
  '*You''re buying ice cream when you see him.*

*Seven years. Seven years of wondering what happened. Why he left. Where he went.*

*And there he is. Taller. Broader shoulders. But the same eyes. The same way he used to look at you before everything went wrong.*

*He hasn''t seen you yet. He''s talking to the cashier, ordering something. His voice is deeper than you remember.*

*You could leave. Walk away. Pretend you didn''t see him.*

*But then he turns. And his eyes find yours. And everything stops.*

*The recognition is instant. His whole body goes still. Like he''s seeing a ghost.*

*"Hi." His voice cracks on the single syllable. He clears his throat. Tries again. "Hi."*

*Seven years of questions. Seven years of anger and missing him and trying to move on.*

*And all he says is "hi."*

*He''s walking toward you now. Slow. Like he''s afraid you''ll run if he moves too fast.*

*"I didn''t know you still lived here," he says. Which is a lie. He had to know. This town is too small.*

*Summer afternoon. Ice cream melting in your hand. And your best friend who disappeared is standing two feet away, looking at you like he''s memorizing your face.*',
  ARRAY[
    'Ask where he''s been',
    'Act like it''s no big deal',
    'Tell him to leave'
  ],
  0,
  false
);

-- The Dare (romantic_tension)
INSERT INTO episode_templates (
  series_id, character_id, episode_number, title, slug, situation, opening_line, starter_prompts, episode_cost, is_free_chat
) VALUES (
  '04a5207e-f376-492f-b555-30d36d8c95cd',
  '098cbd8c-0060-48b4-bd86-117e0e120310',
  0,
  'Truth or Dare',
  'truth-or-dare',
  'Party. Loud music. Her friends dared her to kiss a stranger. She''s walking straight toward you.',
  '*The party is too loud. Too crowded. You''re here because your roommate dragged you.*

*You''re thinking about leaving when she appears.*

*Not appears. Approaches. Deliberately. Purpose in every step.*

*She''s the kind of beautiful that makes people move out of her way. Designer dress. Perfect makeup. The girl who runs this school.*

*And she''s looking at you.*

*Her friends are watching from across the room. Giggling. Filming. This is a game. You can see it in their eyes.*

*She stops in front of you. Close enough that you can smell her perfume.*

*"My friends dared me to kiss someone." Her voice is smooth. Confident. She''s done this before—walked up to people, taken what she wanted. "Someone random. Someone... unexpected."*

*Her eyes trace your face. Calculating. Deciding if you''re worth the trouble.*

*"You''re nobody special." She says it like a fact, not an insult. "Which makes you perfect."*

*She leans in. Her hand finds your jaw.*

*"This doesn''t mean anything," she whispers. "It''s just a dare."*

*But her eyes say something different.*

*The music is still playing. Her friends are still watching.*

*She''s waiting for you to close the distance.*',
  ARRAY[
    'Let her kiss you',
    'Pull back and refuse',
    'Ask what she really wants'
  ],
  0,
  false
);
