"""
Pattern Computation Job - Compute behavioral patterns for active users.

This script is run by Render's cron service daily (e.g., at 2am UTC).
It computes mood trends, engagement patterns, and topic sentiments
for users with recent conversation activity.

Usage:
    python -m app.jobs.patterns
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
log = logging.getLogger(__name__)


async def compute_patterns_for_active_users(db) -> tuple[int, int]:
    """Compute patterns for users with recent conversations.

    Returns:
        tuple: (users_processed, patterns_saved)
    """
    from app.services.patterns import PatternService

    pattern_service = PatternService(db)

    # Get users with conversations in the last 7 days
    week_ago = datetime.utcnow() - timedelta(days=7)

    active_users = await db.fetch_all(
        """
        SELECT DISTINCT c.user_id
        FROM conversations c
        JOIN users u ON c.user_id = u.id
        WHERE c.started_at >= :week_ago
          AND u.onboarding_completed_at IS NOT NULL
        """,
        {"week_ago": week_ago},
    )

    users_processed = 0
    patterns_saved = 0

    for row in active_users:
        user_id = row["user_id"]

        try:
            # Compute all patterns for this user
            patterns = await pattern_service.compute_all_patterns(user_id)

            # Save patterns
            saved = await pattern_service.save_all_patterns(user_id, patterns)
            patterns_saved += saved
            users_processed += 1

            log.info(f"Computed {len(patterns)} patterns for user {user_id}, saved {saved}")

        except Exception as e:
            log.error(f"Failed to compute patterns for user {user_id}: {e}")
            continue

    return users_processed, patterns_saved


async def main():
    """Main entry point for the pattern computation job."""
    log.info("Starting pattern computation job...")

    try:
        # Import here to ensure environment is loaded
        from app.deps import close_db, get_db

        # Initialize database
        db = await get_db()
        log.info("Database connection established")

        # Compute patterns
        users_processed, patterns_saved = await compute_patterns_for_active_users(db)

        log.info(
            f"Pattern computation complete: "
            f"{users_processed} users processed, "
            f"{patterns_saved} patterns saved"
        )

        # Cleanup
        await close_db()

    except Exception as e:
        log.error(f"Pattern computation job failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
