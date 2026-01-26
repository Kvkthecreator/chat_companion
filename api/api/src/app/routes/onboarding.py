"""Onboarding API routes for Chat Companion.

Supports three onboarding paths:
1. Chat path - Conversational onboarding with companion
2. Form path - Quick form-based onboarding
3. Domain-first (v2) - Transition-focused onboarding with immediate value

Domain-first onboarding flow (v2):
- GET /onboarding/templates - Get template options for selection
- POST /onboarding/complete-v2 - Complete with domain selections
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Any, List
from datetime import datetime, timedelta
from uuid import UUID
import json
import logging

from app.deps import get_db
from app.dependencies import get_current_user_id
from app.services.onboarding import ChatOnboardingService
from app.services.domain_classifier import DomainClassifier
from app.services.llm import LLMService

log = logging.getLogger(__name__)

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


class OnboardingState(BaseModel):
    """Onboarding state response."""

    user_id: str
    current_step: str
    completed_at: Optional[datetime] = None
    data: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class OnboardingUpdate(BaseModel):
    """Onboarding update request."""

    step: Optional[str] = None
    data: Optional[dict[str, Any]] = None


class ChatOnboardingState(BaseModel):
    """Current state of chat onboarding."""

    message: Optional[str] = None
    step: str
    expects: Optional[str] = None
    options: Optional[List[str]] = None
    is_complete: bool


class ChatResponseRequest(BaseModel):
    """User response during chat onboarding."""

    response: str


class ChatResponseResult(BaseModel):
    """Result after processing user response."""

    success: bool
    is_complete: bool = False
    step: Optional[str] = None
    next_message: Optional[str] = None
    expects: Optional[str] = None
    options: Optional[List[str]] = None
    error: Optional[str] = None
    retry_message: Optional[str] = None


class OnboardingCompleteRequest(BaseModel):
    """Request body for completing form onboarding."""

    situation: Optional[str] = None  # Current life situation to create initial thread


@router.get("", response_model=OnboardingState)
async def get_onboarding(
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Get current onboarding state for the user."""
    result = await db.fetch_one(
        """
        SELECT user_id, current_step, completed_at, data, created_at, updated_at
        FROM onboarding
        WHERE user_id = :user_id
        """,
        {"user_id": str(user_id)},
    )

    if not result:
        # Create new onboarding record
        await db.execute(
            """
            INSERT INTO onboarding (user_id, current_step, data)
            VALUES (:user_id, 'welcome', '{}')
            ON CONFLICT (user_id) DO NOTHING
            """,
            {"user_id": str(user_id)},
        )
        result = await db.fetch_one(
            """
            SELECT user_id, current_step, completed_at, data, created_at, updated_at
            FROM onboarding
            WHERE user_id = :user_id
            """,
            {"user_id": str(user_id)},
        )

    data = result["data"]
    if isinstance(data, str):
        data = json.loads(data)

    return OnboardingState(
        user_id=str(result["user_id"]),
        current_step=result["current_step"],
        completed_at=result["completed_at"],
        data=data or {},
        created_at=result["created_at"],
        updated_at=result["updated_at"],
    )


