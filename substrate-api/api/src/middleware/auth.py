from __future__ import annotations

import os, sys, logging
from collections.abc import Iterable

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from auth.jwt_verifier import verify_jwt  # your verifier
from auth.integration_tokens import verify_integration_token

log = logging.getLogger("uvicorn.error")

# CORS origins for error responses (mirrors main.py config)
DEFAULT_CORS_ORIGINS = "http://localhost:3000,https://ep-0.com,https://www.ep-0.com,https://*.vercel.app"


def _add_cors_headers(response: JSONResponse, origin: str | None) -> JSONResponse:
    """Add CORS headers to error responses so browsers can read them."""
    if not origin:
        return response

    # Check against allowed origins
    cors_origins_env = os.getenv("CORS_ORIGINS", DEFAULT_CORS_ORIGINS)
    allowed_origins = [o.strip() for o in cors_origins_env.split(",")]

    # Check exact match or wildcard patterns
    origin_allowed = False
    for allowed in allowed_origins:
        if allowed == origin:
            origin_allowed = True
            break
        # Handle wildcard like https://*.vercel.app
        if "*" in allowed:
            import fnmatch
            if fnmatch.fnmatch(origin, allowed.replace("*", "*")):
                origin_allowed = True
                break

    if origin_allowed:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"

    return response


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        *,
        exempt_paths: Iterable[str] | None = None,
        exempt_prefixes: Iterable[str] | None = None,
    ):
        super().__init__(app)
        self.exempt_exact = set(exempt_paths or [])
        # Only *true* prefixes belong here; NEVER include "/"
        self.exempt_prefixes = set(exempt_prefixes or [])

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        # CORS preflight requests (OPTIONS) should always be allowed through
        # so that CORSMiddleware can handle them properly
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path or "/"
        dbg = request.headers.get("x-yarnnn-debug-auth") == "1"
        origin = request.headers.get("origin")

        # Check if path is exempt from auth requirement
        is_exempt = path in self.exempt_exact or any(
            path.startswith(p) for p in self.exempt_prefixes
        )

        # Extract token
        auth = request.headers.get("authorization") or ""
        token = auth.split(" ", 1)[1] if auth.lower().startswith("bearer ") else None

        # If no token and path is exempt, allow through without auth
        if not token:
            if is_exempt:
                return await call_next(request)
            if not dbg:
                log.debug("AuthMiddleware: missing bearer token for %s", path)
            return _add_cors_headers(
                JSONResponse(status_code=401, content={"error": "missing_token"}),
                origin
            )

        # Verify token (even for exempt paths, so endpoints can optionally use auth)
        try:
            claims = verify_jwt(token)
            request.state.user_id = claims.get("sub")
            request.state.jwt_payload = claims
            return await call_next(request)
        except HTTPException as jwt_error:
            try:
                info = verify_integration_token(token)
                request.state.user_id = info["user_id"]
                request.state.workspace_id = info["workspace_id"]
                request.state.integration_token_id = info["id"]
                request.state.integration_token = True
                return await call_next(request)
            except HTTPException as token_error:
                # If exempt path, allow through even with invalid token
                # (endpoint can decide if it needs auth)
                if is_exempt:
                    log.debug(
                        "AuthMiddleware: exempt path %s with invalid token, allowing through",
                        path,
                    )
                    return await call_next(request)
                if not dbg:
                    log.debug(
                        "AuthMiddleware: token verification failed for %s (jwt=%s; integration=%s)",
                        path,
                        jwt_error.detail,
                        token_error.detail,
                    )
                    return _add_cors_headers(
                        JSONResponse(
                            status_code=token_error.status_code,
                            content={"error": "invalid_token"},
                        ),
                        origin
                    )
                return _add_cors_headers(
                    JSONResponse(
                        status_code=token_error.status_code,
                        content={
                            "error": "invalid_token",
                            "detail": {
                                "jwt": jwt_error.detail,
                                "integration": token_error.detail,
                            },
                        },
                    ),
                    origin
                )


__all__ = ["AuthMiddleware"]
