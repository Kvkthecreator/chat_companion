"""Context-driven discovery service for finding relevant memory based on composition intent."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Set
from uuid import UUID, uuid4
import math

from ...models.context import ContextItem
from src.schemas.context_composition_schema import (
    ContextDiscoveryRequest,
    ContextDiscoveryResult,
    BlockRelevanceScore
)
from ...utils.supabase_client import supabase_client as supabase

logger = logging.getLogger("uvicorn.error")


class ContextDiscoveryService:
    """Service for discovering relevant memory objects based on composition context."""
# V3.0 DEPRECATION NOTICE:
# This file contains references to context_items table which was merged into blocks table.
# Entity blocks are now identified by semantic_type='entity'.
# This file is legacy/supporting code - update if actively maintained.

    
    @classmethod
    async def discover_relevant_blocks(
        cls,
        request: ContextDiscoveryRequest,
        workspace_id: str
    ) -> ContextDiscoveryResult:
        """Discover blocks relevant to target contexts."""
        
        # Get target contexts
        target_contexts = await cls._get_contexts_by_ids(request.target_contexts, workspace_id)
        
        if not target_contexts:
            return ContextDiscoveryResult(
                target_context_ids=request.target_contexts,
                discovered_blocks=[],
                discovery_summary="No target contexts found",
                total_candidates_analyzed=0,
                results_returned=0,
                average_relevance_score=0.0
            )
        
        # Get all blocks in the basket
        candidate_blocks = await cls._get_basket_blocks(
            request.basket_id, workspace_id, request.discovery_scope
        )
        
        # Score blocks for relevance to target contexts
        block_scores = []
        
        for block in candidate_blocks:
            relevance_score = await cls._calculate_block_relevance(
                block, target_contexts, workspace_id
            )
            
            if relevance_score.relevance_score >= request.min_relevance_threshold:
                block_scores.append(relevance_score)
        
        # Sort by relevance score and limit results
        block_scores.sort(key=lambda x: x.relevance_score, reverse=True)
        final_results = block_scores[:request.max_results]
        
        # Calculate average relevance
        avg_relevance = (
            sum(score.relevance_score for score in final_results) / len(final_results)
            if final_results else 0.0
        )
        
        # Generate discovery summary
        summary = cls._generate_discovery_summary(
            target_contexts, len(candidate_blocks), len(final_results), avg_relevance
        )
        
        return ContextDiscoveryResult(
            target_context_ids=request.target_contexts,
            discovered_blocks=final_results,
            discovery_summary=summary,
            total_candidates_analyzed=len(candidate_blocks),
            results_returned=len(final_results),
            average_relevance_score=avg_relevance
        )
    
    @classmethod
    async def discover_composition_relevant_memory(
        cls,
        basket_id: UUID,
        composition_intent: str,
        workspace_id: str,
        max_results: int = 15
    ) -> ContextDiscoveryResult:
        """Discover memory relevant to a specific composition intent."""
        
        # Find contexts related to the composition intent
        intent_contexts = await cls._find_intent_related_contexts(
            basket_id, composition_intent, workspace_id
        )
        
        if not intent_contexts:
            # Create a discovery request based on intent patterns
            return await cls._discover_by_intent_patterns(
                basket_id, composition_intent, workspace_id, max_results
            )
        
        # Use context-driven discovery
        request = ContextDiscoveryRequest(
            basket_id=basket_id,
            target_contexts=[ctx.id for ctx in intent_contexts],
            discovery_scope="blocks",
            include_related=True,
            max_results=max_results,
            min_relevance_threshold=0.3
        )
        
        return await cls.discover_relevant_blocks(request, workspace_id)
    
    @classmethod
    async def discover_semantic_clusters(
        cls,
        basket_id: UUID,
        workspace_id: str,
        cluster_threshold: float = 0.6
    ) -> List[Dict[str, Any]]:
        """Discover semantic clusters of related memory objects."""
        
        # Get all contexts and blocks
        contexts = await cls._get_basket_contexts(basket_id, workspace_id)
        blocks = await cls._get_basket_blocks(basket_id, workspace_id, "blocks")
        
        # Create clusters based on semantic similarity
        clusters = []
        processed_items = set()
        
        for context in contexts:
            if context.id in processed_items:
                continue
            
            # Find related contexts and blocks
            cluster_contexts = [context]
            cluster_blocks = []
            processed_items.add(context.id)
            
            # Find semantically similar contexts
            for other_context in contexts:
                if other_context.id in processed_items:
                    continue
                
                similarity = cls._calculate_semantic_similarity(
                    context.content, other_context.content
                )
                
                if similarity >= cluster_threshold:
                    cluster_contexts.append(other_context)
                    processed_items.add(other_context.id)
            
            # Find blocks relevant to this context cluster
            for block in blocks:
                relevance_score = await cls._calculate_block_relevance(
                    block, cluster_contexts, workspace_id
                )
                
                if relevance_score.relevance_score >= 0.5:
                    cluster_blocks.append({
                        "block": block,
                        "relevance_score": relevance_score.relevance_score
                    })
            
            # Sort blocks by relevance
            cluster_blocks.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            if len(cluster_contexts) > 1 or len(cluster_blocks) > 0:
                clusters.append({
                    "cluster_id": str(uuid4()),
                    "primary_context": context,
                    "related_contexts": cluster_contexts[1:],  # Exclude primary
                    "relevant_blocks": cluster_blocks,
                    "cluster_size": len(cluster_contexts) + len(cluster_blocks),
                    "average_relevance": (
                        sum(b["relevance_score"] for b in cluster_blocks) / len(cluster_blocks)
                        if cluster_blocks else 0.0
                    )
                })
        
        # Sort clusters by size and relevance
        clusters.sort(key=lambda x: (x["cluster_size"], x["average_relevance"]), reverse=True)
        
        return clusters
    
    @classmethod
    async def _calculate_block_relevance(
        cls,
        block: Dict[str, Any],
        target_contexts: List[ContextItem],
        workspace_id: str
    ) -> BlockRelevanceScore:
        """Calculate how relevant a block is to target contexts."""
        
        block_content = block.get("content", "").lower()
        block_semantic_type = block.get("semantic_type", "")
        
        relevance_factors = []
        context_alignment_factors = []
        composition_value_factors = []
        contributing_contexts = []
        reasoning_parts = []
        
        # Analyze relevance to each target context
        for context in target_contexts:
            context_content = context.content.lower()
            
            # Content similarity score
            content_similarity = cls._calculate_semantic_similarity(
                block_content, context_content
            )
            
            if content_similarity > 0.3:
                relevance_factors.append(content_similarity)
                contributing_contexts.append(context.id)
                reasoning_parts.append(f"Content similarity to '{context.content[:30]}...'")
            
            # Semantic type alignment
            type_alignment = cls._calculate_type_alignment(
                block_semantic_type, context.type, context.intent_category
            )
            
            if type_alignment > 0.0:
                context_alignment_factors.append(type_alignment)
                reasoning_parts.append(f"Semantic alignment with {context.type} context")
            
            # Composition weight influence
            composition_influence = context.composition_weight / 10.0  # Normalize to 0-1
            composition_value_factors.append(composition_influence)
        
        # Calculate final scores
        relevance_score = (
            max(relevance_factors) if relevance_factors else 0.0
        )
        
        context_alignment = (
            sum(context_alignment_factors) / len(context_alignment_factors)
            if context_alignment_factors else 0.0
        )
        
        composition_value = (
            sum(composition_value_factors) / len(composition_value_factors)
            if composition_value_factors else 0.0
        )
        
        # Block state bonus (accepted blocks are more valuable)
        state_bonus = 0.0
        block_state = block.get("state", "")
        if block_state == "ACCEPTED":
            state_bonus = 0.2
        elif block_state == "LOCKED":
            state_bonus = 0.3
        elif block_state == "CONSTANT":
            state_bonus = 0.4
        
        # Apply state bonus to final relevance
        final_relevance = min(relevance_score + state_bonus, 1.0)
        
        # Generate reasoning
        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "No specific alignment detected"
        if state_bonus > 0:
            reasoning += f"; Block state '{block_state}' adds {state_bonus} bonus"
        
        return BlockRelevanceScore(
            block_id=UUID(block["id"]),
            relevance_score=final_relevance,
            context_alignment=context_alignment,
            composition_value=composition_value,
            reasoning=reasoning,
            contributing_contexts=contributing_contexts
        )
    
    @classmethod
    def _calculate_semantic_similarity(cls, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts."""
        
        if not text1 or not text2:
            return 0.0
        
        # Simple word-based similarity (can be enhanced with embeddings later)
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        # Jaccard similarity
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        jaccard_similarity = len(intersection) / len(union)
        
        # Enhance with phrase matching
        phrases1 = cls._extract_key_phrases(text1)
        phrases2 = cls._extract_key_phrases(text2)
        
        phrase_overlap = len(phrases1.intersection(phrases2))
        phrase_bonus = min(phrase_overlap * 0.1, 0.3)
        
        return min(jaccard_similarity + phrase_bonus, 1.0)
    
    @classmethod
    def _extract_key_phrases(cls, text: str, min_length: int = 10) -> Set[str]:
        """Extract key phrases from text."""
        
        # Simple approach: extract longer phrases
        words = text.lower().split()
        phrases = set()
        
        # 2-word phrases
        for i in range(len(words) - 1):
            phrase = f"{words[i]} {words[i + 1]}"
            if len(phrase) >= min_length:
                phrases.add(phrase)
        
        # 3-word phrases
        for i in range(len(words) - 2):
            phrase = f"{words[i]} {words[i + 1]} {words[i + 2]}"
            if len(phrase) >= min_length:
                phrases.add(phrase)
        
        return phrases
    
    @classmethod
    def _calculate_type_alignment(
        cls,
        block_semantic_type: str,
        context_type: str,
        intent_category: Optional[str]
    ) -> float:
        """Calculate alignment between block semantic type and context."""
        
        # Type alignment matrix
        alignment_matrix = {
            ("goal", "goal"): 1.0,
            ("goal", "theme"): 0.7,
            ("goal", "audience"): 0.6,
            ("insight", "insight"): 1.0,
            ("insight", "theme"): 0.8,
            ("insight", "category"): 0.7,
            ("constraint", "constraint"): 1.0,
            ("constraint", "guideline"): 0.8,
            ("reference", "reference"): 1.0,
            ("reference", "category"): 0.6,
            ("audience", "audience"): 1.0,
            ("audience", "goal"): 0.6,
        }
        
        # Direct type alignment
        alignment_key = (block_semantic_type, context_type)
        direct_alignment = alignment_matrix.get(alignment_key, 0.0)
        
        # Intent category bonus
        intent_bonus = 0.0
        if intent_category:
            if intent_category == "strategic" and block_semantic_type in ["goal", "insight"]:
                intent_bonus = 0.2
            elif intent_category == "technical" and block_semantic_type in ["constraint", "reference"]:
                intent_bonus = 0.2
            elif intent_category == "creative" and block_semantic_type in ["insight", "theme"]:
                intent_bonus = 0.2
        
        return min(direct_alignment + intent_bonus, 1.0)
    
    @classmethod
    async def _get_contexts_by_ids(
        cls,
        context_ids: List[UUID],
        workspace_id: str
    ) -> List[ContextItem]:
        """Get context items by their IDs."""
        
        try:
            resp = (
                supabase.table("context_items")
                .select("*")
                .in_("id", [str(cid) for cid in context_ids])
                .eq("status", "active")
                .execute()
            )
            
            contexts = []
            for item in resp.data or []:
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
            logger.exception(f"Failed to get contexts by IDs: {e}")
            return []
    
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
            
            contexts = []
            for item in resp.data or []:
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
    async def _get_basket_blocks(
        cls,
        basket_id: UUID,
        workspace_id: str,
        scope: str = "blocks"
    ) -> List[Dict[str, Any]]:
        """Get blocks for discovery analysis."""
        
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
    async def _find_intent_related_contexts(
        cls,
        basket_id: UUID,
        composition_intent: str,
        workspace_id: str
    ) -> List[ContextItem]:
        """Find contexts related to a specific composition intent."""
        
        contexts = await cls._get_basket_contexts(basket_id, workspace_id)
        
        # Intent-related keywords
        intent_keywords = {
            "strategic_analysis": ["strategic", "strategy", "business", "market", "competitive"],
            "technical_guide": ["technical", "implementation", "guide", "development", "system"],
            "executive_summary": ["executive", "summary", "overview", "leadership", "brief"],
            "creative_brief": ["creative", "design", "brand", "concept", "vision"],
            "action_plan": ["action", "plan", "roadmap", "steps", "implementation"]
        }
        
        keywords = intent_keywords.get(composition_intent, [])
        if not keywords:
            return []
        
        # Find contexts with intent-related content
        related_contexts = []
        
        for context in contexts:
            content_lower = context.content.lower()
            if any(keyword in content_lower for keyword in keywords):
                related_contexts.append(context)
        
        # Sort by composition weight and hierarchy level
        related_contexts.sort(
            key=lambda x: (
                {"primary": 3, "secondary": 2, "supporting": 1}.get(x.hierarchy_level, 1),
                x.composition_weight
            ),
            reverse=True
        )
        
        return related_contexts[:5]  # Limit to top 5
    
    @classmethod
    async def _discover_by_intent_patterns(
        cls,
        basket_id: UUID,
        composition_intent: str,
        workspace_id: str,
        max_results: int
    ) -> ContextDiscoveryResult:
        """Discover blocks by intent patterns when no related contexts exist."""
        
        blocks = await cls._get_basket_blocks(basket_id, workspace_id, "blocks")
        
        # Intent-specific block type preferences
        intent_preferences = {
            "strategic_analysis": ["goal", "insight", "constraint"],
            "technical_guide": ["reference", "constraint", "insight"],
            "executive_summary": ["goal", "insight"],
            "creative_brief": ["theme", "insight", "reference"],
            "action_plan": ["goal", "constraint"]
        }
        
        preferred_types = intent_preferences.get(composition_intent, ["insight"])
        
        # Score blocks based on type preference and content
        block_scores = []
        
        for block in blocks:
            score = 0.0
            reasoning_parts = []
            
            # Type preference score
            block_type = block.get("semantic_type", "")
            if block_type in preferred_types:
                type_index = preferred_types.index(block_type)
                score += (len(preferred_types) - type_index) / len(preferred_types)
                reasoning_parts.append(f"Preferred type '{block_type}' for {composition_intent}")
            
            # State bonus
            state = block.get("state", "")
            if state in ["ACCEPTED", "LOCKED", "CONSTANT"]:
                score += 0.2
                reasoning_parts.append(f"Mature block state: {state}")
            
            if score > 0:
                block_scores.append(BlockRelevanceScore(
                    block_id=UUID(block["id"]),
                    relevance_score=score,
                    context_alignment=score,  # Same as relevance for pattern-based
                    composition_value=score,
                    reasoning="; ".join(reasoning_parts),
                    contributing_contexts=[]  # No specific contexts
                ))
        
        # Sort and limit
        block_scores.sort(key=lambda x: x.relevance_score, reverse=True)
        final_results = block_scores[:max_results]
        
        # Calculate average
        avg_relevance = (
            sum(score.relevance_score for score in final_results) / len(final_results)
            if final_results else 0.0
        )
        
        return ContextDiscoveryResult(
            target_context_ids=[],
            discovered_blocks=final_results,
            discovery_summary=f"Discovered {len(final_results)} blocks relevant to {composition_intent} intent using pattern matching",
            total_candidates_analyzed=len(blocks),
            results_returned=len(final_results),
            average_relevance_score=avg_relevance
        )
    
    @classmethod
    def _generate_discovery_summary(
        cls,
        target_contexts: List[ContextItem],
        total_candidates: int,
        results_returned: int,
        avg_relevance: float
    ) -> str:
        """Generate a human-readable discovery summary."""
        
        context_types = [ctx.type for ctx in target_contexts]
        context_summary = ", ".join(set(context_types))
        
        return (
            f"Analyzed {total_candidates} blocks for relevance to {len(target_contexts)} "
            f"target contexts ({context_summary}). Returned {results_returned} relevant blocks "
            f"with average relevance score of {avg_relevance:.2f}."
        )