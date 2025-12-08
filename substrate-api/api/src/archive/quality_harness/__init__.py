# Quality Isolation Harness Package
"""
Quality Isolation Harness for diagnosing substrate extraction vs composition bottlenecks.

This non-invasive QA mode runs controlled experiments to isolate quality issues.
"""

from .harness import QualityHarness
from .tests import TestA, TestB, TestC, TestD
from .metrics import MetricsComputer, Diagnosis

__all__ = ['QualityHarness', 'TestA', 'TestB', 'TestC', 'TestD', 'MetricsComputer', 'Diagnosis']