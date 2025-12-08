import json
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request

from src.utils.db import json_safe
from src.services.canonical_queue_processor import get_canonical_queue_health

# Legacy supabase helpers removed - use app.utils.supabase_client directly
from .utils.supabase_client import supabase_admin_client as supabase


# Phase 1 stubs
def build_payload(
    *,
    task_id: str,
    user_id: str,
    agent_type: str,
    message: dict,
    reason: str,
    trace: list,
) -> dict:
    """Simplified payload helper retained for logging."""
    return {
        "task_id": task_id,
        "user_id": user_id,
        "agent_type": agent_type,
        "message": message,
        "reason": reason,
        "trace": trace,
    }


router = APIRouter()

# Known agents mapped by name. Empty until agents are implemented.
AGENT_REGISTRY: dict[str, object] = {}


def log_agent_message(task_id, user_id, agent_type, message):
    try:
        supabase.table("agent_messages").insert(
            json_safe(
                {
                    "task_id": task_id,
                    "user_id": user_id,
                    "agent_type": agent_type,
                    "message_type": message.get("type", "text"),
                    "message_content": message,
                    "created_at": datetime.utcnow().isoformat(),
                }
            )
        ).execute()
    except Exception as e:
        print(f"[warn] Failed to log message to agent_messages: {e}")


async def run_agent(req: Request):
    """Placeholder implementation retained for compatibility."""
    raise HTTPException(501, "Manager agent not implemented")


async def run_agent_direct(req: Request):
    """Legacy agent runner replaced with canonical queue health check."""
    data = await req.json()
    
    agent_type = data.get("agent_type")
    user_id = data.get("user_id")
    
    if not user_id:
        raise HTTPException(422, "Missing 'user_id'")
    
    # Legacy agent runner removed - return canonical queue status
    if agent_type == "canonical_queue":
        health = await get_canonical_queue_health()
        return {"ok": True, "canonical_queue_health": health}
    else:
        raise HTTPException(501, f"Legacy agent runner removed. Agent type '{agent_type}' not supported in canonical pipeline.")
