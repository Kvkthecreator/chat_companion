"""Artifacts API routes.

Provides endpoints for:
- Checking artifact availability
- Getting/generating artifacts by type
- Listing all user artifacts

See: docs/analysis/ARTIFACT_LAYER_ANALYSIS.md
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.deps import get_db
from app.dependencies import get_current_user_id
from app.services.artifacts import ArtifactService, ArtifactType

router = APIRouter(prefix="/artifacts", tags=["Artifacts"])


# =============================================================================
# Response Models
# =============================================================================


class ArtifactAvailabilityResponse(BaseModel):
    """Availability status for all artifact types."""
    thread_journey: Dict[str, Any]
    domain_health: Dict[str, Any]
    communication: Dict[str, Any]
    relationship: Dict[str, Any]


class ArtifactSection(BaseModel):
    """A section within an artifact."""
    type: str
    content: Any


class ArtifactResponse(BaseModel):
    """Full artifact response."""
    id: Optional[str] = None
    artifact_type: str
    title: str
    sections: List[ArtifactSection]
    companion_voice: Optional[str] = None
    data_sources: List[str] = []
    is_meaningful: bool = True
    min_data_reason: Optional[str] = None
    thread_id: Optional[str] = None
    domain: Optional[str] = None
    generated_at: Optional[str] = None


class ArtifactListItem(BaseModel):
    """Artifact summary for lists."""
    id: str
    artifact_type: str
    title: str
    is_meaningful: bool
    thread_id: Optional[str] = None
    domain: Optional[str] = None
    generated_at: str


class ThreadEventRequest(BaseModel):
    """Request to log a thread event."""
    thread_id: str
    event_type: str  # phase_change, milestone, mention, update
    description: str
    event_date: Optional[str] = None  # ISO format


# =============================================================================
# Availability Endpoint
# =============================================================================


@router.get("/available", response_model=ArtifactAvailabilityResponse)
async def check_availability(
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Check which artifacts are available for the current user.

    Returns availability status for each artifact type, including:
    - Whether the artifact can be generated
    - Relevant reference data (threads, domains, stats)
    """
    service = ArtifactService(db)
    availability = await service.check_availability(user_id)

    return ArtifactAvailabilityResponse(
        thread_journey=availability.get("thread_journey", {"available": False}),
        domain_health=availability.get("domain_health", {"available": False}),
        communication=availability.get("communication", {"available": False}),
        relationship=availability.get("relationship", {"available": False}),
    )


# =============================================================================
# Artifact List Endpoint
# =============================================================================


