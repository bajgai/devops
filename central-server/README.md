# Central backend server (vps2)

Source of truth for moving shared backend services onto one host. Owner decision 2026-11-02: **vps2**.

## Goal

Every backend service runs on vps2 and is reachable from every host (Mac, vps1, future) over
Tailscale only. Nothing new listens on the public internet.

## Host facts (measured 2026-11-02)

| Host | CPU | RAM | Free disk | Arch | Tailscale IP | Notes |
|---|---|---|---|---|---|---|
| vps2 (srv2113168) | 4 | 15.6 GB (12 free) | 157 GB | x86_64 | 100.65.14.115 | Arch, Docker 29.9, Compose 5.6, ufw on, sshd on 22+443, otelcol-vps on 127.0.0.1:4317-4319, `vm.max_map_count`=1048576 |
| vps1 (srv1419372) | 2 | 7.7 GB | 82 GB | x86_64 | 100.92.10.29 | idle, no Docker, otelcol-vps inactive; public :22 closed, reach via `ssh -o HostName=100.92.10.29 vps1` |

## Exposure pattern

Containers publish on `127.0.0.1` only; `tailscale serve --bg --tcp <port> tcp://127.0.0.1:<port>`
puts each port on the tailnet (served by tailscaled, so ufw and boot ordering don't matter; no Funnel).
Clients use `vps2:<port>` (MagicDNS) or `100.65.14.115:<port>`.

## Services

| Service | Today | Target on vps2 | Tailnet port | State to move | Status |
|---|---|---|---|---|---|
| patchbay | vps2 `/srv/patchbay` | as is | (check) | none | in place |
| RAGFlow v1.0.0-rc3 | Mac Colima `ragflow`, 127.0.0.1 | `/opt/ragflow`, amd64 image, new infra passwords, OpenAI embeddings | 9380 API+MCP, 80 UI | none (0 datasets) | phase 1 |
| agent-otel (otel-lgtm) | Mac Colima `otel`, 3300/4317/4318 on all interfaces | `/opt/agent-otel`, Grafana 3300, OTLP on tailnet IP | 3300, 4317, 4318 | `otel-lgtm-data` 1.27 GB (or start fresh) | phase 2, needs owner OK |
| cliproxyapi | Mac Colima `cliproxyapi`, 127.0.0.1:8317, local arm64 image | rebuild amd64 image, copy conf/auth/gflow volumes | 8317 | OAuth logins, config | phase 3, needs owner OK |

Clients to repoint: yt-video-gen `.env` (RAGFLOW_*); Mac otelcol-gateway + vps1/vps2 otelcol-vps
exporters; `~/.codex/config.toml`, `~/.config/opencode/opencode.jsonc`,
`~/.config/raycast/ai/providers.yaml` (cliproxy :8317).

## Risks

- cliproxy cutover breaks every running agent session that routes through it: schedule a window.
- Mac→vps2 latency (~100 ms) is added to each cliproxy request.
- vps2 becomes a single point of failure: add backups (RAGFlow MySQL/MinIO, lgtm volume) before relying on it.
- Proton VPN on the Mac may interfere with Tailscale; reverse SSH tunnels were used for that reason.

## Hosting options at 8 vCPU / 16 GB (researched 2026-11-02, ex VAT unless noted; verify at checkout)

| Option | Spec | Price/mo | Notes |
|---|---|---|---|
| Contabo Cloud VPS 8 | 8 vCPU, 24 GB, 300 GB SSD | €11.20 ex VAT on 24 mo (~$16.80 month-to-month) | US regions; shared, oversold reputation |
| netcup VPS Lite 3 G12.5s | 8 vCPU, 16 GB, 320 GB SSD | ~€14 (2-mo billing) | Manassas US or EU |
| Hetzner CX43 | 8 vCPU, 16 GB, 160 GB | €16.49 | sold out, EU only, 2026 price hikes |
| netcup VPS 2000 G12.5 | 8 vCPU, 16 GB, 256 GB | €26.92 (12 mo) | Manassas US or EU |
| Hostinger KVM 8 | 8 vCPU, 32 GB, 400 GB | $25.99 promo (24 mo), renews $49.99 | same vendor as vps1/vps2 |
| netcup RS 2000 G12.5 | 8 dedicated cores, 16 GB, 256 GB NVMe | €40.70 (12 mo) | only dedicated-core pick |
| Oracle A1 (ARM) PAYG | 8 OCPU, 16 GB | ~$76 list, ~$48 after free 2 OCPU/12 GB | free tier halved June 2026 |
| AWS Lightsail compute | 8 vCPU, 16 GB, 640 GB | $168 | hyperscalers 6-10x the VPS hosts |
| GCP e2-standard-4 / Azure B4ms | 4 vCPU, 16 GB | $98 / $121 on demand | 8 vCPU costs more |

Current need (measured idle, OpenAI embeddings): ~5.5 GB on vps2 with deer-flow, 4 vCPU is enough today.

## Open decisions

1. Phase 2: move Grafana history (1.27 GB) or start fresh.
2. Phase 3: cutover time for cliproxy.

## Log

- 2026-11-02 vps2 chosen. Plan written.
