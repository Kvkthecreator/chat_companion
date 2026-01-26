"""Thread Templates API routes.

Provides endpoints for:
- Listing templates (for onboarding and UI)
- Getting a specific template
- Template-based thread creation
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.deps import get_db
from app.dependencies import get_current_user_id
from app.services.domain_classifier import DomainClassifier

router = APIRouter(prefix="/templates", tags=["Templates"])


# =============================================================================
# Response Models
# =============================================================================


class TemplateListItem(BaseModel):
    """Template info for lists/onboarding."""
    template_key: str
    display_name: str
    domain: str
    icon: str
    has_phases: bool


class TemplateDetail(BaseModel):
    """Full template details."""
    id: str
    template_key: str
    display_name: str
    domain: str
    description: Optional[str]
    trigger_phrases: List[str]
    has_phases: bool
    phases: Optional[List[str]]
    follow_up_prompts: Dict[str, Any]
    typical_duration: Optional[str]
    default_follow_up_days: int


class ClassifyRequest(BaseModel):
    """Request to classify a situation."""
    text: str


class ClassifyResponse(BaseModel):
    """Classification result."""
    template_key: Optional[str]
    domain: str
    confidence: float
    summary: str
    key_entities: List[str]
    phase_hint: Optional[str]


# =============================================================================
# Endpoints
# =============================================================================


@router.get("", response_model=List[TemplateListItem])
async def list_templates(
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """List all active templates for onboarding/UI.

    Returns simplified template info sorted by display order.
    Excludes the 'open' catch-all template.
    """
    classifier = DomainClassifier(db)
    templates = await classifier.get_templates_for_onboarding()

    return [
        TemplateListItem(
            template_key=t["template_key"],
            display_name=t["display_name"],
            domain=t["domain"],
            icon=t["icon"],
            has_phases=t["has_phases"],
        )
        for t in templates
    ]


@router.get("/{template_key}", response_model=TemplateDetail)
async def get_template(
    template_key: str,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Get full details for a specific template."""
    classifier = DomainClassifier(db)
    template = await classifier.get_template_by_key(template_key)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{template_key}' not found",
        )

    from app.models.domain import DOMAIN_ICONS

    return TemplateDetail(
        id=str(template.id),
        template_key=template.template_key,
        display_name=template.display_name,
        domain=template.domain.value,
        description=template.description,
        trigger_phrases=template.trigger_phrases,
        has_phases=template.has_phases,
        phases=template.phases,
        follow_up_prompts={
            "initial": template.follow_up_prompts.initial,
            "check_in": template.follow_up_prompts.check_in,
            "phase_specific": template.follow_up_prompts.phase_specific,
        },
        typical_duration=template.typical_duration,
        default_follow_up_days=template.default_follow_up_days,
    )


@router.post("/classify", response_model=ClassifyResponse)
async def classify_situation(
    request: ClassifyRequest,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Classify free-text situation into a domain and template.

    Uses LLM to match user input against available templates.
    Returns the best match with confidence score and extracted details.
    """
    classifier = DomainClassifier(db)
    result = await classifier.classify_situation(request.text)

    return ClassifyResponse(
        template_key=result.template_key,
        domain=result.domain.value,
        confidence=result.confidence,
        summary=result.extracted_details.summary,
        key_entities=result.extracted_details.key_entities,
        phase_hint=result.extracted_details.phase_hint,
    )


@router.get("/{template_key}/follow-up")
async def get_follow_up_prompt(
    template_key: str,
    phase: Optional[str] = None,
    prompt_type: str = "check_in",
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Get the appropriate follow-up prompt for a template.

    Args:
        template_key: The template's key
        phase: Current phase (optional, for phased templates)
        prompt_type: "initial" or "check_in"

    Returns:
        The follow-up prompt string
    """
    classifier = DomainClassifier(db)
    prompt = await classifier.get_follow_up_prompt(template_key, phase, prompt_type)

    return {"prompt": prompt, "template_key": template_key, "phase": phase}
