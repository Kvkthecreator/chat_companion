"""Generate anchor avatars for Genre 02 characters.

This script creates hero avatars (anchor_portrait) for all Genre 02
psychological thriller characters using FLUX image generation.

Usage:
    python -m app.scripts.generate_genre02_avatars

Environment variables required:
    REPLICATE_API_TOKEN - Replicate API key
    SUPABASE_URL - Supabase project URL
    SUPABASE_SERVICE_ROLE_KEY - Supabase service role key
"""

import asyncio
import json
import logging
import os
import sys
import uuid
from typing import Optional

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Set environment variables if not present (for local dev)
if not os.getenv("SUPABASE_URL"):
    os.environ["SUPABASE_URL"] = "https://lfwhdzwbikyzalpbwfnd.supabase.co"
if not os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
    os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imxmd2hkendiaWt5emFscGJ3Zm5kIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NTQzMjQ0NCwiZXhwIjoyMDgxMDA4NDQ0fQ.s2ljzY1YQkz-WTZvRa-_qzLnW1zhoL012Tn2vPOigd0"

# Rate limiting delay between generations (seconds)
GENERATION_DELAY = 5

from databases import Database
from app.services.avatar_generation import (
    assemble_avatar_prompt,
    FANTAZY_STYLE_LOCK,
    FANTAZY_NEGATIVE_PROMPT,
)
from app.services.image import ImageService
from app.services.storage import StorageService

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres.lfwhdzwbikyzalpbwfnd:42PJb25YJhJHJdkl@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres"
)

# Admin user ID for created_by
ADMIN_USER_ID = "82633300-3cfd-4e32-b141-046d0edd616b"

# =============================================================================
# Genre 02 Character Appearance Descriptions
# Physical traits for each character to make them visually distinct
# =============================================================================

GENRE_02_APPEARANCES = {
    "cassian": "handsome man in his late 30s, sharp features, dark slicked-back hair, grey eyes, clean shaven, expensive taste",
    "vera": "striking woman in her late 20s, Eastern European features, platinum blonde pixie cut, green eyes, high cheekbones",
    "dr-marcus-webb": "disheveled man in his 50s, salt-and-pepper beard, tired intelligent eyes behind wire-rim glasses, academic look",
    "maren": "athletic woman in her early 30s, Nordic features, short auburn hair, steel-blue eyes, practical no-nonsense look",
    "elias": "everyman in his 40s, average build, brown hair with grey at temples, worried brown eyes, forgettable face",
    "dr-iris-chen": "sharp woman in her 30s, East Asian features, sleek black hair in bun, dark analytical eyes, elegant",
    "roman": "fit man in his early 30s, military bearing, buzz cut dark hair, intense hazel eyes, subtle scars",
    "nadia": "polished woman in her late 30s, Mediterranean features, dark wavy hair, brown eyes with hidden depths, expensive jewelry",
    "dr-samuel-cross": "distinguished man in his 60s, silver hair swept back, commanding blue eyes, patrician features, gravitas",
    "zero": "androgynous figure of uncertain age, forgettable features, eyes that shift color in different light, shadow",
}


