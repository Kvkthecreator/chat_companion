import types
import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient

from infra.substrate.routes.basket_new import router as basket_new_router

app = FastAPI()
app.include_router(basket_new_router, prefix="/api")
client = TestClient(app)


def _supabase(store):
    def table(name: str):
        class Q:
            def __init__(self):
                self._filters = []
                self._op = None
                self._values = None
                self._single = False
                self._select = None

            def select(self, _cols="*"):
                if self._op is None:
                    self._op = "select"
                self._select = _cols
                return self

            def insert(self, row: dict):
                self._op = "insert"
                self._values = row
                return self

            def update(self, vals: dict):
                self._op = "update"
                self._values = vals
                return self

            def eq(self, col: str, val):
                self._filters.append((col, val))
                return self

            def single(self):
                self._single = True
                return self

            def execute(self):
                data = store.setdefault(name, [])
                if self._op == "insert":
                    row = dict(self._values)
                    row.setdefault("id", str(uuid.uuid4()))
                    data.append(row)
                    return types.SimpleNamespace(data=[row], error=None)
                if self._op == "update":
                    for r in data:
                        if all(r.get(c) == v for c, v in self._filters):
                            r.update(self._values)
                    return types.SimpleNamespace(data=[], error=None)
                # select
                res = data
                for c, v in self._filters:
                    res = [r for r in res if r.get(c) == v]
                if self._single:
                    return types.SimpleNamespace(data=res[0] if res else None, error=None)
                return types.SimpleNamespace(data=res, error=None)

        return Q()

    return types.SimpleNamespace(table=table)


def test_basket_new_replay(monkeypatch):
    store = {
        "workspace_memberships": [
            {"workspace_id": "ws1", "user_id": "00000000-0000-0000-0000-000000000000"}
        ],
        "baskets": [],
    }
    fake = _supabase(store)
    monkeypatch.setattr("app.routes.basket_new.supabase", fake)

    payload = {
        "idempotency_key": str(uuid.uuid4()),
        "basket": {"name": "Test"},
    }

    r1 = client.post("/api/baskets/new", json=payload)
    assert r1.status_code == 201
    bid = r1.json()["basket_id"]

    r2 = client.post("/api/baskets/new", json=payload)
    assert r2.status_code == 200
    assert r2.json()["basket_id"] == bid
    payload2 = {
        "idempotency_key": payload["idempotency_key"],
        "basket": {"name": "Test"},
    }
    r2 = client.post("/api/baskets/new", json=payload2)
    assert r2.status_code == 200
    assert r2.json()["basket_id"] == bid


def test_basket_new_creates_workspace(monkeypatch):
    store = {"workspace_memberships": [], "baskets": [], "workspaces": []}
    fake = _supabase(store)
    monkeypatch.setattr("app.routes.basket_new.supabase", fake)

    payload = {"idempotency_key": str(uuid.uuid4()), "basket": {}}
    resp = client.post("/api/baskets/new", json=payload)
    assert resp.status_code == 201
    assert store["workspaces"]
    assert store["workspace_memberships"]

