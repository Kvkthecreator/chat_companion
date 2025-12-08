from __future__ import annotations

import logging
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from ..utils.jwt import verify_jwt
from ..utils.supabase import supabase_admin
from ..utils.workspace import get_or_create_workspace

router = APIRouter(prefix="/memory/unassigned", tags=["memory"])
logger = logging.getLogger("uvicorn.error")
logger = logging.getLogger("uvicorn.error")


class UnassignedCreateRequest(BaseModel):
    workspace_id: str
    tool: str
    summary: Optional[str] = None
    payload: Optional[dict] = None
    fingerprint: Optional[dict] = None
    candidates: Optional[list[dict]] = None
    requested_by: Optional[str] = None
    source_host: Optional[str] = None
    source_session: Optional[str] = None


class UnassignedResolveRequest(BaseModel):
    status: str = Field(..., description="assigned|dismissed|pending")
    assigned_basket_id: Optional[str] = None


_SHARING_SECRET_HEADER = "x-yarnnn-mcp-secret"


def _require_shared_secret(request: Request):
    from ..routes.openai_apps import config as openai_config  # reuse shared secret helper

    expected = openai_config.sharedSecret or None
    provided = request.headers.get(_SHARING_SECRET_HEADER)
    if not expected or provided != expected:
        raise HTTPException(status_code=401, detail="invalid_shared_secret")


@router.get("/")
async def list_unassigned(user=Depends(verify_jwt)):
    workspace_id = get_or_create_workspace(user["user_id"])
    sb = supabase_admin()
    try:
        resp = (
            sb.table("mcp_unassigned_captures")
            .select("id, tool, summary, payload, fingerprint, candidates, status, assigned_basket_id, source_host, source_session, created_at")
            .eq("workspace_id", workspace_id)
            .eq("status", "pending")
            .order("created_at", desc=True)
            .execute()
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"unassigned_list_failed: {exc}") from exc

    return {"captures": resp.data or []}


@router.post("/")
async def create_unassigned(payload: UnassignedCreateRequest, request: Request):
    _require_shared_secret(request)

    sb = supabase_admin()
    record = {
        "workspace_id": payload.workspace_id,
        "tool": payload.tool,
        "summary": payload.summary,
        "payload": payload.payload,
        "fingerprint": payload.fingerprint,
        "candidates": payload.candidates,
        "requested_by": payload.requested_by,
        "source_host": payload.source_host,
        "source_session": payload.source_session,
    }

    try:
        sb.table("mcp_unassigned_captures").insert(record).execute()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"unassigned_create_failed: {exc}") from exc

    logger.info(
        "[unassigned:create] workspace=%s tool=%s summary=%s",
        payload.workspace_id,
        payload.tool,
        (payload.summary or "<empty>")[:120],
    )

    return {"status": "created"}


@router.post("/{capture_id}/resolve")
async def resolve_unassigned(capture_id: str, body: UnassignedResolveRequest, user=Depends(verify_jwt)):
    workspace_id = get_or_create_workspace(user["user_id"])
    sb = supabase_admin()

    record = {
        "status": body.status,
        "assigned_basket_id": body.assigned_basket_id,
        "resolved_at": datetime.utcnow().isoformat(),
        "resolved_by": user["user_id"],
    }

    try:
        resp = (
            sb.table("mcp_unassigned_captures")
            .update(record)
            .eq("id", capture_id)
            .eq("workspace_id", workspace_id)
            .execute()
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"unassigned_resolve_failed: {exc}") from exc

    if not resp.data:
        raise HTTPException(status_code=404, detail="capture_not_found")

    logger.info(
        "[unassigned:resolve] capture=%s status=%s basket=%s",
        capture_id,
        body.status,
        body.assigned_basket_id,
    )

    return {"status": "updated"}


__all__ = ["router"]
