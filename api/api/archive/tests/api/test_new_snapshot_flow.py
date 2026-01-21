import types
import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient

from infra.substrate.routes.basket_new import router as new_router
from infra.substrate.routes.basket_snapshot import router as snapshot_router
from infra.substrate.routes.dump_new import router as dump_router

app = FastAPI()
app.include_router(new_router, prefix="/api")
app.include_router(dump_router, prefix="/api")
app.include_router(snapshot_router, prefix="/api")
client = TestClient(app)


def _supabase(store):
    def table(name):
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

            def insert(self, row):
                self._op = "insert"
                self._values = row
                return self

            def update(self, vals):
                self._op = "update"
                self._values = vals
                return self

            def eq(self, col, val):
                self._filters.append((col, val))
                return self

            def single(self):
                self._single = True
                return self

            def order(self, *_a, **_k):
                return self

            def in_(self, *_a, **_k):
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
                res = data
                for c, v in self._filters:
                    res = [r for r in res if r.get(c) == v]
                if self._single:
                    return types.SimpleNamespace(data=res[0] if res else None, error=None)
                return types.SimpleNamespace(data=res, error=None)

        return Q()

    return types.SimpleNamespace(table=table)


def test_snapshot_after_flow(monkeypatch):
    user_id = "00000000-0000-0000-0000-000000000000"
    store = {
        "workspace_memberships": [{"workspace_id": "ws1", "user_id": user_id}],
        "baskets": [],
        "raw_dumps": [],
        "blocks": [],
    }
    fake = _supabase(store)
    monkeypatch.setattr("app.routes.basket_new.supabase", fake)
    monkeypatch.setattr("app.routes.dump_new.supabase", fake)
    monkeypatch.setattr("app.routes.basket_snapshot.supabase", fake)

    b_payload = {"idempotency_key": str(uuid.uuid4()), "basket": {}}
    basket = client.post("/api/baskets/new", json=b_payload)
    bid = basket.json()["basket_id"]

    d_payload = {
        "basket_id": bid,
        "dump_request_id": str(uuid.uuid4()),
        "text_dump": "hello",
    }
    dump_resp = client.post("/api/dumps/new", json=d_payload)
    assert dump_resp.status_code == 201

    snap = client.get(f"/api/baskets/{bid}/snapshot")
    assert snap.status_code == 200
    assert snap.json()["raw_dump"] == "hello"

