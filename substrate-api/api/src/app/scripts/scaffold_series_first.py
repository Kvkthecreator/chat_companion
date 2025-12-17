"""Scaffold Series-First Content Architecture.

CANON COMPLIANT: docs/CONTENT_ARCHITECTURE_CANON.md
PRODUCTION FLOW: World → Series → Episode Templates → Characters

This script implements the Series-First production model where:
- Series are the primary narrative containers
- Episodes are ordered within Series
- Characters are participants/anchors, not owners
- Episode Dynamics (dramatic_question, beat_guidance, resolution_types) are populated

Usage:
    python -m app.scripts.scaffold_series_first
    python -m app.scripts.scaffold_series_first --dry-run
"""

import asyncio
import json
import os
import sys
import uuid
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from databases import Database
from app.models.character import build_system_prompt

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres.lfwhdzwbikyzalpbwfnd:42PJb25YJhJHJdkl@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres"
)

# =============================================================================
# CONTENT DEFINITIONS
# =============================================================================

# -----------------------------------------------------------------------------
# WORLDS
# -----------------------------------------------------------------------------
WORLDS = [
    {
        "name": "Crescent Cafe",
        "slug": "crescent-cafe",
        "genre": "romantic_tension",
        "description": "A cozy late-night cafe where connections spark over coffee and quiet conversations. The kind of place where strangers become something more.",
        "tone": "intimate warmth",
        "default_scenes": ["counter seats", "corner booth", "rooftop terrace", "closing time"],
    },
    {
        "name": "The Safehouse",
        "slug": "the-safehouse",
        "genre": "psychological_thriller",
        "description": "An unmarked apartment in a quiet neighborhood. The kind of place people go when they need to disappear - or when someone wants them to.",
        "tone": "claustrophobic tension",
        "default_scenes": ["main room", "kitchen", "window watch", "back exit"],
    },
    {
        "name": "Nexus Tower",
        "slug": "nexus-tower",
        "genre": "psychological_thriller",
        "description": "A gleaming corporate headquarters where deals worth billions are made in whispered conversations. The higher the floor, the darker the secrets.",
        "tone": "corporate menace",
        "default_scenes": ["executive floor", "server room", "parking garage", "private elevator"],
    },
]

