"""
Telegram Bot Service - Handles Telegram bot operations.

Handles:
- Sending messages to users
- Processing incoming messages
- Deep linking for account connection
- Webhook processing
"""

import hashlib
import hmac
import logging
import os
from typing import Optional

import httpx
from pydantic import BaseModel

log = logging.getLogger(__name__)


# =============================================================================
# Data Models
# =============================================================================


class TelegramUser(BaseModel):
    """Telegram user info from an update."""

    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None


class TelegramMessage(BaseModel):
    """Telegram message from an update."""

    message_id: int
    from_user: Optional[TelegramUser] = None
    chat_id: int
    text: Optional[str] = None
    date: int


class TelegramUpdate(BaseModel):
    """Telegram webhook update."""

    update_id: int
    message: Optional[TelegramMessage] = None


# =============================================================================
# Telegram Service
# =============================================================================


class TelegramService:
    """Service for interacting with Telegram Bot API."""

    _instance: Optional["TelegramService"] = None

    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.client = httpx.AsyncClient(timeout=30.0)

    @classmethod
    def get_instance(cls) -> "TelegramService":
        """Get the singleton instance."""
        if cls._instance is None:
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            if not bot_token:
                raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")
            cls._instance = cls(bot_token)
        return cls._instance

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    # =========================================================================
    # Core API Methods
    # =========================================================================

    async def _call_api(self, method: str, data: dict) -> dict:
        """Make a call to the Telegram Bot API."""
        url = f"{self.base_url}/{method}"
        try:
            response = await self.client.post(url, json=data)
            response.raise_for_status()
            result = response.json()
            if not result.get("ok"):
                log.error(f"Telegram API error: {result}")
                raise Exception(f"Telegram API error: {result.get('description', 'Unknown error')}")
            return result.get("result", {})
        except httpx.HTTPStatusError as e:
            log.error(f"Telegram API HTTP error: {e}")
            raise
        except Exception as e:
            log.error(f"Telegram API error: {e}")
            raise

    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = "Markdown",
        reply_to_message_id: Optional[int] = None,
    ) -> int:
        """
        Send a message to a Telegram chat.

        Returns the message_id of the sent message.
        """
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
        }
        if reply_to_message_id:
            data["reply_to_message_id"] = reply_to_message_id

        result = await self._call_api("sendMessage", data)
        return result.get("message_id", 0)

    async def send_typing_action(self, chat_id: int):
        """Send typing indicator to show the bot is 'typing'."""
        await self._call_api("sendChatAction", {"chat_id": chat_id, "action": "typing"})

    async def get_me(self) -> dict:
        """Get bot info."""
        return await self._call_api("getMe", {})

    async def set_webhook(self, url: str, secret_token: Optional[str] = None) -> bool:
        """Set the webhook URL for receiving updates."""
        data = {"url": url}
        if secret_token:
            data["secret_token"] = secret_token
        result = await self._call_api("setWebhook", data)
        return result is not None

    async def delete_webhook(self) -> bool:
        """Delete the webhook."""
        result = await self._call_api("deleteWebhook", {})
        return result is not None

    # =========================================================================
    # Deep Linking
    # =========================================================================

    @staticmethod
    def generate_deep_link_payload(user_id: str) -> str:
        """
        Generate a deep link payload for connecting a web account to Telegram.

        The payload is a hash of the user_id that can be verified later.
        """
        secret = os.getenv("TELEGRAM_WEBHOOK_SECRET", "default-secret")
        # Create a short hash that includes the user_id
        payload = hmac.new(
            secret.encode(), user_id.encode(), hashlib.sha256
        ).hexdigest()[:16]
        return f"{user_id[:8]}_{payload}"

    @staticmethod
    def verify_deep_link_payload(payload: str) -> Optional[str]:
        """
        Verify a deep link payload and extract the user_id prefix.

        Returns the user_id prefix if valid, None otherwise.
        Note: Full verification requires looking up the user by prefix.
        """
        if "_" not in payload:
            return None
        parts = payload.split("_")
        if len(parts) != 2:
            return None
        return parts[0]  # Return user_id prefix for lookup

    def get_deep_link_url(self, user_id: str) -> str:
        """Get the deep link URL for a user to connect their account."""
        bot_username = os.getenv("TELEGRAM_BOT_USERNAME", "YourBotName")
        payload = self.generate_deep_link_payload(user_id)
        return f"https://t.me/{bot_username}?start={payload}"

    # =========================================================================
    # Webhook Verification
    # =========================================================================

    @staticmethod
    def verify_webhook_secret(secret_token: str) -> bool:
        """Verify the webhook secret token from the request header."""
        expected_secret = os.getenv("TELEGRAM_WEBHOOK_SECRET")
        if not expected_secret:
            log.warning("TELEGRAM_WEBHOOK_SECRET not set, skipping verification")
            return True
        return hmac.compare_digest(secret_token, expected_secret)

    # =========================================================================
    # Command Parsing
    # =========================================================================

    @staticmethod
    def parse_command(text: str) -> tuple[Optional[str], Optional[str]]:
        """
        Parse a Telegram command from message text.

        Returns (command, args) tuple. Command includes the leading slash.
        """
        if not text or not text.startswith("/"):
            return None, None

        parts = text.split(maxsplit=1)
        command = parts[0].lower()

        # Remove @botname suffix if present
        if "@" in command:
            command = command.split("@")[0]

        args = parts[1] if len(parts) > 1 else None
        return command, args

    # =========================================================================
    # Message Formatting
    # =========================================================================

    @staticmethod
    def escape_markdown(text: str) -> str:
        """Escape special characters for Telegram Markdown."""
        # Characters that need escaping in MarkdownV2
        special_chars = ["_", "*", "[", "]", "(", ")", "~", "`", ">", "#", "+", "-", "=", "|", "{", "}", ".", "!"]
        for char in special_chars:
            text = text.replace(char, f"\\{char}")
        return text


# =============================================================================
# Module-level functions
# =============================================================================


def get_telegram_service() -> TelegramService:
    """Get the Telegram service singleton."""
    return TelegramService.get_instance()
