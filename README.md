# QR Code Security ("Quishing") — Live Demo Kit

Buildable, **safe** demos for a main-stage talk on QR code security. Everything
here runs on **your own domains and infrastructure**. The point of every demo is
the *perception gap* — "I couldn't tell, and neither could you" — never device
exploitation.

> **A QR code is data, not code. It executes nothing.** Any real device
> compromise needs a *separate* bug in whatever parses the payload. QR just
> removes friction. These demos show *capability* and *perception*; none of them
> fakes a compromise, captures a credential, or intercepts traffic.

---

## The five demos

| | Demo | Point | Backend? |
|---|---|---|---|
| **A** ⭐ | [Two identical codes](demo-a-two-codes/) | Nobody can tell a safe QR from a malicious one | Optional (live poll) |
| **B** | [URL-preview defeat](demo-b-preview-defeat/) | You can catch a lookalike domain typed — not as a QR | No |
| **C** ⭐ | [Dynamic-QR switch](demo-c-dynamic-switch/) | The sticker can change *after* you inspected it | Yes (Flask) |
| **D** | [Quishing-in-PDF](demo-d-pdf-quishing/) | Why the email filter didn't catch it | Build step |
| **E** | [Wi-Fi join reveal](demo-e-wifi-reveal/) | A QR can join your phone to a network with no click | AP + static page |

**Priority order to build/run:** A → C → B → D → E. If your slot is tight,
**A + C alone carry the talk.**

---

## Quick start

```bash
# 1. Install backend deps (for Demo C, Demo D, and Demo A's optional poll)
pip install -r requirements.txt

# 2. Point everything at your own domain: edit shared/config.py, then
python generate_assets.py        # regenerates every QR + the demo PDF
```

`shared/config.py` is the **single source of truth**. Every QR and page is
generated from it, so re-pointing the whole talk at your real infrastructure is
a one-file edit followed by one command.

### Run each demo

- **A — projector slide (no backend):** open `demo-a-two-codes/stage.html`.
  Press <kbd>R</kbd>/<kbd>Space</kbd> to reveal after the vote.
- **A — optional live poll:**
  ```bash
  cd demo-a-two-codes/poll && python poll_server.py
  # projector: http://<laptop-ip>:5000/   ·   phones: http://<laptop-ip>:5000/vote
  ```
  Speaker keys on the projector: <kbd>R</kbd> reveal, <kbd>0</kbd> reset.
- **B — no backend:** open `demo-b-preview-defeat/index.html`. <kbd>R</kbd>
  exposes the homoglyph, <kbd>Q</kbd> toggles URL ↔ QR.
- **C — redirector + admin toggle:**
  ```bash
  cd demo-c-dynamic-switch/server && ADMIN_TOKEN=yoursecret python redirector.py
  # audience/QR: http://<laptop-ip>:5001/go/demo1
  # speaker:     http://<laptop-ip>:5001/admin?token=yoursecret
  ```
  Scan → benign page. Tap the swap on your phone → rescan the *same code* →
  different page. Runs fully self-contained; set `USE_LOCAL_LANDINGS=0` to
  redirect to the absolute URLs in your config instead.
- **D — build the PDF:** `python demo-d-pdf-quishing/make_pdf.py` →
  `demo-d-pdf-quishing/assets/invoice-quishing.pdf`. The destination URL exists
  **only inside the QR image**, never as text — run it through a public
  link-reputation checker live to show it comes back clean.
- **E — Wi-Fi reveal:** display `demo-e-wifi-reveal/stage.html`; see
  [`demo-e-wifi-reveal/SETUP.md`](demo-e-wifi-reveal/SETUP.md) for the AP +
  captive-portal wiring. `portal.html` is the reveal page.

---

## Repo layout

```
├── shared/
│   ├── config.py              # single source of truth — edit this
│   ├── landing.css            # shared projector-legible styling
│   └── qrgen/qrgen.py         # QR + WIFI-payload generator (importable + CLI)
├── generate_assets.py         # regenerate every QR and the PDF from config
├── requirements.txt
├── demo-a-two-codes/          # stage slide, reveal, landing pages, live poll
├── demo-b-preview-defeat/     # single page, URL ↔ QR toggle + homoglyph reveal
├── demo-c-dynamic-switch/     # Flask redirector + JSON store + admin toggle
├── demo-d-pdf-quishing/       # reportlab PDF with QR trapped in an image
└── demo-e-wifi-reveal/        # join QR + captive-portal reveal page
```

Generate a one-off QR from the CLI:

```bash
python shared/qrgen/qrgen.py "https://you.example/x" out.png
python shared/qrgen/qrgen.py --wifi --ssid MyAP --auth WPA --password pw wifi.png
```

---

## Guardrails (keep it clean)

- **Every destination is a domain you own.** Defaults are RFC-reserved
  `*.example` placeholders that resolve nowhere. Register the Demo B lookalike
  yourself before the talk so nothing points at a real brand.
- **No credential capture, ever.** Landing pages *state* what would have
  happened; they don't do it.
- **The Wi-Fi demo terminates at a reveal page.** No traffic interception is
  built — don't add any.
- **Everything is labeled awareness/education material**, including the decoy
  PDF.
- **Rehearse C and E on the actual venue network** — captive portals and
  conference Wi-Fi are where live demos die.

The narrative brief this kit was built from lives in
[`docs/talk-brief.md`](docs/talk-brief.md).
