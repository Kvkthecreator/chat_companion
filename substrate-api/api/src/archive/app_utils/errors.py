from __future__ import annotations

from fastapi import HTTPException


def raise_on_supabase_error(resp) -> None:
    """Raise HTTPException if a Supabase response indicates failure."""
    error = getattr(resp, "error", None)
    status = getattr(resp, "status_code", 200)
    if error or (status and status >= 400):
        detail = str(error or resp)
        raise HTTPException(status_code=500, detail=detail)
