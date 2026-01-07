"""Regenerate images for OC/fanfic series with illustrated style prompts.

These are "bring your own character" series targeting fanfic audience.
Style should be: illustrated, romantic, dreamy - NOT hyper-realistic photography.

Key prompting principle: STYLE + GENRE FIRST, then scene details.
This prompt structure is model-agnostic and can work with any image gen provider.

Usage:
    python -m app.scripts.regenerate_oc_series_images
    python -m app.scripts.regenerate_oc_series_images --series bitter-rivals
    python -m app.scripts.regenerate_oc_series_images --series the-arrangement
    python -m app.scripts.regenerate_oc_series_images --dry-run

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

GENERATION_DELAY = 30  # 30 second delay to avoid rate limits

# =============================================================================
# STYLE PRINCIPLES FOR OC/FANFIC SERIES
# =============================================================================
# 1. Style + Genre FIRST in every prompt
# 2. Illustrated/artistic, NOT photographic
# 3. Romantic, dreamy, emotional atmosphere
# 4. Abstract enough to work with any user's OC
# 5. No specific character features (users bring their own)

# Base style for all OC series - illustrated romance aesthetic
OC_BASE_STYLE = "romantic illustration style, soft watercolor aesthetic, dreamy atmosphere, book cover art quality"
OC_QUALITY = "beautiful illustration, professional digital art, emotional resonance, soft color palette"

# =============================================================================
# BITTER RIVALS (Enemies to Lovers) - Dramatic illustrated style
# =============================================================================

BITTER_RIVALS_GENRE = "enemies to lovers romance"
BITTER_RIVALS_STYLE = f"{OC_BASE_STYLE}, {BITTER_RIVALS_GENRE}, dramatic tension, charged atmosphere, high contrast mood"

BITTER_RIVALS_COVER = {
    "prompt": f"""{BITTER_RIVALS_STYLE}, {OC_QUALITY}.
Two abstract silhouettes facing each other in dramatic standoff composition.
Warm and cool tones clashing - one figure in warm amber, one in cool blue.
Dramatic lighting suggesting tension and attraction. Space between them charged with energy.
Abstract romantic rivalry aesthetic. No detailed faces - emotional through posture and color.
Professional book cover illustration for enemies to lovers romance.""",
}

BITTER_RIVALS_EPISODES = {
    "The Assignment": {
        "prompt": f"""{BITTER_RIVALS_STYLE}, {OC_QUALITY}.
Illustrated scene of two desks or workspaces side by side, forced partnership aesthetic.
Papers scattered between them creating visual bridge. Warm desk lamp lighting.
Tension in the composition - separate but connected. Academic or professional setting.
Soft illustrated style, romantic undertones beneath rivalry surface.
No people visible, let the space tell the story of forced proximity.""",
    },
    "Common Ground": {
        "prompt": f"""{BITTER_RIVALS_STYLE}, {OC_QUALITY}.
Illustrated late night study scene - two sets of notes that mirror each other.
Warm golden lamplight, coffee cups, shared realization moment implied.
Visual parallels in composition showing unexpected similarity.
Soft watercolor rendering, intimate workspace atmosphere.
The moment rivals realize they think alike. No people, just their matching work.""",
    },
    "The Truce": {
        "prompt": f"""{BITTER_RIVALS_STYLE}, {OC_QUALITY}.
Illustrated intimate cafe corner, soft evening lighting through window.
Two coffee cups close together on small table, steam rising and mingling.
Warm romantic atmosphere replacing cold rivalry. Soft focus, dreamy quality.
The space between them shrinking. Watercolor style, emotional warmth.
Tension shifting to something else entirely.""",
    },
    "The Truth": {
        "prompt": f"""{BITTER_RIVALS_STYLE}, {OC_QUALITY}.
Illustrated confession scene aesthetic - golden hour lighting, two shadows almost touching.
Dramatic window light creating silhouettes that lean toward each other.
Emotional climax atmosphere, vulnerability in composition. Warm amber tones.
Soft illustrated style, the moment before everything changes.
Romantic resolution emerging from rivalry. Abstract and emotional.""",
    },
}

# =============================================================================
# THE ARRANGEMENT (Fake Dating) - Warm romantic illustrated style
# =============================================================================

ARRANGEMENT_GENRE = "fake dating romance"
ARRANGEMENT_STYLE = f"{OC_BASE_STYLE}, {ARRANGEMENT_GENRE}, warm intimate lighting, soft romantic atmosphere"

ARRANGEMENT_COVER = {
    "prompt": f"""{ARRANGEMENT_STYLE}, {OC_QUALITY}.
Illustrated romantic scene - two hands almost touching over cafe table.
Napkin with handwritten notes visible, soft candlelight glow.
The tension of pretending, uncertain intimacy. Warm peach and rose tones.
Professional romance book cover illustration. Soft watercolor aesthetic.
Fake dating trope visual - the performance that becomes real.""",
}

ARRANGEMENT_EPISODES = {
    "The Terms": {
        "prompt": f"""{ARRANGEMENT_STYLE}, {OC_QUALITY}.
