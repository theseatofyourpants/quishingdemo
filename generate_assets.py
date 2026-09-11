#!/usr/bin/env python3
"""Regenerate every QR image across all demos from `shared/config.py`.

Run this once after editing the config (e.g. to point the demos at your real
domain). It is idempotent — safe to run repeatedly.

    python generate_assets.py

The PDF for Demo D is built by `demo-d-pdf-quishing/make_pdf.py`, which this
script invokes so a single command produces every artifact.
"""

import os
import subprocess
import sys

# Make `shared` importable when run from the repo root.
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from shared import config
from shared.qrgen.qrgen import make_qr, wifi_payload


def gen_demo_a():
    a = config.DEMO_A
    # Two codes, different destinations, visually the same weight/size. That
    # indistinguishability IS the demo — do not style them differently.
    # Each encodes a scan-counting hop (/s/a, /s/b) so scanning either code
    # casts a live-poll vote before landing on its reveal page.
    make_qr(a["scan_safe_url"], "demo-a-two-codes/assets/code-left.png")
    make_qr(a["scan_malicious_url"], "demo-a-two-codes/assets/code-right.png")
    print("  Demo A: code-left.png (safe), code-right.png (malicious)")


def gen_demo_b():
    b = config.DEMO_B
    make_qr(b["lookalike_url"], "demo-b-preview-defeat/assets/lookalike.png")
    print("  Demo B: lookalike.png")


def gen_demo_c():
    c = config.DEMO_C
    # ONE stable code. Its destination is flipped server-side, not re-encoded.
    make_qr(c["redirect_url"], "demo-c-dynamic-switch/assets/redirector.png",
            error_correction="Q")
    print(f"  Demo C: redirector.png -> {c['redirect_url']}")


def gen_demo_d():
    # Also emit a standalone preview of the PDF's QR, then build the PDF.
    make_qr(config.DEMO_D["pdf_target_url"],
            "demo-d-pdf-quishing/assets/pdf-qr.png")
    print("  Demo D: pdf-qr.png")
    script = os.path.join(ROOT, "demo-d-pdf-quishing", "make_pdf.py")
    if os.path.exists(script):
        subprocess.run([sys.executable, script], check=True)


def gen_demo_e():
    e = config.DEMO_E
    payload = wifi_payload(e["ssid"], e["auth"], e["password"], e["hidden"])
    make_qr(payload, "demo-e-wifi-reveal/assets/wifi.png", error_correction="Q")
    print(f"  Demo E: wifi.png -> SSID '{e['ssid']}'")


def main():
    os.chdir(ROOT)
    print("Regenerating QR assets from shared/config.py ...")
    gen_demo_a()
    gen_demo_b()
    gen_demo_c()
    gen_demo_d()
    gen_demo_e()
    print("Done.")


if __name__ == "__main__":
    main()
