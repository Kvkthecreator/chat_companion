"""Scaffold Bitter Rivals Series.

CANON COMPLIANT: docs/CONTENT_ARCHITECTURE_CANON.md
GENRE: enemies_to_lovers (Escape Room Archetype - Rivalry Path)
WORLD: flexible (works with any user-created character)
TARGET: Fanfic audience, user-created characters

Concept:
- User's OC is their insufferable rival in [context TBD by character]
- Forced to work together on something neither can do alone
- Banter-forward with crackling tension underneath
- The hate is a mask. They both know it. Neither will admit it.

Key Fanfic Tropes:
- "I hate you" (but I can't stop thinking about you)
- Forced proximity through competition
- The moment they realize it was never hate
- Tension through verbal sparring

This series demonstrates:
- User-created character as NPC (OC is the love interest)
- Enemies-to-lovers arc across 4 episodes
- Banter-forward styling for fanfic audience
- Props as rivalry trophies that become meaningful

Usage:
    python -m app.scripts.scaffold_bitter_rivals
    python -m app.scripts.scaffold_bitter_rivals --dry-run
"""

import asyncio
import json
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from databases import Database

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres.lfwhdzwbikyzalpbwfnd:42PJb25YJhJHJdkl@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres"
)

# =============================================================================
# ENEMIES-TO-LOVERS STYLE CONSTANTS
# =============================================================================

ETL_STYLE = "dramatic cinematic photography, high contrast lighting, tension in the frame, two silhouettes, charged atmosphere"
ETL_QUALITY = "masterpiece, best quality, highly detailed, dramatic shadows, emotional intensity"
ETL_NEGATIVE = "anime, cartoon, bright cheerful, low quality, blurry, text, watermark, multiple people beyond two"

# =============================================================================
# SERIES METADATA
# =============================================================================

SERIES_DATA = {
    "title": "Bitter Rivals",
    "slug": "bitter-rivals",
    "description": "They're your rival in everything. Top of every list, always one step ahead or behind. You've hated them since the day you met. At least, that's what you tell yourself. When you're forced to work together, the hate starts to feel like something else entirely.",
    "tagline": "The hate was never hate. You both knew it.",
    "genre": "enemies_to_lovers",
    "series_type": "serial",
    "visual_style": {
        "rendering": ETL_STYLE,
        "quality": ETL_QUALITY,
        "negative": ETL_NEGATIVE,
        "palette": "high contrast, charged shadows, tension lighting, dramatic depth",
    },
}

# =============================================================================
# PROPS DEFINITIONS (ADR-005 - AUTOMATIC REVEALS)
# =============================================================================
# Enemies-to-lovers uses automatic reveals for pacing.
# Props are rivalry artifacts that gain new meaning.

