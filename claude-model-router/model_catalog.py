"""Anthropic-only gateway discovery without replacing Claude Code's OAuth login."""
import http.client
import json
import os
from pathlib import Path
import re
import tempfile
import threading
import time


MODEL_ID = re.compile(r"claude-[a-z0-9]+(?:-[a-z0-9]+)*(?:\[1m\])?")
MAX_RESPONSE_BYTES = 2 * 1024 * 1024


def anthropic_models(data):
    """Require both a canonical Claude ID and the gateway's Anthropic ownership."""
    if not isinstance(data, dict) or not isinstance(data.get("data"), list):
        raise ValueError("invalid catalog schema")
    if data.get("has_more"):
        raise ValueError("incomplete catalog")
    models = {}
    for item in data["data"]:
        if not isinstance(item, dict):
            continue
        model_id = item.get("id")
        if (not isinstance(model_id, str) or not MODEL_ID.fullmatch(model_id)
                or item.get("owned_by") != "anthropic"):
            continue
        row = {"id": model_id, "owned_by": "anthropic"}
        for field in ("display_name", "description"):
            if isinstance(item.get(field), str):
                row[field] = item[field]
        models.setdefault(model_id, row)
    if not models:
        raise ValueError("catalog contains no Anthropic models")
    return [models[key] for key in sorted(models)]


class ModelCatalog:
    def __init__(self, upstream, key, cache_path, base_url, *, timeout=2, interval=300):
        self.upstream, self.key = upstream, key
        self.cache_path, self.base_url = Path(cache_path), base_url
        self.timeout, self.interval = timeout, interval
        self.models = []
        self.lock = threading.Lock()
        self.stop = threading.Event()
        self.last_error = None
        try:
            saved = json.loads(self.cache_path.read_text())
            if saved.get("baseUrl") == self.base_url:
                self.models = anthropic_models({"data": saved.get("models")})
        except (OSError, ValueError, AttributeError):
            pass

    def refresh(self):
        """Keep the last good catalog on upstream, validation, or filesystem errors."""
        with self.lock:
            scheme, host, port = self.upstream
            connection_class = (http.client.HTTPSConnection if scheme == "https"
                                else http.client.HTTPConnection)
            connection = connection_class(host, port, timeout=self.timeout)
            temporary = None
            response = None
            try:
                connection.request("GET", "/v1/models?limit=1000", headers={
                    "x-api-key": self.key, "Accept": "application/json",
                    "Accept-Encoding": "identity",
                })
                response = connection.getresponse()
                if response.status != 200:
                    raise ValueError(f"catalog HTTP {response.status}")
                raw = response.read(MAX_RESPONSE_BYTES + 1)
                if len(raw) > MAX_RESPONSE_BYTES:
                    raise ValueError("catalog response too large")
                models = anthropic_models(json.loads(raw))
                payload = json.dumps({"baseUrl": self.base_url,
                                      "fetchedAt": int(time.time() * 1000),
                                      "models": models})
                self.cache_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8",
                                                 dir=self.cache_path.parent,
                                                 prefix=".gateway-models-", delete=False) as file:
                    temporary = Path(file.name)
                    os.chmod(temporary, 0o600)
                    file.write(payload)
                    file.flush()
                    os.fsync(file.fileno())
                os.replace(temporary, self.cache_path)
                temporary = None
                self.models, self.last_error = models, None
                return True
            except (OSError, ValueError, http.client.HTTPException) as error:
                self.last_error = type(error).__name__
                return False
            finally:
                if response is not None:
                    response.close()
                connection.close()
                if temporary is not None:
                    try:
                        temporary.unlink(missing_ok=True)
                    except OSError:
                        pass

    def start(self):
        def run():
            while not self.stop.is_set():
                self.refresh()
                self.stop.wait(self.interval)
        thread = threading.Thread(target=run, name="model-catalog", daemon=True)
        thread.start()
        return thread
