"""Document architect service for intelligent structure and organization."""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID

from src.schemas.document_composition_schema import (
    DiscoveredBlock, CompositionSuggestion, CompositionOpportunityAnalysis
)
from ...context.services.composition_intelligence import CompositionIntelligenceService
from ...context.services.context_hierarchy import ContextHierarchyService

logger = logging.getLogger("uvicorn.error")


class DocumentArchitectService:
    """Service for intelligent document structure and composition architecture."""
    
    # Document architectures by intent type
    DOCUMENT_ARCHITECTURES = {
        "strategic_analysis": {
            "sections": [
                {"name": "executive_summary", "weight": 0.2, "required": True},
                {"name": "current_situation", "weight": 0.25, "required": True},
                {"name": "strategic_analysis", "weight": 0.3, "required": True},
                {"name": "opportunities", "weight": 0.15, "required": False},
                {"name": "recommendations", "weight": 0.1, "required": True}
            ],
            "preferred_blocks": ["goal", "insight", "constraint"],
            "min_blocks": 8,
            "max_blocks": 20,
            "complexity": "high"
        },
        "technical_guide": {
            "sections": [
                {"name": "overview", "weight": 0.15, "required": True},
                {"name": "prerequisites", "weight": 0.1, "required": False},
                {"name": "implementation", "weight": 0.5, "required": True},
                {"name": "examples", "weight": 0.15, "required": False},
                {"name": "troubleshooting", "weight": 0.1, "required": False}
            ],
            "preferred_blocks": ["insight", "constraint", "reference"],
            "min_blocks": 6,
            "max_blocks": 25,
            "complexity": "high"
        },
        "executive_summary": {
            "sections": [
                {"name": "key_findings", "weight": 0.4, "required": True},
                {"name": "recommendations", "weight": 0.35, "required": True},
                {"name": "next_steps", "weight": 0.25, "required": False}
            ],
            "preferred_blocks": ["goal", "insight"],
            "min_blocks": 3,
            "max_blocks": 8,
            "complexity": "simple"
        },
        "action_plan": {
            "sections": [
                {"name": "objectives", "weight": 0.2, "required": True},
                {"name": "action_items", "weight": 0.4, "required": True},
                {"name": "timeline", "weight": 0.2, "required": True},
                {"name": "resources", "weight": 0.2, "required": False}
            ],
            "preferred_blocks": ["goal", "constraint"],
            "min_blocks": 5,
            "max_blocks": 15,
            "complexity": "medium"
        },
        "research_report": {
            "sections": [
                {"name": "background", "weight": 0.15, "required": True},
                {"name": "methodology", "weight": 0.1, "required": False},
                {"name": "findings", "weight": 0.5, "required": True},
                {"name": "analysis", "weight": 0.15, "required": True},
                {"name": "conclusions", "weight": 0.1, "required": True}
            ],
            "preferred_blocks": ["insight", "reference", "constraint"],
            "min_blocks": 8,
            "max_blocks": 30,
            "complexity": "high"
        },
        "creative_brief": {
            "sections": [
                {"name": "overview", "weight": 0.25, "required": True},
                {"name": "concept", "weight": 0.35, "required": True},
                {"name": "guidelines", "weight": 0.25, "required": True},
                {"name": "deliverables", "weight": 0.15, "required": False}
            ],
            "preferred_blocks": ["theme", "insight", "reference"],
            "min_blocks": 4,
            "max_blocks": 12,
            "complexity": "medium"
        }
    }
    
    @classmethod
    async def analyze_composition_opportunities(
        cls,
        basket_id: UUID,
        workspace_id: str
    ) -> CompositionOpportunityAnalysis:
        """Analyze and suggest document composition opportunities."""
        
        # Get composition intelligence analysis
        composition_analysis = await CompositionIntelligenceService.analyze_composition_intelligence(
            basket_id=basket_id,
            workspace_id=workspace_id
        )
        
        # Get context hierarchy
        hierarchy = await ContextHierarchyService.analyze_context_hierarchy(
            basket_id=basket_id,
            workspace_id=workspace_id
        )
        
        # Analyze existing blocks and contexts
        block_analysis = await cls._analyze_available_blocks(basket_id, workspace_id)
        
        # Generate composition suggestions
        suggestions = cls._generate_composition_suggestions(
            composition_analysis, hierarchy, block_analysis
        )
        
        # Identify gaps and missing elements
        context_gaps = cls._identify_context_gaps(
            composition_analysis, hierarchy, suggestions
        )
        
        # Calculate overall readiness
        readiness_score = cls._calculate_composition_readiness(
            composition_analysis, hierarchy, block_analysis
        )
        
        # Generate recommendations
        next_steps = cls._generate_composition_recommendations(
            suggestions, context_gaps, readiness_score
        )
        
        return CompositionOpportunityAnalysis(
            basket_id=basket_id,
            total_opportunities=len(suggestions),
            high_value_opportunities=len([s for s in suggestions if s.expected_value == "high"]),
            composition_readiness_score=readiness_score,
            suggested_compositions=suggestions,
            missing_context_types=cls._extract_missing_context_types(context_gaps),
            context_gaps=context_gaps,
            recommended_next_steps=next_steps,
            analysis_metadata={
                "primary_contexts": len(hierarchy.primary_contexts),
                "secondary_contexts": len(hierarchy.secondary_contexts),
                "total_blocks": block_analysis.get("total_blocks", 0),
                "intent_confidence": composition_analysis.intent_analysis.intent_confidence
            }
        )
    
    @classmethod
    def suggest_document_structure(
        cls,
        composition_intent: str,
        discovered_blocks: List[DiscoveredBlock],
        target_audience: Optional[str] = None
    ) -> Dict[str, Any]:
        """Suggest optimal document structure based on intent and available blocks."""
        
        # Get architecture template
        architecture = cls.DOCUMENT_ARCHITECTURES.get(
            composition_intent,
            cls.DOCUMENT_ARCHITECTURES["executive_summary"]  # Default fallback
        )
        
        # Adapt structure based on available blocks
        adapted_structure = cls._adapt_structure_to_blocks(
            architecture, discovered_blocks, target_audience
        )
        
        # Calculate structure confidence
        structure_confidence = cls._calculate_structure_confidence(
            architecture, discovered_blocks, adapted_structure
        )
        
        return {
            "composition_intent": composition_intent,
            "suggested_sections": adapted_structure["sections"],
            "estimated_length": adapted_structure["estimated_length"],
            "complexity_level": architecture["complexity"],
            "structure_confidence": structure_confidence,
            "optimization_notes": adapted_structure["optimization_notes"],
            "audience_adaptations": adapted_structure.get("audience_adaptations", [])
        }
    
    @classmethod
    def optimize_block_placement(
        cls,
        document_structure: Dict[str, Any],
        discovered_blocks: List[DiscoveredBlock]
    ) -> Dict[str, List[DiscoveredBlock]]:
        """Optimize placement of discovered blocks within document structure."""
        
        sections = {section["name"]: [] for section in document_structure["suggested_sections"]}
        
        # Smart block placement based on semantic type and relevance
        for block in discovered_blocks:
            optimal_section = cls._find_optimal_section(
                block, document_structure["suggested_sections"]
            )
            sections[optimal_section].append(block)
        
        # Balance sections and ensure minimum content
        sections = cls._balance_section_content(sections, document_structure)
        
        # Sort blocks within sections by relevance
        for section_name, section_blocks in sections.items():
            section_blocks.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return sections
    
    @classmethod
    async def _analyze_available_blocks(
        cls,
        basket_id: UUID,
        workspace_id: str
    ) -> Dict[str, Any]:
        """Analyze available blocks for composition opportunities."""
        
        from ...utils.supabase_client import supabase_client as supabase
        
        try:
            # Get all blocks in basket
            resp = (
                supabase.table("blocks")
                .select("id,semantic_type,content,state,created_at")
                .eq("basket_id", str(basket_id))
                .eq("workspace_id", workspace_id)
                .neq("state", "REJECTED")
                .execute()
            )
            
            blocks = resp.data or []
            
            # Analyze block distribution
            semantic_distribution = {}
            state_distribution = {}
            
            for block in blocks:
                # Semantic type distribution
                semantic_type = block.get("semantic_type", "unknown")
                semantic_distribution[semantic_type] = semantic_distribution.get(semantic_type, 0) + 1
                
                # State distribution
                state = block.get("state", "PROPOSED")
                state_distribution[state] = state_distribution.get(state, 0) + 1
            
            return {
                "total_blocks": len(blocks),
                "semantic_distribution": semantic_distribution,
                "state_distribution": state_distribution,
                "mature_blocks": state_distribution.get("ACCEPTED", 0) + state_distribution.get("LOCKED", 0),
                "diversity_score": len(semantic_distribution) / max(len(blocks), 1)
            }
            
        except Exception as e:
            logger.exception(f"Failed to analyze blocks: {e}")
            return {"total_blocks": 0, "semantic_distribution": {}, "state_distribution": {}}
    
    @classmethod
    def _generate_composition_suggestions(
        cls,
        composition_analysis,
        hierarchy,
        block_analysis: Dict[str, Any]
    ) -> List[CompositionSuggestion]:
        """Generate specific composition suggestions based on analysis."""
        
        suggestions = []
        total_blocks = block_analysis.get("total_blocks", 0)
        semantic_dist = block_analysis.get("semantic_distribution", {})
        
        # Primary intent suggestion
        if composition_analysis.intent_analysis.primary_intent:
            primary_intent = composition_analysis.intent_analysis.primary_intent
            confidence = composition_analysis.intent_analysis.intent_confidence
            
            if primary_intent in cls.DOCUMENT_ARCHITECTURES:
                architecture = cls.DOCUMENT_ARCHITECTURES[primary_intent]
                
                # Check if we have enough blocks
                meets_minimum = total_blocks >= architecture["min_blocks"]
                has_preferred_types = any(
                    semantic_dist.get(block_type, 0) > 0 
                    for block_type in architecture["preferred_blocks"]
                )
                
                suggestions.append(CompositionSuggestion(
                    suggestion_id=f"primary_{primary_intent}",
                    composition_type=primary_intent,
                    suggested_title=cls._generate_title_for_intent(primary_intent, hierarchy),
                    confidence=confidence,
                    primary_contexts=[ctx.id for ctx in hierarchy.primary_contexts],
                    estimated_block_count=min(total_blocks, architecture["max_blocks"]),
                    target_audience=composition_analysis.intent_analysis.audience_indicators[0] 
                    if composition_analysis.intent_analysis.audience_indicators else None,
                    suggested_style=composition_analysis.intent_analysis.style_indicators[0]
                    if composition_analysis.intent_analysis.style_indicators else None,
                    composition_rationale=f"Primary detected intent with {confidence:.1%} confidence",
                    expected_value="high" if meets_minimum and has_preferred_types else "medium",
                    creation_complexity=architecture["complexity"],
                    prerequisite_contexts=architecture["preferred_blocks"] if not has_preferred_types else []
                ))
        
        # Alternative intent suggestions
        for intent in composition_analysis.intent_analysis.detected_intents:
            if intent != composition_analysis.intent_analysis.primary_intent and intent in cls.DOCUMENT_ARCHITECTURES:
                architecture = cls.DOCUMENT_ARCHITECTURES[intent]
                
                # Lower confidence for alternative intents
                alt_confidence = min(composition_analysis.intent_analysis.intent_confidence * 0.7, 0.8)
                
                meets_minimum = total_blocks >= architecture["min_blocks"]
                
                suggestions.append(CompositionSuggestion(
                    suggestion_id=f"alt_{intent}",
                    composition_type=intent,
                    suggested_title=cls._generate_title_for_intent(intent, hierarchy),
                    confidence=alt_confidence,
                    primary_contexts=[ctx.id for ctx in hierarchy.primary_contexts[:1]], # Use top primary context
                    estimated_block_count=min(total_blocks, architecture["max_blocks"]),
                    composition_rationale=f"Alternative composition approach based on detected patterns",
                    expected_value="medium" if meets_minimum else "low",
                    creation_complexity=architecture["complexity"]
                ))
        
        # Always suggest executive summary if we have enough blocks
        if total_blocks >= 3 and not any(s.composition_type == "executive_summary" for s in suggestions):
            suggestions.append(CompositionSuggestion(
                suggestion_id="summary_fallback",
                composition_type="executive_summary",
                suggested_title="Executive Summary",
                confidence=0.6,
                primary_contexts=[ctx.id for ctx in hierarchy.primary_contexts],
                estimated_block_count=min(total_blocks, 8),
                composition_rationale="Fallback option suitable for any content set",
                expected_value="medium",
                creation_complexity="simple"
            ))
        
        # Sort by confidence and expected value
        suggestions.sort(key=lambda x: (
            {"high": 3, "medium": 2, "low": 1}[x.expected_value],
            x.confidence
        ), reverse=True)
        
        return suggestions[:5]  # Limit to top 5 suggestions
    
    @classmethod
    def _identify_context_gaps(
        cls,
        composition_analysis,
        hierarchy,
        suggestions: List[CompositionSuggestion]
    ) -> List[Dict[str, Any]]:
        """Identify gaps in context coverage for composition."""
        
        gaps = []
        
        # Check for missing primary contexts
        if not hierarchy.primary_contexts:
            gaps.append({
                "gap_type": "missing_primary_contexts",
                "description": "No primary contexts identified to drive composition",
                "impact": "high",
                "suggested_action": "Identify and promote key contexts to primary level"
            })
        
        # Check for intent clarity
        if composition_analysis.intent_analysis.intent_confidence < 0.6:
            gaps.append({
                "gap_type": "unclear_intent",
                "description": "Composition intent is not clearly defined",
                "impact": "medium",
                "suggested_action": "Add context items that clarify the document's purpose"
            })
        
        # Check for audience definition
        if not composition_analysis.intent_analysis.audience_indicators:
            gaps.append({
                "gap_type": "undefined_audience",
                "description": "Target audience is not clearly defined",
                "impact": "medium",
                "suggested_action": "Add audience-specific context items"
            })
        
        # Check for insufficient context diversity
        total_contexts = len(hierarchy.primary_contexts) + len(hierarchy.secondary_contexts)
        if total_contexts < 3:
            gaps.append({
                "gap_type": "insufficient_context_diversity",
                "description": "Limited context diversity may result in narrow composition",
                "impact": "low",
                "suggested_action": "Add supporting contexts to provide broader perspective"
            })
        
        return gaps
    
    @classmethod
    def _calculate_composition_readiness(
        cls,
        composition_analysis,
        hierarchy,
        block_analysis: Dict[str, Any]
    ) -> float:
        """Calculate overall composition readiness score."""
        
        factors = []
        
        # Intent clarity
        factors.append(composition_analysis.intent_analysis.intent_confidence)
        
        # Context hierarchy strength
        factors.append(hierarchy.composition_score)
        
        # Block availability
        total_blocks = block_analysis.get("total_blocks", 0)
        block_factor = min(total_blocks / 10, 1.0)  # Ideal: 10+ blocks
        factors.append(block_factor)
        
        # Block maturity (accepted/locked blocks are better)
        mature_blocks = block_analysis.get("mature_blocks", 0)
        if total_blocks > 0:
            maturity_factor = mature_blocks / total_blocks
            factors.append(maturity_factor)
        
        # Semantic diversity
        diversity_score = block_analysis.get("diversity_score", 0.0)
        factors.append(diversity_score)
        
        return sum(factors) / len(factors) if factors else 0.0
    
    @classmethod
    def _generate_composition_recommendations(
        cls,
        suggestions: List[CompositionSuggestion],
        context_gaps: List[Dict[str, Any]],
        readiness_score: float
    ) -> List[str]:
        """Generate actionable composition recommendations."""
        
        recommendations = []
        
        # Readiness-based recommendations
        if readiness_score < 0.4:
            recommendations.append("Focus on building composition foundation before creating documents")
            recommendations.append("Address identified context gaps to improve readiness")
        elif readiness_score < 0.7:
            recommendations.append("Consider starting with simpler compositions while building context")
            recommendations.append("Iteratively improve context quality and block coverage")
        else:
            recommendations.append("Ready for advanced document composition")
            recommendations.append("Consider creating multiple document types to serve different audiences")
        
        # Gap-specific recommendations
        high_impact_gaps = [gap for gap in context_gaps if gap["impact"] == "high"]
        if high_impact_gaps:
            recommendations.append("Prioritize resolving high-impact context gaps")
        
        # Suggestion-specific recommendations
        high_value_suggestions = [s for s in suggestions if s.expected_value == "high"]
        if high_value_suggestions:
            recommendations.append(f"Start with {high_value_suggestions[0].composition_type} as the highest-value opportunity")
        
        if len(suggestions) > 1:
            recommendations.append("Consider creating multiple compositions to serve different purposes")
        
        return recommendations
    
    @classmethod
    def _extract_missing_context_types(cls, context_gaps: List[Dict[str, Any]]) -> List[str]:
        """Extract missing context types from gap analysis."""
        
        missing_types = set()
        
        for gap in context_gaps:
            if gap["gap_type"] == "missing_primary_contexts":
                missing_types.add("goal")
                missing_types.add("theme")
            elif gap["gap_type"] == "undefined_audience":
                missing_types.add("audience")
            elif gap["gap_type"] == "insufficient_context_diversity":
                missing_types.update(["insight", "reference", "constraint"])
        
        return list(missing_types)
    
    @classmethod
    def _generate_title_for_intent(cls, intent: str, hierarchy) -> str:
        """Generate suggested title based on intent and context."""
        
        title_templates = {
            "strategic_analysis": "Strategic Analysis",
            "technical_guide": "Technical Implementation Guide",
            "executive_summary": "Executive Summary",
            "action_plan": "Action Plan",
            "research_report": "Research Report",
            "creative_brief": "Creative Brief"
        }
        
        base_title = title_templates.get(intent, "Analysis")
        
        # Add context-specific suffix if available
        if hierarchy.primary_contexts:
            primary_context = hierarchy.primary_contexts[0]
            # Extract key theme from primary context (simplified)
            context_words = primary_context.content.split()[:3]
            if context_words:
                theme = " ".join(context_words).title()
                return f"{base_title}: {theme}"
        
        return base_title
    
    @classmethod
    def _adapt_structure_to_blocks(
        cls,
        architecture: Dict[str, Any],
        discovered_blocks: List[DiscoveredBlock],
        target_audience: Optional[str] = None
    ) -> Dict[str, Any]:
        """Adapt document structure based on available blocks and audience."""
        
        sections = architecture["sections"].copy()
        total_blocks = len(discovered_blocks)
        
        # Audience adaptations
        audience_adaptations = []
        if target_audience == "executives":
            # Executives prefer concise, high-level sections
            sections = [s for s in sections if s.get("weight", 0) >= 0.15]  # Remove minor sections
            audience_adaptations.append("Removed detailed sections for executive focus")
        elif target_audience == "engineers":
            # Engineers want detailed implementation sections
            for section in sections:
                if section["name"] in ["implementation", "examples", "troubleshooting"]:
                    section["weight"] = section["weight"] * 1.2  # Increase technical section weight
            audience_adaptations.append("Enhanced technical sections for engineering audience")
        
        # Block count adaptations
        if total_blocks < architecture["min_blocks"]:
            # Remove optional sections if we don't have enough blocks
            sections = [s for s in sections if s["required"]]
            audience_adaptations.append(f"Simplified structure due to limited blocks ({total_blocks})")
        
        # Estimate document length
        estimated_length = cls._estimate_document_length(sections, total_blocks)
        
        return {
            "sections": sections,
            "estimated_length": estimated_length,
            "audience_adaptations": audience_adaptations,
            "optimization_notes": [
                f"Adapted for {total_blocks} available blocks",
                f"Optimized for {target_audience or 'general'} audience"
            ]
        }
    
    @classmethod
    def _calculate_structure_confidence(
        cls,
        architecture: Dict[str, Any],
        discovered_blocks: List[DiscoveredBlock],
        adapted_structure: Dict[str, Any]
    ) -> float:
        """Calculate confidence in the suggested structure."""
        
        factors = []
        
        # Block count adequacy
        total_blocks = len(discovered_blocks)
        min_blocks = architecture["min_blocks"]
        block_adequacy = min(total_blocks / min_blocks, 1.0)
        factors.append(block_adequacy)
        
        # Semantic type alignment
        preferred_types = set(architecture["preferred_blocks"])
        available_types = set(block.semantic_type for block in discovered_blocks)
        type_alignment = len(preferred_types.intersection(available_types)) / len(preferred_types)
        factors.append(type_alignment)
        
        # Block quality (average relevance)
        if discovered_blocks:
            avg_relevance = sum(block.relevance_score for block in discovered_blocks) / len(discovered_blocks)
            factors.append(avg_relevance)
        
        # Structure completeness (required sections can be filled)
        required_sections = [s for s in adapted_structure["sections"] if s["required"]]
        completeness = 1.0 if total_blocks >= len(required_sections) else total_blocks / len(required_sections)
        factors.append(completeness)
        
        return sum(factors) / len(factors) if factors else 0.0
    
    @classmethod
    def _find_optimal_section(
        cls,
        block: DiscoveredBlock,
        sections: List[Dict[str, Any]]
    ) -> str:
        """Find the optimal section for a given block."""
        
        semantic_type = block.semantic_type
        
        # Semantic type to section mapping
        type_mappings = {
            "goal": ["objectives", "overview", "executive_summary"],
            "insight": ["analysis", "findings", "key_findings", "current_situation"],
            "constraint": ["prerequisites", "resources", "limitations"],
            "reference": ["background", "methodology", "examples"],
            "theme": ["concept", "overview", "background"]
        }
        
        # Find sections that match the block's semantic type
        preferred_sections = type_mappings.get(semantic_type, [])
        available_section_names = [s["name"] for s in sections]
        
        # Match preferred sections with available sections
        for preferred in preferred_sections:
            if preferred in available_section_names:
                return preferred
        
        # Fallback to first main section
        main_sections = [s["name"] for s in sections if s.get("weight", 0) > 0.2]
        return main_sections[0] if main_sections else sections[0]["name"]
    
    @classmethod
    def _balance_section_content(
        cls,
        sections: Dict[str, List[DiscoveredBlock]],
        document_structure: Dict[str, Any]
    ) -> Dict[str, List[DiscoveredBlock]]:
        """Balance content across sections to ensure adequate coverage."""
        
        # Find sections with no content
        empty_sections = [name for name, blocks in sections.items() if not blocks]
        
        # Find sections with excess content
        excess_sections = [
            (name, blocks) for name, blocks in sections.items() 
            if len(blocks) > 5  # Arbitrary threshold
        ]
        
        # Redistribute blocks from excess to empty sections
        for empty_section in empty_sections:
            for excess_section_name, excess_blocks in excess_sections:
                if len(excess_blocks) > 3:  # Keep at least 3 blocks in original section
                    # Move lowest relevance block to empty section
                    moved_block = excess_blocks.pop()  # Remove last (lowest relevance) block
                    sections[empty_section].append(moved_block)
                    break
        
        return sections
    
    @classmethod
    def _estimate_document_length(cls, sections: List[Dict[str, Any]], total_blocks: int) -> str:
        """Estimate document length based on sections and blocks."""
        
        section_count = len(sections)
        
        if section_count <= 2 and total_blocks <= 5:
            return "short"  # 1-2 pages
        elif section_count <= 4 and total_blocks <= 12:
            return "medium"  # 3-5 pages
        else:
            return "long"  # 6+ pages