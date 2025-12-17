"""World models."""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class VisualStyle(BaseModel):
    """Visual identity for image generation.

    Used at World and Series level with cascade inheritance:
    World visual_style → Series visual_style → Episode generation
    """
    base_style: Optional[str] = None  # Core art direction
    color_palette: Optional[str] = None  # Color themes
    rendering: Optional[str] = None  # Technical rendering notes
    character_framing: Optional[str] = None  # How characters are presented
    negative_prompt: Optional[str] = None  # What to avoid

    # Series-level additions (not typically used at World level)
    mood: Optional[str] = None  # Emotional atmosphere
    recurring_motifs: Optional[List[str]] = None  # Visual themes
    genre_markers: Optional[str] = None  # Genre-specific visual cues
    atmosphere: Optional[str] = None  # Environmental feel


class WorldSummary(BaseModel):
    """Minimal world info for lists."""

    id: UUID
    name: str
    slug: str
    tone: Optional[str] = None


class World(BaseModel):
    """Full world model."""

    id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    default_scenes: List[str] = Field(default_factory=list)
    tone: Optional[str] = None
    ambient_details: Dict[str, Any] = Field(default_factory=dict)
    visual_style: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True
