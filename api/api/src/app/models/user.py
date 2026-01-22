"""User models.

Includes preference schema from ADR-002 (Personalization System).
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Preference Enums (ADR-002)
# ============================================================================


class EmojiLevel(str, Enum):
    """Emoji usage preference."""
    NONE = "none"
    MINIMAL = "minimal"
    MODERATE = "moderate"
    EXPRESSIVE = "expressive"


class Formality(str, Enum):
    """Communication formality preference."""
    FORMAL = "formal"
    CASUAL = "casual"
    MATCH_MINE = "match_mine"


class MessageLength(str, Enum):
    """Preferred message length."""
    BRIEF = "brief"
    MODERATE = "moderate"
    DETAILED = "detailed"


class HumorLevel(str, Enum):
    """Humor preference."""
    NONE = "none"
    LIGHT = "light"
    PLAYFUL = "playful"


class SupportStyle(str, Enum):
    """Support approach preference."""
    FRIENDLY_CHECKIN = "friendly_checkin"
    MOTIVATIONAL = "motivational"
    ACCOUNTABILITY = "accountability"
    LISTENER = "listener"


class FeedbackType(str, Enum):
    """Feedback preference."""
    VALIDATION = "validation"
    CHALLENGE = "challenge"
    BALANCED = "balanced"


class QuestionFrequency(str, Enum):
    """How often companion asks questions."""
    FEW = "few"
    MODERATE = "moderate"
    MANY = "many"


class MessageTone(str, Enum):
    """Overall message tone."""
    GENTLE = "gentle"
    WARM = "warm"
    ENERGETIC = "energetic"
    AFFIRMING = "affirming"


class PersonalityType(str, Enum):
    """User personality type from quiz (ADR-003)."""
    MORNING_REFLECTOR = "morning_reflector"
    QUIET_CONNECTOR = "quiet_connector"
    MOMENTUM_SEEKER = "momentum_seeker"
    STEADY_ANCHOR = "steady_anchor"


class OnboardingPath(str, Enum):
    """Onboarding path taken (ADR-003)."""
    QUIZ = "quiz"
    CHAT = "chat"
    QUIZ_THEN_CHAT = "quiz_then_chat"


# ============================================================================
# Preference Sub-models (ADR-002)
# ============================================================================


class CommunicationPreferences(BaseModel):
    """Communication style preferences."""
    emoji_level: EmojiLevel = EmojiLevel.MODERATE
    formality: Formality = Formality.CASUAL
    message_length: MessageLength = MessageLength.MODERATE
    humor: HumorLevel = HumorLevel.LIGHT
    message_tone: MessageTone = MessageTone.WARM


class SupportPreferences(BaseModel):
    """Support approach preferences."""
    style: SupportStyle = SupportStyle.FRIENDLY_CHECKIN
    feedback_type: FeedbackType = FeedbackType.BALANCED
    questions: QuestionFrequency = QuestionFrequency.MODERATE


class BoundaryPreferences(BaseModel):
    """Boundary and sensitivity settings."""
    avoid_topics: List[str] = Field(default_factory=list)
    sensitive_topics: List[str] = Field(default_factory=list)
    no_advice_on: List[str] = Field(default_factory=list)


class TimingPreferences(BaseModel):
    """Timing preferences for messages."""
    preferred_time: Optional[str] = None  # "09:00" format
    timezone: str = "UTC"
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None


# ============================================================================
# Main Preferences Model (ADR-002)
# ============================================================================


class CompanionPreferences(BaseModel):
    """Full user preferences for companion behavior.

    Based on ADR-002: Personalization System.
    Explicit preferences that users can control directly.
    """
    communication: CommunicationPreferences = Field(default_factory=CommunicationPreferences)
    support: SupportPreferences = Field(default_factory=SupportPreferences)
    boundaries: BoundaryPreferences = Field(default_factory=BoundaryPreferences)
    timing: TimingPreferences = Field(default_factory=TimingPreferences)


# ============================================================================
# Legacy Preferences (for backward compatibility)
# ============================================================================


class UserPreferences(BaseModel):
    """User preferences stored as JSON.

    This model combines legacy fields with new ADR-002 preferences.
    """
    # Legacy fields
    notification_enabled: bool = True
    notification_time: Optional[str] = None
    theme: str = "system"
    language: str = "en"
    vibe_preference: Optional[str] = None
    visual_mode_override: Optional[str] = None  # "always_off" | "always_on" | "episode_default" | None

    # New ADR-002 fields (nested)
    communication: Optional[CommunicationPreferences] = None
    support: Optional[SupportPreferences] = None
    boundaries: Optional[BoundaryPreferences] = None
    timing: Optional[TimingPreferences] = None


class UserCreate(BaseModel):
    """Data for creating a user profile."""

    display_name: Optional[str] = None
    pronouns: Optional[str] = None
    timezone: str = "UTC"


class UserUpdate(BaseModel):
    """Data for updating a user profile."""

    display_name: Optional[str] = None
    pronouns: Optional[str] = None
    timezone: Optional[str] = None
    preferences: Optional[UserPreferences] = None
    onboarding_completed: Optional[bool] = None
    onboarding_step: Optional[str] = None
    # Companion settings
    companion_name: Optional[str] = None
    support_style: Optional[str] = None
    preferred_message_time: Optional[str] = None


class OnboardingData(BaseModel):
    """Data collected during onboarding."""

    display_name: str
    pronouns: Optional[str] = None
    timezone: str = "UTC"
    vibe_preference: str = Field(..., description="comforting, flirty, or chill")
    first_character_id: UUID
    age_confirmed: bool = True


class User(BaseModel):
    """User profile model.

    Extended with ADR-002 (Personalization) and ADR-003 (Onboarding) fields.
    """

    id: UUID
    display_name: Optional[str] = None
    pronouns: Optional[str] = None
    timezone: str = "UTC"
    age_confirmed: bool = False
    onboarding_completed: bool = False
    onboarding_step: Optional[str] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)
    subscription_status: str = "free"
    subscription_expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Chat Companion fields
    companion_name: Optional[str] = None  # What user calls the AI companion
    support_style: Optional[str] = None  # friendly_checkin, motivational, etc.
    preferred_message_time: Optional[str] = None  # HH:MM format

    # ADR-003: Onboarding fields
    personality_type: Optional[str] = None  # From quiz: morning_reflector, etc.
    quiz_answers: Dict[str, Any] = Field(default_factory=dict)  # Raw quiz answers
    onboarding_path: Optional[str] = None  # 'quiz', 'chat', 'quiz_then_chat'
    onboarding_completed_at: Optional[datetime] = None

    @field_validator("preferred_message_time", mode="before")
    @classmethod
    def convert_time_to_string(cls, v: Any) -> Optional[str]:
        """Convert datetime.time to string format HH:MM."""
        if v is None:
            return None
        if isinstance(v, str):
            return v
        # Handle datetime.time objects from database
        from datetime import time
        if isinstance(v, time):
            return v.strftime("%H:%M")
        return str(v)

    @field_validator("preferences", mode="before")
    @classmethod
    def ensure_preferences_is_dict(cls, v: Any) -> Dict[str, Any]:
        """Handle corrupted preferences data (e.g., array instead of dict)."""
        if v is None:
            return {}
        if isinstance(v, dict):
            return v
        if isinstance(v, list):
            # Corrupted data - merge list items into dict
            result: Dict[str, Any] = {}
            for item in v:
                if isinstance(item, dict):
                    result.update(item)
                elif isinstance(item, str):
                    # Try to parse JSON string
                    import json
                    try:
                        parsed = json.loads(item)
                        if isinstance(parsed, dict):
                            result.update(parsed)
                    except (json.JSONDecodeError, TypeError):
                        pass
            return result
        return {}

    class Config:
        from_attributes = True
