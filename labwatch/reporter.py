"""Reporter: collect THIS host's own state, sign it, POST to the collector.

Phase 0 = M4 self-report. Single file (probes + host metrics + M4 domain +
build/sign/post + loop); split per-host when more hosts arrive.
"""

import http.client
import json
import os
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
