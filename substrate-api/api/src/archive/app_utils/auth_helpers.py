"""Authentication helper utilities.

Provide dependencies for FastAPI routes using Supabase tokens.
"""

from __future__ import annotations

from fastapi import HTTPException, Request

from .supabase_client import get_supabase


async def current_user_id(request: Request) -> str:
    """Return the authenticated user's ID from request state."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or missing authentication token")
    return str(user_id)


async def get_user(request: Request):
    """Return the user object for the provided Supabase JWT."""
    await current_user_id(request)
    token = request.headers.get("sb-access-token")
    if not token:
        auth = request.headers.get("Authorization")
        if auth and auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1]
    if not token:
        raise HTTPException(status_code=401, detail="Invalid or missing authentication token")

    supabase = get_supabase(token)
    try:
        user_response = supabase.auth.get_user(token)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=401, detail="Invalid or missing authentication token"
        ) from exc

    return getattr(user_response, "user", user_response)
