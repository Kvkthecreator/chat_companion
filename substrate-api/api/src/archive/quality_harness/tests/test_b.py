"""
Test B - Oracle substrate (downstream cap)

Feeds the composer hand-labeled/ideal blocks to test composition quality
when substrate is perfect.
"""

import time
import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime

from ..types import (
    TestInput, TestResult, TestType, QualityMetrics,
    CitationSpan, HarnessConfig
)
from ..utils import extract_sentences, extract_citations
from ...agents.pipeline.presentation_agent import P4PresentationAgent

logger = logging.getLogger(__name__)


class TestB:
    """Test B - Composition from oracle (perfect) substrate"""
    
    def __init__(self, config: HarnessConfig):
        self.config = config
        self.test_type = TestType.TEST_B
        # Reuse P4 presentation agent for composition
        self.composer = P4PresentationAgent()
    
    async def run(self, test_input: TestInput) -> TestResult:
        """Run Test B with oracle substrate"""
        start_time = time.time()
        errors = []
        
        try:
            # Use oracle blocks if provided, otherwise generate ideal blocks
            oracle_blocks = test_input.oracle_blocks or await self._generate_oracle_blocks(
                test_input.raw_text
            )
            
            # Compose from oracle substrate
            artifact, citations = await self._compose_from_oracle(
                oracle_blocks,
                test_input.input_id
            )
            
            # Compute metrics
            metrics = await self._compute_metrics(
                artifact, 
                citations, 
                oracle_blocks,
                start_time
            )
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            return TestResult(
                test_type=self.test_type,
                input_id=test_input.input_id,
                metrics=metrics,
                artifact=artifact,
                citations=citations,
                execution_time_ms=execution_time_ms,
                errors=errors,
                metadata={
                    "oracle_blocks_count": len(oracle_blocks),
                    "oracle_blocks_roles": self._count_block_roles(oracle_blocks)
                }
            )
            
        except Exception as e:
            logger.error(f"Test B failed for {test_input.input_id}: {e}")
            errors.append(str(e))
            
            return TestResult(
                test_type=self.test_type,
                input_id=test_input.input_id,
                metrics=QualityMetrics(
                    structure_score=0.0,
                    provenance_coverage=0.0,
                    avg_citations_per_sentence=0.0,
                    uncited_sentences_count=0,
                    time_to_draft_ms=int((time.time() - start_time) * 1000),
                    required_sections_present={},
                    total_sentences=0,
                    total_citations=0
                ),
                artifact="",
                citations=[],
                execution_time_ms=int((time.time() - start_time) * 1000),
                errors=errors
            )
    
    async def _generate_oracle_blocks(self, raw_text: str) -> List[Dict[str, Any]]:
        """Generate ideal substrate blocks from raw text"""
        # For testing, create perfect blocks with clear roles and provenance
        # In production, these would be hand-labeled
        
        sentences = raw_text.split('.')[:10]  # Simple split for demo
        oracle_blocks = []
        
        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue
                
            # Assign roles based on content heuristics
            role = "evidence"
            if any(word in sentence.lower() for word in ["should", "recommend", "suggest"]):
                role = "instruction"
            elif any(word in sentence.lower() for word in ["insight", "analysis", "indicates"]):
                role = "insight"
            elif i == 0:
                role = "background"
            
            oracle_blocks.append({
                "id": f"oracle_{i}",
                "text": sentence.strip() + ".",
                "role": role,
                "source_start": raw_text.find(sentence),
                "source_end": raw_text.find(sentence) + len(sentence),
                "confidence": 1.0,
                "semantic_type": role
            })
        
        return oracle_blocks
    
    async def _compose_from_oracle(
        self,
        oracle_blocks: List[Dict[str, Any]],
        input_id: str
    ) -> Tuple[str, List[CitationSpan]]:
        """Compose using oracle substrate blocks"""
        
        # Format blocks for P4 agent
        substrate_elements = []
        for block in oracle_blocks:
            substrate_elements.append({
                "id": block["id"],
                "type": "block",
                "title": f"{block['role'].title()} Block",
                "content": block["text"],
                "semantic_type": block.get("semantic_type", block["role"]),
                "confidence": block.get("confidence", 1.0),
                "metadata": {
                    "source_start": block.get("source_start", 0),
                    "source_end": block.get("source_end", 0)
                }
            })
        
        # Mock composition using the blocks
        # In reality, this would use the P4 agent's compose method
        sections = {
            "Title": f"Analysis of {input_id}",
            "TL;DR": "",
            "Context": "",
            "Findings": "",
            "Recommendations": "",
            "Next Steps": ""
        }
        
        # Distribute blocks into sections based on role
        for block in oracle_blocks:
            citation = f"[{block['id']}]"
            text_with_citation = f"{block['text']} {citation}"
            
            if block["role"] == "background":
                sections["Context"] += text_with_citation + " "
            elif block["role"] == "evidence":
                sections["Findings"] += text_with_citation + " "
            elif block["role"] == "insight":
                sections["Findings"] += text_with_citation + " "
                if not sections["TL;DR"]:
                    sections["TL;DR"] = block["text"]
            elif block["role"] == "instruction":
                sections["Recommendations"] += text_with_citation + " "
                sections["Next Steps"] += f"- {block['text']}\n"
        
        # Build artifact
        artifact_parts = []
        for section, content in sections.items():
            if content.strip():
                artifact_parts.append(f"## {section}\n{content.strip()}")
        
        artifact = "\n\n".join(artifact_parts)
        
        # Extract citations
        citations = []
        for block in oracle_blocks:
            if block["id"] in artifact:
                citations.append(CitationSpan(
                    span_id=block["id"],
                    source_start=block.get("source_start", 0),
                    source_end=block.get("source_end", 0),
                    text=block["text"]
                ))
        
        return artifact, citations
    
    async def _compute_metrics(
        self,
        artifact: str,
        citations: List[CitationSpan],
        oracle_blocks: List[Dict[str, Any]],
        start_time: float
    ) -> QualityMetrics:
        """Compute metrics for oracle-based composition"""
        
        sentences = extract_sentences(artifact)
        total_sentences = len(sentences)
        
        # Check sections
        required_sections_present = {}
        for section in self.config.required_sections:
            required_sections_present[section] = f"## {section}" in artifact
        
        # Citation coverage
        sentences_with_citations = 0
        total_citation_count = 0
        
        for sentence in sentences:
            sentence_citations = extract_citations(sentence)
            if sentence_citations:
                sentences_with_citations += 1
                total_citation_count += len(sentence_citations)
        
        uncited_sentences = total_sentences - sentences_with_citations
        provenance_coverage = sentences_with_citations / total_sentences if total_sentences > 0 else 0.0
        avg_citations = total_citation_count / total_sentences if total_sentences > 0 else 0.0
        
        # Structure score
        sections_present = sum(1 for present in required_sections_present.values() if present)
        structure_score = sections_present / len(self.config.required_sections)
        
        # Bonus for using diverse block roles
        role_diversity = len(set(b["role"] for b in oracle_blocks))
        if role_diversity >= 3:
            structure_score = min(1.0, structure_score + 0.1)
        
        time_to_draft_ms = int((time.time() - start_time) * 1000)
        
        return QualityMetrics(
            structure_score=structure_score,
            provenance_coverage=provenance_coverage,
            avg_citations_per_sentence=avg_citations,
            uncited_sentences_count=uncited_sentences,
            dropped_sentences_due_to_no_citation=0,
            time_to_draft_ms=time_to_draft_ms,
            required_sections_present=required_sections_present,
            total_sentences=total_sentences,
            total_citations=total_citation_count
        )
    
    def _count_block_roles(self, blocks: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count blocks by role"""
        role_counts = {}
        for block in blocks:
            role = block.get("role", "unknown")
            role_counts[role] = role_counts.get(role, 0) + 1
        return role_counts