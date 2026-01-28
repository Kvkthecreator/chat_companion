"""Artifact Service - Memory Output Modality.

Artifacts are structured syntheses of memory data, rendered in companion voice.
They transform accumulated conversation and memory into meaningful reflections.

Artifact Types:
1. Thread Journey - Timeline + insights for a specific thread
2. Domain Health - Overview of threads in a domain
3. Communication Profile - How the user communicates
4. Relationship Summary - Overall companion relationship

See: docs/analysis/ARTIFACT_LAYER_ANALYSIS.md
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.services.llm import LLMService

log = logging.getLogger(__name__)


# =============================================================================
# Artifact Types and Data Structures
# =============================================================================

class ArtifactType(str, Enum):
    """Types of artifacts that can be generated."""
    THREAD_JOURNEY = "thread_journey"
    DOMAIN_HEALTH = "domain_health"
    COMMUNICATION = "communication"
    RELATIONSHIP = "relationship"


@dataclass
class ArtifactSection:
    """A section within an artifact."""
    section_type: str  # header, timeline, observations, key_details, stats, etc.
    content: Any  # Dict or string depending on section type

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.section_type,
            "content": self.content,
        }


@dataclass
class Artifact:
    """Generated artifact ready for storage/display."""
    artifact_type: ArtifactType
    title: str
    sections: List[ArtifactSection] = field(default_factory=list)
    companion_voice: Optional[str] = None
    data_sources: List[str] = field(default_factory=list)
    is_meaningful: bool = True
    min_data_reason: Optional[str] = None

    # Reference fields (only one should be set based on type)
    thread_id: Optional[UUID] = None
    domain: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_type": self.artifact_type.value,
            "title": self.title,
            "sections": [s.to_dict() for s in self.sections],
            "companion_voice": self.companion_voice,
            "data_sources": self.data_sources,
            "is_meaningful": self.is_meaningful,
            "min_data_reason": self.min_data_reason,
            "thread_id": str(self.thread_id) if self.thread_id else None,
            "domain": self.domain,
        }


# =============================================================================
# Availability Thresholds
# =============================================================================

AVAILABILITY_THRESHOLDS = {
    ArtifactType.THREAD_JOURNEY: {
        "min_messages": 3,
        "min_days": 7,
        "description": "Thread needs at least 3 mentions and 7 days of history",
    },
    ArtifactType.DOMAIN_HEALTH: {
        "min_threads": 1,
        "description": "Domain needs at least 1 thread",
    },
    ArtifactType.COMMUNICATION: {
        "min_messages": 20,
        "min_conversations": 5,
        "description": "Need at least 20 user messages across 5 conversations",
    },
    ArtifactType.RELATIONSHIP: {
        "min_days": 14,
        "min_conversations": 10,
        "description": "Need at least 14 days and 10 conversations",
    },
}


# =============================================================================
# LLM Prompts
# =============================================================================

THREAD_JOURNEY_PROMPT = """Generate a companion-voiced reflection on this user's journey with a life situation.

Thread: {thread_summary}
Domain: {domain}
Current Phase: {phase}
Started: {started_date}
Days Active: {days_active}

Timeline Events:
{timeline_events}

Key Details I'm Tracking:
{key_details}

Patterns/Observations:
{patterns}

Generate a warm, personal reflection (2-3 sentences) that:
1. Acknowledges how far they've come
2. Notes any patterns you've observed
3. Feels like a supportive friend reflecting, not an analytics report

Return ONLY the reflection text, no quotes or formatting."""


DOMAIN_HEALTH_PROMPT = """Generate a companion-voiced overview of the user's {domain} domain.

Active Threads in {domain}:
{threads_summary}

Domain Activity:
- Threads: {thread_count}
- Recent mentions: {mention_count} in last 2 weeks
- Most active thread: {most_active}

Generate a brief, warm overview (2-3 sentences) that:
1. Summarizes what's happening in this area of their life
2. Notes any momentum or attention needed
3. Sounds like a thoughtful friend, not a dashboard

Return ONLY the overview text, no quotes or formatting."""


COMMUNICATION_PROMPT = """Analyze this user's communication patterns and generate a companion-voiced profile.

Message Statistics:
- Total conversations: {conversation_count}
- Average messages per conversation: {avg_messages}
- User-initiated conversations: {initiation_rate}%
- Average response length: {avg_length} characters
- Most active time: {active_time}

Observed Patterns:
{patterns}

