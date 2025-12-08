"""
Agent Memory API - Canonical Pipeline Interface (Canon v3.1)

Provides access to canonical pipeline agents (P1, P3) for substrate operations.
All legacy services have been replaced with canonical agents.

Canon v3.1: P2 Graph/Relationships removed - replaced by Neural Map.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Legacy services replaced with canonical pipeline agents
from ..agents.pipeline.improved_substrate_agent import ImprovedP1SubstrateAgent
from ..agents.pipeline.reflection_agent import P3ReflectionAgent

router = APIRouter(prefix="/agents", tags=["agent-memory"])


class SubstrateStatus(BaseModel):
    """Status of canonical substrate pipeline (Canon v3.1)."""
    p1_substrate_active: bool
    p3_reflection_active: bool
    canonical_version: str


@router.get("/substrate/status", response_model=SubstrateStatus)
async def get_substrate_status():
    """Get status of canonical substrate pipeline agents (Canon v3.1)."""

    # Check if canonical agents are available
    try:
        p1_agent = ImprovedP1SubstrateAgent()
        p3_agent = P3ReflectionAgent()

        return SubstrateStatus(
            p1_substrate_active=True,
            p3_reflection_active=True,
            canonical_version="v3.1"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Canonical agents not available: {str(e)}"
        )


@router.get("/health")
async def agent_memory_health():
    """Health check for canonical agent memory system (Canon v3.1)."""
    return {
        "status": "healthy",
        "message": "Canonical pipeline agents (P1, P3) active",
        "architecture": "canonical_v3.1",
        "legacy_services": "removed",
        "p2_graph": "removed (replaced by Neural Map)"
    }