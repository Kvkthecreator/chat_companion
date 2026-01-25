"""Thread Tracking Service - Track ongoing situations in user's life.

This service implements thread tracking as described in MEMORY_SYSTEM.md:
- Detect ongoing situations from conversations
- Track follow-up dates and questions
- Provide priority-based context for message generation

Memory is the product - not content delivery.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from app.services.llm import LLMService

if TYPE_CHECKING:
    from app.services.patterns import PatternService

log = logging.getLogger(__name__)


# =============================================================================
# Enums and Data Classes
# =============================================================================


class ThreadStatus(str, Enum):
    """Status of a life thread."""
    ACTIVE = "active"           # Ongoing, should follow up
    WAITING = "waiting"         # Waiting for something (interview result, etc.)
    RESOLVED = "resolved"       # Situation concluded
    STALE = "stale"             # No updates in a while


class MessagePriority(int, Enum):
    """Message generation priority levels.

    Lower number = higher priority.
    PRESENCE is not a priority - it's an intentional choice for variety.
    """
    FOLLOW_UP = 1       # Specific follow-up from recent conversation
    THREAD = 2          # Reference ongoing life thread
    PATTERN = 3         # Acknowledge mood/engagement pattern
    TEXTURE = 4         # Personal check-in with contextual texture
    GENERIC = 5         # Fallback - no personal content (FAILURE STATE)
    PRESENCE = 6        # Intentional light touch - no question asked (NOT a failure)


@dataclass
class MessageContext:
    """Context for generating a daily message with priority information."""
    priority: MessagePriority
    follow_ups: List[Dict[str, Any]]    # Priority 1
    threads: List[Dict[str, Any]]       # Priority 2
    patterns: List[Dict[str, Any]]      # Priority 3 (mood trends, etc.)
    core_facts: List[Dict[str, Any]]    # Priority 4 texture
    has_personal_content: bool
    # Variety/state tracking
    topic_key: Optional[str] = None     # Key for deduplication
    user_responded_since_last: bool = True  # Did user respond to last outreach?
    force_presence: bool = False        # Force PRESENCE type for variety

    @property
    def is_generic_fallback(self) -> bool:
        """True if we have nothing personal to reference.

        This is a FAILURE STATE we should track.
        """
        return self.priority == MessagePriority.GENERIC


# =============================================================================
# Thread Extraction Prompt
# =============================================================================


THREAD_EXTRACTION_PROMPT = """Analyze this conversation and identify ongoing life situations to track.

A "thread" is an ongoing situation that:
- Spans multiple days or conversations
- Has a timeline or expected resolution
- The user would appreciate follow-up on

CONVERSATION:
{conversation}

EXISTING THREADS (avoid duplicates, but note updates):
{existing_threads}

Extract:

1. NEW THREADS - Situations worth tracking:
   - topic: Short identifier (job_interview, moving, health_checkup, family_visit)
   - summary: What's happening
   - status: active, waiting, or resolved
   - follow_up_date: When to ask about this (YYYY-MM-DD format, or null)
   - key_details: Important facts to remember

2. THREAD UPDATES - Changes to existing threads:
   - topic: Which thread to update
   - new_details: New information learned
   - new_status: Changed status (or null if unchanged)

3. FOLLOW-UP QUESTIONS - Specific things to ask:
   - question: What to ask ("How did the interview go?")
   - context: Why we're asking
   - follow_up_date: When to ask (YYYY-MM-DD)

Look for signals like:
- "I have X tomorrow/next week"
- "I'm working on..."
- "I'll let you know how it goes"
- Mentioned appointments, events, deadlines
- Ongoing situations (job search, moving, relationship issues)

Respond with JSON:
{{
    "threads": [
        {{
            "topic": "...",
            "summary": "...",
            "status": "active|waiting|resolved",
            "follow_up_date": "YYYY-MM-DD" or null,
            "key_details": ["...", "..."]
        }}
    ],
    "thread_updates": [
        {{
            "topic": "existing_topic",
            "new_details": ["..."],
            "new_status": "active|waiting|resolved" or null
        }}
    ],
    "follow_ups": [
        {{
            "question": "How did X go?",
            "context": "They mentioned X was happening Friday",
            "follow_up_date": "YYYY-MM-DD"
        }}
    ]
}}

