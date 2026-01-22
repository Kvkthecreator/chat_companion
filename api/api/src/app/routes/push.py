"""Push notification API routes.

Provides endpoints for testing push notifications and viewing history.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.deps import get_db
from app.dependencies import get_current_user_id
from app.services.push import ExpoPushService

router = APIRouter(prefix="/push", tags=["Push Notifications"])


# =============================================================================
# Request/Response Models
# =============================================================================

class TestPushRequest(BaseModel):
    """Request to send a test push notification."""
    title: Optional[str] = "Test Notification"
    body: Optional[str] = "This is a test push notification from Daisy!"
    device_id: Optional[str] = None  # Send to specific device, or all if None


class PushHistoryItem(BaseModel):
    """A push notification history item."""
    id: str
    title: str
    body: str
    status: str
    sent_at: Optional[str] = None
    delivered_at: Optional[str] = None
    clicked_at: Optional[str] = None
    created_at: str


class PushStatsResponse(BaseModel):
    """Push notification statistics."""
    total_sent: int
    total_delivered: int
    total_clicked: int
    total_failed: int
    delivery_rate: float
    click_rate: float


# =============================================================================
# Endpoints
# =============================================================================

@router.post("/test", status_code=status.HTTP_200_OK)
async def send_test_notification(
    data: TestPushRequest,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Send a test push notification to the current user's devices.

    Useful for testing that push notifications are working correctly.
    """
    push_service = ExpoPushService(db)

    results = await push_service.send_notification(
        user_id=user_id,
        title=data.title,
        body=data.body,
        data={"type": "test"},
    )

    if not results:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active devices with push tokens found",
        )

    successful = sum(1 for r in results if r.success)
    failed = len(results) - successful

    return {
        "status": "sent",
        "devices_targeted": len(results),
        "successful": successful,
        "failed": failed,
    }


@router.get("/history", response_model=List[PushHistoryItem])
async def get_notification_history(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Get push notification history for the current user."""
    push_service = ExpoPushService(db)

    notifications = await push_service.get_notification_history(
        user_id=user_id,
        limit=limit,
        offset=offset,
    )

    return [
        PushHistoryItem(
            id=str(n["id"]),
            title=n["title"],
            body=n["body"],
            status=n["status"],
            sent_at=str(n["sent_at"]) if n["sent_at"] else None,
            delivered_at=str(n["delivered_at"]) if n["delivered_at"] else None,
            clicked_at=str(n["clicked_at"]) if n["clicked_at"] else None,
            created_at=str(n["created_at"]),
        )
        for n in notifications
    ]


@router.patch("/{notification_id}/clicked")
async def mark_notification_clicked(
    notification_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Mark a notification as clicked.

    Called by the mobile app when the user taps on a notification.
    Used for analytics and engagement tracking.
    """
    push_service = ExpoPushService(db)

    updated = await push_service.mark_clicked(
        notification_id=notification_id,
        user_id=user_id,
    )

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    return {"status": "marked_clicked"}


@router.get("/stats", response_model=PushStatsResponse)
async def get_push_stats(
    days: int = Query(7, ge=1, le=30),
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Get push notification statistics for the current user.

    Returns delivery and click rates for the specified time period.
    """
    row = await db.fetch_one(
        """
        SELECT
            COUNT(*) FILTER (WHERE status IN ('sent', 'delivered', 'clicked')) as total_sent,
            COUNT(*) FILTER (WHERE status IN ('delivered', 'clicked')) as total_delivered,
            COUNT(*) FILTER (WHERE status = 'clicked') as total_clicked,
            COUNT(*) FILTER (WHERE status = 'failed') as total_failed
        FROM push_notifications
        WHERE user_id = :user_id
          AND created_at > NOW() - (:days || ' days')::interval
        """,
        {"user_id": str(user_id), "days": days}
    )

    total_sent = int(row["total_sent"]) if row["total_sent"] else 0
    total_delivered = int(row["total_delivered"]) if row["total_delivered"] else 0
    total_clicked = int(row["total_clicked"]) if row["total_clicked"] else 0
    total_failed = int(row["total_failed"]) if row["total_failed"] else 0

    delivery_rate = (total_delivered / total_sent * 100) if total_sent > 0 else 0
    click_rate = (total_clicked / total_delivered * 100) if total_delivered > 0 else 0

    return PushStatsResponse(
        total_sent=total_sent,
        total_delivered=total_delivered,
        total_clicked=total_clicked,
        total_failed=total_failed,
        delivery_rate=round(delivery_rate, 1),
        click_rate=round(click_rate, 1),
    )
