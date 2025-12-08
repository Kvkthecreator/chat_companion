"""
API routes for TaskBrief CRUD operations.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.utils.db import json_safe

from ..utils.jwt import verify_jwt
from ..utils.supabase_client import supabase_client as supabase

router = APIRouter(prefix="/task-brief", tags=["task-brief"])

logger = logging.getLogger("uvicorn.error")


class MediaItem(BaseModel):
    image_url: str
    description: str


class TaskBrief(BaseModel):
    id: Optional[str]
    user_id: str
    intent: str
    sub_instructions: Optional[str]
    compilation_mode: Optional[str]
    media: Optional[list[MediaItem]]
    core_context_snapshot: Optional[dict]
    created_at: Optional[datetime]


@router.post("/", response_model=TaskBrief, status_code=201)
async def create_task_brief(task_brief: TaskBrief, user: dict = Depends(verify_jwt)):
    """Create a new TaskBrief entry in Supabase and return it."""
    payload = task_brief.model_dump(
        mode="json", exclude_unset=True, exclude={"id", "created_at"}
    )
    try:
        resp = supabase.table("task_briefs").insert(json_safe(payload)).execute()
        status = getattr(resp, "status_code", 200)
        if status >= 400 or getattr(resp, "error", None) or not resp.data:
            detail = (
                str(getattr(resp, "error", resp))
                if status >= 400
                else "Failed to insert task_brief"
            )
            raise HTTPException(status_code=500, detail=detail)
        return resp.data[0]
    except Exception as err:
        logger.exception("create_task_brief failed")
        raise HTTPException(status_code=500, detail="internal error") from err


@router.get("/{brief_id}", response_model=TaskBrief)
async def get_task_brief(brief_id: str, user: dict = Depends(verify_jwt)):
    """Fetch a TaskBrief by ID."""
    try:
        resp = (
            supabase.table("task_briefs")
            .select("*")
            .eq("id", brief_id)
            .single()
            .execute()
        )
        status = getattr(resp, "status_code", 200)
        if status >= 400 or getattr(resp, "error", None) or not resp.data:
            raise HTTPException(status_code=404, detail="TaskBrief not found")
        return resp.data
    except Exception as err:
        logger.exception("get_task_brief failed")
        raise HTTPException(status_code=500, detail="internal error") from err
