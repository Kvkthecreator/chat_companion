"""API routes for basket intelligence and pattern analysis."""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from uuid import UUID

from ..auth.dependencies import get_current_workspace_id
from src.schemas.basket_intelligence_schema import (
    PatternAnalysisRequest, BasketIntelligenceReport,
    AgentBasketAnalysisRequest, BasketCoherenceSuggestions,
    CrossDocumentRelationships, BasketContextHealth,
    BasketImprovementGuidance, BasketFlexibilityMetrics
)
from .services.pattern_recognition import BasketPatternRecognitionService
from .services.coherence_suggestions import CoherenceSuggestionsService
from .services.relationship_discovery import RelationshipDiscoveryService
from .services.inconsistency_accommodation import InconsistencyAccommodationService
from .services.improvement_guidance import ImprovementGuidanceService
from ..agents.pipeline.reflection_agent import P3ReflectionAgent

router = APIRouter(prefix="/baskets", tags=["basket-intelligence"])


@router.post("/{basket_id}/analyze-patterns")
async def analyze_basket_patterns(
    basket_id: UUID,
    request: PatternAnalysisRequest,
    workspace_id: str = Depends(get_current_workspace_id)
):
    """Analyze thematic patterns in basket contents with flexibility."""
    try:
        # Ensure request basket_id matches URL
        request.basket_id = basket_id
        
        analysis = await BasketPatternRecognitionService.analyze_basket_patterns(
            request, workspace_id
        )
        return analysis
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Pattern analysis failed: {str(e)}"
        )


@router.get("/{basket_id}/coherence-suggestions")
async def get_coherence_suggestions(
    basket_id: UUID,
    suggestion_style: str = "gentle",
    workspace_id: str = Depends(get_current_workspace_id)
):
    """Get gentle suggestions for improving basket coherence."""
    try:
        suggestions = await CoherenceSuggestionsService.generate_gentle_suggestions(
            basket_id, workspace_id, suggestion_style=suggestion_style
        )
        return suggestions
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Coherence suggestions failed: {str(e)}"
        )


@router.get("/{basket_id}/document-relationships")
async def discover_document_relationships(
    basket_id: UUID,
    include_weak: bool = True,
    workspace_id: str = Depends(get_current_workspace_id)
):
    """Discover relationships between documents in basket."""
    try:
        relationships = await RelationshipDiscoveryService.discover_document_relationships(
            basket_id, workspace_id, include_weak_relationships=include_weak
        )
        return relationships
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Relationship discovery failed: {str(e)}"
        )


@router.get("/{basket_id}/context-health")
async def assess_context_health(
    basket_id: UUID,
    workspace_id: str = Depends(get_current_workspace_id)
):
    """Assess basket context health with accommodation approach."""
    try:
        health = await InconsistencyAccommodationService.assess_context_health(
            basket_id, workspace_id
        )
        return health
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Context health assessment failed: {str(e)}"
        )


@router.get("/{basket_id}/improvement-guidance")
async def get_improvement_guidance(
    basket_id: UUID,
    guidance_style: str = "gentle",
    user_requested: bool = False,
    workspace_id: str = Depends(get_current_workspace_id)
):
    """Get non-enforcing improvement guidance for basket."""
    try:
        guidance = await ImprovementGuidanceService.generate_improvement_guidance(
            basket_id, workspace_id, guidance_style, user_requested
        )
        return guidance
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Improvement guidance failed: {str(e)}"
        )


@router.get("/{basket_id}/flexibility-metrics")
async def get_flexibility_metrics(
    basket_id: UUID,
    workspace_id: str = Depends(get_current_workspace_id)
):
    """Get metrics about basket flexibility and accommodation."""
    try:
        metrics = await InconsistencyAccommodationService.generate_flexibility_metrics(
            basket_id, workspace_id
        )
        return metrics
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Flexibility metrics failed: {str(e)}"
        )


@router.post("/{basket_id}/comprehensive-analysis")
async def comprehensive_basket_analysis(
    basket_id: UUID,
    request: Optional[AgentBasketAnalysisRequest] = None,
    workspace_id: str = Depends(get_current_workspace_id)
):
    """Perform comprehensive basket analysis using infrastructure agent."""
    try:
        # Create agent for analysis
        agent = InfraBasketAnalyzerAgent("basket_analyzer", workspace_id)
        
        # Use provided request or create default
        if not request:
            request = AgentBasketAnalysisRequest(
                agent_id=agent.agent_id,
                agent_type=agent.agent_type,
                basket_id=basket_id,
                analysis_goals=["comprehensive_analysis"],
                respect_inconsistency=True,
                accommodate_messiness=True
            )
        else:
            # Ensure request matches URL parameters
            request.basket_id = basket_id
            request.agent_id = agent.agent_id
            request.agent_type = agent.agent_type
        
        report = await agent.analyze_basket_comprehensively(request)
        return report
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Comprehensive analysis failed: {str(e)}"
        )


