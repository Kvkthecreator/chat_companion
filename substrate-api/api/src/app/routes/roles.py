"""Roles API routes.

Roles are the bridge between episodes and characters (ADR-004 v2 - Cinematic Casting).

KEY PRINCIPLE: Any character can play any role. The system adapts prompts to bridge
archetype differences rather than gating by compatibility.

A Role defines:
- The scene motivation (objective/obstacle/tactic) for the part
- The canonical archetype (what the role was written for - informational only)
- Does NOT enforce archetype compatibility

Reference: docs/decisions/ADR-004-user-character-role-abstraction.md
Reference: docs/implementation/CINEMATIC_CASTING.md
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
    canonical_archetype: str  # What the role was written for (informational only)
    scene_objective: Optional[str] = None
    scene_obstacle: Optional[str] = None
    scene_tactic: Optional[str] = None


class CompatibleCharacter(BaseModel):
    """A character that can be cast in a role.

    Note: ALL characters can play ALL roles per Cinematic Casting model.
    This model is named 'Compatible' for backwards compatibility but no
    filtering is applied.
    """
    id: str
    name: str
    slug: str
    archetype: str
    mapped_archetype: Optional[str] = None
    avatar_url: Optional[str] = None
    is_user_created: bool
    is_canonical: bool  # True for platform characters


class CharacterSelectionContext(BaseModel):
    """Context for character selection before starting an episode.

    Per Cinematic Casting (ADR-004 v2), ALL user characters are returned
    regardless of archetype. The system adapts prompts when archetypes differ.
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
        SELECT id, name, slug, description, archetype as canonical_archetype,
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
            canonical_archetype=row["canonical_archetype"],
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
        SELECT id, name, slug, description, archetype as canonical_archetype,
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
        canonical_archetype=row["canonical_archetype"],
        scene_objective=row["scene_objective"],
        scene_obstacle=row["scene_obstacle"],
        scene_tactic=row["scene_tactic"],
    )


# =============================================================================
# Series-Scoped Character Selection (Cinematic Casting)
# =============================================================================

@router.get("/series/{series_id}/character-selection", response_model=CharacterSelectionContext)
async def get_character_selection_for_series(
    series_id: UUID,
    request: Request,
    db=Depends(get_db),
):
    """Get character selection context for starting a series.

    CINEMATIC CASTING MODEL (ADR-004 v2):
    Returns ALL user characters regardless of archetype. Any character can play
    any role - the system adapts prompts via the Casting Adaptation Layer when
    the character's archetype differs from the role's canonical archetype.

    Returns:
    - The series info
    - The role (with canonical_archetype for reference)
    - The canonical (default) character
    - ALL of the user's characters (no filtering)
    """
    user_id = getattr(request.state, "user_id", None)

    # Get series with its default role
    series_query = """
        SELECT s.id, s.title, s.slug, s.default_role_id,
               r.id as role_id, r.name as role_name, r.slug as role_slug,
               r.description as role_description, r.archetype as canonical_archetype,
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

    # Get ALL user's characters (Cinematic Casting - no archetype filtering)
    user_characters = []
    if user_id:
        user_chars_query = """
            SELECT id, name, slug, archetype, mapped_archetype, avatar_url
            FROM characters
            WHERE created_by = :user_id
            AND is_user_created = TRUE
            AND status = 'active'
            ORDER BY created_at DESC
        """
        user_char_rows = await db.fetch_all(user_chars_query, {"user_id": user_id})

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
        canonical_archetype=series_row["canonical_archetype"],
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
# Casting Adaptation Check (Informational Only)
# =============================================================================

class CastingAdaptationResponse(BaseModel):
    """Information about casting adaptation for a character-role pairing.

    This is informational only - all characters can play all roles.
    The response indicates whether the Casting Adaptation Layer will be
    active for this pairing.
    """
    needs_adaptation: bool
    character_archetype: str
    role_canonical_archetype: str
    adaptation_note: Optional[str] = None


@router.get("/casting-info/{role_id}/{character_id}", response_model=CastingAdaptationResponse)
async def get_casting_adaptation_info(
    role_id: UUID,
    character_id: UUID,
    db=Depends(get_db),
):
    """Get information about how a character will play a role.

    This is INFORMATIONAL ONLY - it does not gate the casting.
    Returns whether the Casting Adaptation Layer will be active and
    provides a preview of how the archetype mismatch will be bridged.
    """
    # Get character
    char_query = """
        SELECT archetype, mapped_archetype, name
        FROM characters
        WHERE id = :id AND status = 'active'
    """
    char_row = await db.fetch_one(char_query, {"id": str(character_id)})

    if not char_row:
        raise HTTPException(status_code=404, detail="Character not found")

    # Get role
    role_query = """
        SELECT archetype as canonical_archetype, name
        FROM roles
        WHERE id = :id
    """
    role_row = await db.fetch_one(role_query, {"id": str(role_id)})

    if not role_row:
        raise HTTPException(status_code=404, detail="Role not found")

    # Use mapped_archetype if available, otherwise use archetype
    char_archetype = char_row["mapped_archetype"] or char_row["archetype"] or ""
    role_archetype = role_row["canonical_archetype"]

    # Check if adaptation is needed
    needs_adaptation = char_archetype != role_archetype

    adaptation_note = None
    if needs_adaptation:
        adaptation_note = (
            f"Your character ({char_row['name']}) brings a {char_archetype.replace('_', ' ')} "
            f"interpretation to a role written for {role_archetype.replace('_', ' ')}. "
            f"The Casting Adaptation Layer will bridge this for a unique experience."
        )

    return CastingAdaptationResponse(
        needs_adaptation=needs_adaptation,
        character_archetype=char_archetype,
        role_canonical_archetype=role_archetype,
        adaptation_note=adaptation_note,
    )
