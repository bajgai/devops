# claude-model-router

Local Anthropic-API router for Claude Code (launchd `com.bajgai.claude-model-router`, :8319).
All `/v1/messages*` requests go to CLIProxyAPI on :8317. For `claude-*`, connection errors
and HTTP 401/403/429/500/502/503/504 fall back to Anthropic using the original OAuth login.
Exports one OTel span per request plus `gen_ai_proxy_*` metrics to the local LGTM stack
(see ~/src/agent-otel). Source: `~/src/devops/claude-model-router/`.
Installed as a symlink: `~/.local/bin/claude-model-router` → `~/src/devops/claude-model-router/claude-model-router`.
Restart: `launchctl kickstart -k gui/$(id -u)/com.bajgai.claude-model-router`.

## Anthropic model discovery

The router refreshes `~/.claude/cache/gateway-models.json` on startup and every five minutes.
It fetches CPA's catalog with the existing `claude` gateway key and includes only canonical
`claude-*` IDs whose `owned_by` is `anthropic`. This excludes GPT, Gemini, and `agy/claude-*`.
Writes are atomic with mode 600. Failed, empty, malformed, oversized, or incomplete responses
preserve the last good catalog. Catalog requests time out after two seconds and run in a
separate thread, so an outage does not block chat. A cached catalog also survives router restarts.

Claude Code needs `CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY=1` to display this cache.
Keep its current OAuth login: do **not** add `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, or
`apiKeyHelper` just for discovery. Those override `/login` and break the router's direct fallback.
The native HTTP discovery step skips without such a credential; the router maintains the cache
instead. Restart Claude Code to pick up the refreshed list; this does not change the active model.
The cache integration is verified against Claude Code 2.1.321 and should be rechecked on upgrades.

`GET` and `HEAD /v1/models` serve the same filtered catalog locally, require the gateway key
in `x-api-key` or a Bearer header, and never forward that key to Anthropic. Other non-messages
requests continue to Anthropic unchanged. A missing initial catalog returns 503.

Tests: `TEST_CLAUDE_CLI=1 python3 -m unittest discover -s tests -v` includes the installed
Claude Code picker checks (local mock upstreams; no paid inference). Omit the variable to
run the Python tests alone. Test artifacts stay under `~/scratch/claude-discovery-tests-*`.
