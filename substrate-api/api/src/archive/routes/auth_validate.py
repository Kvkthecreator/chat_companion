from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from auth.jwt_verifier import verify_jwt
from auth.integration_tokens import verify_integration_token
from ..utils.workspace import get_or_create_workspace

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/validate")
async def validate_auth(request: Request):
    auth_header = request.headers.get("authorization") or ""
    token = auth_header.split(" ", 1)[1] if auth_header.lower().startswith("bearer ") else None
    if not token:
        raise HTTPException(status_code=401, detail="missing_token")

    try:
        claims = verify_jwt(token)
        user_id = claims.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="token_missing_subject")
        workspace_id = get_or_create_workspace(user_id)
        return {
            "valid": True,
            "token_type": "jwt",
            "user_id": user_id,
            "workspace_id": workspace_id,
        }
    except HTTPException:
        info = verify_integration_token(token)
        return {
            "valid": True,
            "token_type": "integration",
            "user_id": info["user_id"],
            "workspace_id": info["workspace_id"],
            "token_id": info["id"],
        }


__all__ = ["router"]
