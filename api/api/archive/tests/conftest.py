import importlib
import os
import sys
import types

tests_dir = os.path.dirname(__file__)
# Ensure api/src has highest priority so tests import new code
sys.path.insert(0, os.path.join(tests_dir, "../../src"))
sys.path.insert(0, os.path.join(tests_dir, ".."))
sys.path.insert(0, os.path.join(tests_dir, "../src"))


def _stub(name: str):
    mod = types.ModuleType(name)
    sys.modules[name] = mod
    return mod


for name in ("supabase", "supabase_py", "asyncpg"):
    if name not in sys.modules:
        mod = _stub(name)
        if name == "supabase":
            class _SupabaseStub:
                def __init__(self):
                    self.postgrest = types.SimpleNamespace(auth=lambda *args, **kwargs: None)

                # Fluent interface used by tests; return self for chaining
                def table(self, *args, **kwargs):
                    return self

                def select(self, *args, **kwargs):
                    return self

                def insert(self, *args, **kwargs):
                    return self

                def update(self, *args, **kwargs):
                    return self

                def eq(self, *args, **kwargs):
                    return self

                def single(self, *args, **kwargs):
                    return self

                def order(self, *args, **kwargs):
                    return self

                def limit(self, *args, **kwargs):
                    return self

                def in_(self, *args, **kwargs):
                    return self

                def rpc(self, *args, **kwargs):
                    return self

                def execute(self, *args, **kwargs):
                    return types.SimpleNamespace(data=[], error=None)

            mod.create_client = lambda *a, **k: _SupabaseStub()
        if name == "asyncpg":
            mod.Pool = type("Pool", (), {})
            mod.create_pool = lambda *a, **k: None
            mod.Connection = type("Connection", (), {})

# ensure pytest can import supabase_py from 'supabase'
sys.modules["supabase_py"] = sys.modules.get("supabase", sys.modules.get("supabase_py"))

os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "stub-key")
os.environ.setdefault("SUPABASE_URL", "http://stub.local")
os.environ.setdefault("SERVICE_ROLE", "stub-key")

if "app.util.snapshot_assembler" not in sys.modules:
    try:
        real = importlib.import_module("app.utils.snapshot_assembler")
    except Exception:
        real = types.ModuleType("snapshot_assembler")
    sys.modules["app.util.snapshot_assembler"] = real

# Bypass JWT verification in API routes so tests can run offline
def stub_user(
    sb_access_token: str | None = None,
    authorization: str | None = None,
) -> dict:
    return {"user_id": "00000000-0000-0000-0000-000000000000"}
try:
    import infra.utils.jwt as jwt
    jwt.verify_jwt = stub_user
    for mod_name in [
        "app.routes.basket_new",
        "app.routes.basket_snapshot",
        "app.routes.baskets",
        "app.routes.context_items",
        "app.routes.dump_new",
        "app.routes.basket_from_template",
        "app.routes.orch_block_manager",
    ]:
        try:
            m = importlib.import_module(mod_name)
            m.verify_jwt = stub_user  # type: ignore[attr-defined]
        except Exception:
            pass
except Exception:
    pass
