"""Chat Onboarding Service for Chat Companion.

Implements conversational onboarding flow as specified in ADR-003.
Handles the chat path: high-intent users who want to meet their companion immediately.

The flow:
1. intro - Companion introduces itself
2. name - Ask user's name
3. situation - What's going on in their life
4. support_style - What kind of support they want
5. wake_time - When they usually wake up
6. companion_name - What to call the companion
7. confirmation - Confirm and close

Each step saves data to appropriate locations:
- user profile fields (display_name, companion_name, preferred_message_time)
- user_context (core memory for facts, active threads for situations)
- preferences JSONB (support style, communication preferences)
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime
import json
import re

from app.services.llm import LLMService

log = logging.getLogger(__name__)


class OnboardingStep(str, Enum):
    """Steps in the chat onboarding flow."""
    INTRO = "intro"
    NAME = "name"
    SITUATION = "situation"
    SUPPORT_STYLE = "support_style"
    WAKE_TIME = "wake_time"
    COMPANION_NAME = "companion_name"
    CONFIRMATION = "confirmation"
    COMPLETE = "complete"


class SupportStyle(str, Enum):
    """Support style preferences."""
    FRIENDLY_CHECKIN = "friendly_checkin"
    MOTIVATIONAL = "motivational"
    ACCOUNTABILITY = "accountability"
    LISTENER = "listener"


@dataclass
class OnboardingMessage:
    """A message in the onboarding flow."""
    step: OnboardingStep
    companion_message: str
    expects: Optional[str]  # 'acknowledgment', 'name', 'free_text', 'choice', 'time', None
    options: Optional[List[str]] = None
    saves_to: Optional[str] = None


# Chat onboarding flow configuration
CHAT_ONBOARDING_FLOW: Dict[OnboardingStep, OnboardingMessage] = {
    OnboardingStep.INTRO: OnboardingMessage(
        step=OnboardingStep.INTRO,
        companion_message="Hey! I'm going to text you every morning - but I want it to actually matter to you, not just generic 'have a great day' stuff. Can I ask you a few things?",
        expects="acknowledgment",
    ),
    OnboardingStep.NAME: OnboardingMessage(
        step=OnboardingStep.NAME,
        companion_message="What should I call you?",
        expects="name",
        saves_to="display_name",
    ),
    OnboardingStep.SITUATION: OnboardingMessage(
        step=OnboardingStep.SITUATION,
        companion_message="Nice to meet you, {name}! What's going on in your life right now? New job, new city, just getting through the days - whatever it is.",
        expects="free_text",
        saves_to="user_context.thread.current_situation",
    ),
    OnboardingStep.SUPPORT_STYLE: OnboardingMessage(
        step=OnboardingStep.SUPPORT_STYLE,
        companion_message="Got it. And when you wake up, what would actually help - a little motivation, someone to help you think through your day, or just a friendly 'hey, I'm thinking of you'?",
        expects="choice",
        options=["motivation", "reflection", "friendly"],
        saves_to="preferences.support.style",
    ),
    OnboardingStep.WAKE_TIME: OnboardingMessage(
        step=OnboardingStep.WAKE_TIME,
        companion_message="One more - what time do you usually wake up? I want to catch you at the right moment.",
        expects="time",
        saves_to="preferred_message_time",
    ),
    OnboardingStep.COMPANION_NAME: OnboardingMessage(
        step=OnboardingStep.COMPANION_NAME,
        companion_message="Last thing - what would you like to call me? Pick a name that feels right.",
        expects="name",
        saves_to="companion_name",
    ),
    OnboardingStep.CONFIRMATION: OnboardingMessage(
        step=OnboardingStep.CONFIRMATION,
        companion_message="Okay {name}, I'll text you tomorrow around {time}. Talk soon!",
        expects=None,
    ),
}

# Step order for progression
STEP_ORDER = [
    OnboardingStep.INTRO,
    OnboardingStep.NAME,
    OnboardingStep.SITUATION,
    OnboardingStep.SUPPORT_STYLE,
    OnboardingStep.WAKE_TIME,
    OnboardingStep.COMPANION_NAME,
    OnboardingStep.CONFIRMATION,
    OnboardingStep.COMPLETE,
]

# Support style mapping from user choices
SUPPORT_STYLE_MAPPING = {
    "motivation": SupportStyle.MOTIVATIONAL,
    "reflection": SupportStyle.LISTENER,
    "friendly": SupportStyle.FRIENDLY_CHECKIN,
}

# Default preferences based on support style
DEFAULT_PREFERENCES_BY_STYLE = {
    SupportStyle.FRIENDLY_CHECKIN: {
        "support": {
            "style": "friendly_checkin",
            "feedback_type": "validation",
            "questions": "moderate",
        },
        "communication": {
            "message_tone": "warm",
        },
    },
    SupportStyle.MOTIVATIONAL: {
        "support": {
            "style": "motivational",
            "feedback_type": "balanced",
            "questions": "moderate",
        },
        "communication": {
            "message_tone": "energetic",
        },
    },
    SupportStyle.ACCOUNTABILITY: {
        "support": {
            "style": "accountability",
            "feedback_type": "challenge",
            "questions": "few",
        },
        "communication": {
            "message_tone": "energetic",
        },
    },
    SupportStyle.LISTENER: {
        "support": {
            "style": "listener",
            "feedback_type": "validation",
            "questions": "many",
        },
        "communication": {
            "message_tone": "gentle",
        },
    },
}


class ChatOnboardingService:
    """Service for managing chat-based onboarding flow."""

    def __init__(self, db):
        self.db = db
        self.llm = LLMService.get_instance()

    async def get_or_create_state(self, user_id: UUID) -> Dict[str, Any]:
        """Get current onboarding state or create new one."""
        result = await self.db.fetch_one(
            """
            SELECT user_id, current_step, completed_at, data, created_at, updated_at
            FROM onboarding
            WHERE user_id = :user_id
            """,
            {"user_id": str(user_id)},
        )

        if not result:
            await self.db.execute(
                """
                INSERT INTO onboarding (user_id, current_step, data)
                VALUES (:user_id, 'intro', '{}')
                ON CONFLICT (user_id) DO NOTHING
                """,
                {"user_id": str(user_id)},
            )
            result = await self.db.fetch_one(
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

        return {
            "user_id": str(result["user_id"]),
            "current_step": result["current_step"],
            "completed_at": result["completed_at"],
            "data": data or {},
            "created_at": result["created_at"],
            "updated_at": result["updated_at"],
        }

    async def get_current_message(self, user_id: UUID) -> Dict[str, Any]:
        """Get the current onboarding message for the user.

        Returns:
            Dict with 'message', 'step', 'expects', 'options', 'is_complete'
        """
        state = await self.get_or_create_state(user_id)
        current_step = state["current_step"]
        data = state["data"]

        # Check if already complete
        if current_step == OnboardingStep.COMPLETE.value or state["completed_at"]:
            return {
                "message": None,
                "step": "complete",
                "expects": None,
                "options": None,
                "is_complete": True,
            }

        try:
            step_enum = OnboardingStep(current_step)
        except ValueError:
            step_enum = OnboardingStep.INTRO

        flow_item = CHAT_ONBOARDING_FLOW.get(step_enum)
        if not flow_item:
            return {
                "message": None,
                "step": current_step,
                "expects": None,
                "options": None,
                "is_complete": True,
            }

        # Format message with user data
        message = flow_item.companion_message
        if "{name}" in message:
            name = data.get("display_name", "there")
            message = message.replace("{name}", name)
        if "{time}" in message:
            time = data.get("preferred_message_time", "8am")
            message = message.replace("{time}", self._format_time_display(time))

        return {
            "message": message,
            "step": current_step,
            "expects": flow_item.expects,
            "options": flow_item.options,
            "is_complete": False,
        }

    async def process_response(
        self,
        user_id: UUID,
        user_response: str,
    ) -> Dict[str, Any]:
        """Process user response and advance onboarding.

        Args:
            user_id: User ID
            user_response: User's text response

        Returns:
            Dict with 'success', 'next_message', 'step', 'is_complete', 'error'
        """
        state = await self.get_or_create_state(user_id)
        current_step = state["current_step"]
        data = state["data"]

        try:
            step_enum = OnboardingStep(current_step)
        except ValueError:
            return {
                "success": False,
                "error": f"Unknown step: {current_step}",
            }

        flow_item = CHAT_ONBOARDING_FLOW.get(step_enum)
        if not flow_item:
            return {"success": True, "is_complete": True}

        # Parse and validate response based on expected type
        parsed_value, validation_error = await self._parse_response(
            user_response,
            flow_item.expects,
            flow_item.options,
        )

        if validation_error:
            # Return helpful error but don't advance
            return {
                "success": False,
                "error": validation_error,
                "step": current_step,
                "retry_message": self._get_retry_message(flow_item.expects),
            }

        # Save the parsed value
        if flow_item.saves_to and parsed_value is not None:
            await self._save_value(user_id, flow_item.saves_to, parsed_value, data)
            data[flow_item.saves_to.split(".")[-1]] = parsed_value

        # Advance to next step
        next_step = self._get_next_step(step_enum)

        await self.db.execute(
            """
            UPDATE onboarding
            SET current_step = :step, data = data || :data::jsonb, updated_at = NOW()
            WHERE user_id = :user_id
            """,
            {
                "user_id": str(user_id),
                "step": next_step.value,
                "data": json.dumps(data),
            },
        )

        # If we've reached confirmation, mark complete
        if next_step == OnboardingStep.COMPLETE:
            await self._complete_onboarding(user_id, data)
            return {
                "success": True,
                "is_complete": True,
                "step": "complete",
                "next_message": None,
            }

        # Get next message
        next_result = await self.get_current_message(user_id)

        return {
            "success": True,
            "is_complete": next_result["is_complete"],
            "step": next_result["step"],
            "next_message": next_result["message"],
            "expects": next_result["expects"],
            "options": next_result["options"],
        }

    async def _parse_response(
        self,
        response: str,
        expects: Optional[str],
        options: Optional[List[str]],
    ) -> tuple[Optional[Any], Optional[str]]:
        """Parse user response based on expected type.

        Returns:
            (parsed_value, error_message) - error is None if valid
        """
        if expects is None or expects == "acknowledgment":
            return response.strip(), None

        response = response.strip()

        if expects == "name":
            # Accept reasonable name (1-50 chars, letters/spaces/hyphens)
            if not response:
                return None, "Please enter a name."
            if len(response) > 50:
                return None, "That name is a bit long. How about something shorter?"
            # Basic sanitization
            name = re.sub(r'[^\w\s\-\']', '', response).strip()
            if not name:
                return None, "Please enter a valid name."
            return name, None

        elif expects == "free_text":
            if not response:
                return None, "I'd love to hear more. Feel free to share anything."
            return response[:1000], None  # Limit length

        elif expects == "choice":
            if not options:
                return response, None
            # Try to match response to options
            response_lower = response.lower()
            for option in options:
                if option.lower() in response_lower or response_lower in option.lower():
                    return option, None
            # Use LLM to interpret if no direct match
            interpreted = await self._interpret_choice(response, options)
            if interpreted:
                return interpreted, None
            return options[0], None  # Default to first option

        elif expects == "time":
            # Parse time from natural language
            parsed_time = self._parse_time(response)
            if parsed_time:
                return parsed_time, None
            return None, "I didn't quite catch that time. Try something like '7am' or '8:30'."

        return response, None

    async def _interpret_choice(
        self,
        response: str,
        options: List[str],
    ) -> Optional[str]:
        """Use LLM to interpret user's choice if not a direct match."""
        try:
            prompt = f"""The user was asked to choose between these options: {options}
Their response was: "{response}"

Which option does their response most closely match? Respond with just the option word, nothing else.
If their response doesn't match any option, respond with the most appropriate default."""

            result = await self.llm.generate(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=50,
            )

            interpreted = result.content.strip().lower()
            for option in options:
                if option.lower() == interpreted or option.lower() in interpreted:
                    return option

            return None
        except Exception as e:
            log.warning(f"Failed to interpret choice: {e}")
            return None

    def _parse_time(self, response: str) -> Optional[str]:
        """Parse time from natural language to HH:MM format."""
        response = response.lower().strip()

        # Common patterns
        patterns = [
            # "7am", "7 am", "7:00am", "7:00 am"
            r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)',
            # "7:00", "07:00"
            r'(\d{1,2}):(\d{2})',
            # Just "7" or "07"
            r'^(\d{1,2})$',
        ]

        for pattern in patterns:
            match = re.search(pattern, response)
            if match:
                groups = match.groups()
                hour = int(groups[0])
                minute = int(groups[1]) if groups[1] else 0

                # Handle AM/PM
                if len(groups) > 2 and groups[2]:
                    if groups[2] == 'pm' and hour < 12:
                        hour += 12
                    elif groups[2] == 'am' and hour == 12:
                        hour = 0

                # Default assumption: if no AM/PM and hour <= 11, assume AM for wake times
                elif hour <= 11:
                    pass  # Keep as is (AM)

                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    return f"{hour:02d}:{minute:02d}"

        # Natural language
        time_words = {
            "sunrise": "06:00",
            "early": "06:00",
            "dawn": "06:00",
            "morning": "08:00",
            "late morning": "10:00",
            "noon": "12:00",
            "afternoon": "14:00",
        }
        for word, time_val in time_words.items():
            if word in response:
                return time_val

        return None

    def _format_time_display(self, time_str: str) -> str:
        """Format HH:MM to display format like '8am' or '7:30am'."""
        try:
            hour, minute = map(int, time_str.split(":"))
            period = "am" if hour < 12 else "pm"
            display_hour = hour if hour <= 12 else hour - 12
            if display_hour == 0:
                display_hour = 12
            if minute == 0:
                return f"{display_hour}{period}"
            return f"{display_hour}:{minute:02d}{period}"
        except:
            return time_str

    def _get_retry_message(self, expects: Optional[str]) -> str:
        """Get a friendly retry message based on expected input type."""
        messages = {
            "name": "Just type a name - whatever you'd like to be called!",
            "time": "Try something like '7am' or '8:30 am'",
            "choice": "Just pick whichever feels right to you",
            "free_text": "Feel free to share whatever's on your mind",
        }
        return messages.get(expects, "Could you try that again?")

    def _get_next_step(self, current: OnboardingStep) -> OnboardingStep:
        """Get the next step in the flow."""
        try:
            current_idx = STEP_ORDER.index(current)
            if current_idx < len(STEP_ORDER) - 1:
                return STEP_ORDER[current_idx + 1]
        except ValueError:
            pass
        return OnboardingStep.COMPLETE

    async def _save_value(
        self,
        user_id: UUID,
        saves_to: str,
        value: Any,
        current_data: Dict,
    ):
        """Save a value to the appropriate location."""
        parts = saves_to.split(".")

        if saves_to == "display_name":
            await self.db.execute(
                "UPDATE users SET display_name = :value, updated_at = NOW() WHERE id = :user_id",
                {"user_id": str(user_id), "value": value},
            )
            current_data["display_name"] = value

        elif saves_to == "companion_name":
            await self.db.execute(
                "UPDATE users SET companion_name = :value, updated_at = NOW() WHERE id = :user_id",
                {"user_id": str(user_id), "value": value},
            )
            current_data["companion_name"] = value

        elif saves_to == "preferred_message_time":
            await self.db.execute(
                "UPDATE users SET preferred_message_time = :value, updated_at = NOW() WHERE id = :user_id",
                {"user_id": str(user_id), "value": value},
            )
            current_data["preferred_message_time"] = value

        elif saves_to.startswith("user_context."):
            # Save to user_context table (memory system)
            # Format: user_context.tier.key or user_context.thread.key
            tier = parts[1] if len(parts) > 1 else "core"
            key = parts[2] if len(parts) > 2 else parts[1]

            await self.db.execute(
                """
                INSERT INTO user_context (user_id, category, key, value, tier, source, importance_score)
                VALUES (:user_id, :category, :key, :value, :tier, 'onboarding', 0.9)
                ON CONFLICT (user_id, category, key)
                DO UPDATE SET value = EXCLUDED.value, tier = EXCLUDED.tier, updated_at = NOW()
                """,
                {
                    "user_id": str(user_id),
                    "category": "situation" if tier == "thread" else "fact",
                    "key": key,
                    "value": value,
                    "tier": tier,
                },
            )

        elif saves_to.startswith("preferences."):
            # Save to user preferences JSONB
            support_style = SUPPORT_STYLE_MAPPING.get(value, SupportStyle.FRIENDLY_CHECKIN)
            prefs = DEFAULT_PREFERENCES_BY_STYLE.get(support_style, {})

            await self.db.execute(
                """
                UPDATE users
                SET preferences = preferences || :prefs::jsonb, updated_at = NOW()
                WHERE id = :user_id
                """,
                {
                    "user_id": str(user_id),
                    "prefs": json.dumps(prefs),
                },
            )
            current_data["support_style"] = value

    async def _complete_onboarding(self, user_id: UUID, data: Dict):
        """Mark onboarding as complete and finalize user setup."""
        # Update onboarding record
        await self.db.execute(
            """
            UPDATE onboarding
            SET completed_at = NOW(), current_step = 'complete', updated_at = NOW()
            WHERE user_id = :user_id
            """,
            {"user_id": str(user_id)},
        )

        # Update user record
        await self.db.execute(
            """
            UPDATE users
            SET onboarding_completed_at = NOW(),
                onboarding_path = 'chat',
                updated_at = NOW()
            WHERE id = :user_id
            """,
            {"user_id": str(user_id)},
        )

        # Ensure we have defaults if anything was skipped
        companion_name = data.get("companion_name", "Aria")
        if not data.get("companion_name"):
            await self.db.execute(
                "UPDATE users SET companion_name = :name WHERE id = :user_id AND companion_name IS NULL",
                {"user_id": str(user_id), "name": companion_name},
            )

        log.info(f"Chat onboarding completed for user {user_id}")

    async def skip_to_step(self, user_id: UUID, step: str) -> Dict[str, Any]:
        """Skip to a specific step (for testing/admin)."""
        try:
            step_enum = OnboardingStep(step)
        except ValueError:
            return {"success": False, "error": f"Invalid step: {step}"}

        await self.db.execute(
            """
            UPDATE onboarding
            SET current_step = :step, updated_at = NOW()
            WHERE user_id = :user_id
            """,
            {"user_id": str(user_id), "step": step},
        )

        return await self.get_current_message(user_id)

    async def reset_onboarding(self, user_id: UUID) -> Dict[str, Any]:
        """Reset onboarding to start (for testing/admin)."""
        await self.db.execute(
            """
            UPDATE onboarding
            SET current_step = 'intro', data = '{}', completed_at = NULL, updated_at = NOW()
            WHERE user_id = :user_id
            """,
            {"user_id": str(user_id)},
        )

        return await self.get_current_message(user_id)
