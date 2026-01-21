"""Onboarding API routes for Chat Companion."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime
from uuid import UUID
import json

from app.deps import get_db
from app.dependencies import get_current_user_id

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


class OnboardingState(BaseModel):
    """Onboarding state response."""

    user_id: str
    current_step: str
    completed_at: Optional[datetime] = None
    data: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class OnboardingUpdate(BaseModel):
    """Onboarding update request."""

    step: Optional[str] = None
    data: Optional[dict[str, Any]] = None


@router.get("", response_model=OnboardingState)
async def get_onboarding(
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Get current onboarding state for the user."""
    result = await db.fetch_one(
        """
        SELECT user_id, current_step, completed_at, data, created_at, updated_at
        FROM onboarding
        WHERE user_id = :user_id
        """,
        {"user_id": str(user_id)},
    )

    if not result:
        # Create new onboarding record
        await db.execute(
            """
            INSERT INTO onboarding (user_id, current_step, data)
            VALUES (:user_id, 'welcome', '{}')
            ON CONFLICT (user_id) DO NOTHING
            """,
            {"user_id": str(user_id)},
        )
        result = await db.fetch_one(
            """
            SELECT user_id, current_step, completed_at, data, created_at, updated_at
            FROM onboarding
            WHERE user_id = :user_id
            """,
            {"user_id": str(user_id)},
        )

    data = result["data"]
    if isinstance(data, str):
        data = json.loads(data)

    return OnboardingState(
        user_id=str(result["user_id"]),
        current_step=result["current_step"],
        completed_at=result["completed_at"],
        data=data or {},
        created_at=result["created_at"],
        updated_at=result["updated_at"],
    )


@router.patch("", response_model=OnboardingState)
async def update_onboarding(
    update: OnboardingUpdate,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Update onboarding state."""
    # First ensure record exists
    await db.execute(
        """
        INSERT INTO onboarding (user_id, current_step, data)
        VALUES (:user_id, 'welcome', '{}')
        ON CONFLICT (user_id) DO NOTHING
        """,
        {"user_id": str(user_id)},
    )

    # Build update query
    updates = []
    params = {"user_id": str(user_id)}

    if update.step is not None:
        updates.append("current_step = :step")
        params["step"] = update.step

    if update.data is not None:
        # Merge with existing data
        updates.append("data = data || :data::jsonb")
        params["data"] = json.dumps(update.data)

    if updates:
        await db.execute(
            f"""
            UPDATE onboarding
            SET {", ".join(updates)}, updated_at = NOW()
            WHERE user_id = :user_id
            """,
            params,
        )

    # Return updated state
    result = await db.fetch_one(
        """
        SELECT user_id, current_step, completed_at, data, created_at, updated_at
        FROM onboarding
        WHERE user_id = :user_id
        """,
        {"user_id": str(user_id)},
    )

    data = result["data"]
    if isinstance(data, str):
        data = json.loads(data)

    return OnboardingState(
        user_id=str(result["user_id"]),
        current_step=result["current_step"],
        completed_at=result["completed_at"],
        data=data or {},
        created_at=result["created_at"],
        updated_at=result["updated_at"],
    )


@router.post("/complete", response_model=OnboardingState)
async def complete_onboarding(
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Mark onboarding as complete."""
    # Update onboarding record
    await db.execute(
        """
        UPDATE onboarding
        SET completed_at = NOW(), current_step = 'complete', updated_at = NOW()
        WHERE user_id = :user_id
        """,
        {"user_id": str(user_id)},
    )

    # Update user record
    await db.execute(
        """
        UPDATE users
        SET onboarding_completed_at = NOW(), updated_at = NOW()
        WHERE id = :user_id
        """,
        {"user_id": str(user_id)},
    )

    # Return updated state
    result = await db.fetch_one(
        """
        SELECT user_id, current_step, completed_at, data, created_at, updated_at
        FROM onboarding
        WHERE user_id = :user_id
        """,
        {"user_id": str(user_id)},
    )

    data = result["data"]
    if isinstance(data, str):
        data = json.loads(data)

    return OnboardingState(
        user_id=str(result["user_id"]),
        current_step=result["current_step"],
        completed_at=result["completed_at"],
        data=data or {},
        created_at=result["created_at"],
        updated_at=result["updated_at"],
    )
