"""
Test C - No-new-facts constraint

Re-runs Tests A and B with a hard rule:
- Every sentence must cite ≥1 source span
- Drop or flag uncitable sentences
"""

import re
import time
import logging
from typing import List, Tuple, Dict, Any

from .test_a import TestA
from .test_b import TestB
from ..types import (
    TestInput, TestResult, TestType, QualityMetrics,
    CitationSpan, HarnessConfig
)
from ..utils import extract_sentences, extract_citations

logger = logging.getLogger(__name__)


class TestC:
    """Test C - Enforce no-new-facts constraint"""
    
    def __init__(self, config: HarnessConfig):
        self.config = config
        self.test_type = TestType.TEST_C
        # Reuse Test A and B runners
        self.test_a = TestA(config)
        self.test_b = TestB(config)
    
    async def run(self, test_input: TestInput) -> TestResult:
        """Run Test C with strict citation enforcement"""
        start_time = time.time()
        errors = []
        
        try:
            # Decide whether to run as Test A or B variant based on oracle blocks
            if test_input.oracle_blocks:
                # Run Test B variant with constraints
                base_result = await self.test_b.run(test_input)
            else:
                # Run Test A variant with constraints
                base_result = await self.test_a.run(test_input)
            
            # Apply no-new-facts constraint
            filtered_artifact, dropped_count, citations = await self._apply_no_new_facts(
                base_result.artifact,
                base_result.citations
            )
            
            # Recompute metrics with filtered artifact
            metrics = await self._compute_metrics(
                filtered_artifact,
                citations,
                dropped_count,
                start_time
            )
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            return TestResult(
                test_type=self.test_type,
                input_id=test_input.input_id,
                metrics=metrics,
                artifact=filtered_artifact,
                citations=citations,
                execution_time_ms=execution_time_ms,
                errors=errors,
                metadata={
                    "base_test": "B" if test_input.oracle_blocks else "A",
                    "original_sentences": base_result.metrics.total_sentences,
                    "dropped_sentences": dropped_count,
                    "filtering_applied": True
                }
            )
            
        except Exception as e:
            logger.error(f"Test C failed for {test_input.input_id}: {e}")
            errors.append(str(e))
            
            return TestResult(
                test_type=self.test_type,
                input_id=test_input.input_id,
                metrics=QualityMetrics(
                    structure_score=0.0,
                    provenance_coverage=0.0,
                    avg_citations_per_sentence=0.0,
                    uncited_sentences_count=0,
                    dropped_sentences_due_to_no_citation=0,
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
    
    async def _apply_no_new_facts(
        self,
        artifact: str,
        citations: List[CitationSpan]
    ) -> Tuple[str, int, List[CitationSpan]]:
        """Apply no-new-facts constraint by filtering uncited sentences"""
        
        # Build citation lookup
        citation_ids = {c.span_id for c in citations}
        
        # Process artifact by sections
        sections = artifact.split('\n## ')
        filtered_sections = []
        total_dropped = 0
        
        for section in sections:
            if not section.strip():
                continue
            
            lines = section.split('\n')
            section_name = lines[0] if lines else ""
            
            # Process each line
            filtered_lines = [section_name] if section_name else []
            
            for line in lines[1:]:
                if not line.strip():
                    filtered_lines.append(line)
                    continue
                
                # Check if line has citations
                line_citations = extract_citations(line)
                
                if line_citations:
                    # Keep lines with citations
                    filtered_lines.append(line)
                else:
                    # Check if this is a structural element (bullet point, etc)
                    if line.strip().startswith(('-', '*', '•')) or line.strip().endswith(':'):
                        # Keep structural elements
                        filtered_lines.append(line)
                    else:
                        # Drop uncited content sentences
                        total_dropped += 1
                        # Add marker for dropped content
                        filtered_lines.append(f"[DROPPED: Uncited sentence removed]")
                        logger.debug(f"Dropped uncited sentence: {line[:50]}...")
            
            if len(filtered_lines) > 1:  # More than just section name
                filtered_sections.append('\n'.join(filtered_lines))
        
        # Rebuild artifact
        filtered_artifact = '\n## '.join(filtered_sections)
        
        # Clean up dropped markers for final artifact
        filtered_artifact = filtered_artifact.replace('[DROPPED: Uncited sentence removed]\n', '')
        filtered_artifact = filtered_artifact.replace('[DROPPED: Uncited sentence removed]', '')
        
        # Filter citations to only those still referenced
        remaining_citations = []
        for citation in citations:
            if citation.span_id in filtered_artifact:
                remaining_citations.append(citation)
        
        return filtered_artifact, total_dropped, remaining_citations
    
    async def _compute_metrics(
        self,
        artifact: str,
        citations: List[CitationSpan],
        dropped_count: int,
        start_time: float
    ) -> QualityMetrics:
        """Compute metrics for filtered artifact"""
        
        sentences = extract_sentences(artifact)
        total_sentences = len(sentences)
        
        # Check sections (may be affected by filtering)
        required_sections_present = {}
        for section in self.config.required_sections:
            # Check if section exists and has content
            section_pattern = f"## {section}"
            if section_pattern in artifact:
                # Check if section has any content after header
                section_start = artifact.find(section_pattern)
                section_end = artifact.find("\n## ", section_start + 1)
                if section_end == -1:
                    section_end = len(artifact)
                section_content = artifact[section_start:section_end].strip()
                # Section is present if it has more than just the header
                required_sections_present[section] = len(section_content) > len(section_pattern) + 5
            else:
                required_sections_present[section] = False
        
        # All remaining sentences should have citations
        sentences_with_citations = 0
        total_citation_count = 0
        
        for sentence in sentences:
            sentence_citations = extract_citations(sentence)
            if sentence_citations:
                sentences_with_citations += 1
                total_citation_count += len(sentence_citations)
        
        # With no-new-facts constraint, coverage should be very high
        uncited_sentences = total_sentences - sentences_with_citations
        provenance_coverage = sentences_with_citations / total_sentences if total_sentences > 0 else 0.0
        avg_citations = total_citation_count / total_sentences if total_sentences > 0 else 0.0
        
        # Structure score may be lower if sections were emptied
        sections_present = sum(1 for present in required_sections_present.values() if present)
        structure_score = sections_present / len(self.config.required_sections)
        
        time_to_draft_ms = int((time.time() - start_time) * 1000)
        
        return QualityMetrics(
            structure_score=structure_score,
            provenance_coverage=provenance_coverage,
            avg_citations_per_sentence=avg_citations,
            uncited_sentences_count=uncited_sentences,
            dropped_sentences_due_to_no_citation=dropped_count,
            time_to_draft_ms=time_to_draft_ms,
            required_sections_present=required_sections_present,
            total_sentences=total_sentences,
            total_citations=total_citation_count
        )