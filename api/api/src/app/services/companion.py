"""
Companion Service - Personality and prompting for the AI companion.

Handles:
- System prompt generation based on user preferences
- Daily message generation
- Response generation for conversations
"""

import logging
from datetime import datetime
from typing import Any, Optional
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
    # Message context for priority-based daily messages (from ThreadService)
    message_context: Optional[Any] = None


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
        """Build prompt for generating a daily check-in message.

        IMPORTANT: This now supports priority-based message generation.
        Pass message_context in ConversationContext for priority awareness.
        """
        profile = context.user_profile
        style_config = cls.get_support_style_config(profile.support_style)
        user_name = profile.display_name or "there"

        # Check for priority-based context (new system)
        message_context = getattr(context, 'message_context', None)

        if message_context and hasattr(message_context, 'priority'):
            return cls._build_priority_message_prompt(
                context, message_context, user_name, style_config
            )

        # Fallback: Legacy behavior for backward compatibility
        follow_ups = [
            item for item in context.user_context if item.category in ("event", "goal", "situation")
        ]

        follow_up_str = ""
        if follow_ups:
            follow_up_str = "Things you might want to ask about:\n"
            for item in follow_ups[:3]:
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
    def _build_priority_message_prompt(
        cls,
        context: ConversationContext,
        message_context,
        user_name: str,
        style_config: dict,
    ) -> str:
        """Build prompt based on message priority.

        Priority Stack:
        1. FOLLOW_UP - Ask about something specific from recent conversation
        2. THREAD - Reference ongoing life situation
        3. PATTERN - Acknowledge mood/engagement pattern
        4. TEXTURE - Personal check-in with weather/context
        5. GENERIC - Warm fallback (FAILURE STATE)
        """
        from app.services.threads import MessagePriority

        priority = message_context.priority
        priority_instruction = ""

        if priority == MessagePriority.FOLLOW_UP:
            # Priority 1: Follow up on something specific
            follow_ups = message_context.follow_ups[:2]
            follow_up_text = "\n".join(
                f"- {fu['question']} (context: {fu['context']})"
                for fu in follow_ups
            )
            priority_instruction = f"""PRIORITY: Follow up on something specific.

The user mentioned something we should ask about:
{follow_up_text}

Your message MUST ask about one of these things naturally. This is the main point of the message.
Example: "Hey! How did that interview go yesterday?"
"""

        elif priority == MessagePriority.THREAD:
            # Priority 2: Reference ongoing thread
            threads = message_context.threads[:2]
            thread_text = "\n".join(
                f"- {t['topic']}: {t['summary']} (details: {', '.join(t.get('key_details', [])[:2])})"
                for t in threads
            )

            # Check for domain-specific follow-up prompt
            domain_prompt = getattr(message_context, 'domain_follow_up_prompt', None)
            if domain_prompt:
                priority_instruction = f"""PRIORITY: Reference an ongoing situation in their life.

Active threads:
{thread_text}

Use this domain-specific question as inspiration (adapt naturally to their details):
"{domain_prompt}"

Your message should feel natural and caring, not template-y.
"""
            else:
                priority_instruction = f"""PRIORITY: Reference an ongoing situation in their life.

Active threads to potentially reference:
{thread_text}

Your message should naturally check in on one of these situations.
Example: "How's the job search going this week?"
"""

        elif priority == MessagePriority.PATTERN:
            # Priority 3: Acknowledge pattern (mood, engagement)
            patterns = message_context.patterns[:2]
            pattern_text = "\n".join(f"- {p}" for p in patterns) if patterns else "None detected"
            priority_instruction = f"""PRIORITY: Acknowledge a pattern you've noticed.

Observed patterns:
{pattern_text}

Your message should gently acknowledge how they've been lately.
Example: "You've seemed a bit flat this week. Everything okay?"
"""

        elif priority == MessagePriority.TEXTURE:
            # Priority 4: Personal check-in with texture
            facts = message_context.core_facts[:3]
            fact_text = "\n".join(
                f"- {f.get('key', '')}: {f.get('value', '')}"
                for f in facts
            ) if facts else "None yet"
            priority_instruction = f"""PRIORITY: Personal check-in with contextual texture.

We don't have anything specific to follow up on, but we know:
{fact_text}

Use weather/day context to make the message feel grounded.
Example: "Morning. Rain today - good excuse to stay in. How are you feeling about the week?"
"""

        elif priority == MessagePriority.PRESENCE:
            # PRESENCE - intentional light touch (NOT a failure)
            priority_instruction = """PRIORITY: Simple presence message.

This is an intentional choice for variety, not a failure.
Just let them know you're thinking of them. Do NOT ask any questions.
Keep it warm, brief, and low-pressure.

Examples:
- "Thinking of you today."
- "Hope your week is going well."
- "Just wanted to say hi."
- "Sending good vibes your way."

IMPORTANT: Do NOT ask any questions. This is a no-ask message.
"""

        else:
            # Priority 5: Generic fallback (FAILURE STATE)
            priority_instruction = """PRIORITY: Generic warm check-in (FALLBACK MODE).

NOTE: We don't have anything personal to reference. This is not ideal.
Generate a warm but generic check-in message.
Example: "Hey, thinking of you. How's your morning going?"
"""

        # Build the full prompt
        prompt = f"""Generate a daily message for {user_name}.

Support style: {style_config['name']} - {style_config['description']}
Day: {context.day_of_week or 'Unknown'}
Time: {context.local_time or 'Morning'}
Weather: {context.weather_info or 'Unknown'}

{priority_instruction}

GUIDELINES:
- Brief (2-4 sentences max)
- Warm but not over-the-top
- One main topic/question
- Varies openings (don't always start with "Good morning!")
- Matches {style_config['morning_energy']} energy

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
