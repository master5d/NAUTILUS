# NAUTILUS Observability — Phase 2a Implementation Plan (Watchers & Alerts)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the collector's empty `alerts: []` into real, persisted alerts: a pure named-evaluator rules engine detects violations from each host's snapshot, a firing/resolved lifecycle persists them, and `/api/state`/`/api/alerts` expose them so the already-wired tray indicator and toasts light up.

**Architecture:** `watchers.py` is a side-effect-free engine — one named evaluator per rule type, **no `eval()`**, driven by `watchers.json`. `collector.tick()` runs assemble→evaluate→reconcile; the lifecycle lives in `store.py` (firing/resolved on the existing `alerts` table, identity `(id, host)`, per-target rules encode the target in `id`). The server runs a tick on every `/ingest` and on a background timer (so `host-silent` fires even when a host stops reporting).

**Tech Stack:** Python 3.13 stdlib (`sqlite3`, `http.server`, `threading`, `json`). Tests: `pytest`. No new dependencies.

**Plan deps:** Builds on merged Phase 1b. Reuses `store.alerts` table (cols `id, host, severity, state, first_seen, last_seen, resolved_at`, PK `(id, host)`), `collector.assemble_state`, `server` ingest path.

**Explicitly rejected from the machine draft:** the `eval()`-based generic engine (injection risk — unacceptable for a security-first mesh) and the Flask/`core/` layout (we are stdlib `http.server` + flat modules). We keep only the rule-catalog shape and firing/resolved concept.

---

## Scope

Phase 2a = local alerting end-to-end **without Telegram**. Rules computable from existing state: `service-down`, `host-silent`, `disk-pressure`, `ram-pressure`, `secops-pending`, `egress-anomaly`. Deferred:
- **Phase 2b:** Telegram escape for `critical` (needs bot token + chat config). `watchers.json` already tags `channels:["tray","telegram"]` so 2b only adds the sender.
- **Phase 3:** `fallback-spike`, `deprecation-soon`, `backup-stale` (their data sources — gateway fallback-rate, deprecation calendar, backup mtime — are added in the advisory tier).

The tray (Phase 1b) already toasts new alerts and reddens on `critical`; no tray change is needed here.

## File structure (Phase 2a)

| File | Change | Responsibility |
|------|--------|----------------|
| `labwatch/watchers.py` | Create | Pure `evaluate(state, rules) -> [alert]` — named evaluators, no eval. |
| `labwatch/watchers.json` | Create | Rule catalog keyed by type: `{enabled, severity, threshold, channels}`. |
| `labwatch/store.py` | Modify | `reconcile_alerts(conn, fired, now)` lifecycle + `get_active_alerts(conn, now, linger_min)`. |
| `labwatch/collector.py` | Modify | `tick(conn, rules, now)` = assemble→evaluate→reconcile; `assemble_state` reads active alerts from store. |
| `labwatch/server.py` | Modify | Load `watchers.json` at init; `/ingest` runs a tick; background timer tick; `GET /api/alerts`. |
| `labwatch/tests/test_watchers.py` | Create | Per-rule fixtures. |
| `labwatch/tests/test_store.py` | Modify | Alert lifecycle tests. |
| `labwatch/tests/test_collector.py` | Modify | `tick` + assemble-with-alerts. |
| `labwatch/tests/test_server_alerts.py` | Create | Ingest a down service → `/api/alerts` shows it. |

**Alert shape (engine output):** `{"id": str, "host": str, "severity": str, "message": str, "channels": [str]}`. **Stored row:** `id, host, severity, state(firing|resolved), first_seen, last_seen, resolved_at`.

---

## Task 1: Pure watchers engine + rule catalog

**Files:**
- Create: `labwatch/watchers.py`, `labwatch/watchers.json`
- Test: `labwatch/tests/test_watchers.py`

- [ ] **Step 1: Write the failing test**

