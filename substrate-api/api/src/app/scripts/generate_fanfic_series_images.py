"""Generate images for OC/fanfic series (Bitter Rivals, The Arrangement).

These are "bring your own character" series, so they only need:
1. Series cover images
2. Episode background images

No character avatars are generated - users bring their own OCs.

Usage:
    python -m app.scripts.generate_fanfic_series_images
    python -m app.scripts.generate_fanfic_series_images --series bitter-rivals
    python -m app.scripts.generate_fanfic_series_images --series the-arrangement

Environment variables required:
    REPLICATE_API_TOKEN - Replicate API key
"""

import asyncio
import logging
import os
import sys

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
    "postgresql://postgres.lfwhdzwbikyzalpbwfnd:42PJb25YJhJHJdkl@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres"
)

GENERATION_DELAY = 5

# =============================================================================
# BITTER RIVALS (Enemies to Lovers) - Dramatic tension aesthetic
# =============================================================================

BITTER_RIVALS_STYLE = "cinematic photography, dramatic lighting, high contrast, tension in frame"
BITTER_RIVALS_NEGATIVE = "anime, cartoon, bright cheerful, low quality, blurry, text, watermark, faces visible"

BITTER_RIVALS_COVER = {
    "prompt": """cinematic photography, two silhouettes facing each other in dramatic standoff,
high contrast lighting casting long shadows, tension visible in posture,
competitive atmosphere, corporate or academic setting implied, no faces visible,
dramatic backlighting, enemies to lovers aesthetic, charged atmosphere,
masterpiece, best quality, dramatic shadows, emotional intensity""",
    "negative": BITTER_RIVALS_NEGATIVE,
}

BITTER_RIVALS_EPISODES = {
    "The Assignment": {
        "prompt": """cinematic photography, modern conference room or study space,
two chairs facing each other across table, dramatic overhead lighting,
papers and documents scattered, competitive workspace atmosphere,
tension implied through composition, no people, dramatic shadows,
high contrast lighting, professional rivalry setting""",
        "negative": BITTER_RIVALS_NEGATIVE,
    },
    "Common Ground": {
        "prompt": """cinematic photography, late night office or library setting,
two workstations side by side with matching notes visible, warm desk lamps,
papers with similar handwriting, mirror effect in composition,
realization moment implied, no people, dramatic lighting,
intimate workspace, reluctant collaboration atmosphere""",
        "negative": BITTER_RIVALS_NEGATIVE,
    },
    "The Truce": {
        "prompt": """cinematic photography, intimate corner of cafe or lounge,
two coffee cups on small table, soft ambient lighting, evening atmosphere,
tension shifting to something else, walls closing in feeling,
no people visible, charged intimate atmosphere, dramatic depth,
romantic tension emerging from rivalry""",
        "negative": BITTER_RIVALS_NEGATIVE,
    },
    "The Truth": {
        "prompt": """cinematic photography, quiet private space at golden hour,
two shadows nearly touching on wall, dramatic window light,
moment of truth atmosphere, vulnerability in composition,
no people visible, romantic dramatic lighting, confession setting,
enemies to lovers climax, emotional intensity in light and shadow""",
        "negative": BITTER_RIVALS_NEGATIVE,
    },
}

# =============================================================================
# THE ARRANGEMENT (Fake Dating) - Warm romantic aesthetic
# =============================================================================

ARRANGEMENT_STYLE = "cinematic photography, warm romantic lighting, soft intimate atmosphere"
ARRANGEMENT_NEGATIVE = "anime, cartoon, harsh lighting, low quality, blurry, text, watermark, faces visible"

ARRANGEMENT_COVER = {
    "prompt": """cinematic photography, two hands almost intertwined on restaurant table,
napkin with handwritten notes visible nearby, candlelight glow,
fake dating arrangement aesthetic, intimate but uncertain atmosphere,
warm romantic lighting, no faces visible, tension of pretending,
masterpiece, best quality, emotional warmth""",
    "negative": ARRANGEMENT_NEGATIVE,
}

ARRANGEMENT_EPISODES = {
    "The Terms": {
        "prompt": """cinematic photography, intimate cafe booth setting,
napkin with handwritten terms visible on table, two coffee cups,
negotiation atmosphere but romantic undertones, warm afternoon light,
no people visible, arrangement being made, warm color grade,
soft focus background, fake dating setup""",
        "negative": ARRANGEMENT_NEGATIVE,
    },
    "The Performance": {
        "prompt": """cinematic photography, elegant event venue entrance,
warm fairy lights and romantic atmosphere, doorway framing,
about to enter together moment, performance about to begin,
no people visible, anticipation in composition, soft romantic lighting,
public appearance setting, fake couple aesthetic""",
        "negative": ARRANGEMENT_NEGATIVE,
    },
    "The Cracks": {
        "prompt": """cinematic photography, quiet balcony or terrace at evening,
city lights in soft focus background, intimate private moment,
two champagne glasses abandoned on railing, jealousy aftermath,
no people visible, tension and confusion, warm romantic lighting,
lines blurring between fake and real""",
        "negative": ARRANGEMENT_NEGATIVE,
    },
    "The End": {
        "prompt": """cinematic photography, quiet street or garden at twilight,
event venue visible in soft background, moment of ending,
two shadows close but uncertain, golden hour lighting,
no people visible, the arrangement ending, romantic atmosphere,
what happens now moment, emotional warmth in fading light""",
        "negative": ARRANGEMENT_NEGATIVE,
    },
}


