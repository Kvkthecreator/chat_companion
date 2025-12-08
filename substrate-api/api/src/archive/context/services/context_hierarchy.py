"""Context hierarchy analysis and management service."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID, uuid4

from ...models.context import (
    ContextItem, CompositionIntent, ContextHierarchy
)
from ...utils.supabase_client import supabase_client as supabase
from ...utils.db import as_json

logger = logging.getLogger("uvicorn.error")


class ContextHierarchyService:
    """Service for analyzing and managing context hierarchies for composition intelligence."""
# V3.0 DEPRECATION NOTICE:
# This file contains references to context_items table which was merged into blocks table.
# Entity blocks are now identified by semantic_type='entity'.
# This file is legacy/supporting code - update if actively maintained.

    
    @classmethod
    async def analyze_context_hierarchy(
        cls,
        basket_id: UUID,
        workspace_id: str
    ) -> ContextHierarchy:
        """Analyze and create context hierarchy for composition intelligence."""
        
        # Get all context items for the basket
        context_items = await cls._get_basket_contexts(basket_id, workspace_id)
        
        if not context_items:
            # Return empty hierarchy
            return ContextHierarchy(
                basket_id=basket_id,
                primary_contexts=[],
                secondary_contexts=[],
                supporting_contexts=[],
                intent_profile=CompositionIntent(primary_intent="unknown"),
                composition_score=0.0
            )
        
        # Analyze and classify contexts by hierarchy level
        primary_contexts, secondary_contexts, supporting_contexts = cls._classify_contexts_by_hierarchy(
            context_items
        )
        
        # If no explicit hierarchy exists, infer it
        if not primary_contexts and not secondary_contexts:
            primary_contexts, secondary_contexts, supporting_contexts = await cls._infer_context_hierarchy(
                context_items, basket_id, workspace_id
            )
        
        # Analyze composition intent from hierarchy
        intent_profile = await cls._analyze_hierarchy_intent(
            primary_contexts, secondary_contexts, supporting_contexts, basket_id, workspace_id
        )
        
        # Calculate composition score
        composition_score = cls._calculate_hierarchy_composition_score(
            primary_contexts, secondary_contexts, supporting_contexts, intent_profile
        )
        
        return ContextHierarchy(
            basket_id=basket_id,
            primary_contexts=primary_contexts,
            secondary_contexts=secondary_contexts,
            supporting_contexts=supporting_contexts,
            intent_profile=intent_profile,
            composition_score=composition_score
        )
    
    @classmethod
    async def enhance_context_hierarchy(
        cls,
        basket_id: UUID,
        workspace_id: str,
        auto_promote: bool = False
    ) -> ContextHierarchy:
        """Enhance existing context hierarchy with intelligent promotions and adjustments."""
        
        current_hierarchy = await cls.analyze_context_hierarchy(basket_id, workspace_id)
        
        # Identify enhancement opportunities
        enhancement_opportunities = await cls._identify_hierarchy_enhancements(
            current_hierarchy, basket_id, workspace_id
        )
        
        # Apply enhancements if auto_promote is enabled
        if auto_promote:
            for opportunity in enhancement_opportunities:
                await cls._apply_hierarchy_enhancement(opportunity, workspace_id)
            
            # Re-analyze after enhancements
            current_hierarchy = await cls.analyze_context_hierarchy(basket_id, workspace_id)
        
        # Log hierarchy analysis
        await cls._log_hierarchy_analysis(basket_id, current_hierarchy, enhancement_opportunities)
        
        return current_hierarchy
    
    @classmethod
    async def promote_context_level(
        cls,
        context_id: UUID,
        new_level: str,
        workspace_id: str,
        reasoning: Optional[str] = None
    ) -> Dict[str, Any]:
        """Promote or demote a context to a different hierarchy level."""
        
        # Validate new level
        if new_level not in ["primary", "secondary", "supporting"]:
            raise ValueError(f"Invalid hierarchy level: {new_level}")
        
        # Update context hierarchy level
        resp = (
            supabase.table("context_items")
            .update({"hierarchy_level": new_level})
            .eq("id", str(context_id))
            .execute()
        )
        
        if not resp.data:
            raise ValueError(f"Context item {context_id} not found")
        
        # Calculate new composition weight based on level
        new_weight = cls._calculate_weight_for_level(new_level)
        
        # Update composition weight
        supabase.table("context_items").update(
            {"composition_weight": new_weight}
        ).eq("id", str(context_id)).execute()
        
        # Log the promotion
        await cls._log_context_promotion(
            context_id, new_level, new_weight, reasoning or "Manual promotion"
        )
        
        return {
            "context_id": str(context_id),
            "new_hierarchy_level": new_level,
            "new_composition_weight": new_weight,
            "success": True
        }
    
    @classmethod
    async def rebalance_hierarchy_weights(
        cls,
        basket_id: UUID,
        workspace_id: str
    ) -> Dict[str, Any]:
        """Rebalance composition weights within the context hierarchy."""
        
        hierarchy = await cls.analyze_context_hierarchy(basket_id, workspace_id)
        
        # Calculate optimal weights for each level
        weight_adjustments = []
        
        # Primary contexts: highest weights (7-10)
        for i, ctx in enumerate(hierarchy.primary_contexts):
            optimal_weight = 10.0 - (i * 0.5)  # Decreasing priority within primary
            if abs(ctx.composition_weight - optimal_weight) > 0.5:
                weight_adjustments.append({
                    "context_id": ctx.id,
                    "current_weight": ctx.composition_weight,
                    "optimal_weight": optimal_weight,
                    "level": "primary"
                })
        
        # Secondary contexts: medium weights (4-7)
        for i, ctx in enumerate(hierarchy.secondary_contexts):
            optimal_weight = 7.0 - (i * 0.3)
            if abs(ctx.composition_weight - optimal_weight) > 0.5:
                weight_adjustments.append({
                    "context_id": ctx.id,
                    "current_weight": ctx.composition_weight,
                    "optimal_weight": optimal_weight,
                    "level": "secondary"
                })
        
        # Supporting contexts: lower weights (1-4)
        for i, ctx in enumerate(hierarchy.supporting_contexts):
            optimal_weight = 4.0 - (i * 0.2)
            if abs(ctx.composition_weight - optimal_weight) > 0.5:
                weight_adjustments.append({
                    "context_id": ctx.id,
                    "current_weight": ctx.composition_weight,
                    "optimal_weight": optimal_weight,
                    "level": "supporting"
                })
        
        # Apply weight adjustments
        adjustments_applied = 0
        for adjustment in weight_adjustments:
            try:
                supabase.table("context_items").update(
                    {"composition_weight": adjustment["optimal_weight"]}
                ).eq("id", str(adjustment["context_id"])).execute()
                adjustments_applied += 1
            except Exception as e:
                logger.warning(f"Failed to adjust weight for context {adjustment['context_id']}: {e}")
        
        return {
            "basket_id": str(basket_id),
            "total_adjustments": len(weight_adjustments),
            "adjustments_applied": adjustments_applied,
            "hierarchy_rebalanced": adjustments_applied > 0
        }
    
    @classmethod
    async def _get_basket_contexts(cls, basket_id: UUID, workspace_id: str) -> List[ContextItem]:
        """Get all context items for a basket with composition intelligence fields."""
        try:
            resp = (
                supabase.table("context_items")
                .select("*")
                .eq("basket_id", str(basket_id))
                .eq("status", "active")
                .execute()
            )
            
            contexts = []
            for item in resp.data or []:
                # Ensure composition intelligence fields have defaults
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
    def _classify_contexts_by_hierarchy(
        cls,
        context_items: List[ContextItem]
    ) -> Tuple[List[ContextItem], List[ContextItem], List[ContextItem]]:
        """Classify contexts by their explicit hierarchy levels."""
        
        primary_contexts = [ctx for ctx in context_items if ctx.hierarchy_level == "primary"]
        secondary_contexts = [ctx for ctx in context_items if ctx.hierarchy_level == "secondary"]
        supporting_contexts = [ctx for ctx in context_items if ctx.hierarchy_level == "supporting"]
        
        # Sort by composition weight within each level
        primary_contexts.sort(key=lambda x: x.composition_weight, reverse=True)
        secondary_contexts.sort(key=lambda x: x.composition_weight, reverse=True)
        supporting_contexts.sort(key=lambda x: x.composition_weight, reverse=True)
        
        return primary_contexts, secondary_contexts, supporting_contexts
    
    @classmethod
    async def _infer_context_hierarchy(
        cls,
        context_items: List[ContextItem],
        basket_id: UUID,
        workspace_id: str
    ) -> Tuple[List[ContextItem], List[ContextItem], List[ContextItem]]:
        """Infer context hierarchy when none exists explicitly."""
        
        # Get blocks to understand context relationships
        blocks_resp = (
            supabase.table("blocks")
            .select("id,semantic_type,content,state")
            .eq("basket_id", str(basket_id))
            .eq("workspace_id", workspace_id)
            .neq("state", "REJECTED")
            .execute()
        )
        
        blocks = blocks_resp.data or []
        
        # Score contexts for hierarchy inference
        context_scores = []
        
        for ctx in context_items:
            score = cls._calculate_hierarchy_inference_score(ctx, blocks)
            context_scores.append((ctx, score))
        
        # Sort by score
        context_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Classify based on scores and types
        primary_contexts = []
        secondary_contexts = []
        supporting_contexts = []
        
        for i, (ctx, score) in enumerate(context_scores):
            # High-scoring contexts become primary (limit to 2)
            if score > 0.7 and len(primary_contexts) < 2:
                primary_contexts.append(ctx)
            # Medium-scoring or important types become secondary
            elif score > 0.4 or ctx.type in ["goal", "theme", "audience"]:
                secondary_contexts.append(ctx)
            # Everything else is supporting
            else:
                supporting_contexts.append(ctx)
        
        return primary_contexts, secondary_contexts, supporting_contexts
    
    @classmethod
    def _calculate_hierarchy_inference_score(
        cls,
        context_item: ContextItem,
        blocks: List[Dict[str, Any]]
    ) -> float:
        """Calculate a score for hierarchy inference."""
        
        score = 0.0
        
        # Type-based scoring
        type_scores = {
            "goal": 0.9,      # Goals are often primary drivers
            "theme": 0.8,     # Themes provide strong composition direction
            "audience": 0.7,  # Audience shapes composition significantly
            "category": 0.6,  # Categories provide good organization
            "insight": 0.5,   # Insights are valuable but often secondary
            "guideline": 0.4, # Guidelines are usually supporting
            "reference": 0.3, # References are typically supporting
            "constraint": 0.4 # Constraints influence but don't drive
        }
        
        score += type_scores.get(context_item.type, 0.3)
        
        # Confidence-based scoring
        if context_item.confidence:
            score += context_item.confidence * 0.2
        
        # Agent vs user creation (user-created might be more intentional)
        if context_item.created_by_type == "user":
            score += 0.1
        
        # Content length/richness (longer content might indicate importance)
        content_length_score = min(len(context_item.content) / 100, 0.2)
        score += content_length_score
        
        # Block relationship (contexts linked to blocks might be more important)
        if context_item.block_id:
            score += 0.1
        
        return min(score, 1.0)
    
    @classmethod
    async def _analyze_hierarchy_intent(
        cls,
        primary_contexts: List[ContextItem],
        secondary_contexts: List[ContextItem],
        supporting_contexts: List[ContextItem],
        basket_id: UUID,
        workspace_id: str
    ) -> CompositionIntent:
        """Analyze composition intent from context hierarchy."""
        
        # Combine context content for intent analysis
        all_contexts = primary_contexts + secondary_contexts + supporting_contexts
        
        if not all_contexts:
            return CompositionIntent(primary_intent="unknown")
        
        # Analyze primary contexts more heavily
        intent_text = []
        
        # Weight primary contexts heavily
        for ctx in primary_contexts:
            intent_text.extend([ctx.content.lower()] * 3)  # 3x weight
        
        # Weight secondary contexts moderately
        for ctx in secondary_contexts:
            intent_text.extend([ctx.content.lower()] * 2)  # 2x weight
        
        # Include supporting contexts
        for ctx in supporting_contexts:
            intent_text.append(ctx.content.lower())
        
        combined_text = " ".join(intent_text)
        
        # Intent pattern matching (simplified)
        intent_patterns = {
            "strategic_analysis": ["strategy", "strategic", "business", "market", "competitive"],
            "technical_guide": ["technical", "implementation", "guide", "how-to", "development"],
            "executive_summary": ["executive", "summary", "overview", "brief", "leadership"],
            "creative_brief": ["creative", "design", "brand", "concept", "vision"],
            "action_plan": ["action", "plan", "roadmap", "steps", "implementation"]
        }
        
        intent_scores = {}
        for intent, patterns in intent_patterns.items():
            score = sum(1 for pattern in patterns if pattern in combined_text)
            if score > 0:
                intent_scores[intent] = score
        
        primary_intent = max(intent_scores.keys(), key=intent_scores.get) if intent_scores else "general_composition"
        
        # Analyze audience from contexts
        audience = None
        audience_keywords = {
            "executives": ["executive", "leadership", "c-suite", "board"],
            "engineers": ["engineer", "developer", "technical", "dev"],
            "general": ["team", "everyone", "all", "general"]
        }
        
        for aud, keywords in audience_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                audience = aud
                break
        
        # Analyze style from contexts
        style = None
        style_keywords = {
            "formal": ["professional", "formal", "business", "official"],
            "conversational": ["conversational", "casual", "friendly", "informal"],
            "detailed": ["detailed", "thorough", "comprehensive", "technical"]
        }
        
        for sty, keywords in style_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                style = sty
                break
        
        # Analyze scope
        scope = None
        if any(word in combined_text for word in ["overview", "summary", "brief"]):
            scope = "overview"
        elif any(word in combined_text for word in ["detailed", "comprehensive", "thorough"]):
            scope = "deep_dive"
        elif any(word in combined_text for word in ["action", "steps", "plan"]):
            scope = "action_items"
        
        return CompositionIntent(
            primary_intent=primary_intent,
            audience=audience,
            style=style,
            scope=scope,
            complexity_level="medium",  # Default
            composition_metadata={
                "primary_context_count": len(primary_contexts),
                "secondary_context_count": len(secondary_contexts),
                "supporting_context_count": len(supporting_contexts),
                "intent_confidence": len(intent_scores) / len(intent_patterns)
            }
        )
    
    @classmethod
    def _calculate_hierarchy_composition_score(
        cls,
        primary_contexts: List[ContextItem],
        secondary_contexts: List[ContextItem],
        supporting_contexts: List[ContextItem],
        intent_profile: CompositionIntent
    ) -> float:
        """Calculate overall composition score for the hierarchy."""
        
        score_factors = []
        
        # Primary context factor (ideal: 1-2 primary contexts)
        primary_factor = min(len(primary_contexts) / 1, 1.0) if primary_contexts else 0.0
        score_factors.append(primary_factor)
        
        # Secondary context factor (ideal: 2-4 secondary contexts)
        secondary_factor = min(len(secondary_contexts) / 3, 1.0)
        score_factors.append(secondary_factor)
        
        # Intent clarity factor
        intent_clarity = 1.0 if intent_profile.primary_intent != "unknown" else 0.2
        score_factors.append(intent_clarity)
        
        # Hierarchy balance factor
        total_contexts = len(primary_contexts) + len(secondary_contexts) + len(supporting_contexts)
        if total_contexts > 0:
            balance_score = 1.0 - abs(0.3 - (len(primary_contexts) / total_contexts))  # Ideal: 30% primary
            balance_score = max(balance_score, 0.0)
        else:
            balance_score = 0.0
        
        score_factors.append(balance_score)
        
        return sum(score_factors) / len(score_factors)
    
    @classmethod
    def _calculate_weight_for_level(cls, hierarchy_level: str) -> float:
        """Calculate appropriate composition weight for hierarchy level."""
        
        weight_ranges = {
            "primary": 8.0,    # High influence on composition
            "secondary": 5.0,  # Moderate influence
            "supporting": 2.0  # Background influence
        }
        
        return weight_ranges.get(hierarchy_level, 1.0)
    
    @classmethod
    async def _identify_hierarchy_enhancements(
        cls,
        hierarchy: ContextHierarchy,
        basket_id: UUID,
        workspace_id: str
    ) -> List[Dict[str, Any]]:
        """Identify opportunities to enhance the context hierarchy."""
        
        enhancements = []
        
        # Check if primary contexts are missing
        if not hierarchy.primary_contexts and hierarchy.secondary_contexts:
            # Suggest promoting high-scoring secondary contexts
            for ctx in hierarchy.secondary_contexts[:2]:
                if ctx.composition_weight > 3.0:  # High weight secondary
                    enhancements.append({
                        "type": "promote_to_primary",
                        "context_id": ctx.id,
                        "current_level": "secondary",
                        "suggested_level": "primary",
                        "reasoning": f"High-weight secondary context '{ctx.content[:50]}...' could drive primary composition"
                    })
        
        # Check for weight imbalances
        for ctx in hierarchy.primary_contexts:
            if ctx.composition_weight < 5.0:  # Low weight for primary
                enhancements.append({
                    "type": "adjust_weight",
                    "context_id": ctx.id,
                    "current_weight": ctx.composition_weight,
                    "suggested_weight": 8.0,
                    "reasoning": "Primary context should have higher composition weight"
                })
        
        return enhancements
    
    @classmethod
    async def _apply_hierarchy_enhancement(
        cls,
        enhancement: Dict[str, Any],
        workspace_id: str
    ) -> None:
        """Apply a hierarchy enhancement."""
        
        try:
            if enhancement["type"] == "promote_to_primary":
                await cls.promote_context_level(
                    UUID(enhancement["context_id"]),
                    enhancement["suggested_level"],
                    workspace_id,
                    enhancement["reasoning"]
                )
            elif enhancement["type"] == "adjust_weight":
                supabase.table("context_items").update(
                    {"composition_weight": enhancement["suggested_weight"]}
                ).eq("id", enhancement["context_id"]).execute()
        except Exception as e:
            logger.warning(f"Failed to apply enhancement: {e}")
    
    @classmethod
    async def _log_hierarchy_analysis(
        cls,
        basket_id: UUID,
        hierarchy: ContextHierarchy,
        enhancements: List[Dict[str, Any]]
    ) -> None:
        """Log hierarchy analysis for audit trail."""
        
        event_data = {
            "id": str(uuid4()),
            "basket_id": str(basket_id),
            "kind": "context.hierarchy_analyzed",
            "payload": {
                "primary_contexts_count": len(hierarchy.primary_contexts),
                "secondary_contexts_count": len(hierarchy.secondary_contexts),
                "supporting_contexts_count": len(hierarchy.supporting_contexts),
                "composition_score": hierarchy.composition_score,
                "primary_intent": hierarchy.intent_profile.primary_intent,
                "enhancements_identified": len(enhancements),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        supabase.table("events").insert(as_json(event_data)).execute()
    
    @classmethod
    async def _log_context_promotion(
        cls,
        context_id: UUID,
        new_level: str,
        new_weight: float,
        reasoning: str
    ) -> None:
        """Log context hierarchy promotion."""
        
        event_data = {
            "id": str(uuid4()),
            "kind": "context.hierarchy_promoted",
            "payload": {
                "context_id": str(context_id),
                "new_hierarchy_level": new_level,
                "new_composition_weight": new_weight,
                "reasoning": reasoning,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        supabase.table("events").insert(as_json(event_data)).execute()