@router.patch("", response_model=OnboardingState)
async def update_onboarding(
    update: OnboardingUpdate,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Update onboarding state."""
    # First ensure record exists
    await db.execute(
        """
        INSERT INTO onboarding (user_id, current_step, data)
        VALUES (:user_id, 'welcome', '{}')
        ON CONFLICT (user_id) DO NOTHING
        """,
        {"user_id": str(user_id)},
    )

    # Build update query
    updates = []
    params = {"user_id": str(user_id)}

    if update.step is not None:
        updates.append("current_step = :step")
        params["step"] = update.step

    if update.data is not None:
        # Merge with existing data
        updates.append("data = data || :data::jsonb")
        params["data"] = json.dumps(update.data)

    if updates:
        await db.execute(
            f"""
            UPDATE onboarding
            SET {", ".join(updates)}, updated_at = NOW()
            WHERE user_id = :user_id
            """,
            params,
        )

    # Return updated state
    result = await db.fetch_one(
        """
        SELECT user_id, current_step, completed_at, data, created_at, updated_at
        FROM onboarding
        WHERE user_id = :user_id
        """,
        {"user_id": str(user_id)},
    )

    data = result["data"]
    if isinstance(data, str):
        data = json.loads(data)

    return OnboardingState(
        user_id=str(result["user_id"]),
        current_step=result["current_step"],
        completed_at=result["completed_at"],
        data=data or {},
        created_at=result["created_at"],
        updated_at=result["updated_at"],
    )


@router.post("/complete", response_model=OnboardingState)
async def complete_onboarding(
    request: Optional[OnboardingCompleteRequest] = None,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Mark onboarding as complete.

    Optionally accepts a situation to create the user's first thread,
    preventing the cold start problem where Day 1 messages are generic.
    """
    # If situation provided, save it as a thread in user_context
    if request and request.situation and request.situation.strip():
        await db.execute(
            """
            INSERT INTO user_context (user_id, category, key, value, tier, source, importance_score)
            VALUES (:user_id, 'situation', 'current_situation', :value, 'thread', 'onboarding', 0.9)
            ON CONFLICT (user_id, category, key)
            DO UPDATE SET value = EXCLUDED.value, tier = EXCLUDED.tier, updated_at = NOW()
            """,
            {
                "user_id": str(user_id),
                "value": request.situation.strip(),
            },
        )

    # Update onboarding record
    await db.execute(
        """
        UPDATE onboarding
        SET completed_at = NOW(), current_step = 'complete', updated_at = NOW()
        WHERE user_id = :user_id
        """,
        {"user_id": str(user_id)},
    )

    # Update user record (mark onboarding_path as 'form' to distinguish from chat path)
    await db.execute(
        """
        UPDATE users
        SET onboarding_completed_at = NOW(), onboarding_path = 'form', updated_at = NOW()
        WHERE id = :user_id
        """,
        {"user_id": str(user_id)},
    )

    # Return updated state
    result = await db.fetch_one(
        """
        SELECT user_id, current_step, completed_at, data, created_at, updated_at
        FROM onboarding
        WHERE user_id = :user_id
        """,
        {"user_id": str(user_id)},
    )

    data = result["data"]
    if isinstance(data, str):
        data = json.loads(data)

    return OnboardingState(
        user_id=str(result["user_id"]),
        current_step=result["current_step"],
        completed_at=result["completed_at"],
        data=data or {},
        created_at=result["created_at"],
        updated_at=result["updated_at"],
    )


# ============================================================================
# Chat Onboarding Endpoints (ADR-003)
# ============================================================================


@router.get("/chat", response_model=ChatOnboardingState)
async def get_chat_onboarding_state(
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Get current chat onboarding state and message.

    Returns the companion's current message in the onboarding flow,
    along with what kind of response is expected.
    """
    service = ChatOnboardingService(db)
    result = await service.get_current_message(user_id)

    return ChatOnboardingState(
        message=result["message"],
        step=result["step"],
        expects=result.get("expects"),
        options=result.get("options"),
        is_complete=result["is_complete"],
    )


@router.post("/chat/respond", response_model=ChatResponseResult)
async def process_chat_response(
    request: ChatResponseRequest,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Process user's response during chat onboarding.

    Takes the user's text response, validates it based on expected input type,
    saves the appropriate data, and returns the next message in the flow.
    """
    if not request.response or not request.response.strip():
        return ChatResponseResult(
            success=False,
            error="Please provide a response.",
        )

    service = ChatOnboardingService(db)
    result = await service.process_response(user_id, request.response)

    return ChatResponseResult(
        success=result.get("success", False),
        is_complete=result.get("is_complete", False),
        step=result.get("step"),
        next_message=result.get("next_message"),
        expects=result.get("expects"),
        options=result.get("options"),
        error=result.get("error"),
        retry_message=result.get("retry_message"),
    )


@router.post("/chat/reset", response_model=ChatOnboardingState)
async def reset_chat_onboarding(
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Reset chat onboarding to the beginning.

    For testing and admin purposes. Clears all progress and starts fresh.
    """
    service = ChatOnboardingService(db)
    result = await service.reset_onboarding(user_id)

    return ChatOnboardingState(
        message=result["message"],
        step=result["step"],
        expects=result.get("expects"),
        options=result.get("options"),
        is_complete=result["is_complete"],
    )


@router.post("/chat/skip/{step}", response_model=ChatOnboardingState)
async def skip_to_step(
    step: str,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Skip to a specific onboarding step.

    For testing and admin purposes.
    Valid steps: intro, name, situation, support_style, wake_time, companion_name, confirmation
    """
    service = ChatOnboardingService(db)
    result = await service.skip_to_step(user_id, step)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return ChatOnboardingState(
        message=result["message"],
        step=result["step"],
        expects=result.get("expects"),
        options=result.get("options"),
        is_complete=result["is_complete"],
    )


# ============================================================================
# Domain-First Onboarding V2 (Transition-Focused)
# ============================================================================


class DomainSelection(BaseModel):
    """A domain/template selection from onboarding."""
    template_key: str           # "job_search", "new_city", etc.
    details: str                # User's description of their situation
    is_primary: bool = False    # First selection is primary


class UserPreferencesV2(BaseModel):
    """User preferences collected during onboarding."""
    display_name: str
    companion_name: str = "Aria"
    preferred_message_time: str = "09:00"  # HH:MM format
    timezone: Optional[str] = None  # Auto-detected if not provided


class OnboardingCompleteV2Request(BaseModel):
    """Request body for domain-first onboarding completion."""
    domain_selections: List[DomainSelection]  # 1-3 selections
    preferences: UserPreferencesV2


class OnboardingCompleteV2Response(BaseModel):
    """Response after completing domain-first onboarding."""
    success: bool
    acknowledgment_message: str
    conversation_id: str
    threads_created: List[str]


ACKNOWLEDGMENT_PROMPT = """Generate a warm, personalized acknowledgment message for a user who just completed onboarding.

User's name: {display_name}
Companion's name: {companion_name}

Their situations:
{situations}

Generate a message that:
1. Acknowledges what they're going through (specific to their situations)
2. Shows you understand the weight/importance
3. Sets expectation that you'll follow up on these things
4. Ends with an open invitation to share more

Keep it warm but not over-the-top. 3-4 sentences max. Sound like a supportive friend, not a therapist.

Return ONLY the message text, no quotes or formatting."""


@router.post("/complete-v2", response_model=OnboardingCompleteV2Response)
async def complete_onboarding_v2(
    request: OnboardingCompleteV2Request,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Complete onboarding with domain-first flow.

    This is the transition-focused onboarding that:
    1. Saves user preferences
    2. Sets domain preferences
    3. Creates typed threads from selections
    4. Generates immediate acknowledgment message
    5. Creates first conversation with acknowledgment
    6. Marks onboarding complete

    Returns the acknowledgment message and conversation ID for immediate display.
    """
    if not request.domain_selections:
        raise HTTPException(
            status_code=400,
            detail="At least one domain selection is required",
        )

    classifier = DomainClassifier(db)
    llm = LLMService()
    threads_created = []
    situations_text = []

    # 1. Save user preferences
    prefs = request.preferences
    await db.execute(
        """
        UPDATE users
        SET display_name = :display_name,
            companion_name = :companion_name,
            preferred_message_time = :preferred_time,
            timezone = COALESCE(:timezone, timezone),
            updated_at = NOW()
        WHERE id = :user_id
        """,
        {
            "user_id": str(user_id),
            "display_name": prefs.display_name,
            "companion_name": prefs.companion_name,
            "preferred_time": prefs.preferred_message_time,
            "timezone": prefs.timezone,
        },
    )

    # 2. Process each domain selection
    primary_domains = []
    domain_weights = {}
    onboarding_selections = []

    for i, selection in enumerate(request.domain_selections):
        is_primary = selection.is_primary or i == 0  # First is always primary

        # Classify the selection (get template, extract details)
        if selection.template_key.startswith("custom:"):
            # Custom free-text input
            custom_text = selection.template_key.replace("custom:", "")
            result = await classifier.classify_situation(custom_text + " " + selection.details)
        else:
            # Known template selected
            result = await classifier.classify_from_template_key(
                selection.template_key, selection.details
            )

        # Get template for domain and follow-up days
        template = await classifier.get_template_by_key(result.template_key or "open")
        domain = result.domain.value
        follow_up_days = template.default_follow_up_days if template else 3

        # Track primary domains
        if is_primary:
            primary_domains.append(domain)
            domain_weights[domain] = 1.5
        else:
            domain_weights.setdefault(domain, 1.0)

        onboarding_selections.append(result.template_key or "open")

        # 3. Create thread in user_context
        thread_value = json.dumps({
            "summary": result.extracted_details.summary,
            "status": "active",
            "key_details": result.extracted_details.key_entities,
            "follow_up_date": (datetime.utcnow() + timedelta(days=follow_up_days)).isoformat(),
            "created_from": "onboarding_v2",
        })

        topic_key = result.template_key or f"situation_{i}"

        await db.execute(
            """
            INSERT INTO user_context (
                user_id, category, key, value, tier, source,
                importance_score, domain, template_id, phase, priority_weight
            )
            VALUES (
                :user_id, 'thread', :key, :value, 'thread', 'onboarding',
                0.9, :domain, :template_id, :phase, :priority_weight
            )
            ON CONFLICT (user_id, category, key)
            DO UPDATE SET
                value = EXCLUDED.value,
                domain = EXCLUDED.domain,
                template_id = EXCLUDED.template_id,
                phase = EXCLUDED.phase,
                priority_weight = EXCLUDED.priority_weight,
                updated_at = NOW()
            RETURNING id
            """,
            {
                "user_id": str(user_id),
                "key": topic_key,
                "value": thread_value,
                "domain": domain,
                "template_id": str(template.id) if template else None,
                "phase": result.extracted_details.phase_hint,
                "priority_weight": 1.5 if is_primary else 1.0,
            },
        )

        # Track for response
        thread_row = await db.fetch_one(
            "SELECT id FROM user_context WHERE user_id = :user_id AND category = 'thread' AND key = :key",
            {"user_id": str(user_id), "key": topic_key},
        )
        if thread_row:
            threads_created.append(str(thread_row["id"]))

        # Build situations text for acknowledgment
        template_name = template.display_name if template else "situation"
        situations_text.append(f"- {template_name}: {result.extracted_details.summary}")

    # 4. Save domain preferences
    domain_prefs = {
        "primary_domains": primary_domains,
        "domain_weights": domain_weights,
        "onboarding_selections": onboarding_selections,
    }
    await db.execute(
        "UPDATE users SET domain_preferences = :prefs, updated_at = NOW() WHERE id = :user_id",
        {"user_id": str(user_id), "prefs": json.dumps(domain_prefs)},
    )

    # 5. Generate acknowledgment message
    try:
        acknowledgment = await llm.generate(
            prompt=ACKNOWLEDGMENT_PROMPT.format(
                display_name=prefs.display_name,
                companion_name=prefs.companion_name,
                situations="\n".join(situations_text),
            ),
            system_prompt="You are a warm, supportive companion. Generate only the message text.",
            max_tokens=300,
        )
        acknowledgment = acknowledgment.strip().strip('"')
    except Exception as e:
        log.warning(f"Failed to generate acknowledgment: {e}")
        # Fallback acknowledgment
        acknowledgment = (
            f"Hey {prefs.display_name}! Thanks for sharing what's going on. "
            "I'll be here to check in on how things are going. "
            "Feel free to tell me more whenever you want."
        )

    # 6. Create conversation and save acknowledgment as first message
    conv_result = await db.fetch_one(
        """
        INSERT INTO conversations (user_id, channel, initiated_by)
        VALUES (:user_id, 'web', 'companion')
        RETURNING id
        """,
        {"user_id": str(user_id)},
    )
    conversation_id = str(conv_result["id"])

    await db.execute(
        """
        INSERT INTO companion_messages (conversation_id, role, content, metadata)
        VALUES (:conv_id, 'assistant', :content, :metadata)
        """,
        {
            "conv_id": conversation_id,
            "content": acknowledgment,
            "metadata": json.dumps({"type": "onboarding_acknowledgment"}),
        },
    )

    # 7. Mark onboarding complete
    await db.execute(
        """
        UPDATE onboarding
        SET completed_at = NOW(), current_step = 'complete', updated_at = NOW()
        WHERE user_id = :user_id
        """,
        {"user_id": str(user_id)},
    )

    await db.execute(
        """
        UPDATE users
        SET onboarding_completed_at = NOW(), onboarding_path = 'domain_v2', updated_at = NOW()
        WHERE id = :user_id
        """,
        {"user_id": str(user_id)},
    )

    return OnboardingCompleteV2Response(
        success=True,
        acknowledgment_message=acknowledgment,
        conversation_id=conversation_id,
        threads_created=threads_created,
    )
