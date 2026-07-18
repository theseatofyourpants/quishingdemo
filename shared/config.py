"""Central configuration for all QR quishing demos.

Every QR code and landing page is generated from the values here, so the whole
talk can be re-pointed at your real infrastructure with environment variables
(or by editing the defaults below) and re-running `python generate_assets.py`.

Deployment model
----------------
Each demo is served on its own port in the 10000 range and exposed publicly
through a Cloudflare tunnel hostname. Because a QR must encode a *reachable*
URL, set `PUBLIC_A`..`PUBLIC_E` to the public hostnames your tunnel maps to each
demo. Locally they default to `http://localhost:1000X` so `docker run` works out
of the box for testing.

GUARDRAIL: every destination MUST be a domain you own. The homograph display
strings in DEMO_B use RFC-6761 reserved `*.example` names that resolve nowhere;
register a real lookalike yourself before the talk. See docs/talk-brief.md §7.
"""

import os


def _env(name, default):
    return os.environ.get(name, default)


def _flag(name, default=False):
    return os.environ.get(name, str(default)).lower() in ("1", "true", "yes", "on")


# ---------------------------------------------------------------------------
# Ports each demo listens on (inside the container). The hub index sits on the
# base port; demos A–E take the next five.
# ---------------------------------------------------------------------------
PORTS = {
    "hub": int(_env("PORT_HUB", "10000")),
    "a":   int(_env("PORT_A", "10001")),
    "b":   int(_env("PORT_B", "10002")),
    "c":   int(_env("PORT_C", "10003")),
    "d":   int(_env("PORT_D", "10004")),
    "e":   int(_env("PORT_E", "10005")),
}

# ---------------------------------------------------------------------------
# Public base URLs. Behind a Cloudflare tunnel, set each to the hostname the
# tunnel maps to that demo's port, e.g. https://qr-a.yourdomain.com
# ---------------------------------------------------------------------------
PUBLIC = {
    "hub": _env("PUBLIC_HUB", f"http://localhost:{PORTS['hub']}"),
    "a":   _env("PUBLIC_A",   f"http://localhost:{PORTS['a']}"),
    "b":   _env("PUBLIC_B",   f"http://localhost:{PORTS['b']}"),
    "c":   _env("PUBLIC_C",   f"http://localhost:{PORTS['c']}"),
    "d":   _env("PUBLIC_D",   f"http://localhost:{PORTS['d']}"),
    "e":   _env("PUBLIC_E",   f"http://localhost:{PORTS['e']}"),
}


def _base(key):
    return PUBLIC[key].rstrip("/")


# Shared secret protecting the Demo C admin toggle.
ADMIN_TOKEN = _env("ADMIN_TOKEN", "changeme")


# ---------------------------------------------------------------------------
# Demo A — two visually indistinguishable codes. Both resolve to landing pages
# YOU control (served on Demo A's own port). Nothing touches a real bank.
# ---------------------------------------------------------------------------
DEMO_A = {
    "safe_url": f"{_base('a')}/your-bank.html",
    "malicious_url": f"{_base('a')}/not-your-bank.html",
}


# ---------------------------------------------------------------------------
# Demo B — URL-preview defeat via a homograph / lookalike domain. The visible
# URL uses a Cyrillic 'а' (U+0430) in place of Latin 'a'. Register a real
# lookalike yourself before the talk; the QR points at a reveal page you own.
# ---------------------------------------------------------------------------
DEMO_B = {
    "legit_display": "your-bank.example",
    # 4th character is Cyrillic small 'а' (U+0430), not Latin 'a' (U+0061).
    "lookalike_display": "your-bаnk.example",
    "lookalike_url": f"{_base('b')}/gotcha",
}


# ---------------------------------------------------------------------------
# Demo C — dynamic-QR switch. The QR encodes ONE stable redirector URL; the
# destination behind the slug is flipped server-side from the admin toggle.
# ---------------------------------------------------------------------------
DEMO_C = {
    "redirect_url": f"{_base('c')}/go/demo1",
    "slug": "demo1",
    "targets": {
        "benign": f"{_base('c')}/land/benign",
        "swapped": f"{_base('c')}/land/swapped",
    },
    "default_target": "benign",
}


# ---------------------------------------------------------------------------
# Demo D — quishing-in-PDF. The QR lives inside an image so email link scanners
# never see the URL as text. It points at a reveal page on Demo D's port.
# ---------------------------------------------------------------------------
DEMO_D = {
    "pdf_target_url": f"{_base('d')}/invoice",
    "from_name": _env("DEMO_D_FROM_NAME", "Accounts Payable"),
    "from_org": _env("DEMO_D_FROM_ORG", "Facilities & Vendor Services"),
    "subject": _env("DEMO_D_SUBJECT",
                    "Action required: outstanding invoice #INV-20487"),
}


# ---------------------------------------------------------------------------
# Demo E — Wi-Fi join reveal. QR encodes standard WIFI: credentials for YOUR
# OWN access point. The landing page only *states* what interception would do.
# ---------------------------------------------------------------------------
DEMO_E = {
    "ssid": _env("WIFI_SSID", "Conference_Free_WiFi"),
    "auth": _env("WIFI_AUTH", "WPA"),          # WPA | WEP | nopass
    "password": _env("WIFI_PASSWORD", "letmein-demo-2026"),
    "hidden": _flag("WIFI_HIDDEN", False),
}
