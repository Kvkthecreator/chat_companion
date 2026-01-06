"""Generate images for Locked In series.

This script generates:
1. Riley's character avatar (romantic comedy style)
2. Series cover image
3. Episode background images (4 episodes)
4. Prop images (8 props)

Usage:
    python -m app.scripts.generate_locked_in_images
    python -m app.scripts.generate_locked_in_images --avatar-only
    python -m app.scripts.generate_locked_in_images --backgrounds-only
    python -m app.scripts.generate_locked_in_images --props-only

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
# ROMANTIC COMEDY STYLE CONSTANTS
# =============================================================================

ROMCOM_STYLE = "cinematic photography, warm golden lighting, intimate atmosphere, soft shadows, romantic aesthetic"
ROMCOM_QUALITY = "masterpiece, best quality, highly detailed, beautiful lighting, romantic mood"
ROMCOM_NEGATIVE = "anime, cartoon, horror, dark shadows, harsh lighting, ugly, low quality, blurry, text, watermark, multiple people"

# Riley's appearance for avatar generation
RILEY_APPEARANCE = """young attractive person mid-20s with warm inviting smile, expressive eyes with mischievous glint,
casual chic fashion, slightly messy hair that looks effortlessly good, comfortable confident posture,
playful knowing expression, dimples when smiling, looking at viewer with flirtatious curiosity"""

RILEY_STYLE = """cinematic portrait photography, warm golden hour lighting, soft background blur,
romantic comedy aesthetic, charming and approachable, shallow depth of field, single subject portrait,
warm color grade, flattering lighting, candid natural pose"""

# Series cover prompt
SERIES_COVER_PROMPT = """cinematic photography, close-up of two hands almost touching in small confined space,
warm intimate lighting, romantic tension visible in the near-touch, soft focus background,
small window visible with warm light streaming in, forced proximity atmosphere,
romantic comedy aesthetic, masterpiece, best quality, no faces visible just hands"""

SERIES_COVER_NEGATIVE = """anime, cartoon, horror, dark, ugly, low quality, blurry,
text, watermark, faces, portraits, full bodies, cold lighting"""

# Episode background configurations
EPISODE_BACKGROUNDS = {
    "The Elevator": {
        "prompt": """cinematic photography, inside modern building elevator, mirrored walls,
soft overhead lighting, floor buttons panel visible, small confined space,
warm ambient light, romantic comedy aesthetic, intimate forced proximity atmosphere,
no people, sense of being stuck together, warm color grade""",
        "negative": ROMCOM_NEGATIVE,
    },
    "The Storage Room": {
        "prompt": """cinematic photography, cozy office storage room, shelving with supplies,
small window with afternoon sunlight streaming in, warm dusty atmosphere,
boxes creating intimate alcove, romantic hideaway feeling, forced proximity,
no people, romantic comedy aesthetic, warm golden lighting""",
        "negative": ROMCOM_NEGATIVE,
    },
    "The Cabin": {
        "prompt": """cinematic photography, rustic cabin interior during snowstorm,
large stone fireplace with dancing flames, soft warm lighting, window showing snow,
cozy blankets and pillows, single couch near fire, intimate romantic atmosphere,
no people, romantic winter aesthetic, warm golden glow from fire""",
        "negative": ROMCOM_NEGATIVE,
    },
    "The Escape Room": {
        "prompt": """cinematic photography, themed escape room interior, mysterious clues visible,
ambient lighting with colorful accents, puzzles on walls, vintage aesthetic,
locked door visible, playful mysterious atmosphere, romantic comedy lighting,
no people, sense of adventure and fun, warm inviting colors""",
        "negative": ROMCOM_NEGATIVE,
    },
}

# Prop image configurations
PROP_IMAGES = {
    "phone-dying": {
        "prompt": """close-up photograph of smartphone showing 3% battery warning,
screen slightly cracked, warm ambient lighting, intimate atmosphere,
single object on wooden surface, romantic comedy aesthetic, soft focus background,
evidence photography style but warm and inviting""",
        "negative": ROMCOM_NEGATIVE,
    },
    "elevator-playlist": {
        "prompt": """close-up photograph of smartphone showing music playlist titled 'stuck with you',
earbuds tangled nearby, warm lighting, romantic comedy aesthetic,
single object, soft focus background, intimate sharing moment implied,
cozy warm color grade""",
        "negative": ROMCOM_NEGATIVE,
    },
    "old-photo": {
        "prompt": """close-up photograph of slightly worn polaroid showing college party scene,
