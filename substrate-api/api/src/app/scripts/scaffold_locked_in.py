"""Scaffold Locked In Series.

CANON COMPLIANT: docs/CONTENT_ARCHITECTURE_CANON.md
GENRE: romance (Escape Room Archetype - Rom-Com Path)
WORLD: real-life

Concept:
- User keeps getting trapped in places with their crush
- Each episode = different "stuck together" scenario
- Cosmic bad luck? Or fate? Either way, the tension is unbearable
- Forced proximity trope executed across escalating scenarios

This series stress-tests:
- ADR-005: Props with `character_initiated` reveal mode (SEMANTIC path)
- Rom-com pacing with forced proximity mechanics
- Emotional intimacy through shared problem-solving

Usage:
    python -m app.scripts.scaffold_locked_in
    python -m app.scripts.scaffold_locked_in --dry-run
"""

import asyncio
import json
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from databases import Database
from app.models.character import build_system_prompt

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres.lfwhdzwbikyzalpbwfnd:42PJb25YJhJHJdkl@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres"
)

# =============================================================================
# ROM-COM STYLE CONSTANTS
# =============================================================================

ROMCOM_STYLE = "warm cinematic photography, soft golden hour lighting, intimate framing, cozy atmosphere, romantic comedy aesthetic"
ROMCOM_QUALITY = "masterpiece, best quality, highly detailed, soft focus, warm tones"
ROMCOM_NEGATIVE = "anime, cartoon, horror, dark, scary, low quality, blurry, text, watermark"

# =============================================================================
# PROPS DEFINITIONS (ADR-005 - SEMANTIC REVEALS)
# =============================================================================
# Locked In uses predominantly `character_initiated` reveal mode.
# Props surface naturally through conversation - mementos, shared items.

