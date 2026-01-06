"""Generate images for The Blacksite series.

This script generates:
1. Alex's character avatar (survival thriller style)
2. Series cover image
3. Episode background images (4 episodes)
4. Prop images (8 props)

Usage:
    python -m app.scripts.generate_the_blacksite_images
    python -m app.scripts.generate_the_blacksite_images --avatar-only
    python -m app.scripts.generate_the_blacksite_images --backgrounds-only
    python -m app.scripts.generate_the_blacksite_images --props-only

Environment variables required:
    REPLICATE_API_TOKEN - Replicate API key
"""

import asyncio
import json
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
    "postgresql://postgres.lfwhdzwbikyzalpbwfnd:42PJb25YJhJHJdkl@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres"
)

# Rate limiting
GENERATION_DELAY = 5

# =============================================================================
# SURVIVAL THRILLER STYLE CONSTANTS
# =============================================================================

THRILLER_STYLE = "cinematic photography, cold harsh lighting, industrial sterile environment, high contrast, clinical atmosphere"
THRILLER_QUALITY = "masterpiece, best quality, highly detailed, dramatic lighting, atmospheric tension"
THRILLER_NEGATIVE = "anime, cartoon, bright cheerful colors, warm lighting, cozy, low quality, blurry, text, watermark, multiple people"

# Alex's appearance for avatar generation
ALEX_APPEARANCE = """ambiguous gender presentation person late-20s, androgynous sharp features, short cropped dark hair,
alert calculating eyes, dressed in dark tactical clothing slightly torn and dirty, fresh bruise on cheekbone,
calm under pressure expression, observing everything, survivor aesthetic, pale from lack of sunlight"""

ALEX_STYLE = """cinematic portrait photography, harsh overhead fluorescent lighting, sterile clinical background,
survival thriller aesthetic, tension visible in alertness not fear, shallow depth of field, single subject portrait,
high contrast, cold blue-green color grade, atmospheric"""

# Series cover prompt
SERIES_COVER_PROMPT = """cinematic photography, long sterile white corridor with harsh fluorescent lights,
industrial doors on both sides, emergency exit sign flickering red, no windows, claustrophobic atmosphere,
cold clinical lighting, high contrast shadows, thriller aesthetic, sense of being watched,
masterpiece, best quality, no people visible, atmospheric dread, government facility"""

SERIES_COVER_NEGATIVE = """anime, cartoon, bright colors, warm lighting, cheerful, sunny, low quality, blurry,
text, watermark, people, faces, portraits, windows, natural light"""

# Episode background configurations
EPISODE_BACKGROUNDS = {
    "Awakening": {
        "prompt": """cinematic photography, sterile medical holding cell, bare concrete walls,
single harsh ceiling light, metal cot with thin mattress, drain in floor center,
no windows, heavy steel door with small reinforced window, cold clinical atmosphere,
thriller aesthetic, isolation, sense of captivity, blue-gray color grade, no people""",
        "negative": THRILLER_NEGATIVE,
    },
    "The Corridor": {
        "prompt": """cinematic photography, long white corridor stretching into darkness,
flickering fluorescent lights creating strobe effect, numbered doors on both sides,
security camera with blinking red light, polished linoleum floor reflecting lights,
claustrophobic ceiling, thriller aesthetic, tension, somewhere deep underground, no people""",
        "negative": THRILLER_NEGATIVE,
    },
    "The Lab": {
        "prompt": """cinematic photography, abandoned research laboratory, overturned equipment,
broken specimen containers, scattered papers and files, emergency lighting casting red glow,
computer screens with corrupted data, biohazard symbols visible, something went wrong here,
thriller aesthetic, scientific horror, cold sterile atmosphere, no people""",
        "negative": THRILLER_NEGATIVE,
    },
    "The Exit": {
        "prompt": """cinematic photography, massive blast door mechanism, heavy industrial locks,
emergency stairwell visible through reinforced window, security checkpoint abandoned,
surface access visible as goal, natural light visible at top of stairs, hope mixed with danger,
thriller aesthetic, final obstacle, tension at highest point, no people""",
        "negative": THRILLER_NEGATIVE,
    },
}