@router.get("/{basket_id}/pattern-analysis-only")
async def pattern_analysis_only(
    basket_id: UUID,
    accommodate_inconsistency: bool = True,
    workspace_id: str = Depends(get_current_workspace_id)
):
    """Perform lightweight pattern-only analysis."""
    try:
        agent = InfraBasketAnalyzerAgent("pattern_analyzer", workspace_id)
        
        report = await agent.analyze_basket_patterns_only(
            basket_id, accommodate_inconsistency
        )
        return report
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Pattern analysis failed: {str(e)}"
        )


@router.get("/{basket_id}/improvement-suggestions")
async def get_improvement_suggestions(
    basket_id: UUID,
    user_requested: bool = False,
    workspace_id: str = Depends(get_current_workspace_id)
):
    """Get gentle improvement suggestions from agent."""
    try:
        agent = InfraBasketAnalyzerAgent("improvement_advisor", workspace_id)
        
        suggestions = await agent.suggest_basket_improvements(
            basket_id, user_requested
        )
        return {"suggestions": suggestions}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Improvement suggestions failed: {str(e)}"
        )


@router.get("/{basket_id}/gentle-connections")
async def get_gentle_connection_suggestions(
    basket_id: UUID,
    max_suggestions: int = 5,
    workspace_id: str = Depends(get_current_workspace_id)
):
    """Get gentle suggestions for document connections."""
    try:
        suggestions = await RelationshipDiscoveryService.suggest_gentle_connections(
            basket_id, workspace_id, max_suggestions
        )
        return {"connection_suggestions": suggestions}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Connection suggestions failed: {str(e)}"
        )


@router.get("/{basket_id}/document-clusters")
async def analyze_document_clusters(
    basket_id: UUID,
    workspace_id: str = Depends(get_current_workspace_id)
):
    """Identify natural document clusters without imposing structure."""
    try:
        clusters = await RelationshipDiscoveryService.analyze_document_clusters(
            basket_id, workspace_id
        )
        return {"clusters": clusters}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Document clustering failed: {str(e)}"
        )


@router.get("/{basket_id}/emergent-themes")
async def detect_emergent_themes(
    basket_id: UUID,
    sensitivity: str = "medium",
    workspace_id: str = Depends(get_current_workspace_id)
):
    """Detect emergent themes that don't fit standard patterns."""
    try:
        themes = await BasketPatternRecognitionService.detect_emergent_themes(
            basket_id, workspace_id, sensitivity
        )
        return {"emergent_themes": themes}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Emergent theme detection failed: {str(e)}"
        )


@router.get("/{basket_id}/improvement-readiness")
async def assess_improvement_readiness(
    basket_id: UUID,
    workspace_id: str = Depends(get_current_workspace_id)
):
    """Assess if basket is ready for improvement suggestions."""
    try:
        readiness = await ImprovementGuidanceService.assess_improvement_readiness(
            basket_id, workspace_id
        )
        return readiness
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Improvement readiness assessment failed: {str(e)}"
        )


@router.get("/{basket_id}/accommodation-examples")
async def get_accommodation_examples(
    basket_id: UUID,
    workspace_id: str = Depends(get_current_workspace_id)
):
    """Get examples of how inconsistencies are accommodated."""
    try:
        health = await InconsistencyAccommodationService.assess_context_health(
            basket_id, workspace_id
        )
        
        examples = []
        for inconsistency in health.inconsistencies:
            examples.append({
                "inconsistency_type": inconsistency.inconsistency_type,
                "description": inconsistency.description,
                "accommodation_strategy": inconsistency.accommodation_strategy,
                "user_benefit": inconsistency.user_benefit
            })
        
        return {"accommodation_examples": examples}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Accommodation examples failed: {str(e)}"
        )


@router.post("/batch-analysis")
async def batch_analyze_baskets(
    basket_ids: List[UUID],
    analysis_type: str = "patterns_only",
    workspace_id: str = Depends(get_current_workspace_id)
):
    """Analyze multiple baskets in batch."""
    try:
        agent = InfraBasketAnalyzerAgent("batch_analyzer", workspace_id)
        results = {}
        
        for basket_id in basket_ids:
            try:
                if analysis_type == "comprehensive":
                    result = await agent.analyze_basket_comprehensively(
                        AgentBasketAnalysisRequest(
                            agent_id=agent.agent_id,
                            agent_type=agent.agent_type,
                            basket_id=basket_id,
                            respect_inconsistency=True
                        )
                    )
                else:  # patterns_only
                    result = await agent.analyze_basket_patterns_only(basket_id)
                
                results[str(basket_id)] = result
                
            except Exception as e:
                results[str(basket_id)] = {"error": str(e)}
        
        return {"batch_results": results}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Batch analysis failed: {str(e)}"
        )