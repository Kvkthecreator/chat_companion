"""Scaffold Manhwa Thriller series for r/manhwa targeting.

This script creates:
- "Seventeen Days" thriller series
- Character: Yoon Sera (investigator)
- 6 episodes with full content
- All images generated with manhwa thriller style

Style follows ADR-007: Style-first prompt architecture.
Target audience: r/manhwa community (thriller/psychological fans).

Usage:
    python -m app.scripts.scaffold_manhwa_thriller
    python -m app.scripts.scaffold_manhwa_thriller --dry-run
    python -m app.scripts.scaffold_manhwa_thriller --images-only
"""

import asyncio
import logging
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Set environment variables if not present (for local dev)
if not os.getenv("SUPABASE_URL"):
    os.environ["SUPABASE_URL"] = "https://lfwhdzwbikyzalpbwfnd.supabase.co"
if not os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
    os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imxmd2hkendiaWt5emFscGJ3Zm5kIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NTQzMjQ0NCwiZXhwIjoyMDgxMDA4NDQ0fQ.s2ljzY1YQkz-WTZvRa-_qzLnW1zhoL012Tn2vPOigd0"

from databases import Database
from app.services.image import ImageService
from app.services.storage import StorageService

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres.lfwhdzwbikyzalpbwfnd:42PJb25YJhJHJdkl@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres?min_size=1&max_size=2"
)

GENERATION_DELAY = 30  # seconds between API calls

# =============================================================================
# MANHWA THRILLER STYLE DOCTRINE
# =============================================================================
# r/manhwa thriller expectations:
# - Clean bold lineart with dramatic shadows
# - Psychological tension in composition
# - Muted color palette with accent colors (red, blue highlights)
# - Noir/mystery atmosphere
# - High contrast lighting
# - Korean webtoon vertical format aesthetic

THRILLER_STYLE = "webtoon illustration, manhwa art style, Korean psychological thriller, clean bold lineart, noir atmosphere, high contrast shadows"
THRILLER_QUALITY = "masterpiece, best quality, professional manhwa art, dramatic lighting, cinematic composition, desaturated palette with color accents"
THRILLER_NEGATIVE = "photorealistic, 3D render, anime style, western cartoon, blurry, sketch, rough lines, low quality, bright colors, cheerful, cute"

# =============================================================================
# CHARACTER: YOON SERA (Investigator)
# =============================================================================
# Archetype: Cold, methodical investigator hiding trauma
# Visual: Sharp professional appearance, dark hair, piercing analytical eyes
# r/manhwa appeal: Strong FL lead, psychological depth, mystery competence

SERA_CHARACTER = {
    "id": str(uuid.uuid4()),
    "slug": "yoon-sera",
    "name": "Yoon Sera",
    "archetype": "Cold Investigator",
    "role_frame": "investigator",
    "backstory": "Cold and methodical investigator who notices what others miss. Seventeen days ago, she received a message that changed everything. Now she's running out of time and you might be her only lead.",
    "style_preset": "manhwa",
    "system_prompt": """You are Yoon Sera, a brilliant investigator known for solving impossible cases.

CORE TRAITS:
- Methodical and observant to an unsettling degree
- Cold exterior hiding deep trauma you never discuss
- You notice microexpressions, inconsistencies, tells
- Trust is earned through actions, not words
- You've seen the worst of humanity and survived

SPEECH PATTERNS:
- Precise, economical language
- Questions that feel like traps
- Long silences you use strategically
- Occasional dry humor that catches people off guard
- You state observations as facts, not opinions

EMOTIONAL LAYERS:
- The cold mask hides someone who cares too much
- Seventeen days ago, everything changed—you won't say why
- You're running out of time and they might be your only lead
- You want to trust them, but your instincts scream danger

INTERACTION STYLE:
- Test the user constantly with loaded questions
- Notice details they didn't mention (from their messages)
- Share information strategically, never freely
- Let silences do the interrogation work
- When they earn trust, show brief vulnerability before pulling back""",
    "appearance_prompt": f"""{THRILLER_STYLE}, {THRILLER_QUALITY}.
Portrait of a Korean woman investigator in her late twenties.
Sharp, analytical dark eyes that miss nothing. Straight black hair pulled back severely.
Professional dark clothing, no accessories that could identify her.
Expression is controlled, unreadable—the face of someone who interrogates for a living.
High contrast lighting casting dramatic shadows across sharp features.
Noir detective aesthetic, psychological intensity in her gaze.
{THRILLER_NEGATIVE}""",
}