# Prop image configurations
PROP_IMAGES = {
    "subject-tag": {
        "prompt": """close-up photograph of white plastic hospital wristband on concrete surface,
black barcode with alphanumeric code 'A-7749', no name just number, slightly dirty,
harsh overhead lighting, clinical sterile atmosphere, high contrast, thriller aesthetic,
single object, no hands visible, evidence photography style""",
        "negative": THRILLER_NEGATIVE,
    },
    "vent-message": {
        "prompt": """close-up photograph of scratched message inside metal ventilation duct,
crude scratches reading 'TRUST NO ONE - THEY LISTEN', multiple scratch marks,
harsh lighting through vent slats, claustrophobic metal interior, thriller aesthetic,
single object, evidence photography style, high contrast""",
        "negative": THRILLER_NEGATIVE,
    },
    "keycard-green": {
        "prompt": """close-up photograph of green access keycard on concrete floor,
'LEVEL 2 ACCESS' printed on surface, magnetic stripe visible, slightly scuffed,
harsh fluorescent lighting, clinical sterile atmosphere, thriller aesthetic,
single object, evidence photography style, high contrast""",
        "negative": THRILLER_NEGATIVE,
    },
    "patrol-schedule": {
        "prompt": """close-up photograph of torn piece of paper with handwritten schedule,
times listed (02:00, 02:45, 03:30), 'PATROL ROTATION' header, coffee stain in corner,
harsh lighting, clinical atmosphere, thriller aesthetic, evidence photography style,
single object, no hands visible, high contrast""",
        "negative": THRILLER_NEGATIVE,
    },
    "specimen-log": {
        "prompt": """close-up photograph of damaged laboratory logbook, pages water-stained,
entries partially redacted with black marker, dates visible from months ago,
last entry has 'DISCONTINUED' stamped in red, scientific charts visible,
harsh lighting, thriller aesthetic, evidence photography style, biohazard atmosphere""",
        "negative": THRILLER_NEGATIVE,
    },
    "alex-note": {
        "prompt": """close-up photograph of folded paper with handwritten note,
clean precise handwriting reading partial text about 'door codes change',
slightly worn from being carried, harsh lighting, thriller aesthetic,
single object, evidence photography style, high contrast, trust building moment""",
        "negative": THRILLER_NEGATIVE,
    },
    "override-device": {
        "prompt": """close-up photograph of small jury-rigged electronic device,
exposed wires and circuitry, small LED light, modified security badge reader,
signs of improvised construction, harsh lighting, thriller aesthetic,
single object, evidence photography style, high contrast""",
        "negative": THRILLER_NEGATIVE,
    },
    "exit-map": {
        "prompt": """close-up photograph of crude hand-drawn facility map on paper,
corridors marked with X's and arrows, 'SURFACE ACCESS' circled, multiple annotations,
escape route marked in thick line, worn from handling, harsh lighting,
thriller aesthetic, evidence photography style, planning document""",
        "negative": THRILLER_NEGATIVE,
    },
}


