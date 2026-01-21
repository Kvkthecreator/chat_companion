"""
Telegram Webhook Routes - Handle incoming Telegram messages and commands.

Endpoints:
- POST /telegram/webhook - Process Telegram updates
- GET /telegram/link - Get deep link for connecting account
"""

import logging
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel

from app.deps import get_db
from app.services.telegram import TelegramService, get_telegram_service
from app.services.companion import (
    CompanionService,
    ConversationContext,
    UserContext,
    UserProfile,
    get_companion_service,
)
from app.services.llm import LLMService

log = logging.getLogger(__name__)

router = APIRouter(prefix="/telegram", tags=["Telegram"])


# =============================================================================
# Request/Response Models
# =============================================================================


class TelegramUser(BaseModel):
    id: int
    is_bot: bool = False
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None


class TelegramChat(BaseModel):
    id: int
    type: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None


class TelegramMessageModel(BaseModel):
    message_id: int
    from_: Optional[TelegramUser] = None
    chat: TelegramChat
    date: int
    text: Optional[str] = None

    class Config:
        populate_by_name = True
        fields = {"from_": "from"}


class TelegramUpdate(BaseModel):
    update_id: int
    message: Optional[TelegramMessageModel] = None


class DeepLinkResponse(BaseModel):
    url: str
    instructions: str


# =============================================================================
# Webhook Handler
# =============================================================================


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: Optional[str] = Header(None),
):
    """
    Process incoming Telegram webhook updates.

    Handles:
    - /start command (with optional deep link payload)
    - /settings command
    - /pause and /resume commands
    - Regular messages (conversations)
    """
    # Verify webhook secret
    telegram_service = get_telegram_service()
    if x_telegram_bot_api_secret_token:
        if not telegram_service.verify_webhook_secret(x_telegram_bot_api_secret_token):
            raise HTTPException(status_code=401, detail="Invalid secret token")

    # Parse the update
    try:
        body = await request.json()
        update = TelegramUpdate(**body)
    except Exception as e:
        log.error(f"Failed to parse Telegram update: {e}")
        raise HTTPException(status_code=400, detail="Invalid update format")

    # Only handle message updates for now
    if not update.message or not update.message.text:
        return {"ok": True}

    message = update.message
    chat_id = message.chat.id
    text = message.text
    telegram_user = message.from_

    if not telegram_user:
        return {"ok": True}

    # Parse command if present
    command, args = telegram_service.parse_command(text)

    try:
        if command == "/start":
            await handle_start_command(telegram_service, chat_id, telegram_user, args)
        elif command == "/settings":
            await handle_settings_command(telegram_service, chat_id, telegram_user)
        elif command == "/pause":
            await handle_pause_command(telegram_service, chat_id, telegram_user)
        elif command == "/resume":
            await handle_resume_command(telegram_service, chat_id, telegram_user)
        elif command == "/help":
            await handle_help_command(telegram_service, chat_id)
        elif command:
            # Unknown command
            await telegram_service.send_message(
                chat_id,
                "I don't recognize that command. Try /help to see what I can do.",
            )
        else:
            # Regular message - have a conversation
            await handle_conversation_message(telegram_service, chat_id, telegram_user, text)

    except Exception as e:
        log.error(f"Error handling Telegram message: {e}", exc_info=True)
        await telegram_service.send_message(
            chat_id,
            "Sorry, something went wrong. Please try again later.",
        )

    return {"ok": True}


# =============================================================================
# Command Handlers
# =============================================================================