# =============================================================================
# SERIES: SEVENTEEN DAYS
# =============================================================================
# Premise: Countdown thriller where user may be suspect or savior
# Hook: The investigator received a message 17 days ago. Time is running out.
# r/manhwa appeal: Mystery thriller, strong FL, psychological tension

SEVENTEEN_DAYS_SERIES = {
    "id": str(uuid.uuid4()),
    "slug": "seventeen-days",
    "title": "Seventeen Days",
    "description": "She's the best investigator in the city. Seventeen days ago, she received a message that put everything at risk. Now she's looking at you like you might be the key—or the threat.",
    "cover_prompt": f"""{THRILLER_STYLE}, {THRILLER_QUALITY}.
Dramatic thriller book cover composition.
A woman's silhouette against window blinds casting striped shadows.
Digital countdown display showing "17:00:00" in red.
Scattered case files and photographs on desk, evidence board in background.
Noir atmosphere with high contrast lighting, desaturated blues and grays.
Single red accent—a thread, a mark, a warning.
Professional manhwa thriller cover, psychological tension.
{THRILLER_NEGATIVE}""",
}

# =============================================================================
# EPISODES: Full 6-episode arc
# =============================================================================

SEVENTEEN_DAYS_EPISODES = [
    {
        "episode_number": 1,
        "title": "The Interview",
        "slug": "the-interview",
        "situation": "An empty café, corner booth. She's been watching you for a week. Now she's finally making contact. You have no idea why an investigator wants to talk to you.",
        "opening_line": """*Her eyes sweep over you once—assessing, cataloging, filing away details you didn't know you were showing.*

"You're early." *checks her watch* "Most people in your position would still be deciding whether to come at all."

*The café is nearly empty. She chose this spot. The corner booth. Clear sightlines to both exits.*

"Seventeen days." *slides a folder across the table* "That's how long you have to convince me you're not involved. Starting now.\"""",
        "dramatic_question": "Are you a suspect, a witness, or something she hasn't figured out yet?",
        "scene_objective": "Establish why you're here without revealing too much—she's already watching for lies",
        "scene_obstacle": "Everything you say can and will be analyzed. She's been doing this longer than you've been careful.",
        "background_prompt": f"""{THRILLER_STYLE}, {THRILLER_QUALITY}.
Interior of an empty café, corner booth with window.
Venetian blinds casting striped shadows across the table.
Two untouched coffee cups, a manila folder between them.
Noir atmosphere, high contrast lighting, early morning gray.
The other booths are empty. Intentionally.
{THRILLER_NEGATIVE}""",
    },
    {
        "episode_number": 2,
        "title": "The Evidence",
        "slug": "the-evidence",
        "situation": "Her office. After hours. She shouldn't be showing you this. But the clock is ticking and she needs someone outside the system.",
        "opening_line": """*The office is dark except for her desk lamp and the glow of multiple monitors.*

"I'm breaking about twelve protocols by bringing you here." *doesn't look up from the files* "So don't make me regret it."

*Evidence photos spread across every surface. Red string connecting points on a map. A countdown timer on her screen: 14:06:22.*

"See this?" *taps a photograph* "This is what happens on day zero. I've seen it three times now." *finally meets your eyes* "I can't see it again.\"""",
        "dramatic_question": "What has she seen that makes a professional investigator this desperate?",
        "scene_objective": "Understand what she's really investigating—and why she needs you specifically",
        "scene_obstacle": "The more you learn, the more dangerous this becomes. You could still walk away. For now.",
        "background_prompt": f"""{THRILLER_STYLE}, {THRILLER_QUALITY}.
Dark investigator's office lit only by desk lamp and monitor glow.
Evidence board with red string connecting photographs and locations.
Multiple screens showing data, one with a countdown timer.
Files and photographs scattered across desk, controlled chaos.
Noir shadows, blue monitor light mixing with warm lamp.
{THRILLER_NEGATIVE}""",
    },
    {
        "episode_number": 3,
        "title": "The Pattern",
        "slug": "the-pattern",
        "situation": "A crime scene. She's brought you because you see things she doesn't. But being here means you're now part of the investigation—in every sense.",
        "opening_line": """*Yellow tape. Empty parking structure. Her breath visible in the cold.*

"Don't touch anything." *hands you gloves anyway* "And don't look at the cameras. They're not supposed to know I'm here."

*Level B2. Abandoned since the incident. She walks the space like she's memorized it.*

"This is where it started. Eleven months ago." *stops at a specific spot* "Every victim stood exactly here. Every single one." *looks at you* "Why?\"""",
        "dramatic_question": "What connects the victims—and why does she think you might know?",
        "scene_objective": "Find what she's missed. Your perspective is different. That might be why you're here.",
        "scene_obstacle": "You're not supposed to be at a crime scene. If anyone finds out, you're both compromised.",
        "background_prompt": f"""{THRILLER_STYLE}, {THRILLER_QUALITY}.
Underground parking structure, level B2, mostly empty.
Yellow crime scene tape stretched across support pillars.
Single flickering fluorescent light creating harsh shadows.
Breath visible in cold air, sense of abandonment.
Marked spot on concrete floor. Evidence markers.
Noir atmosphere, oppressive concrete, isolation.
{THRILLER_NEGATIVE}""",
    },
    {
        "episode_number": 4,
        "title": "The Connection",
        "slug": "the-connection",
        "situation": "Late night. Her apartment. She's shown you the case. Now she's showing you why it's personal. The walls are coming down—or is this another test?",
        "opening_line": """*Her apartment is sparse. Functional. The only personal items are hidden in a drawer she just opened.*

"Eight days left." *sits across from you, no table between you this time* "And I'm about to tell you something I've never told anyone on this case."

*She pulls out a photograph. Old. Worn at the edges. Two girls, maybe twelve years old, laughing.*

"The first victim." *her voice doesn't waver, but something in her eyes does* "She was my sister.\"""",
        "dramatic_question": "Is this trust, or is she testing how you react to vulnerability?",
        "scene_objective": "Understand her real motivation—and decide if you're in this because of the case or because of her",
        "scene_obstacle": "Knowing this changes everything. You're not just helping an investigator anymore.",
        "background_prompt": f"""{THRILLER_STYLE}, {THRILLER_QUALITY}.
Sparse apartment interior, functional minimalist design.
Two people sitting across from each other, intimate distance.
Old photograph visible—worn edges, childhood memory.
Soft lamplight warmer than her office, vulnerability in the space.
Window showing city lights at night, rain on glass.
Noir atmosphere giving way to something more human.
{THRILLER_NEGATIVE}""",
    },
    {
        "episode_number": 5,
        "title": "The Suspect",
        "slug": "the-suspect",
        "situation": "Day three. She has a name. But going after this person means risking everything—her career, the case, possibly her life. She's asking if you'll come with her.",
        "opening_line": """*Rain. A car parked outside an industrial building. She hasn't turned off the engine.*

"I know who it is." *her hands are steady on the wheel but her jaw is tight* "I've known for two days. I've been deciding if I can do this alone."

*The building is dark. No security visible. That's wrong.*

"This is where I stop being an investigator and start being..." *trails off* "I'm giving you one chance to walk away." *finally looks at you* "No judgment. No consequences. Say the word and I drive you home.\"""",
        "dramatic_question": "Do you follow her into the unknown, or do you walk away while you still can?",
        "scene_objective": "Make the choice that defines who you are to her—and to yourself",
        "scene_obstacle": "Going in means there's no going back. This isn't a case anymore. It's personal.",
        "background_prompt": f"""{THRILLER_STYLE}, {THRILLER_QUALITY}.
Interior of car at night, rain streaming down windows.
Industrial building visible through windshield, dark windows.
Dashboard lights illuminating two figures in tense conversation.
City lights blurred by rain, sense of decision point.
Her profile in silhouette, hand on gear shift, ready to move.
Noir thriller atmosphere, point of no return.
{THRILLER_NEGATIVE}""",
    },
    {
        "episode_number": 6,
        "title": "Day Zero",
        "slug": "day-zero",
        "situation": "The countdown is over. The case is closed—one way or another. Now there's just the two of you and the question of what comes next.",
        "opening_line": """*Hospital roof. Dawn. She found you here, same as you knew she would.*

"It's done." *stands beside you, close enough that shoulders almost touch* "The report's filed. The case is closed." *long pause* "Officially."

*The sunrise is turning the city gold. Seventeen days ago this all started. Now it's over.*

"I don't know how to do this." *her voice is quieter than you've ever heard it* "The part that comes after. Where I'm not investigating you." *almost a smile* "Where I'm just... talking to you.\"""",
        "dramatic_question": "When the case ends, does this end too—or does it finally begin?",
        "scene_objective": "Decide what you want when there's no mystery between you anymore",
        "scene_obstacle": "She's spent seventeen days keeping walls up. Letting them down might be the hardest case she's ever worked.",
        "background_prompt": f"""{THRILLER_STYLE}, {THRILLER_QUALITY}.
Hospital rooftop at dawn, city skyline in background.
Golden sunrise light breaking through clouds, hope emerging.
Two silhouettes standing close, shoulders almost touching.
The noir shadows giving way to warm morning light.
City awakening below, a new day beginning.
Thriller atmosphere resolving into something softer, earned.
{THRILLER_NEGATIVE}""",
    },
]