async def generate_avatar(db: Database, storage: StorageService, image_service: ImageService):
    """Generate Alex's survival thriller avatar."""
    print("\n" + "=" * 60)
    print("GENERATING ALEX AVATAR")
    print("=" * 60)

    # Get Alex's character and kit
    char = await db.fetch_one(
        "SELECT id, name, active_avatar_kit_id, avatar_url FROM characters WHERE slug = 'alex'"
    )
    if not char:
        print("ERROR: Alex character not found! Run scaffold_the_blacksite.py first.")
        return False

    kit_id = char["active_avatar_kit_id"]
    if not kit_id:
        print("ERROR: No avatar kit found for Alex!")
        return False

    # Check if already has an avatar
    if char["avatar_url"]:
        print(f"Alex already has an avatar: {char['avatar_url'][:80]}...")
        print("Skipping avatar generation.")
        return True

    try:
        # Build the prompt
        full_prompt = f"{ALEX_APPEARANCE}, {ALEX_STYLE}, {THRILLER_QUALITY}"
        negative_prompt = THRILLER_NEGATIVE

        print(f"Generating with prompt: {full_prompt[:150]}...")

        # Generate image
        response = await image_service.generate(
            prompt=full_prompt,
            negative_prompt=negative_prompt,
            width=1024,
            height=1024,
        )

        if not response.images:
            print("ERROR: No images returned!")
            return False

        image_bytes = response.images[0]

        # Upload to storage
        asset_id = uuid.uuid4()
        storage_path = await storage.upload_avatar_asset(
            image_bytes=image_bytes,
            kit_id=uuid.UUID(str(kit_id)),
            asset_id=asset_id,
            asset_type="anchor_portrait",
        )

        # Create asset record
        await db.execute(
            """INSERT INTO avatar_assets (
                id, avatar_kit_id, asset_type, expression,
                storage_bucket, storage_path, source_type,
                generation_metadata, is_canonical, is_active,
                mime_type, file_size_bytes
            ) VALUES (
                :id, :kit_id, 'portrait', 'default',
                'avatars', :storage_path, 'ai_generated',
                :metadata, TRUE, TRUE,
                'image/png', :file_size
            )""",
            {
                "id": str(asset_id),
                "kit_id": str(kit_id),
                "storage_path": storage_path,
                "metadata": json.dumps({
                    "prompt": full_prompt[:500],
                    "model": response.model,
                    "series": "the-blacksite",
                }),
                "file_size": len(image_bytes),
            }
        )

        # Set as primary anchor
        await db.execute(
            """UPDATE avatar_kits
               SET primary_anchor_id = :asset_id, status = 'active', updated_at = NOW()
               WHERE id = :kit_id""",
            {"asset_id": str(asset_id), "kit_id": str(kit_id)}
        )

        # Update character avatar URL
        image_url = storage.get_public_url("avatars", storage_path)
        await db.execute(
            """UPDATE characters
               SET avatar_url = :avatar_url, updated_at = NOW()
               WHERE id = :id""",
            {"avatar_url": image_url, "id": str(char["id"])}
        )

        print(f"✓ Avatar generated successfully! ({response.latency_ms}ms)")
        print(f"  Storage path: {storage_path}")
        return True

    except Exception as e:
        print(f"✗ Failed to generate avatar: {e}")
        log.exception("Avatar generation failed")
        return False


async def generate_series_cover(db: Database, storage: StorageService, image_service: ImageService):
    """Generate The Blacksite series cover."""
    print("\n" + "=" * 60)
    print("GENERATING SERIES COVER")
    print("=" * 60)

    # Get series
    series = await db.fetch_one(
        "SELECT id, title, cover_image_url FROM series WHERE slug = 'the-blacksite'"
    )
    if not series:
        print("ERROR: Series not found! Run scaffold_the_blacksite.py first.")
        return False

    if series["cover_image_url"]:
        print(f"Series already has cover: {series['cover_image_url'][:80]}...")
        print("Skipping cover generation.")
        return True

    try:
        print(f"Generating cover for: {series['title']}")
        print(f"Prompt: {SERIES_COVER_PROMPT[:150]}...")

        # Generate 16:9 landscape cover
        response = await image_service.generate(
            prompt=SERIES_COVER_PROMPT,
            negative_prompt=SERIES_COVER_NEGATIVE,
            width=1024,
            height=576,  # 16:9 aspect ratio
        )

        if not response.images:
            print("ERROR: No images returned!")
            return False

        image_bytes = response.images[0]

        # Upload to storage
        series_id = series["id"]
        storage_path = f"series/{series_id}/cover.png"

        await storage._upload(
            bucket="scenes",
            path=storage_path,
            data=image_bytes,
            content_type="image/png",
        )

        # Update series with permanent public URL
        cover_url = storage.get_public_url("scenes", storage_path)
        await db.execute(
            """UPDATE series SET cover_image_url = :url, updated_at = NOW() WHERE id = :id""",
            {"url": cover_url, "id": str(series_id)}
        )

        print(f"✓ Series cover generated! ({response.latency_ms}ms)")
        print(f"  Storage path: {storage_path}")
        return True

    except Exception as e:
        print(f"✗ Failed to generate cover: {e}")
        log.exception("Cover generation failed")
        return False


