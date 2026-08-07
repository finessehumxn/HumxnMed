"""Rate limiting on paid endpoints + PHI checkpoint purge.

Run with: python3 backend/tests/test_metering_and_purge.py   (needs fastapi, httpx)

WHY THIS EXISTS
---------------
Every POST in _METERED_PATHS spends Anthropic/OpenAI tokens. Unmetered they were an
uncapped billing liability reachable by anyone with curl. And MemorySaver retained
each session's PatientState -- the patient's own words -- in RAM until the process
restarted, which is both an unbounded leak and PHI retention the app promises not to do.
"""
import sys, types, importlib.util, os, logging
logging.disable(logging.CRITICAL)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def stub(n, **a):
    m=types.ModuleType(n); [setattr(m,k,v) for k,v in a.items()]; sys.modules[n]=m; return m
stub("dotenv", load_dotenv=lambda *a,**k: None)
stub("anthropic", Anthropic=lambda *a,**k: None)
lgg=stub("langgraph.graph", StateGraph=object, START="S", END="E"); stub("langgraph", graph=lgg)
stub("langgraph.checkpoint"); stub("langgraph.checkpoint.memory", MemorySaver=lambda: None)
stub("langgraph.types", Command=object)

class FakeCP:
    def __init__(s): s.storage={"t1":{"phi":"my knee hurts"}, "t2":{}}
fake_graph = types.SimpleNamespace(get_state=lambda c: None, checkpointer=FakeCP())
pkg=types.ModuleType("backend"); pkg.__path__=[f'{ROOT}/backend']; sys.modules['backend']=pkg
stub("backend.graph", build_graph=lambda: fake_graph, graph=fake_graph)
stub("backend.state", PatientState=dict)
sc={n:(lambda *a,**k: None) for n in ("get_supabase","save_session","get_user_history",
    "get_symptom_history","log_symptom","export_user_data","delete_user_data",
    "clear_user_data","add_to_waitlist","set_entitlement","get_entitlement")}
sc["SUPABASE_ENABLED"]=False; stub("backend.supabase_client", **sc)

spec=importlib.util.spec_from_file_location("backend.server", f'{ROOT}/backend/server.py')
S=importlib.util.module_from_spec(spec); sys.modules[spec.name]=S; spec.loader.exec_module(S)

r=[]
def chk(n,c): r.append(c); print(f"{'PASS' if c else 'FAIL'} | {n}")

print("=== rate limiting on paid endpoints ===")
from fastapi.testclient import TestClient
c = TestClient(S.app, raise_server_exceptions=False)
S._attempts.clear()
codes=[c.post("/triage", json={}).status_code for _ in range(S.MC_RATE_LIMIT+3)]
chk(f"POST /triage throttles after {S.MC_RATE_LIMIT}", codes.count(429)==3 and codes[-1]==429)
chk("429 carries Retry-After", c.post("/triage", json={}).headers.get("retry-after")==str(S.MC_RATE_WINDOW))
S._attempts.clear()
polls=[c.get("/session/abc/result").status_code for _ in range(S.MC_RATE_LIMIT+5)]
chk("GET /session/{id}/result never throttled (app polls it)", 429 not in polls)
S._attempts.clear()
chk("unmetered GET /health unaffected", c.get("/health").status_code != 429)
S._attempts.clear()
chk("POST /session/start is metered",
    [c.post("/session/start", json={"raw_input":"x"}).status_code for _ in range(S.MC_RATE_LIMIT+2)].count(429)==2)
S._attempts.clear()
h={"x-forwarded-for":"9.9.9.9, 10.0.0.1"}
for _ in range(S.MC_RATE_LIMIT): c.post("/triage", json={}, headers=h)
chk("throttles per client IP via X-Forwarded-For", c.post("/triage", json={}, headers=h).status_code==429)
chk("a different XFF IP is unaffected",
    c.post("/triage", json={}, headers={"x-forwarded-for":"8.8.8.8"}).status_code!=429)

print("\n=== PHI checkpoint purge ===")
chk("thread present before purge", "t1" in S.graph.checkpointer.storage)
S._purge_thread("t1")
chk("purged after session completes", "t1" not in S.graph.checkpointer.storage)
chk("other threads untouched", "t2" in S.graph.checkpointer.storage)
S._purge_thread("does-not-exist"); chk("purging unknown thread is a no-op", True)
class Broken:
    @property
    def storage(self): raise RuntimeError("boom")
S.graph = types.SimpleNamespace(checkpointer=Broken())
S._purge_thread("t1"); chk("survives a checkpointer that raises", True)

print(f"\n{sum(r)}/{len(r)} passed")
sys.exit(0 if all(r) else 1)