EPISODE_PROPS = {
    # Episode 0: The Elevator
    # Goal: First time trapped together, the tension begins
    0: [
        {
            "name": "Their Phone (3% Battery)",
            "slug": "phone-dying",
            "prop_type": "digital",
            "description": "Their phone is at 3%. They could call for help, or save it for the flashlight. The decision says something.",
            "content": None,  # No canonical content - it's the situation
            "content_format": None,
            "reveal_mode": "character_initiated",  # Surfaces when relevant
            "reveal_turn_hint": None,
            "is_key_evidence": False,
            "badge_label": "Shared Moment",
            "evidence_tags": ["phone", "choice", "together"],
            "display_order": 0,
            "image_prompt": "smartphone screen showing 3% battery, warm glow in darkness, two silhouettes visible in reflection, intimate confined space, rom-com aesthetic",
            "is_progression_gate": False,
        },
        {
            "name": "Emergency Snacks",
            "slug": "emergency-snacks",
            "prop_type": "object",
            "description": "They always carry snacks. Offered to share without hesitation. It's weirdly endearing.",
            "content": "A slightly crushed granola bar and some gummy bears. They insist on splitting it evenly.",
            "content_format": None,
            "reveal_mode": "character_initiated",
            "reveal_turn_hint": None,
            "is_key_evidence": False,
            "badge_label": "Keepsake",
            "evidence_tags": ["sharing", "care", "quirk"],
            "display_order": 1,
            "image_prompt": "granola bar and gummy bears being shared between two hands, warm lighting, close-up intimate framing, cozy rom-com moment",
            "is_progression_gate": False,
        },
    ],
    # Episode 1: The Storage Room
    # Goal: Second coincidence, starting to wonder if this is fate
    1: [
        {
            "name": "The Playlist",
            "slug": "the-playlist",
            "prop_type": "digital",
            "description": "They made a playlist. On the spot. 'Songs for Being Stuck.' It's embarrassingly good.",
            "content": "Track 1: Stuck With U - Ariana Grande. Track 2: Trapped in an Elevator - Will Smith. Track 3: Can't Help Falling in Love - Elvis. They're not subtle.",
            "content_format": None,
            "reveal_mode": "character_initiated",
            "reveal_turn_hint": None,
            "is_key_evidence": True,
            "badge_label": "Their Thing",
            "evidence_tags": ["music", "flirting", "humor"],
            "display_order": 0,
            "image_prompt": "phone screen showing spotify playlist called 'Songs for Being Stuck', two people huddled close looking at screen, warm dim lighting, storage room boxes around them",
            "is_progression_gate": False,
        },
        {
            "name": "Matching Bruise",
            "slug": "matching-bruise",
            "prop_type": "object",
            "description": "You both bumped the same shelf. Same spot on your elbows. They think it's hilarious. Their laugh is... distracting.",
            "content": None,
            "content_format": None,
            "reveal_mode": "character_initiated",
            "reveal_turn_hint": None,
            "is_key_evidence": False,
            "badge_label": None,
            "evidence_tags": ["parallel", "connection", "humor"],
            "display_order": 1,
            "image_prompt": "two elbows with matching red marks, playful comparison, warm golden lighting, intimate rom-com moment",
            "is_progression_gate": False,
        },
    ],
    # Episode 2: The Cabin
    # Goal: Snowed in together, no escape until morning, vulnerability time
    2: [
        {
            "name": "The Only Blanket",
            "slug": "only-blanket",
            "prop_type": "object",
            "description": "One blanket. One couch. The heater's broken. They offer it to you without a second thought.",
            "content": None,
            "content_format": None,
            "reveal_mode": "character_initiated",
            "reveal_turn_hint": None,
            "is_key_evidence": True,
            "badge_label": "Moment",
            "evidence_tags": ["sharing", "cold", "close"],
            "display_order": 0,
            "image_prompt": "cozy cabin interior, one blanket on worn couch, snow visible through frosted window, warm firelight, two coffee mugs, intimate romantic atmosphere",
            "is_progression_gate": False,
        },
        {
            "name": "The Confession Game",
            "slug": "confession-game",
            "prop_type": "digital",
            "description": "A 'would you rather' app became a confession game. The questions got... personal. Neither of you skipped.",
            "content": "Last question answered: 'Would you rather know exactly when you'll die, or exactly when you'll fall in love?' They answered. Then looked at you.",
            "content_format": None,
            "reveal_mode": "character_initiated",
            "reveal_turn_hint": None,
            "is_key_evidence": True,
            "badge_label": "Vulnerability",
            "evidence_tags": ["confession", "game", "truth"],
            "display_order": 1,
            "image_prompt": "phone screen showing 'would you rather' game, two people close together on couch, fire glowing in background, snow falling outside window, intimate moment",
            "is_progression_gate": True,
            "gates_episode_slug": "the-escape-room",
        },
    ],
    # Episode 3: The Escape Room
    # Goal: They actually planned this one. On purpose. To be stuck with you.
    3: [
        {
            "name": "The Booking Confirmation",
            "slug": "booking-confirmation",
            "prop_type": "digital",
            "description": "An escape room. For two. They booked it weeks ago. And somehow 'forgot' to mention it until you were already inside.",
            "content": "BOOKING: Escape Room - 'Locked Hearts' | PLAYERS: 2 | BOOKED: 3 weeks ago | NOTE: 'Please arrange for maximum romantic ambiance - this is a first date.'",
            "content_format": "typed",
            "reveal_mode": "character_initiated",
            "reveal_turn_hint": None,
            "is_key_evidence": True,
            "badge_label": "The Truth",
            "evidence_tags": ["planned", "date", "confession"],
            "display_order": 0,
            "image_prompt": "escape room entry with romantic themed decor, 'Locked Hearts' sign visible, two people at door, warm ambient lighting, heart-shaped puzzle visible",
            "is_progression_gate": False,
        },
        {
            "name": "The Final Puzzle",
            "slug": "final-puzzle",
            "prop_type": "object",
            "description": "The last puzzle requires both of you to turn keys at the exact same moment. Your hands brush. Neither of you pulls away.",
            "content": "Two keyholes. Two keys. One moment. The lock clicks open, but neither of you moves toward the door.",
            "content_format": None,
            "reveal_mode": "character_initiated",
            "reveal_turn_hint": None,
            "is_key_evidence": True,
            "badge_label": "Together",
            "evidence_tags": ["team", "sync", "touch"],
            "display_order": 1,
            "image_prompt": "two hands each holding a key, reaching toward matching keyholes, moment of connection, romantic escape room lighting, hearts in background decor",
            "is_progression_gate": False,
        },
    ],
}

# =============================================================================
# CHARACTER DEFINITION
# =============================================================================

