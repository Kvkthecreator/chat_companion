"""Pattern Detection Service - Compute behavioral patterns from conversation history.

This service implements Priority 3 message generation by detecting patterns like:
- Mood trends: "You've seemed a bit flat this week"
- Engagement changes: "You've been more talkative lately"
- Topic sentiment: "You light up when talking about your side project"

Patterns are stored in user_context with category='pattern', tier='derived'.
They are recomputed periodically, not on every conversation.
"""

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

log = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

# Mood string → numeric valence mapping
MOOD_VALENCE: Dict[str, int] = {
    # Positive (+2)
    "happy": 2, "excited": 2, "grateful": 2, "joyful": 2, "elated": 2,
    # Positive (+1)
    "hopeful": 1, "calm": 1, "content": 1, "optimistic": 1, "relieved": 1,
    "peaceful": 1, "good": 1, "fine": 1, "okay": 1,
    # Neutral (0)
    "neutral": 0, "tired": 0, "busy": 0, "mixed": 0, "uncertain": 0,
    # Negative (-1)
    "anxious": -1, "stressed": -1, "frustrated": -1, "worried": -1,
    "nervous": -1, "overwhelmed": -1, "irritated": -1, "down": -1,
    # Negative (-2)
    "sad": -2, "angry": -2, "hopeless": -2, "depressed": -2,
    "devastated": -2, "miserable": -2,
}

# Time windows for window-based messaging
TIME_WINDOWS = {
    "morning": ("06:00", "10:00"),
    "midday": ("11:00", "14:00"),
    "evening": ("17:00", "20:00"),
    "night": ("20:00", "23:00"),
}


# =============================================================================
# Pattern Types
# =============================================================================

class TrendDirection(str, Enum):
    """Direction of a detected trend."""
    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"


@dataclass
class MoodTrendPattern:
    """Pattern representing mood changes over time."""
    pattern_type: str = "mood_trend"
    window_days: int = 7
    average_valence: float = 0.0      # -2.0 to +2.0
    baseline_valence: float = 0.0     # User's typical mood
    trend_direction: TrendDirection = TrendDirection.STABLE
    notable_shift: bool = False       # Significant deviation from baseline
    conversation_count: int = 0       # Data points in window
    confidence: float = 0.0           # 0.0 to 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_type": self.pattern_type,
            "window_days": self.window_days,
            "average_valence": self.average_valence,
            "baseline_valence": self.baseline_valence,
            "trend_direction": self.trend_direction.value,
            "notable_shift": self.notable_shift,
            "conversation_count": self.conversation_count,
            "confidence": self.confidence,
        }

    def get_message_hint(self) -> Optional[str]:
        """Get a hint for message generation if pattern is notable."""
        if not self.notable_shift or self.confidence < 0.5:
            return None

        if self.trend_direction == TrendDirection.DECLINING:
            if self.average_valence < -0.5:
                return "You've seemed a bit down lately. Everything okay?"
            else:
                return "Things seem a bit heavier this week. How are you holding up?"
        elif self.trend_direction == TrendDirection.IMPROVING:
            if self.average_valence > 0.5:
                return "You've seemed really good lately. What's been fueling that?"
            else:
                return "Things seem to be looking up. Anything in particular?"

        return None


@dataclass
class EngagementTrendPattern:
    """Pattern representing engagement changes."""
    pattern_type: str = "engagement_trend"
    window_days: int = 7
    avg_messages_per_conversation: float = 0.0
    avg_response_length: float = 0.0     # Characters
    user_initiation_rate: float = 0.0    # 0.0 to 1.0
    trend_direction: TrendDirection = TrendDirection.STABLE
    baseline_engagement: float = 0.0
    notable_shift: bool = False
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_type": self.pattern_type,
            "window_days": self.window_days,
            "avg_messages_per_conversation": self.avg_messages_per_conversation,
            "avg_response_length": self.avg_response_length,
            "user_initiation_rate": self.user_initiation_rate,
            "trend_direction": self.trend_direction.value,
            "baseline_engagement": self.baseline_engagement,
            "notable_shift": self.notable_shift,
            "confidence": self.confidence,
        }

    def get_message_hint(self) -> Optional[str]:
        """Get a hint for message generation if pattern is notable."""
        if not self.notable_shift or self.confidence < 0.5:
            return None

        if self.trend_direction == TrendDirection.IMPROVING:
            return "I've noticed you've been sharing more lately. I appreciate that."
        elif self.trend_direction == TrendDirection.DECLINING:
            return "You've been a bit quieter lately. No pressure, just checking in."

        return None


