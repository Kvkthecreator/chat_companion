"""
Diagnosis engine for quality harness
"""

import logging
from typing import Dict, List, Any
from statistics import mean

from .types import (
    TestType, TestResult, Diagnosis, DiagnosisType,
    HarnessConfig
)
from .metrics import MetricsComputer

logger = logging.getLogger(__name__)


class DiagnosisEngine:
    """Generate diagnosis from test results"""
    
    def __init__(self):
        self.metrics_computer = MetricsComputer(HarnessConfig())
    
    async def diagnose(
        self,
        test_results: Dict[TestType, List[TestResult]],
        config: HarnessConfig
    ) -> Diagnosis:
        """Generate diagnosis from all test results"""
        
        # Compute aggregate metrics for each test
        test_summaries = {}
        for test_type, results in test_results.items():
            test_summaries[test_type] = self.metrics_computer.compute_aggregate_metrics(results)
        
        # Analyze patterns
        evidence = []
        diagnosis_scores = {
            DiagnosisType.COMPOSER_BOTTLENECK: 0.0,
            DiagnosisType.EXTRACTION_BOTTLENECK: 0.0,
            DiagnosisType.SCOPE_MISMATCH: 0.0,
            DiagnosisType.MIXED_ISSUES: 0.0
        }
        
        # Test A (upper bound) analysis
        test_a_metrics = test_summaries.get(TestType.TEST_A, {})
        test_a_score = test_a_metrics.get("mean_structure_score", 0) * test_a_metrics.get("mean_provenance_coverage", 0)
        
        if test_a_score < 0.5:
            evidence.append(f"Test A (direct from raw) shows poor quality ({test_a_score:.2f}), indicating fundamental composition issues")
            diagnosis_scores[DiagnosisType.COMPOSER_BOTTLENECK] += 0.3
        else:
            evidence.append(f"Test A (direct from raw) shows good quality ({test_a_score:.2f}), composer is capable")
            diagnosis_scores[DiagnosisType.EXTRACTION_BOTTLENECK] += 0.2
        
        # Test B (oracle substrate) analysis
        test_b_metrics = test_summaries.get(TestType.TEST_B, {})
        test_b_score = test_b_metrics.get("mean_structure_score", 0) * test_b_metrics.get("mean_provenance_coverage", 0)
        
        if test_b_score > test_a_score + 0.2:
            evidence.append(f"Test B (oracle substrate) significantly outperforms Test A ({test_b_score:.2f} vs {test_a_score:.2f}), extraction is the bottleneck")
            diagnosis_scores[DiagnosisType.EXTRACTION_BOTTLENECK] += 0.4
        elif test_b_score < 0.6:
            evidence.append(f"Test B (oracle substrate) still shows poor quality ({test_b_score:.2f}), composer has issues even with perfect input")
            diagnosis_scores[DiagnosisType.COMPOSER_BOTTLENECK] += 0.4
        
        # Test C (no-new-facts) analysis
        test_c_metrics = test_summaries.get(TestType.TEST_C, {})
        dropped_sentences = test_c_metrics.get("total_dropped_sentences", 0)
        
        if dropped_sentences > 10:
            evidence.append(f"Test C dropped {dropped_sentences} sentences due to no citations, extraction is too weak")
            diagnosis_scores[DiagnosisType.EXTRACTION_BOTTLENECK] += 0.3
        elif test_c_metrics.get("mean_structure_score", 0) < 0.5:
            evidence.append("Test C shows structural collapse under citation constraints, scope mismatch")
            diagnosis_scores[DiagnosisType.SCOPE_MISMATCH] += 0.3
        
        # Test D (section ablation) analysis
        if TestType.TEST_D in test_results:
            section_success = self.metrics_computer.identify_section_weaknesses(test_results[TestType.TEST_D])
            weak_sections = [s for s, rate in section_success.items() if rate < 0.7]
            
            if len(weak_sections) >= 3:
                evidence.append(f"Test D shows systematic failures in sections: {', '.join(weak_sections)}")
                diagnosis_scores[DiagnosisType.SCOPE_MISMATCH] += 0.2
            elif "Recommendations" in weak_sections or "Next Steps" in weak_sections:
                evidence.append("Test D shows reasoning/synthesis sections failing, composer limitation")
                diagnosis_scores[DiagnosisType.COMPOSER_BOTTLENECK] += 0.2
        
        # Determine primary diagnosis
        max_score = max(diagnosis_scores.values())
        if max_score < 0.3:
            diagnosis_type = DiagnosisType.MIXED_ISSUES
            evidence.append("No single bottleneck identified, multiple issues present")
        else:
            diagnosis_type = max(diagnosis_scores.items(), key=lambda x: x[1])[0]
        
        # Generate top fixes based on diagnosis
        top_fixes = self._generate_fixes(diagnosis_type, test_summaries, evidence)
        
        # Create summary
        summary = self._generate_summary(diagnosis_type, test_summaries)
        
        return Diagnosis(
            diagnosis_type=diagnosis_type,
            confidence=min(0.9, max_score * 2),  # Scale confidence
            evidence=evidence,
            top_fixes=top_fixes[:3],  # Top 3 fixes
            summary=summary,
            test_results_summary=test_summaries
        )
    
    def _generate_fixes(
        self,
        diagnosis_type: DiagnosisType,
        test_summaries: Dict[str, Any],
        evidence: List[str]
    ) -> List[str]:
        """Generate actionable fixes based on diagnosis"""
        fixes = []
        
        if diagnosis_type == DiagnosisType.EXTRACTION_BOTTLENECK:
            fixes.extend([
                "Implement deterministic chunking with sentence-level provenance tracking",
                "Add role classification to extraction (evidence/insight/instruction/background)",
                "Increase extraction recall by lowering confidence thresholds and adding post-filtering",
                "Use structured extraction prompts with explicit citation requirements",
                "Add extraction validation step to ensure all key facts are captured"
            ])
        
        elif diagnosis_type == DiagnosisType.COMPOSER_BOTTLENECK:
            fixes.extend([
                "Add strict composition templates with required sections and citation rules",
                "Implement section-specific prompts optimized for each content type",
                "Add guardrails to prevent hallucination (require citations for all claims)",
                "Use chain-of-thought prompting for reasoning-heavy sections",
                "Implement composition validation to ensure structure compliance"
            ])
        
        elif diagnosis_type == DiagnosisType.SCOPE_MISMATCH:
            fixes.extend([
                "Redefine document scope and expected sections based on actual content",
                "Implement adaptive sectioning based on available substrate",
                "Add content-type detection to choose appropriate templates",
                "Allow flexible section inclusion based on substrate availability",
                "Create multiple document templates for different use cases"
            ])
        
        else:  # MIXED_ISSUES
            fixes.extend([
                "Start with extraction improvements (typically higher impact)",
                "Implement end-to-end quality metrics and monitoring",
                "Create feedback loop between composition and extraction",
                "Add integration tests for the full pipeline",
                "Consider complete pipeline redesign if issues persist"
            ])
        
        # Add specific fixes based on metrics
        test_a_metrics = test_summaries.get(TestType.TEST_A, {})
        if test_a_metrics.get("mean_provenance_coverage", 0) < 0.5:
            fixes.append("Urgently fix citation generation - over 50% of sentences lack citations")
        
        if test_a_metrics.get("mean_time_to_draft_ms", 0) > 300000:
            fixes.append("Optimize performance - current draft time exceeds 5 minutes")
        
        return fixes
    
    def _generate_summary(
        self,
        diagnosis_type: DiagnosisType,
        test_summaries: Dict[str, Any]
    ) -> str:
        """Generate human-readable summary"""
        
        if diagnosis_type == DiagnosisType.EXTRACTION_BOTTLENECK:
            return (
                "Substrate extraction is the primary bottleneck. The composer performs adequately "
                "when given quality substrate (Test B), but extraction from raw text is insufficient. "
                "Focus improvements on extraction coverage, role classification, and provenance tracking."
            )
        
        elif diagnosis_type == DiagnosisType.COMPOSER_BOTTLENECK:
            return (
                "Document composition is the primary bottleneck. Even with perfect substrate (Test B), "
                "the composer fails to generate quality artifacts. Issues include poor structure, "
                "missing citations, and inability to synthesize coherent narratives. "
                "Focus on composition templates, guardrails, and prompt engineering."
            )
        
        elif diagnosis_type == DiagnosisType.SCOPE_MISMATCH:
            return (
                "The expected document structure doesn't match available content. Tests show systematic "
                "failures in specific sections, indicating a mismatch between template requirements "
                "and actual substrate. Consider adaptive templates or scope redefinition."
            )
        
        else:
            return (
                "Multiple issues detected across the pipeline. Both extraction and composition show "
                "weaknesses, with no single bottleneck. A systematic improvement approach is needed, "
                "starting with extraction improvements followed by composition enhancements."
            )