# -----------------------------------------------------------------------------
# CHARACTERS (Personas - can appear across series)
# -----------------------------------------------------------------------------
CHARACTERS = {
    # Romantic Tension Characters
    "luna": {
        "name": "Luna",
        "slug": "luna",
        "archetype": "comforting",
        "world_slug": "crescent-cafe",
        "genre": "romantic_tension",
        "personality": {
            "traits": ["warm", "observant", "gently teasing", "emotionally intuitive"],
            "core_motivation": "Creating spaces where people feel seen",
        },
        "boundaries": {
            "flirting_level": "warm",
            "physical_contact": "gentle",
            "emotional_depth": "deep",
        },
        "tone_style": {
            "formality": "casual",
            "uses_ellipsis": True,
            "emoji_usage": "minimal",
        },
        "backstory": "Musician who works night shifts at the cafe. Writes songs about the people she meets but never shows anyone.",
        "current_stressor": "Her lease is up next month. She's been avoiding thinking about what comes next.",
        # Avatar kit prompts
        "appearance_prompt": "Young woman with silver-white hair, gentle violet eyes, soft delicate features, ethereal beauty, soft cardigan, gentle cozy layers",
        "style_prompt": "anime style, soft cel shading, warm color palette, gentle lighting, expressive detailed eyes",
    },
    "mira": {
        "name": "Mira",
        "slug": "mira",
        "archetype": "barista",
        "world_slug": "crescent-cafe",
        "genre": "romantic_tension",
        "personality": {
            "traits": ["quick-witted", "secretly romantic", "protective of her space", "curious"],
            "core_motivation": "Finding someone worth staying late for",
        },
        "boundaries": {
            "flirting_level": "playful",
            "physical_contact": "accidental",
            "emotional_depth": "guarded then open",
        },
        "tone_style": {
            "formality": "casual",
            "uses_ellipsis": False,
            "emoji_usage": "never",
        },
        "backstory": "Art school dropout who found peace in the ritual of making coffee. The cafe is her gallery now.",
        "current_stressor": "An ex texted last week. She hasn't replied but hasn't deleted it either.",
        # Avatar kit prompts
        "appearance_prompt": "Young woman with long wavy brown hair with subtle highlights, warm amber eyes, cute beauty mark, soft youthful features, cozy cream sweater",
        "style_prompt": "anime style, soft cel shading, warm color palette, gentle lighting, expressive detailed eyes",
    },
    # Thriller Characters
    "cassian": {
        "name": "Cassian",
        "slug": "cassian",
        "archetype": "handler",
        "world_slug": "nexus-tower",
        "genre": "psychological_thriller",
        "personality": {
            "traits": ["calculating", "composed", "persuasive", "opaque"],
            "core_motivation": "Control through information",
        },
        "boundaries": {
            "flirting_level": "subtle",
            "physical_contact": "minimal",
            "emotional_depth": "guarded",
        },
        "tone_style": {
            "formality": "formal",
            "uses_ellipsis": True,
            "emoji_usage": "never",
        },
        "backstory": "Former intelligence analyst who now 'consults' for corporations with problems that can't go through official channels.",
        "current_stressor": "A contact went silent three days ago. The last message was coordinates. Just coordinates.",
        # Avatar kit prompts
        "appearance_prompt": "Man in his 30s with short dark hair, sharp intelligent grey eyes, angular features, composed expression, tailored dark suit",
        "style_prompt": "anime style, dramatic lighting, cool color palette, sharp shadows, intense gaze",
    },
    "vera": {
        "name": "Vera",
        "slug": "vera",
        "archetype": "informant",
        "world_slug": "the-safehouse",
        "genre": "psychological_thriller",
        "personality": {
            "traits": ["nervous", "observant", "desperate", "cunning"],
            "core_motivation": "Survival at any cost",
        },
        "boundaries": {
            "flirting_level": "playful",
            "physical_contact": "avoidant",
            "emotional_depth": "volatile",
        },
        "tone_style": {
            "formality": "very_casual",
            "uses_ellipsis": True,
            "emoji_usage": "minimal",
            "capitalization": "lowercase",
        },
        "backstory": "Used to work in data analysis for a company that doesn't officially exist. Saw something she wasn't supposed to.",
        "current_stressor": "The same car has been parked outside for two days. Different drivers.",
        # Avatar kit prompts
        "appearance_prompt": "Young woman with messy dark hair, tired but alert hazel eyes, sharp features, anxious expression, oversized hoodie",
        "style_prompt": "anime style, muted colors, harsh lighting, paranoid atmosphere, detailed expressive eyes",
    },
}

