"""Expo Push Notification Service.

Handles sending push notifications to mobile devices via Expo's push service.
Supports batch sending, receipt tracking, and token invalidation.
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

import httpx

logger = logging.getLogger(__name__)


class PushPriority(str, Enum):
    DEFAULT = "default"
    HIGH = "high"


class PushStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    CLICKED = "clicked"


@dataclass
class PushMessage:
    """A push notification message."""
    to: str
    title: str
    body: str
    data: Dict[str, Any] = field(default_factory=dict)
    sound: str = "default"
    priority: PushPriority = PushPriority.HIGH
    badge: Optional[int] = None
    category_id: Optional[str] = None
    channel_id: Optional[str] = None  # Android notification channel


@dataclass
class PushResult:
    """Result of sending a push notification."""
    notification_id: UUID
    device_id: UUID
    success: bool
    receipt_id: Optional[str] = None
    error: Optional[str] = None


class ExpoPushService:
    """Service for sending push notifications via Expo."""

    EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"
    EXPO_RECEIPTS_URL = "https://exp.host/--/api/v2/push/getReceipts"

    def __init__(self, db):
        self.db = db

    async def send_notification(
        self,
        user_id: UUID,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        scheduled_message_id: Optional[UUID] = None,
        channel_id: str = "daily-checkin",
    ) -> List[PushResult]:
        """Send push notification to all user's active devices.

        Args:
            user_id: The user to send to
            title: Notification title
            body: Notification body text
            data: Optional data payload (for deep linking)
            scheduled_message_id: Optional link to scheduled message
            channel_id: Android notification channel ID

        Returns:
            List of PushResult for each device
        """
        # Get all active push tokens for user
        tokens = await self.db.fetch_all(
            "SELECT * FROM get_user_push_tokens(:user_id)",
            {"user_id": str(user_id)}
        )

        if not tokens:
            logger.info(f"No push tokens found for user {user_id}")
            return []

        results: List[PushResult] = []
        messages: List[Dict[str, Any]] = []
        notification_ids: List[UUID] = []

        for token in tokens:
            # Build Expo push message
            msg = {
                "to": token["push_token"],
                "title": title,
                "body": body,
                "data": data or {},
                "sound": "default",
                "priority": "high",
            }

            # Add Android channel
            if token["platform"] == "android":
                msg["channelId"] = channel_id

            messages.append(msg)

            # Record notification in database
            row = await self.db.fetch_one(
                """
                INSERT INTO push_notifications
                    (user_id, device_id, scheduled_message_id, title, body, data, status)
                VALUES (:user_id, :device_id, :scheduled_message_id, :title, :body, :data, 'pending')
                RETURNING id
                """,
                {
                    "user_id": str(user_id),
                    "device_id": str(token["device_id"]),
                    "scheduled_message_id": str(scheduled_message_id) if scheduled_message_id else None,
                    "title": title,
                    "body": body,
                    "data": json.dumps(data or {}),
                }
            )
            notification_ids.append(row["id"])

        # Send batch to Expo Push API
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.EXPO_PUSH_URL,
                    json=messages,
                    headers={
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                    }
                )

                if response.status_code == 200:
                    response_data = response.json()
                    tickets = response_data.get("data", [])

                    for i, ticket in enumerate(tickets):
                        notification_id = notification_ids[i]
                        device_id = tokens[i]["device_id"]

                        if ticket.get("status") == "ok":
                            receipt_id = ticket.get("id")
                            await self.db.execute(
                                """
                                UPDATE push_notifications
                                SET status = 'sent',
                                    expo_receipt_id = :receipt_id,
                                    sent_at = NOW()
                                WHERE id = :id
                                """,
                                {"id": str(notification_id), "receipt_id": receipt_id}
                            )
                            results.append(PushResult(
                                notification_id=notification_id,
                                device_id=device_id,
                                success=True,
                                receipt_id=receipt_id,
                            ))
                        else:
                            error_msg = ticket.get("message", "Unknown error")
                            await self.db.execute(
                                """
                                UPDATE push_notifications
                                SET status = 'failed',
                                    error_message = :error,
                                    sent_at = NOW()
                                WHERE id = :id
                                """,
                                {"id": str(notification_id), "error": error_msg}
                            )
                            results.append(PushResult(
                                notification_id=notification_id,
                                device_id=device_id,
                                success=False,
                                error=error_msg,
                            ))

                            # Handle invalid push token
                            if "DeviceNotRegistered" in error_msg:
                                await self._invalidate_device(device_id)

                else:
                    error_msg = f"Expo API error: {response.status_code}"
                    logger.error(f"{error_msg} - {response.text}")
                    # Mark all as failed
                    for i, notification_id in enumerate(notification_ids):
                        await self.db.execute(
                            """
                            UPDATE push_notifications
                            SET status = 'failed', error_message = :error
                            WHERE id = :id
                            """,
                            {"id": str(notification_id), "error": error_msg}
                        )
                        results.append(PushResult(
                            notification_id=notification_id,
                            device_id=tokens[i]["device_id"],
                            success=False,
                            error=error_msg,
                        ))

        except httpx.RequestError as e:
            error_msg = f"Network error: {str(e)}"
            logger.error(f"Failed to send push notifications: {error_msg}")
            for i, notification_id in enumerate(notification_ids):
                await self.db.execute(
                    """
                    UPDATE push_notifications
                    SET status = 'failed', error_message = :error
                    WHERE id = :id
                    """,
                    {"id": str(notification_id), "error": error_msg}
                )
                results.append(PushResult(
                    notification_id=notification_id,
                    device_id=tokens[i]["device_id"],
                    success=False,
                    error=error_msg,
                ))

        return results

    async def check_receipts(self, receipt_ids: List[str]) -> Dict[str, str]:
        """Check delivery receipts from Expo.

        Args:
            receipt_ids: List of Expo receipt IDs to check

        Returns:
            Dict mapping receipt_id to status ('ok', 'error', or error message)
        """
        if not receipt_ids:
            return {}

        results = {}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.EXPO_RECEIPTS_URL,
                    json={"ids": receipt_ids},
                    headers={
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                    }
                )

                if response.status_code == 200:
                    receipts = response.json().get("data", {})

                    for receipt_id, receipt in receipts.items():
                        status = receipt.get("status")

                        if status == "ok":
                            await self.db.execute(
                                """
                                UPDATE push_notifications
                                SET status = 'delivered', delivered_at = NOW()
                                WHERE expo_receipt_id = :receipt_id
                                """,
                                {"receipt_id": receipt_id}
                            )
                            results[receipt_id] = "ok"

                        elif status == "error":
                            error_details = receipt.get("details", {})
                            error_type = error_details.get("error", "UnknownError")

                            await self.db.execute(
                                """
                                UPDATE push_notifications
                                SET status = 'failed', error_message = :error
                                WHERE expo_receipt_id = :receipt_id
                                """,
                                {"receipt_id": receipt_id, "error": error_type}
                            )
                            results[receipt_id] = error_type

                            # Handle invalid token
                            if error_type == "DeviceNotRegistered":
                                await self._invalidate_token_by_receipt(receipt_id)

        except httpx.RequestError as e:
            logger.error(f"Failed to check receipts: {e}")

        return results

    async def mark_clicked(self, notification_id: UUID, user_id: UUID) -> bool:
        """Mark a notification as clicked (for analytics).

        Args:
            notification_id: The notification ID
            user_id: The user ID (for verification)

        Returns:
            True if updated, False if not found
        """
        result = await self.db.execute(
            """
            UPDATE push_notifications
            SET status = 'clicked', clicked_at = NOW()
            WHERE id = :id AND user_id = :user_id
            """,
            {"id": str(notification_id), "user_id": str(user_id)}
        )
        return result != "UPDATE 0"

    async def get_pending_receipts(self, limit: int = 100) -> List[str]:
        """Get receipt IDs for notifications that need status checking.

        Args:
            limit: Maximum number of receipts to return

        Returns:
            List of Expo receipt IDs
        """
        rows = await self.db.fetch_all(
            """
            SELECT expo_receipt_id
            FROM push_notifications
            WHERE status = 'sent'
              AND expo_receipt_id IS NOT NULL
              AND sent_at > NOW() - INTERVAL '24 hours'
            ORDER BY sent_at ASC
            LIMIT :limit
            """,
            {"limit": limit}
        )
        return [row["expo_receipt_id"] for row in rows]

    async def _invalidate_device(self, device_id: UUID) -> None:
        """Mark a device as inactive due to invalid push token."""
        await self.db.execute(
            """
            UPDATE user_devices
            SET is_active = false, push_token = NULL, updated_at = NOW()
            WHERE id = :device_id
            """,
            {"device_id": str(device_id)}
        )
        logger.info(f"Invalidated device {device_id} due to invalid push token")

    async def _invalidate_token_by_receipt(self, receipt_id: str) -> None:
        """Invalidate device token based on receipt ID."""
        await self.db.execute(
            """
            UPDATE user_devices
            SET is_active = false, push_token = NULL, updated_at = NOW()
            WHERE id = (
                SELECT device_id FROM push_notifications
                WHERE expo_receipt_id = :receipt_id
            )
            """,
            {"receipt_id": receipt_id}
        )
        logger.info(f"Invalidated device for receipt {receipt_id}")

    async def get_notification_history(
        self,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get notification history for a user.

        Args:
            user_id: The user ID
            limit: Maximum notifications to return
            offset: Offset for pagination

        Returns:
            List of notification records
        """
        rows = await self.db.fetch_all(
            """
            SELECT id, title, body, status, sent_at, delivered_at, clicked_at, created_at
            FROM push_notifications
            WHERE user_id = :user_id
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
            """,
            {"user_id": str(user_id), "limit": limit, "offset": offset}
        )
        return [dict(row) for row in rows]
