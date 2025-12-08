"""
P4 Presentation Agent - YARNNN Canon v2.1 Compliant

Sacred Rule: Consumes substrate for narrative, never creates substrate
Pipeline: P4_PRESENTATION

This agent composes documents and narratives from existing substrate
without creating new substrate elements. On-demand only (not in cascade).
"""
# V3.0 DEPRECATION NOTICE:
# This file contains references to context_items table which was merged into blocks table.
# Entity blocks are now identified by semantic_type='entity'.
# This file is legacy/supporting code - update if actively maintained.


import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

from infra.utils.supabase_client import supabase_admin_client as supabase

logger = logging.getLogger("uvicorn.error")


class DocumentCompositionRequest(BaseModel):
    """Request to compose document from substrate."""
    workspace_id: UUID
    basket_id: UUID
    document_title: str
    composition_type: str = Field(default="narrative")  # narrative, summary, report
    substrate_references: List[str]  # IDs of substrate to include
    narrative_prompt: Optional[str] = None
    agent_id: str


class SubstrateReference(BaseModel):
    """A reference to substrate in document composition."""
    substrate_id: str
    substrate_type: str  # block, context_item, relationship
    reference_context: str
    relevance_score: float = Field(ge=0.0, le=1.0)


class ComposedDocument(BaseModel):
    """A composed document with narrative and substrate references."""
    title: str
    narrative_content: str
    substrate_references: List[SubstrateReference]
    composition_metadata: Dict[str, Any]


class DocumentResult(BaseModel):
    """Result of document composition."""
    document_id: UUID
    composed_document: ComposedDocument
    processing_time_ms: int
    substrate_consumed: int
    narrative_word_count: int


