from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from ..utils.jwt import verify_jwt
from ..utils.supabase import supabase_admin
from ..utils.workspace import get_or_create_workspace

router = APIRouter(prefix="/mcp/activity", tags=["mcp"])

logger = logging.getLogger("uvicorn.error")

_SHARED_SECRET_HEADER = "x-yarnnn-mcp-secret"


class ActivityLogRequest(BaseModel):
    workspace_id: str = Field(..., description="Workspace scope for the event")
    user_id: Optional[str] = Field(None, description="User executing the tool, if known")
    tool: str = Field(..., description="Tool name")
    host: str = Field(..., description="Source host (claude, chatgpt, agent:<name>)")
    result: str = Field(..., description="success|queued|error")
    latency_ms: Optional[int] = None
    basket_id: Optional[str] = None
    selection_decision: Optional[str] = None
    selection_score: Optional[float] = None
    error_code: Optional[str] = None
    session_id: Optional[str] = None
    fingerprint_summary: Optional[str] = None
    metadata: Optional[dict] = None


class ActivitySummaryResponse(BaseModel):
    host: str
    last_seen_at: Optional[str]
    calls_last_hour: int
    errors_last_hour: int
    p95_latency_ms: Optional[float]


async def _require_shared_secret(request: Request):
    from ..routes.openai_apps import config as openai_config  # reuse central config

    expected = openai_config.sharedSecret or None
    provided = request.headers.get(_SHARED_SECRET_HEADER)
    if not expected or provided != expected:
        raise HTTPException(status_code=401, detail="invalid_shared_secret")


@router.post("/")
async def log_activity(payload: ActivityLogRequest, request: Request):
    await _require_shared_secret(request)

    record = {
        "workspace_id": payload.workspace_id,
        "user_id": payload.user_id,
        "tool": payload.tool,
        "host": payload.host,
        "result": payload.result,
        "latency_ms": payload.latency_ms,
        "basket_id": payload.basket_id,
        "selection_decision": payload.selection_decision,
        "selection_score": payload.selection_score,
        "error_code": payload.error_code,
        "session_id": payload.session_id,
        "fingerprint_summary": payload.fingerprint_summary,
        "metadata": payload.metadata,
        "created_at": datetime.utcnow().isoformat(),
    }

    try:
        supabase_admin().table("mcp_activity_logs").insert(record).execute()
        logger.info(
            "[mcp:activity] workspace=%s host=%s tool=%s result=%s latency=%s",
            payload.workspace_id,
            payload.host,
            payload.tool,
            payload.result,
            payload.latency_ms,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"activity_log_failed: {exc}") from exc

    return {"status": "logged"}


@router.get("/summary")
async def activity_summary(user=Depends(verify_jwt)):
    workspace_id = get_or_create_workspace(user["user_id"])
    try:
        response = (
            supabase_admin()
            .table("mcp_activity_host_recent")
            .select("host, last_seen_at, calls_last_hour, errors_last_hour, p95_latency_ms")
            .eq("workspace_id", workspace_id)
            .execute()
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"activity_summary_failed: {exc}") from exc

    rows = response.data or []
    return {"hosts": rows}


__all__ = ["router"]
