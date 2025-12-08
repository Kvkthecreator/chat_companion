from uuid import UUID

from fastapi import APIRouter, HTTPException
from postgrest.exceptions import APIError
from pydantic import BaseModel

# Legacy runtime agent removed - use canonical queue processor
from src.services.canonical_queue_processor import get_canonical_queue_health

from ..utils.supabase_client import supabase_client as supabase

router = APIRouter(prefix="/agents", tags=["agents"])


class AgentRunPayload(BaseModel):
    basket_id: UUID


@router.post("/{name}/run")
async def run_agent(name: str, payload: AgentRunPayload):
    res = (
        supabase.table("baskets")
        .select("id")
        .eq("id", str(payload.basket_id))
        .execute()
    )
    if not res.data:  # type: ignore[attr-defined]
        raise HTTPException(status_code=404, detail="basket not found")

    # Legacy agent runner removed - use canonical queue processor
    try:
        if name == "canonical_queue":
            result = await get_canonical_queue_health()
        else:
            raise HTTPException(status_code=404, detail="Agent not found. Use 'canonical_queue' for health check.")
    except APIError as err:
        raise HTTPException(status_code=500, detail=str(err)) from err
    return result
