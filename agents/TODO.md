# Agent configuration checklist

Each agent gets three things, decided with the owner one agent at a time:

- **Personality**: role, tone and focus, stored in that agent's own config
  (not `~/.claude/CLAUDE.md`, which every agent shares through symlinks).
- **Tools**: MCP servers, skills, plugins and extensions it loads.
- **Access**: permission mode, sandbox, and which accounts and models it uses.

| # | Agent | Command | Status |
|---|---|---|---|
| 1 | Claude (+ Agent Teams) | `claude` / `orca claude-teams` | done |
| 3 | Codex | `codex` | done |
| 4 | Grok | `grok` | done |
| 5 | GitHub Copilot | `copilot` | done |
| 6 | OpenCode | `opencode` | done |
| 7 | DeepSeek Harness | `dsh-tui` | done |
| 8 | Pi | `pi` | done |
| 9 | Prime Agent | `prime-agent` | done |
| 10 | Gemini | `gemini` | skipped (Antigravity covers Google) |
| 11 | Antigravity | `agy` | done |
| 12 | Cursor | `cursor-agent` | done |
| 13 | Hermes | `hermes` | done |
| 14 | Devin | `devin` | done |
| 15 | OpenClaw | `openclaw` | done |
| 17 | Grok Bot.app: Income Scout bot | Grok Bot app (cloud bot) | in progress: owner GUI setup |

## Decisions

Recorded per agent as each one is finished.

### 1. Claude + Agent Teams (2026-10-29)

- **Personality:** Project Head (chief of staff): owns the project, delegates to
  teammates and Orca agents, reports status. Output style
  `~/.claude/output-styles/project-head.md`, `outputStyle: "Project Head"`.
  Run it as a team with `orca claude-teams`; plain `claude` shares the same config.
- **Tools:** kept `product-management@synced` (8 MCP servers still need sign-in via `/mcp`);
  disabled `marketing`, `engineering`, `agency-mcp`. Connected MCP: `cua`, `cua-driver`, `treg`.
- **Access:** `permissions.defaultMode: bypassPermissions`; 4 deny rules kept.
  Teammates and subagents inherit Opus 5.5 (`CLAUDE_CODE_SUBAGENT_MODEL=inherit`).
  Backup: `~/.claude/settings.json.bak-20261029-project-head`.

### 3. Codex (2026-10-29)

- **Personality:** Senior implementer: takes scoped tasks, matches local style, tests,
  hands back files changed + verification. `developer_instructions` in `~/.codex/config.toml`.
- **Tools:** removed `flint` (binary missing) and `floot` (never signed in). Kept Paperclip
  gateways (11), `cua`, `cua-driver`, `cua_repl`, `node_repl`, `xcode`, `treg`.
- **Access:** unchanged: `approval_policy = "never"`, `sandbox_mode = "danger-full-access"`.
  Model `gpt-6.1-sol`, reasoning effort low → medium.
  Backup: `~/.codex/config.toml.bak-20261029-implementer`.

### 4. Grok (2026-10-29)

- **Personality:** Researcher: live web/X/treg research, cited briefs under 300 words,
  research only. `~/.grok/AGENTS.md` (read only by Grok).
- **Tools:** MCP `cua` plus new `cua-driver` and `treg` (same treg token as Codex).
- **Access:** `ui.permission_mode = "auto"`; model `grok-4.7` via CLIProxyAPI,
  reasoning `xhigh` → `high`. Backup: `~/.grok/config.toml.bak-20261029-researcher`.

### 5. GitHub Copilot (2026-10-29)

- **Personality:** GitHub operator: PRs, issues, CI failures, releases and repo hygiene for
  `bajgai/*`; confirms before merging, force-pushing, deleting or publishing.
  `~/.copilot/copilot-instructions.md` (personal instructions, Copilot only).
- **Tools:** built-in GitHub MCP only.
- **Access:** asks before tools (default `interactive` mode); model `claude-sonnet-5.5`
  (`~/.copilot/settings.json`).

### 6. OpenCode (2026-10-29)

- **Personality:** Frontend / UI builder: existing stack and tokens, deliberate design,
  WCAG AA, browser-checked at mobile and desktop. `~/.config/opencode/instructions/frontend-builder.md`,
  loaded through `"instructions"` in `~/.config/opencode/opencode.jsonc`.
- **Tools:** unchanged: MCP `lightpanda`, `cua`, `cua-driver`, `treg`.
- **Access:** unchanged: no permission rules (fully open); model `cliproxyapi/gpt-6.1-sol`.
  Backup: `~/.config/opencode/opencode.jsonc.bak-20261029-frontend`.

### 7. DeepSeek Harness (2026-10-29)

- **Personality:** Bulk / batch worker: migrations, scripted refactors, cleanup; proves the
  pattern on one or two files, then applies it consistently. `system-prompt.personaPrefix`
  in `~/.dsh/profiles/{headless,dsh-tui}/cordis.patch.yml`.
