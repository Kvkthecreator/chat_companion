import os
import types
from fastapi import FastAPI
from fastapi.testclient import TestClient

os.environ.setdefault("SUPABASE_URL", "http://localhost")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "svc.key")

from infra.substrate.routes.baskets import router as baskets_router

app = FastAPI()
app.include_router(baskets_router, prefix="/api")
client = TestClient(app)


def _fake_table(name, store):
    def select(*args, **kwargs):
        class Q:
            def __init__(self):
                self._filter = None
                self._order = None

            def eq(self, col, val):
                self._filter = (col, val)
                return self

            def order(self, col, desc=None):
                self._order = (col, desc)
                return self

            def execute(self):
                data = store.get(name, [])
                if self._filter:
                    col, val = self._filter
                    data = [r for r in data if r.get(col) == val]
                if self._order:
                    col, direction = self._order
                    rev = direction == "desc"
                    data = sorted(data, key=lambda x: x.get(col), reverse=rev)
                return types.SimpleNamespace(data=data)

        return Q()

    return types.SimpleNamespace(select=select)


def _fake_supabase(store):
    return types.SimpleNamespace(table=lambda n: _fake_table(n, store))


def test_list_baskets(monkeypatch):
    store = {
        "baskets": [
            {
                "id": "b1",
                "name": "B1",
                "raw_dump_id": "d1",
                "created_at": "t1",
                "workspace_id": "ws",
            },
            {
                "id": "b2",
                "name": "B2",
                "raw_dump_id": "d2",
                "created_at": "t2",
                "workspace_id": "ws",
            },
        ],
        "raw_dumps": [
            {"id": "d1", "body_md": "d1 body"},
            {"id": "d2", "body_md": "d2 body"},
        ],
    }

    fake = _fake_supabase(store)
    monkeypatch.setattr("app.routes.baskets.supabase", fake)
    monkeypatch.setattr("app.routes.baskets.get_or_create_workspace", lambda _u: "ws")
    monkeypatch.setattr("app.routes.baskets.verify_jwt", lambda *_a, **_k: {"user_id": "u"})

    resp = client.get("/api/baskets/list")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2
    assert body[0]["id"] == "b2"
    assert body[0]["raw_dump_body"] == "d2 body"
