"""Inconsistency accommodation service for human-compatible basket intelligence."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from uuid import UUID, uuid4

from src.schemas.basket_intelligence_schema import (
    BasketContextHealth, ContextInconsistency, BasketThematicAnalysis,
    BasketFlexibilityMetrics
)
from .pattern_recognition import BasketPatternRecognitionService
from ...utils.supabase_client import supabase_client as supabase

logger = logging.getLogger("uvicorn.error")


class InconsistencyAccommodationService:
    """Service for accommodating human context inconsistency as a feature, not a bug."""
# V3.0 DEPRECATION NOTICE:
# This file contains references to context_items table which was merged into blocks table.
# Entity blocks are now identified by semantic_type='entity'.
# This file is legacy/supporting code - update if actively maintained.

    
    # Inconsistency accommodation strategies
    ACCOMMODATION_STRATEGIES = {
        "intent_mismatch": {
            "description": "Different intentions across context items",
            "accommodation": "Multiple intentions can coexist in creative projects",
            "value": "Indicates project evolution or multi-faceted goals",
            "handling": "preserve_all_intentions",
            "human_benefit": "Allows natural goal refinement and exploration"
        },
        "audience_conflict": {
            "description": "Context items target different audiences",
            "accommodation": "Multi-audience projects are common and valuable",
            "value": "Shows comprehensive stakeholder consideration",
            "handling": "segment_by_audience",
            "human_benefit": "Enables flexible communication strategies"
        },
        "style_variation": {
            "description": "Inconsistent style or tone across content",
            "accommodation": "Style variation often reflects different contexts or moods",
            "value": "Indicates authentic, human-driven content creation",
            "handling": "preserve_style_diversity",
            "human_benefit": "Allows natural expression and context-appropriate communication"
        },
        "scope_difference": {
            "description": "Context items operate at different scopes",
            "accommodation": "Multi-scope thinking is natural for complex projects",
            "value": "Shows ability to think from micro to macro levels",
            "handling": "organize_by_scope_layers",
            "human_benefit": "Supports comprehensive project understanding"
        },
        "temporal_mismatch": {
            "description": "Context items from different time periods",
            "accommodation": "Projects naturally evolve over time",
            "value": "Shows project growth and learning progression",
            "handling": "preserve_temporal_evolution",
            "human_benefit": "Captures learning journey and evolution"
        },
        "priority_confusion": {
            "description": "Conflicting priorities or importance levels",
            "accommodation": "Priority shifts are normal in dynamic projects",
            "value": "Indicates responsive project management",
            "handling": "allow_priority_fluidity",
            "human_benefit": "Enables adaptive prioritization based on changing circumstances"
        },
        "semantic_overlap": {
            "description": "Similar concepts expressed in different ways",
            "accommodation": "Multiple expressions of similar ideas enrich understanding",
            "value": "Shows deep thinking and exploration of concepts",
            "handling": "preserve_semantic_richness",
            "human_benefit": "Allows nuanced concept exploration and expression"
        },
        "methodological_diversity": {
            "description": "Different approaches or methods in same context",
            "accommodation": "Multiple methodologies can strengthen outcomes",
            "value": "Shows comprehensive problem-solving approach",
            "handling": "preserve_methodological_options",
            "human_benefit": "Provides flexibility in execution and adaptation"
        }
    }
    
    @classmethod
    async def assess_context_health(
        cls,
        basket_id: UUID,
        workspace_id: str,
        thematic_analysis: Optional[BasketThematicAnalysis] = None
    ) -> BasketContextHealth:
        """Assess basket context health with accommodation approach."""
        
        # Get basket contents
        basket_contents = await cls._get_basket_contents(basket_id, workspace_id)
        
        # Get thematic analysis if not provided
        if not thematic_analysis:
            from src.schemas.basket_intelligence_schema import PatternAnalysisRequest
            analysis_request = PatternAnalysisRequest(
                basket_id=basket_id,
                accommodate_inconsistency=True
            )
            thematic_analysis = await BasketPatternRecognitionService.analyze_basket_patterns(
                analysis_request, workspace_id
            )
        
        # Detect inconsistencies with accommodation approach
        inconsistencies = cls._detect_inconsistencies_accommodatingly(
            basket_contents, thematic_analysis
        )
        
        # Generate accommodation strategies
        accommodation_strategies = cls._generate_accommodation_strategies(inconsistencies)
        
        # Identify flexibility benefits
        flexibility_benefits = cls._identify_flexibility_benefits(
            inconsistencies, basket_contents
        )
        
        # Calculate health factors
        health_factors = cls._calculate_health_factors(
            basket_contents, inconsistencies, thematic_analysis
        )
        
        # Calculate overall health score (accommodation-focused)
        overall_health_score = cls._calculate_accommodation_health_score(
            health_factors, inconsistencies
        )
        
        # Calculate human compatibility score
        human_compatibility_score = cls._calculate_human_compatibility(
            inconsistencies, flexibility_benefits
        )
        
        # Generate health insights
        health_insights = cls._generate_health_insights(
            inconsistencies, flexibility_benefits, health_factors
        )
        
        return BasketContextHealth(
            basket_id=basket_id,
            overall_health_score=overall_health_score,
            health_factors=health_factors,
            inconsistencies=inconsistencies,
            accommodation_strategies=accommodation_strategies,
            flexibility_benefits=flexibility_benefits,
            health_insights=health_insights,
            human_compatibility_score=human_compatibility_score,
            health_note="Context health reflects usefulness, not conformity to rigid structure"
        )
    
    @classmethod
    async def generate_flexibility_metrics(
        cls,
        basket_id: UUID,
        workspace_id: str
    ) -> BasketFlexibilityMetrics:
        """Generate metrics about basket flexibility and accommodation."""
        
        basket_contents = await cls._get_basket_contents(basket_id, workspace_id)
        context_health = await cls.assess_context_health(basket_id, workspace_id)
        
        # Calculate flexibility score
        flexibility_score = cls._calculate_flexibility_score(basket_contents, context_health)
        
        # Generate accommodation examples
        accommodation_examples = cls._generate_accommodation_examples(
            context_health.inconsistencies
        )
        
        # Calculate inconsistency tolerance
        inconsistency_tolerance = cls._calculate_inconsistency_tolerance(
            context_health.inconsistencies, basket_contents
        )
        
        # Calculate human compatibility
        human_compatibility = context_health.human_compatibility_score
        
        # Generate flexibility benefits
        flexibility_benefits = cls._generate_flexibility_benefits(
            context_health.inconsistencies, basket_contents
        )
        
        # Generate rigidity warnings
        rigidity_warnings = cls._generate_rigidity_warnings()
        
        return BasketFlexibilityMetrics(
            basket_id=basket_id,
            flexibility_score=flexibility_score,
            accommodation_examples=accommodation_examples,
            inconsistency_tolerance=inconsistency_tolerance,
            human_compatibility=human_compatibility,
            messiness_handling="Graceful accommodation of human context patterns",
            flexibility_benefits=flexibility_benefits,
            rigidity_warnings=rigidity_warnings
        )
    
    @classmethod
    async def accommodate_new_inconsistency(
        cls,
        basket_id: UUID,
        workspace_id: str,
        inconsistency_description: str,
        affected_items: List[UUID]
    ) -> ContextInconsistency:
        """Accommodate a newly detected inconsistency."""
        
        # Classify the inconsistency type
        inconsistency_type = cls._classify_inconsistency(inconsistency_description)
        
        # Determine severity (keeping it low to avoid alarm)
        severity = cls._assess_inconsistency_severity(
            inconsistency_description, len(affected_items)
        )
        
        # Generate accommodation strategy
        strategy_info = cls.ACCOMMODATION_STRATEGIES.get(
            inconsistency_type,
            cls.ACCOMMODATION_STRATEGIES["semantic_overlap"]  # Default fallback
        )
        
        return ContextInconsistency(
            inconsistency_id=f"{inconsistency_type}_{uuid4().hex[:8]}",
            inconsistency_type=inconsistency_type,
            severity=severity,
            description=inconsistency_description,
            involved_objects=affected_items,
            accommodation_strategy=strategy_info["accommodation"],
            potential_value=strategy_info["value"],
            user_benefit=strategy_info["human_benefit"]
        )
    
    @classmethod
    async def _get_basket_contents(
        cls,
        basket_id: UUID,
        workspace_id: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get basket contents for inconsistency analysis."""
        
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
                .select("id,type,content,scope,block_id,document_id,created_at")
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
            logger.exception(f"Failed to get basket contents for inconsistency analysis: {e}")
        
        return contents
    
    @classmethod
    def _detect_inconsistencies_accommodatingly(
        cls,
        basket_contents: Dict[str, List[Dict[str, Any]]],
        thematic_analysis: BasketThematicAnalysis
    ) -> List[ContextInconsistency]:
        """Detect inconsistencies with accommodation mindset."""
        
        inconsistencies = []
        
        # Intent mismatch detection
        intent_inconsistencies = cls._detect_intent_mismatches(basket_contents)
        inconsistencies.extend(intent_inconsistencies)
        
        # Audience conflict detection
        audience_inconsistencies = cls._detect_audience_conflicts(basket_contents)
        inconsistencies.extend(audience_inconsistencies)
        
        # Style variation detection
        style_inconsistencies = cls._detect_style_variations(basket_contents)
        inconsistencies.extend(style_inconsistencies)
        
        # Scope difference detection
        scope_inconsistencies = cls._detect_scope_differences(basket_contents)
        inconsistencies.extend(scope_inconsistencies)
        
        # Temporal mismatch detection
        temporal_inconsistencies = cls._detect_temporal_mismatches(basket_contents)
        inconsistencies.extend(temporal_inconsistencies)
        
        # Semantic overlap detection
        semantic_inconsistencies = cls._detect_semantic_overlaps(basket_contents)
        inconsistencies.extend(semantic_inconsistencies)
        
        return inconsistencies
    
    @classmethod
    def _detect_intent_mismatches(
        cls,
        basket_contents: Dict[str, List[Dict[str, Any]]]
    ) -> List[ContextInconsistency]:
        """Detect intent mismatches with accommodation."""
        
        inconsistencies = []
        context_items = basket_contents["context_items"]
        
        # Group contexts by type
        goal_contexts = [ctx for ctx in context_items if ctx.get("type") == "goal"]
        
        if len(goal_contexts) > 1:
            # Multiple goals might seem inconsistent but often reflect project complexity
            strategy_info = cls.ACCOMMODATION_STRATEGIES["intent_mismatch"]
            
            inconsistencies.append(ContextInconsistency(
                inconsistency_id=f"intent_mismatch_{uuid4().hex[:8]}",
                inconsistency_type="intent_mismatch",
                severity="minor",  # Keep it gentle
                description=f"Multiple goals detected ({len(goal_contexts)}) - shows comprehensive project thinking",
                involved_objects=[UUID(ctx["id"]) for ctx in goal_contexts],
                accommodation_strategy=strategy_info["accommodation"],
                potential_value=strategy_info["value"],
                user_benefit=strategy_info["human_benefit"]
            ))
        
        return inconsistencies
    
    @classmethod
    def _detect_audience_conflicts(
        cls,
        basket_contents: Dict[str, List[Dict[str, Any]]]
    ) -> List[ContextInconsistency]:
        """Detect audience conflicts with accommodation."""
        
        inconsistencies = []
        context_items = basket_contents["context_items"]
        
        # Look for audience contexts
        audience_contexts = [ctx for ctx in context_items if ctx.get("type") == "audience"]
        
        if len(audience_contexts) > 2:
            # Multiple audiences often indicate thoughtful stakeholder consideration
            strategy_info = cls.ACCOMMODATION_STRATEGIES["audience_conflict"]
            
            inconsistencies.append(ContextInconsistency(
                inconsistency_id=f"audience_conflict_{uuid4().hex[:8]}",
                inconsistency_type="audience_conflict",
                severity="minor",
                description=f"Multiple audience contexts ({len(audience_contexts)}) - demonstrates stakeholder awareness",
                involved_objects=[UUID(ctx["id"]) for ctx in audience_contexts],
                accommodation_strategy=strategy_info["accommodation"],
                potential_value=strategy_info["value"],
                user_benefit=strategy_info["human_benefit"]
            ))
        
        return inconsistencies
    
    @classmethod
    def _detect_style_variations(
        cls,
        basket_contents: Dict[str, List[Dict[str, Any]]]
    ) -> List[ContextInconsistency]:
        """Detect style variations with accommodation."""
        
        inconsistencies = []
        documents = basket_contents["documents"]
        
        if len(documents) >= 2:
            # Check for document type diversity
            doc_types = set(doc.get("document_type", "unknown") for doc in documents)
            
            if len(doc_types) > 2:
                strategy_info = cls.ACCOMMODATION_STRATEGIES["style_variation"]
                
                inconsistencies.append(ContextInconsistency(
                    inconsistency_id=f"style_variation_{uuid4().hex[:8]}",
                    inconsistency_type="style_variation",
                    severity="minor",
                    description=f"Document type diversity ({len(doc_types)} types) - reflects comprehensive approach",
                    involved_objects=[UUID(doc["id"]) for doc in documents],
                    accommodation_strategy=strategy_info["accommodation"],
                    potential_value=strategy_info["value"],
                    user_benefit=strategy_info["human_benefit"]
                ))
        
        return inconsistencies
    
    @classmethod
    def _detect_scope_differences(
        cls,
        basket_contents: Dict[str, List[Dict[str, Any]]]
    ) -> List[ContextInconsistency]:
        """Detect scope differences with accommodation."""
        
        inconsistencies = []
        context_items = basket_contents["context_items"]
        
        # Check scope diversity
        scopes = set(ctx.get("scope", "LOCAL") for ctx in context_items)
        
        if len(scopes) > 2:
            strategy_info = cls.ACCOMMODATION_STRATEGIES["scope_difference"]
            
            inconsistencies.append(ContextInconsistency(
                inconsistency_id=f"scope_difference_{uuid4().hex[:8]}",
                inconsistency_type="scope_difference",
                severity="minor",
                description=f"Multi-scope contexts ({len(scopes)} scopes) - shows comprehensive perspective",
                involved_objects=[UUID(ctx["id"]) for ctx in context_items],
                accommodation_strategy=strategy_info["accommodation"],
                potential_value=strategy_info["value"],
                user_benefit=strategy_info["human_benefit"]
            ))
        
        return inconsistencies
    
    @classmethod
    def _detect_temporal_mismatches(
        cls,
        basket_contents: Dict[str, List[Dict[str, Any]]]
    ) -> List[ContextInconsistency]:
        """Detect temporal mismatches with accommodation."""
        
        inconsistencies = []
        
        # Check creation time spread across all items
        all_items = []
        for item_type, items in basket_contents.items():
            for item in items:
                if item.get("created_at"):
                    all_items.append(item)
        
        if len(all_items) > 3:
            # Simple temporal spread check
            timestamps = [item["created_at"] for item in all_items if item.get("created_at")]
            
            if len(set(timestamp[:10] for timestamp in timestamps)) > 7:  # More than a week spread
                strategy_info = cls.ACCOMMODATION_STRATEGIES["temporal_mismatch"]
                
                inconsistencies.append(ContextInconsistency(
                    inconsistency_id=f"temporal_mismatch_{uuid4().hex[:8]}",
                    inconsistency_type="temporal_mismatch",
                    severity="minor",
                    description="Content created over extended time period - shows project evolution",
                    involved_objects=[UUID(item["id"]) for item in all_items[:5]],  # Sample
                    accommodation_strategy=strategy_info["accommodation"],
                    potential_value=strategy_info["value"],
                    user_benefit=strategy_info["human_benefit"]
                ))
        
        return inconsistencies
    
    @classmethod
    def _detect_semantic_overlaps(
        cls,
        basket_contents: Dict[str, List[Dict[str, Any]]]
    ) -> List[ContextInconsistency]:
        """Detect semantic overlaps with accommodation."""
        
        inconsistencies = []
        blocks = basket_contents["blocks"]
        
        # Check for semantic type diversity
        semantic_types = [block.get("semantic_type", "unknown") for block in blocks]
        semantic_counts = {}
        for sem_type in semantic_types:
            semantic_counts[sem_type] = semantic_counts.get(sem_type, 0) + 1
        
        # Look for high diversity as potentially valuable inconsistency
        if len(semantic_counts) > 5 and len(blocks) > 8:
            strategy_info = cls.ACCOMMODATION_STRATEGIES["semantic_overlap"]
            
            inconsistencies.append(ContextInconsistency(
                inconsistency_id=f"semantic_overlap_{uuid4().hex[:8]}",
                inconsistency_type="semantic_overlap",
                severity="minor",
                description=f"Rich semantic diversity ({len(semantic_counts)} types) - comprehensive exploration",
                involved_objects=[UUID(block["id"]) for block in blocks[:5]],  # Sample
                accommodation_strategy=strategy_info["accommodation"],
                potential_value=strategy_info["value"],
                user_benefit=strategy_info["human_benefit"]
            ))
        
        return inconsistencies
    
    @classmethod
    def _generate_accommodation_strategies(
        cls,
        inconsistencies: List[ContextInconsistency]
    ) -> List[str]:
        """Generate strategies for accommodating inconsistencies."""
        
        strategies = []
        
        for inconsistency in inconsistencies:
            strategy_info = cls.ACCOMMODATION_STRATEGIES.get(inconsistency.inconsistency_type)
            if strategy_info:
                strategies.append(f"{inconsistency.inconsistency_type}: {strategy_info['handling']}")
        
        # Add general accommodation strategies
        if inconsistencies:
            strategies.extend([
                "Preserve all user choices and context diversity",
                "Treat inconsistency as creative richness rather than error",
                "Maintain flexibility for natural project evolution"
            ])
        
        return strategies[:5]  # Limit strategies
    
    @classmethod
    def _identify_flexibility_benefits(
        cls,
        inconsistencies: List[ContextInconsistency],
        basket_contents: Dict[str, List[Dict[str, Any]]]
    ) -> List[str]:
        """Identify benefits of maintaining flexibility."""
        
        benefits = []
        
        if inconsistencies:
            benefits.append("Inconsistency indicates active exploration and creative thinking")
            benefits.append("Diverse contexts support multi-faceted project approaches")
            benefits.append("Flexibility enables natural project evolution and adaptation")
        
        # Content-based benefits
        total_items = sum(len(items) for items in basket_contents.values())
        if total_items > 10:
            benefits.append("Rich content diversity provides comprehensive project foundation")
        
        if len(basket_contents["context_items"]) > 5:
            benefits.append("Extensive context collection enables nuanced decision-making")
        
        return benefits[:4]  # Limit benefits
    
    @classmethod
    def _calculate_health_factors(
        cls,
        basket_contents: Dict[str, List[Dict[str, Any]]],
        inconsistencies: List[ContextInconsistency],
        thematic_analysis: BasketThematicAnalysis
    ) -> Dict[str, Any]:
        """Calculate health factors with accommodation focus."""
        
        factors = {}
        
        # Content richness (positive factor)
        total_items = sum(len(items) for items in basket_contents.values())
        factors["content_richness"] = min(total_items / 20, 1.0)  # Normalize against 20 items
        
        # Thematic diversity (positive factor)
        factors["thematic_diversity"] = thematic_analysis.content_diversity
        
        # Inconsistency accommodation (positive factor)
        accommodation_score = len(inconsistencies) * 0.1  # More inconsistencies = more accommodation
        factors["accommodation_capability"] = min(accommodation_score, 1.0)
        
        # Human flexibility (always high)
        factors["human_flexibility"] = 0.9
        
        # Evolution potential (based on temporal spread)
        factors["evolution_potential"] = 0.8  # Default high
        
        return factors
    
    @classmethod
    def _calculate_accommodation_health_score(
        cls,
        health_factors: Dict[str, Any],
        inconsistencies: List[ContextInconsistency]
    ) -> float:
        """Calculate health score that values accommodation."""
        
        # Base score from factors
        base_score = sum(health_factors.values()) / len(health_factors)
        
        # Accommodation bonus (inconsistencies are valued)
        accommodation_bonus = min(len(inconsistencies) * 0.05, 0.2)
        
        # Final score (biased toward health)
        health_score = min(base_score + accommodation_bonus, 1.0)
        
        # Ensure minimum health score (accommodation approach)
        return max(health_score, 0.6)
    
    @classmethod
    def _calculate_human_compatibility(
        cls,
        inconsistencies: List[ContextInconsistency],
        flexibility_benefits: List[str]
    ) -> float:
        """Calculate how compatible the basket is with human working patterns."""
        
        # Base compatibility (high default)
        base_compatibility = 0.85
        
        # Inconsistency accommodation bonus
        accommodation_bonus = min(len(inconsistencies) * 0.02, 0.1)
        
        # Flexibility bonus
        flexibility_bonus = min(len(flexibility_benefits) * 0.02, 0.05)
        
        return min(base_compatibility + accommodation_bonus + flexibility_bonus, 1.0)
    
    @classmethod
    def _generate_health_insights(
        cls,
        inconsistencies: List[ContextInconsistency],
        flexibility_benefits: List[str],
        health_factors: Dict[str, Any]
    ) -> List[str]:
        """Generate insights about context health."""
        
        insights = []
        
        if inconsistencies:
            insights.append(f"Basket accommodates {len(inconsistencies)} areas of creative complexity")
            insights.append("Inconsistency patterns indicate active, human-driven project development")
        else:
            insights.append("Basket shows consistent patterns - may benefit from additional exploration")
        
        if health_factors.get("content_richness", 0) > 0.7:
            insights.append("High content richness provides strong project foundation")
        
        if len(flexibility_benefits) > 2:
            insights.append("Strong flexibility benefits support adaptive project management")
        
        insights.append("Context health optimized for human working patterns rather than rigid structure")
        
        return insights
    
    @classmethod
    def _calculate_flexibility_score(
        cls,
        basket_contents: Dict[str, List[Dict[str, Any]]],
        context_health: BasketContextHealth
    ) -> float:
        """Calculate overall flexibility score."""
        
        # Base flexibility (high default for human compatibility)
        base_flexibility = 0.8
        
        # Content diversity bonus
        total_items = sum(len(items) for items in basket_contents.values())
        diversity_bonus = min(total_items / 50, 0.1)
        
        # Inconsistency accommodation bonus
        accommodation_bonus = min(len(context_health.inconsistencies) * 0.02, 0.1)
        
        return min(base_flexibility + diversity_bonus + accommodation_bonus, 1.0)
    
    @classmethod
    def _generate_accommodation_examples(
        cls,
        inconsistencies: List[ContextInconsistency]
    ) -> List[str]:
        """Generate examples of how inconsistencies are accommodated."""
        
        examples = []
        
        for inconsistency in inconsistencies[:3]:  # Limit examples
            strategy_info = cls.ACCOMMODATION_STRATEGIES.get(inconsistency.inconsistency_type)
            if strategy_info:
                examples.append(f"{inconsistency.inconsistency_type}: {strategy_info['accommodation']}")
        
        if not examples:
            examples.append("Natural project evolution accommodated through flexible context management")
        
        return examples
    
    @classmethod
    def _calculate_inconsistency_tolerance(
        cls,
        inconsistencies: List[ContextInconsistency],
        basket_contents: Dict[str, List[Dict[str, Any]]]
    ) -> float:
        """Calculate how well the system tolerates inconsistency."""
        
        # High base tolerance (accommodation approach)
        base_tolerance = 0.9
        
        # Accommodation experience bonus
        accommodation_bonus = min(len(inconsistencies) * 0.01, 0.05)
        
        return min(base_tolerance + accommodation_bonus, 1.0)
    
    @classmethod
    def _generate_flexibility_benefits(
        cls,
        inconsistencies: List[ContextInconsistency],
        basket_contents: Dict[str, List[Dict[str, Any]]]
    ) -> List[str]:
        """Generate specific flexibility benefits."""
        
        benefits = [
            "Accommodates natural human context creation patterns",
            "Supports project evolution without forcing rigid structure",
            "Enables multi-faceted project exploration",
            "Preserves creative inconsistencies as valuable diversity"
        ]
        
        if len(inconsistencies) > 2:
            benefits.append("High accommodation capability for complex, evolving projects")
        
        if len(basket_contents["context_items"]) > 8:
            benefits.append("Extensive context accommodation supports comprehensive project thinking")
        
        return benefits[:5]
    
    @classmethod
    def _generate_rigidity_warnings(cls) -> List[str]:
        """Generate warnings about what NOT to enforce."""
        
        return [
            "Do not enforce consistent context types across all items",
            "Do not require uniform scope across all contexts",
            "Do not force thematic consistency at the expense of exploration",
            "Do not eliminate apparently conflicting goals or audiences",
            "Do not standardize creative expression styles"
        ]
    
    @classmethod
    def _classify_inconsistency(cls, description: str) -> str:
        """Classify inconsistency type from description."""
        
        description_lower = description.lower()
        
        if any(word in description_lower for word in ["goal", "intent", "purpose"]):
            return "intent_mismatch"
        elif any(word in description_lower for word in ["audience", "stakeholder", "user"]):
            return "audience_conflict"
        elif any(word in description_lower for word in ["style", "tone", "voice"]):
            return "style_variation"
        elif any(word in description_lower for word in ["scope", "scale", "level"]):
            return "scope_difference"
        elif any(word in description_lower for word in ["time", "temporal", "chronological"]):
            return "temporal_mismatch"
        elif any(word in description_lower for word in ["priority", "importance", "rank"]):
            return "priority_confusion"
        elif any(word in description_lower for word in ["method", "approach", "technique"]):
            return "methodological_diversity"
        else:
            return "semantic_overlap"
    
    @classmethod
    def _assess_inconsistency_severity(cls, description: str, affected_count: int) -> str:
        """Assess inconsistency severity (keeping it gentle)."""
        
        # Default to minor to avoid alarming users
        if affected_count > 10:
            return "notable"
        elif affected_count > 5:
            return "minor"
        else:
            return "minor"