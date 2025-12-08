"""
P4 Composition Agent - YARNNN Canon v3.1 Compliant

Implements intelligent document composition from substrate memory.
Sacred Principle #3: "Narrative is Deliberate" - Documents compose substrate references + authored prose.

This agent:
1. Analyzes intent to understand document purpose
2. Queries substrate comprehensively from unified blocks table
3. Scores relevance based on semantic similarity and recency
4. Generates thoughtful narrative structure
5. Composes document with clear reasoning

V3.1 Changes:
- Relationships removed (replaced by Neural Map)
- Composition uses blocks only (unified substrate)
- All substrate types: knowledge, meaning, structural (entity)
- Emergent anchors for semantic organization
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from uuid import UUID
import math

from infra.utils.supabase_client import supabase_admin_client as supabase
from infra.substrate.services.llm import get_llm
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass 
class AgentResponse:
    """Standard agent response format"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None

@dataclass
class RetrievalBudget:
    """
    V3.0: Phase 1: Retrieval budget configuration

    All substrate is now blocks (no context_items).
    Increased block budget since entities are now blocks.
    """
    total_budget: int = 120
    type_weights: Dict[str, float] = None
    per_type_caps: Dict[str, int] = None
    recency_days: int = 90
    mmr_lambda: float = 0.7  # Diversity vs relevance balance

    def __post_init__(self):
        if self.type_weights is None:
            # Canon v3.1: Only blocks (relationships removed)
            self.type_weights = {"blocks": 1.0, "dumps": 0.00}
        if self.per_type_caps is None:
            # Canon v3.1: Increased block cap (includes entities, no relationships)
            self.per_type_caps = {"blocks": 120, "dumps": 0}

@dataclass
class CompositionMetrics:
    """Phase 1: Metrics for composition analysis"""
    start_time: datetime
    end_time: Optional[datetime] = None
    candidates_found: Dict[str, int] = None
    candidates_selected: Dict[str, int] = None
    provenance_percentage: float = 0.0
    freshness_score: float = 0.0
    raw_gaps_used: bool = False
    coverage_percentage: float = 0.0
    tokens_used: int = 0
    
    def __post_init__(self):
        if self.candidates_found is None:
            self.candidates_found = {}
        if self.candidates_selected is None:
            self.candidates_selected = {}

logger = logging.getLogger("uvicorn.error")


class CompositionRequest:
    """Request for P4 document composition"""
    def __init__(
        self,
        document_id: str,
        basket_id: str,
        workspace_id: str,
        intent: str,
        window: Optional[Dict[str, Any]] = None,
        pinned_ids: Optional[List[str]] = None
    ):
        self.document_id = document_id
        self.basket_id = basket_id
        self.workspace_id = workspace_id
        self.intent = intent
        self.window = window or {}
        self.pinned_ids = pinned_ids or []