- **Tools:** unchanged: dsh built-ins + Orca status hook; no MCP servers.
- **Access:** unchanged: `workspace-write` sandbox, approval `ask`; model `deepseek-flash`
  (default) via CLIProxyAPI. Backups: `cordis.patch.yml.bak-20261029-bulk-worker`.

### 8. Pi (2026-10-29)

- **Personality:** Ops / sysadmin for the Mac and VPS: looks before changing, backs up,
  verifies, redacts secrets, asks before destructive steps. `~/.pi/agent/APPEND_SYSTEM.md`.
- **Tools:** MCP via pi-mcp-adapter: `cua` (156 tools), `cua-driver` (62), `treg` (10), all
  connected (`~/.pi/agent/mcp.json`, backup `mcp.json.bak-20261029-ops`).
- **Access:** unchanged: no approval prompts; `cliproxyapi/gpt-6.1-sol`, thinking high.

### 9. Prime Agent (2026-10-29)

- **Personality:** Data analyst: Python kernel, treg data, subagent fan-out, shows method,
  sample sizes and caveats. `~/.prime/agent/AGENTS.md` (Prime ignores `APPEND_SYSTEM.md`).
- **Tools:** MCP `treg` via `prime-agent mcp add --bearer-token-env-var TREG_MCP_TOKEN`;
  token in `~/.config/treg/mcp_token` (600), exported from `~/.zshenv`
  (backup `~/.zshenv.bak-20261029-treg`).
- **Access:** no approval prompts; moved off its own OpenAI login to CLIProxyAPI:
  `~/.prime/agent/models.json` (key read from `~/.pi/agent/cliproxyapi.json`),
  `defaultProvider: cliproxyapi`, `defaultModel: gpt-6.1-sol`.
  Backup: `~/.prime/agent/settings.json.bak-20261029-analyst`.
- **Security:** Prime's stored Anthropic and OpenAI OAuth tokens were printed into a session
  transcript on 2026-10-29; owner to sign out and back in (or revoke) to invalidate them.

### 10. Gemini (2026-10-29)

- Skipped at the owner's request; Antigravity is the team's Google agent.

### 11. Antigravity (2026-10-29)