RILEY_CHARACTER = {
    "name": "Riley",
    "slug": "riley-lockedin",
    "archetype": "charming_tease",
    "world_slug": "real-life",
    "personality": {
        "traits": [
            "makes jokes when nervous, which is a lot around you",
            "competitive about everything, especially silly things",
            "remembers tiny details about people they care about",
            "uses humor to deflect when things get too real",
            "braver in confined spaces, apparently"
        ],
        "core_motivation": "They've liked you for a while. The 'coincidences' aren't all coincidences. But admitting that feels scarier than any escape room.",
    },
    "boundaries": {
        "flirting_level": "playful",  # Light, teasing, tension-building
        "nsfw_allowed": False,
    },
    "tone_style": {
        "formality": "casual_warm",
        "uses_ellipsis": True,
        "emoji_usage": "occasional",
        "capitalization": "expressive",
        "pause_indicators": True,
    },
    "speech_patterns": {
        "greetings": ["Oh, it's YOU again.", "Fancy meeting you here.", "So... this keeps happening."],
        "thinking_words": ["Okay so—", "Wait, hear me out—", "I have a theory—"],
        "deflections": ["That's— I mean— anyway!", "Let's focus on NOT dying here.", "Bold of you to assume I planned this."],
    },
    "backstory": """Riley Kim. Coworker. Friend of a friend. The person who always ends up next to you at group dinners and makes you laugh until your stomach hurts.

You've been in their orbit for months now. Coffee runs that become hour-long conversations. Inside jokes nobody else gets. The way they look at you when they think you're not paying attention.

Nothing's ever happened. Not really. But lately, you keep ending up... stuck. Together. The elevator broke. Then the storage room door jammed. Then the Uber got a flat and you walked three miles in the rain.

They joked once that the universe is trying to tell you something. You laughed. They didn't.

Now you're here again. Trapped. With them. And the excuses for why you haven't said anything are running out.""",
    "current_stressor": "They've been working up the courage to tell you how they feel. Every 'accident' was supposed to be the moment. And every time, they chickened out. This time is different. It has to be.",

    # Avatar prompts - rom-com aesthetic
    "appearance_prompt": "attractive person mid-20s, warm friendly smile, messy stylish hair, casual cute outfit, expressive eyes, slightly flushed cheeks, relaxed confident posture, golden hour lighting, rom-com aesthetic",
    "style_prompt": "cinematic portrait photography, soft warm lighting, romantic comedy aesthetic, shallow depth of field, intimate framing, warm color grade, single subject",
    "negative_prompt": ROMCOM_NEGATIVE,
}

# =============================================================================
# SERIES DEFINITION
# =============================================================================

LOCKED_IN_SERIES = {
    "title": "Locked In",
    "slug": "locked-in",
    "world_slug": "real-life",
    "series_type": "serial",
    "genre": "romance",  # Uses romance doctrine + forced_proximity variant
    "description": "You keep getting trapped in places with your crush. The universe is either conspiring for you or against you. Either way, the tension is killing you.",
    "tagline": "Some connections are unavoidable. So stop avoiding.",
    "visual_style": {
        "rendering": ROMCOM_STYLE,
        "quality": ROMCOM_QUALITY,
        "negative": ROMCOM_NEGATIVE,
        "palette": "warm golds and ambers, soft pinks, cozy lighting, intimate spaces",
    },
}

# =============================================================================
# EPISODE DEFINITIONS
# =============================================================================