Create `labwatch/tests/test_watchers.py`:
```python
import watchers

RULES = {
    "service-down":   {"enabled": True, "severity": "critical", "channels": ["tray", "telegram"]},
    "host-silent":    {"enabled": True, "severity": "critical", "channels": ["tray", "telegram"]},
    "disk-pressure":  {"enabled": True, "severity": "warning", "threshold": 90, "channels": ["tray"]},
    "ram-pressure":   {"enabled": True, "severity": "warning", "threshold": 90, "channels": ["tray"]},
    "secops-pending": {"enabled": True, "severity": "warning", "channels": ["tray"]},
    "egress-anomaly": {"enabled": True, "severity": "critical", "threshold": 0, "channels": ["tray", "telegram"]},
}


def _state(host="m4", freshness="live", services=None, hm=None, domain=None):
    return {"hosts": {host: {"freshness": freshness, "payload": {
        "services": services or [], "host_metrics": hm or {}, "domain": domain or {}}}}}


def test_service_down_fires_per_service():
    st = _state(services=[{"name": "litellm", "up": True}, {"name": "stt", "up": False}])
    fired = watchers.evaluate(st, RULES)
    ids = {a["id"] for a in fired}
    assert ids == {"service-down:stt"}
    assert fired[0]["host"] == "m4" and fired[0]["severity"] == "critical"


def test_host_silent_fires_on_down_freshness():
    fired = watchers.evaluate(_state(freshness="down"), RULES)
    assert any(a["id"] == "host-silent" for a in fired)


def test_host_silent_not_fired_when_live():
    assert not any(a["id"] == "host-silent" for a in watchers.evaluate(_state(freshness="live"), RULES))


def test_disk_pressure_threshold():
    assert any(a["id"] == "disk-pressure" for a in watchers.evaluate(_state(hm={"disk_pct": 95.0}), RULES))
    assert not any(a["id"] == "disk-pressure" for a in watchers.evaluate(_state(hm={"disk_pct": 80.0}), RULES))


def test_ram_pressure_uses_ratio():
    st = _state(hm={"ram_used_gb": 15.2, "ram_total_gb": 16.0})  # 95%
    assert any(a["id"] == "ram-pressure" for a in watchers.evaluate(st, RULES))
    st2 = _state(hm={"ram_used_gb": 8.0, "ram_total_gb": 16.0})  # 50%
    assert not any(a["id"] == "ram-pressure" for a in watchers.evaluate(st2, RULES))


def test_secops_pending_fires():
    st = _state(domain={"secops": {"rotations_pending": [{"x": 1}, {"y": 2}]}})
    fired = [a for a in watchers.evaluate(st, RULES) if a["id"] == "secops-pending"]
    assert fired and "2" in fired[0]["message"]


def test_egress_anomaly_fires_on_novel():
    st = _state(domain={"secops": {"egress": {"novel_today": 3}}})
    assert any(a["id"] == "egress-anomaly" for a in watchers.evaluate(st, RULES))


def test_disabled_rule_does_not_fire():
    rules = dict(RULES, **{"disk-pressure": {"enabled": False, "severity": "warning", "threshold": 90}})
    assert not any(a["id"] == "disk-pressure" for a in watchers.evaluate(_state(hm={"disk_pct": 99.0}), rules))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest labwatch/tests/test_watchers.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'watchers'`).

- [ ] **Step 3: Create `labwatch/watchers.py`**

