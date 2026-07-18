"""QR generation helper shared by every demo.

Importable API:
    from shared.qrgen.qrgen import make_qr, wifi_payload

    make_qr("https://example.com", "out.png")          # PNG
    make_qr("https://example.com", "out.svg")          # SVG (format inferred)
    wifi_payload("MyAP", "WPA", "hunter2")             # WIFI:...;; string

CLI:
    python shared/qrgen/qrgen.py "https://example.com" out.png
    python shared/qrgen/qrgen.py --wifi --ssid MyAP --auth WPA --password pw out.png

The QR itself is *data, not code* — it executes nothing. It just removes the
"read the URL first" friction. That honesty is the whole point of the talk.
"""

from __future__ import annotations

import argparse
import os

import qrcode
from qrcode.image.svg import SvgPathImage


def _escape_wifi(value: str) -> str:
    """Escape special chars per the WIFI: URI convention."""
    for ch in ("\\", ";", ",", ":", '"'):
        value = value.replace(ch, "\\" + ch)
    return value


def wifi_payload(ssid: str, auth: str = "WPA", password: str = "",
                 hidden: bool = False) -> str:
    """Build a standard WIFI: join payload that phones auto-parse.

    Format: WIFI:T:<auth>;S:<ssid>;P:<password>;H:<true|false>;;
    auth is WPA, WEP, or nopass.
    """
    auth = auth.upper() if auth.lower() != "nopass" else "nopass"
    parts = [f"T:{auth}", f"S:{_escape_wifi(ssid)}"]
    if auth != "nopass":
        parts.append(f"P:{_escape_wifi(password)}")
    if hidden:
        parts.append("H:true")
    return "WIFI:" + ";".join(parts) + ";;"


def make_qr(data: str, out_path: str, *, box_size: int = 16, border: int = 2,
            error_correction: str = "M") -> str:
    """Render `data` to a QR image at `out_path`. Format inferred from extension.

    High-contrast black-on-white, chunky modules — legible from the back row and
    reliable for a phone camera on a projector. Returns the path written.
    """
    ec_map = {
        "L": qrcode.constants.ERROR_CORRECT_L,
        "M": qrcode.constants.ERROR_CORRECT_M,
        "Q": qrcode.constants.ERROR_CORRECT_Q,
        "H": qrcode.constants.ERROR_CORRECT_H,
    }
    ext = os.path.splitext(out_path)[1].lower()
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)

    qr = qrcode.QRCode(
        version=None,  # auto-size to fit the data
        error_correction=ec_map.get(error_correction.upper(),
                                    qrcode.constants.ERROR_CORRECT_M),
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    if ext == ".svg":
        img = qr.make_image(image_factory=SvgPathImage)
    else:
        img = qr.make_image(fill_color="black", back_color="white")
    img.save(out_path)
    return out_path


def _main() -> None:
    p = argparse.ArgumentParser(description="Generate a QR code (PNG or SVG).")
    p.add_argument("data", nargs="?", help="URL or text to encode (omit with --wifi)")
    p.add_argument("out", help="Output path; .svg or .png inferred from extension")
    p.add_argument("--box-size", type=int, default=16)
    p.add_argument("--border", type=int, default=2)
    p.add_argument("--ec", default="M", choices=["L", "M", "Q", "H"],
                   help="Error correction level")
    p.add_argument("--wifi", action="store_true", help="Build a WIFI: join payload")
    p.add_argument("--ssid")
    p.add_argument("--auth", default="WPA", help="WPA | WEP | nopass")
    p.add_argument("--password", default="")
    p.add_argument("--hidden", action="store_true")
    args = p.parse_args()

    if args.wifi:
        if not args.ssid:
            p.error("--wifi requires --ssid")
        data = wifi_payload(args.ssid, args.auth, args.password, args.hidden)
    else:
        if not args.data:
            p.error("provide DATA to encode, or use --wifi")
        data = args.data

    path = make_qr(data, args.out, box_size=args.box_size, border=args.border,
                   error_correction=args.ec)
    print(f"wrote {path}  ({len(data)} bytes encoded)")


if __name__ == "__main__":
    _main()
