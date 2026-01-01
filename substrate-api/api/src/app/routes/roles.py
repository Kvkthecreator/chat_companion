"""Roles API routes.

Roles are the bridge between episodes and characters (ADR-004).
A Role defines the archetype slot an episode requires, which can be filled by
any compatible character (canonical or user-created).

Reference: docs/decisions/ADR-004-user-character-role-abstraction.md
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from app.deps import get_db
from app.models.role import Role, can_character_play_role, get_compatible_archetypes
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
    archetype: str
    compatible_archetypes: List[str] = Field(default_factory=list)
    scene_objective: Optional[str] = None
    scene_obstacle: Optional[str] = None
    scene_tactic: Optional[str] = None


class CompatibleCharacter(BaseModel):
    """A character that can fill a role."""
    id: str
    name: str
    slug: str
    archetype: str
    mapped_archetype: Optional[str] = None
    avatar_url: Optional[str] = None
    is_user_created: bool
    is_canonical: bool  # True for platform characters


class RoleWithCharactersResponse(RoleResponse):
    """Role with list of compatible characters."""
    canonical_character: Optional[CompatibleCharacter] = None  # The "default" character
    compatible_characters: List[CompatibleCharacter] = Field(default_factory=list)


class CharacterSelectionContext(BaseModel):
    """Context for character selection before starting an episode."""
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
    archetype: Optional[str] = Query(None, description="Filter by primary archetype"),
    limit: int = Query(50, ge=1, le=100),
    db=Depends(get_db),
):
    """List all roles with optional archetype filter."""
    query = """
        SELECT id, name, slug, description, archetype, compatible_archetypes,
               scene_objective, scene_obstacle, scene_tactic
        FROM roles
        WHERE 1=1
    """
    params = {"limit": limit}

    if archetype:
        query += " AND (archetype = :archetype OR :archetype = ANY(compatible_archetypes))"
        params["archetype"] = archetype

    query += " ORDER BY name LIMIT :limit"

    rows = await db.fetch_all(query, params)

    return [
        RoleResponse(
            id=str(row["id"]),
            name=row["name"],
            slug=row["slug"],
            description=row["description"],
            archetype=row["archetype"],
            compatible_archetypes=row["compatible_archetypes"] or [],
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
        SELECT id, name, slug, description, archetype, compatible_archetypes,
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
        archetype=row["archetype"],
        compatible_archetypes=row["compatible_archetypes"] or [],
        scene_objective=row["scene_objective"],
        scene_obstacle=row["scene_obstacle"],
        scene_tactic=row["scene_tactic"],
    )


@router.get("/{role_id}/compatible-characters", response_model=RoleWithCharactersResponse)
async def get_role_with_compatible_characters(
    role_id: UUID,
    request: Request,
    db=Depends(get_db),
):
    """Get a role with all characters that can fill it.

    Returns:
    - The role details
    - The canonical character (if one exists for this role's series)
    - All user-created characters that are archetype-compatible
    """
    user_id = getattr(request.state, "user_id", None)

    # Get role
    role_query = """
        SELECT id, name, slug, description, archetype, compatible_archetypes,
               scene_objective, scene_obstacle, scene_tactic
        FROM roles
        WHERE id = :id
    """
    role_row = await db.fetch_one(role_query, {"id": str(role_id)})

    if not role_row:
        raise HTTPException(status_code=404, detail="Role not found")

    role_archetype = role_row["archetype"]
    role_compatible = role_row["compatible_archetypes"] or []

    # Build list of all compatible archetypes
    all_compatible = [role_archetype] + list(role_compatible)

    # Get canonical character for this role's series
    # Find the series that uses this role, then get its canonical character
    canonical_query = """
        SELECT DISTINCT c.id, c.name, c.slug, c.archetype, c.mapped_archetype, c.avatar_url
        FROM characters c
        JOIN episode_templates et ON et.character_id = c.id
        WHERE et.role_id = :role_id
        AND c.is_user_created = FALSE
        AND c.status = 'active'
        LIMIT 1
    """
    canonical_row = await db.fetch_one(canonical_query, {"role_id": str(role_id)})

    canonical_character = None
    storage = StorageService.get_instance()

    if canonical_row:
        avatar_url = canonical_row["avatar_url"]
        if avatar_url and not avatar_url.startswith("http"):
            avatar_url = await storage.create_signed_url("avatars", avatar_url, expires_in=3600)

        canonical_character = CompatibleCharacter(
            id=str(canonical_row["id"]),
            name=canonical_row["name"],
            slug=canonical_row["slug"],
            archetype=canonical_row["archetype"] or "",
            mapped_archetype=canonical_row["mapped_archetype"],
            avatar_url=avatar_url,
            is_user_created=False,
            is_canonical=True,
        )

    # Get user's compatible characters
    compatible_characters = []
    if user_id:
        user_chars_query = """
            SELECT id, name, slug, archetype, mapped_archetype, avatar_url
            FROM characters
            WHERE created_by = :user_id
            AND is_user_created = TRUE
            AND status = 'active'
            AND (
                mapped_archetype = ANY(:archetypes)
                OR archetype = ANY(:archetypes)
            )
        """
        user_char_rows = await db.fetch_all(user_chars_query, {
            "user_id": user_id,
            "archetypes": all_compatible,
        })

        for row in user_char_rows:
            avatar_url = row["avatar_url"]
            if avatar_url and not avatar_url.startswith("http"):
                avatar_url = await storage.create_signed_url("avatars", avatar_url, expires_in=3600)

            compatible_characters.append(CompatibleCharacter(
                id=str(row["id"]),
                name=row["name"],
                slug=row["slug"],
                archetype=row["archetype"] or "",
                mapped_archetype=row["mapped_archetype"],
                avatar_url=avatar_url,
                is_user_created=True,
                is_canonical=False,
            ))

    return RoleWithCharactersResponse(
        id=str(role_row["id"]),
        name=role_row["name"],
        slug=role_row["slug"],
        description=role_row["description"],
        archetype=role_archetype,
        compatible_archetypes=role_compatible,
        scene_objective=role_row["scene_objective"],
        scene_obstacle=role_row["scene_obstacle"],
        scene_tactic=role_row["scene_tactic"],
        canonical_character=canonical_character,
        compatible_characters=compatible_characters,
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

    This is the primary endpoint for the pre-episode character selection UI.
    Returns:
    - The series info
    - The role required for this series
    - The canonical (default) character
    - User's characters that can fill the role
    """
    user_id = getattr(request.state, "user_id", None)

    # Get series with its default role
    series_query = """
        SELECT s.id, s.title, s.slug, s.default_role_id,
               r.id as role_id, r.name as role_name, r.slug as role_slug,
               r.description as role_description, r.archetype, r.compatible_archetypes,
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

    role_archetype = series_row["archetype"]
    role_compatible = series_row["compatible_archetypes"] or []
    all_compatible = [role_archetype] + list(role_compatible)

    # Get canonical character for this series
    canonical_query = """
        SELECT DISTINCT c.id, c.name, c.slug, c.archetype, c.mapped_archetype, c.avatar_url
        FROM characters c
        JOIN episode_templates et ON et.character_id = c.id
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
        if avatar_url and not avatar_url.startswith("http"):
            avatar_url = await storage.create_signed_url("avatars", avatar_url, expires_in=3600)

        canonical_character = CompatibleCharacter(
            id=str(canonical_row["id"]),
            name=canonical_row["name"],
            slug=canonical_row["slug"],
            archetype=canonical_row["archetype"] or "",
            mapped_archetype=canonical_row["mapped_archetype"],
            avatar_url=avatar_url,
            is_user_created=False,
            is_canonical=True,
        )

    # Get user's compatible characters
    user_characters = []
    if user_id:
        user_chars_query = """
            SELECT id, name, slug, archetype, mapped_archetype, avatar_url
            FROM characters
            WHERE created_by = :user_id
            AND is_user_created = TRUE
            AND status = 'active'
            AND (
                mapped_archetype = ANY(:archetypes)
                OR archetype = ANY(:archetypes)
            )
        """
        user_char_rows = await db.fetch_all(user_chars_query, {
            "user_id": user_id,
            "archetypes": all_compatible,
        })

        for row in user_char_rows:
            avatar_url = row["avatar_url"]
            if avatar_url and not avatar_url.startswith("http"):
                avatar_url = await storage.create_signed_url("avatars", avatar_url, expires_in=3600)

            user_characters.append(CompatibleCharacter(
                id=str(row["id"]),
                name=row["name"],
                slug=row["slug"],
                archetype=row["archetype"] or "",
                mapped_archetype=row["mapped_archetype"],
                avatar_url=avatar_url,
                is_user_created=True,
                is_canonical=False,
            ))

    role = RoleResponse(
        id=str(series_row["role_id"]),
        name=series_row["role_name"],
        slug=series_row["role_slug"],
        description=series_row["role_description"],
        archetype=role_archetype,
        compatible_archetypes=role_compatible,
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


# =============================================================================
# Character Compatibility Check
# =============================================================================

class CompatibilityCheckRequest(BaseModel):
    """Request to check if a character can play a role."""
    character_id: str
    role_id: str


class CompatibilityCheckResponse(BaseModel):
    """Result of compatibility check."""
    compatible: bool
    character_archetype: str
    role_archetype: str
    role_compatible_archetypes: List[str]
    reason: Optional[str] = None


@router.post("/check-compatibility", response_model=CompatibilityCheckResponse)
async def check_character_role_compatibility(
    data: CompatibilityCheckRequest,
    db=Depends(get_db),
):
    """Check if a character can play a specific role.

    Used before session creation to validate character selection.
    """
    # Get character
    char_query = """
        SELECT archetype, mapped_archetype
        FROM characters
        WHERE id = :id AND status = 'active'
    """
    char_row = await db.fetch_one(char_query, {"id": data.character_id})

    if not char_row:
        raise HTTPException(status_code=404, detail="Character not found")

    # Get role
    role_query = """
        SELECT archetype, compatible_archetypes
        FROM roles
        WHERE id = :id
    """
    role_row = await db.fetch_one(role_query, {"id": data.role_id})

    if not role_row:
        raise HTTPException(status_code=404, detail="Role not found")

    # Use mapped_archetype if available, otherwise use archetype
    char_archetype = char_row["mapped_archetype"] or char_row["archetype"] or ""
    role_archetype = role_row["archetype"]
    role_compatible = role_row["compatible_archetypes"] or []

    # Check compatibility
    is_compatible = can_character_play_role(
        char_archetype,
        role_archetype,
        role_compatible,
    )

    reason = None
    if not is_compatible:
        reason = f"Character archetype '{char_archetype}' is not compatible with role requiring '{role_archetype}'"

    return CompatibilityCheckResponse(
        compatible=is_compatible,
        character_archetype=char_archetype,
        role_archetype=role_archetype,
        role_compatible_archetypes=role_compatible,
        reason=reason,
    )
