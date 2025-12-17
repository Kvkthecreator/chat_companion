"""Generate Series Images Script.

Generates series cover and episode background images using the
corrected prompt architecture (docs/IMAGE_STRATEGY.md).

Key Changes from Previous Version:
- NO visual style cascade - each episode has explicit config
- Subject-first prompt ordering
- Purpose-specific prompts (no character styling in backgrounds)
- Series cover now includes character in scene

Usage:
    cd substrate-api/api/src
    FANTAZY_DB_PASSWORD='...' REPLICATE_API_TOKEN='...' python -m app.scripts.generate_series_images --series-slug stolen-moments

Options:
    --series-slug: Series slug to generate images for
    --cover-only: Only generate series cover
    --backgrounds-only: Only generate episode backgrounds
    --dry-run: Show prompts without generating
    --skip-existing: Skip if image already exists
"""

import asyncio
import argparse
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from databases import Database

from app.services.content_image_generation import (
    ContentImageGenerator,
    ALL_EPISODE_BACKGROUNDS,
    build_episode_background_prompt,
    SERIES_COVER_PROMPTS,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)


# =============================================================================
# Database Helpers
# =============================================================================

async def get_database() -> Database:
    """Get database connection."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        db_host = os.getenv("FANTAZY_DB_HOST", "aws-1-ap-northeast-1.pooler.supabase.com")
        db_port = os.getenv("FANTAZY_DB_PORT", "5432")
        db_name = os.getenv("FANTAZY_DB_NAME", "postgres")
        db_user = os.getenv("FANTAZY_DB_USER", "postgres.lfwhdzwbikyzalpbwfnd")
        db_password = os.getenv("FANTAZY_DB_PASSWORD", "")

        if not db_password:
            raise ValueError("FANTAZY_DB_PASSWORD environment variable required")

        database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    db = Database(database_url)
    await db.connect()
    return db


async def fetch_series(db: Database, series_slug: str) -> Dict[str, Any]:
    """Fetch series data."""
    query = """
        SELECT id, title, slug, cover_image_url
        FROM series
        WHERE slug = :slug
    """
    row = await db.fetch_one(query, {"slug": series_slug})
    if not row:
        raise ValueError(f"Series '{series_slug}' not found")
    return dict(row)


async def fetch_episodes(db: Database, series_id: str) -> list:
    """Fetch episodes for a series."""
    query = """
        SELECT id, episode_number, title, situation, background_image_url
        FROM episode_templates
        WHERE series_id = :series_id
        ORDER BY episode_number
    """
    rows = await db.fetch_all(query, {"series_id": series_id})
    return [dict(row) for row in rows]


async def fetch_character_anchor(db: Database, series_slug: str) -> Optional[bytes]:
    """Fetch the primary character's avatar anchor image for series cover generation."""
    # Get the featured character for the series
    query = """
        SELECT c.avatar_url
        FROM series s
        JOIN episode_templates et ON et.series_id = s.id AND et.episode_number = 0
        JOIN characters c ON c.id = et.character_id
        WHERE s.slug = :slug
    """
    row = await db.fetch_one(query, {"slug": series_slug})
    if not row or not row["avatar_url"]:
        return None

    # Download the avatar image
    import httpx
    avatar_url = row["avatar_url"]

    # If it's a storage path, convert to signed URL
    if not avatar_url.startswith("http"):
        from app.services.storage import StorageService
        storage = StorageService.get_instance()
        avatar_url = await storage.get_signed_url("avatars", avatar_url)

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(avatar_url)
        response.raise_for_status()
        return response.content


# =============================================================================
# Storage Helpers
# =============================================================================

async def upload_to_supabase(image_bytes: bytes, storage_path: str) -> str:
    """Upload image bytes to Supabase Storage."""
    import httpx
    from app.services.storage import StorageService

    storage = StorageService.get_instance()

    url = f"{storage.supabase_url}/storage/v1/object/scenes/{storage_path}"
    headers = {
        "Authorization": f"Bearer {storage.service_role_key}",
        "Content-Type": "image/png",
        "x-upsert": "true",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, headers=headers, content=image_bytes)
        if response.status_code not in (200, 201):
            log.error(f"Storage upload failed: {response.status_code} {response.text}")
            response.raise_for_status()

    log.info(f"Uploaded to scenes/{storage_path}")
    return storage_path


