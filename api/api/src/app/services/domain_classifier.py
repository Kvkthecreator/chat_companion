"""Domain Classification Service.

Classifies user input into domains and templates for the domain layer.
Uses LLM to match free-text situations to thread templates.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.models.domain import (
    ClassificationResult,
    Domain,
    DomainPreferences,
    ExtractedDetails,
    ThreadTemplate,
)
from app.services.llm import LLMService

log = logging.getLogger(__name__)


CLASSIFICATION_PROMPT = """You are classifying a user's life situation into predefined categories.

The user said: "{user_input}"

Available templates (pick the best match):
{templates_formatted}

Return a JSON object with:
{{
    "template_key": "the template_key that best matches, or null if no good match",
    "domain": "the domain (career, location, relationships, health, creative, life_stage, or personal)",
    "confidence": 0.0-1.0 (how confident you are in the match),
    "extracted_details": {{
        "summary": "one sentence summary of their situation",
        "key_entities": ["specific names, dates, places, companies mentioned"],
        "phase_hint": "if the template has phases, which phase are they likely in (or null)"
    }}
}}

Guidelines:
- Match to a template if there's a clear fit (confidence >= 0.7)
- If unclear, set template_key to null and domain to "personal"
- Extract specific details even if no template matches
- Phase hints should match the template's defined phases

