"""
P3/P4 Context-Driven Freshness Computation (V3.0 Compliant)

Implements staleness detection based on substrate changes and graph topology,
NOT time-based thresholds (per YARNNN Canon v3.1).

Freshness Model:
  Staleness = f(substrate_hash_changed, graph_topology_changed, temporal_scope_invalid)

V3.0 Migration Completed:
- Removed context_items references (merged into blocks table)
- Updated state queries to use V3.0 enum values (ACCEPTED, LOCKED, CONSTANT)
"""


import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from supabase import Client
else:
    Client = object  # Runtime placeholder


def compute_basket_substrate_hash(supabase: Client, basket_id: str) -> str:
    """
    Compute deterministic hash of basket's current substrate state (V3.0 compliant).

    Includes:
    - All ACCEPTED+ blocks (content + semantic_type)
    - All raw_dumps (body_md)
    - All timeline_events (event_type + summary)

    V3.0 Changes:
    - context_items removed (merged into blocks)
    - Query blocks with ACCEPTED, LOCKED, CONSTANT states only

    Returns SHA256 hex digest.
    """
    hasher = hashlib.sha256()

    # Fetch all substrate ordered deterministically
    blocks = supabase.table('blocks').select('id, content, semantic_type').eq(
        'basket_id', basket_id
    ).in_('state', ['ACCEPTED', 'LOCKED', 'CONSTANT']).order('created_at').execute()

    dumps = supabase.table('raw_dumps').select('id, body_md').eq(
        'basket_id', basket_id
    ).order('created_at').execute()

    events = supabase.table('timeline_events').select('id, kind, preview').eq(
        'basket_id', basket_id
    ).order('ts').execute()

    # Hash each substrate component
    for block in blocks.data:
        hasher.update(f"block:{block['id']}:{block['semantic_type']}:{block.get('content', '')}".encode())

    for dump in dumps.data:
        hasher.update(f"dump:{dump['id']}:{dump.get('body_md', '')}".encode())

    for event in events.data:
        hasher.update(f"event:{event['id']}:{event['kind']}:{event.get('preview', '')}".encode())

    return hasher.hexdigest()


def compute_graph_signature(supabase: Client, basket_id: str) -> str:
    """
    Compute deterministic signature of basket's relationship graph topology (V3.1 compliant).

    Captures:
    - All substrate_relationships (from_block_id, to_block_id, relationship_type)
    - Ordered by creation to ensure determinism

    V3.1 Changes:
    - substrate_relationships is graph edge table (no basket_id column)
    - Must join through blocks table to filter by basket
    - Uses from_block_id/to_block_id (not from_type/from_id)

    Returns SHA256 hex digest.
    """
    hasher = hashlib.sha256()

    # Get all blocks in basket first
    blocks = supabase.table('blocks').select('id').eq('basket_id', basket_id).in_(
        'state', ['ACCEPTED', 'LOCKED', 'CONSTANT']
    ).execute()

    block_ids = [block['id'] for block in blocks.data] if blocks.data else []

    if not block_ids:
        return hasher.hexdigest()  # Empty basket = empty hash

    # Get relationships where from_block is in this basket
    relationships = supabase.table('substrate_relationships').select(
        'from_block_id, to_block_id, relationship_type, confidence_score'
    ).in_('from_block_id', block_ids).in_(
        'state', ['ACCEPTED', 'LOCKED', 'CONSTANT']
    ).order('created_at').execute()

    for rel in relationships.data:
        hasher.update(
            f"rel:{rel['from_block_id']}:{rel['to_block_id']}:{rel['relationship_type']}:{rel.get('confidence_score', 0.5)}".encode()
        )

    return hasher.hexdigest()