- **Personality:** Visual / multimodal specialist: screenshots, mockups, PDFs, video,
  image generation, GUI driving with cua. `~/.gemini/config/AGENTS.md` (Antigravity's
  global rules folder; Gemini CLI doesn't read it).
- **Tools:** unchanged: MCP `cua`, `cua-driver`.
- **Access:** unchanged: `toolPermission` and `artifactReviewPolicy` `always-proceed`.
  Model Gemini 3.8 Flash (High) → Gemini 4 Argon (High).
  Backup: `~/.gemini/antigravity-cli/settings.json.bak-20261029-visual`.

### 12. Cursor (2026-10-29)

- **Personality:** Code reviewer: whole-codebase context, findings as file:line + why + fix
  by severity, review only. `~/.cursor/rules/code-reviewer.mdc` (`alwaysApply: true`);
  Cursor finds it by walking up from projects under `~` (no effect for paths outside home).
- **Tools:** removed broken `flint`; kept `xcode`, `cua`, `cua-driver`, `treg`.
  Backup: `~/.cursor/mcp.json.bak-20261029-reviewer`.
- **Access:** unchanged: model Auto, `approvalMode: unrestricted`.

### 13. Hermes (2026-10-29)

- **Personality:** Long-running research agent: market and topic research, business
  opportunities, multi-site information gathering; per-project briefs come later. Rewrote the
  charter in `~/.hermes/SOUL.md` (voice paragraph, Telegram approval rules, Never list and
  OpenClaw claims files kept; Apify/Algora selling mandate removed).
  Backup: `~/.hermes/SOUL.md.bak-20261029-researcher`.
- **Tools:** unchanged (owner's choice): MCP `composio`, `firecrawl`, `flint` (broken), `xcode`,
  `cua-driver`, `cua`, `composio_grok`, `cliproxyapi`.
- **Access:** unchanged: `approvals.mode: false`; model `gpt-6.1-sol` via CLIProxyAPI.

### 14. Devin (2026-10-29)

- **Personality:** Autonomous feature builder: whole features/tickets, plan → branch → tests →
  PR for Cursor to review; never merges or deploys without the owner. `~/.devin/global_rules.md`
  (Devin's global rule location; `~/.config/devin/` is not read for rules).
- **Tools:** unchanged: own MCP `cua`, `cua-driver`; imported `treg` (~/.claude.json), `xcode`
  (~/.cursor/mcp.json), `firecrawl` (~/.codeium/windsurf/mcp_config.json).
- **Access:** `agent.permission_mode: "dangerous"` in `~/.config/devin/config.json` (never asks).
  Workspace trust still applies in print mode (`--respect-workspace-trust false` to skip).
  Backup: `~/.config/devin/config.json.bak-20261029-builder`.

### 15. OpenClaw (2026-10-29)

- **Personality:** Long-running research agent, same remit as Hermes (research, business
  opportunities, multi-site gathering; per-project briefs later). Rewrote the charter in
  `~/src/money-maker/data/openclaw/workspace/AGENTS.md` (Telegram approval rules, Never list
  incl. Astra/Fable rule, ClawHub vetting, claims files and craft section kept; RapidAPI/MCP
  selling mandate removed). `TEAM-POLICY.md`: team is research-first; Builder/Writer start
  only when a brief asks for a build. The workspace is git-ignored; the old charter was rebuilt
  from the session transcript into `AGENTS.md.bak-20261029-researcher`.
- **Tools:** unchanged: MCP `firecrawl`, `cua`, `cua-driver`; built-in web search and fetch.
- **Access:** unchanged: `openai/gpt-6.1-sol`; exec `auto` on the gateway; elevated commands
  only from the owner's Telegram.

### 16. Codex Browser on GPT-6.1 Terra (2026-10-29)

- **Personality:** Browser operator in the owner's Default Chrome profile ("Your Chrome") only:
  new tabs, closes its own, script first, computer use only for chrome:// pages, Web Store,
  extension pages, native dialogs and canvas apps. `developer_instructions` in
  `~/.codex/browser.config.toml` (includes the plugin bootstrap: 1-2 tool calls, ~17 s per task).
- **Tools:** bundled `chrome@openai-bundled` via `node_repl`. The Cowork skills synced into
  `~/.agents/skills/synced/` (`chrome-browser`, `built-in-browser`, `computer-use`) are disabled
  for Codex with `[[skills.config]]` in `~/.codex/config.toml`; they name `mcp__Claude_*` tools.
- **Access:** `gpt-6.1-terra`, ChatGPT login; `codex-browser --cpa` routes through CLIProxyAPI.
  `~/.codex/browser/config.toml`: approvals `never_ask`, full CDP access, file URL access on.
- **Decisions:** Orca Dispatch → `orca orchestration ask`; started by an agent → returns
  "DECISION NEEDED" for `codex exec resume`; owner at terminal → asks; else Project Head via
  `orca terminal send`. Payments, publishing, deletions, password/account changes → owner.
  Explicit instructions in the prompt count as approval (a test form submit went through).
- **Launcher:** `~/.local/bin/codex-browser [--exec] [--cpa] [prompt]` starts the ChatGPT app
  (required: it provides the browser channel) and Chrome, wraps `caffeinate -i`, uses the app's
  bundled codex (matches the plugin) and warns when app, config and plugin versions differ.

### 17. Grok Bot.app: Income Scout (2026-10-29)

- **Personality:** Research-only income scout: finds and validates paid-demand opportunities in
  6 lanes (sell existing products, business freelance/contract/bounties, software, digital
  products, video/reels, adjacent B2B); drafts Action Cards, never posts, buys, bids or signs up.
  Charter, memory facts, 13 skills, 10 routines: `bajgai/income-scout-data` → `bot/`
  (clone `~/src/income-scout-data`); owner setup checklist `bot/SETUP.md`.
- **Tools:** none connected (no X, GitHub, Slack, MCP or treg); own receive-only email inbox;
  writes only to the private repo with a single-repo deploy key. Mac side (no LLM except the
  Grok-CLI reviewer): `~/src/money-maker/agents/income-scout/` intake, mirror, watchdog,
  review, notify; config `config/income-scout.toml` (`enabled = false` until first heartbeat).
- **Access:** Grok Bot global settings (owner, GUI, `bot/SETUP.md` steps 2-3): local tools on
  Ask, egress tunnel off, six auto-review block rules, spend fixed at $0. Telegram fault alerts
  through `openclaw message send`.

## Browser profiles (2026-10-29)

Each browser-using agent has its own Chrome profile; its instruction file has a `## Browser`
block (profile, script-first/computer-use fallback, decision routing). Backups: `*.bak-20261029-browser`.

| Agent | Chrome profile (directory) | Where it's set |
|---|---|---|
| Codex Browser | Your Chrome (`Default`) | `~/.codex/browser.config.toml` |
| Claude | Claude (`Profile 3`, Claude in Chrome) | `~/.claude/output-styles/project-head.md` |
| Pi | pi (`agent-pi`) | `~/.pi/agent/APPEND_SYSTEM.md` |
| Antigravity | antigravity (`agent-antigravity`) | `~/.gemini/config/AGENTS.md` |
| Hermes | hermes (`agent-hermes`) | `~/.hermes/SOUL.md`; `browser.real_profile_pin` in `~/.hermes/config.yaml` |
| Devin | devin (`agent-devin`) | `~/.devin/global_rules.md` |
| OpenCode | opencode (`agent-opencode`) | `~/.config/opencode/instructions/frontend-builder.md` |
| OpenClaw | its managed `openclaw` browser profile | workspace `AGENTS.md` |

New profiles are signed out; the owner signs each in. Copilot, Cursor, DeepSeek Harness, Prime
and Grok have no profile (no real-browser work).
