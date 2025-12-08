"""
Utility: look up (or lazily create) the caller’s workspace.

Authoritative rule:
‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
A user *always* operates inside exactly one workspace.
If they have none, we create one and add the caller as owner/member.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import HTTPException
from .supabase import supabase_admin

log = logging.getLogger("uvicorn.error")

def get_or_create_workspace(user_id: str) -> str:
    """
    Ensure the user operates in exactly one workspace.
    If no workspace exists → create one and add membership.
    """
    sb = supabase_admin()  # service role → bypass RLS
    
    # Validate user_id is a UUID
    try:
        uuid.UUID(user_id)
    except ValueError:
        log.error("Invalid user_id for workspace: %s", user_id)
        raise HTTPException(status_code=401, detail="Invalid user_id")

    # Try lookup first
    res = sb.table("workspaces").select("id").eq("owner_id", user_id).limit(1).execute()
    if res.data:
        wid = res.data[0]["id"]
        log.info("WS: found existing workspace id=%s for user=%s", wid, user_id)
        return wid

    # Create if missing (use select() to get id back)
    ins = (
        sb.table("workspaces")
        .insert({"owner_id": user_id, "name": f"{user_id[:6]}'s workspace", "is_demo": False})
        .select("id")
        .execute()
    )
    if not ins.data:
        log.error("WS: insert returned no row for user=%s", user_id)
        raise RuntimeError("workspace_insert_failed")

    wid = ins.data[0]["id"]
    log.info("WS: created workspace id=%s for user=%s", wid, user_id)
    return wid
