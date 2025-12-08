"""Minimal Supabase JWT verification helper."""

from __future__ import annotations

from fastapi import HTTPException, Request


def verify_jwt(request: Request) -> dict[str, str]:
    """Return the caller's user ID, set by :class:`AuthMiddleware`."""

    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    return {"user_id": str(user_id)}

