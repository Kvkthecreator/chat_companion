"""Generate Avatars for New Genre Characters.

Generates avatar images for characters that have avatar_kits with prompts
but no actual generated images yet.

Target characters:
- Hana (Corner Cafe - cozy)
- Yuna (Debate Partners - GL)
- Lord Ashworth (Duke's Third Son - historical)
- Dr. Seong (Session Notes - psychological)
- Daniel Park (Corner Office - workplace)

Each character has unique appearance_prompt and style_prompt in their avatar_kit
that ensures visual differentiation.

Usage:
    cd substrate-api/api/src
    REPLICATE_API_TOKEN='...' python -m app.scripts.generate_new_genre_avatars
    REPLICATE_API_TOKEN='...' python -m app.scripts.generate_new_genre_avatars --character hana-cafe
    REPLICATE_API_TOKEN='...' python -m app.scripts.generate_new_genre_avatars --dry-run
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

from typing import Optional
from databases import Database
from app.services.image import ImageService
from app.services.storage import StorageService

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres.lfwhdzwbikyzalpbwfnd:42PJb25YJhJHJdkl@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres"
)

# Rate limiting between generations
GENERATION_DELAY = 5

# Characters to generate avatars for (those missing avatars)
TARGET_CHARACTERS = [
    "hana-cafe",      # Corner Cafe - cozy
    "yuna-rival",     # Debate Partners - GL
    "lord-ashworth",  # Duke's Third Son - historical
    "dr-seong",       # Session Notes - psychological
    "daniel-park",    # Corner Office - workplace
]


async def fetch_character_with_kit(db: Database, char_slug: str) -> Optional[dict]:
    """Fetch character with their avatar kit prompts."""
    query = """
        SELECT
            c.id, c.name, c.slug, c.avatar_url,
            c.active_avatar_kit_id,
            ak.appearance_prompt, ak.style_prompt, ak.negative_prompt
        FROM characters c
        LEFT JOIN avatar_kits ak ON ak.id = c.active_avatar_kit_id
        WHERE c.slug = :slug
    """
    row = await db.fetch_one(query, {"slug": char_slug})
    if not row:
        return None
    return dict(row)


async def generate_avatar(
    db: Database,
    storage: StorageService,
    image_service: ImageService,
    char_data: dict,
    dry_run: bool = False,
) -> bool:
    """Generate avatar for a character using their avatar_kit prompts."""
    char_name = char_data["name"]
    char_slug = char_data["slug"]
    char_id = char_data["id"]
    kit_id = char_data["active_avatar_kit_id"]

    print(f"\n{'=' * 60}")
    print(f"GENERATING AVATAR: {char_name} ({char_slug})")
    print(f"{'=' * 60}")

    # Check if already has avatar
    if char_data["avatar_url"]:
        print(f"Already has avatar: {char_data['avatar_url'][:60]}...")
        print("Skipping.")
        return True

    # Check for avatar kit
    if not kit_id:
        print("ERROR: No avatar kit found!")
        return False

    # Get prompts from avatar kit
    appearance_prompt = char_data.get("appearance_prompt")
    style_prompt = char_data.get("style_prompt")
    negative_prompt = char_data.get("negative_prompt", "low quality, blurry, deformed, multiple people, text, watermark")

    if not appearance_prompt:
        print("ERROR: No appearance_prompt in avatar kit!")
        return False

    # Build full prompt
    full_prompt = f"{appearance_prompt}, {style_prompt}" if style_prompt else appearance_prompt

    print(f"Appearance: {appearance_prompt[:100]}...")
    print(f"Style: {style_prompt[:80]}..." if style_prompt else "Style: (none)")

    if dry_run:
        print("[DRY RUN] Would generate avatar with above prompts")
        return True

    try:
        # Generate image
        print("Generating...")
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
                    "character": char_slug,
                }),
                "file_size": len(image_bytes),
            }
        )

        # Set as primary anchor on kit
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
            {"avatar_url": image_url, "id": str(char_id)}
        )

        print(f"Avatar generated! ({response.latency_ms}ms)")
        print(f"Storage path: {storage_path}")
        return True

    except Exception as e:
        print(f"FAILED: {e}")
        log.exception("Avatar generation failed")
        return False


async def main(character_slug: Optional[str] = None, dry_run: bool = False):
    """Main generation function."""
    print("=" * 60)
    print("NEW GENRE CHARACTER AVATAR GENERATION")
    print("=" * 60)
    print("Generates avatars using unique prompts from avatar_kits")
    print("Each character has distinct appearance/style for differentiation")

    if dry_run:
        print("\n[DRY RUN MODE - No images will be generated]")

    db = Database(DATABASE_URL)
    await db.connect()
    storage = StorageService.get_instance()
    image_service = ImageService.get_client("replicate", "black-forest-labs/flux-1.1-pro")

    # Determine which characters to process
    characters_to_process = [character_slug] if character_slug else TARGET_CHARACTERS

    try:
        success_count = 0
        skip_count = 0
        fail_count = 0

        for i, char_slug in enumerate(characters_to_process):
            char_data = await fetch_character_with_kit(db, char_slug)

            if not char_data:
                print(f"\nERROR: Character '{char_slug}' not found!")
                fail_count += 1
                continue

            result = await generate_avatar(db, storage, image_service, char_data, dry_run)

            if result:
                if char_data["avatar_url"]:
                    skip_count += 1
                else:
                    success_count += 1
            else:
                fail_count += 1

            # Rate limiting between generations (not on last one)
            if not dry_run and i < len(characters_to_process) - 1 and not char_data["avatar_url"]:
                print(f"\n(Waiting {GENERATION_DELAY}s...)")
                await asyncio.sleep(GENERATION_DELAY)

        # Summary
        print("\n" + "=" * 60)
        print("GENERATION COMPLETE")
        print("=" * 60)
        print(f"Success: {success_count}")
        print(f"Skipped (already had avatar): {skip_count}")
        print(f"Failed: {fail_count}")

    finally:
        await db.disconnect()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate avatars for new genre characters")
    parser.add_argument("--character", help="Generate for specific character slug only")
    parser.add_argument("--dry-run", action="store_true", help="Show prompts without generating")
    args = parser.parse_args()

    asyncio.run(main(
        character_slug=args.character,
        dry_run=args.dry_run,
    ))
