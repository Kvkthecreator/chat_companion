"""Database helper functions for idempotency and metadata handling."""

from typing import Optional, Dict, Any, List
import json
from uuid import uuid4

from .supabase_client import supabase_client as supabase
from .db import as_json


async def check_existing_dumps(basket_id: str, trace_id: str) -> Optional[List[str]]:
    """
    Check if dumps already exist for this basket and trace_id.
    Returns list of dump IDs if found, None otherwise.
    """
    try:
        resp = (
            supabase.table("raw_dumps")
            .select("id")
            .eq("basket_id", basket_id)
            .eq("ingest_trace_id", trace_id)
            .execute()
        )
        
        if resp.data:
            return [row["id"] for row in resp.data]
        return None
    except Exception:
        # If query fails (e.g., column doesn't exist yet), return None
        return None


def format_source_meta(meta_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Format source metadata for storage."""
    return {
        "version": 1,
        "items": meta_items,
        "summary": {
            "total_files": len(meta_items),
            "parsed_files": sum(1 for m in meta_items if m.get("parsed", False)),
            "total_chars": sum(m.get("chars_extracted", 0) for m in meta_items),
        }
    }