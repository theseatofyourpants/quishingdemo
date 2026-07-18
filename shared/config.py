"""Central configuration for all QR quishing demos.

Every QR code and landing page is generated from the values here, so the whole
talk can be re-pointed at your real infrastructure by editing ONE file and
re-running `python generate_assets.py`.

GUARDRAIL: every destination below MUST be a domain you own. The defaults are
RFC-6761 reserved placeholders (`*.example`) that resolve nowhere. Register the
lookalike domain in DEMO_B yourself ahead of time so nothing ever points at a
real brand. See section 7 of the talk brief.
"""

# ---------------------------------------------------------------------------
# The domain you control for the talk. Replace with your real demo domain.
# ---------------------------------------------------------------------------
BASE_DOMAIN = "quishing.example"

# The short redirector host for the dynamic-switch demo (Demo C). This is the
# host printed on the physical sticker, so keep it short and stable.
REDIRECTOR_HOST = "go.quishing.example"


# ---------------------------------------------------------------------------
# Demo A — two visually indistinguishable codes.
# Both resolve to landing pages YOU control. Nothing here touches a real bank.
# ---------------------------------------------------------------------------
DEMO_A = {
    # Shown as "you'd have gone to your bank" on reveal.
    "safe_url": f"https://{BASE_DOMAIN}/a/your-bank",
    # Shown as "you'd have gone to definitely-not-your-bank" on reveal.
    "malicious_url": f"https://{BASE_DOMAIN}/a/not-your-bank",
}


# ---------------------------------------------------------------------------
# Demo B — URL-preview defeat via a homograph / lookalike domain.
# The visible URL uses a Cyrillic 'а' (U+0430) in place of Latin 'a'. A human
# reading the URL can be taught to spot it; nobody can spot it inside a QR.
# Register this exact lookalike yourself before the talk.
# ---------------------------------------------------------------------------
DEMO_B = {
    # Latin baseline the crowd expects to see.
    "legit_display": "your-bank.example",
    # The lookalike. The 4th character is Cyrillic small 'а' (U+0430), not
    # Latin 'a' (U+0061). Rendered, they are nearly identical.
    "lookalike_display": "your-bаnk.example",
    # Where the lookalike QR actually points (a page you own that reveals the trick).
    "lookalike_url": f"https://{BASE_DOMAIN}/b/gotcha",
}


# ---------------------------------------------------------------------------
# Demo C — dynamic-QR switch. The QR encodes ONE stable redirector URL. The
# destination behind the slug is flipped server-side from the admin toggle.
# ---------------------------------------------------------------------------
DEMO_C = {
    # The stable URL printed on the sticker / slide. Never changes.
    "redirect_url": f"https://{REDIRECTOR_HOST}/go/demo1",
    "slug": "demo1",
    # The two destinations the admin can flip between mid-demo.
    "targets": {
        "benign": f"https://{BASE_DOMAIN}/c/benign",
        "swapped": f"https://{BASE_DOMAIN}/c/swapped",
    },
    # Destination the redirector starts on when the server boots.
    "default_target": "benign",
}


# ---------------------------------------------------------------------------
# Demo D — quishing-in-PDF. The QR lives inside an image in the PDF so email
# link scanners never see the URL as text.
# ---------------------------------------------------------------------------
DEMO_D = {
    "pdf_target_url": f"https://{BASE_DOMAIN}/d/invoice",
    # Cosmetic sender details for the decoy document. All fictitious.
    "from_name": "Accounts Payable",
    "from_org": "Facilities & Vendor Services",
    "subject": "Action required: outstanding invoice #INV-20487",
}


# ---------------------------------------------------------------------------
# Demo E — Wi-Fi join reveal. QR encodes standard WIFI: credentials for YOUR
# OWN access point. The landing page only *states* what interception would do.
# ---------------------------------------------------------------------------
DEMO_E = {
    "ssid": "Conference_Free_WiFi",
    "auth": "WPA",          # WPA | WEP | nopass
    "password": "letmein-demo-2026",
    "hidden": False,
}
