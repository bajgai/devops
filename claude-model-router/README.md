# claude-model-router

Local Anthropic-API router for Claude Code (launchd `com.bajgai.claude-model-router`, :8319).
`claude-*` models go to api.anthropic.com; other models go to CLIProxyAPI on :8317.
Exports one OTel span per request plus `gen_ai_proxy_*` metrics to the local LGTM stack
(see ~/src/agent-otel). Source: `~/src/devops/claude-model-router/`.
Installed as a symlink: `~/.local/bin/claude-model-router` → `~/src/devops/claude-model-router/claude-model-router`.
Restart: `launchctl kickstart -k gui/$(id -u)/com.bajgai.claude-model-router`.