EPISODE_PROPS = {
    # Episode 0: The Assignment
    # Goal: Forced to be partners, hostility is palpable
    0: [
        {
            "name": "The Scoreboard",
            "slug": "the-scoreboard",
            "prop_type": "document",
            "description": "A running tally of every time you've beaten them. And every time they've beaten you. The margins are razor thin. They've been keeping track too.",
            "content": "Wins: You - 47, Them - 48. Last updated: yesterday. In their handwriting: 'Enjoy second place.'",
            "content_format": "handwritten",
            "reveal_mode": "automatic",
            "reveal_turn_hint": 0,
            "is_key_evidence": True,
            "badge_label": "History",
            "evidence_tags": ["rivalry", "obsession", "equal"],
            "display_order": 0,
        },
        {
            "name": "Their Tell",
            "slug": "their-tell",
            "prop_type": "object",
            "description": "You've watched them long enough to know when they're nervous. The way they tap their finger, adjust their collar. You're not sure when you started noticing.",
            "content": None,
            "content_format": None,
            "reveal_mode": "automatic",
            "reveal_turn_hint": 4,
            "is_key_evidence": False,
            "badge_label": "Observation",
            "evidence_tags": ["watching", "detail", "intimacy"],
            "display_order": 1,
        },
    ],
    # Episode 1: Common Ground
    # Goal: Working together reveals uncomfortable similarities
    1: [
        {
            "name": "The Same Strategy",
            "slug": "same-strategy",
            "prop_type": "document",
            "description": "You both had the same plan. Down to the details. They look at you differently after that - like they're seeing you for the first time.",
            "content": "Two pages of notes, side by side. Almost identical reasoning. Different handwriting, same conclusion.",
            "content_format": None,
            "reveal_mode": "automatic",
            "reveal_turn_hint": 2,
            "is_key_evidence": True,
            "badge_label": "Mirror",
            "evidence_tags": ["parallel", "recognition", "unnerving"],
            "display_order": 0,
        },
        {
            "name": "Reluctant Compliment",
            "slug": "reluctant-compliment",
            "prop_type": "object",
            "description": "They said something almost nice. Then immediately took it back. But you heard it. And they know you heard it.",
            "content": None,
            "content_format": None,
            "reveal_mode": "automatic",
            "reveal_turn_hint": 5,
            "is_key_evidence": False,
            "badge_label": "Crack",
            "evidence_tags": ["slip", "genuine", "denial"],
            "display_order": 1,
        },
    ],
    # Episode 2: The Truce
    # Goal: A crisis forces real cooperation, walls start crumbling
    2: [
        {
            "name": "Their Real Laugh",
            "slug": "real-laugh",
            "prop_type": "object",
            "description": "Not the smirk they use in competition. An actual laugh. Surprised out of them. At something you said. You want to hear it again.",
            "content": None,
            "content_format": None,
            "reveal_mode": "automatic",
            "reveal_turn_hint": 3,
            "is_key_evidence": True,
            "badge_label": "Unguarded",
            "evidence_tags": ["genuine", "surprise", "want"],
            "display_order": 0,
        },
        {
            "name": "The Almost-Moment",
            "slug": "almost-moment",
            "prop_type": "object",
            "description": "Something shifted. A pause that lasted too long. Eyes that dropped to lips. Neither of you acknowledged it. But it happened.",
            "content": None,
            "content_format": None,
            "reveal_mode": "automatic",
            "reveal_turn_hint": 7,
            "is_key_evidence": True,
            "badge_label": "Turning Point",
            "evidence_tags": ["tension", "unspoken", "charged"],
            "display_order": 1,
        },
    ],
    # Episode 3: The Truth
    # Goal: No more pretending, confrontation of what this really is
    3: [
        {
            "name": "The Question",
            "slug": "the-question",
            "prop_type": "object",
            "description": "'Why do you hate me?' They finally ask. But the way they ask... they already know the answer isn't hate.",
            "content": None,
            "content_format": None,
            "reveal_mode": "automatic",
            "reveal_turn_hint": 2,
            "is_key_evidence": True,
            "badge_label": "Confrontation",
            "evidence_tags": ["direct", "vulnerability", "truth"],
            "display_order": 0,
        },
        {
            "name": "The Admission",
            "slug": "the-admission",
            "prop_type": "object",
            "description": "One of you says it first. The thing you've both been pretending wasn't true. The rivalry was never about winning. It was about not losing them.",
            "content": None,
            "content_format": None,
            "reveal_mode": "automatic",
            "reveal_turn_hint": 6,
            "is_key_evidence": True,
            "badge_label": "The Truth",
            "evidence_tags": ["confession", "release", "finally"],
            "display_order": 1,
        },
    ],
}

# =============================================================================
# EPISODE DEFINITIONS
# =============================================================================

