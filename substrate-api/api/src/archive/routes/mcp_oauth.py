"""
MCP OAuth 2.0 Authorization Server

RFC 6749 compliant OAuth 2.0 implementation for MCP server integration.
Integrates with Supabase authentication for user identity.

Flow:
1. MCP server redirects to /auth/mcp/authorize
2. User authenticates with Supabase (existing session or new login)
3. User authorizes MCP client access
4. Backend generates authorization code (5-minute TTL)
5. MCP server exchanges code for access token at /auth/mcp/token
6. Access token stored in mcp_oauth_sessions (90-day TTL)
"""

from __future__ import annotations

import os
import secrets
from datetime import datetime, timezone, timedelta
from typing import Annotated, Optional
from urllib.parse import urlencode, parse_qs, urlparse
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel

from ..utils.jwt import verify_jwt
from ..utils.supabase import supabase_admin
from ..utils.workspace import get_or_create_workspace

router = APIRouter(prefix="/auth/mcp", tags=["mcp-oauth"])


# ------------------------------------------------------------------
# Authorization Code Storage (in-memory for simplicity, move to Redis for production)
# ------------------------------------------------------------------
# Structure: {code: {user_id, client_id, redirect_uri, expires_at, workspace_id}}
_auth_codes: dict[str, dict] = {}


def _cleanup_expired_codes():
    """Remove expired authorization codes"""
    now = datetime.now(timezone.utc)
    expired = [code for code, data in _auth_codes.items()
               if datetime.fromisoformat(data['expires_at']) < now]
    for code in expired:
        del _auth_codes[code]


# ------------------------------------------------------------------
# OAuth Client Registry (static clients + dynamic registration)
# ------------------------------------------------------------------
# Static clients (pre-configured, high-trust)
MCP_CLIENTS = {
    "yarnnn-mcp-anthropic": {
        "client_secret": None,  # Will be set from env var
        "redirect_uris": [
            "https://yarnnn-mcp-server.onrender.com/oauth/callback",
            "http://localhost:3000/oauth/callback",  # For local development
        ],
        "name": "YARNNN MCP Server (Claude)",
        "registration_type": "static",
    },
    "yarnnn-mcp-openai": {
        "client_secret": None,
        "redirect_uris": [
            "https://yarnnn-openai-apps.onrender.com/oauth/callback",
            "http://localhost:4000/oauth/callback",
        ],
        "name": "YARNNN MCP Server (OpenAI)",
        "registration_type": "static",
    },
}

# Dynamic clients (registered at runtime via /register endpoint)
# Structure: {client_id: {client_secret, redirect_uris, name, registration_type: "dynamic"}}
_dynamic_clients: dict[str, dict] = {}


def validate_client(client_id: str, client_secret: Optional[str] = None,
                   redirect_uri: Optional[str] = None) -> bool:
    """Validate OAuth client credentials (checks both static and dynamic clients)"""
    # Check static clients first
    client = MCP_CLIENTS.get(client_id)

    # Check dynamic clients if not found in static registry
    if not client:
        client = _dynamic_clients.get(client_id)

    if not client:
        return False

    # Validate client secret if provided (for confidential clients)
    if client_secret is not None and client["client_secret"] is not None:
        if client_secret != client["client_secret"]:
            return False

    # Validate redirect URI if provided
    if redirect_uri is not None:
        if redirect_uri not in client["redirect_uris"]:
            return False

    return True


