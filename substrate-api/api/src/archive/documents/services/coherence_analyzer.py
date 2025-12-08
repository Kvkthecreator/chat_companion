"""Document coherence analysis service for context-alignment assessment."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID, uuid4
import re

from ...models.document import Document
from src.schemas.document_composition_schema import DocumentContextAlignment
from ...context.services.composition_intelligence import CompositionIntelligenceService
from ...utils.supabase_client import supabase_client as supabase
from ...utils.db import as_json

logger = logging.getLogger("uvicorn.error")


class CoherenceAnalyzerService:
    """Service for analyzing document coherence and context alignment."""
# V3.0 DEPRECATION NOTICE:
# This file contains references to context_items table which was merged into blocks table.
# Entity blocks are now identified by semantic_type='entity'.
# This file is legacy/supporting code - update if actively maintained.

    
    @classmethod
    async def analyze_document_context_alignment(
        cls,
        document_id: UUID,
        workspace_id: str
    ) -> DocumentContextAlignment:
        """Comprehensive analysis of document alignment with context DNA."""
        
        # Get document
        document = await cls._get_document(document_id, workspace_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        # Skip analysis for non-context-driven documents
        if not document.is_context_driven():
            return DocumentContextAlignment(
                document_id=document_id,
                overall_alignment_score=0.5,  # Neutral score for manual documents
                context_coverage=0.0,
                intent_alignment=0.0,
                audience_appropriateness=0.5,
                style_consistency=0.5,
                content_coherence=0.5,
                analysis_timestamp=datetime.utcnow()
            )
        
        # Analyze different alignment dimensions
        context_coverage = await cls._analyze_context_coverage(document, workspace_id)
        intent_alignment = await cls._analyze_intent_alignment(document, workspace_id)
        audience_appropriateness = cls._analyze_audience_appropriateness(document)
        style_consistency = cls._analyze_style_consistency(document)
        content_coherence = cls._analyze_content_coherence(document)
        
        # Identify alignment issues
        missing_contexts, underrepresented_contexts = await cls._identify_context_gaps(
            document, workspace_id
        )
        
        alignment_issues = cls._identify_alignment_issues(
            document, context_coverage, intent_alignment, audience_appropriateness,
            style_consistency, content_coherence
        )
        
        # Generate enhancement opportunities
        enhancement_opportunities = cls._generate_enhancement_opportunities(
            document, alignment_issues, missing_contexts, underrepresented_contexts
        )
        
        # Calculate overall alignment score
        overall_score = cls._calculate_overall_alignment(
            context_coverage, intent_alignment, audience_appropriateness,
            style_consistency, content_coherence
        )
        
        return DocumentContextAlignment(
            document_id=document_id,
            overall_alignment_score=overall_score,
            context_coverage=context_coverage,
            intent_alignment=intent_alignment,
            audience_appropriateness=audience_appropriateness,
            style_consistency=style_consistency,
            content_coherence=content_coherence,
            missing_contexts=missing_contexts,
            underrepresented_contexts=underrepresented_contexts,
            alignment_issues=alignment_issues,
            enhancement_opportunities=enhancement_opportunities,
            analysis_timestamp=datetime.utcnow()
        )
    
    @classmethod
    async def calculate_document_coherence(
        cls,
        document_id: UUID,
        workspace_id: str
    ) -> float:
        """Calculate overall document coherence score."""
        
        alignment = await cls.analyze_document_context_alignment(document_id, workspace_id)
        return alignment.overall_alignment_score
    
    @classmethod
    async def assess_document_quality(
        cls,
        document_id: UUID,
        workspace_id: str
    ) -> Dict[str, Any]:
        """Comprehensive document quality assessment."""
        
        document = await cls._get_document(document_id, workspace_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        # Get alignment analysis
        alignment = await cls.analyze_document_context_alignment(document_id, workspace_id)
        
        # Content quality metrics
        content_metrics = cls._analyze_content_quality(document)
        
        # Structure quality metrics
        structure_metrics = cls._analyze_structure_quality(document)
        
        # Completeness metrics
        completeness_metrics = cls._analyze_completeness(document)
        
        # Generate quality score
        quality_factors = [
            alignment.overall_alignment_score,
            content_metrics["readability_score"],
            structure_metrics["organization_score"],
            completeness_metrics["completeness_score"]
        ]
        
        overall_quality = sum(quality_factors) / len(quality_factors)
        
        return {
            "document_id": str(document_id),
            "overall_quality_score": overall_quality,
            "quality_breakdown": {
                "context_alignment": alignment.overall_alignment_score,
                "content_quality": content_metrics,
                "structure_quality": structure_metrics,
                "completeness": completeness_metrics
            },
            "quality_grade": cls._assign_quality_grade(overall_quality),
            "improvement_recommendations": cls._generate_quality_recommendations(
                overall_quality, alignment, content_metrics, structure_metrics, completeness_metrics
            ),
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
    
    @classmethod
    async def monitor_document_drift(
        cls,
        document_id: UUID,
        workspace_id: str,
        baseline_timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Monitor how document alignment drifts from its original context."""
        
        document = await cls._get_document(document_id, workspace_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        # Current alignment
        current_alignment = await cls.analyze_document_context_alignment(document_id, workspace_id)
        
        # Get baseline (document creation or specified timestamp)
        baseline_coherence = document.document_coherence.overall_coherence_score
        baseline_timestamp = baseline_timestamp or document.created_at
        
        # Calculate drift metrics
        alignment_drift = current_alignment.overall_alignment_score - baseline_coherence
        time_drift_days = (datetime.utcnow() - baseline_timestamp).days
        
        # Drift analysis
        drift_analysis = {
            "document_id": str(document_id),
            "baseline_timestamp": baseline_timestamp.isoformat(),
            "baseline_coherence": baseline_coherence,
            "current_coherence": current_alignment.overall_alignment_score,
            "alignment_drift": alignment_drift,
            "drift_direction": "improvement" if alignment_drift > 0 else "degradation" if alignment_drift < 0 else "stable",
            "time_since_baseline_days": time_drift_days,
            "drift_rate": alignment_drift / max(time_drift_days, 1),  # Drift per day
            "drift_severity": cls._assess_drift_severity(alignment_drift, time_drift_days),
            "contributing_factors": cls._identify_drift_factors(document, current_alignment),
            "monitoring_timestamp": datetime.utcnow().isoformat()
        }
        
        return drift_analysis
    
    @classmethod
    async def _get_document(cls, document_id: UUID, workspace_id: str) -> Optional[Document]:
        """Get document by ID."""
        
        try:
            resp = (
                supabase.table("documents")
                .select("*")
                .eq("id", str(document_id))
                .eq("workspace_id", workspace_id)
                .single()
                .execute()
            )
            
            if resp.data:
                return Document(**resp.data)
            return None
            
        except Exception as e:
            logger.exception(f"Failed to get document {document_id}: {e}")
            return None
    
    @classmethod
    async def _analyze_context_coverage(cls, document: Document, workspace_id: str) -> float:
        """Analyze how well the document covers its contexts."""
        
        if not document.is_context_driven():
            return 0.0
        
        all_contexts = document.get_all_contexts()
        if not all_contexts:
            return 0.0
        
        # Simple coverage: check if context content appears in document
        covered_contexts = 0
        content_lower = document.content_raw.lower()
        
        for context_id in all_contexts:
            # Get context content
            context_content = await cls._get_context_content(context_id, workspace_id)
            if context_content:
                # Check if key words from context appear in document
                context_words = set(context_content.lower().split())
                # Remove common words
                context_words = {w for w in context_words if len(w) > 3 and w.isalpha()}
                
                if context_words:
                    overlap = sum(1 for word in context_words if word in content_lower)
                    coverage_ratio = overlap / len(context_words)
                    if coverage_ratio > 0.3:  # At least 30% of context words appear
                        covered_contexts += 1
        
        return covered_contexts / len(all_contexts)
    
    @classmethod
    async def _analyze_intent_alignment(cls, document: Document, workspace_id: str) -> float:
        """Analyze alignment between document and detected intent."""
        
        if not document.is_context_driven():
            return 0.5  # Neutral for manual documents
        
        detected_intent = document.composition_intelligence.detected_intent
        intent_confidence = document.composition_intelligence.intent_confidence
        
        if not detected_intent:
            return 0.0
        
        # Analyze document structure against intent expectations
        intent_alignment_score = cls._calculate_intent_structural_alignment(
            document, detected_intent
        )
        
        # Weight by original intent confidence
        return intent_alignment_score * intent_confidence
    
    @classmethod
    def _analyze_audience_appropriateness(cls, document: Document) -> float:
        """Analyze if document is appropriate for target audience."""
        
        if not document.is_context_driven():
            return 0.5
        
        target_audience = document.composition_intelligence.target_audience
        if not target_audience:
            return 0.5
        
        content = document.content_raw.lower()
        
        # Audience-specific indicators
        audience_indicators = {
            "executives": {
                "positive": ["strategic", "business", "roi", "growth", "competitive", "leadership"],
                "negative": ["technical details", "implementation", "code", "specific steps"]
            },
            "engineers": {
                "positive": ["implementation", "technical", "architecture", "system", "code", "api"],
                "negative": ["high-level only", "strategic overview", "business justification"]
            },
            "designers": {
                "positive": ["user experience", "design", "visual", "interface", "usability"],
                "negative": ["technical implementation", "code details", "backend"]
            },
            "general": {
                "positive": ["clear", "accessible", "overview", "practical", "actionable"],
                "negative": ["jargon", "technical complexity", "insider knowledge"]
            }
        }
        
        indicators = audience_indicators.get(target_audience, audience_indicators["general"])
        
        # Count positive and negative indicators
        positive_count = sum(1 for term in indicators["positive"] if term in content)
        negative_count = sum(1 for term in indicators["negative"] if term in content)
        
        # Calculate appropriateness score
        total_indicators = len(indicators["positive"]) + len(indicators["negative"])
        if total_indicators == 0:
            return 0.5
        
        positive_score = positive_count / len(indicators["positive"])
        negative_penalty = negative_count / len(indicators["negative"])
        
        return max(0.0, positive_score - negative_penalty * 0.5)
    
    @classmethod
    def _analyze_style_consistency(cls, document: Document) -> float:
        """Analyze consistency of document style."""
        
        if not document.is_context_driven():
            return 0.5
        
        expected_style = document.narrative_metadata.narrative_style
        content = document.content_raw
        
        # Style indicators
        style_patterns = {
            "formal": {
                "patterns": [r"\banalysis\b", r"\bstrategic\b", r"\bcomprehensive\b", r"\bsystematic\b"],
                "anti_patterns": [r"\blet's\b", r"\bhere's\b", r"\bwe'll\b", r"!{2,}"]
            },
            "conversational": {
                "patterns": [r"\blet's\b", r"\bhere's\b", r"\byou\b", r"\bwe\b"],
                "anti_patterns": [r"\banalysis indicates\b", r"\bcomprehensive assessment\b"]
            },
            "detailed": {
                "patterns": [r"\bspecifically\b", r"\bdetailed\b", r"\bin-depth\b", r"\bthorough\b"],
                "anti_patterns": [r"\bbriefly\b", r"\bquickly\b", r"\boverview\b"]
            }
        }
        
        if expected_style not in style_patterns:
            return 0.5
        
        patterns = style_patterns[expected_style]
        
        # Count pattern matches
        positive_matches = sum(len(re.findall(pattern, content, re.IGNORECASE)) 
                             for pattern in patterns["patterns"])
        negative_matches = sum(len(re.findall(pattern, content, re.IGNORECASE)) 
                             for pattern in patterns["anti_patterns"])
        
        # Calculate consistency score
        total_patterns = len(patterns["patterns"]) + len(patterns["anti_patterns"])
        if total_patterns == 0:
            return 0.5
        
        consistency_score = (positive_matches - negative_matches * 0.5) / total_patterns
        return max(0.0, min(1.0, consistency_score))
    
    @classmethod
    def _analyze_content_coherence(cls, document: Document) -> float:
        """Analyze internal content coherence."""
        
        content = document.content_raw
        if len(content) < 100:
            return 0.0
        
        # Simple coherence metrics
        coherence_factors = []
        
        # Section structure coherence
        sections = document.sections
        if sections:
            # Check if sections have reasonable lengths
            section_lengths = [len(section.content) for section in sections]
            if section_lengths:
                length_variance = max(section_lengths) / (min(section_lengths) + 1)
                # Penalize extreme length differences
                section_balance = max(0.0, 1.0 - (length_variance - 1.0) / 10.0)
                coherence_factors.append(section_balance)
        
        # Paragraph structure
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        if paragraphs:
            # Check paragraph length distribution
            para_lengths = [len(p) for p in paragraphs]
            avg_length = sum(para_lengths) / len(para_lengths)
            length_consistency = 1.0 - (max(para_lengths) - min(para_lengths)) / max(avg_length, 100)
            coherence_factors.append(max(0.0, length_consistency))
        
        # Transition coherence (simple keyword connectivity)
        transition_words = ["however", "therefore", "furthermore", "additionally", "consequently", "meanwhile"]
        transitions_count = sum(content.lower().count(word) for word in transition_words)
        transition_density = transitions_count / max(len(paragraphs), 1)
        transition_score = min(1.0, transition_density / 2.0)  # Normalize to 0-1
        coherence_factors.append(transition_score)
        
        return sum(coherence_factors) / len(coherence_factors) if coherence_factors else 0.5
    
    @classmethod
    async def _identify_context_gaps(
        cls,
        document: Document,
        workspace_id: str
    ) -> Tuple[List[UUID], List[UUID]]:
        """Identify missing and underrepresented contexts."""
        
        if not document.is_context_driven():
            return [], []
        
        all_contexts = document.get_all_contexts()
        primary_contexts = document.get_primary_contexts()
        
        missing_contexts = []
        underrepresented_contexts = []
        
        # Check coverage of each context
        content_lower = document.content_raw.lower()
        
        for context_id in all_contexts:
            context_content = await cls._get_context_content(context_id, workspace_id)
            if context_content:
                # Check representation in document
                context_words = set(context_content.lower().split())
                context_words = {w for w in context_words if len(w) > 3 and w.isalpha()}
                
                if context_words:
                    overlap = sum(1 for word in context_words if word in content_lower)
                    representation_ratio = overlap / len(context_words)
                    
                    if representation_ratio == 0:
                        missing_contexts.append(context_id)
                    elif representation_ratio < 0.2:  # Less than 20% representation
                        underrepresented_contexts.append(context_id)
        
        return missing_contexts, underrepresented_contexts
    
    @classmethod
    def _identify_alignment_issues(
        cls,
        document: Document,
        context_coverage: float,
        intent_alignment: float,
        audience_appropriateness: float,
        style_consistency: float,
        content_coherence: float
    ) -> List[Dict[str, Any]]:
        """Identify specific alignment issues."""
        
        issues = []
        
        if context_coverage < 0.5:
            issues.append({
                "type": "low_context_coverage",
                "severity": "high" if context_coverage < 0.3 else "medium",
                "description": f"Only {context_coverage:.1%} of contexts are adequately represented",
                "metric_value": context_coverage
            })
        
        if intent_alignment < 0.6:
            issues.append({
                "type": "poor_intent_alignment",
                "severity": "high" if intent_alignment < 0.4 else "medium",
                "description": f"Document structure doesn't align well with detected intent",
                "metric_value": intent_alignment
            })
        
        if audience_appropriateness < 0.5:
            issues.append({
                "type": "audience_mismatch",
                "severity": "medium",
                "description": f"Content may not be appropriate for target audience",
                "metric_value": audience_appropriateness
            })
        
        if style_consistency < 0.5:
            issues.append({
                "type": "style_inconsistency",
                "severity": "low",
                "description": f"Inconsistent narrative style throughout document",
                "metric_value": style_consistency
            })
        
        if content_coherence < 0.5:
            issues.append({
                "type": "poor_coherence",
                "severity": "medium",
                "description": f"Internal content flow and structure need improvement",
                "metric_value": content_coherence
            })
        
        return issues
    
    @classmethod
    def _generate_enhancement_opportunities(
        cls,
        document: Document,
        alignment_issues: List[Dict[str, Any]],
        missing_contexts: List[UUID],
        underrepresented_contexts: List[UUID]
    ) -> List[Dict[str, Any]]:
        """Generate enhancement opportunities based on analysis."""
        
        opportunities = []
        
        # Context-based opportunities
        if missing_contexts:
            opportunities.append({
                "type": "add_missing_contexts",
                "priority": "high",
                "description": f"Incorporate {len(missing_contexts)} missing contexts into document",
                "expected_impact": "high",
                "effort_required": "medium"
            })
        
        if underrepresented_contexts:
            opportunities.append({
                "type": "enhance_context_representation",
                "priority": "medium",
                "description": f"Better represent {len(underrepresented_contexts)} underutilized contexts",
                "expected_impact": "medium",
                "effort_required": "low"
            })
        
        # Issue-based opportunities
        high_severity_issues = [issue for issue in alignment_issues if issue["severity"] == "high"]
        if high_severity_issues:
            opportunities.append({
                "type": "address_critical_issues",
                "priority": "high",
                "description": f"Address {len(high_severity_issues)} critical alignment issues",
                "expected_impact": "high",
                "effort_required": "high"
            })
        
        # Structure optimization
        if document.is_context_driven() and len(document.sections) < 3:
            opportunities.append({
                "type": "improve_structure",
                "priority": "medium",
                "description": "Enhance document structure with additional sections",
                "expected_impact": "medium",
                "effort_required": "medium"
            })
        
        return opportunities
    
    @classmethod
    def _calculate_overall_alignment(
        cls,
        context_coverage: float,
        intent_alignment: float,
        audience_appropriateness: float,
        style_consistency: float,
        content_coherence: float
    ) -> float:
        """Calculate weighted overall alignment score."""
        
        # Weighted scoring (context coverage and intent alignment are most important)
        weights = {
            "context_coverage": 0.3,
            "intent_alignment": 0.25,
            "audience_appropriateness": 0.2,
            "style_consistency": 0.15,
            "content_coherence": 0.1
        }
        
        weighted_score = (
            context_coverage * weights["context_coverage"] +
            intent_alignment * weights["intent_alignment"] +
            audience_appropriateness * weights["audience_appropriateness"] +
            style_consistency * weights["style_consistency"] +
            content_coherence * weights["content_coherence"]
        )
        
        return weighted_score
    
    @classmethod
    def _calculate_intent_structural_alignment(cls, document: Document, detected_intent: str) -> float:
        """Calculate how well document structure aligns with intent expectations."""
        
        # Expected sections by intent
        intent_expectations = {
            "strategic_analysis": ["analysis", "opportunities", "recommendations"],
            "technical_guide": ["overview", "implementation", "examples"],
            "executive_summary": ["findings", "recommendations"],
            "action_plan": ["objectives", "actions", "timeline"],
            "research_report": ["background", "findings", "conclusions"]
        }
        
        expected_sections = intent_expectations.get(detected_intent, [])
        if not expected_sections:
            return 0.5  # Neutral for unknown intents
        
        # Check if document has appropriate sections
        document_sections = [section.title.lower() for section in document.sections]
        
        # Count matches
        matches = 0
        for expected in expected_sections:
            if any(expected in section for section in document_sections):
                matches += 1
        
        return matches / len(expected_sections) if expected_sections else 0.5
    
    @classmethod
    def _analyze_content_quality(cls, document: Document) -> Dict[str, float]:
        """Analyze content quality metrics."""
        
        content = document.content_raw
        
        # Basic readability metrics
        word_count = len(content.split())
        sentence_count = len([s for s in content.split('.') if s.strip()])
        avg_sentence_length = word_count / max(sentence_count, 1)
        
        # Readability score (simplified)
        readability_score = min(1.0, max(0.0, 1.0 - abs(avg_sentence_length - 20) / 20))
        
        return {
            "readability_score": readability_score,
            "word_count": word_count,
            "sentence_count": sentence_count,
            "avg_sentence_length": avg_sentence_length
        }
    
    @classmethod
    def _analyze_structure_quality(cls, document: Document) -> Dict[str, float]:
        """Analyze document structure quality."""
        
        sections = document.sections
        
        # Organization score based on section count and balance
        if not sections:
            organization_score = 0.3  # Poor organization
        elif len(sections) < 2:
            organization_score = 0.5  # Minimal organization
        elif len(sections) > 8:
            organization_score = 0.7  # Possibly over-organized
        else:
            organization_score = 0.9  # Good organization
        
        return {
            "organization_score": organization_score,
            "section_count": len(sections)
        }
    
    @classmethod
    def _analyze_completeness(cls, document: Document) -> Dict[str, float]:
        """Analyze document completeness."""
        
        content_length = len(document.content_raw)
        
        # Completeness based on content length and structure
        if content_length < 500:
            completeness_score = 0.3  # Very incomplete
        elif content_length < 1500:
            completeness_score = 0.6  # Somewhat complete
        elif content_length < 5000:
            completeness_score = 0.9  # Well developed
        else:
            completeness_score = 1.0  # Comprehensive
        
        return {
            "completeness_score": completeness_score,
            "content_length": content_length
        }
    
    @classmethod
    def _assign_quality_grade(cls, overall_quality: float) -> str:
        """Assign quality grade based on score."""
        
        if overall_quality >= 0.9:
            return "A"
        elif overall_quality >= 0.8:
            return "B"
        elif overall_quality >= 0.7:
            return "C"
        elif overall_quality >= 0.6:
            return "D"
        else:
            return "F"
    
    @classmethod
    def _generate_quality_recommendations(
        cls,
        overall_quality: float,
        alignment: DocumentContextAlignment,
        content_metrics: Dict[str, Any],
        structure_metrics: Dict[str, Any],
        completeness_metrics: Dict[str, Any]
    ) -> List[str]:
        """Generate quality improvement recommendations."""
        
        recommendations = []
        
        if overall_quality < 0.6:
            recommendations.append("Document requires significant improvement across multiple dimensions")
        
        if alignment.context_coverage < 0.5:
            recommendations.append("Improve context coverage by incorporating more relevant context items")
        
        if content_metrics["readability_score"] < 0.6:
            recommendations.append("Improve readability by adjusting sentence length and complexity")
        
        if structure_metrics["organization_score"] < 0.7:
            recommendations.append("Enhance document organization with clearer section structure")
        
        if completeness_metrics["completeness_score"] < 0.6:
            recommendations.append("Expand content to provide more comprehensive coverage")
        
        return recommendations
    
    @classmethod
    def _assess_drift_severity(cls, alignment_drift: float, time_days: int) -> str:
        """Assess severity of document drift."""
        
        if abs(alignment_drift) < 0.1:
            return "minimal"
        elif abs(alignment_drift) < 0.2:
            return "moderate"
        elif abs(alignment_drift) < 0.3:
            return "significant"
        else:
            return "severe"
    
    @classmethod
    def _identify_drift_factors(
        cls,
        document: Document,
        current_alignment: DocumentContextAlignment
    ) -> List[str]:
        """Identify factors contributing to alignment drift."""
        
        factors = []
        
        if current_alignment.context_coverage < 0.5:
            factors.append("Decreased context coverage")
        
        if current_alignment.intent_alignment < 0.6:
            factors.append("Intent alignment degradation")
        
        if len(current_alignment.missing_contexts) > 0:
            factors.append(f"{len(current_alignment.missing_contexts)} contexts no longer represented")
        
        return factors
    
    @classmethod
    async def _get_context_content(cls, context_id: UUID, workspace_id: str) -> Optional[str]:
        """Get context content by ID."""
        
        try:
            resp = (
                supabase.table("context_items")
                .select("content")
                .eq("id", str(context_id))
                .eq("status", "active")
                .single()
                .execute()
            )
            
            return resp.data.get("content") if resp.data else None
            
        except Exception as e:
            logger.warning(f"Failed to get context {context_id}: {e}")
            return None