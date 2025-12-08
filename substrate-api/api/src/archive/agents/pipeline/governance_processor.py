"""
Governance Dump Processor - Canonical Implementation
Integrates ImprovedP1SubstrateAgent with governance workflow for quality substrate extraction.

V3.1: Semantic duplicate detection integrated into block creation workflow.
"""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4

from app.agents.pipeline.improved_substrate_agent import ImprovedP1SubstrateAgent
from infra.utils.supabase_client import supabase_admin_client as supabase
from services.enhanced_cascade_manager import canonical_cascade_manager
from infra.substrate.services.semantic_primitives import (
    semantic_search,
    SemanticSearchFilters,
    DUPLICATE_HIGH_CONFIDENCE,
    DUPLICATE_MEDIUM_CONFIDENCE
)
from jobs.embedding_generator import queue_embedding_generation

logger = logging.getLogger("uvicorn.error")


@dataclass
class SubstrateCandidate:
    """Structured representation of extracted substrate prior to proposal creation."""

    type: str
    content: Optional[str] = None
    semantic_type: Optional[str] = None
    label: Optional[str] = None
    confidence: float = 0.7
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GovernanceProposal:
    """Lightweight governance proposal descriptor used for testing and planning."""

    basket_id: UUID
    workspace_id: UUID
    ops: List[Dict[str, Any]]
    provenance: List[UUID] = field(default_factory=list)
    confidence: float = 0.0
    proposal_kind: str = "Extraction"
    origin: str = "agent"


def _sanitize_for_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _sanitize_for_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize_for_json(v) for v in value]
    if isinstance(value, tuple):
        return [_sanitize_for_json(v) for v in value]
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return value