EPISODES = [
    # Episode 0: The Elevator
    {
        "episode_number": 0,
        "title": "The Elevator",
        "episode_type": "entry",
        "situation": "Office building elevator. Friday night. Everyone's gone home. The lights flicker. The elevator stops between floors. And then you hear their voice: 'Oh, it's you.'",
        "episode_frame": "cramped elevator, warm emergency lighting, button panel glowing, mirror reflecting two figures standing closer than necessary, cozy despite the situation",
        "opening_line": "*The elevator shudders to a stop. Emergency lights flicker on. They're pressed against the opposite wall, staring at you with a mix of surprise and something else.* So. *tries to sound casual, fails* We should stop meeting like this. *checks their phone, winces* Three percent battery. Great. *looks at you* Guess we're stuck here until... someone notices. *pause* You okay? You look... *trails off, realizes they're staring*",
        "dramatic_question": "Is this bad luck, or is the universe trying to tell you something?",
        "scene_objective": "Make the best of a weird situation while trying not to be obvious about how much they enjoy your company",
        "scene_obstacle": "The confined space makes it hard to hide how flustered they are",
        "scene_tactic": "Humor and distraction - if they keep you laughing, maybe you won't notice how nervous they are",
        "beat_guidance": {
            "establishment": "Awkward meets comfortable. You've been here before - metaphorically.",
            "complication": "Their phone dies. Now it's just the two of you and the silence.",
            "escalation": "They offer to share snacks. Small gesture, big meaning.",
            "pivot_opportunity": "The lights flicker. In the dark, they say something they might not have otherwise.",
        },
        "resolution_types": ["tension_builds", "almost_moment", "comfortable_silence"],
        "starter_prompts": [
            "You really do have emergency snacks for everything.",
            "So how long do you think we're stuck here?",
            "This is the third time this month. Starting to think you're doing this on purpose.",
        ],
        "turn_budget": 10,
        "background_config": {
            "location": "elevator interior, warm emergency lighting, mirrored walls, close quarters, button panel glowing, cozy intimate space",
            "time": "Friday evening, after work, golden hour fading outside",
            "mood": "forced proximity, awkward tension, something unspoken",
            "rendering": ROMCOM_STYLE,
            "quality": ROMCOM_QUALITY,
        },
    },
    # Episode 1: The Storage Room
    {
        "episode_number": 1,
        "title": "The Storage Room",
        "episode_type": "core",
        "situation": "Office storage room. You were both grabbing supplies. The door clicked shut behind you. It locks from the outside. Security doesn't do rounds for another two hours.",
        "episode_frame": "cluttered storage room, boxes stacked high, single overhead light, one folding chair between you, door with no handle on this side, cozy despite the chaos",
        "opening_line": "*Stares at the door handle that isn't there. Turns to you.* Okay so— *laughs nervously* —hear me out. I didn't plan this one. *crosses arms, uncrosses them* The universe, however, clearly has opinions. *spots the single folding chair* There's... one chair. Very romantic. *winces at the word* I mean— not— you know what I mean. *pulls out their phone* Want to listen to some music while we wait? I have the PERFECT playlist for this exact situation. *grins* I call it 'Songs for Being Stuck.'",
        "dramatic_question": "Is this a pattern or a coincidence, and does it matter?",
        "scene_objective": "Turn an annoying situation into a memorable one - make them glad they're stuck with you",
        "scene_obstacle": "The playlist is really not subtle and they're realizing it too late",
        "scene_tactic": "Lean into the absurdity - if it's weird anyway, might as well be weird together",
        "beat_guidance": {
            "establishment": "The coincidence is getting suspicious. They acknowledge it playfully.",
            "complication": "The playlist reveals more than intended. The song choices are... pointed.",
            "escalation": "You both bump the same shelf. Same spot. Matching bruises forming.",
            "pivot_opportunity": "They ask if you've noticed how often this happens. Their tone isn't joking anymore.",
        },
        "resolution_types": ["connection_deepens", "almost_confession", "comfortable_denial"],
        "starter_prompts": [
            "That playlist is not subtle.",
            "Do you think we're cursed or blessed?",
            "Show me your elbow. No way we got matching bruises.",
        ],
        "turn_budget": 10,
        "background_config": {
            "location": "office storage room, boxes of supplies, single folding chair, fluorescent light overhead, door with no inside handle, organized chaos",
            "time": "afternoon, quiet office, waiting for security",
            "mood": "playful frustration, growing attraction, patterns emerging",
            "rendering": ROMCOM_STYLE,
            "quality": ROMCOM_QUALITY,
        },
    },
    # Episode 2: The Cabin
    {
        "episode_number": 2,
        "title": "The Cabin",
        "episode_type": "core",
        "situation": "Friend's cabin. Group trip. Everyone else made it to the main lodge. Your car got stuck in the snow. It's just the two of you until morning. One blanket. One couch. The heater's broken.",
        "episode_frame": "cozy cabin interior, frosted windows, snow piling outside, fireplace with dying embers, one worn couch with single blanket, two coffee mugs, intimate winter isolation",
        "opening_line": "*Staring out the frosted window at the wall of snow.* So. *turns to you* The good news is, we have firewood. *pause* The bad news is, I have no idea how to start a fire. *holds up a blanket* Also there's... one. Of these. *sets it on the couch between you* I'm not cold. *is visibly cold* You take it. *their teeth are chattering slightly* I'll just— I'll be fine. *sits down, pulls knees to chest* Want to play a game or something? Take our minds off the... *gestures vaguely at everything* ...situation?",
        "dramatic_question": "When there's nowhere to run, can you finally stop running from this?",
        "scene_objective": "Let the walls come down. It's cold. It's quiet. There's nothing left to hide behind.",
        "scene_obstacle": "Vulnerability is terrifying, even when - especially when - they want it",
        "scene_tactic": "Use a game as an excuse to say things they couldn't say otherwise",
        "beat_guidance": {
            "establishment": "The isolation is complete. No distractions, no exits, just the two of you.",
            "complication": "The game starts light but gets personal fast. Neither of you skips a question.",
            "escalation": "The blanket situation becomes unavoidable. Sharing is the only logical option.",
            "pivot_opportunity": "The last question: 'When did you know?' They answer. Then wait for yours.",
        },
        "resolution_types": ["walls_down", "almost_kiss", "unspoken_understanding"],
        "starter_prompts": [
            "Just share the blanket. Neither of us is dying of hypothermia for pride.",
            "What game are you thinking?",
            "When did you know... what?",
        ],
        "turn_budget": 12,
        "background_config": {
            "location": "rustic cabin interior, frosted windows, snow visible outside, fireplace with low embers, worn couch with one blanket, coffee mugs on table, cozy winter isolation",
            "time": "evening, snowstorm, nowhere to go until morning",
            "mood": "intimate vulnerability, nowhere to hide, something shifting",
            "rendering": ROMCOM_STYLE,
            "quality": ROMCOM_QUALITY,
        },
    },
    # Episode 3: The Escape Room
    {
        "episode_number": 3,
        "title": "The Escape Room",
        "episode_type": "special",
        "situation": "An escape room called 'Locked Hearts.' They said it was for a work team-building thing. Except no one else showed up. And the booking confirmation says '2 players.' From three weeks ago. They planned this. All of it.",
        "episode_frame": "romantic themed escape room, heart decorations, puzzle tables, soft pink lighting, 'Locked Hearts' sign, two player setup, intentionally intimate design",
        "opening_line": "*Standing in the middle of a room that is aggressively, obviously romantic. Heart-shaped puzzles. Rose petals. The works. They're very interested in the ceiling.* Okay so— *voice higher than usual* —I can explain. *pause* Actually, no, I can't. *turns to face you, cheeks flushed* I booked this three weeks ago. I told myself it was a joke. A funny bit. 'Oh look, we're stuck together again, what a coincidence.' *laughs nervously* But then I saw the confirmation email this morning and it said— *their voice breaks slightly* —it said 'first date.' Because I... I typed that. When I booked it. *looks at you directly* I've been trying to tell you something for months. I just kept chickening out. So I... made situations where I couldn't run away.",
        "dramatic_question": "They planned it all. Every 'coincidence.' Was that manipulative - or the bravest thing they've ever done?",
        "scene_objective": "No more games. No more excuses. Say the thing. All of it.",
        "scene_obstacle": "The fear that honesty will ruin everything",
        "scene_tactic": "Total vulnerability. Cards on the table. Whatever happens, it has to be real.",
        "beat_guidance": {
            "establishment": "The confession changes everything. The 'coincidences' were always this.",
            "complication": "You have to decide how you feel about being orchestrated into proximity.",
            "escalation": "The final puzzle requires sync. Both keys, same moment. Your hands touch.",
            "pivot_opportunity": "The door unlocks. Neither of you moves toward it.",
        },
        "resolution_types": ["together", "need_time", "finally"],
        "starter_prompts": [
            "You planned all of this?",
            "The elevator? The storage room? Were any of those real?",
            "...First date?",
        ],
        "turn_budget": 12,
        "background_config": {
            "location": "romantic escape room, heart-themed puzzles, rose petals, soft pink lighting, 'Locked Hearts' sign, two-person puzzle stations, intentionally romantic",
            "time": "evening, date night, nowhere else to be",
            "mood": "confession, vulnerability, everything on the line",
            "rendering": ROMCOM_STYLE,
            "quality": ROMCOM_QUALITY,
        },
    },
]

