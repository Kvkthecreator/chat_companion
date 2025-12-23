"""Regenerate all character system prompts with genre-appropriate doctrine.

This script updates all active characters' system_prompts using the canonical
build_system_prompt() function which incorporates the appropriate genre doctrine.

Supported genres:
- romantic_tension (Genre 01)
- psychological_thriller (Genre 02)

Usage:
    python -m app.scripts.regenerate_system_prompts
"""

import asyncio
import json
import os
import sys

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from databases import Database
from app.models.character import build_system_prompt


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres.lfwhdzwbikyzalpbwfnd:42PJb25YJhJHJdkl@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres"
)


async def regenerate_all_prompts():
    """Regenerate system prompts for all active characters."""
    db = Database(DATABASE_URL)
    await db.connect()

    try:
        # Get all active characters with their genre
        # NOTE: short_backstory/full_backstory merged into backstory
        # NOTE: current_stressor removed - episode situation conveys emotional state
        rows = await db.fetch_all("""
            SELECT id, name, archetype, baseline_personality, boundaries,
                   tone_style, speech_patterns, backstory,
                   likes, dislikes, genre
            FROM characters
            WHERE status = 'active'
            ORDER BY name
        """)

        print(f"Found {len(rows)} active characters to update")

        for row in rows:
            char = dict(row)
            char_id = char["id"]
            name = char["name"]

            # Parse JSON fields
            personality = char["baseline_personality"]
            if isinstance(personality, str):
                personality = json.loads(personality)

            boundaries = char["boundaries"]
            if isinstance(boundaries, str):
                boundaries = json.loads(boundaries)

            tone_style = char["tone_style"]
            if isinstance(tone_style, str):
                tone_style = json.loads(tone_style) if tone_style else {}

            speech_patterns = char["speech_patterns"]
            if isinstance(speech_patterns, str):
                speech_patterns = json.loads(speech_patterns) if speech_patterns else {}

            likes = char["likes"]
            if isinstance(likes, str):
                likes = json.loads(likes) if likes else []

            dislikes = char["dislikes"]
            if isinstance(dislikes, str):
                dislikes = json.loads(dislikes) if dislikes else []

            # Get genre (default to romantic_tension for existing characters)
            genre = char.get("genre") or "romantic_tension"

            # Build new system prompt with genre-appropriate doctrine
            new_prompt = build_system_prompt(
                name=name,
                archetype=char["archetype"],
                personality=personality or {},
                boundaries=boundaries or {},
                tone_style=tone_style,
                speech_patterns=speech_patterns,
                backstory=char.get("backstory"),
                likes=likes,
                dislikes=dislikes,
                genre=genre,
            )

            # Update in database
            await db.execute(
                "UPDATE characters SET system_prompt = :prompt, updated_at = NOW() WHERE id = :id",
                {"id": str(char_id), "prompt": new_prompt}
            )

            print(f"  Updated {name} ({char['archetype']}) - {genre}")
            print(f"    - Prompt length: {len(new_prompt)} chars")
            print(f"    - Energy level: {boundaries.get('flirting_level', 'playful')}")

        print(f"\nSuccessfully updated {len(rows)} character system prompts")

    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(regenerate_all_prompts())
