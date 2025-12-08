"""Supabase client wrapper for legacy modules using anon key."""

from __future__ import annotations

import os
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise RuntimeError("Supabase env vars missing")

supabase_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

__all__ = ["supabase_client"]
