"""Memory API routes.

Provides endpoints for:
- Memory summary (dashboard card)
- Full memory retrieval (management page)
- Memory CRUD operations
- Thread management
"""
import json
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.deps import get_db
from app.dependencies import get_current_user_id

# Try to import old Episode-0 models for backwards compatibility
try:
    from app.models.memory import MemoryEvent, MemoryEventCreate, MemoryType
    HAS_LEGACY_MEMORY = True
except ImportError:
    HAS_LEGACY_MEMORY = False

router = APIRouter(prefix="/memory", tags=["Memory"])


# =============================================================================
# Response Models
# =============================================================================

class ThreadSummary(BaseModel):
    """Thread summary for display."""
    id: str
    topic: str
    summary: str
    status: str
    follow_up_date: Optional[str] = None
    key_details: List[str] = []
    updated_at: Optional[str] = None


class FollowUpSummary(BaseModel):
    """Follow-up question for display."""
    id: str
    question: str
    context: str
    follow_up_date: str
    source_thread: Optional[str] = None


class MemorySummary(BaseModel):
    """Summary for dashboard card."""
    active_threads: List[ThreadSummary]
    pending_follow_ups: List[FollowUpSummary]
    thread_count: int
    fact_count: int


class FactItem(BaseModel):
    """A single fact/memory item."""
    id: str
    category: str
    key: str
    value: str
    importance_score: float
    created_at: Optional[str] = None


class PatternItem(BaseModel):
    """A detected pattern."""
    id: str
    pattern_type: str
    description: str
    confidence: float
    message_hint: Optional[str] = None


class FullMemory(BaseModel):
    """Full memory for management page."""
    threads: List[ThreadSummary]
    follow_ups: List[FollowUpSummary]
    facts: Dict[str, List[FactItem]]
    patterns: List[PatternItem]


# =============================================================================
# Chat Companion Memory Endpoints
# =============================================================================

