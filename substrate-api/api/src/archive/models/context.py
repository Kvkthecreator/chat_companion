from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
import uuid
import datetime


class ContextItemType(str, Enum):
    guideline = "guideline"
    theme = "theme"
    category = "category"
    relationship = "relationship"
    audience = "audience"
    goal = "goal"
    topic = "topic"
    insight = "insight"
    reference = "reference"
    constraint = "constraint"


class ContextItemStatus(str, Enum):
    active = "active"
    archived = "archived"


class ContextItem(BaseModel):
    id: uuid.UUID
    basket_id: uuid.UUID
    document_id: Optional[uuid.UUID] = None
    block_id: Optional[uuid.UUID] = None
    type: ContextItemType
    content: str
    status: ContextItemStatus
    confidence: Optional[float] = None  # Agent confidence score
    created_by: Optional[str] = None    # User ID or agent ID
    created_by_type: Optional[str] = None  # 'user' or 'agent'
    meta_notes: Optional[str] = None    # Agent reasoning/notes
    created_at: datetime.datetime
    
    # Composition intelligence fields (without schema changes)
    composition_weight: float = Field(default=1.0, ge=0.0, le=10.0)
    hierarchy_level: str = Field(default="secondary", pattern="^(primary|secondary|supporting)$")
    intent_category: Optional[str] = None  # "strategic", "technical", "creative", etc.
    composition_metadata: dict = Field(default_factory=dict)  # Intelligence data


class ContextItemCreate(BaseModel):
    document_id: Optional[uuid.UUID] = None
    block_id: Optional[uuid.UUID] = None
    type: ContextItemType = Field(example="guideline")
    content: str = Field(..., min_length=3)
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    meta_notes: Optional[str] = None
    composition_weight: float = Field(default=1.0, ge=0.0, le=10.0)
    hierarchy_level: str = Field(default="secondary", pattern="^(primary|secondary|supporting)$")
    intent_category: Optional[str] = None
    composition_metadata: dict = Field(default_factory=dict)


class ContextItemUpdate(BaseModel):
    content: Optional[str]
    status: Optional[ContextItemStatus]
    composition_weight: Optional[float] = Field(None, ge=0.0, le=10.0)
    hierarchy_level: Optional[str] = Field(None, pattern="^(primary|secondary|supporting)$")
    intent_category: Optional[str] = None
    composition_metadata: Optional[dict] = None


class CompositionIntent(BaseModel):
    """Composition intelligence profile for memory expression."""
    primary_intent: str  # "strategic_analysis", "technical_guide", "creative_brief"
    audience: Optional[str] = None  # "executives", "engineers", "general"
    style: Optional[str] = None     # "formal", "conversational", "detailed"
    scope: Optional[str] = None     # "overview", "deep_dive", "action_items"
    complexity_level: str = Field(default="medium", pattern="^(simple|medium|complex)$")
    composition_metadata: dict = Field(default_factory=dict)


class ContextHierarchy(BaseModel):
    """Hierarchical organization of contexts for composition intelligence."""
    basket_id: uuid.UUID
    primary_contexts: List[ContextItem]    # Main compositional drivers
    secondary_contexts: List[ContextItem]  # Supporting aspects
    supporting_contexts: List[ContextItem] # Background elements
    intent_profile: CompositionIntent      # Overall composition direction
    composition_score: float = Field(ge=0.0, le=1.0)  # Overall composition readiness
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)


class CompositionProfile(BaseModel):
    """Complete composition intelligence profile for a basket."""
    basket_id: uuid.UUID
    context_hierarchy: ContextHierarchy
    composition_opportunities: List[str]   # Identified composition possibilities
    missing_contexts: List[str]            # Gaps in composition intelligence
    recommended_actions: List[str]         # Actions to improve composition readiness
    confidence_score: float = Field(ge=0.0, le=1.0)
    analysis_timestamp: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
