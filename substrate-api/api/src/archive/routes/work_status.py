"""
Universal Work Status API - YARNNN Canon v2.1 Compliant

Provides unified status tracking for all async work in YARNNN:
- P0-P4 pipeline operations  
- Manual substrate edits
- Governance proposal reviews
- Document composition
- Timeline restoration

Canon Compliance:
- Single source of truth: agent_processing_queue (canonical_queue)
- Workspace isolation via RLS policies
- Status derived from existing substrate and timeline data
- Memory-first architecture with substrate impact metrics
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from uuid import UUID

from app.schemas.work_status import (
    WorkStatusResponse, 
    WorkStatusListResponse,
    WorkInitiationRequest,
    WorkInitiationResponse, 
    QueueHealthResponse,
    WorkType
)
from infra.utils.supabase_client import supabase_admin_client as supabase
from infra.utils.jwt import verify_jwt
from services.universal_work_tracker import universal_work_tracker, WorkContext
from app.services.status_derivation import status_derivation_service

router = APIRouter(prefix="/api/work", tags=["work-status"])

@router.get("/health", response_model=QueueHealthResponse)
async def get_queue_health():
    """
    Get queue health metrics for monitoring.
    
    Returns overall system health for universal work orchestration.
    """
    try:
        # Get queue statistics
        stats_response = supabase.rpc('fn_queue_health').execute()
        queue_stats = stats_response.data or []
        
        # Calculate totals and averages
        total_items = sum(stat['count'] for stat in queue_stats)
        pending_items = next((stat['count'] for stat in queue_stats if stat['processing_state'] == 'pending'), 0)
        processing_items = next((stat['count'] for stat in queue_stats if stat['processing_state'] == 'processing'), 0)
        failed_items = next((stat['count'] for stat in queue_stats if stat['processing_state'] == 'failed'), 0)
        
        # Calculate average processing time (from completed items)
        avg_time = 0
        completed_stat = next((stat for stat in queue_stats if stat['processing_state'] == 'completed'), None)
        if completed_stat and completed_stat['avg_age_seconds']:
            avg_time = float(completed_stat['avg_age_seconds'])
        
        # Count active cascade flows
        cascade_response = supabase.table("agent_processing_queue").select(
            "id"
        ).eq("processing_state", "cascading").execute()
        cascade_flows_active = len(cascade_response.data or [])
        
        # Estimate worker count (unique claimed_by values)
        workers_response = supabase.table("agent_processing_queue").select(
            "claimed_by"
        ).in_("processing_state", ["claimed", "processing"]).execute()
        
        unique_workers = set()
        for worker in (workers_response.data or []):
            if worker.get('claimed_by'):
                unique_workers.add(worker['claimed_by'])
        
        return QueueHealthResponse(
            total_items=int(total_items),
            pending_items=int(pending_items),
            processing_items=int(processing_items),
            failed_items=int(failed_items),
            avg_processing_time=avg_time,
            worker_count=len(unique_workers),
            cascade_flows_active=cascade_flows_active
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get queue health: {str(e)}"
        )

@router.get("/{work_id}/status", response_model=WorkStatusResponse)
async def get_work_status(work_id: str, user: dict = Depends(verify_jwt)):
    """
    Get comprehensive status for any work item with cascade flow visualization.
    
    Canon-compliant status derivation from canonical queue + substrate impact.
    Includes cascade flow status and relationship mapping.
    Respects workspace isolation via user JWT verification.
    """
    try:
        user_id = user.get('sub')
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid user token")
        
        # Get user's workspace IDs for access control
        workspaces_response = supabase.table("workspace_memberships").select(
            "workspace_id"
        ).eq("user_id", user_id).execute()
        
        if not workspaces_response.data:
            raise HTTPException(
                status_code=403, 
                detail="User has no workspace access"
            )
        
        user_workspace_ids = [w['workspace_id'] for w in workspaces_response.data]
        
        # Get comprehensive work status using status derivation service
        status_response = await status_derivation_service.derive_work_status(
            work_id=work_id,
            user_workspace_ids=user_workspace_ids
        )
        
        if not status_response:
            raise HTTPException(
                status_code=404, 
                detail="Work not found or access denied"
            )
        
        return status_response
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get work status: {str(e)}"
        )

@router.get("/", response_model=WorkStatusListResponse)
async def list_work_statuses(
    user: dict = Depends(verify_jwt),
    work_type: Optional[WorkType] = Query(None, description="Filter by work type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    basket_id: Optional[str] = Query(None, description="Filter by basket ID"),
    limit: int = Query(20, description="Maximum number of results", le=100),
    offset: int = Query(0, description="Offset for pagination")
):
    """
    List work statuses for user's workspaces.
    
    Supports filtering by work_type, status, and basket_id.
    Results are workspace-isolated via user JWT.
    """
    try:
        user_id = user.get('sub')
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid user token")
        
        # Get user's workspaces
        workspaces_response = supabase.table("workspace_memberships").select(
            "workspace_id"
        ).eq("user_id", user_id).execute()
        
        if not workspaces_response.data:
            return WorkStatusListResponse(
                work_statuses=[],
                total_count=0,
                pending_count=0,
                processing_count=0,
                completed_count=0,
                failed_count=0
            )
        
        workspace_ids = [w['workspace_id'] for w in workspaces_response.data]
        
        # Build query filters
        query = supabase.table("agent_processing_queue").select(
            "work_id, work_type, processing_state, created_at, workspace_id, basket_id"
        ).in_("workspace_id", workspace_ids).order("created_at", desc=True)
        
        if work_type:
            query = query.eq("work_type", work_type)
        if status:
            query = query.eq("processing_state", status)
        if basket_id:
            query = query.eq("basket_id", basket_id)
        
        # Get paginated results
        query = query.range(offset, offset + limit - 1)
        response = query.execute()
        
        work_items = response.data or []
        
        # Get detailed status for each work item using status derivation service
        work_statuses = []
        for item in work_items:
            try:
                detailed_status = await status_derivation_service.derive_work_status(
                    work_id=item['work_id'],
                    user_workspace_ids=workspace_ids
                )
                if detailed_status:
                    work_statuses.append(detailed_status)
            except Exception as e:
                # Skip items that fail status lookup
                continue
        
        # Get counts for summary
        counts_response = supabase.table("agent_processing_queue").select(
            "processing_state, count:id.count()"
        ).in_("workspace_id", workspace_ids).execute()
        
        status_counts = {}
        total_count = 0
        for count_item in (counts_response.data or []):
            state = count_item['processing_state']
            count = count_item['count']
            status_counts[state] = count
            total_count += count
        
        return WorkStatusListResponse(
            work_statuses=work_statuses,
            total_count=total_count,
            pending_count=status_counts.get('pending', 0),
            processing_count=status_counts.get('processing', 0) + status_counts.get('claimed', 0),
            completed_count=status_counts.get('completed', 0),
            failed_count=status_counts.get('failed', 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to list work statuses: {str(e)}"
        )

@router.post("/initiate", response_model=WorkInitiationResponse)
async def initiate_work(
    request: WorkInitiationRequest,
    user: dict = Depends(verify_jwt)
):
    """
    Initiate new async work in YARNNN.
    
    Creates work entry in canonical queue and returns work_id for status tracking.
    Supports all work types: P0-P4, manual edits, governance, document composition.
    """
    try:
        user_id = user.get('sub')
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid user token")
        
        # Get user's default workspace (for now, use first workspace)
        workspaces_response = supabase.table("workspace_memberships").select(
            "workspace_id"
        ).eq("user_id", user_id).limit(1).execute()
        
        if not workspaces_response.data:
            raise HTTPException(
                status_code=403, 
                detail="User has no workspace memberships"
            )
        
        workspace_id = workspaces_response.data[0]['workspace_id']
        
        # Create work context
        context = WorkContext(
            user_id=user_id,
            workspace_id=workspace_id,
            basket_id=request.basket_id,
            dump_id=request.dump_id,
            proposal_id=request.proposal_id,
            document_id=request.document_id
        )
        
        # Initiate work using universal work tracker
        work_id = await universal_work_tracker.initiate_work(
            work_type=request.work_type,
            payload=request.payload,
            context=context,
            priority=request.priority,
            parent_work_id=request.parent_work_id
        )
        
        # Calculate estimated completion time
        time_estimates = {
            'P0_CAPTURE': '~10s',
            'P1_SUBSTRATE': '~45s', 
            'P2_GRAPH': '~20s',
            'P3_REFLECTION': '~15s',
            'P4_COMPOSE': '~30s',
            'MANUAL_EDIT': '~5s',
            'PROPOSAL_REVIEW': '~3s',
            'TIMELINE_RESTORE': '~15s'
        }
        
        estimated_completion = time_estimates.get(request.work_type, '~30s')
        
        return WorkInitiationResponse(
            work_id=work_id,
            status_url=f"/api/work/{work_id}/status",
            estimated_completion=estimated_completion
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to initiate work: {str(e)}"
        )

@router.post("/{work_id}/retry")
async def retry_failed_work(work_id: str, user: dict = Depends(verify_jwt)):
    """
    Retry failed work by resetting to pending state.
    
    Only works for failed work items within user's workspace.
    """
    try:
        user_id = user.get('sub')
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid user token")
        
        # Get work item and verify access
        work_response = supabase.table("agent_processing_queue").select(
            "work_id, workspace_id, processing_state, user_id"
        ).eq("work_id", work_id).single().execute()
        
        if not work_response.data:
            raise HTTPException(status_code=404, detail="Work not found")
        
        work = work_response.data
        
        # Check workspace access
        access_response = supabase.table("workspace_memberships").select(
            "workspace_id"
        ).eq("user_id", user_id).eq("workspace_id", work['workspace_id']).execute()
        
        if not access_response.data:
            raise HTTPException(
                status_code=403, 
                detail="Access denied: User not member of workspace"
            )
        
        # Only allow retry of failed work
        if work['processing_state'] != 'failed':
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot retry work with status: {work['processing_state']}"
            )
        
        # Reset to pending state
        supabase.table("agent_processing_queue").update({
            'processing_state': 'pending',
            'error_message': None,
            'claimed_at': None,
            'claimed_by': None,
            'completed_at': None
        }).eq("work_id", work_id).execute()
        
        return {"message": "Work reset to pending for retry", "work_id": work_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to retry work: {str(e)}"
        )

@router.get("/{work_id}/cascade", response_model=dict)
async def get_cascade_flow_status(work_id: str, user: dict = Depends(verify_jwt)):
    """
    Get detailed cascade flow status for work item.
    
    Shows full P1→P2→P3 flow relationships, completion status, and timing.
    Canon-compliant with workspace isolation.
    """
    try:
        user_id = user.get('sub')
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid user token")
        
        # Get user's workspace IDs for access control
        workspaces_response = supabase.table("workspace_memberships").select(
            "workspace_id"
        ).eq("user_id", user_id).execute()
        
        if not workspaces_response.data:
            raise HTTPException(
                status_code=403, 
                detail="User has no workspace access"
            )
        
        user_workspace_ids = [w['workspace_id'] for w in workspaces_response.data]
        
        # Verify work exists and user has access
        work_response = supabase.table("agent_processing_queue").select(
            "work_id, workspace_id"
        ).eq("work_id", work_id).single().execute()
        
        if not work_response.data:
            raise HTTPException(status_code=404, detail="Work not found")
        
        work = work_response.data
        if work['workspace_id'] not in user_workspace_ids:
            raise HTTPException(
                status_code=403, 
                detail="Access denied: Work not in user workspace"
            )
        
        # Get cascade status using status derivation service
        cascade_status = await status_derivation_service.derive_cascade_status(work_id)
        
        return {
            "work_id": work_id,
            "cascade_flow": cascade_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get cascade flow status: {str(e)}"
        )

@router.get("/workspace/{workspace_id}/summary", response_model=dict)
async def get_workspace_work_summary(workspace_id: str, user: dict = Depends(verify_jwt)):
    """
    Get comprehensive work summary for a workspace.
    
    Shows all active work, cascade flows, queue health, and timing metrics.
    Canon-compliant with workspace isolation.
    """
    try:
        user_id = user.get('sub')
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid user token")
        
        # Check workspace access
        access_response = supabase.table("workspace_memberships").select(
            "workspace_id"
        ).eq("user_id", user_id).eq("workspace_id", workspace_id).execute()
        
        if not access_response.data:
            raise HTTPException(
                status_code=403, 
                detail="Access denied: User not member of workspace"
            )
        
        # Get workspace work summary using status derivation service
        summary = await status_derivation_service.get_workspace_work_summary(workspace_id)
        
        return {
            "workspace_id": workspace_id,
            "summary": summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get workspace work summary: {str(e)}"
        )