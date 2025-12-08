"""Assemble read-only snapshot data for a basket."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def assemble_snapshot(
    raw_dumps: Iterable[dict[str, Any]], blocks: Iterable[dict[str, Any]]
) -> dict[str, Any]:
    """Return snapshot dict joining dumps and selected blocks."""
    dumps = sorted(raw_dumps, key=lambda d: d.get("created_at", ""))
    latest = dumps[-1] if dumps else {"body_md": ""}

    grouped = {
        "constants": [b for b in blocks if b.get("state") == "CONSTANT"],
        "locked_blocks": [b for b in blocks if b.get("state") == "LOCKED"],
        "accepted_blocks": [b for b in blocks if b.get("state") == "ACCEPTED"],
        "proposed_blocks": [b for b in blocks if b.get("state") == "PROPOSED"],
    }

    return {"raw_dump": latest["body_md"], **grouped}