two figures close together in background, warm nostalgic lighting,
single object on wooden surface, romantic comedy aesthetic, memory moment,
soft edges, warm color grade, sentimental feeling""",
        "negative": ROMCOM_NEGATIVE,
    },
    "supply-closet-key": {
        "prompt": """close-up photograph of old brass key on wooden shelf,
warm afternoon light from small window, dust particles visible in light,
single object, romantic comedy aesthetic, possibility and escape,
warm golden lighting, soft focus background""",
        "negative": ROMCOM_NEGATIVE,
    },
    "shared-sweater": {
        "prompt": """close-up photograph of soft cozy sweater draped over chair arm,
warm firelight illuminating fabric, snowfall visible through window,
single object, romantic comedy aesthetic, intimacy and warmth implied,
soft golden lighting, cabin romantic atmosphere""",
        "negative": ROMCOM_NEGATIVE,
    },
    "confession-note": {
        "prompt": """close-up photograph of folded paper note with visible handwriting,
warm firelight illuminating paper, soft romantic atmosphere,
single object on blanket, romantic comedy aesthetic, vulnerable moment,
warm golden lighting, confession and honesty implied""",
        "negative": ROMCOM_NEGATIVE,
    },
    "puzzle-clue": {
        "prompt": """close-up photograph of escape room puzzle piece with cryptic symbols,
colorful ambient lighting, mysterious but playful atmosphere,
single object on table, romantic comedy adventure aesthetic,
fun and flirtatious energy, warm undertones""",
        "negative": ROMCOM_NEGATIVE,
    },
    "winner-prize": {
        "prompt": """close-up photograph of small trophy or prize with 'CHAMPIONS' text,
warm celebratory lighting, confetti visible, joyful atmosphere,
single object, romantic comedy aesthetic, victory and celebration,
warm golden lighting, shared accomplishment feeling""",
        "negative": ROMCOM_NEGATIVE,
    },
}


async def generate_avatar(db: Database, storage: StorageService, image_service: ImageService):
    """Generate Riley's romantic comedy avatar."""
    print("\n" + "=" * 60)
    print("GENERATING RILEY AVATAR")
    print("=" * 60)

    # Get Riley's character and kit
    char = await db.fetch_one(
        "SELECT id, name, active_avatar_kit_id, avatar_url FROM characters WHERE slug = 'riley'"
    )
    if not char:
        print("ERROR: Riley character not found! Run scaffold_locked_in.py first.")
        return False

    kit_id = char["active_avatar_kit_id"]
    if not kit_id:
        print("ERROR: No avatar kit found for Riley!")
        return False

    # Check if already has an avatar
    if char["avatar_url"]:
        print(f"Riley already has an avatar: {char['avatar_url'][:80]}...")
        print("Skipping avatar generation.")
        return True

    try:
        # Build the prompt
        full_prompt = f"{RILEY_APPEARANCE}, {RILEY_STYLE}, {ROMCOM_QUALITY}"
        negative_prompt = ROMCOM_NEGATIVE

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
                    "series": "locked-in",
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
    """Generate Locked In series cover."""
    print("\n" + "=" * 60)
    print("GENERATING SERIES COVER")
    print("=" * 60)

    # Get series
    series = await db.fetch_one(
        "SELECT id, title, cover_image_url FROM series WHERE slug = 'locked-in'"
    )
    if not series:
        print("ERROR: Series not found! Run scaffold_locked_in.py first.")
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
        "SELECT id FROM series WHERE slug = 'locked-in'"
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
            negative = config.get("negative", ROMCOM_NEGATIVE)

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
        "SELECT id FROM series WHERE slug = 'locked-in'"
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
            negative = config.get("negative", ROMCOM_NEGATIVE)

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
        "UPDATE characters SET status = 'active' WHERE slug = 'riley'"
    )
    print("  ✓ Riley character activated")

    # Activate series
    await db.execute(
        "UPDATE series SET status = 'active' WHERE slug = 'locked-in'"
    )
    print("  ✓ Locked In series activated")

    # Activate episodes
    await db.execute(
        """UPDATE episode_templates SET status = 'active'
           WHERE series_id = (SELECT id FROM series WHERE slug = 'locked-in')"""
    )
    print("  ✓ Episodes activated")


async def main(avatar_only: bool = False, backgrounds_only: bool = False, props_only: bool = False, skip_activation: bool = False):
    """Main generation function."""
    print("=" * 60)
    print("LOCKED IN - IMAGE GENERATION")
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
    parser = argparse.ArgumentParser(description="Generate Locked In images")
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
