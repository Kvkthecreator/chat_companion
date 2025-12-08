from __future__ import annotations

import logging
import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from infra.substrate.services.embedding import generate_embedding
from ..utils.supabase import supabase_admin

logger = logging.getLogger("uvicorn.error")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_text(value: Optional[str]) -> str:
    return (value or "").strip()


def _extract_anchor_candidates(reflections: Iterable[Dict[str, Any]], limit: int = 5) -> List[str]:
    anchors: List[str] = []
    for reflection in reflections:
        meta = reflection.get("meta") or {}
        headline = _clean_text(meta.get("headline"))
        body = _clean_text(meta.get("body"))
        if headline:
            anchors.append(headline)
        elif body:
            anchors.append(body[:140])
        if len(anchors) >= limit:
            break
    return anchors


ENTITY_PATTERN = re.compile(r"\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)?\b")
STOPWORDS = {
    "the",
    "and",
    "that",
    "with",
    "from",
    "into",
    "about",
    "over",
    "this",
    "have",
    "your",
    "their",
    "will",
    "should",
    "because",
    "while",
    "where",
    "which",
}


def _extract_entities(text_windows: Iterable[str], limit: int = 12) -> List[str]:
    seen: List[str] = []
    for window in text_windows:
        for match in ENTITY_PATTERN.findall(window or ""):
            candidate = match.strip()
            if candidate and candidate not in seen and len(seen) < limit:
                seen.append(candidate)
        if len(seen) >= limit:
            break
    return seen


def _extract_keywords(summary: str, anchors: Iterable[str], limit: int = 12) -> List[str]:
    tokens: Counter[str] = Counter()
    source = " ".join(filter(None, [summary, *anchors]))
    for raw in re.findall(r"[a-zA-Z]{4,}", source.lower()):
        if raw in STOPWORDS:
            continue
        tokens[raw] += 1
    return [word for word, _count in tokens.most_common(limit)]


def build_signature_payload(
    *,
    workspace_id: str,
    basket_id: str,
    summary: str,
    reflections: List[Dict[str, Any]],
    text_window: List[Dict[str, Any]],
    source_reflection_id: Optional[str],
) -> Optional[Dict[str, Any]]:
    """Prepare the payload used to upsert ``basket_signatures`` rows."""

    summary_clean = _clean_text(summary)
    if not summary_clean:
        return None

    anchors = _extract_anchor_candidates(reflections)
    text_samples = [dump.get("text_dump") or dump.get("body_md") or "" for dump in text_window]
    entities = _extract_entities(text_samples)
    keywords = _extract_keywords(summary_clean, anchors)

    embed_source = "\n".join(filter(None, [summary_clean, *anchors]))
    embedding = generate_embedding(embed_source)

    payload = {
        "basket_id": str(basket_id),
        "workspace_id": str(workspace_id),
        "summary": summary_clean,
        "anchors": anchors,
        "entities": entities or None,
        "keywords": keywords or None,
        "embedding": embedding or None,
        "last_refreshed": _now_iso(),
        "source_reflection_id": str(source_reflection_id) if source_reflection_id else None,
        "updated_at": _now_iso(),
    }

    if embedding is None:
        logger.warning("Basket signature embedding missing (basket=%s)", basket_id)

    return payload


def upsert_basket_signature(payload: Dict[str, Any]) -> None:
    """Persist the signature using Supabase."""

    sb = supabase_admin()
    try:
        sb.table("basket_signatures").upsert(payload, on_conflict="basket_id").execute()
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to upsert basket signature: %s", exc)
