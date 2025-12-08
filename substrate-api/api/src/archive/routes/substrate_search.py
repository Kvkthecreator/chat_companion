"""
Substrate semantic search routes for Claude Agent SDK MCP tools.

Provides semantic search endpoints that wrap the semantic_primitives.py service.
These endpoints are called by work-platform MCP tools to query the knowledge substrate.

Pattern: Service-to-service + user JWT auth supported
"""

from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..utils.service_auth import verify_user_or_service
from ..utils.supabase_client import supabase_admin_client
from services.semantic_primitives import semantic_search, SemanticSearchFilters

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/substrate", tags=["substrate-search"])


# ============================================================================
# Pydantic Schemas
# ============================================================================


class SemanticSearchRequest(BaseModel):
    """Request schema for semantic search."""

    basket_id: str
    query_text: str = Field(..., min_length=1, description="Natural language query")
    filters: dict = Field(default_factory=dict, description="Search filters")
    limit: int = Field(20, ge=1, le=100, description="Maximum results")


class BlockSearchResult(BaseModel):
    """Result schema for search results."""

    id: str
    basket_id: str
    content: str
    semantic_type: str
    anchor_role: Optional[str]
    state: str
    metadata: dict
    similarity_score: float


class SemanticSearchResponse(BaseModel):
    """Response schema for semantic search."""

    blocks: List[BlockSearchResult]
    total: int
    basket_id: str
    query: str


# ============================================================================
# Helper Functions
# ============================================================================


async def get_workspace_id_from_basket(basket_id: str) -> str:
    """Get workspace_id for a basket (for authorization)."""
    if not supabase_admin_client:
        raise HTTPException(status_code=500, detail="Supabase client not initialized")

    result = supabase_admin_client.table("baskets").select("workspace_id").eq("id", basket_id).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Basket not found")

    return result.data["workspace_id"]


async def verify_workspace_access(basket_id: str, auth_info: dict) -> str:
    """
    Verify caller has access to basket's workspace.

    For user JWT: Checks workspace membership.
    For service auth: Trusts the service (work-platform already verified).
    """
    workspace_id = await get_workspace_id_from_basket(basket_id)

    # Service-to-service auth bypasses membership check
    if auth_info.get("is_service"):
        logger.debug(f"Service {auth_info.get('service_name')} accessing basket {basket_id}")
        return workspace_id

    # Check workspace membership for user auth
    user_id = auth_info.get("user_id") or auth_info.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid authentication")

    result = (
        supabase_admin_client.table("workspace_memberships")
        .select("workspace_id")
        .eq("workspace_id", workspace_id)
        .eq("user_id", user_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=403, detail="Access denied to basket's workspace")

    return workspace_id


# ============================================================================
# Substrate Search Endpoint
# ============================================================================


@router.post("/search", response_model=SemanticSearchResponse)
async def search_substrate_blocks(
    request: SemanticSearchRequest,
):
    """
    Semantic search across substrate blocks.

    This endpoint is called by work-platform MCP tools to query the knowledge substrate.
    Uses vector similarity + structured filters for hybrid search.

    Args:
        request: Search request (basket_id, query_text, filters, limit)

    Returns:
        List of blocks with similarity scores, sorted by relevance

    Note: Phase 1 - Auth temporarily disabled via exempt_prefixes.
          In production, should use verify_user_or_service dependency.
    """
    try:
        # Phase 1: Skip workspace access verification (endpoint is exempt from auth)
        # await verify_workspace_access(request.basket_id, auth_info)

        # Parse filters
        filters = SemanticSearchFilters(
            semantic_types=request.filters.get("semantic_types"),
            anchor_roles=request.filters.get("anchor_roles"),
            states=request.filters.get("states"),
            min_similarity=request.filters.get("min_similarity", 0.70),
        )

        # Execute semantic search
        results = await semantic_search(
            supabase=supabase_admin_client,
            basket_id=request.basket_id,
            query_text=request.query_text,
            filters=filters,
            limit=request.limit,
        )

        # Convert to response format
        blocks = [
            BlockSearchResult(
                id=block.id,
                basket_id=block.basket_id,
                content=block.content,
                semantic_type=block.semantic_type,
                anchor_role=block.anchor_role,
                state=block.state,
                metadata=block.metadata,
                similarity_score=block.similarity_score,
            )
            for block in results
        ]

        logger.info(
            f"Semantic search in basket {request.basket_id}: query='{request.query_text[:50]}...', results={len(blocks)}"
        )

        return SemanticSearchResponse(
            blocks=blocks,
            total=len(blocks),
            basket_id=request.basket_id,
            query=request.query_text,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Semantic search failed: {str(e)}")
