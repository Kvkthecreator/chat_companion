"""Series models.

A Series is a narrative container grouping episodes into a coherent experience.
Reference: docs/GLOSSARY.md, docs/CONTENT_ARCHITECTURE_CANON.md
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SeriesType:
    """Series type constants (per GLOSSARY.md)."""
    STANDALONE = "standalone"  # Self-contained, any episode can be entry
    SERIAL = "serial"          # Sequential narrative, Episode 0 recommended first
    ANTHOLOGY = "anthology"    # Themed collection, loosely connected
    CROSSOVER = "crossover"    # Multiple characters from different worlds


class SeriesSummary(BaseModel):
    """Minimal series info for lists and cards."""
    id: UUID
    title: str
    slug: str
    tagline: Optional[str] = None
    series_type: str = SeriesType.STANDALONE
    genre: Optional[str] = None
    total_episodes: int = 0
    cover_image_url: Optional[str] = None
    is_featured: bool = False


class Series(BaseModel):
    """Full series model."""
    id: UUID
    title: str
    slug: str
    description: Optional[str] = None
    tagline: Optional[str] = None
    genre: Optional[str] = None

    # Relationships
    world_id: Optional[UUID] = None

    # Series taxonomy
    series_type: str = SeriesType.STANDALONE

    # Content organization
    featured_characters: List[UUID] = Field(default_factory=list)
    episode_order: List[UUID] = Field(default_factory=list)
    total_episodes: int = 0

    # Visual assets
    cover_image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    visual_style: Dict[str, Any] = Field(default_factory=dict)

    # Publishing state
    status: str = "draft"
    is_featured: bool = False
    featured_at: Optional[datetime] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SeriesCreate(BaseModel):
    """Input for creating a new series."""
    title: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=2000)
    tagline: Optional[str] = Field(None, max_length=200)
    world_id: Optional[UUID] = None
    series_type: str = Field(default=SeriesType.STANDALONE)


class SeriesUpdate(BaseModel):
    """Input for updating a series."""
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=2000)
    tagline: Optional[str] = Field(None, max_length=200)
    world_id: Optional[UUID] = None
    series_type: Optional[str] = None
    featured_characters: Optional[List[UUID]] = None
    episode_order: Optional[List[UUID]] = None
    cover_image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    status: Optional[str] = None
    is_featured: Optional[bool] = None


class SeriesWithEpisodes(Series):
    """Series with embedded episode templates."""
    episodes: List[Any] = Field(default_factory=list)


class SeriesWithCharacters(Series):
    """Series with embedded character summaries."""
    characters: List[Any] = Field(default_factory=list)
