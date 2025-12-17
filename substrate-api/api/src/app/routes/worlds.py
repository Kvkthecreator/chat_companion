"""World routes for browsing and filtering worlds."""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.deps import get_db
from app.models.world import World, WorldSummary

router = APIRouter(prefix="/worlds", tags=["Worlds"])


@router.get("", response_model=List[World])
async def list_worlds(
    status_filter: Optional[str] = Query(None, alias="status"),
    transparency: Optional[str] = Query(None),
    db=Depends(get_db),
):
    """
    List all worlds.

    Worlds are top-level containers in the content hierarchy.
    World → Series → Episode → Character
    """
    query = "SELECT * FROM worlds WHERE 1=1"
    params = {}

    # Filter by active status
    if status_filter == "active":
        query += " AND is_active = TRUE"
    elif status_filter == "inactive":
        query += " AND is_active = FALSE"
    else:
        # Default to active only
        query += " AND is_active = TRUE"

    # Optional transparency filter (from metadata)
    if transparency:
        query += " AND metadata->>'transparency' = :transparency"
        params["transparency"] = transparency

    query += " ORDER BY name ASC"

    rows = await db.fetch_all(query, params)
    return [World(**dict(row)) for row in rows]


@router.get("/{world_id}", response_model=World)
async def get_world(
    world_id: UUID,
    db=Depends(get_db),
):
    """Get a single world by ID."""
    query = "SELECT * FROM worlds WHERE id = :world_id"
    row = await db.fetch_one(query, {"world_id": str(world_id)})

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="World not found",
        )

    return World(**dict(row))


@router.get("/slug/{slug}", response_model=World)
async def get_world_by_slug(
    slug: str,
    db=Depends(get_db),
):
    """Get a world by its slug."""
    query = "SELECT * FROM worlds WHERE slug = :slug AND is_active = TRUE"
    row = await db.fetch_one(query, {"slug": slug})

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="World not found",
        )

    return World(**dict(row))