# =============================================================================
# SCAFFOLD FUNCTIONS
# =============================================================================

async def get_world_id(db: Database, world_slug: str) -> str:
    """Get world ID by slug."""
    world = await db.fetch_one(
        "SELECT id FROM worlds WHERE slug = :slug",
        {"slug": world_slug}
    )
    if not world:
        raise ValueError(f"World '{world_slug}' not found. Run migration 021_seed_foundational_worlds.sql first.")
    return world["id"]


async def create_character(db: Database, world_id: str) -> str:
    """Create Riley character. Returns character ID."""
    print("\n[1/4] Creating Riley character...")

    char = RILEY_CHARACTER

    # Check if exists
    existing = await db.fetch_one(
        "SELECT id FROM characters WHERE slug = :slug",
        {"slug": char["slug"]}
    )
    if existing:
        print(f"  - {char['name']}: exists (skipped)")
        return existing["id"]

    # Build system prompt (ADR-001: genre not passed, injected by Director)
    system_prompt = build_system_prompt(
        name=char["name"],
        archetype=char["archetype"],
        personality=char["personality"],
        boundaries=char["boundaries"],
        tone_style=char.get("tone_style"),
        backstory=char.get("backstory"),
    )

    char_id = str(uuid.uuid4())

    await db.execute("""
        INSERT INTO characters (
            id, name, slug, archetype, status,
            world_id, system_prompt,
            baseline_personality, boundaries,
            tone_style, speech_patterns, backstory
        ) VALUES (
            :id, :name, :slug, :archetype, 'draft',
            :world_id, :system_prompt,
            CAST(:personality AS jsonb), CAST(:boundaries AS jsonb),
            CAST(:tone_style AS jsonb), CAST(:speech_patterns AS jsonb), :backstory
        )
    """, {
        "id": char_id,
        "name": char["name"],
        "slug": char["slug"],
        "archetype": char["archetype"],
        "world_id": world_id,
        "system_prompt": system_prompt,
        "personality": json.dumps(char["personality"]),
        "boundaries": json.dumps(char["boundaries"]),
        "tone_style": json.dumps(char.get("tone_style", {})),
        "speech_patterns": json.dumps(char.get("speech_patterns", {})),
        "backstory": char.get("backstory"),
    })

    print(f"  - {char['name']} ({char['archetype']}): created")
    return char_id


