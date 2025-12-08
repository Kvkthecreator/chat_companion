"""Utility helpers for making payloads Supabase-safe (JSON-serialisable)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID
from typing import Any


def _to_safe(value: Any) -> Any:
    """Recursively convert non-JSON-safe objects (UUID, datetime, etc.)."""
    if isinstance(value, (UUID, datetime)):
        return str(value)
    if isinstance(value, dict):
        return {k: _to_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_to_safe(v) for v in value]
    return value


def json_safe(data: dict) -> dict:
    """
    Return a copy of *data* where all UUIDs, datetimes, and nested structures
    have been converted to plain JSON-serialisable primitives.
    """
    return {k: _to_safe(v) for k, v in data.items()}


# ── Legacy alias (keeps older code working) ────────────────────────────────
def as_json(obj: Any) -> Any:  # noqa: D401  (short alias kept for backward compatibility)
    """Alias to json_safe for old call-sites."""
    return _to_safe(obj)
