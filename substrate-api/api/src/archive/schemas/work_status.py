"""
Work Status Schemas - YARNNN Canon v2.1 Compliant

Defines API contracts for universal work status across all async operations.
Supports P0-P4 pipeline work, manual edits, governance, and document composition.

Canon Compliance:
- Derived from existing substrate and timeline data (Sacred Principle #3)
- Respects workspace isolation via RLS
- Shows substrate impact metrics for memory-first architecture
- Includes cascade flow visualization for pipeline operations
"""
# V3.0 DEPRECATION NOTICE:
# This file contains references to context_items table which was merged into blocks table.
# Entity blocks are now identified by semantic_type='entity'.
# This file is legacy/supporting code - update if actively maintained.


from datetime import datetime
from typing import Optional, Dict, Any, List, Literal, Union
from pydantic import BaseModel, Field
from uuid import UUID

# Canon v2.1 Work Types
WorkType = Literal[
    'P0_CAPTURE',
    'P1_SUBSTRATE', 
    'P2_GRAPH',
    'P3_REFLECTION',
    'P4_COMPOSE',
    'MANUAL_EDIT',
    'PROPOSAL_REVIEW', 
    'TIMELINE_RESTORE'
]

# Work Status States aligned with processing_state enum
WorkStatus = Literal[
    'pending',      # Waiting for worker
    'claimed',      # Worker assigned
    'processing',   # Agent executing
    'cascading',    # Triggering next stage
    'completed',    # Successfully processed
    'failed'        # Processing failed
]

class SubstrateImpact(BaseModel):
    """Substrate impact metrics per Canon memory-first architecture."""
    proposals_created: int = Field(description="Number of governance proposals created")
    substrate_created: Dict[str, int] = Field(
        description="Substrate elements created",
        default_factory=lambda: {"blocks": 0, "context_items": 0}
    )
    relationships_mapped: int = Field(description="Graph relationships created", default=0)
    artifacts_generated: int = Field(description="Documents/reflections generated", default=0)

class CascadeFlow(BaseModel):
    """Cascade flow status for pipeline operations."""
    active: bool = Field(description="Whether cascade is currently active")
    current_stage: Optional[str] = Field(description="Current pipeline stage (P1/P2/P3)")
    completed_stages: List[str] = Field(description="Completed pipeline stages", default_factory=list)
    next_stage: Optional[str] = Field(description="Next stage in cascade flow")

class WorkError(BaseModel):
    """Error information for failed work."""
    code: str = Field(description="Error code for categorization")
    message: str = Field(description="Human-readable error message")
    recovery_actions: List[str] = Field(description="Suggested recovery actions", default_factory=list)

class WorkStatusResponse(BaseModel):
    """
    Canon-compliant work status response.
    
    Provides comprehensive status for any async work in YARNNN:
    - P0-P4 pipeline operations
    - Manual substrate edits  
    - Governance proposal reviews
    - Document composition
    - Timeline restoration
    """
    work_id: str = Field(description="Unique work identifier")
    work_type: WorkType = Field(description="Type of work being processed")
    
    # Current State
    status: WorkStatus = Field(description="Current processing status")
    processing_stage: Optional[str] = Field(description="Stage-specific detail within work type")
    progress_percentage: int = Field(description="Completion percentage (0-100)", ge=0, le=100)
    
    # Context Information
    basket_id: Optional[str] = Field(description="Associated basket ID")
    workspace_id: str = Field(description="Workspace ID for isolation")
    user_id: str = Field(description="User who initiated this work")
    
    # Timing Information
    started_at: datetime = Field(description="When work was initiated")
    last_activity: datetime = Field(description="Last status update time")
    estimated_completion: Optional[str] = Field(description="Estimated time remaining (e.g. '~45s')")
    
    # Canon-compliant Metadata
    substrate_impact: SubstrateImpact = Field(description="Impact on substrate layer")
    cascade_flow: CascadeFlow = Field(description="Pipeline cascade status")
    
    # Error Handling
    error: Optional[WorkError] = Field(description="Error details if work failed")

class WorkStatusListResponse(BaseModel):
    """Response for listing multiple work statuses."""
    work_statuses: List[WorkStatusResponse] = Field(description="List of work statuses")
    total_count: int = Field(description="Total number of work items")
    pending_count: int = Field(description="Number of pending work items")
    processing_count: int = Field(description="Number of currently processing items")
    completed_count: int = Field(description="Number of completed items")
    failed_count: int = Field(description="Number of failed items")

class WorkInitiationRequest(BaseModel):
    """Request to initiate new async work."""
    work_type: WorkType = Field(description="Type of work to initiate")
    payload: Dict[str, Any] = Field(description="Work-specific input data", default_factory=dict)
    basket_id: Optional[str] = Field(description="Associated basket ID")
    dump_id: Optional[str] = Field(description="Associated dump ID")
    proposal_id: Optional[str] = Field(description="Associated proposal ID") 
    document_id: Optional[str] = Field(description="Associated document ID")
    priority: int = Field(description="Work priority (1-10)", default=5, ge=1, le=10)
    parent_work_id: Optional[str] = Field(description="Parent work ID for cascade flows")

class WorkInitiationResponse(BaseModel):
    """Response after initiating work."""
    work_id: str = Field(description="Generated work identifier")
    status_url: str = Field(description="URL for status tracking")
    estimated_completion: str = Field(description="Estimated completion time")

class QueueHealthResponse(BaseModel):
    """Queue health metrics for monitoring."""
    total_items: int = Field(description="Total items in queue")
    pending_items: int = Field(description="Items waiting for processing")
    processing_items: int = Field(description="Items currently being processed")
    failed_items: int = Field(description="Items that failed processing")
    avg_processing_time: float = Field(description="Average processing time in seconds")
    worker_count: int = Field(description="Number of active workers")
    cascade_flows_active: int = Field(description="Number of active cascade flows")

__all__ = [
    "WorkType", 
    "WorkStatus", 
    "WorkStatusResponse", 
    "WorkStatusListResponse",
    "WorkInitiationRequest", 
    "WorkInitiationResponse",
    "QueueHealthResponse",
    "SubstrateImpact",
    "CascadeFlow", 
    "WorkError"
]