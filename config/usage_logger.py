"""
SOVERN Labwatch — LiteLLM custom callback.
Logs every request passing through the gateway into a local SQLite DB
(sovereign usage tracking, no Postgres / no cloud dependency).

Wired in litellm-config.yaml:
    litellm_settings:
      callbacks: usage_logger.usage_tracker

DB: C:\\telo\\Efforts\\Ongoing\\NAUTILUS\\labwatch\\usage.db
Read by the Labwatch dashboard (labwatch/server.py, port 4002).
"""

import os
import sqlite3
import threading
import traceback
from datetime import datetime, timezone

from litellm.integrations.custom_logger import CustomLogger

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "labwatch", "usage.db",
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    model_group TEXT,
    model TEXT,
    provider TEXT,
    agent TEXT,
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    status TEXT,
    latency_ms REAL,
    error TEXT
);
CREATE INDEX IF NOT EXISTS idx_usage_ts ON usage(ts);
CREATE INDEX IF NOT EXISTS idx_usage_provider ON usage(provider);
CREATE INDEX IF NOT EXISTS idx_usage_agent ON usage(agent);
"""

_lock = threading.Lock()

# Agent attribution: api keys agents present to the gateway → agent name.
KEY_AGENT_MAP = {
    "sk-hermes": "hermes",
    "sk-claude": "claude",
    "sk-codex": "codex",
    "sk-gemini": "gemini",
    "sk-antigravity": "antigravity",
    "sk-n8n": "n8n",
    "sk-hooks": "hooks",
}


def _conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    c = sqlite3.connect(DB_PATH, timeout=10)
    c.executescript(_SCHEMA)
    return c


def _provider_from(kwargs, model: str) -> str:
    lp = kwargs.get("litellm_params") or {}
    api_base = str(lp.get("api_base") or "")
    if "localhost:8080" in api_base or "127.0.0.1:8080" in api_base:
        return "local"
    if "integrate.api.nvidia.com" in api_base:
        return "nvidia_nim"
    if "router.huggingface.co" in api_base:
        return "huggingface"
    custom = lp.get("custom_llm_provider") or kwargs.get("custom_llm_provider")
    if custom and custom != "openai":
        return str(custom)
    if "/" in model:
        prefix = model.split("/", 1)[0]
        if prefix in ("cerebras", "groq", "gemini", "openrouter"):
            return prefix
    return "other"


def _agent_from(kwargs) -> str:
    """Best-effort agent attribution: explicit header → api key → user field."""
    lp = kwargs.get("litellm_params") or {}
    meta = lp.get("metadata") or {}
    # 1. Explicit header
    headers = (lp.get("proxy_server_request") or {}).get("headers") or meta.get("headers") or {}
    if isinstance(headers, dict):
        for k, v in headers.items():
            if str(k).lower() == "x-sovern-agent" and v:
                return str(v).lower()
        auth = headers.get("authorization") or headers.get("Authorization") or ""
        token = str(auth).replace("Bearer ", "").strip()
        if token in KEY_AGENT_MAP:
            return KEY_AGENT_MAP[token]
    # 2. Virtual-key metadata (if litellm auth in use)
    for key_field in ("user_api_key_alias", "user_api_key"):
        v = meta.get(key_field)
        if v in KEY_AGENT_MAP:
            return KEY_AGENT_MAP[v]
    # 3. OpenAI `user` param
    user = (kwargs.get("optional_params") or {}).get("user") or kwargs.get("user")
    if user:
        return str(user).lower()
    return "unattributed"


def _tokens_from(response_obj):
    pt = ct = tt = 0
    try:
        usage = getattr(response_obj, "usage", None)
        if usage is None and isinstance(response_obj, dict):
            usage = response_obj.get("usage")
        if usage is not None:
            pt = int(getattr(usage, "prompt_tokens", 0) or (usage.get("prompt_tokens", 0) if isinstance(usage, dict) else 0) or 0)
            ct = int(getattr(usage, "completion_tokens", 0) or (usage.get("completion_tokens", 0) if isinstance(usage, dict) else 0) or 0)
            tt = int(getattr(usage, "total_tokens", 0) or (usage.get("total_tokens", 0) if isinstance(usage, dict) else 0) or (pt + ct))
    except Exception:
        pass
    return pt, ct, tt


def _latency_ms(start_time, end_time) -> float:
    try:
        return (end_time - start_time).total_seconds() * 1000.0
    except Exception:
        return 0.0


class SovernUsageTracker(CustomLogger):
    def _write(self, kwargs, response_obj, start_time, end_time, status: str, error: str = ""):
        try:
            model = kwargs.get("model") or ""
            lp = kwargs.get("litellm_params") or {}
            meta = lp.get("metadata") or {}
            model_group = meta.get("model_group") or model
            pt, ct, tt = _tokens_from(response_obj)
            row = (
                datetime.now(timezone.utc).isoformat(),
                str(model_group),
                str(model),
                _provider_from(kwargs, model),
                _agent_from(kwargs),
                pt, ct, tt,
                status,
                _latency_ms(start_time, end_time),
                (error or "")[:500],
            )
            with _lock:
                c = _conn()
                try:
                    c.execute(
                        "INSERT INTO usage (ts, model_group, model, provider, agent, "
                        "prompt_tokens, completion_tokens, total_tokens, status, latency_ms, error) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        row,
                    )
                    c.commit()
                finally:
                    c.close()
        except Exception:
            # Never break the gateway because of logging.
            traceback.print_exc()

    # --- sync ---
    def log_success_event(self, kwargs, response_obj, start_time, end_time):
        self._write(kwargs, response_obj, start_time, end_time, "success")

    def log_failure_event(self, kwargs, response_obj, start_time, end_time):
        err = str(kwargs.get("exception") or "")
        self._write(kwargs, response_obj, start_time, end_time, "failure", err)

    # --- async (proxy uses these) ---
    async def async_log_success_event(self, kwargs, response_obj, start_time, end_time):
        self._write(kwargs, response_obj, start_time, end_time, "success")

    async def async_log_failure_event(self, kwargs, response_obj, start_time, end_time):
        err = str(kwargs.get("exception") or "")
        self._write(kwargs, response_obj, start_time, end_time, "failure", err)


usage_tracker = SovernUsageTracker()
