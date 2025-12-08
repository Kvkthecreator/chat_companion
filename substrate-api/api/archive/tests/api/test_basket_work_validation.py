import os
import sys
import types
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Set env vars and stub external deps before importing router
os.environ.setdefault("SUPABASE_URL", "http://stub.local")
os.environ.setdefault("SUPABASE_ANON_KEY", "stub-anon")
sys.modules["supabase"] = types.SimpleNamespace(create_client=lambda *a, **k: None, Client=object)
sys.modules["app.utils.jwt"] = types.SimpleNamespace(verify_jwt=lambda *_a, **_k: {"user_id": "u"})

from app.routes import baskets


def build_client(monkeypatch: types.SimpleNamespace) -> TestClient:
    monkeypatch.setattr(baskets, "get_or_create_workspace", lambda _u: "ws1")
    app = FastAPI()
    app.include_router(baskets.router)

    async def _get_db_override():
        return None

    app.dependency_overrides[baskets.get_db] = _get_db_override
    return TestClient(app)


def test_work_requires_sources(monkeypatch):
    client = build_client(monkeypatch)
    resp = client.post("/api/baskets/b1/work", json={"mode": "init_build", "sources": []})
    assert resp.status_code == 422


def test_invalid_json(monkeypatch):
    client = build_client(monkeypatch)
    resp = client.post(
        "/api/baskets/b1/work",
        content=b"not-json",
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code in (400, 422)
