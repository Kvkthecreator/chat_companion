from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator

from ..utils.jwt import verify_jwt
from ..utils.workspace import get_or_create_workspace
from ...services.events import EventService

router = APIRouter(prefix="/events", tags=["events"])


class EmitEventRequest(BaseModel):
    type: str
    name: str
    message: str
    severity: str = "info"
    phase: Optional[str] = None
    basket_id: Optional[str] = None
    entity_id: Optional[str] = None
    correlation_id: Optional[str] = None
    dedupe_key: Optional[str] = None
    ttl_ms: Optional[int] = None
    payload: Optional[Dict[str, Any]] = None

    @field_validator('type')
    @classmethod
    def validate_type(cls, value: str) -> str:
        allowed = {"job_update", "system_alert", "action_result", "collab_activity", "validation"}
        if value not in allowed:
            raise ValueError(f"Unsupported event type '{value}'")
        return value


@router.post('/emit')
async def emit_event(body: EmitEventRequest, user=Depends(verify_jwt)):
    workspace_id = get_or_create_workspace(user['user_id'])

    try:
        EventService.emit_app_event(
            workspace_id=workspace_id,
            type=body.type,
            name=body.name,
            message=body.message,
            severity=body.severity,
            phase=body.phase,
            basket_id=body.basket_id,
            entity_id=body.entity_id,
            correlation_id=body.correlation_id,
            dedupe_key=body.dedupe_key,
            ttl_ms=body.ttl_ms,
            payload=body.payload,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"event_emit_failed: {exc}") from exc

    return {"ok": True}


__all__ = ["router"]
