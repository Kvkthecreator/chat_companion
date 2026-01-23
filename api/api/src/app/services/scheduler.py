"""
Scheduler Service - Handles scheduled message delivery.

Handles:
- Finding users who should receive messages at current time
- Generating personalized daily messages using priority stack
- Sending messages via appropriate channel
- Tracking message delivery and priority metrics

Priority Stack (from MEMORY_SYSTEM.md):
1. FOLLOW_UP - Ask about something specific from recent conversation
2. THREAD - Reference ongoing life situation
3. PATTERN - Acknowledge mood/engagement pattern
4. TEXTURE - Personal check-in with weather/context
5. GENERIC - Warm fallback (FAILURE STATE - should track)
"""

import logging
import os
from datetime import datetime
from typing import Optional
from uuid import UUID

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
from app.services.push import ExpoPushService
from app.services.threads import ThreadService, MessagePriority

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
        - Has an active push token (mobile device registered)
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
                u.location
            FROM users u
            WHERE
                -- User has completed onboarding
                u.onboarding_completed_at IS NOT NULL
                -- User has an active push token
                AND EXISTS (
                    SELECT 1 FROM user_devices ud
                    WHERE ud.user_id = u.id
                    AND ud.is_active = true
                    AND ud.push_token IS NOT NULL
                )
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
        message_context=None,
    ) -> tuple[str, MessagePriority]:
        """Generate a personalized daily check-in message.

        Uses priority-based message generation from ThreadService.

        Returns:
            tuple: (message content, priority level used)
        """
        companion_service = get_companion_service()

        # Get time context
        day_of_week, local_time = companion_service.get_local_time_context(
            user_profile.timezone
        )

        # Build context with message_context for priority-based generation
        context = ConversationContext(
            user_profile=user_profile,
            user_context=user_context,
            recent_messages=[],
            weather_info=weather_info,
            day_of_week=day_of_week,
            local_time=local_time,
            is_daily_message=True,
        )

        # Attach message context for priority-based generation
        if message_context:
            context.message_context = message_context  # type: ignore

        # Generate with LLM
        llm = LLMService.get_instance()
        prompt = companion_service.build_daily_message_prompt(context)

        response = await llm.generate(
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates warm, personal messages."},
                {"role": "user", "content": prompt},
            ],
        )

        # Determine priority level
        priority = MessagePriority.GENERIC
        if message_context:
            priority = message_context.priority

        return response.content.strip(), priority

    @classmethod
    async def send_scheduled_message(cls, user: dict) -> bool:
        """
        Send a scheduled message to a user.

        Uses priority-based message generation:
        1. Follow-ups from recent conversations
        2. Active life threads
        3. Patterns (mood trends)
        4. Core facts for texture
        5. Generic fallback (tracked as failure)

        Returns True if successful, False otherwise.
        """
        db = await get_db()
        user_id = user["user_id"]

        try:
            # Get user context
            user_context = await cls.get_user_context(str(user_id))

            # Get weather
            weather_info = await get_weather(user.get("location"))

            # Get priority-based message context from ThreadService
            thread_service = ThreadService(db)
            message_context = await thread_service.get_message_context(UUID(str(user_id)))

            # Log priority level for metrics
            log.info(
                f"Message priority for user {user_id}: {message_context.priority.name} "
                f"(has_personal={message_context.has_personal_content})"
            )

            # Build profile
            profile = UserProfile(
                user_id=str(user_id),
                display_name=user.get("display_name"),
                companion_name=user.get("companion_name"),
                support_style=user.get("support_style", "friendly_checkin"),
                timezone=user.get("timezone", "America/New_York"),
                location=user.get("location"),
            )

            # Generate message with priority context
            message, priority = await cls.generate_daily_message(
                profile, user_context, weather_info, message_context
            )

            # Create scheduled message record with priority tracking
            scheduled_msg = await db.fetchrow(
                """
                INSERT INTO scheduled_messages (user_id, scheduled_for, content, status, priority_level)
                VALUES ($1, NOW(), $2, 'pending', $3)
                RETURNING id
                """,
                user_id,
                message,
                priority.name,
            )
            scheduled_id = scheduled_msg["id"]

            # Track generic fallback as failure metric
            if priority == MessagePriority.GENERIC:
                log.warning(
                    f"GENERIC FALLBACK for user {user_id} - no personal content available. "
                    "This is a failure state that should be investigated."
                )

            # Create conversation record first (message will be visible when user opens app)
            conv = await db.fetchrow(
                """
                INSERT INTO conversations (user_id, channel, initiated_by)
                VALUES ($1, 'app', 'companion')
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

            # Send push notification to most recently active device
            push_service = ExpoPushService(db)
            push_results = await push_service.send_notification(
                user_id=UUID(str(user_id)),
                title=f"{profile.companion_name} is here",
                body=message[:100] + "..." if len(message) > 100 else message,
                data={
                    "type": "daily-checkin",
                    "conversation_id": str(conversation_id),
                    "scheduled_message_id": str(scheduled_id),
                },
                scheduled_message_id=scheduled_id,
                channel_id="daily-checkin",
                single_device=True,  # Only send to most recent device
            )

            # Check if push was sent successfully
            push_sent = any(r.success for r in push_results) if push_results else False

            # Mark scheduled message as sent (even if push failed - message is in app)
            await db.execute(
                """
                UPDATE scheduled_messages
                SET status = 'sent', sent_at = NOW(), conversation_id = $2
                WHERE id = $1
                """,
                scheduled_id,
                conversation_id,
            )

            if push_sent:
                log.info(f"Sent scheduled message to user {user_id} with push notification")
            else:
                log.info(f"Sent scheduled message to user {user_id} (no push - message waiting in app)")

            return True

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
