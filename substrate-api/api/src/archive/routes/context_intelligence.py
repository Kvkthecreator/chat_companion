"""Context intelligence API routes for composition intelligence."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from ..context.services.composition_intelligence import CompositionIntelligenceService
from ..context.services.context_hierarchy import ContextHierarchyService
from ..context.services.intent_analyzer import IntentAnalyzerService
from ..context.services.context_discovery import ContextDiscoveryService
from src.schemas.context_composition_schema import (
    CompositionIntelligenceReport,
    CompositionReadinessAssessment,
    ContextDiscoveryRequest,
    ContextDiscoveryResult,
    IntentAnalysisResult
)
from ..models.context import ContextHierarchy, CompositionIntent
from ..dependencies import get_current_user

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/api/context-intelligence", tags=["Context Intelligence"])


# Request/Response Models
class AnalyzeCompositionIntelligenceRequest(BaseModel):
    basket_id: UUID
    workspace_id: str
    analysis_focus: str = Field(default="comprehensive", pattern="^(comprehensive|intent|hierarchy|discovery)$")


class AssessCompositionReadinessRequest(BaseModel):
    basket_id: UUID
    workspace_id: str


class AnalyzeContextHierarchyRequest(BaseModel):
    basket_id: UUID
    workspace_id: str


class EnhanceContextHierarchyRequest(BaseModel):
    basket_id: UUID
    workspace_id: str
    auto_promote: bool = False


class PromoteContextLevelRequest(BaseModel):
    context_id: UUID
    new_level: str = Field(pattern="^(primary|secondary|supporting)$")
    workspace_id: str
    reasoning: Optional[str] = None


class RebalanceHierarchyWeightsRequest(BaseModel):
    basket_id: UUID
    workspace_id: str


class AnalyzeIntentRequest(BaseModel):
    basket_id: UUID
    workspace_id: str
    analysis_depth: str = Field(default="comprehensive", pattern="^(basic|comprehensive|deep)$")


class ProfileIntentRequest(BaseModel):
    basket_id: UUID
    workspace_id: str
    intent_override: Optional[str] = None


class SuggestIntentEnhancementsRequest(BaseModel):
    basket_id: UUID
    workspace_id: str
    target_intent: Optional[str] = None


class DiscoverCompositionRelevantMemoryRequest(BaseModel):
    basket_id: UUID
    composition_intent: str
    workspace_id: str
    max_results: int = Field(default=15, ge=1, le=50)


class DiscoverSemanticClustersRequest(BaseModel):
    basket_id: UUID
    workspace_id: str
    cluster_threshold: float = Field(default=0.6, ge=0.0, le=1.0)


# Composition Intelligence Endpoints
@router.post("/analyze", response_model=CompositionIntelligenceReport)
async def analyze_composition_intelligence(
    request: AnalyzeCompositionIntelligenceRequest,
    current_user = Depends(get_current_user)
):
    """Perform comprehensive composition intelligence analysis."""
    
    try:
        report = await CompositionIntelligenceService.analyze_composition_intelligence(
            basket_id=request.basket_id,
            workspace_id=request.workspace_id,
            analysis_focus=request.analysis_focus
        )
        
        logger.info(f"Composition intelligence analysis completed for basket {request.basket_id}")
        return report
        
    except Exception as e:
        logger.exception(f"Failed to analyze composition intelligence: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze composition intelligence: {str(e)}"
        )


@router.post("/readiness", response_model=CompositionReadinessAssessment)
async def assess_composition_readiness(
    request: AssessCompositionReadinessRequest,
    current_user = Depends(get_current_user)
):
    """Assess how ready a basket is for composition."""
    
    try:
        assessment = await CompositionIntelligenceService.assess_composition_readiness(
            basket_id=request.basket_id,
            workspace_id=request.workspace_id
        )
        
        logger.info(f"Composition readiness assessed for basket {request.basket_id}: {assessment.readiness_score:.2f}")
        return assessment
        
    except Exception as e:
        logger.exception(f"Failed to assess composition readiness: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to assess composition readiness: {str(e)}"
        )


# Context Hierarchy Endpoints
@router.post("/hierarchy/analyze", response_model=ContextHierarchy)
async def analyze_context_hierarchy(
    request: AnalyzeContextHierarchyRequest,
    current_user = Depends(get_current_user)
):
    """Analyze and create context hierarchy for composition intelligence."""
    
    try:
        hierarchy = await ContextHierarchyService.analyze_context_hierarchy(
            basket_id=request.basket_id,
            workspace_id=request.workspace_id
        )
        
        logger.info(f"Context hierarchy analyzed for basket {request.basket_id}")
        return hierarchy
        
    except Exception as e:
        logger.exception(f"Failed to analyze context hierarchy: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze context hierarchy: {str(e)}"
        )


@router.post("/hierarchy/enhance", response_model=ContextHierarchy)
async def enhance_context_hierarchy(
    request: EnhanceContextHierarchyRequest,
    current_user = Depends(get_current_user)
):
    """Enhance existing context hierarchy with intelligent promotions and adjustments."""
    
    try:
        enhanced_hierarchy = await ContextHierarchyService.enhance_context_hierarchy(
            basket_id=request.basket_id,
            workspace_id=request.workspace_id,
            auto_promote=request.auto_promote
        )
        
        logger.info(f"Context hierarchy enhanced for basket {request.basket_id}")
        return enhanced_hierarchy
        
    except Exception as e:
        logger.exception(f"Failed to enhance context hierarchy: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to enhance context hierarchy: {str(e)}"
        )


@router.post("/hierarchy/promote")
async def promote_context_level(
    request: PromoteContextLevelRequest,
    current_user = Depends(get_current_user)
):
    """Promote or demote a context to a different hierarchy level."""
    
    try:
        result = await ContextHierarchyService.promote_context_level(
            context_id=request.context_id,
            new_level=request.new_level,
            workspace_id=request.workspace_id,
            reasoning=request.reasoning
        )
        
        logger.info(f"Context {request.context_id} promoted to {request.new_level}")
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to promote context level: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to promote context level: {str(e)}"
        )


@router.post("/hierarchy/rebalance")
async def rebalance_hierarchy_weights(
    request: RebalanceHierarchyWeightsRequest,
    current_user = Depends(get_current_user)
):
    """Rebalance composition weights within the context hierarchy."""
    
    try:
        result = await ContextHierarchyService.rebalance_hierarchy_weights(
            basket_id=request.basket_id,
            workspace_id=request.workspace_id
        )
        
        logger.info(f"Hierarchy weights rebalanced for basket {request.basket_id}")
        return result
        
    except Exception as e:
        logger.exception(f"Failed to rebalance hierarchy weights: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to rebalance hierarchy weights: {str(e)}"
        )


# Intent Analysis Endpoints
@router.post("/intent/analyze", response_model=IntentAnalysisResult)
async def analyze_composition_intent(
    request: AnalyzeIntentRequest,
    current_user = Depends(get_current_user)
):
    """Analyze composition intent from basket memory."""
    
    try:
        intent_result = await IntentAnalyzerService.analyze_composition_intent(
            basket_id=request.basket_id,
            workspace_id=request.workspace_id,
            analysis_depth=request.analysis_depth
        )
        
        logger.info(f"Composition intent analyzed for basket {request.basket_id}")
        return intent_result
        
    except Exception as e:
        logger.exception(f"Failed to analyze composition intent: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze composition intent: {str(e)}"
        )


@router.post("/intent/profile", response_model=CompositionIntent)
async def profile_composition_intent(
    request: ProfileIntentRequest,
    current_user = Depends(get_current_user)
):
    """Create a detailed composition intent profile."""
    
    try:
        intent_profile = await IntentAnalyzerService.profile_composition_intent(
            basket_id=request.basket_id,
            workspace_id=request.workspace_id,
            intent_override=request.intent_override
        )
        
        logger.info(f"Composition intent profiled for basket {request.basket_id}")
        return intent_profile
        
    except Exception as e:
        logger.exception(f"Failed to profile composition intent: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to profile composition intent: {str(e)}"
        )


@router.post("/intent/enhance")
async def suggest_intent_enhancements(
    request: SuggestIntentEnhancementsRequest,
    current_user = Depends(get_current_user)
):
    """Suggest enhancements to clarify composition intent."""
    
    try:
        suggestions = await IntentAnalyzerService.suggest_intent_enhancements(
            basket_id=request.basket_id,
            workspace_id=request.workspace_id,
            target_intent=request.target_intent
        )
        
        logger.info(f"Intent enhancement suggestions generated for basket {request.basket_id}")
        return {"suggestions": suggestions}
        
    except Exception as e:
        logger.exception(f"Failed to suggest intent enhancements: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to suggest intent enhancements: {str(e)}"
        )


# Context Discovery Endpoints
@router.post("/discover/blocks", response_model=ContextDiscoveryResult)
async def discover_relevant_blocks(
    request: ContextDiscoveryRequest,
    current_user = Depends(get_current_user)
):
    """Discover blocks relevant to target contexts."""
    
    try:
        # Validate workspace access
        discovery_result = await ContextDiscoveryService.discover_relevant_blocks(
            request=request,
            workspace_id=request.workspace_id
        )
        
        logger.info(f"Block discovery completed for basket {request.basket_id}")
        return discovery_result
        
    except Exception as e:
        logger.exception(f"Failed to discover relevant blocks: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to discover relevant blocks: {str(e)}"
        )


@router.post("/discover/composition-memory", response_model=ContextDiscoveryResult)
async def discover_composition_relevant_memory(
    request: DiscoverCompositionRelevantMemoryRequest,
    current_user = Depends(get_current_user)
):
    """Discover memory relevant to a specific composition intent."""
    
    try:
        discovery_result = await ContextDiscoveryService.discover_composition_relevant_memory(
            basket_id=request.basket_id,
            composition_intent=request.composition_intent,
            workspace_id=request.workspace_id,
            max_results=request.max_results
        )
        
        logger.info(f"Composition memory discovery completed for basket {request.basket_id}")
        return discovery_result
        
    except Exception as e:
        logger.exception(f"Failed to discover composition-relevant memory: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to discover composition-relevant memory: {str(e)}"
        )


@router.post("/discover/semantic-clusters")
async def discover_semantic_clusters(
    request: DiscoverSemanticClustersRequest,
    current_user = Depends(get_current_user)
):
    """Discover semantic clusters of related memory objects."""
    
    try:
        clusters = await ContextDiscoveryService.discover_semantic_clusters(
            basket_id=request.basket_id,
            workspace_id=request.workspace_id,
            cluster_threshold=request.cluster_threshold
        )
        
        logger.info(f"Semantic cluster discovery completed for basket {request.basket_id}")
        return {"clusters": clusters}
        
    except Exception as e:
        logger.exception(f"Failed to discover semantic clusters: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to discover semantic clusters: {str(e)}"
        )


# Utility Endpoints
@router.get("/health")
async def health_check():
    """Health check endpoint for context intelligence services."""
    return {
        "status": "healthy",
        "service": "context-intelligence",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "composition_analysis",
            "readiness_assessment", 
            "context_hierarchy",
            "intent_analysis",
            "context_discovery"
        ]
    }


@router.get("/capabilities")
async def get_capabilities():
    """Get available context intelligence capabilities."""
    return {
        "analysis_focuses": ["comprehensive", "intent", "hierarchy", "discovery"],
        "analysis_depths": ["basic", "comprehensive", "deep"],
        "hierarchy_levels": ["primary", "secondary", "supporting"],
        "intent_types": [
            "strategic_analysis",
            "technical_guide", 
            "executive_summary",
            "creative_brief",
            "research_report",
            "action_plan",
            "product_specification",
            "meeting_summary"
        ],
        "audience_types": ["executives", "engineers", "designers", "product", "general"],
        "style_types": ["formal", "conversational", "detailed"],
        "scope_types": ["overview", "deep_dive", "action_items"]
    }