@router.get("/summary", response_model=MemorySummary)
async def get_memory_summary(
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Get memory summary for dashboard card.

    Returns active threads, pending follow-ups, and counts.
    """
    from app.services.threads import ThreadService

    thread_service = ThreadService(db)

    # Get active threads (limit 5)
    threads = await thread_service.get_active_threads(user_id, limit=5)
    active_threads = [
        ThreadSummary(
            id=str(t["id"]),
            topic=t["topic"],
            summary=t["summary"],
            status=t["status"],
            follow_up_date=t.get("follow_up_date"),
            key_details=t.get("key_details", []),
            updated_at=str(t["updated_at"]) if t.get("updated_at") else None,
        )
        for t in threads
        if t["status"] != "resolved"
    ]

    # Get pending follow-ups (limit 3)
    follow_ups = await thread_service.get_pending_follow_ups(user_id)
    pending_follow_ups = [
        FollowUpSummary(
            id=str(f["id"]),
            question=f["question"],
            context=f["context"],
            follow_up_date=str(f["follow_up_date"]),
            source_thread=f.get("source_thread"),
        )
        for f in follow_ups[:3]
    ]

    # Get counts
    thread_count = len([t for t in threads if t["status"] != "resolved"])

    fact_count_row = await db.fetch_one(
        """
        SELECT COUNT(*) as count
        FROM user_context
        WHERE user_id = :user_id
          AND category NOT IN ('thread', 'follow_up', 'pattern')
          AND (expires_at IS NULL OR expires_at > NOW())
        """,
        {"user_id": str(user_id)},
    )
    fact_count = int(fact_count_row["count"]) if fact_count_row else 0

    return MemorySummary(
        active_threads=active_threads,
        pending_follow_ups=pending_follow_ups,
        thread_count=thread_count,
        fact_count=fact_count,
    )


@router.get("/full", response_model=FullMemory)
async def get_full_memory(
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Get full memory for management page.

    Returns all threads, follow-ups, facts (grouped by category), and patterns.
    """
    from app.services.threads import ThreadService
    from app.services.patterns import PatternService

    thread_service = ThreadService(db)
    pattern_service = PatternService(db)

    # Get all threads
    all_threads = await thread_service.get_active_threads(user_id, limit=20)
    threads = [
        ThreadSummary(
            id=str(t["id"]),
            topic=t["topic"],
            summary=t["summary"],
            status=t["status"],
            follow_up_date=t.get("follow_up_date"),
            key_details=t.get("key_details", []),
            updated_at=str(t["updated_at"]) if t.get("updated_at") else None,
        )
        for t in all_threads
    ]

    # Get all follow-ups
    all_follow_ups = await thread_service.get_pending_follow_ups(user_id)
    follow_ups = [
        FollowUpSummary(
            id=str(f["id"]),
            question=f["question"],
            context=f["context"],
            follow_up_date=str(f["follow_up_date"]),
            source_thread=f.get("source_thread"),
        )
        for f in all_follow_ups
    ]

    # Get facts grouped by category
    fact_rows = await db.fetch_all(
        """
        SELECT id, category, key, value, importance_score, created_at
        FROM user_context
        WHERE user_id = :user_id
          AND category NOT IN ('thread', 'follow_up', 'pattern')
          AND (expires_at IS NULL OR expires_at > NOW())
        ORDER BY category, importance_score DESC
        """,
        {"user_id": str(user_id)},
    )

    facts: Dict[str, List[FactItem]] = {}
    category_labels = {
        "fact": "personal",
        "preference": "preferences",
        "relationship": "relationships",
        "goal": "goals",
        "emotion": "feelings",
        "situation": "situations",
        "routine": "routines",
        "struggle": "challenges",
        "event": "events",
    }

    for row in fact_rows:
        cat = row["category"]
        label = category_labels.get(cat, cat)
        if label not in facts:
            facts[label] = []
        facts[label].append(FactItem(
            id=str(row["id"]),
            category=cat,
            key=row["key"],
            value=row["value"],
            importance_score=float(row["importance_score"]) if row["importance_score"] else 0.5,
            created_at=str(row["created_at"]) if row["created_at"] else None,
        ))

    # Get patterns
    pattern_rows = await pattern_service.get_patterns(user_id)
    patterns = []
    for p in pattern_rows:
        pattern_type = p.get("pattern_type", "")
        description = _pattern_to_description(p)
        if description:
            patterns.append(PatternItem(
                id=str(p.get("id", "")),
                pattern_type=pattern_type,
                description=description,
                confidence=float(p.get("confidence", 0)),
                message_hint=p.get("message_hint"),
            ))

    return FullMemory(
        threads=threads,
        follow_ups=follow_ups,
        facts=facts,
        patterns=patterns,
    )


def _pattern_to_description(pattern: Dict[str, Any]) -> str:
    """Convert pattern data to human-readable description."""
    pattern_type = pattern.get("pattern_type", "")

    if pattern_type == "mood_trend":
        trend = pattern.get("trend_direction", "stable")
        window = pattern.get("window_days", 7)
        if trend == "improving":
            return f"Your mood has been improving over the past {window} days"
        elif trend == "declining":
            return f"You've seemed a bit lower over the past {window} days"
        else:
            return f"Your mood has been stable over the past {window} days"

    elif pattern_type == "engagement_trend":
        trend = pattern.get("trend_direction", "stable")
        if trend == "improving":
            return "You've been sharing more in conversations lately"
        elif trend == "declining":
            return "You've been a bit quieter in conversations lately"
        else:
            return "Your conversation engagement has been consistent"

    elif pattern_type == "topic_sentiment":
        topic = pattern.get("topic", "")
        sentiment = pattern.get("sentiment", "neutral")
        if sentiment == "positive":
            return f"You tend to feel positive when talking about {topic}"
        elif sentiment == "negative":
            return f"Talking about {topic} seems to be stressful for you"
        else:
            return f"You have mixed feelings about {topic}"

    return ""


@router.delete("/context/{context_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory_item(
    context_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Delete a memory item (fact, thread, or follow-up)."""
    result = await db.execute(
        """
        DELETE FROM user_context
        WHERE id = :id AND user_id = :user_id
        """,
        {"id": str(context_id), "user_id": str(user_id)},
    )

    # Check if anything was deleted
    if result == "DELETE 0":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory item not found",
        )


class UpdateMemoryRequest(BaseModel):
    """Request to update a memory item."""
    value: Optional[str] = None
    importance_score: Optional[float] = None


@router.patch("/context/{context_id}")
async def update_memory_item(
    context_id: UUID,
    data: UpdateMemoryRequest,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Update a memory item."""
    updates = []
    values = {"id": str(context_id), "user_id": str(user_id)}

    if data.value is not None:
        updates.append("value = :value")
        values["value"] = data.value

    if data.importance_score is not None:
        updates.append("importance_score = :importance_score")
        values["importance_score"] = data.importance_score

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No updates provided",
        )

    updates.append("updated_at = NOW()")

    query = f"""
        UPDATE user_context
        SET {', '.join(updates)}
        WHERE id = :id AND user_id = :user_id
        RETURNING *
    """

    row = await db.fetch_one(query, values)

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory item not found",
        )

    return dict(row)


