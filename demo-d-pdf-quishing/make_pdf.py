#!/usr/bin/env python3
"""Demo D — quishing-in-PDF.

Builds a phishing-style decoy PDF whose call-to-action is a QR *image*. Because
the destination URL lives inside a rasterized QR — not as selectable text or a
link annotation — email link scanners and URL-reputation filters never see it.
That's the point: "this is why your filter didn't catch it."

The QR points at the speaker's own harmless page (shared/config.DEMO_D). No real
brand, no real invoice, no credential capture.

Run:
    pip install -r ../../requirements.txt
    python make_pdf.py                 # -> assets/invoice-quishing.pdf
"""

import os
import sys

# Deterministic output: fixed creation date + document ID, so regenerating the
# PDF from the same config produces byte-identical output (no git churn, and CI
# can rebuild it without changing tracked bytes). Must be set BEFORE importing
# reportlab.pdfgen.canvas, which reads these values at import time.
from reportlab import rl_config                    # noqa: E402

rl_config.invariant = 1

from reportlab.lib.colors import HexColor          # noqa: E402
from reportlab.lib.pagesizes import LETTER         # noqa: E402
from reportlab.lib.units import inch               # noqa: E402
from reportlab.pdfgen import canvas                # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, ROOT)
from shared import config              # noqa: E402
from shared.qrgen.qrgen import make_qr  # noqa: E402

ASSETS = os.path.join(HERE, "assets")
QR_PNG = os.path.join(ASSETS, "pdf-qr.png")
OUT_PDF = os.path.join(ASSETS, "invoice-quishing.pdf")

INK = HexColor("#1a2233")
MUTED = HexColor("#6b7280")
RULE = HexColor("#d1d5db")
ACCENT = HexColor("#1d4ed8")
BANNER = HexColor("#f3f4f6")


def build():
    os.makedirs(ASSETS, exist_ok=True)
    d = config.DEMO_D
    make_qr(d["pdf_target_url"], QR_PNG, box_size=10, border=2)

    c = canvas.Canvas(OUT_PDF, pagesize=LETTER)
    w, h = LETTER

    # Header band
    c.setFillColor(BANNER)
    c.rect(0, h - 1.3 * inch, w, 1.3 * inch, stroke=0, fill=1)
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(0.9 * inch, h - 0.85 * inch, d["from_org"])
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 10)
    c.drawString(0.9 * inch, h - 1.08 * inch, d["from_name"] + " · Automated billing notice")

    # Subject / body
    y = h - 1.9 * inch
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 15)
    c.drawString(0.9 * inch, y, d["subject"])

    y -= 0.45 * inch
    c.setFont("Helvetica", 11)
    body = [
        "Our records show an outstanding balance associated with your account.",
        "To avoid a late fee and service interruption, please review and settle",
        "the invoice below within 48 hours.",
        "",
        "For your convenience, scan the secure payment code with your phone",
        "camera to open the payment portal. No login link is included in this",
        "message for your security.",
    ]
    for line in body:
        c.drawString(0.9 * inch, y, line)
        y -= 0.26 * inch

    # Fake invoice line items box
    y -= 0.1 * inch
    box_top = y
    c.setStrokeColor(RULE)
    c.setLineWidth(1)
    rows = [
        ("Description", "Amount"),
        ("Vendor services — Q2 facilities", "$1,284.00"),
        ("Late processing adjustment", "$45.00"),
        ("Total due", "$1,329.00"),
    ]
    row_h = 0.34 * inch
    box_h = row_h * len(rows)
    c.rect(0.9 * inch, box_top - box_h, w - 1.8 * inch, box_h, stroke=1, fill=0)
    for i, (a, b) in enumerate(rows):
        ry = box_top - (i + 1) * row_h + 0.09 * inch
        if i == 0:
            c.setFont("Helvetica-Bold", 10)
            c.setFillColor(MUTED)
        elif i == len(rows) - 1:
            c.setFont("Helvetica-Bold", 11)
            c.setFillColor(INK)
        else:
            c.setFont("Helvetica", 11)
            c.setFillColor(INK)
        c.drawString(1.05 * inch, ry, a)
        c.drawRightString(w - 1.05 * inch, ry, b)
        if i < len(rows) - 1:
            c.setStrokeColor(RULE)
            c.line(0.9 * inch, box_top - (i + 1) * row_h,
                   w - 0.9 * inch, box_top - (i + 1) * row_h)

    # The QR call-to-action — the whole trick. URL is inside this image only.
    qr_size = 1.9 * inch
    qr_x = (w - qr_size) / 2
    qr_y = box_top - box_h - qr_size - 0.7 * inch
    c.drawImage(QR_PNG, qr_x, qr_y, qr_size, qr_size,
                preserveAspectRatio=True, mask="auto")
    c.setFillColor(ACCENT)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(w / 2, qr_y - 0.28 * inch, "Scan to pay securely")
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    c.drawCentredString(w / 2, qr_y - 0.5 * inch,
                        "The payment link is embedded in the code above and is not shown as text.")

    # Honesty footer so the artifact can never be mistaken for a real lure
    c.setFillColor(MUTED)
    c.setFont("Helvetica-Oblique", 8)
    # NOTE: the destination URL is deliberately NOT written as text anywhere in
    # this PDF — only inside the QR image — so a link/URL scanner has nothing to
    # find. That is the demo. (The address is in shared/config.py if you need it.)
    c.drawCentredString(
        w / 2, 0.6 * inch,
        "AWARENESS / EDUCATION DEMO. The QR points to the speaker's own harmless page. "
        "No real invoice, brand, or payment is involved.")

    c.showPage()
    c.save()
    print(f"  Demo D: wrote {os.path.relpath(OUT_PDF, ROOT)} "
          f"(QR -> {d['pdf_target_url']}, not present as text)")


if __name__ == "__main__":
    build()