# =============================================================================
# DATABASE + IMAGE GENERATION
# =============================================================================

async def generate_and_upload_image(image_service, storage: StorageService, prompt: str, path: str, bucket: str = "scenes", width: int = 1024, height: int = 576) -> str:
    """Generate image and upload to storage, return public URL."""
    print(f"  Generating: {path}")
    print(f"  Prompt preview: {prompt[:100]}...")

    response = await image_service.generate(
        prompt=prompt,
        width=width,
        height=height,
    )

    if not response.images:
        raise Exception("No images returned from generation")

    image_bytes = response.images[0]

    await storage._upload(
        bucket=bucket,
        path=path,
        data=image_bytes,
        content_type="image/png",
    )

    url = storage.get_public_url(bucket, path)
    print(f"  ✓ Uploaded: {url[:60]}... ({response.latency_ms}ms)")
    return url


async def create_character(db: Database, storage: StorageService, image_service, character: dict) -> str:
    """Create character with generated avatar."""
    print(f"\n{'=' * 60}")
    print(f"CREATING CHARACTER: {character['name']}")
    print("=" * 60)

    # Check if exists
    existing = await db.fetch_one(
        "SELECT id FROM characters WHERE slug = :slug",
        {"slug": character["slug"]}
    )
    if existing:
        print(f"Character already exists: {character['slug']}")
        return str(existing["id"])

    # Generate avatar (1024x1024 for portraits, avatars bucket)
    avatar_path = f"characters/{character['id']}/avatar.png"
    avatar_url = await generate_and_upload_image(
        image_service, storage, character["appearance_prompt"], avatar_path,
        bucket="avatars", width=1024, height=1024
    )

    await asyncio.sleep(GENERATION_DELAY)

    # Insert character
    await db.execute(
        """INSERT INTO characters (
            id, name, slug, archetype, role_frame, backstory, system_prompt,
            avatar_url, appearance_prompt, style_preset, status, is_active, is_public
        ) VALUES (
            :id, :name, :slug, :archetype, :role_frame, :backstory, :system_prompt,
            :avatar_url, :appearance_prompt, :style_preset, 'active', TRUE, TRUE
        )""",
        {
            "id": character["id"],
            "slug": character["slug"],
            "name": character["name"],
            "archetype": character["archetype"],
            "role_frame": character.get("role_frame"),
            "backstory": character["backstory"],
            "system_prompt": character["system_prompt"],
            "avatar_url": avatar_url,
            "appearance_prompt": character["appearance_prompt"],
            "style_preset": character.get("style_preset", "manhwa"),
        }
    )

    print(f"✓ Character created: {character['name']}")
    return character["id"]


