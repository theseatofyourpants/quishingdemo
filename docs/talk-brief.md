# QR Code Security ("Quishing") — Main Stage Talk + Demo Build Spec

> Working brief for a 10,000-attendee conference main stage talk on QR code
> security, plus buildable specs for five safe, high-impact live demos.
> All demos run on **your own infrastructure and domains** — the whole point
> is the *perception gap*, not device exploitation.

---

## 1. Core thesis

**QR codes are a trust-transfer mechanism that strips away every signal we
normally use to evaluate a link** — no human-readable destination, no sender
identity, no domain reputation — and, in the physical world, they borrow the
institutional trust of wherever they're stuck. That gap between "I scanned a
thing" and "I know where it goes" is the root of every attack in this talk.

The line that inoculates you against the "isn't this overhyped?" heckler:

> **QR is social engineering plus delivery — not magic code execution.**
> A QR code is data, not code. It executes nothing. Any real device
> compromise requires a *separate* vulnerability in whatever parses the
> payload (browser, QR library, or an over-trusting app). QR just removes
> friction.

Say that plainly on stage and you earn credibility with a sharp crowd while
still landing the genuine, growing risk: quishing.

---

## 2. Talk narrative arc

**Beat 1 — Why QR is uniquely dangerous as a vector.**
No human-readable destination, no sender, no domain reputation. Physical
context does the social engineering for free: a sticker on an official-looking
parking meter carries borrowed institutional trust no email ever gets.

**Beat 2 — Quishing as the headline threat.**
- Parking-meter sticker waves (multiple US cities issued public warnings).
- QR-in-PDF-attachment phishing that bypasses email link scanners because the
  URL is trapped inside an image.
- MFA-resistant flows: the QR kicks off an **OAuth consent grant** rather than
  a password page — defeats "but I have MFA," which is an underappreciated
  angle that plays well with a security-literate audience.

**Beat 3 — The mechanism spectrum (low → high sophistication).**
Static phishing → **dynamic QR** (destination changed after the code is
printed/distributed) → redirect chaining through trusted open-redirects →
non-`http` schemes (`tel:`, `sms:`, Wi-Fi join, app deeplinks).

**Beat 4 — The honest technical ceiling.**
QR delivers a URL; the browser/app/parser is what actually gets exploited *if*
it has a bug. Cases that have mattered historically: QR-library parser bugs
(malformed payloads crashing or compromising the handler), browser/webview
zero-days (QR removes the "type a URL" step), and deeplink abuse (app trusts
custom URL schemes too much). QR is the delivery vector, not the exploit.

**Beat 5 — The defense close.**
- OS/browser patching closes the parser/webview exploitation paths.
- URL preview + "treat it like an unsolicited link" closes the human paths.
- Verification-by-other-channel closes payment/crypto redirection.

---

## 3. Demo philosophy

The emotional beat you want is **"I couldn't tell, and neither could you"** —
not a wall of terminal output the back rows can't read. Every demo below is:

- **Safe:** runs on your own domains/infra, no real credentials, no exploit
  chain, nothing that works against a patched device.
- **Legible from the back row:** big visual reveals, not scrolling logs.
- **Honest:** demonstrates *capability* and *perception*, never fakes a
  compromise it isn't actually doing.

---

## 4. Demo specs (buildable)

### Demo A — "Two identical codes" reveal  ⭐ top pick
**Point:** nobody in the room can tell a safe QR from a malicious one.

- Two QR codes on screen, visually indistinguishable.
- Audience votes (show of hands, or live web poll) on which is "safe."
- Reveal: both resolve to landing pages *you* control. One shows "you'd have
  gone to your bank"; the other "you'd have gone to definitely-not-your-bank."
- **Build:** two static landing pages on your domain; a reveal slide/page that
  flips after the vote. Optional: live poll via a lightweight websocket page so
  the vote count animates on the projector.
- **Stack:** static site (any host) + optional tiny Node/Flask websocket for
  the poll.

### Demo B — Live URL-preview defeat
**Point:** you can catch a lookalike domain when it's typed; you can't when
it's a QR.

- Show the *same* destination first as a raw URL (audience spots the homograph
  / lookalike), then as a QR (they can't).
- **Build:** one page, two render modes. Pre-generate the QR from the lookalike
  URL. No backend needed.

### Demo C — Dynamic-QR switch
**Point:** "the sticker on the meter can change after you inspected it."

- Print/display a code live → scan → benign page. Change the destination
  **server-side** → rescan the *same physical code* → different landing.
- **Build:** QR encodes a stable redirector URL you own
  (e.g. `go.yourdomain.com/demo1`). A tiny backend maps that slug to a target
  you can flip from an admin toggle mid-demo.
- **Stack:** Flask/Express redirector + a key-value store (even a JSON file) +
  a hidden admin page or a single toggle endpoint. This is the most
  "engineered" demo and the most memorable — worth the extra build time.

### Demo D — Quishing-in-PDF
**Point:** "this is why your email filter didn't catch it."

- A phishing-style PDF whose QR points at your own harmless page, sailing
  through a link scanner because the URL is trapped inside an image.
- **Build:** generate a PDF with an embedded QR image (destination = your demo
  page). Optionally run it through a public link-reputation checker live to
  show it comes back clean.
- **Stack:** any PDF generator (reportlab / a template) + a QR image lib.

### Demo E — Wi-Fi join reveal
**Point:** QR can join a phone to a network with no "click," and that alone is
enough to matter.

- A QR encoding standard Wi-Fi credentials for **your own AP** named something
  like `Conference_Free_WiFi`. Phone auto-parses, prompts to join, lands on a
  captive page: *"If this were malicious, your traffic would now be routed
  through me."*
- **Demonstrates the capability and the auto-join behavior without intercepting
  anything.** Do **not** build interception — the reveal page makes the point.
- **Stack:** your own AP/hotspot + a captive-portal landing page. Keep it
  clearly benign and clearly yours.

---

## 5. Suggested repo layout (for Claude Code)

```
qr-quishing-demos/
├── README.md                 # this brief, trimmed to build notes
├── shared/                   # shared landing-page styling, QR generation
│   └── qrgen/
├── demo-a-two-codes/         # static pages + optional live poll
├── demo-b-preview-defeat/    # single page, two render modes
├── demo-c-dynamic-switch/    # redirector backend + admin toggle
│   ├── server/
│   └── admin/
├── demo-d-pdf-quishing/      # PDF generator + embedded QR
└── demo-e-wifi-reveal/       # captive-portal landing page
```

**Priority order to build:** A (highest impact / lowest effort) → C (highest
"wow," moderate effort) → B → D → E. If your slot is tight, A + C alone carry
the talk.

---

## 6. Timing guidance

- ~20 min slot: narrative + Demo A + Demo C.
- ~30–45 min slot: add B, D, and E, with the defense close as the landing.
- Always rehearse the dynamic-switch (C) and Wi-Fi (E) demos on the actual
  venue network — captive portals and conference Wi-Fi are where live demos die.

---

## 7. Guardrails to keep it clean

- Every destination is a domain **you own**. Register demo lookalikes yourself
  ahead of time so nothing points at a real brand.
- No real credential capture, ever — the landing pages *state* what would have
  happened, they don't do it.
- The Wi-Fi demo terminates at a reveal page; no traffic interception is built.
- Label the deck and repo clearly as awareness/education material.
