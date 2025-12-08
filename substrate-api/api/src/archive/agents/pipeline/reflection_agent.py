"""
P3 Reflection Agent - YARNNN Canon v2.1 Compliant

Sacred Rule: Read-only computation, optionally cached
Pipeline: P3_REFLECTION

This agent computes derived patterns and insights from existing substrate
without creating new substrate or modifying existing content. Terminal
stage in cascade flow (P4 is on-demand only).
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

from infra.utils.supabase_client import supabase_admin_client as supabase
from infra.substrate.services.llm import get_llm

logger = logging.getLogger("uvicorn.error")


class ReflectionComputationRequest(BaseModel):
    """Request to compute reflections from workspace substrate."""
    workspace_id: UUID
    basket_id: Optional[UUID] = None  # Optional: scope to specific basket
    reflection_types: List[str] = Field(default=["patterns", "insights", "gaps"])
    agent_id: str


class PatternReflection(BaseModel):
    """A pattern derived from substrate analysis."""
    pattern_type: str  # thematic, structural, temporal, quality
    description: str
    evidence_count: int
    confidence: float = Field(ge=0.0, le=1.0)
    substrate_references: List[str]  # IDs of supporting substrate


class InsightReflection(BaseModel):
    """An insight derived from substrate analysis."""
    insight_type: str  # synthesis, contradiction, opportunity, risk
    description: str
    supporting_evidence: List[str]
    confidence: float = Field(ge=0.0, le=1.0)


class GapReflection(BaseModel):
    """A gap identified in substrate coverage."""
    gap_type: str  # missing_context, incomplete_analysis, unanswered_questions
    description: str
    suggested_actions: List[str]
    priority: str  # high, medium, low


class ReflectionResult(BaseModel):
    """Result of reflection computation."""
    workspace_id: UUID
    basket_id: Optional[UUID]
    patterns_found: List[PatternReflection]
    insights_derived: List[InsightReflection]
    gaps_identified: List[GapReflection]
    processing_time_ms: int
    substrate_analyzed: int
    computation_timestamp: str


class P3ReflectionAgent:
    """
    Canonical P3 Reflection pipeline agent.
    
    Sacred Rule: Read-only computation, optionally cached.
    This agent computes derived patterns without modifying substrate.
    """
    
    pipeline = "P3_REFLECTION"
    agent_name = "P3ReflectionAgent"
    
    def __init__(self):
        self.logger = logger
        self.llm = get_llm()
        
    async def compute_reflections(self, request: ReflectionComputationRequest) -> ReflectionResult:
        """
        Compute reflections from existing substrate.
        
        Operations allowed:
        - Pattern recognition across substrates
        - Insight derivation from substrate analysis
        - Gap identification in substrate coverage
        - Reflection caching (optional)
        
        Operations forbidden:
        - Substrate creation (P1 responsibility)
        - Substrate modification (P1 responsibility)
        - Relationship creation (P2 responsibility)
        - Document composition (P4 responsibility)
        """
        start_time = datetime.utcnow()
        
        try:
            # Get all substrate for analysis (P3 read-only operation)
            substrate_data = await self._get_substrate_for_analysis(
                request.workspace_id,
                request.basket_id
            )
            
            if not substrate_data:
                self.logger.info(f"P3 Reflection: No substrate found for analysis")
                return ReflectionResult(
                    workspace_id=request.workspace_id,
                    basket_id=request.basket_id,
                    patterns_found=[],
                    insights_derived=[],
                    gaps_identified=[],
                    processing_time_ms=0,
                    substrate_analyzed=0,
                    computation_timestamp=datetime.utcnow().isoformat()
                )
            
            patterns = []
            insights = []
            gaps = []
            
            # Compute patterns if requested (P3 operation)
            if "patterns" in request.reflection_types:
                patterns = self._compute_patterns(substrate_data)
            
            # Derive insights if requested (P3 operation)
            if "insights" in request.reflection_types:
                insights = self._derive_insights(substrate_data)
            
            # Identify gaps if requested (P3 operation)
            if "gaps" in request.reflection_types:
                gaps = self._identify_gaps(substrate_data)
            
            # Calculate metrics
            processing_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            self.logger.info(
                f"P3 Reflection completed: workspace_id={request.workspace_id}, "
                f"patterns={len(patterns)}, insights={len(insights)}, gaps={len(gaps)}, "
                f"substrate_analyzed={len(substrate_data)}, processing_time_ms={processing_time_ms}"
            )
            
            result = ReflectionResult(
                workspace_id=request.workspace_id,
                basket_id=request.basket_id,
                patterns_found=patterns,
                insights_derived=insights,
                gaps_identified=gaps,
                processing_time_ms=processing_time_ms,
                substrate_analyzed=len(substrate_data),
                computation_timestamp=datetime.utcnow().isoformat()
            )
            
            # Optionally cache reflection results (P3 caching allowed)
            await self._cache_reflections_if_enabled(request, result)

            # NEW: LLM-powered narrative reflection (structured) when enough signal
            try:
                if len(substrate_data) >= 5:  # minimal signal threshold
                    digest = self._build_digest(substrate_data)
                    llm_res = await self.llm.get_json_response(
                        f"""Analyze this knowledge substrate to generate deep, actionable insights.

