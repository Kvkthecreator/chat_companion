"""Role model - bridge between episode and character.

ADR-004: Role as Episode-Character Bridge

A Role represents the archetype slot in an episode that a character fills.
It defines:
- The archetype required (e.g., "warm café worker", "mysterious stranger")
- The compatibility constraints a character must satisfy
- The scene motivation (objective/obstacle/tactic) - the "director's notes"

Any compatible character (canonical or user-created) can fill a role.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator
import json


class Role(BaseModel):
    """Role entity - archetype slot that characters can fill.

    Scene motivation fields (objective/obstacle/tactic) are the "director's notes"
    that the character internalizes during "rehearsal" (context building).
    Per ADR-002 Theatrical Model, these guide behavior without per-turn generation.
    """

    id: UUID
    name: str  # "The Barista", "The Stranger"
    slug: str
    description: Optional[str] = None  # For content authoring UI

    # Compatibility constraints
    archetype: str  # Required archetype (warm_supportive, mysterious_reserved, etc.)
    compatible_archetypes: List[str] = Field(default_factory=list)  # Additional compatible
    required_traits: Dict[str, Any] = Field(default_factory=dict)  # Minimum personality requirements

    # Scene motivation (moved from episode_template per ADR-002)
    scene_objective: Optional[str] = None  # What character wants from user
    scene_obstacle: Optional[str] = None   # What's stopping them
    scene_tactic: Optional[str] = None     # How they're playing it

    created_at: datetime
    updated_at: datetime

    @field_validator("compatible_archetypes", mode="before")
    @classmethod
    def ensure_list(cls, v: Any) -> List[str]:
        """Handle list fields as JSON string or array from DB."""
        if v is None:
            return []
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, TypeError):
                return [v] if v else []
        return []

    @field_validator("required_traits", mode="before")
    @classmethod
    def ensure_dict(cls, v: Any) -> Dict[str, Any]:
        """Handle dict fields as JSON string from DB."""
        if v is None:
            return {}
        if isinstance(v, dict):
            return v
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, dict):
                    return parsed
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}


class RoleCreate(BaseModel):
    """Input model for creating a role."""

    name: str
    slug: str
    description: Optional[str] = None
    archetype: str
    compatible_archetypes: List[str] = Field(default_factory=list)
    required_traits: Dict[str, Any] = Field(default_factory=dict)
    scene_objective: Optional[str] = None
    scene_obstacle: Optional[str] = None
    scene_tactic: Optional[str] = None


class RoleUpdate(BaseModel):
    """Input model for updating a role."""

    name: Optional[str] = None
    description: Optional[str] = None
    archetype: Optional[str] = None
    compatible_archetypes: Optional[List[str]] = None
    required_traits: Optional[Dict[str, Any]] = None
    scene_objective: Optional[str] = None
    scene_obstacle: Optional[str] = None
    scene_tactic: Optional[str] = None


def can_character_play_role(
    character_archetype: str,
    role_archetype: str,
    role_compatible_archetypes: List[str],
) -> bool:
    """Check if a character's archetype is compatible with a role.

    Args:
        character_archetype: The character's archetype (e.g., "warm_supportive")
        role_archetype: The role's primary archetype
        role_compatible_archetypes: Additional compatible archetypes for the role

    Returns:
        True if the character can play this role
    """
    # Primary archetype match
    if character_archetype == role_archetype:
        return True

    # Check compatible archetypes list
    if role_compatible_archetypes and character_archetype in role_compatible_archetypes:
        return True

    return False


# Archetype compatibility matrix
# Defines which archetypes can substitute for each other
ARCHETYPE_COMPATIBILITY = {
    "warm_supportive": ["playful_teasing"],
    "playful_teasing": ["warm_supportive"],
    "mysterious_reserved": ["intense_passionate"],
    "intense_passionate": ["mysterious_reserved", "confident_assertive"],
    "confident_assertive": ["intense_passionate"],
}


def get_compatible_archetypes(archetype: str) -> List[str]:
    """Get archetypes that can substitute for a given archetype.

    Args:
        archetype: The primary archetype

    Returns:
        List of compatible archetypes (including the primary)
    """
    compatible = [archetype]  # Always include self
    if archetype in ARCHETYPE_COMPATIBILITY:
        compatible.extend(ARCHETYPE_COMPATIBILITY[archetype])
    return compatible
