"""
Canonical Pipeline Agents - YARNNN Canon v3.1 Compliant

Each agent maps to exactly one pipeline (P0, P1, P3, P4) with strict boundary enforcement.
This eliminates canon violations and ensures proper substrate processing.

Pipeline Agents:
- P0CaptureAgent: Only writes raw_dumps, never interprets
- P1SubstrateAgent: Creates blocks with semantic intelligence (duplicate detection via embeddings)
- P3ReflectionAgent: Read-only pattern analysis, generates insights
- P4PresentationAgent: Composes documents from substrate + insights

Note: P2 (Graph/Relationships) removed in v3.1 - replaced by Neural Map (client-side visualization)
"""

from .capture_agent import P0CaptureAgent
from .improved_substrate_agent import ImprovedP1SubstrateAgent
from .reflection_agent import P3ReflectionAgent
from .presentation_agent import P4PresentationAgent

# Canonical P1 agent (quality-focused)
P1SubstrateAgent = ImprovedP1SubstrateAgent

__all__ = [
    "P0CaptureAgent",
    "P1SubstrateAgent",
    "P3ReflectionAgent",
    "P4PresentationAgent"
]