async def generate_episode_backgrounds(db: Database, storage: StorageService, image_service: ImageService):
    """Generate background images for all episodes."""
    print("\n" + "=" * 60)
    print("GENERATING EPISODE BACKGROUNDS")
    print("=" * 60)

    # Get all episodes for the series
    series = await db.fetch_one(
        "SELECT id FROM series WHERE slug = 'the-blacksite'"
    )
    if not series:
        print("ERROR: Series not found!")
        return False

    episodes = await db.fetch_all(
        """SELECT id, title, episode_number, background_image_url
           FROM episode_templates
           WHERE series_id = :series_id
           ORDER BY episode_number""",
        {"series_id": str(series["id"])}
    )

    print(f"Found {len(episodes)} episodes")

    success_count = 0
    skip_count = 0
    fail_count = 0

    for ep in episodes:
        title = ep["title"]
        ep_id = ep["id"]
        ep_num = ep["episode_number"]

        if ep["background_image_url"]:
            print(f"  Ep {ep_num} ({title}): already has background, skipping")
            skip_count += 1
            continue

        # Get config from our background configs
        config = EPISODE_BACKGROUNDS.get(title)
        if not config:
            print(f"  Ep {ep_num} ({title}): no config found, skipping")
            fail_count += 1
            continue

        try:
            prompt = config["prompt"]
            negative = config.get("negative", THRILLER_NEGATIVE)

            print(f"  Generating Ep {ep_num}: {title}")
            print(f"    Prompt: {prompt[:100]}...")

            # Generate 9:16 portrait background
            response = await image_service.generate(
                prompt=prompt,
                negative_prompt=negative,
                width=576,
                height=1024,  # 9:16 aspect ratio
            )

            if not response.images:
                print(f"    ✗ No images returned")
                fail_count += 1
                continue

            image_bytes = response.images[0]

            # Upload to storage
            storage_path = f"episodes/{ep_id}/background.png"
            await storage._upload(
                bucket="scenes",
                path=storage_path,
                data=image_bytes,
                content_type="image/png",
            )

            # Update episode with permanent public URL
            bg_url = storage.get_public_url("scenes", storage_path)
            await db.execute(
                """UPDATE episode_templates SET background_image_url = :url, updated_at = NOW() WHERE id = :id""",
                {"url": bg_url, "id": str(ep_id)}
            )

            print(f"    ✓ Generated ({response.latency_ms}ms)")
            success_count += 1

            # Rate limiting
            if ep != episodes[-1]:
                print(f"    (waiting {GENERATION_DELAY}s...)")
                await asyncio.sleep(GENERATION_DELAY)

        except Exception as e:
            print(f"    ✗ Failed: {e}")
            log.exception(f"Background generation failed for {title}")
            fail_count += 1

    print(f"\nBackground generation complete:")
    print(f"  Success: {success_count}")
    print(f"  Skipped: {skip_count}")
    print(f"  Failed: {fail_count}")

    return fail_count == 0


