"""
Status Derivation Service - YARNNN Canon v2.1 Compliant

Derives comprehensive work status from existing substrate and timeline data.
Provides real-time visibility into cascade flows and pipeline processing.

Canon Compliance:
- Derives status from existing data (Sacred Principle #3: Memory-first architecture)
- Respects workspace isolation via RLS
- Shows substrate impact metrics and cascade flows
- Maintains event-driven consistency with timeline_events
"""
# V3.0 DEPRECATION NOTICE:
# This file contains references to context_items table which was merged into blocks table.
# Entity blocks are now identified by semantic_type='entity'.
# This file is legacy/supporting code - update if actively maintained.


import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID

from infra.utils.supabase_client import supabase_admin_client as supabase
from app.schemas.work_status import WorkStatusResponse, SubstrateImpact, CascadeFlow, WorkError

logger = logging.getLogger("uvicorn.error")

class StatusDerivationService:
    """
    Canon-compliant status derivation from existing data.
    
    Derives comprehensive work status by analyzing:
    - agent_processing_queue entries
    - cascade_metadata for pipeline flows
    - timeline_events for state changes
    - substrate impact from work_result
    - workspace and user context
    """
    
    def __init__(self):
        logger.info("Status Derivation Service initialized - Canon v2.1 compliant")
    
    async def derive_work_status(self, work_id: str, user_workspace_ids: List[str]) -> Optional[WorkStatusResponse]:
        """
        Derive comprehensive work status from existing data.
        
        Args:
            work_id: Work identifier to get status for
            user_workspace_ids: List of workspace IDs user has access to (for isolation)
            
        Returns:
            Complete work status or None if not found/no access
        """
        try:
            # Get work entry with full context
            work_data = await self._get_work_data(work_id, user_workspace_ids)
            if not work_data:
                return None
            
            # Derive substrate impact
            substrate_impact = await self._derive_substrate_impact(work_data)
            
            # Derive cascade flow status
            cascade_flow = await self._derive_cascade_flow(work_data)
            
            # Calculate progress and timing
            progress_percentage = self._calculate_progress_percentage(work_data, cascade_flow)
            estimated_completion = self._calculate_estimated_completion(work_data, cascade_flow)
            
            # Check for error information
            error_info = self._derive_error_info(work_data)
            
            return WorkStatusResponse(
                work_id=work_id,
                work_type=work_data['work_type'],
                status=work_data['processing_state'],
                processing_stage=work_data.get('processing_stage'),
                progress_percentage=progress_percentage,
                basket_id=work_data.get('basket_id'),
                workspace_id=work_data['workspace_id'],
                user_id=work_data['user_id'],
                started_at=work_data['created_at'],
                last_activity=work_data.get('completed_at') or work_data.get('claimed_at') or work_data['created_at'],
                estimated_completion=estimated_completion,
                substrate_impact=substrate_impact,
                cascade_flow=cascade_flow,
                error=error_info
            )
            
        except Exception as e:
            logger.error(f"Failed to derive work status for {work_id}: {e}")
            return None
    
    async def derive_cascade_status(self, work_id: str) -> Dict[str, Any]:
        """
        Derive detailed cascade status for a work item.
        
        Shows full P1→P2→P3 flow status and relationships.
        """
        try:
            # Get work with cascade metadata
            work_response = supabase.table("agent_processing_queue").select(
                "work_id, work_type, processing_state, cascade_metadata, parent_work_id, created_at"
            ).eq("work_id", work_id).single().execute()
            
            if not work_response.data:
                return {'cascade_active': False, 'reason': 'work_not_found'}
            
            work = work_response.data
            
            # Find cascade family (parent + children)
            cascade_family = await self._get_cascade_family(work_id)
            
            # Determine cascade stage
            cascade_stage = self._determine_cascade_stage(work['work_type'], cascade_family)
            
            # Check if cascade is currently active
            cascade_active = (
                work['processing_state'] in ['processing', 'cascading'] or
                any(child['processing_state'] in ['pending', 'claimed', 'processing'] 
                    for child in cascade_family['children'])
            )
            
            return {
                'cascade_active': cascade_active,
                'cascade_stage': cascade_stage,
                'work_type': work['work_type'],
                'processing_state': work['processing_state'],
                'parent_work': cascade_family['parent'],
                'children_work': cascade_family['children'],
                'cascade_metadata': work.get('cascade_metadata', {}),
                'flow_completion': self._calculate_flow_completion(cascade_family),
                'estimated_total_time': self._estimate_cascade_total_time(cascade_family)
            }
            
        except Exception as e:
            logger.error(f"Failed to derive cascade status for {work_id}: {e}")
            return {'cascade_active': False, 'error': str(e)}
    
    async def get_workspace_work_summary(self, workspace_id: str) -> Dict[str, Any]:
        """
        Get comprehensive work summary for a workspace.
        
        Shows all active work, cascade flows, and queue health.
        """
        try:
            # Get all work for workspace
            work_response = supabase.table("agent_processing_queue").select(
                "work_id, work_type, processing_state, created_at, parent_work_id"
            ).eq("workspace_id", workspace_id).order("created_at", desc=True).execute()
            
            work_items = work_response.data or []
            
            # Categorize work by status
            status_counts = self._categorize_work_by_status(work_items)
            
            # Find active cascade flows
            active_cascades = await self._find_active_cascades(work_items)
            
            # Calculate timing metrics
            timing_metrics = self._calculate_timing_metrics(work_items)
            
            return {
                'workspace_id': workspace_id,
                'total_work_items': len(work_items),
                'status_breakdown': status_counts,
                'active_cascade_flows': len(active_cascades),
                'cascade_details': active_cascades,
                'timing_metrics': timing_metrics,
                'last_activity': work_items[0]['created_at'] if work_items else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get workspace work summary for {workspace_id}: {e}")
            return {'error': str(e)}
    
    async def _get_work_data(self, work_id: str, user_workspace_ids: List[str]) -> Optional[Dict[str, Any]]:
        """Get work data with workspace isolation check."""
        try:
            work_response = supabase.table("agent_processing_queue").select("*").eq(
                "work_id", work_id
            ).single().execute()
            
            if not work_response.data:
                return None
            
            work = work_response.data
            
            # Check workspace access
            if work['workspace_id'] not in user_workspace_ids:
                logger.warning(f"Access denied: work {work_id} not in user workspaces")
                return None
            
            return work
            
        except Exception as e:
            logger.error(f"Failed to get work data for {work_id}: {e}")
            return None
    
    async def _derive_substrate_impact(self, work_data: Dict[str, Any]) -> SubstrateImpact:
        """Derive substrate impact from work result."""
        work_result = work_data.get('work_result', {})
        
        return SubstrateImpact(
            proposals_created=work_result.get('proposals_created', 0),
            substrate_created={
                'blocks': work_result.get('blocks_created', 0),
                'context_items': work_result.get('context_items_created', 0)
            },
            relationships_mapped=work_result.get('relationships_created', 0),
            artifacts_generated=work_result.get('artifacts_created', 0)
        )
    
    async def _derive_cascade_flow(self, work_data: Dict[str, Any]) -> CascadeFlow:
        """Derive cascade flow status from work and metadata."""
        work_type = work_data['work_type']
        processing_state = work_data['processing_state']
        cascade_metadata = work_data.get('cascade_metadata', {})
        
        # Define pipeline sequence
        PIPELINE_SEQUENCE = ['P1_SUBSTRATE', 'P2_GRAPH', 'P3_REFLECTION']
        
        if work_type not in PIPELINE_SEQUENCE:
            return CascadeFlow(
                active=False,
                current_stage=None,
                completed_stages=[],
                next_stage=None
            )
        
        current_index = PIPELINE_SEQUENCE.index(work_type)
        completed_stages = PIPELINE_SEQUENCE[:current_index] if current_index > 0 else []
        next_stage = PIPELINE_SEQUENCE[current_index + 1] if current_index < len(PIPELINE_SEQUENCE) - 1 else None
        
        # Check if cascade is active
        cascade_active = (
            processing_state in ['processing', 'cascading'] or
            cascade_metadata.get('cascade_trigger') is not None
        )
        
        return CascadeFlow(
            active=cascade_active,
            current_stage=work_type,
            completed_stages=completed_stages,
            next_stage=next_stage
        )
    
    def _calculate_progress_percentage(self, work_data: Dict[str, Any], cascade_flow: CascadeFlow) -> int:
        """Calculate progress percentage based on work state and cascade position."""
        status = work_data['processing_state']
        work_type = work_data['work_type']
        
        if status == 'completed':
            return 100
        elif status == 'failed':
            return 0
        
        # Base progress by status
        status_progress = {
            'pending': 5,
            'claimed': 10,
            'processing': 50,
            'cascading': 80
        }
        
        base_progress = status_progress.get(status, 0)
        
        # Adjust for cascade position in pipeline
        if cascade_flow.active and work_type in ['P1_SUBSTRATE', 'P2_GRAPH', 'P3_REFLECTION']:
            pipeline_position = {
                'P1_SUBSTRATE': 0.3,  # 30% of total pipeline
                'P2_GRAPH': 0.6,      # 60% of total pipeline
                'P3_REFLECTION': 0.9  # 90% of total pipeline
            }
            
            position_weight = pipeline_position.get(work_type, 0.5)
            cascade_progress = int(position_weight * 100)
            
            # Blend status progress with cascade position
            return min(100, int(base_progress * 0.3 + cascade_progress * 0.7))
        
        return base_progress
    
    def _calculate_estimated_completion(self, work_data: Dict[str, Any], cascade_flow: CascadeFlow) -> Optional[str]:
        """Calculate estimated completion time."""
        status = work_data['processing_state']
        work_type = work_data['work_type']
        
        if status in ['completed', 'failed']:
            return None
        
        # Historical averages per work type (in seconds)
        time_estimates = {
            'P0_CAPTURE': 10,
            'P1_SUBSTRATE': 45,
            'P2_GRAPH': 20,
            'P3_REFLECTION': 15,
            'P4_COMPOSE': 30,
            'MANUAL_EDIT': 10,
            'PROPOSAL_REVIEW': 5,
            'TIMELINE_RESTORE': 15
        }
        
        base_estimate = time_estimates.get(work_type, 30)
        
        # Add cascade time if this is part of an active cascade
        if cascade_flow.active and cascade_flow.next_stage:
            next_stage_estimate = time_estimates.get(cascade_flow.next_stage, 30)
            base_estimate += next_stage_estimate
            
        # Adjust based on current status
        if status == 'processing':
            base_estimate = int(base_estimate * 0.5)  # Already halfway through
        elif status == 'cascading':
            base_estimate = int(base_estimate * 0.2)  # Almost done, just triggering next
        
        return f"~{base_estimate}s"
    
    def _derive_error_info(self, work_data: Dict[str, Any]) -> Optional[WorkError]:
        """Derive error information if work failed."""
        if work_data['processing_state'] != 'failed':
            return None
        
        error_message = work_data.get('error_message', 'Processing failed')
        
        # Categorize error types
        error_code = 'PROCESSING_FAILED'
        if 'timeout' in error_message.lower():
            error_code = 'TIMEOUT'
        elif 'constraint' in error_message.lower():
            error_code = 'CONSTRAINT_VIOLATION'
        elif 'connection' in error_message.lower():
            error_code = 'CONNECTION_ERROR'
        
        recovery_actions = self._get_recovery_actions(work_data['work_type'], error_code)
        
        return WorkError(
            code=error_code,
            message=error_message,
            recovery_actions=recovery_actions
        )
    
    def _get_recovery_actions(self, work_type: str, error_code: str) -> List[str]:
        """Get recovery actions for failed work."""
        common_actions = ["Check error details", "Contact support if issue persists"]
        
        type_actions = {
            'P1_SUBSTRATE': ["Verify dump content is valid", "Check proposal schema"],
            'P2_GRAPH': ["Ensure substrate exists", "Check relationship mapping rules"],
            'P3_REFLECTION': ["Verify substrate and relationships exist"],
            'P4_COMPOSE': ["Check document template availability"],
            'MANUAL_EDIT': ["Verify permissions", "Check data format"]
        }
        
        error_actions = {
            'TIMEOUT': ["Try again in a few minutes", "Check system load"],
            'CONSTRAINT_VIOLATION': ["Verify data integrity", "Check foreign key relationships"],
            'CONNECTION_ERROR': ["Check network connectivity", "Verify service availability"]
        }
        
        actions = type_actions.get(work_type, []) + error_actions.get(error_code, []) + common_actions
        return list(dict.fromkeys(actions))  # Remove duplicates while preserving order
    
    async def _get_cascade_family(self, work_id: str) -> Dict[str, Any]:
        """Get cascade family (parent and children) for a work item."""
        try:
            # Get current work
            current_response = supabase.table("agent_processing_queue").select(
                "work_id, parent_work_id, work_type, processing_state"
            ).eq("work_id", work_id).single().execute()
            
            if not current_response.data:
                return {'parent': None, 'children': []}
            
            current = current_response.data
            parent_work = None
            
            # Get parent work if exists
            if current.get('parent_work_id'):
                parent_response = supabase.table("agent_processing_queue").select(
                    "work_id, work_type, processing_state, created_at"
                ).eq("work_id", current['parent_work_id']).execute()
                
                if parent_response.data:
                    parent_work = parent_response.data[0]
            
            # Get children work
            children_response = supabase.table("agent_processing_queue").select(
                "work_id, work_type, processing_state, created_at"
            ).eq("parent_work_id", work_id).execute()
            
            children_work = children_response.data or []
            
            return {
                'parent': parent_work,
                'children': children_work
            }
            
        except Exception as e:
            logger.error(f"Failed to get cascade family for {work_id}: {e}")
            return {'parent': None, 'children': []}
    
    def _determine_cascade_stage(self, work_type: str, cascade_family: Dict[str, Any]) -> str:
        """Determine which stage of cascade flow this work represents."""
        if work_type == 'P1_SUBSTRATE':
            return 'substrate_creation'
        elif work_type == 'P2_GRAPH':
            return 'relationship_mapping'
        elif work_type == 'P3_REFLECTION':
            return 'pattern_analysis'
        elif work_type == 'P4_COMPOSE':
            return 'document_composition'
        else:
            return 'standalone_operation'
    
    def _categorize_work_by_status(self, work_items: List[Dict[str, Any]]) -> Dict[str, int]:
        """Categorize work items by processing status."""
        status_counts = {
            'pending': 0,
            'processing': 0,
            'cascading': 0,
            'completed': 0,
            'failed': 0
        }
        
        for item in work_items:
            status = item['processing_state']
            if status in status_counts:
                status_counts[status] += 1
            elif status in ['claimed']:
                status_counts['processing'] += 1  # Group claimed with processing
        
        return status_counts
    
    async def _find_active_cascades(self, work_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find active cascade flows in work items."""
        cascades = []
        
        # Group by parent-child relationships
        parents = {}
        for item in work_items:
            parent_id = item.get('parent_work_id')
            if parent_id:
                if parent_id not in parents:
                    parents[parent_id] = []
                parents[parent_id].append(item)
        
        # Find cascade flows with active work
        for parent_id, children in parents.items():
            # Check if any child is active
            active_children = [
                child for child in children 
                if child['processing_state'] in ['pending', 'claimed', 'processing', 'cascading']
            ]
            
            if active_children:
                cascades.append({
                    'parent_work_id': parent_id,
                    'active_children': len(active_children),
                    'total_children': len(children),
                    'work_types': [child['work_type'] for child in children]
                })
        
        return cascades
    
    def _calculate_timing_metrics(self, work_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate timing metrics for work items."""
        if not work_items:
            return {'avg_processing_time': 0, 'oldest_pending_age': 0}
        
        now = datetime.now(timezone.utc)
        
        # Calculate average processing time for completed items
        completed_items = [item for item in work_items if item['processing_state'] == 'completed']
        avg_processing_time = 0
        
        if completed_items:
            total_time = 0
            count = 0
            
            for item in completed_items:
                created_at = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
                # Assume completion time is now if not tracked
                processing_time = (now - created_at).total_seconds()
                total_time += processing_time
                count += 1
            
            avg_processing_time = total_time / count if count > 0 else 0
        
        # Find oldest pending work
        pending_items = [item for item in work_items if item['processing_state'] == 'pending']
        oldest_pending_age = 0
        
        if pending_items:
            oldest_created = min(
                datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
                for item in pending_items
            )
            oldest_pending_age = (now - oldest_created).total_seconds()
        
        return {
            'avg_processing_time': int(avg_processing_time),
            'oldest_pending_age': int(oldest_pending_age),
            'completed_count': len(completed_items),
            'pending_count': len(pending_items)
        }
    
    def _calculate_flow_completion(self, cascade_family: Dict[str, Any]) -> float:
        """Calculate completion percentage of entire cascade flow."""
        all_work = []
        
        if cascade_family['parent']:
            all_work.append(cascade_family['parent'])
        
        all_work.extend(cascade_family['children'])
        
        if not all_work:
            return 0.0
        
        completed = len([w for w in all_work if w['processing_state'] == 'completed'])
        return (completed / len(all_work)) * 100
    
    def _estimate_cascade_total_time(self, cascade_family: Dict[str, Any]) -> int:
        """Estimate total time for complete cascade flow."""
        # Base estimates per stage
        stage_times = {
            'P1_SUBSTRATE': 45,
            'P2_GRAPH': 20,
            'P3_REFLECTION': 15
        }
        
        all_work = []
        if cascade_family['parent']:
            all_work.append(cascade_family['parent'])
        all_work.extend(cascade_family['children'])
        
        total_estimate = sum(
            stage_times.get(w['work_type'], 30)
            for w in all_work
        )
        
        return total_estimate

# Global instance
status_derivation_service = StatusDerivationService()

__all__ = ["status_derivation_service", "StatusDerivationService"]