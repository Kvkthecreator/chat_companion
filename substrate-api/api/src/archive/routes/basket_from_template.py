# V3.0 DEPRECATION NOTICE:
# This file contains references to context_items table which was merged into blocks table.
# Entity blocks are now identified by semantic_type='entity'.
# This file is legacy/supporting code - update if actively maintained.

# ruff: noqa
from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..agent_entrypoints import run_agent_direct
from ..templates import TEMPLATES
from ..utils.db import json_safe
from ..utils.jwt import verify_jwt
from ..utils.supabase_client import supabase_client as supabase
from ..utils.workspace import get_or_create_workspace

router = APIRouter(prefix="/baskets", tags=["baskets"])
log = logging.getLogger("uvicorn.error")


class TemplatePayload(BaseModel):
    template_id: str = Field(..., pattern="^.+$")
    files: list[str] = Field(...)
    guidelines: str | None = None


@router.post("/new-from-template")
async def create_from_template(payload: TemplatePayload, user: dict = Depends(verify_jwt)):
    if payload.template_id not in TEMPLATES:
        raise HTTPException(status_code=400, detail="unknown template_id")
    if len(payload.files) != 3:
        raise HTTPException(status_code=400, detail="exactly 3 files required")

    tpl = TEMPLATES[payload.template_id]
    ws = await get_or_create_workspace(user)
    workspace_id = ws.id
    basket_id = str(uuid.uuid4())

    try:
        supabase.table("baskets").insert(
            json_safe(
                {
                    "id": basket_id,
                    "workspace_id": workspace_id,
                    "user_id": user["user_id"],
                    "state": "INIT",
                    "origin_template": payload.template_id,
                }
            )
        ).execute()
    except Exception:
        log.exception("basket insert failed")
        raise HTTPException(status_code=500, detail="internal error")

    for idx, file_url in enumerate(payload.files):
        try:
            doc_resp = supabase.rpc('fn_document_create', {
                "p_basket_id": basket_id,
                "p_workspace_id": workspace_id,
                "p_title": tpl["doc_titles"][idx],
                "p_content_raw": "",
            }).execute()
            doc_id = doc_resp.data
            supabase.table("raw_dumps").insert(
                json_safe(
                    {
                        "id": str(uuid.uuid4()),
                        "document_id": doc_id,
                        "file_url": file_url,
                        "body_md": None,
                    }
                )
            ).execute()
        except Exception:
            log.exception("document/raw_dump insert failed")
            raise HTTPException(status_code=500, detail="internal error")

    seed = tpl.get("seed_block")
    if seed:
        try:
            supabase.rpc('fn_block_create', {
                "p_basket_id": basket_id,
                "p_workspace_id": workspace_id,
                "p_title": seed.get("text"),
                "p_body_md": seed.get("text"),
            }).execute()
        except Exception:
            log.exception("seed block insert failed")
            raise HTTPException(status_code=500, detail="internal error")

    if payload.guidelines and payload.guidelines.strip():
        try:
            supabase.table("context_items").insert(
                json_safe(
                    {
                        "basket_id": basket_id,
                        "type": "guideline",
                        "content": payload.guidelines,
                        "title": None,
                        "description": None,
                        "metadata": {"source": "template_guideline"},
                        "normalized_label": None,
                        "state": "ACTIVE",
                        "status": "active",
                    }
                )
            ).execute()
        except Exception:
            log.exception("context item insert failed")
            raise HTTPException(status_code=500, detail="internal error")

    try:
        await run_agent_direct(
            {
                "agent_type": "orch_block_manager_agent",
                "input": {"basket_id": str(basket_id)},
                "user_id": user["user_id"],
            }
        )
    except Exception:
        log.exception("orch_block_manager_agent invocation failed")

    return {"basket_id": basket_id}