```python
"""Pure watchers rules engine — maps an /api/state snapshot to fired alerts.

NO eval(): each rule type is a named evaluator. Rules come from watchers.json,
keyed by type with {enabled, severity, threshold, channels}. Alert identity is
(id, host); per-target rules encode the target in id ("service-down:litellm").
"""


def _alert(aid, host, rule, message):
    return {
        "id": aid,
        "host": host,
        "severity": rule.get("severity", "warning"),
        "message": message,
        "channels": rule.get("channels", ["tray"]),
    }


def evaluate(state, rules) -> list:
    fired = []
    for host, h in (state.get("hosts") or {}).items():
        payload = h.get("payload") or {}
        hm = payload.get("host_metrics") or {}
        secops = (payload.get("domain") or {}).get("secops") or {}

        r = rules.get("host-silent") or {}
        if r.get("enabled") and h.get("freshness") == "down":
            fired.append(_alert("host-silent", host, r, f"{host} silent — no snapshot"))

        r = rules.get("service-down") or {}
        if r.get("enabled"):
            for s in payload.get("services") or []:
                if s.get("up") is False:
                    name = s.get("name", "?")
                    fired.append(_alert(f"service-down:{name}", host, r, f"{name} down on {host}"))

        r = rules.get("disk-pressure") or {}
        disk = hm.get("disk_pct")
        if r.get("enabled") and isinstance(disk, (int, float)) and disk > r.get("threshold", 90):
            fired.append(_alert("disk-pressure", host, r, f"disk {disk:.0f}% on {host}"))

        r = rules.get("ram-pressure") or {}
        used, total = hm.get("ram_used_gb"), hm.get("ram_total_gb")
        if (r.get("enabled") and isinstance(used, (int, float))
                and isinstance(total, (int, float)) and total > 0):
            pct = used / total * 100
            if pct > r.get("threshold", 90):
                fired.append(_alert("ram-pressure", host, r, f"ram {pct:.0f}% on {host}"))

        r = rules.get("secops-pending") or {}
        pend = secops.get("rotations_pending")
        if r.get("enabled") and isinstance(pend, list) and len(pend) > 0:
            fired.append(_alert("secops-pending", host, r, f"{len(pend)} secret rotation(s) pending"))

        r = rules.get("egress-anomaly") or {}
        nov = (secops.get("egress") or {}).get("novel_today")
        if r.get("enabled") and isinstance(nov, int) and nov > r.get("threshold", 0):
            fired.append(_alert("egress-anomaly", host, r, f"{nov} novel egress domain(s) today"))
    return fired
```

- [ ] **Step 4: Create `labwatch/watchers.json`**

```json
{
  "service-down":   {"enabled": true, "severity": "critical", "channels": ["tray", "telegram"]},
  "host-silent":    {"enabled": true, "severity": "critical", "channels": ["tray", "telegram"]},
  "disk-pressure":  {"enabled": true, "severity": "warning", "threshold": 90, "channels": ["tray"]},
  "ram-pressure":   {"enabled": true, "severity": "warning", "threshold": 90, "channels": ["tray"]},
  "secops-pending": {"enabled": true, "severity": "warning", "channels": ["tray"]},
  "egress-anomaly": {"enabled": true, "severity": "critical", "threshold": 0, "channels": ["tray", "telegram"]}
}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest labwatch/tests/test_watchers.py -v`
Expected: PASS (8 passed).

- [ ] **Step 6: Commit**

```bash
git add labwatch/watchers.py labwatch/watchers.json labwatch/tests/test_watchers.py
git commit -m "feat(watchers): pure named-evaluator rules engine + rule catalog (no eval)"
```

---

## Task 2: Alert lifecycle in the store

**Files:**
- Modify: `labwatch/store.py`
- Test: `labwatch/tests/test_store.py`

- [ ] **Step 1: Write the failing test (append)**