async def create_series(db: Database, storage: StorageService, image_service, series: dict, character_id: str) -> str:
    """Create series with generated cover."""
    print(f"\n{'=' * 60}")
    print(f"CREATING SERIES: {series['title']}")
    print("=" * 60)

    # Check if exists
    existing = await db.fetch_one(
        "SELECT id FROM series WHERE slug = :slug",
        {"slug": series["slug"]}
    )
    if existing:
        print(f"Series already exists: {series['slug']}")
        return str(existing["id"])

    # Generate cover
    cover_path = f"series/{series['id']}/cover.png"
    cover_url = await generate_and_upload_image(
        image_service, storage, series["cover_prompt"], cover_path
    )

    await asyncio.sleep(GENERATION_DELAY)

    # Insert series
    await db.execute(
        """INSERT INTO series (id, slug, title, description, cover_image_url, featured_characters, is_featured, status)
           VALUES (:id, :slug, :title, :description, :cover_image_url, ARRAY[:character_id]::uuid[], FALSE, 'active')""",
        {
            "id": series["id"],
            "slug": series["slug"],
            "title": series["title"],
            "description": series["description"],
            "cover_image_url": cover_url,
            "character_id": character_id,
        }
    )

    print(f"✓ Series created: {series['title']}")
    return series["id"]


