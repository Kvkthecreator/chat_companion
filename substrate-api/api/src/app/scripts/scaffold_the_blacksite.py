"""Scaffold The Blacksite Series.

CANON COMPLIANT: docs/CONTENT_ARCHITECTURE_CANON.md
GENRE: survival_thriller (Escape Room Archetype - Thriller Path)
WORLD: real-life

Concept:
- User wakes up in a government black site with no memory
- Character is Alex, a mysterious ally in adjacent cell
- Neither knows why they're there, but they need to escape
- Each episode = escaping one containment zone
- Trust builds under pressure, but is Alex who they say they are?

This series stress-tests:
- ADR-005: Props with `automatic` reveal mode (STRUCTURAL path)
- Escape room progression mechanics
- High-stakes trust dynamics

Usage:
    python -m app.scripts.scaffold_the_blacksite
    python -m app.scripts.scaffold_the_blacksite --dry-run
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
# THRILLER STYLE CONSTANTS
# =============================================================================

THRILLER_STYLE = "cinematic thriller photography, harsh fluorescent lighting, clinical sterile atmosphere, desaturated cold tones, institutional setting"
THRILLER_QUALITY = "masterpiece, best quality, highly detailed, atmospheric tension, high contrast"
THRILLER_NEGATIVE = "anime, cartoon, warm colors, cozy, comfortable, low quality, blurry, text, watermark"

# =============================================================================
# PROPS DEFINITIONS (ADR-005 - STRUCTURAL REVEALS)
# =============================================================================
# The Blacksite uses predominantly `automatic` reveal mode.
# Props are plot-critical and reveal at authored turns.

EPISODE_PROPS = {
    # Episode 0: Awakening
    # Goal: Establish captivity, first contact with Alex
    0: [
        {
            "name": "Subject Tag",
            "slug": "subject-tag",
            "prop_type": "object",
            "description": "A hospital-style wristband with a barcode and number: SUBJECT-7749. It's tight. You don't remember putting it on.",
            "content": "SUBJECT-7749 | CLEARANCE: NONE | STATUS: ACTIVE | HANDLER: [REDACTED]",
            "content_format": "printed",
            "reveal_mode": "automatic",  # Turn 0 - player sees this immediately
            "reveal_turn_hint": 0,
            "is_key_evidence": True,
            "badge_label": "Identity",
            "evidence_tags": ["identity", "captivity", "numbered"],
            "display_order": 0,
            "image_prompt": "hospital wristband with barcode, white plastic, printed text partially visible, clinical lighting, on bare wrist, institutional aesthetic, no readable text",
            "is_progression_gate": False,
        },
        {
            "name": "The Vent Message",
            "slug": "vent-message",
            "prop_type": "document",
            "description": "Scratched into the metal inside the air vent. Someone was here before you.",
            "content": "THEY WATCH EVERYTHING. TRUST THE ONE WHO DOESN'T ASK YOUR NAME.",
            "content_format": "scratched",
            "reveal_mode": "automatic",
            "reveal_turn_hint": 3,
            "is_key_evidence": True,
            "badge_label": "Warning",
            "evidence_tags": ["warning", "previous_subject", "trust"],
            "display_order": 1,
            "image_prompt": "scratched message inside metal air vent, harsh lighting from below, desperate handwriting etched into metal, dust particles, claustrophobic, thriller atmosphere",
            "is_progression_gate": True,
            "gates_episode_slug": "the-corridor",
        },
    ],
    # Episode 1: The Corridor
    # Goal: First movement, Alex proves useful, discover facility purpose
    1: [
        {
            "name": "Keycard (Level 1)",
            "slug": "keycard-level-1",
            "prop_type": "object",
            "description": "A magnetic keycard Alex had hidden. Level 1 access only. It opens some doors - but not the ones that matter.",
            "content": "ACCESS LEVEL: 1 | ZONES: CONTAINMENT A-C | EXPIRES: [ERROR]",
            "content_format": "printed",
            "reveal_mode": "automatic",
            "reveal_turn_hint": 2,
            "is_key_evidence": True,
            "badge_label": "Access Key",
            "evidence_tags": ["access", "progression", "limited"],
            "display_order": 0,
            "image_prompt": "white magnetic keycard with level 1 marking, red stripe, held in hand under fluorescent light, industrial corridor background blurred, thriller aesthetic",
            "is_progression_gate": True,
            "gates_episode_slug": "the-lab",
        },
        {
            "name": "Facility Map (Partial)",
            "slug": "facility-map-partial",
            "prop_type": "document",
            "description": "Torn from a wall mount. Shows three floors, but the fourth level is scratched out. What's on Level 4?",
            "content": "LEVEL 1: Containment | LEVEL 2: Processing | LEVEL 3: Administration | LEVEL 4: [SCRATCHED OUT]",
            "content_format": "printed",
            "reveal_mode": "character_initiated",
            "reveal_turn_hint": 5,
            "is_key_evidence": True,
            "badge_label": "Intel",
            "evidence_tags": ["map", "layout", "level_4_mystery"],
            "display_order": 1,
            "image_prompt": "torn facility map on concrete floor, emergency lighting, partial floor plan visible, scratch marks obscuring one section, industrial aesthetic",
            "is_progression_gate": False,
        },
    ],
    # Episode 2: The Lab
    # Goal: Discover what they were doing here, stakes become personal
    2: [
        {
            "name": "Subject File (Yours)",
            "slug": "subject-file-yours",
            "prop_type": "document",
            "description": "A manila folder with your photo. You don't remember the photo being taken. The contents explain why you're here.",
            "content": "SUBJECT-7749 | RECRUITMENT: INVOLUNTARY | SUITABILITY: HIGH | NOTES: Subject demonstrated unusual pattern recognition in Phase 1 testing. Recommended for Phase 3 escalation. Memory suppression: COMPLETE.",
            "content_format": "typed",
            "reveal_mode": "automatic",
            "reveal_turn_hint": 4,
            "is_key_evidence": True,
            "badge_label": "Your File",
            "evidence_tags": ["identity", "memory", "purpose", "phase_3"],
            "display_order": 0,
            "image_prompt": "manila folder open on metal table, photo clipped inside, typed documents visible, laboratory setting, harsh overhead light, clinical thriller atmosphere",
            "is_progression_gate": True,
            "gates_episode_slug": "the-exit",
        },
        {
            "name": "Alex's ID Badge",
            "slug": "alex-id-badge",
            "prop_type": "object",
            "description": "It fell from Alex's pocket during the struggle. The photo matches, but the name... the name doesn't.",
            "content": "DR. ELENA VANCE | DEPARTMENT: COGNITIVE RESEARCH | CLEARANCE: LEVEL 4 | STATUS: ACTIVE",
            "content_format": "printed",
            "reveal_mode": "automatic",
            "reveal_turn_hint": 8,
            "is_key_evidence": True,
            "badge_label": "Revelation",
            "evidence_tags": ["alex", "identity", "betrayal_or_ally", "level_4"],
            "display_order": 1,
            "image_prompt": "ID badge on floor, photo of woman visible, level 4 clearance marking, dropped in struggle, blood spatter nearby, harsh fluorescent lighting, thriller reveal",
            "is_progression_gate": False,
        },
    ],
    # Episode 3: The Exit
    # Goal: Final escape or final revelation - Alex's true nature
    3: [
        {
            "name": "The Override Code",
            "slug": "override-code",
            "prop_type": "digital",
            "description": "Alex knows the exit code. They've known it all along. The question is: why didn't they leave?",
            "content": "OVERRIDE SEQUENCE: 7-7-4-9-VANCE-ALPHA | AUTHORIZATION: DR. ELENA VANCE | NOTE: One use only. All doors. Twenty seconds.",
            "content_format": "typed",
            "reveal_mode": "automatic",
            "reveal_turn_hint": 2,
            "is_key_evidence": True,
            "badge_label": "Exit Key",
            "evidence_tags": ["escape", "code", "alex_choice", "twenty_seconds"],
            "display_order": 0,
            "image_prompt": "terminal screen showing override code input, green text on black, countdown timer visible, emergency lighting, finger hovering over enter key, tension",
            "is_progression_gate": False,  # Final episode
        },
        {
            "name": "The Surveillance Recording",
            "slug": "surveillance-recording",
            "prop_type": "recording",
            "description": "Security footage from two weeks ago. It shows Alex - or whoever they really are - walking in. Not being brought in. Walking in.",
            "content": "TIMESTAMP: 14 DAYS AGO | SUBJECT: DR. VANCE ENTERING VOLUNTARILY | COMPANION: SUBJECT-7749 (UNCONSCIOUS, TRANSPORTED) | NOTE: Dr. Vance initiated containment protocol for both subjects. Self-included.",
            "content_format": "video_transcript",
            "reveal_mode": "character_initiated",
            "reveal_turn_hint": 6,
            "is_key_evidence": True,
            "badge_label": "The Truth",
            "evidence_tags": ["alex", "sacrifice", "voluntary", "protection"],
            "display_order": 1,
            "image_prompt": "security monitor showing grainy footage, two figures visible, one walking one carried, timestamp visible, multiple monitors in dark room, revelation moment",
            "is_progression_gate": False,
        },
    ],
}

# =============================================================================
# CHARACTER DEFINITION
# =============================================================================

ALEX_CHARACTER = {
    "name": "Alex",
    "slug": "alex-blacksite",
    "archetype": "mysterious_ally",
    "world_slug": "real-life",
    "personality": {
        "traits": [
            "calm under pressure - too calm, maybe",
            "knows too much about this place for a prisoner",
            "protective, but of what exactly?",
            "gives information in pieces, never the whole picture",
            "humor in dark moments - coping or deflecting?"
        ],
        "core_motivation": "Get you out. Whatever it takes. Even if it means you never trust them again once you know the truth.",
    },
    "boundaries": {
        "flirting_level": "reserved",  # Trust before attraction
        "nsfw_allowed": False,
    },
    "tone_style": {
        "formality": "casual_urgent",
        "uses_ellipsis": True,
        "emoji_usage": "none",
        "capitalization": "normal",
        "pause_indicators": True,
    },
    "speech_patterns": {
        "greetings": ["Hey—you awake?", "Listen to me carefully.", "We don't have much time."],
        "thinking_words": ["Wait—", "That's not right—", "I need you to trust me on this."],
        "deflections": ["Later. I'll explain later.", "That's not important right now.", "Focus."],
    },
    "backstory": """They call themselves Alex. They were in the cell next to yours when you woke up. Same hospital gown, same wristband, same confusion—or so they claim.

