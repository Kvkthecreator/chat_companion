"""
Companion Service - Personality and prompting for the AI companion.

Handles:
- System prompt generation based on user preferences
- Daily message generation
- Response generation for conversations
"""

import logging
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from pydantic import BaseModel

log = logging.getLogger(__name__)


# =============================================================================
# Support Styles Configuration
# =============================================================================

SUPPORT_STYLES = {
    "motivational": {
        "name": "Motivational",
        "description": "Encouraging and energizing",
        "tone": "encouraging, energizing, and optimistic",
        "focus": "goals, growth, achievements, and positive momentum",
        "morning_energy": "high",
        "sample_opener": "Rise and shine! Today's got potential written all over it.",
    },
    "friendly_checkin": {
        "name": "Friendly Check-in",
        "description": "Warm and casual, like a close friend",
        "tone": "warm, casual, and genuinely interested",
        "focus": "how you're feeling, what's going on in your life, being present",
        "morning_energy": "medium",
        "sample_opener": "Hey! Just wanted to check in and see how you're doing today.",
    },
    "accountability": {
        "name": "Accountability",
        "description": "Supportive but direct",
        "tone": "supportive but direct and honest",
        "focus": "progress on goals, habits, commitments, and following through",
        "morning_energy": "medium-high",
        "sample_opener": "Good morning! Let's make today count. What's the one thing you want to accomplish?",
    },
    "listener": {
        "name": "Listener",
        "description": "Gentle and present",
        "tone": "gentle, present, and validating",
        "focus": "creating space to share, validating feelings, being there without judgment",
        "morning_energy": "low-medium",
        "sample_opener": "Hi there. How are you feeling today? I'm here if you want to talk.",
    },
}


# =============================================================================
# Data Models
# =============================================================================


class UserProfile(BaseModel):
    """User profile for companion context."""

    user_id: str
    display_name: Optional[str] = None
    companion_name: Optional[str] = None
    support_style: str = "friendly_checkin"
    timezone: str = "America/New_York"
    location: Optional[str] = None


class UserContext(BaseModel):
    """Context item about the user."""

    category: str
    key: str
    value: str
    importance_score: float = 0.5


class ConversationContext(BaseModel):
    """Context for generating responses."""

    user_profile: UserProfile
    user_context: list[UserContext] = []
    recent_messages: list[dict] = []  # [{role: "user"|"assistant", content: str}]
    weather_info: Optional[str] = None
    day_of_week: Optional[str] = None
    local_time: Optional[str] = None
    is_daily_message: bool = False


# =============================================================================
# Companion Service
# =============================================================================


