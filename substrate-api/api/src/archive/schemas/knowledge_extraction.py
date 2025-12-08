"""
Knowledge Extraction Schema for P1 Substrate Agent
Defines structured data ingredients that blocks should contain.
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum


class ProvenanceSpan(BaseModel):
    """Text span reference for provenance tracking."""
    start: int = Field(description="Character start position in source text")
    end: int = Field(description="Character end position in source text")
    text: str = Field(description="Extracted text for validation")


class Provenance(BaseModel):
    """Provenance tracking for extracted knowledge."""
    dump_id: str = Field(description="Source dump UUID")
    ranges: List[ProvenanceSpan] = Field(description="Text spans supporting this extraction")
    extraction_method: str = Field(default="llm_structured_extraction")
    confidence: float = Field(ge=0.0, le=1.0, description="Provenance confidence")


class EntityType(str, Enum):
    """Types of entities that can be extracted."""
    PERSON = "person"
    ORGANIZATION = "organization"
    PROJECT = "project"
    CONCEPT = "concept"
    TOOL = "tool"
    PROCESS = "process"
    GOAL = "goal"
    CONSTRAINT = "constraint"
    METRIC = "metric"


class RelationshipType(str, Enum):
    """Types of relationships between entities."""
    DEPENDS_ON = "depends_on"
    CONFLICTS_WITH = "conflicts_with"
    ENABLES = "enables"
    MEASURES = "measures"
    OWNS = "owns"
    PARTICIPATES_IN = "participates_in"
    IMPLEMENTS = "implements"
    REQUIRES = "requires"


class Entity(BaseModel):
    """A structured entity extracted from raw content."""
    name: str = Field(description="Canonical name of the entity")
    type: EntityType = Field(description="Classification of the entity")
    description: Optional[str] = Field(default=None, description="Brief description")
    attributes: Dict[str, Union[str, float, bool]] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0, description="Extraction confidence")
    provenance: Provenance = Field(description="Source text provenance")


class Relationship(BaseModel):
    """A relationship between two entities."""
    source_entity: str = Field(description="Source entity name")
    target_entity: str = Field(description="Target entity name")
    relationship_type: RelationshipType = Field(description="Type of relationship")
    strength: float = Field(ge=0.0, le=1.0, description="Relationship strength")
    evidence: Optional[str] = Field(default=None, description="Text evidence for relationship")


class Goal(BaseModel):
    """A goal or objective extracted from content."""
    title: str = Field(description="Goal title")
    description: str = Field(description="Detailed goal description")
    success_criteria: List[str] = Field(default_factory=list)
    priority: Optional[str] = Field(default=None, description="high/medium/low")
    timeline: Optional[str] = Field(default=None, description="Expected timeframe")
    owner: Optional[str] = Field(default=None, description="Responsible entity")
    confidence: float = Field(ge=0.0, le=1.0)
    provenance: Provenance = Field(description="Source text provenance")


class Constraint(BaseModel):
    """A constraint or limitation extracted from content."""
    title: str = Field(description="Constraint title")
    description: str = Field(description="Detailed constraint description")
    constraint_type: str = Field(description="time/resource/technical/policy/etc")
    impact_level: Optional[str] = Field(default=None, description="high/medium/low")
    affected_entities: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    provenance: Provenance = Field(description="Source text provenance")


class Metric(BaseModel):
    """A metric or measurement extracted from content."""
    name: str = Field(description="Metric name")
    description: str = Field(description="What this metric measures")
    unit: Optional[str] = Field(default=None, description="Unit of measurement")
    target_value: Optional[Union[str, float]] = Field(default=None)
    current_value: Optional[Union[str, float]] = Field(default=None)
    measurement_method: Optional[str] = Field(default=None)
    confidence: float = Field(ge=0.0, le=1.0)
    provenance: Provenance = Field(description="Source text provenance")


class KnowledgeIngredients(BaseModel):
    """Complete structured knowledge extracted from raw content."""
    
    # Core structured data
    entities: List[Entity] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)
    goals: List[Goal] = Field(default_factory=list)
    constraints: List[Constraint] = Field(default_factory=list)
    metrics: List[Metric] = Field(default_factory=list)
    
    # Semantic classification
    primary_theme: Optional[str] = Field(default=None, description="Main topic/theme")
    secondary_themes: List[str] = Field(default_factory=list)
    content_type: str = Field(description="meeting_notes/requirements/analysis/etc")
    
    # Quality metadata
    extraction_confidence: float = Field(ge=0.0, le=1.0, description="Overall extraction quality")
    semantic_density: float = Field(ge=0.0, le=1.0, description="Information density score")
    
    # Raw context preservation
    key_quotes: List[str] = Field(default_factory=list, description="Important verbatim text")
    source_structure: Optional[str] = Field(default=None, description="Original formatting hints")


class BlockIngredient(BaseModel):
    """A block as a data ingredient with structured knowledge."""
    
    # Identity
    semantic_type: str = Field(description="goal/constraint/metric/entity/process/etc")
    title: str = Field(description="Human-readable block title")
    
    # Structured knowledge (the "ingredient")
    ingredients: KnowledgeIngredients = Field(description="Extracted structured data")
    
    # Transformation metadata
    transformation_hints: Dict[str, Any] = Field(
        default_factory=dict,
        description="Hints for how this ingredient can be transformed/composed"
    )
    
    # Quality scores
    confidence: float = Field(ge=0.0, le=1.0, description="Overall block confidence")
    reusability_score: float = Field(ge=0.0, le=1.0, description="How reusable this ingredient is")
    
    # Provenance
    source_dump_id: str = Field(description="Source raw dump")
    extraction_timestamp: str = Field(description="When extracted")
    
    # Legacy compatibility (for gradual migration)
    legacy_content: Optional[str] = Field(
        default=None, 
        description="Original text content for backward compatibility"
    )


class ExtractionPromptTemplate(BaseModel):
    """Template for LLM knowledge extraction prompts."""
    
    system_prompt: str = Field(description="System instructions for extraction")
    user_template: str = Field(description="Template with {content} placeholder")
    response_schema: str = Field(description="JSON schema for expected response")
    max_tokens: int = Field(default=4000)
    temperature: float = Field(default=0.1, ge=0.0, le=1.0)


class KnowledgeBlock(BaseModel):
    """A structured knowledge block with provenance."""
    semantic_type: str = Field(description="Type of knowledge (goal/constraint/entity/etc)")
    title: str = Field(description="Block title")
    entities: List[Entity] = Field(default_factory=list)
    goals: List[Goal] = Field(default_factory=list)
    constraints: List[Constraint] = Field(default_factory=list)
    metrics: List[Metric] = Field(default_factory=list)
    primary_theme: Optional[str] = Field(default=None)
    confidence: float = Field(ge=0.0, le=1.0)
    provenance: Provenance = Field(description="Overall block provenance")


class KnowledgeBlockList(BaseModel):
    """List of knowledge blocks for LLM structured output."""
    blocks: List[KnowledgeBlock] = Field(description="Extracted knowledge blocks")
    extraction_metadata: Dict[str, Any] = Field(default_factory=dict)


# Default extraction prompt for P1 agent
DEFAULT_EXTRACTION_PROMPT = ExtractionPromptTemplate(
    system_prompt="""You extract structured knowledge from raw text.
Return ONLY the JSON that matches the provided schema.
All items MUST include provenance spans [start,end] that index into the original text.""",

    user_template="""Text to extract from:
{content}

Instructions:
- Identify goals, constraints, metrics, entities, relationships, timelines, evidence, quotes, findings.
- Normalize metrics: {{name, value, unit, period}}.
- Dates ISO-8601 when possible.
- provenance.dump_id must match the provided dump_id; add at least one [start,end] per item.""",

    response_schema="KnowledgeBlockList",
    max_tokens=4000,
    temperature=0.0
)