async def update_series_cover(db: Database, series_id: str, storage_path: str):
    """Update series cover_image_url."""
    await db.execute(
        "UPDATE series SET cover_image_url = :path, updated_at = NOW() WHERE id = :id",
        {"path": storage_path, "id": series_id}
    )


async def update_episode_background(db: Database, episode_id: str, storage_path: str):
    """Update episode background_image_url."""
    await db.execute(
        "UPDATE episode_templates SET background_image_url = :path WHERE id = :id",
        {"path": storage_path, "id": episode_id}
    )


# =============================================================================
# Generation Functions
# =============================================================================

async def generate_series_cover(
    db: Database,
    series_data: Dict[str, Any],
    dry_run: bool = False,
    skip_existing: bool = False,
) -> Optional[Dict[str, Any]]:
    """Generate series cover with character in scene."""
    series_slug = series_data["slug"]

    if skip_existing and series_data.get("cover_image_url"):
        log.info("Series cover already exists, skipping")
        return None

    # Get series-specific cover prompt builder
    cover_builder = SERIES_COVER_PROMPTS.get(series_slug)
    if not cover_builder:
        log.error(f"No cover prompt builder found for series '{series_slug}'")
        return None

    # Build prompt
    prompt, negative = cover_builder()

    log.info("\n" + "="*60)
    log.info("SERIES COVER")
    log.info("="*60)
    log.info(f"Prompt:\n{prompt}\n")
    log.info(f"Negative:\n{negative}\n")

    if dry_run:
        log.info("[DRY RUN] Would generate series cover")
        return {"dry_run": True, "prompt": prompt}

    # Generate using text-to-image
    generator = ContentImageGenerator()

    # Use the generic generate method with our custom prompt
    from app.services.content_image_generation import ASPECT_RATIOS, ImageType, SERIES_COVER_NEGATIVE
    width, height = ASPECT_RATIOS[ImageType.SERIES_COVER]

    service = generator._get_service()
    result = await service.generate(
        prompt=prompt,
        negative_prompt=negative,
        width=width,
        height=height,
    )

    # Package result in expected format
    result = {
        "images": result.images,
        "prompt": prompt,
        "negative_prompt": negative,
        "model": result.model,
        "latency_ms": result.latency_ms,
    }

    if result.get("images"):
        # Upload to Supabase
        storage_path = f"series/{series_slug}/cover.png"
        await upload_to_supabase(result["images"][0], storage_path)
        await update_series_cover(db, str(series_data["id"]), storage_path)
        log.info(f"Series cover saved to: {storage_path}")
        return {
            "storage_path": storage_path,
            "prompt": result["prompt"],
            "latency_ms": result.get("latency_ms"),
        }

    return None


