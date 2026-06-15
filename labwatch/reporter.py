"""Reporter: collect THIS host's own state, sign it, POST to the collector.

Phase 0 = M4 self-report. Single file (probes + host metrics + M4 domain +
build/sign/post + loop); split per-host when more hosts arrive.
"""

import glob
import http.client
import json
import os
import re
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

import keys as keymod

# --- service probes (localhost only — each host probes its OWN services) ----

def probe(name: str, url: str, timeout: float = 2.0) -> dict:
    p = urlparse(url)
    port = p.port or (443 if p.scheme == "https" else 80)
    path = p.path or "/"
    t0 = time.time()
    try:
        conn = http.client.HTTPConnection(p.hostname or "127.0.0.1", port, timeout=timeout)
        try:
            conn.request("GET", path, headers={"User-Agent": "labwatch-reporter"})
            status = conn.getresponse().status
            up = 200 <= status < 500
        finally:
            conn.close()
    except Exception:
        return {"name": name, "port": port, "up": False, "latency_ms": None}
    return {"name": name, "port": port, "up": up,
            "latency_ms": round((time.time() - t0) * 1000, 1)}


def probe_all(services_cfg) -> list:
    return [probe(name, url) for name, url in services_cfg]


# --- host metrics (psutil, best-effort per platform) -----------------------

def host_metrics() -> dict:
    import psutil
    vm = psutil.virtual_memory()
    try:
        disk = psutil.disk_usage("/").percent
    except Exception:
        disk = None
    temp = None
    try:
        sensors = psutil.sensors_temperatures()  # absent on macOS/Windows → {}
        if sensors:
            first = next(iter(sensors.values()))
            if first:
                temp = float(first[0].current)
    except Exception:
        temp = None
    return {
        "cpu_pct": float(psutil.cpu_percent(interval=0.1)),
        "ram_used_gb": round((vm.total - vm.available) / 1e9, 2),
        "ram_total_gb": round(vm.total / 1e9, 2),
        "disk_pct": float(disk) if disk is not None else None,
        "temp_c": temp,
        "power_w": None,
    }


# --- M4 domain (reuse existing labwatch collectors) ------------------------

def domain_m4() -> dict:
    import server
    return {
        "usage": server.usage_stats(),
        "secops": server.secops_state(),
        "quotas": server._read_json(server.QUOTAS_PATH),
        "econ": server._read_json(server.ECON_PATH),
    }


# --- Surface domain: agent-CLI usage signals (port of collect-wallets.ps1) --
# "Wallets" = how much of each delegate agent's free tier was used today.
# These read the same on-disk signals the PowerShell collector read.

