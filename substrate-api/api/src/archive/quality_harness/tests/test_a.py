"""
Test A - Upper-bound (compose directly from raw)

Composes artifact directly from raw text with strict constraints:
- Summarize only from provided text
- Require inline citations per sentence
- Map citations to source spans
"""

import re
import time
import logging
from typing import List, Tuple, Optional
from datetime import datetime

from infra.substrate.services.llm import get_llm
from ..types import (
    TestInput, TestResult, TestType, QualityMetrics,
    CitationSpan, HarnessConfig
)
from ..utils import extract_sentences, extract_citations, compute_text_spans

logger = logging.getLogger(__name__)


class TestA:
    """Test A - Direct composition from raw text with citations"""
    
    def __init__(self, config: HarnessConfig):
        self.config = config
        self.llm = get_llm()
        self.test_type = TestType.TEST_A
    
    async def run(self, test_input: TestInput) -> TestResult:
        """Run Test A on single input"""
        start_time = time.time()
        errors = []
        
        try:
            # Generate text spans for citation
            text_spans = compute_text_spans(test_input.raw_text)
            
            # Compose directly from raw with strict citation requirements
            artifact, citations = await self._compose_with_citations(
                test_input.raw_text,
                text_spans
            )
            
            # Compute metrics
            metrics = await self._compute_metrics(artifact, citations, start_time)
            
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
                    "text_spans_count": len(text_spans),
                    "raw_text_length": len(test_input.raw_text)
                }
            )
            
        except Exception as e:
            logger.error(f"Test A failed for {test_input.input_id}: {e}")
            errors.append(str(e))
            
            # Return error result
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
    
    async def _compose_with_citations(
        self, 
        raw_text: str, 
        text_spans: List[Tuple[str, int, int]]
    ) -> Tuple[str, List[CitationSpan]]:
        """Compose artifact from raw text with inline citations"""
        
        # Build span reference for prompt
        span_references = []
        for i, (text, start, end) in enumerate(text_spans):
            span_id = f"S{i+1}"
            span_references.append(f"[{span_id}] {text.strip()}")
        
        prompt = f"""You are composing a structured brief from raw source material.

STRICT REQUIREMENTS:
1. Use ONLY information from the provided text spans
2. EVERY sentence must have at least one citation using [S#] format
3. Citations must accurately reference the source span
4. Structure the brief with these sections: Title, TL;DR, Context, Findings, Recommendations, Next Steps
5. Be concise and factual

SOURCE TEXT SPANS:
{chr(10).join(span_references[:50])}  # Limit to 50 spans for prompt size

TASK: Compose a structured brief using the source spans above. Remember to cite every sentence.

Brief:"""

        response = await self.llm.get_text_response(
            prompt=prompt,
            temperature=self.config.llm_temperature,
            max_tokens=2000
        )
        
        if not response.success or not response.content:
            raise ValueError("LLM composition failed")
        
        artifact = response.content.strip()
        
        # Extract citations from artifact
        citations = []
        citation_pattern = re.compile(r'\[S(\d+)\]')
        
        for match in citation_pattern.finditer(artifact):
            span_num = int(match.group(1)) - 1
            if 0 <= span_num < len(text_spans):
                text, start, end = text_spans[span_num]
                citations.append(CitationSpan(
                    span_id=f"S{span_num+1}",
                    source_start=start,
                    source_end=end,
                    text=text
                ))
        
        return artifact, citations
    
    async def _compute_metrics(
        self,
        artifact: str,
        citations: List[CitationSpan],
        start_time: float
    ) -> QualityMetrics:
        """Compute quality metrics for the artifact"""
        
        # Extract sentences
        sentences = extract_sentences(artifact)
        total_sentences = len(sentences)
        
        # Check required sections
        required_sections_present = {}
        for section in self.config.required_sections:
            # Simple check - could be made more sophisticated
            required_sections_present[section] = section.lower() in artifact.lower()
        
        # Count citations per sentence
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
        
        # Structure score based on required sections
        sections_present = sum(1 for present in required_sections_present.values() if present)
        structure_score = sections_present / len(self.config.required_sections)
        
        # Time to draft
        time_to_draft_ms = int((time.time() - start_time) * 1000)
        
        return QualityMetrics(
            structure_score=structure_score,
            provenance_coverage=provenance_coverage,
            avg_citations_per_sentence=avg_citations,
            uncited_sentences_count=uncited_sentences,
            dropped_sentences_due_to_no_citation=0,  # Test A doesn't drop
            time_to_draft_ms=time_to_draft_ms,
            required_sections_present=required_sections_present,
            total_sentences=total_sentences,
            total_citations=total_citation_count
        )