"""
Focused Extraction Schema - Simplified for Real-World Quality

Replaces the overly complex knowledge_extraction.py with practical schemas
that LLMs can actually execute reliably.
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from enum import Enum


class ContentType(str, Enum):
    """Content types for domain-specific extraction"""
    FINANCIAL = "financial"
    SECURITY = "security" 
    PRODUCT = "product"
    MEETING = "meeting"
    TECHNICAL = "technical"
    GENERAL = "general"


class ExtractedFact(BaseModel):
    """A simple fact extracted from content"""
    text: str = Field(description="The factual statement")
    type: Literal[
        "metric",
        "event",
        "status",
        "quote",
        "finding",
        "fact",
        "feature",
        "feature performance",
        "technical",
        "technical capability",
        "pricing",
        "monetization",
    ] = Field(description="Type of fact")
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    source_hint: Optional[str] = Field(default=None, description="Simple source reference")


class ExtractedInsight(BaseModel):
    """An insight or analysis from the content"""
    insight: str = Field(description="The key insight or analysis")
    supporting_facts: List[str] = Field(description="Facts that support this insight")
    confidence: float = Field(ge=0.0, le=1.0, default=0.7)


class ExtractedAction(BaseModel):
    """An action item or recommendation"""
    action: str = Field(description="What should be done")
    priority: Literal["high", "medium", "low"] = Field(description="Action priority")
    timeline: Optional[str] = Field(default=None, description="When it should be done")
    owner: Optional[str] = Field(default=None, description="Who should do it")


class ExtractedContext(BaseModel):
    """Important contextual information"""
    entity: str = Field(description="Person, company, product, etc.")
    role: str = Field(description="How this entity relates to the content")
    details: Optional[str] = Field(default=None, description="Additional context")


class FocusedExtraction(BaseModel):
    """Simple, focused extraction that LLMs can execute reliably"""
    
    # Core content
    summary: str = Field(description="2-3 sentence summary of the content")
    facts: List[ExtractedFact] = Field(description="Key factual statements")
    insights: List[ExtractedInsight] = Field(description="Analysis and insights")
    actions: List[ExtractedAction] = Field(description="Action items and recommendations")
    context: List[ExtractedContext] = Field(description="Important entities and context")
    
    # Content classification
    content_type: ContentType = Field(description="Type of content for downstream processing")
    primary_theme: str = Field(description="Main topic in 2-3 words")
    
    # Quality metadata
    extraction_confidence: float = Field(ge=0.0, le=1.0, description="Overall extraction quality")


# Domain-specific extraction prompts
FINANCIAL_EXTRACTION_PROMPT = """You are analyzing financial content. Extract:

FACTS (metrics, events, status, quotes, findings):
- Revenue figures, growth rates, margins
- Key performance indicators
- Market conditions and events
- Executive quotes and commentary
- Analyst observations

INSIGHTS (analysis that requires reasoning):
- What trends do the numbers reveal?
- What are the strategic implications?
- What risks or opportunities are indicated?
- How do results compare to expectations?

ACTIONS (recommendations, next steps):
- What should investors/management do?
- What areas need attention?
- What decisions are required?

CONTEXT (entities and their roles):
- Companies, executives, products mentioned
- Market segments, competitors
- Time periods, geographic regions"""

SECURITY_EXTRACTION_PROMPT = """You are analyzing security incident content. Extract:

FACTS (events, findings, metrics):
- Timeline of events with timestamps
- Attack vectors and techniques used
- Systems affected and data accessed
- Controls that worked/failed
- Quantified impact (users, records, downtime)

INSIGHTS (analysis of the incident):
- How did the attack succeed?
- What was the root cause?
- Which controls were effective?
- What patterns indicate broader risk?

ACTIONS (immediate and long-term):
- Immediate containment steps
- Investigation priorities
- Process improvements needed
- Policy/technical changes required

CONTEXT (entities and roles):
- Attackers, affected systems, stakeholders
- Vulnerabilities, tools, techniques
- Business processes impacted"""

PRODUCT_EXTRACTION_PROMPT = """You are analyzing product/business content. Extract:

FACTS (metrics, status, feedback):
- User metrics and adoption data
- Feature performance and usage
- Customer feedback and satisfaction
- Market data and competitive position
- Technical capabilities and limitations

