"""Snapshot route for basket narrative (workspace-aware)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from ..utils.snapshot_assembler import assemble_snapshot
from ..utils.supabase_client import supabase_client as supabase

router = APIRouter(prefix="/baskets", tags=["baskets"])
log = logging.getLogger("uvicorn.error")


@router.get("/{basket_id}/snapshot")
def get_basket_snapshot(basket_id: str) -> dict:
    """
    Return a read-only snapshot for a basket.

    Expected JSON (matches the old contract):

    {
      "basket": { … },          # single row
      "raw_dumps": [ … ],       # *array* (len == 1 today)
      "blocks": [ … ]           # constant | locked | accepted
    }
    """
    try:
        # ── 1. basket row (RLS will hide others) ──────────────────
        basket_res = (
            supabase.table("baskets")
            .select("id, name, created_at, raw_dump_id")
            .eq("id", basket_id)
            .single()
            .execute()
        )
        if basket_res.data is None:
            raise HTTPException(status_code=404, detail="Basket not found")
        basket = basket_res.data

        # ── 2. the ONE raw_dump referenced by the basket ──────────
        dump_res = (
            supabase.table("raw_dumps")
            .select("id, body_md, created_at")
            .eq("id", basket["raw_dump_id"])
            .single()
            .execute()
        )
        if dump_res.data is None:
            raise HTTPException(
                status_code=404,
                detail="Raw dump not found for basket",
            )
        raw_dumps = [dump_res.data]  # keep array shape

        # ── 3. blocks in constant / locked / accepted state ───────
        blocks_res = (
            supabase.table("blocks")
            .select(
                "id, semantic_type, content, state, scope, canonical_value"
            )
            .eq("basket_id", basket_id)
            .in_("state", ["CONSTANT", "LOCKED", "ACCEPTED", "PROPOSED"])
            .execute()
        )
        blocks = blocks_res.data or []

    except HTTPException:
        raise
    except Exception as err:
        log.exception("get_basket_snapshot failed")
        raise HTTPException(status_code=500, detail="internal error") from err

    # ── 4. assemble & return in legacy shape ─────────────────────
    snapshot = assemble_snapshot(raw_dumps, blocks)  # returns dict
    snapshot["basket"] = basket
    return snapshot


@router.get("/snapshot/{basket_id}")
def get_basket_snapshot_service(basket_id: str) -> dict:
    """Expose snapshot via a stable path using the service role."""
    return get_basket_snapshot(basket_id)
