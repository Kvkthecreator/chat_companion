from __future__ import annotations


def log_event(kind: str, payload: dict | None = None) -> None:
    """Placeholder logger.  In future this will insert into the
    `events` table or send to telemetry.  For now it is a no-op.
    """
    return None
