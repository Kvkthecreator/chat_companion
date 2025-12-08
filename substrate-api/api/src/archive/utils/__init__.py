from .db import json_safe

try:  # noqa: WPS501
    from .supabase_client import supabase_client
except Exception:  # pragma: no cover - best effort import
    supabase_client = None

__all__ = ["json_safe", "supabase_client"]