Append to `labwatch/tests/test_store.py`:
```python
def test_reconcile_fires_then_resolves_then_lingers():
    conn = store.connect(":memory:")
    store.init_db(conn)
    now = datetime.now(timezone.utc)

    # tick 1: one alert fires
    store.reconcile_alerts(conn, [{"id": "service-down:stt", "host": "m4", "severity": "critical"}], now_dt=now)
    active = store.get_active_alerts(conn, now_dt=now)
    assert len(active) == 1 and active[0]["state"] == "firing"
    first_seen = active[0]["first_seen"]

    # tick 2: same alert still firing -> first_seen preserved, last_seen advances
    later = now + timedelta(seconds=30)
    store.reconcile_alerts(conn, [{"id": "service-down:stt", "host": "m4", "severity": "critical"}], now_dt=later)
    active = store.get_active_alerts(conn, now_dt=later)
    assert active[0]["first_seen"] == first_seen
    assert active[0]["last_seen"] != first_seen

    # tick 3: alert clears -> resolved, but lingers in active for the window
    later2 = later + timedelta(seconds=30)
    store.reconcile_alerts(conn, [], now_dt=later2)
    active = store.get_active_alerts(conn, now_dt=later2)
    assert len(active) == 1 and active[0]["state"] == "resolved"

    # much later -> dropped from active (past linger window)
    way_later = later2 + timedelta(minutes=31)
    assert store.get_active_alerts(conn, now_dt=way_later) == []


def test_resolved_then_refires_clears_resolved_at():
    conn = store.connect(":memory:")
    store.init_db(conn)
    now = datetime.now(timezone.utc)
    a = {"id": "host-silent", "host": "surface", "severity": "critical"}
    store.reconcile_alerts(conn, [a], now_dt=now)
    store.reconcile_alerts(conn, [], now_dt=now + timedelta(seconds=10))   # resolve
    store.reconcile_alerts(conn, [a], now_dt=now + timedelta(seconds=20))  # refire
    active = store.get_active_alerts(conn, now_dt=now + timedelta(seconds=20))
    assert len(active) == 1 and active[0]["state"] == "firing"
    assert active[0]["resolved_at"] is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest labwatch/tests/test_store.py -k "reconcile or refires" -v`
Expected: FAIL (`AttributeError: module 'store' has no attribute 'reconcile_alerts'`).

- [ ] **Step 3: Append to `labwatch/store.py`**

```python
def reconcile_alerts(conn, fired: list, now_dt: datetime = None):
    """Upsert currently-fired alerts as 'firing'; mark previously-firing alerts
    that are no longer fired as 'resolved'. Alert identity is (id, host)."""
    now = (now_dt or datetime.now(timezone.utc)).isoformat()
    fired_keys = {(a["id"], a["host"]) for a in fired}
    for a in fired:
        conn.execute(
            "INSERT INTO alerts (id, host, severity, state, first_seen, last_seen, resolved_at) "
            "VALUES (?, ?, ?, 'firing', ?, ?, NULL) "
            "ON CONFLICT(id, host) DO UPDATE SET state='firing', severity=excluded.severity, "
            "last_seen=excluded.last_seen, resolved_at=NULL",
            (a["id"], a["host"], a.get("severity", "warning"), now, now),
        )
    for row in conn.execute("SELECT id, host FROM alerts WHERE state='firing'").fetchall():
        if (row["id"], row["host"]) not in fired_keys:
            conn.execute(
                "UPDATE alerts SET state='resolved', resolved_at=? WHERE id=? AND host=?",
                (now, row["id"], row["host"]),
            )
    conn.commit()


def get_active_alerts(conn, now_dt: datetime = None, linger_min: int = 30) -> list:
    """Firing alerts + recently-resolved ones (within linger_min) so the UI can
    show what just cleared. Each item is a plain dict of the alert row."""
    now_dt = now_dt or datetime.now(timezone.utc)
    out = []
    for r in conn.execute(
        "SELECT id, host, severity, state, first_seen, last_seen, resolved_at FROM alerts"
    ):
        if r["state"] == "firing":
            out.append(dict(r))
        elif r["resolved_at"]:
            try:
                if (now_dt - _parse(r["resolved_at"])).total_seconds() <= linger_min * 60:
                    out.append(dict(r))
            except Exception:
                pass
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest labwatch/tests/test_store.py -v`
Expected: PASS (all store tests).

- [ ] **Step 5: Commit**

```bash
git add labwatch/store.py labwatch/tests/test_store.py
git commit -m "feat(store): alert firing/resolved lifecycle + active-alerts with linger window"
```