async def handle_start_command(
    telegram_service: TelegramService,
    chat_id: int,
    telegram_user: TelegramUser,
    args: Optional[str],
):
    """Handle /start command, optionally with deep link payload."""
    db = await get_db()

    # Check if this Telegram user is already linked
    existing_user = await db.fetchrow(
        "SELECT id, display_name, companion_name FROM users WHERE telegram_user_id = $1",
        telegram_user.id,
    )

    if existing_user:
        # Already linked
        companion_name = existing_user["companion_name"] or "your companion"
        display_name = existing_user["display_name"] or telegram_user.first_name
        await telegram_service.send_message(
            chat_id,
            f"Welcome back, {display_name}! 👋\n\n"
            f"I'm {companion_name}, and I'm here whenever you want to chat.\n\n"
            f"Just send me a message anytime, or use /help to see what I can do.",
        )
        return

    # Check if deep link payload is provided
    if args:
        user_id_prefix = telegram_service.verify_deep_link_payload(args)
        if user_id_prefix:
            # Look up user by ID prefix
            user = await db.fetchrow(
                "SELECT id, display_name, companion_name FROM users WHERE id::text LIKE $1",
                f"{user_id_prefix}%",
            )

            if user:
                # Link the accounts
                await db.execute(
                    """
                    UPDATE users
                    SET telegram_user_id = $1,
                        telegram_username = $2,
                        telegram_linked_at = NOW()
                    WHERE id = $3
                    """,
                    telegram_user.id,
                    telegram_user.username,
                    user["id"],
                )

                companion_name = user["companion_name"] or "your companion"
                display_name = user["display_name"] or telegram_user.first_name
                await telegram_service.send_message(
                    chat_id,
                    f"Perfect! Your account is now connected. 🎉\n\n"
                    f"Hi {display_name}, I'm {companion_name}!\n\n"
                    f"I'll send you a message each day at your preferred time. "
                    f"You can also chat with me anytime by sending a message here.\n\n"
                    f"Type /help to see what I can do.",
                )
                return

    # No deep link or invalid - prompt to sign up
    await telegram_service.send_message(
        chat_id,
        f"Hi {telegram_user.first_name}! 👋\n\n"
        f"I'm an AI companion who'd love to check in with you each day.\n\n"
        f"To get started, please sign up at our website and connect your Telegram account.\n\n"
        f"Once you're set up, I'll send you personalized daily messages and we can chat anytime!",
    )


async def handle_settings_command(
    telegram_service: TelegramService,
    chat_id: int,
    telegram_user: TelegramUser,
):
    """Handle /settings command."""
    db = await get_db()

    user = await db.fetchrow(
        """
        SELECT display_name, companion_name, timezone, preferred_message_time, support_style
        FROM users WHERE telegram_user_id = $1
        """,
        telegram_user.id,
    )

    if not user:
        await telegram_service.send_message(
            chat_id,
            "You haven't connected your account yet.\n\n"
            "Please sign up at our website and connect your Telegram to manage settings.",
        )
        return

    time_str = user["preferred_message_time"].strftime("%I:%M %p") if user["preferred_message_time"] else "Not set"
    style = user["support_style"] or "friendly_checkin"
    style_name = {
        "motivational": "Motivational",
        "friendly_checkin": "Friendly Check-in",
        "accountability": "Accountability",
        "listener": "Listener",
    }.get(style, style)

    await telegram_service.send_message(
        chat_id,
        f"*Your Settings*\n\n"
        f"📝 Name: {user['display_name'] or 'Not set'}\n"
        f"🤖 Companion: {user['companion_name'] or 'Not named'}\n"
        f"🌍 Timezone: {user['timezone'] or 'Not set'}\n"
        f"⏰ Daily message: {time_str}\n"
        f"💬 Style: {style_name}\n\n"
        f"To change settings, visit our website.",
    )


async def handle_pause_command(
    telegram_service: TelegramService,
    chat_id: int,
    telegram_user: TelegramUser,
):
    """Handle /pause command - pause daily messages."""
    db = await get_db()

    result = await db.execute(
        """
        UPDATE users
        SET preferences = jsonb_set(COALESCE(preferences, '{}'::jsonb), '{daily_messages_paused}', 'true')
        WHERE telegram_user_id = $1
        """,
        telegram_user.id,
    )

    await telegram_service.send_message(
        chat_id,
        "Daily messages paused. ⏸️\n\n"
        "I won't send you scheduled check-ins, but you can still chat with me anytime.\n\n"
        "Use /resume when you're ready to hear from me again.",
    )


async def handle_resume_command(
    telegram_service: TelegramService,
    chat_id: int,
    telegram_user: TelegramUser,
):
    """Handle /resume command - resume daily messages."""
    db = await get_db()

    result = await db.execute(
        """
        UPDATE users
        SET preferences = jsonb_set(COALESCE(preferences, '{}'::jsonb), '{daily_messages_paused}', 'false')
        WHERE telegram_user_id = $1
        """,
        telegram_user.id,
    )

    await telegram_service.send_message(
        chat_id,
        "Daily messages resumed! ▶️\n\n"
        "I'll check in with you at your usual time. Looking forward to it!",
    )


async def handle_help_command(telegram_service: TelegramService, chat_id: int):
    """Handle /help command."""
    await telegram_service.send_message(
        chat_id,
        "*What I Can Do*\n\n"
        "💬 *Chat* - Just send me a message anytime\n"
        "☀️ *Daily Check-ins* - I'll reach out at your preferred time\n\n"
        "*Commands*\n"
        "/settings - View your settings\n"
        "/pause - Pause daily messages\n"
        "/resume - Resume daily messages\n"
        "/help - Show this help\n\n"
        "To change settings like your timezone or message time, visit our website.",
    )


