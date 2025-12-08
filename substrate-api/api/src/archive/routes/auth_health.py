"""Auth health endpoint for verifying JWT env alignment."""
from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/health")
async def auth_health(request: Request):
    payload = getattr(request.state, "jwt_payload", {}) or {}
    return {
        "iss": payload.get("iss"),
        "aud": payload.get("aud"),
        "sub": payload.get("sub"),
    }
