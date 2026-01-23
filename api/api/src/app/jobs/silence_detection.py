"""
Silence Detection Job - Entry point for the cron job that checks on quiet users.

This script is run by Render's cron service periodically (recommended: every 6 hours).
It finds users who haven't messaged in N days and sends a gentle check-in.

This is Phase 2 of the Companion Outreach System.
See: docs/design/COMPANION_OUTREACH_SYSTEM.md

Usage:
    python -m app.jobs.silence_detection
"""

import asyncio
import logging
import os
import sys

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


async def main():
    """Main entry point for the silence detection job."""
    log.info("Starting silence detection job...")

    try:
        # Import here to ensure environment is loaded
        from app.deps import close_db, get_db
        from app.services.scheduler import run_silence_detection

        # Initialize database
        await get_db()
        log.info("Database connection established")

        # Run silence detection
        success, total = await run_silence_detection()

        log.info(f"Silence detection job complete: {success}/{total} check-ins sent")

        # Cleanup
        await close_db()

    except Exception as e:
        log.error(f"Silence detection job failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
