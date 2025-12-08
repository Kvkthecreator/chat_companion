"""Cross-document relationship discovery service without enforcement."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Set, Tuple
from uuid import UUID, uuid4
from collections import defaultdict
import re

from src.schemas.basket_intelligence_schema import (
    CrossDocumentRelationships, DocumentRelationship, BasketThematicAnalysis
)
from .pattern_recognition import BasketPatternRecognitionService
from ...utils.supabase_client import supabase_client as supabase

logger = logging.getLogger("uvicorn.error")


class RelationshipDiscoveryService:
    """Service for discovering relationships between documents without enforcement."""
    
    # Relationship type indicators
    RELATIONSHIP_INDICATORS = {
        "thematic_overlap": {
            "keywords": ["similar", "theme", "concept", "approach", "method"],
            "patterns": ["shared_themes", "concept_overlap", "methodological_similarity"],
            "min_confidence": 0.4
        },
        "sequential": {
            "keywords": ["next", "follow", "then", "after", "before", "step", "phase"],
            "patterns": ["temporal_sequence", "process_flow", "iterative_development"],
            "min_confidence": 0.3
        },
        "complementary": {
            "keywords": ["complement", "support", "enhance", "combine", "together"],
            "patterns": ["skill_complementarity", "perspective_diversity", "holistic_approach"],
            "min_confidence": 0.35
        },
        "conflicting": {
            "keywords": ["conflict", "different", "opposing", "alternative", "versus"],
            "patterns": ["approach_conflict", "perspective_disagreement", "option_comparison"],
            "min_confidence": 0.5
        },
        "foundational": {
            "keywords": ["foundation", "basis", "core", "fundamental", "essential"],
            "patterns": ["dependency_relationship", "hierarchical_structure", "prerequisite"],
            "min_confidence": 0.4
        },
        "exploratory": {
            "keywords": ["explore", "investigate", "discover", "experiment", "test"],
            "patterns": ["research_connection", "experimental_relationship", "discovery_path"],
            "min_confidence": 0.3
        }
    }
    
    @classmethod
    async def discover_document_relationships(
        cls,
        basket_id: UUID,
        workspace_id: str,
        thematic_analysis: Optional[BasketThematicAnalysis] = None,
        include_weak_relationships: bool = True
    ) -> CrossDocumentRelationships:
        """Discover relationships between documents in basket."""
        
        # Get basket contents
        basket_contents = await cls._get_basket_contents(basket_id, workspace_id)
        documents = basket_contents["documents"]
        
        if len(documents) < 2:
            # Single or no documents - return empty relationships
            return CrossDocumentRelationships(
                basket_id=basket_id,
                document_pairs=[],
                relationship_strength={},
                suggested_connections=[],
                missed_opportunities=[],
                overall_connectivity=0.0,
                connection_insights=["Single document basket - no cross-document relationships possible"],
                autonomy_note="Each document maintains its independent context and purpose"
            )
        
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
        
        # Discover pairwise relationships
        document_pairs = cls._discover_pairwise_relationships(
            documents, thematic_analysis, include_weak_relationships
        )
        
        # Calculate relationship strengths
        relationship_strength = cls._calculate_relationship_strengths(document_pairs)
        
        # Generate connection suggestions (gentle)
        suggested_connections = cls._generate_connection_suggestions(
            document_pairs, documents
        )
        
        # Identify missed opportunities (without judgment)
        missed_opportunities = cls._identify_missed_opportunities(
            documents, document_pairs, thematic_analysis
        )
        
        # Calculate overall connectivity
        overall_connectivity = cls._calculate_overall_connectivity(
            len(documents), document_pairs
        )
        
        # Generate insights
        connection_insights = cls._generate_connection_insights(
            document_pairs, relationship_strength, overall_connectivity
        )
        
        return CrossDocumentRelationships(
            basket_id=basket_id,
            document_pairs=document_pairs,
            relationship_strength=relationship_strength,
            suggested_connections=suggested_connections,
            missed_opportunities=missed_opportunities,
            overall_connectivity=overall_connectivity,
            connection_insights=connection_insights,
            autonomy_note="Documents maintain their independent context - these are connection opportunities"
        )
    
    @classmethod
    async def suggest_gentle_connections(
        cls,
        basket_id: UUID,
        workspace_id: str,
        max_suggestions: int = 5
    ) -> List[str]:
        """Generate gentle connection suggestions without enforcement."""
        
        relationships = await cls.discover_document_relationships(
            basket_id, workspace_id, include_weak_relationships=False
        )
        
        # Filter to most valuable suggestions
        high_value_pairs = [
            pair for pair in relationships.document_pairs
            if pair.potential_value in ["medium", "high"] and pair.strength > 0.4
        ]
        
        suggestions = []
        for pair in high_value_pairs[:max_suggestions]:
            suggestion = f"Consider connecting '{cls._get_doc_title(pair.document_a_id)}' and '{cls._get_doc_title(pair.document_b_id)}' - {pair.relationship_description.lower()}"
            suggestions.append(suggestion)
        
        if not suggestions:
            suggestions.append("Your documents work well independently - no connection suggestions needed")
        
        return suggestions
    
    @classmethod
    async def analyze_document_clusters(
        cls,
        basket_id: UUID,
        workspace_id: str
    ) -> Dict[str, List[UUID]]:
        """Identify natural document clusters without imposing structure."""
        
        relationships = await cls.discover_document_relationships(basket_id, workspace_id)
        
        # Build adjacency list
        adjacency = defaultdict(list)
        for pair in relationships.document_pairs:
            if pair.strength > 0.3:  # Only consider meaningful relationships
                adjacency[pair.document_a_id].append(pair.document_b_id)
                adjacency[pair.document_b_id].append(pair.document_a_id)
        
        # Find connected components (clusters)
        visited = set()
        clusters = {}
        cluster_id = 1
        
        def dfs(doc_id: UUID, cluster_docs: List[UUID]):
            if doc_id in visited:
                return
            visited.add(doc_id)
            cluster_docs.append(doc_id)
            for neighbor in adjacency[doc_id]:
                dfs(neighbor, cluster_docs)
        
        for doc_id in adjacency.keys():
            if doc_id not in visited:
                cluster_docs = []
                dfs(doc_id, cluster_docs)
                if len(cluster_docs) > 1:  # Only meaningful clusters
                    clusters[f"cluster_{cluster_id}"] = cluster_docs
                    cluster_id += 1
        
        return clusters
    
    @classmethod
    async def _get_basket_contents(
        cls,
        basket_id: UUID,
        workspace_id: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get basket contents for relationship analysis."""
        
        contents = {
            "documents": [],
            "blocks": []
            # V3.0: No context_items (merged into blocks)
        }

        try:
            # Get documents with full content
            docs_resp = (
                supabase.table("documents")
                .select("id,title,content_raw,document_type,created_at")
                .eq("basket_id", str(basket_id))
                .eq("workspace_id", workspace_id)
                .execute()
            )
            contents["documents"] = docs_resp.data or []

            # V3.0: Get blocks (includes all substrate types: knowledge, meaning, entities)
            blocks_resp = (
                supabase.table("blocks")
                .select("id,content,semantic_type,anchor_role,document_id")
                .eq("basket_id", str(basket_id))
                .eq("workspace_id", workspace_id)
                .neq("state", "REJECTED")
                .execute()
            )
            contents["blocks"] = blocks_resp.data or []
            
        except Exception as e:
            logger.exception(f"Failed to get basket contents for relationships: {e}")
        
        return contents
    
    @classmethod
    def _discover_pairwise_relationships(
        cls,
        documents: List[Dict[str, Any]],
        thematic_analysis: BasketThematicAnalysis,
        include_weak: bool = True
    ) -> List[DocumentRelationship]:
        """Discover relationships between document pairs."""
        
        relationships = []
        
        for i, doc_a in enumerate(documents):
            for doc_b in documents[i+1:]:
                # Analyze relationship between this pair
                relationship = cls._analyze_document_pair(
                    doc_a, doc_b, thematic_analysis
                )
                
                if relationship and (include_weak or relationship.strength > 0.4):
                    relationships.append(relationship)
        
        return relationships
    
    @classmethod
    def _analyze_document_pair(
        cls,
        doc_a: Dict[str, Any],
        doc_b: Dict[str, Any],
        thematic_analysis: BasketThematicAnalysis
    ) -> Optional[DocumentRelationship]:
        """Analyze relationship between two specific documents."""
        
        # Get content from both documents
        content_a = (doc_a.get("content_raw", "") + " " + doc_a.get("title", "")).lower()
        content_b = (doc_b.get("content_raw", "") + " " + doc_b.get("title", "")).lower()
        
        if not content_a.strip() or not content_b.strip():
            return None
        
        # Calculate different types of relationships
        relationship_scores = {}
        evidence_collections = {}
        
        for rel_type, indicators in cls.RELATIONSHIP_INDICATORS.items():
            score, evidence = cls._calculate_relationship_score(
                content_a, content_b, indicators, thematic_analysis
            )
            relationship_scores[rel_type] = score
            evidence_collections[rel_type] = evidence
        
        # Find strongest relationship
        best_type = max(relationship_scores, key=relationship_scores.get)
        best_score = relationship_scores[best_type]
        
        if best_score < cls.RELATIONSHIP_INDICATORS[best_type]["min_confidence"]:
            return None
        
        # Generate relationship description
        description = cls._generate_relationship_description(
            doc_a, doc_b, best_type, evidence_collections[best_type]
        )
        
        # Determine potential value
        potential_value = cls._assess_relationship_value(best_score, best_type, doc_a, doc_b)
        
        # Generate suggested links
        suggested_links = cls._generate_suggested_links(
            doc_a, doc_b, best_type, evidence_collections[best_type]
        )
        
        return DocumentRelationship(
            relationship_id=f"{doc_a['id']}_{doc_b['id']}_{best_type}",
            document_a_id=UUID(doc_a["id"]),
            document_b_id=UUID(doc_b["id"]),
            relationship_type=best_type,
            strength=best_score,
            connection_evidence=evidence_collections[best_type],
            suggested_links=suggested_links,
            relationship_description=description,
            potential_value=potential_value
        )
    
    @classmethod
    def _calculate_relationship_score(
        cls,
        content_a: str,
        content_b: str,
        indicators: Dict[str, Any],
        thematic_analysis: BasketThematicAnalysis
    ) -> Tuple[float, List[str]]:
        """Calculate relationship score and gather evidence."""
        
        score = 0.0
        evidence = []
        
        # Keyword-based scoring
        keywords = indicators["keywords"]
        keyword_matches = 0
        for keyword in keywords:
            if keyword in content_a and keyword in content_b:
                keyword_matches += 1
                evidence.append(f"Both documents mention '{keyword}'")
            elif keyword in content_a or keyword in content_b:
                keyword_matches += 0.5
        
        if keywords:
            keyword_score = keyword_matches / len(keywords)
            score += keyword_score * 0.4
        
        # Thematic overlap scoring
        shared_themes = cls._find_shared_themes(content_a, content_b, thematic_analysis)
        if shared_themes:
            theme_score = len(shared_themes) / max(len(thematic_analysis.dominant_themes), 1)
            score += theme_score * 0.3
            evidence.extend([f"Share theme: {theme}" for theme in shared_themes])
        
        # Content similarity scoring
        similarity = cls._calculate_content_similarity(content_a, content_b)
        score += similarity * 0.2
        
        if similarity > 0.3:
            evidence.append(f"Content similarity: {similarity:.2f}")
        
        # Cross-reference scoring
        cross_refs = cls._find_cross_references(content_a, content_b)
        if cross_refs:
            score += min(len(cross_refs) * 0.1, 0.1)
            evidence.extend([f"Cross-reference: {ref}" for ref in cross_refs[:2]])
        
        return min(score, 1.0), evidence[:5]  # Limit evidence
    
    @classmethod
    def _find_shared_themes(
        cls,
        content_a: str,
        content_b: str,
        thematic_analysis: BasketThematicAnalysis
    ) -> List[str]:
        """Find themes that appear in both documents."""
        
        shared_themes = []
        
        for pattern in thematic_analysis.discovered_patterns:
            keywords = pattern.keywords
            
            a_has_theme = any(keyword in content_a for keyword in keywords)
            b_has_theme = any(keyword in content_b for keyword in keywords)
            
            if a_has_theme and b_has_theme:
                shared_themes.append(pattern.theme_name)
        
        return shared_themes
    
    @classmethod
    def _calculate_content_similarity(cls, content_a: str, content_b: str) -> float:
        """Calculate similarity between document contents."""
        
        if not content_a or not content_b:
            return 0.0
        
        # Extract meaningful words
        words_a = set(re.findall(r'\b[a-zA-Z]{4,}\b', content_a.lower()))
        words_b = set(re.findall(r'\b[a-zA-Z]{4,}\b', content_b.lower()))
        
        # Remove common words
        common_words = {
            "this", "that", "with", "from", "they", "will", "have", "been",
            "were", "said", "each", "which", "their", "would", "there",
            "could", "should", "more", "very", "what", "know", "just"
        }
        
        words_a = words_a - common_words
        words_b = words_b - common_words
        
        if not words_a or not words_b:
            return 0.0
        
        intersection = words_a.intersection(words_b)
        union = words_a.union(words_b)
        
        return len(intersection) / len(union) if union else 0.0
    
    @classmethod
    def _find_cross_references(cls, content_a: str, content_b: str) -> List[str]:
        """Find cross-references between documents."""
        
        cross_refs = []
        
        # Simple URL detection
        urls_a = set(re.findall(r'https?://[^\s]+', content_a))
        urls_b = set(re.findall(r'https?://[^\s]+', content_b))
        
        shared_urls = urls_a.intersection(urls_b)
        cross_refs.extend([f"URL: {url[:30]}..." for url in list(shared_urls)[:2]])
        
        # Simple citation pattern detection
        citations_a = set(re.findall(r'\b[A-Z][a-z]+ \(\d{4}\)', content_a))
        citations_b = set(re.findall(r'\b[A-Z][a-z]+ \(\d{4}\)', content_b))
        
        shared_citations = citations_a.intersection(citations_b)
        cross_refs.extend([f"Citation: {cite}" for cite in list(shared_citations)[:2]])
        
        return cross_refs
    
    @classmethod
    def _generate_relationship_description(
        cls,
        doc_a: Dict[str, Any],
        doc_b: Dict[str, Any],
        relationship_type: str,
        evidence: List[str]
    ) -> str:
        """Generate human-friendly relationship description."""
        
        title_a = doc_a.get("title", "document")[:20]
        title_b = doc_b.get("title", "document")[:20]
        
        descriptions = {
            "thematic_overlap": f"Share similar themes and concepts",
            "sequential": f"Form a natural sequence or progression",
            "complementary": f"Complement each other's perspectives",
            "conflicting": f"Present alternative approaches or viewpoints",
            "foundational": f"One provides foundation for the other",
            "exploratory": f"Both explore related research areas"
        }
        
        base_description = descriptions.get(relationship_type, "Are related")
        
        if evidence:
            return f"{base_description} - {evidence[0].lower()}"
        else:
            return base_description
    
    @classmethod
    def _assess_relationship_value(
        cls,
        score: float,
        relationship_type: str,
        doc_a: Dict[str, Any],
        doc_b: Dict[str, Any]
    ) -> str:
        """Assess the potential value of connecting these documents."""
        
        # High-value relationship types
        high_value_types = {"sequential", "foundational", "complementary"}
        
        if relationship_type in high_value_types and score > 0.6:
            return "high"
        elif score > 0.5:
            return "medium"
        else:
            return "low"
    
    @classmethod
    def _generate_suggested_links(
        cls,
        doc_a: Dict[str, Any],
        doc_b: Dict[str, Any],
        relationship_type: str,
        evidence: List[str]
    ) -> List[str]:
        """Generate suggestions for linking these documents."""
        
        suggestions = []
        
        link_templates = {
            "thematic_overlap": [
                "Add context item connecting shared themes",
                "Create thematic bridge between documents"
            ],
            "sequential": [
                "Add sequential context showing progression",
                "Link as part of process or workflow"
            ],
            "complementary": [
                "Add context showing how they complement",
                "Create perspective bridge"
            ],
            "conflicting": [
                "Add context comparing approaches",
                "Create comparison framework"
            ],
            "foundational": [
                "Add dependency context",
                "Show foundation-building relationship"
            ],
            "exploratory": [
                "Add research connection context",
                "Link exploration themes"
            ]
        }
        
        templates = link_templates.get(relationship_type, ["Add connecting context"])
        suggestions.extend(templates[:2])  # Limit suggestions
        
        return suggestions
    
    @classmethod
    def _calculate_relationship_strengths(
        cls,
        document_pairs: List[DocumentRelationship]
    ) -> Dict[str, float]:
        """Calculate overall relationship strengths by type."""
        
        type_strengths = defaultdict(list)
        
        for pair in document_pairs:
            type_strengths[pair.relationship_type].append(pair.strength)
        
        # Calculate average strength for each type
        avg_strengths = {}
        for rel_type, strengths in type_strengths.items():
            avg_strengths[rel_type] = sum(strengths) / len(strengths)
        
        return dict(avg_strengths)
    
    @classmethod
    def _generate_connection_suggestions(
        cls,
        document_pairs: List[DocumentRelationship],
        documents: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate gentle connection suggestions."""
        
        suggestions = []
        
        # Focus on highest-value relationships
        high_value_pairs = [
            pair for pair in document_pairs
            if pair.potential_value in ["medium", "high"]
        ]
        
        if not high_value_pairs:
            suggestions.append("Your documents work well independently")
            return suggestions
        
        # Generate specific suggestions
        for pair in high_value_pairs[:3]:  # Limit to avoid overwhelming
            title_a = cls._get_doc_title(pair.document_a_id, documents)
            title_b = cls._get_doc_title(pair.document_b_id, documents)
            
            suggestion = f"Consider connecting '{title_a}' and '{title_b}' - {pair.relationship_description.lower()}"
            suggestions.append(suggestion)
        
        return suggestions
    
    @classmethod
    def _identify_missed_opportunities(
        cls,
        documents: List[Dict[str, Any]],
        discovered_pairs: List[DocumentRelationship],
        thematic_analysis: BasketThematicAnalysis
    ) -> List[str]:
        """Identify missed connection opportunities without judgment."""
        
        opportunities = []
        
        # Check for documents that could be connected but aren't
        connected_docs = set()
        for pair in discovered_pairs:
            connected_docs.add(pair.document_a_id)
            connected_docs.add(pair.document_b_id)
        
        isolated_docs = []
        for doc in documents:
            if UUID(doc["id"]) not in connected_docs:
                isolated_docs.append(doc["title"][:20] if doc.get("title") else "untitled")
        
        if isolated_docs and len(isolated_docs) < len(documents):
            opportunities.append(f"Documents '{', '.join(isolated_docs)}' could potentially connect with others")
        
        # Check for thematic opportunities
        strong_themes = [p.theme_name for p in thematic_analysis.discovered_patterns if p.pattern_strength == "strong"]
        if len(strong_themes) > 1:
            opportunities.append(f"Strong themes ({', '.join(strong_themes[:2])}) could be explicitly connected")
        
        return opportunities[:3]  # Limit opportunities
    
    @classmethod
    def _calculate_overall_connectivity(
        cls,
        total_documents: int,
        relationships: List[DocumentRelationship]
    ) -> float:
        """Calculate overall connectivity score."""
        
        if total_documents < 2:
            return 0.0
        
        # Maximum possible relationships
        max_relationships = (total_documents * (total_documents - 1)) // 2
        
        # Weight relationships by strength
        weighted_connections = sum(pair.strength for pair in relationships)
        
        # Normalize
        connectivity = weighted_connections / max_relationships if max_relationships > 0 else 0.0
        
        return min(connectivity, 1.0)
    
    @classmethod
    def _generate_connection_insights(
        cls,
        document_pairs: List[DocumentRelationship],
        relationship_strengths: Dict[str, float],
        overall_connectivity: float
    ) -> List[str]:
        """Generate insights about document connections."""
        
        insights = []
        
        if not document_pairs:
            insights.append("Documents maintain independent focus - no strong cross-connections detected")
            return insights
        
        # Connectivity insights
        if overall_connectivity > 0.7:
            insights.append("High document connectivity indicates integrated project approach")
        elif overall_connectivity > 0.4:
            insights.append("Moderate connectivity shows balanced independent and connected work")
        else:
            insights.append("Low connectivity suggests focused, independent documents")
        
        # Relationship type insights
        if relationship_strengths:
            dominant_type = max(relationship_strengths, key=relationship_strengths.get)
            insights.append(f"Primary relationship pattern: {dominant_type.replace('_', ' ')}")
        
        # Value insights
        high_value_count = len([p for p in document_pairs if p.potential_value == "high"])
        if high_value_count > 0:
            insights.append(f"{high_value_count} high-value connection opportunities identified")
        
        return insights
    
    @classmethod
    def _get_doc_title(cls, doc_id: UUID, documents: List[Dict[str, Any]] = None) -> str:
        """Get document title by ID."""
        if documents:
            for doc in documents:
                if doc["id"] == str(doc_id):
                    return doc.get("title", "untitled")[:20]
        return "document"