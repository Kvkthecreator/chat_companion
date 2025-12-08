"""
Canon-Pure P4 Composition Agent Endpoint

Direct artifact operations for document composition - NO governance required per Canon v2.3
P4 operates directly on the artifact layer without substrate governance overhead
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
from uuid import UUID

from app.agents.pipeline.composition_agent_v2 import P4CompositionAgent, CompositionRequest
from middleware.service_auth import verify_service_role

logger = logging.getLogger("uvicorn.error")

router = APIRouter(tags=["p4-composition"], prefix="/agents")

class P4CompositionRequestDto(BaseModel):
    document_id: str = Field(..., description="Target document ID")
    basket_id: str = Field(..., description="Basket context")
    workspace_id: str = Field(..., description="Workspace context")
    intent: str = Field(default="", description="Composition intent")
    target_audience: Optional[str] = Field(default=None, description="Target audience for composition")
    tone: Optional[str] = Field(default=None, description="Desired tone (e.g., strategic, friendly, concise)")
    purpose: Optional[str] = Field(default=None, description="External purpose (e.g., shareable_overview, external_host_reasoning)")
    window: Optional[dict] = Field(default={"days": 90}, description="Memory window")
    pinned_ids: List[str] = Field(default=[], description="Pinned substrate IDs")
    operation_type: str = Field(default="compose", description="Operation type: compose or recompose")

class P4CompositionResponseDto(BaseModel):
    success: bool
    document_id: str
    message: str
    substrate_count: int = 0
    confidence: float = 0.0
    processing_time_ms: int = 0
    version_hash: Optional[str] = None
    summary: Optional[str] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)
    timeline_event_emitted: bool = False
    substrate_references_created: int = 0

@router.post("/p4-composition", response_model=P4CompositionResponseDto)
async def compose_document(
    request: P4CompositionRequestDto,
    service_role_verified: bool = Depends(verify_service_role)
):
    """
    Canon-Pure P4 Document Composition
    
    Direct artifact operation - bypasses governance per Canon v2.3
    Creates or updates document content by composing from substrate
    """
    logger.info(f"P4 composition request: document_id={request.document_id}, operation={request.operation_type}")
    
    try:
        # Initialize P4 composition agent
        p4_agent = P4CompositionAgent()
        
        # Create composition request
        composition_request = CompositionRequest(
            document_id=UUID(request.document_id),
            basket_id=UUID(request.basket_id),
            workspace_id=UUID(request.workspace_id),
            intent=request.intent,
            target_audience=request.target_audience,
            tone=request.tone,
            purpose=request.purpose,
            window=request.window,
            pinned_ids=[UUID(pid) for pid in request.pinned_ids] if request.pinned_ids else []
        )
        
        # Execute P4 composition (direct artifact operation)
        result = await p4_agent.process(composition_request)
        
        if not result.success:
            logger.error(f"P4 composition failed: {result.message}")
            raise HTTPException(status_code=500, detail=f"Composition failed: {result.message}")
        
        logger.info(f"P4 composition completed successfully: {result.message}")
        
        data = result.data or {}

        return P4CompositionResponseDto(
            success=True,
            document_id=request.document_id,
            message=result.message,
            substrate_count=data.get('substrate_count', 0),
            confidence=data.get('confidence', 0.0),
            processing_time_ms=data.get('processing_time_ms', 0),
            version_hash=data.get('version_hash'),
            summary=data.get('composition_summary'),
            metrics=data.get('phase1_metrics', {}),
            timeline_event_emitted=data.get('timeline_emitted', False),
            substrate_references_created=data.get('substrate_references_created', 0)
        )
        
    except ValueError as e:
        logger.error(f"P4 composition validation error: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception(f"P4 composition error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal composition error: {str(e)}")

@router.get("/p4-composition/health")
async def p4_health():
    """Health check for P4 composition agent"""
    try:
        agent = P4CompositionAgent()
        agent_info = agent.get_agent_info() if hasattr(agent, 'get_agent_info') else {"status": "available"}
        
        return {
            "status": "healthy",
            "agent": "P4CompositionAgent",
            "canon_version": "v2.3",
            "operation_mode": "direct_artifact",
            "agent_info": agent_info
        }
    except Exception as e:
        logger.error(f"P4 health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"P4 agent unavailable: {str(e)}")