If nothing to extract, return empty arrays.
"""


# =============================================================================
# Thread Service
# =============================================================================


class ThreadService:
    """Service for tracking ongoing life situations and generating follow-ups."""

    def __init__(self, db, pattern_service: Optional["PatternService"] = None):
        self.db = db
        self.llm = LLMService.get_instance()
        self._pattern_service = pattern_service

    @property
    def pattern_service(self) -> Optional["PatternService"]:
        """Lazy load pattern service to avoid circular imports."""
        if self._pattern_service is None:
            try:
                from app.services.patterns import PatternService
                self._pattern_service = PatternService(self.db)
            except ImportError:
                log.warning("PatternService not available")
        return self._pattern_service

    # -------------------------------------------------------------------------
    # Thread CRUD
    # -------------------------------------------------------------------------

    async def save_thread(
        self,
        user_id: UUID,
        topic: str,
        summary: str,
        status: ThreadStatus = ThreadStatus.ACTIVE,
        follow_up_date: Optional[datetime] = None,
        key_details: Optional[List[str]] = None,
    ) -> Optional[Dict]:
        """Save or update a life thread."""
        thread_id = uuid4()

        # Store thread data as JSON value
        thread_data = {
            "summary": summary,
            "status": status.value,
            "follow_up_date": follow_up_date.isoformat() if follow_up_date else None,
            "key_details": key_details or [],
        }

        # Threads expire after 30 days of no activity
        expires_at = datetime.utcnow() + timedelta(days=30)

        query = """
            INSERT INTO user_context (
                id, user_id, category, key, value, tier,
                importance_score, source, expires_at
            )
            VALUES (
                :id, :user_id, 'thread', :topic, :value, 'thread',
                0.9, 'extracted', :expires_at
            )
            ON CONFLICT (user_id, category, key)
            DO UPDATE SET
                value = EXCLUDED.value,
                expires_at = EXCLUDED.expires_at,
                updated_at = NOW()
            RETURNING *
        """

        row = await self.db.fetch_one(
            query,
            {
                "id": str(thread_id),
                "user_id": str(user_id),
                "topic": topic,
                "value": json.dumps(thread_data),
                "expires_at": expires_at,
            },
        )

        if row:
            log.info(f"Saved thread '{topic}' for user {user_id}")

        return dict(row) if row else None

    async def update_thread(
        self,
        user_id: UUID,
        topic: str,
        new_details: Optional[List[str]] = None,
        new_status: Optional[ThreadStatus] = None,
        new_follow_up_date: Optional[datetime] = None,
    ) -> bool:
        """Update an existing thread with new information."""
        current = await self.db.fetch_one(
            """
            SELECT value FROM user_context
            WHERE user_id = :user_id AND category = 'thread' AND key = :topic
            """,
            {"user_id": str(user_id), "topic": topic},
        )

        if not current:
            return False

        try:
            data = json.loads(current["value"])
        except:
            data = {"summary": "", "status": "active", "key_details": []}

        # Update fields
        if new_details:
            existing_details = data.get("key_details", [])
            data["key_details"] = existing_details + new_details

        if new_status:
            data["status"] = new_status.value

        if new_follow_up_date:
            data["follow_up_date"] = new_follow_up_date.isoformat()

        # Extend expiration
        expires_at = datetime.utcnow() + timedelta(days=30)

        await self.db.execute(
            """
            UPDATE user_context
            SET value = :value, expires_at = :expires_at, updated_at = NOW()
            WHERE user_id = :user_id AND category = 'thread' AND key = :topic
            """,
            {
                "user_id": str(user_id),
                "topic": topic,
                "value": json.dumps(data),
                "expires_at": expires_at,
            },
        )

        log.info(f"Updated thread '{topic}' for user {user_id}")
        return True

    async def get_active_threads(
        self,
        user_id: UUID,
        limit: int = 5,
    ) -> List[Dict]:
        """Get active threads for a user."""
        rows = await self.db.fetch_all(
            """
            SELECT id, key as topic, value, updated_at, expires_at
            FROM user_context
            WHERE user_id = :user_id
                AND category = 'thread'
                AND tier = 'thread'
                AND (expires_at IS NULL OR expires_at > NOW())
            ORDER BY updated_at DESC
            LIMIT :limit
            """,
            {"user_id": str(user_id), "limit": limit},
        )

        threads = []
        for row in rows:
            try:
                data = json.loads(row["value"])
                threads.append({
                    "id": row["id"],
                    "topic": row["topic"],
                    "summary": data.get("summary", ""),
                    "status": data.get("status", "active"),
                    "follow_up_date": data.get("follow_up_date"),
                    "key_details": data.get("key_details", []),
                    "updated_at": row["updated_at"],
                })
            except:
                continue

        return threads

    async def get_threads_needing_followup(
        self,
        user_id: UUID,
        as_of: Optional[datetime] = None,
    ) -> List[Dict]:
        """Get threads with follow-up dates that have passed."""
        as_of = as_of or datetime.utcnow()
        threads = await self.get_active_threads(user_id, limit=10)

        needing_followup = []
        for thread in threads:
            if thread.get("follow_up_date"):
                try:
                    follow_up_date = datetime.fromisoformat(thread["follow_up_date"])
                    if follow_up_date <= as_of and thread["status"] != "resolved":
                        needing_followup.append(thread)
                except:
                    continue

        return needing_followup

    # -------------------------------------------------------------------------
    # Follow-up Management
    # -------------------------------------------------------------------------

    async def save_follow_up(
        self,
        user_id: UUID,
        question: str,
        context: str,
        follow_up_date: datetime,
        source_thread_topic: Optional[str] = None,
    ) -> Optional[Dict]:
        """Save a pending follow-up question."""
        follow_up_id = uuid4()

        # Use question hash as key to avoid duplicates
        key = f"followup_{hash(question) % 100000}"

        follow_up_data = {
            "question": question,
            "context": context,
            "follow_up_date": follow_up_date.isoformat(),
            "source_thread": source_thread_topic,
            "asked": False,
        }

        # Expire 7 days after follow-up date
        expires_at = follow_up_date + timedelta(days=7)

        query = """
            INSERT INTO user_context (
                id, user_id, category, key, value, tier,
                importance_score, source, expires_at
            )
            VALUES (
                :id, :user_id, 'follow_up', :key, :value, 'thread',
                0.95, 'extracted', :expires_at
            )
            ON CONFLICT (user_id, category, key)
            DO UPDATE SET
                value = EXCLUDED.value,
                expires_at = EXCLUDED.expires_at,
                updated_at = NOW()
            RETURNING *
        """

        row = await self.db.fetch_one(
            query,
            {
                "id": str(follow_up_id),
                "user_id": str(user_id),
                "key": key,
                "value": json.dumps(follow_up_data),
                "expires_at": expires_at,
            },
        )

        if row:
            log.info(f"Saved follow-up question for user {user_id}: {question[:50]}...")

        return dict(row) if row else None

    async def get_pending_follow_ups(
        self,
        user_id: UUID,
        as_of: Optional[datetime] = None,
    ) -> List[Dict]:
        """Get follow-ups that are due and haven't been asked."""
        as_of = as_of or datetime.utcnow()

        rows = await self.db.fetch_all(
            """
            SELECT id, key, value, updated_at
            FROM user_context
            WHERE user_id = :user_id
                AND category = 'follow_up'
                AND (expires_at IS NULL OR expires_at > NOW())
            ORDER BY importance_score DESC, updated_at DESC
            LIMIT 10
            """,
            {"user_id": str(user_id)},
        )

        follow_ups = []
        for row in rows:
            try:
                data = json.loads(row["value"])
                follow_up_date = datetime.fromisoformat(data["follow_up_date"])

                # Only return if due and not already asked
                if follow_up_date <= as_of and not data.get("asked", False):
                    follow_ups.append({
                        "id": row["id"],
                        "question": data["question"],
                        "context": data["context"],
                        "follow_up_date": follow_up_date,
                        "source_thread": data.get("source_thread"),
                    })
            except:
                continue

        return follow_ups

    async def mark_follow_up_asked(self, follow_up_id: UUID) -> bool:
        """Mark a follow-up as asked."""
        row = await self.db.fetch_one(
            "SELECT value FROM user_context WHERE id = :id",
            {"id": str(follow_up_id)},
        )

        if not row:
            return False

        try:
            data = json.loads(row["value"])
            data["asked"] = True

            await self.db.execute(
                "UPDATE user_context SET value = :value WHERE id = :id",
                {"id": str(follow_up_id), "value": json.dumps(data)},
            )
            return True
        except:
            return False

    # -------------------------------------------------------------------------
    # Extraction from Conversations
    # -------------------------------------------------------------------------

    async def extract_from_conversation(
        self,
        user_id: UUID,
        messages: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """Extract threads and follow-ups from a conversation.

        Returns dict with counts of items created/updated.
        """
        if len(messages) < 2:
            return {"threads_created": 0, "threads_updated": 0, "follow_ups_created": 0}

        # Format conversation
        conversation = self._format_conversation(messages[-10:])

        # Get existing threads
        existing = await self.get_active_threads(user_id, limit=10)
        existing_text = "\n".join(
            f"- {t['topic']}: {t['summary']} (status: {t['status']})"
            for t in existing
        ) or "None"

        prompt = THREAD_EXTRACTION_PROMPT.format(
            conversation=conversation,
            existing_threads=existing_text,
        )

        try:
            result = await self.llm.extract_json(
                prompt=prompt,
                schema_description="""{
    "threads": [{"topic": "string", "summary": "string", "status": "string", "follow_up_date": "string|null", "key_details": ["string"]}],
    "thread_updates": [{"topic": "string", "new_details": ["string"], "new_status": "string|null"}],
    "follow_ups": [{"question": "string", "context": "string", "follow_up_date": "string"}]
}""",
            )
        except Exception as e:
            log.error(f"Thread extraction failed: {e}")
            return {"threads_created": 0, "threads_updated": 0, "follow_ups_created": 0}

        counts = {"threads_created": 0, "threads_updated": 0, "follow_ups_created": 0}

        # Save new threads
        for thread in result.get("threads", []):
            follow_up_date = None
            if thread.get("follow_up_date"):
                try:
                    follow_up_date = datetime.fromisoformat(thread["follow_up_date"])
                except:
                    pass

            try:
                status = ThreadStatus(thread.get("status", "active"))
            except:
                status = ThreadStatus.ACTIVE

            saved = await self.save_thread(
                user_id=user_id,
                topic=thread["topic"],
                summary=thread["summary"],
                status=status,
                follow_up_date=follow_up_date,
                key_details=thread.get("key_details", []),
            )
            if saved:
                counts["threads_created"] += 1

        # Update existing threads
        for update in result.get("thread_updates", []):
            new_status = None
            if update.get("new_status"):
                try:
                    new_status = ThreadStatus(update["new_status"])
                except:
                    pass

            updated = await self.update_thread(
                user_id=user_id,
                topic=update["topic"],
                new_details=update.get("new_details"),
                new_status=new_status,
            )
            if updated:
                counts["threads_updated"] += 1

        # Save follow-ups
        for follow_up in result.get("follow_ups", []):
            try:
                follow_up_date = datetime.fromisoformat(follow_up["follow_up_date"])
            except:
                follow_up_date = datetime.utcnow() + timedelta(days=1)

            saved = await self.save_follow_up(
                user_id=user_id,
                question=follow_up["question"],
                context=follow_up["context"],
                follow_up_date=follow_up_date,
            )
            if saved:
                counts["follow_ups_created"] += 1

        log.info(f"Thread extraction for user {user_id}: {counts}")
        return counts

    # -------------------------------------------------------------------------
    # Message Context (Priority Stack)
    # -------------------------------------------------------------------------

    async def get_message_context(
        self,
        user_id: UUID,
    ) -> MessageContext:
        """Get prioritized context for daily message generation.

        Implements the priority stack from MEMORY_SYSTEM.md with variety improvements:
        1. Follow-ups from recent conversations (filtered for recently-used)
        2. Active life threads (filtered for recently-used)
        3. Patterns (mood trends, engagement)
        4. Core facts for texture
        5. Generic fallback (FAILURE STATE)
        6. PRESENCE - intentional light touch (NOT a failure, chosen for variety)

        Variety features:
        - Filters out topics used in last 7 days
        - ~20% chance of PRESENCE even when data available
        - Backs off to PRESENCE if user didn't respond to last outreach
        """
        import random

        # Get recently used topic keys (last 7 days) to avoid repetition
        recent_topics = await self._get_recently_used_topics(user_id, days=7)
        log.debug(f"Recently used topics for {user_id}: {recent_topics}")

        # Check if user responded since last outreach
        user_responded = await self._check_user_responded_since_last_outreach(user_id)

        # Priority 1: Pending follow-ups (filtered)
        all_follow_ups = await self.get_pending_follow_ups(user_id)
        follow_ups = [
            fu for fu in all_follow_ups
            if f"followup_{fu.get('id', '')}" not in recent_topics
        ]

        # Priority 2: Active threads (filtered)
        all_threads = await self.get_active_threads(user_id, limit=5)
        threads = [
            t for t in all_threads
            if f"thread_{t.get('id', '')}" not in recent_topics
        ]
        threads_needing_followup = await self.get_threads_needing_followup(user_id)
        threads_needing_followup = [
            t for t in threads_needing_followup
            if f"thread_{t.get('id', '')}" not in recent_topics
        ]

        # Priority 3: Patterns (mood trends, engagement changes)
        patterns: List[Dict[str, Any]] = []
        if self.pattern_service:
            try:
                patterns = await self.pattern_service.get_actionable_patterns(user_id)
            except Exception as e:
                log.warning(f"Failed to get patterns for {user_id}: {e}")

        # Priority 4: Core facts
        core_facts_rows = await self.db.fetch_all(
            """
            SELECT category, key, value, importance_score
            FROM user_context
            WHERE user_id = :user_id
                AND tier = 'core'
                AND (expires_at IS NULL OR expires_at > NOW())
            ORDER BY importance_score DESC, updated_at DESC
            LIMIT 10
            """,
            {"user_id": str(user_id)},
        )
        core_facts = [dict(row) for row in core_facts_rows]

        # Determine topic_key for the selected priority
        topic_key: Optional[str] = None

        # Determine priority level with variety logic
        force_presence = False

        # Back-off logic: if user didn't respond to last outreach, prefer PRESENCE
        if not user_responded:
            log.info(f"User {user_id} hasn't responded since last outreach, preferring PRESENCE")
            force_presence = True

        # Random variety: ~20% chance of PRESENCE even with data available
        if not force_presence and random.random() < 0.20:
            log.info(f"Randomly choosing PRESENCE for variety (user {user_id})")
            force_presence = True

        if force_presence:
            priority = MessagePriority.PRESENCE
        elif follow_ups:
            priority = MessagePriority.FOLLOW_UP
            topic_key = f"followup_{follow_ups[0].get('id', '')}"
        elif threads_needing_followup:
            priority = MessagePriority.THREAD
            topic_key = f"thread_{threads_needing_followup[0].get('id', '')}"
        elif threads:
            priority = MessagePriority.THREAD
            topic_key = f"thread_{threads[0].get('id', '')}"
        elif patterns:
            priority = MessagePriority.PATTERN
        elif core_facts:
            priority = MessagePriority.TEXTURE
        else:
            priority = MessagePriority.GENERIC

        return MessageContext(
            priority=priority,
            follow_ups=follow_ups,
            threads=threads,
            patterns=patterns,
            core_facts=core_facts,
            has_personal_content=priority not in (MessagePriority.GENERIC, MessagePriority.PRESENCE),
            topic_key=topic_key,
            user_responded_since_last=user_responded,
            force_presence=force_presence,
        )

    async def _get_recently_used_topics(
        self,
        user_id: UUID,
        days: int = 7,
    ) -> set:
        """Get topic_keys used in recent scheduled messages."""
        rows = await self.db.fetch_all(
            """
            SELECT DISTINCT topic_key
            FROM scheduled_messages
            WHERE user_id = :user_id
                AND topic_key IS NOT NULL
                AND sent_at > NOW() - INTERVAL ':days days'
                AND status = 'sent'
            """.replace(":days", str(days)),  # Interval doesn't support params
            {"user_id": str(user_id)},
        )
        return {row["topic_key"] for row in rows}

    async def _check_user_responded_since_last_outreach(
        self,
        user_id: UUID,
    ) -> bool:
        """Check if user has sent a message since our last scheduled outreach."""
        # Get last scheduled message sent_at
        last_outreach = await self.db.fetch_one(
            """
            SELECT sent_at
            FROM scheduled_messages
            WHERE user_id = :user_id AND status = 'sent'
            ORDER BY sent_at DESC
            LIMIT 1
            """,
            {"user_id": str(user_id)},
        )

        if not last_outreach or not last_outreach["sent_at"]:
            # No previous outreach, assume they're engaged
            return True

        # Get last user message
        last_user_msg = await self.db.fetch_one(
            """
            SELECT MAX(m.created_at) as last_msg
            FROM messages m
            JOIN conversations c ON m.conversation_id = c.id
            WHERE c.user_id = :user_id AND m.role = 'user'
            """,
            {"user_id": str(user_id)},
        )

        if not last_user_msg or not last_user_msg["last_msg"]:
            # User has never messaged (new user), give them benefit of doubt
            return True

        # User responded if their last message is after our last outreach
        return last_user_msg["last_msg"] > last_outreach["sent_at"]

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

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