@dataclass
class TopicSentimentPattern:
    """Pattern representing sentiment toward a specific topic."""
    pattern_type: str = "topic_sentiment"
    topic: str = ""
    sentiment: str = "neutral"  # positive, negative, mixed, avoidant
    evidence_count: int = 0
    avg_valence: float = 0.0
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_type": self.pattern_type,
            "topic": self.topic,
            "sentiment": self.sentiment,
            "evidence_count": self.evidence_count,
            "avg_valence": self.avg_valence,
            "confidence": self.confidence,
        }

    def get_message_hint(self) -> Optional[str]:
        """Get a hint for message generation."""
        if self.confidence < 0.6 or self.evidence_count < 3:
            return None

        if self.sentiment == "positive":
            return f"You always seem to light up when talking about {self.topic}."
        elif self.sentiment == "negative":
            return f"I've noticed {self.topic} tends to be stressful for you."

        return None


# =============================================================================
# Pattern Service
# =============================================================================

class PatternService:
    """Service for computing and retrieving user behavior patterns."""

    def __init__(self, db):
        self.db = db

    # -------------------------------------------------------------------------
    # Mood Trend Computation
    # -------------------------------------------------------------------------

    async def compute_mood_trend(
        self,
        user_id: UUID,
        window_days: int = 7,
    ) -> MoodTrendPattern:
        """Compute mood trend for a user over the specified window.

        Compares recent mood to baseline (30-day average excluding window).
        """
        now = datetime.utcnow()
        window_start = now - timedelta(days=window_days)
        baseline_start = now - timedelta(days=window_days + 30)
        baseline_end = window_start

        # Get recent conversations with mood
        recent_rows = await self.db.fetch_all(
            """
            SELECT mood_summary, started_at
            FROM conversations
            WHERE user_id = :user_id
              AND started_at >= :window_start
              AND mood_summary IS NOT NULL
            ORDER BY started_at DESC
            """,
            {"user_id": str(user_id), "window_start": window_start},
        )

        # Get baseline conversations
        baseline_rows = await self.db.fetch_all(
            """
            SELECT mood_summary
            FROM conversations
            WHERE user_id = :user_id
              AND started_at >= :baseline_start
              AND started_at < :baseline_end
              AND mood_summary IS NOT NULL
            """,
            {
                "user_id": str(user_id),
                "baseline_start": baseline_start,
                "baseline_end": baseline_end,
            },
        )

        # Calculate recent average valence
        recent_valences = [
            self._mood_to_valence(row["mood_summary"])
            for row in recent_rows
        ]
        recent_avg = sum(recent_valences) / len(recent_valences) if recent_valences else 0.0

        # Calculate baseline average valence
        baseline_valences = [
            self._mood_to_valence(row["mood_summary"])
            for row in baseline_rows
        ]
        baseline_avg = sum(baseline_valences) / len(baseline_valences) if baseline_valences else 0.0

        # Determine trend direction and if it's notable
        diff = recent_avg - baseline_avg
        if diff > 0.5:
            trend = TrendDirection.IMPROVING
            notable = True
        elif diff < -0.5:
            trend = TrendDirection.DECLINING
            notable = True
        else:
            trend = TrendDirection.STABLE
            notable = abs(diff) > 0.3

        # Calculate confidence based on data points
        data_points = len(recent_valences)
        if data_points >= 5:
            confidence = 0.9
        elif data_points >= 3:
            confidence = 0.7
        elif data_points >= 2:
            confidence = 0.5
        else:
            confidence = 0.3

        return MoodTrendPattern(
            window_days=window_days,
            average_valence=round(recent_avg, 2),
            baseline_valence=round(baseline_avg, 2),
            trend_direction=trend,
            notable_shift=notable,
            conversation_count=data_points,
            confidence=confidence,
        )

    def _mood_to_valence(self, mood: str) -> float:
        """Convert mood string to numeric valence."""
        if not mood:
            return 0.0
        mood_lower = mood.lower().strip()
        return float(MOOD_VALENCE.get(mood_lower, 0))

    # -------------------------------------------------------------------------
    # Engagement Trend Computation
    # -------------------------------------------------------------------------

    async def compute_engagement_trend(
        self,
        user_id: UUID,
        window_days: int = 7,
    ) -> EngagementTrendPattern:
        """Compute engagement trend based on message patterns."""
        now = datetime.utcnow()
        window_start = now - timedelta(days=window_days)
        baseline_start = now - timedelta(days=window_days + 30)
        baseline_end = window_start

        # Get recent conversation stats
        recent_stats = await self.db.fetch_one(
            """
            SELECT
                COUNT(DISTINCT c.id) as conv_count,
                AVG(c.message_count) as avg_messages,
                SUM(CASE WHEN c.initiated_by = 'user' THEN 1 ELSE 0 END)::float /
                    NULLIF(COUNT(c.id), 0) as initiation_rate
            FROM conversations c
            WHERE c.user_id = :user_id
              AND c.started_at >= :window_start
            """,
            {"user_id": str(user_id), "window_start": window_start},
        )

        # Get recent message lengths
        recent_lengths = await self.db.fetch_one(
            """
            SELECT AVG(LENGTH(m.content)) as avg_length
            FROM companion_messages m
            JOIN conversations c ON m.conversation_id = c.id
            WHERE c.user_id = :user_id
              AND c.started_at >= :window_start
              AND m.role = 'user'
            """,
            {"user_id": str(user_id), "window_start": window_start},
        )

        # Get baseline stats
        baseline_stats = await self.db.fetch_one(
            """
            SELECT
                AVG(c.message_count) as avg_messages,
                SUM(CASE WHEN c.initiated_by = 'user' THEN 1 ELSE 0 END)::float /
                    NULLIF(COUNT(c.id), 0) as initiation_rate
            FROM conversations c
            WHERE c.user_id = :user_id
              AND c.started_at >= :baseline_start
              AND c.started_at < :baseline_end
            """,
            {
                "user_id": str(user_id),
                "baseline_start": baseline_start,
                "baseline_end": baseline_end,
            },
        )

        # Calculate engagement score (normalized composite)
        recent_msgs = float(recent_stats["avg_messages"] or 0)
        recent_init = float(recent_stats["initiation_rate"] or 0)
        recent_len = float(recent_lengths["avg_length"] or 0)
        baseline_msgs = float(baseline_stats["avg_messages"] or 0) if baseline_stats else 0
        baseline_init = float(baseline_stats["initiation_rate"] or 0) if baseline_stats else 0

        # Simple engagement score: weighted average
        recent_engagement = (recent_msgs * 0.4) + (recent_init * 100 * 0.3) + (recent_len / 100 * 0.3)
        baseline_engagement = (baseline_msgs * 0.4) + (baseline_init * 100 * 0.3)

        # Determine trend
        diff = recent_engagement - baseline_engagement
        if diff > 5:
            trend = TrendDirection.IMPROVING
            notable = True
        elif diff < -5:
            trend = TrendDirection.DECLINING
            notable = True
        else:
            trend = TrendDirection.STABLE
            notable = False

        conv_count = int(recent_stats["conv_count"] or 0)
        confidence = min(0.9, conv_count * 0.2) if conv_count > 0 else 0.0

        return EngagementTrendPattern(
            window_days=window_days,
            avg_messages_per_conversation=round(recent_msgs, 1),
            avg_response_length=round(recent_len, 0),
            user_initiation_rate=round(recent_init, 2),
            trend_direction=trend,
            baseline_engagement=round(baseline_engagement, 2),
            notable_shift=notable,
            confidence=confidence,
        )

    # -------------------------------------------------------------------------
    # Topic Sentiment Computation
    # -------------------------------------------------------------------------

    async def compute_topic_sentiment(
        self,
        user_id: UUID,
        topic: str,
    ) -> Optional[TopicSentimentPattern]:
        """Compute sentiment toward a specific topic."""
        # Get conversations mentioning this topic
        rows = await self.db.fetch_all(
            """
            SELECT mood_summary, topics
            FROM conversations
            WHERE user_id = :user_id
              AND topics::text ILIKE :topic_pattern
              AND mood_summary IS NOT NULL
            ORDER BY started_at DESC
            LIMIT 20
            """,
            {"user_id": str(user_id), "topic_pattern": f"%{topic}%"},
        )

        if len(rows) < 2:
            return None

        # Calculate average valence for conversations with this topic
        valences = [self._mood_to_valence(row["mood_summary"]) for row in rows]
        avg_valence = sum(valences) / len(valences)

        # Determine sentiment category
        if avg_valence > 0.5:
            sentiment = "positive"
        elif avg_valence < -0.5:
            sentiment = "negative"
        elif avg_valence > -0.2 and avg_valence < 0.2:
            sentiment = "neutral"
        else:
            sentiment = "mixed"

        confidence = min(0.9, len(rows) * 0.15)

        return TopicSentimentPattern(
            topic=topic,
            sentiment=sentiment,
            evidence_count=len(rows),
            avg_valence=round(avg_valence, 2),
            confidence=confidence,
        )

    # -------------------------------------------------------------------------
    # Compute All Patterns
    # -------------------------------------------------------------------------

    async def compute_all_patterns(
        self,
        user_id: UUID,
    ) -> List[Dict[str, Any]]:
        """Compute all patterns for a user."""
        patterns = []

        # Mood trends (7-day and 14-day)
        for window in [7, 14]:
            try:
                mood = await self.compute_mood_trend(user_id, window_days=window)
                if mood.confidence >= 0.3:
                    patterns.append(mood)
            except Exception as e:
                log.warning(f"Failed to compute mood trend ({window}d) for {user_id}: {e}")

        # Engagement trend
        try:
            engagement = await self.compute_engagement_trend(user_id)
            if engagement.confidence >= 0.3:
                patterns.append(engagement)
        except Exception as e:
            log.warning(f"Failed to compute engagement trend for {user_id}: {e}")

        # Topic sentiments for common topics
        common_topics = ["work", "family", "health", "relationships", "hobbies", "project"]
        for topic in common_topics:
            try:
                topic_pattern = await self.compute_topic_sentiment(user_id, topic)
                if topic_pattern and topic_pattern.confidence >= 0.4:
                    patterns.append(topic_pattern)
            except Exception as e:
                log.warning(f"Failed to compute topic sentiment ({topic}) for {user_id}: {e}")

        return patterns

    # -------------------------------------------------------------------------
    # Storage
    # -------------------------------------------------------------------------

    async def save_pattern(
        self,
        user_id: UUID,
        pattern: Any,
    ) -> Optional[Dict]:
        """Save a pattern to user_context."""
        pattern_dict = pattern.to_dict()
        pattern_type = pattern_dict["pattern_type"]

        # Create unique key for this pattern
        if pattern_type == "mood_trend":
            key = f"mood_trend_{pattern_dict['window_days']}d"
        elif pattern_type == "engagement_trend":
            key = f"engagement_trend_{pattern_dict['window_days']}d"
        elif pattern_type == "topic_sentiment":
            key = f"topic_sentiment_{pattern_dict['topic']}"
        else:
            key = f"{pattern_type}_default"

        # Patterns expire after 24 hours (recomputed daily)
        expires_at = datetime.utcnow() + timedelta(hours=24)

        query = """
            INSERT INTO user_context (
                user_id, category, key, value, tier,
                importance_score, source, expires_at
            )
            VALUES (
                :user_id, 'pattern', :key, :value, 'derived',
                :importance, 'computed', :expires_at
            )
            ON CONFLICT (user_id, category, key)
            DO UPDATE SET
                value = EXCLUDED.value,
                importance_score = EXCLUDED.importance_score,
                expires_at = EXCLUDED.expires_at,
                updated_at = NOW()
            RETURNING *
        """

        # Higher importance for notable patterns
        importance = 0.8 if getattr(pattern, 'notable_shift', False) else 0.5

        row = await self.db.fetch_one(
            query,
            {
                "user_id": str(user_id),
                "key": key,
                "value": json.dumps(pattern_dict),
                "importance": importance,
                "expires_at": expires_at,
            },
        )

        return dict(row) if row else None

    async def save_all_patterns(
        self,
        user_id: UUID,
        patterns: List[Any],
    ) -> int:
        """Save multiple patterns, return count saved."""
        saved = 0
        for pattern in patterns:
            result = await self.save_pattern(user_id, pattern)
            if result:
                saved += 1
        return saved

    # -------------------------------------------------------------------------
    # Retrieval
    # -------------------------------------------------------------------------

    async def get_patterns(
        self,
        user_id: UUID,
    ) -> List[Dict[str, Any]]:
        """Get all stored patterns for a user."""
        rows = await self.db.fetch_all(
            """
            SELECT id, key, value, importance_score, updated_at, last_referenced_at
            FROM user_context
            WHERE user_id = :user_id
              AND category = 'pattern'
              AND tier = 'derived'
              AND (expires_at IS NULL OR expires_at > NOW())
            ORDER BY importance_score DESC, updated_at DESC
            """,
            {"user_id": str(user_id)},
        )

        patterns = []
        for row in rows:
            try:
                data = json.loads(row["value"])
                data["id"] = row["id"]
                data["last_referenced_at"] = row["last_referenced_at"]
                patterns.append(data)
            except Exception:
                continue

        return patterns

    async def get_actionable_patterns(
        self,
        user_id: UUID,
    ) -> List[Dict[str, Any]]:
        """Get patterns worth mentioning in a message.

        A pattern is actionable if:
        - It has a notable shift from baseline
        - It hasn't been referenced in the last 3 days
        - It has sufficient confidence
        """
        patterns = await self.get_patterns(user_id)
        three_days_ago = datetime.utcnow() - timedelta(days=3)

        actionable = []
        for p in patterns:
            # Check if notable
            if not p.get("notable_shift", False):
                continue

            # Check confidence
            if p.get("confidence", 0) < 0.5:
                continue

            # Check if recently referenced
            last_ref = p.get("last_referenced_at")
            if last_ref and last_ref > three_days_ago:
                continue

            # Generate message hint
            hint = self._get_message_hint(p)
            if hint:
                p["message_hint"] = hint
                actionable.append(p)

        return actionable

    def _get_message_hint(self, pattern: Dict[str, Any]) -> Optional[str]:
        """Generate a message hint for a pattern."""
        pattern_type = pattern.get("pattern_type")

        if pattern_type == "mood_trend":
            trend = pattern.get("trend_direction")
            avg = pattern.get("average_valence", 0)

            if trend == "declining":
                if avg < -0.5:
                    return "You've seemed a bit down lately. Everything okay?"
                else:
                    return "Things seem a bit heavier this week. How are you holding up?"
            elif trend == "improving":
                if avg > 0.5:
                    return "You've seemed really good lately. What's been fueling that?"
                else:
                    return "Things seem to be looking up. Anything in particular?"

        elif pattern_type == "engagement_trend":
            trend = pattern.get("trend_direction")
            if trend == "improving":
                return "I've noticed you've been sharing more lately. I appreciate that."
            elif trend == "declining":
                return "You've been a bit quieter lately. No pressure, just checking in."

        elif pattern_type == "topic_sentiment":
            topic = pattern.get("topic", "")
            sentiment = pattern.get("sentiment")
            if sentiment == "positive":
                return f"You always seem to light up when talking about {topic}."
            elif sentiment == "negative":
                return f"I've noticed {topic} tends to be stressful for you."

        return None

    async def mark_pattern_used(
        self,
        pattern_id: UUID,
    ) -> bool:
        """Mark a pattern as referenced in a message."""
        result = await self.db.execute(
            """
            UPDATE user_context
            SET last_referenced_at = NOW()
            WHERE id = :id AND category = 'pattern'
            """,
            {"id": str(pattern_id)},
        )
        return result is not None