Illustrated intimate cafe booth, soft afternoon light.
Napkin with handwritten "terms" visible, two coffee cups.
Negotiation becoming something more. Warm honey lighting.
Soft illustrated style - the arrangement being made.
Romantic undertones beneath the business-like setup.""",
    },
    "The Performance": {
        "prompt": f"""{ARRANGEMENT_STYLE}, {OC_QUALITY}.
Illustrated elegant venue entrance, fairy lights and warm glow.
Romantic doorway framing, about to step into the performance.
Soft focus background with bokeh lights. Anticipation in composition.
Watercolor style - the moment before going public as a "couple".
Warm rose and gold tones, romantic event aesthetic.""",
    },
    "The Cracks": {
        "prompt": f"""{ARRANGEMENT_STYLE}, {OC_QUALITY}.
Illustrated balcony scene at evening, city lights soft in background.
Two champagne glasses abandoned on railing, moment after tension.
Private moment where fake feelings become confusingly real.
Soft romantic illustration, warm lighting despite emotional confusion.
The arrangement cracking - jealousy that shouldn't exist.""",
    },
    "The End": {
        "prompt": f"""{ARRANGEMENT_STYLE}, {OC_QUALITY}.
Illustrated twilight garden scene, soft golden hour ending.
Two figures as gentle silhouettes, close but uncertain.
The arrangement is over but neither moves to leave.
Warm romantic illustration, emotional ending that could be beginning.
Soft watercolor style, "what happens now" atmosphere.""",
    },
}


async def regenerate_series_cover(db: Database, storage: StorageService, image_service, series_slug: str, config: dict, force: bool = False):
    """Generate or regenerate series cover image."""
    print(f"\n{'=' * 60}")
    print(f"REGENERATING COVER: {series_slug}")
    print("=" * 60)

    series = await db.fetch_one(
        "SELECT id, title, cover_image_url FROM series WHERE slug = :slug",
        {"slug": series_slug}
    )
    if not series:
        print(f"ERROR: Series '{series_slug}' not found!")
        return False

    if series["cover_image_url"] and not force:
        print(f"Series already has cover (use --force to regenerate)")
        print(f"Current: {series['cover_image_url'][:80]}...")
        # For regeneration, we always force

    try:
        print(f"Generating cover for: {series['title']}")
        print(f"Using Gemini/Imagen with illustrated style")
        print(f"Prompt preview: {config['prompt'][:200]}...")

        response = await image_service.generate(
            prompt=config["prompt"],
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


async def regenerate_episode_backgrounds(db: Database, storage: StorageService, image_service, series_slug: str, episode_configs: dict, force: bool = False):
    """Generate or regenerate background images for all episodes."""
    print(f"\n{'=' * 60}")
    print(f"REGENERATING EPISODE BACKGROUNDS: {series_slug}")
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

        config = episode_configs.get(title)
        if not config:
            print(f"  Episode {ep['episode_number']} '{title}': no config found, skipping")
            continue

        try:
            print(f"  Episode {ep['episode_number']} '{title}': generating with Gemini...")

            response = await image_service.generate(
                prompt=config["prompt"],
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


async def main(series_filter: str = None, dry_run: bool = False):
    """Main entry point."""
    print("=" * 60)
    print("OC SERIES IMAGE REGENERATION (Gemini + Illustrated Style)")
    print("=" * 60)

    if dry_run:
        print("\n[DRY RUN - Showing prompts only, no generation]\n")

    db = Database(DATABASE_URL)
    await db.connect()

    storage = StorageService()

    # ADR-007: Use FLUX Schnell for backgrounds/covers (no characters, style-first OK)
    # The key improvement is prompt structure (style + genre FIRST)
    # Schnell at $0.003/image vs Dev at $0.05/image = 94% savings
    image_service = ImageService.get_client("replicate", "black-forest-labs/flux-schnell")
    print(f"Using provider: {image_service.provider.value}, model: {image_service.model}")

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

            if dry_run:
                print(f"\nCOVER PROMPT:\n{series_config['cover']['prompt']}\n")
                for ep_title, ep_config in series_config["episodes"].items():
                    print(f"\nEPISODE '{ep_title}' PROMPT:\n{ep_config['prompt']}\n")
            else:
                # Generate cover
                await regenerate_series_cover(db, storage, image_service, slug, series_config["cover"], force=True)
                await asyncio.sleep(GENERATION_DELAY)

                # Generate episode backgrounds
                await regenerate_episode_backgrounds(db, storage, image_service, slug, series_config["episodes"], force=True)

        print("\n" + "=" * 60)
        print("REGENERATION COMPLETE" if not dry_run else "DRY RUN COMPLETE")
        print("=" * 60)

    finally:
        await db.disconnect()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Regenerate OC series images with Gemini")
    parser.add_argument("--series", choices=["bitter-rivals", "the-arrangement"],
                        help="Regenerate images for specific series only")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show prompts without generating images")
    args = parser.parse_args()

    asyncio.run(main(series_filter=args.series, dry_run=args.dry_run))
