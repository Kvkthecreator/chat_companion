from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from ..utils.jwt import verify_jwt
from ..utils.workspace import get_or_create_workspace
from ..utils.supabase import supabase_admin

router = APIRouter(prefix="/mcp/baskets", tags=["mcp"])


class Fingerprint(BaseModel):
    embedding: List[float]
    summary: Optional[str] = None
    intent: Optional[str] = None
    entities: Optional[List[str]] = None
    keywords: Optional[List[str]] = None


class BasketInferenceRequest(BaseModel):
    tool: str = Field(..., description="Tool requesting basket inference")
    fingerprint: Fingerprint


class BasketSignatureModel(BaseModel):
    id: str
    name: Optional[str]
    embedding: List[float]
    summary: Optional[str]
    last_updated: Optional[str]


class BasketCandidateModel(BaseModel):
    signature: BasketSignatureModel
    recency_boost: float = 0.0
    user_affinity: float = 0.0
    conflict: bool = False


class BasketInferenceResponse(BaseModel):
    candidates: List[BasketCandidateModel]


def _resolve_workspace(request: Request, user: dict) -> str:
    workspace_id = getattr(request.state, "workspace_id", None)
    if workspace_id:
        return str(workspace_id)
    return str(get_or_create_workspace(user["user_id"]))


def _recency_boost(last_refreshed: Optional[str]) -> float:
    if not last_refreshed:
        return 0.0
    try:
        refreshed = datetime.fromisoformat(last_refreshed.replace("Z", "+00:00"))
    except ValueError:
        return 0.0

    diff_days = (datetime.now(timezone.utc) - refreshed).total_seconds() / (60 * 60 * 24)
    if diff_days <= 0:
        return 1.0
    if diff_days >= 30:
        return 0.0
    return max(0.0, 1.0 - (diff_days / 30.0))


@router.post("/infer", response_model=BasketInferenceResponse)
async def infer_basket(
    payload: BasketInferenceRequest,
    request: Request,
    user: dict = Depends(verify_jwt),
):
    if not payload.fingerprint.embedding:
        raise HTTPException(status_code=400, detail="fingerprint_missing_embedding")

    workspace_id = _resolve_workspace(request, user)

    sb = supabase_admin()
    signature_resp = (
        sb.table("basket_signatures")
        .select("basket_id, summary, anchors, entities, keywords, embedding, last_refreshed")
        .eq("workspace_id", workspace_id)
        .order("last_refreshed", desc=True)
        .limit(50)
        .execute()
    )

    rows = signature_resp.data or []
    if not rows:
        return BasketInferenceResponse(candidates=[])

    basket_ids = [row["basket_id"] for row in rows if row.get("basket_id")]

    basket_names: dict[str, str] = {}
    if basket_ids:
        info_resp = (
            sb.table("baskets")
            .select("id, name")
            .in_("id", basket_ids)
            .execute()
        )
        if info_resp.data:
            for record in info_resp.data:
                basket_names[str(record.get("id"))] = record.get("name")

    candidates: List[BasketCandidateModel] = []
    for row in rows:
        embedding = row.get("embedding") or []
        if not embedding:
            continue
        basket_id = str(row.get("basket_id"))
        basket_name = basket_names.get(basket_id) or "Untitled basket"
        candidate = BasketCandidateModel(
            signature=BasketSignatureModel(
                id=basket_id,
                name=basket_name,
                embedding=list(embedding),
                summary=row.get("summary"),
                last_updated=row.get("last_refreshed"),
            ),
            recency_boost=_recency_boost(row.get("last_refreshed")),
            user_affinity=0.0,
            conflict=False,
        )
        candidates.append(candidate)

    return BasketInferenceResponse(candidates=candidates[:20])


__all__ = ["router"]
