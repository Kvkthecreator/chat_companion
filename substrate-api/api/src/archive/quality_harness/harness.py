"""
Main Quality Isolation Harness orchestrator
"""

import os
import json
import asyncio
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from .types import (
    TestType, TestInput, TestResult, Diagnosis, DiagnosisType,
    HarnessConfig, QualityMetrics
)
from .tests import TestA, TestB, TestC, TestD
from .metrics import MetricsComputer
from .diagnosis_engine import DiagnosisEngine

logger = logging.getLogger(__name__)


class QualityHarness:
    """
    Quality Isolation Harness for diagnosing substrate vs composition issues.
    
    Non-invasive QA mode that runs controlled experiments.
    """
    
    def __init__(self, config: Optional[HarnessConfig] = None):
        self.config = config or self._load_config()
        self.metrics_computer = MetricsComputer(self.config)
        self.diagnosis_engine = DiagnosisEngine()
        
        # Initialize test runners
        self.test_runners = {
            TestType.TEST_A: TestA(self.config),
            TestType.TEST_B: TestB(self.config),
            TestType.TEST_C: TestC(self.config),
            TestType.TEST_D: TestD(self.config)
        }
        
        # Create output directory
        Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)
    
    def _load_config(self) -> HarnessConfig:
        """Load configuration from environment or defaults"""
        enabled = os.getenv("QUALITY_HARNESS_ENABLED", "false").lower() == "true"
        
        config_path = os.getenv("QUALITY_HARNESS_CONFIG")
        if config_path and Path(config_path).exists():
            with open(config_path) as f:
                config_data = json.load(f)
                return HarnessConfig(enabled=enabled, **config_data)
        
        return HarnessConfig(enabled=enabled)
    
    async def run_test(self, test_type: TestType, inputs: List[TestInput]) -> List[TestResult]:
        """Run a specific test on given inputs"""
        if not self.config.enabled:
            logger.warning("Quality harness is disabled. Set QUALITY_HARNESS_ENABLED=true")
            return []
        
        logger.info(f"Running {test_type} on {len(inputs)} inputs")
        test_runner = self.test_runners[test_type]
        
        results = []
        for test_input in inputs:
            try:
                result = await test_runner.run(test_input)
                results.append(result)
            except Exception as e:
                logger.error(f"Test {test_type} failed for {test_input.input_id}: {e}")
                # Create error result
                results.append(TestResult(
                    test_type=test_type,
                    input_id=test_input.input_id,
                    metrics=QualityMetrics(
                        structure_score=0.0,
                        provenance_coverage=0.0,
                        avg_citations_per_sentence=0.0,
                        uncited_sentences_count=0,
                        time_to_draft_ms=0,
                        required_sections_present={},
                        total_sentences=0,
                        total_citations=0
                    ),
                    artifact="",
                    citations=[],
                    execution_time_ms=0,
                    errors=[str(e)]
                ))
        
        return results
    
    async def run_all_tests(self, inputs: Optional[List[TestInput]] = None) -> Dict[TestType, List[TestResult]]:
        """Run all tests on the golden set or provided inputs"""
        if inputs is None:
            inputs = await self._load_golden_set()
        
        results = {}
        for test_type in TestType:
            results[test_type] = await self.run_test(test_type, inputs)
        
        return results
    
    async def diagnose(self, test_results: Dict[TestType, List[TestResult]]) -> Diagnosis:
        """Generate diagnosis from test results"""
        return await self.diagnosis_engine.diagnose(test_results, self.config)
    
    async def run_full_harness(self) -> Tuple[Dict[TestType, List[TestResult]], Diagnosis]:
        """Run complete harness: all tests + diagnosis"""
        if not self.config.enabled:
            raise RuntimeError("Quality harness is disabled. Set QUALITY_HARNESS_ENABLED=true")
        
        logger.info("Starting full quality harness run")
        start_time = datetime.utcnow()
        
        # Load golden set
        inputs = await self._load_golden_set()
        logger.info(f"Loaded {len(inputs)} golden inputs")
        
        # Run all tests
        test_results = await self.run_all_tests(inputs)
        
        # Save individual results
        await self._save_test_results(test_results)
        
        # Generate diagnosis
        diagnosis = await self.diagnose(test_results)
        
        # Save diagnosis
        await self._save_diagnosis(diagnosis)
        
        # Print summary
        elapsed_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        logger.info(f"Quality harness completed in {elapsed_ms}ms")
        self._print_summary(diagnosis)
        
        return test_results, diagnosis
    
    async def _load_golden_set(self) -> List[TestInput]:
        """Load golden set inputs"""
        golden_path = Path(self.config.golden_set_path)
        
        if not golden_path.exists():
            # Create placeholder golden set
            logger.warning(f"Golden set not found at {golden_path}. Creating placeholder.")
            placeholder_inputs = [
                TestInput(
                    input_id="placeholder_1",
                    raw_text="TODO: Add real golden input text here",
                    metadata={"note": "Placeholder - replace with real data"}
                )
            ]
            
            golden_path.parent.mkdir(parents=True, exist_ok=True)
            with open(golden_path, 'w') as f:
                json.dump([inp.dict() for inp in placeholder_inputs], f, indent=2)
            
            return placeholder_inputs
        
        with open(golden_path) as f:
            data = json.load(f)
            return [TestInput(**item) for item in data]
    
    async def _save_test_results(self, results: Dict[TestType, List[TestResult]]):
        """Save test results to output directory"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        for test_type, test_results in results.items():
            output_path = Path(self.config.output_dir) / f"{test_type}_{timestamp}.json"
            with open(output_path, 'w') as f:
                json.dump(
                    [result.dict() for result in test_results],
                    f,
                    indent=2,
                    default=str
                )
            logger.info(f"Saved {test_type} results to {output_path}")
    
    async def _save_diagnosis(self, diagnosis: Diagnosis):
        """Save diagnosis to output directory"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_path = Path(self.config.output_dir) / f"diagnosis_{timestamp}.json"
        
        with open(output_path, 'w') as f:
            json.dump(diagnosis.dict(), f, indent=2, default=str)
        
        logger.info(f"Saved diagnosis to {output_path}")
    
    def _print_summary(self, diagnosis: Diagnosis):
        """Print human-readable summary"""
        print("\n" + "="*60)
        print("QUALITY ISOLATION HARNESS - DIAGNOSIS")
        print("="*60)
        print(f"\nDiagnosis: {diagnosis.diagnosis_type.value}")
        print(f"Confidence: {diagnosis.confidence:.1%}")
        print(f"\nSummary: {diagnosis.summary}")
        
        print("\nEvidence:")
        for i, evidence in enumerate(diagnosis.evidence, 1):
            print(f"  {i}. {evidence}")
        
        print("\nTop 3 Fixes:")
        for i, fix in enumerate(diagnosis.top_fixes[:3], 1):
            print(f"  {i}. {fix}")
        
        print("\n" + "="*60)