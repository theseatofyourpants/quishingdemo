#!/usr/bin/env python3
"""Launch every demo on its own port, one process, for the Docker container.

Ports (defaults, overridable via PORT_* env):
    10000  hub index (links to all demos)
    10001  Demo A — two identical codes + live poll
    10002  Demo B — URL-preview defeat
    10003  Demo C — dynamic-QR switch (redirector + admin toggle)
    10004  Demo D — quishing-in-PDF (download + reveal)
    10005  Demo E — Wi-Fi join reveal

Each demo is a Flask app served by waitress in its own thread. On startup the
QR assets and the decoy PDF are regenerated from shared/config.py so every code
encodes the current PUBLIC_* URLs (skip with REGEN_ASSETS=0).

Behind a Cloudflare tunnel you map one hostname per port; see deploy/README or
deploy/cloudflared.example.yml.
"""

import html
import importlib.util
import os
import sys
import threading

from flask import Flask, Response, send_from_directory
from waitress import serve

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from shared import config  # noqa: E402


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def static_app(base_dir, routes, name):
    """Build a Flask app that serves `base_dir`.

    routes: {url_rule: filename} for named pages. /assets/<f> and /shared/<f>
    are always wired so landing pages find their QR images and the shared CSS.
    """
    app = Flask(name)

    def make_view(filename):
        def view():
            return send_from_directory(base_dir, filename)
        return view

    for i, (rule, filename) in enumerate(routes.items()):
        app.add_url_rule(rule, endpoint=f"page_{i}", view_func=make_view(filename))

    @app.route("/assets/<path:f>")
    def assets(f):
        return send_from_directory(os.path.join(base_dir, "assets"), f)

    @app.route("/shared/<path:f>")
    def shared(f):
        return send_from_directory(os.path.join(ROOT, "shared"), f)

    @app.route("/healthz")
    def healthz():
        return {"ok": True, "demo": name}

    return app


def demo_d_app():
    base = os.path.join(ROOT, "demo-d-pdf-quishing")
    app = static_app(base, {
        "/": "index.html",
        "/invoice": "invoice.html",
    }, "demo-d")

    @app.route("/invoice.pdf")
    def pdf():
        return send_from_directory(os.path.join(base, "assets"),
                                   "invoice-quishing.pdf")

    return app


def hub_app():
    """A simple index linking to each demo at its public URL."""
    app = Flask("hub")
    demos = [
        ("A", "Two identical codes", "Nobody can tell a safe QR from a malicious one", config.PUBLIC["a"]),
        ("B", "URL-preview defeat", "Spot a lookalike domain typed — not as a QR", config.PUBLIC["b"]),
        ("C", "Dynamic-QR switch", "The sticker can change after you inspect it", config.PUBLIC["c"]),
        ("D", "Quishing-in-PDF", "Why the email filter didn't catch it", config.PUBLIC["d"]),
        ("E", "Wi-Fi join reveal", "A QR can join your phone to a network with no click", config.PUBLIC["e"]),
    ]
    cards = "\n".join(
        f'<a class="card" href="{html.escape(url)}"><span class="k">{k}</span>'
        f'<span class="t">{html.escape(title)}</span>'
        f'<span class="d">{html.escape(desc)}</span></a>'
        for k, title, desc, url in demos)

    page = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>QR Quishing Demo Kit</title>
<link rel="stylesheet" href="/shared/landing.css">
<style>
 body{{justify-content:flex-start;padding-top:6vh}}
 .grid{{display:grid;gap:1rem;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));
   width:100%;max-width:900px;margin-top:1.5rem}}
 .card{{display:flex;flex-direction:column;gap:.4rem;text-align:left;
   background:var(--bg-panel);border:1px solid var(--border);border-radius:16px;
   padding:1.3rem 1.4rem;text-decoration:none;color:var(--ink);transition:border-color .15s}}
 .card:hover{{border-color:var(--accent)}}
 .card .k{{font-size:1.6rem;font-weight:800;color:var(--accent)}}
 .card .t{{font-size:1.15rem;font-weight:700}}
 .card .d{{color:var(--muted);font-size:.95rem}}
</style></head><body><div class="wrap">
<p class="eyebrow">Awareness / education material</p>
<h1>QR <span class="hl-m">Quishing</span> Demo Kit</h1>
<p class="lede">Five safe demos. Every destination is a domain the speaker owns.</p>
<div class="grid">{cards}</div>
<p class="foot">A QR code is data, not code — it executes nothing</p>
</div></body></html>"""

    @app.route("/")
    def index():
        return Response(page, mimetype="text/html")

    @app.route("/shared/<path:f>")
    def shared(f):
        return send_from_directory(os.path.join(ROOT, "shared"), f)

    @app.route("/healthz")
    def healthz():
        return {"ok": True, "demo": "hub"}

    return app


def build_apps():
    demo_a = _load_module(
        "demo_a", os.path.join(ROOT, "demo-a-two-codes", "poll", "poll_server.py"))
    demo_c = _load_module(
        "demo_c", os.path.join(ROOT, "demo-c-dynamic-switch", "server", "redirector.py"))

    demo_b = static_app(os.path.join(ROOT, "demo-b-preview-defeat"), {
        "/": "index.html",
        "/gotcha": "gotcha.html",
    }, "demo-b")

    demo_e = static_app(os.path.join(ROOT, "demo-e-wifi-reveal"), {
        "/": "stage.html",
        "/portal": "portal.html",
    }, "demo-e")

    return {
        "hub": (config.PORTS["hub"], hub_app(), 4),
        "a":   (config.PORTS["a"],   demo_a.app, 8),   # SSE: extra threads
        "b":   (config.PORTS["b"],   demo_b, 4),
        "c":   (config.PORTS["c"],   demo_c.app, 6),
        "d":   (config.PORTS["d"],   demo_d_app(), 4),
        "e":   (config.PORTS["e"],   demo_e, 4),
    }


def _serve(port, app, threads):
    serve(app, host="0.0.0.0", port=port, threads=threads,
          channel_timeout=300, ident="qr-quishing-demos")


def main():
    if os.environ.get("REGEN_ASSETS", "1") != "0":
        import generate_assets
        generate_assets.main()

    apps = build_apps()
    print("Serving demos:")
    threads = []
    for key, (port, app, nthreads) in apps.items():
        print(f"  {key:4} -> http://0.0.0.0:{port}  ({config.PUBLIC[key]})")
        t = threading.Thread(target=_serve, args=(port, app, nthreads), daemon=True)
        t.start()
        threads.append(t)

    # Block forever; daemon threads run the servers.
    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("\nshutting down")


if __name__ == "__main__":
    main()
