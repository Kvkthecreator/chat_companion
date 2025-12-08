"""Core composition intelligence service for transforming context_items into composition drivers."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID, uuid4

from pydantic import BaseModel

from ...models.context import (
    ContextItem, CompositionIntent, ContextHierarchy, CompositionProfile
)
from src.schemas.context_composition_schema import (
    CompositionIntelligenceReport,
    CompositionOpportunity,
    ContextEnhancementSuggestion,
    CompositionReadinessAssessment,
    IntentAnalysisResult
)
from ...utils.supabase_client import supabase_client as supabase
from ...utils.db import as_json

logger = logging.getLogger("uvicorn.error")


class CompositionIntelligenceService:
    """Core service for composition intelligence analysis and management."""
# V3.0 DEPRECATION NOTICE:
# This file contains references to context_items table which was merged into blocks table.
# Entity blocks are now identified by semantic_type='entity'.
# This file is legacy/supporting code - update if actively maintained.

    
    # Intent detection patterns
    INTENT_PATTERNS = {
        "strategic_analysis": [
            "strategy", "strategic", "analysis", "market", "competitive",
            "business", "growth", "opportunity", "risk", "positioning"
        ],
        "technical_guide": [
            "technical", "implementation", "guide", "how-to", "tutorial",
            "architecture", "system", "development", "engineering", "code"
        ],
        "executive_summary": [
            "executive", "summary", "overview", "brief", "highlights",
            "key points", "recommendations", "decisions", "leadership"
        ],
        "creative_brief": [
            "creative", "design", "brand", "concept", "vision",
            "aesthetic", "style", "creative direction", "inspiration"
        ],
        "research_report": [
            "research", "findings", "data", "analysis", "study",
            "investigation", "methodology", "results", "conclusions"
        ],
        "action_plan": [
            "action", "plan", "roadmap", "timeline", "steps",
            "implementation", "execution", "milestones", "deliverables"
        ]
    }
    
    # Audience detection patterns
    AUDIENCE_PATTERNS = {
        "executives": [
            "executives", "leadership", "C-suite", "board", "directors",
            "senior management", "stakeholders", "decision makers"
        ],
        "engineers": [
            "engineers", "developers", "technical team", "dev team",
            "engineering", "technical", "architects", "programmers"
        ],
        "general": [
            "team", "everyone", "all", "general", "broad audience",
            "stakeholders", "users", "public"
        ],
        "customers": [
            "customers", "users", "clients", "end users", "market",
            "target audience", "consumers", "buyers"
        ]
    }
    
    # Style detection patterns
    STYLE_PATTERNS = {
        "formal": [
            "professional", "formal", "business", "corporate",
            "official", "structured", "detailed", "comprehensive"
        ],
        "conversational": [
            "conversational", "casual", "friendly", "accessible",
            "informal", "approachable", "easy", "simple"
        ],
        "detailed": [
            "detailed", "thorough", "comprehensive", "in-depth",
            "complete", "extensive", "exhaustive", "technical"
        ]
    }
    
    @classmethod
    async def analyze_composition_intelligence(
        cls,
        basket_id: UUID,
        workspace_id: str,
        analysis_focus: str = "comprehensive"
    ) -> CompositionIntelligenceReport:
        """Perform comprehensive composition intelligence analysis."""
        
        # Get all context items and blocks for the basket
        context_items = await cls._get_basket_contexts(basket_id, workspace_id)
        blocks = await cls._get_basket_blocks(basket_id, workspace_id)
        
        # Analyze intent from contexts and blocks
        intent_analysis = await cls._analyze_intent(context_items, blocks)
        
        # Identify composition opportunities
        opportunities = await cls._identify_composition_opportunities(
            context_items, blocks, intent_analysis
        )
        
        # Generate context enhancement suggestions
        enhancements = await cls._suggest_context_enhancements(
            context_items, blocks, intent_analysis
        )
        
        # Calculate overall readiness
        readiness_score = cls._calculate_composition_readiness(
            context_items, blocks, intent_analysis
        )
        
        # Generate insights and recommendations
        insights = cls._generate_key_insights(
            context_items, blocks, intent_analysis, opportunities
        )
        
        next_steps = cls._generate_next_steps(
            readiness_score, opportunities, enhancements
        )
        
        return CompositionIntelligenceReport(
            basket_id=basket_id,
            intent_analysis=intent_analysis,
            composition_opportunities=opportunities,
            context_enhancements=enhancements,
            overall_composition_readiness=readiness_score,
            key_insights=insights,
            recommended_next_steps=next_steps,
            analysis_metadata={
                "context_count": len(context_items),
                "block_count": len(blocks),
                "analysis_focus": analysis_focus
            }
        )
    
    @classmethod
    async def assess_composition_readiness(
        cls,
        basket_id: UUID,
        workspace_id: str
    ) -> CompositionReadinessAssessment:
        """Assess how ready a basket is for composition."""
        
        context_items = await cls._get_basket_contexts(basket_id, workspace_id)
        blocks = await cls._get_basket_blocks(basket_id, workspace_id)
        
        # Calculate component scores
        context_coverage = cls._calculate_context_coverage(context_items, blocks)
        intent_clarity = await cls._calculate_intent_clarity(context_items, blocks)
        hierarchy_strength = cls._calculate_hierarchy_strength(context_items)
        block_alignment = cls._calculate_block_alignment(context_items, blocks)
        
        # Overall readiness score
        readiness_score = (context_coverage + intent_clarity + hierarchy_strength + block_alignment) / 4
        
        # Specific readiness factors
        has_primary_context = any(
            ctx.hierarchy_level == "primary" for ctx in context_items
        )
        has_clear_intent = intent_clarity > 0.6
        sufficient_supporting_contexts = len([
            ctx for ctx in context_items if ctx.hierarchy_level in ["secondary", "supporting"]
        ]) >= 2
        adequate_block_coverage = len(blocks) >= 3
        
        # Generate improvement recommendations
        improvement_areas = []
        quick_wins = []
        strategic_improvements = []
        
        if not has_primary_context:
            improvement_areas.append("Missing primary composition context")
            quick_wins.append("Identify and elevate a primary context driver")
        
        if not has_clear_intent:
            improvement_areas.append("Unclear composition intent")
            strategic_improvements.append("Analyze memory for composition intent patterns")
        
        if not sufficient_supporting_contexts:
            improvement_areas.append("Insufficient supporting contexts")
            quick_wins.append("Add semantic tags to key blocks")
        
        if not adequate_block_coverage:
            improvement_areas.append("Limited memory substrate")
            strategic_improvements.append("Expand memory with additional insights")
        
        return CompositionReadinessAssessment(
            basket_id=basket_id,
            readiness_score=readiness_score,
            context_coverage=context_coverage,
            intent_clarity=intent_clarity,
            hierarchy_strength=hierarchy_strength,
            block_alignment=block_alignment,
            has_primary_context=has_primary_context,
            has_clear_intent=has_clear_intent,
            sufficient_supporting_contexts=sufficient_supporting_contexts,
            adequate_block_coverage=adequate_block_coverage,
            improvement_areas=improvement_areas,
            quick_wins=quick_wins,
            strategic_improvements=strategic_improvements
        )
    
    @classmethod
    async def _get_basket_contexts(cls, basket_id: UUID, workspace_id: str) -> List[ContextItem]:
        """Get all context items for a basket."""
        try:
            resp = (
                supabase.table("context_items")
                .select("*")
                .eq("basket_id", str(basket_id))
                .eq("status", "active")
                .execute()
            )
            
            # Convert to ContextItem models with composition intelligence defaults
            contexts = []
            for item in resp.data or []:
                # Set defaults for composition intelligence fields if missing
                context_data = {
                    **item,
                    "composition_weight": item.get("composition_weight", 1.0),
                    "hierarchy_level": item.get("hierarchy_level", "secondary"),
                    "intent_category": item.get("intent_category"),
                    "composition_metadata": item.get("composition_metadata", {})
                }
                contexts.append(ContextItem(**context_data))
            
            return contexts
            
        except Exception as e:
            logger.exception(f"Failed to get basket contexts: {e}")
            return []
    
    @classmethod
    async def _get_basket_blocks(cls, basket_id: UUID, workspace_id: str) -> List[Dict[str, Any]]:
        """Get all blocks for a basket."""
        try:
            resp = (
                supabase.table("blocks")
                .select("id,semantic_type,content,state,created_at")
                .eq("basket_id", str(basket_id))
                .eq("workspace_id", workspace_id)
                .neq("state", "REJECTED")
                .execute()
            )
            
            return resp.data or []
            
        except Exception as e:
            logger.exception(f"Failed to get basket blocks: {e}")
            return []
    
    @classmethod
    async def _analyze_intent(
        cls,
        context_items: List[ContextItem],
        blocks: List[Dict[str, Any]]
    ) -> IntentAnalysisResult:
        """Analyze composition intent from contexts and blocks."""
        
        # Combine all text for analysis
        all_text = []
        
        # Add context content
        for ctx in context_items:
            all_text.append(ctx.content.lower())
        
        # Add block content
        for block in blocks:
            if block.get("content"):
                all_text.append(block["content"].lower())
        
        combined_text = " ".join(all_text)
        
        # Detect intents
        detected_intents = []
        intent_scores = {}
        
        for intent, patterns in cls.INTENT_PATTERNS.items():
            score = sum(1 for pattern in patterns if pattern in combined_text)
            if score > 0:
                intent_scores[intent] = score / len(patterns)
                detected_intents.append(intent)
        
        # Primary intent is highest scoring
        primary_intent = max(intent_scores.keys(), key=intent_scores.get) if intent_scores else None
        intent_confidence = intent_scores.get(primary_intent, 0.0) if primary_intent else 0.0
        
        # Detect audience indicators
        audience_indicators = []
        for audience, patterns in cls.AUDIENCE_PATTERNS.items():
            if any(pattern in combined_text for pattern in patterns):
                audience_indicators.append(audience)
        
        # Detect style indicators
        style_indicators = []
        for style, patterns in cls.STYLE_PATTERNS.items():
            if any(pattern in combined_text for pattern in patterns):
                style_indicators.append(style)
        
        # Detect scope indicators
        scope_indicators = []
        if any(word in combined_text for word in ["overview", "summary", "brief"]):
            scope_indicators.append("overview")
        if any(word in combined_text for word in ["detailed", "comprehensive", "thorough"]):
            scope_indicators.append("deep_dive")
        if any(word in combined_text for word in ["action", "steps", "plan", "implementation"]):
            scope_indicators.append("action_items")
        
        reasoning = f"Analyzed {len(context_items)} contexts and {len(blocks)} blocks. "
        if primary_intent:
            reasoning += f"Primary intent '{primary_intent}' detected with {intent_confidence:.1%} confidence."
        else:
            reasoning += "No clear primary intent detected from available content."
        
        return IntentAnalysisResult(
            detected_intents=detected_intents,
            primary_intent=primary_intent,
            intent_confidence=min(intent_confidence, 1.0),
            audience_indicators=audience_indicators,
            style_indicators=style_indicators,
            scope_indicators=scope_indicators,
            reasoning=reasoning
        )
    
    @classmethod
    async def _identify_composition_opportunities(
        cls,
        context_items: List[ContextItem],
        blocks: List[Dict[str, Any]],
        intent_analysis: IntentAnalysisResult
    ) -> List[CompositionOpportunity]:
        """Identify composition opportunities based on available memory."""
        
        opportunities = []
        
        # Strategic analysis opportunity
        if intent_analysis.primary_intent == "strategic_analysis" or "strategic" in intent_analysis.detected_intents:
            strategic_blocks = len([b for b in blocks if b.get("semantic_type") in ["goal", "insight", "constraint"]])
            opportunities.append(CompositionOpportunity(
                opportunity_type="strategic_analysis",
                description="Create strategic analysis document from business insights and goals",
                required_contexts=["goal", "insight", "constraint"],
                available_blocks=strategic_blocks,
                composition_readiness=min(strategic_blocks / 5, 1.0),
                estimated_value="high",
                creation_complexity="medium"
            ))
        
        # Technical guide opportunity
        if intent_analysis.primary_intent == "technical_guide" or "technical" in intent_analysis.detected_intents:
            technical_blocks = len([b for b in blocks if b.get("semantic_type") in ["insight", "constraint", "reference"]])
            opportunities.append(CompositionOpportunity(
                opportunity_type="technical_guide",
                description="Create technical implementation guide from insights and constraints",
                required_contexts=["insight", "constraint", "reference"],
                available_blocks=technical_blocks,
                composition_readiness=min(technical_blocks / 4, 1.0),
                estimated_value="high",
                creation_complexity="complex"
            ))
        
        # Executive summary opportunity
        if len(blocks) >= 3:
            summary_readiness = len([ctx for ctx in context_items if ctx.hierarchy_level == "primary"]) / max(1, len(context_items))
            opportunities.append(CompositionOpportunity(
                opportunity_type="executive_summary",
                description="Create executive summary highlighting key insights and recommendations",
                required_contexts=["goal", "insight"],
                available_blocks=len(blocks),
                composition_readiness=summary_readiness,
                estimated_value="medium",
                creation_complexity="simple"
            ))
        
        return opportunities
    
    @classmethod
    async def _suggest_context_enhancements(
        cls,
        context_items: List[ContextItem],
        blocks: List[Dict[str, Any]],
        intent_analysis: IntentAnalysisResult
    ) -> List[ContextEnhancementSuggestion]:
        """Suggest context enhancements for better composition intelligence."""
        
        suggestions = []
        
        # Find blocks without context items
        blocks_with_context = set()
        for ctx in context_items:
            if ctx.block_id:
                blocks_with_context.add(str(ctx.block_id))
        
        untagged_blocks = [b for b in blocks if b["id"] not in blocks_with_context]
        
        # Suggest context for untagged blocks based on semantic type
        for block in untagged_blocks[:3]:  # Limit suggestions
            semantic_type = block.get("semantic_type", "insight")
            content = block.get("content", "")
            
            if semantic_type == "goal":
                suggestions.append(ContextEnhancementSuggestion(
                    target_id=UUID(block["id"]),
                    target_type="block",
                    suggested_context_type="goal",
                    suggested_content=f"Goal context: {content[:50]}...",
                    enhancement_reason="Goal blocks benefit from explicit goal context for composition",
                    composition_impact="high",
                    confidence=0.8
                ))
            elif semantic_type == "insight":
                suggestions.append(ContextEnhancementSuggestion(
                    target_id=UUID(block["id"]),
                    target_type="block",
                    suggested_context_type="theme",
                    suggested_content=f"Theme: {content[:50]}...",
                    enhancement_reason="Insights benefit from thematic context for better composition",
                    composition_impact="medium",
                    confidence=0.7
                ))
        
        return suggestions
    
    @classmethod
    def _calculate_composition_readiness(
        cls,
        context_items: List[ContextItem],
        blocks: List[Dict[str, Any]],
        intent_analysis: IntentAnalysisResult
    ) -> float:
        """Calculate overall composition readiness score."""
        
        factors = []
        
        # Context coverage (blocks with context items)
        context_coverage = cls._calculate_context_coverage(context_items, blocks)
        factors.append(context_coverage)
        
        # Intent clarity
        factors.append(intent_analysis.intent_confidence)
        
        # Hierarchy strength
        hierarchy_strength = cls._calculate_hierarchy_strength(context_items)
        factors.append(hierarchy_strength)
        
        # Memory substrate adequacy
        substrate_score = min(len(blocks) / 5, 1.0)  # Ideal: 5+ blocks
        factors.append(substrate_score)
        
        return sum(factors) / len(factors) if factors else 0.0
    
    @classmethod
    def _calculate_context_coverage(
        cls,
        context_items: List[ContextItem],
        blocks: List[Dict[str, Any]]
    ) -> float:
        """Calculate what percentage of blocks have context coverage."""
        
        if not blocks:
            return 0.0
        
        blocks_with_context = set()
        for ctx in context_items:
            if ctx.block_id:
                blocks_with_context.add(str(ctx.block_id))
        
        return len(blocks_with_context) / len(blocks)
    
    @classmethod
    async def _calculate_intent_clarity(
        cls,
        context_items: List[ContextItem],
        blocks: List[Dict[str, Any]]
    ) -> float:
        """Calculate how clear the composition intent is."""
        
        intent_analysis = await cls._analyze_intent(context_items, blocks)
        return intent_analysis.intent_confidence
    
    @classmethod
    def _calculate_hierarchy_strength(cls, context_items: List[ContextItem]) -> float:
        """Calculate strength of context hierarchy."""
        
        if not context_items:
            return 0.0
        
        primary_count = len([ctx for ctx in context_items if ctx.hierarchy_level == "primary"])
        secondary_count = len([ctx for ctx in context_items if ctx.hierarchy_level == "secondary"])
        supporting_count = len([ctx for ctx in context_items if ctx.hierarchy_level == "supporting"])
        
        # Ideal: 1-2 primary, 2-4 secondary, any number supporting
        primary_score = min(primary_count / 1, 1.0) if primary_count > 0 else 0.0
        secondary_score = min(secondary_count / 2, 1.0)
        
        return (primary_score + secondary_score) / 2
    
    @classmethod
    def _calculate_block_alignment(
        cls,
        context_items: List[ContextItem],
        blocks: List[Dict[str, Any]]
    ) -> float:
        """Calculate how well blocks align with composition contexts."""
        
        if not blocks or not context_items:
            return 0.0
        
        # Simple heuristic: blocks with context items are "aligned"
        aligned_blocks = set()
        for ctx in context_items:
            if ctx.block_id:
                aligned_blocks.add(str(ctx.block_id))
        
        return len(aligned_blocks) / len(blocks)
    
    @classmethod
    def _generate_key_insights(
        cls,
        context_items: List[ContextItem],
        blocks: List[Dict[str, Any]],
        intent_analysis: IntentAnalysisResult,
        opportunities: List[CompositionOpportunity]
    ) -> List[str]:
        """Generate key insights from composition analysis."""
        
        insights = []
        
        if intent_analysis.primary_intent:
            insights.append(f"Primary composition intent detected: {intent_analysis.primary_intent}")
        
        if len(opportunities) > 0:
            insights.append(f"Identified {len(opportunities)} composition opportunities")
        
        primary_contexts = [ctx for ctx in context_items if ctx.hierarchy_level == "primary"]
        if primary_contexts:
            insights.append(f"Strong composition drivers: {len(primary_contexts)} primary contexts")
        else:
            insights.append("No primary composition contexts identified - consider elevating key contexts")
        
        context_coverage = cls._calculate_context_coverage(context_items, blocks)
        if context_coverage > 0.7:
            insights.append(f"Excellent context coverage: {context_coverage:.1%} of blocks have semantic context")
        elif context_coverage < 0.3:
            insights.append(f"Limited context coverage: Only {context_coverage:.1%} of blocks have semantic context")
        
        return insights
    
    @classmethod
    def _generate_next_steps(
        cls,
        readiness_score: float,
        opportunities: List[CompositionOpportunity],
        enhancements: List[ContextEnhancementSuggestion]
    ) -> List[str]:
        """Generate recommended next steps."""
        
        steps = []
        
        if readiness_score < 0.4:
            steps.append("Focus on building foundational composition intelligence")
            steps.append("Add primary context drivers to guide composition")
        elif readiness_score < 0.7:
            steps.append("Enhance context coverage and hierarchy strength")
            steps.append("Consider creating compositions from high-readiness opportunities")
        else:
            steps.append("Ready for advanced composition - consider document creation")
            
        if enhancements:
            steps.append(f"Apply {len(enhancements)} context enhancement suggestions")
        
        high_value_opportunities = [op for op in opportunities if op.estimated_value == "high"]
        if high_value_opportunities:
            steps.append(f"Prioritize {len(high_value_opportunities)} high-value composition opportunities")
        
        return steps