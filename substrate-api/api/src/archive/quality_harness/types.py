"""
Type definitions for Quality Isolation Harness
"""

from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime


class TestType(str, Enum):
    """Test types for quality isolation"""
    TEST_A = "upper_bound_raw"
    TEST_B = "oracle_substrate"
    TEST_C = "no_new_facts"
    TEST_D = "section_ablation"


class CitationSpan(BaseModel):
    """Citation span linking to source text"""
    span_id: str  # e.g., "S12"
    source_start: int
    source_end: int
    text: str


class QualityMetrics(BaseModel):
    """Standardized quality metrics"""
    structure_score: float = Field(ge=0.0, le=1.0)
    provenance_coverage: float = Field(ge=0.0, le=1.0)
    avg_citations_per_sentence: float
    uncited_sentences_count: int
    dropped_sentences_due_to_no_citation: int = 0
    time_to_draft_ms: int
    estimated_edit_distance: Optional[int] = None
    
    # Additional diagnostic metrics
    required_sections_present: Dict[str, bool]
    total_sentences: int
    total_citations: int


class TestInput(BaseModel):
    """Input for quality tests"""
    input_id: str
    raw_text: str
    oracle_blocks: Optional[List[Dict[str, Any]]] = None  # For Test B
    reference_brief: Optional[str] = None  # For edit distance
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TestResult(BaseModel):
    """Result from a single test run"""
    test_type: TestType
    input_id: str
    metrics: QualityMetrics
    artifact: str  # Generated document/composition
    citations: List[CitationSpan]
    execution_time_ms: int
    errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DiagnosisType(str, Enum):
    """Types of diagnosis conclusions"""
    COMPOSER_BOTTLENECK = "composer_bottleneck"
    EXTRACTION_BOTTLENECK = "extraction_bottleneck"
    SCOPE_MISMATCH = "scope_mismatch"
    MIXED_ISSUES = "mixed_issues"


class Diagnosis(BaseModel):
    """Diagnosis result with evidence and fixes"""
    diagnosis_type: DiagnosisType
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: List[str]
    top_fixes: List[str]  # Top 3 actionable fixes
    summary: str
    test_results_summary: Dict[TestType, Dict[str, Any]]
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class HarnessConfig(BaseModel):
    """Configuration for quality harness"""
    enabled: bool = False
    golden_set_path: str = "quality_harness/golden_set.json"
    output_dir: str = "quality_harness/outputs"
    
    # Thresholds
    required_sections: List[str] = Field(default_factory=lambda: [
        "Title", "TL;DR", "Context", "Findings", "Recommendations", "Next Steps"
    ])
    min_provenance_coverage: float = 0.8
    max_uncited_sentences: int = 2
    target_time_to_draft_ms: int = 180000
    
    # Test-specific configs
    max_blocks_per_test: int = 10
    citation_format: str = "[S{id}]"  # Format for inline citations
    llm_temperature: float = 0.0  # Deterministic for tests