# ------------------------------------------------------------------
# Authorization Endpoint (RFC 6749 Section 3.1)
# ------------------------------------------------------------------
@router.get("/authorize")
async def authorize(
    request: Request,
    client_id: str,
    redirect_uri: str,
    state: str,
    response_type: str = "code",
    scope: Optional[str] = None,
):
    """
    OAuth 2.0 Authorization Endpoint

    1. User must be authenticated (Supabase session)
    2. Validates client_id and redirect_uri
    3. Presents authorization consent screen
    4. On approval, generates authorization code
    5. Redirects back to client with code

    Query Parameters:
    - client_id: OAuth client identifier
    - redirect_uri: Where to redirect after authorization
    - state: CSRF protection token from client
    - response_type: Must be "code" (authorization code flow)
    - scope: Requested permissions (optional, defaults to full access)
    """
    # RFC 6749: Only authorization code flow supported
    if response_type != "code":
        return RedirectResponse(
            f"{redirect_uri}?error=unsupported_response_type&state={state}",
            status_code=302
        )

    # Validate client
    if not validate_client(client_id, redirect_uri=redirect_uri):
        return RedirectResponse(
            f"{redirect_uri}?error=invalid_client&state={state}",
            status_code=302
        )

    # Check if user is authenticated (has Supabase session cookie)
    auth_cookie = request.cookies.get("sb-access-token") or request.cookies.get("sb:token")

    if not auth_cookie:
        # User not logged in - redirect to Supabase auth
        # Store authorization request parameters to resume after login
        auth_request_id = str(uuid4())
        _auth_codes[f"pending_{auth_request_id}"] = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": scope or "mcp:full",
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
        }

        # Redirect to YARNNN web app login page with return URL
        # After login, user will be redirected back to resume OAuth authorization
        backend_url = os.getenv("BACKEND_URL", "https://api.yarnnn.com")
        frontend_url = os.getenv("FRONTEND_URL", "https://yarnnn.com")
        resume_url = f"{backend_url}/api/auth/mcp/authorize/resume?request_id={auth_request_id}"
        login_url = f"{frontend_url}/login?return_to={resume_url}"
        return RedirectResponse(login_url, status_code=302)

    # User is authenticated - verify JWT and show consent screen
    try:
        # Decode Supabase JWT to get user info
        from ..utils.jwt import decode_jwt
        user_payload = decode_jwt(auth_cookie)
        user_id = user_payload.get("sub")

        if not user_id:
            raise ValueError("Invalid user session")

        # Get workspace for user
        workspace_id = get_or_create_workspace(user_id)

        # Show authorization consent screen
        client_name = MCP_CLIENTS[client_id]["name"]
        consent_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Authorize {client_name}</title>
    <style>
        body {{
            font-family: system-ui, -apple-system, sans-serif;
            max-width: 500px;
            margin: 100px auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .card {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        h1 {{ font-size: 24px; margin-bottom: 10px; }}
        .client {{ color: #666; font-size: 14px; margin-bottom: 20px; }}
        .scope {{
            background: #f9f9f9;
            padding: 15px;
            border-radius: 4px;
            margin: 20px 0;
            font-size: 14px;
        }}
        .buttons {{
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }}
        button {{
            flex: 1;
            padding: 12px;
            border: none;
            border-radius: 4px;
            font-size: 14px;
            cursor: pointer;
            font-weight: 500;
        }}
        .approve {{
            background: #0070f3;
            color: white;
        }}
        .approve:hover {{
            background: #0060df;
        }}
        .deny {{
            background: #eee;
            color: #333;
        }}
        .deny:hover {{
            background: #ddd;
        }}
    </style>
</head>
<body>
    <div class="card">
        <h1>Authorize Access</h1>
        <p class="client"><strong>{client_name}</strong> wants to access your YARNNN workspace</p>

        <div class="scope">
            <strong>Permissions requested:</strong>
            <ul>
                <li>Create and read memory dumps</li>
                <li>Access substrate (building blocks)</li>
                <li>Manage baskets</li>
            </ul>
        </div>

        <form method="POST" action="/auth/mcp/authorize/approve">
            <input type="hidden" name="client_id" value="{client_id}">
            <input type="hidden" name="redirect_uri" value="{redirect_uri}">
            <input type="hidden" name="state" value="{state}">
            <input type="hidden" name="scope" value="{scope or 'mcp:full'}">
            <input type="hidden" name="user_id" value="{user_id}">
            <input type="hidden" name="workspace_id" value="{workspace_id}">

            <div class="buttons">
                <button type="submit" name="action" value="deny" class="deny">Deny</button>
                <button type="submit" name="action" value="approve" class="approve">Authorize</button>
            </div>
        </form>
    </div>
</body>
</html>
"""
        return HTMLResponse(content=consent_html)

    except Exception as e:
        # Invalid session - redirect to login
        return RedirectResponse(f"/login?error=session_expired", status_code=302)


@router.post("/authorize/approve")
async def approve_authorization(
    action: str = Form(...),
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    state: str = Form(...),
    scope: str = Form(...),
    user_id: str = Form(...),
    workspace_id: str = Form(...),
):
    """
    Process authorization approval/denial

    Called from consent screen form submission.
    """
    # User denied authorization
    if action == "deny":
        return RedirectResponse(
            f"{redirect_uri}?error=access_denied&state={state}",
            status_code=302
        )

    # User approved - generate authorization code
    _cleanup_expired_codes()

    # Generate cryptographically secure authorization code
    auth_code = secrets.token_urlsafe(32)

    # Store authorization code with 5-minute expiration (RFC 6749 recommendation)
    _auth_codes[auth_code] = {
        "user_id": user_id,
        "workspace_id": workspace_id,
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
    }

    # RFC 6749: Redirect back to client with authorization code
    callback_params = {
        "code": auth_code,
        "state": state,
    }
    callback_url = f"{redirect_uri}?{urlencode(callback_params)}"

    return RedirectResponse(callback_url, status_code=302)


@router.get("/authorize/resume")
async def resume_authorization(request: Request, request_id: str):
    """
    Resume authorization after user login

    Called after user successfully authenticates via /login redirect.
    """
    # Retrieve pending authorization request
    pending_key = f"pending_{request_id}"
    pending = _auth_codes.get(pending_key)

    if not pending:
        return HTMLResponse(
            "<h1>Authorization request expired</h1><p>Please try connecting again.</p>",
            status_code=400
        )

    # Check expiration
    if datetime.fromisoformat(pending["expires_at"]) < datetime.now(timezone.utc):
        del _auth_codes[pending_key]
        return HTMLResponse(
            "<h1>Authorization request expired</h1><p>Please try connecting again.</p>",
            status_code=400
        )

    # Remove from pending
    del _auth_codes[pending_key]

    # Redirect back to authorization endpoint (now with authenticated session)
    return RedirectResponse(
        f"/auth/mcp/authorize?client_id={pending['client_id']}&redirect_uri={pending['redirect_uri']}&state={pending['state']}&response_type=code&scope={pending['scope']}",
        status_code=302
    )


# ------------------------------------------------------------------
# Token Endpoint (RFC 6749 Section 3.2)
# ------------------------------------------------------------------
@router.post("/token")
async def token_exchange(
    grant_type: str = Form(...),
    code: Optional[str] = Form(None),
    redirect_uri: Optional[str] = Form(None),
    client_id: Optional[str] = Form(None),
    client_secret: Optional[str] = Form(None),
):
    """
    OAuth 2.0 Token Endpoint

    Exchange authorization code for access token.

    RFC 6749 Section 4.1.3: Authorization Code Grant

    Request Parameters (application/x-www-form-urlencoded):
    - grant_type: Must be "authorization_code"
    - code: Authorization code from /authorize
    - redirect_uri: Must match the redirect_uri from /authorize
    - client_id: OAuth client identifier
    - client_secret: Client secret (optional for public clients)

    Response (application/json):
    {
        "access_token": "<token>",
        "token_type": "Bearer",
        "expires_in": 7776000,  // 90 days in seconds
        "scope": "mcp:full"
    }
    """
    # RFC 6749: Only authorization code grant supported
    if grant_type != "authorization_code":
        raise HTTPException(
            status_code=400,
            detail={
                "error": "unsupported_grant_type",
                "error_description": "Only 'authorization_code' grant type is supported"
            }
        )

    if not code or not redirect_uri or not client_id:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_request",
                "error_description": "Missing required parameters: code, redirect_uri, client_id"
            }
        )

    # Validate client credentials
    if not validate_client(client_id, client_secret, redirect_uri):
        raise HTTPException(
            status_code=401,
            detail={
                "error": "invalid_client",
                "error_description": "Invalid client credentials or redirect_uri"
            }
        )

    # Retrieve authorization code
    _cleanup_expired_codes()
    auth_data = _auth_codes.get(code)

    if not auth_data:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_grant",
                "error_description": "Invalid or expired authorization code"
            }
        )

    # Validate authorization code matches request
    if auth_data["client_id"] != client_id or auth_data["redirect_uri"] != redirect_uri:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_grant",
                "error_description": "Authorization code does not match request parameters"
            }
        )

    # Check expiration
    if datetime.fromisoformat(auth_data["expires_at"]) < datetime.now(timezone.utc):
        del _auth_codes[code]
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_grant",
                "error_description": "Authorization code expired"
            }
        )

    # Code is single-use - delete immediately (RFC 6749 Section 4.1.2)
    del _auth_codes[code]

    # Generate access token (cryptographically secure)
    access_token = secrets.token_urlsafe(48)

    # Get Supabase JWT for the user (create new long-lived session)
    # In production, this should be a service role action
    # For now, we'll create a placeholder token that will be validated against mcp_oauth_sessions
    sb = supabase_admin()

    # For security, we generate a new Supabase session instead of reusing
    # This ensures MCP access is separate from web session
    # Note: In production, use Supabase Admin API to create custom JWT
    supabase_token = f"supabase_session_{secrets.token_urlsafe(32)}"

    # Store session mapping in database
    session_id = str(uuid4())
    expires_at = (datetime.now(timezone.utc) + timedelta(days=90)).isoformat()

    sb.table("mcp_oauth_sessions").insert({
        "id": session_id,
        "mcp_token": access_token,
        "supabase_token": supabase_token,
        "user_id": auth_data["user_id"],
        "workspace_id": auth_data["workspace_id"],
        "expires_at": expires_at,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_used_at": datetime.now(timezone.utc).isoformat(),
    }).execute()

    # RFC 6749 Section 5.1: Successful Response
    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 90 * 24 * 60 * 60,  # 90 days in seconds
        "scope": auth_data["scope"],
    }


# ------------------------------------------------------------------
# Introspection Endpoint (RFC 7662) - Optional
# ------------------------------------------------------------------
@router.post("/introspect")
async def introspect_token(
    token: str = Form(...),
    client_id: str = Form(...),
    client_secret: Optional[str] = Form(None),
):
    """
    OAuth 2.0 Token Introspection (RFC 7662)

    Allows clients to check token validity and metadata.
    """
    # Validate client
    if not validate_client(client_id, client_secret):
        raise HTTPException(status_code=401, detail="Invalid client credentials")

    # Look up token in database
    sb = supabase_admin()
    resp = sb.table("mcp_oauth_sessions").select("*").eq("mcp_token", token).limit(1).execute()

    if not resp.data:
        # RFC 7662: Return inactive for invalid tokens
        return {"active": False}

    session = resp.data[0]
    expires_at = datetime.fromisoformat(session["expires_at"].replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)

    if now > expires_at:
        return {"active": False}

    # RFC 7662: Active token response
    return {
        "active": True,
        "scope": "mcp:full",
        "client_id": client_id,
        "username": session["user_id"],
        "token_type": "Bearer",
        "exp": int(expires_at.timestamp()),
        "iat": int(datetime.fromisoformat(session["created_at"].replace("Z", "+00:00")).timestamp()),
        "sub": session["user_id"],
        "workspace_id": session["workspace_id"],
    }


# ------------------------------------------------------------------
# Dynamic Client Registration (RFC 7591)
# ------------------------------------------------------------------
class ClientRegistrationRequest(BaseModel):
    """RFC 7591 Dynamic Client Registration Request"""
    redirect_uris: list[str]
    client_name: Optional[str] = None
    client_secret: Optional[str] = None  # Clients can suggest a secret (usually null for public clients)
    token_endpoint_auth_method: Optional[str] = "none"  # Default to public client
    grant_types: Optional[list[str]] = ["authorization_code"]
    response_types: Optional[list[str]] = ["code"]
    scope: Optional[str] = "mcp:full"


class ClientRegistrationResponse(BaseModel):
    """RFC 7591 Dynamic Client Registration Response"""
    client_id: str
    client_secret: Optional[str] = None
    client_name: str
    redirect_uris: list[str]
    grant_types: list[str]
    response_types: list[str]
    token_endpoint_auth_method: str
    registration_client_uri: Optional[str] = None
    registration_access_token: Optional[str] = None

    class Config:
        # Exclude None values from JSON response (RFC 7591 compliant)
        exclude_none = True


@router.post("/register", response_model=ClientRegistrationResponse, response_model_exclude_none=True)
async def register_client(request: ClientRegistrationRequest):
    """
    RFC 7591 Dynamic Client Registration Endpoint

    Allows MCP clients (like MCP Inspector, future integrations) to register
    themselves at runtime instead of requiring pre-configuration.

    This makes the YARNNN MCP OAuth server universally compatible with any
    MCP client that supports dynamic registration.

    Request Body:
    - redirect_uris: List of allowed redirect URIs
    - client_name: Human-readable client name (optional)
    - token_endpoint_auth_method: "none" for public clients, "client_secret_post" for confidential
    - grant_types: OAuth grant types (defaults to ["authorization_code"])
    - response_types: OAuth response types (defaults to ["code"])

    Response:
    - client_id: Generated unique client identifier
    - client_secret: Generated secret (only for confidential clients, null for public)
    - Other metadata echoing the request
    """
    # Generate unique client_id
    client_id = f"dynamic-{secrets.token_urlsafe(16)}"

    # Generate client_secret for confidential clients
    client_secret = None
    if request.token_endpoint_auth_method in ["client_secret_post", "client_secret_basic"]:
        client_secret = secrets.token_urlsafe(32)

    # Store dynamic client
    _dynamic_clients[client_id] = {
        "client_secret": client_secret,
        "redirect_uris": request.redirect_uris,
        "name": request.client_name or f"Dynamic Client {client_id[:8]}",
        "registration_type": "dynamic",
        "token_endpoint_auth_method": request.token_endpoint_auth_method,
        "grant_types": request.grant_types,
        "response_types": request.response_types,
        "registered_at": datetime.now(timezone.utc).isoformat(),
    }

    # RFC 7591 compliant response
    return ClientRegistrationResponse(
        client_id=client_id,
        client_secret=client_secret,
        client_name=request.client_name or f"Dynamic Client {client_id[:8]}",
        redirect_uris=request.redirect_uris,
        grant_types=request.grant_types or ["authorization_code"],
        response_types=request.response_types or ["code"],
        token_endpoint_auth_method=request.token_endpoint_auth_method or "none",
    )


__all__ = ["router"]