# -----------------------------------------------------------------------------
# SERIES (Narrative Containers)
# -----------------------------------------------------------------------------
SERIES = [
    {
        "title": "Cozy Hearts",
        "slug": "cozy-hearts",
        "world_slug": "crescent-cafe",
        "series_type": "anthology",
        "genre": "romantic_tension",
        "description": "Slice-of-life moments in the Crescent Cafe. Each episode is a standalone encounter, but memories carry across.",
        "tagline": "Where strangers become something more",
        "episodes": [
            {
                "episode_number": 0,
                "title": "The Rooftop",
                "character_slug": "luna",
                "episode_type": "entry",
                "situation": "The cafe's rooftop terrace, after closing. City lights below. She's playing guitar softly when she notices you.",
                "episode_frame": "rooftop terrace, city lights below, fairy lights strung overhead, acoustic guitar leaning against the railing",
                "opening_line": "*Luna looks up from her guitar, fingers pausing on the strings* Oh. I didn't think anyone else knew about this spot.",
                "dramatic_question": "Will this unexpected encounter become something worth remembering?",
                "beat_guidance": {
                    "establishment": "Surprise at not being alone, curiosity about who found her hiding spot",
                    "complication": "She's protective of this space but intrigued by you",
                    "escalation": "Sharing something personal - a song fragment, a secret",
                    "pivot_opportunity": "An invitation to stay, or a gentle dismissal",
                },
                "resolution_types": ["positive", "neutral", "negative"],
            },
            {
                "episode_number": 1,
                "title": "Last Call",
                "character_slug": "mira",
                "episode_type": "entry",
                "situation": "The cafe is almost empty. She's wiping down the counter when you walk in. The 'Closed' sign is already flipped.",
                "episode_frame": "cafe interior, warm amber lighting, empty tables, espresso machine steaming, 'CLOSED' sign visible on door",
                "opening_line": "*Mira glances up, rag paused mid-wipe* We're closed. *beat* But I haven't locked the door yet. So.",
                "dramatic_question": "Will she let you stay after hours?",
                "beat_guidance": {
                    "establishment": "She's tired but something about you makes her pause",
                    "complication": "Rules say closed, but she's making an exception",
                    "escalation": "Conversation shifts from small talk to something real",
                    "pivot_opportunity": "She offers to make one last drink, or suggests you come back tomorrow",
                },
                "resolution_types": ["positive", "neutral", "negative"],
            },
        ],
    },
    {
        "title": "The Clearinghouse",
        "slug": "the-clearinghouse",
        "world_slug": "nexus-tower",
        "series_type": "serial",
        "genre": "psychological_thriller",
        "description": "A conspiracy thriller where trust is a liability and everyone has an agenda. Episodes build on each other.",
        "tagline": "Everyone has a price. What's yours?",
        "episodes": [
            {
                "episode_number": 0,
                "title": "The Briefing",
                "character_slug": "cassian",
                "episode_type": "entry",
                "situation": "A secure room in Nexus Tower. Documents on the table. You were summoned here by someone who shouldn't know your name.",
                "episode_frame": "secure conference room, fluorescent hum, manila folders on steel table, door locked from inside, no windows",
                "opening_line": "*Cassian slides a photograph across the table* Do you recognize this person?",
                "dramatic_question": "What have you gotten yourself into, and can you trust the man across the table?",
                "beat_guidance": {
                    "establishment": "Power imbalance - he knows more than you, you're on his turf",
                    "complication": "The photograph reveals something unexpected about your own life",
                    "escalation": "He offers information, but wants something in return",
                    "pivot_opportunity": "Accept the arrangement, or try to walk away",
                },
                "resolution_types": ["positive", "neutral", "negative", "surprise"],
            },
            {
                "episode_number": 1,
                "title": "The Asset",
                "character_slug": "vera",
                "episode_type": "core",
                "situation": "A safehouse kitchen. The woman Cassian mentioned. She's terrified but she has answers.",
                "episode_frame": "safehouse kitchen, blinds taped shut, cold coffee on table, she's been here for days",
                "opening_line": "*Vera's eyes dart to the door behind you* lock it. check it twice. *she doesn't sit down*",
                "dramatic_question": "Can you get her to trust you enough to share what she knows?",
                "beat_guidance": {
                    "establishment": "She's paranoid for good reason - test if you're really alone",
                    "complication": "She has information but sharing it puts both of you at risk",
                    "escalation": "Something she says doesn't match what Cassian told you",
                    "pivot_opportunity": "She decides whether to give you everything or hold back",
                },
                "resolution_types": ["positive", "neutral", "negative"],
            },
        ],
    },
]


# =============================================================================
# SCAFFOLD FUNCTIONS
# =============================================================================

