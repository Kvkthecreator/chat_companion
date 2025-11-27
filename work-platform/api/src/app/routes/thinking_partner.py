"""
Thinking Partner API Routes

Gateway/Mirror/Meta agent that orchestrates specialized agents via chat interface.

NOTE: Post-SDK removal, Thinking Partner functionality is temporarily reduced.
Use workflow-specific endpoints (/work/research, /work/reporting) instead.

Endpoints:
- POST /tp/chat - Send message to Thinking Partner (returns migration notice)
- GET /tp/capabilities - Get TP capabilities
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.utils.jwt import verify_jwt
from app.utils.supabase_client import supabase_admin_client

router = APIRouter(prefix="/tp", tags=["thinking-partner"])
logger = logging.getLogger(__name__)

logger.info("Thinking Partner routes initialized (SDK removed - limited functionality)")


async def _get_workspace_id_for_user(user_id: str) -> str:
    """Get workspace_id for user."""
    response = supabase_admin_client.table("workspace_memberships").select(
        "workspace_id"
    ).eq("user_id", user_id).limit(1).execute()

    if not response.data or len(response.data) == 0:
        logger.error(f"No workspace found for user {user_id}")
        raise HTTPException(
            status_code=403,
            detail="User does not belong to any workspace"
        )

    return response.data[0]['workspace_id']


class TPChatRequest(BaseModel):
    """Request to chat with Thinking Partner."""
    basket_id: str = Field(..., description="Basket ID for context")
    message: str = Field(..., description="User's message")
    claude_session_id: Optional[str] = Field(None, description="Claude session ID (deprecated)")


class TPChatResponse(BaseModel):
    """Response from Thinking Partner chat."""
    message: str = Field(..., description="Response message")
    status: str = Field(default="migration_notice")
    recommended_endpoint: Optional[str] = None
    work_outputs: List[Dict[str, Any]] = Field(default_factory=list)


class TPSessionResponse(BaseModel):
    """Thinking Partner session details."""
    session_id: str
    basket_id: str
    workspace_id: str
    user_id: str
    created_at: str
    updated_at: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


@router.post("/chat", response_model=TPChatResponse)
async def tp_chat(
    request: TPChatRequest,
    user: dict = Depends(verify_jwt)
):
    """
    Send message to Thinking Partner.

    NOTE: The Claude Agent SDK has been removed. Thinking Partner orchestration
    is temporarily disabled. Use direct workflow endpoints instead:
    - POST /api/work/research/execute - For research tasks
    - POST /api/work/reporting/execute - For reporting tasks

    Args:
        request: Chat request with message and basket context
        user: Authenticated user from JWT

    Returns:
        Migration notice with recommended endpoint
    """
    user_id = user.get("sub") or user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user token")

    logger.info(
        f"TP chat (SDK removed): user={user_id}, basket={request.basket_id}, "
        f"message={request.message[:50]}..."
    )

    # Analyze message to suggest appropriate endpoint
    message_lower = request.message.lower()
    recommended = None
    suggestion = ""

    if any(word in message_lower for word in ["research", "search", "find", "investigate", "analyze"]):
        recommended = "/api/work/research/execute"
        suggestion = "Your message suggests a research task. Use the research workflow endpoint."
    elif any(word in message_lower for word in ["report", "document", "create", "generate", "write"]):
        recommended = "/api/work/reporting/execute"
        suggestion = "Your message suggests a reporting task. Use the reporting workflow endpoint."
    else:
        suggestion = "Please use the specific workflow endpoints for your task."

    return TPChatResponse(
        message=f"""Thinking Partner orchestration is temporarily disabled (SDK migration in progress).

{suggestion}

For research tasks: POST /api/work/research/execute
For reporting tasks: POST /api/work/reporting/execute

Your message: "{request.message[:100]}..."
""",
        status="migration_notice",
        recommended_endpoint=recommended,
        work_outputs=[]
    )


@router.get("/session/{session_id}", response_model=TPSessionResponse)
async def get_tp_session(
    session_id: str,
    user: dict = Depends(verify_jwt)
):
    """
    Get Thinking Partner session details.

    Args:
        session_id: AgentSession ID
        user: Authenticated user from JWT

    Returns:
        Session details
    """
    user_id = user.get("sub") or user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user token")

    try:
        workspace_id = await _get_workspace_id_for_user(user_id)

        response = supabase_admin_client.table("agent_sessions").select(
            "id, basket_id, workspace_id, created_by_user_id, created_at, last_active_at, metadata"
        ).eq("id", session_id).eq(
            "agent_type", "thinking_partner"
        ).eq("workspace_id", workspace_id).single().execute()

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail="Session not found or access denied"
            )

        session = response.data

        return TPSessionResponse(
            session_id=session["id"],
            basket_id=session["basket_id"],
            workspace_id=session["workspace_id"],
            user_id=session.get("created_by_user_id", ""),
            created_at=session["created_at"],
            updated_at=session.get("last_active_at", session["created_at"]),
            metadata=session.get("metadata", {})
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get TP session: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve session: {str(e)}"
        )


@router.get("/capabilities")
async def get_tp_capabilities():
    """
    Get Thinking Partner capabilities.

    Returns:
        Dictionary of TP capabilities (note: reduced functionality post-SDK removal)
    """
    return {
        "description": "Thinking Partner - Meta-agent (SDK migration in progress)",
        "status": "limited_functionality",
        "migration_note": "Claude Agent SDK has been removed. Use direct workflow endpoints.",
        "available_workflows": {
            "research": {
                "endpoint": "/api/work/research/execute",
                "description": "Intelligence gathering with web search",
                "status": "active"
            },
            "reporting": {
                "endpoint": "/api/work/reporting/execute",
                "description": "Document generation",
                "status": "migration_pending"
            }
        },
        "temporarily_disabled": [
            "TP chat orchestration",
            "Multi-agent coordination",
            "Session-based conversations"
        ],
        "substrate_access": "Active - via SubstrateQueryAdapter",
        "work_outputs": "Active - via substrate-API HTTP"
    }
