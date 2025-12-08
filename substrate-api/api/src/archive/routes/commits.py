"""
/api/baskets/{basket_id}/commits
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from ..utils.supabase_client import supabase_client as supabase
from ..utils.jwt import verify_jwt
from ..utils.workspace import get_or_create_workspace

router = APIRouter(tags=["commits"])

logger = logging.getLogger("uvicorn.error")


def _commit_stats(cid: str) -> tuple[int | None, int | None, int | None]:
    try:
        new_blocks = (
            supabase.table("blocks")
            .select("id", count="exact")
            .eq("commit_id", cid)
            .execute()
            .count  # type: ignore[attr-defined]
        )
        supersedes = (
            supabase.table("block_change_queue")
            .select("id", count="exact")
            .eq("commit_id", cid)
            .execute()
            .count  # type: ignore[attr-defined]
        )
        edited_blocks = (
            supabase.table("blocks")
            .select("id", count="exact")
            .eq("commit_id", cid)
            .gt("version", 1)
            .execute()
            .count  # type: ignore[attr-defined]
        )
        return new_blocks, edited_blocks, supersedes
    except Exception as err:
        logger.exception("_commit_stats failed")
        raise HTTPException(status_code=500, detail="internal error") from err


@router.get("/baskets/{basket_id}/commits")
def list_commits(
    basket_id: str,
    limit: int = Query(20, le=100),
    offset: int = 0,
    user: dict = Depends(verify_jwt),
) -> list[dict]:
    try:
        workspace_id = get_or_create_workspace(user["user_id"])
        resp = (
            supabase.table("dump_commits")
            .select("*")
            .eq("basket_id", basket_id)
            .eq("workspace_id", workspace_id)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        commits = []
        for row in resp.data:  # type: ignore[attr-defined]
            nb, eb, sp = _commit_stats(row["id"])
            commits.append(
                {
                    "id": row["id"],
                    "created_at": row["created_at"],
                    "summary": row["summary"],
                    "new_blocks": nb,
                    "edited_blocks": eb,
                    "supersedes": sp,
                }
            )
        return commits
    except Exception as err:
        logger.exception("list_commits failed")
        raise HTTPException(status_code=500, detail="internal error") from err