SUBSTRATE DIGEST:
{digest}

INSTRUCTIONS:
1. Look for PATTERNS: What themes, concepts, or ideas appear repeatedly?
2. Find TENSIONS: What contradictions, trade-offs, or difficult choices emerge?
3. Trace EVOLUTION: How is the thinking changing or developing over time?
4. Identify GAPS: What's missing that could unlock new understanding?
5. Surface CONNECTIONS: What non-obvious relationships exist between elements?
6. Spot TRAJECTORIES: Where is this line of thinking heading?

Generate insights that are:
- SPECIFIC (not generic platitudes)
- ACTIONABLE (suggest concrete next steps)
- REVEALING (surface what the user might not see themselves)
- FORWARD-LOOKING (help anticipate what's coming)

Focus on providing "aha moment" insights that help the user see their own thinking from a new angle.

Return JSON with deep analysis, not surface observations.""",
                        temperature=1.0,  # Use default temperature for model compatibility
                        schema_name="p3_reflection",
                    )
                    summary = None
                    if llm_res.success and llm_res.parsed:
                        summary = llm_res.parsed.get("summary")
                    # Persist artifact via RPC
                    try:
                        payload_text = summary or "Automated reflection computed from recent substrate."
                        resp = supabase.rpc(
                            'fn_reflection_create_from_substrate',
                            {
                                'p_basket_id': str(request.basket_id) if request.basket_id else self._infer_any_basket(substrate_data),
                                'p_reflection_text': payload_text,
                            }
                        ).execute()
                        # Update meta with structured JSON (post-insert update)
                        if resp.data:
                            ref_id = resp.data
                            supabase.table('reflections_artifact').update({
                                'meta': {
                                    'engine': 'p3_llm',
                                    'structured': llm_res.parsed or {},
                                    'substrate_analyzed': len(substrate_data)
                                }
                            }).eq('id', ref_id).execute()
                    except Exception as ie:
                        self.logger.warning(f"Failed to persist LLM reflection: {ie}")
            except Exception as le:
                self.logger.warning(f"LLM reflection generation failed (non-critical): {le}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"P3 Reflection failed for workspace {request.workspace_id}: {e}")
            raise
    
    async def _get_substrate_for_analysis(
        self, 
        workspace_id: UUID, 
        basket_id: Optional[UUID]
    ) -> List[Dict[str, Any]]:
        """Get all substrate elements for read-only analysis."""
        try:
            substrate_data = []
            
            # Build query filters
            workspace_filter = str(workspace_id)
            basket_filter = str(basket_id) if basket_id else None
            basket_ids = None  # Initialize basket_ids
            
            # Get blocks - Canon: use canonical fields only
            blocks_query = supabase.table("blocks").select(
                "id,basket_id,title,content,semantic_type,state,confidence_score,created_at,updated_at"
            )
            
            if basket_filter:
                blocks_query = blocks_query.eq("basket_id", basket_filter)
            else:
                # Get all blocks in workspace
                baskets_response = supabase.table("baskets").select("id").eq("workspace_id", workspace_filter).execute()
                if baskets_response.data and len(baskets_response.data) > 0:
                    basket_ids = [b["id"] for b in baskets_response.data if b and "id" in b]
                    if basket_ids:
                        blocks_query = blocks_query.in_("basket_id", basket_ids)
                    else:
                        # No valid basket IDs found
                        return substrate_data
            
            blocks_response = blocks_query.execute()
            
            if blocks_response.data and len(blocks_response.data) > 0:
                for block in blocks_response.data:
                    if block and isinstance(block, dict) and "id" in block:
                        substrate_data.append({
                            "id": block["id"],
                            "type": "block", 
                            "basket_id": block.get("basket_id"),
                            "title": block.get("title", ""),
                            "content": block.get("content", ""),  # Canon: use canonical content field
                            "semantic_type": block.get("semantic_type", "concept"),
                            "status": block.get("state", "PROPOSED"),  # Canon: use state field
                            "confidence": block.get("confidence_score", 0.5),
                            "created_at": block.get("created_at"),
                            "updated_at": block.get("updated_at")
                        })
            
            # V3.0: No context_items table - entities are blocks with semantic_type='entity'
            # Entity blocks already included in blocks query above

            # Canon v3.1: Relationships removed - pattern analysis uses blocks only
            
            return substrate_data
            
        except Exception as e:
            self.logger.error(f"Failed to get substrate for analysis: {e}")
            return []
    
    def _compute_patterns(self, substrate_data: List[Dict[str, Any]]) -> List[PatternReflection]:
        """Compute patterns from substrate data through read-only analysis."""
        patterns = []

        # V3.0: Filter blocks (all substrate) for pattern analysis
        blocks = [item for item in substrate_data if item["type"] == "block"]
        # Canon v3.1: Relationships removed

        # Thematic patterns (V3.0: only blocks, no separate context_items)
        thematic_patterns = self._analyze_thematic_patterns(blocks)
        patterns.extend(thematic_patterns)

        # Structural patterns (v3.1: no relationships)
        structural_patterns = self._analyze_structural_patterns(blocks)
        patterns.extend(structural_patterns)
        
        # Quality patterns
        quality_patterns = self._analyze_quality_patterns(blocks)
        patterns.extend(quality_patterns)
        
        # Temporal patterns
        temporal_patterns = self._analyze_temporal_patterns(substrate_data)
        patterns.extend(temporal_patterns)
        
        return patterns
    
    def _derive_insights(self, substrate_data: List[Dict[str, Any]]) -> List[InsightReflection]:
        """Derive insights from substrate analysis."""
        insights = []
        
        blocks = [item for item in substrate_data if item["type"] == "block"]
        
        # Synthesis insights
        synthesis_insights = self._identify_synthesis_opportunities(blocks)
        insights.extend(synthesis_insights)
        
        # Contradiction insights
        contradiction_insights = self._identify_contradictions(blocks)
        insights.extend(contradiction_insights)
        
        # Opportunity insights
        opportunity_insights = self._identify_opportunities(blocks)
        insights.extend(opportunity_insights)
        
        return insights
    
    def _identify_gaps(self, substrate_data: List[Dict[str, Any]]) -> List[GapReflection]:
        """Identify gaps in substrate coverage."""
        gaps = []
        
        blocks = [item for item in substrate_data if item["type"] == "block"]

        # V3.0: Missing context gaps (blocks only, no separate context_items)
        context_gaps = self._identify_missing_context(blocks)
        gaps.extend(context_gaps)
        
        # Incomplete analysis gaps
        analysis_gaps = self._identify_incomplete_analysis(blocks)
        gaps.extend(analysis_gaps)
        
        # V3.0: Unanswered questions gaps (blocks only)
        question_gaps = self._identify_unanswered_questions(blocks)
        gaps.extend(question_gaps)
        
        return gaps
    
    def _analyze_thematic_patterns(self, blocks: List[Dict[str, Any]]) -> List[PatternReflection]:
        """V3.0: Analyze thematic patterns from unified blocks."""
        """Analyze thematic patterns across substrate."""
        patterns = []
        
        # Group by semantic type
        semantic_groups = {}
        for block in blocks:
            semantic_type = block.get("semantic_type", "concept")
            if semantic_type not in semantic_groups:
                semantic_groups[semantic_type] = []
            semantic_groups[semantic_type].append(block)
        
        # Find dominant themes
        for semantic_type, group_blocks in semantic_groups.items():
            if len(group_blocks) >= 3:  # Pattern threshold
                patterns.append(PatternReflection(
                    pattern_type="thematic",
                    description=f"Strong {semantic_type} theme with {len(group_blocks)} instances",
                    evidence_count=len(group_blocks),
                    confidence=min(0.9, 0.5 + (len(group_blocks) * 0.1)),
                    substrate_references=[block["id"] for block in group_blocks]
                ))
        
        return patterns
    
    def _analyze_structural_patterns(self, blocks: List[Dict[str, Any]]) -> List[PatternReflection]:
        """Analyze structural patterns in substrate organization (Canon v3.1: blocks only)."""
        patterns = []

        # Canon v3.1: Relationships removed - analyze blocks structure instead
        # Could analyze semantic_type clustering, anchor_role patterns, etc.
        # For now, return empty (relationships-based patterns removed)

        return patterns
    
    def _analyze_quality_patterns(self, blocks: List[Dict[str, Any]]) -> List[PatternReflection]:
        """Analyze quality patterns in substrate."""
        patterns = []
        
        if blocks:
            # Calculate average confidence
            avg_confidence = sum(block.get("confidence", 0.5) for block in blocks) / len(blocks)
            
            if avg_confidence >= 0.7:
                patterns.append(PatternReflection(
                    pattern_type="quality",
                    description=f"High confidence substrate with average score {avg_confidence:.2f}",
                    evidence_count=len(blocks),
                    confidence=avg_confidence,
                    substrate_references=[block["id"] for block in blocks if block.get("confidence", 0.5) >= 0.7]
                ))
            elif avg_confidence <= 0.4:
                patterns.append(PatternReflection(
                    pattern_type="quality",
                    description=f"Low confidence substrate requiring review (average: {avg_confidence:.2f})",
                    evidence_count=len(blocks),
                    confidence=0.8,  # High confidence in identifying low quality
                    substrate_references=[block["id"] for block in blocks if block.get("confidence", 0.5) <= 0.4]
                ))
        
        return patterns
    
    def _analyze_temporal_patterns(self, substrate_data: List[Dict[str, Any]]) -> List[PatternReflection]:
        """Analyze temporal patterns in substrate creation."""
        patterns = []
        
        # Filter items with creation timestamps
        timestamped_items = [item for item in substrate_data if item.get("created_at")]
        
        if len(timestamped_items) >= 5:
            patterns.append(PatternReflection(
                pattern_type="temporal",
                description=f"Consistent substrate creation with {len(timestamped_items)} timestamped items",
                evidence_count=len(timestamped_items),
                confidence=0.7,
                substrate_references=[item["id"] for item in timestamped_items]
            ))
        
        return patterns
    
    def _identify_synthesis_opportunities(self, blocks: List[Dict[str, Any]]) -> List[InsightReflection]:
        """Identify synthesis opportunities from blocks."""
        insights = []
        
        # Group related blocks
        goal_blocks = [b for b in blocks if b.get("semantic_type") == "goal"]
        solution_blocks = [b for b in blocks if b.get("semantic_type") == "solution"]
        
        if goal_blocks and solution_blocks:
            insights.append(InsightReflection(
                insight_type="synthesis",
                description=f"Opportunity to synthesize {len(goal_blocks)} goals with {len(solution_blocks)} solutions",
                supporting_evidence=[b["id"] for b in goal_blocks + solution_blocks],
                confidence=0.8
            ))
        
        return insights
    
    def _identify_contradictions(self, blocks: List[Dict[str, Any]]) -> List[InsightReflection]:
        """Identify potential contradictions in blocks."""
        insights = []
        
        # Simple heuristic: look for opposing keywords
        opposing_pairs = [
            ("increase", "decrease"), ("add", "remove"), ("expand", "reduce"),
            ("more", "less"), ("high", "low")
        ]
        
        contradiction_blocks = []
        for i, block1 in enumerate(blocks):
            for block2 in blocks[i+1:]:
                content1 = block1.get("content", "").lower()
                content2 = block2.get("content", "").lower()
                
                for word1, word2 in opposing_pairs:
                    if word1 in content1 and word2 in content2:
                        contradiction_blocks.extend([block1["id"], block2["id"]])
                        break
        
        if contradiction_blocks:
            insights.append(InsightReflection(
                insight_type="contradiction",
                description=f"Potential contradictions found across {len(set(contradiction_blocks))} blocks",
                supporting_evidence=list(set(contradiction_blocks)),
                confidence=0.6
            ))
        
        return insights
    
    def _identify_opportunities(self, blocks: List[Dict[str, Any]]) -> List[InsightReflection]:
        """Identify opportunity insights from blocks."""
        insights = []
        
        # Look for opportunity keywords
        opportunity_keywords = ["opportunity", "potential", "could", "might", "possible", "consider"]
        opportunity_blocks = []
        
        for block in blocks:
            content = block.get("content", "").lower()
            if any(keyword in content for keyword in opportunity_keywords):
                opportunity_blocks.append(block["id"])
        
        if opportunity_blocks:
            insights.append(InsightReflection(
                insight_type="opportunity",
                description=f"Opportunity signals found in {len(opportunity_blocks)} blocks",
                supporting_evidence=opportunity_blocks,
                confidence=0.7
            ))
        
        return insights
    
    def _identify_missing_context(self, blocks: List[Dict[str, Any]]) -> List[GapReflection]:
        """V3.0: Identify missing context gaps from unified blocks."""
        gaps = []

        # V3.0: Count entity blocks (structural type)
        entity_blocks = [b for b in blocks if b.get('semantic_type') == 'entity']

        # Simple heuristic: if we have many knowledge blocks but few entities
        knowledge_blocks = [b for b in blocks if b.get('semantic_type') in [
            'fact', 'metric', 'event', 'insight', 'action', 'finding', 'quote', 'summary'
        ]]

        if len(knowledge_blocks) >= 5 and len(entity_blocks) < 3:
            gaps.append(GapReflection(
                gap_type="missing_context",
                description=f"Rich knowledge substrate ({len(knowledge_blocks)} blocks) with limited entities ({len(entity_blocks)} blocks)",
                suggested_actions=[
                    "Add more entity blocks to enrich understanding",
                    "Tag existing blocks with relevant themes",
                    "Identify key stakeholders and entities"
                ],
                priority="medium"
            ))
        
        return gaps
    
    def _identify_incomplete_analysis(self, blocks: List[Dict[str, Any]]) -> List[GapReflection]:
        """Identify incomplete analysis gaps."""
        gaps = []
        
        # Look for low-confidence blocks
        low_confidence_blocks = [b for b in blocks if b.get("confidence", 0.5) < 0.5]
        
        if len(low_confidence_blocks) >= 3:
            gaps.append(GapReflection(
                gap_type="incomplete_analysis",
                description=f"{len(low_confidence_blocks)} blocks have low confidence scores",
                suggested_actions=[
                    "Review and refine low-confidence blocks",
                    "Add more supporting evidence",
                    "Consider merging or restructuring weak blocks"
                ],
                priority="high"
            ))
        
        return gaps
    
    def _identify_unanswered_questions(self, blocks: List[Dict[str, Any]]) -> List[GapReflection]:
        """V3.0: Identify unanswered questions gaps from unified blocks."""
        gaps = []

        # V3.0: Look for question-type blocks (all blocks unified)
        question_blocks = [b for b in blocks if b.get("semantic_type") == "question" or "?" in b.get("content", "")]

        total_questions = len(question_blocks)
        
        if total_questions >= 2:
            gaps.append(GapReflection(
                gap_type="unanswered_questions",
                description=f"{total_questions} questions identified that may need investigation",
                suggested_actions=[
                    "Prioritize answering key questions",
                    "Research solutions for open questions",
                    "Consider expert consultation for complex questions"
                ],
                priority="medium"
            ))
        
        return gaps
    
    async def _cache_reflections_if_enabled(
        self, 
        request: ReflectionComputationRequest, 
        result: ReflectionResult
    ) -> None:
        """Optionally cache reflection results (P3 caching allowed)."""
        try:
            # Simple caching approach - store in reflections table if exists
            cache_data = {
                "workspace_id": str(request.workspace_id),
                "basket_id": str(request.basket_id) if request.basket_id else None,
                "reflection_type": "computed_analysis",
                "content": {
                    "patterns_count": len(result.patterns_found),
                    "insights_count": len(result.insights_derived),
                    "gaps_count": len(result.gaps_identified),
                    "computation_time_ms": result.processing_time_ms,
                    "substrate_analyzed": result.substrate_analyzed
                },
                "metadata": {
                    "generated_by": self.agent_name,
                    "pipeline": self.pipeline,
                    "computation_timestamp": result.computation_timestamp,
                    "agent_id": request.agent_id
                }
            }
            
            # Try to cache (optional - don't fail if caching fails)
            # Store lightweight artifact meta (optional)
            if request.basket_id:
                supabase.table('reflections_artifact').insert({
                    'basket_id': str(request.basket_id),
                    'workspace_id': str(request.workspace_id),
                    'reflection_text': 'Automated analysis available (patterns/insights/gaps).',
                    'reflection_target_type': 'substrate',
                    'meta': {
                        'generated_by': self.agent_name,
                        'pipeline': self.pipeline,
                        'computation_timestamp': result.computation_timestamp,
                        'patterns_count': len(result.patterns_found),
                        'insights_count': len(result.insights_derived),
                        'gaps_count': len(result.gaps_identified),
                        'agent_id': request.agent_id
                    }
                }).execute()
            
        except Exception as e:
            # Caching failure is non-critical for P3 operations
            self.logger.warning(f"Reflection caching failed (non-critical): {e}")
    
    def get_agent_info(self) -> Dict[str, str]:
        """Get agent information."""
        return {
            "name": self.agent_name,
            "pipeline": self.pipeline,
            "type": "reflection",
            "status": "active",
            "sacred_rule": "Read-only computation, optionally cached",
            "canon_compliance": "fully_compliant",
            "improvements": "canonical_field_usage,semantic_meaning_processing,enhanced_context_analysis"
        }

    def _build_digest(self, substrate_data: List[Dict[str, Any]]) -> str:
        """V3.0: Build a compact digest from substrate data for LLM input (size-capped)."""
        lines: List[str] = []
        for item in substrate_data[:50]:  # cap
            t = item.get('type')
            if t == 'block':
                title = (item.get('title') or '')[:80]
                content = (item.get('content') or '')[:200]
                st = item.get('semantic_type')
                anchor = item.get('anchor_role', '')
                anchor_text = f"[{anchor}]" if anchor else ""
                lines.append(f"BLOCK[{st}]{anchor_text}: {title}\n{content}")
            # Canon v3.1: Relationships removed
        return '\n\n'.join(lines)

    def _infer_any_basket(self, substrate_data: List[Dict[str, Any]]) -> str:
        for it in substrate_data:
            if it.get('basket_id'):
                return str(it['basket_id'])
        return ''
