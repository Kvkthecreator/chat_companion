"""Narrative intelligence API routes for user-facing AI interactions."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from ..agents.pipeline.reflection_agent import P3ReflectionAgent
from ..agents.pipeline.presentation_agent import P4PresentationAgent
from ..dependencies import get_current_user

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/api/narrative-intelligence", tags=["Narrative Intelligence"])


# Request/Response Models
class ProjectUnderstandingRequest(BaseModel):
    basket_id: UUID
    workspace_id: str
    user_context: Optional[Dict[str, str]] = None


class AIAssistanceRequest(BaseModel):
    basket_id: UUID
    workspace_id: str
    user_query: Optional[str] = None
    user_context: Optional[Dict[str, str]] = None


class IntelligentGuidanceRequest(BaseModel):
    basket_id: UUID
    workspace_id: str
    focus_area: Optional[str] = Field(default=None, pattern="^(development|organization|creativity|completion)?$")
    user_goal: Optional[str] = None


class ProjectHealthRequest(BaseModel):
    basket_id: UUID
    workspace_id: str
    previous_analysis: Optional[Dict[str, Any]] = None


class ContextualNextStepsRequest(BaseModel):
    basket_id: UUID
    workspace_id: str
    user_goal: Optional[str] = None


# Response Models
class ProjectUnderstandingResponse(BaseModel):
    success: bool
    understanding: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class AIAssistanceResponse(BaseModel):
    success: bool
    response: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class IntelligentGuidanceResponse(BaseModel):
    success: bool
    guidance: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


class ProjectHealthResponse(BaseModel):
    success: bool
    health_assessment: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ContextualNextStepsResponse(BaseModel):
    success: bool
    next_steps: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# Project Understanding Endpoints
@router.post("/project-understanding", response_model=ProjectUnderstandingResponse)
async def get_project_understanding(
    request: ProjectUnderstandingRequest,
    current_user = Depends(get_current_user)
):
    """Get comprehensive project understanding from narrative agents."""
    
    try:
        result = await agent_get_project_understanding(
            basket_id=str(request.basket_id),
            workspace_id=request.workspace_id,
            user_context=request.user_context
        )
        
        logger.info(f"Project understanding generated for basket {request.basket_id}")
        return ProjectUnderstandingResponse(**result)
        
    except Exception as e:
        logger.exception(f"Failed to get project understanding: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get project understanding: {str(e)}"
        )


# AI Assistance Endpoints
@router.post("/ai-assistance", response_model=AIAssistanceResponse)
async def generate_ai_assistance(
    request: AIAssistanceRequest,
    current_user = Depends(get_current_user)
):
    """Generate conversational AI assistance."""
    
    try:
        result = await agent_generate_ai_assistance(
            basket_id=str(request.basket_id),
            workspace_id=request.workspace_id,
            user_query=request.user_query,
            user_context=request.user_context
        )
        
        logger.info(f"AI assistance generated for basket {request.basket_id}")
        return AIAssistanceResponse(**result)
        
    except Exception as e:
        logger.exception(f"Failed to generate AI assistance: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate AI assistance: {str(e)}"
        )


# Intelligent Guidance Endpoints
@router.post("/intelligent-guidance", response_model=IntelligentGuidanceResponse)
async def get_intelligent_guidance(
    request: IntelligentGuidanceRequest,
    current_user = Depends(get_current_user)
):
    """Get strategic guidance and recommendations."""
    
    try:
        result = await agent_get_intelligent_guidance(
            basket_id=str(request.basket_id),
            workspace_id=request.workspace_id,
            focus_area=request.focus_area,
            user_goal=request.user_goal
        )
        
        logger.info(f"Intelligent guidance generated for basket {request.basket_id}")
        return IntelligentGuidanceResponse(**result)
        
    except Exception as e:
        logger.exception(f"Failed to get intelligent guidance: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get intelligent guidance: {str(e)}"
        )


# Project Health Endpoints
@router.post("/project-health", response_model=ProjectHealthResponse)
async def assess_project_health(
    request: ProjectHealthRequest,
    current_user = Depends(get_current_user)
):
    """Assess project health and provide recommendations."""
    
    try:
        result = await agent_assess_project_health(
            basket_id=str(request.basket_id),
            workspace_id=request.workspace_id,
            previous_analysis=request.previous_analysis
        )
        
        logger.info(f"Project health assessed for basket {request.basket_id}")
        return ProjectHealthResponse(**result)
        
    except Exception as e:
        logger.exception(f"Failed to assess project health: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to assess project health: {str(e)}"
        )


# Contextual Next Steps Endpoints
@router.post("/next-steps", response_model=ContextualNextStepsResponse)
async def get_contextual_next_steps(
    request: ContextualNextStepsRequest,
    current_user = Depends(get_current_user)
):
    """Get contextual next steps based on current project state."""
    
    try:
        result = await agent_get_contextual_next_steps(
            basket_id=str(request.basket_id),
            workspace_id=request.workspace_id,
            user_goal=request.user_goal
        )
        
        logger.info(f"Contextual next steps generated for basket {request.basket_id}")
        return ContextualNextStepsResponse(**result)
        
    except Exception as e:
        logger.exception(f"Failed to get contextual next steps: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get contextual next steps: {str(e)}"
        )


# Utility Endpoints
@router.get("/health")
async def health_check():
    """Health check endpoint for narrative intelligence services."""
    return {
        "status": "healthy",
        "service": "narrative-intelligence",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "project_understanding",
            "ai_assistance",
            "intelligent_guidance",
            "project_health",
            "contextual_next_steps"
        ]
    }


@router.get("/capabilities")
async def get_capabilities():
    """Get available narrative intelligence capabilities."""
    return {
        "focus_areas": ["development", "organization", "creativity", "completion"],
        "guidance_timeframes": ["immediate", "short_term", "medium_term", "long_term"],
        "difficulty_levels": ["beginner_friendly", "moderate_effort", "advanced_focus"],
        "health_levels": ["excellent", "good", "developing", "needs_attention"],
        "progress_trajectories": ["accelerating", "steady", "slowing", "stalled"],
        "conversation_tones": ["helpful", "encouraging", "insightful", "collaborative", "strategic"],
        "assistant_personalities": ["curious_learner", "knowledgeable_guide", "strategic_partner", "creative_collaborator"],
        "engagement_levels": ["new_user", "exploring", "actively_building", "seeking_insights"],
        "conversation_flows": ["greeting", "guidance", "analysis_sharing", "problem_solving", "brainstorming"]
    }


# Dashboard Integration Endpoints
@router.get("/dashboard/{basket_id}")
async def get_dashboard_intelligence(
    basket_id: UUID,
    workspace_id: str = Query(...),
    current_user = Depends(get_current_user)
):
    """Get comprehensive intelligence for dashboard display."""
    
    try:
        # Get all narrative intelligence components
        understanding_result = await agent_get_project_understanding(
            basket_id=str(basket_id),
            workspace_id=workspace_id
        )
        
        guidance_result = await agent_get_intelligent_guidance(
            basket_id=str(basket_id),
            workspace_id=workspace_id
        )
        
        health_result = await agent_assess_project_health(
            basket_id=str(basket_id),
            workspace_id=workspace_id
        )
        
        next_steps_result = await agent_get_contextual_next_steps(
            basket_id=str(basket_id),
            workspace_id=workspace_id
        )
        
        # Combine results for dashboard
        dashboard_data = {
            "success": True,
            "dashboard": {
                "understanding": understanding_result.get("understanding") if understanding_result.get("success") else None,
                "guidance": guidance_result.get("guidance", [])[:3] if guidance_result.get("success") else [],  # Top 3 guidance items
                "health": health_result.get("health_assessment") if health_result.get("success") else None,
                "next_steps": next_steps_result.get("next_steps") if next_steps_result.get("success") else None,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        logger.info(f"Dashboard intelligence generated for basket {basket_id}")
        return dashboard_data
        
    except Exception as e:
        logger.exception(f"Failed to get dashboard intelligence: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get dashboard intelligence: {str(e)}"
        )