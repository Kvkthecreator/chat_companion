"""Document models with context-driven composition intelligence."""

from __future__ import annotations

from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class DocumentState(str, Enum):
    """Document lifecycle states."""
    DRAFT = "DRAFT"
    REVIEW = "REVIEW"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class CompositionMethod(str, Enum):
    """How the document was composed."""
    MANUAL = "manual"
    CONTEXT_DRIVEN = "context_driven"
    AGENT_COMPOSED = "agent_composed"
    TEMPLATE_BASED = "template_based"


class DocumentType(str, Enum):
    """Types of documents based on composition intent."""
    STRATEGIC_ANALYSIS = "strategic_analysis"
    TECHNICAL_GUIDE = "technical_guide"
    EXECUTIVE_SUMMARY = "executive_summary"
    CREATIVE_BRIEF = "creative_brief"
    RESEARCH_REPORT = "research_report"
    ACTION_PLAN = "action_plan"
    PRODUCT_SPECIFICATION = "product_specification"
    MEETING_SUMMARY = "meeting_summary"
    GENERAL_COMPOSITION = "general_composition"


class DocumentSection(BaseModel):
    """A section within a document."""
    section_id: str
    title: str
    content: str
    section_type: str = "main"  # "introduction", "main", "conclusion", "appendix"
    order_index: int = 0
    context_alignment: float = Field(default=0.0, ge=0.0, le=1.0)
    contributing_blocks: List[UUID] = Field(default_factory=list)
    contributing_contexts: List[UUID] = Field(default_factory=list)
    generation_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CompositionIntelligence(BaseModel):
    """Intelligence metadata about document composition."""
    primary_contexts: List[UUID] = Field(default_factory=list)
    secondary_contexts: List[UUID] = Field(default_factory=list)
    supporting_contexts: List[UUID] = Field(default_factory=list)
    detected_intent: Optional[str] = None
    intent_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    target_audience: Optional[str] = None
    composition_style: Optional[str] = None
    composition_scope: Optional[str] = None
    hierarchy_strength: float = Field(default=0.0, ge=0.0, le=1.0)
    context_coherence: float = Field(default=0.0, ge=0.0, le=1.0)
    composition_method: CompositionMethod = CompositionMethod.MANUAL
    agent_composer_id: Optional[str] = None
    composition_timestamp: datetime = Field(default_factory=datetime.utcnow)


class NarrativeMetadata(BaseModel):
    """Metadata about narrative generation and style."""
    generation_approach: str = "manual"  # "context_driven", "template_based", "agent_composed"
    narrative_style: str = "conversational"  # "formal", "conversational", "detailed"
    structure_type: str = "linear"  # "linear", "hierarchical", "thematic"
    audience_adaptation: Dict[str, Any] = Field(default_factory=dict)
    style_elements: List[str] = Field(default_factory=list)
    content_organization: Dict[str, Any] = Field(default_factory=dict)
    generation_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    enhancement_suggestions: List[str] = Field(default_factory=list)
    generation_timestamp: datetime = Field(default_factory=datetime.utcnow)


class DocumentCoherence(BaseModel):
    """Document coherence and alignment metrics."""
    overall_coherence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    context_coverage: float = Field(default=0.0, ge=0.0, le=1.0)
    intent_alignment: float = Field(default=0.0, ge=0.0, le=1.0)
    audience_appropriateness: float = Field(default=0.0, ge=0.0, le=1.0)
    style_consistency: float = Field(default=0.0, ge=0.0, le=1.0)
    content_coherence: float = Field(default=0.0, ge=0.0, le=1.0)
    semantic_cohesion: float = Field(default=0.0, ge=0.0, le=1.0)
    narrative_flow: float = Field(default=0.0, ge=0.0, le=1.0)
    last_analyzed: datetime = Field(default_factory=datetime.utcnow)


class BlockReference(BaseModel):
    """Reference to a block used in document composition."""
    block_id: UUID
    relevance_score: float = Field(ge=0.0, le=1.0)
    context_alignment: float = Field(ge=0.0, le=1.0)
    composition_value: float = Field(ge=0.0, le=1.0)
    discovery_reasoning: str = ""
    contributing_contexts: List[UUID] = Field(default_factory=list)
    section_placement: Optional[str] = None
    usage_metadata: Dict[str, Any] = Field(default_factory=dict)
    linked_at: datetime = Field(default_factory=datetime.utcnow)


