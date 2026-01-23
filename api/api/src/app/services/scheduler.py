"""
Scheduler Service - Handles scheduled message delivery.

Handles:
- Finding users who should receive messages at current time
- Generating personalized daily messages using priority stack
- Sending messages via appropriate channel (push notifications, email)
- Tracking message delivery and priority metrics

Priority Stack (from MEMORY_SYSTEM.md):
1. FOLLOW_UP - Ask about something specific from recent conversation
2. THREAD - Reference ongoing life situation
3. PATTERN - Acknowledge mood/engagement pattern
4. TEXTURE - Personal check-in with weather/context
5. GENERIC - Warm fallback (FAILURE STATE - should track)

Channels:
- PUSH: Mobile app users with active push tokens
- EMAIL: Web users without push tokens (or with email preference enabled)
"""

import logging
import os
from datetime import datetime
from enum import Enum
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
from app.services.email import get_email_service
from app.services.llm import LLMService
from app.services.push import ExpoPushService
from app.services.threads import ThreadService, MessagePriority

log = logging.getLogger(__name__)


class DeliveryChannel(str, Enum):
    """Delivery channel for scheduled messages."""
    PUSH = "push"
    EMAIL = "email"


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

    # Web app base URL for email links
    WEB_APP_URL = os.getenv("WEB_APP_URL", "https://chat-companion.vercel.app")

    @staticmethod
    async def get_users_for_scheduled_message() -> list[dict]:
        """
        Get users who should receive a scheduled message right now.

        Returns users where:
        - Onboarding is complete
        - Has a delivery channel (push token OR email enabled)
        - Current time matches their preferred time (within 2 minute window)
        - Haven't received a message today
        - Daily messages not paused

        Each user includes their preferred delivery channel.
        """
        db = await get_db()

        users = await db.fetch_all(
            """
            SELECT
                u.id as user_id,
                u.email,
                u.display_name,
                u.companion_name,
                u.support_style,
                u.timezone,
                u.location,
                -- Determine delivery channel
                CASE
                    WHEN EXISTS (
                        SELECT 1 FROM user_devices ud
                        WHERE ud.user_id = u.id
                        AND ud.is_active = true
                        AND ud.push_token IS NOT NULL
                    ) THEN 'push'
                    WHEN COALESCE((u.preferences->>'email_notifications_enabled')::boolean, true) = true
                         AND u.email IS NOT NULL
                    THEN 'email'
                    ELSE NULL
                END as delivery_channel
            FROM users u
            WHERE
                -- User has completed onboarding
                u.onboarding_completed_at IS NOT NULL
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
                -- Has at least one delivery method
                AND (
                    -- Has push token
                    EXISTS (
                        SELECT 1 FROM user_devices ud
                        WHERE ud.user_id = u.id
                        AND ud.is_active = true
                        AND ud.push_token IS NOT NULL
                    )
                    -- OR has email enabled (default true for web users)
                    OR (
                        COALESCE((u.preferences->>'email_notifications_enabled')::boolean, true) = true
                        AND u.email IS NOT NULL
                    )
                )
            """
        )

        return [dict(u) for u in users]

    @staticmethod
    async def get_user_context(user_id: str) -> list[UserContext]:
        """Get context items for a user."""
        db = await get_db()

        rows = await db.fetch_all(
            """
            SELECT category, key, value, importance_score
            FROM user_context
            WHERE user_id = :user_id
            AND (expires_at IS NULL OR expires_at > NOW())
            ORDER BY importance_score DESC, last_referenced_at DESC NULLS LAST
            LIMIT 20
            """,
            {"user_id": user_id},
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
        Send a scheduled message to a user via their preferred channel.

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
        delivery_channel = user.get("delivery_channel")

        if not delivery_channel:
            log.warning(f"No delivery channel for user {user_id}, skipping")
            return False

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
                f"(has_personal={message_context.has_personal_content}, channel={delivery_channel})"
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

            # Create scheduled message record with priority and channel tracking
            scheduled_msg = await db.fetch_one(
                """
                INSERT INTO scheduled_messages (user_id, scheduled_for, content, status, priority_level, channel)
                VALUES (:user_id, NOW(), :content, 'pending', :priority_level, :channel)
                RETURNING id
                """,
                {
                    "user_id": user_id,
                    "content": message,
                    "priority_level": priority.name,
                    "channel": delivery_channel,
                },
            )
            scheduled_id = scheduled_msg["id"]

            # Track generic fallback as failure metric
            if priority == MessagePriority.GENERIC:
                log.warning(
                    f"GENERIC FALLBACK for user {user_id} - no personal content available. "
                    "This is a failure state that should be investigated."
                )

            # Create conversation record (message will be visible when user opens app/clicks email)
            channel_type = "web" if delivery_channel == "email" else "app"
            conv = await db.fetch_one(
                """
                INSERT INTO conversations (user_id, channel, initiated_by)
                VALUES (:user_id, :channel, 'companion')
                RETURNING id
                """,
                {"user_id": user_id, "channel": channel_type},
            )
            conversation_id = conv["id"]

            # Store message
            await db.execute(
                """
                INSERT INTO messages (conversation_id, role, content)
                VALUES (:conversation_id, 'assistant', :content)
                """,
                {"conversation_id": conversation_id, "content": message},
            )

            # Send via appropriate channel
            delivery_success = False

            if delivery_channel == DeliveryChannel.PUSH.value:
                # Send push notification
                delivery_success = await cls._send_via_push(
                    db, user_id, profile, message, conversation_id, scheduled_id
                )
            elif delivery_channel == DeliveryChannel.EMAIL.value:
                # Send email
                delivery_success = await cls._send_via_email(
                    user, profile, message, conversation_id
                )

            # Mark scheduled message as sent
            await db.execute(
                """
                UPDATE scheduled_messages
                SET status = 'sent', sent_at = NOW(), conversation_id = :conversation_id
                WHERE id = :id
                """,
                {"id": scheduled_id, "conversation_id": conversation_id},
            )

            if delivery_success:
                log.info(f"Sent scheduled message to user {user_id} via {delivery_channel}")
            else:
                log.info(f"Sent scheduled message to user {user_id} (delivery attempted via {delivery_channel})")

            return True

        except Exception as e:
            log.error(f"Failed to send scheduled message to user {user_id}: {e}", exc_info=True)

            # Record failure - simple insert, no conflict handling needed
            try:
                await db.execute(
                    """
                    INSERT INTO scheduled_messages (user_id, scheduled_for, status, failure_reason, channel)
                    VALUES (:user_id, NOW(), 'failed', :failure_reason, :channel)
                    """,
                    {
                        "user_id": user_id,
                        "failure_reason": str(e)[:500],
                        "channel": delivery_channel,
                    },
                )
            except Exception as insert_error:
                log.error(f"Failed to record failure for user {user_id}: {insert_error}")
            return False

    @classmethod
    async def _send_via_push(
        cls,
        db,
        user_id: UUID,
        profile: UserProfile,
        message: str,
        conversation_id: UUID,
        scheduled_id: UUID,
    ) -> bool:
        """Send message via push notification."""
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
            single_device=True,
        )
        return any(r.success for r in push_results) if push_results else False

    @classmethod
    async def _send_via_email(
        cls,
        user: dict,
        profile: UserProfile,
        message: str,
        conversation_id: UUID,
    ) -> bool:
        """Send message via email."""
        email_service = get_email_service()

        if not email_service.is_configured:
            log.warning("Email service not configured, skipping email delivery")
            return False

        user_email = user.get("email")
        if not user_email:
            log.warning(f"No email for user {user['user_id']}, skipping email delivery")
            return False

        # Build conversation URL
        conversation_url = f"{cls.WEB_APP_URL}/chat/{conversation_id}"

        result = await email_service.send_daily_checkin(
            to_email=user_email,
            user_name=profile.display_name or "there",
            companion_name=profile.companion_name or "Your companion",
            message=message,
            conversation_url=conversation_url,
        )

        return result.success

    @classmethod
    async def run_scheduler(cls):
        """
        Main scheduler loop - find users and send messages.

        This is called by the cron job every minute.
        """
        log.info("Running scheduler...")

        users = await cls.get_users_for_scheduled_message()
        log.info(f"Found {len(users)} users to message")

        # Count by channel for metrics
        push_users = sum(1 for u in users if u.get("delivery_channel") == "push")
        email_users = sum(1 for u in users if u.get("delivery_channel") == "email")
        log.info(f"Channels: {push_users} push, {email_users} email")

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
# Silence Detection Service
# =============================================================================


