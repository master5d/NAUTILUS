"""
SOVERN Labwatch — AI lab budget & usage dashboard.
Stdlib-only (no pip deps): http.server + sqlite3 + urllib.

Run:  python server.py            → http://localhost:4002
Data: usage.db (written by config/usage_logger.py LiteLLM callback)
      quotas.json (free-tier registry), ../config/orchestrator.json
"""

import http.client
import json
import os
import shutil
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
NAUTILUS = os.path.dirname(HERE)
DB_PATH = os.path.join(HERE, "usage.db")
QUOTAS_PATH = os.path.join(HERE, "quotas.json")
ORCH_PATH = os.path.join(NAUTILUS, "config", "orchestrator.json")
SERVICES_PATH = os.path.join(NAUTILUS, "config", "services.json")
POSTURE_PATH = os.path.join(NAUTILUS, "secops", "posture.json")
STATIC_DIR = os.path.join(HERE, "static")
PORT = 4002
HOME = os.path.expanduser("~")
CLAUDE_HOME = os.environ.get("CLAUDE_HOME", os.path.join(HOME, ".claude"))
EGRESS_LOG = os.path.join(CLAUDE_HOME, "semantic-logger", "egress.jsonl")

_health_cache = {"ts": 0.0, "data": {}}
_health_lock = threading.Lock()
_secops_cache = {"ts": 0.0, "data": {}}
_secops_lock = threading.Lock()


def _local_port_path(url: str):
    """Parse a localhost-only http URL into (port, path). None if not local http."""
    try:
        from urllib.parse import urlparse
        p = urlparse(url)
        if p.scheme == "http" and p.hostname in ("localhost", "127.0.0.1"):
            return p.port or 80, p.path or "/"
    except Exception:
        pass
    return None


def _litellm_url():
    try:
        with open(SERVICES_PATH, encoding="utf-8") as f:
            url = json.load(f)["litellm"]["url"]
            if _local_port_path(url):
                return url
    except Exception:
        pass
    return "http://localhost:4001"


def _probe(name, url):
    """Probe a local service. http.client pinned to 127.0.0.1 — no scheme handlers."""
    parsed = _local_port_path(url)
    if not parsed:
        return name, False
    port, path = parsed
    try:
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
        try:
            conn.request("GET", path, headers={"User-Agent": "labwatch"})
            status = conn.getresponse().status
            return name, (200 <= status < 500)
        finally:
            conn.close()
    except Exception:
        return name, False


def services_health():
    with _health_lock:
        if time.time() - _health_cache["ts"] < 5:
            return _health_cache["data"]
    litellm = _litellm_url()
    targets = {
        "litellm": f"{litellm}/health/liveliness",
        "llama_server": "http://localhost:8080/health",
        "langfuse": "http://localhost:3000/api/public/health",
        "ollama": "http://localhost:11434/api/tags",
    }
    with ThreadPoolExecutor(max_workers=4) as ex:
        results = dict(ex.map(lambda kv: _probe(*kv), targets.items()))
    data = {"endpoints": targets, "up": results, "litellm_url": litellm}
    with _health_lock:
        _health_cache.update(ts=time.time(), data=data)
    return data


def _today_utc_bounds():
    """Local midnight → now, as UTC ISO strings (matches usage_logger UTC timestamps)."""
    local_midnight = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_utc = local_midnight.astimezone(timezone.utc)
    return start_utc.isoformat()


def usage_stats():
    if not os.path.exists(DB_PATH):
        return {"today": {"providers": {}, "agents": {}, "models": {}}, "week": [], "total_rows": 0}
    since = _today_utc_bounds()
    week_since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    c = sqlite3.connect(DB_PATH, timeout=5)
    c.row_factory = sqlite3.Row
    try:
        def agg(group_col, since_ts):
            rows = c.execute(
                f"SELECT {group_col} AS k, COUNT(*) AS calls, "
                "SUM(total_tokens) AS tokens, SUM(prompt_tokens) AS pt, "
                "SUM(completion_tokens) AS ct, "
                "SUM(CASE WHEN status='failure' THEN 1 ELSE 0 END) AS failures "
                f"FROM usage WHERE ts >= ? GROUP BY {group_col}",
                (since_ts,),
            ).fetchall()
            return {r["k"]: {"calls": r["calls"], "tokens": r["tokens"] or 0,
                             "prompt_tokens": r["pt"] or 0, "completion_tokens": r["ct"] or 0,
                             "failures": r["failures"]} for r in rows}

        week = c.execute(
            "SELECT substr(ts, 1, 10) AS day, COUNT(*) AS calls, SUM(total_tokens) AS tokens "
            "FROM usage WHERE ts >= ? GROUP BY day ORDER BY day",
            (week_since,),
        ).fetchall()
        total = c.execute("SELECT COUNT(*) FROM usage").fetchone()[0]
        return {
            "today": {
                "providers": agg("provider", since),
                "agents": agg("agent", since),
                "models": agg("model_group", since),
            },
            "week": [{"day": r["day"], "calls": r["calls"], "tokens": r["tokens"] or 0} for r in week],
            "total_rows": total,
        }
    finally:
        c.close()


