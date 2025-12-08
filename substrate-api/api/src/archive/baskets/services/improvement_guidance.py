"""Non-enforcing improvement guidance service for basket enhancement."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4

from src.schemas.basket_intelligence_schema import (
    BasketImprovementGuidance, BasketThematicAnalysis, BasketCoherenceSuggestions,
    CrossDocumentRelationships, BasketContextHealth
)
from .pattern_recognition import BasketPatternRecognitionService
from .coherence_suggestions import CoherenceSuggestionsService
from .relationship_discovery import RelationshipDiscoveryService
from .inconsistency_accommodation import InconsistencyAccommodationService
from ...utils.supabase_client import supabase_client as supabase

logger = logging.getLogger("uvicorn.error")


class ImprovementGuidanceService:
    """Service for providing gentle, non-enforcing guidance for basket improvement."""
# V3.0 DEPRECATION NOTICE:
# This file contains references to context_items table which was merged into blocks table.
# Entity blocks are now identified by semantic_type='entity'.
# This file is legacy/supporting code - update if actively maintained.

    
    # Improvement opportunity templates
    IMPROVEMENT_TEMPLATES = {
        "context_enrichment": {
            "opportunity": "Your basket could benefit from additional context items",
            "description": "Adding more context might help capture project nuances",
            "gentle_approach": "Only if you feel something is missing",
            "value_proposition": "Could help preserve important project details",
            "confidence": 0.6
        },
        "thematic_clarification": {
            "opportunity": "Some themes could be made more explicit",
            "description": "Clarifying themes might help others understand your project direction",
            "gentle_approach": "This is just an idea - your current approach works too",
            "value_proposition": "Might make it easier to communicate your project vision",
            "confidence": 0.7
        },
        "document_connection": {
            "opportunity": "Your documents could be more connected",
            "description": "Linking related documents might show project relationships",
            "gentle_approach": "Only if seeing connections would be helpful",
            "value_proposition": "Could help reveal the bigger picture of your work",
            "confidence": 0.5
        },
        "scope_organization": {
            "opportunity": "Context scopes could be organized differently",
            "description": "Organizing by scope might make navigation easier",
            "gentle_approach": "Your current organization might already work perfectly",
            "value_proposition": "Could help distinguish local vs global contexts",
            "confidence": 0.4
        },
        "semantic_grouping": {
            "opportunity": "Similar content could be grouped together",
            "description": "Grouping similar items might make patterns more visible",
            "gentle_approach": "This is optional - your current structure might be ideal",
            "value_proposition": "Might help identify recurring themes",
            "confidence": 0.5
        },
        "evolution_planning": {
            "opportunity": "Your project could benefit from evolution planning",
            "description": "Planning next steps might help maintain momentum",
            "gentle_approach": "Only if forward planning would be useful",
            "value_proposition": "Could help guide natural project development",
            "confidence": 0.6
        },
        "diversity_balancing": {
            "opportunity": "Content diversity could be balanced differently",
            "description": "Adjusting content balance might improve focus",
            "gentle_approach": "Your current diversity might be exactly what you need",
            "value_proposition": "Could help balance exploration with focus",
            "confidence": 0.3
        },
        "consistency_enhancement": {
            "opportunity": "Some consistency improvements are possible",
            "description": "Light consistency improvements might help clarity",
            "gentle_approach": "Inconsistency often reflects creative thinking",
            "value_proposition": "Might make project easier to navigate",
            "confidence": 0.4
        }
    }
    
    @classmethod
    async def generate_improvement_guidance(
        cls,
        basket_id: UUID,
        workspace_id: str,
        guidance_style: str = "gentle",
        user_requested: bool = False
    ) -> BasketImprovementGuidance:
        """Generate non-enforcing improvement guidance."""
        
        # Get comprehensive basket analysis
        analysis_components = await cls._get_comprehensive_analysis(basket_id, workspace_id)
        
        # Identify improvement opportunities (gently)
        improvement_opportunities = cls._identify_improvement_opportunities(
            analysis_components, guidance_style, user_requested
        )
        
        # Generate gentle recommendations
        gentle_recommendations = cls._generate_gentle_recommendations(
            improvement_opportunities, analysis_components
        )
        
        # Assess guidance confidence (keeping it modest)
        guidance_confidence = cls._assess_guidance_confidence(
            improvement_opportunities, analysis_components
        )
        
        # Generate value propositions
        value_if_interested = cls._generate_value_propositions(
            improvement_opportunities, gentle_recommendations
        )
        
        # Determine guidance type
        guidance_type = cls._determine_guidance_type(
            improvement_opportunities, user_requested
        )
        
        return BasketImprovementGuidance(
            basket_id=basket_id,
            guidance_type=guidance_type,
            improvement_opportunities=improvement_opportunities,
            gentle_recommendations=gentle_recommendations,
            user_autonomy_note="You know your project best - these are just ideas to consider",
            no_pressure_message="Your basket is working fine as-is",
            value_if_interested=value_if_interested,
            guidance_confidence=guidance_confidence
        )
    
    @classmethod
    async def suggest_next_steps(
        cls,
        basket_id: UUID,
        workspace_id: str,
        user_goals: Optional[List[str]] = None
    ) -> List[str]:
        """Suggest gentle next steps for basket development."""
        
        guidance = await cls.generate_improvement_guidance(
            basket_id, workspace_id, user_requested=True
        )
        
        next_steps = []
        
        # Convert recommendations to actionable steps
        for recommendation in guidance.gentle_recommendations[:3]:
            if "context" in recommendation.lower():
                next_steps.append("Consider adding context items if any project details feel missing")
            elif "document" in recommendation.lower():
                next_steps.append("If helpful, explore connections between your documents")
            elif "theme" in recommendation.lower():
                next_steps.append("Clarify themes if it would help communicate your project")
            else:
                next_steps.append(f"Consider: {recommendation.lower()}")
        
        # Add user goal alignment if provided
        if user_goals:
            next_steps.append("Review if current basket aligns with your stated goals")
        
        # Always include the autonomy message
        if not next_steps:
            next_steps.append("Your basket is well-developed - continue with your current approach")
        
        return next_steps
    
    @classmethod
    async def assess_improvement_readiness(
        cls,
        basket_id: UUID,
        workspace_id: str
    ) -> Dict[str, Any]:
        """Assess if basket is ready for improvement suggestions."""
        
        basket_contents = await cls._get_basket_contents(basket_id, workspace_id)
        
        readiness_factors = {
            "content_maturity": cls._assess_content_maturity(basket_contents),
            "exploration_depth": cls._assess_exploration_depth(basket_contents),
            "user_engagement": cls._assess_user_engagement(basket_contents),
            "natural_development": cls._assess_natural_development(basket_contents)
        }
        
        # Calculate overall readiness (biased toward "ready")
        overall_readiness = sum(readiness_factors.values()) / len(readiness_factors)
        
        return {
            "overall_readiness": overall_readiness,
            "readiness_factors": readiness_factors,
            "improvement_timing": cls._determine_improvement_timing(overall_readiness),
            "readiness_note": "Improvement suggestions are always optional and based on observed patterns"
        }
    
    @classmethod
    async def _get_comprehensive_analysis(
        cls,
        basket_id: UUID,
        workspace_id: str
    ) -> Dict[str, Any]:
        """Get comprehensive analysis for improvement guidance."""
        
        # Get thematic analysis
        from src.schemas.basket_intelligence_schema import PatternAnalysisRequest
        analysis_request = PatternAnalysisRequest(
            basket_id=basket_id,
            accommodate_inconsistency=True
        )
        thematic_analysis = await BasketPatternRecognitionService.analyze_basket_patterns(
            analysis_request, workspace_id
        )
        
        # Get coherence suggestions
        coherence_suggestions = await CoherenceSuggestionsService.generate_gentle_suggestions(
            basket_id, workspace_id, thematic_analysis
        )
        
        # Get document relationships
        document_relationships = await RelationshipDiscoveryService.discover_document_relationships(
            basket_id, workspace_id, thematic_analysis
        )
        
        # Get context health
        context_health = await InconsistencyAccommodationService.assess_context_health(
            basket_id, workspace_id, thematic_analysis
        )
        
        return {
            "thematic_analysis": thematic_analysis,
            "coherence_suggestions": coherence_suggestions,
            "document_relationships": document_relationships,
            "context_health": context_health
        }
    
    @classmethod
    def _identify_improvement_opportunities(
        cls,
        analysis_components: Dict[str, Any],
        guidance_style: str,
        user_requested: bool
    ) -> List[str]:
        """Identify improvement opportunities gently."""
        
        opportunities = []
        
        thematic_analysis = analysis_components["thematic_analysis"]
        coherence_suggestions = analysis_components["coherence_suggestions"]
        document_relationships = analysis_components["document_relationships"]
        context_health = analysis_components["context_health"]
        
        # Context enrichment opportunities
        if len(thematic_analysis.discovered_patterns) < 2:
            template = cls.IMPROVEMENT_TEMPLATES["context_enrichment"]
            opportunities.append(template["opportunity"])
        
        # Thematic clarification opportunities
        weak_patterns = [p for p in thematic_analysis.discovered_patterns if p.pattern_strength == "weak"]
        if len(weak_patterns) > 2:
            template = cls.IMPROVEMENT_TEMPLATES["thematic_clarification"]
            opportunities.append(template["opportunity"])
        
        # Document connection opportunities
        if document_relationships.overall_connectivity < 0.3 and len(document_relationships.document_pairs) > 0:
            template = cls.IMPROVEMENT_TEMPLATES["document_connection"]
            opportunities.append(template["opportunity"])
        
        # Scope organization opportunities
        if len(coherence_suggestions.suggestions) > 0:
            scope_suggestions = [s for s in coherence_suggestions.suggestions if "scope" in s.suggestion_type]
            if scope_suggestions:
                template = cls.IMPROVEMENT_TEMPLATES["scope_organization"]
                opportunities.append(template["opportunity"])
        
        # Semantic grouping opportunities
        if thematic_analysis.content_diversity > 0.8:
            template = cls.IMPROVEMENT_TEMPLATES["semantic_grouping"]
            opportunities.append(template["opportunity"])
        
        # Evolution planning opportunities
        if context_health.overall_health_score > 0.7 and len(thematic_analysis.discovered_patterns) > 1:
            template = cls.IMPROVEMENT_TEMPLATES["evolution_planning"]
            opportunities.append(template["opportunity"])
        
        # Limit opportunities to avoid overwhelming
        max_opportunities = 3 if user_requested else 2
        return opportunities[:max_opportunities]
    
    @classmethod
    def _generate_gentle_recommendations(
        cls,
        opportunities: List[str],
        analysis_components: Dict[str, Any]
    ) -> List[str]:
        """Generate gentle, non-enforcing recommendations."""
        
        recommendations = []
        
        for opportunity in opportunities:
            # Find matching template
            for template_name, template in cls.IMPROVEMENT_TEMPLATES.items():
                if template["opportunity"] == opportunity:
                    recommendation = f"{template['description']} - {template['gentle_approach']}"
                    recommendations.append(recommendation)
                    break
        
        # Add general gentle recommendations
        if opportunities:
            recommendations.append("These are all optional suggestions - your current approach may be perfect")
            recommendations.append("Consider only changes that feel natural and helpful to your workflow")
        
        return recommendations
    
    @classmethod
    def _assess_guidance_confidence(
        cls,
        opportunities: List[str],
        analysis_components: Dict[str, Any]
    ) -> float:
        """Assess confidence in guidance (keeping it modest)."""
        
        if not opportunities:
            return 0.3  # Low confidence when no opportunities
        
        # Base confidence is modest
        base_confidence = 0.5
        
        # Slight boost for multiple analysis components agreeing
        thematic_patterns = len(analysis_components["thematic_analysis"].discovered_patterns)
        suggestions_count = len(analysis_components["coherence_suggestions"].suggestions)
        
        if thematic_patterns > 2 and suggestions_count > 2:
            base_confidence += 0.1
        
        # Slight boost for high-quality analysis
        if analysis_components["thematic_analysis"].coherence_level in ["high", "medium"]:
            base_confidence += 0.1
        
        return min(base_confidence, 0.8)  # Cap at 80% to maintain humility
    
    @classmethod
    def _generate_value_propositions(
        cls,
        opportunities: List[str],
        recommendations: List[str]
    ) -> List[str]:
        """Generate value propositions for interested users."""
        
        value_props = []
        
        for opportunity in opportunities:
            # Find matching template
            for template_name, template in cls.IMPROVEMENT_TEMPLATES.items():
                if template["opportunity"] == opportunity:
                    value_props.append(template["value_proposition"])
                    break
        
        # Add general value propositions
        if opportunities:
            value_props.extend([
                "May help reveal hidden patterns in your work",
                "Could make your project easier to navigate and understand",
                "Might facilitate better communication with collaborators"
            ])
        
        return value_props[:5]  # Limit value propositions
    
    @classmethod
    def _determine_guidance_type(
        cls,
        opportunities: List[str],
        user_requested: bool
    ) -> str:
        """Determine the type of guidance being provided."""
        
        if user_requested:
            return "opportunity"
        elif len(opportunities) > 2:
            return "idea"
        else:
            return "optional"
    
    @classmethod
    async def _get_basket_contents(
        cls,
        basket_id: UUID,
        workspace_id: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get basket contents for improvement assessment."""
        
        contents = {
            "documents": [],
            "blocks": [],
            "context_items": [],
            "raw_dumps": []
        }
        
        try:
            # Get documents
            docs_resp = (
                supabase.table("documents")
                .select("id,title,content_raw,document_type,created_at")
                .eq("basket_id", str(basket_id))
                .eq("workspace_id", workspace_id)
                .execute()
            )
            contents["documents"] = docs_resp.data or []
            
            # Get blocks
            blocks_resp = (
                supabase.table("blocks")
                .select("id,semantic_type,content,state,created_at")
                .eq("basket_id", str(basket_id))
                .eq("workspace_id", workspace_id)
                .neq("state", "REJECTED")
                .execute()
            )
            contents["blocks"] = blocks_resp.data or []
            
            # Get context items
            contexts_resp = (
                supabase.table("context_items")
                .select("id,type,content,scope,created_at")
                .eq("basket_id", str(basket_id))
                .eq("status", "active")
                .execute()
            )
            contents["context_items"] = contexts_resp.data or []
            
            # Get raw dumps
            dumps_resp = (
                supabase.table("raw_dumps")
                .select("id,content,source,created_at")
                .eq("basket_id", str(basket_id))
                .eq("workspace_id", workspace_id)
                .execute()
            )
            contents["raw_dumps"] = dumps_resp.data or []
            
        except Exception as e:
            logger.exception(f"Failed to get basket contents for improvement assessment: {e}")
        
        return contents
    
    @classmethod
    def _assess_content_maturity(cls, basket_contents: Dict[str, List[Dict[str, Any]]]) -> float:
        """Assess how mature the basket content is."""
        
        total_items = sum(len(items) for items in basket_contents.values())
        
        # Content maturity based on volume and diversity
        if total_items >= 15:
            return 0.9
        elif total_items >= 8:
            return 0.7
        elif total_items >= 3:
            return 0.5
        else:
            return 0.3
    
    @classmethod
    def _assess_exploration_depth(cls, basket_contents: Dict[str, List[Dict[str, Any]]]) -> float:
        """Assess depth of exploration in the basket."""
        
        # Check content type diversity
        content_types = set()
        
        for doc in basket_contents["documents"]:
            content_types.add(doc.get("document_type", "unknown"))
        
        for block in basket_contents["blocks"]:
            content_types.add(block.get("semantic_type", "unknown"))
        
        for context in basket_contents["context_items"]:
            content_types.add(context.get("type", "unknown"))
        
        # Depth based on diversity
        diversity_score = min(len(content_types) / 8, 1.0)
        return diversity_score
    
    @classmethod
    def _assess_user_engagement(cls, basket_contents: Dict[str, List[Dict[str, Any]]]) -> float:
        """Assess level of user engagement with the basket."""
        
        # Simple engagement assessment based on activity
        context_items = len(basket_contents["context_items"])
        
        if context_items >= 10:
            return 0.9
        elif context_items >= 5:
            return 0.7
        elif context_items >= 2:
            return 0.5
        else:
            return 0.3
    
    @classmethod
    def _assess_natural_development(cls, basket_contents: Dict[str, List[Dict[str, Any]]]) -> float:
        """Assess if basket shows natural development patterns."""
        
        # Check temporal distribution
        all_items = []
        for items in basket_contents.values():
            all_items.extend(items)
        
        if not all_items:
            return 0.5
        
        # Simple check for spread over time
        timestamps = [item.get("created_at") for item in all_items if item.get("created_at")]
        
        if len(set(ts[:10] for ts in timestamps if ts)) > 1:  # Multiple days
            return 0.8
        else:
            return 0.6
    
    @classmethod
    def _determine_improvement_timing(cls, readiness_score: float) -> str:
        """Determine when improvement suggestions are appropriate."""
        
        if readiness_score > 0.7:
            return "ready_for_enhancement"
        elif readiness_score > 0.5:
            return "developing_naturally"
        else:
            return "early_exploration"