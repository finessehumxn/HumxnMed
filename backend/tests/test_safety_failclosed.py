"""Regression tests for the safety guardrail's fail-closed behaviour.

Run with: python3 backend/tests/test_safety_failclosed.py   (no deps required)

WHY THIS EXISTS
---------------
The guardrail node previously returned `guardrail_status: "pass"` from its except
branch, and both the router and the API layer defaulted to "pass"/"extraction" when
the status was missing or unrecognised. Any API timeout, 429, 529, refusal, or
markdown-fenced JSON reply therefore routed a crisis message into the normal
briefing pipeline instead of to 988.

Every test below is a path that used to fail open. If one of these starts failing,
someone has reintroduced a default that assumes "unknown means safe". It does not.
"""
import sys, types, importlib.util, os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _stub(name, **attrs):
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules[name] = m
    return m


def _load(mod_name, path):
    spec = importlib.util.spec_from_file_location(mod_name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


def _bootstrap():
    """Register package shells + third-party stubs so the real modules import
    without langgraph / anthropic / dotenv installed."""
    _stub("dotenv", load_dotenv=lambda *a, **k: None)
    _stub("anthropic", Anthropic=lambda *a, **k: None)

    class StateGraph:
        def __init__(s, *a): s.nodes, s.edges, s.cond = {}, [], {}
        def add_node(s, n, f): s.nodes[n] = f
        def add_edge(s, a, b): s.edges.append((a, b))
        def add_conditional_edges(s, src, fn, m): s.cond[src] = (fn, m)
        def compile(s, **k): return s

    lgg = _stub("langgraph.graph", StateGraph=StateGraph, START="START", END="END")
    _stub("langgraph", graph=lgg)
    _stub("langgraph.checkpoint")
    _stub("langgraph.checkpoint.memory", MemorySaver=lambda: None)

    pkg = types.ModuleType("backend"); pkg.__path__ = [f"{ROOT}/backend"]
    sys.modules["backend"] = pkg
    _stub("backend.state", PatientState=dict)
    nodes = types.ModuleType("backend.nodes"); nodes.__path__ = [f"{ROOT}/backend/nodes"]
    sys.modules["backend.nodes"] = nodes
    for n in ("extraction", "normalization", "confirmation", "briefing"):
        _stub(f"backend.nodes.{n}_node", **{f"{n}_node": lambda s: {}})

    G = _load("backend.nodes.guardrail_node", f"{ROOT}/backend/nodes/guardrail_node.py")
    GR = _load("backend.graph", f"{ROOT}/backend/graph.py")
    return G, GR


class _Blk:
    def __init__(s, t, txt): s.type, s.text = t, txt


class _Resp:
    def __init__(s, blocks): s.content = blocks


def main():
    import logging
    logging.disable(logging.CRITICAL)  # the node logs failures loudly by design
    G, GR = _bootstrap()
    results = []

    def check(name, cond):
        results.append(cond)
        print(f"{'PASS' if cond else 'FAIL'} | {name}")

    def guard(name, blocks=None, exc=None, raw="my knee hurts", expect=None):
        def fake_create(**kw):
            if exc: raise exc
            return _Resp(blocks)
        G.get_client = lambda: types.SimpleNamespace(
            messages=types.SimpleNamespace(create=fake_create))
        got = G.guardrail_node({"raw_input": raw})["guardrail_status"]
        check(f"{name:<42} -> {got}", got == expect)

    print("=== guardrail_node: outages and bad replies fail CLOSED ===")
    guard("API timeout",              exc=TimeoutError("timeout"),          expect="unavailable")
    guard("API 529 overloaded",       exc=RuntimeError("overloaded_error"), expect="unavailable")
    guard("refusal (empty content)",  blocks=[],                            expect="unavailable")
    guard("JSON missing status key",  blocks=[_Blk("text", '{"message":"hi"}')],       expect="unavailable")
    guard("unknown status value",     blocks=[_Blk("text", '{"status":"PASS_MAYBE"}')], expect="unavailable")
    guard("non-JSON prose",           blocks=[_Blk("text", 'Sure! status is pass.')],   expect="unavailable")

    print("\n=== crisis language still reaches 988 when the classifier is down ===")
    guard("crisis + API down",  exc=TimeoutError(), raw="i want to kill myself", expect="crisis")
    guard("emergency + API down", exc=TimeoutError(), raw="severe chest pain now", expect="emergency")

    print("\n=== normal operation is unchanged ===")
    guard("plain pass",           blocks=[_Blk("text", '{"status":"pass","message":""}')], expect="pass")
    guard("markdown-fenced JSON", blocks=[_Blk("text", '```json\n{"status":"crisis"}\n```')], expect="crisis")
    guard("JSON embedded in prose", blocks=[_Blk("text", 'ok: {"status":"invalid"} !')], expect="invalid")
    guard("uppercase + padded",   blocks=[_Blk("text", '{"status":" Emergency "}')], expect="emergency")
    guard("thinking block first", blocks=[_Blk("thinking", "..."), _Blk("text", '{"status":"pass"}')], expect="pass")

    print("\n=== route_after_guardrail: unknown never means extraction ===")
    for state, want in [
        ({"guardrail_status": "pass"},        "extraction"),
        ({"guardrail_status": "crisis"},      "crisis_handler"),
        ({"guardrail_status": "emergency"},   "emergency_handler"),
        ({"guardrail_status": "unavailable"}, "unavailable_handler"),
        ({},                                  "unavailable_handler"),
        ({"guardrail_status": None},          "unavailable_handler"),
        ({"guardrail_status": "Crisis"},      "unavailable_handler"),
        ({"guardrail_status": "weird"},       "unavailable_handler"),
    ]:
        got = GR.route_after_guardrail(state)
        check(f"{str(state):<36} -> {got}", got == want)

    print("\n=== graph wiring ===")
    g = GR.build_graph()
    check("unavailable_handler registered", "unavailable_handler" in g.nodes)
    check("unavailable_handler -> END", ("unavailable_handler", "END") in g.edges)
    check("reachable from guardrail", "unavailable_handler" in g.cond["guardrail"][1].values())
    msg = GR.unavailable_handler({})["guardrail_message"]
    check("handler message carries 911 and 988", "911" in msg and "988" in msg)

    print(f"\n{sum(results)}/{len(results)} passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
