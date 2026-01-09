"""Expand New Genre Series with Genre-Appropriate Episode Arcs.

Each genre gets episodes 3-5 with arc structures that match its natural narrative rhythm,
avoiding the formulaic romance arc (Entry → Intrigue → Vulnerability → Complication → Crisis → Resolution).

Usage:
    python -m app.scripts.expand_new_genres
    python -m app.scripts.expand_new_genres --dry-run
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
# GENRE-SPECIFIC EPISODE EXPANSIONS (Episodes 3-5)
# =============================================================================

EPISODE_EXPANSIONS = {
    # =========================================================================
    # COZY - No crisis needed. Warmth builds gradually. Comfort over conflict.
    # Arc: Comfort → Belonging → Ritual → Quiet Confession → Gentle Future
    # =========================================================================
    "corner-cafe": {
        "character_slug": "hana-cafe",
        "episodes": [
            {
                "episode_number": 3,
                "title": "Regulars",
                "episode_type": "core",
                "situation": "Sunday morning. The cafe is full of regulars and she introduces you to each one by name. You realize she's been telling them about you.",
                "episode_frame": "sunny cafe morning, regulars at their usual spots, warm chatter, she's behind the counter watching you fit in",
                "opening_line": "*Slides you a cup with a new design* I've been practicing this one. *watches the regulars wave at you* They already knew your order. I might have mentioned you.",
                "dramatic_question": "Have you already become part of this place without realizing it?",
                "resolution_types": ["belonging", "gentle_joy", "quiet_realization"],
            },
            {
                "episode_number": 4,
                "title": "Closed Sign",
                "episode_type": "core",
                "situation": "She flipped the sign to Closed but you're still inside. She's teaching you her grandmother's recipe. The kitchen smells like home.",
                "episode_frame": "cafe kitchen after hours, flour and sugar scattered, her grandmother's handwritten recipe card, both of you covered in ingredients",
                "opening_line": "*Hands you the worn recipe card* My grandmother gave me this when I opened the shop. *soft smile* I've never shown anyone else.",
                "dramatic_question": "What does it mean to be trusted with someone's inheritance?",
                "resolution_types": ["tender_trust", "shared_tradition", "quiet_intimacy"],
            },
            {
                "episode_number": 5,
                "title": "Morning Light",
                "episode_type": "special",
                "situation": "You helped her open early. The first light is coming through the windows. Coffee is brewing. Neither of you has anywhere else to be.",
                "episode_frame": "cafe at dawn, golden light through windows, first pot of coffee steaming, empty chairs waiting, peaceful silence",
                "opening_line": "*Leans against the counter beside you, watching the light change* I used to do this alone. *quiet* I like it better this way.",
                "dramatic_question": "Is this the beginning of something that doesn't need to be named?",
                "resolution_types": ["gentle_beginning", "unspoken_promise", "comfortable_together"],
            },
        ],
    },

    # =========================================================================
    # BL - Identity and discovery. The tension of being seen + choosing to stay visible.
    # Arc: Trust → Witness → External Threat → Choice to Be Seen → Claiming Space Together
    # =========================================================================
    "ink-and-canvas": {
        "character_slug": "jae-artist",
        "episodes": [
            {
                "episode_number": 3,
                "title": "Opening Night",
                "episode_type": "core",
                "situation": "He said yes to the gallery. Opening night. He's standing in a room full of his hidden self, and you're the only face he keeps finding in the crowd.",
                "episode_frame": "gallery opening, his paintings on white walls, strangers studying his work, him in a corner trying to breathe, finding your eyes",
                "opening_line": "*Finds you in the crowd, voice tight* Everyone's looking at things I made alone in the dark. *grabs your wrist* Stay where I can see you.",
                "dramatic_question": "Can he survive being seen by strangers if you're there to anchor him?",
                "resolution_types": ["shared_courage", "protective_presence", "pride_together"],
            },
            {
                "episode_number": 4,
                "title": "After the Crowd",
                "episode_type": "core",
                "situation": "Gallery closed. Everyone's gone. He's sitting on the floor surrounded by red 'sold' dots, overwhelmed. You sit down next to him.",
                "episode_frame": "empty gallery after hours, sold stickers on paintings, him on the floor back against wall, you sliding down beside him",
                "opening_line": "*Staring at the sold dots* They bought pieces of me. *turns to look at you* You're the only one who got them for free.",
                "dramatic_question": "What does it mean to have witnessed someone before the world did?",
                "resolution_types": ["intimate_recognition", "earned_closeness", "quiet_claim"],
            },
            {
                "episode_number": 5,
                "title": "New Canvas",
                "episode_type": "special",
                "situation": "His studio. A blank canvas. He asks you to sit. He's never painted anyone before. He wants to start with you.",
                "episode_frame": "studio at golden hour, blank canvas on easel, paint-stained everything, him holding a brush looking at you differently",
                "opening_line": "*Positions the canvas, then looks at you for a long moment* I've never wanted to paint a person before. *quiet* Stay still. Let me see you the way I do.",
                "dramatic_question": "What does it mean to be the first person he wants to capture?",
                "resolution_types": ["being_seen", "artistic_intimacy", "choosing_each_other"],
            },
        ],
    },

    # =========================================================================
    # GL - Rivalry dissolving into recognition. Competitive energy becoming protective.
    # Arc: Reluctant Trust → Unexpected Care → Public Moment → Private Admission → Choosing This
    # =========================================================================
    "debate-partners": {
        "character_slug": "yuna-rival",
        "episodes": [
            {
                "episode_number": 3,
                "title": "The Round",
                "episode_type": "core",
                "situation": "Nationals. Final round. You're across from each other on opposite teams. The topic is about vulnerability. She keeps looking at you like she's arguing with herself.",
                "episode_frame": "debate stage, judges panel, audience watching, her at the opposing podium, eyes finding yours between points",
                "opening_line": "*After the round, backstage* You argued that vulnerability is strength. *steps closer* Were you talking about the case, or were you talking about last night?",
                "dramatic_question": "When the competition forces honesty, what truths slip through?",
                "resolution_types": ["competitive_honesty", "charged_recognition", "public_private_blur"],
            },
            {
                "episode_number": 4,
                "title": "Second Place",
                "episode_type": "core",
                "situation": "She won. You came second. She finds you in the hallway after, trophy in hand, and she doesn't look happy about it.",
                "episode_frame": "empty hallway outside auditorium, her holding trophy like it weighs too much, finding you alone",
                "opening_line": "*Holds up the trophy* This doesn't feel right. *sets it down* You threw that last rebuttal. Why?",
                "dramatic_question": "What matters more - winning, or what winning costs?",
                "resolution_types": ["confronting_care", "competitive_vulnerability", "redefining_victory"],
            },
            {
                "episode_number": 5,
                "title": "After Nationals",
                "episode_type": "special",
                "situation": "Hotel room. Everyone else is at the celebration party. She knocked on your door instead. She's still in her competition blazer. She's not here to argue.",
                "episode_frame": "hotel room, city lights through window, muffled party noise down the hall, her in the doorway deciding whether to step in",
                "opening_line": "*Still in the doorway* I've spent four years trying to beat you. *finally steps inside* I don't want to compete with you anymore. I want... *stops, frustrated* I don't know how to say this without sounding like I'm losing.",
                "dramatic_question": "What happens when the person you've been fighting becomes the person you want?",
                "resolution_types": ["surrender_as_choice", "competitive_tenderness", "beginning_together"],
            },
        ],
    },

    # =========================================================================
    # HISTORICAL - Propriety as tension. Society pressure. Stolen moments.
    # Arc: Secret Shared → Scandal Risk → Propriety Demanded → Defiance Choice → Claiming Despite Cost
    # =========================================================================
    "dukes-third-son": {
        "character_slug": "lord-ashworth",
        "episodes": [
            {
                "episode_number": 3,
                "title": "The Letter",
                "episode_type": "core",
                "situation": "A servant delivered a note to your room. His handwriting. He's asking you to meet him in the conservatory at midnight. It's wildly improper.",
                "episode_frame": "conservatory at midnight, moonlight through glass ceiling, exotic plants, him waiting in shadows away from windows",
                "opening_line": "*Steps out of shadow* I shouldn't have written. *closer* I couldn't stop thinking about the garden. About what I almost said.",
                "dramatic_question": "What is he willing to risk by putting his feelings in writing?",
                "resolution_types": ["improper_honesty", "dangerous_admission", "restraint_breaking"],
            },
            {
                "episode_number": 4,
                "title": "The Announcement",
                "episode_type": "core",
                "situation": "Breakfast. His mother announces his engagement to Lady Catherine. He didn't know. He's looking at you across the table as the room applauds.",
                "episode_frame": "formal breakfast room, family and guests applauding, his mother beaming, him frozen mid-bite, eyes only on you",
                "opening_line": "*Finds you in the hallway after, voice urgent* I didn't know. I swear to you, I didn't know. *grabs your hands* This changes nothing about what I—",
                "dramatic_question": "Can private feeling survive public obligation?",
                "resolution_types": ["desperate_truth", "society_versus_heart", "impossible_choice"],
            },
            {
                "episode_number": 5,
                "title": "The Departure",
                "episode_type": "special",
                "situation": "Dawn. Carriages being loaded. The house party ends today. He intercepts you on the way to your carriage. He has something to say before you leave.",
                "episode_frame": "manor entrance at dawn, carriages waiting, servants busy, him pulling you aside behind a pillar, hidden from view",
                "opening_line": "*Pulls you into the alcove, breathless* I told my mother no. *cups your face* I don't care about the scandal. I don't care about the title. *voice breaking* Tell me you'll wait. Tell me this isn't goodbye.",
                "dramatic_question": "Is he willing to give up everything his world expects for something real?",
                "resolution_types": ["defiant_love", "choosing_scandal", "uncertain_hope"],
            },
        ],
    },

    # =========================================================================
    # PSYCHOLOGICAL - Unreliable narrator. Revelation beats. Trust/doubt cycles.
    # Arc: Method Revealed → Roles Reverse → Truth Uncertain → Mutual Exposure → Choosing to Stay Entangled
    # =========================================================================
    "session-notes": {
        "character_slug": "dr-seong",
        "episodes": [
            {
                "episode_number": 3,
                "title": "The File",
                "episode_type": "core",
                "situation": "You found your own file on his desk. He's not in the office. The notes don't match what you remember from your sessions.",
                "episode_frame": "his office empty, file open on desk, your name on the folder, notes in his handwriting that describe sessions differently than you remember",
                "opening_line": "*Appears in doorway, unsurprised* You found it. *walks to his chair, sits* Go ahead. Ask me which version is real - what you remember, or what I wrote.",
                "dramatic_question": "Can you trust your own memory when his records contradict it?",
                "resolution_types": ["destabilizing_truth", "paranoid_clarity", "complicit_uncertainty"],
            },
            {
                "episode_number": 4,
                "title": "His Session",
                "episode_type": "core",
                "situation": "He asked you to switch chairs. He wants you to ask the questions today. He says it's only fair. Something about this feels like a trap and a gift.",
                "episode_frame": "same office, chairs switched, you in his seat, him where patients sit, watching you with that unreadable expression",
                "opening_line": "*Settles into the patient chair* I've been analyzing you for weeks. *slight smile* Your turn. Ask me anything. I promise to tell you one truth and one lie.",
                "dramatic_question": "If he gives you power, what do you do with it?",
                "resolution_types": ["role_reversal", "mutual_dissection", "dangerous_equality"],
            },
            {
                "episode_number": 5,
                "title": "Last Session",
                "episode_type": "special",
                "situation": "He says your treatment is complete. This is your final session. But neither of you is moving toward the door. Something isn't finished.",
                "episode_frame": "his office, late afternoon, files closed on desk, termination paperwork unsigned, both of you still seated, not leaving",
                "opening_line": "*Taps the unsigned termination form* Professionally, I should let you go. *looks at you without the clinical mask* Personally... I find I don't want to stop seeing you. *pause* What do you want?",
                "dramatic_question": "When therapy ends, what remains? And is it healthy?",
                "resolution_types": ["boundary_dissolution", "mutual_obsession", "choosing_entanglement"],
            },
        ],
    },

    # =========================================================================
    # WORKPLACE - Professional stakes intertwined with personal. Ambition vs connection.
    # Arc: Forced Collaboration → Grudging Respect → After-Hours Blur → Career Crossroads → Choosing Both
    # =========================================================================
    "corner-office-romance": {
        "character_slug": "daniel-park",
        "episodes": [
            {
                "episode_number": 3,
                "title": "The Win",
                "episode_type": "core",
                "situation": "You won the case. Together. Champagne in the conference room. Partners are congratulating you both. His hand brushes yours under the table.",
                "episode_frame": "conference room, champagne bottles, partners shaking hands, celebration noise, his hand finding yours below the table where no one can see",
                "opening_line": "*Publicly professional, hand warm against yours under the table* Great work, counsel. *leans close enough only you hear* My place. One hour. We should celebrate properly.",
                "dramatic_question": "What happens when professional success creates private opportunity?",
                "resolution_types": ["secret_celebration", "public_private_split", "earned_together"],
            },
            {
                "episode_number": 4,
                "title": "The Offer",
                "episode_type": "core",
                "situation": "Partner track. One slot. Two candidates: you and him. He found out before you did. He's standing in your office doorway with two glasses of whiskey.",
                "episode_frame": "your office at night, him in doorway with whiskey, partnership memo visible on your desk, city lights behind him",
                "opening_line": "*Sets both glasses down* I heard about the slot. *sits in your chair instead of across from it* I'm not going to pretend I don't want it. But I'm not going to sabotage you for it either. *holds your eyes* What are we doing here?",
                "dramatic_question": "Can you want the same thing professionally and still choose each other personally?",
                "resolution_types": ["honest_competition", "professional_respect", "complicated_wanting"],
            },
            {
                "episode_number": 5,
                "title": "The Decision",
                "episode_type": "special",
                "situation": "Partnership announcement tomorrow. You're both in his apartment. Neither of you knows who got it. Tonight might be your last night as equals.",
                "episode_frame": "his apartment at night, city view, two glasses untouched, both of you knowing tomorrow changes everything",
                "opening_line": "*Looking out the window, not at you* Tomorrow one of us moves up. One of us stays. *finally turns* I need to know - whatever happens - does this survive it?",
                "dramatic_question": "Is what you've built strong enough to survive success?",
                "resolution_types": ["commitment_despite_outcome", "choosing_both", "uncertain_but_together"],
            },
        ],
    },
}


# =============================================================================
# SCAFFOLD FUNCTIONS
# =============================================================================

async def get_series_and_characters(db: Database) -> tuple[dict, dict]:
    """Get series IDs and character IDs for the new genre content."""
    print("\n[1/3] Fetching series and characters...")

    series_slugs = list(EPISODE_EXPANSIONS.keys())
    series_ids = {}
    character_ids = {}

    for slug in series_slugs:
        series = await db.fetch_one(
            "SELECT id FROM series WHERE slug = :slug",
            {"slug": slug}
        )
        if series:
            series_ids[slug] = series["id"]
            print(f"  - Series '{slug}': found")
        else:
            print(f"  - Series '{slug}': NOT FOUND")

    char_slugs = [exp["character_slug"] for exp in EPISODE_EXPANSIONS.values()]
    for slug in set(char_slugs):
        char = await db.fetch_one(
            "SELECT id FROM characters WHERE slug = :slug",
            {"slug": slug}
        )
        if char:
            character_ids[slug] = char["id"]
            print(f"  - Character '{slug}': found")
        else:
            print(f"  - Character '{slug}': NOT FOUND")

    return series_ids, character_ids


async def add_episodes(db: Database, series_ids: dict, character_ids: dict) -> dict:
    """Add new episodes to each series."""
    print("\n[2/3] Adding genre-appropriate episodes...")

    episode_map = {}

    for series_slug, expansion in EPISODE_EXPANSIONS.items():
        series_id = series_ids.get(series_slug)
        char_id = character_ids.get(expansion["character_slug"])

        if not series_id or not char_id:
            print(f"  - {series_slug}: missing series or character (skipped)")
            continue

        new_episode_ids = []

        for ep in expansion["episodes"]:
            # Check if episode already exists
            existing = await db.fetch_one(
                """SELECT id FROM episode_templates
                   WHERE series_id = :series_id AND episode_number = :ep_num""",
                {"series_id": series_id, "ep_num": ep["episode_number"]}
            )

            if existing:
                new_episode_ids.append(existing["id"])
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
                    dramatic_question, resolution_types
                ) VALUES (
                    :id, :series_id, :character_id,
                    :episode_number, :title, :slug,
                    :situation, :opening_line, :episode_frame,
                    :episode_type, 'active',
                    :dramatic_question, :resolution_types
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
                "resolution_types": ep.get("resolution_types", ["positive", "neutral", "negative"]),
            })

            new_episode_ids.append(ep_id)
            print(f"    - Ep {ep['episode_number']}: {ep['title']} - created")

        episode_map[series_slug] = new_episode_ids

    return episode_map


async def update_series_episode_order(db: Database, series_ids: dict, episode_map: dict):
    """Update series.episode_order to include new episodes."""
    print("\n[3/3] Updating series episode order...")

    for series_slug, new_episode_ids in episode_map.items():
        series_id = series_ids.get(series_slug)
        if not series_id:
            continue

        # Get existing episode_order
        series = await db.fetch_one(
            "SELECT episode_order, total_episodes FROM series WHERE id = :id",
            {"id": series_id}
        )

        existing_order = series["episode_order"] or []

        # Get all episodes for this series in order
        all_episodes = await db.fetch_all(
            """SELECT id FROM episode_templates
               WHERE series_id = :series_id
               ORDER BY episode_number""",
            {"series_id": series_id}
        )

        new_order = [ep["id"] for ep in all_episodes]

        await db.execute("""
            UPDATE series
            SET episode_order = :episode_ids, total_episodes = :count
            WHERE id = :series_id
        """, {
            "series_id": series_id,
            "episode_ids": new_order,
            "count": len(new_order),
        })

        print(f"  - {series_slug}: {len(new_order)} total episodes")


async def expand_all(dry_run: bool = False):
    """Main expansion function."""
    print("=" * 60)
    print("GENRE-APPROPRIATE EPISODE EXPANSION")
    print("Adding episodes 3-5 with genre-specific arc structures")
    print("=" * 60)

    if dry_run:
        print("\n[DRY RUN] Would add:")
        for series_slug, expansion in EPISODE_EXPANSIONS.items():
            print(f"\n  {series_slug}:")
            for ep in expansion["episodes"]:
                print(f"    - Ep {ep['episode_number']}: {ep['title']}")
                print(f"      Arc beat: {ep.get('dramatic_question', 'N/A')[:50]}...")
        return

    db = Database(DATABASE_URL)
    await db.connect()

    try:
        series_ids, character_ids = await get_series_and_characters(db)
        episode_map = await add_episodes(db, series_ids, character_ids)
        await update_series_episode_order(db, series_ids, episode_map)

        print("\n" + "=" * 60)
        print("EXPANSION COMPLETE")
        print("=" * 60)

        total_new = sum(len(eps) for eps in episode_map.values())
        print(f"New episodes added: {total_new}")
        print("\nGenre arc structures:")
        print("  - Cozy: Comfort → Belonging → Ritual → Quiet Confession")
        print("  - BL: Trust → Witness → External Validation → Claiming Space")
        print("  - GL: Rivalry → Care → Public/Private → Surrender as Choice")
        print("  - Historical: Impropriety → Scandal Risk → Defiance → Cost")
        print("  - Psychological: Revelation → Role Reversal → Mutual Exposure")
        print("  - Workplace: Collaboration → Respect → Career Stakes → Choosing Both")

    finally:
        await db.disconnect()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Expand new genre series with genre-appropriate episodes")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be created")
    args = parser.parse_args()

    asyncio.run(expand_all(dry_run=args.dry_run))