@router.get("", response_model=List[ArtifactListItem])
async def list_artifacts(
    meaningful_only: bool = True,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """List all stored artifacts for the current user.

    Args:
        meaningful_only: If True, only return artifacts with sufficient data
    """
    service = ArtifactService(db)
    artifacts = await service.get_all_artifacts(user_id, meaningful_only=meaningful_only)

    return [
        ArtifactListItem(
            id=str(a["id"]),
            artifact_type=a["artifact_type"],
            title=a["title"],
            is_meaningful=a.get("is_meaningful", True),
            thread_id=str(a["thread_id"]) if a.get("thread_id") else None,
            domain=a.get("domain"),
            generated_at=a["generated_at"].isoformat() if a.get("generated_at") else "",
        )
        for a in artifacts
    ]


# =============================================================================
# Thread Journey Artifact
# =============================================================================


@router.get("/thread-journey/{thread_id}", response_model=ArtifactResponse)
async def get_thread_journey(
    thread_id: str,
    regenerate: bool = False,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Get the Thread Journey artifact for a specific thread.

    Args:
        thread_id: UUID of the thread
        regenerate: If True, regenerate even if cached

    Returns the timeline, insights, and companion reflection for the thread.
    """
    service = ArtifactService(db)

    # Check for existing artifact
    if not regenerate:
        existing = await service.get_artifact(
            user_id,
            ArtifactType.THREAD_JOURNEY,
            thread_id=UUID(thread_id),
        )
        if existing:
            return _format_artifact_response(existing)

    # Generate new artifact
    artifact = await service.generate_thread_journey(user_id, UUID(thread_id))

    # Save artifact
    if artifact.is_meaningful:
        saved = await service.save_artifact(user_id, artifact)
        if saved:
            artifact_dict = artifact.to_dict()
            artifact_dict["id"] = str(saved["id"])
            artifact_dict["generated_at"] = saved["generated_at"].isoformat()
            return ArtifactResponse(**artifact_dict)

    return ArtifactResponse(**artifact.to_dict())


# =============================================================================
# Domain Health Artifact
# =============================================================================


@router.get("/domain-health/{domain}", response_model=ArtifactResponse)
async def get_domain_health(
    domain: str,
    regenerate: bool = False,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Get the Domain Health artifact for a specific domain.

    Args:
        domain: Domain name (career, location, relationships, health, creative, life_stage, personal)
        regenerate: If True, regenerate even if cached

    Returns an overview of all threads in the domain with companion reflection.
    """
    valid_domains = ["career", "location", "relationships", "health", "creative", "life_stage", "personal"]
    if domain not in valid_domains:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid domain. Must be one of: {', '.join(valid_domains)}",
        )

    service = ArtifactService(db)

    # Check for existing artifact
    if not regenerate:
        existing = await service.get_artifact(
            user_id,
            ArtifactType.DOMAIN_HEALTH,
            domain=domain,
        )
        if existing:
            return _format_artifact_response(existing)

    # Generate new artifact
    artifact = await service.generate_domain_health(user_id, domain)

    # Save artifact
    if artifact.is_meaningful:
        saved = await service.save_artifact(user_id, artifact)
        if saved:
            artifact_dict = artifact.to_dict()
            artifact_dict["id"] = str(saved["id"])
            artifact_dict["generated_at"] = saved["generated_at"].isoformat()
            return ArtifactResponse(**artifact_dict)

    return ArtifactResponse(**artifact.to_dict())


# =============================================================================
# Communication Profile Artifact
# =============================================================================


@router.get("/communication-profile", response_model=ArtifactResponse)
async def get_communication_profile(
    regenerate: bool = False,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Get the Communication Profile artifact.

    Args:
        regenerate: If True, regenerate even if cached

    Returns analysis of how the user communicates with companion reflection.
    """
    service = ArtifactService(db)

    # Check for existing artifact
    if not regenerate:
        existing = await service.get_artifact(
            user_id,
            ArtifactType.COMMUNICATION,
        )
        if existing:
            return _format_artifact_response(existing)

    # Generate new artifact
    artifact = await service.generate_communication_profile(user_id)

    # Save artifact
    if artifact.is_meaningful:
        saved = await service.save_artifact(user_id, artifact)
        if saved:
            artifact_dict = artifact.to_dict()
            artifact_dict["id"] = str(saved["id"])
            artifact_dict["generated_at"] = saved["generated_at"].isoformat()
            return ArtifactResponse(**artifact_dict)

    return ArtifactResponse(**artifact.to_dict())


# =============================================================================
# Relationship Summary Artifact
# =============================================================================


@router.get("/relationship-summary", response_model=ArtifactResponse)
async def get_relationship_summary(
    regenerate: bool = False,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Get the Relationship Summary artifact.

    Args:
        regenerate: If True, regenerate even if cached

    Returns overall relationship summary with companion reflection.
    """
    service = ArtifactService(db)

    # Check for existing artifact
    if not regenerate:
        existing = await service.get_artifact(
            user_id,
            ArtifactType.RELATIONSHIP,
        )
        if existing:
            return _format_artifact_response(existing)

    # Generate new artifact
    artifact = await service.generate_relationship_summary(user_id)

    # Save artifact
    if artifact.is_meaningful:
        saved = await service.save_artifact(user_id, artifact)
        if saved:
            artifact_dict = artifact.to_dict()
            artifact_dict["id"] = str(saved["id"])
            artifact_dict["generated_at"] = saved["generated_at"].isoformat()
            return ArtifactResponse(**artifact_dict)

    return ArtifactResponse(**artifact.to_dict())


# =============================================================================
# Event Logging (for Thread Journey timeline)
# =============================================================================


@router.post("/events")
async def log_thread_event(
    request: ThreadEventRequest,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Log an event for a thread (for building timeline).

    Events are used to build the Thread Journey artifact timeline.
    Call this when significant things happen to a thread.

    Args:
        thread_id: UUID of the thread
        event_type: Type of event (phase_change, milestone, mention, update)
        description: Human-readable description
        event_date: Optional ISO date (defaults to now)
    """
    from datetime import datetime

    service = ArtifactService(db)

    event_date = None
    if request.event_date:
        try:
            event_date = datetime.fromisoformat(request.event_date.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid event_date format. Use ISO 8601.",
            )

    result = await service.log_thread_event(
        user_id=user_id,
        thread_id=UUID(request.thread_id),
        event_type=request.event_type,
        description=request.description,
        event_date=event_date,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to log event",
        )

    return {
        "success": True,
        "event_id": str(result["id"]),
        "thread_id": request.thread_id,
    }


# =============================================================================
# Helper Functions
# =============================================================================


def _format_artifact_response(artifact_dict: Dict[str, Any]) -> ArtifactResponse:
    """Format a database artifact dict into an API response."""
    sections = artifact_dict.get("sections", [])
    if isinstance(sections, str):
        import json
        sections = json.loads(sections)

    return ArtifactResponse(
        id=str(artifact_dict.get("id", "")),
        artifact_type=artifact_dict.get("artifact_type", ""),
        title=artifact_dict.get("title", ""),
        sections=[ArtifactSection(**s) for s in sections],
        companion_voice=artifact_dict.get("companion_voice"),
        data_sources=artifact_dict.get("data_sources", []),
        is_meaningful=artifact_dict.get("is_meaningful", True),
        min_data_reason=artifact_dict.get("min_data_reason"),
        thread_id=str(artifact_dict["thread_id"]) if artifact_dict.get("thread_id") else None,
        domain=artifact_dict.get("domain"),
        generated_at=artifact_dict["generated_at"].isoformat() if artifact_dict.get("generated_at") else None,
    )
