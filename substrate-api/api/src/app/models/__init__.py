"""Pydantic models for Fantazy API."""

from app.models.user import (
    User,
    UserCreate,
    UserUpdate,
    UserPreferences,
    OnboardingData,
)
from app.models.character import (
    Character,
    CharacterSummary,
    CharacterPersonality,
    CharacterToneStyle,
    CharacterBoundaries,
)
from app.models.world import World, WorldSummary
from app.models.series import (
    Series,
    SeriesSummary,
    SeriesCreate,
    SeriesUpdate,
    SeriesWithEpisodes,
    SeriesWithCharacters,
    SeriesType,
)
from app.models.engagement import (
    Engagement,
    EngagementCreate,
    EngagementUpdate,
    EngagementWithCharacter,
)
from app.models.session import (
    Session,
    SessionCreate,
    SessionSummary,
    SessionUpdate,
    SessionWithMessages,
    SessionState,
    ResolutionType,
)
from app.models.message import (
    Message,
    MessageCreate,
    MessageRole,
    ConversationContext,
)
from app.models.memory import (
    MemoryEvent,
    MemoryEventCreate,
    MemoryType,
    MemoryQuery,
)
from app.models.hook import (
    Hook,
    HookCreate,
    HookType,
)
from app.models.usage import (
    UsageStats,
    UsageResponse,
    FluxUsage,
    MessageUsage,
    QuotaCheckResult,
    UsageEvent,
    UsageEventCreate,
)

__all__ = [
    # User
    "User",
    "UserCreate",
    "UserUpdate",
    "UserPreferences",
    "OnboardingData",
    # Character
    "Character",
    "CharacterSummary",
    "CharacterPersonality",
    "CharacterToneStyle",
    "CharacterBoundaries",
    # World
    "World",
    "WorldSummary",
    # Series (new)
    "Series",
    "SeriesSummary",
    "SeriesCreate",
    "SeriesUpdate",
    "SeriesWithEpisodes",
    "SeriesWithCharacters",
    "SeriesType",
    # Engagement
    "Engagement",
    "EngagementCreate",
    "EngagementUpdate",
    "EngagementWithCharacter",
    # Session
    "Session",
    "SessionCreate",
    "SessionSummary",
    "SessionUpdate",
    "SessionWithMessages",
    "SessionState",
    "ResolutionType",
    # Message
    "Message",
    "MessageCreate",
    "MessageRole",
    "ConversationContext",
    # Memory
    "MemoryEvent",
    "MemoryEventCreate",
    "MemoryType",
    "MemoryQuery",
    # Hook
    "Hook",
    "HookCreate",
    "HookType",
    # Usage
    "UsageStats",
    "UsageResponse",
    "FluxUsage",
    "MessageUsage",
    "QuotaCheckResult",
    "UsageEvent",
    "UsageEventCreate",
]