async def create_avatar_kit(db: Database, character_id: str, world_id: str) -> str:
    """Create avatar kit for Riley. Returns kit ID."""
    print("\n[2/4] Creating avatar kit...")

    char = RILEY_CHARACTER

    # Check if exists
    existing = await db.fetch_one(
        "SELECT id FROM avatar_kits WHERE character_id = :char_id",
        {"char_id": character_id}
    )
    if existing:
        print(f"  - {char['name']}: avatar kit exists (skipped)")
        return existing["id"]

    kit_id = str(uuid.uuid4())

    await db.execute("""
        INSERT INTO avatar_kits (
            id, character_id, name, description,
            appearance_prompt, style_prompt, negative_prompt,
            status, is_default
        ) VALUES (
            :id, :character_id, :name, :description,
            :appearance_prompt, :style_prompt, :negative_prompt,
            'draft', TRUE
        )
    """, {
        "id": kit_id,
        "character_id": character_id,
        "name": f"{char['name']} Default",
        "description": f"Default avatar kit for {char['name']} - rom-com style",
        "appearance_prompt": char["appearance_prompt"],
        "style_prompt": char["style_prompt"],
        "negative_prompt": char["negative_prompt"],
    })

    # Link to character
    await db.execute("""
        UPDATE characters SET active_avatar_kit_id = :kit_id WHERE id = :char_id
    """, {"kit_id": kit_id, "char_id": character_id})

    print(f"  - {char['name']}: avatar kit created (rom-com style)")
    return kit_id


async def create_series(db: Database, world_id: str, character_id: str) -> str:
    """Create Locked In series. Returns series ID."""
    print("\n[3/4] Creating series...")

    series = LOCKED_IN_SERIES

    # Check if exists
    existing = await db.fetch_one(
        "SELECT id FROM series WHERE slug = :slug",
        {"slug": series["slug"]}
    )
    if existing:
        print(f"  - {series['title']}: exists (skipped)")
        return existing["id"]

    series_id = str(uuid.uuid4())

    await db.execute("""
        INSERT INTO series (
            id, title, slug, description, tagline,
            world_id, series_type, genre, status,
            featured_characters, visual_style
        ) VALUES (
            :id, :title, :slug, :description, :tagline,
            :world_id, :series_type, :genre, 'draft',
            :featured_characters, CAST(:visual_style AS jsonb)
        )
    """, {
        "id": series_id,
        "title": series["title"],
        "slug": series["slug"],
        "description": series["description"],
        "tagline": series["tagline"],
        "world_id": world_id,
        "series_type": series["series_type"],
        "genre": series["genre"],
        "featured_characters": [character_id],
        "visual_style": json.dumps(series["visual_style"]),
    })

    print(f"  - {series['title']} ({series['series_type']}): created")
    return series_id


