"""
Narrative jobs API routes.

Provides endpoints for async narrative generation with from_scaffold and refresh_full modes.
"""

import os
import sys
from typing import List, Literal, Optional

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..utils.jwt import verify_jwt
from ..utils.workspace import get_or_create_workspace
from services.narrative_jobs import start_job, get_job, JobMode

router = APIRouter(prefix="/api", tags=["narrative_jobs"])

class NarrativeJobRequest(BaseModel):
    mode: JobMode = Field(..., description="Generation mode: from_scaffold or refresh_full")
    include: List[str] = Field(
        default=["blocks", "context", "documents"], 
        description="Types to include: blocks, context, documents, raw_dumps"
    )

class NarrativeJobResponse(BaseModel):
    job_id: str

@router.post("/baskets/{basket_id}/narrative/jobs", response_model=NarrativeJobResponse)
async def create_narrative_job(
    basket_id: str,
    req: NarrativeJobRequest,
    user: dict = Depends(verify_jwt)
):
    """
    Start a narrative generation job for a basket.
    
    - **from_scaffold**: Read fresh substrate from DB and generate narrative
    - **refresh_full**: Refetch all requested types before generation
    """
    # Feature gate for production
    if not os.getenv("NARRATIVE_JOBS_ENABLED", "false").lower() == "true":
        raise HTTPException(501, "Narrative jobs are not enabled. Set NARRATIVE_JOBS_ENABLED=true to enable.")
    
    workspace_id = get_or_create_workspace(user["user_id"])
    
    # Validate include types
    valid_types = {"blocks", "context", "documents", "raw_dumps"}
    invalid_types = set(req.include) - valid_types
    if invalid_types:
        raise HTTPException(400, f"Invalid include types: {invalid_types}")
    
    # Start the job
    job_id = await start_job(
        basket_id=basket_id,
        mode=req.mode,
        include=req.include,
        workspace_id=workspace_id
    )
    
    return NarrativeJobResponse(job_id=job_id)

@router.get("/jobs/{job_id}")
async def get_narrative_job(
    job_id: str,
    user: dict = Depends(verify_jwt)
):
    """
    Get the status and results of a narrative job.
    
    Returns job state, progress, and narrative content when complete.
    """
    job_status = await get_job(job_id)
    
    if not job_status:
        raise HTTPException(404, "Job not found")
    
    return job_status