"""User context extraction and retrieval service for Chat Companion.

This service extracts and manages user context - remembered facts, preferences,
goals, and situations from conversations. This is the companion's "memory"
of who the user is and what's going on in their life.
"""

import json
import logging
from typing import Dict, List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from app.services.llm import LLMService

log = logging.getLogger(__name__)


class ContextCategory(str, Enum):
    """Categories of user context."""
    FACT = "fact"  # Personal facts (name, job, location)
    PREFERENCE = "preference"  # Likes, dislikes, preferences
    EVENT = "event"  # Upcoming or past significant events
    GOAL = "goal"  # Things they're working toward
    RELATIONSHIP = "relationship"  # People in their life
    EMOTION = "emotion"  # Recurring emotional states
    SITUATION = "situation"  # Ongoing life situations
    ROUTINE = "routine"  # Daily habits and routines
    STRUGGLE = "struggle"  # Challenges they're facing


@dataclass
class ExtractedContext:
    """A piece of context extracted from conversation."""
    category: ContextCategory
    key: str  # Unique key within category (e.g., "job", "pet_name")
    value: str  # The actual information
    importance_score: float  # 0.0-1.0
    emotional_valence: int  # -2 to +2
    expires_in_days: Optional[int] = None  # For time-bound context


CONTEXT_EXTRACTION_PROMPT = """Analyze this conversation and extract important information about the user to remember.

CONVERSATION:
{conversation}

Extract context in these categories:
- fact: Personal facts (name, job, location, age, pets, hobbies)
- preference: Likes, dislikes, preferences
- event: Upcoming or past significant events (meeting tomorrow, birthday next week)
- goal: Goals, aspirations, things they're working toward
- relationship: People in their life (friends, family, partner)
- emotion: Recurring emotional states or feelings
- situation: Ongoing life situations (job search, moving, breakup)
- routine: Daily habits and routines
- struggle: Challenges they're facing

EXISTING CONTEXT (don't extract duplicates):
{existing_context}

For each NEW piece of context, provide:
- category: One of the categories above
- key: A unique identifier (e.g., "job", "pet_cat", "meeting_tomorrow")
- value: A concise statement of the information
- importance_score: 0.0-1.0 (how important to remember?)
- emotional_valence: -2 to +2 (negative to positive association)
- expires_in_days: For time-bound things (e.g., 1 for "meeting tomorrow"), null otherwise

Only extract information that would help a caring friend remember important things about the user's life.

Respond with JSON:
{{
    "context": [
        {{
            "category": "...",
            "key": "...",
            "value": "...",
            "importance_score": 0.5,
            "emotional_valence": 0,
            "expires_in_days": null
        }}
    ],
    "mood_summary": "Brief description of how the user seems to be feeling in this conversation"
}}
"""

CONVERSATION_SUMMARY_PROMPT = """Summarize this conversation between a user and their AI companion.

CONVERSATION:
{conversation}

Provide:
1. A brief 1-2 sentence summary
2. Topics discussed
3. Overall mood (happy, sad, anxious, hopeful, stressed, neutral, etc.)

Respond with JSON:
{{
    "summary": "...",
    "topics": ["...", "..."],
    "mood": "..."
}}
"""


