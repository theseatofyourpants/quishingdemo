#!/usr/bin/env python3
"""Demo C — dynamic-QR redirector.

The physical QR encodes ONE stable URL: /go/<slug>. The destination behind that
slug is flipped mid-demo from the admin toggle, WITHOUT re-printing the code.
That is the whole point: "the sticker you inspected can change after you walk
away."

Runs fully self-contained on one laptop:
    pip install -r ../../requirements.txt
    ADMIN_TOKEN=letmein python redirector.py
    # QR / audience:  http://<laptop-ip>:5001/go/demo1
    # speaker admin:   http://<laptop-ip>:5001/admin?token=letmein

State (which target each slug currently points to) persists in state.json next
to this file, so a crash mid-talk doesn't lose your toggle position.

Set USE_LOCAL_LANDINGS=0 to redirect to the absolute URLs in shared/config.py
(your real demo domain) instead of the built-in local landing pages.
"""

import json
import os
import sys

from flask import (Flask, Response, abort, redirect, request,
                   send_from_directory)

# Make `shared` importable when run from anywhere in the repo.
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
from shared import config  # noqa: E402

app = Flask(__name__)

STATE_PATH = os.path.join(HERE, "state.json")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "changeme")
USE_LOCAL_LANDINGS = os.environ.get("USE_LOCAL_LANDINGS", "1") != "0"
LANDINGS_DIR = os.path.abspath(os.path.join(HERE, "..", "assets"))
ADMIN_DIR = os.path.abspath(os.path.join(HERE, "..", "admin"))

SLUG = config.DEMO_C["slug"]
TARGET_KEYS = list(config.DEMO_C["targets"].keys())  # e.g. ["benign", "swapped"]


# ---- persistent state -----------------------------------------------------
def _load_state():
    try:
        with open(STATE_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {SLUG: config.DEMO_C["default_target"]}


def _save_state(state):
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, STATE_PATH)


def _target_url(key: str) -> str:
    if USE_LOCAL_LANDINGS:
        return f"/land/{key}"
    return config.DEMO_C["targets"][key]


def _require_token():
    token = request.args.get("token") or request.headers.get("X-Admin-Token")
    if token != ADMIN_TOKEN:
        abort(403)


# ---- the redirector (what the QR hits) ------------------------------------
@app.route("/go/<slug>")
def go(slug):
    state = _load_state()
    key = state.get(slug)
    if key is None or key not in config.DEMO_C["targets"]:
        abort(404)
    # 302 (temporary) so nothing caches the destination — it changes on us.
    resp = redirect(_target_url(key), code=302)
    resp.headers["Cache-Control"] = "no-store, must-revalidate"
    return resp


# ---- local landing pages (self-contained rehearsal) -----------------------
@app.route("/land/<key>")
def land(key):
    if key not in config.DEMO_C["targets"]:
        abort(404)
    return send_from_directory(LANDINGS_DIR, f"{key}.html")


@app.route("/shared/<path:p>")
def shared_static(p):
    # Serves shared/landing.css so the landing pages look right whether they're
    # opened as a local file OR served here at /land/<key>.
    return send_from_directory(os.path.join(ROOT, "shared"), p)


# ---- admin toggle ---------------------------------------------------------
@app.route("/admin")
def admin_page():
    _require_token()
    return send_from_directory(ADMIN_DIR, "admin.html")


@app.route("/admin/state")
def admin_state():
    _require_token()
    state = _load_state()
    key = state.get(SLUG, config.DEMO_C["default_target"])
    return {"slug": SLUG, "current": key, "targets": TARGET_KEYS,
            "url": _target_url(key)}


@app.route("/admin/set", methods=["POST"])
def admin_set():
    _require_token()
    data = request.get_json(silent=True) or request.form
    key = data.get("target")
    if key not in config.DEMO_C["targets"]:
        return {"error": f"target must be one of {TARGET_KEYS}"}, 400
    state = _load_state()
    state[SLUG] = key
    _save_state(state)
    return {"ok": True, "current": key}


@app.route("/")
def index():
    return Response(
        "Demo C redirector is running.\n"
        f"  audience/QR : /go/{SLUG}\n"
        "  speaker     : /admin?token=***\n",
        mimetype="text/plain")


if __name__ == "__main__":
    if ADMIN_TOKEN == "changeme":
        print("WARNING: using default ADMIN_TOKEN='changeme'. "
              "Set ADMIN_TOKEN=... before the talk.", file=sys.stderr)
    app.run(host="0.0.0.0", port=5001, threaded=True, debug=False)
