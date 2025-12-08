import logging

from fastapi import APIRouter, HTTPException

from infra.utils.supabase_client import supabase_client as supabase

router = APIRouter(prefix="/debug", tags=["debug"])

logger = logging.getLogger("uvicorn.error")


@router.get("/{basket_id}")
async def get_trace(basket_id: str):
    try:
        resp = (
            supabase.table("agent_events")
            .select("*")
            .eq("basket_id", basket_id)
            .order("created_at")
            .execute()
        )
        return resp.data
    except Exception:
        logger.exception("get_trace failed")
        raise HTTPException(status_code=500, detail="internal error")