async def generate_episode_backgrounds(
    db: Database,
    series_data: Dict[str, Any],
    episodes: list,
    dry_run: bool = False,
    skip_existing: bool = False,
) -> list:
    """Generate backgrounds for all episodes."""
    series_slug = series_data["slug"]
    generator = ContentImageGenerator()
    results = []

    log.info("\n" + "="*60)
    log.info(f"EPISODE BACKGROUNDS ({len(episodes)} episodes)")
    log.info("="*60)

    for ep in episodes:
        title = ep["title"]
        ep_id = str(ep["id"])
        ep_num = ep["episode_number"]

        log.info(f"\n--- Episode {ep_num}: {title} ---")

        if skip_existing and ep.get("background_image_url"):
            log.info("Background already exists, skipping")
            continue

        # Get episode config (from combined lookup in service module)
        ep_config = ALL_EPISODE_BACKGROUNDS.get(title)

        if not ep_config:
            log.warning(f"No config found for '{title}', using situation as fallback")
            ep_config = None
            fallback = ep.get("situation")
        else:
            fallback = None

        # Build and show prompt
        prompt, negative = build_episode_background_prompt(
            episode_title=title,
            episode_config=ep_config,
            fallback_situation=fallback,
        )

        log.info(f"Prompt:\n{prompt}\n")

        if dry_run:
            log.info("[DRY RUN] Would generate background")
            results.append({"episode": title, "dry_run": True, "prompt": prompt})
            continue

        # Generate
        try:
            result = await generator.generate_episode_background(
                episode_title=title,
                episode_config=ep_config,
                fallback_situation=fallback,
            )

            if result.get("images"):
                # Upload to Supabase
                safe_title = title.lower().replace(" ", "_").replace("'", "")
                storage_path = f"series/{series_slug}/episodes/ep{ep_num:02d}_{safe_title}.png"
                await upload_to_supabase(result["images"][0], storage_path)
                await update_episode_background(db, ep_id, storage_path)
                log.info(f"Background saved to: {storage_path}")

                results.append({
                    "episode": title,
                    "episode_number": ep_num,
                    "storage_path": storage_path,
                    "prompt": result["prompt"],
                    "latency_ms": result.get("latency_ms"),
                    "success": True,
                })
            else:
                results.append({
                    "episode": title,
                    "success": False,
                    "error": "No images returned",
                })

        except Exception as e:
            log.error(f"Failed to generate background for '{title}': {e}")
            results.append({
                "episode": title,
                "success": False,
                "error": str(e),
            })

        # Add delay between generations to avoid rate limiting
        await asyncio.sleep(3)

    return results


# =============================================================================
# Main
# =============================================================================

async def main():
    parser = argparse.ArgumentParser(description="Generate series images")
    parser.add_argument("--series-slug", required=True, help="Series slug")
    parser.add_argument("--cover-only", action="store_true", help="Only generate cover")
    parser.add_argument("--backgrounds-only", action="store_true", help="Only generate backgrounds")
    parser.add_argument("--dry-run", action="store_true", help="Show prompts without generating")
    parser.add_argument("--skip-existing", action="store_true", help="Skip if image exists")
    args = parser.parse_args()

    log.info("="*60)
    log.info(f"SERIES IMAGE GENERATION: {args.series_slug}")
    log.info("="*60)
    if args.dry_run:
        log.info("MODE: DRY RUN - No images will be generated")
    log.info(f"Architecture: docs/IMAGE_STRATEGY.md (corrected)")
    log.info("")

    db = await get_database()

    try:
        # Fetch series data
        series_data = await fetch_series(db, args.series_slug)
        log.info(f"Series: {series_data['title']}")

        results = {
            "series": args.series_slug,
            "timestamp": datetime.now().isoformat(),
            "cover": None,
            "backgrounds": [],
        }

        # Generate cover
        if not args.backgrounds_only:
            cover_result = await generate_series_cover(
                db=db,
                series_data=series_data,
                dry_run=args.dry_run,
                skip_existing=args.skip_existing,
            )
            results["cover"] = cover_result

        # Generate backgrounds
        if not args.cover_only:
            episodes = await fetch_episodes(db, str(series_data["id"]))
            log.info(f"Found {len(episodes)} episodes")

            background_results = await generate_episode_backgrounds(
                db=db,
                series_data=series_data,
                episodes=episodes,
                dry_run=args.dry_run,
                skip_existing=args.skip_existing,
            )
            results["backgrounds"] = background_results

        # Summary
        log.info("\n" + "="*60)
        log.info("GENERATION COMPLETE")
        log.info("="*60)

        if results["cover"]:
            log.info(f"Cover: {results['cover'].get('storage_path', 'dry_run')}")

        successful = [b for b in results["backgrounds"] if b.get("success")]
        failed = [b for b in results["backgrounds"] if not b.get("success") and not b.get("dry_run")]

        log.info(f"Backgrounds: {len(successful)} generated, {len(failed)} failed")

        if failed:
            log.error("Failed episodes:")
            for f in failed:
                log.error(f"  - {f['episode']}: {f.get('error')}")

    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
