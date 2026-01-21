import types
import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient

from infra.substrate.routes.basket_new import router as new_router

app = FastAPI()
app.include_router(new_router, prefix="/api")
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

            def eq(self, col: str, val):
                self._filters.append((col, val))
                return self

            def execute(self):
                data = store.setdefault(name, [])
                if self._op == "insert":
                    row = dict(self._values)
                    row.setdefault("id", str(uuid.uuid4()))
                    data.append(row)
                    return types.SimpleNamespace(data=[row], error=None)
                res = data
                for c, v in self._filters:
                    res = [r for r in res if r.get(c) == v]
                return types.SimpleNamespace(data=res, error=None)

        return Q()

    return types.SimpleNamespace(table=table)


def test_create_and_list(monkeypatch):
    user_id = "00000000-0000-0000-0000-000000000000"
    store = {
        "workspace_memberships": [{"workspace_id": "ws1", "user_id": user_id}],
        "baskets": [],
    }
    fake = _supabase(store)
    monkeypatch.setattr("app.routes.basket_new.supabase", fake)

    payload = {
        "idempotency_key": str(uuid.uuid4()),
        "basket": {},
    }

    resp = client.post("/api/baskets/new", json=payload)
    assert resp.status_code == 201
    bid = resp.json()["basket_id"]

    items = fake.table("baskets").select("*").eq("user_id", user_id).execute()
    assert len(items.data) == 1
    assert items.data[0]["id"] == bid


def test_auto_workspace(monkeypatch):
    store = {"workspace_memberships": [], "baskets": [], "workspaces": []}
    fake = _supabase(store)
    monkeypatch.setattr("app.routes.basket_new.supabase", fake)

    payload = {"idempotency_key": str(uuid.uuid4()), "basket": {}}
    resp = client.post("/api/baskets/new", json=payload)
    assert resp.status_code == 201
    assert store["workspaces"]

