"""
P1 Validator/Enricher Agent - YARNNN Governance Canon v2.0 Compliant

Sacred Rule: Validates all proposals before governance review
Pipeline: P1_SUBSTRATE (Governance Extension)

This agent validates proposals from both agent and human origins,
providing mandatory intelligence for governance decisions.
"""
# V3.0 DEPRECATION NOTICE:
# This file contains references to context_items table which was merged into blocks table.
# Entity blocks are now identified by semantic_type='entity'.
# This file is legacy/supporting code - update if actively maintained.


import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
from uuid import UUID
from pydantic import BaseModel, Field
import hashlib

from infra.utils.supabase_client import supabase_admin_client as supabase

logger = logging.getLogger("uvicorn.error")


class ProposalConflict(BaseModel):
    """Detected conflict with existing substrate."""
    existing_id: UUID
    existing_title: str
    similarity_score: float
    conflict_type: str  # 'duplicate', 'similar', 'merge_candidate'


class ValidationReport(BaseModel):
    """Agent validation report for governance review."""
    confidence: float = Field(ge=0.0, le=1.0)
    dupes: List[ProposalConflict]
    ontology_hits: List[str]
    suggested_merges: List[UUID]
    warnings: List[str]
    impact_summary: str


class ProposalOperation(BaseModel):
    """Single atomic operation in a proposal."""
    type: str  # CreateBlock, CreateContextItem, AttachContextItem, etc.
    data: Dict[str, Any]


class ProposalValidationRequest(BaseModel):
    """Request to validate a proposal."""
    basket_id: UUID
    workspace_id: UUID
    ops: List[ProposalOperation]
    origin: str  # 'agent' | 'human'
    provenance: List[UUID]  # dump_ids or artifact refs


