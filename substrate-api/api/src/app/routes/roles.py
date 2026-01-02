"""Roles API routes.

Roles are the bridge between episodes and characters (ADR-004).

KEY PRINCIPLE: Any character can play any role. No compatibility gating.

A Role defines:
- The scene motivation (objective/obstacle/tactic) for the part
- A name and description for the UI
- Reusable across episodes

Reference: docs/decisions/ADR-004-user-character-role-abstraction.md
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from app.deps import get_db
from app.services.storage import StorageService


router = APIRouter(prefix="/roles", tags=["Roles"])


# =============================================================================
# Response Models
# =============================================================================

class RoleResponse(BaseModel):
    """Role with full details."""
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    scene_objective: Optional[str] = None
    scene_obstacle: Optional[str] = None
    scene_tactic: Optional[str] = None


class CompatibleCharacter(BaseModel):
    """A character that can play a role.

    Note: ALL characters can play ALL roles. No compatibility gating.
    """
    id: str
    name: str
    slug: str
    archetype: str
    avatar_url: Optional[str] = None
    is_user_created: bool
    is_canonical: bool  # True for platform characters


class CharacterSelectionContext(BaseModel):
    """Context for character selection before starting an episode.

    Per ADR-004, ALL user characters are returned. Any character can play any role.
    """
    series_id: str
    series_title: str
    role: RoleResponse
    canonical_character: Optional[CompatibleCharacter] = None
    user_characters: List[CompatibleCharacter] = Field(default_factory=list)
    can_use_canonical: bool = True


# =============================================================================
# API Endpoints
# =============================================================================

@router.get("", response_model=List[RoleResponse])
async def list_roles(
    limit: int = Query(50, ge=1, le=100),
    db=Depends(get_db),
):
    """List all roles."""
    query = """
        SELECT id, name, slug, description,
               scene_objective, scene_obstacle, scene_tactic
        FROM roles
        ORDER BY name
        LIMIT :limit
    """
    rows = await db.fetch_all(query, {"limit": limit})

    return [
        RoleResponse(
            id=str(row["id"]),
            name=row["name"],
            slug=row["slug"],
            description=row["description"],
            scene_objective=row["scene_objective"],
            scene_obstacle=row["scene_obstacle"],
            scene_tactic=row["scene_tactic"],
        )
        for row in rows
    ]


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: UUID,
    db=Depends(get_db),
):
    """Get a specific role by ID."""
    query = """
        SELECT id, name, slug, description,
               scene_objective, scene_obstacle, scene_tactic
        FROM roles
        WHERE id = :id
    """
    row = await db.fetch_one(query, {"id": str(role_id)})

    if not row:
        raise HTTPException(status_code=404, detail="Role not found")

    return RoleResponse(
        id=str(row["id"]),
        name=row["name"],
        slug=row["slug"],
        description=row["description"],
        scene_objective=row["scene_objective"],
        scene_obstacle=row["scene_obstacle"],
        scene_tactic=row["scene_tactic"],
    )


# =============================================================================
# Series-Scoped Character Selection
# =============================================================================

@router.get("/series/{series_id}/character-selection", response_model=CharacterSelectionContext)
async def get_character_selection_for_series(
    series_id: UUID,
    request: Request,
    db=Depends(get_db),
):
    """Get character selection context for starting a series.

    ADR-004: Any character can play any role. Returns ALL user characters.

    Returns:
    - The series info
    - The role (scene motivation)
    - The canonical (default) character
    - ALL of the user's characters (no filtering)
    """
    user_id = getattr(request.state, "user_id", None)

    # Get series with its default role
    series_query = """
        SELECT s.id, s.title, s.slug, s.default_role_id,
               r.id as role_id, r.name as role_name, r.slug as role_slug,
               r.description as role_description,
               r.scene_objective, r.scene_obstacle, r.scene_tactic
        FROM series s
        LEFT JOIN roles r ON r.id = s.default_role_id
        WHERE s.id = :series_id
    """
    series_row = await db.fetch_one(series_query, {"series_id": str(series_id)})

    if not series_row:
        raise HTTPException(status_code=404, detail="Series not found")

    if not series_row["role_id"]:
        raise HTTPException(
            status_code=400,
            detail="Series does not have a role defined. Cannot select character."
        )

    # Get canonical character for this series (with avatar kit for permanent URL)
    canonical_query = """
        SELECT DISTINCT c.id, c.name, c.slug, c.archetype, c.avatar_url,
               aa.storage_path as anchor_path
        FROM characters c
        JOIN episode_templates et ON et.character_id = c.id
        LEFT JOIN avatar_kits ak ON ak.id = c.active_avatar_kit_id
        LEFT JOIN avatar_assets aa ON aa.id = ak.primary_anchor_id AND aa.is_active = TRUE
        WHERE et.series_id = :series_id
        AND c.is_user_created = FALSE
        AND c.status = 'active'
        LIMIT 1
    """
    canonical_row = await db.fetch_one(canonical_query, {"series_id": str(series_id)})

    storage = StorageService.get_instance()
    canonical_character = None

    if canonical_row:
        avatar_url = canonical_row["avatar_url"]
        anchor_path = canonical_row["anchor_path"]

        # Use permanent public URL from anchor_path if available
        if anchor_path:
            avatar_url = storage.get_public_url("avatars", anchor_path)
        elif avatar_url and not avatar_url.startswith("http"):
            # Fallback: use public URL for relative paths
            avatar_url = storage.get_public_url("avatars", avatar_url)

        canonical_character = CompatibleCharacter(
            id=str(canonical_row["id"]),
            name=canonical_row["name"],
            slug=canonical_row["slug"],
            archetype=canonical_row["archetype"] or "",
            avatar_url=avatar_url,
            is_user_created=False,
            is_canonical=True,
        )

    # Get ALL user's characters (no filtering - any character can play any role)
    user_characters = []
    if user_id:
        user_chars_query = """
            SELECT c.id, c.name, c.slug, c.archetype, c.avatar_url,
                   aa.storage_path as anchor_path
            FROM characters c
            LEFT JOIN avatar_kits ak ON ak.id = c.active_avatar_kit_id
            LEFT JOIN avatar_assets aa ON aa.id = ak.primary_anchor_id AND aa.is_active = TRUE
            WHERE c.created_by = :user_id
            AND c.is_user_created = TRUE
            AND c.status = 'active'
            ORDER BY c.created_at DESC
        """
        user_char_rows = await db.fetch_all(user_chars_query, {"user_id": user_id})

        for row in user_char_rows:
            avatar_url = row["avatar_url"]
            anchor_path = row["anchor_path"]

            # For user-uploaded avatars (public URLs), keep the direct URL
            # For kit-based avatars, use permanent public URL from anchor_path
            is_uploaded_avatar = avatar_url and "user-uploads/" in avatar_url
            if anchor_path and not is_uploaded_avatar:
                avatar_url = storage.get_public_url("avatars", anchor_path)
            elif avatar_url and not avatar_url.startswith("http"):
                avatar_url = storage.get_public_url("avatars", avatar_url)

            user_characters.append(CompatibleCharacter(
                id=str(row["id"]),
                name=row["name"],
                slug=row["slug"],
                archetype=row["archetype"] or "",
                avatar_url=avatar_url,
                is_user_created=True,
                is_canonical=False,
            ))

    role = RoleResponse(
        id=str(series_row["role_id"]),
        name=series_row["role_name"],
        slug=series_row["role_slug"],
        description=series_row["role_description"],
        scene_objective=series_row["scene_objective"],
        scene_obstacle=series_row["scene_obstacle"],
        scene_tactic=series_row["scene_tactic"],
    )

    return CharacterSelectionContext(
        series_id=str(series_row["id"]),
        series_title=series_row["title"],
        role=role,
        canonical_character=canonical_character,
        user_characters=user_characters,
        can_use_canonical=True,
    )
