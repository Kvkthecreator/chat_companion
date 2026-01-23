"""Conversation service for Chat Companion.

Simple conversation management for the push-based AI companion.
Handles message storage, context retrieval, and conversation flow.
"""

import json
import logging
from typing import AsyncIterator, Dict, List, Optional
from uuid import UUID

from app.services.llm import LLMService
from app.services.context import ContextService
from app.services.threads import ThreadService

log = logging.getLogger(__name__)


class ConversationService:
    """Service for managing companion conversations."""

    def __init__(self, db):
        self.db = db
        self.llm = LLMService.get_instance()
        self.context_service = ContextService(db)

    async def send_message(
        self,
        user_id: UUID,
        conversation_id: UUID,
        content: str,
    ) -> Dict:
        """Send a message and get a response.

        Args:
            user_id: User UUID
            conversation_id: Conversation UUID
            content: User message content

        Returns:
            Assistant message dict with id, role, content, created_at
        """
        # Save user message
        user_message = await self._save_message(
            conversation_id=conversation_id,
            role="user",
            content=content,
        )

        # Build context for LLM
        messages = await self._build_messages(user_id, conversation_id)

        # Generate response
        llm_response = await self.llm.generate(messages)

        # Save assistant message
        assistant_message = await self._save_message(
            conversation_id=conversation_id,
            role="assistant",
            content=llm_response.content,
        )

        # Update conversation message count
        await self.db.execute(
            """
            UPDATE conversations
            SET message_count = message_count + 2, updated_at = NOW()
            WHERE id = :conversation_id
            """,
            {"conversation_id": str(conversation_id)},
        )

        # Extract context in background (don't block response)
        try:
            recent_messages = await self._get_recent_messages(conversation_id, limit=10)
            context_items, mood = await self.context_service.extract_context(
                user_id, conversation_id, recent_messages
            )
            if context_items:
                await self.context_service.save_context(user_id, context_items)
        except Exception as e:
            log.warning(f"Context extraction failed: {e}")

        # Extract threads for follow-ups and ongoing situation tracking
        try:
            thread_service = ThreadService(self.db)
            await thread_service.extract_from_conversation(user_id, recent_messages)
        except Exception as e:
            log.warning(f"Thread extraction failed: {e}")

        return {
            "id": str(assistant_message["id"]),
            "role": "assistant",
            "content": assistant_message["content"],
            "created_at": assistant_message["created_at"].isoformat(),
        }

    async def send_message_stream(
        self,
        user_id: UUID,
        conversation_id: UUID,
        content: str,
    ) -> AsyncIterator[str]:
        """Send a message and stream the response.

        Args:
            user_id: User UUID
            conversation_id: Conversation UUID
            content: User message content

        Yields:
            JSON strings with type "chunk" or "done"
        """
        # Save user message
        await self._save_message(
            conversation_id=conversation_id,
            role="user",
            content=content,
        )

        # Build context for LLM
        messages = await self._build_messages(user_id, conversation_id)

        # Stream response
        full_response = []
        async for chunk in self.llm.generate_stream(messages):
            full_response.append(chunk)
            yield json.dumps({"type": "chunk", "content": chunk})

        response_content = "".join(full_response)

        # Save assistant message
        assistant_message = await self._save_message(
            conversation_id=conversation_id,
            role="assistant",
            content=response_content,
        )

        # Update conversation message count
        await self.db.execute(
            """
            UPDATE conversations
            SET message_count = message_count + 2, updated_at = NOW()
            WHERE id = :conversation_id
            """,
            {"conversation_id": str(conversation_id)},
        )

        # Yield done event
        yield json.dumps({
            "type": "done",
            "content": response_content,
            "message_id": str(assistant_message["id"]),
        })

        # Extract context in background
        try:
            recent_messages = await self._get_recent_messages(conversation_id, limit=10)
            context_items, mood = await self.context_service.extract_context(
                user_id, conversation_id, recent_messages
            )
            if context_items:
                await self.context_service.save_context(user_id, context_items)
        except Exception as e:
            log.warning(f"Context extraction failed: {e}")

        # Extract threads for follow-ups and ongoing situation tracking
        try:
            thread_service = ThreadService(self.db)
            await thread_service.extract_from_conversation(user_id, recent_messages)
        except Exception as e:
            log.warning(f"Thread extraction failed: {e}")

    async def get_or_create_conversation(
        self,
        user_id: UUID,
        channel: str = "web",
        initiated_by: str = "user",
    ) -> Dict:
        """Get active conversation or create a new one.

        Args:
            user_id: User UUID
            channel: Channel (web, telegram, whatsapp)
            initiated_by: Who started (user, companion)

        Returns:
            Conversation dict
        """
        # Check for existing active conversation today
        query = """
            SELECT * FROM conversations
            WHERE user_id = :user_id
            AND channel = :channel
            AND DATE(started_at) = CURRENT_DATE
            AND ended_at IS NULL
            ORDER BY started_at DESC
            LIMIT 1
        """
        row = await self.db.fetch_one(query, {
            "user_id": str(user_id),
            "channel": channel,
        })

        if row:
            return dict(row)

        # Create new conversation
        insert_query = """
            INSERT INTO conversations (user_id, channel, initiated_by)
            VALUES (:user_id, :channel, :initiated_by)
            RETURNING *
        """
        new_row = await self.db.fetch_one(insert_query, {
            "user_id": str(user_id),
            "channel": channel,
            "initiated_by": initiated_by,
        })

        return dict(new_row)

    async def get_conversation(self, conversation_id: UUID) -> Optional[Dict]:
        """Get conversation by ID."""
        query = "SELECT * FROM conversations WHERE id = :conversation_id"
        row = await self.db.fetch_one(query, {"conversation_id": str(conversation_id)})
        return dict(row) if row else None

    async def list_conversations(
        self,
        user_id: UUID,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Dict]:
        """List conversations for a user, ordered by most recent."""
        query = """
            SELECT * FROM conversations
            WHERE user_id = :user_id
            ORDER BY started_at DESC
            LIMIT :limit OFFSET :offset
        """
        rows = await self.db.fetch_all(query, {
            "user_id": str(user_id),
            "limit": limit,
            "offset": offset,
        })
        return [dict(row) for row in rows]

    async def end_conversation(
        self,
        conversation_id: UUID,
    ) -> Optional[Dict]:
        """End a conversation and generate summary."""
        # Get messages for summary
        messages = await self._get_recent_messages(conversation_id, limit=50)

        if not messages:
            return None

        # Generate summary
        summary_data = await self.context_service.generate_conversation_summary(messages)

        # Update conversation
        update_query = """
            UPDATE conversations
            SET
                ended_at = NOW(),
                mood_summary = :mood,
                topics = :topics
            WHERE id = :conversation_id
            RETURNING *
        """
        row = await self.db.fetch_one(update_query, {
            "conversation_id": str(conversation_id),
            "mood": summary_data.get("mood"),
            "topics": json.dumps(summary_data.get("topics", [])),
        })

        return dict(row) if row else None

    async def get_messages(
        self,
        conversation_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict]:
        """Get messages for a conversation."""
        query = """
            SELECT id, role, content, created_at
            FROM messages
            WHERE conversation_id = :conversation_id
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """
        rows = await self.db.fetch_all(query, {
            "conversation_id": str(conversation_id),
            "limit": limit,
            "offset": offset,
        })
        # Return in chronological order
        return [dict(row) for row in reversed(rows)]

    async def _build_messages(
        self,
        user_id: UUID,
        conversation_id: UUID,
    ) -> List[Dict[str, str]]:
        """Build messages list for LLM including system prompt and context."""
        # Get user settings
        user_query = """
            SELECT display_name, companion_name, support_style, timezone, location
            FROM users
            WHERE id = :user_id
        """
        user_row = await self.db.fetch_one(user_query, {"user_id": str(user_id)})

        display_name = user_row["display_name"] if user_row else "friend"
        companion_name = user_row["companion_name"] if user_row else "Aria"
        support_style = user_row["support_style"] if user_row else "supportive"
        timezone = user_row["timezone"] if user_row else "UTC"
        location = user_row["location"] if user_row else None

        # Get user context
        context_text = await self.context_service.get_context_for_prompt(user_id)

        # Build system prompt
        system_prompt = self._build_system_prompt(
            companion_name=companion_name,
            user_name=display_name,
            support_style=support_style,
            context=context_text,
            timezone=timezone,
            location=location,
        )

        messages = [{"role": "system", "content": system_prompt}]

        # Get recent messages
        recent = await self._get_recent_messages(conversation_id, limit=20)
        for msg in recent:
            messages.append({
                "role": msg["role"],
                "content": msg["content"],
            })

        return messages

    def _build_system_prompt(
        self,
        companion_name: str,
        user_name: str,
        support_style: str,
        context: str,
        timezone: str,
        location: Optional[str] = None,
    ) -> str:
        """Build the companion's system prompt."""
        style_descriptions = {
            "supportive": "warm, encouraging, and affirming",
            "direct": "honest, straightforward, and practical",
            "curious": "interested, thoughtful, and exploratory",
            "playful": "light-hearted, fun, and witty",
        }
        style_desc = style_descriptions.get(support_style, style_descriptions["supportive"])

        location_context = f"\nTheir location: {location}" if location else ""

        return f"""You are {companion_name}, a caring AI companion for {user_name}.

Your communication style is {style_desc}. You genuinely care about {user_name}'s wellbeing and want to be a supportive presence in their life.

WHAT YOU KNOW ABOUT {user_name.upper()}:
{context}

Their timezone: {timezone}{location_context}

GUIDELINES:
- Be genuinely interested in how they're doing
- Remember details they share and reference them naturally
- Keep responses concise (2-3 sentences usually)
- Ask follow-up questions to show you care
- Celebrate their wins, no matter how small
- Be supportive during tough times without being preachy
- Use their name occasionally to feel more personal
- Match their energy - if they're brief, be brief; if they want to chat, engage fully

You're not a therapist or life coach - you're a caring friend who checks in regularly."""

    async def _save_message(
        self,
        conversation_id: UUID,
        role: str,
        content: str,
    ) -> Dict:
        """Save a message to the database."""
        query = """
            INSERT INTO messages (conversation_id, role, content)
            VALUES (:conversation_id, :role, :content)
            RETURNING id, conversation_id, role, content, created_at
        """
        row = await self.db.fetch_one(query, {
            "conversation_id": str(conversation_id),
            "role": role,
            "content": content,
        })
        return dict(row)

    async def _get_recent_messages(
        self,
        conversation_id: UUID,
        limit: int = 20,
    ) -> List[Dict]:
        """Get recent messages for context building."""
        query = """
            SELECT role, content
            FROM messages
            WHERE conversation_id = :conversation_id
            ORDER BY created_at DESC
            LIMIT :limit
        """
        rows = await self.db.fetch_all(query, {
            "conversation_id": str(conversation_id),
            "limit": limit,
        })
        return [dict(row) for row in reversed(rows)]
