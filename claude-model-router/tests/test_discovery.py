"""Integration coverage using local HTTP upstreams and the installed Claude CLI."""
import gzip
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import select
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from model_catalog import ModelCatalog, anthropic_models, MAX_RESPONSE_BYTES

RUN = Path(tempfile.mkdtemp(prefix="claude-discovery-tests-", dir=Path.home() / "scratch"))
KEY = "test-gateway-key"
OAUTH = "Bearer test-original-oauth"
FABLE = {"id": "claude-fable-5-2", "owned_by": "anthropic"}
MIXED = {"data": [FABLE, {"id": "claude-opus-5-5", "owned_by": "anthropic"},
                   {"id": "gpt-test", "owned_by": "openai"},
                   {"id": "gemini-test", "owned_by": "google"},
                   {"id": "agy/claude-opus-5-5-high", "owned_by": "antigravity"},
                   {"id": "claude-wrong-owner", "owned_by": "antigravity"}]}


class Upstream:
    def __init__(self):
        self.requests = []
        self.status = 200
        self.body = json.dumps(MIXED).encode()
        self.headers = {"Content-Type": "application/json"}
        self.delay = 0
        self.chunked = False
        owner = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *args):
                pass

            def handle_request(self):
                body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
                owner.requests.append({"method": self.command, "path": self.path,
                                       "headers": dict(self.headers), "body": body})
                time.sleep(owner.delay)
                self.send_response_only(owner.status)
                for key, value in owner.headers.items():
                    self.send_header(key, value)
                self.send_header("Connection", "close")
                self.send_header("Transfer-Encoding" if owner.chunked else "Content-Length",
                                 "chunked" if owner.chunked else str(len(owner.body)))
                self.end_headers()
                try:
                    if self.command != "HEAD":
                        if owner.chunked:
                            for chunk in [owner.body[:7], owner.body[7:]]:
                                if chunk:
                                    self.wfile.write(b"%x\r\n%s\r\n" % (len(chunk), chunk))
                            self.wfile.write(b"0\r\n\r\n")
                        else:
                            self.wfile.write(owner.body)
                except (BrokenPipeError, ConnectionResetError):
                    pass
                self.close_connection = True

            do_GET = do_HEAD = do_POST = do_DELETE = handle_request

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever,
                                       kwargs={"poll_interval": 0.01}, daemon=True)
        self.thread.start()
        self.target = ("http", "127.0.0.1", self.server.server_port)
        self.url = f"http://127.0.0.1:{self.server.server_port}"

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)