Generate a warm, insightful profile (3-4 sentences) that:
1. Describes how they communicate (not prescriptively, observationally)
2. Notes what seems to help them (open questions? validation? direct advice?)
3. Mentions any timing or style preferences you've noticed
4. Sounds like a friend who's learned how to be there for them

Return ONLY the profile text, no quotes or formatting."""


RELATIONSHIP_PROMPT = """Generate a companion-voiced summary of your relationship with this user.

Relationship Stats:
- Together since: {start_date}
- Days together: {days_together}
- Total conversations: {conversation_count}
- Things learned: {facts_count} facts, {patterns_count} patterns
- Active threads: {thread_count}

Highlights:
{highlights}

What I'm Currently Following:
{active_threads}

Generate a warm relationship reflection (3-4 sentences) that:
1. Acknowledges the relationship duration meaningfully
2. Mentions specific things you've learned about them
3. Notes what you're currently following in their life
4. Feels genuine and personal, not a report

Return ONLY the reflection text, no quotes or formatting."""


# =============================================================================
# Artifact Service
# =============================================================================

class ArtifactService:
    """Service for generating and managing artifacts."""

    def __init__(self, db, llm_service: Optional[LLMService] = None):
        self.db = db
        self.llm = llm_service or LLMService()

    # -------------------------------------------------------------------------
    # Availability Checks
    # -------------------------------------------------------------------------

    async def check_availability(
        self,
        user_id: UUID,
    ) -> Dict[str, Any]:
        """Check which artifacts are available for a user.

        Returns a dict with artifact types and their availability status.
        """
        availability = {}

        # Check thread journey availability (per thread)
        threads = await self._get_user_threads(user_id)
        thread_journeys = []
        for thread in threads:
            created_at = thread.get("created_at") or thread.get("updated_at")
            if created_at:
                days_active = (datetime.utcnow() - created_at).days if isinstance(created_at, datetime) else 0
            else:
                days_active = 0

            # For now, any thread with 7+ days is available
            if days_active >= AVAILABILITY_THRESHOLDS[ArtifactType.THREAD_JOURNEY]["min_days"]:
                thread_journeys.append({
                    "thread_id": str(thread["id"]),
                    "topic": thread.get("topic"),
                    "domain": thread.get("domain"),
                    "days_active": days_active,
                })

        availability["thread_journey"] = {
            "available": len(thread_journeys) > 0,
            "threads": thread_journeys,
        }

        # Check domain health availability
        domains_with_threads = {}
        for thread in threads:
            domain = thread.get("domain")
            if domain:
                if domain not in domains_with_threads:
                    domains_with_threads[domain] = 0
                domains_with_threads[domain] += 1

        available_domains = [
            {"domain": d, "thread_count": c}
            for d, c in domains_with_threads.items()
            if c >= AVAILABILITY_THRESHOLDS[ArtifactType.DOMAIN_HEALTH]["min_threads"]
        ]

        availability["domain_health"] = {
            "available": len(available_domains) > 0,
            "domains": available_domains,
        }

        # Check communication profile availability
        user_stats = await self._get_user_stats(user_id)
        comm_available = (
            user_stats.get("message_count", 0) >= AVAILABILITY_THRESHOLDS[ArtifactType.COMMUNICATION]["min_messages"]
            and user_stats.get("conversation_count", 0) >= AVAILABILITY_THRESHOLDS[ArtifactType.COMMUNICATION]["min_conversations"]
        )

        availability["communication"] = {
            "available": comm_available,
            "message_count": user_stats.get("message_count", 0),
            "conversation_count": user_stats.get("conversation_count", 0),
        }

        # Check relationship summary availability
        days_since_first = user_stats.get("days_since_first", 0)
        rel_available = (
            days_since_first >= AVAILABILITY_THRESHOLDS[ArtifactType.RELATIONSHIP]["min_days"]
            and user_stats.get("conversation_count", 0) >= AVAILABILITY_THRESHOLDS[ArtifactType.RELATIONSHIP]["min_conversations"]
        )

        availability["relationship"] = {
            "available": rel_available,
            "days_together": days_since_first,
            "conversation_count": user_stats.get("conversation_count", 0),
        }

        return availability

    # -------------------------------------------------------------------------
    # Artifact Generation
    # -------------------------------------------------------------------------

    async def generate_thread_journey(
        self,
        user_id: UUID,
        thread_id: UUID,
    ) -> Artifact:
        """Generate a Thread Journey artifact for a specific thread."""
        # Get thread data
        thread = await self._get_thread_by_id(user_id, thread_id)
        if not thread:
            return Artifact(
                artifact_type=ArtifactType.THREAD_JOURNEY,
                title="Thread Not Found",
                is_meaningful=False,
                min_data_reason="Thread not found",
                thread_id=thread_id,
            )

        # Get timeline events
        events = await self._get_thread_events(thread_id)

        # Get patterns related to this thread
        patterns = await self._get_thread_patterns(user_id, thread.get("topic", ""))

        # Calculate days active
        created_at = thread.get("created_at") or thread.get("updated_at")
        if created_at:
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            days_active = (datetime.utcnow() - created_at.replace(tzinfo=None)).days
        else:
            days_active = 0

        # Check minimum threshold
        if days_active < AVAILABILITY_THRESHOLDS[ArtifactType.THREAD_JOURNEY]["min_days"]:
            return Artifact(
                artifact_type=ArtifactType.THREAD_JOURNEY,
                title=f"Your {thread.get('topic', 'Journey')} Journey",
                is_meaningful=False,
                min_data_reason=f"Thread needs {AVAILABILITY_THRESHOLDS[ArtifactType.THREAD_JOURNEY]['min_days']} days of history",
                thread_id=thread_id,
            )

        # Build sections
        sections = []

        # Header section
        sections.append(ArtifactSection(
            section_type="header",
            content={
                "started": created_at.isoformat() if created_at else None,
                "days_active": days_active,
                "current_phase": thread.get("phase"),
                "domain": thread.get("domain"),
            }
        ))

        # Timeline section
        if events:
            sections.append(ArtifactSection(
                section_type="timeline",
                content=[
                    {"date": e.get("event_date"), "description": e.get("description")}
                    for e in events[:10]  # Limit to 10 most recent
                ]
            ))

        # Key details section
        key_details = thread.get("key_details", [])
        if key_details:
            sections.append(ArtifactSection(
                section_type="key_details",
                content=key_details,
            ))

        # Observations section (patterns)
        if patterns:
            sections.append(ArtifactSection(
                section_type="observations",
                content=[p.get("message_hint") or p.get("value") for p in patterns if p],
            ))

        # Generate companion voice
        companion_voice = await self._generate_companion_voice(
            THREAD_JOURNEY_PROMPT,
            thread_summary=thread.get("summary", ""),
            domain=thread.get("domain", "personal"),
            phase=thread.get("phase") or "ongoing",
            started_date=created_at.strftime("%B %d, %Y") if created_at else "recently",
            days_active=days_active,
            timeline_events="\n".join([f"- {e.get('date', 'Unknown')}: {e.get('description', '')}" for e in events[:5]]) or "No timeline events yet",
            key_details="\n".join([f"- {d}" for d in key_details]) or "None tracked yet",
            patterns="\n".join([p.get("message_hint", "") for p in patterns]) or "Still learning patterns",
        )

        return Artifact(
            artifact_type=ArtifactType.THREAD_JOURNEY,
            title=f"Your {thread.get('topic', 'Journey')} Journey",
            sections=sections,
            companion_voice=companion_voice,
            data_sources=[f"thread:{thread_id}", f"events:{len(events)}", f"patterns:{len(patterns)}"],
            is_meaningful=True,
            thread_id=thread_id,
            domain=thread.get("domain"),
        )

    async def generate_domain_health(
        self,
        user_id: UUID,
        domain: str,
    ) -> Artifact:
        """Generate a Domain Health artifact for a specific domain."""
        # Get all threads in this domain
        threads = await self._get_domain_threads(user_id, domain)

        if not threads:
            return Artifact(
                artifact_type=ArtifactType.DOMAIN_HEALTH,
                title=f"{domain.title()} Overview",
                is_meaningful=False,
                min_data_reason=f"No threads in {domain} domain",
                domain=domain,
            )

        # Calculate domain metrics
        mention_count = await self._count_domain_mentions(user_id, domain)
        most_active = max(threads, key=lambda t: t.get("priority_weight", 1.0))

        # Build sections
        sections = []

        # Header section
        sections.append(ArtifactSection(
            section_type="header",
            content={
                "domain": domain,
                "thread_count": len(threads),
                "mention_count": mention_count,
            }
        ))

        # Threads section
        sections.append(ArtifactSection(
            section_type="threads",
            content=[
                {
                    "id": str(t.get("id")),
                    "topic": t.get("topic"),
                    "summary": t.get("summary"),
                    "phase": t.get("phase"),
                    "status": t.get("status"),
                    "priority": "primary" if t.get("priority_weight", 1.0) > 1.0 else "normal",
                }
                for t in threads
            ]
        ))

        # Generate companion voice
        threads_summary = "\n".join([
            f"- {t.get('topic')}: {t.get('summary', 'No summary')} (Phase: {t.get('phase') or 'ongoing'})"
            for t in threads
        ])

        companion_voice = await self._generate_companion_voice(
            DOMAIN_HEALTH_PROMPT,
            domain=domain.title(),
            threads_summary=threads_summary,
            thread_count=len(threads),
            mention_count=mention_count,
            most_active=most_active.get("topic", "Unknown"),
        )

        return Artifact(
            artifact_type=ArtifactType.DOMAIN_HEALTH,
            title=f"{domain.title()} Overview",
            sections=sections,
            companion_voice=companion_voice,
            data_sources=[f"domain:{domain}", f"threads:{len(threads)}"],
            is_meaningful=True,
            domain=domain,
        )

    async def generate_communication_profile(
        self,
        user_id: UUID,
    ) -> Artifact:
        """Generate a Communication Profile artifact."""
        # Get communication stats
        stats = await self._get_communication_stats(user_id)

        # Check minimum threshold
        if stats.get("message_count", 0) < AVAILABILITY_THRESHOLDS[ArtifactType.COMMUNICATION]["min_messages"]:
            return Artifact(
                artifact_type=ArtifactType.COMMUNICATION,
                title="How You Communicate",
                is_meaningful=False,
                min_data_reason="Need more conversations to build a profile",
            )

        # Get patterns
        patterns = await self._get_user_patterns(user_id)

        # Build sections
        sections = []

        # Stats section
        sections.append(ArtifactSection(
            section_type="stats",
            content={
                "total_conversations": stats.get("conversation_count", 0),
                "total_messages": stats.get("message_count", 0),
                "avg_messages_per_conversation": round(stats.get("avg_messages", 0), 1),
                "initiation_rate": round(stats.get("initiation_rate", 0) * 100, 1),
                "avg_response_length": round(stats.get("avg_length", 0)),
            }
        ))

        # Patterns section
        if patterns:
            sections.append(ArtifactSection(
                section_type="patterns",
                content=[
                    p.get("message_hint") or f"{p.get('pattern_type', 'pattern')}: {p.get('trend_direction', 'stable')}"
                    for p in patterns
                ]
            ))

        # Generate companion voice
        pattern_text = "\n".join([
            p.get("message_hint", "") for p in patterns if p.get("message_hint")
        ]) or "Still learning your patterns"

        companion_voice = await self._generate_companion_voice(
            COMMUNICATION_PROMPT,
            conversation_count=stats.get("conversation_count", 0),
            avg_messages=round(stats.get("avg_messages", 0), 1),
            initiation_rate=round(stats.get("initiation_rate", 0) * 100),
            avg_length=round(stats.get("avg_length", 0)),
            active_time=stats.get("active_time", "varies"),
            patterns=pattern_text,
        )

        return Artifact(
            artifact_type=ArtifactType.COMMUNICATION,
            title="How You Communicate",
            sections=sections,
            companion_voice=companion_voice,
            data_sources=[f"conversations:{stats.get('conversation_count', 0)}", f"patterns:{len(patterns)}"],
            is_meaningful=True,
        )

    async def generate_relationship_summary(
        self,
        user_id: UUID,
    ) -> Artifact:
        """Generate a Relationship Summary artifact."""
        # Get relationship stats
        stats = await self._get_user_stats(user_id)
        user_info = await self._get_user_info(user_id)

        # Check minimum threshold
        if stats.get("days_since_first", 0) < AVAILABILITY_THRESHOLDS[ArtifactType.RELATIONSHIP]["min_days"]:
            return Artifact(
                artifact_type=ArtifactType.RELATIONSHIP,
                title="Our Relationship",
                is_meaningful=False,
                min_data_reason="We need a bit more time together",
            )

        # Get threads and facts
        threads = await self._get_user_threads(user_id)
        facts = await self._get_user_facts(user_id)
        patterns = await self._get_user_patterns(user_id)

        # Build sections
        sections = []

        # Stats section
        first_message_at = stats.get("first_message_at")
        if first_message_at and isinstance(first_message_at, str):
            first_message_at = datetime.fromisoformat(first_message_at.replace("Z", "+00:00"))

        sections.append(ArtifactSection(
            section_type="header",
            content={
                "started": first_message_at.isoformat() if first_message_at else None,
                "days_together": stats.get("days_since_first", 0),
                "conversation_count": stats.get("conversation_count", 0),
                "companion_name": user_info.get("companion_name", "Aria"),
            }
        ))

        # What I've learned section
        sections.append(ArtifactSection(
            section_type="learned",
            content={
                "facts_count": len(facts),
                "patterns_count": len(patterns),
                "threads_count": len(threads),
                "sample_facts": [f.get("value", "") for f in facts[:5]],
            }
        ))

        # Active threads section
        if threads:
            sections.append(ArtifactSection(
                section_type="following",
                content=[
                    {
                        "topic": t.get("topic"),
                        "domain": t.get("domain"),
                        "phase": t.get("phase"),
                        "status": t.get("status"),
                    }
                    for t in threads[:5]
                ]
            ))

        # Generate companion voice
        active_threads_text = "\n".join([
            f"- {t.get('topic')}: {t.get('summary', 'Ongoing')}"
            for t in threads[:3]
        ]) or "No active threads right now"

        highlights_text = "\n".join([
            f"- {f.get('value', '')}"
            for f in facts[:3]
        ]) or "Still learning about you"

        companion_voice = await self._generate_companion_voice(
            RELATIONSHIP_PROMPT,
            start_date=first_message_at.strftime("%B %d, %Y") if first_message_at else "recently",
            days_together=stats.get("days_since_first", 0),
            conversation_count=stats.get("conversation_count", 0),
            facts_count=len(facts),
            patterns_count=len(patterns),
            thread_count=len(threads),
            highlights=highlights_text,
            active_threads=active_threads_text,
        )

        return Artifact(
            artifact_type=ArtifactType.RELATIONSHIP,
            title="Our Relationship",
            sections=sections,
            companion_voice=companion_voice,
            data_sources=[
                f"conversations:{stats.get('conversation_count', 0)}",
                f"facts:{len(facts)}",
                f"threads:{len(threads)}",
            ],
            is_meaningful=True,
        )

    # -------------------------------------------------------------------------
    # Storage Operations
    # -------------------------------------------------------------------------

    async def save_artifact(
        self,
        user_id: UUID,
        artifact: Artifact,
    ) -> Optional[Dict[str, Any]]:
        """Save or update an artifact in the database."""
        # Generate data snapshot hash for cache invalidation
        data_hash = hashlib.md5(
            json.dumps(artifact.data_sources, sort_keys=True).encode()
        ).hexdigest()[:16]

        # Determine unique constraint fields based on type
        if artifact.artifact_type == ArtifactType.THREAD_JOURNEY:
            conflict_clause = """
                ON CONFLICT (user_id, artifact_type, thread_id)
                WHERE artifact_type = 'thread_journey' AND thread_id IS NOT NULL
            """
        elif artifact.artifact_type == ArtifactType.DOMAIN_HEALTH:
            conflict_clause = """
                ON CONFLICT (user_id, artifact_type, domain)
                WHERE artifact_type = 'domain_health' AND domain IS NOT NULL
            """
        elif artifact.artifact_type == ArtifactType.COMMUNICATION:
            conflict_clause = """
                ON CONFLICT (user_id, artifact_type)
                WHERE artifact_type = 'communication'
            """
        else:  # RELATIONSHIP
            conflict_clause = """
                ON CONFLICT (user_id, artifact_type)
                WHERE artifact_type = 'relationship'
            """

        query = f"""
            INSERT INTO artifacts (
                user_id, artifact_type, thread_id, domain,
                title, sections, companion_voice,
                data_sources, data_snapshot_hash,
                is_meaningful, min_data_reason,
                generated_at
            )
            VALUES (
                :user_id, :artifact_type, :thread_id, :domain,
                :title, :sections, :companion_voice,
                :data_sources, :data_hash,
                :is_meaningful, :min_data_reason,
                NOW()
            )
            {conflict_clause}
            DO UPDATE SET
                title = EXCLUDED.title,
                sections = EXCLUDED.sections,
                companion_voice = EXCLUDED.companion_voice,
                data_sources = EXCLUDED.data_sources,
                data_snapshot_hash = EXCLUDED.data_snapshot_hash,
                is_meaningful = EXCLUDED.is_meaningful,
                min_data_reason = EXCLUDED.min_data_reason,
                generated_at = NOW(),
                updated_at = NOW()
            RETURNING *
        """

        try:
            row = await self.db.fetch_one(
                query,
                {
                    "user_id": str(user_id),
                    "artifact_type": artifact.artifact_type.value,
                    "thread_id": str(artifact.thread_id) if artifact.thread_id else None,
                    "domain": artifact.domain,
                    "title": artifact.title,
                    "sections": json.dumps([s.to_dict() for s in artifact.sections]),
                    "companion_voice": artifact.companion_voice,
                    "data_sources": json.dumps(artifact.data_sources),
                    "data_hash": data_hash,
                    "is_meaningful": artifact.is_meaningful,
                    "min_data_reason": artifact.min_data_reason,
                },
            )
            return dict(row) if row else None
        except Exception as e:
            log.error(f"Failed to save artifact: {e}")
            return None

    async def get_artifact(
        self,
        user_id: UUID,
        artifact_type: ArtifactType,
        thread_id: Optional[UUID] = None,
        domain: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get a stored artifact."""
        if artifact_type == ArtifactType.THREAD_JOURNEY:
            query = """
                SELECT * FROM artifacts
                WHERE user_id = :user_id
                  AND artifact_type = :type
                  AND thread_id = :thread_id
            """
            params = {"user_id": str(user_id), "type": artifact_type.value, "thread_id": str(thread_id)}
        elif artifact_type == ArtifactType.DOMAIN_HEALTH:
            query = """
                SELECT * FROM artifacts
                WHERE user_id = :user_id
                  AND artifact_type = :type
                  AND domain = :domain
            """
            params = {"user_id": str(user_id), "type": artifact_type.value, "domain": domain}
        else:
            query = """
                SELECT * FROM artifacts
                WHERE user_id = :user_id
                  AND artifact_type = :type
            """
            params = {"user_id": str(user_id), "type": artifact_type.value}

        row = await self.db.fetch_one(query, params)
        if not row:
            return None

        result = dict(row)
        # Parse JSON fields
        if result.get("sections"):
            result["sections"] = json.loads(result["sections"]) if isinstance(result["sections"], str) else result["sections"]
        if result.get("data_sources"):
            result["data_sources"] = json.loads(result["data_sources"]) if isinstance(result["data_sources"], str) else result["data_sources"]

        return result

    async def get_all_artifacts(
        self,
        user_id: UUID,
        meaningful_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """Get all artifacts for a user."""
        query = """
            SELECT * FROM artifacts
            WHERE user_id = :user_id
        """
        if meaningful_only:
            query += " AND is_meaningful = TRUE"
        query += " ORDER BY generated_at DESC"

        rows = await self.db.fetch_all(query, {"user_id": str(user_id)})

        artifacts = []
        for row in rows:
            result = dict(row)
            if result.get("sections"):
                result["sections"] = json.loads(result["sections"]) if isinstance(result["sections"], str) else result["sections"]
            if result.get("data_sources"):
                result["data_sources"] = json.loads(result["data_sources"]) if isinstance(result["data_sources"], str) else result["data_sources"]
            artifacts.append(result)

        return artifacts

    # -------------------------------------------------------------------------
    # Event Tracking
    # -------------------------------------------------------------------------

    async def log_thread_event(
        self,
        user_id: UUID,
        thread_id: UUID,
        event_type: str,
        description: str,
        event_date: Optional[datetime] = None,
        source_message_id: Optional[UUID] = None,
        metadata: Optional[Dict] = None,
    ) -> Optional[Dict[str, Any]]:
        """Log an event for a thread (for timeline building)."""
        event_date = event_date or datetime.utcnow()

        query = """
            INSERT INTO artifact_events (
                user_id, thread_id, event_type, event_date,
                description, source_message_id, metadata
            )
            VALUES (
                :user_id, :thread_id, :event_type, :event_date,
                :description, :source_message_id, :metadata
            )
            RETURNING *
        """

        try:
            row = await self.db.fetch_one(
                query,
                {
                    "user_id": str(user_id),
                    "thread_id": str(thread_id),
                    "event_type": event_type,
                    "event_date": event_date.date(),
                    "description": description,
                    "source_message_id": str(source_message_id) if source_message_id else None,
                    "metadata": json.dumps(metadata or {}),
                },
            )
            return dict(row) if row else None
        except Exception as e:
            log.warning(f"Failed to log thread event: {e}")
            return None

    # -------------------------------------------------------------------------
    # Private Helper Methods
    # -------------------------------------------------------------------------

    async def _generate_companion_voice(
        self,
        prompt_template: str,
        **kwargs,
    ) -> str:
        """Generate companion-voiced text using LLM."""
        try:
            prompt = prompt_template.format(**kwargs)
            messages = [
                {
                    "role": "system",
                    "content": "You are a warm, supportive companion reflecting on someone you care about. Be genuine and personal, not analytical.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ]
            response = await self.llm.generate(
                messages=messages,
                max_tokens=300,
            )
            # response is LLMResponse with .content attribute
            return response.content.strip().strip('"')
        except Exception as e:
            log.warning(f"Failed to generate companion voice: {e}")
            return ""

    async def _get_user_threads(self, user_id: UUID) -> List[Dict]:
        """Get all active threads for a user."""
        rows = await self.db.fetch_all(
            """
            SELECT id, key as topic, value, updated_at, created_at,
                   domain, template_id, phase, priority_weight
            FROM user_context
            WHERE user_id = :user_id
              AND category = 'thread'
              AND tier = 'thread'
              AND (expires_at IS NULL OR expires_at > NOW())
            ORDER BY priority_weight DESC, updated_at DESC
            """,
            {"user_id": str(user_id)},
        )

        threads = []
        for row in rows:
            try:
                data = json.loads(row["value"]) if isinstance(row["value"], str) else row["value"]
                threads.append({
                    "id": row["id"],
                    "topic": row["topic"],
                    "summary": data.get("summary", ""),
                    "status": data.get("status", "active"),
                    "key_details": data.get("key_details", []),
                    "domain": row["domain"],
                    "phase": row["phase"],
                    "priority_weight": float(row["priority_weight"]) if row["priority_weight"] else 1.0,
                    "updated_at": row["updated_at"],
                    "created_at": row.get("created_at"),
                })
            except Exception:
                continue

        return threads

    async def _get_thread_by_id(self, user_id: UUID, thread_id: UUID) -> Optional[Dict]:
        """Get a specific thread by ID."""
        row = await self.db.fetch_one(
            """
            SELECT id, key as topic, value, updated_at, created_at,
                   domain, template_id, phase, priority_weight
            FROM user_context
            WHERE user_id = :user_id AND id = :thread_id
            """,
            {"user_id": str(user_id), "thread_id": str(thread_id)},
        )

        if not row:
            return None

        try:
            data = json.loads(row["value"]) if isinstance(row["value"], str) else row["value"]
            return {
                "id": row["id"],
                "topic": row["topic"],
                "summary": data.get("summary", ""),
                "status": data.get("status", "active"),
                "key_details": data.get("key_details", []),
                "domain": row["domain"],
                "phase": row["phase"],
                "priority_weight": float(row["priority_weight"]) if row["priority_weight"] else 1.0,
                "updated_at": row["updated_at"],
                "created_at": row.get("created_at"),
            }
        except Exception:
            return None

    async def _get_domain_threads(self, user_id: UUID, domain: str) -> List[Dict]:
        """Get all threads in a specific domain."""
        threads = await self._get_user_threads(user_id)
        return [t for t in threads if t.get("domain") == domain]

    async def _get_thread_events(self, thread_id: UUID) -> List[Dict]:
        """Get events for a thread."""
        rows = await self.db.fetch_all(
            """
            SELECT id, event_type, event_date, description, metadata
            FROM artifact_events
            WHERE thread_id = :thread_id
            ORDER BY event_date DESC
            """,
            {"thread_id": str(thread_id)},
        )
        return [dict(row) for row in rows]

    async def _get_thread_patterns(self, user_id: UUID, topic: str) -> List[Dict]:
        """Get patterns related to a thread topic."""
        rows = await self.db.fetch_all(
            """
            SELECT id, key, value
            FROM user_context
            WHERE user_id = :user_id
              AND category = 'pattern'
              AND (value ILIKE :topic_pattern OR key ILIKE :topic_pattern)
              AND (expires_at IS NULL OR expires_at > NOW())
            """,
            {"user_id": str(user_id), "topic_pattern": f"%{topic}%"},
        )

        patterns = []
        for row in rows:
            try:
                data = json.loads(row["value"]) if isinstance(row["value"], str) else row["value"]
                patterns.append(data)
            except Exception:
                continue
        return patterns

    async def _get_user_patterns(self, user_id: UUID) -> List[Dict]:
        """Get all patterns for a user."""
        rows = await self.db.fetch_all(
            """
            SELECT id, key, value
            FROM user_context
            WHERE user_id = :user_id
              AND category = 'pattern'
              AND tier = 'derived'
              AND (expires_at IS NULL OR expires_at > NOW())
            ORDER BY importance_score DESC
            """,
            {"user_id": str(user_id)},
        )

        patterns = []
        for row in rows:
            try:
                data = json.loads(row["value"]) if isinstance(row["value"], str) else row["value"]
                patterns.append(data)
            except Exception:
                continue
        return patterns

    async def _get_user_facts(self, user_id: UUID) -> List[Dict]:
        """Get facts about a user."""
        rows = await self.db.fetch_all(
            """
            SELECT id, key, value, category
            FROM user_context
            WHERE user_id = :user_id
              AND category IN ('fact', 'preference', 'relationship')
              AND tier = 'core'
              AND (expires_at IS NULL OR expires_at > NOW())
            ORDER BY importance_score DESC
            LIMIT 20
            """,
            {"user_id": str(user_id)},
        )
        return [{"key": r["key"], "value": r["value"], "category": r["category"]} for r in rows]

    async def _get_user_stats(self, user_id: UUID) -> Dict[str, Any]:
        """Get aggregate stats for a user."""
        stats_row = await self.db.fetch_one(
            """
            SELECT
                COUNT(*) as conversation_count,
                MIN(started_at) as first_conversation,
                EXTRACT(DAY FROM NOW() - MIN(started_at)) as days_since_first
            FROM conversations
            WHERE user_id = :user_id
            """,
            {"user_id": str(user_id)},
        )

        message_row = await self.db.fetch_one(
            """
            SELECT COUNT(*) as message_count
            FROM messages m
            JOIN conversations c ON m.conversation_id = c.id
            WHERE c.user_id = :user_id AND m.role = 'user'
            """,
            {"user_id": str(user_id)},
        )

        return {
            "conversation_count": int(stats_row["conversation_count"] or 0) if stats_row else 0,
            "first_message_at": stats_row["first_conversation"] if stats_row else None,
            "days_since_first": int(stats_row["days_since_first"] or 0) if stats_row else 0,
            "message_count": int(message_row["message_count"] or 0) if message_row else 0,
        }

    async def _get_communication_stats(self, user_id: UUID) -> Dict[str, Any]:
        """Get communication-specific stats."""
        stats = await self._get_user_stats(user_id)

        # Get additional communication metrics
        comm_row = await self.db.fetch_one(
            """
            SELECT
                AVG(message_count) as avg_messages,
                SUM(CASE WHEN initiated_by = 'user' THEN 1 ELSE 0 END)::float /
                    NULLIF(COUNT(*), 0) as initiation_rate
            FROM conversations
            WHERE user_id = :user_id
            """,
            {"user_id": str(user_id)},
        )

        length_row = await self.db.fetch_one(
            """
            SELECT AVG(LENGTH(m.content)) as avg_length
            FROM messages m
            JOIN conversations c ON m.conversation_id = c.id
            WHERE c.user_id = :user_id AND m.role = 'user'
            """,
            {"user_id": str(user_id)},
        )

        stats.update({
            "avg_messages": float(comm_row["avg_messages"] or 0) if comm_row else 0,
            "initiation_rate": float(comm_row["initiation_rate"] or 0) if comm_row else 0,
            "avg_length": float(length_row["avg_length"] or 0) if length_row else 0,
            "active_time": "varies",  # Could compute from message timestamps
        })

        return stats

    async def _count_domain_mentions(self, user_id: UUID, domain: str) -> int:
        """Count mentions of a domain in recent conversations."""
        # This is a simplified count - could be enhanced with NLP
        row = await self.db.fetch_one(
            """
            SELECT COUNT(*) as count
            FROM user_context
            WHERE user_id = :user_id
              AND domain = :domain
              AND updated_at > NOW() - INTERVAL '14 days'
            """,
            {"user_id": str(user_id), "domain": domain},
        )
        return int(row["count"] or 0) if row else 0

    async def _get_user_info(self, user_id: UUID) -> Dict[str, Any]:
        """Get basic user info."""
        row = await self.db.fetch_one(
            "SELECT display_name, companion_name, created_at FROM users WHERE id = :user_id",
            {"user_id": str(user_id)},
        )
        return dict(row) if row else {}