class SilenceDetectionService:
    """Service for detecting and reaching out to users who've been quiet.

    This implements Phase 2 of the Companion Outreach System:
    - Detects users who haven't messaged in N days
    - Sends a gentle check-in that feels caring, not guilt-inducing
    - Respects user preferences (allow_silence_checkins setting)

    See: docs/design/COMPANION_OUTREACH_SYSTEM.md
    """

    # Web app base URL for email links
    WEB_APP_URL = os.getenv("WEB_APP_URL", "https://chat-companion.vercel.app")

    @staticmethod
    async def get_users_for_silence_checkin() -> list[dict]:
        """
        Get users who should receive a silence check-in.

        Returns users where:
        - Onboarding is complete
        - Has allow_silence_checkins enabled (default: true)
        - Last user message was more than silence_threshold_days ago
        - Hasn't received a silence check-in in the last 24 hours
        - Has a delivery channel
        """
        db = await get_db()

        users = await db.fetch_all(
            """
            SELECT
                u.id as user_id,
                u.email,
                u.display_name,
                u.companion_name,
                u.support_style,
                u.timezone,
                u.location,
                u.last_user_message_at,
                u.silence_threshold_days,
                -- Determine delivery channel
                CASE
                    WHEN EXISTS (
                        SELECT 1 FROM user_devices ud
                        WHERE ud.user_id = u.id
                        AND ud.is_active = true
                        AND ud.push_token IS NOT NULL
                    ) THEN 'push'
                    WHEN COALESCE((u.preferences->>'email_notifications_enabled')::boolean, true) = true
                         AND u.email IS NOT NULL
                    THEN 'email'
                    ELSE NULL
                END as delivery_channel
            FROM users u
            WHERE
                -- User has completed onboarding
                u.onboarding_completed_at IS NOT NULL
                -- User allows silence check-ins (default: true)
                AND COALESCE(u.allow_silence_checkins, true) = true
                -- User has sent at least one message (we know their baseline)
                AND u.last_user_message_at IS NOT NULL
                -- Last message was more than threshold days ago
                AND u.last_user_message_at < NOW() - (COALESCE(u.silence_threshold_days, 3) || ' days')::interval
                -- No silence check-in sent in last 24 hours
                AND NOT EXISTS (
                    SELECT 1 FROM scheduled_messages sm
                    WHERE sm.user_id = u.id
                    AND sm.trigger_type = 'silence_detection'
                    AND sm.sent_at > NOW() - INTERVAL '24 hours'
                )
                -- Has at least one delivery method
                AND (
                    EXISTS (
                        SELECT 1 FROM user_devices ud
                        WHERE ud.user_id = u.id
                        AND ud.is_active = true
                        AND ud.push_token IS NOT NULL
                    )
                    OR (
                        COALESCE((u.preferences->>'email_notifications_enabled')::boolean, true) = true
                        AND u.email IS NOT NULL
                    )
                )
            """
        )

        return [dict(u) for u in users]

    @classmethod
    async def generate_silence_checkin_message(
        cls,
        user_profile: UserProfile,
        days_since_message: int,
    ) -> str:
        """Generate a gentle silence check-in message.

        Key principles:
        - Gentle, not guilt-inducing
        - No pressure to respond
        - Shows care without being needy
        """
        llm = LLMService.get_instance()

        companion_name = user_profile.companion_name or "Your companion"
        display_name = user_profile.display_name or "there"

        prompt = f"""Generate a short, gentle check-in message from {companion_name} to {display_name}.

Context: It's been {days_since_message} days since they last messaged. We want to show we care without being pushy or guilt-inducing.

Guidelines:
- Keep it to 1-2 short sentences
- Warm but not clingy
- No pressure to respond
- Don't mention the exact number of days
- Don't say "I noticed you haven't..." (sounds surveillance-y)
- Examples of good tone:
  * "Hey, just thinking of you. Here when you're ready to chat."
  * "Hope things are going okay. No pressure, just wanted to say hi."
  * "Just a gentle hello. I'm around if you need anything."

Generate ONE message in this style:"""

        response = await llm.generate(
            messages=[
                {"role": "system", "content": "You generate warm, gentle messages. Keep responses very brief."},
                {"role": "user", "content": prompt},
            ],
        )

        return response.content.strip().strip('"')

    @classmethod
    async def send_silence_checkin(cls, user: dict) -> bool:
        """Send a silence check-in to a user."""
        db = await get_db()
        user_id = user["user_id"]
        delivery_channel = user.get("delivery_channel")

        if not delivery_channel:
            log.warning(f"No delivery channel for user {user_id}, skipping silence check-in")
            return False

        try:
            # Calculate days since last message
            last_message_at = user.get("last_user_message_at")
            if last_message_at:
                days_since = (datetime.utcnow() - last_message_at.replace(tzinfo=None)).days
            else:
                days_since = user.get("silence_threshold_days", 3)

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
            message = await cls.generate_silence_checkin_message(profile, days_since)

            # Create scheduled message record
            scheduled_msg = await db.fetch_one(
                """
                INSERT INTO scheduled_messages (
                    user_id, scheduled_for, content, status,
                    priority_level, channel, trigger_type
                )
                VALUES (
                    :user_id, NOW(), :content, 'pending',
                    'TEXTURE', :channel, 'silence_detection'
                )
                RETURNING id
                """,
                {
                    "user_id": user_id,
                    "content": message,
                    "channel": delivery_channel,
                },
            )
            scheduled_id = scheduled_msg["id"]

            # Create conversation record
            channel_type = "web" if delivery_channel == "email" else "app"
            conv = await db.fetch_one(
                """
                INSERT INTO conversations (user_id, channel, initiated_by)
                VALUES (:user_id, :channel, 'companion')
                RETURNING id
                """,
                {"user_id": user_id, "channel": channel_type},
            )
            conversation_id = conv["id"]

            # Store message
            await db.execute(
                """
                INSERT INTO messages (conversation_id, role, content)
                VALUES (:conversation_id, 'assistant', :content)
                """,
                {"conversation_id": conversation_id, "content": message},
            )

            # Send via appropriate channel
            delivery_success = False

            if delivery_channel == DeliveryChannel.PUSH.value:
                push_service = ExpoPushService(db)
                push_results = await push_service.send_notification(
                    user_id=UUID(str(user_id)),
                    title=f"{profile.companion_name} is thinking of you",
                    body=message[:100] + "..." if len(message) > 100 else message,
                    data={
                        "type": "silence-checkin",
                        "conversation_id": str(conversation_id),
                        "scheduled_message_id": str(scheduled_id),
                    },
                    scheduled_message_id=scheduled_id,
                    channel_id="daily-checkin",
                    single_device=True,
                )
                delivery_success = any(r.success for r in push_results) if push_results else False

            elif delivery_channel == DeliveryChannel.EMAIL.value:
                email_service = get_email_service()
                if email_service.is_configured and user.get("email"):
                    conversation_url = f"{cls.WEB_APP_URL}/chat/{conversation_id}"
                    result = await email_service.send_daily_checkin(
                        to_email=user["email"],
                        user_name=profile.display_name or "there",
                        companion_name=profile.companion_name or "Your companion",
                        message=message,
                        conversation_url=conversation_url,
                    )
                    delivery_success = result.success

            # Mark as sent
            await db.execute(
                """
                UPDATE scheduled_messages
                SET status = 'sent', sent_at = NOW(), conversation_id = :conversation_id
                WHERE id = :id
                """,
                {"id": scheduled_id, "conversation_id": conversation_id},
            )

            log.info(
                f"Sent silence check-in to user {user_id} via {delivery_channel} "
                f"(days since last message: {days_since})"
            )
            return True

        except Exception as e:
            log.error(f"Failed to send silence check-in to user {user_id}: {e}", exc_info=True)
            return False

    @classmethod
    async def run_silence_detection(cls):
        """
        Main silence detection loop - find quiet users and check in.

        This should be run periodically (e.g., every hour or every 6 hours).
        """
        log.info("Running silence detection...")

        users = await cls.get_users_for_silence_checkin()
        log.info(f"Found {len(users)} users who've been quiet")

        if not users:
            log.info("No users need silence check-ins")
            return 0, 0

        success_count = 0
        for user in users:
            try:
                if await cls.send_silence_checkin(user):
                    success_count += 1
            except Exception as e:
                log.error(f"Error processing user {user['user_id']}: {e}")

        log.info(f"Silence detection complete: {success_count}/{len(users)} check-ins sent")
        return success_count, len(users)


# =============================================================================
# Module-level functions
# =============================================================================


async def run_scheduler():
    """Run the daily scheduler (called by cron job)."""
    service = SchedulerService()
    return await service.run_scheduler()


async def run_silence_detection():
    """Run silence detection (called by cron job)."""
    service = SilenceDetectionService()
    return await service.run_silence_detection()