def _codex_tokens(home: str, today) -> int:
    """Sum the LAST token_count.total_tokens per Codex session file for today."""
    d = os.path.join(home, ".codex", "sessions",
                     f"{today.year}", f"{today.month:02d}", f"{today.day:02d}")
    if not os.path.isdir(d):
        return 0
    total = 0
    for fn in glob.glob(os.path.join(d, "rollout-*.jsonl")):
        last = None
        try:
            with open(fn, encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if '"type":"token_count"' in line or '"type": "token_count"' in line:
                        last = line
        except OSError:
            continue
        if last:
            m = re.search(r'"total_tokens":\s*(\d+)', last)
            if m:
                total += int(m.group(1))
    return total


def _gemini_requests(home: str, today) -> int:
    """Count '"type":"gemini"' turns in Gemini-CLI session files modified today."""
    base = os.path.join(home, ".gemini", "tmp")
    if not os.path.isdir(base):
        return 0
    n = 0
    for root, _dirs, files in os.walk(base):
        for fn in files:
            if not fn.endswith(".jsonl"):
                continue
            p = os.path.join(root, fn)
            try:
                if datetime.fromtimestamp(os.path.getmtime(p)).date() != today:
                    continue
                with open(p, encoding="utf-8", errors="ignore") as f:
                    n += f.read().count('"type":"gemini"')
            except OSError:
                continue
    return n


def _agy_runs(home: str, today) -> int:
    """Count Antigravity brain subdirectories modified today."""
    base = os.path.join(home, ".gemini", "antigravity-cli", "brain")
    if not os.path.isdir(base):
        return 0
    n = 0
    for name in os.listdir(base):
        p = os.path.join(base, name)
        try:
            if os.path.isdir(p) and datetime.fromtimestamp(os.path.getmtime(p)).date() == today:
                n += 1
        except OSError:
            continue
    return n


def domain_surface(home: str = None, today=None) -> dict:
    home = home or os.path.expanduser("~")
    today = today or datetime.now().date()
    agents = {
        "codex":       {"used_today": _codex_tokens(home, today), "unit": "tokens",
                        "budget": None, "signal": "session logs", "confidence": "medium"},
        "gemini-cli":  {"used_today": _gemini_requests(home, today), "unit": "requests",
                        "budget": None, "signal": "session logs", "confidence": "high"},
        "antigravity": {"used_today": _agy_runs(home, today), "unit": "requests",
                        "budget": 20, "signal": "brain dirs", "confidence": "medium"},
        "claude":      {"used_today": None, "unit": "requests",
                        "budget": None, "signal": "unknown", "confidence": "low"},
    }
    return {"wallets": {"as_of": datetime.now(timezone.utc).isoformat(), "agents": agents}}


# --- assemble + sign + post ------------------------------------------------

_UNSET = object()


def build_payload(services_cfg, domain=_UNSET) -> dict:
    # domain omitted  -> default to domain_m4() (the M4 self-report case)
    # domain=None/{}   -> no domain block (non-M4 hosts in later phases)
    # domain=<dict>    -> use it verbatim
    payload = {
        "services": probe_all(services_cfg),
        "host_metrics": host_metrics(),
    }
    dom = domain_m4() if domain is _UNSET else domain
    if dom:
        payload["domain"] = dom
    return payload


def sign_envelope(host: str, payload: dict, master: bytes) -> bytes:
    canon = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    sig = keymod.sign_payload(master, canon)
    env = {"host": host, "ts": datetime.now(timezone.utc).isoformat(),
           "sig": sig, "payload": payload}
    return json.dumps(env).encode("utf-8")


def post_snapshot(ingest_url: str, host: str, master: bytes, body: bytes,
                  spool_path: str = None) -> bool:
    p = urlparse(ingest_url)
    headers = {"Authorization": "Bearer " + keymod.bearer_token(master),
               "Content-Type": "application/json"}
    try:
        conn = http.client.HTTPConnection(p.hostname, p.port or 80, timeout=5)
        conn.request("POST", p.path or "/ingest", body=body, headers=headers)
        ok = conn.getresponse().status == 200
        conn.close()
    except Exception:
        ok = False
    if not ok and spool_path:
        try:
            with open(spool_path, "ab") as f:
                f.write(body + b"\n")
        except OSError:
            pass
    return ok


# --- config + main loop -------------------------------------------------------

DEFAULT_SERVICES = {
    "m4": [
        ("litellm", "http://127.0.0.1:4000/health/liveliness"),
        ("stt", "http://127.0.0.1:4100/health"),
        ("labwatch", "http://127.0.0.1:4002/health"),
    ],
    "surface": [
        ("ollama", "http://127.0.0.1:11434/api/tags"),
    ],
}


def load_master(host: str, keyring_path: str = None) -> bytes:
    kr = keymod.load_keyring(keyring_path or keymod.KEYRING_PATH)
    return keymod.material(kr, host, keymod.active_key_id(kr, host))


def run_once(host: str, ingest_url: str, services_cfg, keyring_path: str = None,
             spool_path: str = None) -> bool:
    master = load_master(host, keyring_path)
    # Resolve the host's domain block by name (looked up at call time so tests
    # can monkeypatch domain_m4 / domain_surface).
    if host == "m4":
        domain = domain_m4()
    elif host == "surface":
        domain = domain_surface()
    else:
        domain = None
    payload = build_payload(services_cfg, domain=domain)
    body = sign_envelope(host, payload, master)
    return post_snapshot(ingest_url, host, master, body, spool_path=spool_path)


def main():
    host = os.environ.get("REPORTER_HOST", "m4")
    ingest = os.environ.get("INGEST_URL", "http://127.0.0.1:4002/ingest")
    interval = int(os.environ.get("REPORTER_INTERVAL", "30"))
    spool = os.environ.get("REPORTER_SPOOL", os.path.join(os.path.dirname(__file__), "spool.jsonl"))
    services = DEFAULT_SERVICES.get(host, [])
    while True:
        try:
            run_once(host, ingest, services, spool_path=spool)
        except Exception as e:  # never let the loop die
            print(f"[reporter] cycle error: {type(e).__name__}", flush=True)
        time.sleep(interval)


if __name__ == "__main__":
    main()
