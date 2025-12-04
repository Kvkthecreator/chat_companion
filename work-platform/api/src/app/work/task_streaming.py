"""
Real-time Task Updates Streaming for Work Tickets

Provides two mechanisms for streaming agent task progress to the frontend:
1. SSE (Server-Sent Events) - Legacy, works but limited by in-memory state
2. Database persistence - Updates work_tickets.metadata.current_todos for
   Supabase Realtime to deliver to frontend (preferred approach)

Compatible with TodoWrite tool from Claude Agent SDK.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator, Optional
import asyncio
import json
from datetime import datetime
from uuid import UUID

from app.utils.jwt import verify_jwt
from app.utils.supabase_client import supabase_admin_client as supabase
import logging

router = APIRouter(prefix="/work/tickets", tags=["work-streaming"])
logger = logging.getLogger(__name__)


# In-memory store for task updates (legacy SSE support)
TASK_UPDATES: dict[str, list[dict]] = {}


def emit_task_update(ticket_id: str, update: dict, persist_to_db: bool = True):
    """
    Emit a task update to be streamed to subscribed clients.

    Called by agent execution code to broadcast progress updates.
    Updates are stored both in-memory (for SSE) and in the database
    (for Supabase Realtime to deliver to frontend).

    Args:
        ticket_id: Work ticket UUID
        update: Update data (status, step, progress, etc.)
        persist_to_db: Whether to persist to work_tickets.metadata.current_todos
    """
    if ticket_id not in TASK_UPDATES:
        TASK_UPDATES[ticket_id] = []

    update["timestamp"] = datetime.utcnow().isoformat()
    TASK_UPDATES[ticket_id].append(update)

    logger.info(f"[Task Update] {ticket_id}: {update.get('current_step', 'N/A')}")

    # Persist to database for Supabase Realtime
    if persist_to_db:
        _persist_current_todos(ticket_id)


def _persist_current_todos(ticket_id: str):
    """
    Persist current task progress to work_tickets.metadata.current_todos.

    This triggers Supabase Realtime updates for connected frontend clients.
    The frontend subscribes to work_tickets table and receives updates
    when metadata changes.
    """
    try:
        updates = TASK_UPDATES.get(ticket_id, [])

        # Convert to TodoWrite format for frontend
        current_todos = []
        for update in updates:
            update_type = update.get("type", "")
            status = update.get("status", "pending")

            # Map to TodoWrite status
            if update_type == "task_completed":
                todo_status = "completed"
            elif update_type == "task_failed":
                todo_status = "failed"
            elif status == "in_progress":
                todo_status = "in_progress"
            else:
                todo_status = "pending"

            todo = {
                "content": update.get("current_step", "Task"),
                "status": todo_status,
                "activeForm": update.get("activeForm", update.get("current_step", "Working")),
            }
            current_todos.append(todo)

        # Update metadata with current_todos
        existing = supabase.table("work_tickets").select("metadata").eq("id", ticket_id).single().execute()
        existing_metadata = existing.data.get("metadata", {}) if existing.data else {}

        updated_metadata = {
            **existing_metadata,
            "current_todos": current_todos,
            "last_progress_update": datetime.utcnow().isoformat(),
        }

        supabase.table("work_tickets").update({
            "metadata": updated_metadata
        }).eq("id", ticket_id).execute()

        logger.debug(f"[Task Update] Persisted {len(current_todos)} todos to DB for {ticket_id}")

    except Exception as e:
        # Log but don't fail - SSE still works as fallback
        logger.warning(f"[Task Update] Failed to persist to DB: {e}")


def get_final_todos(ticket_id: str) -> list[dict]:
    """
    Convert task updates to final_todos format for storage in work_tickets.metadata.

    This is called when execution completes to persist the task history.

    Returns:
        List of todo items in TodoWrite format:
        [
            {"content": "...", "status": "completed", "activeForm": "..."},
            ...
        ]
    """
    updates = TASK_UPDATES.get(ticket_id, [])

    # Convert updates to TodoWrite format
    todos = []
    for update in updates:
        update_type = update.get("type", "")
        status = update.get("status", "pending")

        # Determine final status
        if update_type in ["task_completed", "task_failed"]:
            final_status = "completed" if update_type == "task_completed" else "failed"
        elif status == "in_progress":
            final_status = "completed"  # In-progress tasks are complete by end
        else:
            final_status = "completed"

        todo = {
            "content": update.get("current_step", "Task"),
            "status": final_status,
            "activeForm": update.get("activeForm", update.get("current_step", "Working")),
        }
        todos.append(todo)

    return todos


def cleanup_task_updates(ticket_id: str):
    """Remove task updates for a ticket from memory after persistence."""
    TASK_UPDATES.pop(ticket_id, None)


async def task_update_generator(
    ticket_id: str,
    timeout: int = 600  # 10 minutes max
) -> AsyncGenerator[str, None]:
    """
    Generate SSE stream for task updates.

    Yields updates as they arrive until ticket is completed or timeout.
    """
    start_time = asyncio.get_event_loop().time()
    last_sent_index = 0

    # Send initial connection event
    yield f"data: {json.dumps({'type': 'connected', 'ticket_id': ticket_id})}\n\n"

    while asyncio.get_event_loop().time() - start_time < timeout:
        # Check for new updates
        if ticket_id in TASK_UPDATES:
            updates = TASK_UPDATES[ticket_id]

            # Send any new updates
            while last_sent_index < len(updates):
                update = updates[last_sent_index]
                yield f"data: {json.dumps(update)}\n\n"
                last_sent_index += 1

                # Check if task is complete
                if update.get("status") in ["completed", "failed"]:
                    # Clean up updates after sending completion
                    TASK_UPDATES.pop(ticket_id, None)
                    return

        # Check ticket status in database
        try:
            result = supabase.table("work_tickets").select("status").eq("id", ticket_id).maybe_single().execute()
            if result.data and result.data["status"] in ["completed", "failed"]:
                yield f"data: {json.dumps({'type': 'completed', 'status': result.data['status']})}\n\n"
                TASK_UPDATES.pop(ticket_id, None)
                return
        except Exception as e:
            logger.error(f"Error checking ticket status: {e}")

        await asyncio.sleep(0.5)

    # Timeout
    yield f"data: {json.dumps({'type': 'timeout'})}\n\n"
    TASK_UPDATES.pop(ticket_id, None)


@router.get("/{ticket_id}/stream")
async def stream_task_updates(
    ticket_id: str,
    user: dict = Depends(verify_jwt)
):
    """
    Stream real-time task updates for a work ticket via SSE.

    Frontend subscribes to this endpoint to get live progress updates
    from the agent execution (TodoWrite tool outputs, intermediate steps, etc.).

    Usage (Frontend):
        const eventSource = new EventSource('/api/work/tickets/{id}/stream');
        eventSource.onmessage = (event) => {
            const update = JSON.parse(event.data);
            console.log('Task update:', update);
        };

    Args:
        ticket_id: Work ticket UUID
        user: Authenticated user from JWT

    Returns:
        SSE stream of task updates
    """
    user_id = user.get("sub") or user.get("user_id")

    # Verify ticket exists and user has access
    try:
        ticket_result = supabase.table("work_tickets").select(
            "id, workspace_id, basket_id"
        ).eq("id", ticket_id).maybe_single().execute()

        if not ticket_result.data:
            raise HTTPException(status_code=404, detail="Work ticket not found")

        # TODO: Add workspace permission check

        logger.info(f"[SSE Stream] Client connected: ticket={ticket_id}, user={user_id}")

        return StreamingResponse(
            task_update_generator(ticket_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[SSE Stream] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
