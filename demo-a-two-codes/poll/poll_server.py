#!/usr/bin/env python3
"""Demo A — full app: the two-codes stage slide plus the optional live poll.

Serves everything Demo A needs on one port:
    /                stage slide (both codes, keyboard reveal)
    /stage           same
    /your-bank.html      reveal landing for the "safe" code (QR target)
    /not-your-bank.html  reveal landing for the "malicious" code (QR target)
    /assets/<f>      the QR images
    /poll            live-poll projector view (animated tally)
    /vote            phone voting page
    /api/vote        POST {"choice":"a"|"b"}
    /api/reset       POST
    /api/reveal      POST
    /stream          Server-Sent Events feed of the live tally
    /shared/<f>      shared landing.css

The poll uses SSE (no websocket dependency). Vote state is in-memory — this is a
single-process live demo, not a service.

Standalone:
    python poll_server.py            # http://<ip>:5000/
"""

import json
import os
import queue
import threading

from flask import (Flask, Response, request, send_from_directory)

HERE = os.path.dirname(os.path.abspath(__file__))          # .../poll
DEMO_DIR = os.path.abspath(os.path.join(HERE, ".."))       # .../demo-a-two-codes
ROOT = os.path.abspath(os.path.join(DEMO_DIR, ".."))       # repo root
SHARED_DIR = os.path.join(ROOT, "shared")

# ---- shared state ---------------------------------------------------------
_lock = threading.Lock()
_tally = {"a": 0, "b": 0}
_revealed = False
_subscribers: "set[queue.Queue]" = set()


def _snapshot():
    with _lock:
        return {"tally": dict(_tally), "revealed": _revealed}


def _broadcast():
    payload = _snapshot()
    dead = []
    for q in list(_subscribers):
        try:
            q.put_nowait(payload)
        except Exception:
            dead.append(q)
    for q in dead:
        _subscribers.discard(q)


def create_app():
    app = Flask(__name__)

    # ---- stage + landing pages -------------------------------------------
    @app.route("/")
    @app.route("/stage")
    def stage():
        return send_from_directory(DEMO_DIR, "stage.html")

    @app.route("/your-bank.html")
    def safe_landing():
        return send_from_directory(DEMO_DIR, "your-bank.html")

    @app.route("/not-your-bank.html")
    def malicious_landing():
        return send_from_directory(DEMO_DIR, "not-your-bank.html")

    @app.route("/assets/<path:f>")
    def assets(f):
        return send_from_directory(os.path.join(DEMO_DIR, "assets"), f)

    @app.route("/shared/<path:f>")
    def shared(f):
        return send_from_directory(SHARED_DIR, f)

    # ---- poll pages ------------------------------------------------------
    @app.route("/poll")
    def projector():
        return send_from_directory(HERE, "projector.html")

    @app.route("/vote")
    def vote_page():
        return send_from_directory(HERE, "vote.html")

    # ---- poll api --------------------------------------------------------
    @app.route("/api/vote", methods=["POST"])
    def api_vote():
        data = request.get_json(silent=True) or request.form
        choice = (data.get("choice") or "").lower()
        if choice not in ("a", "b"):
            return {"error": "choice must be 'a' or 'b'"}, 400
        with _lock:
            _tally[choice] += 1
        _broadcast()
        return {"ok": True}

    @app.route("/api/reset", methods=["POST"])
    def api_reset():
        global _revealed
        with _lock:
            _tally["a"] = 0
            _tally["b"] = 0
            _revealed = False
        _broadcast()
        return {"ok": True}

    @app.route("/api/reveal", methods=["POST"])
    def api_reveal():
        global _revealed
        with _lock:
            _revealed = True
        _broadcast()
        return {"ok": True}

    @app.route("/stream")
    def stream():
        def gen():
            q: "queue.Queue" = queue.Queue()
            _subscribers.add(q)
            q.put_nowait(_snapshot())
            try:
                while True:
                    try:
                        payload = q.get(timeout=15)
                        yield f"data: {json.dumps(payload)}\n\n"
                    except queue.Empty:
                        yield ": keepalive\n\n"
            finally:
                _subscribers.discard(q)

        return Response(gen(), mimetype="text/event-stream",
                        headers={"Cache-Control": "no-cache",
                                 "X-Accel-Buffering": "no"})

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True, debug=False)
