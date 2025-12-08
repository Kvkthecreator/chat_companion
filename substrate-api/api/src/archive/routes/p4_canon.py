"""
P4 Canon Generation Endpoints

Implements P4 document taxonomy:
- document_canon: Context Brief (mandatory, ONE per basket)
- starter_prompt: Prompt Starter Pack (reasoning capsules for external hosts)

Note: Separate from existing p4_composition.py which handles general document composition.
      This module focuses specifically on canon generation workflows.
"""
# V3.1 NOTICE:
# Substrate references use the unified blocks table (semantic_type + anchor_role).
# Entity/anchor metadata is derived from block fields; no context_items access remains.


import logging
from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Tuple, Iterable
from uuid import UUID
from datetime import datetime

from infra.utils.supabase import supabase_admin
from lib.freshness import (
    should_regenerate_document_canon,
    compute_basket_substrate_hash
)
from infra.utils.jwt import verify_jwt

router = APIRouter(prefix="/p4", tags=["p4-documents"])

logger = logging.getLogger("uvicorn.error")


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class GenerateDocumentCanonRequest(BaseModel):
    basket_id: str = Field(..., description="Target basket UUID")
    force: bool = Field(False, description="Force regeneration even if fresh")
    composition_mode: Optional[str] = Field(
        "comprehensive",
        description="Composition style: comprehensive, concise, narrative"
    )


class GenerateDocumentCanonResponse(BaseModel):
    document_id: str
    basket_id: str
    title: str
    version_hash: str
    is_fresh: bool
    previous_id: Optional[str]
    derived_from: Dict[str, Any]
    created_at: datetime


class GenerateStarterPromptRequest(BaseModel):
    basket_id: str
    target_host: str = Field(..., description="Target host: claude_ai, chatgpt, cursor, etc.")
    scope_filter: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional substrate filter for focused prompts"
    )
    prompt_style: Optional[str] = Field(
        "concise",
        description="Style: concise, detailed, creative"
    )


class GenerateStarterPromptResponse(BaseModel):
    document_id: str
    basket_id: str
    title: str
    target_host: str
    version_hash: str
    content_preview: str
    created_at: datetime


# =============================================================================
# DOCUMENT CANON ENDPOINTS
# =============================================================================