class P4CompositionAgent:
    """
    V3.0: P4 Composition Agent - Thoughtful document composition from substrate

    Canon Compliance:
    - P4 consumes substrate, never creates it
    - V3.0: Unified blocks (knowledge, meaning, structural types)
    - Creates document artifacts with clear reasoning
    - Emits proper timeline events
    """
    
    def __init__(self):
        self.llm = get_llm()
        logger.info("P4 Composition Agent initialized")
    
    async def process(self, request: CompositionRequest) -> AgentResponse:
        """
        Process document composition request with intelligent substrate selection
        """
        logger.info(f"P4 Composition: Processing document {request.document_id} with intent: {request.intent}")
        
        try:
            # Phase 1: Analyze intent and determine composition strategy
            strategy = await self._analyze_intent(request)
            
            # Phase 2: Query substrate with budgets and metrics
            substrate_candidates, query_metrics = await self._query_substrate(request, strategy)
            
            # Phase 3: Score and select substrate with MMR diversity
            selected_substrate, query_metrics = await self._score_and_select(substrate_candidates, request, strategy, query_metrics)
            
            # Phase 4: Generate narrative structure
            narrative = await self._generate_narrative(selected_substrate, request, strategy)
            if narrative is None:
                return AgentResponse(
                    success=False,
                    message="Failed to generate narrative structure"
                )
            
            # Phase 5: Compose document
            composition_result = await self._compose_document(
                request.document_id,
                selected_substrate,
                narrative,
                request.workspace_id,
                query_metrics
            )
            
            return AgentResponse(
                success=True,
                message="Document composed successfully",
                data={
                    "document_id": str(request.document_id),
                    "substrate_count": len(selected_substrate),
                    "composition_summary": composition_result.get("summary"),
                    "confidence": strategy.get("confidence", 0.8),
                    "phase1_metrics": composition_result.get("phase1_metrics", {}),
                    "processing_time_ms": composition_result.get("phase1_metrics", {}).get("processing_time_ms", 0),
                    "version_hash": composition_result.get("version_hash"),
                    "timeline_emitted": composition_result.get("timeline_emitted", False),
                    "substrate_references_created": composition_result.get("substrate_references_created", 0)
                }
            )
            
        except Exception as e:
            logger.exception(f"P4 Composition failed for document {request.document_id}: {e}")
            
            # Update document with failure status
            await self._mark_composition_failed(request.document_id, str(e))
            
            return AgentResponse(
                success=False,
                message=f"Composition failed: {str(e)}",
                data={"document_id": request.document_id}
            )
    
    async def _analyze_intent(self, request: CompositionRequest) -> Dict[str, Any]:
        """
        Analyze user intent to determine composition strategy
        """
        prompt = f"""Analyze this document composition intent and provide a strategy.

Intent: {request.intent}
Basket Context: Document being composed from memory in basket {request.basket_id}

Provide a JSON strategy with:
1. document_type: The type of document (e.g., "summary", "analysis", "plan", "reflection", "report")
2. key_themes: List of 3-5 key themes or topics to focus on
3. substrate_priorities: What types of substrate to prioritize (Canon v3.1: blocks only)
   - blocks: true/false (knowledge, meaning, entities - unified substrate)
   - dumps: true/false (raw memories)
4. organization: How to organize the document ("chronological", "thematic", "priority", "categorical")
5. tone: The appropriate tone ("analytical", "narrative", "instructional", "reflective")
6. confidence: 0.0-1.0 confidence in understanding the intent
7. original_intent: The user's original intent (exactly as provided)

Example response:
{{
  "document_type": "analysis",
  "key_themes": ["project planning", "technical architecture", "team coordination"],
  "substrate_priorities": {{
    "blocks": true,
    "dumps": false
  }},
  "organization": "thematic",
  "tone": "analytical",
  "confidence": 0.85,
  "original_intent": "Create comprehensive project timeline"
}}"""

        response = await self.llm.get_json_response(
            prompt,
            temperature=1.0,  # Use default temperature for model compatibility
            schema_name="p4_intent_strategy",
        )
        
        strategy = response.parsed
        if strategy is None:
            logger.error("P4 Intent Analysis failed: No strategy parsed from LLM response")
            raise ValueError("Intent analysis failed - could not parse strategy from LLM response")
        
        logger.info(f"P4 Composition strategy: {strategy}")
        return strategy
    
    async def _query_substrate(self, request: CompositionRequest, strategy: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], CompositionMetrics]:
        """
        Phase 1: Query substrate with budgets, caps, and recency filtering
        """
        metrics = CompositionMetrics(start_time=datetime.utcnow())
        budget = RetrievalBudget()
        candidates = []
        
        # Calculate recency cutoff (90 days by default)
        recency_cutoff = datetime.utcnow() - timedelta(days=budget.recency_days)
        
        logger.info(f"P4 Phase 1: Applying retrieval budget - total={budget.total_budget}, recency_days={budget.recency_days}")
        
        # Query blocks with budget and recency constraints
        if strategy["substrate_priorities"].get("blocks", True) and budget.per_type_caps["blocks"] > 0:
            blocks_query = supabase.table("blocks").select("*").eq("basket_id", request.basket_id)
            
            # Apply recency filter (Phase 1 improvement)
            blocks_query = blocks_query.gte("created_at", recency_cutoff.isoformat())
            
            # Apply window filter if specified
            if request.window.get("start_date"):
                blocks_query = blocks_query.gte("created_at", request.window["start_date"])
            if request.window.get("end_date"):
                blocks_query = blocks_query.lte("created_at", request.window["end_date"])
            
            # Exclude rejected blocks and apply cap
            blocks_query = blocks_query.neq("state", "REJECTED").limit(budget.per_type_caps["blocks"])
            
            blocks_response = blocks_query.execute()
            metrics.candidates_found["blocks"] = len(blocks_response.data or [])
        else:
            blocks_response = type("Response", (), {"data": []})()
            
        for block in blocks_response.data or []:
            candidates.append({
                "type": "block",
                "id": block["id"],
                "content": block.get("content", ""),
                "title": block.get("title", ""),
                "semantic_type": block.get("semantic_type"),
                "confidence_score": block.get("confidence_score", 0.7),
                "created_at": block["created_at"],
                "metadata": block,
                "freshness_score": self._calculate_freshness(block["created_at"], recency_cutoff)
            })
        
        # V3.0: No context_items table - entities are blocks with semantic_type='entity'
        # Entity blocks already included in blocks query above
        
        # Phase 1: Raw dumps only for gaps-only policy (controlled by feature flag)
        use_raw_gaps = os.getenv("USE_RAW_GAPS_ONLY", "false").lower() == "true"
        if strategy["substrate_priorities"].get("dumps", False) and not use_raw_gaps:
            # Legacy behavior: include raw dumps if strategy requests them
            dumps_query = supabase.table("raw_dumps").select("*").eq("basket_id", request.basket_id)
            
            # Apply recency filter
            dumps_query = dumps_query.gte("created_at", recency_cutoff.isoformat())
            
            if request.window.get("start_date"):
                dumps_query = dumps_query.gte("created_at", request.window["start_date"])
            if request.window.get("end_date"):
                dumps_query = dumps_query.lte("created_at", request.window["end_date"])
            
            # Apply cap (much lower for raw dumps)
            dumps_response = dumps_query.limit(min(20, budget.per_type_caps.get("dumps", 0))).execute()
            metrics.candidates_found["dumps"] = len(dumps_response.data or [])
            
            for dump in dumps_response.data or []:
                candidates.append({
                    "type": "dump",
                    "id": dump["id"],
                    "content": dump.get("body_md", "") or dump.get("text_dump", ""),  # Use available content
                    "title": f"Memory from {dump.get('created_at', '')[:10]}",  # Generate descriptive title
                    "created_at": dump["created_at"],
                    "metadata": dump,
                    "freshness_score": self._calculate_freshness(dump["created_at"], recency_cutoff)
                })
        
        # Canon v3.1: Relationships removed - composition uses blocks only
        
        # Add pinned items if specified
        if request.pinned_ids:
            # TODO: Query pinned items across all substrate types
            pass
        
        # Calculate overall metrics
        total_found = sum(metrics.candidates_found.values())
        metrics.end_time = datetime.utcnow()
        
        logger.info(f"P4 Phase 1: Found {total_found} substrate candidates with budget constraints: {dict(metrics.candidates_found)}")
        return candidates, metrics
    
    async def _score_and_select(
        self,
        candidates: List[Dict[str, Any]],
        request: CompositionRequest,
        strategy: Dict[str, Any],
        query_metrics: CompositionMetrics
    ) -> Tuple[List[Dict[str, Any]], CompositionMetrics]:
        """
        Score substrate candidates and select the most relevant
        """
        if not candidates:
            return [], query_metrics
        
        # Prepare candidates for LLM scoring
        def _preview_content(value: Any, limit: int = 500) -> str:
            if value is None:
                return ""
            if isinstance(value, str):
                return value[:limit]
            try:
                return json.dumps(value)[:limit]
            except (TypeError, ValueError):
                return str(value)[:limit]


        def _parse_created_at(raw_value: Any) -> datetime:
            if isinstance(raw_value, datetime):
                return raw_value.astimezone(timezone.utc) if raw_value.tzinfo else raw_value.replace(tzinfo=timezone.utc)
            if isinstance(raw_value, str):
                candidate = raw_value.rstrip("Z")
                try:
                    parsed = datetime.fromisoformat(candidate)
                    return parsed.astimezone(timezone.utc) if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
                except ValueError:
                    pass
            return datetime(1970, 1, 1, tzinfo=timezone.utc)

        def _fallback_selection(reason: str, limit: int = 5) -> List[Dict[str, Any]]:
            logger.warning(
                "P4 Composition: Falling back to heuristic substrate selection (%s)",
                reason,
            )
            scored = sorted(
                candidates,
                key=lambda item: (
                    item.get("confidence_score", 0.0),
                    _parse_created_at(item.get("created_at")),
                ),
                reverse=True,
            )
            fallback = []
            for source in scored[:limit]:
                chosen = source.copy()
                chosen["selection_reason"] = f"fallback: {reason}"
                fallback.append(chosen)
            logger.info("P4 Composition: Selected %d substrate items via fallback", len(fallback))
            return fallback
        metadata_keys = {"semantic_type", "confidence_score", "kind", "relationship_type"}
        candidates_text = "\n\n".join([
            f"[{i}] Type: {c.get('type', 'unknown')}\n"
            f"Content: {_preview_content(c.get('content'))}...\n"
            f"Created: {c.get('created_at', 'unknown')}\n"
            f"Metadata: {json.dumps({k: v for k, v in c.get('metadata', {}).items() if k in metadata_keys})}"
            for i, c in enumerate(candidates[:30])  # Limit to prevent context overflow
        ])
        
        scoring_prompt = f"""Score these substrate candidates for relevance to the document composition.

Document Intent: {request.intent}
Document Type: {strategy['document_type']}
Key Themes: {', '.join(strategy['key_themes'])}

Substrate Candidates:
{candidates_text}

Provide a JSON response with:
1. selected_indices: List of candidate indices to include (aim for 5-15 most relevant)
2. reasoning: Brief explanation of selection criteria
3. groupings: How to group selected substrate (by theme, chronology, etc.)
4. coverage_assessment: Assessment of whether we have enough substrate

Example:
{{
  "selected_indices": [0, 2, 5, 7, 11],
  "reasoning": "Selected blocks that directly address project architecture and planning themes",
  "groupings": {{
    "architecture": [0, 2],
    "planning": [5, 7],
    "insights": [11]
  }},
  "coverage_assessment": "Good coverage of main themes, but lacking recent updates"
}}"""

        response = await self.llm.get_json_response(
            scoring_prompt,
            temperature=1.0,  # Use default temperature for model compatibility
            schema_name="p4_scoring_selection",
        )

        if not response.success or not isinstance(response.parsed, dict):
            fallback_selected = _fallback_selection(response.error or "LLM scoring unavailable")
            # Update metrics for fallback
            for substrate in fallback_selected:
                substrate_type = substrate.get("type", "unknown")
                query_metrics.candidates_selected[substrate_type] = query_metrics.candidates_selected.get(substrate_type, 0) + 1
            query_metrics.coverage_percentage = self._calculate_coverage_percentage(fallback_selected, strategy)
            query_metrics.freshness_score = self._calculate_average_freshness(fallback_selected)
            query_metrics.provenance_percentage = self._calculate_provenance_percentage(fallback_selected)
            return fallback_selected, query_metrics

        selection_result = response.parsed

        # Extract selected substrate
        selected = []
        selected_indices = selection_result.get("selected_indices", [])
        if not isinstance(selected_indices, list):
            fallback_selected = _fallback_selection("Invalid scoring response format")
            # Update metrics for fallback
            for substrate in fallback_selected:
                substrate_type = substrate.get("type", "unknown")
                query_metrics.candidates_selected[substrate_type] = query_metrics.candidates_selected.get(substrate_type, 0) + 1
            query_metrics.coverage_percentage = self._calculate_coverage_percentage(fallback_selected, strategy)
            query_metrics.freshness_score = self._calculate_average_freshness(fallback_selected)
            query_metrics.provenance_percentage = self._calculate_provenance_percentage(fallback_selected)
            return fallback_selected, query_metrics

        for idx in selected_indices:
            if not isinstance(idx, int):
                continue
            if 0 <= idx < len(candidates):
                substrate = candidates[idx].copy()
                # Add selection metadata
                substrate["selection_reason"] = selection_result.get("reasoning", "")
                selected.append(substrate)

        # If no substrate selected, provide explanation
        if not selected and candidates:
            fallback_selected = _fallback_selection("LLM returned no substrate indices")
            # Update metrics for fallback
            for substrate in fallback_selected:
                substrate_type = substrate.get("type", "unknown")
                query_metrics.candidates_selected[substrate_type] = query_metrics.candidates_selected.get(substrate_type, 0) + 1
            query_metrics.coverage_percentage = self._calculate_coverage_percentage(fallback_selected, strategy)
            query_metrics.freshness_score = self._calculate_average_freshness(fallback_selected)
            query_metrics.provenance_percentage = self._calculate_provenance_percentage(fallback_selected)
            return fallback_selected, query_metrics

        # Update metrics with selections
        for substrate in selected:
            substrate_type = substrate.get("type", "unknown")
            if substrate_type not in query_metrics.candidates_selected:
                query_metrics.candidates_selected[substrate_type] = 0
            query_metrics.candidates_selected[substrate_type] += 1
        
        # Calculate coverage and freshness
        query_metrics.coverage_percentage = self._calculate_coverage_percentage(selected, strategy)
        query_metrics.freshness_score = self._calculate_average_freshness(selected)
        query_metrics.provenance_percentage = self._calculate_provenance_percentage(selected)
        
        # Phase 1: Gaps-only raw retrieval if coverage is insufficient
        use_raw_gaps = os.getenv("USE_RAW_GAPS_ONLY", "false").lower() == "true"
        coverage_target = 0.90  # 90% coverage target
        
        if use_raw_gaps and query_metrics.coverage_percentage < coverage_target:
            logger.info(f"P4 Phase 1: Coverage {query_metrics.coverage_percentage:.1%} below target {coverage_target:.1%}, adding gaps-only raw")
            gap_filled_substrate = await self._fill_gaps_with_raw(request, selected, strategy, query_metrics)
            selected = gap_filled_substrate
            query_metrics.raw_gaps_used = True
            
            # Recalculate metrics after gap filling
            query_metrics.coverage_percentage = self._calculate_coverage_percentage(selected, strategy)
        
        logger.info(f"P4 Phase 1: Selected {len(selected)} substrate items with coverage={query_metrics.coverage_percentage:.1%}, freshness={query_metrics.freshness_score:.2f}, gaps_used={query_metrics.raw_gaps_used}")
        return selected, query_metrics
    
    async def _generate_narrative(
        self,
        selected_substrate: List[Dict[str, Any]],
        request: CompositionRequest,
        strategy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate narrative structure for the document
        """
        if not selected_substrate:
            # Handle case with no substrate
            return {
                "sections": [{
                    "title": "Document Status",
                    "content": f"This document was created with the intent: \"{request.intent}\". However, there is insufficient substrate (memory) available in this basket to compose a meaningful document. Consider adding more memories, thoughts, or observations related to this topic.",
                    "order": 0
                }],
                "summary": "Insufficient substrate for composition"
            }
        
        # Canon v3.1: Prepare substrate summary (relationships removed)
        substrate_summary = self._prepare_substrate_summary(selected_substrate)

        narrative_prompt = f"""Generate a narrative structure for this document using INTELLIGENT SYNTHESIS.

Intent: {request.intent}
Document Type: {strategy['document_type']}
Tone: {strategy['tone']}
Organization: {strategy['organization']}

Selected Substrate:
{substrate_summary}

IMPORTANT: Synthesize insights by connecting patterns across substrate blocks.
Focus on thematic coherence, temporal sequences, and how concepts build on each other.

Create a JSON structure with:
1. sections: Array of sections, each with:
   - title: Section title
   - content: Brief description emphasizing patterns and synthesis
   - substrate_refs: List of substrate types to reference
   - order: Section order (0-based)
2. introduction: Opening that sets context and themes
3. summary: One-line summary emphasizing key insights
4. composition_notes: Notes about synthesis approach
5. synthesis_approach: How substrate informs narrative flow

Example:
{{
  "sections": [
    {{
      "title": "Technical Evolution",
      "content": "How technical decisions evolved over time based on substrate patterns",
      "substrate_refs": ["block"],
      "order": 0
    }}
  ],
  "introduction": "This document synthesizes patterns across technical decisions and their outcomes...",
  "summary": "Analysis revealing evolution of architecture choices and system performance",
  "composition_notes": "Organized substrate by semantic type and temporal patterns",
  "synthesis_approach": "Chronological flow with thematic clustering"
}}"""

        response = await self.llm.get_json_response(
            narrative_prompt,
            temperature=1.0,  # Use default temperature for model compatibility
            schema_name="p4_narrative_structure",
        )
        
        narrative = response.parsed
        if narrative is None:
            logger.error(f"P4 Composition: Failed to generate narrative - LLM returned None")
            return None
            
        logger.info(f"P4 Composition: Generated narrative with {len(narrative.get('sections', []))} sections")
        
        return narrative
    
    def _prepare_substrate_summary(self, selected_substrate: List[Dict[str, Any]]) -> str:
        """
        Canon v3.1: Prepare substrate summary for narrative generation.

        Organizes substrate blocks by semantic type for better composition.
        Relationships removed - composition uses blocks only.
        """
        # Separate substrate by type
        blocks = [s for s in selected_substrate if s['type'] == 'block']
        dumps = [s for s in selected_substrate if s['type'] == 'dump']

        # Categorize blocks by semantic_type for better organization
        knowledge_blocks = [b for b in blocks if b.get('semantic_type') in [
            'fact', 'metric', 'event', 'insight', 'action', 'finding', 'quote', 'summary'
        ]]
        meaning_blocks = [b for b in blocks if b.get('semantic_type') in [
            'intent', 'objective', 'rationale', 'principle', 'assumption', 'context', 'constraint'
        ]]
        entity_blocks = [b for b in blocks if b.get('semantic_type') == 'entity']

        # Generate substrate summary
        summary_parts = []

        # Add knowledge blocks
        if knowledge_blocks:
            summary_parts.append("=== KNOWLEDGE BLOCKS ===")
            for block in knowledge_blocks:
                semantic_type = block.get('semantic_type', 'concept')
                anchor = block.get('anchor_role', '')
                anchor_text = f" [{anchor}]" if anchor else ""
                title = block.get('title', block.get('content', '')[:100])
                summary_parts.append(f"[{semantic_type.upper()}]{anchor_text} {title}...")

        # Add meaning blocks
        if meaning_blocks:
            summary_parts.append("\n=== MEANING & INTENT ===")
            for block in meaning_blocks:
                semantic_type = block.get('semantic_type', 'context')
                title = block.get('title', 'Untitled')
                summary_parts.append(f"[{semantic_type.upper()}] {title}")

        # Add entity blocks
        if entity_blocks:
            summary_parts.append("\n=== ENTITIES ===")
            for block in entity_blocks:
                entity_label = block.get('title', 'Unknown Entity')
                content = block.get('content', '')
                summary_parts.append(f"[ENTITY] {entity_label}: {content[:150]}")

        # Add raw dumps if selected
        if dumps:
            summary_parts.append("\n=== RAW MEMORIES ===")
            for dump in dumps[:3]:  # Limit to prevent overwhelming
                summary_parts.append(f"[MEMORY] {dump.get('content', '')[:150]}...")

        return "\n".join(summary_parts)
    
    async def _generate_section_content(
        self,
        section: Dict[str, Any],
        selected_substrate: List[Dict[str, Any]],
        narrative: Dict[str, Any]
    ) -> str:
        """
        Canon v3.1: Generate detailed content for a section using substrate blocks.

        Relationships removed - composition synthesizes insights from blocks only.
        """
        # Get substrate relevant to this section
        relevant_substrate = []
        section_refs = section.get('substrate_refs', [])

        for substrate in selected_substrate:
            if substrate['type'] in section_refs:
                relevant_substrate.append(substrate)

        # If no specific refs, use all substrate
        if not relevant_substrate:
            relevant_substrate = selected_substrate

        # Prepare substrate for content generation
        substrate_context = []
        for sub in relevant_substrate[:8]:  # Limit to prevent context overflow
            sub_info = f"[{sub['type'].upper()}] {sub.get('content', '')[:300]}"
            substrate_context.append(sub_info)

        substrate_text = "\n\n".join(substrate_context)

        # Generate content using synthesis approach
        content_prompt = f"""Generate detailed content for this document section using INTELLIGENT SYNTHESIS.

Section Title: {section['title']}
Section Purpose: {section['content']}
Document Intent: {narrative.get('summary', 'Document composition')}
Synthesis Approach: {narrative.get('synthesis_approach', 'Connect related information')}

Relevant Substrate:
{substrate_text}

CRITICAL: Generate 2-4 paragraphs that:
1. Show HOW concepts connect and influence each other
2. Identify patterns and themes across the information
3. Provide INSIGHTS that emerge from synthesis, not just facts
4. Use transition phrases like "This led to...", "As a result...", "Building on this..."
5. Create narrative coherence across substrate blocks

Write in a {narrative.get('tone', 'analytical')} tone. Focus on synthesis, not summarization."""

        try:
            response = await self.llm.get_text_response(
                content_prompt,
                temperature=1.0,  # Use default temperature for model compatibility
                max_tokens=4000  # Increased to prevent truncation for longer documents
            )
        except Exception as e:
            logger.warning(f"Failed to generate section content: {e}")
            return section.get('content', 'Content generation failed.')

        if not response.success:
            logger.warning(
                "LLM section generation returned unsuccessful response: %s",
                response.error or "unknown error",
            )
            return section.get('content', 'Content generation failed.')

        generated = response.content.strip()
        if not generated:
            return section.get('content', 'Content generation failed.')

        return generated
    
    async def _compose_document(
        self,
        document_id: str,
        selected_substrate: List[Dict[str, Any]],
        narrative: Dict[str, Any],
        workspace_id: str,
        query_metrics: CompositionMetrics
    ) -> Dict[str, Any]:
        """
        Canon v3.1: Compose final document with synthesized content and substrate references.

        Relationships removed - composition uses blocks only.
        """
        try:
            # Load existing document context for metadata merging
            context_response = supabase.table("documents")\
                .select("metadata,basket_id,workspace_id")\
                .eq("id", str(document_id))\
                .maybe_single()\
                .execute()

            if not context_response.data:
                raise RuntimeError(f"Document {document_id} not found for composition")

            document_context = context_response.data
            existing_metadata = document_context.get("metadata", {}) or {}

            # Build document content
            content_parts = []
            
            # Add introduction
            if narrative.get("introduction"):
                content_parts.append(narrative["introduction"])
                content_parts.append("")  # Empty line
            
            # Add composition notes if substrate was limited
            if len(selected_substrate) == 0:
                content_parts.append("*Note: This document has limited content due to insufficient substrate in the basket.*")
                content_parts.append("")
            elif narrative.get("composition_notes"):
                content_parts.append(f"*Composition Notes: {narrative['composition_notes']}*")
                content_parts.append("")
            
            # Get relationship map for metadata
            _, relationship_map = self._prepare_substrate_with_relationships(selected_substrate)
            
            # Generate relationship-aware section content
            for section in narrative.get("sections", []):
                content_parts.append(f"## {section['title']}")
                content_parts.append("")
                
                # Generate detailed content using relationships
                section_content = await self._generate_section_content(
                    section, selected_substrate, narrative
                )
                content_parts.append(section_content)
                content_parts.append("")
            
            # Join content
            final_content = "\n".join(content_parts)
            
            # Update document with composed content (Canon: P4 = Pure Artifact Creation)
            base_metadata = {
                **existing_metadata,
                "composition_status": "completed",
                "composition_completed_at": datetime.now(timezone.utc).isoformat(),
                "composition_summary": narrative.get("summary", ""),
                "composition_substrate_count": len(selected_substrate),
                "composition_narrative": narrative,
                "relationship_map": relationship_map,
                "synthesis_approach": narrative.get("synthesis_approach", "Connected intelligence"),
                "phase1_metrics": {
                    "coverage_percentage": query_metrics.coverage_percentage,
                    "freshness_score": query_metrics.freshness_score,
                    "provenance_percentage": query_metrics.provenance_percentage,
                    "candidates_found": query_metrics.candidates_found,
                    "candidates_selected": query_metrics.candidates_selected,
                    "raw_gaps_used": query_metrics.raw_gaps_used,
                    "processing_time_ms": 0  # filled in after timing recorded
                }
            }

            # Canon v4.0: Update document metadata only (content goes to document_versions via RPC)
            doc_update = {
                "metadata": base_metadata
            }

            update_response = supabase.table("documents")\
                .update(doc_update)\
                .eq("id", str(document_id))\
                .execute()

            api_error = getattr(update_response, "error", None)
            if api_error is not None:
                raise RuntimeError(f"Failed to update document metadata: {api_error}")

            if update_response.data is None:
                raise RuntimeError("Failed to update document metadata: empty response")
            updated_metadata = base_metadata

            # V3.0: Canon-Pure: Create substrate references in dedicated table
            substrate_refs_created = []
            # V3.0: No context_item type (all substrate is blocks)
            allowed_substrate_types = {"block", "dump", "timeline_event"}

            for idx, substrate in enumerate(selected_substrate):
                try:
                    # V3.0: Map substrate type to canonical enum
                    substrate_type_map = {
                        "block": "block",
                        "dump": "dump",
                        "raw_dump": "dump",
                        "timeline_event": "timeline_event"
                    }
                    canonical_type = substrate_type_map.get(substrate["type"], substrate["type"])

                    if canonical_type not in allowed_substrate_types:
                        logger.warning(
                            "Skipping unsupported substrate attachment",
                            extra={
                                "document_id": document_id,
                                "substrate_id": substrate.get("id"),
                                "substrate_type": substrate.get("type"),
                            }
                        )
                        continue

                    # Create substrate reference via type-specific canonical RPC
                    if canonical_type == "block":
                        # Use fn_document_attach_block for blocks
                        snippets = [substrate.get("content", "")[:200]] if substrate.get("content") else []
                        ref_response = supabase.rpc("fn_document_attach_block", {
                            "p_document_id": str(document_id),
                            "p_block_id": str(substrate["id"]),
                            "p_occurrences": 1,
                            "p_snippets": snippets
                        }).execute()
                    else:
                        # Skip non-block substrates for now (no RPC available for dumps/timeline_events)
                        logger.info(f"Skipping substrate attachment for type {canonical_type} (no RPC available)")
                        continue
                    
                    if ref_response.data:
                        substrate_refs_created.append(ref_response.data)
                        logger.info(f"✅ Created substrate reference: {canonical_type}:{substrate['id']}")
                    else:
                        logger.warning(f"Failed to create substrate reference: {canonical_type}:{substrate['id']}")
                        
                except Exception as e:
                    logger.warning(f"Error creating substrate reference for {substrate['type']}:{substrate['id']}: {e}")
            
            logger.info(f"✅ Canon-pure P4 composition: {len(substrate_refs_created)}/{len(selected_substrate)} substrate references created in canonical table")
            
            version_hash = None
            try:
                version_response = supabase.rpc("fn_document_create_version", {
                    "p_document_id": str(document_id),
                    "p_content": final_content,
                    "p_version_message": f"Composed from {len(selected_substrate)} substrate items"
                }).execute()
                if version_response.data is not None:
                    if isinstance(version_response.data, list) and version_response.data:
                        version_hash = version_response.data[0]
                    elif isinstance(version_response.data, str):
                        version_hash = version_response.data
            except Exception as version_error:
                logger.warning(f"Failed to create document version for {document_id}: {version_error}")
            
            timeline_emitted = False
            try:
                supabase.rpc("fn_timeline_emit", {
                    "p_basket_id": document_context["basket_id"],
                    "p_kind": "document.composed",
                    "p_ref_id": str(document_id),
                    "p_preview": f"Document composed: {narrative.get('summary', 'Composition complete')}",
                    "p_payload": json.dumps({
                        "substrate_count": len(selected_substrate),
                        "narrative_sections": len(narrative.get("sections", [])),
                        "composition_type": "intelligent"
                    })
                }).execute()
                timeline_emitted = True
            except Exception as timeline_error:
                logger.warning(f"Timeline event emit failed for {document_id}: {timeline_error}")
            
            # Log final metrics before returning
            query_metrics.end_time = datetime.utcnow()
            query_metrics.tokens_used = len(final_content.split())  # Rough token estimate
            if doc_update["metadata"].get("phase1_metrics"):
                doc_update["metadata"]["phase1_metrics"]["processing_time_ms"] = int((query_metrics.end_time - query_metrics.start_time).total_seconds() * 1000) if query_metrics.end_time else 0
                # Persist updated metrics with timing
                try:
                    supabase.table("documents")\
                        .update({"metadata": {**updated_metadata, "phase1_metrics": doc_update["metadata"]["phase1_metrics"]}})\
                        .eq("id", str(document_id))\
                        .execute()
                except Exception as metric_update_error:
                    logger.warning(f"Failed to persist phase1 metrics timing for {document_id}: {metric_update_error}")
            self._log_composition_metrics(str(document_id), query_metrics)
            
            return {
                "success": True,
                "summary": narrative.get("summary", "Document composed"),
                "substrate_count": len(selected_substrate),
                "substrate_references_created": len(substrate_refs_created),
                "content_length": len(final_content),
                "version_hash": version_hash,
                "timeline_emitted": timeline_emitted,
                "canon_compliance": "substrate_references_in_canonical_table",
                "phase1_metrics": {
                    "coverage_percentage": query_metrics.coverage_percentage,
                    "freshness_score": query_metrics.freshness_score,
                    "provenance_percentage": query_metrics.provenance_percentage,
                    "candidates_found": query_metrics.candidates_found,
                    "candidates_selected": query_metrics.candidates_selected,
                    "processing_time_ms": int((query_metrics.end_time - query_metrics.start_time).total_seconds() * 1000) if query_metrics.end_time else 0,
                    "raw_gaps_used": query_metrics.raw_gaps_used
                }
            }
            
        except Exception as e:
            logger.exception(f"Failed to compose document {document_id}: {e}")
            raise
    
    async def _mark_composition_failed(self, document_id: str, error: str) -> None:
        """
        Mark document composition as failed
        """
        try:
            doc_response = supabase.table("documents")\
                .select("metadata")\
                .eq("id", str(document_id))\
                .maybe_single()\
                .execute()

            existing_metadata = doc_response.data.get("metadata", {}) if doc_response.data else {}
            failure_metadata = {
                **(existing_metadata or {}),
                "composition_status": "failed",
                "composition_error": error,
                "composition_failed_at": datetime.now(timezone.utc).isoformat()
            }

            supabase.table("documents")\
                .update({"metadata": failure_metadata})\
                .eq("id", str(document_id))\
                .execute()

        except Exception as e:
            logger.error(f"Failed to mark composition failed for {document_id}: {e}")
    
    def _calculate_freshness(self, created_at: str, recency_cutoff: datetime) -> float:
        """
        Phase 1: Calculate freshness score (0.0 to 1.0) based on recency
        """
        try:
            if isinstance(created_at, str):
                created_time = datetime.fromisoformat(created_at.rstrip('Z'))
            else:
                created_time = created_at
            
            if created_time.tzinfo is None:
                created_time = created_time.replace(tzinfo=timezone.utc)
            
            # Calculate days since creation
            age_days = (datetime.utcnow().replace(tzinfo=timezone.utc) - created_time).days
            
            # Fresher items get higher scores (exponential decay)
            # Items from today = 1.0, items from 30 days ago ≈ 0.5, items from 90 days ago ≈ 0.1
            freshness = math.exp(-age_days / 30.0)
            return min(1.0, freshness)
            
        except Exception:
            return 0.5  # Default middle score for unparseable dates
    
    def _calculate_coverage_percentage(self, selected_substrate: List[Dict[str, Any]], strategy: Dict[str, Any]) -> float:
        """
        Phase 1: Calculate how well selected substrate covers the intended document types
        """
        if not selected_substrate:
            return 0.0
        
        # Count coverage by substrate type
        type_counts = {}
        for substrate in selected_substrate:
            substrate_type = substrate.get("type", "unknown")
            type_counts[substrate_type] = type_counts.get(substrate_type, 0) + 1
        
        # Assess coverage based on strategy priorities
        priorities = strategy.get("substrate_priorities", {})
        expected_types = [t for t, needed in priorities.items() if needed]
        
        if not expected_types:
            return 1.0  # If no specific types needed, any content is full coverage
        
        covered_types = set(type_counts.keys())
        expected_set = set(expected_types)
        
        # Coverage = intersection / expected
        coverage = len(covered_types.intersection(expected_set)) / len(expected_set)
        return coverage
    
    def _calculate_average_freshness(self, selected_substrate: List[Dict[str, Any]]) -> float:
        """
        Phase 1: Calculate average freshness of selected substrate
        """
        if not selected_substrate:
            return 0.0
        
        freshness_scores = [s.get("freshness_score", 0.5) for s in selected_substrate]
        return sum(freshness_scores) / len(freshness_scores)
    
    def _calculate_provenance_percentage(self, selected_substrate: List[Dict[str, Any]]) -> float:
        """
        Phase 1: Calculate percentage of substrate with clear provenance
        """
        if not selected_substrate:
            return 0.0
        
        # Count substrate with confidence scores or clear metadata
        provenance_count = 0
        for substrate in selected_substrate:
            has_confidence = substrate.get("confidence_score", 0) > 0
            has_metadata = bool(substrate.get("metadata", {}))
            has_selection_reason = bool(substrate.get("selection_reason", ""))
            
            if has_confidence or has_metadata or has_selection_reason:
                provenance_count += 1
        
        return provenance_count / len(selected_substrate)
    
    async def _fill_gaps_with_raw(
        self, 
        request: CompositionRequest, 
        selected_substrate: List[Dict[str, Any]], 
        strategy: Dict[str, Any],
        metrics: CompositionMetrics
    ) -> List[Dict[str, Any]]:
        """
        Phase 1: Fill coverage gaps with raw dumps (gaps-only policy)
        """
        try:
            # Identify what types of content we're missing
            existing_types = set(s.get("type") for s in selected_substrate)
            needed_types = set(k for k, v in strategy.get("substrate_priorities", {}).items() if v)
            missing_types = needed_types - existing_types
            
            if not missing_types:
                logger.info("P4 Phase 1: No content gaps detected, skipping raw retrieval")
                return selected_substrate
            
            # Query raw dumps with strict limits (gaps-only policy)
            recency_cutoff = datetime.utcnow() - timedelta(days=90)
            raw_token_cap = 2000  # Strict token limit for raw content
            max_snippets = 12     # Maximum number of raw snippets
            
            dumps_query = supabase.table("raw_dumps").select("*")\
                .eq("basket_id", request.basket_id)\
                .gte("created_at", recency_cutoff.isoformat())\
                .limit(max_snippets)
            
            # Apply window filter if specified
            if request.window.get("start_date"):
                dumps_query = dumps_query.gte("created_at", request.window["start_date"])
            if request.window.get("end_date"):
                dumps_query = dumps_query.lte("created_at", request.window["end_date"])
            
            dumps_response = dumps_query.execute()
            
            # Process raw dumps with token caps and snapshotting
            gap_filled = selected_substrate.copy()
            total_tokens = 0
            
            for i, dump in enumerate(dumps_response.data or []):
                if total_tokens >= raw_token_cap:
                    break
                
                content = dump.get("body_md", "") or dump.get("text_dump", "")
                content_tokens = len(content.split())  # Rough token estimate
                
                # Apply token cap per snippet
                if total_tokens + content_tokens > raw_token_cap:
                    remaining_tokens = raw_token_cap - total_tokens
                    content_words = content.split()[:remaining_tokens]
                    content = " ".join(content_words) + "... [truncated]"
                    content_tokens = remaining_tokens
                
                gap_filled.append({
                    "type": "dump",
                    "id": dump["id"],
                    "content": content,
                    "title": f"Gap-fill memory from {dump.get('created_at', '')[:10]}",
                    "created_at": dump["created_at"],
                    "metadata": {
                        **dump,
                        "gap_fill_reason": f"Missing types: {', '.join(missing_types)}",
                        "token_count": content_tokens,
                        "truncated": "[truncated]" in content
                    },
                    "freshness_score": self._calculate_freshness(dump["created_at"], recency_cutoff),
                    "selection_reason": f"Gap-fill for missing {', '.join(missing_types)} content"
                })
                
                total_tokens += content_tokens
                
                # Update metrics
                if "dumps" not in metrics.candidates_found:
                    metrics.candidates_found["dumps"] = 0
                metrics.candidates_found["dumps"] += 1
                
                if "dumps" not in metrics.candidates_selected:
                    metrics.candidates_selected["dumps"] = 0
                metrics.candidates_selected["dumps"] += 1
            
            logger.info(f"P4 Phase 1: Added {len(gap_filled) - len(selected_substrate)} raw dumps for gap-filling (tokens: {total_tokens}/{raw_token_cap})")
            return gap_filled
            
        except Exception as e:
            logger.warning(f"Gap-fill with raw dumps failed: {e}")
            return selected_substrate
    
    def _log_composition_metrics(self, document_id: str, metrics: CompositionMetrics) -> None:
        """
        Phase 1: Log composition metrics for analysis
        """
        try:
            metrics_data = {
                "document_id": document_id,
                "processing_time_ms": int((metrics.end_time - metrics.start_time).total_seconds() * 1000) if metrics.end_time else 0,
                "candidates_found": metrics.candidates_found,
                "candidates_selected": metrics.candidates_selected,
                "coverage_percentage": metrics.coverage_percentage,
                "freshness_score": metrics.freshness_score,
                "provenance_percentage": metrics.provenance_percentage,
                "raw_gaps_used": metrics.raw_gaps_used,
                "tokens_estimated": metrics.tokens_used,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Log for analysis (could be sent to analytics system later)
            logger.info(f"P4 Phase 1 Metrics: {json.dumps(metrics_data)}")
            
        except Exception as e:
            logger.warning(f"Failed to log composition metrics: {e}")
