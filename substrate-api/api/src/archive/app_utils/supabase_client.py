"""Supabase client factory that builds a per-request client using user JWT."""

from __future__ import annotations

import os
from typing import Any

try:  # pragma: no cover - guard for slim supabase client builds
    from supabase import create_client, Client  # type: ignore
except ImportError:  # pragma: no cover - fallback for test environments
    from supabase import create_client  # type: ignore
    Client = Any  # type: ignore

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise RuntimeError("Supabase env vars missing")


def get_supabase(token: str) -> Client:
    """Create a new Supabase client scoped to the provided JWT."""
    client: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    client.postgrest.auth(token)
    return client


# Client for user operations (with anon key)
supabase_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Client for backend operations (with service role key)
supabase_admin_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY) if SUPABASE_SERVICE_ROLE_KEY else None


__all__ = ["get_supabase", "supabase_client", "supabase_admin_client"]