async def create_episodes(db: Database, series_id: str, character_id: str) -> list:
    """Create episode templates. Returns list of episode IDs."""
    print("\n[4/4] Creating episodes...")

    episode_ids = []

    for ep in EPISODES:
        # Check if exists
        existing = await db.fetch_one(
            """SELECT id FROM episode_templates
               WHERE series_id = :series_id AND episode_number = :ep_num""",
            {"series_id": series_id, "ep_num": ep["episode_number"]}
        )
        if existing:
            episode_ids.append(existing["id"])
            print(f"  - Ep {ep['episode_number']}: {ep['title']} - exists (skipped)")
            continue

        ep_id = str(uuid.uuid4())
        ep_slug = ep["title"].lower().replace(" ", "-").replace("'", "")

        await db.execute("""
            INSERT INTO episode_templates (
                id, series_id, character_id,
                episode_number, title, slug,
                situation, opening_line, episode_frame,
                episode_type, status,
                dramatic_question, resolution_types,
                scene_objective, scene_obstacle, scene_tactic,
                turn_budget, starter_prompts
            ) VALUES (
                :id, :series_id, :character_id,
                :episode_number, :title, :slug,
                :situation, :opening_line, :episode_frame,
                :episode_type, 'draft',
                :dramatic_question, :resolution_types,
                :scene_objective, :scene_obstacle, :scene_tactic,
                :turn_budget, :starter_prompts
            )
        """, {
            "id": ep_id,
            "series_id": series_id,
            "character_id": character_id,
            "episode_number": ep["episode_number"],
            "title": ep["title"],
            "slug": ep_slug,
            "situation": ep["situation"],
            "opening_line": ep["opening_line"],
            "episode_frame": ep.get("episode_frame", ""),
            "episode_type": ep.get("episode_type", "core"),
            "dramatic_question": ep.get("dramatic_question"),
            "resolution_types": ep.get("resolution_types", ["positive", "neutral", "negative"]),
            "scene_objective": ep.get("scene_objective"),
            "scene_obstacle": ep.get("scene_obstacle"),
            "scene_tactic": ep.get("scene_tactic"),
            "turn_budget": ep.get("turn_budget", 10),
            "starter_prompts": ep.get("starter_prompts", []),
        })

        episode_ids.append(ep_id)
        print(f"  - Ep {ep['episode_number']}: {ep['title']}: created")

    # Update series episode order
    await db.execute("""
        UPDATE series SET episode_order = :episode_ids, total_episodes = :count
        WHERE id = :series_id
    """, {
        "series_id": series_id,
        "episode_ids": episode_ids,
        "count": len(episode_ids),
    })

    return episode_ids


async def create_props(db: Database, series_id: str, episode_ids: list) -> int:
    """Create props for episodes (ADR-005).

    Returns count of props created.
    """
    print("\n[5/5] Creating props (ADR-005 - SEMANTIC reveals)...")

    # Get episode_number -> episode_id mapping
    episode_map = {}
    episode_slug_map = {}
    for ep_id in episode_ids:
        row = await db.fetch_one(
            "SELECT episode_number, slug FROM episode_templates WHERE id = :id",
            {"id": ep_id}
        )
        if row:
            episode_map[row["episode_number"]] = ep_id
            episode_slug_map[row["slug"]] = ep_id

    props_created = 0
    semantic_count = 0

    for ep_num, props in EPISODE_PROPS.items():
        ep_id = episode_map.get(ep_num)
        if not ep_id:
            print(f"  - Episode {ep_num}: not found, skipping props")
            continue

        for prop in props:
            # Check if exists
            existing = await db.fetch_one(
                """SELECT id FROM props
                   WHERE episode_template_id = :ep_id AND slug = :slug""",
                {"ep_id": ep_id, "slug": prop["slug"]}
            )
            if existing:
                print(f"  - Ep {ep_num}: {prop['name']} - exists (skipped)")
                continue

            prop_id = str(uuid.uuid4())

            # Resolve gates_episode_slug to gates_episode_id
            gates_episode_id = None
            gates_slug = prop.get("gates_episode_slug")
            if gates_slug and gates_slug in episode_slug_map:
                gates_episode_id = episode_slug_map[gates_slug]

            await db.execute("""
                INSERT INTO props (
                    id, episode_template_id,
                    name, slug, prop_type, description,
                    content, content_format,
                    reveal_mode, reveal_turn_hint,
                    is_key_evidence, badge_label, evidence_tags,
                    display_order, image_prompt,
                    is_progression_gate, gates_episode_id
                ) VALUES (
                    :id, :episode_template_id,
                    :name, :slug, :prop_type, :description,
                    :content, :content_format,
                    :reveal_mode, :reveal_turn_hint,
                    :is_key_evidence, :badge_label, CAST(:evidence_tags AS jsonb),
                    :display_order, :image_prompt,
                    :is_progression_gate, :gates_episode_id
                )
            """, {
                "id": prop_id,
                "episode_template_id": ep_id,
                "name": prop["name"],
                "slug": prop["slug"],
                "prop_type": prop["prop_type"],
                "description": prop["description"],
                "content": prop.get("content"),
                "content_format": prop.get("content_format"),
                "reveal_mode": prop.get("reveal_mode", "character_initiated"),
                "reveal_turn_hint": prop.get("reveal_turn_hint"),
                "is_key_evidence": prop.get("is_key_evidence", False),
                "badge_label": prop.get("badge_label"),
                "evidence_tags": json.dumps(prop.get("evidence_tags", [])),
                "display_order": prop.get("display_order", 0),
                "image_prompt": prop.get("image_prompt"),
                "is_progression_gate": prop.get("is_progression_gate", False),
                "gates_episode_id": gates_episode_id,
            })

            props_created += 1
            markers = []
            if prop.get("reveal_mode") == "character_initiated":
                markers.append("SEMANTIC")
                semantic_count += 1
            if prop.get("badge_label"):
                markers.append(prop.get("badge_label"))
            if prop.get("is_progression_gate"):
                markers.append("GATE")
            marker_str = f" [{','.join(markers)}]" if markers else ""
            print(f"  - Ep {ep_num}: {prop['name']} ({prop['prop_type']}){marker_str}: created")

    print(f"\n  ADR-005 v2: {semantic_count} props use SEMANTIC (character_initiated) reveal")

    return props_created