But they know things. Which cameras have blind spots. Which doors are on timers. Where the guards change shifts. They say they've been here 'long enough to learn.' You're not sure you believe that.

There's something in how they move. Too confident for a captive. Too aware of the exits. They could have left by now—you're almost sure of it. So why are they still here? Why are they helping you?

The message in the vent said to trust the one who doesn't ask your name. Alex hasn't asked.

Maybe that should comfort you. Maybe it should terrify you.""",
    "current_stressor": "Time is running out. Whatever window Alex has been waiting for is closing. And they're scared - not of getting caught, but of what you'll think when you find out the truth.",

    # Avatar prompts - thriller aesthetic
    "appearance_prompt": "androgynous person late 20s, intense focused eyes, messy short dark hair, wearing hospital gown slightly torn, alert vigilant expression, athletic build, minor cuts on face, cinematic lighting, thriller aesthetic",
    "style_prompt": "cinematic portrait photography, harsh industrial lighting, cold color grade, thriller aesthetic, tension visible, shallow depth of field, single subject, clinical background",
    "negative_prompt": THRILLER_NEGATIVE,
}

# =============================================================================
# SERIES DEFINITION
# =============================================================================

THE_BLACKSITE_SERIES = {
    "title": "The Blacksite",
    "slug": "the-blacksite",
    "world_slug": "real-life",
    "series_type": "serial",
    "genre": "survival_thriller",
    "description": "You wake up in a government black site with no memory. The person in the next cell says they can get you out. But something doesn't add up about your mysterious ally.",
    "tagline": "Trust is a survival skill. So is knowing when not to.",
    "visual_style": {
        "rendering": THRILLER_STYLE,
        "quality": THRILLER_QUALITY,
        "negative": THRILLER_NEGATIVE,
        "palette": "cold blues and grays, harsh fluorescent whites, clinical sterility, shadows in corners",
    },
}

# =============================================================================
# EPISODE DEFINITIONS
# =============================================================================

EPISODES = [
    # Episode 0: Awakening
    {
        "episode_number": 0,
        "title": "Awakening",
        "episode_type": "entry",
        "situation": "A cell. White walls, fluorescent lights, no windows. You're on a metal cot in a hospital gown. Your head is pounding. There's a wristband on your wrist you don't remember putting on. And someone is whispering through the vent in the wall.",
        "episode_frame": "sterile white cell, flickering fluorescent light, metal cot, air vent near floor where whispers emerge, hospital aesthetic, no windows, something deeply wrong",
        "opening_line": "*The voice comes through the vent, low and urgent.* Hey—you awake? Finally. *pause* Don't talk. They're listening through the intercom, but not the vents. Nod if you can understand me. *you see movement in the shadows of the vent grate* My name's Alex. I'm in the cell next to yours. And we need to get out of here before they come back for Phase 3.",
        "dramatic_question": "Why are you here, and can you trust the voice in the vent?",
        "scene_objective": "Convince you to cooperate and begin planning escape",
        "scene_obstacle": "You have no memory and every reason to distrust",
        "scene_tactic": "Offer urgent help while revealing just enough to hook interest",
        "beat_guidance": {
            "establishment": "Disorientation gives way to survival instinct. Alex seems to know what's happening.",
            "complication": "Alex knows too much. How long have they really been here?",
            "escalation": "Sounds in the corridor. Footsteps. They're coming to check on you.",
            "pivot_opportunity": "You find the message scratched in the vent. Someone was here before. What happened to them?",
        },
        "resolution_types": ["trust_forming", "suspicious_alliance", "desperate_cooperation"],
        "starter_prompts": [
            "Who are you? How do you know my cell has vents?",
            "Phase 3? What the hell is Phase 3?",
            "Why should I trust you?",
        ],
        "turn_budget": 12,
        "background_config": {
            "location": "sterile white cell, fluorescent lights, metal cot with thin mattress, air vent near floor, no windows, institutional hospital aesthetic, surveillance camera in corner",
            "time": "impossible to tell, artificial light only, timeless captivity",
            "mood": "disorientation, survival instinct, something watching",
            "rendering": THRILLER_STYLE,
            "quality": THRILLER_QUALITY,
        },
    },
    # Episode 1: The Corridor
    {
        "episode_number": 1,
        "title": "The Corridor",
        "episode_type": "core",
        "situation": "You're out of your cell. The corridor stretches in both directions - identical doors, flickering lights, no signs. Alex is beside you now, flesh and blood instead of a whisper through a vent. They move like they know exactly where they're going.",
        "episode_frame": "long institutional corridor, identical doors on both sides, flickering fluorescent lights, Alex leading with confidence, emergency lighting casting red shadows, somewhere distant an alarm is silent but imminent",
        "opening_line": "*Alex pulls you through the door, checks both directions.* Left. Always left when you don't know. *starts moving* Stay behind me, step where I step. The floor sensors are pressure-sensitive in some sections. *glances back* You're doing good. Better than most. *pause* Most don't make it out of the cell.",
        "dramatic_question": "How does Alex know so much about this place?",
        "scene_objective": "Navigate to the next zone while earning your trust through competence",
        "scene_obstacle": "Security patrols, locked doors, and your growing suspicions",
        "scene_tactic": "Prove usefulness through knowledge, but deflect questions about how they know",
        "beat_guidance": {
            "establishment": "Alex's expertise is undeniable. They know every corner.",
            "complication": "A patrol almost catches you. Alex's reaction is too practiced.",
            "escalation": "You find the map. Level 4 is scratched out. Alex doesn't want to talk about it.",
            "pivot_opportunity": "A door requires Level 2 access. Alex produces a keycard. Where did they get it?",
        },
        "resolution_types": ["deeper_trust", "growing_doubt", "uneasy_alliance"],
        "starter_prompts": [
            "How do you know about the floor sensors?",
            "What's on Level 4?",
            "Where did you get that keycard?",
        ],
        "turn_budget": 12,
        "background_config": {
            "location": "institutional corridor, flickering lights, identical doors, emergency signage, security camera with blinking red light, tile floor, exposed pipes on ceiling",
            "time": "artificial light only, sense of late night shift change",
            "mood": "tension, pursuit, something following",
            "rendering": THRILLER_STYLE,
            "quality": THRILLER_QUALITY,
        },
    },
    # Episode 2: The Lab
    {
        "episode_number": 2,
        "title": "The Lab",
        "episode_type": "core",
        "situation": "The laboratory. Banks of monitors, medical equipment, file cabinets. This is where they were doing... whatever they were doing. Alex is searching for something specific. You find a folder with your name on it.",
        "episode_frame": "clinical laboratory, banks of monitors showing brain scans, medical equipment, file cabinets, harsh overhead lighting, your photo visible in an open folder, Alex frantically searching through files",
        "opening_line": "*Alex is already at the file cabinets, pulling folders.* Don't look at the screens. The data loops—it'll mess with you. *finds what they're looking for, pauses* I need to tell you something. About why you're here. About why I'm here. *looks at you* But first— *nods toward a folder on the table* —you should see your file. You need to know what they were planning before I explain the rest.",
        "dramatic_question": "What were they doing here, and what was Alex's role?",
        "scene_objective": "Reveal the truth about the facility - and begin revealing the truth about Alex",
        "scene_obstacle": "Some truths might make you turn against Alex",
        "scene_tactic": "Control the flow of revelation - your file first, then the harder truth",
        "beat_guidance": {
            "establishment": "Your file reveals you were chosen. Memory suppression was intentional.",
            "complication": "Alex's reaction to your file is wrong. They already knew what it said.",
            "escalation": "A badge falls from Alex's pocket. Dr. Elena Vance. Level 4 clearance.",
            "pivot_opportunity": "Alex tries to explain. They had reasons. But do those reasons matter now?",
        },
        "resolution_types": ["trust_shattered", "complicated_understanding", "betrayal_forgiven"],
        "starter_prompts": [
            "You knew. You knew what was in my file.",
            "Dr. Vance? That's not even your real name.",
            "Why are you really here?",
        ],
        "turn_budget": 14,
        "background_config": {
            "location": "research laboratory, computer monitors showing brain scans, medical equipment, file cabinets with patient folders, examination table, harsh clinical lighting",
            "time": "artificial light, timeless facility, crisis moment",
            "mood": "revelation, betrayal, everything recontextualized",
            "rendering": THRILLER_STYLE,
            "quality": THRILLER_QUALITY,
        },
    },
    # Episode 3: The Exit
    {
        "episode_number": 3,
        "title": "The Exit",
        "episode_type": "special",
        "situation": "The exit is ahead. Alex - Elena - whoever they are, they know the override code. They've always known it. Twenty seconds, all doors, one chance. But the surveillance recording you found changes everything about what you thought this was.",
        "episode_frame": "exit door with electronic lock, countdown timer ready, surveillance room visible through glass, recording frozen on screen showing Alex walking in voluntarily two weeks ago, decision point",
        "opening_line": "*Alex—Elena—stands at the terminal, fingers hovering.* I can get us out. Right now. Twenty seconds, every door opens, we run and don't stop. *turns to face you* But before I enter this code, you deserve to know. I wasn't captured. I walked in. I brought you here. *their voice breaks* Not to hurt you. To save you from something worse. The recording—you saw it. I need you to understand before we do this. Because once we're out... you might never want to see me again.",
        "dramatic_question": "Was everything a lie, or was it the only way to save you?",
        "scene_objective": "Tell the complete truth and accept whatever you decide",
        "scene_obstacle": "The truth might mean escaping alone",
        "scene_tactic": "Total honesty. No more deflection. Whatever you decide, decide knowing everything.",
        "beat_guidance": {
            "establishment": "The recording proves it. Alex chose this. But why?",
            "complication": "The 'something worse' - what Alex was protecting you from. The real threat outside.",
            "escalation": "Alarms trigger. Time's up. Enter the code or face what's coming.",
            "pivot_opportunity": "Together or apart. Trust or abandonment. Twenty seconds to decide.",
        },
        "resolution_types": ["escape_together", "escape_alone", "face_it_together"],
        "starter_prompts": [
            "What was the 'something worse'?",
            "Why didn't you just tell me from the start?",
            "Enter the code. We'll figure out the rest outside.",
        ],
        "turn_budget": 15,
        "background_config": {
            "location": "facility exit, heavy door with electronic lock, terminal with keypad, countdown display, alarm lights spinning, surveillance room through reinforced glass",
            "time": "crisis moment, alarms active, countdown",
            "mood": "decision, trust or betrayal, twenty seconds to freedom",
            "rendering": THRILLER_STYLE,
            "quality": THRILLER_QUALITY,
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
    """Create Alex character. Returns character ID."""
    print("\n[1/4] Creating Alex character...")

    char = ALEX_CHARACTER

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
    """Create avatar kit for Alex. Returns kit ID."""
    print("\n[2/4] Creating avatar kit...")

    char = ALEX_CHARACTER

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
        "description": f"Default avatar kit for {char['name']} - thriller style",
        "appearance_prompt": char["appearance_prompt"],
        "style_prompt": char["style_prompt"],
        "negative_prompt": char["negative_prompt"],
    })

    # Link to character
    await db.execute("""
        UPDATE characters SET active_avatar_kit_id = :kit_id WHERE id = :char_id
    """, {"kit_id": kit_id, "char_id": character_id})

    print(f"  - {char['name']}: avatar kit created (thriller style)")
    return kit_id


async def create_series(db: Database, world_id: str, character_id: str) -> str:
    """Create The Blacksite series. Returns series ID."""
    print("\n[3/4] Creating series...")

    series = THE_BLACKSITE_SERIES

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
            "turn_budget": ep.get("turn_budget", 12),
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
    print("\n[5/5] Creating props (ADR-005 - STRUCTURAL reveals)...")

    # Get episode_number -> episode_id mapping
    episode_map = {}
    episode_slug_map = {}  # slug -> id for gating resolution
    for ep_id in episode_ids:
        row = await db.fetch_one(
            "SELECT episode_number, slug FROM episode_templates WHERE id = :id",
            {"id": ep_id}
        )
        if row:
            episode_map[row["episode_number"]] = ep_id
            episode_slug_map[row["slug"]] = ep_id

    props_created = 0
    automatic_count = 0

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
            if prop.get("reveal_mode") == "automatic":
                markers.append(f"AUTO@{prop.get('reveal_turn_hint', '?')}")
                automatic_count += 1
            if prop.get("is_key_evidence"):
                markers.append("KEY")
            if prop.get("is_progression_gate"):
                markers.append("GATE")
            marker_str = f" [{','.join(markers)}]" if markers else ""
            print(f"  - Ep {ep_num}: {prop['name']} ({prop['prop_type']}){marker_str}: created")

    print(f"\n  ADR-005 v2: {automatic_count} props use STRUCTURAL (automatic) reveal")

    return props_created


async def scaffold_all(dry_run: bool = False):
    """Main scaffold function."""
    print("=" * 60)
    print("THE BLACKSITE - ESCAPE ROOM THRILLER SCAFFOLDING")
    print("=" * 60)
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"World: real-life")
    print(f"Genre: survival_thriller")
    print(f"Episodes: {len(EPISODES)}")

    # Count props
    total_props = sum(len(props) for props in EPISODE_PROPS.values())

    # Count automatic reveals (STRUCTURAL path)
    automatic_props = sum(
        1 for props in EPISODE_PROPS.values()
        for p in props if p.get("reveal_mode") == "automatic"
    )

    if dry_run:
        print("\n[DRY RUN] Would create:")
        print(f"  - 1 character (Alex)")
        print(f"  - 1 avatar kit")
        print(f"  - 1 series (The Blacksite)")
        print(f"  - {len(EPISODES)} episode templates")
        print(f"  - {total_props} props (ADR-005)")
        print(f"  - {automatic_props} use STRUCTURAL reveal (automatic mode)")
        print("\nEpisode Arc:")
        for ep in EPISODES:
            print(f"  - Ep {ep['episode_number']}: {ep['title']} ({ep['episode_type']})")
            print(f"    Dramatic Question: {ep['dramatic_question']}")
            props = EPISODE_PROPS.get(ep['episode_number'], [])
            if props:
                for p in props:
                    mode = "AUTO" if p.get('reveal_mode') == 'automatic' else "SEMANTIC"
                    turn = f"@{p.get('reveal_turn_hint', '?')}" if mode == "AUTO" else ""
                    print(f"    - {p['name']} [{mode}{turn}]")
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
        print(f"Props: {props_count} (ADR-005 - STRUCTURAL reveals)")

        print("\n>>> NEXT STEPS:")
        print("1. Run: python -m app.scripts.generate_the_blacksite_images")
        print("2. Activate: UPDATE series SET status = 'active' WHERE slug = 'the-blacksite'")

    finally:
        await db.disconnect()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Scaffold The Blacksite series")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be created")
    args = parser.parse_args()

    asyncio.run(scaffold_all(dry_run=args.dry_run))
