"""
Email Service - Handles email delivery via Resend.

Used for:
- Daily check-in messages for web users
- Transactional emails (password reset, etc.)
"""

import logging
import os
from dataclasses import dataclass
from typing import Optional

import httpx

log = logging.getLogger(__name__)


@dataclass
class EmailResult:
    """Result of sending an email."""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None


class ResendEmailService:
    """Email service using Resend API."""

    API_URL = "https://api.resend.com/emails"

    def __init__(self):
        self.api_key = os.getenv("RESEND_API_KEY")
        self.from_email = os.getenv("RESEND_FROM_EMAIL", "Daisy <daisy@updates.yourdomain.com>")

        if not self.api_key:
            log.warning("RESEND_API_KEY not configured - email delivery disabled")

    @property
    def is_configured(self) -> bool:
        """Check if email service is properly configured."""
        return bool(self.api_key)

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> EmailResult:
        """
        Send an email via Resend.

        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_content: HTML body of the email
            text_content: Plain text fallback (optional, derived from html if not provided)
            reply_to: Reply-to address (optional)

        Returns:
            EmailResult with success status and message ID or error
        """
        if not self.is_configured:
            log.warning("Email service not configured, skipping send")
            return EmailResult(success=False, error="Email service not configured")

        payload = {
            "from": self.from_email,
            "to": [to_email],
            "subject": subject,
            "html": html_content,
        }

        if text_content:
            payload["text"] = text_content

        if reply_to:
            payload["reply_to"] = reply_to

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.API_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )

                if response.status_code == 200:
                    data = response.json()
                    log.info(f"Email sent successfully to {to_email}, id={data.get('id')}")
                    return EmailResult(success=True, message_id=data.get("id"))
                else:
                    error_msg = f"Resend API error: {response.status_code} - {response.text}"
                    log.error(error_msg)
                    return EmailResult(success=False, error=error_msg)

        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            log.error(error_msg, exc_info=True)
            return EmailResult(success=False, error=error_msg)

    async def send_daily_checkin(
        self,
        to_email: str,
        user_name: str,
        companion_name: str,
        message: str,
        conversation_url: str,
    ) -> EmailResult:
        """
        Send a daily check-in email.

        Args:
            to_email: User's email address
            user_name: User's display name
            companion_name: Companion's name (e.g., "Daisy")
            message: The daily check-in message content
            conversation_url: URL to continue the conversation

        Returns:
            EmailResult
        """
        subject = f"{companion_name} is thinking of you"

        html_content = self._build_daily_checkin_html(
            user_name=user_name,
            companion_name=companion_name,
            message=message,
            conversation_url=conversation_url,
        )

        text_content = self._build_daily_checkin_text(
            user_name=user_name,
            companion_name=companion_name,
            message=message,
            conversation_url=conversation_url,
        )

        return await self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
        )

    def _build_daily_checkin_html(
        self,
        user_name: str,
        companion_name: str,
        message: str,
        conversation_url: str,
    ) -> str:
        """Build HTML email template for daily check-in."""
        # Escape HTML in message content
        import html
        escaped_message = html.escape(message).replace("\n", "<br>")

        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{companion_name} is thinking of you</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <tr>
            <td style="background-color: #ffffff; border-radius: 12px; padding: 32px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                <!-- Header -->
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                    <tr>
                        <td style="padding-bottom: 24px; border-bottom: 1px solid #eee;">
                            <h1 style="margin: 0; font-size: 24px; font-weight: 600; color: #333;">
                                {companion_name}
                            </h1>
                            <p style="margin: 4px 0 0 0; font-size: 14px; color: #666;">
                                Your daily check-in
                            </p>
                        </td>
                    </tr>
                </table>

                <!-- Message -->
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                    <tr>
                        <td style="padding: 24px 0;">
                            <p style="margin: 0; font-size: 16px; line-height: 1.6; color: #333;">
                                {escaped_message}
                            </p>
                        </td>
                    </tr>
                </table>

                <!-- CTA Button -->
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                    <tr>
                        <td style="padding: 16px 0 24px 0;">
                            <a href="{conversation_url}"
                               style="display: inline-block; padding: 14px 28px; background-color: #FF6B6B; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                                Reply to {companion_name}
                            </a>
                        </td>
                    </tr>
                </table>

                <!-- Footer -->
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                    <tr>
                        <td style="padding-top: 24px; border-top: 1px solid #eee;">
                            <p style="margin: 0; font-size: 12px; color: #999; line-height: 1.5;">
                                You're receiving this because you signed up for daily check-ins from {companion_name}.<br>
                                <a href="{conversation_url.rsplit('/', 1)[0]}/settings" style="color: #666;">Manage your preferences</a>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

    def _build_daily_checkin_text(
        self,
        user_name: str,
        companion_name: str,
        message: str,
        conversation_url: str,
    ) -> str:
        """Build plain text email for daily check-in."""
        return f"""{companion_name} - Your daily check-in

{message}

---

Reply to {companion_name}: {conversation_url}

You're receiving this because you signed up for daily check-ins.
Manage preferences: {conversation_url.rsplit('/', 1)[0]}/settings
"""


# Singleton instance
_email_service: Optional[ResendEmailService] = None


def get_email_service() -> ResendEmailService:
    """Get or create the email service singleton."""
    global _email_service
    if _email_service is None:
        _email_service = ResendEmailService()
    return _email_service
