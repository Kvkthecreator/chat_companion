"""Create baskets following the v1 interface spec."""

from __future__ import annotations

import json
import logging
import time
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..utils.jwt import verify_jwt
from ..utils.supabase import supabase_admin
from ..utils.workspace import get_or_create_workspace

router = APIRouter(prefix="/baskets", tags=["baskets"])
log = logging.getLogger("uvicorn.error")


class CreateBasketReq(BaseModel):
    idempotency_key: str
    basket: Optional[dict] = None

@router.post("/new", status_code=201)
async def create_basket(
    request: Request,
    payload: CreateBasketReq,
    user: Annotated[dict, Depends(verify_jwt)]
):
    """Create a basket with idempotency and workspace membership checks."""
    dbg = request.headers.get("x-yarnnn-debug-auth") == "1"
    
    try:
        start = time.time()

        workspace_id = get_or_create_workspace(user["user_id"])

        idempotency_key = payload.idempotency_key
        basket_payload = payload.basket or {}
        basket_name = basket_payload.get("name") or "Untitled Basket"

        # Check for replay using idempotency key
        sb = supabase_admin()
        existing = (
            sb.table("baskets")
            .select("id,name")
            .eq("user_id", user["user_id"])
            .eq("idempotency_key", idempotency_key)
            .execute()
        )
        if existing.data:
            basket_id = existing.data[0]["id"]
            name = existing.data[0].get("name")
            log.info(
                json.dumps(
                    {
                        "route": "/api/baskets/new",
                        "user_id": user["user_id"],
                        "idempotency_key": idempotency_key,
                        "action": "replayed",
                        "basket_id": basket_id,
                        "duration_ms": int((time.time() - start) * 1000),
                    }
                )
            )
            return JSONResponse({
                "basket_id": basket_id,
                "id": basket_id,
                "name": name,
            }, status_code=200)

        # Insert new basket with generated ID
        import uuid
        basket_id = str(uuid.uuid4())
        row = {
            "id": basket_id,
            "workspace_id": workspace_id,
            "user_id": user["user_id"],
            "name": basket_name,
            "idempotency_key": idempotency_key,
            "status": "INIT",
        }
        # Insert and return the created basket
        try:
            resp = sb.table("baskets").insert(row).execute()
        except Exception as e:
            log.error(f"Basket insert failed: {e}")
            raise

        if getattr(resp, "error", None):
            err = resp.error
            if getattr(err, "code", "") == "23505":
                log.info(
                    json.dumps(
                        {
                            "route": "/api/baskets/new",
                            "user_id": user["user_id"],
                            "idempotency_key": idempotency_key,
                            "action": "conflict",
                            "duration_ms": int((time.time() - start) * 1000),
                        }
                    )
                )
                raise HTTPException(status_code=409, detail="IDEMPOTENCY_CONFLICT")
            log.exception("basket insert failed: %s", err)
            raise HTTPException(status_code=500, detail="INTERNAL_ERROR")

        # ID was already generated above
        log.info(
            json.dumps(
                {
                    "route": "/api/baskets/new",
                    "user_id": user["user_id"],
                    "idempotency_key": idempotency_key,
                    "action": "created",
                    "basket_id": basket_id,
                    "duration_ms": int((time.time() - start) * 1000),
                }
            )
        )
        return JSONResponse({
            "basket_id": basket_id,
            "id": basket_id,
            "name": basket_name,
        }, status_code=201)
        
    except Exception as e:
        log.exception("basket_new failed")
        if dbg:
            return JSONResponse(status_code=500, content={"error":"internal_error", "detail": str(e)})
        return JSONResponse(status_code=500, content={"error": "Internal Server Error"})