async def generate_avatars():
    """Generate anchor avatars for all Genre 02 characters."""
    db = Database(DATABASE_URL)
    await db.connect()
    storage = StorageService.get_instance()

    try:
        # Get all Genre 02 characters without avatar kits
        rows = await db.fetch_all("""
            SELECT id, name, slug, archetype, boundaries
            FROM characters
            WHERE genre = 'psychological_thriller'
              AND active_avatar_kit_id IS NULL
            ORDER BY name
        """)

        print(f"\n{'='*60}")
        print("GENERATING GENRE 02 ANCHOR AVATARS")
        print(f"{'='*60}")
        print(f"Found {len(rows)} characters needing avatars\n")

        if not rows:
            print("All Genre 02 characters already have avatar kits!")
            return

        # Initialize image service (FLUX Pro for initial generation)
        image_service = ImageService.get_client("replicate", "black-forest-labs/flux-1.1-pro")

        success_count = 0
        fail_count = 0

        for row in rows:
            char = dict(row)
            char_id = char["id"]
            name = char["name"]
            slug = char["slug"]
            archetype = char["archetype"]

            print(f"Generating avatar for {name} ({archetype})...")

            # Parse boundaries
            boundaries = char.get("boundaries", {})
            if isinstance(boundaries, str):
                boundaries = json.loads(boundaries)

            # Get appearance description
            appearance = GENRE_02_APPEARANCES.get(slug, "attractive person, distinctive features")

            try:
                # Assemble prompt
                prompt_assembly = assemble_avatar_prompt(
                    name=name,
                    archetype=archetype,
                    role_frame=archetype,  # Use archetype as role_frame for thriller
                    boundaries=boundaries,
                    content_rating="sfw",
                    custom_appearance=appearance,
                )

                log.info(f"Prompt for {name}: {prompt_assembly.full_prompt[:200]}...")

                # Generate image
                response = await image_service.generate(
                    prompt=prompt_assembly.full_prompt,
                    negative_prompt=prompt_assembly.negative_prompt,
                    width=1024,
                    height=1024,
                )

                if not response.images:
                    print(f"  ✗ No images returned for {name}")
                    fail_count += 1
                    continue

                image_bytes = response.images[0]

                # Create avatar kit
                kit_id = uuid.uuid4()
                await db.execute(
                    """INSERT INTO avatar_kits (
                        id, character_id, created_by, name,
                        appearance_prompt, style_prompt, negative_prompt,
                        status, is_default
                    ) VALUES (
                        :id, :character_id, :created_by, :name,
                        :appearance_prompt, :style_prompt, :negative_prompt,
                        'active', TRUE
                    )""",
                    {
                        "id": str(kit_id),
                        "character_id": str(char_id),
                        "created_by": ADMIN_USER_ID,
                        "name": f"{name}'s Avatar Kit",
                        "appearance_prompt": prompt_assembly.appearance_prompt,
                        "style_prompt": prompt_assembly.style_prompt,
                        "negative_prompt": prompt_assembly.negative_prompt,
                    }
                )

                # Upload to storage
                asset_id = uuid.uuid4()
                storage_path = await storage.upload_avatar_asset(
                    image_bytes=image_bytes,
                    kit_id=kit_id,
                    asset_id=asset_id,
                    asset_type="anchor_portrait",
                )

                # Create asset record
                await db.execute(
                    """INSERT INTO avatar_assets (
                        id, avatar_kit_id, asset_type,
                        storage_bucket, storage_path, source_type,
                        generation_metadata, is_canonical, is_active,
                        mime_type, file_size_bytes
                    ) VALUES (
                        :id, :kit_id, 'anchor_portrait',
                        'avatars', :storage_path, 'ai_generated',
                        :metadata, TRUE, TRUE,
                        'image/png', :file_size
                    )""",
                    {
                        "id": str(asset_id),
                        "kit_id": str(kit_id),
                        "storage_path": storage_path,
                        "metadata": json.dumps({
                            "prompt": prompt_assembly.full_prompt[:500],
                            "model": response.model,
                        }),
                        "file_size": len(image_bytes),
                    }
                )

                # Set as primary anchor
                await db.execute(
                    """UPDATE avatar_kits
                       SET primary_anchor_id = :asset_id, updated_at = NOW()
                       WHERE id = :kit_id""",
                    {"asset_id": str(asset_id), "kit_id": str(kit_id)}
                )

                # Update character
                image_url = await storage.create_signed_url("avatars", storage_path)
                await db.execute(
                    """UPDATE characters
                       SET avatar_url = :avatar_url,
                           active_avatar_kit_id = :kit_id,
                           updated_at = NOW()
                       WHERE id = :id""",
                    {
                        "avatar_url": image_url,
                        "kit_id": str(kit_id),
                        "id": str(char_id),
                    }
                )

                print(f"  ✓ {name}: avatar generated ({response.latency_ms}ms)")
                success_count += 1

            except Exception as e:
                print(f"  ✗ {name}: {e}")
                log.exception(f"Failed to generate avatar for {name}")
                fail_count += 1

            # Rate limiting delay between generations
            print(f"  (waiting {GENERATION_DELAY}s before next...)")
            await asyncio.sleep(GENERATION_DELAY)

        print(f"\n{'='*60}")
        print("GENERATION COMPLETE")
        print(f"{'='*60}")
        print(f"Success: {success_count}")
        print(f"Failed: {fail_count}")

    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(generate_avatars())