Return ONLY valid JSON, no markdown or explanation."""


class DomainClassifier:
    """Classifies user situations into domains and templates."""

    def __init__(self, db, llm_service: Optional[LLMService] = None):
        self.db = db
        self.llm = llm_service or LLMService()

    async def get_templates(self, active_only: bool = True) -> List[ThreadTemplate]:
        """Fetch all thread templates from database."""
        query = """
            SELECT * FROM thread_templates
            WHERE is_active = :active OR :active = FALSE
            ORDER BY display_order
        """
        rows = await self.db.fetch_all(query, {"active": active_only})
        return [ThreadTemplate.from_row(dict(row)) for row in rows]

    async def get_template_by_key(self, template_key: str) -> Optional[ThreadTemplate]:
        """Fetch a specific template by key."""
        query = "SELECT * FROM thread_templates WHERE template_key = :key"
        row = await self.db.fetch_one(query, {"key": template_key})
        return ThreadTemplate.from_row(dict(row)) if row else None

    async def get_templates_for_onboarding(self) -> List[Dict[str, Any]]:
        """Get templates formatted for onboarding UI.

        Returns simplified template info for display:
        - template_key, display_name, domain, icon
        - Excludes 'open' template (that's the "Something else" option)
        """
        templates = await self.get_templates()
        from app.models.domain import DOMAIN_ICONS

        return [
            {
                "template_key": t.template_key,
                "display_name": t.display_name,
                "domain": t.domain.value,
                "icon": DOMAIN_ICONS.get(t.domain, "💭"),
                "has_phases": t.has_phases,
            }
            for t in templates
            if t.template_key != "open"  # Exclude catch-all
        ]

    def _format_templates_for_prompt(self, templates: List[ThreadTemplate]) -> str:
        """Format templates for LLM prompt."""
        lines = []
        for t in templates:
            phases_str = f" Phases: {', '.join(t.phases)}" if t.phases else ""
            lines.append(
                f"- {t.template_key} ({t.domain.value}): {t.display_name}. "
                f"Triggers: {', '.join(t.trigger_phrases[:5])}.{phases_str}"
            )
        return "\n".join(lines)

    async def classify_situation(
        self,
        user_input: str,
        templates: Optional[List[ThreadTemplate]] = None,
    ) -> ClassificationResult:
        """Classify free-text situation into domain and template.

        Args:
            user_input: The user's description of their situation
            templates: Optional pre-fetched templates (fetches if not provided)

        Returns:
            ClassificationResult with template_key, domain, confidence, and details
        """
        if not templates:
            templates = await self.get_templates()

        prompt = CLASSIFICATION_PROMPT.format(
            user_input=user_input,
            templates_formatted=self._format_templates_for_prompt(templates),
        )

        try:
            response = await self.llm.generate(
                prompt=prompt,
                system_prompt="You are a classification assistant. Return only valid JSON.",
                max_tokens=500,
            )

            # Parse JSON response
            result_data = json.loads(response.strip())
            return ClassificationResult.from_dict(result_data)

        except json.JSONDecodeError as e:
            log.warning(f"Failed to parse classification response: {e}")
            # Fallback: return personal domain with extracted summary
            return ClassificationResult(
                template_key=None,
                domain=Domain.PERSONAL,
                confidence=0.3,
                extracted_details=ExtractedDetails(
                    summary=user_input[:200] if len(user_input) > 200 else user_input,
                    key_entities=[],
                    phase_hint=None,
                ),
            )
        except Exception as e:
            log.error(f"Classification error: {e}")
            raise

    async def classify_from_template_key(
        self,
        template_key: str,
        details: str,
    ) -> ClassificationResult:
        """Create classification from a known template key.

        Used during onboarding when user selects from predefined options.

        Args:
            template_key: The selected template key
            details: User's additional details about the situation

        Returns:
            ClassificationResult with the template and extracted details
        """
        template = await self.get_template_by_key(template_key)

        if not template:
            # Unknown template, treat as personal
            return ClassificationResult(
                template_key=None,
                domain=Domain.PERSONAL,
                confidence=0.5,
                extracted_details=ExtractedDetails(summary=details),
            )

        # Extract details from the user's input using LLM
        extract_prompt = f"""Extract key details from this situation description.

Situation type: {template.display_name}
User said: "{details}"
{f"Possible phases: {', '.join(template.phases)}" if template.phases else ""}

Return JSON:
{{
    "summary": "one sentence summary",
    "key_entities": ["specific names, dates, places mentioned"],
    "phase_hint": {"one of " + str(template.phases) + " or null" if template.phases else "null"}
}}

Return ONLY valid JSON."""

        try:
            response = await self.llm.generate(
                prompt=extract_prompt,
                system_prompt="You extract structured details from text. Return only valid JSON.",
                max_tokens=300,
            )

            details_data = json.loads(response.strip())

            return ClassificationResult(
                template_key=template_key,
                domain=template.domain,
                confidence=1.0,  # User explicitly selected
                extracted_details=ExtractedDetails(
                    summary=details_data.get("summary", details[:200]),
                    key_entities=details_data.get("key_entities", []),
                    phase_hint=details_data.get("phase_hint"),
                ),
            )

        except (json.JSONDecodeError, Exception) as e:
            log.warning(f"Detail extraction failed: {e}")
            return ClassificationResult(
                template_key=template_key,
                domain=template.domain,
                confidence=1.0,
                extracted_details=ExtractedDetails(
                    summary=details[:200] if len(details) > 200 else details,
                ),
            )

    async def get_follow_up_prompt(
        self,
        template_key: str,
        phase: Optional[str] = None,
        prompt_type: str = "check_in",
    ) -> str:
        """Get the appropriate follow-up prompt for a thread.

        Args:
            template_key: The thread's template key
            phase: Current phase (if applicable)
            prompt_type: "initial" or "check_in"

        Returns:
            The follow-up prompt string
        """
        template = await self.get_template_by_key(template_key)

        if not template:
            return "How are things going?"

        prompts = template.follow_up_prompts

        # Check for phase-specific prompt first
        if phase and phase in prompts.phase_specific:
            return prompts.phase_specific[phase]

        # Fall back to general prompt type
        if prompt_type == "initial":
            return prompts.initial

        return prompts.check_in

    async def save_domain_preferences(
        self,
        user_id: UUID,
        preferences: DomainPreferences,
    ) -> None:
        """Save user's domain preferences."""
        await self.db.execute(
            """
            UPDATE users
            SET domain_preferences = :prefs, updated_at = NOW()
            WHERE id = :user_id
            """,
            {"user_id": str(user_id), "prefs": json.dumps(preferences.to_dict())},
        )

    async def get_domain_preferences(self, user_id: UUID) -> DomainPreferences:
        """Get user's domain preferences."""
        row = await self.db.fetch_one(
            "SELECT domain_preferences FROM users WHERE id = :user_id",
            {"user_id": str(user_id)},
        )

        if not row or not row["domain_preferences"]:
            return DomainPreferences()

        prefs_data = row["domain_preferences"]
        if isinstance(prefs_data, str):
            prefs_data = json.loads(prefs_data)

        return DomainPreferences.from_dict(prefs_data)