EPISODES = [
    {
        "episode_number": 0,
        "title": "The Assignment",
        "situation": "You've been paired with them. Of all people. The one person you can't stand - the one who matches you in everything, beats you half the time, and never lets you forget it. You'll have to work together. The thought is unbearable. Almost.",
        "dramatic_question": "Can you work with someone you've spent years competing against - and why does their presence affect you this much?",
        "opening_line": "*They're already there when you arrive, leaning against the wall with that infuriating smirk.* 'Well. This should be interesting.'",
        "scene_objective": "Establish the rivalry dynamic. Banter is sharp but underneath there's something else - awareness, obsession disguised as competition.",
        "turn_budget": 10,
        "starter_prompts": [
            "Of course they stuck me with you.",
            "Don't expect me to carry you through this.",
            "Try not to slow me down.",
        ],
    },
    {
        "episode_number": 1,
        "title": "Common Ground",
        "situation": "Working together is going better than expected. Worse than expected. You keep finishing each other's thoughts. They're smart - really smart - and watching them work is... You need to focus. This is still a competition, even if you're on the same side.",
        "dramatic_question": "What happens when your rival starts to feel less like an enemy and more like an equal - someone who actually sees you?",
        "opening_line": "*They slide their notes across the table, then freeze when they see yours.* '...You have got to be kidding me.'",
        "scene_objective": "Reveal uncomfortable similarities. The animosity becomes harder to maintain when you realize how alike you are.",
        "turn_budget": 10,
        "starter_prompts": [
            "Great minds think alike. Unfortunately.",
            "Stop agreeing with me, it's unsettling.",
            "This doesn't mean anything.",
        ],
    },
    {
        "episode_number": 2,
        "title": "The Truce",
        "situation": "Something's changed. The barbs don't land the same way. When you argue now, it feels like something else. They've started looking at you differently. Or maybe you've started noticing. The competition isn't the problem anymore. The problem is what's underneath it.",
        "dramatic_question": "When the rivalry stops being a shield, what are you left with - and are you brave enough to face it?",
        "opening_line": "*They catch you staring and don't look away.* 'See something you like?' *But there's no edge to it. Just a question.*",
        "scene_objective": "Build genuine tension. This is where the denial starts to crack. Physical awareness, loaded silences, almost-moments.",
        "turn_budget": 12,
        "starter_prompts": [
            "We should probably talk about... never mind.",
            "Why are you looking at me like that?",
            "This is getting complicated.",
        ],
    },
    {
        "episode_number": 3,
        "title": "The Truth",
        "situation": "No more games. No more competition. Something happened - or almost happened - and you can't pretend anymore. They're not your rival. They never really were. The question is whether you're brave enough to admit what they actually are.",
        "dramatic_question": "When you finally admit the truth - to yourself and to them - what happens to everything you thought you knew?",
        "opening_line": "*They find you alone, and for once, neither of you has a clever comeback.* 'We need to talk. Actually talk.'",
        "scene_objective": "Emotional climax. The walls come down. This is the confession scene fanfic readers live for.",
        "turn_budget": 12,
        "starter_prompts": [
            "I never hated you. I think you know that.",
            "Tell me I'm not imagining this.",
            "What are we doing?",
        ],
    },
]


