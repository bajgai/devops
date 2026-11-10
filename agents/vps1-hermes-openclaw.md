# Hermes and OpenClaw on vps1 (fresh installs, 2026-11-10)

Both agents run 24/7 on vps1 (srv1419372, tailnet `vps1.tailcb0867.ts.net`, 100.92.10.29) and are
prompted from the Mac, Omarchy, iPhone and iPad. Nothing runs on the Mac any more.

| | Hermes | OpenClaw |
|---|---|---|
| Version | v0.23.1 (stable) | 2026.11.3 (npm) |
| User / home | `hermes`, `~/.hermes` | `openclaw`, `~/.openclaw` (no sudo) |
| Service | system `hermes-gateway.service` | user `openclaw-gateway.service` (linger on) |
| Model | `gpt-6.1-sol`, provider `custom` → `http://vps2:8317/v1` | `cliproxy/gpt-6.1-sol` → same |
| Telegram | previous Hermes bot, allowlist | `@VpsOpenclawNiranjanbot`, allowlist |
| Tailnet URL | API `https://vps1.tailcb0867.ts.net:8642/v1`, dashboard `http://vps1.tailcb0867.ts.net:9119` | Control UI / gateway `https://vps1.tailcb0867.ts.net` (`wss://` for clients) |
| Secret (Mac Keychain service) | `vps1-hermes-api-key`, `vps1-hermes-dashboard-password` (user `owner`) | `vps1-openclaw-gateway-token` |

- Both share the one cliproxyapi key (`CPA_LOCAL_API_KEY`); no per-agent keys yet.
- Exposure: gateways bind 127.0.0.1; root-managed `tailscale serve` publishes 443 → 18789 and 8642 → 8642
  (tailnet only, no Funnel). `hermes-dashboard.service` binds the tailnet IP with password login.
- New OpenClaw clients (browser, app, CLI) need a one-time approval on vps1 as `openclaw`:
  `openclaw devices list`, then `openclaw devices approve <requestId>`.
- Mac: `ai.openclaw.gateway` and `ai.openclaw.node` are in `~/Library/LaunchAgents/disabled`; the Mac
  `openclaw` CLI is in remote mode (backup `~/.openclaw/openclaw.json.bak-pre-remote-20261110`).
- Old Hermes install (config, plugins, skills, Discord/Inkbox setup, `rae-agent` profile) is parked, not
  deleted: `/home/hermes/pre-fresh-20261110` (7.3 GB).
- Verified 2026-11-10: prompts answered from the Mac over the tailnet for both; both Telegram bots
  connected; all services returned after a reboot.
- Open: backups for vps1 (none), phone/tablet/Omarchy pairing, otelcol on vps1.
