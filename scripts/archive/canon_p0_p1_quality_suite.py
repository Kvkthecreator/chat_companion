#!/usr/bin/env python3
"""
Canon Smoke Suite: P0 Capture + P1 Quality (+ optional P2)

Purpose
  - Create an isolated basket in the provided workspace
  - Ingest a deterministic dump (P0)
  - Validate P1 proposals obey canon (blocks + context_items only, adequate quality)
  - Optionally map P2 relationships (lightweight check)

Usage
  # Env (override as needed)
  export SUPABASE_URL=https://<project>.supabase.co
  export SUPABASE_ANON_KEY=<anon>
  export SUPABASE_SERVICE_ROLE_KEY=<service>
  export YARNNN_TEST_WORKSPACE_ID=<workspace-uuid>

  # Run
  python3 scripts/canon_p0_p1_quality_suite.py [--p2]

Notes
  - Uses service-role client; intended for internal verification.
  - Does not require the Next.js server; uses direct DB API for speed.
  - Idempotent enough for repeated runs; creates a new basket each time.
"""

from __future__ import annotations

import os
import sys
import time
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Add API src for unified client usage
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api", "src"))

from app.utils.supabase_client import supabase_admin_client as supabase  # type: ignore

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger("canon-smoke")


WORKSPACE_ID = os.getenv("YARNNN_TEST_WORKSPACE_ID", "31ee30fe-6ae3-4604-ab6d-ac9b9f06dfde")
CONFIDENCE_MIN = float(os.getenv("YARNNN_P1_CONFIDENCE_MIN", "0.70"))
WAIT_PROPOSALS_SEC = int(os.getenv("YARNNN_WAIT_PROPOSALS_SEC", "30"))


TEST_CONTENT = (
    "Canon Smoke: Project Beacon — deterministic substrate probe.\n\n"
    "Goals: reduce incident MTTR by 40%, ship SOC2 Type II by Q4.\n"
    "Entities: SRE Team, SIEM, PagerDuty, Compliance.\n"
    "Risks: data retention gaps, alert fatigue.\n"
    "Metrics: MTTR < 30m, NPS > 50, coverage > 95%.\n"
    "Plan: phased rollout, runbooks, auto-remediation.\n"
)


def _require_env() -> None:
    miss = [k for k in ("SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_SERVICE_ROLE_KEY") if not os.getenv(k)]
    if miss:
        raise RuntimeError(f"Missing required env: {', '.join(miss)}")


