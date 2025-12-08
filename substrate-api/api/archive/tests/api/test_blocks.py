import types
import uuid
import sys
from fastapi import FastAPI
from fastapi.testclient import TestClient

import os
os.environ.setdefault("SUPABASE_URL", "http://localhost")

os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "svc.key")
sys.modules.setdefault("supabase", types.SimpleNamespace(create_client=lambda *a, **k: None))

from infra.substrate.routes.blocks import router as blocks_router, verify_jwt, get_or_create_workspace

app = FastAPI()
app.include_router(blocks_router, prefix="/api")
app.dependency_overrides[verify_jwt] = lambda: {"user_id": "00000000-0000-0000-0000-000000000000"}
app.dependency_overrides[get_or_create_workspace] = lambda: "ws1"
client = TestClient(app)


class Resp:
    def __init__(self, data=None, status_code=200, error=None):
        self.data = data
        self.status_code = status_code
        self.error = error

    def json(self):  # pragma: no cover - compatibility
        return self.data


def _fake_table(name, store):
    def update(data):
        q_filters = []

        def eq(col, val):
            q_filters.append((col, val))
            return query

        def execute():
            rows = store.get(name, [])
            updated = None
            for row in rows:
                if all(row.get(c) == v for c, v in q_filters):
                    row.update(data)
                    updated = row
                    break
            return Resp([updated] if updated else [])

        query = types.SimpleNamespace(eq=eq, execute=execute)
        return query

    def delete():
        q_filters = []

        def eq(col, val):
            q_filters.append((col, val))
            return query

        def execute():
            rows = store.get(name, [])
            store[name] = [r for r in rows if not all(r.get(c) == v for c, v in q_filters)]
            return Resp()

        query = types.SimpleNamespace(eq=eq, execute=execute)
        return query

    def select(cols="*"):
        q_filters = []
        single = False

        def eq(col, val):
            q_filters.append((col, val))
            return query

        def order(_c):
            return query

        def execute():
            rows = store.get(name, [])
            for c, v in q_filters:
                rows = [r for r in rows if r.get(c) == v]
            data = rows[0] if single else rows
            return Resp(data)

        query = types.SimpleNamespace(eq=eq, order=order, single=lambda: query, execute=execute)
        return query

    return types.SimpleNamespace(update=update, delete=delete, select=select)


def _fake_supabase(store):
    return types.SimpleNamespace(table=lambda n: _fake_table(n, store))


def test_block_update_delete(monkeypatch):
    store = {"blocks": [{"id": "b1", "workspace_id": "ws1", "basket_id": "bx", "content": "old", "metadata": {"knowledge_ingredients": {"goals": [], "constraints": [], "metrics": [], "entities": []}}}]}
    fake = _fake_supabase(store)
    monkeypatch.setattr("app.routes.blocks.supabase", fake)
    monkeypatch.setattr(
        "app.routes.blocks.verify_jwt",
        lambda *_a, **_k: {"user_id": "00000000-0000-0000-0000-000000000000"},
    )
    monkeypatch.setattr("app.routes.blocks.get_or_create_workspace", lambda *_a, **_k: "ws1")

    r = client.put("/api/blocks/b1", json={"content": "new"})
    assert r.status_code == 200
    assert store["blocks"][0]["content"] == "new"
    # Verify structured ingredients metadata is preserved
    assert "knowledge_ingredients" in store["blocks"][0]["metadata"]

    r = client.delete("/api/blocks/b1")
    assert r.status_code == 204
    assert store["blocks"] == []