class Document(BaseModel):
    """Core document model with context-driven composition capabilities."""
    
    # Core document fields
    id: UUID
    title: str
    content_raw: str = ""  # Raw content (markdown)
    content_rendered: str = ""  # Rendered content (HTML)
    state: DocumentState = DocumentState.DRAFT
    document_type: DocumentType = DocumentType.GENERAL_COMPOSITION
    
    # Relationships
    workspace_id: str
    basket_id: UUID
    created_by: Optional[str] = None  # User ID
    created_by_agent: Optional[str] = None  # Agent ID
    
    # Context-driven composition fields
    composition_intelligence: CompositionIntelligence = Field(default_factory=CompositionIntelligence)
    narrative_metadata: NarrativeMetadata = Field(default_factory=NarrativeMetadata)
    document_coherence: DocumentCoherence = Field(default_factory=DocumentCoherence)
    
    # Document structure
    sections: List[DocumentSection] = Field(default_factory=list)
    block_references: List[BlockReference] = Field(default_factory=list)
    
    # Metadata and tracking
    version: int = 1
    composition_metadata: Dict[str, Any] = Field(default_factory=dict)
    evolution_history: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_composed_at: Optional[datetime] = None
    last_coherence_check: Optional[datetime] = None
    
    # Configuration
    auto_recompose: bool = False  # Auto-update when context changes
    preserve_manual_edits: bool = True  # Preserve manual content changes
    
    def is_context_driven(self) -> bool:
        """Check if document was created with context intelligence."""
        return (
            self.composition_intelligence.composition_method in [
                CompositionMethod.CONTEXT_DRIVEN,
                CompositionMethod.AGENT_COMPOSED
            ]
        )
    
    def get_primary_contexts(self) -> List[UUID]:
        """Get primary context IDs driving this document."""
        return self.composition_intelligence.primary_contexts
    
    def get_all_contexts(self) -> List[UUID]:
        """Get all context IDs associated with this document."""
        return (
            self.composition_intelligence.primary_contexts +
            self.composition_intelligence.secondary_contexts +
            self.composition_intelligence.supporting_contexts
        )
    
    def get_composition_readiness(self) -> float:
        """Calculate composition readiness score."""
        factors = []
        
        # Intent clarity
        factors.append(self.composition_intelligence.intent_confidence)
        
        # Context coverage
        factors.append(self.composition_intelligence.context_coherence)
        
        # Document coherence
        factors.append(self.document_coherence.overall_coherence_score)
        
        # Hierarchy strength
        factors.append(self.composition_intelligence.hierarchy_strength)
        
        return sum(factors) / len(factors) if factors else 0.0
    
    def needs_recomposition(self, threshold: float = 0.7) -> bool:
        """Check if document needs recomposition based on coherence."""
        return self.document_coherence.overall_coherence_score < threshold
    
    def get_context_driven_metadata(self) -> Dict[str, Any]:
        """Get metadata specific to context-driven composition."""
        return {
            "is_context_driven": self.is_context_driven(),
            "composition_method": self.composition_intelligence.composition_method,
            "primary_context_count": len(self.composition_intelligence.primary_contexts),
            "total_context_count": len(self.get_all_contexts()),
            "block_reference_count": len(self.block_references),
            "section_count": len(self.sections),
            "composition_readiness": self.get_composition_readiness(),
            "needs_recomposition": self.needs_recomposition(),
            "last_composition": self.last_composed_at,
            "composition_intelligence": self.composition_intelligence.model_dump(),
            "narrative_metadata": self.narrative_metadata.model_dump(),
            "coherence_metrics": self.document_coherence.model_dump()
        }


class DocumentTemplate(BaseModel):
    """Template for creating context-driven documents."""
    id: UUID
    name: str
    description: str
    document_type: DocumentType
    template_content: str  # Markdown template with placeholders
    required_context_types: List[str] = Field(default_factory=list)
    target_audience: Optional[str] = None
    style_preference: Optional[str] = None
    section_structure: List[Dict[str, Any]] = Field(default_factory=list)
    composition_guidelines: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    workspace_id: str
    is_active: bool = True


class DocumentCompositionJob(BaseModel):
    """Represents a document composition job for async processing."""
    job_id: UUID
    request_type: str  # "context_driven", "agent_composed", "recomposition"
    basket_id: UUID
    workspace_id: str
    composition_request: Dict[str, Any] = Field(default_factory=dict)
    status: str = "pending"  # "pending", "processing", "completed", "failed"
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    result_document_id: Optional[UUID] = None
    error_message: Optional[str] = None
    processing_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: Optional[str] = None
    created_by_agent: Optional[str] = None