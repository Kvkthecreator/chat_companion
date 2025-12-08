"""Intent analysis service for composition intelligence profiling."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID, uuid4
import re

from ...models.context import ContextItem, CompositionIntent
from src.schemas.context_composition_schema import IntentAnalysisResult
from ...utils.supabase_client import supabase_client as supabase
from ...utils.db import as_json

logger = logging.getLogger("uvicorn.error")


class IntentAnalyzerService:
    """Service for analyzing composition intent from memory substrate."""
# V3.0 DEPRECATION NOTICE:
# This file contains references to context_items table which was merged into blocks table.
# Entity blocks are now identified by semantic_type='entity'.
# This file is legacy/supporting code - update if actively maintained.

    
    # Enhanced intent pattern library
    INTENT_TAXONOMY = {
        "strategic_analysis": {
            "patterns": [
                "strategic", "strategy", "business strategy", "market analysis", "competitive analysis",
                "swot", "market positioning", "business model", "strategic planning", "growth strategy",
                "market opportunity", "competitive advantage", "strategic objectives", "business goals"
            ],
            "semantic_types": ["goal", "insight", "constraint"],
            "composition_indicators": ["analysis", "assessment", "evaluation", "framework"],
            "audience_signals": ["executives", "leadership", "board", "stakeholders"],
            "complexity": "high"
        },
        "technical_guide": {
            "patterns": [
                "technical", "implementation", "how-to", "guide", "tutorial", "architecture",
                "system design", "development", "engineering", "code", "api", "documentation",
                "setup", "configuration", "deployment", "technical specification"
            ],
            "semantic_types": ["reference", "constraint", "insight"],
            "composition_indicators": ["guide", "manual", "documentation", "specification"],
            "audience_signals": ["developers", "engineers", "technical team", "dev team"],
            "complexity": "high"
        },
        "executive_summary": {
            "patterns": [
                "executive", "summary", "overview", "brief", "highlights", "key points",
                "recommendations", "decisions", "leadership brief", "board presentation",
                "executive overview", "high-level", "strategic summary"
            ],
            "semantic_types": ["goal", "insight"],
            "composition_indicators": ["summary", "brief", "overview", "highlights"],
            "audience_signals": ["executives", "leadership", "c-suite", "board"],
            "complexity": "medium"
        },
        "creative_brief": {
            "patterns": [
                "creative", "design", "brand", "concept", "vision", "aesthetic", "style",
                "creative direction", "design brief", "brand guidelines", "visual identity",
                "creative strategy", "brand positioning", "creative concept"
            ],
            "semantic_types": ["theme", "insight", "reference"],
            "composition_indicators": ["brief", "guidelines", "concept", "direction"],
            "audience_signals": ["designers", "creative team", "marketing", "brand team"],
            "complexity": "medium"
        },
        "research_report": {
            "patterns": [
                "research", "findings", "data", "analysis", "study", "investigation",
                "methodology", "results", "conclusions", "research findings", "data analysis",
                "survey results", "market research", "user research"
            ],
            "semantic_types": ["insight", "reference", "constraint"],
            "composition_indicators": ["report", "findings", "results", "analysis"],
            "audience_signals": ["researchers", "analysts", "stakeholders", "team"],
            "complexity": "high"
        },
        "action_plan": {
            "patterns": [
                "action", "plan", "roadmap", "timeline", "steps", "implementation",
                "execution", "milestones", "deliverables", "action items", "next steps",
                "implementation plan", "project plan", "execution strategy"
            ],
            "semantic_types": ["goal", "constraint"],
            "composition_indicators": ["plan", "roadmap", "timeline", "steps"],
            "audience_signals": ["team", "project team", "stakeholders", "everyone"],
            "complexity": "medium"
        },
        "product_specification": {
            "patterns": [
                "product", "specification", "requirements", "features", "functionality",
                "product requirements", "feature specification", "product brief",
                "product roadmap", "product strategy", "user stories"
            ],
            "semantic_types": ["goal", "constraint", "reference"],
            "composition_indicators": ["specification", "requirements", "brief"],
            "audience_signals": ["product team", "engineers", "stakeholders"],
            "complexity": "high"
        },
        "meeting_summary": {
            "patterns": [
                "meeting", "discussion", "notes", "decisions", "action items",
                "meeting notes", "discussion summary", "meeting outcomes",
                "key decisions", "follow-up actions"
            ],
            "semantic_types": ["insight", "goal"],
            "composition_indicators": ["summary", "notes", "outcomes"],
            "audience_signals": ["attendees", "team", "stakeholders"],
            "complexity": "low"
        }
    }
    
    # Audience classification patterns
    AUDIENCE_TAXONOMY = {
        "executives": {
            "patterns": ["executive", "ceo", "cto", "cfo", "leadership", "c-suite", "board", 
                        "senior management", "directors", "vp", "vice president"],
            "composition_style": "formal",
            "preferred_scope": "overview",
            "detail_level": "high-level"
        },
        "engineers": {
            "patterns": ["engineer", "developer", "programmer", "architect", "technical team",
                        "dev team", "engineering", "software engineer", "backend", "frontend"],
            "composition_style": "detailed",
            "preferred_scope": "deep_dive",
            "detail_level": "technical"
        },
        "designers": {
            "patterns": ["designer", "ux", "ui", "creative", "design team", "visual designer",
                        "product designer", "user experience", "user interface"],
            "composition_style": "conversational",
            "preferred_scope": "overview",
            "detail_level": "visual"
        },
        "product": {
            "patterns": ["product manager", "product team", "pm", "product owner", "product",
                        "product management", "product strategy"],
            "composition_style": "formal",
            "preferred_scope": "deep_dive",
            "detail_level": "strategic"
        },
        "general": {
            "patterns": ["team", "everyone", "all", "general", "stakeholders", "company",
                        "organization", "staff", "employees"],
            "composition_style": "conversational",
            "preferred_scope": "overview",
            "detail_level": "accessible"
        }
    }
    
    @classmethod
    async def analyze_composition_intent(
        cls,
        basket_id: UUID,
        workspace_id: str,
        analysis_depth: str = "comprehensive"
    ) -> IntentAnalysisResult:
        """Analyze composition intent from basket memory."""
        
        # Gather memory substrate
        context_items = await cls._get_basket_contexts(basket_id, workspace_id)
        blocks = await cls._get_basket_blocks(basket_id, workspace_id)
        
        # Extract all textual content
        content_corpus = cls._build_content_corpus(context_items, blocks)
        
        # Analyze intents with weighted scoring
        intent_analysis = cls._analyze_intent_patterns(
            content_corpus, context_items, blocks
        )
        
        # Analyze audience indicators
        audience_analysis = cls._analyze_audience_indicators(content_corpus)
        
        # Analyze style indicators
        style_analysis = cls._analyze_style_indicators(content_corpus, intent_analysis)
        
        # Analyze scope indicators
        scope_analysis = cls._analyze_scope_indicators(content_corpus, blocks)
        
        # Generate reasoning
        reasoning = cls._generate_intent_reasoning(
            intent_analysis, audience_analysis, style_analysis, scope_analysis,
            len(context_items), len(blocks)
        )
        
        return IntentAnalysisResult(
            detected_intents=list(intent_analysis.keys()),
            primary_intent=intent_analysis.get("primary_intent"),
            intent_confidence=intent_analysis.get("confidence", 0.0),
            audience_indicators=audience_analysis.get("detected_audiences", []),
            style_indicators=style_analysis.get("detected_styles", []),
            scope_indicators=scope_analysis.get("detected_scopes", []),
            reasoning=reasoning
        )
    
    @classmethod
    async def profile_composition_intent(
        cls,
        basket_id: UUID,
        workspace_id: str,
        intent_override: Optional[str] = None
    ) -> CompositionIntent:
        """Create a detailed composition intent profile."""
        
        # Get intent analysis
        intent_result = await cls.analyze_composition_intent(basket_id, workspace_id)
        
        # Use override if provided, otherwise use detected primary intent
        primary_intent = intent_override or intent_result.primary_intent or "general_composition"
        
        # Determine audience from analysis
        audience = intent_result.audience_indicators[0] if intent_result.audience_indicators else None
        
        # Determine style from analysis or intent taxonomy
        style = None
        if intent_result.style_indicators:
            style = intent_result.style_indicators[0]
        elif primary_intent in cls.INTENT_TAXONOMY:
            # Infer style from audience
            if audience == "executives":
                style = "formal"
            elif audience == "engineers":
                style = "detailed"
            else:
                style = "conversational"
        
        # Determine scope from analysis
        scope = intent_result.scope_indicators[0] if intent_result.scope_indicators else None
        
        # Determine complexity from intent taxonomy
        complexity_level = "medium"
        if primary_intent in cls.INTENT_TAXONOMY:
            complexity_level = cls.INTENT_TAXONOMY[primary_intent].get("complexity", "medium")
        
        # Build composition metadata
        composition_metadata = {
            "intent_confidence": intent_result.intent_confidence,
            "detected_intents": intent_result.detected_intents,
            "analysis_reasoning": intent_result.reasoning,
            "audience_options": intent_result.audience_indicators,
            "style_options": intent_result.style_indicators,
            "scope_options": intent_result.scope_indicators
        }
        
        return CompositionIntent(
            primary_intent=primary_intent,
            audience=audience,
            style=style,
            scope=scope,
            complexity_level=complexity_level,
            composition_metadata=composition_metadata
        )
    
    @classmethod
    async def suggest_intent_enhancements(
        cls,
        basket_id: UUID,
        workspace_id: str,
        target_intent: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Suggest enhancements to clarify composition intent."""
        
        current_intent = await cls.analyze_composition_intent(basket_id, workspace_id)
        context_items = await cls._get_basket_contexts(basket_id, workspace_id)
        blocks = await cls._get_basket_blocks(basket_id, workspace_id)
        
        suggestions = []
        
        # If intent confidence is low, suggest clarifying contexts
        if current_intent.intent_confidence < 0.6:
            suggestions.append({
                "type": "clarify_intent",
                "priority": "high",
                "description": "Add context items that clarify the primary composition intent",
                "specific_action": f"Create context items with intent-specific language",
                "impact": "Improves composition direction and coherence"
            })
        
        # If no audience detected, suggest audience context
        if not current_intent.audience_indicators:
            suggestions.append({
                "type": "specify_audience",
                "priority": "medium",
                "description": "Add context items specifying the target audience",
                "specific_action": "Create 'audience' type context item describing who this is for",
                "impact": "Enables audience-appropriate composition style and detail level"
            })
        
        # If target intent is specified, suggest alignment
        if target_intent and target_intent != current_intent.primary_intent:
            taxonomy_info = cls.INTENT_TAXONOMY.get(target_intent, {})
            missing_patterns = taxonomy_info.get("patterns", [])
            
            suggestions.append({
                "type": "align_with_target_intent",
                "priority": "high",
                "description": f"Enhance contexts to align with '{target_intent}' intent",
                "specific_action": f"Add context items using language from: {', '.join(missing_patterns[:5])}",
                "impact": "Aligns composition with desired intent"
            })
        
        # Check for missing semantic types for detected intent
        if current_intent.primary_intent in cls.INTENT_TAXONOMY:
            required_types = cls.INTENT_TAXONOMY[current_intent.primary_intent].get("semantic_types", [])
            existing_types = set(ctx.type for ctx in context_items)
            missing_types = set(required_types) - existing_types
            
            if missing_types:
                suggestions.append({
                    "type": "add_required_semantic_types",
                    "priority": "medium",
                    "description": f"Add context items of types: {', '.join(missing_types)}",
                    "specific_action": f"Create context items to cover missing semantic areas",
                    "impact": "Provides complete foundation for the intended composition type"
                })
        
        return suggestions
    
    @classmethod
    def _build_content_corpus(
        cls,
        context_items: List[ContextItem],
        blocks: List[Dict[str, Any]]
    ) -> str:
        """Build a text corpus from all available content."""
        
        content_parts = []
        
        # Add context content with hierarchy weighting
        for ctx in context_items:
            weight = cls._get_hierarchy_weight(ctx.hierarchy_level)
            # Repeat content based on hierarchy weight for analysis
            content_parts.extend([ctx.content.lower()] * weight)
        
        # Add block content
        for block in blocks:
            if block.get("content"):
                content_parts.append(block["content"].lower())
        
        return " ".join(content_parts)
    
    @classmethod
    def _get_hierarchy_weight(cls, hierarchy_level: str) -> int:
        """Get analysis weight based on hierarchy level."""
        weights = {
            "primary": 3,    # Primary contexts get 3x weight
            "secondary": 2,  # Secondary contexts get 2x weight
            "supporting": 1  # Supporting contexts get 1x weight
        }
        return weights.get(hierarchy_level, 1)
    
    @classmethod
    def _analyze_intent_patterns(
        cls,
        content_corpus: str,
        context_items: List[ContextItem],
        blocks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze intent patterns with sophisticated scoring."""
        
        intent_scores = {}
        
        for intent_name, intent_data in cls.INTENT_TAXONOMY.items():
            score = 0.0
            
            # Pattern matching score
            patterns = intent_data.get("patterns", [])
            pattern_matches = sum(1 for pattern in patterns if pattern in content_corpus)
            pattern_score = (pattern_matches / len(patterns)) * 0.4
            
            # Semantic type alignment score
            required_types = set(intent_data.get("semantic_types", []))
            available_types = set(ctx.type for ctx in context_items)
            type_alignment = len(required_types.intersection(available_types)) / len(required_types) if required_types else 0
            type_score = type_alignment * 0.3
            
            # Composition indicator score
            composition_indicators = intent_data.get("composition_indicators", [])
            indicator_matches = sum(1 for indicator in composition_indicators if indicator in content_corpus)
            indicator_score = (indicator_matches / len(composition_indicators)) * 0.2 if composition_indicators else 0
            
            # Audience signal alignment score
            audience_signals = intent_data.get("audience_signals", [])
            audience_matches = sum(1 for signal in audience_signals if signal in content_corpus)
            audience_score = (audience_matches / len(audience_signals)) * 0.1 if audience_signals else 0
            
            # Total score
            total_score = pattern_score + type_score + indicator_score + audience_score
            
            if total_score > 0:
                intent_scores[intent_name] = total_score
        
        # Determine primary intent and confidence
        if intent_scores:
            primary_intent = max(intent_scores.keys(), key=intent_scores.get)
            confidence = min(intent_scores[primary_intent], 1.0)
        else:
            primary_intent = None
            confidence = 0.0
        
        return {
            "scores": intent_scores,
            "primary_intent": primary_intent,
            "confidence": confidence
        }
    
    @classmethod
    def _analyze_audience_indicators(cls, content_corpus: str) -> Dict[str, Any]:
        """Analyze audience indicators from content."""
        
        detected_audiences = []
        audience_scores = {}
        
        for audience_name, audience_data in cls.AUDIENCE_TAXONOMY.items():
            patterns = audience_data.get("patterns", [])
            matches = sum(1 for pattern in patterns if pattern in content_corpus)
            
            if matches > 0:
                score = matches / len(patterns)
                audience_scores[audience_name] = score
                detected_audiences.append(audience_name)
        
        # Sort by score
        detected_audiences.sort(key=lambda x: audience_scores.get(x, 0), reverse=True)
        
        return {
            "detected_audiences": detected_audiences,
            "audience_scores": audience_scores
        }
    
    @classmethod
    def _analyze_style_indicators(
        cls,
        content_corpus: str,
        intent_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze style indicators from content and intent."""
        
        style_patterns = {
            "formal": ["professional", "formal", "business", "corporate", "official", 
                      "structured", "comprehensive", "systematic"],
            "conversational": ["conversational", "casual", "friendly", "accessible", 
                             "informal", "approachable", "easy", "simple"],
            "detailed": ["detailed", "thorough", "comprehensive", "in-depth", 
                        "complete", "extensive", "technical", "specific"]
        }
        
        detected_styles = []
        style_scores = {}
        
        for style_name, patterns in style_patterns.items():
            matches = sum(1 for pattern in patterns if pattern in content_corpus)
            if matches > 0:
                score = matches / len(patterns)
                style_scores[style_name] = score
                detected_styles.append(style_name)
        
        # Infer style from primary intent if not directly detected
        primary_intent = intent_analysis.get("primary_intent")
        if not detected_styles and primary_intent in cls.INTENT_TAXONOMY:
            # Some intents have style implications
            if primary_intent in ["executive_summary", "strategic_analysis"]:
                detected_styles.append("formal")
            elif primary_intent in ["technical_guide", "research_report"]:
                detected_styles.append("detailed")
            else:
                detected_styles.append("conversational")
        
        # Sort by score
        detected_styles.sort(key=lambda x: style_scores.get(x, 0), reverse=True)
        
        return {
            "detected_styles": detected_styles,
            "style_scores": style_scores
        }
    
    @classmethod
    def _analyze_scope_indicators(
        cls,
        content_corpus: str,
        blocks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze scope indicators from content and block count."""
        
        scope_patterns = {
            "overview": ["overview", "summary", "brief", "highlights", "key points", 
                        "high-level", "executive summary", "at a glance"],
            "deep_dive": ["detailed", "comprehensive", "thorough", "in-depth", 
                         "complete", "extensive", "deep dive", "detailed analysis"],
            "action_items": ["action", "steps", "plan", "implementation", "next steps", 
                           "deliverables", "milestones", "roadmap", "execution"]
        }
        
        detected_scopes = []
        scope_scores = {}
        
        for scope_name, patterns in scope_patterns.items():
            matches = sum(1 for pattern in patterns if pattern in content_corpus)
            if matches > 0:
                score = matches / len(patterns)
                scope_scores[scope_name] = score
                detected_scopes.append(scope_name)
        
        # Infer scope from block count if not directly detected
        if not detected_scopes:
            block_count = len(blocks)
            if block_count <= 3:
                detected_scopes.append("overview")
            elif block_count >= 8:
                detected_scopes.append("deep_dive")
            else:
                detected_scopes.append("overview")  # Default
        
        # Sort by score
        detected_scopes.sort(key=lambda x: scope_scores.get(x, 0), reverse=True)
        
        return {
            "detected_scopes": detected_scopes,
            "scope_scores": scope_scores
        }
    
    @classmethod
    def _generate_intent_reasoning(
        cls,
        intent_analysis: Dict[str, Any],
        audience_analysis: Dict[str, Any],
        style_analysis: Dict[str, Any],
        scope_analysis: Dict[str, Any],
        context_count: int,
        block_count: int
    ) -> str:
        """Generate human-readable reasoning for the intent analysis."""
        
        reasoning_parts = []
        
        # Intent analysis reasoning
        primary_intent = intent_analysis.get("primary_intent")
        confidence = intent_analysis.get("confidence", 0.0)
        
        if primary_intent:
            reasoning_parts.append(
                f"Primary composition intent '{primary_intent}' detected with {confidence:.1%} confidence"
            )
        else:
            reasoning_parts.append("No clear primary intent detected from available content")
        
        # Content analysis
        reasoning_parts.append(f"Analyzed {context_count} context items and {block_count} blocks")
        
        # Audience reasoning
        audiences = audience_analysis.get("detected_audiences", [])
        if audiences:
            reasoning_parts.append(f"Target audience appears to be: {', '.join(audiences)}")
        
        # Style reasoning
        styles = style_analysis.get("detected_styles", [])
        if styles:
            reasoning_parts.append(f"Composition style indicators: {', '.join(styles)}")
        
        # Scope reasoning
        scopes = scope_analysis.get("detected_scopes", [])
        if scopes:
            reasoning_parts.append(f"Suggested scope: {', '.join(scopes)}")
        
        return ". ".join(reasoning_parts) + "."
    
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
    async def _get_basket_blocks(cls, basket_id: UUID, workspace_id: str) -> List[Dict[str, Any]]:
        """Get all blocks for a basket."""
        try:
            resp = (
                supabase.table("blocks")
                .select("id,semantic_type,content,state")
                .eq("basket_id", str(basket_id))
                .eq("workspace_id", workspace_id)
                .neq("state", "REJECTED")
                .execute()
            )
            
            return resp.data or []
            
        except Exception as e:
            logger.exception(f"Failed to get basket blocks: {e}")
            return []