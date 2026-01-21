"""
Scheduler Service - Handles scheduled message delivery.

Handles:
- Finding users who should receive messages at current time
- Generating personalized daily messages
- Sending messages via appropriate channel
- Tracking message delivery
"""

import logging
import os
from datetime import datetime
from typing import Optional

import httpx

from app.deps import get_db
from app.services.companion import (
    CompanionService,
    ConversationContext,
    UserContext,
    UserProfile,
    get_companion_service,
)
from app.services.llm import LLMService
from app.services.telegram import TelegramService, get_telegram_service

log = logging.getLogger(__name__)


# =============================================================================
# Weather Service (simple implementation)
# =============================================================================


async def get_weather(location: Optional[str]) -> Optional[str]:
    """
    Get weather description for a location.

    Returns a simple weather string like "Sunny, 72°F" or None if unavailable.
    """
    if not location:
        return None

    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return None

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={
                    "q": location,
                    "appid": api_key,
                    "units": "imperial",  # Fahrenheit
                },
            )
            if response.status_code == 200:
                data = response.json()
                weather_desc = data["weather"][0]["main"]
                temp = round(data["main"]["temp"])
                return f"{weather_desc}, {temp}°F"
    except Exception as e:
        log.warning(f"Failed to get weather for {location}: {e}")

    return None


# =============================================================================
# Scheduler Service
# =============================================================================