@router.post("/document-canon", response_model=GenerateDocumentCanonResponse)
async def generate_document_canon(
    request: GenerateDocumentCanonRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(verify_jwt)
):
    """
    Generate or regenerate document_canon (Context Brief).

    Direct operation (not governed per Canon v3.1).
    The Context Brief is the mandatory comprehensive view of basket state.

    Process:
    1. Check if basket has document_canon
    2. If exists and fresh (unless force), return existing
    3. Otherwise, compose new canon from P3 insight_canon + substrate
    4. Create new document_version
    5. Link via previous_id for version chain
    """
    supabase = supabase_admin()

    # Get basket details
    basket_result = supabase.table('baskets').select('workspace_id, name').eq('id', request.basket_id).single().execute()
    if not basket_result.data:
        raise HTTPException(status_code=404, detail="Basket not found")

    basket = basket_result.data
    workspace_id = basket['workspace_id']
    basket_name = basket.get('name', 'Untitled Basket')

    # Check staleness
    staleness_check = should_regenerate_document_canon(supabase, request.basket_id)

    if not staleness_check['stale'] and not request.force:
        current = staleness_check['current_canon']
        if current and current.get('title', '').endswith('Context Canon'):
            new_title = f"{basket_name} — Context Brief"
            supabase.table('documents').update({'title': new_title}).eq('id', current['id']).execute()
            current['title'] = new_title
        return GenerateDocumentCanonResponse(
            document_id=current['id'],
            basket_id=current['basket_id'],
            title=current['title'],
            version_hash=current['current_version_hash'],
            is_fresh=True,
            previous_id=current.get('previous_id'),
            derived_from=current.get('derived_from', {}),
            created_at=current['created_at']
        )

    # Get current insight_canon
    insight_canon_result = supabase.table('reflections_artifact').select('*').eq(
        'basket_id', request.basket_id
    ).eq('insight_type', 'insight_canon').eq('is_current', True).limit(1).execute()

    if not insight_canon_result.data:
        raise HTTPException(
            status_code=400,
            detail="Cannot generate document_canon without insight_canon. Generate insight_canon first."
        )

    insight_canon = insight_canon_result.data[0]

    # Fetch substrate
    substrate = await _fetch_basket_substrate_for_canon(supabase, request.basket_id)

    compose_result = await _compose_document_canon(
        basket_name=basket_name,
        insight_canon=insight_canon,
        substrate=substrate,
        composition_mode=request.composition_mode
    )

    fallback_mode = False
    if isinstance(compose_result, tuple) and len(compose_result) == 3:
        structured_outline = None
        canon_content = compose_result[1]
        version_hash = compose_result[2]
        fallback_mode = True
    else:
        structured_outline, canon_content = compose_result  # type: ignore[misc]
        import hashlib
        raw_hash = hashlib.sha256(canon_content.encode('utf-8')).hexdigest()
        version_hash = f"doc_v{raw_hash[:58]}"

    substrate_hash = compute_basket_substrate_hash(supabase, request.basket_id)

    generated_at = datetime.utcnow().isoformat()
    derived_from = {
        'insight_canon_id': insight_canon['id'],
        'substrate_hash': substrate_hash,
        'composition_mode': request.composition_mode,
        'generated_at': generated_at,
        'fallback': fallback_mode
    }

    existing_doc = supabase.table('documents').select('id, metadata').eq(
        'basket_id', request.basket_id
    ).eq('doc_type', 'document_canon').maybe_single().execute()

    metadata_update = {
        'composition_mode': request.composition_mode,
        'composition_status': 'completed',
        'composition_completed_at': generated_at,
        'structured_outline': structured_outline,
    }

    if existing_doc and existing_doc.data:
        document_id = existing_doc.data['id']
        base_metadata = existing_doc.data.get('metadata') or {}
        supabase.table('documents').update({
            'title': f"{basket_name} — Context Brief",
            'current_version_hash': version_hash,
            'derived_from': derived_from,
            'metadata': {**base_metadata, **metadata_update}
        }).eq('id', document_id).execute()
    else:
        insert_doc = supabase.table('documents').insert({
            'basket_id': request.basket_id,
            'workspace_id': workspace_id,
            'title': f"{basket_name} — Context Brief",
            'document_type': 'basket_context',
            'doc_type': 'document_canon',
            'current_version_hash': version_hash,
            'derived_from': derived_from,
            'composition_instructions': {
                'mode': request.composition_mode,
                'source': 'p4_canon_generator'
            },
            'metadata': metadata_update
        }).execute()

        if not insert_doc.data:
            raise HTTPException(status_code=500, detail="Failed to create document")

        document_id = insert_doc.data[0]['id']

    version_insert = supabase.table('document_versions').insert({
        'document_id': document_id,
        'version_hash': version_hash,
        'content': canon_content,
        'metadata_snapshot': {
            'insight_canon_id': insight_canon['id'],
            'substrate_hash': substrate_hash,
            'composition_mode': request.composition_mode,
            'structured_outline': structured_outline,
            'fallback_mode': fallback_mode,
        },
        'substrate_refs_snapshot': _build_substrate_refs(substrate),
        'version_trigger': 'substrate_update',
        'version_message': 'Generated from current insight_canon and substrate'
    }).execute()

    if not version_insert.data:
        raise HTTPException(status_code=500, detail="Failed to create document version")

    version_row = version_insert.data[0]

    _upsert_doc_insight_for_version(
        supabase,
        document_id=document_id,
        basket_id=request.basket_id,
        workspace_id=workspace_id,
        version_hash=version_hash,
        structured_outline=structured_outline,
        insight_canon_text=insight_canon.get('reflection_text', ''),
        document_title=f"{basket_name} — Context Brief"
    )

    return GenerateDocumentCanonResponse(
        document_id=document_id,
        basket_id=request.basket_id,
        title=f"{basket_name} — Context Brief",
        version_hash=version_hash,
        is_fresh=True,
        previous_id=None,
        derived_from=derived_from,
        created_at=version_row['created_at']
    )


# =============================================================================
# STARTER PROMPT ENDPOINTS
# =============================================================================

