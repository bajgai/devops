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