class SchedulerService:
    """Service for managing scheduled message delivery."""

    @staticmethod
    async def get_users_for_scheduled_message() -> list[dict]:
        """
        Get users who should receive a scheduled message right now.

        Returns users where:
        - Onboarding is complete
        - Has a connected channel (Telegram/WhatsApp)
        - Current time matches their preferred time (within 2 minute window)
        - Haven't received a message today
        - Daily messages not paused
        """
        db = await get_db()

        users = await db.fetch(
            """
            SELECT
                u.id as user_id,
                u.display_name,
                u.companion_name,
                u.support_style,
                u.timezone,
                u.telegram_user_id,
                u.whatsapp_number,
                u.location
            FROM users u
            WHERE
                -- User has completed onboarding
                u.onboarding_completed_at IS NOT NULL
                -- User has a connected channel
                AND (u.telegram_user_id IS NOT NULL OR u.whatsapp_number IS NOT NULL)
                -- Daily messages not paused
                AND COALESCE((u.preferences->>'daily_messages_paused')::boolean, false) = false
                -- Current time matches their preferred time (within 2 minute window)
                AND (NOW() AT TIME ZONE COALESCE(u.timezone, 'UTC'))::time
                    BETWEEN u.preferred_message_time
                    AND (u.preferred_message_time + interval '2 minutes')
                -- No message sent today
                AND NOT EXISTS (
                    SELECT 1 FROM scheduled_messages sm
                    WHERE sm.user_id = u.id
                    AND sm.status = 'sent'
                    AND (sm.sent_at AT TIME ZONE COALESCE(u.timezone, 'UTC'))::date
                        = (NOW() AT TIME ZONE COALESCE(u.timezone, 'UTC'))::date
                )
            """
        )

        return [dict(u) for u in users]

    @staticmethod
    async def get_user_context(user_id: str) -> list[UserContext]:
        """Get context items for a user."""
        db = await get_db()

        rows = await db.fetch(
            """
            SELECT category, key, value, importance_score
            FROM user_context
            WHERE user_id = $1
            AND (expires_at IS NULL OR expires_at > NOW())
            ORDER BY importance_score DESC, last_referenced_at DESC NULLS LAST
            LIMIT 20
            """,
            user_id,
        )

        return [
            UserContext(
                category=row["category"],
                key=row["key"],
                value=row["value"],
                importance_score=row["importance_score"],
            )
            for row in rows
        ]

    @classmethod
    async def generate_daily_message(
        cls,
        user_profile: UserProfile,
        user_context: list[UserContext],
        weather_info: Optional[str] = None,
    ) -> str:
        """Generate a personalized daily check-in message."""
        companion_service = get_companion_service()

        # Get time context
        day_of_week, local_time = companion_service.get_local_time_context(
            user_profile.timezone
        )

        # Build context
        context = ConversationContext(
            user_profile=user_profile,
            user_context=user_context,
            recent_messages=[],
            weather_info=weather_info,
            day_of_week=day_of_week,
            local_time=local_time,
            is_daily_message=True,
        )

        # Generate with LLM
        llm = LLMService.get_instance()
        prompt = companion_service.build_daily_message_prompt(context)

        response = await llm.generate(
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates warm, personal messages."},
                {"role": "user", "content": prompt},
            ],
        )

        return response.content.strip()

    @classmethod
    async def send_scheduled_message(cls, user: dict) -> bool:
        """
        Send a scheduled message to a user.

        Returns True if successful, False otherwise.
        """
        db = await get_db()
        user_id = user["user_id"]

        try:
            # Get user context
            user_context = await cls.get_user_context(str(user_id))

            # Get weather
            weather_info = await get_weather(user.get("location"))

            # Build profile
            profile = UserProfile(
                user_id=str(user_id),
                display_name=user.get("display_name"),
                companion_name=user.get("companion_name"),
                support_style=user.get("support_style", "friendly_checkin"),
                timezone=user.get("timezone", "America/New_York"),
                location=user.get("location"),
            )

            # Generate message
            message = await cls.generate_daily_message(profile, user_context, weather_info)

            # Create scheduled message record
            scheduled_msg = await db.fetchrow(
                """
                INSERT INTO scheduled_messages (user_id, scheduled_for, content, status)
                VALUES ($1, NOW(), $2, 'pending')
                RETURNING id
                """,
                user_id,
                message,
            )
            scheduled_id = scheduled_msg["id"]

            # Send via appropriate channel
            sent = False
            conversation_id = None

            if user.get("telegram_user_id"):
                telegram_service = get_telegram_service()
                await telegram_service.send_message(user["telegram_user_id"], message)
                sent = True

                # Create conversation record
                conv = await db.fetchrow(
                    """
                    INSERT INTO conversations (user_id, channel, initiated_by)
                    VALUES ($1, 'telegram', 'companion')
                    RETURNING id
                    """,
                    user_id,
                )
                conversation_id = conv["id"]

                # Store message
                await db.execute(
                    """
                    INSERT INTO companion_messages (conversation_id, role, content)
                    VALUES ($1, 'assistant', $2)
                    """,
                    conversation_id,
                    message,
                )

            # TODO: Add WhatsApp support here

            if sent:
                # Mark as sent
                await db.execute(
                    """
                    UPDATE scheduled_messages
                    SET status = 'sent', sent_at = NOW(), conversation_id = $2
                    WHERE id = $1
                    """,
                    scheduled_id,
                    conversation_id,
                )
                log.info(f"Sent scheduled message to user {user_id}")
                return True
            else:
                # No channel available
                await db.execute(
                    """
                    UPDATE scheduled_messages
                    SET status = 'failed', failure_reason = 'No channel available'
                    WHERE id = $1
                    """,
                    scheduled_id,
                )
                log.warning(f"No channel available for user {user_id}")
                return False

        except Exception as e:
            log.error(f"Failed to send scheduled message to user {user_id}: {e}", exc_info=True)

            # Record failure
            await db.execute(
                """
                INSERT INTO scheduled_messages (user_id, scheduled_for, status, failure_reason)
                VALUES ($1, NOW(), 'failed', $2)
                ON CONFLICT (user_id, scheduled_for)
                DO UPDATE SET status = 'failed', failure_reason = $2
                """,
                user_id,
                str(e)[:500],
            )
            return False

    @classmethod
    async def run_scheduler(cls):
        """
        Main scheduler loop - find users and send messages.

        This is called by the cron job every minute.
        """
        log.info("Running scheduler...")

        users = await cls.get_users_for_scheduled_message()
        log.info(f"Found {len(users)} users to message")

        success_count = 0
        for user in users:
            try:
                if await cls.send_scheduled_message(user):
                    success_count += 1
            except Exception as e:
                log.error(f"Error processing user {user['user_id']}: {e}")

        log.info(f"Scheduler complete: {success_count}/{len(users)} messages sent")
        return success_count, len(users)


# =============================================================================
# Module-level function
# =============================================================================


async def run_scheduler():
    """Run the scheduler (called by cron job)."""
    service = SchedulerService()
    return await service.run_scheduler()
