"""Canonical-host redirect.

Run with: python3 backend/tests/test_canonical_host.py   (needs fastapi, httpx)

WHY THIS EXISTS
---------------
Four domains serve this app. The purchase unlock is same-origin localStorage, so a
buyer who browses on one domain and gets sent by Stripe to /welcome on another pays
and still sees the free tier. MC_CANONICAL_HOST forces every page load onto one
origin. It must stay inert when unset, must never redirect API POSTs, and must not
break Capacitor (host: localhost), local dev, or Railway's /health probe.
"""
import sys, types, importlib.util, os, logging

logging.disable(logging.CRITICAL)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CANON = "humxnmed.millennialscreatives.com"


def _stub(n, **a):
    m = types.ModuleType(n)
    for k, v in a.items():
        setattr(m, k, v)
    sys.modules[n] = m
    return m


def _load_server():
    for mod in [m for m in sys.modules if m.startswith("backend")]:
        sys.modules.pop(mod, None)
    _stub("dotenv", load_dotenv=lambda *a, **k: None)
    _stub("anthropic", Anthropic=lambda *a, **k: None)
    lgg = _stub("langgraph.graph", StateGraph=object, START="S", END="E")
    _stub("langgraph", graph=lgg)
    _stub("langgraph.checkpoint")
    _stub("langgraph.checkpoint.memory", MemorySaver=lambda: None)
    _stub("langgraph.types", Command=object)
    pkg = types.ModuleType("backend"); pkg.__path__ = [f"{ROOT}/backend"]
    sys.modules["backend"] = pkg
    g = types.SimpleNamespace(get_state=lambda c: None, checkpointer=None)
    _stub("backend.graph", build_graph=lambda: g, graph=g)
    _stub("backend.state", PatientState=dict)
    sc = {n: (lambda *a, **k: None) for n in
          ("get_supabase", "save_session", "get_user_history", "get_symptom_history",
           "log_symptom", "export_user_data", "delete_user_data", "clear_user_data",
           "add_to_waitlist", "set_entitlement", "get_entitlement")}
    sc["SUPABASE_ENABLED"] = False
    _stub("backend.supabase_client", **sc)
    spec = importlib.util.spec_from_file_location("backend.server", f"{ROOT}/backend/server.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


results = []


def check(name, cond, detail=""):
    results.append(cond)
    print(f"{'PASS' if cond else 'FAIL'} | {name}" + (f"  <- {detail}" if not cond and detail else ""))


def main():
    from fastapi.testclient import TestClient

    print("=== default: unset means inert ===")
    os.environ.pop("MC_CANONICAL_HOST", None)
    S = _load_server()
    check("MC_CANONICAL_HOST empty by default", S.MC_CANONICAL_HOST == "")
    c = TestClient(S.app, follow_redirects=False)
    r = c.get("/health", headers={"host": "medcompanionai.com"})
    check("no redirect when unset", r.status_code != 301, f"got {r.status_code}")

    print("\n=== enabled ===")
    os.environ["MC_CANONICAL_HOST"] = CANON
    S = _load_server()
    S._attempts.clear()
    c = TestClient(S.app, follow_redirects=False)

    r = c.get("/founding", headers={"host": "medcompanionai.com"})
    check("wrong host redirects 301", r.status_code == 301, f"got {r.status_code}")
    check("redirects to the canonical origin",
          r.headers.get("location", "").startswith(f"https://{CANON}/founding"),
          r.headers.get("location", ""))

    r = c.get("/welcome?session_id=cs_test_123", headers={"host": "medcompanionai.com"})
    check("query string preserved (session_id survives)",
          r.headers.get("location", "").endswith("/welcome?session_id=cs_test_123"),
          r.headers.get("location", ""))

    r = c.get("/founding", headers={"host": CANON})
    check("canonical host passes through", r.status_code != 301, f"got {r.status_code}")

    r = c.post("/triage", json={}, headers={"host": "medcompanionai.com"})
    check("POST is never redirected (would break API clients)",
          r.status_code != 301, f"got {r.status_code}")

    r = c.get("/health", headers={"host": "medcompanion-ai.up.railway.app"})
    check("/health answers on any host (Railway probe)", r.status_code == 200, f"got {r.status_code}")

    r = c.get("/founding", headers={"host": "localhost"})
    check("localhost not redirected (dev + Capacitor shell)",
          r.status_code != 301, f"got {r.status_code}")
    r = c.get("/founding", headers={"host": "127.0.0.1"})
    check("127.0.0.1 not redirected", r.status_code != 301, f"got {r.status_code}")

    print("\n=== config tolerance ===")
    for raw in (f"https://{CANON}", f"{CANON}/", f"  {CANON.upper()}  "):
        os.environ["MC_CANONICAL_HOST"] = raw
        check(f"normalises {raw!r}", _load_server().MC_CANONICAL_HOST == CANON)

    os.environ.pop("MC_CANONICAL_HOST", None)
    print(f"\n{sum(results)}/{len(results)} passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
