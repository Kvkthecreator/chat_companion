import os
import logging
from typing import Any

try:  # pragma: no cover - tolerate minimal supabase builds in tests
    from supabase import create_client, Client  # type: ignore
except ImportError:  # pragma: no cover
    from supabase import create_client  # type: ignore
    Client = Any  # type: ignore

log = logging.getLogger("uvicorn.error")

SUPABASE_URL = os.environ["SUPABASE_URL"]
ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

def supabase_admin() -> Client:
    if not SERVICE_ROLE_KEY:
        log.error("SUPABASE_SERVICE_ROLE_KEY missing")
        raise RuntimeError("supabase_admin_misconfigured")
    log.info("SB: admin client init (url=%s)", SUPABASE_URL)
    return create_client(SUPABASE_URL, SERVICE_ROLE_KEY)

def supabase_user(access_token: str) -> Client:
    if not ANON_KEY:
        log.error("SUPABASE_ANON_KEY missing")
        raise RuntimeError("supabase_user_misconfigured")
    client = create_client(SUPABASE_URL, ANON_KEY)
    client.postgrest.auth(access_token)
    return client