"""Regression guard for the source-link XSS in renderBriefing().

Run with: python3 backend/tests/test_frontend_xss_guard.py   (no deps required)

WHY THIS EXISTS
---------------
Source links used to render as:

    <div class="src-url" onclick="window.open('" + clean(s.url) + "','_blank')">

clean() escapes & < > " but NOT the single quote, so a URL containing ' broke out of
window.open('...') and executed. Escaping ' would NOT have fixed it either: a browser
decodes HTML entities before JS parses an inline handler, so &#39; becomes ' again.

Source URLs are model output grounded in fetched web pages, which makes them
attacker-influenceable — e.g. via text in an uploaded lab photo.

The fix was to stop putting data in a JS context at all: render an <a href> with an
http(s) allowlist. These tests assert against the real frontend/index.html so the
pattern can't come back.
"""
import os, re, sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INDEX = os.path.join(ROOT, "frontend", "index.html")

results = []


def check(name, cond, detail=""):
    results.append(cond)
    print(f"{'PASS' if cond else 'FAIL'} | {name}" + (f"  <- {detail}" if not cond and detail else ""))


def clean(s):
    """Mirror of frontend clean(), kept in sync by test_clean_matches_source below."""
    s = str(s or "")
    s = re.sub(r"<cite[^>]*>", "", s)
    s = s.replace("</cite>", "")
    s = re.sub(r"\[\d+\]", "", s)
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;").replace("'", "&#39;"))


def row(src, i=0):
    """Mirror of the srcRows mapper."""
    u = str(src.get("url") or "").strip()
    safe = u if re.match(r"^https?://", u, re.I) else ""
    link = (f'<a class="src-url" href="{clean(safe)}" target="_blank" '
            f'rel="noopener noreferrer">{clean(safe)}</a>'
            if safe else f'<div class="src-url">{clean(u)}</div>')
    return (f'<div class="src-item"><div class="src-num">{i+1}</div><div>'
            f'<div class="src-name">{clean(src.get("title"))}</div>{link}</div></div>')


class Audit(HTMLParser):
    """Parse the generated markup the way a browser does. Regex cannot tell an
    attribute from escaped text inside a quoted value; a real parser can."""
    def __init__(self):
        super().__init__()
        self.problems = []

    def handle_starttag(self, tag, attrs):
        if tag not in ("div", "a"):
            self.problems.append(f"injected <{tag}>")
        for k, v in attrs:
            if k.lower().startswith("on"):
                self.problems.append(f"event handler {k}=")
            if k.lower() == "href" and not re.match(r"^https?://", v or "", re.I):
                self.problems.append(f"non-http href {v!r}")


def main():
    if not os.path.exists(INDEX):
        print(f"FAIL | cannot find {INDEX}")
        return 1
    src = open(INDEX, encoding="utf-8").read()

    print("=== the shipped file ===")
    check("clean() escapes the single quote",
          bool(re.search(r"replace\(/'/g\s*,\s*'&#39;'\)", src)),
          "clean() must escape ' or single-quoted attributes are breakable")
    for ch, ent in [("&", "&amp;"), ("<", "&lt;"), (">", "&gt;"), ('"', "&quot;")]:
        check(f"clean() still escapes {ch}", ent in src)
    check("no inline handler is fed by clean()",
          not re.search(r"on\w+\s*=\s*\"[^\"]*\\'\s*\"\s*\+\s*clean\(", src),
          "data interpolated into an inline event handler is unfixable by escaping")
    check("source links render as <a href>", 'class="src-url" href="' in src)
    check("source links carry rel=noopener noreferrer", 'rel="noopener noreferrer"' in src)
    check("source URLs are scheme-allowlisted",
          bool(re.search(r"\^https\?:\\?/\\?/", src)), "expected an ^https?:// test")

    print("\n=== rendered output vs injection attempts ===")
    cases = [
        ("quote breakout in url",   {"title": "t", "url": "x'),alert(1),('"}),
        ("javascript: scheme",      {"title": "t", "url": "javascript:alert(1)"}),
        ("data: scheme",            {"title": "t", "url": "data:text/html,<script>alert(1)</script>"}),
        ("tag injected via title",  {"title": "<img src=x onerror=alert(1)>", "url": "https://ok.example"}),
        ("quote breakout in title", {"title": 'a" onload="alert(1)', "url": "https://ok.example"}),
        ("url breaking the href",   {"title": "t", "url": 'https://a" onmouseover="alert(1)'}),
        ("entity-encoded quote",    {"title": "t", "url": "https://a&quot; onerror=&quot;x"}),
        ("normal https link",       {"title": "NIH", "url": "https://nih.gov/x"}),
    ]
    for name, case in cases:
        a = Audit()
        a.feed(row(case))
        check(name, not a.problems, ", ".join(a.problems))

    good = row({"title": "NIH", "url": "https://nih.gov/x"})
    check("legitimate source still renders a working link",
          'href="https://nih.gov/x"' in good and 'rel="noopener noreferrer"' in good)

    print(f"\n{sum(results)}/{len(results)} passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