@router.post("/starter-prompt", response_model=GenerateStarterPromptResponse)
async def generate_starter_prompt(
    request: GenerateStarterPromptRequest,
    user: dict = Depends(verify_jwt)
):
    """
    Generate starter_prompt for external AI host.

    Starter prompts are reasoning capsules optimized for specific hosts:
    - claude_ai: Claude.ai chat interface
    - chatgpt: ChatGPT web/app
    - cursor: Cursor IDE
    - windsurf: Windsurf editor
    - etc.

    Each prompt captures basket context in a concise, actionable format.
    """
    supabase = supabase_admin()

    # Get basket details
    basket_result = supabase.table('baskets').select('workspace_id, name').eq('id', request.basket_id).single().execute()
    if not basket_result.data:
        raise HTTPException(status_code=404, detail="Basket not found")

    basket = basket_result.data
    workspace_id = basket['workspace_id']
    basket_name = basket.get('name', 'Untitled Basket')

    # Get insight_canon
    insight_canon_result = supabase.table('reflections_artifact').select('*').eq(
        'basket_id', request.basket_id
    ).eq('insight_type', 'insight_canon').eq('is_current', True).limit(1).execute()

    if not insight_canon_result.data:
        raise HTTPException(
            status_code=400,
            detail="Cannot generate starter_prompt without insight_canon."
        )

    insight_canon = insight_canon_result.data[0]

    # Fetch substrate (filtered if scope_filter provided)
    substrate = await _fetch_basket_substrate_filtered(
        supabase,
        request.basket_id,
        request.scope_filter
    )

    # Compose starter prompt
    structured_prompt, prompt_content = await _compose_starter_prompt(
        basket_name=basket_name,
        target_host=request.target_host,
        insight_canon=insight_canon,
        substrate=substrate,
        prompt_style=request.prompt_style
    )

    # Compute version hash
    import hashlib
    raw_hash = hashlib.sha256(prompt_content.encode()).hexdigest()
    version_hash = f"doc_v{raw_hash[:58]}"

    # Create starter_prompt document
    host_label = request.target_host.replace('_', ' ').title()

    new_doc = supabase.table('documents').insert({
        'basket_id': request.basket_id,
        'workspace_id': workspace_id,
        'title': f"{basket_name} — Prompt Starter Pack ({host_label})",
        'document_type': 'starter_prompt',
        'doc_type': 'starter_prompt',
        'current_version_hash': version_hash,
        'derived_from': {
            'insight_canon_id': insight_canon['id'],
            'target_host': request.target_host,
            'prompt_style': request.prompt_style
        },
        'composition_instructions': {
            'target_host': request.target_host,
            'style': request.prompt_style,
            'scope_filter': request.scope_filter
        },
        'metadata': {
            'structured_prompt': structured_prompt,
            'prompt_style': request.prompt_style,
            'target_host': request.target_host
        }
    }).execute()

    if not new_doc.data:
        raise HTTPException(status_code=500, detail="Failed to create starter prompt")

    document_id = new_doc.data[0]['id']

    # Create document_version
    version = supabase.table('document_versions').insert({
        'document_id': document_id,
        'version_hash': version_hash,
        'content': prompt_content,
        'metadata_snapshot': {
            'insight_canon_id': insight_canon['id'],
            'target_host': request.target_host,
            'style': request.prompt_style,
            'structured_prompt': structured_prompt
        },
        'substrate_refs_snapshot': _build_substrate_refs(substrate),
        'version_trigger': 'user_requested',
        'version_message': f'Generated for {host_label}'
    }).execute()

    if not version.data:
        raise HTTPException(status_code=500, detail="Failed to create prompt version")

    # Preview (first 200 chars)
    content_preview = prompt_content[:200] + "..." if len(prompt_content) > 200 else prompt_content

    return GenerateStarterPromptResponse(
        document_id=document_id,
        basket_id=request.basket_id,
        title=f"{basket_name} — Prompt Starter Pack ({host_label})",
        target_host=request.target_host,
        version_hash=version_hash,
        content_preview=content_preview,
        created_at=new_doc.data[0]['created_at']
    )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def _fetch_basket_substrate_for_canon(supabase, basket_id: str) -> Dict[str, Any]:
    """Fetch substrate snapshot for canon composition (V3-compliant)."""
    blocks = supabase.table('blocks').select(
        'id, title, content, semantic_type, anchor_role, state, scope, updated_at'
    ).eq('basket_id', basket_id).in_('state', ['ACCEPTED', 'LOCKED', 'CONSTANT']).order('updated_at', desc=True).execute()

    dumps = supabase.table('raw_dumps').select('id, created_at, body_md').eq('basket_id', basket_id).order('created_at', desc=True).limit(20).execute()

    events = supabase.table('timeline_events').select('id, ts, kind, preview').eq('basket_id', basket_id).order('ts', desc=True).limit(20).execute()

    return {
        'blocks': blocks.data or [],
        'dumps': dumps.data or [],
        'events': events.data or []
    }


