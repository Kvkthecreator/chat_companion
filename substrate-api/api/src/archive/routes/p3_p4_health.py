"""
P3/P4 Health Check Endpoints

Provides visibility into canon freshness and completeness.
Used by frontend to validate basket readiness and trigger regeneration.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from uuid import UUID

from infra.utils.supabase import supabase_admin
from infra.utils.jwt import verify_jwt
from lib.freshness import (
    get_basket_canons_health,
    should_regenerate_insight_canon,
    should_regenerate_document_canon
)

router = APIRouter(prefix="/health", tags=["p3-p4-health"])


# =============================================================================
# RESPONSE MODELS
# =============================================================================

class BasketCanonsHealthResponse(BaseModel):
    basket_id: str
    has_insight_canon: bool
    has_document_canon: bool
    insight_canon_stale: bool
    document_canon_stale: bool
    ready: bool
    insight_check: Dict[str, Any]
    doc_check: Dict[str, Any]


class WorkspaceCanonsHealthResponse(BaseModel):
    workspace_id: str
    baskets_checked: int
    baskets_ready: int
    baskets_missing_canons: int
    baskets_stale: int
    basket_health: List[BasketCanonsHealthResponse]


# =============================================================================
# HEALTH CHECK ENDPOINTS
# =============================================================================

@router.get("/basket/{basket_id}", response_model=BasketCanonsHealthResponse)
async def check_basket_health(
    basket_id: str,
    user: dict = Depends(verify_jwt)
):
    """
    Check health of required P3/P4 canons for a basket.

    Returns:
    - has_insight_canon: Does basket have current insight_canon?
    - has_document_canon: Does basket have document_canon?
    - insight_canon_stale: Is insight_canon out of date?
    - document_canon_stale: Is document_canon out of date?
    - ready: All canons exist and are fresh

    Use this endpoint to:
    1. Frontend basket page load validation
    2. Determine if "Generate Canon" button should show
    3. Display staleness warnings to user
    """
    supabase = supabase_admin()

    # Verify basket exists
    basket_result = supabase.table('baskets').select('id').eq('id', basket_id).execute()
    if not basket_result.data:
        raise HTTPException(status_code=404, detail="Basket not found")

    health = get_basket_canons_health(supabase, basket_id)

    return BasketCanonsHealthResponse(**health)


@router.get("/workspace/{workspace_id}", response_model=WorkspaceCanonsHealthResponse)
async def check_workspace_health(
    workspace_id: str,
    user: dict = Depends(verify_jwt)
):
    """
    Check health of P3/P4 canons across all baskets in a workspace.

    Returns aggregate stats:
    - baskets_checked: Total baskets in workspace
    - baskets_ready: Baskets with all canons fresh
    - baskets_missing_canons: Baskets without required canons
    - baskets_stale: Baskets with stale canons
    - basket_health: Array of individual basket health checks

    Use this endpoint to:
    1. Workspace dashboard overview
    2. Bulk regeneration planning
    3. Data quality monitoring
    """
    supabase = supabase_admin()

    # Get all baskets in workspace
    baskets_result = supabase.table('baskets').select('id').eq('workspace_id', workspace_id).execute()

    if not baskets_result.data:
        return WorkspaceCanonsHealthResponse(
            workspace_id=workspace_id,
            baskets_checked=0,
            baskets_ready=0,
            baskets_missing_canons=0,
            baskets_stale=0,
            basket_health=[]
        )

    basket_health = []
    baskets_ready = 0
    baskets_missing = 0
    baskets_stale = 0

    for basket in baskets_result.data:
        health = get_basket_canons_health(supabase, basket['id'])
        basket_health.append(BasketCanonsHealthResponse(**health))

        if health['ready']:
            baskets_ready += 1
        elif not health['has_insight_canon'] or not health['has_document_canon']:
            baskets_missing += 1
        elif health['insight_canon_stale'] or health['document_canon_stale']:
            baskets_stale += 1

    return WorkspaceCanonsHealthResponse(
        workspace_id=workspace_id,
        baskets_checked=len(baskets_result.data),
        baskets_ready=baskets_ready,
        baskets_missing_canons=baskets_missing,
        baskets_stale=baskets_stale,
        basket_health=basket_health
    )


@router.get("/insight-canon/{basket_id}/staleness")
async def check_insight_canon_staleness(
    basket_id: str,
    user: dict = Depends(verify_jwt)
):
    """
    Detailed staleness check for insight_canon.

    Returns full staleness analysis including:
    - substrate_changed: Has substrate been modified?
    - graph_changed: Have relationships changed?
    - substrate_delta: Summary of what changed (if stale)
    - current_hashes: Current substrate_hash and graph_signature

    Use this endpoint to:
    1. Show detailed staleness reasons to user
    2. Decide whether to auto-regenerate
    3. Display "last updated X ago, substrate changed Y" messages
    """
    supabase = supabase_admin()

    basket_result = supabase.table('baskets').select('id').eq('id', basket_id).execute()
    if not basket_result.data:
        raise HTTPException(status_code=404, detail="Basket not found")

    staleness = should_regenerate_insight_canon(supabase, basket_id)

    return {
        "basket_id": basket_id,
        "stale": staleness['stale'],
        "reasons": staleness['reasons'],
        "current_canon": staleness.get('current_canon'),
        "substrate_delta": staleness.get('substrate_delta'),
        "current_substrate_hash": staleness.get('current_substrate_hash'),
        "current_graph_signature": staleness.get('current_graph_signature')
    }


@router.get("/document-canon/{basket_id}/staleness")
async def check_document_canon_staleness(
    basket_id: str,
    user: dict = Depends(verify_jwt)
):
    """
    Detailed staleness check for document_canon.

    Returns:
    - insight_canon_regenerated: Has insight_canon been updated since document?
    - substrate_changed: Has substrate changed since document composition?

    Use this endpoint to:
    1. Determine if document needs recomposition
    2. Show "Document out of sync with latest insights" warnings
    """
    supabase = supabase_admin()

    basket_result = supabase.table('baskets').select('id').eq('id', basket_id).execute()
    if not basket_result.data:
        raise HTTPException(status_code=404, detail="Basket not found")

    staleness = should_regenerate_document_canon(supabase, basket_id)

    return {
        "basket_id": basket_id,
        "stale": staleness['stale'],
        "reasons": staleness['reasons'],
        "current_canon": staleness.get('current_canon'),
        "current_substrate_hash": staleness.get('current_substrate_hash')
    }