async def main(dry_run: bool = False):
    """Scaffold the Bitter Rivals series."""
    print("=" * 60)
    print("SCAFFOLDING: Bitter Rivals (Enemies to Lovers)")
    print("=" * 60)

    if dry_run:
        print("\n[DRY RUN - No database changes will be made]\n")

    db = Database(DATABASE_URL)
    await db.connect()

    try:
        # Create series
        series_id = uuid.uuid4()
        print(f"\n1. Creating series: {SERIES_DATA['title']}")
        print(f"   ID: {series_id}")
        print(f"   Genre: {SERIES_DATA['genre']}")

        if not dry_run:
            await db.execute(
                """INSERT INTO series (
                    id, title, slug, description, tagline,
                    series_type, genre, status, visual_style
                ) VALUES (
                    :id, :title, :slug, :description, :tagline,
                    :series_type, :genre, 'draft', CAST(:visual_style AS jsonb)
                )""",
                {
                    "id": str(series_id),
                    "title": SERIES_DATA["title"],
                    "slug": SERIES_DATA["slug"],
                    "description": SERIES_DATA["description"],
                    "tagline": SERIES_DATA["tagline"],
                    "series_type": SERIES_DATA["series_type"],
                    "genre": SERIES_DATA["genre"],
                    "visual_style": json.dumps(SERIES_DATA["visual_style"]),
                }
            )
            print("   ✓ Series created")

        # Create episodes and props
        print(f"\n2. Creating {len(EPISODES)} episodes with props...")
        for ep in EPISODES:
            ep_id = uuid.uuid4()
            print(f"\n   Episode {ep['episode_number']}: {ep['title']}")
            print(f"   ID: {ep_id}")

            ep_slug = f"{SERIES_DATA['slug']}-ep{ep['episode_number']}"
            if not dry_run:
                await db.execute(
                    """INSERT INTO episode_templates (
                        id, series_id, episode_number, title, slug,
                        situation, opening_line, episode_type, status,
                        dramatic_question, scene_objective,
                        turn_budget, starter_prompts
                    ) VALUES (
                        :id, :series_id, :episode_number, :title, :slug,
                        :situation, :opening_line, 'core', 'draft',
                        :dramatic_question, :scene_objective,
                        :turn_budget, :starter_prompts
                    )""",
                    {
                        "id": str(ep_id),
                        "series_id": str(series_id),
                        "episode_number": ep["episode_number"],
                        "title": ep["title"],
                        "slug": ep_slug,
                        "situation": ep["situation"],
                        "opening_line": ep["opening_line"],
                        "dramatic_question": ep["dramatic_question"],
                        "scene_objective": ep["scene_objective"],
                        "turn_budget": ep.get("turn_budget", 10),
                        "starter_prompts": ep.get("starter_prompts", []),
                    }
                )
                print("   ✓ Episode created")

            # Create props for this episode
            props = EPISODE_PROPS.get(ep["episode_number"], [])
            for prop in props:
                prop_id = uuid.uuid4()
                print(f"      Prop: {prop['name']} (turn {prop['reveal_turn_hint']})")

                if not dry_run:
                    await db.execute(
                        """INSERT INTO props (
                            id, episode_template_id, name, slug, prop_type,
                            description, content, content_format, reveal_mode,
                            reveal_turn_hint, is_key_evidence, badge_label,
                            display_order
                        ) VALUES (
                            :id, :episode_template_id, :name, :slug, :prop_type,
                            :description, :content, :content_format, :reveal_mode,
                            :reveal_turn_hint, :is_key_evidence, :badge_label,
                            :display_order
                        )""",
                        {
                            "id": str(prop_id),
                            "episode_template_id": str(ep_id),
                            "name": prop["name"],
                            "slug": prop["slug"],
                            "prop_type": prop["prop_type"],
                            "description": prop["description"],
                            "content": prop.get("content"),
                            "content_format": prop.get("content_format"),
                            "reveal_mode": prop["reveal_mode"],
                            "reveal_turn_hint": prop.get("reveal_turn_hint"),
                            "is_key_evidence": prop["is_key_evidence"],
                            "badge_label": prop.get("badge_label"),
                            "display_order": prop["display_order"],
                        }
                    )

        print("\n" + "=" * 60)
        if dry_run:
            print("DRY RUN COMPLETE - No changes made")
        else:
            print("SCAFFOLD COMPLETE")
            print(f"Series ID: {series_id}")
            print("\nNext steps:")
            print("1. Create/assign a user character to play as the rival")
            print("2. Generate images: python -m app.scripts.generate_bitter_rivals_images")
            print("3. Activate via SQL: UPDATE series SET status = 'active' WHERE slug = 'bitter-rivals'")
        print("=" * 60)

    finally:
        await db.disconnect()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Scaffold Bitter Rivals series")
    parser.add_argument("--dry-run", action="store_true", help="Preview without database changes")
    args = parser.parse_args()

    asyncio.run(main(dry_run=args.dry_run))