def new_path(name):
    return Path(tempfile.mkdtemp(prefix=name + "-", dir=RUN))


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.upstream = Upstream()
        self.addCleanup(self.upstream.close)
        self.cache = new_path("cache") / "gateway-models.json"
        self.catalog = ModelCatalog(self.upstream.target, KEY, self.cache,
                                    "http://127.0.0.1:8319", timeout=0.1)

    def test_only_anthropic_owned_canonical_ids(self):
        self.assertEqual([x["id"] for x in anthropic_models(MIXED)],
                         ["claude-fable-5-2", "claude-opus-5-5"])

    def test_duplicates_invalid_rows_and_metadata(self):
        rows = [None, 1, {}, {"id": 1, "owned_by": "anthropic"},
                {**FABLE, "display_name": "Fable", "description": None, "secret": "omitted"},
                FABLE, {"id": "claude-fable-5.2", "owned_by": "anthropic"},
                {"id": "claude-fable-5-2\n", "owned_by": "anthropic"}]
        self.assertEqual(anthropic_models({"data": rows}), [{**FABLE, "display_name": "Fable"}])

    def test_fetch_auth_and_atomic_private_cache(self):
        self.assertTrue(self.catalog.refresh())
        request = self.upstream.requests[-1]
        self.assertEqual(request["path"], "/v1/models?limit=1000")
        self.assertEqual(request["headers"].get("x-api-key"), KEY)
        self.assertNotIn("Authorization", request["headers"])
        saved = json.loads(self.cache.read_text())
        self.assertEqual(saved["baseUrl"], self.catalog.base_url)
        self.assertEqual(saved["models"], self.catalog.models)
        self.assertGreater(saved["fetchedAt"], 0)
        self.assertEqual(self.cache.stat().st_mode & 0o777, 0o600)
        self.assertEqual(list(self.cache.parent.glob(".gateway-models-*")), [])
        self.assertNotIn(KEY, self.cache.read_text())

    def check_preserves(self):
        prior = self.cache.read_bytes()
        models = self.catalog.models
        self.assertFalse(self.catalog.refresh())
        self.assertEqual(self.cache.read_bytes(), prior)
        self.assertEqual(self.catalog.models, models)

    def test_http_failures_preserve_last_good(self):
        self.assertTrue(self.catalog.refresh())
        for status in [301, 302, 401, 403, 404, 429, 500, 502, 503, 504]:
            with self.subTest(status=status):
                self.upstream.status = status
                self.check_preserves()

    def test_invalid_incomplete_empty_and_oversized_responses(self):
        self.assertTrue(self.catalog.refresh())
        for body in [b"not-json", b"[]", b"null", b'{"data":null}', b'{"data":[]}',
                     json.dumps({**MIXED, "has_more": True}).encode(),
                     b"x" * (MAX_RESPONSE_BYTES + 1), b"\xff"]:
            with self.subTest(body=body[:40]):
                self.upstream.body = body
                self.check_preserves()

    def test_timeout_preserves_last_good(self):
        self.assertTrue(self.catalog.refresh())
        self.upstream.delay = 0.3
        start = time.monotonic()
        self.check_preserves()
        self.assertLess(time.monotonic() - start, 0.5)

    def test_cache_write_failure_preserves_last_good(self):
        self.assertTrue(self.catalog.refresh())
        with patch("model_catalog.os.replace", side_effect=OSError("test write failure")):
            self.check_preserves()
        self.assertEqual(list(self.cache.parent.glob(".gateway-models-*")), [])

    def test_failed_temporary_cleanup_does_not_kill_refresh(self):
        self.assertTrue(self.catalog.refresh())
        with patch("model_catalog.os.replace", side_effect=OSError("test write failure")), \
                patch("model_catalog.Path.unlink", side_effect=OSError("test cleanup failure")):
            self.check_preserves()
        self.assertTrue(self.catalog.refresh())

    def test_concurrent_cache_readers_only_see_complete_json(self):
        self.assertTrue(self.catalog.refresh())
        errors = []
        done = threading.Event()
        def read():
            while not done.is_set():
                try:
                    saved = json.loads(self.cache.read_text())
                    if not saved["models"]:
                        errors.append("empty catalog")
                except Exception as error:
                    errors.append(type(error).__name__)
        reader = threading.Thread(target=read)
        reader.start()
        try:
            for _ in range(15):
                self.assertTrue(self.catalog.refresh())
        finally:
            done.set()
            reader.join(timeout=2)
        self.assertEqual(errors, [])

    def test_cache_restart_and_wrong_endpoint(self):
        self.assertTrue(self.catalog.refresh())
        restored = ModelCatalog(self.upstream.target, KEY, self.cache, self.catalog.base_url)
        self.assertEqual(restored.models, self.catalog.models)
        wrong = ModelCatalog(self.upstream.target, KEY, self.cache, "http://localhost:9999")
        self.assertEqual(wrong.models, [])

    def test_bad_initial_cache_is_ignored(self):
        for raw in [b"invalid", b"[]", b"null", b'{}']:
            with self.subTest(raw=raw):
                self.cache.write_bytes(raw)
                catalog = ModelCatalog(self.upstream.target, KEY, self.cache, self.catalog.base_url)
                self.assertEqual(catalog.models, [])

    def test_background_refresh_recovers_and_stops(self):
        self.upstream.status = 503
        self.catalog.interval = 0.03
        thread = self.catalog.start()
        self.addCleanup(self.catalog.stop.set)
        deadline = time.monotonic() + 2
        while not self.upstream.requests and time.monotonic() < deadline:
            time.sleep(0.01)
        self.upstream.status = 200
        while not self.catalog.models and time.monotonic() < deadline:
            time.sleep(0.01)
        self.catalog.stop.set()
        thread.join(timeout=1)
        self.assertTrue(self.catalog.models)
        self.assertFalse(thread.is_alive())


class RouterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        loader = importlib.machinery.SourceFileLoader("router_under_test", str(ROOT / "claude-model-router"))
        cls.router = importlib.util.module_from_spec(importlib.util.spec_from_loader(loader.name, loader))
        with patch.dict(os.environ, {"OTEL_SDK_DISABLED": "true"}), \
                patch("subprocess.run", return_value=subprocess.CompletedProcess([], 0, KEY)):
            loader.exec_module(cls.router)
        cls.router.log = lambda *args: None
        cls.router.record = lambda *args, **kwargs: None

    def setUp(self):
        self.cpa, self.anthropic = Upstream(), Upstream()
        self.addCleanup(self.cpa.close)
        self.addCleanup(self.anthropic.close)
        self.router.CPA, self.router.ANTHROPIC = self.cpa.target, self.anthropic.target
        self.router.CLAUDE_VIA_CPA = True
        self.router.CATALOG = ModelCatalog(self.cpa.target, KEY, new_path("router") / "cache.json", "http://test")
        self.assertTrue(self.router.CATALOG.refresh())
        self.cpa.requests.clear()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), self.router.Router)
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever,
                                       kwargs={"poll_interval": 0.01}, daemon=True)
        self.thread.start()
        self.addCleanup(self.close)

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def request(self, path="/v1/messages", method="POST", model="claude-opus-5-5", headers=None):
        body = json.dumps({"model": model, "messages": [{"role": "user", "content": "test"}],
                           "max_tokens": 1}).encode() if method == "POST" else None
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        try:
            connection.request(method, path, body, headers or {"Authorization": OAUTH})
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    def test_catalog_key_and_bearer_auth_query_and_trailing_slash(self):
        for path, headers in [("/v1/models?limit=1000", {"x-api-key": KEY}),
                              ("/v1/models/", {"Authorization": "Bearer " + KEY})]:
            with self.subTest(path=path):
                status, _, body = self.request(path, "GET", headers=headers)
                self.assertEqual(status, 200)
                self.assertEqual(json.loads(body)["data"], self.router.CATALOG.models)
        self.assertFalse(self.anthropic.requests)
        self.assertFalse(self.cpa.requests)

    def test_catalog_missing_wrong_and_oauth_credentials_rejected(self):
        for headers in [{}, {"x-api-key": "wrong"}, {"Authorization": OAUTH}]:
            with self.subTest(headers=headers):
                status, _, body = self.request("/v1/models", "GET", headers=headers)
                self.assertEqual(status, 401)
                self.assertNotIn(KEY.encode(), body)
        self.assertFalse(self.anthropic.requests)
        self.assertFalse(self.cpa.requests)

    def test_catalog_head_and_unsupported_methods(self):
        status, headers, body = self.request("/v1/models", "HEAD", headers={"x-api-key": KEY})
        self.assertEqual(status, 200)
        self.assertGreater(int(headers["Content-Length"]), 0)
        self.assertEqual(body, b"")
        self.assertEqual(self.request("/v1/models", "POST", headers={"x-api-key": KEY})[0], 405)
        self.assertFalse(self.anthropic.requests)

    def test_catalog_unavailable_is_503(self):
        self.router.CATALOG.models = []
        self.assertEqual(self.request("/v1/models", "GET", headers={"x-api-key": KEY})[0], 503)

    def test_chat_uses_cpa_and_strips_oauth(self):
        status, _, _ = self.request("/v1/messages?beta=true", headers={
            "Authorization": OAUTH, "x-api-key": "original-key", "anthropic-beta": "test-beta"})
        self.assertEqual(status, 200)
        sent = self.cpa.requests[-1]
        self.assertEqual(sent["path"], "/v1/messages?beta=true")
        self.assertEqual(sent["headers"]["x-api-key"], KEY)
        self.assertNotIn("Authorization", sent["headers"])
        self.assertEqual(sent["headers"]["anthropic-beta"], "test-beta")
        self.assertFalse(self.anthropic.requests)

    def test_count_tokens_keeps_existing_routing(self):
        self.assertEqual(self.request("/v1/messages/count_tokens")[0], 200)
        self.assertEqual(self.cpa.requests[-1]["path"], "/v1/messages/count_tokens")

    def test_every_fallback_status_preserves_original_oauth_and_body(self):
        for status in [401, 403, 429, 500, 502, 503, 504]:
            with self.subTest(status=status):
                self.cpa.status = status
                self.assertEqual(self.request()[0], 200)
                forwarded = self.anthropic.requests[-1]
                self.assertEqual(forwarded["headers"]["Authorization"], OAUTH)
                self.assertNotIn("x-api-key", forwarded["headers"])
                self.assertEqual(forwarded["body"], self.cpa.requests[-1]["body"])

    def test_connection_failure_falls_back(self):
        original = self.router.conn
        def connect(target):
            if target is self.router.CPA:
                raise ConnectionRefusedError("test tunnel failure")
            return original(target)
        with patch.object(self.router, "conn", side_effect=connect):
            self.assertEqual(self.request()[0], 200)
        self.assertEqual(self.anthropic.requests[-1]["headers"]["Authorization"], OAUTH)

    def test_bad_request_and_nonclaude_do_not_fallback(self):
        self.cpa.status = 400
        self.assertEqual(self.request()[0], 400)
        self.cpa.status = 503
        self.assertEqual(self.request(model="gpt-test")[0], 503)
        self.assertFalse(self.anthropic.requests)

    def test_other_routes_preserve_oauth(self):
        for path in ["/api/hello", "/api/bootstrap"]:
            with self.subTest(path=path):
                self.assertEqual(self.request(path, "GET")[0], 200)
                self.assertEqual(self.anthropic.requests[-1]["headers"]["Authorization"], OAUTH)
        self.assertFalse(self.cpa.requests)

    def test_old_direct_routing_switch_still_works(self):
        self.router.CLAUDE_VIA_CPA = False
        self.assertEqual(self.request()[0], 200)
        self.assertFalse(self.cpa.requests)
        self.assertEqual(self.anthropic.requests[-1]["headers"]["Authorization"], OAUTH)

    def test_sse_chunked_and_gzip_bodies_preserved(self):
        sse = b'event: message_start\ndata: {"type":"message_start","message":{}}\n\n'
        for compressed in [False, True]:
            with self.subTest(compressed=compressed):
                self.cpa.body = gzip.compress(sse) if compressed else sse
                self.cpa.headers = {"Content-Type": "text/event-stream"}
                if compressed:
                    self.cpa.headers["Content-Encoding"] = "gzip"
                self.cpa.chunked = True
                status, headers, body = self.request()
                self.assertEqual(status, 200)
                self.assertEqual(body, self.cpa.body)
                self.assertEqual(headers["Transfer-Encoding"], "chunked")

    def test_catalog_refresh_cannot_block_chat(self):
        waiting = threading.Event()
        release = threading.Event()
        def stall():
            waiting.set()
            release.wait(timeout=2)
        with patch.object(self.router.CATALOG, "refresh", side_effect=stall):
            thread = self.router.CATALOG.start()
            try:
                self.assertTrue(waiting.wait(timeout=1))
                start = time.monotonic()
                self.assertEqual(self.request()[0], 200)
                self.assertLess(time.monotonic() - start, 0.5)
            finally:
                self.router.CATALOG.stop.set()
                release.set()
                thread.join(timeout=2)


