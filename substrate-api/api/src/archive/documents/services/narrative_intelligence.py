"""Narrative intelligence service for context-aware document generation."""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional
from uuid import UUID

from src.schemas.document_composition_schema import (
    DiscoveredBlock, NarrativeIntelligence
)

logger = logging.getLogger("uvicorn.error")


class NarrativeIntelligenceService:
    """Service for generating context-aware narrative and document content."""
    
    # Style templates for different audiences and intents
    STYLE_TEMPLATES = {
        "formal": {
            "introduction_patterns": [
                "This analysis examines",
                "This document presents",
                "The following assessment provides"
            ],
            "transition_phrases": [
                "Furthermore", "Additionally", "In consideration of",
                "Subsequently", "Therefore", "Consequently"
            ],
            "conclusion_patterns": [
                "In conclusion", "To summarize", "The analysis indicates"
            ],
            "tone_modifiers": ["comprehensive", "systematic", "thorough"]
        },
        "conversational": {
            "introduction_patterns": [
                "Let's explore", "Here's what we found", "Let's dive into"
            ],
            "transition_phrases": [
                "Also", "Plus", "What's more", "Here's the thing",
                "On top of that", "Another key point"
            ],
            "conclusion_patterns": [
                "So, to wrap up", "Here's the bottom line", "The key takeaway"
            ],
            "tone_modifiers": ["clear", "straightforward", "practical"]
        },
        "detailed": {
            "introduction_patterns": [
                "This comprehensive analysis covers",
                "The detailed examination reveals",
                "This in-depth study addresses"
            ],
            "transition_phrases": [
                "Building upon this foundation", "Examining this further",
                "Delving deeper into", "Expanding on this concept"
            ],
            "conclusion_patterns": [
                "The comprehensive analysis concludes",
                "This detailed examination demonstrates",
                "The thorough investigation reveals"
            ],
            "tone_modifiers": ["exhaustive", "meticulous", "comprehensive"]
        }
    }
    
    # Audience adaptation patterns
    AUDIENCE_ADAPTATIONS = {
        "executives": {
            "focus": "strategic_implications",
            "detail_level": "high_level",
            "metrics_emphasis": True,
            "action_orientation": True,
            "vocabulary": "business"
        },
        "engineers": {
            "focus": "implementation_details",
            "detail_level": "technical",
            "metrics_emphasis": True,
            "action_orientation": True,
            "vocabulary": "technical"
        },
        "designers": {
            "focus": "user_experience",
            "detail_level": "visual",
            "metrics_emphasis": False,
            "action_orientation": True,
            "vocabulary": "design"
        },
        "general": {
            "focus": "practical_applications",
            "detail_level": "accessible",
            "metrics_emphasis": False,
            "action_orientation": True,
            "vocabulary": "general"
        }
    }
    
    @classmethod
    async def generate_contextual_narrative(
        cls,
        composition_context: Dict[str, Any],
        discovered_blocks: List[DiscoveredBlock],
        section_organization: Dict[str, List[DiscoveredBlock]],
        custom_instructions: Optional[str] = None
    ) -> NarrativeIntelligence:
        """Generate narrative intelligence for context-driven composition."""
        
        # Determine narrative approach
        generation_approach = "context_driven"
        
        # Determine narrative style from context
        narrative_style = cls._determine_narrative_style(composition_context)
        
        # Determine structure type
        structure_type = cls._determine_structure_type(
            composition_context, section_organization
        )
        
        # Build audience adaptation
        audience_adaptation = cls._build_audience_adaptation(composition_context)
        
        # Extract style elements
        style_elements = cls._extract_style_elements(
            composition_context, narrative_style
        )
        
        # Build content organization strategy
        content_organization = cls._build_content_organization(
            composition_context, section_organization, discovered_blocks
        )
        
        # Calculate generation confidence
        generation_confidence = cls._calculate_generation_confidence(
            composition_context, discovered_blocks, section_organization
        )
        
        # Generate enhancement suggestions
        enhancement_suggestions = cls._generate_enhancement_suggestions(
            composition_context, discovered_blocks, generation_confidence
        )
        
        return NarrativeIntelligence(
            generation_approach=generation_approach,
            narrative_style=narrative_style,
            structure_type=structure_type,
            audience_adaptation=audience_adaptation,
            style_elements=style_elements,
            content_organization=content_organization,
            generation_confidence=generation_confidence,
            enhancement_suggestions=enhancement_suggestions
        )
    
    @classmethod
    async def compose_document_content(
        cls,
        title: str,
        composition_context: Dict[str, Any],
        discovered_blocks: List[DiscoveredBlock],
        section_organization: Dict[str, List[DiscoveredBlock]],
        narrative_intelligence: NarrativeIntelligence
    ) -> str:
        """Compose complete document content using narrative intelligence."""
        
        content_parts = []
        
        # Add title
        content_parts.append(f"# {title}\n")
        
        # Generate introduction
        introduction = cls._generate_introduction(
            composition_context, discovered_blocks, narrative_intelligence
        )
        content_parts.append(introduction)
        
        # Generate sections
        for section_name, section_blocks in section_organization.items():
            if section_blocks:  # Only create sections with content
                section_content = cls._generate_section_content(
                    section_name, section_blocks, composition_context, narrative_intelligence
                )
                content_parts.append(section_content)
        
        # Generate conclusion if appropriate
        if len(section_organization) > 1:  # Multi-section documents get conclusions
            conclusion = cls._generate_conclusion(
                composition_context, discovered_blocks, narrative_intelligence
            )
            content_parts.append(conclusion)
        
        return "\n\n".join(content_parts)
    
    @classmethod
    def _determine_narrative_style(cls, composition_context: Dict[str, Any]) -> str:
        """Determine narrative style from composition context."""
        
        # Check explicit style preference
        explicit_style = composition_context.get("composition_style")
        if explicit_style in ["formal", "conversational", "detailed"]:
            return explicit_style
        
        # Infer from audience
        audience = composition_context.get("target_audience")
        if audience == "executives":
            return "formal"
        elif audience == "engineers":
            return "detailed"
        elif audience in ["designers", "general"]:
            return "conversational"
        
        # Infer from intent
        intent = composition_context.get("detected_intent")
        if intent in ["strategic_analysis", "executive_summary"]:
            return "formal"
        elif intent in ["technical_guide", "research_report"]:
            return "detailed"
        else:
            return "conversational"
    
    @classmethod
    def _determine_structure_type(
        cls,
        composition_context: Dict[str, Any],
        section_organization: Dict[str, List[DiscoveredBlock]]
    ) -> str:
        """Determine document structure type."""
        
        intent = composition_context.get("detected_intent")
        
        # Intent-based structure preferences
        if intent in ["strategic_analysis", "research_report"]:
            return "hierarchical"
        elif intent in ["action_plan", "technical_guide"]:
            return "linear"
        elif intent == "creative_brief":
            return "thematic"
        else:
            # Determine by section count and organization
            section_count = len(section_organization)
            if section_count <= 2:
                return "linear"
            elif section_count >= 4:
                return "hierarchical"
            else:
                return "thematic"
    
    @classmethod
    def _build_audience_adaptation(cls, composition_context: Dict[str, Any]) -> Dict[str, Any]:
        """Build audience-specific adaptation rules."""
        
        audience = composition_context.get("target_audience", "general")
        adaptation_template = cls.AUDIENCE_ADAPTATIONS.get(audience, cls.AUDIENCE_ADAPTATIONS["general"])
        
        return {
            "target_audience": audience,
            "focus_area": adaptation_template["focus"],
            "detail_level": adaptation_template["detail_level"],
            "include_metrics": adaptation_template["metrics_emphasis"],
            "action_oriented": adaptation_template["action_orientation"],
            "vocabulary_level": adaptation_template["vocabulary"],
            "adaptation_confidence": 0.8 if audience != "general" else 0.6
        }
    
    @classmethod
    def _extract_style_elements(
        cls,
        composition_context: Dict[str, Any],
        narrative_style: str
    ) -> List[str]:
        """Extract style elements for narrative generation."""
        
        style_template = cls.STYLE_TEMPLATES.get(narrative_style, cls.STYLE_TEMPLATES["conversational"])
        
        elements = []
        elements.extend(style_template["tone_modifiers"])
        
        # Add intent-specific elements
        intent = composition_context.get("detected_intent")
        if intent == "strategic_analysis":
            elements.extend(["analytical", "forward_looking", "data_driven"])
        elif intent == "technical_guide":
            elements.extend(["step_by_step", "precise", "implementation_focused"])
        elif intent == "executive_summary":
            elements.extend(["concise", "high_impact", "decision_oriented"])
        
        return list(set(elements))  # Remove duplicates
    
    @classmethod
    def _build_content_organization(
        cls,
        composition_context: Dict[str, Any],
        section_organization: Dict[str, List[DiscoveredBlock]],
        discovered_blocks: List[DiscoveredBlock]
    ) -> Dict[str, Any]:
        """Build content organization strategy."""
        
        return {
            "total_sections": len(section_organization),
            "blocks_per_section": {
                section: len(blocks) for section, blocks in section_organization.items()
            },
            "primary_context_emphasis": len(composition_context.get("primary_contexts", [])),
            "semantic_distribution": cls._analyze_semantic_distribution(discovered_blocks),
            "relevance_weighting": "high_relevance_first",
            "context_threading": True,  # Thread context through sections
            "narrative_flow": "logical_progression"
        }
    
    @classmethod
    def _analyze_semantic_distribution(cls, discovered_blocks: List[DiscoveredBlock]) -> Dict[str, int]:
        """Analyze distribution of semantic types in discovered blocks."""
        
        distribution = {}
        for block in discovered_blocks:
            semantic_type = block.semantic_type
            distribution[semantic_type] = distribution.get(semantic_type, 0) + 1
        
        return distribution
    
    @classmethod
    def _calculate_generation_confidence(
        cls,
        composition_context: Dict[str, Any],
        discovered_blocks: List[DiscoveredBlock],
        section_organization: Dict[str, List[DiscoveredBlock]]
    ) -> float:
        """Calculate confidence in narrative generation."""
        
        factors = []
        
        # Intent confidence
        factors.append(composition_context.get("intent_confidence", 0.0))
        
        # Context hierarchy strength
        factors.append(composition_context.get("hierarchy_strength", 0.0))
        
        # Block quality (average relevance)
        if discovered_blocks:
            avg_relevance = sum(block.relevance_score for block in discovered_blocks) / len(discovered_blocks)
            factors.append(avg_relevance)
        
        # Section balance (how well blocks are distributed)
        if section_organization:
            section_counts = [len(blocks) for blocks in section_organization.values()]
            if section_counts:
                balance_score = 1.0 - (max(section_counts) - min(section_counts)) / max(section_counts)
                factors.append(max(balance_score, 0.0))
        
        # Audience clarity
        if composition_context.get("target_audience"):
            factors.append(0.8)
        else:
            factors.append(0.4)
        
        return sum(factors) / len(factors) if factors else 0.0
    
    @classmethod
    def _generate_enhancement_suggestions(
        cls,
        composition_context: Dict[str, Any],
        discovered_blocks: List[DiscoveredBlock],
        generation_confidence: float
    ) -> List[str]:
        """Generate suggestions for improving narrative generation."""
        
        suggestions = []
        
        if generation_confidence < 0.6:
            suggestions.append("Consider adding more primary contexts to strengthen composition direction")
        
        if not composition_context.get("target_audience"):
            suggestions.append("Specify target audience for more focused narrative style")
        
        if len(discovered_blocks) < 5:
            suggestions.append("Additional relevant blocks could enrich the narrative")
        
        if composition_context.get("intent_confidence", 0.0) < 0.7:
            suggestions.append("Clarify composition intent for better structural organization")
        
        # Check semantic diversity
        semantic_types = set(block.semantic_type for block in discovered_blocks)
        if len(semantic_types) < 3:
            suggestions.append("More diverse block types could improve narrative depth")
        
        return suggestions
    
    @classmethod
    def _generate_introduction(
        cls,
        composition_context: Dict[str, Any],
        discovered_blocks: List[DiscoveredBlock],
        narrative_intelligence: NarrativeIntelligence
    ) -> str:
        """Generate document introduction."""
        
        style_template = cls.STYLE_TEMPLATES.get(
            narrative_intelligence.narrative_style,
            cls.STYLE_TEMPLATES["conversational"]
        )
        
        # Choose introduction pattern
        intro_pattern = style_template["introduction_patterns"][0]
        
        # Build introduction content
        intent = composition_context.get("detected_intent", "analysis")
        audience = composition_context.get("target_audience")
        
        intro_parts = [f"## Introduction\n"]
        
        # Context-aware opening
        if intent == "strategic_analysis":
            intro_parts.append(f"{intro_pattern} the strategic landscape and key opportunities.")
        elif intent == "technical_guide":
            intro_parts.append(f"{intro_pattern} the technical implementation approach and requirements.")
        elif intent == "executive_summary":
            intro_parts.append(f"{intro_pattern} the key findings and recommendations.")
        else:
            intro_parts.append(f"{intro_pattern} the relevant insights and analysis.")
        
        # Add context about the analysis
        if len(discovered_blocks) > 0:
            intro_parts.append(
                f"\nThis analysis draws from {len(discovered_blocks)} relevant insights "
                f"to provide {'executives' if audience == 'executives' else 'stakeholders'} "
                f"with actionable intelligence."
            )
        
        return " ".join(intro_parts)
    
    @classmethod
    def _generate_section_content(
        cls,
        section_name: str,
        section_blocks: List[DiscoveredBlock],
        composition_context: Dict[str, Any],
        narrative_intelligence: NarrativeIntelligence
    ) -> str:
        """Generate content for a document section."""
        
        if not section_blocks:
            return ""
        
        section_parts = []
        
        # Section header
        section_title = section_name.replace("_", " ").title()
        section_parts.append(f"## {section_title}\n")
        
        # Section introduction
        style_template = cls.STYLE_TEMPLATES.get(
            narrative_intelligence.narrative_style,
            cls.STYLE_TEMPLATES["conversational"]
        )
        
        # Generate section content from blocks
        for i, block in enumerate(section_blocks):
            block_content = cls._format_block_content(
                block, narrative_intelligence, is_first=(i == 0)
            )
            section_parts.append(block_content)
            
            # Add transitions between blocks
            if i < len(section_blocks) - 1:
                transition = style_template["transition_phrases"][i % len(style_template["transition_phrases"])]
                section_parts.append(f"\n{transition}, ")
        
        return "".join(section_parts)
    
    @classmethod
    def _format_block_content(
        cls,
        block: DiscoveredBlock,
        narrative_intelligence: NarrativeIntelligence,
        is_first: bool = False
    ) -> str:
        """Format individual block content for narrative flow."""
        
        content = block.content
        
        # Add context about why this block is relevant
        if block.relevance_score > 0.8:
            relevance_intro = "This key insight reveals that "
        elif block.relevance_score > 0.6:
            relevance_intro = "Analysis shows that "
        else:
            relevance_intro = "It's worth noting that "
        
        # Format based on semantic type
        if block.semantic_type == "goal":
            formatted_content = f"{relevance_intro}the objective is to {content.lower()}"
        elif block.semantic_type == "insight":
            formatted_content = f"{relevance_intro}{content}"
        elif block.semantic_type == "constraint":
            formatted_content = f"{relevance_intro}there is a constraint: {content}"
        else:
            formatted_content = f"{relevance_intro}{content}"
        
        return formatted_content + ".\n\n"
    
    @classmethod
    def _generate_conclusion(
        cls,
        composition_context: Dict[str, Any],
        discovered_blocks: List[DiscoveredBlock],
        narrative_intelligence: NarrativeIntelligence
    ) -> str:
        """Generate document conclusion."""
        
        style_template = cls.STYLE_TEMPLATES.get(
            narrative_intelligence.narrative_style,
            cls.STYLE_TEMPLATES["conversational"]
        )
        
        conclusion_pattern = style_template["conclusion_patterns"][0]
        
        conclusion_parts = [f"## Conclusion\n"]
        
        # Intent-specific conclusion
        intent = composition_context.get("detected_intent")
        if intent == "strategic_analysis":
            conclusion_parts.append(
                f"{conclusion_pattern}, this strategic analysis highlights key opportunities "
                f"for organizational growth and competitive advantage."
            )
        elif intent == "action_plan":
            conclusion_parts.append(
                f"{conclusion_pattern}, the outlined action items provide a clear path "
                f"toward achieving the stated objectives."
            )
        else:
            conclusion_parts.append(
                f"{conclusion_pattern}, the analysis provides valuable insights "
                f"for informed decision-making."
            )
        
        # Add next steps if action-oriented
        audience_adaptation = narrative_intelligence.audience_adaptation
        if audience_adaptation.get("action_oriented", False):
            conclusion_parts.append(
                "\n\nRecommended next steps include reviewing these findings with stakeholders "
                "and developing implementation strategies based on the insights presented."
            )
        
        return " ".join(conclusion_parts)