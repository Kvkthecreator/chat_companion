import os
import types
import uuid
from fastapi import FastAPI
from fastapi.testclient import TestClient

os.environ.setdefault("SUPABASE_URL", "http://localhost")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "svc.key")

from infra.substrate.routes.context_items import router as items_router

app = FastAPI()
app.include_router(items_router, prefix="/api")
client = TestClient(app)


class Resp:
    def __init__(self, data=None, status_code=200, error=None):
        self.data = data
        self.status_code = status_code
        self.error = error

    def json(self):  # pragma: no cover - compatibility
        return self.data


def _fake_table(name, store):
    def insert(record):
        record = {**record}
        record.setdefault("id", str(uuid.uuid4()))
        store.setdefault(name, []).append(record)
        return types.SimpleNamespace(execute=lambda: Resp([record]))

    def select(_cols="*"):
        q_filters = []
        single = False

        def eq(col, val):
            q_filters.append((col, val))
            return query

        def single_fn():
            nonlocal single
            single = True
            return query

        def execute():
            rows = store.get(name, [])
            for c, v in q_filters:
                rows = [r for r in rows if r.get(c) == v]
            data = rows[0] if single else rows
            return Resp(data)

        query = types.SimpleNamespace(eq=eq, single=single_fn, execute=execute)
        return query

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

    return types.SimpleNamespace(insert=insert, select=select, update=update, delete=delete)


def _fake_supabase(store):
    return types.SimpleNamespace(table=lambda n: _fake_table(n, store))


def test_context_crud(monkeypatch):
    store = {}
    fake = _fake_supabase(store)
    monkeypatch.setattr("app.routes.context_items.supabase", fake)
    monkeypatch.setattr("app.routes.context_items.verify_jwt", lambda *_a, **_k: {"user_id": "u"})
    monkeypatch.setattr(
        "app.routes.context_items.get_or_create_workspace",
        lambda *_a, **_k: types.SimpleNamespace(basket_id="b1"),
    )

    r = client.post("/api/context-items", json={"content": "Keep tone witty", "type": "guideline"})
    assert r.status_code == 200
    item_id = r.json()["id"]

    r = client.get("/api/context-items")
    assert any(i["id"] == item_id for i in r.json())

    r = client.put(f"/api/context-items/{item_id}", json={"content": "Keep tone witty & optimistic"})
    assert "optimistic" in r.json()["content"]

    r = client.delete(f"/api/context-items/{item_id}")
    assert r.status_code == 204
