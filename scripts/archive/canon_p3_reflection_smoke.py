#!/usr/bin/env python3
"""
Canon P3 Reflection Smoke

Computes a reflection artifact for a basket using the canon P3 agent and
verifies an artifact row exists in `reflections_artifact`.

Env: SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY,
     YARNNN_TEST_WORKSPACE_ID (defaults to shared test workspace)
"""

from __future__ import annotations

import os
import sys
import asyncio
import logging
from uuid import UUID
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api", "src"))

from app.utils.supabase_client import supabase_admin_client as supabase  # type: ignore
from app.agents.pipeline.reflection_agent_canon_v2 import (
    CanonP3ReflectionAgent,
    ReflectionComputationRequest,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger("canon-p3-smoke")

WORKSPACE_ID = os.getenv("YARNNN_TEST_WORKSPACE_ID", "31ee30fe-6ae3-4604-ab6d-ac9b9f06dfde")


def pick_or_create_basket(workspace_id: str) -> str:
    # Prefer a basket with at least one dump
    r = (
        supabase.table("raw_dumps")
        .select("basket_id")
        .eq("workspace_id", workspace_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if r.data:
        return r.data[0]["basket_id"]
    # Create a small basket + dump if no existing
    import uuid
    bid = str(uuid.uuid4())
    supabase.table("baskets").insert({
        "id": bid, "workspace_id": workspace_id, "name": "P3 Smoke", "status": "ACTIVE",
        "created_at": datetime.now(timezone.utc).isoformat()
    }).execute()
    dumps = [{
        "dump_request_id": str(uuid.uuid4()),
        "text_dump": "P3 smoke minimal substrate for reflection",
        "source_meta": {"smoke": "p3"}
    }]
    supabase.rpc('fn_ingest_dumps', {
        'p_workspace_id': workspace_id, 'p_basket_id': bid, 'p_dumps': dumps
    }).execute()
    return bid


def main() -> int:
    bid = pick_or_create_basket(WORKSPACE_ID)
    log.info(f"Basket: {bid}")
    agent = CanonP3ReflectionAgent()
    req = ReflectionComputationRequest(
        workspace_id=UUID(WORKSPACE_ID), basket_id=UUID(bid), agent_id="p3-smoke"
    )
    res = asyncio.run(agent.compute_reflections(req))
    log.info("Reflection meta: %s", res.meta)
    chk = (
        supabase.table("reflections_artifact")
        .select("id,reflection_text,computation_timestamp")
        .eq("workspace_id", WORKSPACE_ID)
        .eq("basket_id", bid)
        .order("computation_timestamp", desc=True)
        .limit(1)
        .execute()
    )
    ok = bool(chk.data)
    print("artifact:", ok)
    if ok:
        print("preview:", (chk.data[0]["reflection_text"] or "")[:100])
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())

