"""API route for listing available task types."""

from fastapi import APIRouter


# Phase 1 stub: no task types registered
def get_all_task_types() -> list[dict]:
    return []


router = APIRouter(prefix="/task-types", tags=["task-types"])


@router.get("/", response_model=list[dict])
async def list_all():
    """Return all registered TaskTypes. Phase 1 returns an empty list."""
    return get_all_task_types()
