from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Annotated, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..utils.jwt import verify_jwt
from ..utils.supabase import supabase_admin
from ..utils.workspace import get_or_create_workspace

router = APIRouter(prefix="/mcp/auth", tags=["mcp-auth"])


class StoreSessionRequest(BaseModel):
    mcp_token: str
    supabase_token: str
    user_id: str
    expires_in_days: int = 90  # Default to 90 days for MCP tokens


class ValidateSessionRequest(BaseModel):
    mcp_token: str


class SessionResponse(BaseModel):
    supabase_token: str
    workspace_id: str
    user_id: str
    expires_at: str


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _expires_at(days: int = 90) -> str:
    """Generate expiration timestamp (default 90 days from now)"""
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


@router.post("/sessions", status_code=201)
async def store_session(
    payload: StoreSessionRequest,
    user: Annotated[dict, Depends(verify_jwt)]
):
    """
    Store OAuth session mapping: MCP token → Supabase token + workspace

    Called by the MCP adapter after successful OAuth token exchange.
    """
    workspace_id = get_or_create_workspace(payload.user_id)
    sb = supabase_admin()

    # Check if session already exists (update instead of insert)
    existing = (
        sb.table("mcp_oauth_sessions")
        .select("id")
        .eq("mcp_token", payload.mcp_token)
        .limit(1)
        .execute()
    )

    # Use configurable expiration (default 90 days for MCP)
    expires_at = _expires_at(payload.expires_in_days)

    if existing.data:
        # Update existing session
        update_resp = (
            sb.table("mcp_oauth_sessions")
            .update({
                "supabase_token": payload.supabase_token,
                "user_id": payload.user_id,
                "workspace_id": workspace_id,
                "expires_at": expires_at,
                "last_used_at": _now_iso(),
            })
            .eq("mcp_token", payload.mcp_token)
            .execute()
        )
        if update_resp.error:
            raise HTTPException(status_code=500, detail="Failed to update session")
    else:
        # Create new session
        insert_payload = {
            "id": str(uuid4()),
            "mcp_token": payload.mcp_token,
            "supabase_token": payload.supabase_token,
            "user_id": payload.user_id,
            "workspace_id": workspace_id,
            "expires_at": expires_at,
            "created_at": _now_iso(),
            "last_used_at": _now_iso(),
        }

        insert_resp = sb.table("mcp_oauth_sessions").insert(insert_payload).execute()

        if getattr(insert_resp, "error", None):
            raise HTTPException(status_code=500, detail="Failed to store session")

    return {
        "success": True,
        "workspace_id": workspace_id,
        "expires_at": expires_at,
    }


@router.post("/sessions/validate", response_model=SessionResponse)
async def validate_session(payload: ValidateSessionRequest):
    """
    Validate MCP OAuth token and return associated Supabase session

    Called by the MCP adapter on every SSE connection or tool invocation.
    No auth required (this IS the auth check).
    """
    sb = supabase_admin()

    resp = (
        sb.table("mcp_oauth_sessions")
        .select("supabase_token, workspace_id, user_id, expires_at, last_used_at")
        .eq("mcp_token", payload.mcp_token)
        .limit(1)
        .execute()
    )

    if not resp.data:
        raise HTTPException(status_code=401, detail="Invalid or expired MCP token")

    session = resp.data[0]
    expires_at = session.get("expires_at")

    # Check expiration and auto-renew if close to expiry
    should_renew = False
    if expires_at:
        try:
            exp_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)

            if now > exp_dt:
                raise HTTPException(status_code=401, detail="MCP token expired")

            # Auto-renew if within 7 days of expiration (rolling window)
            days_until_expiry = (exp_dt - now).days
            if days_until_expiry < 7:
                should_renew = True
        except ValueError:
            pass  # Invalid date format, allow through

    # Update last_used_at and optionally renew expiration
    update_data = {"last_used_at": _now_iso()}
    if should_renew:
        update_data["expires_at"] = _expires_at(90)  # Extend by another 90 days

    sb.table("mcp_oauth_sessions").update(update_data).eq("mcp_token", payload.mcp_token).execute()

    return SessionResponse(
        supabase_token=session["supabase_token"],
        workspace_id=session["workspace_id"],
        user_id=session["user_id"],
        expires_at=session.get("expires_at", ""),
    )


@router.delete("/sessions/{mcp_token}", status_code=204)
async def revoke_session(
    mcp_token: str,
    user: Annotated[dict, Depends(verify_jwt)]
):
    """
    Revoke an OAuth session

    User can revoke their own sessions via this endpoint.
    """
    workspace_id = get_or_create_workspace(user["user_id"])
    sb = supabase_admin()

    delete_resp = (
        sb.table("mcp_oauth_sessions")
        .delete()
        .eq("mcp_token", mcp_token)
        .eq("workspace_id", workspace_id)
        .execute()
    )

    if delete_resp.error:
        raise HTTPException(status_code=500, detail="Failed to revoke session")

    if not delete_resp.data:
        raise HTTPException(status_code=404, detail="Session not found")

    return None


__all__ = ["router"]
