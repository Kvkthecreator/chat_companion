"""Generate episode background images for all episode templates.

This script generates atmospheric background images based on each episode's
episode_frame prompt. Uses FLUX 1.1 Pro for high-quality scene generation.

Usage:
    cd substrate-api/api/src
    python -m app.scripts.generate_episode_backgrounds

Options:
    --dry-run: Show what would be generated without actually generating
    --episode-id: Generate for specific episode template ID only
    --character: Generate for specific character name only
"""

import asyncio
import logging
import os
import sys
from typing import Optional
from uuid import UUID

# Setup logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Load environment
from dotenv import load_dotenv
load_dotenv()


# Episode background style lock (no characters, atmospheric scenes)
BACKGROUND_STYLE = """masterpiece, best quality, highly detailed anime background,
beautiful atmospheric lighting, cinematic composition,
professional digital art, immersive environment,
detailed scenery, mood setting background, no characters, empty scene"""

BACKGROUND_NEGATIVE = """people, person, character, figure, human, face, eyes,
lowres, bad anatomy, text, watermark, signature, blurry,
multiple scenes, collage, border, frame"""


async def generate_background(
    episode_frame: str,
    character_id: UUID,
    episode_number: int,
    db,
    storage,
    image_service,
    dry_run: bool = False,
) -> Optional[str]:
    """Generate a single episode background.

    Args:
        episode_frame: Mood/scene description from episode_templates
        character_id: Character UUID
        episode_number: Episode number (0, 1, 2)
        db: Database connection
        storage: StorageService instance
        image_service: ImageService instance
        dry_run: If True, only log what would happen

    Returns:
        Storage path if successful, None otherwise.
        Note: Returns storage path (not signed URL) to avoid expiration issues.
    """
    # Build prompt for atmospheric background (no characters)
    full_prompt = f"{episode_frame}, {BACKGROUND_STYLE}"

    log.info(f"  Episode {episode_number}: {episode_frame[:60]}...")

    if dry_run:
        log.info(f"  [DRY RUN] Would generate: {full_prompt[:100]}...")
        return None

    try:
        # Generate 16:9 landscape background
        response = await image_service.generate(
            prompt=full_prompt,
            negative_prompt=BACKGROUND_NEGATIVE,
            width=1344,  # FLUX supports this for 16:9
            height=768,
        )

        if not response.images:
            log.error(f"  No image returned for episode {episode_number}")
            return None

        image_bytes = response.images[0]

        # Upload to storage
        storage_path = await storage.upload_episode_background(
            image_bytes=image_bytes,
            character_id=character_id,
            episode_number=episode_number,
        )

        # Return storage path (not signed URL) - signed URLs expire after 1 hour
        # Paths are converted to signed URLs on fetch
        log.info(f"  Generated background: {storage_path}")
        return storage_path

    except Exception as e:
        log.error(f"  Failed to generate episode {episode_number}: {e}")
        return None


async def main(dry_run: bool = False, episode_id: str = None, character_name: str = None):
    """Generate backgrounds for all episode templates."""

    # Initialize services
    from app.deps import get_db
    from app.services.storage import StorageService
    from app.services.image import ImageService

    db = await get_db()
    storage = StorageService.get_instance()

    # Use FLUX 1.1 Pro for high quality backgrounds
    image_service = ImageService.get_client("replicate", "black-forest-labs/flux-1.1-pro")

    log.info("=" * 60)
    log.info("Episode Background Generation")
    log.info("=" * 60)

    if dry_run:
        log.info("DRY RUN MODE - No images will be generated")

    # Build query based on filters
    query = """
        SELECT et.id, et.character_id, et.episode_number, et.title,
               et.episode_frame, et.background_image_url, c.name
        FROM episode_templates et
        JOIN characters c ON c.id = et.character_id
        WHERE et.episode_frame IS NOT NULL
        AND et.episode_frame != ''
    """
    params = {}

    if episode_id:
        query += " AND et.id = :episode_id"
        params["episode_id"] = episode_id

    if character_name:
        query += " AND c.name = :character_name"
        params["character_name"] = character_name

    query += " ORDER BY c.name, et.episode_number"

    episodes = await db.fetch_all(query, params)

    log.info(f"Found {len(episodes)} episode templates to process")

    # Track stats
    generated = 0
    skipped = 0
    failed = 0

    current_character = None

    for row in episodes:
        ep = dict(row)

        # Print character header
        if ep["name"] != current_character:
            current_character = ep["name"]
            log.info(f"\n{current_character}:")

        # Skip if already has background
        if ep.get("background_image_url") and not dry_run:
            log.info(f"  Episode {ep['episode_number']} ({ep['title']}): Already has background, skipping")
            skipped += 1
            continue

        # Generate background (returns storage path, not signed URL)
        storage_path = await generate_background(
            episode_frame=ep["episode_frame"],
            character_id=UUID(ep["character_id"]),
            episode_number=ep["episode_number"],
            db=db,
            storage=storage,
            image_service=image_service,
            dry_run=dry_run,
        )

        if storage_path:
            # Update database with storage path (not signed URL)
            await db.execute(
                """UPDATE episode_templates
                   SET background_image_url = :path, updated_at = NOW()
                   WHERE id = :id""",
                {"path": storage_path, "id": str(ep["id"])}
            )
            generated += 1
        elif not dry_run:
            failed += 1

    log.info("\n" + "=" * 60)
    log.info("Generation Complete")
    log.info(f"  Generated: {generated}")
    log.info(f"  Skipped (existing): {skipped}")
    log.info(f"  Failed: {failed}")
    log.info("=" * 60)

    # Cleanup
    await image_service.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate episode background images")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be generated")
    parser.add_argument("--episode-id", type=str, help="Generate for specific episode ID")
    parser.add_argument("--character", type=str, help="Generate for specific character name")

    args = parser.parse_args()

    asyncio.run(main(
        dry_run=args.dry_run,
        episode_id=args.episode_id,
        character_name=args.character,
    ))
