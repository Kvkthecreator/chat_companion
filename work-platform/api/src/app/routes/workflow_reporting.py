"""
Deterministic Reporting Workflow Endpoint

Part of Workflow-First Architecture:
- Explicit parameters (no TP orchestration)
- Direct specialist invocation
- Auditable execution tracking

NOTE: Post-SDK removal, reporting workflow is pending migration.
Currently returns 501 Not Implemented.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timezone

from app.utils.jwt import verify_jwt
from app.utils.supabase_client import supabase_admin_client as supabase
import logging

router = APIRouter(prefix="/work/reporting", tags=["workflows"])
logger = logging.getLogger(__name__)


class ReportingWorkflowRequest(BaseModel):
    """Deterministic reporting workflow parameters."""
    basket_id: str
    task_description: str
    output_format: Optional[str] = "markdown"  # markdown, pptx, json
    priority: Optional[int] = 5

    # Recipe integration (optional)
    recipe_id: Optional[str] = None
    recipe_parameters: Optional[Dict[str, Any]] = None
    reference_asset_ids: Optional[list[str]] = None

    # Async execution mode
    async_execution: Optional[bool] = False


class ReportingWorkflowResponse(BaseModel):
    """Reporting workflow execution result."""
    work_request_id: str
    work_ticket_id: str
    status: str
    outputs: list[dict]
    execution_time_ms: Optional[int]
    message: str
    recipe_used: Optional[str] = None


@router.post("/execute", response_model=ReportingWorkflowResponse)
async def execute_reporting_workflow(
    request: ReportingWorkflowRequest,
    user: dict = Depends(verify_jwt)
):
    """
    Execute deterministic reporting workflow.

    NOTE: Post-SDK removal, reporting workflow is pending migration.
    Use research workflow (/api/work/research/execute) in the meantime.

    Args:
        request: Reporting workflow parameters
        user: Authenticated user from JWT

    Returns:
        501 Not Implemented with migration notice
    """
    user_id = user.get("sub") or user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user token")

    logger.info(
        f"[REPORTING WORKFLOW] Request received (SDK removed): user={user_id}, "
        f"basket={request.basket_id}"
    )

    # Validate basket access
    try:
        basket_response = supabase.table("baskets").select(
            "id, workspace_id, name"
        ).eq("id", request.basket_id).single().execute()

        if not basket_response.data:
            raise HTTPException(status_code=404, detail="Basket not found")

        workspace_id = basket_response.data["workspace_id"]

        # Create a work_request to track the attempt
        work_request_data = {
            "workspace_id": workspace_id,
            "basket_id": request.basket_id,
            "requested_by_user_id": user_id,
            "request_type": "reporting_workflow_pending",
            "task_intent": request.task_description,
            "parameters": {
                "output_format": request.output_format,
                "recipe_id": request.recipe_id,
                "status": "migration_pending"
            },
            "priority": "normal",
        }

        work_request_response = supabase.table("work_requests").insert(
            work_request_data
        ).execute()
        work_request_id = work_request_response.data[0]["id"]

        # Create a work_ticket with pending_migration status
        work_ticket_data = {
            "work_request_id": work_request_id,
            "workspace_id": workspace_id,
            "basket_id": request.basket_id,
            "agent_type": "reporting",
            "status": "pending_migration",
            "metadata": {
                "workflow": "reporting_workflow",
                "task_description": request.task_description,
                "output_format": request.output_format,
                "migration_note": "ReportingExecutor not yet implemented",
            },
        }
        work_ticket_response = supabase.table("work_tickets").insert(
            work_ticket_data
        ).execute()
        work_ticket_id = work_ticket_response.data[0]["id"]

        logger.warning(
            f"[REPORTING WORKFLOW] SDK removed - returning 501. "
            f"Created tracking: request={work_request_id}, ticket={work_ticket_id}"
        )

        # Return informative response instead of 501
        return ReportingWorkflowResponse(
            work_request_id=work_request_id,
            work_ticket_id=work_ticket_id,
            status="pending_migration",
            outputs=[],
            execution_time_ms=0,
            message=(
                "Reporting workflow is pending migration from Claude Agent SDK. "
                "Your request has been logged. "
                "Use /api/work/research/execute for research tasks in the meantime."
            ),
            recipe_used=request.recipe_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[REPORTING WORKFLOW] Error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Reporting workflow error: {str(e)}"
        )


@router.get("/status")
async def reporting_workflow_status():
    """
    Get reporting workflow migration status.

    Returns:
        Migration status information
    """
    return {
        "status": "migration_pending",
        "message": "Reporting workflow is pending migration from Claude Agent SDK",
        "available_alternatives": {
            "research": "/api/work/research/execute"
        },
        "migration_eta": "Phase 2 of SDK removal"
    }
