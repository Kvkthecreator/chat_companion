"""Basket pattern recognition service for flexible thematic analysis."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from uuid import UUID, uuid4
from collections import Counter
import re

from src.schemas.basket_intelligence_schema import (
    BasketThematicAnalysis, ThematicPattern, PatternAnalysisRequest
)
from ...utils.supabase_client import supabase_client as supabase

logger = logging.getLogger("uvicorn.error")


class BasketPatternRecognitionService:
    """Service for recognizing patterns in basket contents without enforcement."""
# V3.0 DEPRECATION NOTICE:
# This file contains references to context_items table which was merged into blocks table.
# Entity blocks are now identified by semantic_type='entity'.
# This file is legacy/supporting code - update if actively maintained.

    
    # Flexible thematic pattern libraries (accommodating inconsistency)
    THEMATIC_INDICATORS = {
        "product_development": {
            "keywords": ["product", "feature", "development", "roadmap", "release", "mvp", "prototype"],
            "context_types": ["goal", "constraint", "insight"],
            "flexibility": "high"  # Can coexist with many other themes
        },
        "business_strategy": {
            "keywords": ["strategy", "business", "market", "competitive", "growth", "opportunity"],
            "context_types": ["goal", "insight", "audience"],
            "flexibility": "high"
        },
        "technical_implementation": {
            "keywords": ["technical", "architecture", "system", "implementation", "code", "api"],
            "context_types": ["constraint", "reference", "insight"],
            "flexibility": "medium"
        },
        "marketing_campaign": {
            "keywords": ["marketing", "campaign", "brand", "audience", "messaging", "launch"],
            "context_types": ["audience", "theme", "goal"],
            "flexibility": "high"
        },
        "user_research": {
            "keywords": ["user", "research", "feedback", "testing", "interview", "survey"],
            "context_types": ["insight", "audience", "reference"],
            "flexibility": "medium"
        },
        "project_planning": {
            "keywords": ["project", "planning", "timeline", "milestone", "deliverable", "scope"],
            "context_types": ["goal", "constraint", "guideline"],
            "flexibility": "very_high"  # Can span any project
        },
        "creative_direction": {
            "keywords": ["creative", "design", "visual", "brand", "aesthetic", "concept"],
            "context_types": ["theme", "reference", "insight"],
            "flexibility": "medium"
        },
        "operational_process": {
            "keywords": ["process", "workflow", "operations", "efficiency", "optimization"],
            "context_types": ["constraint", "guideline", "reference"],
            "flexibility": "medium"
        }
    }
    
    @classmethod
    async def analyze_basket_patterns(
        cls,
        request: PatternAnalysisRequest,
        workspace_id: str
    ) -> BasketThematicAnalysis:
        """Analyze thematic patterns in basket contents with flexibility."""
        
        # Get basket contents with accommodation for inconsistency
        basket_contents = await cls._get_basket_contents(request.basket_id, workspace_id)
        
        # Extract content for pattern analysis
        content_corpus = cls._build_flexible_content_corpus(basket_contents)
        
        # Discover thematic patterns (accommodating inconsistency)
        discovered_patterns = cls._discover_flexible_patterns(
            content_corpus, basket_contents, request.accommodate_inconsistency
        )
        
        # Calculate content diversity (inconsistency as feature)
        content_diversity = cls._calculate_content_diversity(basket_contents, discovered_patterns)
        
        # Determine coherence level (without judgment)
        coherence_level = cls._assess_coherence_level(discovered_patterns, content_diversity)
        
        # Identify inconsistency areas (accommodation approach)
        inconsistency_areas = cls._identify_inconsistency_areas(
            discovered_patterns, basket_contents, accommodate=True
        )
        
        # Generate thematic insights
        pattern_insights = cls._generate_pattern_insights(
            discovered_patterns, inconsistency_areas, content_diversity
        )
        
        # Build dominant themes list
        dominant_themes, theme_confidence = cls._extract_dominant_themes(discovered_patterns)
        
        # Generate human-friendly summary
        thematic_summary = cls._generate_thematic_summary(
            dominant_themes, inconsistency_areas, content_diversity
        )
        
        return BasketThematicAnalysis(
            basket_id=request.basket_id,
            dominant_themes=dominant_themes,
            theme_confidence=theme_confidence,
            discovered_patterns=discovered_patterns,
            content_diversity=content_diversity,
            coherence_level=coherence_level,
            inconsistency_areas=inconsistency_areas,
            thematic_summary=thematic_summary,
            pattern_insights=pattern_insights,
            analysis_metadata={
                "analysis_depth": request.analysis_depth,
                "accommodation_enabled": request.accommodate_inconsistency,
                "total_content_items": len(basket_contents["all_items"]),
                "pattern_discovery_method": "flexible_accommodation",
                "inconsistency_tolerance": "high"
            }
        )
    
    @classmethod
    async def detect_emergent_themes(
        cls,
        basket_id: UUID,
        workspace_id: str,
        sensitivity: str = "medium"
    ) -> List[ThematicPattern]:
        """Detect emergent themes that don't fit standard patterns."""
        
        basket_contents = await cls._get_basket_contents(basket_id, workspace_id)
        content_corpus = cls._build_flexible_content_corpus(basket_contents)
        
        # Extract emergent patterns through keyword frequency and co-occurrence
        emergent_patterns = []
        
        # Get all text content
        all_text = " ".join([
            item.get("content", "") for item in basket_contents["all_items"]
        ]).lower()
        
        # Extract meaningful words (exclude common words)
        words = re.findall(r'\b[a-zA-Z]{4,}\b', all_text)
        excluded_words = {
            "this", "that", "with", "from", "they", "will", "have", "been",
            "were", "said", "each", "which", "their", "would", "there",
            "could", "should", "more", "very", "what", "know", "just",
            "first", "also", "after", "back", "other", "many", "than",
            "then", "them", "these", "some", "time", "into", "only",
            "over", "think", "about", "through", "where", "being"
        }
        
        meaningful_words = [w for w in words if w not in excluded_words and len(w) > 4]
        
        # Find frequently occurring words as potential themes
        word_freq = Counter(meaningful_words)
        threshold = max(2, len(basket_contents["all_items"]) // 3)  # Flexible threshold
        
        for word, count in word_freq.most_common(10):
            if count >= threshold:
                # Check if this forms a coherent theme
                related_words = cls._find_related_words(word, meaningful_words, all_text)
                
                emergent_patterns.append(ThematicPattern(
                    pattern_id=f"emergent_{word}_{uuid4().hex[:8]}",
                    theme_name=word.title(),
                    keywords=[word] + related_words[:5],
                    confidence=min(count / len(meaningful_words), 1.0),
                    evidence_sources=[],  # Would be populated with source IDs
                    pattern_strength="emerging",
                    cross_document=count > len(basket_contents["documents"])
                ))
        
        return emergent_patterns
    
    @classmethod
    async def _get_basket_contents(
        cls,
        basket_id: UUID,
        workspace_id: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get all contents of a basket for pattern analysis."""
        
        contents = {
            "documents": [],
            "blocks": [],
            "context_items": [],
            "raw_dumps": [],
            "all_items": []
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
            
            # Combine all items for comprehensive analysis
            contents["all_items"] = (
                contents["documents"] + 
                contents["blocks"] + 
                contents["context_items"] + 
                contents["raw_dumps"]
            )
            
        except Exception as e:
            logger.exception(f"Failed to get basket contents: {e}")
        
        return contents
    
    @classmethod
    def _build_flexible_content_corpus(
        cls,
        basket_contents: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, str]:
        """Build content corpus that accommodates diverse content types."""
        
        corpus = {
            "all_content": "",
            "documents_content": "",
            "blocks_content": "",
            "contexts_content": "",
            "dumps_content": ""
        }
        
        # Document content
        doc_texts = []
        for doc in basket_contents["documents"]:
            content = doc.get("content_raw", "") or doc.get("title", "")
            doc_texts.append(content)
        corpus["documents_content"] = " ".join(doc_texts)
        
        # Block content
        block_texts = []
        for block in basket_contents["blocks"]:
            block_texts.append(block.get("content", ""))
        corpus["blocks_content"] = " ".join(block_texts)
        
        # Context content
        context_texts = []
        for context in basket_contents["context_items"]:
            context_texts.append(context.get("content", ""))
        corpus["contexts_content"] = " ".join(context_texts)
        
        # Raw dump content
        dump_texts = []
        for dump in basket_contents["raw_dumps"]:
            dump_texts.append(dump.get("content", ""))
        corpus["dumps_content"] = " ".join(dump_texts)
        
        # Combined content
        corpus["all_content"] = " ".join([
            corpus["documents_content"],
            corpus["blocks_content"], 
            corpus["contexts_content"],
            corpus["dumps_content"]
        ])
        
        return corpus
    
    @classmethod
    def _discover_flexible_patterns(
        cls,
        content_corpus: Dict[str, str],
        basket_contents: Dict[str, List[Dict[str, Any]]],
        accommodate_inconsistency: bool = True
    ) -> List[ThematicPattern]:
        """Discover thematic patterns with accommodation for inconsistency."""
        
        patterns = []
        all_content = content_corpus["all_content"].lower()
        
        # Check each thematic indicator
        for theme_name, theme_data in cls.THEMATIC_INDICATORS.items():
            keywords = theme_data["keywords"]
            flexibility = theme_data["flexibility"]
            
            # Count keyword occurrences
            keyword_matches = sum(1 for keyword in keywords if keyword in all_content)
            
            if keyword_matches > 0:
                # Calculate confidence with flexibility adjustment
                base_confidence = keyword_matches / len(keywords)
                
                # Adjust confidence based on flexibility
                flexibility_multiplier = {
                    "very_high": 1.2,
                    "high": 1.1,
                    "medium": 1.0,
                    "low": 0.8
                }.get(flexibility, 1.0)
                
                confidence = min(base_confidence * flexibility_multiplier, 1.0)
                
                # Check cross-document presence
                cross_document = cls._check_cross_document_presence(
                    keywords, basket_contents["documents"]
                )
                
                # Determine pattern strength
                if confidence > 0.7:
                    strength = "strong"
                elif confidence > 0.4:
                    strength = "medium"
                else:
                    strength = "weak"
                
                # Find evidence sources
                evidence_sources = cls._find_evidence_sources(
                    keywords, basket_contents
                )
                
                patterns.append(ThematicPattern(
                    pattern_id=f"{theme_name}_{uuid4().hex[:8]}",
                    theme_name=theme_name.replace("_", " ").title(),
                    keywords=keywords,
                    confidence=confidence,
                    evidence_sources=evidence_sources,
                    pattern_strength=strength,
                    cross_document=cross_document
                ))
        
        # Sort by confidence but don't filter out weak patterns if accommodating inconsistency
        patterns.sort(key=lambda x: x.confidence, reverse=True)
        
        if accommodate_inconsistency:
            # Keep all patterns, even weak ones - they might indicate emerging themes
            return patterns
        else:
            # Only return patterns with reasonable confidence
            return [p for p in patterns if p.confidence > 0.3]
    
    @classmethod
    def _calculate_content_diversity(
        cls,
        basket_contents: Dict[str, List[Dict[str, Any]]],
        patterns: List[ThematicPattern]
    ) -> float:
        """Calculate content diversity as a positive metric (not a problem)."""
        
        # Count different types of content
        content_type_count = sum(1 for content_type, items in basket_contents.items() 
                                if content_type != "all_items" and len(items) > 0)
        
        # Count different semantic types in blocks
        semantic_types = set()
        for block in basket_contents["blocks"]:
            semantic_types.add(block.get("semantic_type", "unknown"))
        
        # Count different context types
        context_types = set()
        for context in basket_contents["context_items"]:
            context_types.add(context.get("type", "unknown"))
        
        # Count thematic diversity
        strong_patterns = len([p for p in patterns if p.pattern_strength == "strong"])
        weak_patterns = len([p for p in patterns if p.pattern_strength == "weak"])
        
        # Diversity factors
        type_diversity = min(content_type_count / 4, 1.0)  # Max 4 content types
        semantic_diversity = min(len(semantic_types) / 6, 1.0)  # Normalize against expected types
        context_diversity = min(len(context_types) / 8, 1.0)  # Normalize against context types
        thematic_diversity = min((strong_patterns + weak_patterns * 0.5) / 5, 1.0)
        
        # Calculate overall diversity (high diversity is good, not bad)
        diversity_score = (
            type_diversity * 0.25 +
            semantic_diversity * 0.25 +
            context_diversity * 0.25 +
            thematic_diversity * 0.25
        )
        
        return diversity_score
    
    @classmethod
    def _assess_coherence_level(
        cls,
        patterns: List[ThematicPattern],
        content_diversity: float
    ) -> str:
        """Assess coherence level without judgment (descriptive, not prescriptive)."""
        
        if not patterns:
            return "emerging"  # Neutral term instead of "low"
        
        strong_patterns = len([p for p in patterns if p.pattern_strength == "strong"])
        cross_doc_patterns = len([p for p in patterns if p.cross_document])
        
        # High coherence: strong patterns across documents
        if strong_patterns >= 2 and cross_doc_patterns >= 1:
            return "high"
        
        # Medium coherence: some strong patterns
        elif strong_patterns >= 1:
            return "medium"
        
        # Mixed coherence: diverse patterns (often valuable for creative projects)
        elif content_diversity > 0.6:
            return "mixed"
        
        # Low coherence: few patterns detected
        else:
            return "emerging"
    
    @classmethod
    def _identify_inconsistency_areas(
        cls,
        patterns: List[ThematicPattern],
        basket_contents: Dict[str, List[Dict[str, Any]]],
        accommodate: bool = True
    ) -> List[str]:
        """Identify inconsistency areas with accommodation approach."""
        
        inconsistencies = []
        
        # Check for conflicting document types
        doc_types = [doc.get("document_type", "") for doc in basket_contents["documents"]]
        unique_doc_types = set(doc_types)
        
        if len(unique_doc_types) > 2:
            if accommodate:
                inconsistencies.append(f"Diverse document types ({len(unique_doc_types)}) - indicates multi-faceted project")
            else:
                inconsistencies.append("Multiple document types may indicate scope confusion")
        
        # Check for semantic type diversity in blocks
        semantic_types = set(block.get("semantic_type", "") for block in basket_contents["blocks"])
        
        if len(semantic_types) > 4:
            if accommodate:
                inconsistencies.append(f"Rich semantic diversity ({len(semantic_types)} types) - comprehensive exploration")
            else:
                inconsistencies.append("High semantic diversity may indicate unfocused content")
        
        # Check for competing strong patterns
        strong_patterns = [p for p in patterns if p.pattern_strength == "strong"]
        
        if len(strong_patterns) > 3:
            if accommodate:
                inconsistencies.append(f"Multiple strong themes ({len(strong_patterns)}) - complex project with various dimensions")
            else:
                inconsistencies.append("Too many strong patterns may indicate conflicting directions")
        
        # Check for context scope variety
        context_scopes = set(ctx.get("scope", "LOCAL") for ctx in basket_contents["context_items"])
        
        if len(context_scopes) > 2:
            if accommodate:
                inconsistencies.append(f"Multi-scope contexts ({len(context_scopes)} scopes) - connects local work to broader context")
            else:
                inconsistencies.append("Mixed context scopes may indicate unclear boundaries")
        
        return inconsistencies
    
    @classmethod
    def _generate_pattern_insights(
        cls,
        patterns: List[ThematicPattern],
        inconsistency_areas: List[str],
        content_diversity: float
    ) -> List[str]:
        """Generate insights about discovered patterns."""
        
        insights = []
        
        if not patterns:
            insights.append("This basket is in early exploration phase with emerging themes")
            return insights
        
        strong_patterns = [p for p in patterns if p.pattern_strength == "strong"]
        cross_doc_patterns = [p for p in patterns if p.cross_document]
        
        if strong_patterns:
            theme_names = [p.theme_name for p in strong_patterns]
            insights.append(f"Strong thematic focus on: {', '.join(theme_names)}")
        
        if cross_doc_patterns:
            insights.append(f"{len(cross_doc_patterns)} themes span multiple documents, showing good integration")
        
        if content_diversity > 0.7:
            insights.append("High content diversity indicates comprehensive project exploration")
        
        if len(inconsistency_areas) > 0:
            insights.append(f"Contains {len(inconsistency_areas)} areas of creative complexity")
        
        # Pattern combination insights
        pattern_names = [p.theme_name.lower() for p in patterns]
        
        if "product development" in pattern_names and "marketing campaign" in pattern_names:
            insights.append("Product and marketing themes suggest launch preparation")
        
        if "technical implementation" in pattern_names and "business strategy" in pattern_names:
            insights.append("Technical and business themes indicate comprehensive solution development")
        
        if "user research" in pattern_names and "creative direction" in pattern_names:
            insights.append("Research and creative themes suggest user-centered design approach")
        
        return insights
    
    @classmethod
    def _extract_dominant_themes(
        cls,
        patterns: List[ThematicPattern]
    ) -> tuple[List[str], Dict[str, float]]:
        """Extract dominant themes and their confidence levels."""
        
        # Sort patterns by confidence
        sorted_patterns = sorted(patterns, key=lambda x: x.confidence, reverse=True)
        
        # Take top themes (but accommodate all themes present)
        dominant_themes = []
        theme_confidence = {}
        
        for pattern in sorted_patterns[:5]:  # Top 5 themes
            theme_name = pattern.theme_name
            dominant_themes.append(theme_name)
            theme_confidence[theme_name] = pattern.confidence
        
        return dominant_themes, theme_confidence
    
    @classmethod
    def _generate_thematic_summary(
        cls,
        dominant_themes: List[str],
        inconsistency_areas: List[str],
        content_diversity: float
    ) -> str:
        """Generate human-friendly thematic summary."""
        
        if not dominant_themes:
            return "This basket contains emerging content with developing themes. The diversity suggests active exploration of ideas."
        
        summary_parts = []
        
        # Theme summary
        if len(dominant_themes) == 1:
            summary_parts.append(f"This basket focuses primarily on {dominant_themes[0].lower()}")
        elif len(dominant_themes) <= 3:
            themes_text = ", ".join(dominant_themes[:-1]) + f" and {dominant_themes[-1]}"
            summary_parts.append(f"This basket spans {themes_text.lower()}")
        else:
            summary_parts.append(f"This basket covers {len(dominant_themes)} main themes including {dominant_themes[0].lower()}")
        
        # Diversity commentary
        if content_diversity > 0.7:
            summary_parts.append("The high content diversity suggests a comprehensive, multi-faceted project")
        elif content_diversity > 0.4:
            summary_parts.append("The moderate diversity indicates balanced exploration across themes")
        else:
            summary_parts.append("The focused content suggests concentrated work on specific themes")
        
        # Inconsistency accommodation
        if inconsistency_areas:
            summary_parts.append(f"The {len(inconsistency_areas)} areas of complexity add creative richness to the project")
        
        return ". ".join(summary_parts) + "."
    
    @classmethod
    def _check_cross_document_presence(
        cls,
        keywords: List[str],
        documents: List[Dict[str, Any]]
    ) -> bool:
        """Check if keywords appear across multiple documents."""
        
        if len(documents) <= 1:
            return False
        
        doc_matches = 0
        for doc in documents:
            content = (doc.get("content_raw", "") + " " + doc.get("title", "")).lower()
            if any(keyword in content for keyword in keywords):
                doc_matches += 1
        
        return doc_matches >= 2
    
    @classmethod
    def _find_evidence_sources(
        cls,
        keywords: List[str],
        basket_contents: Dict[str, List[Dict[str, Any]]]
    ) -> List[str]:
        """Find sources that provide evidence for patterns."""
        
        evidence = []
        
        # Check documents
        for doc in basket_contents["documents"]:
            content = (doc.get("content_raw", "") + " " + doc.get("title", "")).lower()
            if any(keyword in content for keyword in keywords):
                evidence.append(f"document:{doc.get('id')}")
        
        # Check blocks
        for block in basket_contents["blocks"]:
            content = block.get("content", "").lower()
            if any(keyword in content for keyword in keywords):
                evidence.append(f"block:{block.get('id')}")
        
        # Check contexts
        for context in basket_contents["context_items"]:
            content = context.get("content", "").lower()
            if any(keyword in content for keyword in keywords):
                evidence.append(f"context:{context.get('id')}")
        
        return evidence[:10]  # Limit evidence list
    
    @classmethod
    def _find_related_words(
        cls,
        target_word: str,
        word_list: List[str],
        full_text: str
    ) -> List[str]:
        """Find words that frequently appear near the target word."""
        
        related = []
        
        # Simple co-occurrence detection
        sentences = full_text.split('.')
        target_sentences = [s for s in sentences if target_word in s.lower()]
        
        if target_sentences:
            related_words = []
            for sentence in target_sentences:
                words = re.findall(r'\b[a-zA-Z]{4,}\b', sentence.lower())
                related_words.extend([w for w in words if w != target_word and w in word_list])
            
            # Get most common related words
            if related_words:
                word_counts = Counter(related_words)
                related = [word for word, count in word_counts.most_common(5)]
        
        return related