def _egress_stats():
    """Tail egress.jsonl (last 64 KB): events/novel domains today + last event ts."""
    out = {"log_exists": os.path.exists(EGRESS_LOG), "events_today": 0,
           "novel_today": 0, "last_event": None}
    if not out["log_exists"]:
        return out
    today = datetime.now(timezone.utc).date().isoformat()
    try:
        size = os.path.getsize(EGRESS_LOG)
        with open(EGRESS_LOG, "rb") as f:
            if size > 65536:
                f.seek(-65536, os.SEEK_END)
                f.readline()  # drop partial line
            for raw in f:
                try:
                    ev = json.loads(raw)
                except Exception:
                    continue
                ts = str(ev.get("ts", ""))
                out["last_event"] = ts or out["last_event"]
                if ts.startswith(today):
                    out["events_today"] += 1
                    if ev.get("new_domain"):
                        out["novel_today"] += 1
    except Exception:
        pass
    return out


def secops_state():
    """Local security-control checks + manually-maintained posture register. Cached 60s."""
    with _secops_lock:
        if time.time() - _secops_cache["ts"] < 60:
            return _secops_cache["data"]
    settings = _read_json(os.path.join(CLAUDE_HOME, "settings.json"))
    deny = (settings.get("permissions") or {}).get("deny") or []
    controls = {
        "gitleaks_cli": bool(shutil.which("gitleaks")),
        "gitleaks_config": os.path.exists(os.path.join(CLAUDE_HOME, "gitleaks.toml")),
        "semgrep_cli": bool(shutil.which("semgrep")),
        "semgrep_login": os.path.exists(os.path.join(HOME, ".semgrep", "settings.yml")),
        "egress_guard_hook": os.path.exists(os.path.join(CLAUDE_HOME, "hooks", "egress-guard.sh")),
        "permission_deny_rules": len(deny),
    }
    posture = _read_json(POSTURE_PATH)
    rotations = posture.get("pending_rotations") or []
    data = {
        "controls": controls,
        "egress": _egress_stats(),
        "posture_as_of": posture.get("as_of"),
        "rotations_pending": [r for r in rotations if r.get("status") != "done"],
        "rotations_done": sum(1 for r in rotations if r.get("status") == "done"),
        "infra_stack": posture.get("infra_stack") or {},
        "agent_attack_classes": posture.get("agent_attack_classes") or {},
        "open_posture_findings": posture.get("open_posture_findings") or [],
        "deploy_targets": posture.get("deploy_targets") or [],
        "accepted_risks": posture.get("accepted_risks") or [],
    }
    with _secops_lock:
        _secops_cache.update(ts=time.time(), data=data)
    return data


def _read_json(path, fallback=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return fallback if fallback is not None else {}


def set_orchestrator(agent: str):
    orch = _read_json(ORCH_PATH)
    if agent not in (orch.get("agents") or {}):
        return False, f"unknown agent: {agent}"
    orch["active"] = agent
    orch["updated"] = datetime.now(timezone.utc).isoformat()
    tmp = ORCH_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(orch, f, ensure_ascii=False, indent=2)
    os.replace(tmp, ORCH_PATH)
    return True, orch


def build_state():
    quotas = _read_json(QUOTAS_PATH)
    usage = usage_stats()
    providers_today = usage["today"]["providers"]
    # Daily free token budget across providers with explicit TPD
    budget_tpd = sum(p["tpd"] for p in quotas.get("providers", {}).values() if p.get("tpd"))
    used_tokens = sum(v["tokens"] for v in providers_today.values())
    return {
        "generated": datetime.now(timezone.utc).isoformat(),
        "services": services_health(),
        "secops": secops_state(),
        "orchestrator": _read_json(ORCH_PATH),
        "quotas": quotas,
        "usage": usage,
        "budget": {
            "free_tpd_capacity": budget_tpd,
            "tokens_today": used_tokens,
            "calls_today": sum(v["calls"] for v in providers_today.values()),
        },
    }


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            try:
                with open(os.path.join(STATIC_DIR, "index.html"), "rb") as f:
                    self._send(200, f.read(), "text/html; charset=utf-8")
            except FileNotFoundError:
                self._send(404, {"error": "index.html missing"})
        elif self.path == "/api/state":
            try:
                self._send(200, build_state())
            except Exception as e:
                self._send(500, {"error": str(e)})
        elif self.path == "/health":
            self._send(200, {"ok": True})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/api/orchestrator":
            try:
                length = int(self.headers.get("Content-Length", 0))
                payload = json.loads(self.rfile.read(length) or b"{}")
                ok, result = set_orchestrator(str(payload.get("active", "")))
                self._send(200 if ok else 400, result if ok else {"error": result})
            except Exception as e:
                self._send(500, {"error": str(e)})
        else:
            self._send(404, {"error": "not found"})

    def log_message(self, fmt, *args):  # quiet
        pass


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"SOVERN Labwatch on http://localhost:{PORT}")
    server.serve_forever()
