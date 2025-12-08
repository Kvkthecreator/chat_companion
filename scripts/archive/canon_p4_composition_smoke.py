#!/usr/bin/env python3
"""
Canon P4 Composition Smoke — Substrate equality

Creates:
  - new basket
  - one block + one context_item (substrate)
  - one document
  - attaches both substrates via substrate_references
Validates:
  - document_composition_stats shows both types as peers
"""

from __future__ import annotations

import os
import sys
import uuid
import logging
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api", "src"))
from app.utils.supabase_client import supabase_admin_client as supabase  # type: ignore

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
log = logging.getLogger('canon-p4-smoke')

WORKSPACE_ID = os.getenv('YARNNN_TEST_WORKSPACE_ID', '31ee30fe-6ae3-4604-ab6d-ac9b9f06dfde')


def create_basket() -> str:
    bid = str(uuid.uuid4())
    supabase.table('baskets').insert({
        'id': bid,
        'workspace_id': WORKSPACE_ID,
        'name': 'P4 Composition Smoke',
        'status': 'ACTIVE',
        'created_at': datetime.now(timezone.utc).isoformat(),
    }).execute()
    return bid


def seed_substrate(basket_id: str) -> tuple[str, str]:
    # Block
    blk_id = str(uuid.uuid4())
    supabase.table('blocks').insert({
        'id': blk_id,
        'basket_id': basket_id,
        'workspace_id': WORKSPACE_ID,
        'title': 'Beacon MTTR insight',
        'body_md': 'Reducing MTTR requires improved on-call runbooks.',
        'semantic_type': 'insight',
        'confidence_score': 0.85,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'metadata': {'source': 'p4_smoke'},
    }).execute()

    # Context item
    ci_id = str(uuid.uuid4())
    supabase.table('context_items').insert({
        'id': ci_id,
        'basket_id': basket_id,
        'type': 'entity',
        'content': 'PagerDuty',
        'metadata': {'source': 'p4_smoke'},
        'created_at': datetime.now(timezone.utc).isoformat(),
    }).execute()

    return blk_id, ci_id


def create_document(basket_id: str) -> str:
    doc_id = str(uuid.uuid4())
    supabase.table('documents').insert({
        'id': doc_id,
        'basket_id': basket_id,
        'title': 'Canon Composition Smoke',
        'content_raw': '# Smoke Doc\nDemonstrate substrate equality.',
        'content_rendered': None,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'updated_at': datetime.now(timezone.utc).isoformat(),
    }).execute()
    return doc_id


def attach(doc_id: str, substrate_type: str, substrate_id: str) -> None:
    # Prefer RPC helper if available; fall back to direct insert
    try:
        supabase.rpc('fn_document_attach_substrate', {
            'p_document_id': doc_id,
            'p_substrate_type': substrate_type,
            'p_substrate_id': substrate_id,
            'p_role': 'supporting',
            'p_weight': 0.7,
            'p_snippets': [],
            'p_metadata': {'source': 'p4_smoke'}
        }).execute()
        return
    except Exception:
        pass

    supabase.table('substrate_references').insert({
        'document_id': doc_id,
        'substrate_type': substrate_type,
        'substrate_id': substrate_id,
        'role': 'supporting',
        'weight': 0.7,
        'snippets': [],
        'metadata': {'source': 'p4_smoke'},
        'created_at': datetime.now(timezone.utc).isoformat(),
    }).execute()


def main() -> int:
    bid = create_basket()
    blk_id, ci_id = seed_substrate(bid)
    doc_id = create_document(bid)
    attach(doc_id, 'block', blk_id)
    attach(doc_id, 'context_item', ci_id)

    # Validate stats show both
    stats = (
        supabase.table('document_composition_stats')
        .select('*')
        .eq('document_id', doc_id)
        .single()
        .execute()
    )
    row = stats.data or {}
    blocks = int(row.get('blocks_count') or 0)
    items = int(row.get('context_items_count') or 0)
    ok = blocks >= 1 and items >= 1
    print('composition_ok:', ok)
    print('stats:', {'blocks': blocks, 'context_items': items})
    return 0 if ok else 2


if __name__ == '__main__':
    sys.exit(main())