def create_basket(workspace_id: str) -> str:
    basket_id = str(uuid.uuid4())
    payload = {
        "id": basket_id,
        "workspace_id": workspace_id,
        "name": f"Canon Smoke {datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
        "status": "ACTIVE",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    resp = supabase.table("baskets").insert(payload).execute()
    if not resp.data:
        raise RuntimeError("Failed to create basket")
    log.info(f"Created basket: {basket_id}")
    return basket_id


def ingest_dump(basket_id: str, content: str) -> str:
    # Use RPC for canonical ingestion
    dumps = [{
        "dump_request_id": str(uuid.uuid4()),
        "text_dump": content,
        "source_meta": {"smoke": "canon_p0_p1", "ts": datetime.utcnow().isoformat()},
    }]
    r = supabase.rpc(
        "fn_ingest_dumps",
        {"p_workspace_id": WORKSPACE_ID, "p_basket_id": basket_id, "p_dumps": dumps},
    ).execute()
    if not getattr(r, "data", None):
        raise RuntimeError("Dump ingest failed (no data returned)")
    dump_id = r.data[0]["dump_id"]
    log.info(f"Ingested dump: {dump_id}")
    return dump_id


def wait_for_p1_proposal(dump_id: str, timeout_sec: int) -> Optional[Dict[str, Any]]:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        res = supabase.table("proposals").select(
            "id,status,ops,validator_report,is_executed,created_at,provenance"
        ).filter("provenance", "cs", f'["{dump_id}"]').order("created_at", desc=True).limit(1).execute()
        if res.data:
            return res.data[0]
        time.sleep(2)
    return None


KEY_TOKENS = [
    "mttr", "soc2", "sre team", "pagerduty", "compliance",
    "nps", "coverage", "auto-remediation", "runbooks"
]


def assert_p1_canon_quality(proposal: Dict[str, Any]) -> Dict[str, Any]:
    ops = proposal.get("ops", []) or []
    kinds = [op.get("type") for op in ops if isinstance(op, dict)]
    counts: Dict[str, int] = {}
    for k in kinds:
        counts[k] = counts.get(k, 0) + 1

    # Canon: Only substrate ops here, no relationships, no artifact ops
    forbidden = {"CreateRelationship", "AttachBlockToDoc", "CreateReflection", "ComposeDocument"}
    if any(k in forbidden for k in kinds):
        raise AssertionError(f"Forbidden op present: {sorted(set(kinds) & forbidden)}")

    create_blocks = counts.get("CreateBlock", 0)
    create_items = counts.get("CreateContextItem", 0)

    # Expect both present (content contains goals/entities/metrics)
    if create_blocks < 1 or create_items < 2:
        raise AssertionError(
            f"Low-quality extraction: blocks={create_blocks}, context_items={create_items}"
        )

    # Basic semantic grounding: ensure some known tokens appear in proposed substrate
    hay = []
    for op in ops:
        if not isinstance(op, dict):
            continue
        # capture label/content fields if present
        for field in ("content", "label", "title"):
            v = op.get(field)
            if isinstance(v, str) and v:
                hay.append(v.lower())
    haystack = "\n".join(hay)
    grounded = any(tok in haystack for tok in KEY_TOKENS)
    if not grounded:
        raise AssertionError("Proposed substrate does not reflect expected first‑principles tokens from the dump")

    vr = proposal.get("validator_report") or {}
    conf = float(vr.get("confidence", 0.0))
    if conf < CONFIDENCE_MIN:
        raise AssertionError(f"Low validator confidence: {conf:.3f} < {CONFIDENCE_MIN:.2f}")

    # Double-check provenance
    provenance = proposal.get("provenance") or []
    if not provenance:
        raise AssertionError("Missing provenance in proposal")

    return {
        "counts": counts,
        "confidence": conf,
        "executed": bool(proposal.get("is_executed")),
        "proposal_id": proposal.get("id"),
    }


def optional_p2_relationships(basket_id: str) -> int:
    """Best-effort: create a few relationships if agent RPCs not available."""
    try:
        # Minimal heuristic: insert a self-evident relationship between first two blocks if they exist
        blocks = supabase.table("blocks").select("id,content,semantic_type").eq("basket_id", basket_id).limit(2).execute()
        if not blocks.data or len(blocks.data) < 2:
            return 0
        a, b = blocks.data[0]["id"], blocks.data[1]["id"]
        rel = {
            "basket_id": basket_id,
            "from_type": "block",
            "from_id": a,
            "to_type": "block",
            "to_id": b,
            "relationship_type": "semantic_similarity",
            "strength": 0.7,
            "description": "canon_smoke_pair",
            "metadata": {"source": "canon_smoke"},
        }
        ins = supabase.table("substrate_relationships").insert(rel).execute()
        return 1 if ins.data else 0
    except Exception:
        return 0


def main() -> int:
    _require_env()
    log.info(f"Workspace: {WORKSPACE_ID}")
    basket_id = create_basket(WORKSPACE_ID)
    dump_id = ingest_dump(basket_id, TEST_CONTENT)

    log.info("Waiting for P1 proposal (up to %ss)...", WAIT_PROPOSALS_SEC)
    proposal = wait_for_p1_proposal(dump_id, WAIT_PROPOSALS_SEC)
    if not proposal:
        log.error("No P1 proposal detected for dump %s", dump_id)
        return 2

    summary = assert_p1_canon_quality(proposal)
    log.info("P1 OK — ops=%s, confidence=%.3f, executed=%s",
             json.dumps(summary["counts"]), summary["confidence"], summary["executed"])

    # Optional P2 (best-effort) if flag present
    if "--p2" in sys.argv:
        created = optional_p2_relationships(basket_id)
        log.info("P2 relationships created: %s", created)

    print("\n=== Canon Smoke Result ===")
    print(json.dumps({
        "workspace_id": WORKSPACE_ID,
        "basket_id": basket_id,
        "dump_id": dump_id,
        "proposal_id": summary.get("proposal_id"),
        "ops": summary.get("counts"),
        "confidence": summary.get("confidence"),
        "executed": summary.get("executed"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