class ContextService:
    """Service for user context extraction and retrieval."""

    def __init__(self, db):
        self.db = db
        self.llm = LLMService.get_instance()

    async def extract_context(
        self,
        user_id: UUID,
        conversation_id: UUID,
        messages: List[Dict[str, str]],
    ) -> tuple[List[ExtractedContext], Optional[str]]:
        """Extract user context from a conversation exchange.

        Returns:
            tuple: (list of ExtractedContext, mood_summary or None)
        """
        if len(messages) < 2:
            return [], None

        # Format conversation
        conversation = self._format_conversation(messages[-10:])

        # Get existing context
        existing = await self.get_user_context(user_id, limit=30)
        existing_text = "\n".join(
            f"- [{c['category']}:{c['key']}] {c['value']}"
            for c in existing
        ) or "None yet"

        prompt = CONTEXT_EXTRACTION_PROMPT.format(
            conversation=conversation,
            existing_context=existing_text,
        )

        try:
            result = await self.llm.extract_json(
                prompt=prompt,
                schema_description="""{
    "context": [
        {
            "category": "fact|preference|event|goal|relationship|emotion|situation|routine|struggle",
            "key": "string",
            "value": "string",
            "importance_score": 0.0-1.0,
            "emotional_valence": -2 to 2,
            "expires_in_days": number or null
        }
    ],
    "mood_summary": "string"
}""",
            )

            context_items = []
            mood_summary = result.get("mood_summary")

            for item in result.get("context", []):
                try:
                    ctx = ExtractedContext(
                        category=ContextCategory(item["category"].lower()),
                        key=item["key"],
                        value=item["value"],
                        importance_score=float(item.get("importance_score", 0.5)),
                        emotional_valence=int(item.get("emotional_valence", 0)),
                        expires_in_days=item.get("expires_in_days"),
                    )
                    context_items.append(ctx)
                except (KeyError, ValueError) as e:
                    log.warning(f"Failed to parse context: {e}")
                    continue

            return context_items, mood_summary

        except Exception as e:
            log.error(f"Context extraction failed: {e}")
            return [], None

    async def save_context(
        self,
        user_id: UUID,
        context_items: List[ExtractedContext],
    ) -> List[Dict]:
        """Save extracted context to database.

        Uses upsert to update existing context with same category+key.
        """
        saved = []

        for ctx in context_items:
            expires_at = None
            if ctx.expires_in_days:
                expires_at = datetime.utcnow() + timedelta(days=ctx.expires_in_days)

            # Upsert - update if same category+key exists
            query = """
                INSERT INTO user_context (
                    user_id, category, key, value,
                    importance_score, emotional_valence, source, expires_at
                )
                VALUES (
                    :user_id, :category, :key, :value,
                    :importance_score, :emotional_valence, 'extracted', :expires_at
                )
                ON CONFLICT (user_id, category, key)
                DO UPDATE SET
                    value = EXCLUDED.value,
                    importance_score = EXCLUDED.importance_score,
                    emotional_valence = EXCLUDED.emotional_valence,
                    expires_at = EXCLUDED.expires_at,
                    updated_at = NOW()
                RETURNING *
            """
            row = await self.db.fetch_one(
                query,
                {
                    "user_id": str(user_id),
                    "category": ctx.category.value,
                    "key": ctx.key,
                    "value": ctx.value,
                    "importance_score": ctx.importance_score,
                    "emotional_valence": ctx.emotional_valence,
                    "expires_at": expires_at,
                },
            )
            if row:
                saved.append(dict(row))

        return saved

    async def get_user_context(
        self,
        user_id: UUID,
        category: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict]:
        """Get user context for conversation generation.

        Returns context ordered by importance and recency, excluding expired items.
        """
        params = {"user_id": str(user_id), "limit": limit}

        category_filter = ""
        if category:
            category_filter = "AND category = :category"
            params["category"] = category

        query = f"""
            SELECT id, category, key, value, importance_score,
                   emotional_valence, source, created_at, updated_at,
                   last_referenced_at, expires_at
            FROM user_context
            WHERE user_id = :user_id
                AND (expires_at IS NULL OR expires_at > NOW())
                {category_filter}
            ORDER BY
                importance_score DESC,
                last_referenced_at DESC NULLS LAST,
                updated_at DESC
            LIMIT :limit
        """
        rows = await self.db.fetch_all(query, params)
        return [dict(row) for row in rows]

    async def get_context_for_prompt(
        self,
        user_id: UUID,
        limit: int = 15,
    ) -> str:
        """Get formatted context for inclusion in companion prompts."""
        context = await self.get_user_context(user_id, limit=limit)

        if not context:
            return "No context saved yet - this is a new user."

        # Group by category
        by_category: Dict[str, List[Dict]] = {}
        for item in context:
            cat = item["category"]
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(item)

        # Format for prompt
        lines = []
        category_labels = {
            "fact": "Personal Facts",
            "preference": "Preferences",
            "event": "Events",
            "goal": "Goals",
            "relationship": "People",
            "emotion": "Emotional State",
            "situation": "Current Situations",
            "routine": "Routines",
            "struggle": "Challenges",
        }

        for cat, items in by_category.items():
            label = category_labels.get(cat, cat.title())
            lines.append(f"\n{label}:")
            for item in items:
                lines.append(f"  - {item['value']}")

        return "\n".join(lines)

    async def mark_context_referenced(
        self,
        user_id: UUID,
        context_ids: List[UUID],
    ):
        """Mark context items as referenced (used in conversation)."""
        if not context_ids:
            return

        query = """
            UPDATE user_context
            SET last_referenced_at = NOW()
            WHERE id = ANY(:ids) AND user_id = :user_id
        """
        await self.db.execute(
            query,
            {"ids": [str(id) for id in context_ids], "user_id": str(user_id)},
        )

    async def delete_context(
        self,
        user_id: UUID,
        context_id: UUID,
    ) -> bool:
        """Delete a context item."""
        query = """
            DELETE FROM user_context
            WHERE id = :id AND user_id = :user_id
        """
        result = await self.db.execute(
            query,
            {"id": str(context_id), "user_id": str(user_id)},
        )
        return result is not None

    async def generate_conversation_summary(
        self,
        messages: List[Dict[str, str]],
    ) -> Dict:
        """Generate a summary for a conversation."""
        conversation = self._format_conversation(messages)

        prompt = CONVERSATION_SUMMARY_PROMPT.format(conversation=conversation)

        try:
            result = await self.llm.extract_json(
                prompt=prompt,
                schema_description="""{
    "summary": "string",
    "topics": ["string"],
    "mood": "string"
}""",
            )
            return result
        except Exception as e:
            log.error(f"Summary generation failed: {e}")
            return {
                "summary": None,
                "topics": [],
                "mood": "unknown",
            }

    async def update_conversation_summary(
        self,
        conversation_id: UUID,
        summary: Dict,
    ):
        """Update conversation with summary data."""
        query = """
            UPDATE conversations
            SET mood_summary = :mood,
                topics = :topics
            WHERE id = :id
        """
        await self.db.execute(
            query,
            {
                "id": str(conversation_id),
                "mood": summary.get("mood"),
                "topics": json.dumps(summary.get("topics", [])),
            },
        )

    def _format_conversation(self, messages: List[Dict[str, str]]) -> str:
        """Format messages for prompts."""
        lines = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if role == "user":
                lines.append(f"User: {content}")
            elif role == "assistant":
                lines.append(f"Companion: {content}")
        return "\n".join(lines)