class P1ValidatorAgent:
    """
    Canonical P1 Validator/Enricher Agent for governance workflow.
    
    Sacred Rule: Validates all proposals regardless of origin.
    Provides mandatory intelligence for human governance decisions.
    """
    
    pipeline = "P1_SUBSTRATE"
    agent_name = "P1ValidatorAgent"
    
    def __init__(self):
        self.logger = logger
        
    async def validate_proposal(self, request: ProposalValidationRequest) -> ValidationReport:
        """
        Validate proposal operations before governance review.
        
        Validation includes:
        - Duplicate detection across existing substrate
        - Impact analysis (affected documents, relationships)
        - Confidence scoring based on operation quality
        - Merge suggestions for similar items
        - Warning detection for potential issues
        """
        try:
            # Get current substrate snapshot for comparison
            substrate_snapshot = await self._get_substrate_snapshot(
                request.basket_id, request.workspace_id
            )
            
            # Validate each operation
            all_conflicts = []
            all_warnings = []
            confidence_scores = []
            suggested_merges = []
            ontology_hits = []
            
            for op in request.ops:
                op_validation = await self._validate_operation(
                    op, substrate_snapshot, request.workspace_id
                )
                
                all_conflicts.extend(op_validation['conflicts'])
                all_warnings.extend(op_validation['warnings'])
                confidence_scores.append(op_validation['confidence'])
                suggested_merges.extend(op_validation['suggested_merges'])
                ontology_hits.extend(op_validation['ontology_hits'])
            
            # Calculate overall confidence
            overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.5
            
            # Generate impact summary
            impact_summary = await self._generate_impact_summary(
                request.ops, request.basket_id, request.workspace_id
            )
            
            return ValidationReport(
                confidence=overall_confidence,
                dupes=all_conflicts,
                ontology_hits=list(set(ontology_hits)),
                suggested_merges=list(set(suggested_merges)),
                warnings=list(set(all_warnings)),
                impact_summary=impact_summary
            )
            
        except Exception as e:
            self.logger.error(f"Proposal validation failed: {e}")
            # Return safe default for failed validation
            return ValidationReport(
                confidence=0.3,
                dupes=[],
                ontology_hits=[],
                suggested_merges=[],
                warnings=[f"Validation failed: {str(e)}"],
                impact_summary="Unable to assess impact due to validation error"
            )
    
    async def _get_substrate_snapshot(self, basket_id: UUID, workspace_id: UUID) -> Dict[str, Any]:
        """Get current substrate state for comparison."""
        try:
            # Get existing blocks
            blocks_response = supabase.table("blocks").select(
                "id,title,body_md,semantic_type,confidence_score,state"
            ).eq("basket_id", str(basket_id)).eq("workspace_id", str(workspace_id)).execute()
            
            # Get existing context items
            context_response = supabase.table("context_items").select(
                "id,title,content,type,normalized_label,state,equivalence_class"
            ).eq("basket_id", str(basket_id)).execute()
            
            return {
                'blocks': blocks_response.data or [],
                'context_items': context_response.data or []
            }
            
        except Exception as e:
            self.logger.warning(f"Failed to get substrate snapshot: {e}")
            return {'blocks': [], 'context_items': []}
    
    async def _validate_operation(
        self, 
        op: ProposalOperation, 
        substrate_snapshot: Dict[str, Any],
        workspace_id: UUID
    ) -> Dict[str, Any]:
        """Validate a single operation against existing substrate."""
        if op.type == 'CreateBlock':
            return await self._validate_create_block(op, substrate_snapshot, workspace_id)
        elif op.type == 'CreateContextItem':
            return await self._validate_create_context_item(op, substrate_snapshot, workspace_id)
        elif op.type == 'MergeContextItems':
            return await self._validate_merge_context_items(op, substrate_snapshot, workspace_id)
        else:
            return {
                'conflicts': [],
                'warnings': [f"Unknown operation type: {op.type}"],
                'confidence': 0.5,
                'suggested_merges': [],
                'ontology_hits': []
            }
    
    async def _validate_create_block(
        self, 
        op: ProposalOperation, 
        substrate_snapshot: Dict[str, Any],
        workspace_id: UUID
    ) -> Dict[str, Any]:
        """Validate CreateBlock operation."""
        conflicts = []
        warnings = []
        suggested_merges = []
        
        block_data = op.data
        title = block_data.get('title', '')
        content = block_data.get('content', '')
        
        # Check for duplicate blocks
        for existing_block in substrate_snapshot['blocks']:
            similarity = self._calculate_similarity(title, existing_block.get('title', ''))
            
            if similarity > 0.9:
                conflicts.append(ProposalConflict(
                    existing_id=existing_block['id'],
                    existing_title=existing_block.get('title', ''),
                    similarity_score=similarity,
                    conflict_type='duplicate'
                ))
            elif similarity > 0.7:
                suggested_merges.append(existing_block['id'])
        
        # Confidence based on content quality
        confidence = 0.7 if len(content) > 50 else 0.5
        if any(word in content.lower() for word in ['goal', 'strategy', 'plan']):
            confidence += 0.1
        
        return {
            'conflicts': conflicts,
            'warnings': warnings,
            'confidence': min(0.95, confidence),
            'suggested_merges': suggested_merges,
            'ontology_hits': []
        }
    
    async def _validate_create_context_item(
        self, 
        op: ProposalOperation, 
        substrate_snapshot: Dict[str, Any],
        workspace_id: UUID
    ) -> Dict[str, Any]:
        """Validate CreateContextItem operation."""
        conflicts = []
        warnings = []
        suggested_merges = []
        
        item_data = op.data
        label = item_data.get('label', '')
        content = item_data.get('content', '')
        
        # Check for duplicate context items
        for existing_item in substrate_snapshot['context_items']:
            existing_label = existing_item.get('normalized_label') or existing_item.get('title', '')
            similarity = self._calculate_similarity(label, existing_label)
            
            if similarity > 0.9:
                conflicts.append(ProposalConflict(
                    existing_id=existing_item['id'],
                    existing_title=existing_label,
                    similarity_score=similarity,
                    conflict_type='duplicate'
                ))
            elif similarity > 0.7:
                suggested_merges.append(existing_item['id'])
        
        # Context item specific validation
        confidence = 0.6
        if len(label) > 3 and len(label) < 50:
            confidence += 0.2
        
        return {
            'conflicts': conflicts,
            'warnings': warnings,
            'confidence': min(0.9, confidence),
            'suggested_merges': suggested_merges,
            'ontology_hits': []
        }
    
    async def _validate_merge_context_items(
        self, 
        op: ProposalOperation, 
        substrate_snapshot: Dict[str, Any],
        workspace_id: UUID
    ) -> Dict[str, Any]:
        """Validate MergeContextItems operation."""
        merge_data = op.data
        from_ids = merge_data.get('from_ids', [])
        canonical_id = merge_data.get('canonical_id')
        
        warnings = []
        
        # Verify all items exist
        existing_ids = {item['id'] for item in substrate_snapshot['context_items']}
        missing_ids = [id for id in from_ids if id not in existing_ids]
        
        if missing_ids:
            warnings.append(f"Cannot merge non-existent items: {missing_ids}")
        
        if canonical_id and canonical_id not in existing_ids:
            warnings.append(f"Canonical item {canonical_id} does not exist")
        
        return {
            'conflicts': [],
            'warnings': warnings,
            'confidence': 0.8 if not warnings else 0.4,
            'suggested_merges': [],
            'ontology_hits': []
        }
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings."""
        if not text1 or not text2:
            return 0.0
            
        # Simple character-based similarity (in production, use semantic similarity)
        text1_normalized = text1.lower().strip()
        text2_normalized = text2.lower().strip()
        
        if text1_normalized == text2_normalized:
            return 1.0
        
        # Jaccard similarity on words
        words1 = set(text1_normalized.split())
        words2 = set(text2_normalized.split())
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    async def _generate_impact_summary(
        self, 
        ops: List[ProposalOperation], 
        basket_id: UUID, 
        workspace_id: UUID
    ) -> str:
        """Generate human-readable impact summary."""
        try:
            # Count operations by type
            op_counts = {}
            for op in ops:
                op_counts[op.type] = op_counts.get(op.type, 0) + 1
            
            # Get affected document count (simplified)
            docs_response = supabase.table("documents").select(
                "id"
            ).eq("basket_id", str(basket_id)).execute()
            
            doc_count = len(docs_response.data) if docs_response.data else 0
            
            # Generate summary
            ops_summary = ", ".join([f"{count} {op_type}" for op_type, count in op_counts.items()])
            
            if doc_count > 0:
                return f"{ops_summary}; affects {doc_count} documents"
            else:
                return f"{ops_summary}; no document impact"
                
        except Exception as e:
            self.logger.warning(f"Failed to generate impact summary: {e}")
            return f"{len(ops)} operations; impact analysis failed"
    
    def get_agent_info(self) -> Dict[str, str]:
        """Get agent information."""
        return {
            "name": self.agent_name,
            "pipeline": self.pipeline,
            "type": "validator",
            "status": "active",
            "sacred_rule": "Validates all proposals before governance review"
        }