"""
Real-time Task Updates for Work Tickets

Persists task progress to work_tickets.metadata.current_todos for
Supabase Realtime to deliver to connected frontend clients.

The frontend subscribes to work_tickets table changes and receives
progress updates when metadata is updated.
"""

from datetime import datetime
import logging

from app.utils.supabase_client import supabase_admin_client as supabase

logger = logging.getLogger(__name__)


# In-memory accumulator for building current_todos list
_TASK_UPDATES: dict[str, list[dict]] = {}


def emit_task_update(ticket_id: str, update: dict):
    """
    Emit a task update that gets persisted to work_tickets.metadata.

    Called by agent execution code to broadcast progress updates.
    Each call updates the database, triggering Supabase Realtime for
    connected frontend clients.

    Args:
        ticket_id: Work ticket UUID
        update: Update data with fields:
            - type: "task_started" | "task_update" | "task_completed" | "task_failed"
            - status: "pending" | "in_progress" | "completed" | "failed"
            - current_step: Description of current step
            - activeForm: Display text for the task (present tense)
    """
    if ticket_id not in _TASK_UPDATES:
        _TASK_UPDATES[ticket_id] = []

    update["timestamp"] = datetime.utcnow().isoformat()
    _TASK_UPDATES[ticket_id].append(update)

    logger.info(f"[Task Update] {ticket_id}: {update.get('current_step', 'N/A')}")

    # Persist to database for Supabase Realtime
    _persist_current_todos(ticket_id)


def _persist_current_todos(ticket_id: str):
    """
    Persist current task progress to work_tickets.metadata.current_todos.

    This triggers Supabase Realtime updates for connected frontend clients.
    """
    try:
        updates = _TASK_UPDATES.get(ticket_id, [])

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
        logger.warning(f"[Task Update] Failed to persist to DB: {e}")


def get_final_todos(ticket_id: str) -> list[dict]:
    """
    Get final todos list for storage when execution completes.

    Returns:
        List of todo items in TodoWrite format:
        [{"content": "...", "status": "completed", "activeForm": "..."}]
    """
    updates = _TASK_UPDATES.get(ticket_id, [])

    todos = []
    for update in updates:
        update_type = update.get("type", "")

        # All tasks are completed by end
        final_status = "failed" if update_type == "task_failed" else "completed"

        todo = {
            "content": update.get("current_step", "Task"),
            "status": final_status,
            "activeForm": update.get("activeForm", update.get("current_step", "Working")),
        }
        todos.append(todo)

    return todos


def cleanup_task_updates(ticket_id: str):
    """Remove task updates for a ticket from memory after persistence."""
    _TASK_UPDATES.pop(ticket_id, None)