INSIGHTS (strategic analysis):
- What do user patterns reveal?
- Where is product-market fit strong/weak?
- What competitive advantages exist?
- What market opportunities are indicated?

ACTIONS (product decisions needed):
- Feature priorities and roadmap items
- Market positioning changes
- Resource allocation decisions
- Partnership or investment needs

CONTEXT (stakeholders and market):
- Customer segments, user personas
- Competitors, partners, technologies
- Market trends, business model factors"""

GENERAL_EXTRACTION_PROMPT = """You are analyzing general content. Extract:

FACTS (key information):
- Important statements and data points
- Events and their outcomes
- Status updates and progress
- Quotes and key messages

INSIGHTS (analysis and reasoning):
- What patterns or trends emerge?
- What are the implications?
- What connections exist between facts?
- What conclusions can be drawn?

ACTIONS (what should happen next):
- Decisions that need to be made
- Tasks that should be completed
- Areas requiring attention
- Next steps to take

CONTEXT (important background):
- Key people, organizations, concepts
- Relationships and dependencies
- Historical context and precedents"""


class ExtractionTemplate(BaseModel):
    """Template for domain-specific extraction"""
    content_type: ContentType
    system_prompt: str
    extraction_guidance: str
    max_tokens: int = Field(default=2000)
    temperature: float = Field(default=0.1)


# Pre-defined templates for each domain
EXTRACTION_TEMPLATES = {
    ContentType.FINANCIAL: ExtractionTemplate(
        content_type=ContentType.FINANCIAL,
        system_prompt="""You extract structured information from financial content.
Focus on metrics, trends, strategic implications, and actionable insights.
Return only valid JSON matching the FocusedExtraction schema.""",
        extraction_guidance=FINANCIAL_EXTRACTION_PROMPT,
        max_tokens=2500
    ),
    
    ContentType.SECURITY: ExtractionTemplate(
        content_type=ContentType.SECURITY,
        system_prompt="""You extract structured information from security incident content.
Focus on timeline, attack vectors, impact, and response actions.
Return only valid JSON matching the FocusedExtraction schema.""",
        extraction_guidance=SECURITY_EXTRACTION_PROMPT,
        max_tokens=2500
    ),
    
    ContentType.PRODUCT: ExtractionTemplate(
        content_type=ContentType.PRODUCT,
        system_prompt="""You extract structured information from product/business content.
Focus on user insights, market analysis, and strategic decisions.
Return only valid JSON matching the FocusedExtraction schema.""",
        extraction_guidance=PRODUCT_EXTRACTION_PROMPT,
        max_tokens=2500
    ),
    
    ContentType.GENERAL: ExtractionTemplate(
        content_type=ContentType.GENERAL,
        system_prompt="""You extract structured information from general content.
Focus on key facts, insights, actions, and context.
Return only valid JSON matching the FocusedExtraction schema.""",
        extraction_guidance=GENERAL_EXTRACTION_PROMPT,
        max_tokens=2000
    )
}


def detect_content_type(text: str) -> ContentType:
    """Detect content type from text for template selection"""
    text_lower = text.lower()
    
    # Financial indicators
    financial_keywords = ["revenue", "profit", "earnings", "quarter", "margin", "growth", 
                         "financial", "ceo", "cfo", "investor", "stock", "market cap"]
    financial_score = sum(1 for kw in financial_keywords if kw in text_lower)
    
    # Security indicators  
    security_keywords = ["incident", "attack", "vulnerability", "breach", "malware",
                        "security", "threat", "compromise", "exploit", "cve"]
    security_score = sum(1 for kw in security_keywords if kw in text_lower)
    
    # Product indicators
    product_keywords = ["product", "feature", "user", "customer", "feedback", "market",
                       "adoption", "retention", "roadmap", "competitive"]
    product_score = sum(1 for kw in product_keywords if kw in text_lower)
    
    # Determine type based on highest score
    scores = {
        ContentType.FINANCIAL: financial_score,
        ContentType.SECURITY: security_score, 
        ContentType.PRODUCT: product_score
    }
    
    max_score = max(scores.values())
    if max_score >= 3:  # Minimum threshold for classification
        return max(scores.items(), key=lambda x: x[1])[0]
    
    return ContentType.GENERAL