def check_temporal_scope_validity(insight: Dict[str, Any]) -> bool:
    """
    Check if timeboxed_insight's temporal scope is still valid.

    Only applicable for insight_type = 'timeboxed_insight'.
    Returns True if scope has drifted (needs regeneration).
    """
    if insight.get('insight_type') != 'timeboxed_insight':
        return False

    substrate_window_start = insight.get('substrate_window_start')
    substrate_window_end = insight.get('substrate_window_end')

    if not substrate_window_start or not substrate_window_end:
        return False  # No window defined = always valid

    now = datetime.utcnow()

    # If we've moved significantly past the window, consider it drifted
    # "Significantly" = 1.5x the window duration past end
    if isinstance(substrate_window_start, str):
        substrate_window_start = datetime.fromisoformat(substrate_window_start.replace('Z', '+00:00'))
    if isinstance(substrate_window_end, str):
        substrate_window_end = datetime.fromisoformat(substrate_window_end.replace('Z', '+00:00'))

    window_duration = (substrate_window_end - substrate_window_start).total_seconds()
    drift_threshold = substrate_window_end.timestamp() + (window_duration * 0.5)

    return now.timestamp() > drift_threshold


def compute_substrate_diff(
    supabase: Client,
    basket_id: str,
    old_hash: str,
    new_hash: str
) -> Optional[Dict[str, Any]]:
    """
    Compute high-level summary of what changed in substrate (V3.0 compliant).

    Returns dict with:
    - blocks_accepted: int (ACCEPTED, LOCKED, CONSTANT states)
    - dumps_total: int
    - relationships_total: int

    V3.0 Changes:
    - context_items removed (merged into blocks)
    - Query blocks with ACCEPTED+ states only
    - substrate_relationships requires join through blocks

    (Note: Full diff would require storing substrate snapshot at old_hash time.
     This is a simplified version that shows current counts.)
    """
    if old_hash == new_hash:
        return None

    # For now, return high-level counts
    # Full implementation would store substrate snapshots keyed by hash

    blocks_count = supabase.table('blocks').select('id', count='exact').eq(
        'basket_id', basket_id
    ).in_('state', ['ACCEPTED', 'LOCKED', 'CONSTANT']).execute().count

    dumps_count = supabase.table('raw_dumps').select('id', count='exact').eq(
        'basket_id', basket_id
    ).execute().count

    # Get relationships: join through blocks
    blocks = supabase.table('blocks').select('id').eq('basket_id', basket_id).in_(
        'state', ['ACCEPTED', 'LOCKED', 'CONSTANT']
    ).execute()
    block_ids = [block['id'] for block in blocks.data] if blocks.data else []

    relationships_count = 0
    if block_ids:
        relationships_count = supabase.table('substrate_relationships').select('id', count='exact').in_(
            'from_block_id', block_ids
        ).in_('state', ['ACCEPTED', 'LOCKED', 'CONSTANT']).execute().count

    return {
        "blocks_accepted": blocks_count,
        "dumps_total": dumps_count,
        "relationships_total": relationships_count,
        "note": "Full delta requires substrate snapshots (future enhancement)"
    }


def should_regenerate_insight_canon(
    supabase: Client,
    basket_id: str
) -> Dict[str, Any]:
    """
    Context-driven staleness check for insight_canon (basket-level insight).

    Returns:
    {
        "stale": bool,
        "reasons": {
            "substrate_changed": bool,
            "graph_changed": bool,
            "temporal_drift": bool
        },
        "current_canon": {...} or None,
        "substrate_delta": {...} or None
    }
    """
    # Get current insight_canon for this basket
    result = supabase.table('reflections_artifact').select('*').eq(
        'basket_id', basket_id
    ).eq('insight_type', 'insight_canon').eq('is_current', True).limit(1).execute()

    if not result.data:
        return {
            "stale": True,
            "reasons": {"missing": True},
            "current_canon": None,
            "substrate_delta": None
        }

    current_canon = result.data[0]

    # Check 1: Substrate changed?
    current_substrate_hash = compute_basket_substrate_hash(supabase, basket_id)
    substrate_changed = current_substrate_hash != current_canon.get('substrate_hash')

    # Check 2: Relationship graph changed?
    current_graph_signature = compute_graph_signature(supabase, basket_id)
    graph_changed = current_graph_signature != current_canon.get('graph_signature')

    # Check 3: Temporal drift (should not apply to insight_canon, but check anyway)
    temporal_drift = check_temporal_scope_validity(current_canon)

    stale = substrate_changed or graph_changed or temporal_drift

    substrate_delta = None
    if substrate_changed:
        substrate_delta = compute_substrate_diff(
            supabase,
            basket_id,
            current_canon.get('substrate_hash', ''),
            current_substrate_hash
        )

    return {
        "stale": stale,
        "reasons": {
            "substrate_changed": substrate_changed,
            "graph_changed": graph_changed,
            "temporal_drift": temporal_drift
        },
        "current_canon": current_canon,
        "substrate_delta": substrate_delta,
        "current_substrate_hash": current_substrate_hash,
        "current_graph_signature": current_graph_signature
    }