---

## Task 3: collector.tick + assemble_state reads alerts

**Files:**
- Modify: `labwatch/collector.py`
- Test: `labwatch/tests/test_collector.py`

- [ ] **Step 1: Write the failing test (append)**

Append to `labwatch/tests/test_collector.py`:
```python
import watchers as _watchers  # noqa: E402


def test_tick_fires_service_down_and_assemble_includes_it():
    conn = store.connect(":memory:")
    store.init_db(conn)
    now = datetime.now(timezone.utc)
    payload = {"services": [{"name": "ollama", "port": 11434, "up": False}],
               "host_metrics": {"cpu_pct": 5.0}}
    store.upsert_snapshot(conn, "surface", now.isoformat(), payload)
    rules = {"service-down": {"enabled": True, "severity": "critical", "channels": ["tray"]}}

    state, fired = collector.tick(conn, rules, now_dt=now)
    assert any(a["id"] == "service-down:ollama" for a in fired)

    state2 = collector.assemble_state(conn, now_dt=now)
    ids = {a["id"] for a in state2["alerts"]}
    assert "service-down:ollama" in ids
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest labwatch/tests/test_collector.py -k tick -v`
Expected: FAIL (`AttributeError: module 'collector' has no attribute 'tick'`).

- [ ] **Step 3: Modify `labwatch/collector.py`**

(a) Add `import watchers as watchersmod` to the imports (next to `import schema as schemamod`).

(b) Replace `assemble_state` with the version that reads alerts from the store:
```python
def assemble_state(conn, now_dt: datetime = None) -> dict:
    now_dt = now_dt or datetime.now(timezone.utc)
    hosts = storemod.get_snapshots(conn, now_dt=now_dt)
    return {
        "generated": now_dt.isoformat(),
        "hosts": hosts,
        "alerts": storemod.get_active_alerts(conn, now_dt=now_dt),
    }
```

(c) Add `tick` at the end of the module:
```python
def tick(conn, rules, now_dt: datetime = None):
    """One evaluation cycle: assemble state, evaluate rules, reconcile alerts.
    Returns (state, fired_alerts)."""
    state = assemble_state(conn, now_dt=now_dt)
    fired = watchersmod.evaluate(state, rules)
    storemod.reconcile_alerts(conn, fired, now_dt=now_dt)
    return state, fired
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest labwatch/tests/test_collector.py -v`
Expected: PASS (all collector tests, incl. the existing `test_assemble_state_shape` which still sees `alerts == []` on an empty DB).

- [ ] **Step 5: Commit**

```bash
git add labwatch/collector.py labwatch/tests/test_collector.py
git commit -m "feat(collector): tick (assemble→evaluate→reconcile) + assemble_state reads active alerts"
```

---

## Task 4: Server wiring — run ticks, expose /api/alerts

**Files:**
- Modify: `labwatch/server.py`
- Test: `labwatch/tests/test_server_alerts.py`

- [ ] **Step 1: Write the failing integration test**

