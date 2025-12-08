from __future__ import annotations
# ruff: noqa
import json
import logging
import uuid
from pathlib import Path

from fastapi import HTTPException

from ..utils.db import json_safe

log = logging.getLogger("uvicorn.error")

# Root folder containing built-in basket templates
TEMPLATE_ROOT = Path(__file__).resolve().parents[3] / "templates"


def clone_template(template_slug: str, user_id: str, workspace_id: str, supabase) -> str:
    """Clone a starter basket template and return the new basket_id."""

    tpl_dir = TEMPLATE_ROOT / template_slug
    if not tpl_dir.is_dir():
        raise HTTPException(status_code=400, detail="unknown template_slug")

    try:
        basket_json = json.loads((tpl_dir / "basket.json").read_text())
        blocks_json = json.loads((tpl_dir / "blocks.json").read_text())
        docs_dir = tpl_dir / "docs"
        docs = []
        if docs_dir.is_dir():
            for md_file in docs_dir.glob("*.md"):
                docs.append({"title": md_file.stem, "content_raw": md_file.read_text()})
    except FileNotFoundError as exc:  # pragma: no cover - misconfigured template
        log.error("template files missing: %s", exc)
        raise HTTPException(status_code=500, detail="template files missing") from exc
    except Exception as exc:  # pragma: no cover
        log.exception("failed to load template")
        raise HTTPException(status_code=500, detail="template load failed") from exc

    basket_id = str(uuid.uuid4())

    supabase.table("baskets").insert(
        json_safe(
            {
                **basket_json,
                "id": basket_id,
                "user_id": user_id,
                "workspace_id": workspace_id,
                "origin_template": template_slug,
                "mode": basket_json.get("mode", "default"),
            }
        )
    ).execute()

    for blk in blocks_json:
        supabase.rpc('fn_block_create', {
            "p_basket_id": basket_id,
            "p_workspace_id": workspace_id,
            "p_title": blk.get("title"),
            "p_body_md": blk.get("content"),
        }).execute()

    for doc in docs:
        supabase.rpc('fn_document_create', {
            "p_basket_id": basket_id,
            "p_workspace_id": workspace_id,
            "p_title": doc["title"],
            "p_content_raw": doc["content_raw"],
        }).execute()

    # TODO: queue docs->blockifier importer in follow-up task

    return basket_id