class P4PresentationAgent:
    """
    Canonical P4 Presentation pipeline agent.
    
    Sacred Rule: Consumes substrate for narrative, never creates substrate.
    This agent composes user-facing documents from existing substrate only.
    """
    
    pipeline = "P4_PRESENTATION"
    agent_name = "P4PresentationAgent"
    
    def __init__(self):
        self.logger = logger
        
    async def compose_document(self, request: DocumentCompositionRequest) -> DocumentResult:
        """
        Compose document from existing substrate.
        
        Operations allowed:
        - Document composition from substrate
        - Narrative generation for user consumption
        - User-facing content creation
        - Presentation formatting
        
        Operations forbidden:
        - Substrate creation (P1 responsibility)
        - Substrate modification (P1 responsibility)
        - Relationship creation (P2 responsibility)
        - Pattern computation (P3 responsibility)
        """
        start_time = datetime.utcnow()
        
        try:
            # Get substrate elements for composition (P4 read-only operation)
            substrate_elements = await self._get_substrate_for_composition(
                request.workspace_id,
                request.basket_id,
                request.substrate_references
            )
            
            if not substrate_elements:
                raise ValueError(f"No substrate found for document composition")
            
            # Generate substrate references (P4 operation)
            substrate_refs = self._generate_substrate_references(substrate_elements)
            
            # Compose narrative content (P4 operation)
            narrative_content = self._compose_narrative(
                substrate_elements,
                request.composition_type,
                request.narrative_prompt
            )
            
            # Create composed document (P4 operation)
            composed_document = ComposedDocument(
                title=request.document_title,
                narrative_content=narrative_content,
                substrate_references=substrate_refs,
                composition_metadata={
                    "composition_type": request.composition_type,
                    "substrate_count": len(substrate_elements),
                    "composed_by": self.agent_name,
                    "pipeline": self.pipeline,
                    "composition_timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Persist document (P4 operation)
            document_id = await self._persist_document(
                request.workspace_id,
                request.basket_id,
                composed_document,
                request.agent_id
            )
            
            # Calculate metrics
            processing_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            word_count = len(narrative_content.split()) if narrative_content else 0
            
            self.logger.info(
                f"P4 Presentation completed: document_id={document_id}, "
                f"substrate_consumed={len(substrate_elements)}, word_count={word_count}, "
                f"processing_time_ms={processing_time_ms}"
            )
            
            return DocumentResult(
                document_id=document_id,
                composed_document=composed_document,
                processing_time_ms=processing_time_ms,
                substrate_consumed=len(substrate_elements),
                narrative_word_count=word_count
            )
            
        except Exception as e:
            self.logger.error(f"P4 Presentation failed for basket {request.basket_id}: {e}")
            raise
    
    async def _get_substrate_for_composition(
        self,
        workspace_id: UUID,
        basket_id: UUID,
        substrate_references: List[str]
    ) -> List[Dict[str, Any]]:
        """Get substrate elements for document composition (read-only)."""
        try:
            substrate_elements = []
            
            if substrate_references:
                # Get specific referenced substrate
                for ref_id in substrate_references:
                    # Try blocks first
                    block_response = supabase.table("blocks").select(
                        "id,title,body_md,semantic_type,status,confidence_score,metadata"
                    ).eq("id", ref_id).eq("basket_id", str(basket_id)).execute()
                    
                    if block_response.data:
                        for block in block_response.data:
                            substrate_elements.append({
                                "id": block["id"],
                                "type": "block",
                                "title": block.get("title", ""),
                                "content": block.get("body_md", ""),
                                "semantic_type": block.get("semantic_type", "concept"),
                                "status": block.get("status", "proposed"),
                                "confidence": block.get("confidence_score", 0.5),
                                "metadata": block.get("metadata", {})
                            })
                        continue
                    
                    # Try context items
                    context_response = supabase.table("context_items").select(
                        "id,type,content,metadata"
                    ).eq("id", ref_id).eq("basket_id", str(basket_id)).execute()
                    
                    if context_response.data:
                        for item in context_response.data:
                            substrate_elements.append({
                                "id": item["id"],
                                "type": "context_item",
                                "title": item.get("content", "")[:50],
                                "content": item.get("content", ""),
                                "semantic_type": item.get("type", "concept"),
                                "metadata": item.get("metadata", {})
                            })
            
            else:
                # Get all substrate from basket if no specific references
                # Get blocks
                blocks_response = supabase.table("blocks").select(
                    "id,title,body_md,semantic_type,status,confidence_score,metadata"
                ).eq("basket_id", str(basket_id)).execute()
                
                if blocks_response.data:
                    for block in blocks_response.data:
                        substrate_elements.append({
                            "id": block["id"],
                            "type": "block",
                            "title": block.get("title", ""),
                            "content": block.get("body_md", ""),
                            "semantic_type": block.get("semantic_type", "concept"),
                            "status": block.get("status", "proposed"),
                            "confidence": block.get("confidence_score", 0.5),
                            "metadata": block.get("metadata", {})
                        })
                
                # Get context items
                context_response = supabase.table("context_items").select(
                    "id,type,content,metadata"
                ).eq("basket_id", str(basket_id)).execute()
                
                if context_response.data:
                    for item in context_response.data:
                        substrate_elements.append({
                            "id": item["id"],
                            "type": "context_item",
                            "title": item.get("content", "")[:50],
                            "content": item.get("content", ""),
                            "semantic_type": item.get("type", "concept"),
                            "metadata": item.get("metadata", {})
                        })
            
            return substrate_elements
            
        except Exception as e:
            self.logger.error(f"Failed to get substrate for composition: {e}")
            return []
    
    def _generate_substrate_references(self, substrate_elements: List[Dict[str, Any]]) -> List[SubstrateReference]:
        """Generate structured references to substrate elements."""
        references = []
        
        for element in substrate_elements:
            # Calculate relevance score based on confidence and content quality
            relevance = self._calculate_relevance_score(element)
            
            # Generate reference context
            context = self._generate_reference_context(element)
            
            references.append(SubstrateReference(
                substrate_id=element["id"],
                substrate_type=element["type"],
                reference_context=context,
                relevance_score=relevance
            ))
        
        # Sort by relevance score (highest first)
        return sorted(references, key=lambda r: r.relevance_score, reverse=True)
    
    def _compose_narrative(
        self,
        substrate_elements: List[Dict[str, Any]],
        composition_type: str,
        narrative_prompt: Optional[str]
    ) -> str:
        """Compose narrative content from substrate elements."""
        
        # Filter and organize substrate by type
        blocks = [elem for elem in substrate_elements if elem["type"] == "block"]
        context_items = [elem for elem in substrate_elements if elem["type"] == "context_item"]
        
        # Sort blocks by confidence and semantic type
        blocks.sort(key=lambda b: (b.get("confidence", 0.5), b.get("semantic_type", "")), reverse=True)
        
        if composition_type == "summary":
            return self._compose_summary_narrative(blocks, context_items)
        elif composition_type == "report":
            return self._compose_report_narrative(blocks, context_items)
        else:  # default: narrative
            return self._compose_standard_narrative(blocks, context_items, narrative_prompt)
    
    def _compose_summary_narrative(self, blocks: List[Dict[str, Any]], context_items: List[Dict[str, Any]]) -> str:
        """Compose a summary narrative from substrate."""
        parts = []
        
        # Executive summary
        parts.append("## Summary")
        parts.append(f"This analysis encompasses {len(blocks)} structured insights and {len(context_items)} contextual elements.")
        
        # Key insights
        if blocks:
            parts.append("\n## Key Insights")
            for i, block in enumerate(blocks[:5], 1):  # Top 5 blocks
                semantic_type = block.get("semantic_type", "concept").title()
                title = block.get("title", f"Insight {i}")
                confidence = block.get("confidence", 0.5)
                
                parts.append(f"\n**{i}. {title}** _{semantic_type}_ (Confidence: {confidence:.1f})")
                
                # Extract first sentence or first 150 chars
                content = block.get("content", "")
                if content:
                    first_sentence = content.split('.')[0].strip()
                    if len(first_sentence) > 150:
                        first_sentence = first_sentence[:147] + "..."
                    parts.append(first_sentence + ".")
        
        # Context overview
        if context_items:
            parts.append(f"\n## Context Overview")
            context_types = {}
            for item in context_items:
                item_type = item.get("semantic_type", "concept")
                if item_type not in context_types:
                    context_types[item_type] = 0
                context_types[item_type] += 1
            
            context_summary = ", ".join([f"{count} {type_name}(s)" for type_name, count in context_types.items()])
            parts.append(f"Contextual elements include: {context_summary}.")
        
        return "\n".join(parts)
    
    def _compose_report_narrative(self, blocks: List[Dict[str, Any]], context_items: List[Dict[str, Any]]) -> str:
        """Compose a structured report narrative from substrate."""
        parts = []
        
        # Report header
        parts.append("# Analysis Report")
        parts.append(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
        parts.append(f"Substrate Analysis: {len(blocks)} blocks, {len(context_items)} context items")
        
        # Group blocks by semantic type
        semantic_groups = {}
        for block in blocks:
            semantic_type = block.get("semantic_type", "concept")
            if semantic_type not in semantic_groups:
                semantic_groups[semantic_type] = []
            semantic_groups[semantic_type].append(block)
        
        # Report sections by semantic type
        for semantic_type, group_blocks in semantic_groups.items():
            parts.append(f"\n## {semantic_type.title()} Analysis")
            parts.append(f"Found {len(group_blocks)} {semantic_type}(s) with varying confidence levels.")
            
            for block in group_blocks[:3]:  # Top 3 per category
                title = block.get("title", "Untitled")
                confidence = block.get("confidence", 0.5)
                parts.append(f"\n### {title}")
                parts.append(f"_Confidence: {confidence:.1f}_")
                
                content = block.get("content", "")
                if content:
                    # Use first paragraph or first 200 chars
                    if '\n' in content:
                        first_para = content.split('\n')[0].strip()
                    else:
                        first_para = content[:200] + ("..." if len(content) > 200 else "")
                    parts.append(first_para)
        
        # Context section
        if context_items:
            parts.append("\n## Contextual Elements")
            for item in context_items[:10]:  # Top 10 context items
                content = item.get("content", "")
                item_type = item.get("semantic_type", "concept")
                if content:
                    parts.append(f"- **{item_type.title()}**: {content}")
        
        return "\n".join(parts)
    
    def _compose_standard_narrative(
        self,
        blocks: List[Dict[str, Any]],
        context_items: List[Dict[str, Any]],
        narrative_prompt: Optional[str]
    ) -> str:
        """Compose a standard narrative from substrate."""
        parts = []
        
        # Introduction
        if narrative_prompt:
            parts.append(narrative_prompt)
            parts.append("")
        
        parts.append(f"This narrative synthesizes insights from {len(blocks)} structured elements and {len(context_items)} contextual pieces.")
        
        # Main narrative flow
        if blocks:
            parts.append("\n## Core Insights")
            
            # Group by semantic type for narrative flow
            goals = [b for b in blocks if b.get("semantic_type") == "goal"]
            problems = [b for b in blocks if b.get("semantic_type") == "problem"]
            solutions = [b for b in blocks if b.get("semantic_type") == "solution"]
            insights = [b for b in blocks if b.get("semantic_type") == "insight"]
            other_blocks = [b for b in blocks if b.get("semantic_type") not in ["goal", "problem", "solution", "insight"]]
            
            # Goals narrative
            if goals:
                parts.append("\n### Objectives & Goals")
                for goal in goals:
                    title = goal.get("title", "Goal")
                    content = goal.get("content", "")
                    if content:
                        parts.append(f"**{title}**: {content}")
            
            # Problems narrative
            if problems:
                parts.append("\n### Challenges & Issues")
                for problem in problems:
                    title = problem.get("title", "Challenge")
                    content = problem.get("content", "")
                    if content:
                        parts.append(f"**{title}**: {content}")
            
            # Solutions narrative
            if solutions:
                parts.append("\n### Solutions & Approaches")
                for solution in solutions:
                    title = solution.get("title", "Solution")
                    content = solution.get("content", "")
                    if content:
                        parts.append(f"**{title}**: {content}")
            
            # Insights narrative
            if insights:
                parts.append("\n### Key Insights")
                for insight in insights:
                    title = insight.get("title", "Insight")
                    content = insight.get("content", "")
                    if content:
                        parts.append(f"**{title}**: {content}")
            
            # Other blocks
            if other_blocks:
                parts.append("\n### Additional Considerations")
                for block in other_blocks:
                    title = block.get("title", "Note")
                    content = block.get("content", "")
                    if content:
                        parts.append(f"**{title}**: {content}")
        
        # Context integration
        if context_items:
            parts.append("\n## Context & Background")
            
            # Group context by type
            context_groups = {}
            for item in context_items:
                item_type = item.get("semantic_type", "concept")
                if item_type not in context_groups:
                    context_groups[item_type] = []
                context_groups[item_type].append(item)
            
            for context_type, items in context_groups.items():
                if items:
                    parts.append(f"\n### {context_type.title()} Context")
                    for item in items[:5]:  # Limit per type
                        content = item.get("content", "")
                        if content:
                            parts.append(f"- {content}")
        
        return "\n".join(parts)
    
    def _calculate_relevance_score(self, element: Dict[str, Any]) -> float:
        """Calculate relevance score for substrate element."""
        base_score = 0.5
        
        # Boost for confidence
        confidence = element.get("confidence", 0.5)
        base_score += confidence * 0.3
        
        # Boost for content length (more detailed = more relevant)
        content = element.get("content", "")
        if len(content) > 100:
            base_score += 0.1
        if len(content) > 300:
            base_score += 0.1
        
        # Boost for accepted status
        if element.get("status") == "accepted":
            base_score += 0.2
        
        return min(1.0, base_score)
    
    def _generate_reference_context(self, element: Dict[str, Any]) -> str:
        """Generate context description for substrate reference."""
        element_type = element.get("type", "substrate")
        semantic_type = element.get("semantic_type", "concept")
        title = element.get("title", "Untitled")
        
        if element_type == "block":
            return f"{semantic_type.title()} block: {title}"
        elif element_type == "context_item":
            return f"{semantic_type.title()} context: {title}"
        else:
            return f"{element_type.title()}: {title}"
    
    async def _persist_document(
        self,
        workspace_id: UUID,
        basket_id: UUID,
        composed_document: ComposedDocument,
        agent_id: str
    ) -> UUID:
        """Persist composed document to database."""
        try:
            # Prepare document data
            document_data = {
                "workspace_id": str(workspace_id),
                "basket_id": str(basket_id),
                "title": composed_document.title,
                "content": composed_document.narrative_content,
                "document_type": composed_document.composition_metadata.get("composition_type", "narrative"),
                "metadata": {
                    **composed_document.composition_metadata,
                    "substrate_references": [ref.dict() for ref in composed_document.substrate_references],
                    "generated_by": self.agent_name,
                    "pipeline": self.pipeline,
                    "agent_id": agent_id
                },
                "status": "draft"
            }
            
            # FIXED: Split insert and select calls for Supabase client compatibility
            response = supabase.table("documents").insert(document_data).execute()
            
            if response.data and len(response.data) > 0:
                # Get the inserted record with all fields
                inserted_id = response.data[0]["id"]
                select_response = supabase.table("documents").select("*").eq("id", inserted_id).single().execute()
                
                if select_response.data:
                    return UUID(select_response.data["id"])
                else:
                    raise RuntimeError("Failed to retrieve created document")
            else:
                raise RuntimeError("Document persistence returned no document_id")
                
        except Exception as e:
            self.logger.error(f"Failed to persist document: {e}")
            raise
    
    def get_agent_info(self) -> Dict[str, str]:
        """Get agent information."""
        return {
            "name": self.agent_name,
            "pipeline": self.pipeline,
            "type": "presentation",
            "status": "active",
            "sacred_rule": "Consumes substrate for narrative, never creates substrate"
        }