Create `labwatch/tests/test_server_alerts.py`:
```python
import base64
import json
import threading
from datetime import datetime, timezone

import http.client

import keys


def _b64(raw):
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _start(tmp_path, monkeypatch):
    import server
    master = b"\x66" * 32
    krp = tmp_path / "kr.json"
    krp.write_text(json.dumps({"hosts": {"surface": {"active": "s-1",
        "keys": {"s-1": {"material": _b64(master), "created": "t", "revoked": False}}}}}),
        encoding="utf-8")
    monkeypatch.setattr(server, "KEYRING_PATH", str(krp))
    monkeypatch.setattr(server, "DB_PATH_OBS", str(tmp_path / "labwatch.db"))
    httpd = server.make_server(("127.0.0.1", 0))
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, port, master


def _ingest(port, master, payload):
    canon = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    env = json.dumps({"host": "surface", "ts": datetime.now(timezone.utc).isoformat(),
                      "sig": keys.sign_payload(master, canon), "payload": payload}).encode()
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    c.request("POST", "/ingest", body=env,
              headers={"Authorization": "Bearer " + keys.bearer_token(master)})
    st = c.getresponse().status
    c.close()
    return st


def test_ingest_down_service_surfaces_in_api_alerts(tmp_path, monkeypatch):
    httpd, port, master = _start(tmp_path, monkeypatch)
    try:
        payload = {"services": [{"name": "ollama", "port": 11434, "up": False}],
                   "host_metrics": {"cpu_pct": 1.0}}
        assert _ingest(port, master, payload) == 200

        c = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        c.request("GET", "/api/alerts")
        body = json.loads(c.getresponse().read()); c.close()
        ids = {a["id"] for a in body["alerts"]}
        assert "service-down:ollama" in ids
        assert body["max_severity"] == "critical"
    finally:
        httpd.shutdown()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest labwatch/tests/test_server_alerts.py -v`
Expected: FAIL (no `/api/alerts` route → KeyError/404).

- [ ] **Step 3: Modify `labwatch/server.py` — load rules + tick on ingest**

(a) Add constants after the existing `DB_PATH_OBS` block:
```python
WATCHERS_PATH = os.path.join(HERE, "watchers.json")
WATCH_INTERVAL = 30          # seconds between background watcher ticks
RULES = {}
```

(b) In `init_observability()`, after `storemod.init_db(_obs_conn)`, load the rules:
```python
    global RULES
    RULES = _read_json(WATCHERS_PATH)
```

(c) In `Handler.do_POST`, in the `/ingest` branch, after the successful `storemod.upsert_snapshot(...)` line, run a tick (still inside the `with _obs_lock:` block):
```python
                with _obs_lock:
                    storemod.upsert_snapshot(_obs_conn, host, ts, payload)
                    collector.tick(_obs_conn, RULES)
```
(Replace the existing single-line `with _obs_lock: storemod.upsert_snapshot(...)` so both calls share the lock.)

- [ ] **Step 4: Modify `labwatch/server.py` — /api/alerts route + background timer**

(a) In `Handler.do_GET`, add a branch alongside `/api/state`:
```python
        elif self.path == "/api/alerts":
            with _obs_lock:
                alerts = storemod.get_active_alerts(_obs_conn)
            order = {"critical": 2, "warning": 1}
            max_sev = "none"
            if alerts:
                max_sev = max((a["severity"] for a in alerts), key=lambda s: order.get(s, 0))
            self._send(200, {"alerts": alerts, "max_severity": max_sev})
            return
```

(b) Add a background timer started by `make_server`. Add this function above `make_server`:
```python
def _start_watcher_timer():
    def _loop():
        while True:
            time.sleep(WATCH_INTERVAL)
            try:
                with _obs_lock:
                    collector.tick(_obs_conn, RULES)
            except Exception:
                pass
    t = threading.Thread(target=_loop, daemon=True)
    t.start()
    return t
```
and call it inside `make_server` after `init_observability()`:
```python
def make_server(addr=("127.0.0.1", PORT)):
    init_observability()
    _start_watcher_timer()
    return ThreadingHTTPServer(addr, Handler)
```

- [ ] **Step 5: Run the integration test**

Run: `python -m pytest labwatch/tests/test_server_alerts.py -v`
Expected: PASS (1 passed).

- [ ] **Step 6: Run the full suite**

Run: `python -m pytest labwatch/tests/ -q`
Expected: all green.

- [ ] **Step 7: Commit**

```bash
git add labwatch/server.py labwatch/tests/test_server_alerts.py
git commit -m "feat(server): tick on ingest + background watcher timer + /api/alerts"
```

---

## Task 5: Deploy to M4 + live-verify a real alert

**Files:** Ops only (M4 deploy + verification).

