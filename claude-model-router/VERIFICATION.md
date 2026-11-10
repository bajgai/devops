# Model discovery verification — 2026-11-09

Environment: macOS, Python 3.15.1, Claude Code 2.1.321.

## Result

`TEST_CLAUDE_CLI=1 python3 -m unittest discover -s tests -v`: **32 tests passed**.
Tests use local mock upstreams and Claude's initialization control protocol. They do not
send a user prompt or perform model inference. Several tests exercise multiple failure cases.

## Coverage

- Filter by both `owned_by: anthropic` and a canonical `claude-*` ID; reject GPT, Gemini,
  Antigravity aliases, spoofed ownership, malformed IDs, and duplicate entries.
- Keep the last good catalog on HTTP 301/302/401/403/404/429/500/502/503/504, timeouts,
  invalid JSON/schema/encoding, incomplete pagination, empty lists, and oversized responses.
- Atomic mode-600 cache writes, concurrent readers, filesystem failures, failed temporary-file
  cleanup, router restart, mismatched gateway URLs, refresh recovery, and thread shutdown.
- Catalog GET/HEAD, query strings, trailing slashes, Bearer/API-key authentication, rejected
  credentials, unsupported methods, and initial unavailability. No catalog key goes to Anthropic.
- Chat/count-token routing, original OAuth/body preservation on every fallback status and
  connection failure, no inappropriate non-Claude fallback, original direct-routing switch,
  gzip and chunked SSE preservation, and chat responsiveness during a blocked catalog refresh.
- Installed launcher symlink starts successfully and populates an isolated cache.
- Real Claude Code picker: native discovery, filtering, cached discovery without an API-key
  override, discovery disabled, failed refresh, mismatched URL, and an existing Fable 5.1 entry.

## Live checks

- Router restarted after its traffic counters remained idle; service startup succeeded.
- Authenticated `GET http://127.0.0.1:8319/v1/models?limit=1000`: HTTP 200, 15 Anthropic models,
  including `claude-fable-5-2`. Missing authentication: HTTP 401.
- The cache matches the served catalog and has mode 600.
- `claude auth status --json` still reports `claude.ai` and the Max subscription.
- A fresh real-config Claude Code initialization lists Fable 5.2, excludes non-Anthropic
  entries, and reports no API-key override. No model prompt was submitted.

## Authentication finding and limits

The proposed `apiKeyHelper` approach was tested with a command-line-only override: Claude's
auth method changed from `claude.ai` to `api_key_helper`. It was not installed. That approach
would remove the original OAuth credential needed for direct-Anthropic fallback.

Instead, the router uses its existing CPA key to refresh Claude's documented gateway cache
on startup and every five minutes. Claude's discovery flag enables the cached picker rows;
native HTTP discovery skips because no API credential overrides the saved login.

Restart Claude Code to read the latest catalog. Existing sessions may retain their loaded list.
This integration depends on Claude Code's cache format and should be checked on CLI upgrades.
Paid inference and real upstream outages were not induced; chat/fallback tests use mock servers.
