import datetime
import os

import httpx
from src.utils.db import json_safe

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
TOKEN_URL = "https://oauth2.googleapis.com/token"
DOCS_ENDPOINT = "https://docs.googleapis.com/v1/documents"
DRIVE_URL = "https://www.googleapis.com/drive/v3/files"


async def refresh_token(row, supabase):
    if row["token_expiry"] > datetime.datetime.utcnow() + datetime.timedelta(minutes=5):
        return row["access_token"]

    async with httpx.AsyncClient() as cli:
        r = await cli.post(
            TOKEN_URL,
            data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "refresh_token": row["refresh_token"],
                "grant_type": "refresh_token",
            },
        )
        tok = r.json()
        await (
            supabase.from_("user_integrations")
            .update(
                json_safe(
                    {
                        "access_token": tok["access_token"],
                        "token_expiry": datetime.datetime.utcnow()
                        + datetime.timedelta(seconds=int(tok["expires_in"])),
                    }
                )
            )
            .eq("id", row["id"])
        )
        return tok["access_token"]
