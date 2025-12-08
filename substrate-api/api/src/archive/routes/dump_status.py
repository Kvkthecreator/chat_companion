"""
Dump Processing Status API - Derived from Existing Data

Implements an enhanced "Option A" approach that derives processing status
from existing tables without adding new schema.
"""
# V3.0 DEPRECATION NOTICE:
# This file contains references to context_items table which was merged into blocks table.
# Entity blocks are now identified by semantic_type='entity'.
# This file is legacy/supporting code - update if actively maintained.


from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID

from ..utils.jwt import verify_jwt
from ..utils.supabase_client import supabase_client as supabase

router = APIRouter(prefix="/api/dumps", tags=["dump-status"])


@router.get("/{dump_id}/status")
async def get_dump_processing_status(
    dump_id: str,
    user: dict = Depends(verify_jwt)
) -> Dict[str, Any]:
    """
    Get processing status for a dump by deriving from existing data.
    
    This endpoint provides real-time status without requiring new schema
    by intelligently querying existing tables:
    - raw_dumps: Basic dump info
    - canonical_queue: Current processing stage
    - proposals: Governance proposals created
    - timeline_events: Processing milestones
    - blocks/context_items: Created substrate
    """
    try:
        # 1. Verify dump exists and user has access
        dump_response = supabase.table("raw_dumps").select(
            "id, basket_id, workspace_id, created_at"
        ).eq("id", dump_id).single().execute()
        
        if not dump_response.data:
            raise HTTPException(status_code=404, detail="Dump not found")
            
        dump = dump_response.data
        
        # 2. Check canonical queue for current processing
        queue_response = supabase.table("canonical_queue").select(
            "id, work_type, status, created_at, updated_at, worker_id, error_details"
        ).eq("dump_id", dump_id).order("created_at", desc=True).execute()
        
        queue_entries = queue_response.data or []
        
        # 3. Check for proposals created from this dump
        proposals_response = supabase.table("proposals").select(
            "id, status, ops, created_at, is_executed"
        ).contains("provenance", [dump_id]).execute()
        
        proposals = proposals_response.data or []
        
        # 4. Check timeline events for processing milestones
        events_response = supabase.table("timeline_events").select(
            "event_type, event_data, created_at"
        ).eq("basket_id", dump["basket_id"]).filter(
            "event_data", "cs", f'"{dump_id}"'  # Contains dump_id in event_data
        ).order("created_at", desc=True).limit(10).execute()
        
        events = events_response.data or []
        
        # 5. Count created substrate
        blocks_count = supabase.table("blocks").select(
            "id", count="exact"
        ).eq("basket_id", dump["basket_id"]).gte(
            "created_at", dump["created_at"]
        ).execute().count
        
        items_count = supabase.table("context_items").select(
            "id", count="exact"
        ).eq("basket_id", dump["basket_id"]).gte(
            "created_at", dump["created_at"]
        ).execute().count
        
        # Derive current stage and status
        stage_info = _derive_processing_stage(
            dump, queue_entries, proposals, events, blocks_count, items_count
        )
        
        # Calculate time estimates
        time_info = _calculate_time_estimates(dump, queue_entries, stage_info["stage"])
        
        # Build status response
        return {
            "dump_id": dump_id,
            "stage": stage_info["stage"],
            "stage_display": stage_info["display"],
            "current_pipeline_stage": stage_info.get("pipeline_stage"),
            "queue_position": _get_queue_position(queue_entries),
            "started_at": dump["created_at"],
            "last_activity": stage_info["last_activity"],
            "cascade_active": _is_cascade_active(queue_entries),
            "progress_percentage": stage_info["progress"],
            "meta": {
                "proposals_created": len(proposals),
                "proposals_executed": sum(1 for p in proposals if p.get("is_executed")),
                "substrate_created": {
                    "blocks": blocks_count or 0,
                    "context_items": items_count or 0
                },
                "queue_entries": len(queue_entries),
                "error": stage_info.get("error")
            },
            "estimated_time_remaining": time_info["estimate"],
            "average_total_time": time_info["average"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _derive_processing_stage(
    dump: Dict,
    queue_entries: list,
    proposals: list,
    events: list,
    blocks_count: int,
    items_count: int
) -> Dict[str, Any]:
    """Derive the current processing stage from available data."""
    
    # Check for errors first
    failed_entries = [q for q in queue_entries if q["status"] == "failed"]
    if failed_entries:
        return {
            "stage": "failed",
            "display": "Processing failed",
            "error": failed_entries[0].get("error_details", "Unknown error"),
            "last_activity": failed_entries[0]["updated_at"],
            "progress": 0
        }
    
    # Check if completed (proposals executed and substrate created)
    if proposals and any(p.get("is_executed") for p in proposals):
        # Check for P3 reflection completion
        p3_complete = any(
            q["work_type"] == "P3_REFLECTION" and q["status"] == "completed"
            for q in queue_entries
        )
        if p3_complete:
            return {
                "stage": "completed",
                "display": "Processing complete",
                "last_activity": max(q["updated_at"] for q in queue_entries),
                "progress": 100
            }
    
    # Check active queue entries
    active_entry = next(
        (q for q in queue_entries if q["status"] in ["processing", "claimed"]),
        None
    )
    
    if active_entry:
        stage_map = {
            "P1_SUBSTRATE": ("analyzing", "Extracting knowledge", "P1_SUBSTRATE", 30),
            "P2_GRAPH": ("linking", "Mapping relationships", "P2_GRAPH", 60),
            "P3_REFLECTION": ("reflecting", "Computing insights", "P3_REFLECTION", 80)
        }
        
        if active_entry["work_type"] in stage_map:
            stage, display, pipeline, progress = stage_map[active_entry["work_type"]]
            return {
                "stage": stage,
                "display": display,
                "pipeline_stage": pipeline,
                "last_activity": active_entry["updated_at"],
                "progress": progress
            }
    
    # Check if awaiting review (proposals exist but not executed)
    if proposals and not any(p.get("is_executed") for p in proposals):
        return {
            "stage": "awaiting_review",
            "display": "Awaiting approval",
            "last_activity": proposals[0]["created_at"],
            "progress": 50
        }
    
    # Check if substrate exists (P1 complete)
    if blocks_count > 0 or items_count > 0:
        return {
            "stage": "substrate_created",
            "display": "Knowledge extracted",
            "last_activity": dump["created_at"],  # Approximate
            "progress": 40
        }
    
    # Check if any queue entry exists
    if queue_entries:
        return {
            "stage": "queued",
            "display": "Queued for processing",
            "last_activity": queue_entries[0]["created_at"],
            "progress": 10
        }
    
    # Just created
    return {
        "stage": "uploaded",
        "display": "Upload complete",
        "last_activity": dump["created_at"],
        "progress": 5
    }


def _calculate_time_estimates(
    dump: Dict,
    queue_entries: list,
    current_stage: str
) -> Dict[str, str]:
    """Calculate time estimates based on historical data."""
    
    # Static estimates for MVP (could be data-driven later)
    stage_times = {
        "uploaded": 45,
        "queued": 40,
        "analyzing": 30,
        "substrate_created": 25,
        "awaiting_review": 15,
        "linking": 20,
        "reflecting": 15,
        "completed": 0,
        "failed": 0
    }
    
    remaining = stage_times.get(current_stage, 30)
    
    if remaining == 0:
        return {"estimate": "Complete", "average": "~60s total"}
    
    return {
        "estimate": f"~{remaining}s",
        "average": "~60s total"
    }


def _get_queue_position(queue_entries: list) -> Optional[int]:
    """Get position in queue if waiting."""
    pending = [q for q in queue_entries if q["status"] == "pending"]
    if pending:
        # In real implementation, would query global queue position
        return 1
    return None


def _is_cascade_active(queue_entries: list) -> bool:
    """Check if cascade processing is active."""
    return any(
        q.get("metadata", {}).get("cascade_trigger") is not None
        for q in queue_entries
    )