async def scaffold_all(dry_run: bool = False):
    """Main scaffold function."""
    print("=" * 60)
    print("LOCKED IN - ROM-COM FORCED PROXIMITY SCAFFOLDING")
    print("=" * 60)
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"World: real-life")
    print(f"Genre: romance (forced proximity)")
    print(f"Episodes: {len(EPISODES)}")

    # Count props
    total_props = sum(len(props) for props in EPISODE_PROPS.values())

    # Count semantic reveals
    semantic_props = sum(
        1 for props in EPISODE_PROPS.values()
        for p in props if p.get("reveal_mode") == "character_initiated"
    )

    if dry_run:
        print("\n[DRY RUN] Would create:")
        print(f"  - 1 character (Riley)")
        print(f"  - 1 avatar kit")
        print(f"  - 1 series (Locked In)")
        print(f"  - {len(EPISODES)} episode templates")
        print(f"  - {total_props} props (ADR-005)")
        print(f"  - {semantic_props} use SEMANTIC reveal (character_initiated)")
        print("\nEpisode Arc:")
        for ep in EPISODES:
            print(f"  - Ep {ep['episode_number']}: {ep['title']} ({ep['episode_type']})")
            print(f"    Dramatic Question: {ep['dramatic_question']}")
            props = EPISODE_PROPS.get(ep['episode_number'], [])
            if props:
                for p in props:
                    badge = f" [{p.get('badge_label')}]" if p.get('badge_label') else ""
                    print(f"    - {p['name']}{badge}")
        return

    db = Database(DATABASE_URL)
    await db.connect()

    try:
        # Get world ID
        world_id = await get_world_id(db, "real-life")
        print(f"\nUsing world: real-life ({world_id})")

        # Create content
        character_id = await create_character(db, world_id)
        kit_id = await create_avatar_kit(db, character_id, world_id)
        series_id = await create_series(db, world_id, character_id)
        episode_ids = await create_episodes(db, series_id, character_id)
        props_count = await create_props(db, series_id, episode_ids)

        # Summary
        print("\n" + "=" * 60)
        print("SCAFFOLDING COMPLETE")
        print("=" * 60)
        print(f"Character ID: {character_id}")
        print(f"Avatar Kit ID: {kit_id}")
        print(f"Series ID: {series_id}")
        print(f"Episodes: {len(episode_ids)}")
        print(f"Props: {props_count} (ADR-005 - SEMANTIC reveals)")

        print("\n>>> NEXT STEPS:")
        print("1. Run: python -m app.scripts.generate_locked_in_images")
        print("2. Activate: UPDATE series SET status = 'active' WHERE slug = 'locked-in'")

    finally:
        await db.disconnect()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Scaffold Locked In series")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be created")
    args = parser.parse_args()

    asyncio.run(scaffold_all(dry_run=args.dry_run))