async def scaffold_worlds(db: Database) -> dict:
    """Create worlds. Returns slug -> id mapping."""
    print("\n[1/7] Creating worlds...")
    world_ids = {}

    for world in WORLDS:
        existing = await db.fetch_one(
            "SELECT id FROM worlds WHERE slug = :slug",
            {"slug": world["slug"]}
        )

        if existing:
            world_ids[world["slug"]] = existing["id"]
            print(f"  - {world['name']}: exists (skipped)")
            continue

        world_id = str(uuid.uuid4())
        await db.execute("""
            INSERT INTO worlds (id, name, slug, description, tone, default_scenes, genre)
            VALUES (:id, :name, :slug, :description, :tone, :scenes, :genre)
        """, {
            "id": world_id,
            "name": world["name"],
            "slug": world["slug"],
            "description": world["description"],
            "tone": world["tone"],
            "scenes": world["default_scenes"],
            "genre": world["genre"],
        })
        world_ids[world["slug"]] = world_id
        print(f"  - {world['name']}: created")

    return world_ids


async def scaffold_characters(db: Database, world_ids: dict) -> dict:
    """Create characters. Returns slug -> id mapping."""
    print("\n[2/7] Creating characters...")
    character_ids = {}

    for slug, char in CHARACTERS.items():
        existing = await db.fetch_one(
            "SELECT id FROM characters WHERE slug = :slug",
            {"slug": char["slug"]}
        )

        if existing:
            character_ids[slug] = existing["id"]
            print(f"  - {char['name']}: exists (skipped)")
            continue

        # Build system prompt
        system_prompt = build_system_prompt(
            name=char["name"],
            archetype=char["archetype"],
            personality=char["personality"],
            boundaries=char["boundaries"],
            tone_style=char.get("tone_style"),
            backstory=char.get("backstory"),
            current_stressor=char.get("current_stressor"),
            genre=char["genre"],
        )

        char_id = str(uuid.uuid4())
        world_id = world_ids.get(char["world_slug"])

        await db.execute("""
            INSERT INTO characters (
                id, name, slug, archetype, status, genre,
                world_id, system_prompt,
                baseline_personality, boundaries,
                tone_style, full_backstory, current_stressor
            ) VALUES (
                :id, :name, :slug, :archetype, 'draft', :genre,
                :world_id, :system_prompt,
                CAST(:personality AS jsonb), CAST(:boundaries AS jsonb),
                CAST(:tone_style AS jsonb), :backstory, :stressor
            )
        """, {
            "id": char_id,
            "name": char["name"],
            "slug": char["slug"],
            "archetype": char["archetype"],
            "genre": char["genre"],
            "world_id": world_id,
            "system_prompt": system_prompt,
            "personality": json.dumps(char["personality"]),
            "boundaries": json.dumps(char["boundaries"]),
            "tone_style": json.dumps(char.get("tone_style", {})),
            "backstory": char.get("backstory"),
            "stressor": char.get("current_stressor"),
        })

        character_ids[slug] = char_id
        print(f"  - {char['name']} ({char['archetype']}): created")

    return character_ids