def should_regenerate_document_canon(
    supabase: Client,
    basket_id: str
) -> Dict[str, Any]:
    """
    Context-driven staleness check for document_canon (Basket Context Canon).

    Document Canon is derived from P3 insights + substrate, so check:
    1. Has the insight_canon changed? (regenerated)
    2. Has substrate changed? (might need recomposition even if insight unchanged)

    Returns same structure as should_regenerate_insight_canon.
    """
    # Get current document_canon for this basket
    result = supabase.table('documents').select('*').eq(
        'basket_id', basket_id
    ).eq('doc_type', 'document_canon').limit(1).execute()

    if not result.data:
        return {
            "stale": True,
            "reasons": {"missing": True},
            "current_canon": None
        }

    current_doc_canon = result.data[0]
    derived_from = current_doc_canon.get('derived_from', {})

    # Check 1: Has insight_canon been regenerated since document was composed?
    insight_canon_result = supabase.table('reflections_artifact').select('id, created_at').eq(
        'basket_id', basket_id
    ).eq('insight_type', 'insight_canon').eq('is_current', True).limit(1).execute()

    insight_changed = False
    if insight_canon_result.data:
        insight_canon = insight_canon_result.data[0]
        # Check if insight was regenerated after document
        doc_created = datetime.fromisoformat(current_doc_canon['created_at'].replace('Z', '+00:00'))
        insight_created = datetime.fromisoformat(insight_canon['created_at'].replace('Z', '+00:00'))
        insight_changed = insight_created > doc_created

    # Check 2: Has substrate changed since document composition?
    # (Documents store composition_instructions which may include substrate filters)
    current_substrate_hash = compute_basket_substrate_hash(supabase, basket_id)
    substrate_changed = current_substrate_hash != derived_from.get('substrate_hash', '')

    stale = insight_changed or substrate_changed

    return {
        "stale": stale,
        "reasons": {
            "insight_canon_regenerated": insight_changed,
            "substrate_changed": substrate_changed
        },
        "current_canon": current_doc_canon,
        "current_substrate_hash": current_substrate_hash
    }


def get_basket_canons_health(
    supabase: Client,
    basket_id: str
) -> Dict[str, Any]:
    """
    Health check for required P3/P4 canons in a basket.

    Returns:
    {
        "basket_id": str,
        "has_insight_canon": bool,
        "has_document_canon": bool,
        "insight_canon_stale": bool,
        "document_canon_stale": bool,
        "ready": bool (all required canons exist and fresh)
    }
    """
    insight_check = should_regenerate_insight_canon(supabase, basket_id)
    doc_check = should_regenerate_document_canon(supabase, basket_id)

    has_insight = insight_check['current_canon'] is not None
    has_document = doc_check['current_canon'] is not None

    insight_stale = insight_check['stale']
    doc_stale = doc_check['stale']

    # Basket is "ready" if both canons exist and are fresh
    ready = has_insight and has_document and not insight_stale and not doc_stale

    return {
        "basket_id": basket_id,
        "has_insight_canon": has_insight,
        "has_document_canon": has_document,
        "insight_canon_stale": insight_stale,
        "document_canon_stale": doc_stale,
        "ready": ready,
        "insight_check": insight_check,
        "doc_check": doc_check
    }
