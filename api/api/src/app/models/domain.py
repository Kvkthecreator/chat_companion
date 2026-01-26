"""Domain layer models for thread templates and classification.

This module defines the data structures for the domain layer:
- ThreadTemplate: Schema for thread templates (stored in thread_templates table)
- DomainPreferences: User's domain preferences (stored in users.domain_preferences)
- ClassificationResult: Result of classifying user input into a domain/template
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID


class Domain(str, Enum):
    """High-level domains for life transitions."""
    CAREER = "career"
    LOCATION = "location"
    RELATIONSHIPS = "relationships"
    HEALTH = "health"
    CREATIVE = "creative"
    LIFE_STAGE = "life_stage"
    PERSONAL = "personal"


DOMAIN_ICONS = {
    Domain.CAREER: "💼",
    Domain.LOCATION: "📍",
    Domain.RELATIONSHIPS: "💕",
    Domain.HEALTH: "🏥",
    Domain.CREATIVE: "🚀",
    Domain.LIFE_STAGE: "🎓",
    Domain.PERSONAL: "💭",
}

DOMAIN_LABELS = {
    Domain.CAREER: "Career",
    Domain.LOCATION: "Location",
    Domain.RELATIONSHIPS: "Relationships",
    Domain.HEALTH: "Health",
    Domain.CREATIVE: "Creative",
    Domain.LIFE_STAGE: "Life Stage",
    Domain.PERSONAL: "Personal",
}


@dataclass
class FollowUpPrompts:
    """Follow-up prompts for a thread template."""
    initial: str
    check_in: str
    phase_specific: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FollowUpPrompts":
        return cls(
            initial=data.get("initial", "Tell me more about what's going on."),
            check_in=data.get("check_in", "How are things going?"),
            phase_specific=data.get("phase_specific", {}),
        )

    def get_prompt_for_phase(self, phase: Optional[str]) -> str:
        """Get the appropriate follow-up prompt for a phase."""
        if phase and phase in self.phase_specific:
            return self.phase_specific[phase]
        return self.check_in


@dataclass
class ThreadTemplate:
    """A thread template defining a type of life transition.

    Templates are stored in the thread_templates table and used for:
    1. Onboarding (user selects from options)
    2. Classification (LLM matches input to template)
    3. Follow-up prompts (domain-specific language)
    """
    id: UUID
    domain: Domain
    template_key: str
    display_name: str
    trigger_phrases: List[str]
    description: Optional[str]
    has_phases: bool
    phases: Optional[List[str]]
    follow_up_prompts: FollowUpPrompts
    typical_duration: Optional[str]
    default_follow_up_days: int
    is_active: bool
    display_order: int

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> "ThreadTemplate":
        """Create from database row."""
        return cls(
            id=row["id"],
            domain=Domain(row["domain"]),
            template_key=row["template_key"],
            display_name=row["display_name"],
            trigger_phrases=row.get("trigger_phrases") or [],
            description=row.get("description"),
            has_phases=row.get("has_phases", False),
            phases=row.get("phases"),
            follow_up_prompts=FollowUpPrompts.from_dict(row.get("follow_up_prompts", {})),
            typical_duration=row.get("typical_duration"),
            default_follow_up_days=row.get("default_follow_up_days", 3),
            is_active=row.get("is_active", True),
            display_order=row.get("display_order", 99),
        )


@dataclass
class DomainPreferences:
    """User's domain preferences from onboarding.

    Stored in users.domain_preferences JSONB column.
    """
    primary_domains: List[str] = field(default_factory=list)
    domain_weights: Dict[str, float] = field(default_factory=dict)
    onboarding_selections: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "DomainPreferences":
        if not data:
            return cls()
        return cls(
            primary_domains=data.get("primary_domains", []),
            domain_weights=data.get("domain_weights", {}),
            onboarding_selections=data.get("onboarding_selections", []),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary_domains": self.primary_domains,
            "domain_weights": self.domain_weights,
            "onboarding_selections": self.onboarding_selections,
        }

    def get_weight(self, domain: str) -> float:
        """Get priority weight for a domain. Primary domains get 1.5."""
        return self.domain_weights.get(domain, 1.0)

    def is_primary(self, domain: str) -> bool:
        """Check if domain is a primary domain."""
        return domain in self.primary_domains


@dataclass
class ExtractedDetails:
    """Details extracted from user input during classification."""
    summary: str
    key_entities: List[str] = field(default_factory=list)
    phase_hint: Optional[str] = None


@dataclass
class ClassificationResult:
    """Result of classifying user input into a domain/template."""
    template_key: Optional[str]
    domain: Domain
    confidence: float
    extracted_details: ExtractedDetails

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ClassificationResult":
        """Parse LLM response into ClassificationResult."""
        details_data = data.get("extracted_details", {})
        return cls(
            template_key=data.get("template_key"),
            domain=Domain(data.get("domain", "personal")),
            confidence=data.get("confidence", 0.5),
            extracted_details=ExtractedDetails(
                summary=details_data.get("summary", ""),
                key_entities=details_data.get("key_entities", []),
                phase_hint=details_data.get("phase_hint"),
            ),
        )

    @property
    def is_matched(self) -> bool:
        """True if a template was matched with reasonable confidence."""
        return self.template_key is not None and self.confidence >= 0.6


@dataclass
class DomainSelection:
    """A domain selection from onboarding."""
    template_key: str
    details: str
    is_primary: bool = False


@dataclass
class TypedThread:
    """A thread with domain layer fields.

    This extends the basic thread concept with domain classification.
    Stored in user_context with category='thread' and domain layer fields.
    """
    id: UUID
    user_id: UUID
    topic: str
    summary: str
    status: str
    domain: Optional[Domain]
    template_id: Optional[UUID]
    phase: Optional[str]
    priority_weight: float
    follow_up_date: Optional[str]
    key_details: List[str] = field(default_factory=list)

    @classmethod
    def from_context_row(cls, row: Dict[str, Any], value_data: Dict[str, Any]) -> "TypedThread":
        """Create from user_context row with parsed value JSON."""
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            topic=row["key"],
            summary=value_data.get("summary", ""),
            status=value_data.get("status", "active"),
            domain=Domain(row["domain"]) if row.get("domain") else None,
            template_id=row.get("template_id"),
            phase=row.get("phase"),
            priority_weight=float(row.get("priority_weight", 1.0)),
            follow_up_date=value_data.get("follow_up_date"),
            key_details=value_data.get("key_details", []),
        )
