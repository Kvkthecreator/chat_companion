"""Placeholder /agent-run route for Phase 1."""

from fastapi import APIRouter

router = APIRouter(tags=["agents"])


@router.post("/agent-run")
async def agent_run():
    """Stub endpoint kept for compatibility."""
    return {"status": "ok"}
