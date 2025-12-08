# V3.0 DEPRECATION NOTICE:
# This file contains references to context_items table which was merged into blocks table.
# Entity blocks are now identified by semantic_type='entity'.
# This file is legacy/supporting code - update if actively maintained.

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any
from datetime import datetime

from ..utils.supabase_client import supabase_client as supabase

router = APIRouter(prefix="/api/baskets", tags=["projection"])


@router.get("/{basket_id}/projection")
async def get_projection(
    basket_id: str,
    limit: int = Query(200, ge=1, le=1000),
    since: str | None = None,
) -> Dict[str, Any]:
    """
    Build an in-memory projection from existing tables:
      - recent raw_dumps (window)
      - context_items touching those dumps or basket
      - substrate_relationships touching those dumps
    Returns a light graph usable by reflections.
    """
    since_dt = None
    if since:
        try:
            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid 'since' ISO timestamp")

    q = (
        supabase.table("raw_dumps")
        .select("id, created_at")
        .eq("basket_id", basket_id)
        .order("created_at", desc=True)
        .limit(limit)
    )
    if since_dt:
        q = q.gte("created_at", since_dt.isoformat())
    dumps_resp = q.execute()
    dump_rows = dumps_resp.data or []
    dump_ids = [r["id"] for r in dump_rows]
    if not dump_ids:
        return {"entities": [], "edges": []}

    ci_resp = (
        supabase.table("context_items")
        .select("id, type, title, raw_dump_id, metadata")
        .eq("basket_id", basket_id)
        .in_("raw_dump_id", dump_ids)
        .execute()
    )
    ci_rows = ci_resp.data or []

    ci_basket_resp = (
        supabase.table("context_items")
        .select("id, type, title, raw_dump_id, metadata")
        .eq("basket_id", basket_id)
        .is_("raw_dump_id", None)
        .execute()
    )
    ci_rows += ci_basket_resp.data or []

    rel_resp = (
        supabase.table("substrate_relationships")
        .select("from_type,from_id,to_type,to_id,relationship_type,strength")
        .eq("basket_id", basket_id)
        .in_("from_id", dump_ids)
        .execute()
    )
    rel_rows = rel_resp.data or []

    rel_resp2 = (
        supabase.table("substrate_relationships")
        .select("from_type,from_id,to_type,to_id,relationship_type,strength")
        .eq("basket_id", basket_id)
        .in_("to_id", dump_ids)
        .execute()
    )
    rel_rows += rel_resp2.data or []

    ent_counts: Dict[str, int] = {}
    for ci in ci_rows:
        title = (ci.get("title") or "").strip()
        if not title:
            continue
        ent_counts[title] = ent_counts.get(title, 0) + 1
    entities = [
        {"title": t, "count": c}
        for t, c in sorted(ent_counts.items(), key=lambda x: -x[1])
    ]

    edges = [
        {
            "from_id": f'{r["from_type"]}:{r["from_id"]}',
            "to_id": f'{r["to_type"]}:{r["to_id"]}',
            "weight": r.get("strength", 0.5),
        }
        for r in rel_rows
    ]

    return {"entities": entities[:50], "edges": edges[:500]}