class EntrypointTests(unittest.TestCase):
    def test_installed_symlink_starts_and_populates_isolated_cache(self):
        upstream = Upstream()
        self.addCleanup(upstream.close)
        config = new_path("entrypoint")
        helper = config / "llm-gateway-key"
        helper.write_text("#!/bin/sh\nprintf '%s\\n' '" + KEY + "'\n")
        helper.chmod(0o700)
        with socket.socket() as socket_:
            socket_.bind(("127.0.0.1", 0))
            port = socket_.getsockname()[1]
        cache = config / "cache.json"
        env = {**os.environ, "PATH": str(config) + os.pathsep + os.environ["PATH"],
               "ROUTER_PORT": str(port), "ROUTER_CPA_PORT": str(upstream.server.server_port),
               "ROUTER_CATALOG_CACHE_PATH": str(cache), "OTEL_SDK_DISABLED": "true"}
        installed = Path.home() / ".local/bin/claude-model-router"
        entrypoint = installed if installed.resolve() == ROOT / "claude-model-router" else ROOT / "claude-model-router"
        process = subprocess.Popen([sys.executable, str(entrypoint)], env=env,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            deadline = time.monotonic() + 3
            while not cache.exists() and process.poll() is None and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertTrue(cache.exists(), "router entrypoint did not populate cache")
            self.assertEqual(json.loads(cache.read_text())["baseUrl"], f"http://127.0.0.1:{port}")
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
            try:
                connection.request("GET", "/v1/models?limit=1000", headers={"x-api-key": KEY})
                response = connection.getresponse()
                self.assertEqual(response.status, 200)
                self.assertEqual(json.loads(response.read())["data"], anthropic_models(MIXED))
            finally:
                connection.close()
        finally:
            process.terminate()
            try:
                process.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()


def cli_initialize(config, upstream, *, credential=False, enabled=True):
    env = os.environ.copy()
    for key in list(env):
        if key.startswith(("ANTHROPIC_", "CLAUDE_CODE_", "CLAUDE_CONFIG_DIR", "ORCA_")):
            env.pop(key)
    env.update(CLAUDE_CONFIG_DIR=str(config), ANTHROPIC_BASE_URL=upstream.url,
               CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY="1" if enabled else "0",
               CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1", DISABLE_AUTOUPDATER="1",
               DISABLE_TELEMETRY="1", OTEL_SDK_DISABLED="true")
    if credential:
        env["ANTHROPIC_API_KEY"] = KEY
    cmd = ["claude", "--setting-sources", "", "--settings",
           '{"disableAllHooks":true,"autoMemoryEnabled":false}', "--strict-mcp-config",
           "--mcp-config", '{"mcpServers":{}}', "--model", "opus", "--no-session-persistence",
           "--debug-file", str(config / "debug.log"), "--input-format", "stream-json",
           "--output-format", "stream-json", "--verbose", "-p"]
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True, env=env, cwd=RUN)
    try:
        process.stdin.write(json.dumps({"type": "control_request", "request_id": "init",
                                       "request": {"subtype": "initialize"}}) + "\n")
        process.stdin.flush()
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            ready, _, _ = select.select([process.stdout], [], [], 0.2)
            if ready:
                line = process.stdout.readline()
                if not line:
                    break
                data = json.loads(line)
                if data.get("type") == "control_response":
                    return data["response"]["response"]
        raise AssertionError("Claude initialization did not return")
    finally:
        process.terminate()
        try:
            process.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()


