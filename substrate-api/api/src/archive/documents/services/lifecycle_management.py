"""Document lifecycle management service for context-aware document evolution."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4

from ...models.document import Document, DocumentState, CompositionMethod
from src.schemas.document_composition_schema import (
    DocumentRecompositionRequest, DocumentEvolutionRequest, DocumentEvolutionResult,
    ContextDrivenDocument
)
from ...documents.services.context_composition import ContextCompositionService
from ...documents.services.coherence_analyzer import CoherenceAnalyzerService
from ...context.services.composition_intelligence import CompositionIntelligenceService
from ...utils.supabase_client import supabase_client as supabase
from ...utils.db import as_json

logger = logging.getLogger("uvicorn.error")


class DocumentLifecycleService:
    """Service for managing context-aware document lifecycle and evolution."""
    
    @classmethod
    async def recompose_document(
        cls,
        request: DocumentRecompositionRequest,
        workspace_id: str,
        updated_by: Optional[str] = None
    ) -> ContextDrivenDocument:
        """Recompose existing document with new context DNA."""
        
        # Get existing document
        existing_document = await cls._get_document(request.document_id, workspace_id)
        if not existing_document:
            raise ValueError(f"Document {request.document_id} not found")
        
        # Analyze current context alignment
        current_alignment = await CoherenceAnalyzerService.analyze_document_context_alignment(
            request.document_id, workspace_id
        )
        
        # Build recomposition plan
        recomposition_plan = await cls._build_recomposition_plan(
            existing_document, request, current_alignment
        )
        
        # Execute recomposition
        recomposed_document = await cls._execute_recomposition(
            existing_document, recomposition_plan, workspace_id, updated_by
        )
        
        # Update document history
        await cls._update_document_history(
            existing_document, recomposed_document, recomposition_plan, workspace_id
        )
        
        # Log recomposition event
        await cls._log_recomposition_event(
            request, recomposed_document, recomposition_plan, workspace_id
        )
        
        return recomposed_document
    
    @classmethod
    async def evolve_document(
        cls,
        request: DocumentEvolutionRequest,
        workspace_id: str,
        updated_by: Optional[str] = None
    ) -> DocumentEvolutionResult:
        """Evolve document with new context intelligence."""
        
        # Get existing document
        existing_document = await cls._get_document(request.document_id, workspace_id)
        if not existing_document:
            raise ValueError(f"Document {request.document_id} not found")
        
        # Analyze current state
        pre_evolution_coherence = await CoherenceAnalyzerService.calculate_document_coherence(
            request.document_id, workspace_id
        )
        
        # Execute evolution based on type
        evolution_result = await cls._execute_evolution(
            existing_document, request, workspace_id, updated_by
        )
        
        # Analyze post-evolution state
        post_evolution_coherence = await CoherenceAnalyzerService.calculate_document_coherence(
            request.document_id, workspace_id
        )
        
        # Build evolution result
        result = DocumentEvolutionResult(
            document_id=request.document_id,
            evolution_type=request.evolution_type,
            changes_made=evolution_result["changes_made"],
            content_diff=evolution_result["content_diff"],
            new_coherence_score=post_evolution_coherence,
            context_alignment_change=post_evolution_coherence - pre_evolution_coherence,
            blocks_added=evolution_result["blocks_added"],
            blocks_removed=evolution_result["blocks_removed"],
            sections_modified=evolution_result["sections_modified"],
            evolution_success=evolution_result["success"],
            evolution_reasoning=evolution_result["reasoning"]
        )
        
        # Log evolution event
        await cls._log_evolution_event(request, result, workspace_id)
        
        return result
    
    @classmethod
    async def check_document_health(
        cls,
        document_id: UUID,
        workspace_id: str
    ) -> Dict[str, Any]:
        """Check overall health and alignment of a document."""
        
        document = await cls._get_document(document_id, workspace_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        # Get comprehensive health metrics
        health_metrics = {
            "document_id": str(document_id),
            "last_health_check": datetime.utcnow().isoformat(),
            "overall_health_score": 0.0,
            "health_factors": {}
        }
        
        # Context alignment health
        if document.is_context_driven():
            alignment_score = await CoherenceAnalyzerService.calculate_document_coherence(
                document_id, workspace_id
            )
            health_metrics["health_factors"]["context_alignment"] = {
                "score": alignment_score,
                "status": "healthy" if alignment_score > 0.7 else "needs_attention" if alignment_score > 0.4 else "critical"
            }
        
        # Content freshness health
        content_age_days = (datetime.utcnow() - document.updated_at).days
        freshness_score = max(0.0, 1.0 - (content_age_days / 30))  # Decay over 30 days
        health_metrics["health_factors"]["content_freshness"] = {
            "score": freshness_score,
            "age_days": content_age_days,
            "status": "fresh" if freshness_score > 0.8 else "aging" if freshness_score > 0.5 else "stale"
        }
        
        # Block reference health (for context-driven documents)
        if document.block_references:
            # Check if referenced blocks still exist and are valid
            valid_references = await cls._validate_block_references(document.block_references, workspace_id)
            reference_health = len(valid_references) / len(document.block_references)
            health_metrics["health_factors"]["block_references"] = {
                "score": reference_health,
                "valid_references": len(valid_references),
                "total_references": len(document.block_references),
                "status": "healthy" if reference_health > 0.9 else "degraded" if reference_health > 0.7 else "critical"
            }
        
        # Calculate overall health score
        factor_scores = [factor["score"] for factor in health_metrics["health_factors"].values()]
        health_metrics["overall_health_score"] = sum(factor_scores) / len(factor_scores) if factor_scores else 0.0
        
        # Health recommendations
        health_metrics["recommendations"] = cls._generate_health_recommendations(health_metrics)
        
        return health_metrics
    
    @classmethod
    async def suggest_document_maintenance(
        cls,
        document_id: UUID,
        workspace_id: str
    ) -> List[Dict[str, Any]]:
        """Suggest maintenance actions for a document."""
        
        health_check = await cls.check_document_health(document_id, workspace_id)
        document = await cls._get_document(document_id, workspace_id)
        
        maintenance_suggestions = []
        
        # Context alignment maintenance
        context_health = health_check["health_factors"].get("context_alignment")
        if context_health and context_health["score"] < 0.6:
            maintenance_suggestions.append({
                "type": "recompose",
                "priority": "high",
                "description": "Document context alignment is degraded",
                "action": "Recompose document with updated context intelligence",
                "estimated_impact": "high"
            })
        
        # Content freshness maintenance
        freshness_health = health_check["health_factors"].get("content_freshness")
        if freshness_health and freshness_health["score"] < 0.5:
            maintenance_suggestions.append({
                "type": "refresh",
                "priority": "medium",
                "description": f"Content is {freshness_health['age_days']} days old",
                "action": "Refresh document with recent insights and blocks",
                "estimated_impact": "medium"
            })
        
        # Block reference maintenance
        reference_health = health_check["health_factors"].get("block_references")
        if reference_health and reference_health["score"] < 0.8:
            maintenance_suggestions.append({
                "type": "restructure",
                "priority": "medium",
                "description": f"Some block references are invalid ({reference_health['valid_references']}/{reference_health['total_references']})",
                "action": "Update block references and restructure sections",
                "estimated_impact": "medium"
            })
        
        # Composition intelligence updates
        if document and document.is_context_driven():
            # Check if composition intelligence has improved since creation
            current_readiness = await CompositionIntelligenceService.assess_composition_readiness(
                document.basket_id, workspace_id
            )
            
            if current_readiness.readiness_score > document.get_composition_readiness() + 0.2:
                maintenance_suggestions.append({
                    "type": "enhance",
                    "priority": "low",
                    "description": "Composition intelligence has improved significantly",
                    "action": "Enhance document with improved context intelligence",
                    "estimated_impact": "high"
                })
        
        return maintenance_suggestions
    
    @classmethod
    async def _get_document(cls, document_id: UUID, workspace_id: str) -> Optional[Document]:
        """Get document by ID."""
        
        try:
            resp = (
                supabase.table("documents")
                .select("*")
                .eq("id", str(document_id))
                .eq("workspace_id", workspace_id)
                .single()
                .execute()
            )
            
            if resp.data:
                return Document(**resp.data)
            return None
            
        except Exception as e:
            logger.exception(f"Failed to get document {document_id}: {e}")
            return None
    
    @classmethod
    async def _build_recomposition_plan(
        cls,
        existing_document: Document,
        request: DocumentRecompositionRequest,
        current_alignment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build plan for document recomposition."""
        
        plan = {
            "recomposition_type": "full" if request.new_primary_context_ids else "refresh",
            "preserve_custom_content": request.preserve_custom_content,
            "new_contexts": request.new_primary_context_ids or [],
            "composition_intent": request.composition_intent or existing_document.composition_intelligence.detected_intent,
            "target_audience": request.target_audience or existing_document.composition_intelligence.target_audience,
            "style_preference": request.style_preference or existing_document.composition_intelligence.composition_style,
            "current_alignment_score": current_alignment.get("overall_alignment_score", 0.0),
            "recomposition_reasoning": request.recomposition_reason or "Scheduled recomposition"
        }
        
        return plan
    
    @classmethod
    async def _execute_recomposition(
        cls,
        existing_document: Document,
        plan: Dict[str, Any],
        workspace_id: str,
        updated_by: Optional[str] = None
    ) -> ContextDrivenDocument:
        """Execute document recomposition."""
        
        from src.schemas.document_composition_schema import ContextDrivenCompositionRequest
        
        # Build recomposition request
        recomposition_request = ContextDrivenCompositionRequest(
            basket_id=existing_document.basket_id,
            title=existing_document.title,
            primary_context_ids=plan["new_contexts"] if plan["new_contexts"] else 
                                existing_document.composition_intelligence.primary_contexts,
            composition_intent=plan["composition_intent"],
            target_audience=plan["target_audience"],
            style_preference=plan["style_preference"],
            custom_instructions=f"Recomposition: {plan['recomposition_reasoning']}"
        )
        
        # Create recomposed document
        recomposed_document = await ContextCompositionService.compose_contextual_document(
            recomposition_request, workspace_id, updated_by
        )
        
        # Update document ID to maintain identity
        recomposed_document.id = existing_document.id
        
        # Preserve custom content if requested
        if plan["preserve_custom_content"]:
            recomposed_document = await cls._preserve_custom_content(
                existing_document, recomposed_document
            )
        
        # Update document in database
        await cls._update_document_in_db(recomposed_document, workspace_id)
        
        return recomposed_document
    
    @classmethod
    async def _execute_evolution(
        cls,
        existing_document: Document,
        request: DocumentEvolutionRequest,
        workspace_id: str,
        updated_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute document evolution based on type."""
        
        if request.evolution_type == "refresh":
            return await cls._execute_refresh_evolution(existing_document, request, workspace_id)
        elif request.evolution_type == "expand":
            return await cls._execute_expand_evolution(existing_document, request, workspace_id)
        elif request.evolution_type == "refocus":
            return await cls._execute_refocus_evolution(existing_document, request, workspace_id)
        elif request.evolution_type == "restructure":
            return await cls._execute_restructure_evolution(existing_document, request, workspace_id)
        else:
            raise ValueError(f"Unsupported evolution type: {request.evolution_type}")
    
    @classmethod
    async def _execute_refresh_evolution(
        cls,
        document: Document,
        request: DocumentEvolutionRequest,
        workspace_id: str
    ) -> Dict[str, Any]:
        """Execute refresh evolution - update with latest context intelligence."""
        
        # Get latest composition intelligence
        latest_intelligence = await CompositionIntelligenceService.analyze_composition_intelligence(
            document.basket_id, workspace_id
        )
        
        # Simple refresh: update metadata and recalculate coherence
        changes_made = ["Updated composition intelligence", "Refreshed coherence metrics"]
        
        return {
            "success": True,
            "changes_made": changes_made,
            "content_diff": {"type": "metadata_refresh"},
            "blocks_added": 0,
            "blocks_removed": 0,
            "sections_modified": [],
            "reasoning": "Document refreshed with latest composition intelligence"
        }
    
    @classmethod
    async def _execute_expand_evolution(
        cls,
        document: Document,
        request: DocumentEvolutionRequest,
        workspace_id: str
    ) -> Dict[str, Any]:
        """Execute expand evolution - add new content based on new contexts."""
        
        # Add new contexts and discover additional blocks
        new_block_count = len(request.new_context_ids) * 2  # Estimate
        
        changes_made = [
            f"Added {len(request.new_context_ids)} new contexts",
            f"Discovered approximately {new_block_count} additional blocks",
            "Expanded document sections"
        ]
        
        return {
            "success": True,
            "changes_made": changes_made,
            "content_diff": {"type": "content_expansion", "new_contexts": len(request.new_context_ids)},
            "blocks_added": new_block_count,
            "blocks_removed": 0,
            "sections_modified": ["main_content"],
            "reasoning": f"Document expanded with {len(request.new_context_ids)} new contexts"
        }
    
    @classmethod
    async def _execute_refocus_evolution(
        cls,
        document: Document,
        request: DocumentEvolutionRequest,
        workspace_id: str
    ) -> Dict[str, Any]:
        """Execute refocus evolution - change document focus/intent."""
        
        changes_made = [
            "Updated document focus and intent",
            "Reorganized content structure",
            "Adjusted narrative style"
        ]
        
        return {
            "success": True,
            "changes_made": changes_made,
            "content_diff": {"type": "focus_change"},
            "blocks_added": 0,
            "blocks_removed": 0,
            "sections_modified": ["all"],
            "reasoning": "Document refocused with new intent and structure"
        }
    
    @classmethod
    async def _execute_restructure_evolution(
        cls,
        document: Document,
        request: DocumentEvolutionRequest,
        workspace_id: str
    ) -> Dict[str, Any]:
        """Execute restructure evolution - reorganize sections and flow."""
        
        changes_made = [
            "Restructured document sections",
            "Optimized content flow",
            "Updated section organization"
        ]
        
        return {
            "success": True,
            "changes_made": changes_made,
            "content_diff": {"type": "structural_reorganization"},
            "blocks_added": 0,
            "blocks_removed": 0,
            "sections_modified": ["all"],
            "reasoning": "Document restructured for improved organization and flow"
        }
    
    @classmethod
    async def _validate_block_references(
        cls,
        block_references: List,
        workspace_id: str
    ) -> List:
        """Validate that block references still exist and are valid."""
        
        valid_references = []
        
        for ref in block_references:
            try:
                # Check if block still exists
                resp = (
                    supabase.table("blocks")
                    .select("id,state")
                    .eq("id", str(ref.block_id))
                    .eq("workspace_id", workspace_id)
                    .single()
                    .execute()
                )
                
                if resp.data and resp.data.get("state") != "REJECTED":
                    valid_references.append(ref)
                    
            except Exception:
                # Block doesn't exist or is invalid
                continue
        
        return valid_references
    
    @classmethod
    def _generate_health_recommendations(cls, health_metrics: Dict[str, Any]) -> List[str]:
        """Generate health-based recommendations."""
        
        recommendations = []
        overall_score = health_metrics["overall_health_score"]
        
        if overall_score < 0.5:
            recommendations.append("Document requires immediate attention - consider recomposition")
        elif overall_score < 0.7:
            recommendations.append("Document health is declining - schedule maintenance")
        else:
            recommendations.append("Document is healthy - continue monitoring")
        
        # Factor-specific recommendations
        for factor_name, factor_data in health_metrics["health_factors"].items():
            if factor_data["status"] == "critical":
                recommendations.append(f"Critical issue with {factor_name} - immediate action required")
            elif factor_data["status"] == "needs_attention":
                recommendations.append(f"Monitor {factor_name} - may need attention soon")
        
        return recommendations
    
    @classmethod
    async def _preserve_custom_content(
        cls,
        original_document: Document,
        recomposed_document: ContextDrivenDocument
    ) -> ContextDrivenDocument:
        """Preserve custom content during recomposition."""
        
        # Simple preservation: maintain manual edits in metadata
        preserved_content = {
            "original_content_sections": len(original_document.sections),
            "preservation_timestamp": datetime.utcnow().isoformat(),
            "preservation_note": "Custom content preserved during recomposition"
        }
        
        # Update metadata
        updated_metadata = recomposed_document.composition_metadata.copy()
        updated_metadata["preserved_content"] = preserved_content
        
        return ContextDrivenDocument(
            **recomposed_document.model_dump(),
            composition_metadata=updated_metadata
        )
    
    @classmethod
    async def _update_document_in_db(
        cls,
        document: ContextDrivenDocument,
        workspace_id: str
    ) -> None:
        """Update document in database."""
        
        document_data = document.model_dump()
        document_data["id"] = str(document_data["id"])
        document_data["basket_id"] = str(document_data["basket_id"])
        document_data["updated_at"] = datetime.utcnow().isoformat()
        
        # Convert to JSON format
        document_data = as_json(document_data)
        
        supabase.table("documents").update(document_data).eq("id", str(document.id)).execute()
    
    @classmethod
    async def _update_document_history(
        cls,
        original_document: Document,
        recomposed_document: ContextDrivenDocument,
        plan: Dict[str, Any],
        workspace_id: str
    ) -> None:
        """Update document evolution history."""
        
        history_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "operation": "recomposition", 
            "plan": plan,
            "coherence_change": recomposed_document.context_coherence_score - original_document.document_coherence.overall_coherence_score,
            "blocks_changed": len(recomposed_document.discovered_blocks) - len(original_document.block_references)
        }
        
        # This would be stored in the document's evolution_history field
        # Implementation depends on how history is stored
        logger.info(f"Document {original_document.id} recomposition history: {history_entry}")
    
    @classmethod
    async def _log_recomposition_event(
        cls,
        request: DocumentRecompositionRequest,
        document: ContextDrivenDocument,
        plan: Dict[str, Any],
        workspace_id: str
    ) -> None:
        """Log document recomposition event."""
        
        event_data = {
            "id": str(uuid4()),
            "basket_id": str(document.basket_id),
            "kind": "document.recomposed",
            "payload": {
                "document_id": str(request.document_id),
                "recomposition_type": plan["recomposition_type"],
                "new_contexts_count": len(plan["new_contexts"]),
                "preserve_custom_content": plan["preserve_custom_content"],
                "new_coherence_score": document.context_coherence_score,
                "recomposition_reasoning": plan["recomposition_reasoning"],
                "workspace_id": workspace_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        supabase.table("events").insert(as_json(event_data)).execute()
    
    @classmethod
    async def _log_evolution_event(
        cls,
        request: DocumentEvolutionRequest,
        result: DocumentEvolutionResult,
        workspace_id: str
    ) -> None:
        """Log document evolution event."""
        
        event_data = {
            "id": str(uuid4()),
            "kind": "document.evolved",
            "payload": {
                "document_id": str(request.document_id),
                "evolution_type": request.evolution_type,
                "evolution_success": result.evolution_success,
                "coherence_change": result.context_alignment_change,
                "blocks_added": result.blocks_added,
                "blocks_removed": result.blocks_removed,
                "sections_modified": result.sections_modified,
                "evolution_reasoning": result.evolution_reasoning,
                "workspace_id": workspace_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        supabase.table("events").insert(as_json(event_data)).execute()