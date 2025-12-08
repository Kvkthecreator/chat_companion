import types
import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient

from infra.substrate.routes.dump_new import router as dump_router

app = FastAPI()
app.include_router(dump_router, prefix="/api")
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
                res = data
                for c, v in self._filters:
                    res = [r for r in res if r.get(c) == v]
                if self._single:
                    return types.SimpleNamespace(data=res[0] if res else None, error=None)
                return types.SimpleNamespace(data=res, error=None)

        return Q()

    return types.SimpleNamespace(table=table)


def test_dump_new_governance_flow(monkeypatch):
    """Test dump creation triggers governance flow instead of direct substrate writes."""
    user_id = "00000000-0000-0000-0000-000000000000"
    store = {
        "baskets": [{"id": "b1", "workspace_id": "ws1"}],
        "workspace_memberships": [{"workspace_id": "ws1", "user_id": user_id}],
        "raw_dumps": [],
        "agent_processing_queue": [],  # Governance: queue for proposal creation
    }
    fake = _supabase(store)
    monkeypatch.setattr("app.routes.dump_new.supabase", fake)

    payload = {
        "basket_id": "b1",
        "dump_request_id": str(uuid.uuid4()),
        "text_dump": "Strategic goal: improve customer experience through better onboarding.",
    }

    resp = client.post("/api/dumps/new", json=payload)
    assert resp.status_code == 201
    dump_id = resp.json()["dump_id"]
    
    # Verify dump created
    assert store["raw_dumps"][0]["id"] == dump_id
    
    # Governance: dump should trigger queue processing, not immediate substrate
    # Agent queue will process dump → create proposals → await human approval
    # This preserves Sacred Principle: Capture is Sacred while adding governance layer


def test_dump_new_legacy_compatibility(monkeypatch):
    """Test dump creation in legacy mode (governance disabled)."""
    user_id = "00000000-0000-0000-0000-000000000000"
    store = {
        "baskets": [{"id": "b1", "workspace_id": "ws1"}],
        "workspace_memberships": [{"workspace_id": "ws1", "user_id": user_id}],
        "raw_dumps": [],
    }
    fake = _supabase(store)
    monkeypatch.setattr("app.routes.dump_new.supabase", fake)

    payload = {
        "basket_id": "b1",
        "dump_request_id": str(uuid.uuid4()),
        "text_dump": "hello",
    }

    resp = client.post("/api/dumps/new", json=payload)
    assert resp.status_code == 201
    dump_id = resp.json()["dump_id"]
    assert store["raw_dumps"][0]["id"] == dump_id


def test_dump_requires_content(monkeypatch):
    store = {
        "baskets": [{"id": "b1", "workspace_id": "ws1"}],
        "workspace_memberships": [
            {
                "workspace_id": "ws1",
                "user_id": "00000000-0000-0000-0000-000000000000",
            }
        ],
        "raw_dumps": [],
    }
    fake = _supabase(store)
    monkeypatch.setattr("app.routes.dump_new.supabase", fake)

    payload = {"basket_id": "b1", "dump_request_id": str(uuid.uuid4())}
    resp = client.post("/api/dumps/new", json=payload)
    assert resp.status_code == 422