@unittest.skipUnless(os.environ.get("TEST_CLAUDE_CLI") == "1", "set TEST_CLAUDE_CLI=1 for installed CLI checks")
class ClaudeCLITests(unittest.TestCase):
    def setUp(self):
        self.upstream = Upstream()
        self.addCleanup(self.upstream.close)
        self.config = new_path("cli")
        self.cache = self.config / "cache/gateway-models.json"

    def assert_no_inference(self):
        self.assertFalse([r for r in self.upstream.requests if r["method"] == "POST"])

    def values(self, result):
        return {x["value"] for x in result["models"]}

    def seed_cache(self):
        catalog = ModelCatalog(self.upstream.target, KEY, self.cache, self.upstream.url)
        self.assertTrue(catalog.refresh())
        self.upstream.requests.clear()

    def test_native_discovery_with_key_and_builtin_name_filter(self):
        result = cli_initialize(self.config, self.upstream, credential=True)
        values = self.values(result)
        self.assertIn("claude-fable-5-2", values)
        self.assertIn("agy/claude-opus-5-5-high", values)
        self.assertNotIn("gpt-test", values)
        self.assertNotIn("gemini-test", values)
        self.assert_no_inference()

    def test_cached_anthropic_catalog_without_api_credential(self):
        self.seed_cache()
        result = cli_initialize(self.config, self.upstream)
        values = self.values(result)
        self.assertIn("claude-fable-5-2", values)
        self.assertNotIn("agy/claude-opus-5-5-high", values)
        self.assertNotIn("claude-wrong-owner", values)
        self.assertEqual(result["account"].get("apiKeySource", "none"), "none")
        self.assertFalse(self.upstream.requests)
        self.assert_no_inference()

    def test_old_fable_51_picker_cache_keeps_new_52(self):
        self.seed_cache()
        (self.config / ".claude.json").write_text(json.dumps({
            "additionalModelOptionsCache": [{"value": "claude-fable-5-1[1m]", "label": "Fable",
                                             "description": "Fable 5.1"}],
            "additionalModelOptionsAnsweredAt": int(time.time() * 1000)}))
        result = cli_initialize(self.config, self.upstream)
        self.assertIn("claude-fable-5-2", self.values(result))
        self.assert_no_inference()

    def test_disabled_flag_hides_gateway_cache(self):
        self.seed_cache()
        result = cli_initialize(self.config, self.upstream, enabled=False)
        self.assertNotIn("claude-fable-5-2", self.values(result))
        self.assertFalse(self.upstream.requests)

    def test_failed_native_refresh_keeps_cached_models(self):
        self.seed_cache()
        self.upstream.status = 401
        result = cli_initialize(self.config, self.upstream, credential=True)
        self.assertIn("claude-fable-5-2", self.values(result))
        self.assert_no_inference()

    def test_cache_for_other_endpoint_ignored(self):
        self.seed_cache()
        saved = json.loads(self.cache.read_text())
        saved["baseUrl"] = "http://127.0.0.1:1"
        self.cache.write_text(json.dumps(saved))
        result = cli_initialize(self.config, self.upstream)
        self.assertNotIn("claude-fable-5-2", self.values(result))
        self.assertFalse(self.upstream.requests)


if __name__ == "__main__":
    unittest.main()
