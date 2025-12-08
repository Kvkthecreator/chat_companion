"""
Test D - Section ablation

Generates sections independently and allows swapping in human-written sections
to identify which sections systematically fail.
"""

import time
import logging
from typing import List, Dict, Any, Optional, Tuple

from infra.substrate.services.llm import get_llm
from ..types import (
    TestInput, TestResult, TestType, QualityMetrics,
    CitationSpan, HarnessConfig
)
from ..utils import extract_sentences, extract_citations, compute_text_spans

logger = logging.getLogger(__name__)


class TestD:
    """Test D - Section-by-section composition with ablation"""
    
    def __init__(self, config: HarnessConfig):
        self.config = config
        self.test_type = TestType.TEST_D
        self.llm = get_llm()
        
        # Define section generation strategies
        self.section_generators = {
            "Title": self._generate_title,
            "TL;DR": self._generate_tldr,
            "Context": self._generate_context,
            "Findings": self._generate_findings,
            "Recommendations": self._generate_recommendations,
            "Next Steps": self._generate_next_steps
        }
    
    async def run(self, test_input: TestInput) -> TestResult:
        """Run Test D with section ablation"""
        start_time = time.time()
        errors = []
        
        try:
            # Generate text spans for citation
            text_spans = compute_text_spans(test_input.raw_text)
            
            # Generate each section independently
            sections = {}
            section_citations = {}
            section_metrics = {}
            
            for section_name in self.config.required_sections:
                if section_name in self.section_generators:
                    # Check if we have a human override for this section
                    override = test_input.metadata.get(f"override_{section_name.lower()}")
                    
                    if override:
                        # Use human-written section
                        sections[section_name] = override
                        section_citations[section_name] = []
                        section_metrics[section_name] = {"source": "human_override"}
                    else:
                        # Generate section
                        content, citations = await self.section_generators[section_name](
                            test_input.raw_text,
                            text_spans
                        )
                        sections[section_name] = content
                        section_citations[section_name] = citations
                        section_metrics[section_name] = {
                            "source": "generated",
                            "citations_count": len(citations)
                        }
            
            # Combine sections into artifact
            artifact = self._combine_sections(sections)
            
            # Combine all citations
            all_citations = []
            for citations in section_citations.values():
                all_citations.extend(citations)
            
            # Compute overall metrics
            metrics = await self._compute_metrics(
                artifact,
                all_citations,
                sections,
                section_metrics,
                start_time
            )
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            return TestResult(
                test_type=self.test_type,
                input_id=test_input.input_id,
                metrics=metrics,
                artifact=artifact,
                citations=all_citations,
                execution_time_ms=execution_time_ms,
                errors=errors,
                metadata={
                    "section_metrics": section_metrics,
                    "text_spans_count": len(text_spans)
                }
            )
            
        except Exception as e:
            logger.error(f"Test D failed for {test_input.input_id}: {e}")
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
    
    async def _generate_title(
        self,
        raw_text: str,
        text_spans: List[Tuple[str, int, int]]
    ) -> Tuple[str, List[CitationSpan]]:
        """Generate title section"""
        prompt = f"""Generate a concise title (5-10 words) for this content:

{raw_text[:500]}...

Title:"""
        
        response = await self.llm.get_text_response(
            prompt=prompt,
            temperature=self.config.llm_temperature,
            max_tokens=50
        )
        
        title = response.content.strip() if response.success else "Analysis Report"
        return title, []  # Titles typically don't have citations
    
    async def _generate_tldr(
        self,
        raw_text: str,
        text_spans: List[Tuple[str, int, int]]
    ) -> Tuple[str, List[CitationSpan]]:
        """Generate TL;DR section"""
        # Build span references
        span_refs = []
        for i, (text, _, _) in enumerate(text_spans[:20]):
            span_refs.append(f"[S{i+1}] {text.strip()}")
        
        prompt = f"""Generate a 2-3 sentence TL;DR summary using ONLY the provided spans. 
Cite each claim with [S#].

SOURCE SPANS:
{chr(10).join(span_refs)}

TL;DR:"""
        
        response = await self.llm.get_text_response(
            prompt=prompt,
            temperature=self.config.llm_temperature,
            max_tokens=150
        )
        
        if not response.success:
            return "Summary generation failed.", []
        
        # Extract citations
        content = response.content.strip()
        citations = self._extract_span_citations(content, text_spans)
        
        return content, citations
    
    async def _generate_context(
        self,
        raw_text: str,
        text_spans: List[Tuple[str, int, int]]
    ) -> Tuple[str, List[CitationSpan]]:
        """Generate Context section"""
        # Focus on background/context sentences
        context_spans = []
        for i, (text, start, end) in enumerate(text_spans[:30]):
            if any(word in text.lower() for word in ["background", "context", "history", "previously", "began"]):
                context_spans.append((i, text, start, end))
        
        if not context_spans:
            context_spans = [(i, t, s, e) for i, (t, s, e) in enumerate(text_spans[:10])]
        
        span_refs = [f"[S{i+1}] {text.strip()}" for i, text, _, _ in context_spans]
        
        prompt = f"""Generate a Context section using the provided spans. 
Explain the background and situation. Cite each fact with [S#].

SOURCE SPANS:
{chr(10).join(span_refs)}

Context:"""
        
        response = await self.llm.get_text_response(
            prompt=prompt,
            temperature=self.config.llm_temperature,
            max_tokens=300
        )
        
        if not response.success:
            return "Context unavailable.", []
        
        content = response.content.strip()
        citations = self._extract_span_citations(content, text_spans)
        
        return content, citations
    
    async def _generate_findings(
        self,
        raw_text: str,
        text_spans: List[Tuple[str, int, int]]
    ) -> Tuple[str, List[CitationSpan]]:
        """Generate Findings section"""
        # Focus on evidence and insights
        finding_spans = []
        for i, (text, start, end) in enumerate(text_spans):
            if any(word in text.lower() for word in ["found", "discovered", "shows", "indicates", "reveals", "data", "evidence"]):
                finding_spans.append((i, text, start, end))
        
        if len(finding_spans) < 5:
            finding_spans.extend([(i, t, s, e) for i, (t, s, e) in enumerate(text_spans[10:30])])
        
        span_refs = [f"[S{i+1}] {text.strip()}" for i, text, _, _ in finding_spans[:20]]
        
        prompt = f"""Generate a Findings section with key discoveries and insights.
Use bullet points. Cite each finding with [S#].

SOURCE SPANS:
{chr(10).join(span_refs)}

Findings:"""
        
        response = await self.llm.get_text_response(
            prompt=prompt,
            temperature=self.config.llm_temperature,
            max_tokens=400
        )
        
        if not response.success:
            return "Findings unavailable.", []
        
        content = response.content.strip()
        citations = self._extract_span_citations(content, text_spans)
        
        return content, citations
    
    async def _generate_recommendations(
        self,
        raw_text: str,
        text_spans: List[Tuple[str, int, int]]
    ) -> Tuple[str, List[CitationSpan]]:
        """Generate Recommendations section"""
        # Look for action-oriented content
        rec_spans = []
        for i, (text, start, end) in enumerate(text_spans):
            if any(word in text.lower() for word in ["should", "recommend", "suggest", "must", "need to", "action"]):
                rec_spans.append((i, text, start, end))
        
        span_refs = [f"[S{i+1}] {text.strip()}" for i, text, _, _ in rec_spans[:15]]
        
        prompt = f"""Generate a Recommendations section based on the findings.
If no explicit recommendations in source, infer reasonable ones and cite supporting evidence.

SOURCE SPANS:
{chr(10).join(span_refs)}

Recommendations:"""
        
        response = await self.llm.get_text_response(
            prompt=prompt,
            temperature=self.config.llm_temperature,
            max_tokens=300
        )
        
        if not response.success:
            return "Recommendations unavailable.", []
        
        content = response.content.strip()
        citations = self._extract_span_citations(content, text_spans)
        
        return content, citations
    
    async def _generate_next_steps(
        self,
        raw_text: str,
        text_spans: List[Tuple[str, int, int]]
    ) -> Tuple[str, List[CitationSpan]]:
        """Generate Next Steps section"""
        # Similar to recommendations but more concrete
        prompt = f"""Generate a Next Steps section with 3-5 concrete actions.
Base on the content provided. Format as a numbered list.

CONTENT SUMMARY:
{raw_text[:500]}...

Next Steps:"""
        
        response = await self.llm.get_text_response(
            prompt=prompt,
            temperature=self.config.llm_temperature,
            max_tokens=200
        )
        
        if not response.success:
            return "1. Review findings\n2. Plan implementation\n3. Monitor progress", []
        
        return response.content.strip(), []  # Next steps often don't need citations
    
    def _combine_sections(self, sections: Dict[str, str]) -> str:
        """Combine sections into final artifact"""
        artifact_parts = []
        
        # Add title without section marker
        if "Title" in sections and sections["Title"]:
            artifact_parts.append(f"# {sections['Title']}")
        
        # Add other sections with markers
        for section in ["TL;DR", "Context", "Findings", "Recommendations", "Next Steps"]:
            if section in sections and sections[section]:
                artifact_parts.append(f"## {section}\n{sections[section]}")
        
        return "\n\n".join(artifact_parts)
    
    def _extract_span_citations(
        self,
        content: str,
        text_spans: List[Tuple[str, int, int]]
    ) -> List[CitationSpan]:
        """Extract citation spans from content"""
        citations = []
        citation_pattern = re.compile(r'\[S(\d+)\]')
        
        for match in citation_pattern.finditer(content):
            span_num = int(match.group(1)) - 1
            if 0 <= span_num < len(text_spans):
                text, start, end = text_spans[span_num]
                citations.append(CitationSpan(
                    span_id=f"S{span_num+1}",
                    source_start=start,
                    source_end=end,
                    text=text
                ))
        
        return citations
    
    async def _compute_metrics(
        self,
        artifact: str,
        citations: List[CitationSpan],
        sections: Dict[str, str],
        section_metrics: Dict[str, Dict[str, Any]],
        start_time: float
    ) -> QualityMetrics:
        """Compute metrics for section-based generation"""
        
        sentences = extract_sentences(artifact)
        total_sentences = len(sentences)
        
        # Check which sections are present and non-empty
        required_sections_present = {}
        for section in self.config.required_sections:
            required_sections_present[section] = (
                section in sections and 
                len(sections[section].strip()) > 10
            )
        
        # Citation analysis
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
        
        # Penalty for sections that failed to generate
        for section, metrics in section_metrics.items():
            if metrics.get("source") == "generated" and section not in sections:
                structure_score *= 0.9
        
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