@router.post("/threads/{thread_id}/resolve", status_code=status.HTTP_200_OK)
async def resolve_thread(
    thread_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Mark a thread as resolved."""
    # Get current thread data
    row = await db.fetch_one(
        """
        SELECT value FROM user_context
        WHERE id = :id AND user_id = :user_id AND category = 'thread'
        """,
        {"id": str(thread_id), "user_id": str(user_id)},
    )

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found",
        )

    # Update status to resolved
    try:
        data = json.loads(row["value"])
    except:
        data = {}

    data["status"] = "resolved"

    await db.execute(
        """
        UPDATE user_context
        SET value = :value, updated_at = NOW()
        WHERE id = :id AND user_id = :user_id
        """,
        {"id": str(thread_id), "user_id": str(user_id), "value": json.dumps(data)},
    )

    return {"status": "resolved"}


@router.get("", response_model=List[MemoryEvent])
async def list_memories(
    user_id: UUID = Depends(get_current_user_id),
    character_id: Optional[UUID] = Query(None),
    types: Optional[List[MemoryType]] = Query(None),
    min_importance: float = Query(0.0, ge=0, le=1),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db),
):
    """List memory events for the current user."""
    conditions = ["user_id = :user_id", "is_active = TRUE"]
    values = {"user_id": str(user_id), "limit": limit}

    if character_id:
        conditions.append("(character_id = :character_id OR character_id IS NULL)")
        values["character_id"] = str(character_id)

    if types:
        # Build IN clause with indexed parameters
        type_params = []
        for i, t in enumerate(types):
            param_name = f"type_{i}"
            type_params.append(f":{param_name}")
            values[param_name] = t.value
        conditions.append(f"type IN ({', '.join(type_params)})")

    if min_importance > 0:
        conditions.append("importance_score >= :min_importance")
        values["min_importance"] = min_importance

    query = f"""
        SELECT * FROM memory_events
        WHERE {" AND ".join(conditions)}
        ORDER BY importance_score DESC, created_at DESC
        LIMIT :limit
    """

    rows = await db.fetch_all(query, values)
    return [MemoryEvent(**dict(row)) for row in rows]


@router.get("/relevant", response_model=List[MemoryEvent])
async def get_relevant_memories(
    user_id: UUID = Depends(get_current_user_id),
    character_id: UUID = Query(...),
    limit: int = Query(10, ge=1, le=30),
    db=Depends(get_db),
):
    """Get memories relevant for a conversation.

    This uses a combination of:
    - Recent memories (last 7 days)
    - High importance memories
    - Character-specific and global memories
    """
    # For now, use a simple heuristic. Later can add vector similarity.
    query = """
        WITH ranked_memories AS (
            SELECT *,
                ROW_NUMBER() OVER (
                    PARTITION BY type
                    ORDER BY
                        CASE WHEN created_at > NOW() - INTERVAL '7 days' THEN 1 ELSE 0 END DESC,
                        importance_score DESC,
                        created_at DESC
                ) as rn
            FROM memory_events
            WHERE user_id = :user_id
                AND (character_id = :character_id OR character_id IS NULL)
                AND is_active = TRUE
        )
        SELECT * FROM ranked_memories
        WHERE rn <= 3
        ORDER BY importance_score DESC, created_at DESC
        LIMIT :limit
    """

    rows = await db.fetch_all(query, {"user_id": str(user_id), "character_id": str(character_id), "limit": limit})
    return [MemoryEvent(**dict(row)) for row in rows]


@router.post("", response_model=MemoryEvent, status_code=status.HTTP_201_CREATED)
async def create_memory(
    data: MemoryEventCreate,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Create a new memory event."""
    import json

    query = """
        INSERT INTO memory_events (
            user_id, character_id, episode_id, type, category,
            content, summary, emotional_valence, importance_score
        )
        VALUES (:user_id, :character_id, :episode_id, :type, :category,
                :content, :summary, :emotional_valence, :importance_score)
        RETURNING *
    """

    row = await db.fetch_one(
        query,
        {
            "user_id": str(user_id),
            "character_id": str(data.character_id) if data.character_id else None,
            "episode_id": str(data.episode_id) if data.episode_id else None,
            "type": data.type.value,
            "category": data.category,
            "content": json.dumps(data.content),
            "summary": data.summary,
            "emotional_valence": data.emotional_valence,
            "importance_score": data.importance_score,
        },
    )

    return MemoryEvent(**dict(row))


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memory_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Soft delete a memory event."""
    query = """
        UPDATE memory_events
        SET is_active = FALSE
        WHERE id = :memory_id AND user_id = :user_id
    """
    result = await db.execute(query, {"memory_id": str(memory_id), "user_id": str(user_id)})

    if result == "UPDATE 0":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found",
        )


@router.post("/{memory_id}/reference", response_model=MemoryEvent)
async def mark_memory_referenced(
    memory_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Mark a memory as referenced in conversation."""
    query = """
        UPDATE memory_events
        SET
            last_referenced_at = NOW(),
            reference_count = reference_count + 1
        WHERE id = :memory_id AND user_id = :user_id
        RETURNING *
    """
    row = await db.fetch_one(query, {"memory_id": str(memory_id), "user_id": str(user_id)})

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found",
        )

    return MemoryEvent(**dict(row))
