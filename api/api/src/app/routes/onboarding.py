"""Onboarding API routes for Chat Companion."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

from ..middleware.auth import get_current_user
from ..db import get_db

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
    user: dict = Depends(get_current_user),
):
    """Get current onboarding state for the user."""
    db = await get_db()

    result = await db.fetch_one(
        """
        SELECT user_id, current_step, completed_at, data, created_at, updated_at
        FROM onboarding
        WHERE user_id = :user_id
        """,
        {"user_id": user["id"]},
    )

    if not result:
        # Create new onboarding record
        await db.execute(
            """
            INSERT INTO onboarding (user_id, current_step, data)
            VALUES (:user_id, 'welcome', '{}')
            ON CONFLICT (user_id) DO NOTHING
            """,
            {"user_id": user["id"]},
        )
        result = await db.fetch_one(
            """
            SELECT user_id, current_step, completed_at, data, created_at, updated_at
            FROM onboarding
            WHERE user_id = :user_id
            """,
            {"user_id": user["id"]},
        )

    return OnboardingState(
        user_id=str(result["user_id"]),
        current_step=result["current_step"],
        completed_at=result["completed_at"],
        data=result["data"] or {},
        created_at=result["created_at"],
        updated_at=result["updated_at"],
    )


@router.patch("", response_model=OnboardingState)
async def update_onboarding(
    update: OnboardingUpdate,
    user: dict = Depends(get_current_user),
):
    """Update onboarding state."""
    db = await get_db()

    # First ensure record exists
    await db.execute(
        """
        INSERT INTO onboarding (user_id, current_step, data)
        VALUES (:user_id, 'welcome', '{}')
        ON CONFLICT (user_id) DO NOTHING
        """,
        {"user_id": user["id"]},
    )

    # Build update query
    updates = []
    params = {"user_id": user["id"]}

    if update.step is not None:
        updates.append("current_step = :step")
        params["step"] = update.step

    if update.data is not None:
        # Merge with existing data
        updates.append("data = data || :data::jsonb")
        params["data"] = update.data

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
        {"user_id": user["id"]},
    )

    return OnboardingState(
        user_id=str(result["user_id"]),
        current_step=result["current_step"],
        completed_at=result["completed_at"],
        data=result["data"] or {},
        created_at=result["created_at"],
        updated_at=result["updated_at"],
    )


@router.post("/complete", response_model=OnboardingState)
async def complete_onboarding(
    user: dict = Depends(get_current_user),
):
    """Mark onboarding as complete."""
    db = await get_db()

    # Update onboarding record
    await db.execute(
        """
        UPDATE onboarding
        SET completed_at = NOW(), current_step = 'complete', updated_at = NOW()
        WHERE user_id = :user_id
        """,
        {"user_id": user["id"]},
    )

    # Update user record
    await db.execute(
        """
        UPDATE users
        SET onboarding_completed_at = NOW(), updated_at = NOW()
        WHERE id = :user_id
        """,
        {"user_id": user["id"]},
    )

    # Return updated state
    result = await db.fetch_one(
        """
        SELECT user_id, current_step, completed_at, data, created_at, updated_at
        FROM onboarding
        WHERE user_id = :user_id
        """,
        {"user_id": user["id"]},
    )

    return OnboardingState(
        user_id=str(result["user_id"]),
        current_step=result["current_step"],
        completed_at=result["completed_at"],
        data=result["data"] or {},
        created_at=result["created_at"],
        updated_at=result["updated_at"],
    )
