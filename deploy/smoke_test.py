#!/usr/bin/env python3
"""Smoke test for the demo kit — probes every demo on its port.

Used by CI (against the running Docker container) and handy locally:

    python deploy/serve.py &                 # or: docker compose up
    ADMIN_TOKEN=test python deploy/smoke_test.py

Exits non-zero on the first failure. Uses only the standard library so it needs
no dependencies beyond Python itself.
"""

import os
import sys
import time
import urllib.error
import urllib.request

HOST = os.environ.get("SMOKE_HOST", "127.0.0.1")
TOKEN = os.environ.get("ADMIN_TOKEN", "changeme")

PORTS = {
    "hub": int(os.environ.get("PORT_HUB", "10000")),
    "a": int(os.environ.get("PORT_A", "10001")),
    "b": int(os.environ.get("PORT_B", "10002")),
    "c": int(os.environ.get("PORT_C", "10003")),
    "d": int(os.environ.get("PORT_D", "10004")),
    "e": int(os.environ.get("PORT_E", "10005")),
}


def url(key, path=""):
    return f"http://{HOST}:{PORTS[key]}{path}"


def fetch(u, method="GET", data=None, headers=None, follow=True):
    """Return (status, location, body_bytes). Never raises on HTTP errors."""
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None

    opener = urllib.request.build_opener(
        *( () if follow else (NoRedirect,) ))
    req = urllib.request.Request(u, method=method, data=data,
                                 headers=headers or {})
    try:
        with opener.open(req, timeout=10) as r:
            return r.status, r.headers.get("Location"), r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Location"), e.read()


def wait_ready(timeout=60):
    """Block until the hub answers /healthz, or fail."""
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        try:
            status, _, _ = fetch(url("hub", "/healthz"))
            if status == 200:
                return
            last = f"status {status}"
        except Exception as e:  # connection refused while booting
            last = str(e)
        time.sleep(1)
    fail(f"hub never became ready on {url('hub', '/healthz')} ({last})")


PASS, FAILED = 0, 0


def check(label, got, want):
    global PASS, FAILED
    ok = got == want
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}: got {got!r}, want {want!r}")
    if ok:
        PASS += 1
    else:
        FAILED += 1


def check_true(label, cond, detail=""):
    global PASS, FAILED
    print(f"  [{'PASS' if cond else 'FAIL'}] {label} {detail}")
    if cond:
        PASS += 1
    else:
        FAILED += 1


def fail(msg):
    print(f"FATAL: {msg}", file=sys.stderr)
    sys.exit(2)


def status_of(key, path, follow=True):
    return fetch(url(key, path), follow=follow)[0]


def main():
    print(f"Waiting for stack at {HOST} ...")
    wait_ready()
    print("Stack is up. Probing demos:\n")

    print("hub")
    check("GET /", status_of("hub", "/"), 200)
    check("GET /healthz", status_of("hub", "/healthz"), 200)

    print("Demo A")
    for p in ("/", "/your-bank.html", "/not-your-bank.html", "/poll", "/vote",
              "/assets/code-left.png", "/assets/code-right.png", "/healthz"):
        check(f"GET {p}", status_of("a", p), 200)

    print("Demo B")
    for p in ("/", "/gotcha", "/assets/lookalike.png"):
        check(f"GET {p}", status_of("b", p), 200)

    print("Demo C")
    check("GET /go/demo1 (no-follow)", status_of("c", "/go/demo1", follow=False), 302)
    check("GET /admin (no token)", status_of("c", "/admin"), 403)
    check("GET /admin?token=", status_of("c", f"/admin?token={TOKEN}"), 200)
    check("GET /land/benign", status_of("c", "/land/benign"), 200)
    # Toggle: flip to swapped, confirm the redirect target follows, then reset.
    fetch(url("c", f"/admin/set?token={TOKEN}"), method="POST",
          data=b'{"target":"swapped"}',
          headers={"Content-Type": "application/json"})
    _, loc, _ = fetch(url("c", "/go/demo1"), follow=False)
    check_true("toggle flips redirect to swapped", bool(loc and "swapped" in loc),
               f"(Location={loc})")
    fetch(url("c", f"/admin/set?token={TOKEN}"), method="POST",
          data=b'{"target":"benign"}',
          headers={"Content-Type": "application/json"})
    _, loc2, _ = fetch(url("c", "/go/demo1"), follow=False)
    check_true("reset flips redirect back to benign",
               bool(loc2 and "benign" in loc2), f"(Location={loc2})")

    print("Demo D")
    check("GET /", status_of("d", "/"), 200)
    check("GET /invoice", status_of("d", "/invoice"), 200)
    _, _, pdf = fetch(url("d", "/invoice.pdf"))
    check_true("GET /invoice.pdf is a PDF", pdf[:5] == b"%PDF-",
               f"(first bytes {pdf[:5]!r})")

    print("Demo E")
    for p in ("/", "/portal", "/assets/wifi.png"):
        check(f"GET {p}", status_of("e", p), 200)

    print(f"\n{PASS} passed, {FAILED} failed")
    sys.exit(1 if FAILED else 0)


if __name__ == "__main__":
    main()
