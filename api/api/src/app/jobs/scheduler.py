"""
Scheduler Job - Entry point for the cron job that sends daily messages.

This script is run by Render's cron service every minute.
It finds users who should receive their daily message at the current time
and sends personalized check-ins.

Usage:
    python -m app.jobs.scheduler
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
    """Main entry point for the scheduler job."""
    log.info("Starting scheduler job...")

    try:
        # Import here to ensure environment is loaded
        from app.deps import close_db, get_db
        from app.services.scheduler import run_scheduler

        # Initialize database
        await get_db()
        log.info("Database connection established")

        # Run scheduler
        success, total = await run_scheduler()

        log.info(f"Scheduler job complete: {success}/{total} messages sent")

        # Cleanup
        await close_db()

    except Exception as e:
        log.error(f"Scheduler job failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