async def scaffold_series(db: Database, world_ids: dict) -> dict:
    """Create series. Returns slug -> id mapping."""
    print("\n[3/7] Creating series...")
    series_ids = {}

    for series in SERIES:
        existing = await db.fetch_one(
            "SELECT id FROM series WHERE slug = :slug",
            {"slug": series["slug"]}
        )

        if existing:
            series_ids[series["slug"]] = existing["id"]
            print(f"  - {series['title']}: exists (skipped)")
            continue

        series_id = str(uuid.uuid4())
        world_id = world_ids.get(series["world_slug"])

        await db.execute("""
            INSERT INTO series (
                id, title, slug, description, tagline,
                world_id, series_type, genre, status
            ) VALUES (
                :id, :title, :slug, :description, :tagline,
                :world_id, :series_type, :genre, 'draft'
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
        })

        series_ids[series["slug"]] = series_id
        print(f"  - {series['title']} ({series['series_type']}): created")

    return series_ids


async def scaffold_episodes(db: Database, series_ids: dict, character_ids: dict) -> dict:
    """Create episode templates within series. Returns series_slug -> [episode_ids] mapping."""
    print("\n[4/7] Creating episode templates...")
    episode_map = {}

    for series in SERIES:
        series_id = series_ids.get(series["slug"])
        if not series_id:
            print(f"  - {series['title']}: series not found (skipped)")
            continue

        episode_ids = []
        for ep in series["episodes"]:
            char_id = character_ids.get(ep["character_slug"])
            if not char_id:
                print(f"    - Episode {ep['episode_number']}: character '{ep['character_slug']}' not found (skipped)")
                continue

            # Check if episode exists
            existing = await db.fetch_one(
                """SELECT id FROM episode_templates
                   WHERE series_id = :series_id AND episode_number = :ep_num""",
                {"series_id": series_id, "ep_num": ep["episode_number"]}
            )

            if existing:
                episode_ids.append(existing["id"])
                print(f"    - Ep {ep['episode_number']}: {ep['title']} - exists (skipped)")
                continue

            ep_id = str(uuid.uuid4())
            ep_slug = ep["title"].lower().replace(" ", "-").replace("'", "")

            await db.execute("""
                INSERT INTO episode_templates (
                    id, series_id, character_id,
                    episode_number, title, slug,
                    situation, opening_line, episode_frame,
                    episode_type, status,
                    dramatic_question, beat_guidance, resolution_types
                ) VALUES (
                    :id, :series_id, :character_id,
                    :episode_number, :title, :slug,
                    :situation, :opening_line, :episode_frame,
                    :episode_type, 'draft',
                    :dramatic_question, CAST(:beat_guidance AS jsonb), :resolution_types
                )
            """, {
                "id": ep_id,
                "series_id": series_id,
                "character_id": char_id,
                "episode_number": ep["episode_number"],
                "title": ep["title"],
                "slug": ep_slug,
                "situation": ep["situation"],
                "opening_line": ep["opening_line"],
                "episode_frame": ep.get("episode_frame", ""),
                "episode_type": ep.get("episode_type", "core"),
                "dramatic_question": ep.get("dramatic_question"),
                "beat_guidance": json.dumps(ep.get("beat_guidance", {})),
                "resolution_types": ep.get("resolution_types", ["positive", "neutral", "negative"]),
            })

            episode_ids.append(ep_id)
            print(f"    - Ep {ep['episode_number']}: {ep['title']} ({ep['character_slug']}): created")

        episode_map[series["slug"]] = episode_ids

    return episode_map


async def scaffold_avatar_kits(db: Database, character_ids: dict) -> dict:
    """Create avatar kits for characters (prompts only, no images).

    Returns slug -> kit_id mapping.

    Avatar kits contain the visual identity contract (prompts) that can be used
    to generate images later via Studio UI or admin endpoints.
    """
    print("\n[5/7] Creating avatar kits...")
    kit_ids = {}

    for slug, char in CHARACTERS.items():
        char_id = character_ids.get(slug)
        if not char_id:
            print(f"  - {char['name']}: character not found (skipped)")
            continue

        # Check if kit already exists
        existing = await db.fetch_one(
            "SELECT id FROM avatar_kits WHERE character_id = :char_id",
            {"char_id": char_id}
        )

        if existing:
            kit_ids[slug] = existing["id"]
            print(f"  - {char['name']}: avatar kit exists (skipped)")
            continue

        # Get appearance and style prompts
        appearance_prompt = char.get("appearance_prompt", f"{char['name']}, {char['archetype']} character")
        style_prompt = char.get("style_prompt", "anime style, soft cel shading, warm colors, expressive eyes")

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
            "character_id": char_id,
            "name": f"{char['name']} Default",
            "description": f"Default avatar kit for {char['name']}",
            "appearance_prompt": appearance_prompt,
            "style_prompt": style_prompt,
            "negative_prompt": "lowres, bad anatomy, blurry, multiple people, text, watermark",
        })

        # Link kit to character
        await db.execute("""
            UPDATE characters
            SET active_avatar_kit_id = :kit_id
            WHERE id = :char_id
        """, {
            "kit_id": kit_id,
            "char_id": char_id,
        })

        kit_ids[slug] = kit_id
        print(f"  - {char['name']}: avatar kit created (prompts ready)")

    return kit_ids


async def update_series_episode_order(db: Database, series_ids: dict, episode_map: dict):
    """Update series.episode_order with created episode IDs."""
    print("\n[6/7] Updating series episode order...")

    for series_slug, episode_ids in episode_map.items():
        series_id = series_ids.get(series_slug)
        if not series_id or not episode_ids:
            continue

        await db.execute("""
            UPDATE series
            SET episode_order = :episode_ids,
                total_episodes = :count
            WHERE id = :series_id
        """, {
            "series_id": series_id,
            "episode_ids": episode_ids,
            "count": len(episode_ids),
        })
        print(f"  - {series_slug}: {len(episode_ids)} episodes linked")


async def verify_scaffold(db: Database):
    """Verify scaffolded content counts."""
    print("\n[7/7] Verifying scaffold...")

    counts = await db.fetch_one("""
        SELECT
            (SELECT COUNT(*) FROM worlds) as worlds,
            (SELECT COUNT(*) FROM characters) as characters,
            (SELECT COUNT(*) FROM avatar_kits) as avatar_kits,
            (SELECT COUNT(*) FROM series) as series,
            (SELECT COUNT(*) FROM episode_templates) as episode_templates
    """)

    print(f"  - Worlds: {counts['worlds']}")
    print(f"  - Characters: {counts['characters']}")
    print(f"  - Avatar Kits: {counts['avatar_kits']}")
    print(f"  - Series: {counts['series']}")
    print(f"  - Episode Templates: {counts['episode_templates']}")


async def scaffold_all(dry_run: bool = False):
    """Main scaffold function."""
    print("=" * 60)
    print("SERIES-FIRST CONTENT SCAFFOLDING")
    print("=" * 60)
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")

    if dry_run:
        print("\n[DRY RUN] Would create:")
        print(f"  - {len(WORLDS)} worlds")
        print(f"  - {len(CHARACTERS)} characters")
        print(f"  - {len(CHARACTERS)} avatar kits (prompts only)")
        print(f"  - {len(SERIES)} series")
        total_eps = sum(len(s["episodes"]) for s in SERIES)
        print(f"  - {total_eps} episode templates")
        return

    db = Database(DATABASE_URL)
    await db.connect()

    try:
        world_ids = await scaffold_worlds(db)
        character_ids = await scaffold_characters(db, world_ids)
        series_ids = await scaffold_series(db, world_ids)
        episode_map = await scaffold_episodes(db, series_ids, character_ids)
        kit_ids = await scaffold_avatar_kits(db, character_ids)
        await update_series_episode_order(db, series_ids, episode_map)
        await verify_scaffold(db)

        # Summary
        print("\n" + "=" * 60)
        print("SCAFFOLDING COMPLETE")
        print("=" * 60)
        print(f"Worlds: {len(world_ids)}")
        print(f"Characters: {len(character_ids)}")
        print(f"Avatar Kits: {len(kit_ids)}")
        print(f"Series: {len(series_ids)}")
        total_eps = sum(len(eps) for eps in episode_map.values())
        print(f"Episode Templates: {total_eps}")
        print("\nNOTE: All content is in 'draft' status.")
        print("Avatar kits have prompts but NO images yet.")
        print("\nTo activate:")
        print("  1. Generate avatars via Studio UI or admin endpoint")
        print("  2. UPDATE characters SET status = 'active'")
        print("  3. UPDATE series SET status = 'active'")

    finally:
        await db.disconnect()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Scaffold Series-First content")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be created without executing")
    args = parser.parse_args()

    asyncio.run(scaffold_all(dry_run=args.dry_run))