async def _fetch_basket_substrate_filtered(
    supabase,
    basket_id: str,
    scope_filter: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Fetch substrate with optional filtering."""
    # TODO: Implement filtering logic based on scope_filter
    # For now, return all substrate
    return await _fetch_basket_substrate_for_canon(supabase, basket_id)


async def _compose_document_canon(
    basket_name: str,
    insight_canon: Dict[str, Any],
    substrate: Dict[str, Any],
    composition_mode: Optional[str]
) -> Tuple[Optional[Dict[str, Any]], str] | Tuple[None, str, str]:
    structured = await _compose_document_canon_structured(
        basket_name=basket_name,
        insight_canon=insight_canon,
        substrate=substrate,
        composition_mode=composition_mode
    )

    if structured:
        rendered = _render_document_canon(structured, basket_name, insight_canon)
        return structured, rendered

    fallback = _render_document_canon_fallback(basket_name, insight_canon, substrate)
    logger.warning("Document canon structured compose failed; using fallback content")

    import hashlib
    raw_hash = hashlib.sha256(fallback.encode('utf-8')).hexdigest()
    fallback_hash = f"doc_v{raw_hash[:58]}"
    return None, fallback, fallback_hash


async def _compose_document_canon_structured(
    basket_name: str,
    insight_canon: Dict[str, Any],
    substrate: Dict[str, Any],
    composition_mode: Optional[str]
) -> Optional[Dict[str, Any]]:
    from infra.substrate.services.llm import get_llm

    llm = get_llm()
    prompt = _build_document_canon_prompt(basket_name, insight_canon, substrate, composition_mode)
    response = await llm.get_json_response(
        prompt,
        max_tokens=2200,
        schema_name="p4_document_canon_v1"
    )

    if response.success and response.parsed:
        return response.parsed

    logger.warning(
        "Document canon structured compose failed; falling back (%s)",
        response.error,
    )
    return None


def _render_document_canon(structured: Dict[str, Any], basket_name: str, insight_canon: Dict[str, Any]) -> str:
    """Render a Context Brief with balanced sections and scan-friendly bullets."""

    def _trim_list(values: Iterable[str], limit: int) -> List[str]:
        return [v for v in values if v][:limit]

    lines: List[str] = [f"# {basket_name} — Context Brief", ""]

    summary = (structured.get("summary") or "").strip()
    if summary:
        lines.extend(["## Executive Snapshot", summary, ""])

    themes = _trim_list(structured.get("themes") or [], 5)
    if themes:
        lines.append("## Current Priorities")
        for theme in themes:
            lines.append(f"- {theme}")
        lines.append("")

    sections = structured.get("sections") or []
    for section in sections[:4]:
        title = section.get("title") or "Focus Area"
        narrative = (section.get("narrative") or "").strip()
        key_points = _trim_list(section.get("key_points") or [], 4)
        lines.append(f"## {title}")
        if narrative:
            lines.append(narrative)
        if key_points:
            lines.append("")
            for point in key_points:
                lines.append(f"- {point}")
        lines.append("")

    tensions = structured.get("tensions") or []
    if tensions:
        lines.append("## Risks & Tensions")
        for tension in tensions[:4]:
            description = tension.get("description") or "Unspecified tension"
            impact = tension.get("impact")
            lines.append(f"- **{description}**" + (f" — {impact}" if impact else ""))
        lines.append("")

    opportunities = structured.get("opportunities") or []
    if opportunities:
        lines.append("## Opportunities to Pursue")
        for opp in opportunities[:4]:
            desc = opp.get("description") or "Opportunity"
            benefit = opp.get("benefit")
            lines.append(f"- **{desc}**" + (f" — {benefit}" if benefit else ""))
        lines.append("")

    actions = structured.get("recommended_actions") or []
    if actions:
        lines.append("## Recommended Moves")
        for action in actions[:5]:
            desc = action.get("description") or "Action"
            urgency = action.get("urgency")
            owner = action.get("owner_hint")
            meta_bits: List[str] = []
            if urgency:
                meta_bits.append(f"urgency: {urgency}")
            if owner:
                meta_bits.append(f"owner: {owner}")
            suffix = f" ({'; '.join(meta_bits)})" if meta_bits else ""
            lines.append(f"- {desc}{suffix}")
        lines.append("")

    next_steps = _trim_list(structured.get("next_steps") or [], 4)
    if next_steps:
        lines.append("## Next Checkpoints")
        for step in next_steps:
            lines.append(f"- {step}")
        lines.append("")

    insight_reference = (insight_canon.get('reflection_text') or '').strip()
    if insight_reference:
        lines.append("## Reference: Insight Canon Highlights")
        lines.append(insight_reference)
        lines.append("")

    return "\n".join(lines).strip()


def _render_document_canon_fallback(
    basket_name: str,
    insight_canon: Dict[str, Any],
    substrate: Dict[str, Any]
) -> str:
    blocks = substrate.get('blocks', [])
    dumps = substrate.get('dumps', [])
    events = substrate.get('events', [])

    lines = [
        f"# {basket_name} — Context Brief",
        "",
        "## Executive Snapshot",
        insight_canon.get('reflection_text', 'No insight available').strip(),
        "",
        "## Substrate At-a-glance",
        f"- Accepted knowledge blocks: {len(blocks)}",
        f"- Raw captures in scope: {len(dumps)}",
        f"- Timeline events considered: {len(events)}",
        "",
        "This fallback summary is based on raw substrate counts because composition returned no narrative.",
    ]

    return "\n".join(lines)


def _build_document_canon_prompt(
    basket_name: str,
    insight_canon: Dict[str, Any],
    substrate: Dict[str, Any],
    composition_mode: Optional[str]
) -> str:
    blocks = substrate.get('blocks', [])
    dumps = substrate.get('dumps', [])
    events = substrate.get('events', [])

    anchor_counts = Counter(
        (block.get('anchor_role') or '').strip().lower()
        for block in blocks
        if block.get('anchor_role')
    )
    anchor_summary = ", ".join(
        f"{anchor}: {count}"
        for anchor, count in anchor_counts.most_common(6)
    ) or "(no anchors tagged)"

    semantic_counts = Counter(block.get('semantic_type', 'unknown') for block in blocks)
    semantic_summary = ", ".join(
        f"{semantic}: {count}"
        for semantic, count in semantic_counts.most_common(6)
    )

    block_snippets = []
    for block in blocks[:15]:
        title = block.get('title') or ''
        content = block.get('content') or ''
        snippet = title if title else content[:160]
        block_snippets.append(
            f"- ({block.get('id')}) [{block.get('semantic_type', 'unknown')}] {snippet.strip()}"
        )

    recent_events = []
    for event in (events or [])[:10]:
        preview = event.get('preview') or event.get('description') or ''
        recent_events.append(f"- {event.get('kind', 'event')}: {preview[:120]}")

    mode = composition_mode or 'comprehensive'

    prompt_parts = [
        "You are Yarnnn's Document Canon composer.",
        "Produce a Context Brief using the p4_document_canon_v1 schema.",
        "Every section must reflect the provided substrate. Do not invent new entities, numbers, or decisions.",
        "Keep paragraphs under roughly 160 words and lists under five items so the brief is easily scannable.",
        "",
        f"Basket: {basket_name}",
        "",
        "Current Insight Canon (foundation):",
        insight_canon.get('reflection_text', 'No insight available'),
        "",
        "Anchor usage (top):",
        anchor_summary,
        "",
        "Semantic distribution:",
        semantic_summary,
        "",
        "Representative blocks:",
        "\n".join(block_snippets) or "(no blocks)",
        "",
        "Recent timeline events:",
        "\n".join(recent_events) or "(no events)",
        "",
        f"Composition mode: {mode}",
        "",
        "Return JSON with keys: summary, themes, sections (title, narrative, key_points), tensions, opportunities, recommended_actions (description, urgency, owner_hint), next_steps.",
        "If information is missing, explicitly note the gap instead of fabricating content.",
    ]

    return "\n".join(prompt_parts)


def _upsert_doc_insight_for_version(
    supabase,
    *,
    document_id: str,
    basket_id: str,
    workspace_id: str,
    version_hash: str,
    structured_outline: Optional[Dict[str, Any]],
    insight_canon_text: str,
    document_title: str,
) -> None:
    if structured_outline:
        reflection_text = _render_doc_insight(structured_outline, document_title, insight_canon_text)
    else:
        reflection_text = _render_doc_insight_fallback(document_title, insight_canon_text)

    try:
        supabase.table('reflections_artifact').update({
            'is_current': False
        }).filter('meta->>document_id', 'eq', document_id).filter('insight_type', 'eq', 'doc_insight').execute()
    except Exception:
        logger.debug("No existing doc insights to retire for document %s", document_id)

    supabase.table('reflections_artifact').insert({
        'basket_id': basket_id,
        'workspace_id': workspace_id,
        'substrate_hash': f"doc_{version_hash}",
        'reflection_text': reflection_text,
        'insight_type': 'doc_insight',
        'is_current': True,
        'derived_from': [
            {
                'type': 'document_version',
                'document_id': document_id,
                'version_hash': version_hash,
            }
        ],
        'computation_timestamp': datetime.utcnow().isoformat(),
        'meta': {
            'document_id': document_id,
            'version_hash': version_hash,
            'structured_outline': structured_outline or {}
        }
    }).execute()


def _render_doc_insight(structured: Dict[str, Any], document_title: str, insight_canon_text: str) -> str:
    themes = structured.get('themes') or []
    tensions = structured.get('tensions') or []
    actions = structured.get('recommended_actions') or []

    lines = [
        f"Document Insight — {document_title}",
        "",
    ]

    summary = structured.get('summary')
    if summary:
        lines.append(summary.strip())
        lines.append("")

    if themes:
        lines.append("Key Themes:")
        for theme in themes[:5]:
            lines.append(f"- {theme}")
        lines.append("")

    if tensions:
        lines.append("Tensions / Risks:")
        for tension in tensions[:5]:
            desc = tension.get('description', 'Unspecified tension')
            impact = tension.get('impact')
            lines.append(f"- {desc}" + (f" — impact: {impact}" if impact else ""))
        lines.append("")

    if actions:
        lines.append("Recommended Actions:")
        for action in actions[:5]:
            desc = action.get('description', 'Action')
            urgency = action.get('urgency')
            lines.append(f"- {desc}" + (f" (urgency: {urgency})" if urgency else ""))
        lines.append("")

    lines.append("Alignment with Basket Insight:")
    lines.append(insight_canon_text[:400].strip())

    return "\n".join(lines).strip()


def _render_doc_insight_fallback(document_title: str, insight_canon_text: str) -> str:
    return (
        f"Document Insight — {document_title}\n\n"
        "Unable to compute structured insight. Review alongside the basket insight below:\n\n"
        f"{insight_canon_text[:400]}"
    )


async def _compose_starter_prompt_structured(
    basket_name: str,
    target_host: str,
    insight_canon: Dict[str, Any],
    substrate: Dict[str, Any],
    prompt_style: Optional[str]
) -> Optional[Dict[str, Any]]:
    from infra.substrate.services.llm import get_llm

    llm = get_llm()
    prompt = _build_starter_prompt_context(basket_name, target_host, insight_canon, substrate, prompt_style)
    response = await llm.get_json_response(
        prompt,
        max_tokens=900,
        schema_name="p4_prompt_starter_v1"
    )

    if response.success and response.parsed:
        return response.parsed

    logger.warning(
        "Starter prompt structured compose failed; falling back (%s)",
        response.error,
    )
    return None


def _render_starter_prompt(structured: Dict[str, Any], target_host: str) -> str:
    opening = (structured.get('opening') or '').strip()
    context = (structured.get('context') or '').strip()
    instructions = (structured.get('instructions') or '').strip()
    call_to_action = (structured.get('call_to_action') or '').strip()
    followups = structured.get('suggested_followups') or []

    lines: List[str] = []

    if opening:
        lines.append(opening)
    if context:
        lines.extend(["", "Context to share:", context])
    if instructions:
        lines.extend(["", "When responding, the assistant should:", instructions])
    if call_to_action:
        lines.extend(["", "Call to action:", call_to_action])
    followup_items = [item for item in followups if item][:5]
    if followup_items:
        lines.append("")
        lines.append("Suggested follow-up questions:")
        for item in followup_items:
            lines.append(f"- {item}")

    lines.append("")
    lines.append(f"(Designed for {target_host})")

    return "\n".join(line for line in lines if line).strip()


def _render_starter_prompt_fallback(
    basket_name: str,
    target_host: str,
    insight_canon: Dict[str, Any],
    substrate: Dict[str, Any]
) -> str:
    return "\n".join([
        f"Use this prompt with {target_host} for {basket_name}.",
        "",
        "Context to share:",
        (insight_canon.get('reflection_text') or 'No insight available').strip()[:500],
        "",
        "Guidance:",
        "1. Ground every response in the context above.",
        "2. Ask clarifying questions before making assumptions.",
        "3. Propose next actions with owners when possible.",
        "",
        f"Structured blocks available: {len(substrate.get('blocks', []))} | captures: {len(substrate.get('dumps', []))}",
    ]).strip()


def _build_starter_prompt_context(
    basket_name: str,
    target_host: str,
    insight_canon: Dict[str, Any],
    substrate: Dict[str, Any],
    prompt_style: Optional[str]
) -> str:
    blocks = substrate.get('blocks', [])
    top_blocks = []
    for block in blocks[:10]:
        semantic = block.get('semantic_type', 'unknown')
        title = block.get('title') or block.get('content', '')[:160]
        top_blocks.append(f"- [{semantic}] {title}")

    style = prompt_style or 'concise'

    return "\n".join([
        "You are generating a Yarnnn Starter Prompt for an external assistant.",
        f"Basket: {basket_name}",
        f"Target host: {target_host}",
        f"Desired style: {style}",
        "",
        "Insight Canon (core understanding):",
        insight_canon.get('reflection_text', 'No insight available'),
        "",
        "Key knowledge blocks:",
        "\n".join(top_blocks) or "(no accepted blocks)",
        "",
        "Return JSON fields: opening (<=2 sentences), context (paragraph <=140 words), instructions (numbered list guidance), call_to_action (clear ask), suggested_followups (<=5 short questions).",
        "All guidance must be actionable and grounded in the provided material. If information is missing, encourage the host to ask for it rather than inventing details.",
    ])
async def _compose_starter_prompt(
    basket_name: str,
    target_host: str,
    insight_canon: Dict[str, Any],
    substrate: Dict[str, Any],
    prompt_style: Optional[str]
) -> Tuple[Optional[Dict[str, Any]], str]:
    """Compose starter prompt for target host using structured LLM output."""
    structured = await _compose_starter_prompt_structured(
        basket_name=basket_name,
        target_host=target_host,
        insight_canon=insight_canon,
        substrate=substrate,
        prompt_style=prompt_style
    )

    if structured:
        return structured, _render_starter_prompt(structured, target_host)

    return None, _render_starter_prompt_fallback(basket_name, target_host, insight_canon, substrate)


def _build_substrate_refs(substrate: Dict[str, Any]) -> Dict[str, List[str]]:
    """Build substrate references snapshot."""
    return {
        'block_ids': [b['id'] for b in substrate.get('blocks', []) if b.get('id')],
        'dump_ids': [d['id'] for d in substrate.get('dumps', []) if d.get('id')],
        'event_ids': [e['id'] for e in substrate.get('events', []) if e.get('id')]
    }
