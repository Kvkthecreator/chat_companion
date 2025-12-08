"""
Metrics computation for quality harness
"""

import logging
from typing import Dict, List, Any, Optional
from statistics import mean, stdev

from .types import QualityMetrics, TestResult, TestType

logger = logging.getLogger(__name__)


class MetricsComputer:
    """Compute and aggregate quality metrics"""
    
    def __init__(self, config):
        self.config = config
    
    def compute_aggregate_metrics(
        self,
        test_results: List[TestResult]
    ) -> Dict[str, Any]:
        """Compute aggregate metrics across test results"""
        if not test_results:
            return {
                "mean_structure_score": 0.0,
                "mean_provenance_coverage": 0.0,
                "mean_citations_per_sentence": 0.0,
                "total_uncited_sentences": 0,
                "total_dropped_sentences": 0,
                "mean_time_to_draft_ms": 0,
                "success_rate": 0.0
            }
        
        # Extract metrics
        structure_scores = []
        provenance_coverages = []
        citations_per_sentence = []
        uncited_sentences = 0
        dropped_sentences = 0
        draft_times = []
        successful_runs = 0
        
        for result in test_results:
            if not result.errors:
                successful_runs += 1
                structure_scores.append(result.metrics.structure_score)
                provenance_coverages.append(result.metrics.provenance_coverage)
                citations_per_sentence.append(result.metrics.avg_citations_per_sentence)
                uncited_sentences += result.metrics.uncited_sentences_count
                dropped_sentences += result.metrics.dropped_sentences_due_to_no_citation
                draft_times.append(result.metrics.time_to_draft_ms)
        
        total_runs = len(test_results)
        success_rate = successful_runs / total_runs if total_runs > 0 else 0.0
        
        return {
            "mean_structure_score": mean(structure_scores) if structure_scores else 0.0,
            "std_structure_score": stdev(structure_scores) if len(structure_scores) > 1 else 0.0,
            "mean_provenance_coverage": mean(provenance_coverages) if provenance_coverages else 0.0,
            "std_provenance_coverage": stdev(provenance_coverages) if len(provenance_coverages) > 1 else 0.0,
            "mean_citations_per_sentence": mean(citations_per_sentence) if citations_per_sentence else 0.0,
            "total_uncited_sentences": uncited_sentences,
            "total_dropped_sentences": dropped_sentences,
            "mean_time_to_draft_ms": mean(draft_times) if draft_times else 0,
            "success_rate": success_rate,
            "total_runs": total_runs,
            "successful_runs": successful_runs
        }
    
    def compare_test_results(
        self,
        results_a: List[TestResult],
        results_b: List[TestResult]
    ) -> Dict[str, Any]:
        """Compare metrics between two sets of test results"""
        metrics_a = self.compute_aggregate_metrics(results_a)
        metrics_b = self.compute_aggregate_metrics(results_b)
        
        comparison = {
            "structure_score_delta": metrics_b["mean_structure_score"] - metrics_a["mean_structure_score"],
            "provenance_coverage_delta": metrics_b["mean_provenance_coverage"] - metrics_a["mean_provenance_coverage"],
            "citations_per_sentence_delta": metrics_b["mean_citations_per_sentence"] - metrics_a["mean_citations_per_sentence"],
            "uncited_sentences_delta": metrics_b["total_uncited_sentences"] - metrics_a["total_uncited_sentences"],
            "time_delta_ms": metrics_b["mean_time_to_draft_ms"] - metrics_a["mean_time_to_draft_ms"],
            "success_rate_delta": metrics_b["success_rate"] - metrics_a["success_rate"]
        }
        
        return comparison
    
    def identify_section_weaknesses(
        self,
        test_d_results: List[TestResult]
    ) -> Dict[str, float]:
        """Identify which sections consistently fail in Test D"""
        section_scores = {}
        section_counts = {}
        
        for result in test_d_results:
            if not result.errors:
                for section, present in result.metrics.required_sections_present.items():
                    if section not in section_scores:
                        section_scores[section] = 0
                        section_counts[section] = 0
                    
                    section_scores[section] += 1 if present else 0
                    section_counts[section] += 1
        
        # Calculate success rate per section
        section_success_rates = {}
        for section in section_scores:
            if section_counts[section] > 0:
                section_success_rates[section] = section_scores[section] / section_counts[section]
            else:
                section_success_rates[section] = 0.0
        
        return section_success_rates
    
    def check_thresholds(
        self,
        metrics: Dict[str, Any]
    ) -> Dict[str, bool]:
        """Check if metrics meet configured thresholds"""
        checks = {
            "structure_acceptable": metrics["mean_structure_score"] >= 0.8,
            "provenance_acceptable": metrics["mean_provenance_coverage"] >= self.config.min_provenance_coverage,
            "uncited_acceptable": metrics["total_uncited_sentences"] <= self.config.max_uncited_sentences * metrics["total_runs"],
            "time_acceptable": metrics["mean_time_to_draft_ms"] <= self.config.target_time_to_draft_ms,
            "success_rate_acceptable": metrics["success_rate"] >= 0.9
        }
        
        return checks