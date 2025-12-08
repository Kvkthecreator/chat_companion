from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..utils.jwt import verify_jwt
from ..utils.supabase import supabase_admin
from ..utils.workspace import get_or_create_workspace

router = APIRouter(prefix="/integrations/tokens", tags=["integrations"])


class CreateTokenRequest(BaseModel):
    description: Optional[str] = None


def _hash_token(raw: str) -> str:
    import hashlib

    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.get("/")
async def list_tokens(user: Annotated[dict, Depends(verify_jwt)]):
    workspace_id = get_or_create_workspace(user["user_id"])
    sb = supabase_admin()
    resp = (
        sb.table("integration_tokens")
        .select("id, description, created_at, revoked_at, last_used_at")
        .eq("workspace_id", workspace_id)
        .order("created_at", desc=True)
        .execute()
    )
    data = resp.data or []
    return {"tokens": data}


@router.post("/", status_code=201)
async def create_token(
    payload: CreateTokenRequest,
    user: Annotated[dict, Depends(verify_jwt)]
):
    workspace_id = get_or_create_workspace(user["user_id"])
    sb = supabase_admin()

    import secrets

    raw_token = "yit_" + secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token)

    insert_payload = {
        "token_hash": token_hash,
        "user_id": user["user_id"],
        "workspace_id": workspace_id,
        "description": payload.description,
        "created_at": _now_iso(),
    }

    insert_resp = (
        sb.table("integration_tokens")
        .insert(insert_payload)
        .execute()
    )

    if getattr(insert_resp, "error", None):
        raise HTTPException(status_code=500, detail="Failed to create token")

    record_resp = (
        sb.table("integration_tokens")
        .select("id, description, created_at")
        .eq("token_hash", token_hash)
        .limit(1)
        .execute()
    )

    record_data = record_resp.data or []
    if not record_data:
        raise HTTPException(status_code=500, detail="Failed to load new token")

    record = record_data[0]
    return {
        "token": raw_token,
        "token_id": record["id"],
        "description": record.get("description"),
        "created_at": record.get("created_at"),
    }


@router.delete("/{token_id}", status_code=204)
async def revoke_token(token_id: str, user: Annotated[dict, Depends(verify_jwt)]):
    workspace_id = get_or_create_workspace(user["user_id"])
    sb = supabase_admin()

    update = sb.table("integration_tokens").update({
        "revoked_at": _now_iso(),
    }).eq("id", token_id).eq("workspace_id", workspace_id).execute()

    if update.error:
        raise HTTPException(status_code=500, detail="Failed to revoke token")

    if not update.data:
        raise HTTPException(status_code=404, detail="Token not found")

    return JSONResponse(status_code=204, content=None)


__all__ = ["router"]
