
# ruff: noqa
import os
import sys
import types
import uuid
import pytest

pytest.skip("requires full dependency stack", allow_module_level=True)

from fastapi import FastAPI
from fastapi.testclient import TestClient

asyncpg_stub = types.SimpleNamespace(Connection=object)
sys.modules.setdefault("asyncpg", asyncpg_stub)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../src"))

from infra.substrate.routes.agents import router as agents_router

app = FastAPI()
app.include_router(agents_router, prefix="/api")
client = TestClient(app)


def _fake_supabase(store):
    def table(name: str):
        def insert(row: dict):
            row = {**row}
            if "id" not in row:
                row["id"] = str(uuid.uuid4())
            store.setdefault(name, []).append(row)
            return types.SimpleNamespace(
                execute=lambda: types.SimpleNamespace(data=[row], error=None)
            )

        def select(_cols="*"):
            def eq(col: str, val: str):
                items = [r for r in store.get(name, []) if r.get(col) == val]
                return types.SimpleNamespace(
                    execute=lambda: types.SimpleNamespace(data=items, error=None)
                )

            return types.SimpleNamespace(eq=eq)

        return types.SimpleNamespace(insert=insert, select=select)

    return types.SimpleNamespace(table=table)


def test_run_blockifier(monkeypatch):
    store = {"baskets": [], "raw_dumps": [], "blocks": []}
    fake = _fake_supabase(store)
    monkeypatch.setattr("app.routes.agents.supabase", fake)
    monkeypatch.setattr(
        "app.agents.runtime.infra_observer_agent.supabase",
        fake,
    )

    basket_id = str(uuid.uuid4())
    dump_id = str(uuid.uuid4())
    store["baskets"].append({"id": basket_id, "raw_dump_id": dump_id, "workspace_id": "ws1"})
    store["raw_dumps"].append({"id": dump_id, "basket_id": basket_id, "body_md": "d"})

    resp = client.post("/api/agents/orch_block_manager/run", json={"basket_id": basket_id})
    assert resp.status_code == 200
    assert resp.json()["inserted"] >= 1
    assert store["blocks"]

