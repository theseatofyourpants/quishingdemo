# Deploying to a public cloud VPS (Hetzner Cloud)

The default deploy (`deploy/docker-compose.yml`) is built for a LAN/NAS behind a
Cloudflare tunnel. This guide covers the other model: a **public VPS with a real
IP**, where **Caddy** terminates TLS on 80/443 and reverse-proxies to the six
demo ports internally. Only 22/80/443 are ever exposed.

It's written for **Hetzner Cloud**, but any Docker-capable Linux VPS works.

> **Cost tip:** Hetzner bills hourly. Spin the server up the day before the
> talk and **delete it afterward** — the whole run costs pennies.

---

## 1. Create the server
- **Image:** Ubuntu 24.04.
- **Type:** the smallest is plenty (1–2 vCPU / 2–4 GB). US locations use the
  CPX (AMD) / CAX (ARM) lines; either is fine — the image is `linux/amd64`, so
  on a CAX (ARM) server let Docker build natively (it will) or pick a CPX.
- Add your SSH key during creation.

## 2. Lock down inbound (Hetzner Cloud Firewall)
Create a firewall and attach it to the server. Allow inbound only:
- **TCP 22** (SSH)
- **TCP 80** (ACME challenge + HTTP→HTTPS redirect)
- **TCP 443** (HTTPS)

Everything else denied. The demo ports (10000–10005) are never published to the
host in this variant, but this is defense in depth.

## 3. Install Docker
```bash
ssh root@YOUR_SERVER_IP
curl -fsSL https://get.docker.com | sh
docker compose version      # confirm Compose v2 is present
```

## 4. Point DNS at the server
Create six **A records** at your DNS provider, all pointing at the server's
public IPv4:

| Host | → |
|---|---|
| `qr` | `YOUR_SERVER_IP` |
| `qr-a` | `YOUR_SERVER_IP` |
| `qr-b` | `YOUR_SERVER_IP` |
| `qr-c` | `YOUR_SERVER_IP` |
| `qr-d` | `YOUR_SERVER_IP` |
| `qr-e` | `YOUR_SERVER_IP` |

If your DNS is on Cloudflare, set these **DNS-only** (grey cloud), not proxied,
so Caddy can complete the Let's Encrypt challenge and serve certs directly.
Wait for the records to resolve (`dig +short qr.yourdomain.com`) before step 6.

## 5. Get the code + configure
Clone the repo (use a read-only **deploy key** or an HTTPS token — same as the
NAS setup), then fill in the two config files:
```bash
git clone git@github.com:theseatofyourpants/quishingdemo.git
cd quishingdemo/deploy

cp .env.example .env
$EDITOR .env
#   PUBLIC_HUB=https://qr.yourdomain.com
#   PUBLIC_A=https://qr-a.yourdomain.com   ... through PUBLIC_E
#   ADMIN_TOKEN=<a strong secret>
#   WIFI_SSID / WIFI_PASSWORD = your own access point

cp Caddyfile.example Caddyfile
$EDITOR Caddyfile
#   set the six hostnames to match PUBLIC_* above, and a real ACME email
```
The `PUBLIC_*` hostnames and the Caddyfile hostnames **must match** — the QR
codes are generated from `PUBLIC_*` at container startup.

## 6. Launch
```bash
docker compose -f docker-compose.cloud.yml up -d --build
```
Caddy will fetch certificates on first start (a few seconds per hostname).

## 7. Verify
```bash
docker compose -f docker-compose.cloud.yml ps          # both services up; demos healthy
docker compose -f docker-compose.cloud.yml logs demos  # "Demo C: redirector.png -> https://qr-c...."
curl -s https://qr.yourdomain.com/healthz              # -> ok
```
Then, from a phone on cellular (not the venue wifi), open the hub and scan a
Demo A code — it should land on your `qr-a` host over HTTPS.

## 8. Update later
```bash
git pull
docker compose -f docker-compose.cloud.yml up -d --build   # re-encodes QRs to PUBLIC_*
```

## 9. Tear down after the talk
```bash
docker compose -f docker-compose.cloud.yml down
```
…then **delete the Hetzner server** so it stops billing.

---

## Alternative ingress: Cloudflare Tunnel on the VPS
Prefer to reuse the tunnel setup from the NAS instead of exposing 80/443? Skip
Caddy and steps 2/4/6 above:
1. Deploy with the standard file so the ports are reachable locally:
   `docker compose up -d --build`
2. Install `cloudflared` on the server and use the same ingress mapping from
   `deploy/cloudflared.example.yml` (a tunnel runs in one place at a time, so
   use a **separate tunnel** for the VPS or move the existing one).
With a tunnel you don't open any inbound ports and Cloudflare handles TLS.

---

## Troubleshooting
- **Cert won't issue / TLS errors:** DNS not resolving yet, port 80 blocked by
  the firewall, or Cloudflare set to *proxied* instead of DNS-only. Check
  `docker compose -f docker-compose.cloud.yml logs caddy`.
- **QRs point at localhost:** `PUBLIC_*` not set in `.env` — fix and rebuild.
- **502 from Caddy:** the `demos` container isn't healthy yet; check its logs.
- **Admin returns 403:** the `?token=` doesn't match `ADMIN_TOKEN`.