> Runs against the live M4 via `ssh m4`/`scp` from the Surface PowerShell. The Surface reporter probes `ollama` (`:11434`), which is normally down — so a real `service-down:ollama` alert should appear once the Surface reporter posts.

- [ ] **Step 1: Sync the new/changed modules to M4**

Run (PowerShell):
```powershell
$f = "C:\telo\Efforts\Ongoing\NAUTILUS\labwatch"
scp "$f\watchers.py" "$f\watchers.json" "$f\store.py" "$f\collector.py" "$f\server.py" m4:/Users/sovrnnode03/nautilus/labwatch/
```
Expected: 5 files copied.

- [ ] **Step 2: Restart the collector**

Run (PowerShell):
```powershell
ssh m4 "sudo launchctl kickstart -k system/com.sovern.labwatch && sleep 3 && tail -5 ~/nautilus/run/labwatch.err.log; curl -s -o /dev/null -w 'health=%{http_code}\n' http://127.0.0.1:4002/health"
```
Expected: empty/clean err log, `health=200`.

- [ ] **Step 3: Push an M4 self-report so a tick runs**

Run (PowerShell):
```powershell
ssh m4 "cd ~/nautilus/labwatch && /opt/homebrew/bin/python3.12 -c \"import reporter; print('posted=', reporter.run_once('m4','http://127.0.0.1:4002/ingest', reporter.DEFAULT_SERVICES['m4']))\""
```
Expected: `posted= True`.

- [ ] **Step 4: Push a Surface report (ollama down) and check the alert**

Run (PowerShell):
```powershell
cd "C:\telo\Efforts\Ongoing\NAUTILUS\labwatch"
python -c "import tunnel, reporter; tunnel.ensure(4002,'m4',4002); print('posted=', reporter.run_once('surface','http://127.0.0.1:4002/ingest', reporter.DEFAULT_SERVICES['surface']))"
ssh m4 "curl -s http://127.0.0.1:4002/api/alerts" | python -c "import sys,json; d=json.load(sys.stdin); print('max_severity=', d['max_severity']); print('alert_ids=', [a['id'] for a in d['alerts']])"
```
Expected: `service-down:ollama` present in `alert_ids` (unless ollama happens to be running), `max_severity=critical`.

- [ ] **Step 5: Verify resolution lingers then clears (optional sanity)**

If `ollama` is actually running on Surface, instead verify the plumbing by confirming `/api/alerts` returns valid JSON with `max_severity` and an `alerts` list. The lifecycle itself is covered by Task 2 unit tests.

- [ ] **Step 6: Note for the tray**

No code change needed: the running tray (Phase 1b) polls `/api/state`, will redden on the `critical` service-down, and toast `surface: service-down:ollama`. Confirm visually if the tray is up.

---

## Phase 2a self-review checklist (run before handoff)

- [ ] Full suite green: `python -m pytest labwatch/tests/ -q`
- [ ] gitleaks clean: `gitleaks detect --no-banner --log-opts="main..HEAD"`
- [ ] No `eval`/`exec` anywhere in `watchers.py`
- [ ] `/api/alerts` returns `{alerts, max_severity}`; `/api/state.alerts` non-empty when a rule fires
- [ ] Existing `test_assemble_state_shape` still passes (empty DB → no alerts)
- [ ] Live: a real `service-down` alert appears on M4 and the tray reflects it

---

## Notes for Phase 2b (Telegram escape — next plan)

- Add `notify.py` (stdlib `urllib` POST to `https://api.telegram.org/bot<token>/sendMessage`); token + chat id from a gitignored `~/.config/nautilus/secrets/telegram.env` (unified key store).
- Wire into `collector.tick`: on a NEW firing alert whose `channels` include `telegram` and `severity == "critical"`, send; on resolve, send a clear. Add cooldown/debounce here (where rate-limiting matters) — keyed by `(id, host)`.
- Draft to reconcile: `docs/superpowers/drafts/phase2-watchers-gemini.md` (lifecycle ideas; ignore its eval engine).
```