# =============================================================================
# Conversation Handler
# =============================================================================


async def handle_conversation_message(
    telegram_service: TelegramService,
    chat_id: int,
    telegram_user: TelegramUser,
    text: str,
):
    """Handle a regular conversation message."""
    db = await get_db()

    # Get user
    user = await db.fetchrow(
        """
        SELECT id, display_name, companion_name, support_style, timezone, location
        FROM users WHERE telegram_user_id = $1
        """,
        telegram_user.id,
    )

    if not user:
        await telegram_service.send_message(
            chat_id,
            "I don't recognize your account yet.\n\n"
            "Please sign up at our website and connect your Telegram to chat with me!",
        )
        return

    # Show typing indicator
    await telegram_service.send_typing_action(chat_id)

    # Get or create conversation
    conversation = await db.fetchrow(
        """
        SELECT id FROM conversations
        WHERE user_id = $1 AND channel = 'telegram'
        AND ended_at IS NULL
        AND started_at > NOW() - INTERVAL '24 hours'
        ORDER BY started_at DESC LIMIT 1
        """,
        user["id"],
    )

    if not conversation:
        conversation = await db.fetchrow(
            """
            INSERT INTO conversations (user_id, channel, initiated_by)
            VALUES ($1, 'telegram', 'user')
            RETURNING id
            """,
            user["id"],
        )

    conversation_id = conversation["id"]

    # Store user message
    await db.execute(
        """
        INSERT INTO companion_messages (conversation_id, role, content, telegram_message_id)
        VALUES ($1, 'user', $2, $3)
        """,
        conversation_id,
        text,
        telegram_user.id,  # Using user id as message tracking
    )

    # Get recent messages for context
    recent_messages = await db.fetch(
        """
        SELECT role, content FROM companion_messages
        WHERE conversation_id = $1
        ORDER BY created_at DESC LIMIT 10
        """,
        conversation_id,
    )
    recent_messages = [{"role": m["role"], "content": m["content"]} for m in reversed(recent_messages)]

    # Get user context
    context_rows = await db.fetch(
        """
        SELECT category, key, value, importance_score
        FROM user_context
        WHERE user_id = $1
        AND (expires_at IS NULL OR expires_at > NOW())
        ORDER BY importance_score DESC LIMIT 15
        """,
        user["id"],
    )
    user_context = [
        UserContext(
            category=row["category"],
            key=row["key"],
            value=row["value"],
            importance_score=row["importance_score"],
        )
        for row in context_rows
    ]

    # Build context for companion
    companion_service = get_companion_service()
    day_of_week, local_time = companion_service.get_local_time_context(
        user["timezone"] or "America/New_York"
    )

    context = ConversationContext(
        user_profile=UserProfile(
            user_id=str(user["id"]),
            display_name=user["display_name"],
            companion_name=user["companion_name"],
            support_style=user["support_style"] or "friendly_checkin",
            timezone=user["timezone"] or "America/New_York",
            location=user["location"],
        ),
        user_context=user_context,
        recent_messages=recent_messages,
        day_of_week=day_of_week,
        local_time=local_time,
        is_daily_message=False,
    )

    # Generate response
    system_prompt = companion_service.build_system_prompt(context)
    llm = LLMService.get_instance()

    try:
        # Build messages with system prompt
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(recent_messages)

        llm_response = await llm.generate(messages=messages)
        response_content = llm_response.content

        # Store assistant message
        await db.execute(
            """
            INSERT INTO companion_messages (conversation_id, role, content)
            VALUES ($1, 'assistant', $2)
            """,
            conversation_id,
            response_content,
        )

        # Send response
        await telegram_service.send_message(chat_id, response_content)

    except Exception as e:
        log.error(f"Failed to generate response: {e}", exc_info=True)
        await telegram_service.send_message(
            chat_id,
            "I'm having trouble thinking right now. Can you try again in a moment?",
        )


# =============================================================================
# Deep Link Endpoint (for web app)
# =============================================================================


@router.get("/link/{user_id}", response_model=DeepLinkResponse)
async def get_telegram_link(user_id: str):
    """
    Get a deep link URL for connecting a user's Telegram account.

    This endpoint should be called from the web app after authentication.
    """
    telegram_service = get_telegram_service()
    url = telegram_service.get_deep_link_url(user_id)

    return DeepLinkResponse(
        url=url,
        instructions="Click the link to open Telegram and connect your account. Then tap 'Start' in the chat.",
    )
