#!/usr/bin/env python3
"""Optional live poll for Demo A.

The audience votes A vs B from their phones; the projector page animates the
tally in real time via Server-Sent Events (no websocket library needed, so the
only dependency is Flask). Vote state is in-memory — this is a single-process
live demo, not a service.

Run:
    pip install -r ../../requirements.txt
    python poll_server.py
    # projector:  http://<your-laptop-ip>:5000/
    # phones:     http://<your-laptop-ip>:5000/vote   (or scan the QR the
    #             projector shows)

Routes:
    /            projector view (animated bars)
    /vote        phone voting page
    /api/vote    POST {"choice": "a"|"b"}   register a vote
    /api/reset   POST                        zero the tally
    /api/reveal  POST                        push a "reveal" event to projector
    /stream      Server-Sent Events feed of the live tally
"""

import json
import os
import queue
import threading

from flask import Flask, Response, request, send_from_directory

app = Flask(__name__)

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- shared state ---------------------------------------------------------
_lock = threading.Lock()
_tally = {"a": 0, "b": 0}
_revealed = False
_subscribers: "set[queue.Queue]" = set()


def _snapshot():
    with _lock:
        return {"tally": dict(_tally), "revealed": _revealed}


def _broadcast():
    """Push the current snapshot to every connected projector."""
    payload = _snapshot()
    dead = []
    for q in list(_subscribers):
        try:
            q.put_nowait(payload)
        except Exception:
            dead.append(q)
    for q in dead:
        _subscribers.discard(q)


# ---- pages ----------------------------------------------------------------
@app.route("/")
def projector():
    return send_from_directory(HERE, "projector.html")


@app.route("/vote")
def vote_page():
    return send_from_directory(HERE, "vote.html")


# ---- api ------------------------------------------------------------------
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
        # Send the current state immediately on connect.
        q.put_nowait(_snapshot())
        try:
            while True:
                try:
                    payload = q.get(timeout=15)
                    yield f"data: {json.dumps(payload)}\n\n"
                except queue.Empty:
                    # Heartbeat comment keeps proxies from closing the stream.
                    yield ": keepalive\n\n"
        finally:
            _subscribers.discard(q)

    return Response(gen(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache",
                             "X-Accel-Buffering": "no"})


if __name__ == "__main__":
    # threaded=True so SSE streams don't block votes.
    app.run(host="0.0.0.0", port=5000, threaded=True, debug=False)
