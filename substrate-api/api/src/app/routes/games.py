"""Games API routes - bounded episode gameplay.

Endpoints for game-type episodes like the Flirt Test.
These are public-facing routes that work with or without authentication.

Reference: docs/plans/FLIRT_TEST_IMPLEMENTATION_PLAN.md
"""

import json
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.deps import get_db
from app.dependencies import get_optional_user_id, get_current_user_id
from app.services.games import GamesService
from app.services.director import DirectorService

router = APIRouter(prefix="/games", tags=["Games"])


# ============================================================================
# Request/Response Models
# ============================================================================

class GameStartRequest(BaseModel):
    """Request to start a game."""
    character_choice: Optional[str] = None  # "m" or "f" for character preference


class GameStartResponse(BaseModel):
    """Response from starting a game."""
    session_id: str
    character_id: str
    character_name: str
    character_avatar_url: Optional[str]
    opening_line: str
    turn_budget: int
    situation: str


class GameMessageRequest(BaseModel):
    """Request to send a message in a game."""
    content: str


class GameMessageResponse(BaseModel):
    """Response from a game message."""
    message_content: str
    turn_count: int
    turns_remaining: int
    is_complete: bool
    mood: Optional[str] = None


class GameResultResponse(BaseModel):
    """Response with game evaluation result."""
    evaluation_type: str
    result: dict
    share_id: str
    share_url: str
    character_id: str
    character_name: str
    series_id: Optional[str] = None


class ShareableResultResponse(BaseModel):
    """Public shareable result for share pages."""
    evaluation_type: str
    result: dict
    share_id: str
    share_count: int
    character_name: Optional[str] = None
    character_id: Optional[str] = None
    series_id: Optional[str] = None


# ============================================================================
# Game Endpoints
# ============================================================================

@router.post("/{game_slug}/start", response_model=GameStartResponse)
async def start_game(
    game_slug: str,
    data: GameStartRequest,
    user_id: Optional[UUID] = Depends(get_optional_user_id),
    db=Depends(get_db),
):
    """Start a new game session.

    Creates an anonymous session if not authenticated.
    Games work without login to maximize top-of-funnel engagement.
    """
    # For anonymous users, create a temporary user ID
    # (In production, would use session tokens)
    effective_user_id = user_id
    if not effective_user_id:
        # TODO: Implement anonymous session handling
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required (anonymous games coming soon)"
        )

    service = GamesService(db)

    try:
        result = await service.start_game(
            user_id=effective_user_id,
            game_slug=game_slug,
            character_choice=data.character_choice,
        )

        return GameStartResponse(
            session_id=str(result.session_id),
            character_id=str(result.character_id),
            character_name=result.character_name,
            character_avatar_url=result.character_avatar_url,
            opening_line=result.opening_line,
            turn_budget=result.turn_budget,
            situation=result.situation,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/{game_slug}/{session_id}/message", response_model=GameMessageResponse)
async def send_game_message(
    game_slug: str,
    session_id: UUID,
    data: GameMessageRequest,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Send a message in a game session.

    Returns the character response and game state.
    When is_complete=True, use GET /games/{game_slug}/{session_id}/result to get evaluation.
    """
    service = GamesService(db)

    try:
        result = await service.send_message(
            user_id=user_id,
            session_id=session_id,
            content=data.content,
        )

        return GameMessageResponse(
            message_content=result.message_content,
            turn_count=result.turn_count,
            turns_remaining=result.turns_remaining,
            is_complete=result.is_complete,
            mood=result.structured_response.get("mood") if result.structured_response else None,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/{game_slug}/{session_id}/message/stream")
async def send_game_message_stream(
    game_slug: str,
    session_id: UUID,
    data: GameMessageRequest,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Send a message and stream the response.

    Returns SSE stream with chunks, then final game state.
    Event types:
    - chunk: Character response text chunk
    - message_complete: Full response with game state (turn_count, turns_remaining)
    - episode_complete: Game finished with evaluation
    - done: Stream complete
    """
    service = GamesService(db)

    async def generate():
        try:
            async for chunk in service.send_message_stream(
                user_id=user_id,
                session_id=session_id,
                content=data.content,
            ):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
        except ValueError as e:
            error_data = json.dumps({"type": "error", "message": str(e)})
            yield f"data: {error_data}\n\n"
        except Exception as e:
            import logging
            logging.error(f"Game stream error: {e}")
            error_data = json.dumps({"type": "error", "message": "An error occurred"})
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{game_slug}/{session_id}/result", response_model=GameResultResponse)
async def get_game_result(
    game_slug: str,
    session_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Get the evaluation result for a completed game.

    Returns the archetype result and share URL.
    """
    service = GamesService(db)

    result = await service.get_result(
        session_id=session_id,
        user_id=user_id,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result not found or game not complete"
        )

    return GameResultResponse(
        evaluation_type=result["evaluation"]["evaluation_type"],
        result=result["evaluation"]["result"],
        share_id=result["evaluation"]["share_id"],
        share_url=result["share_url"],
        character_id=result["character_id"],
        character_name=result["character_name"],
        series_id=result["series_id"],
    )


# ============================================================================
# Share Endpoints (Public)
# ============================================================================

@router.get("/r/{share_id}", response_model=ShareableResultResponse)
async def get_shared_result(
    share_id: str,
    db=Depends(get_db),
):
    """Get a shared game result.

    Public endpoint - no authentication required.
    This is for the share page (ep-0.com/r/{share_id}).
    """
    director = DirectorService(db)

    result = await director.get_evaluation_by_share_id(share_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result not found"
        )

    return ShareableResultResponse(
        evaluation_type=result["evaluation_type"],
        result=result["result"],
        share_id=result["share_id"],
        share_count=result["share_count"],
        character_name=result.get("character_name"),
        character_id=result.get("character_id"),
        series_id=result.get("series_id"),
    )


@router.post("/r/{share_id}/view")
async def record_share_view(
    share_id: str,
    db=Depends(get_db),
):
    """Record a view of a shared result.

    Public endpoint - used for analytics.
    Called when someone views a share page.
    """
    director = DirectorService(db)
    await director.increment_share_count(share_id)
    return {"success": True}
