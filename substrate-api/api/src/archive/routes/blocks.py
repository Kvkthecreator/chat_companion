# ruff: noqa
import logging

from fastapi import APIRouter, Depends, HTTPException

from ..deps import get_db
from ..utils.jwt import verify_jwt
from ..utils.workspace import get_or_create_workspace

router = APIRouter(tags=["blocks"])

logger = logging.getLogger("uvicorn.error")

# Canon v2.2 Compliance Note:
# This module now only provides READ-ONLY block operations.
# All block mutations (create/update/delete) must flow through the Universal Work
# Orchestration system (/api/work) in the Next.js backend to ensure governance compliance.


@router.get("/blocks/by-basket/{basket_id}")
async def list_blocks(
    basket_id: str,
    user: dict = Depends(verify_jwt),
    db=Depends(get_db),  # noqa: B008
):
    """
    List blocks for a basket (user-facing endpoint with workspace filtering).

    Requires JWT auth. Filters blocks by user's workspace_id for security.

    Note: For service-to-service calls, use /api/baskets/{basket_id}/blocks instead
    (no auth required, returns all blocks in basket).
    """
    try:
        workspace_id = get_or_create_workspace(user["user_id"])

        # Direct SQL query (bypasses RLS, consistent with basket routes)
        query = """
            SELECT id, title, content, semantic_type, confidence_score, state, created_at, updated_at
            FROM blocks
            WHERE basket_id = :basket_id
            AND workspace_id = :workspace_id
            ORDER BY created_at DESC
        """

        results = await db.fetch_all(
            query,
            values={
                "basket_id": basket_id,
                "workspace_id": workspace_id,
            }
        )

        # Convert to dict format
        blocks = [dict(row) for row in results]
        return blocks

    except Exception as err:
        logger.exception("list_blocks failed")
        raise HTTPException(status_code=500, detail="internal error") from err



# REMOVED: PUT /blocks/{block_id} and DELETE /blocks/{block_id} endpoints
# 
# These endpoints bypassed Universal Work Orchestration governance and violated Canon v2.2.
# All block mutations must now flow through the Next.js /api/work endpoint to ensure
# proper governance evaluation, user-controlled execution modes, and confidence-informed routing.
#
# Migration path for clients:
# - Block updates: Use /api/work with work_type='MANUAL_EDIT'
# - Block deletions: Use /api/work with work_type='MANUAL_EDIT'  
# - Read operations: Continue using GET /api/baskets/{basket_id}/blocks (unchanged)