class GovernanceDumpProcessor:
    """
    Canonical governance processor using ImprovedP1SubstrateAgent for quality extraction.
    
    Creates governance proposals with high-quality substrate ingredients.
    """
    
    def __init__(self):
        self.logger = logger
        try:
            self.p1_agent = ImprovedP1SubstrateAgent()
        except RuntimeError as e:
            self.logger.error(f"Failed to initialize ImprovedP1SubstrateAgent: {e}")
            # Fall back to None - governance processor will handle gracefully
            self.p1_agent = None

        # Feature flags for degraded environments
        self._timeline_enabled = True
        self._execution_logging_enabled = True
        
    async def process_batch_dumps(
        self,
        dump_ids: List[UUID],
        basket_id: UUID,
        workspace_id: UUID,
        max_blocks: int = 20
    ) -> Dict[str, Any]:
        """
        Process multiple dumps through comprehensive governance review for Share Updates.
        
        Creates unified proposal from cross-content analysis of all provided dumps.
        """
        start_time = datetime.utcnow()
        
        try:
            # Validate P1 agent is available
            if not self.p1_agent:
                raise RuntimeError("ImprovedP1SubstrateAgent not initialized - likely missing OPENAI_API_KEY")
            
            # Canon purity: governance is mandatory; no direct substrate writes here.
            
            # Create comprehensive governance proposal with structured ingredients
            proposals_result = await self._create_batch_ingredient_proposals(
                dump_ids, basket_id, workspace_id, max_blocks
            )
            
            processing_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            self.logger.info(
                f"Governance batch processing v2 completed: {len(dump_ids)} dumps, "
                f"proposals={proposals_result['proposals_created']}, "
                f"processing_time_ms={processing_time_ms}"
            )
            
            return {
                **proposals_result,
                "processing_time_ms": processing_time_ms,
                "batch_mode": True,
                "source_dumps": len(dump_ids)
            }
            
        except Exception as e:
            self.logger.error(f"Governance batch processing v2 failed for dumps {dump_ids}: {e}")
            raise
        
    async def process_dump(
        self, 
        dump_id: UUID, 
        basket_id: UUID, 
        workspace_id: UUID,
        max_blocks: int = 10
    ) -> Dict[str, Any]:
        """
        Process dump through governance with structured knowledge extraction.
        
        Creates governance proposals containing structured data ingredients.
        """
        start_time = datetime.utcnow()
        
        try:
            # Validate P1 agent is available
            if not self.p1_agent:
                raise RuntimeError("ImprovedP1SubstrateAgent not initialized - likely missing OPENAI_API_KEY")
            
            # Canon purity: governance is mandatory; no direct substrate writes here.
            
            # Create governance proposals with structured ingredients
            proposals_result = await self._create_ingredient_proposals(
                dump_id, basket_id, workspace_id, max_blocks
            )
            
            processing_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            self.logger.info(
                f"Governance dump processing v2 completed: dump_id={dump_id}, "
                f"proposals={proposals_result['proposals_created']}, "
                f"processing_time_ms={processing_time_ms}"
            )
            
            return {
                "dump_id": str(dump_id),
                "proposals_created": proposals_result["proposals_created"],
                "proposal_ids": proposals_result["proposal_ids"],
                "processing_time_ms": processing_time_ms,
                "confidence": proposals_result.get("avg_confidence", 0.0),
                "method": "quality_extraction_governance"
            }
            
        except Exception as e:
            self.logger.error(f"Governance dump processing failed for dump {dump_id}: {e}")
            raise
    
    async def _check_governance_enabled(self, workspace_id: UUID) -> bool:
        """Check if governance is enabled for workspace."""
        try:
            response = supabase.table("workspace_governance_settings").select(
                "governance_enabled"
            ).eq("workspace_id", str(workspace_id)).single().execute()
            
            if response.data:
                return response.data.get("governance_enabled", False)
            else:
                # Default to governance enabled for new workspaces
                return True
                
        except Exception as e:
            self.logger.warning(f"Failed to check governance settings: {e}")
            return True  # Fail safe to governance
    
    async def _create_ingredient_proposals(
        self,
        dump_id: UUID,
        basket_id: UUID, 
        workspace_id: UUID,
        max_blocks: int
    ) -> Dict[str, Any]:
        """
        Create governance proposals containing structured knowledge ingredients.
        """
        try:
            # Use improved P1 Agent to extract quality ingredients
            substrate_result = await self.p1_agent.create_substrate({
                "dump_id": str(dump_id),
                "workspace_id": str(workspace_id),
                "basket_id": str(basket_id),
                "max_blocks": max_blocks,
                "agent_id": "canonical_governance_processor"
            })
            substrate_result = _sanitize_for_json(substrate_result)

            # V3.0: Log extraction quality metrics for unified substrate
            substrate_ingredients = substrate_result.get("substrate_ingredients", [])
            extraction_summary = substrate_result.get("extraction_summary", {})
            avg_confidence = substrate_result.get("agent_confidence", 0.0)
            processing_time = substrate_result.get("processing_time_ms", 0)

            try:
                await self._log_extraction_metrics(
                    dump_id=dump_id,
                    basket_id=basket_id,
                    workspace_id=workspace_id,
                    agent_version="improved_p1_v3_unified_substrate",
                    extraction_method=substrate_result.get("extraction_method", "focused_extraction"),
                    blocks_created=extraction_summary.get("total_blocks", len(substrate_ingredients)),
                    context_items_created=0,  # V3.0: No separate context_items
                    avg_confidence=avg_confidence,
                    processing_time_ms=processing_time
                )
            except Exception as metrics_error:
                self.logger.warning(f"Failed to log extraction metrics: {metrics_error}")

            # V3.0: Single unified substrate source
            blocks_source = substrate_ingredients or substrate_result.get("blocks_created", [])

            # Respect extraction summary total if provided
            extracted_total = extraction_summary.get("total_blocks") if isinstance(extraction_summary, dict) else None
            if extracted_total is not None:
                try:
                    max_blocks = min(max_blocks, max(0, int(extracted_total)))
                except Exception:
                    pass

            # Sort by confidence desc and cap to max_blocks for signal density
            def _conf(b: Dict[str, Any]) -> float:
                try:
                    return float(b.get("confidence") if b.get("confidence") is not None else b.get("confidence_score", 0.7))
                except Exception:
                    return 0.7
            try:
                blocks_source = sorted(blocks_source, key=_conf, reverse=True)
            except Exception:
                pass

            if max_blocks > 0:
                blocks_source = blocks_source[: max(1, int(max_blocks))]

            # V3.0: All substrate is blocks (no separate context_items processing)
            ops_accum: List[Dict[str, Any]] = []
            block_confidences: List[float] = []

            if not blocks_source:
                return {
                    "proposals_created": 0,
                    "proposal_ids": [],
                    "avg_confidence": 0.0
                }

            for block_data in blocks_source:
                confidence = block_data.get("confidence") if isinstance(block_data, dict) else None
                if confidence is None:
                    confidence = block_data.get("confidence_score", 0.7)
                try:
                    block_confidences.append(float(confidence))
                except Exception:
                    block_confidences.append(0.7)
                metadata = _sanitize_for_json(block_data.get("metadata", {}))
                if isinstance(block_data, dict):
                    block_data["metadata"] = metadata
                semantic_type = block_data.get("semantic_type") or metadata.get("semantic_type") or metadata.get("fact_type") or "insight"
                title = block_data.get("title") or metadata.get("title") or "Untitled insight"
                # CRITICAL FIX: Include content field that P1 agent generated
                content = block_data.get("content", "")
                if not content:
                    # Fallback to title if no content (shouldn't happen with new P1 agent)
                    content = title

                # V3.0: Create unified block with emergent anchors
                ops_accum.append({
                    "type": "CreateBlock",
                    "data": {
                        "title": title,
                        "content": content,
                        "semantic_type": semantic_type,
                        "metadata": metadata,
                        "confidence": confidence,
                        # V3.0: Include emergent anchor data
                        "anchor_role": block_data.get("anchor_role"),
                        "anchor_status": block_data.get("anchor_status"),
                        "anchor_confidence": block_data.get("anchor_confidence")
                    }
                })

            if not ops_accum:
                return {
                    "proposals_created": 0,
                    "proposal_ids": [],
                    "avg_confidence": 0.0
                }

            avg_confidence = sum(block_confidences) / len(block_confidences) if block_confidences else 0.0
            impact_summary = f"{len(ops_accum)} substrate operations"

            # V3.0: All substrate is blocks (no context_items_total needed)
            proposal_payload = {
                "basket_id": str(basket_id),
                "workspace_id": str(workspace_id),
                "proposal_kind": "Extraction",
                "origin": "agent",
                "provenance": [{"dump_id": str(dump_id), "method": "structured_extraction_v2"}],
                "ops": ops_accum,
                "blast_radius": "Local",
                "validator_report": {
                    "confidence": avg_confidence,
                    "method": "structured_knowledge_extraction",
                    "ingredients_count": len(ops_accum),  # V3.0: Total operations count
                    "extraction_quality": "high" if avg_confidence > 0.7 else "medium",
                    "impact_summary": impact_summary
                },
                "status": "PROPOSED"
            }

            response = supabase.table("proposals").insert(_sanitize_for_json(proposal_payload)).execute()

            proposal_ids: List[str] = []
            inserted_records: List[Dict[str, Any]] = []
            if response.data:
                inserted_records = [_sanitize_for_json(record) for record in response.data]
                proposal_ids = [str(record["id"]) for record in inserted_records if record.get("id") is not None]

                for proposal in inserted_records:
                    await self._check_auto_approval(proposal)

            return {
                "proposals_created": len(inserted_records),
                "proposal_ids": proposal_ids,
                "avg_confidence": avg_confidence
            }
            
        except Exception as e:
            self.logger.exception("Failed to create ingredient proposals")
            return {
                "proposals_created": 0,
                "proposal_ids": [],
                "avg_confidence": 0.0
            }
    
    async def _create_batch_ingredient_proposals(
        self,
        dump_ids: List[UUID], 
        basket_id: UUID, 
        workspace_id: UUID, 
        max_blocks: int
    ) -> Dict[str, Any]:
        """Create unified governance proposal from comprehensive batch analysis."""
        
        try:
            # Use improved P1 Agent batch mode for comprehensive analysis
            agent_request = {
                "dump_ids": [str(did) for did in dump_ids],
                "workspace_id": str(workspace_id),
                "basket_id": str(basket_id),
                "agent_id": f"canonical_governance_batch_{uuid4().hex[:8]}",
                "max_blocks": max_blocks
            }
            
            substrate_result = await self.p1_agent.create_substrate(agent_request)
            blocks_created = _sanitize_for_json(
                substrate_result.get("block_ingredients") or substrate_result.get("blocks_created", [])
            )

            if not blocks_created:
                return {
                    "proposals_created": 0,
                    "status": "no_substrate_from_batch",
                    "message": f"No structured ingredients extracted from {len(dump_ids)} dumps"
                }
            
            # Create single unified proposal
            if max_blocks > 0:
                blocks_created = blocks_created[: max(1, int(max_blocks))]

            proposal_id = await self._create_unified_governance_proposal(
                basket_id, workspace_id, blocks_created, dump_ids
            )
            
            return {
                "proposals_created": 1,
                "proposal_ids": [str(proposal_id)],
                "substrate_candidates": len(blocks_created),
                "comprehensive_analysis": True,
                "source_dumps": len(dump_ids)
            }
            
        except Exception as e:
            self.logger.exception("Failed to create batch ingredient proposals")
            return {
                "proposals_created": 0,
                "proposal_ids": [],
                "comprehensive_analysis": False
            }
    
    async def _direct_substrate_creation(
        self,
        dump_id: UUID,
        basket_id: UUID,
        workspace_id: UUID,
        max_blocks: int
    ) -> Dict[str, Any]:
        """
        Direct substrate creation when governance is disabled.
        Uses improved agent but bypasses proposal workflow.
        """
        try:
            # Use improved P1 Agent directly
            result = await self.p1_agent.create_substrate({
                "dump_id": str(dump_id),
                "workspace_id": str(workspace_id),
                "basket_id": str(basket_id),
                "max_blocks": max_blocks,
                "agent_id": "direct_processor_v2"
            })
            
            return {
                "dump_id": str(dump_id),
                "proposals_created": 0,  # No proposals, direct creation
                "blocks_created": len(result.get("blocks_created", [])),
                "context_items_created": 0,  # V3.0: No separate context_items
                "processing_time_ms": result.get("processing_time_ms"),
                "confidence": result.get("agent_confidence"),
                "method": "direct_quality_extraction"
            }
            
        except Exception as e:
            self.logger.error(f"Direct substrate creation failed: {e}")
            raise
    
    async def _create_unified_governance_proposal(
        self,
        basket_id: UUID,
        workspace_id: UUID, 
        blocks_created: List[Dict[str, Any]],
        dump_ids: List[UUID]
    ) -> UUID:
        """Create single unified proposal for comprehensive batch processing."""
        
        sanitized_blocks: List[Dict[str, Any]] = []
        for block in blocks_created:
            sanitized_blocks.append({
                **block,
                "metadata": _sanitize_for_json(block.get("metadata", {})),
            })

        # Generate comprehensive summary
        summary_parts = []
        total_goals = sum(len(block.get("metadata", {}).get("knowledge_ingredients", {}).get("goals", [])) for block in sanitized_blocks)
        total_constraints = sum(len(block.get("metadata", {}).get("knowledge_ingredients", {}).get("constraints", [])) for block in sanitized_blocks)
        total_metrics = sum(len(block.get("metadata", {}).get("knowledge_ingredients", {}).get("metrics", [])) for block in sanitized_blocks)
        total_entities = sum(len(block.get("metadata", {}).get("knowledge_ingredients", {}).get("entities", [])) for block in sanitized_blocks)
        
        summary_parts.append(f"Comprehensive analysis of {len(dump_ids)} content sources")
        if total_goals > 0:
            summary_parts.append(f"{total_goals} strategic goals identified")
        if total_constraints > 0:
            summary_parts.append(f"{total_constraints} operational constraints") 
        if total_metrics > 0:
            summary_parts.append(f"{total_metrics} measurable success criteria")
        if total_entities > 0:
            summary_parts.append(f"{total_entities} key stakeholders and systems")
            
        ops_summary = "; ".join(summary_parts)
        
        # Translate blocks into an array of CreateBlock operations
        ops: List[Dict[str, Any]] = []
        confidences: List[float] = []
        for b in sanitized_blocks:
            conf = b.get("confidence") if isinstance(b, dict) else None
            if conf is None:
                conf = b.get("confidence_score", 0.7)
            try:
                confidences.append(float(conf))
            except Exception:
                confidences.append(0.7)
            ops.append({
                "type": "CreateBlock",
                "data": {
                    "title": b.get("title"),
                    "content": b.get("content"),
                    "semantic_type": b.get("semantic_type"),
                    "metadata": _sanitize_for_json(b.get("metadata", {})),
                    "confidence": conf
                }
            })

        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        # Create unified proposal data using canonical ops[] array
        proposal_data = {
            "id": str(uuid4()),
            "workspace_id": str(workspace_id),
            "basket_id": str(basket_id),
            "proposal_kind": "Extraction",
            "origin": "agent",
            "status": "PROPOSED",
            "ops": ops,
            "metadata": {
                "batch_mode": True,
                "source_dumps": len(dump_ids),
                "comprehensive_review": True,
                "processing_method": "share_updates_batch",
                "ops_summary": ops_summary
            },
            "validator_report": {
                "confidence": avg_confidence,
                "method": "structured_knowledge_batch",
                "ingredients_count": total_entities,
                "impact_summary": ops_summary or "batch substrate extraction"
            }
        }
        
        response = supabase.table("proposals").insert(_sanitize_for_json(proposal_data)).execute()

        if not response.data:
            raise RuntimeError("Failed to create unified governance proposal")

        inserted_record = _sanitize_for_json(response.data[0])
        proposal_id = UUID(str(inserted_record.get("id")))
        self.logger.info(
            "Created unified proposal %s from %d dumps",
            proposal_id,
            len(dump_ids)
        )

        # Auto-approval logic per Canon v2.2: Agent origin + confidence > 0.7 → Auto-approved
        await self._check_auto_approval(inserted_record)

        return proposal_id
    
    async def _check_auto_approval(self, proposal: Dict[str, Any]) -> bool:
        """
        Check if proposal meets auto-approval criteria per Canon v2.2:
        Agent origin + confidence > 0.7 → Auto-approved
        """
        try:
            # Check auto-approval criteria
            origin = proposal.get("origin")
            validator_report = proposal.get("validator_report", {})
            confidence = validator_report.get("confidence", 0.0) if isinstance(validator_report, dict) else 0.0
            
            should_auto_approve = (
                origin == "agent" and 
                confidence > 0.7
            )
            
            if should_auto_approve:
                proposal_id = str(proposal["id"])
                self.logger.info(f"Auto-approving proposal {proposal_id} (origin={origin}, confidence={confidence})")
                
                # Update proposal status to APPROVED
                supabase.table("proposals").update({
                    "status": "APPROVED",
                    "reviewed_at": datetime.utcnow().isoformat(),
                    "review_notes": f"Auto-approved: agent origin with confidence {confidence:.3f} > 0.7"
                }).eq("id", proposal_id).execute()

                # Execute the proposal operations
                execution_result = await self._execute_proposal_operations(proposal)

                supabase.table("proposals").update({
                    "is_executed": True,
                    "executed_at": datetime.utcnow().isoformat()
                }).eq("id", proposal_id).execute()

                created_substrate_ids = execution_result.get("created_substrate_ids", {}) if execution_result else {}
                blocks_created = len(created_substrate_ids.get("blocks", []))

                # V3.0: No separate context_items (all substrate is blocks)
                basket_id = proposal.get("basket_id")
                workspace_id = proposal.get("workspace_id")

                if blocks_created:
                    if not basket_id or not workspace_id:
                        self.logger.warning(
                            "Skipping cascade trigger for proposal %s due to missing basket/workspace",
                            proposal_id
                        )
                        self.logger.info(
                            "Auto-approved proposal %s created substrate but lacks routing context",
                            proposal_id
                        )
                    else:
                        cascade_user_id = (
                            proposal.get("created_by")
                            or proposal.get("created_by_user")
                            or proposal.get("created_by_user_id")
                            or proposal.get("reviewer_id")
                            or proposal.get("user_id")
                            or "00000000-0000-0000-0000-000000000000"
                        )
                        try:
                            await canonical_cascade_manager.trigger_p1_substrate_cascade(
                                proposal_id=proposal_id,
                                basket_id=str(basket_id),
                                workspace_id=str(workspace_id),
                                user_id=str(cascade_user_id),
                                substrate_created={
                                    "blocks": blocks_created
                                    # V3.0: No context_items field
                                }
                            )
                            self.logger.info(
                                "Triggered P1→P2 cascade for proposal %s (blocks=%s)",
                                proposal_id,
                                blocks_created
                            )
                        except Exception as cascade_error:
                            self.logger.warning(
                                "Failed to trigger P1→P2 cascade for proposal %s: %s",
                                proposal_id,
                                cascade_error
                            )
                else:
                    self.logger.info(
                        "Auto-approved proposal %s created no new substrate; skipping cascade",
                        proposal_id
                    )

                self.logger.info(f"Auto-approved and executed proposal {proposal_id}")
                return True
            else:
                self.logger.info(f"Proposal {proposal['id']} requires manual review (origin={origin}, confidence={confidence})")
                return False
                
        except Exception as e:
            self.logger.error(f"Auto-approval check failed for proposal {proposal.get('id')}: {e}")
            return False
    
    async def _execute_proposal_operations(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the operations in an approved proposal to create substrate."""
        try:
            proposal_id = proposal["id"]
            ops = proposal.get("ops", [])
            basket_id = proposal.get("basket_id")
            workspace_id = proposal.get("workspace_id")

            self.logger.info(f"Executing {len(ops)} operations for proposal {proposal_id}")

            executed_operations = []
            created_substrate_ids: Dict[str, List[str]] = {
                "blocks": []
                # V3.0: No context_items (all substrate is blocks)
            }

            for i, op in enumerate(ops):
                op_type = (op.get("type") if isinstance(op, dict) else None) or (op.get("operation_type") if isinstance(op, dict) else None)
                op_data = op.get("data", op) if isinstance(op, dict) else op
                try:
                    if op_type == "CreateBlock":
                        metadata = _sanitize_for_json(op_data.get("metadata") or {})
                        # Canon-compliant: P1 agent provides title and content separately
                        title = op_data.get("title") or metadata.get("title") or "Untitled insight"
                        semantic_type_raw = (
                            op_data.get("semantic_type")
                            or metadata.get("semantic_type")
                            or metadata.get("fact_type")
                            or metadata.get("semanticType")
                        )
                        if isinstance(semantic_type_raw, str):
                            semantic_type = semantic_type_raw.strip() or "insight"
                        else:
                            semantic_type = "insight"
                        if not semantic_type:
                            semantic_type = "insight"
                            self.logger.warning(
                                "Proposal %s CreateBlock missing semantic_type; defaulting to insight. op_data=%s",
                                proposal_id,
                                op_data
                            )
                        confidence = op_data.get("confidence") or metadata.get("confidence") or 0.7
                        try:
                            confidence_value = float(confidence)
                        except Exception:
                            confidence_value = 0.7
                        # Canon-compliant: P1 agent provides content in 'content' field
                        content = op_data.get("content", "")
                        if not content:
                            self.logger.warning(f"Block missing content: {title}")
                            content = metadata.get("summary", "No content provided")
                        
                        body = content if isinstance(content, str) else str(content)

                        # V3.1: Semantic duplicate detection before block creation
                        duplicate_check_result = await self._check_semantic_duplicate(
                            basket_id=str(basket_id),
                            title=title,
                            content=body,
                            semantic_type=semantic_type
                        )

                        # If high confidence duplicate found, skip creation and log merge suggestion
                        if duplicate_check_result and duplicate_check_result['is_duplicate']:
                            self.logger.info(
                                f"V3.1 Semantic duplicate detected: similarity={duplicate_check_result['similarity']:.2f}, "
                                f"existing_block={duplicate_check_result['existing_block_id']}. "
                                f"Skipping creation of '{title[:50]}...'"
                            )

                            # Record as skipped operation (future: could create MERGE proposal)
                            executed_operations.append({
                                "type": "CreateBlock",
                                "success": True,
                                "skipped": True,
                                "reason": "semantic_duplicate",
                                "duplicate_of": duplicate_check_result['existing_block_id'],
                                "similarity_score": duplicate_check_result['similarity']
                            })
                            continue  # Skip to next operation

                        # V3.0: Canon-compliant block creation with emergent anchors
                        # V3.1: Enhanced with duplicate detection metadata
                        block_metadata = metadata.copy() if metadata else {}
                        try:
                            fingerprint = hashlib.sha256(body.strip().lower().encode("utf-8")).hexdigest()
                            block_metadata.setdefault("content_hash", fingerprint)
                        except Exception:
                            fingerprint = None
                        if duplicate_check_result and duplicate_check_result.get('similar_blocks'):
                            block_metadata['v3_1_similar_blocks'] = [
                                {
                                    'block_id': sb['id'],
                                    'similarity': sb['similarity']
                                }
                                for sb in duplicate_check_result['similar_blocks']
                            ]

                        block_payload = _sanitize_for_json({
                            "basket_id": str(basket_id),
                            "workspace_id": str(workspace_id),
                            "title": title,
                            "content": body,
                            "semantic_type": semantic_type,
                            "confidence_score": confidence_value,
                            "metadata": block_metadata,
                            "state": "ACCEPTED",
                            "status": "accepted",
                            # V3.0: Emergent anchor fields
                            "anchor_role": op_data.get("anchor_role"),
                            "anchor_status": op_data.get("anchor_status") or ("proposed" if op_data.get("anchor_role") else None),
                            "anchor_confidence": op_data.get("anchor_confidence")
                        })

                        insert_resp = (
                            supabase
                            .table("blocks")
                            .insert(block_payload)
                            .execute()
                        )

                        if getattr(insert_resp, "error", None):
                            raise RuntimeError(f"block insert failed: {insert_resp.error}")

                        created_id = None
                        if insert_resp.data:
                            created_id = insert_resp.data[0].get("id") if isinstance(insert_resp.data, list) else insert_resp.data.get("id")

                        if not created_id:
                            # Fallback: lookup most recent block with same basket/title
                            lookup_resp = (
                                supabase
                                .table("blocks")
                                .select("id")
                                .eq("basket_id", str(basket_id))
                                .eq("title", title)
                                .order("created_at", desc=True)
                                .limit(1)
                                .execute()
                            )
                            if lookup_resp.data:
                                candidate = lookup_resp.data[0]
                                created_id = candidate.get("id")

                        if not created_id:
                            raise RuntimeError("block insert returned no id")

                        # V3.1: Queue embedding generation for newly created ACCEPTED block
                        try:
                            await queue_embedding_generation(str(created_id))
                            self.logger.debug(f"V3.1: Queued embedding generation for block {created_id}")
                        except Exception as embed_error:
                            # Non-blocking: log error but continue
                            self.logger.warning(f"V3.1: Failed to queue embedding for block {created_id}: {embed_error}")

                        if self._timeline_enabled:
                            try:
                                timeline_resp = supabase.rpc(
                                    'fn_timeline_emit',
                                    {
                                        "p_basket_id": str(basket_id),
                                        "p_kind": "block.created",
                                        "p_ref_id": str(created_id),
                                        "p_preview": (title or "")[:140],
                                        "p_payload": _sanitize_for_json({
                                            "source": "governance_auto_execute",
                                            "proposal_id": proposal_id,
                                            "semantic_type": semantic_type,
                                            "confidence": confidence_value
                                        })
                                    }
                                ).execute()
                                if getattr(timeline_resp, "error", None):
                                    raise RuntimeError(timeline_resp.error)
                            except Exception as timeline_error:
                                self._timeline_enabled = False
                                self.logger.warning(
                                    "Failed to emit timeline event for block %s: %s",
                                    created_id,
                                    timeline_error
                                )

                        executed_operations.append({
                            "type": "CreateBlock",
                            "success": True,
                            "created_id": created_id
                        })
                        created_substrate_ids["blocks"].append(str(created_id))

                    # V3.0: CreateContextItem removed - all substrate is blocks now

                    else:
                        self.logger.warning(f"Unsupported operation type: {op_type}")
                        
                except Exception as op_error:
                    self.logger.error(f"Failed to execute operation {i}: {op_error}")
                    executed_operations.append({
                        "type": op_type,
                        "success": False,
                        "error": str(op_error)
                    })
            
            # Record execution results; tolerate older schema variants
            execution_summary = {
                "executed": executed_operations,
                "success_count": len([op for op in executed_operations if op.get("success")]),
                "created_substrate": created_substrate_ids
            }

            if self._execution_logging_enabled and executed_operations:
                execution_rows: List[Dict[str, Any]] = []
                sanitized_summary = _sanitize_for_json(execution_summary)

                for index, op_result in enumerate(executed_operations):
                    op_type = op_result.get("type") or "unknown"
                    success = bool(op_result.get("success"))
                    result_data = {
                        k: v for k, v in op_result.items()
                        if k not in {"type", "success", "error"}
                    } or {}

                    row: Dict[str, Any] = {
                        "proposal_id": str(proposal_id),
                        "operation_index": index,
                        "operation_type": op_type,
                        "success": success,
                        "result_data": _sanitize_for_json(result_data),
                        "error_message": op_result.get("error"),
                    }

                    created_id = op_result.get("created_id")
                    if created_id:
                        row["substrate_id"] = str(created_id)

                    # Only attach aggregate metadata on the first row to reduce duplication
                    if index == 0:
                        row["operations_count"] = len(ops)
                        row["operations_summary"] = sanitized_summary

                    execution_rows.append(row)

                try:
                    exec_resp = supabase.table("proposal_executions").insert(_sanitize_for_json(execution_rows)).execute()
                    if getattr(exec_resp, "error", None):
                        raise RuntimeError(exec_resp.error)
                except Exception as exec_error:
                    error_text = str(exec_error)
                    if "operation_index" in error_text:
                        self._execution_logging_enabled = False
                    self.logger.warning(
                        "Failed to persist proposal execution summary for proposal %s: %s",
                        proposal_id,
                        exec_error
                    )
            
            self.logger.info(f"Completed execution of proposal {proposal_id}: {len(executed_operations)} operations")

            return {
                "executed_operations": executed_operations,
                "created_substrate_ids": created_substrate_ids
            }

        except Exception as e:
            self.logger.error(f"Failed to execute proposal operations: {e}")
            raise

    async def _check_semantic_duplicate(
        self,
        basket_id: str,
        title: str,
        content: str,
        semantic_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        V3.1: Check for semantic duplicates before creating a new block.

        Uses semantic search to find similar existing blocks and determines if
        the new block is a high-confidence duplicate.

        Args:
            basket_id: Basket to search within
            title: Block title
            content: Block content
            semantic_type: Block semantic type

        Returns:
            {
                'is_duplicate': bool,  # True if similarity > 0.85
                'similarity': float,
                'existing_block_id': str,
                'similar_blocks': List[Dict]  # All similar blocks found
            }
            or None if no similar blocks found or error occurs
        """
        try:
            # Combine title + content for richer semantic matching
            query_text = f"{title} {content}".strip()

            if not query_text:
                return None

            fingerprint = hashlib.sha256(query_text.lower().encode("utf-8")).hexdigest()

            # Search for semantically similar blocks
            similar_blocks = await semantic_search(
                supabase=supabase,
                basket_id=basket_id,
                query_text=query_text,
                filters=SemanticSearchFilters(
                    semantic_types=[semantic_type],  # Same semantic type only
                    states=['ACCEPTED', 'LOCKED', 'CONSTANT'],
                    min_similarity=DUPLICATE_MEDIUM_CONFIDENCE  # 0.70
                ),
                limit=5
            )

            # Fallback to hash-based detection if vectors unavailable
            if not similar_blocks:
                hash_resp = (
                    supabase.table("blocks")
                    .select("id, title")
                    .eq("basket_id", basket_id)
                    .eq("state", "ACCEPTED")
                    .eq("metadata->>content_hash", fingerprint)
                    .limit(1)
                    .execute()
                )
                if hash_resp.data:
                    match_id = hash_resp.data[0].get("id") if isinstance(hash_resp.data, list) else hash_resp.data.get("id")
                    return {
                        'is_duplicate': True,
                        'similarity': 1.0,
                        'existing_block_id': match_id,
                        'similar_blocks': []
                    }
                return None

            # Get highest similarity match
            top_match = similar_blocks[0]

            # High confidence duplicate (>0.85)
            is_duplicate = top_match.similarity_score >= DUPLICATE_HIGH_CONFIDENCE

            result = {
                'is_duplicate': is_duplicate,
                'similarity': top_match.similarity_score,
                'existing_block_id': top_match.id,
                'similar_blocks': [
                    {
                        'id': block.id,
                        'similarity': block.similarity_score,
                        'title': block.content[:100]  # Preview
                    }
                    for block in similar_blocks
                ]
            }

            if is_duplicate:
                self.logger.info(
                    f"V3.1 Duplicate detection: similarity={top_match.similarity_score:.2f}, "
                    f"existing_block={top_match.id}"
                )
            elif top_match.similarity_score >= DUPLICATE_MEDIUM_CONFIDENCE:
                self.logger.debug(
                    f"V3.1 Similar block found (not duplicate): similarity={top_match.similarity_score:.2f}, "
                    f"existing_block={top_match.id}"
                )

            return result

        except Exception as exc:
            # Non-blocking: log error and return None (allow block creation)
            self.logger.warning(f"V3.1 Semantic duplicate check failed: {exc}")
            return None

    async def _log_extraction_metrics(
        self,
        dump_id: UUID,
        basket_id: UUID,
        workspace_id: UUID,
        agent_version: str,
        extraction_method: str,
        blocks_created: int,
        context_items_created: int,  # V3.0: Kept for DB compatibility, always 0
        avg_confidence: float,
        processing_time_ms: int
    ):
        """
        V3.0: Log extraction quality metrics for continuous monitoring

        Note: context_items_created parameter kept for DB function compatibility
        but will always be 0 in v3.0 (all substrate is blocks).
        """
        try:
            result = supabase.rpc(
                'log_extraction_metrics',
                {
                    'p_dump_id': str(dump_id),
                    'p_basket_id': str(basket_id),
                    'p_workspace_id': str(workspace_id),
                    'p_agent_version': agent_version,
                    # 'p_extraction_method': extraction_method,  # Removed - DB function doesn't have this param
                    'p_blocks_created': blocks_created,
                    'p_context_items_created': 0,  # V3.0: Always 0 (legacy field)
                    'p_avg_confidence': avg_confidence,
                    'p_processing_time_ms': processing_time_ms
                }
            ).execute()
            self.logger.info(f"Logged extraction metrics for dump {dump_id}")
        except Exception as e:
            self.logger.warning(f"Failed to log extraction metrics: {e}")

    def get_agent_info(self) -> Dict[str, str]:
        """Get processor information."""
        return {
            "name": "GovernanceDumpProcessorV2_ContextAware",
            "pipeline": "P1_GOVERNANCE_V2_CONTEXT_AWARE",
            "type": "governance_processor",
            "status": "active",
            "substrate_agent": self.p1_agent.agent_name,
            "extraction_method": "context_aware_structured_ingredients",
            "version": "2.1_context_aware"
        }
