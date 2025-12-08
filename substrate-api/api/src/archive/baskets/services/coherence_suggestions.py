"""Coherence suggestions service for gentle basket improvement guidance."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4

from src.schemas.basket_intelligence_schema import (
    BasketCoherenceSuggestions, CoherenceSuggestion, BasketThematicAnalysis
)
from .pattern_recognition import BasketPatternRecognitionService
from ...utils.supabase_client import supabase_client as supabase

logger = logging.getLogger("uvicorn.error")


class CoherenceSuggestionsService:
    """Service for generating gentle, non-enforcing coherence suggestions."""
# V3.0 DEPRECATION NOTICE:
# This file contains references to context_items table which was merged into blocks table.
# Entity blocks are now identified by semantic_type='entity'.
# This file is legacy/supporting code - update if actively maintained.

    
    # Gentle suggestion templates that emphasize user choice
    SUGGESTION_TEMPLATES = {
        "context_link": {
            "description_template": "You might find it helpful to link {item_a} and {item_b}",
            "reasoning_template": "These items seem related through {connection_type}",
            "action_template": "Consider adding a context_item that connects these concepts",
            "benefit_template": "This could help show the relationship between your ideas",
            "effort": "low",
            "user_choice_emphasis": "Only if you think it would be useful"
        },
        "theme_clarification": {
            "description_template": "Your {theme_name} theme could be made more explicit",
            "reasoning_template": "This theme appears in multiple places but isn't clearly defined",
            "action_template": "You could add a theme context_item to make this connection clearer",
            "benefit_template": "This might help others understand your project's direction",
            "effort": "low",
            "user_choice_emphasis": "This is just an idea - your current approach works fine too"
        },
        "document_connection": {
            "description_template": "Your documents on {topic_a} and {topic_b} seem related",
            "reasoning_template": "Both documents mention {shared_concepts}",
            "action_template": "You might want to add context that shows how they connect",
            "benefit_template": "This could help show the bigger picture of your work",
            "effort": "medium",
            "user_choice_emphasis": "Only if seeing these connections would be valuable to you"
        },
        "scope_organization": {
            "description_template": "Your contexts span different scopes - that might be intentional",
            "reasoning_template": "You have {local_count} local and {global_count} global contexts",
            "action_template": "If you want, you could organize them by scope for clarity",
            "benefit_template": "This might make it easier to see what's project-specific vs reusable",
            "effort": "medium",
            "user_choice_emphasis": "Your current organization might already work perfectly for you"
        },
        "semantic_grouping": {
            "description_template": "You have several {semantic_type} items that could be grouped",
            "reasoning_template": "These items share similar themes or purposes",
            "action_template": "You could create a category context to group them if helpful",
            "benefit_template": "This might make it easier to see patterns in your thinking",
            "effort": "low",
            "user_choice_emphasis": "Only if grouping would be helpful for your workflow"
        },
        "cross_reference": {
            "description_template": "Some of your items reference similar external sources",
            "reasoning_template": "Multiple items mention {external_reference}",
            "action_template": "You could create a reference context to capture that source",
            "benefit_template": "This might make it easier to track important references",
            "effort": "low",
            "user_choice_emphasis": "This is just a convenience suggestion"
        }
    }
    
    @classmethod
    async def generate_gentle_suggestions(
        cls,
        basket_id: UUID,
        workspace_id: str,
        thematic_analysis: Optional[BasketThematicAnalysis] = None,
        suggestion_style: str = "gentle"
    ) -> BasketCoherenceSuggestions:
        """Generate gentle, non-enforcing suggestions for basket coherence."""
        
        # Get thematic analysis if not provided
        if not thematic_analysis:
            from src.schemas.basket_intelligence_schema import PatternAnalysisRequest
            
            analysis_request = PatternAnalysisRequest(
                basket_id=basket_id,
                accommodate_inconsistency=True,
                suggestion_gentleness=suggestion_style
            )
            thematic_analysis = await BasketPatternRecognitionService.analyze_basket_patterns(
                analysis_request, workspace_id
            )
        
        # Get basket contents for suggestion generation
        basket_contents = await cls._get_basket_contents(basket_id, workspace_id)
        
        # Generate different types of gentle suggestions
        suggestions = []
        
        # Context linking suggestions
        link_suggestions = await cls._suggest_context_links(
            basket_contents, thematic_analysis, suggestion_style
        )
        suggestions.extend(link_suggestions)
        
        # Theme clarification suggestions
        theme_suggestions = cls._suggest_theme_clarifications(
            thematic_analysis, suggestion_style
        )
        suggestions.extend(theme_suggestions)
        
        # Document connection suggestions
        doc_suggestions = cls._suggest_document_connections(
            basket_contents, thematic_analysis, suggestion_style
        )
        suggestions.extend(doc_suggestions)
        
        # Scope organization suggestions
        scope_suggestions = cls._suggest_scope_organization(
            basket_contents, suggestion_style
        )
        suggestions.extend(scope_suggestions)
        
        # Semantic grouping suggestions
        semantic_suggestions = cls._suggest_semantic_grouping(
            basket_contents, suggestion_style
        )
        suggestions.extend(semantic_suggestions)
        
        # Cross-reference suggestions
        ref_suggestions = cls._suggest_cross_references(
            basket_contents, suggestion_style
        )
        suggestions.extend(ref_suggestions)
        
        # Filter and prioritize suggestions gently
        filtered_suggestions = cls._filter_suggestions_gently(suggestions)
        
        # Determine overall priority (keeping it low-pressure)
        priority_level = cls._determine_gentle_priority(filtered_suggestions)
        
        # Generate accommodation-focused reasoning
        suggestion_reasoning = cls._generate_accommodation_reasoning(
            thematic_analysis, len(filtered_suggestions)
        )
        
        return BasketCoherenceSuggestions(
            basket_id=basket_id,
            suggestions=filtered_suggestions,
            priority_level=priority_level,
            user_choice_required=False,  # Never require user action
            suggestion_reasoning=suggestion_reasoning,
            accommodation_note="Your basket works fine as-is. These are just ideas if you're interested.",
            total_suggestions=len(filtered_suggestions),
            high_value_suggestions=len([s for s in filtered_suggestions if s.priority == "medium"]),  # No "high" priority suggestions
            suggestions_metadata={
                "suggestion_style": suggestion_style,
                "accommodation_focus": True,
                "user_autonomy_preserved": True,
                "pressure_level": "none",
                "basket_respected_as_is": True
            }
        )
    
    @classmethod
    async def suggest_improvements_if_interested(
        cls,
        basket_id: UUID,
        workspace_id: str,
        user_explicitly_requested: bool = False
    ) -> BasketCoherenceSuggestions:
        """Generate suggestions only if user is explicitly interested."""
        
        if not user_explicitly_requested:
            # Return minimal, very gentle suggestions
            return BasketCoherenceSuggestions(
                basket_id=basket_id,
                suggestions=[],
                priority_level="none",
                user_choice_required=False,
                suggestion_reasoning="No suggestions generated - your basket is working fine",
                accommodation_note="Your basket is working perfectly as-is. Let us know if you'd ever like ideas for organization."
            )
        
        # User explicitly asked, so provide thoughtful suggestions
        return await cls.generate_gentle_suggestions(
            basket_id, workspace_id, suggestion_style="helpful"
        )
    
    @classmethod
    async def _get_basket_contents(
        cls,
        basket_id: UUID,
        workspace_id: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get basket contents for suggestion analysis."""
        
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
            logger.exception(f"Failed to get basket contents for suggestions: {e}")
        
        return contents
    
    @classmethod
    async def _suggest_context_links(
        cls,
        basket_contents: Dict[str, List[Dict[str, Any]]],
        thematic_analysis: BasketThematicAnalysis,
        style: str
    ) -> List[CoherenceSuggestion]:
        """Suggest gentle context links between related items."""
        
        suggestions = []
        
        # Find unlinked blocks that share themes
        blocks = basket_contents["blocks"]
        context_items = basket_contents["context_items"]
        
        # Get blocks without context items
        linked_blocks = set(ctx.get("block_id") for ctx in context_items if ctx.get("block_id"))
        unlinked_blocks = [b for b in blocks if b.get("id") not in linked_blocks]
        
        # Find pairs of unlinked blocks with similar content
        for i, block_a in enumerate(unlinked_blocks):
            for block_b in unlinked_blocks[i+1:]:
                similarity = cls._calculate_content_similarity(
                    block_a.get("content", ""),
                    block_b.get("content", "")
                )
                
                if similarity > 0.4:  # Moderate similarity threshold
                    template = cls.SUGGESTION_TEMPLATES["context_link"]
                    
                    suggestion = CoherenceSuggestion(
                        suggestion_id=f"link_{block_a['id']}_{block_b['id']}",
                        suggestion_type="context_link",
                        priority="low",
                        description=template["description_template"].format(
                            item_a=f"block about '{block_a.get('content', '')[:30]}...'",
                            item_b=f"block about '{block_b.get('content', '')[:30]}...'"
                        ),
                        reasoning=template["reasoning_template"].format(
                            connection_type="similar themes or concepts"
                        ),
                        suggested_action=template["action_template"],
                        target_objects=[UUID(block_a["id"]), UUID(block_b["id"])],
                        expected_benefit=template["benefit_template"],
                        effort_estimate=template["effort"],
                        user_choice_emphasis=template["user_choice_emphasis"]
                    )
                    suggestions.append(suggestion)
        
        return suggestions[:3]  # Limit to avoid overwhelming
    
    @classmethod
    def _suggest_theme_clarifications(
        cls,
        thematic_analysis: BasketThematicAnalysis,
        style: str
    ) -> List[CoherenceSuggestion]:
        """Suggest gentle theme clarifications."""
        
        suggestions = []
        
        # Look for themes that could be made more explicit
        for pattern in thematic_analysis.discovered_patterns:
            if pattern.pattern_strength == "medium" and pattern.confidence > 0.5:
                template = cls.SUGGESTION_TEMPLATES["theme_clarification"]
                
                suggestion = CoherenceSuggestion(
                    suggestion_id=f"theme_{pattern.pattern_id}",
                    suggestion_type="theme_clarification",
                    priority="low",
                    description=template["description_template"].format(
                        theme_name=pattern.theme_name
                    ),
                    reasoning=template["reasoning_template"],
                    suggested_action=template["action_template"],
                    target_objects=[],
                    expected_benefit=template["benefit_template"],
                    effort_estimate=template["effort"],
                    user_choice_emphasis=template["user_choice_emphasis"]
                )
                suggestions.append(suggestion)
        
        return suggestions[:2]  # Keep it gentle
    
    @classmethod
    def _suggest_document_connections(
        cls,
        basket_contents: Dict[str, List[Dict[str, Any]]],
        thematic_analysis: BasketThematicAnalysis,
        style: str
    ) -> List[CoherenceSuggestion]:
        """Suggest gentle document connections."""
        
        suggestions = []
        documents = basket_contents["documents"]
        
        if len(documents) < 2:
            return suggestions
        
        # Find documents that might benefit from connection
        for i, doc_a in enumerate(documents):
            for doc_b in documents[i+1:]:
                # Check for shared concepts
                content_a = (doc_a.get("content_raw", "") + " " + doc_a.get("title", "")).lower()
                content_b = (doc_b.get("content_raw", "") + " " + doc_b.get("title", "")).lower()
                
                shared_concepts = cls._find_shared_concepts(content_a, content_b)
                
                if shared_concepts:
                    template = cls.SUGGESTION_TEMPLATES["document_connection"]
                    
                    suggestion = CoherenceSuggestion(
                        suggestion_id=f"doc_connect_{doc_a['id']}_{doc_b['id']}",
                        suggestion_type="document_connection",
                        priority="low",
                        description=template["description_template"].format(
                            topic_a=doc_a.get("title", "document")[:20],
                            topic_b=doc_b.get("title", "document")[:20]
                        ),
                        reasoning=template["reasoning_template"].format(
                            shared_concepts=", ".join(shared_concepts[:3])
                        ),
                        suggested_action=template["action_template"],
                        target_objects=[UUID(doc_a["id"]), UUID(doc_b["id"])],
                        expected_benefit=template["benefit_template"],
                        effort_estimate=template["effort"],
                        user_choice_emphasis=template["user_choice_emphasis"]
                    )
                    suggestions.append(suggestion)
        
        return suggestions[:2]  # Keep it manageable
    
    @classmethod
    def _suggest_scope_organization(
        cls,
        basket_contents: Dict[str, List[Dict[str, Any]]],
        style: str
    ) -> List[CoherenceSuggestion]:
        """Suggest gentle scope organization."""
        
        suggestions = []
        context_items = basket_contents["context_items"]
        
        # Count different scopes
        scope_counts = {}
        for ctx in context_items:
            scope = ctx.get("scope", "LOCAL")
            scope_counts[scope] = scope_counts.get(scope, 0) + 1
        
        # Only suggest if there's meaningful scope diversity
        if len(scope_counts) > 2 and sum(scope_counts.values()) > 5:
            template = cls.SUGGESTION_TEMPLATES["scope_organization"]
            
            suggestion = CoherenceSuggestion(
                suggestion_id=f"scope_org_{uuid4().hex[:8]}",
                suggestion_type="scope_organization",
                priority="low",
                description=template["description_template"],
                reasoning=template["reasoning_template"].format(
                    local_count=scope_counts.get("LOCAL", 0),
                    global_count=scope_counts.get("GLOBAL", 0)
                ),
                suggested_action=template["action_template"],
                target_objects=[],
                expected_benefit=template["benefit_template"],
                effort_estimate=template["effort"],
                user_choice_emphasis=template["user_choice_emphasis"]
            )
            suggestions.append(suggestion)
        
        return suggestions
    
    @classmethod
    def _suggest_semantic_grouping(
        cls,
        basket_contents: Dict[str, List[Dict[str, Any]]],
        style: str
    ) -> List[CoherenceSuggestion]:
        """Suggest gentle semantic grouping."""
        
        suggestions = []
        blocks = basket_contents["blocks"]
        
        # Count semantic types
        semantic_counts = {}
        for block in blocks:
            semantic_type = block.get("semantic_type", "unknown")
            semantic_counts[semantic_type] = semantic_counts.get(semantic_type, 0) + 1
        
        # Suggest grouping for types with multiple instances
        for semantic_type, count in semantic_counts.items():
            if count >= 3 and semantic_type != "unknown":
                template = cls.SUGGESTION_TEMPLATES["semantic_grouping"]
                
                suggestion = CoherenceSuggestion(
                    suggestion_id=f"semantic_{semantic_type}_{uuid4().hex[:8]}",
                    suggestion_type="semantic_grouping",
                    priority="low",
                    description=template["description_template"].format(
                        semantic_type=semantic_type
                    ),
                    reasoning=template["reasoning_template"],
                    suggested_action=template["action_template"],
                    target_objects=[],
                    expected_benefit=template["benefit_template"],
                    effort_estimate=template["effort"],
                    user_choice_emphasis=template["user_choice_emphasis"]
                )
                suggestions.append(suggestion)
        
        return suggestions[:2]  # Limit suggestions
    
    @classmethod
    def _suggest_cross_references(
        cls,
        basket_contents: Dict[str, List[Dict[str, Any]]],
        style: str
    ) -> List[CoherenceSuggestion]:
        """Suggest gentle cross-reference organization."""
        
        suggestions = []
        
        # Look for common external references across items
        all_content = []
        for items in basket_contents.values():
            for item in items:
                content = item.get("content", "") or item.get("content_raw", "")
                all_content.append(content)
        
        # Simple external reference detection (URLs, papers, etc.)
        import re
        
        combined_content = " ".join(all_content)
        
        # Find URLs
        urls = re.findall(r'https?://[^\s]+', combined_content)
        url_counts = {}
        for url in urls:
            base_url = url.split('/')[2] if '/' in url else url
            url_counts[base_url] = url_counts.get(base_url, 0) + 1
        
        # Suggest reference organization for frequently mentioned sources
        for source, count in url_counts.items():
            if count >= 2:
                template = cls.SUGGESTION_TEMPLATES["cross_reference"]
                
                suggestion = CoherenceSuggestion(
                    suggestion_id=f"ref_{source.replace('.', '_')}",
                    suggestion_type="cross_reference",
                    priority="low",
                    description=template["description_template"],
                    reasoning=template["reasoning_template"].format(
                        external_reference=source
                    ),
                    suggested_action=template["action_template"],
                    target_objects=[],
                    expected_benefit=template["benefit_template"],
                    effort_estimate=template["effort"],
                    user_choice_emphasis=template["user_choice_emphasis"]
                )
                suggestions.append(suggestion)
        
        return suggestions[:1]  # Very limited to avoid spam
    
    @classmethod
    def _filter_suggestions_gently(
        cls,
        suggestions: List[CoherenceSuggestion]
    ) -> List[CoherenceSuggestion]:
        """Filter suggestions with gentle approach (keeping most)."""
        
        # Sort by priority but keep all low-priority suggestions
        suggestions.sort(key=lambda x: {"medium": 1, "low": 2}.get(x.priority, 3))
        
        # Limit total suggestions to avoid overwhelming
        max_suggestions = 8
        
        # Ensure variety in suggestion types
        filtered = []
        type_counts = {}
        
        for suggestion in suggestions:
            suggestion_type = suggestion.suggestion_type
            type_count = type_counts.get(suggestion_type, 0)
            
            # Allow up to 2 of each type
            if type_count < 2 and len(filtered) < max_suggestions:
                filtered.append(suggestion)
                type_counts[suggestion_type] = type_count + 1
        
        return filtered
    
    @classmethod
    def _determine_gentle_priority(
        cls,
        suggestions: List[CoherenceSuggestion]
    ) -> str:
        """Determine overall priority keeping it gentle."""
        
        if not suggestions:
            return "none"
        
        # Count medium priority suggestions
        medium_count = len([s for s in suggestions if s.priority == "medium"])
        
        if medium_count >= 3:
            return "medium"  # Never use "high" to avoid pressure
        elif medium_count >= 1:
            return "low-medium"
        else:
            return "low"
    
    @classmethod
    def _generate_accommodation_reasoning(
        cls,
        thematic_analysis: BasketThematicAnalysis,
        suggestion_count: int
    ) -> str:
        """Generate reasoning that emphasizes accommodation."""
        
        if suggestion_count == 0:
            return "Your basket is well-organized as-is. No suggestions needed."
        
        reasoning_parts = []
        
        # Acknowledge current state positively
        if thematic_analysis.coherence_level == "high":
            reasoning_parts.append("Your basket shows strong thematic coherence")
        elif thematic_analysis.coherence_level == "mixed":
            reasoning_parts.append("Your basket shows interesting thematic diversity")
        else:
            reasoning_parts.append("Your basket contains developing themes")
        
        # Frame suggestions as optional
        if suggestion_count == 1:
            reasoning_parts.append("We noticed one small opportunity if you're interested")
        elif suggestion_count <= 3:
            reasoning_parts.append(f"We noticed {suggestion_count} small opportunities if you're interested")
        else:
            reasoning_parts.append(f"We noticed several opportunities if you'd like to explore them")
        
        # Emphasize choice
        reasoning_parts.append("Your current organization works fine - these are just ideas")
        
        return ". ".join(reasoning_parts) + "."
    
    @classmethod
    def _calculate_content_similarity(cls, content_a: str, content_b: str) -> float:
        """Calculate similarity between two pieces of content."""
        
        if not content_a or not content_b:
            return 0.0
        
        # Simple word overlap similarity
        words_a = set(content_a.lower().split())
        words_b = set(content_b.lower().split())
        
        # Remove common words
        common_words = {"the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        words_a = words_a - common_words
        words_b = words_b - common_words
        
        if not words_a or not words_b:
            return 0.0
        
        intersection = words_a.intersection(words_b)
        union = words_a.union(words_b)
        
        return len(intersection) / len(union) if union else 0.0
    
    @classmethod
    def _find_shared_concepts(cls, content_a: str, content_b: str) -> List[str]:
        """Find shared concepts between two pieces of content."""
        
        # Simple approach: find meaningful words that appear in both
        import re
        
        words_a = set(re.findall(r'\b[a-zA-Z]{4,}\b', content_a.lower()))
        words_b = set(re.findall(r'\b[a-zA-Z]{4,}\b', content_b.lower()))
        
        # Remove common words
        common_words = {
            "this", "that", "with", "from", "they", "will", "have", "been",
            "were", "said", "each", "which", "their", "would", "there"
        }
        
        words_a = words_a - common_words
        words_b = words_b - common_words
        
        shared = words_a.intersection(words_b)
        return list(shared)[:5]  # Return up to 5 shared concepts