async def generate_prop_images(db: Database, storage: StorageService, image_service: ImageService):
    """Generate prop images for all props."""
    print("\n" + "=" * 60)
    print("GENERATING PROP IMAGES")
    print("=" * 60)

    # Get all props for the series
    series = await db.fetch_one(
        "SELECT id FROM series WHERE slug = 'the-blacksite'"
    )
    if not series:
        print("ERROR: Series not found!")
        return False

    props = await db.fetch_all(
        """SELECT p.id, p.slug, p.name, p.image_url
           FROM props p
           JOIN episode_templates et ON p.episode_template_id = et.id
           WHERE et.series_id = :series_id
           ORDER BY et.episode_number, p.display_order""",
        {"series_id": str(series["id"])}
    )

    print(f"Found {len(props)} props")

    success_count = 0
    skip_count = 0
    fail_count = 0

    for prop in props:
        slug = prop["slug"]
        prop_id = prop["id"]
        name = prop["name"]

        if prop["image_url"]:
            print(f"  {name}: already has image, skipping")
            skip_count += 1
            continue

        # Get config from our prop configs
        config = PROP_IMAGES.get(slug)
        if not config:
            print(f"  {name}: no config found, skipping")
            fail_count += 1
            continue

        try:
            prompt = config["prompt"]
            negative = config.get("negative", THRILLER_NEGATIVE)

            print(f"  Generating prop: {name}")
            print(f"    Prompt: {prompt[:100]}...")

            # Generate square prop image
            response = await image_service.generate(
                prompt=prompt,
                negative_prompt=negative,
                width=768,
                height=768,
            )

            if not response.images:
                print(f"    ✗ No images returned")
                fail_count += 1
                continue

            image_bytes = response.images[0]

            # Upload to storage
            storage_path = f"props/{prop_id}/image.png"
            await storage._upload(
                bucket="scenes",
                path=storage_path,
                data=image_bytes,
                content_type="image/png",
            )

            # Update prop with permanent public URL
            img_url = storage.get_public_url("scenes", storage_path)
            await db.execute(
                """UPDATE props SET image_url = :url, updated_at = NOW() WHERE id = :id""",
                {"url": img_url, "id": str(prop_id)}
            )

            print(f"    ✓ Generated ({response.latency_ms}ms)")
            success_count += 1

            # Rate limiting
            if prop != props[-1]:
                print(f"    (waiting {GENERATION_DELAY}s...)")
                await asyncio.sleep(GENERATION_DELAY)

        except Exception as e:
            print(f"    ✗ Failed: {e}")
            log.exception(f"Prop image generation failed for {name}")
            fail_count += 1

    print(f"\nProp image generation complete:")
    print(f"  Success: {success_count}")
    print(f"  Skipped: {skip_count}")
    print(f"  Failed: {fail_count}")

    return fail_count == 0


async def activate_content(db: Database):
    """Activate the character, series, and episodes."""
    print("\n" + "=" * 60)
    print("ACTIVATING CONTENT")
    print("=" * 60)

    # Activate character
    await db.execute(
        "UPDATE characters SET status = 'active' WHERE slug = 'alex'"
    )
    print("  ✓ Alex character activated")

    # Activate series
    await db.execute(
        "UPDATE series SET status = 'active' WHERE slug = 'the-blacksite'"
    )
    print("  ✓ The Blacksite series activated")

    # Activate episodes
    await db.execute(
        """UPDATE episode_templates SET status = 'active'
           WHERE series_id = (SELECT id FROM series WHERE slug = 'the-blacksite')"""
    )
    print("  ✓ Episodes activated")


async def main(avatar_only: bool = False, backgrounds_only: bool = False, props_only: bool = False, skip_activation: bool = False):
    """Main generation function."""
    print("=" * 60)
    print("THE BLACKSITE - IMAGE GENERATION")
    print("=" * 60)

    db = Database(DATABASE_URL)
    await db.connect()
    storage = StorageService.get_instance()
    image_service = ImageService.get_client("replicate", "black-forest-labs/flux-1.1-pro")

    try:
        if avatar_only:
            await generate_avatar(db, storage, image_service)
        elif backgrounds_only:
            await generate_episode_backgrounds(db, storage, image_service)
        elif props_only:
            await generate_prop_images(db, storage, image_service)
        else:
            # Generate everything
            await generate_avatar(db, storage, image_service)
            await asyncio.sleep(GENERATION_DELAY)

            await generate_series_cover(db, storage, image_service)
            await asyncio.sleep(GENERATION_DELAY)

            await generate_episode_backgrounds(db, storage, image_service)
            await asyncio.sleep(GENERATION_DELAY)

            await generate_prop_images(db, storage, image_service)

            if not skip_activation:
                await activate_content(db)

        print("\n" + "=" * 60)
        print("GENERATION COMPLETE")
        print("=" * 60)

    finally:
        await db.disconnect()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate The Blacksite images")
    parser.add_argument("--avatar-only", action="store_true", help="Only generate avatar")
    parser.add_argument("--backgrounds-only", action="store_true", help="Only generate backgrounds")
    parser.add_argument("--props-only", action="store_true", help="Only generate prop images")
    parser.add_argument("--skip-activation", action="store_true", help="Don't activate content after generation")
    args = parser.parse_args()

    asyncio.run(main(
        avatar_only=args.avatar_only,
        backgrounds_only=args.backgrounds_only,
        props_only=args.props_only,
        skip_activation=args.skip_activation,
    ))
