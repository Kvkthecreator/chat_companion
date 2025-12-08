"""
Substrate Equality Engine - YARNNN Canon v1.4.0 Compliant
Ensures all substrate types are treated as peers per Sacred Principle #2
"""
# V3.0 DEPRECATION NOTICE:
# This file contains references to context_items table which was merged into blocks table.
# Entity blocks are now identified by semantic_type='entity'.
# This file is legacy/supporting code - update if actively maintained.


from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID
from enum import Enum

logger = logging.getLogger("uvicorn.error")


class SubstrateType(Enum):
    """Canonical substrate types as defined in YARNNN Canon v1.4.0"""
    RAW_DUMP = "dump"
    CONTEXT_BLOCK = "block"
    CONTEXT_ITEM = "context_item"
    REFLECTION = "reflection"
    TIMELINE_EVENT = "timeline_event"


class SubstrateReference:
    """Uniform substrate reference for equal treatment"""
    
    def __init__(
        self,
        substrate_id: UUID,
        substrate_type: SubstrateType,
        content: str,
        title: Optional[str] = None,
        relevance_score: float = 0.0,
        context_alignment: float = 0.0,
        composition_value: float = 0.0,
        discovery_reasoning: str = "",
        contributing_contexts: Optional[List[UUID]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.substrate_id = substrate_id
        self.substrate_type = substrate_type
        self.content = content
        self.title = title
        self.relevance_score = relevance_score
        self.context_alignment = context_alignment
        self.composition_value = composition_value
        self.discovery_reasoning = discovery_reasoning
        self.contributing_contexts = contributing_contexts or []
        self.metadata = metadata or {}
        
        # Canon compliance: All substrates get equal weight by default
        self.weight = 1.0
        self.priority = "EQUAL_PRIORITY"
        self.access = "UNIFORM_ACCESS"


class SubstrateEqualityEngine:
    """
    Implementation of Substrate Equality Engine as per YARNNN Canon Gap Mitigation Plan
    Ensures all substrate types are treated as peers with no type-based discrimination
    """

    @classmethod
    def treatAsPeers(cls, substrates: List[SubstrateReference]) -> List[SubstrateReference]:
        """
        Ensure substrate references are treated as peers with equal priority and access
        Implementation of mitigation plan specification
        """
        processed_substrates = []
        
        for substrate in substrates:
            # Canon enforcement: No type-based discrimination
            processed_substrate = SubstrateReference(
                substrate_id=substrate.substrate_id,
                substrate_type=substrate.substrate_type,
                content=substrate.content,
                title=substrate.title,
                relevance_score=substrate.relevance_score,
                context_alignment=substrate.context_alignment,
                composition_value=substrate.composition_value,
                discovery_reasoning=substrate.discovery_reasoning,
                contributing_contexts=substrate.contributing_contexts,
                metadata=substrate.metadata
            )
            
            # Sacred Principle #2 enforcement: All substrates are peers
            processed_substrate.weight = substrate.weight  # No type-based modification
            processed_substrate.priority = "EQUAL_PRIORITY"
            processed_substrate.access = "UNIFORM_ACCESS"
            
            processed_substrates.append(processed_substrate)
        
        return processed_substrates

    @classmethod
    def discoverUniformly(
        cls,
        basket_id: UUID,
        workspace_id: str,
        composition_context: Dict[str, Any],
        max_results: int = 20,
        substrate_types: Optional[List[SubstrateType]] = None
    ) -> List[SubstrateReference]:
        """
        Discover substrates uniformly across all types without bias
        Replaces the block-only discovery logic
        """
        if substrate_types is None:
            substrate_types = list(SubstrateType)
            
        discovered_substrates = []
        results_per_type = max(1, max_results // len(substrate_types))
        
        for substrate_type in substrate_types:
            type_substrates = cls._discover_by_type(
                substrate_type=substrate_type,
                basket_id=basket_id,
                workspace_id=workspace_id,
                composition_context=composition_context,
                max_results=results_per_type
            )
            discovered_substrates.extend(type_substrates)
        
        # Sort by relevance score, maintaining substrate equality
        discovered_substrates.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Limit total results while maintaining type diversity
        return cls._ensure_type_diversity(discovered_substrates, max_results)

    @classmethod
    def _discover_by_type(
        cls,
        substrate_type: SubstrateType,
        basket_id: UUID,
        workspace_id: str,
        composition_context: Dict[str, Any],
        max_results: int
    ) -> List[SubstrateReference]:
        """Discover substrates of a specific type uniformly"""
        
        # This would integrate with the actual discovery services
        # For now, returning mock data to demonstrate the interface
        
        mock_substrates = []
        for i in range(min(max_results, 3)):  # Mock 3 results per type
            mock_substrates.append(SubstrateReference(
                substrate_id=UUID(f"00000000-0000-0000-0000-{substrate_type.value[:8]}{i:03d}"),
                substrate_type=substrate_type,
                content=f"Mock {substrate_type.value} content {i+1}",
                title=f"Mock {substrate_type.value} {i+1}" if substrate_type != SubstrateType.RAW_DUMP else None,
                relevance_score=0.8 - (i * 0.1),
                context_alignment=0.7 - (i * 0.1),
                composition_value=0.8 - (i * 0.1),
                discovery_reasoning=f"Mock discovery reasoning for {substrate_type.value}"
            ))
        
        return mock_substrates

    @classmethod
    def _ensure_type_diversity(
        cls,
        substrates: List[SubstrateReference],
        max_results: int
    ) -> List[SubstrateReference]:
        """Ensure diverse substrate types in final results"""
        
        if len(substrates) <= max_results:
            return substrates
            
        # Group by type
        type_groups = {}
        for substrate in substrates:
            substrate_type = substrate.substrate_type
            if substrate_type not in type_groups:
                type_groups[substrate_type] = []
            type_groups[substrate_type].append(substrate)
        
        # Distribute slots fairly across types
        result = []
        slots_per_type = max(1, max_results // len(type_groups))
        remaining_slots = max_results
        
        for substrate_type, group in type_groups.items():
            take_count = min(slots_per_type, len(group), remaining_slots)
            result.extend(group[:take_count])
            remaining_slots -= take_count
            
            if remaining_slots == 0:
                break
        
        return result[:max_results]

    @classmethod
    def organizeEquallyBySections(
        cls,
        substrates: List[SubstrateReference],
        composition_context: Dict[str, Any]
    ) -> Dict[str, List[SubstrateReference]]:
        """
        Organize substrates by document sections treating all types equally
        Replaces the block-only organization logic
        """
        
        intent = composition_context.get("detected_intent", "general_composition")
        
        # Define section structures by intent (same as original)
        section_structures = {
            "strategic_analysis": ["introduction", "analysis", "opportunities", "recommendations"],
            "technical_guide": ["overview", "prerequisites", "implementation", "examples"],
            "executive_summary": ["overview", "key_findings", "recommendations"],
            "action_plan": ["objectives", "action_items", "timeline", "resources"],
            "research_report": ["background", "methodology", "findings", "conclusions"]
        }
        
        sections = section_structures.get(intent, ["overview", "main_content", "conclusion"])
        organized = {section: [] for section in sections}
        
        # Canon-compliant organization: All substrate types considered equally
        for substrate in substrates:
            section_placement = cls._determine_section_placement(
                substrate=substrate,
                available_sections=sections,
                composition_context=composition_context
            )
            organized[section_placement].append(substrate)
        
        return organized

    @classmethod
    def _determine_section_placement(
        cls,
        substrate: SubstrateReference,
        available_sections: List[str],
        composition_context: Dict[str, Any]
    ) -> str:
        """Determine section placement for any substrate type equally"""
        
        # Canon compliance: Section placement logic treats all substrate types equally
        content_lower = substrate.content.lower()
        
        # Intent-based placement (works for all substrate types)
        if "objective" in content_lower or "goal" in content_lower:
            if "objectives" in available_sections:
                return "objectives"
            elif "overview" in available_sections:
                return "overview"
        
        if "analysis" in content_lower or "insight" in content_lower:
            if "analysis" in available_sections:
                return "analysis"
            elif "findings" in available_sections:
                return "findings"
        
        if "constraint" in content_lower or "limitation" in content_lower:
            if "prerequisites" in available_sections:
                return "prerequisites"
            elif "resources" in available_sections:
                return "resources"
        
        # Default to main content section (treats all types equally)
        main_section = available_sections[1] if len(available_sections) > 1 else available_sections[0]
        return main_section

    @classmethod
    def calculateEqualStats(
        cls,
        substrates: List[SubstrateReference]
    ) -> Dict[str, Union[int, float]]:
        """Calculate composition statistics treating all substrate types equally"""
        
        stats = {
            "total_substrates": len(substrates),
            "blocks_count": 0,
            "dumps_count": 0,
            "context_items_count": 0,
            "reflections_count": 0,
            "timeline_events_count": 0,
            "average_relevance": 0.0,
            "type_diversity_score": 0.0
        }
        
        if not substrates:
            return stats
        
        # Count by type (equal treatment)
        type_counts = {}
        total_relevance = 0.0
        
        for substrate in substrates:
            substrate_type = substrate.substrate_type.value
            type_counts[substrate_type] = type_counts.get(substrate_type, 0) + 1
            total_relevance += substrate.relevance_score
            
            # Update specific counters
            if substrate_type == "block":
                stats["blocks_count"] += 1
            elif substrate_type == "dump":
                stats["dumps_count"] += 1
            elif substrate_type == "context_item":
                stats["context_items_count"] += 1
            elif substrate_type == "reflection":
                stats["reflections_count"] += 1
            elif substrate_type == "timeline_event":
                stats["timeline_events_count"] += 1
        
        # Calculate equality metrics
        stats["average_relevance"] = total_relevance / len(substrates)
        
        # Type diversity score: Higher when types are more evenly distributed
        num_unique_types = len(type_counts)
        ideal_per_type = len(substrates) / 5  # 5 canonical substrate types
        diversity_penalties = []
        
        for count in type_counts.values():
            penalty = abs(count - ideal_per_type) / ideal_per_type if ideal_per_type > 0 else 0
            diversity_penalties.append(penalty)
        
        avg_penalty = sum(diversity_penalties) / len(diversity_penalties) if diversity_penalties else 0
        stats["type_diversity_score"] = max(0.0, 1.0 - avg_penalty)
        
        return stats

    @classmethod
    def validateSubstrateEquality(
        cls,
        substrates: List[SubstrateReference]
    ) -> Dict[str, Any]:
        """Validate that substrate equality principles are maintained"""
        
        validation_result = {
            "is_compliant": True,
            "violations": [],
            "equality_score": 1.0,
            "recommendations": []
        }
        
        if not substrates:
            return validation_result
        
        # Check for type bias
        type_counts = {}
        for substrate in substrates:
            substrate_type = substrate.substrate_type.value
            type_counts[substrate_type] = type_counts.get(substrate_type, 0) + 1
        
        # Check for significant imbalance (Canon violation)
        total_substrates = len(substrates)
        expected_per_type = total_substrates / 5  # 5 canonical types
        
        for substrate_type, count in type_counts.items():
            ratio = count / total_substrates
            if ratio > 0.7:  # More than 70% of one type indicates bias
                validation_result["is_compliant"] = False
                validation_result["violations"].append({
                    "type": "substrate_type_bias",
                    "substrate_type": substrate_type,
                    "ratio": ratio,
                    "description": f"Substrate type '{substrate_type}' represents {ratio:.1%} of composition, indicating potential bias"
                })
        
        # Check for weight equality
        weights = [s.weight for s in substrates]
        if len(set(weights)) > 1:  # Different weights detected
            avg_weight = sum(weights) / len(weights)
            for substrate in substrates:
                if abs(substrate.weight - avg_weight) > 0.3:  # Significant weight difference
                    validation_result["violations"].append({
                        "type": "weight_inequality",
                        "substrate_id": str(substrate.substrate_id),
                        "weight": substrate.weight,
                        "average_weight": avg_weight,
                        "description": f"Substrate {substrate.substrate_id} has weight {substrate.weight:.2f}, significantly different from average {avg_weight:.2f}"
                    })
        
        # Calculate overall equality score
        num_violations = len(validation_result["violations"])
        validation_result["equality_score"] = max(0.0, 1.0 - (num_violations * 0.2))
        
        # Generate recommendations
        if num_violations > 0:
            validation_result["is_compliant"] = False
            validation_result["recommendations"] = [
                "Ensure substrate discovery includes all 5 canonical types equally",
                "Use SubstrateEqualityEngine.discoverUniformly() for canon-compliant discovery",
                "Apply equal weighting to all substrate types during composition",
                "Validate composition using SubstrateEqualityEngine.validateSubstrateEquality()"
            ]
        
        return validation_result