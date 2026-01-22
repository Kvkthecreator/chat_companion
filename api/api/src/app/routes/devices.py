"""Device management API routes.

Handles device registration, push token updates, and device listing
for mobile app push notification support.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.deps import get_db
from app.dependencies import get_current_user_id

router = APIRouter(prefix="/devices", tags=["Devices"])


# =============================================================================
# Request/Response Models
# =============================================================================

class DeviceRegister(BaseModel):
    """Request to register a device."""
    device_id: str  # Unique device identifier from Expo
    platform: str  # 'ios' or 'android'
    push_token: Optional[str] = None  # Expo push token
    app_version: Optional[str] = None
    os_version: Optional[str] = None
    device_model: Optional[str] = None


class DeviceUpdate(BaseModel):
    """Request to update device info."""
    push_token: Optional[str] = None
    app_version: Optional[str] = None
    is_active: Optional[bool] = None


class DeviceResponse(BaseModel):
    """Device info response."""
    id: str
    device_id: str
    platform: str
    has_push_token: bool
    app_version: Optional[str] = None
    last_active_at: str


# =============================================================================
# Endpoints
# =============================================================================

@router.post("", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def register_device(
    data: DeviceRegister,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Register a device or update existing registration.

    This endpoint handles both new device registration and updating
    existing devices (upsert behavior based on user_id + device_id).
    """
    if data.platform not in ("ios", "android"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Platform must be 'ios' or 'android'",
        )

    row = await db.fetch_one(
        """
        INSERT INTO user_devices (
            user_id, device_id, platform, push_token,
            push_token_updated_at, app_version, os_version, device_model
        )
        VALUES (
            :user_id, :device_id, :platform, :push_token,
            CASE WHEN :push_token IS NOT NULL THEN NOW() END,
            :app_version, :os_version, :device_model
        )
        ON CONFLICT (user_id, device_id)
        DO UPDATE SET
            push_token = EXCLUDED.push_token,
            push_token_updated_at = CASE
                WHEN EXCLUDED.push_token IS NOT NULL AND EXCLUDED.push_token != user_devices.push_token
                THEN NOW()
                ELSE user_devices.push_token_updated_at
            END,
            app_version = COALESCE(EXCLUDED.app_version, user_devices.app_version),
            os_version = COALESCE(EXCLUDED.os_version, user_devices.os_version),
            device_model = COALESCE(EXCLUDED.device_model, user_devices.device_model),
            is_active = true,
            last_active_at = NOW(),
            updated_at = NOW()
        RETURNING
            id,
            device_id,
            platform,
            push_token IS NOT NULL as has_push_token,
            app_version,
            last_active_at::text
        """,
        {
            "user_id": str(user_id),
            "device_id": data.device_id,
            "platform": data.platform,
            "push_token": data.push_token,
            "app_version": data.app_version,
            "os_version": data.os_version,
            "device_model": data.device_model,
        }
    )

    return DeviceResponse(
        id=str(row["id"]),
        device_id=row["device_id"],
        platform=row["platform"],
        has_push_token=row["has_push_token"],
        app_version=row["app_version"],
        last_active_at=row["last_active_at"],
    )


@router.patch("/{device_id}")
async def update_device(
    device_id: str,
    data: DeviceUpdate,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Update device push token or status.

    Args:
        device_id: The device identifier (not UUID, the Expo device ID)
    """
    updates = ["last_active_at = NOW()", "updated_at = NOW()"]
    values = {"user_id": str(user_id), "device_id": device_id}

    if data.push_token is not None:
        updates.append("push_token = :push_token")
        updates.append("push_token_updated_at = NOW()")
        values["push_token"] = data.push_token

    if data.is_active is not None:
        updates.append("is_active = :is_active")
        values["is_active"] = data.is_active
        # Clear push token if deactivating
        if not data.is_active:
            updates.append("push_token = NULL")

    if data.app_version is not None:
        updates.append("app_version = :app_version")
        values["app_version"] = data.app_version

    query = f"""
        UPDATE user_devices
        SET {', '.join(updates)}
        WHERE user_id = :user_id AND device_id = :device_id
        RETURNING id
    """

    row = await db.fetch_one(query, values)

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    return {"status": "updated", "device_id": device_id}


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unregister_device(
    device_id: str,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Unregister a device (soft delete).

    Marks the device as inactive and clears the push token.
    The device record is preserved for analytics.
    """
    result = await db.execute(
        """
        UPDATE user_devices
        SET is_active = false, push_token = NULL, updated_at = NOW()
        WHERE user_id = :user_id AND device_id = :device_id
        """,
        {"user_id": str(user_id), "device_id": device_id}
    )

    # Don't error if device doesn't exist - idempotent delete


@router.get("", response_model=List[DeviceResponse])
async def list_devices(
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """List all registered devices for the current user."""
    rows = await db.fetch_all(
        """
        SELECT
            id,
            device_id,
            platform,
            push_token IS NOT NULL as has_push_token,
            app_version,
            last_active_at::text
        FROM user_devices
        WHERE user_id = :user_id AND is_active = true
        ORDER BY last_active_at DESC
        """,
        {"user_id": str(user_id)}
    )

    return [
        DeviceResponse(
            id=str(row["id"]),
            device_id=row["device_id"],
            platform=row["platform"],
            has_push_token=row["has_push_token"],
            app_version=row["app_version"],
            last_active_at=row["last_active_at"],
        )
        for row in rows
    ]


@router.post("/{device_id}/heartbeat")
async def device_heartbeat(
    device_id: str,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Update device last_active_at timestamp.

    Called periodically by the mobile app to indicate the device is still active.
    """
    result = await db.execute(
        """
        UPDATE user_devices
        SET last_active_at = NOW(), updated_at = NOW()
        WHERE user_id = :user_id AND device_id = :device_id AND is_active = true
        """,
        {"user_id": str(user_id), "device_id": device_id}
    )

    if result == "UPDATE 0":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found or inactive",
        )

    return {"status": "ok"}
