# ruff: noqa
import os
import types
import pytest

pytest.skip("requires full dependency stack", allow_module_level=True)

from fastapi import FastAPI
from fastapi.testclient import TestClient

os.environ.setdefault("SUPABASE_URL", "http://localhost")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "svc.key")

from infra.substrate.routes.basket_from_template import router as tpl_router

app = FastAPI()
app.include_router(tpl_router, prefix="/api")
client = TestClient(app)


class Resp:
    def __init__(self, data=None, status_code=201, error=None):
        self.data = [data] if data else []
        self.status_code = status_code
        self.error = error

    def json(self):  # pragma: no cover - compat
        return self.data


def _fake_table(name, store):
    def insert(rec):
        store.setdefault(name, []).append(rec)
        return types.SimpleNamespace(execute=lambda: Resp(rec))

    return types.SimpleNamespace(insert=insert)


def _fake_supabase(store):
    return types.SimpleNamespace(table=lambda n: _fake_table(n, store))


async def _noop(*_a, **_k):
    return None


def test_create_from_template(monkeypatch):
    store = {}
    fake = _fake_supabase(store)
    monkeypatch.setattr("app.routes.basket_from_template.supabase", fake)
    monkeypatch.setattr("app.routes.basket_from_template.verify_jwt", lambda *_a, **_k: {"user_id": "u"})
    async def _ws(_u):
        return types.SimpleNamespace(id="ws")

    monkeypatch.setattr("app.routes.basket_from_template.get_or_create_workspace", _ws)
    monkeypatch.setattr("app.routes.basket_from_template.run_agent_direct", _noop)

    payload = {
        "template_id": "multi_doc_consistency",
        "files": ["f1", "f2", "f3"],
        "guidelines": "Keep tone witty & optimistic",
    }

    resp = client.post("/api/baskets/new-from-template", json=payload)
    assert resp.status_code == 200
    bid = resp.json()["basket_id"]
    assert bid
    assert len(store.get("baskets", [])) == 1
    assert len(store.get("documents", [])) == 3
    assert len(store.get("raw_dumps", [])) == 3
    assert all(rd.get("document_id") for rd in store["raw_dumps"])
    assert all(rd["file_url"] == f"f{i+1}" for i, rd in enumerate(store["raw_dumps"]))
    assert store["blocks"][0]["text"] == "{{BRAND_NAME}}"
    assert store["context_items"][0]["content"] == payload["guidelines"]


def test_reject_wrong_file_count(monkeypatch):
    store = {}
    fake = _fake_supabase(store)
    monkeypatch.setattr("app.routes.basket_from_template.supabase", fake)
    monkeypatch.setattr("app.routes.basket_from_template.verify_jwt", lambda *_a, **_k: {"user_id": "u"})
    async def _ws(_u):
        return types.SimpleNamespace(id="ws")

    monkeypatch.setattr("app.routes.basket_from_template.get_or_create_workspace", _ws)
    monkeypatch.setattr("app.routes.basket_from_template.run_agent_direct", _noop)

    payload = {
        "template_id": "multi_doc_consistency",
        "files": ["f1", "f2"],
    }
    resp = client.post("/api/baskets/new-from-template", json=payload)
    assert resp.status_code == 400

