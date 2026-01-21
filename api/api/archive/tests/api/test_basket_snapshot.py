import os
import types

from fastapi import FastAPI
from fastapi.testclient import TestClient

os.environ.setdefault("SUPABASE_URL", "http://localhost")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "svc.key")

from infra.substrate.routes.basket_snapshot import router as snapshot_router

app = FastAPI()
app.include_router(snapshot_router, prefix="/api")
client = TestClient(app)


def _fake_table(name, store):
    def select(*args, **kwargs):
        class Q:
            def eq(self, *a, **k):
                return self

            def order(self, *a, **k):
                return self

            def in_(self, *a, **k):
                return self

            def execute(self):
                return types.SimpleNamespace(data=store.get(name, []))

        return Q()

    return types.SimpleNamespace(select=select)


def test_snapshot_empty(monkeypatch):
    store = {"raw_dumps": [], "blocks": []}
    fake = types.SimpleNamespace(table=lambda n: _fake_table(n, store))
    monkeypatch.setattr("app.routes.basket_snapshot.supabase", fake)
    res = client.get("/api/baskets/b1/snapshot")
    assert res.status_code == 200
    assert res.json() == {
        "raw_dump": "",
        "accepted_blocks": [],
        "locked_blocks": [],
        "constants": [],
        "proposed_blocks": [],
    }


def test_snapshot_filters(monkeypatch):
    store = {
        "raw_dumps": [{"id": "r1", "body_md": "d", "created_at": "t"}],
        "blocks": [
            {"id": "b1", "state": "ACCEPTED"},
            {"id": "b2", "state": "PROPOSED"},
            {"id": "b3", "state": "LOCKED"},
        ],
    }
    fake = types.SimpleNamespace(table=lambda n: _fake_table(n, store))
    monkeypatch.setattr("app.routes.basket_snapshot.supabase", fake)
    res = client.get("/api/baskets/b2/snapshot")
    assert res.status_code == 200
    body = res.json()
    assert body["raw_dump"] == "d"
    assert len(body["accepted_blocks"]) == 1
    assert len(body["locked_blocks"]) == 1
    assert len(body["proposed_blocks"]) == 1
