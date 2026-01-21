"""Onboarding API routes for Chat Companion.

Supports two onboarding paths (ADR-003):
1. Chat path - Conversational onboarding with companion
2. Quiz path - Structured quiz with personality typing (TODO)

Chat onboarding flow:
- GET /onboarding/chat - Get current message/state
- POST /onboarding/chat/respond - Process user response, advance flow
- POST /onboarding/chat/reset - Reset for testing
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Any, List
from datetime import datetime
from uuid import UUID
import json

from app.deps import get_db
from app.dependencies import get_current_user_id
from app.services.onboarding import ChatOnboardingService

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


class ChatOnboardingState(BaseModel):
    """Current state of chat onboarding."""

    message: Optional[str] = None
    step: str
    expects: Optional[str] = None
    options: Optional[List[str]] = None
    is_complete: bool


class ChatResponseRequest(BaseModel):
    """User response during chat onboarding."""

    response: str


class ChatResponseResult(BaseModel):
    """Result after processing user response."""

    success: bool
    is_complete: bool = False
    step: Optional[str] = None
    next_message: Optional[str] = None
    expects: Optional[str] = None
    options: Optional[List[str]] = None
    error: Optional[str] = None
    retry_message: Optional[str] = None


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


# ============================================================================
# Chat Onboarding Endpoints (ADR-003)
# ============================================================================


@router.get("/chat", response_model=ChatOnboardingState)
async def get_chat_onboarding_state(
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Get current chat onboarding state and message.

    Returns the companion's current message in the onboarding flow,
    along with what kind of response is expected.
    """
    service = ChatOnboardingService(db)
    result = await service.get_current_message(user_id)

    return ChatOnboardingState(
        message=result["message"],
        step=result["step"],
        expects=result.get("expects"),
        options=result.get("options"),
        is_complete=result["is_complete"],
    )


@router.post("/chat/respond", response_model=ChatResponseResult)
async def process_chat_response(
    request: ChatResponseRequest,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Process user's response during chat onboarding.

    Takes the user's text response, validates it based on expected input type,
    saves the appropriate data, and returns the next message in the flow.
    """
    if not request.response or not request.response.strip():
        return ChatResponseResult(
            success=False,
            error="Please provide a response.",
        )

    service = ChatOnboardingService(db)
    result = await service.process_response(user_id, request.response)

    return ChatResponseResult(
        success=result.get("success", False),
        is_complete=result.get("is_complete", False),
        step=result.get("step"),
        next_message=result.get("next_message"),
        expects=result.get("expects"),
        options=result.get("options"),
        error=result.get("error"),
        retry_message=result.get("retry_message"),
    )


@router.post("/chat/reset", response_model=ChatOnboardingState)
async def reset_chat_onboarding(
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Reset chat onboarding to the beginning.

    For testing and admin purposes. Clears all progress and starts fresh.
    """
    service = ChatOnboardingService(db)
    result = await service.reset_onboarding(user_id)

    return ChatOnboardingState(
        message=result["message"],
        step=result["step"],
        expects=result.get("expects"),
        options=result.get("options"),
        is_complete=result["is_complete"],
    )


@router.post("/chat/skip/{step}", response_model=ChatOnboardingState)
async def skip_to_step(
    step: str,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Skip to a specific onboarding step.

    For testing and admin purposes.
    Valid steps: intro, name, situation, support_style, wake_time, companion_name, confirmation
    """
    service = ChatOnboardingService(db)
    result = await service.skip_to_step(user_id, step)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return ChatOnboardingState(
        message=result["message"],
        step=result["step"],
        expects=result.get("expects"),
        options=result.get("options"),
        is_complete=result["is_complete"],
    )