async def generate_series_cover(db: Database, storage: StorageService, image_service: ImageService, series_slug: str, config: dict):
    """Generate series cover image."""
    print(f"\n{'=' * 60}")
    print(f"GENERATING COVER: {series_slug}")
    print("=" * 60)

    series = await db.fetch_one(
        "SELECT id, title, cover_image_url FROM series WHERE slug = :slug",
        {"slug": series_slug}
    )
    if not series:
        print(f"ERROR: Series '{series_slug}' not found!")
        return False

    if series["cover_image_url"]:
        print(f"Series already has cover: {series['cover_image_url'][:80]}...")
        print("Skipping cover generation.")
        return True

    try:
        print(f"Generating cover for: {series['title']}")
        print(f"Prompt: {config['prompt'][:150]}...")

        response = await image_service.generate(
            prompt=config["prompt"],
            negative_prompt=config["negative"],
            width=1024,
            height=576,  # 16:9 aspect ratio
        )

        if not response.images:
            print("ERROR: No images returned!")
            return False

        image_bytes = response.images[0]
        series_id = series["id"]
        storage_path = f"series/{series_id}/cover.png"

        await storage._upload(
            bucket="scenes",
            path=storage_path,
            data=image_bytes,
            content_type="image/png",
        )

        cover_url = storage.get_public_url("scenes", storage_path)
        await db.execute(
            "UPDATE series SET cover_image_url = :url, updated_at = NOW() WHERE id = :id",
            {"url": cover_url, "id": str(series_id)}
        )

        print(f"✓ Cover generated! ({response.latency_ms}ms)")
        print(f"  URL: {cover_url}")
        return True

    except Exception as e:
        print(f"✗ Failed to generate cover: {e}")
        log.exception("Cover generation failed")
        return False


async def generate_episode_backgrounds(db: Database, storage: StorageService, image_service: ImageService, series_slug: str, episode_configs: dict):
    """Generate background images for all episodes."""
    print(f"\n{'=' * 60}")
    print(f"GENERATING EPISODE BACKGROUNDS: {series_slug}")
    print("=" * 60)

    series = await db.fetch_one(
        "SELECT id FROM series WHERE slug = :slug",
        {"slug": series_slug}
    )
    if not series:
        print(f"ERROR: Series '{series_slug}' not found!")
        return False

    episodes = await db.fetch_all(
        """SELECT id, title, episode_number, background_image_url
           FROM episode_templates
           WHERE series_id = :series_id
           ORDER BY episode_number""",
        {"series_id": str(series["id"])}
    )

    if not episodes:
        print("ERROR: No episodes found!")
        return False

    success_count = 0
    for ep in episodes:
        title = ep["title"]
        if ep["background_image_url"]:
            print(f"  Episode {ep['episode_number']} '{title}': already has background, skipping")
            success_count += 1
            continue

        config = episode_configs.get(title)
        if not config:
            print(f"  Episode {ep['episode_number']} '{title}': no config found, skipping")
            continue

        try:
            print(f"  Episode {ep['episode_number']} '{title}': generating...")

            response = await image_service.generate(
                prompt=config["prompt"],
                negative_prompt=config["negative"],
                width=1024,
                height=576,  # 16:9 aspect ratio
            )

            if not response.images:
                print(f"    ✗ No images returned")
                continue

            image_bytes = response.images[0]
            storage_path = f"episodes/{ep['id']}/background.png"

            await storage._upload(
                bucket="scenes",
                path=storage_path,
                data=image_bytes,
                content_type="image/png",
            )

            bg_url = storage.get_public_url("scenes", storage_path)
            await db.execute(
                "UPDATE episode_templates SET background_image_url = :url, updated_at = NOW() WHERE id = :id",
                {"url": bg_url, "id": str(ep["id"])}
            )

            print(f"    ✓ Generated! ({response.latency_ms}ms)")
            success_count += 1

            # Rate limiting
            await asyncio.sleep(GENERATION_DELAY)

        except Exception as e:
            print(f"    ✗ Failed: {e}")
            log.exception(f"Background generation failed for {title}")

    print(f"\nBackgrounds complete: {success_count}/{len(episodes)}")
    return success_count == len(episodes)


async def main(series_filter: str = None):
    """Main entry point."""
    print("=" * 60)
    print("FANFIC SERIES IMAGE GENERATION")
    print("=" * 60)

    db = Database(DATABASE_URL)
    await db.connect()

    storage = StorageService()
    image_service = ImageService()

    try:
        series_to_process = []

        if series_filter is None or series_filter == "bitter-rivals":
            series_to_process.append({
                "slug": "bitter-rivals",
                "cover": BITTER_RIVALS_COVER,
                "episodes": BITTER_RIVALS_EPISODES,
            })

        if series_filter is None or series_filter == "the-arrangement":
            series_to_process.append({
                "slug": "the-arrangement",
                "cover": ARRANGEMENT_COVER,
                "episodes": ARRANGEMENT_EPISODES,
            })

        for series_config in series_to_process:
            slug = series_config["slug"]
            print(f"\n{'#' * 60}")
            print(f"# Processing: {slug}")
            print("#" * 60)

            # Generate cover
            await generate_series_cover(db, storage, image_service, slug, series_config["cover"])
            await asyncio.sleep(GENERATION_DELAY)

            # Generate episode backgrounds
            await generate_episode_backgrounds(db, storage, image_service, slug, series_config["episodes"])

        print("\n" + "=" * 60)
        print("IMAGE GENERATION COMPLETE")
        print("=" * 60)

    finally:
        await db.disconnect()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate images for fanfic series")
    parser.add_argument("--series", choices=["bitter-rivals", "the-arrangement"],
                        help="Generate images for specific series only")
    args = parser.parse_args()

    asyncio.run(main(series_filter=args.series))