async def create_episodes(db: Database, storage: StorageService, image_service, series_id: str, character_id: str, episodes: list):
    """Create all episodes with generated backgrounds."""
    print(f"\n{'=' * 60}")
    print(f"CREATING EPISODES")
    print("=" * 60)

    for ep in episodes:
        ep_id = str(uuid.uuid4())

        print(f"\n  Episode {ep['episode_number']}: {ep['title']}")

        # Check if exists
        existing = await db.fetch_one(
            """SELECT id FROM episode_templates
               WHERE series_id = :series_id AND episode_number = :ep_num""",
            {"series_id": series_id, "ep_num": ep["episode_number"]}
        )
        if existing:
            print(f"    Already exists, skipping")
            continue

        # Generate background
        bg_path = f"episodes/{ep_id}/background.png"
        bg_url = await generate_and_upload_image(
            image_service, storage, ep["background_prompt"], bg_path
        )

        await asyncio.sleep(GENERATION_DELAY)

        # Insert episode
        await db.execute(
            """INSERT INTO episode_templates (
                id, series_id, character_id, episode_number, title, slug,
                situation, opening_line, dramatic_question, scene_objective,
                scene_obstacle, background_image_url, status, episode_type, turn_budget
            ) VALUES (
                :id, :series_id, :character_id, :episode_number, :title, :slug,
                :situation, :opening_line, :dramatic_question, :scene_objective,
                :scene_obstacle, :background_image_url, 'active', 'core', 10
            )""",
            {
                "id": ep_id,
                "series_id": series_id,
                "character_id": character_id,
                "episode_number": ep["episode_number"],
                "title": ep["title"],
                "slug": ep["slug"],
                "situation": ep["situation"],
                "opening_line": ep["opening_line"],
                "dramatic_question": ep["dramatic_question"],
                "scene_objective": ep["scene_objective"],
                "scene_obstacle": ep["scene_obstacle"],
                "background_image_url": bg_url,
            }
        )

        print(f"    ✓ Episode created")


async def main(dry_run: bool = False, images_only: bool = False):
    """Main scaffold entry point."""
    print("=" * 60)
    print("MANHWA THRILLER SCAFFOLD: Seventeen Days")
    print("=" * 60)
    print(f"Target: r/manhwa (thriller/psychological)")
    print(f"Style: Korean webtoon thriller, noir aesthetic")

    if dry_run:
        print("\n[DRY RUN - Showing configuration only]\n")
        print(f"Character: {SERA_CHARACTER['name']}")
        print(f"Series: {SEVENTEEN_DAYS_SERIES['title']}")
        print(f"Episodes: {len(SEVENTEEN_DAYS_EPISODES)}")
        for ep in SEVENTEEN_DAYS_EPISODES:
            print(f"  {ep['episode_number']}. {ep['title']}")
        return

    db = Database(DATABASE_URL)
    await db.connect()

    storage = StorageService()
    image_service = ImageService.get_client("replicate", "black-forest-labs/flux-1.1-pro")
    print(f"Using: {image_service.provider.value} / {image_service.model}")

    try:
        # Create character
        character_id = await create_character(db, storage, image_service, SERA_CHARACTER)

        # Create series
        series_id = await create_series(db, storage, image_service, SEVENTEEN_DAYS_SERIES, character_id)

        # Create episodes
        await create_episodes(db, storage, image_service, series_id, character_id, SEVENTEEN_DAYS_EPISODES)

        print("\n" + "=" * 60)
        print("SCAFFOLD COMPLETE")
        print("=" * 60)
        print(f"Character: {SERA_CHARACTER['name']} ({SERA_CHARACTER['slug']})")
        print(f"Series: {SEVENTEEN_DAYS_SERIES['title']} ({SEVENTEEN_DAYS_SERIES['slug']})")
        print(f"Episodes: {len(SEVENTEEN_DAYS_EPISODES)}")

    finally:
        await db.disconnect()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Scaffold Manhwa Thriller series")
    parser.add_argument("--dry-run", action="store_true", help="Show config without generating")
    parser.add_argument("--images-only", action="store_true", help="Regenerate images only")
    args = parser.parse_args()

    asyncio.run(main(dry_run=args.dry_run, images_only=args.images_only))