class CompanionService:
    """Service for generating companion responses and messages."""

    @staticmethod
    def get_support_style_config(style: str) -> dict:
        """Get configuration for a support style."""
        return SUPPORT_STYLES.get(style, SUPPORT_STYLES["friendly_checkin"])

    @staticmethod
    def format_user_context(context_items: list[UserContext]) -> str:
        """Format user context items for the system prompt."""
        if not context_items:
            return "No specific context known yet - this is a new relationship."

        # Group by category
        by_category: dict[str, list[str]] = {}
        for item in context_items:
            if item.category not in by_category:
                by_category[item.category] = []
            by_category[item.category].append(f"- {item.key}: {item.value}")

        # Format output
        sections = []
        category_labels = {
            "fact": "Personal Facts",
            "preference": "Preferences",
            "event": "Upcoming/Recent Events",
            "goal": "Goals",
            "relationship": "People in Their Life",
            "emotion": "Recent Emotional States",
            "situation": "Current Life Situations",
            "routine": "Routines & Habits",
            "struggle": "Challenges They're Facing",
        }

        for category, items in by_category.items():
            label = category_labels.get(category, category.title())
            sections.append(f"{label}:\n" + "\n".join(items))

        return "\n\n".join(sections)

    @staticmethod
    def format_recent_conversation(messages: list[dict], max_messages: int = 10) -> str:
        """Format recent messages for context."""
        if not messages:
            return "No recent conversation."

        recent = messages[-max_messages:]
        formatted = []
        for msg in recent:
            role = "You" if msg["role"] == "assistant" else "Them"
            formatted.append(f"{role}: {msg['content']}")

        return "\n".join(formatted)

    @classmethod
    def build_system_prompt(cls, context: ConversationContext) -> str:
        """Build the system prompt for the companion."""
        profile = context.user_profile
        style_config = cls.get_support_style_config(profile.support_style)

        # User's name for addressing them
        user_name = profile.display_name or "there"

        # Companion's name (or default)
        companion_name = profile.companion_name or "your companion"

        # Format context
        user_context_str = cls.format_user_context(context.user_context)

        # Time context
        time_context = ""
        if context.day_of_week:
            time_context += f"Day: {context.day_of_week}\n"
        if context.local_time:
            time_context += f"Their local time: {context.local_time}\n"
        if context.weather_info:
            time_context += f"Weather: {context.weather_info}\n"

        # Build the prompt
        prompt = f"""You are {companion_name}, a caring AI companion for {user_name}. Your role is to reach out daily and be someone who genuinely cares about their wellbeing.

## Your Personality
- Warm and supportive, like a caring friend
- Not overly bubbly or fake-positive
- Remember and naturally reference things they've shared
- Ask thoughtful follow-up questions
- Adapt your tone to their mood and energy
- Keep messages concise but personal (not walls of text)

## Support Style: {style_config['name']}
Your tone is {style_config['tone']}.
You focus on {style_config['focus']}.

## What You Know About {user_name}
{user_context_str}

## Current Context
{time_context if time_context else "No specific time context available."}

## Guidelines
- Be genuine, not performative
- Match their energy - don't be hyper if they seem tired
- Reference specific things they've mentioned naturally
- If they mentioned something upcoming, ask about it
- End with something that invites response without pressure
- Use their name occasionally but not excessively
- Keep responses focused - one main topic at a time
- Be curious about their life but not interrogating"""

        # Add daily message specific guidance
        if context.is_daily_message:
            prompt += """

## Daily Check-in Guidelines
This is your daily reach-out message. Make it:
- Personal (reference something specific to them if possible)
- Brief (2-4 sentences typically)
- Warm but not overwhelming
- End with something that invites them to share
- Consider the day of week (weekday vs weekend energy)"""

        return prompt

    @classmethod
    def build_daily_message_prompt(cls, context: ConversationContext) -> str:
        """Build prompt for generating a daily check-in message."""
        profile = context.user_profile
        style_config = cls.get_support_style_config(profile.support_style)
        user_name = profile.display_name or "there"

        # Gather any follow-up items from context
        follow_ups = [
            item for item in context.user_context if item.category in ("event", "goal", "situation")
        ]

        follow_up_str = ""
        if follow_ups:
            follow_up_str = "Things you might want to ask about:\n"
            for item in follow_ups[:3]:  # Max 3 follow-ups
                follow_up_str += f"- {item.key}: {item.value}\n"

        prompt = f"""Generate a daily check-in message for {user_name}.

Support style: {style_config['name']} - {style_config['description']}
Energy level: {style_config['morning_energy']}

{follow_up_str}

Day: {context.day_of_week or 'Unknown'}
Time: {context.local_time or 'Morning'}
Weather: {context.weather_info or 'Unknown'}

Generate a warm, personal message that:
1. Feels like it's from someone who genuinely cares
2. Is brief (2-4 sentences)
3. References something specific if possible (weather, day of week, or something from their context)
4. Ends with something that invites them to respond
5. Matches the {style_config['morning_energy']} energy level

Do NOT:
- Be overly enthusiastic or use excessive exclamation marks
- Ask multiple questions
- Be generic or template-y
- Start with "Good morning!" every time (vary your openings)

Just output the message, nothing else."""

        return prompt

    @classmethod
    def get_local_time_context(cls, timezone: str) -> tuple[str, str]:
        """Get day of week and local time for a timezone."""
        try:
            tz = ZoneInfo(timezone)
            now = datetime.now(tz)
            day_of_week = now.strftime("%A")
            local_time = now.strftime("%I:%M %p")
            return day_of_week, local_time
        except Exception as e:
            log.warning(f"Failed to get time for timezone {timezone}: {e}")
            return "Unknown", "Unknown"


# Singleton instance
_companion_service: Optional[CompanionService] = None


def get_companion_service() -> CompanionService:
    """Get the companion service singleton."""
    global _companion_service
    if _companion_service is None:
        _companion_service = CompanionService()
    return _companion_service
