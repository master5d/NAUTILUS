# NAUTILUS Observability — Phase 2b Implementation Plan (Telegram Escape)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Critical alerts reach the user even when the laptop is off — by pushing them to the existing Telegram bot when a `critical` + `telegram`-channeled alert starts firing (and a clear when it resolves).

**Architecture:** A stdlib-only `notify.py` (urllib → Telegram Bot API; config from the unified secret store). The server runs `_tick_and_notify()`: it ticks the collector UNDER the sqlite lock, then notifies OUTSIDE the lock (never hold the DB lock during network I/O). Episode dedup via an in-memory `_tg_notified` set — one fire message per firing episode, one clear when it stops — mirroring the tray's toast diffing. Both the `/ingest` path and the background timer go through this helper.

**Tech Stack:** Python 3.13 stdlib (`urllib`, `json`, `os`). Tests: `pytest` (mock `urllib` — no real network). No third-party deps (no `requests`).

**Plan deps:** Builds on merged Phase 2a (`collector.tick` returns `(state, fired)`, `watchers.json` tags `channels:["tray","telegram"]` on critical rules, server `_obs_lock` + tick-on-ingest + background timer).

**Secret handling:** The bot token + chat id are USER-PROVIDED in `~/.config/nautilus/secrets/telegram.env` (unified key store). The implementation only reads the file; the value is never printed, committed, or echoed. Tests mock the sender.

---

## Scope

Phase 2b = the Telegram escape only. Tray toasts (Phase 1b) and `/api/alerts` (Phase 2a) already cover the on-laptop path; this adds the off-laptop path for `critical` severity. Cooldown is **episode-membership** (a continuously-firing alert is messaged once, re-messaged only after it resolves and re-fires) — no time-based cooldown needed.

## File structure (Phase 2b)

| File | Change | Responsibility |
|------|--------|----------------|
| `labwatch/notify.py` | Create | `load_config`, `send_message` (urllib→Bot API), `critical_telegram` filter, `format_fire`/`format_clear`. Pure + one network fn. |
| `labwatch/server.py` | Modify | Load telegram config at init; `_tg_notified` set; `_notify_telegram(fired)`; `_tick_and_notify()`; route `/ingest` + timer through it. |
| `labwatch/tests/test_notify.py` | Create | config parse, send (mocked urllib), filter, formatting. |
| `labwatch/tests/test_server_telegram.py` | Create | ingest critical → fire sent; clear on resolve (mocked sender). |

---

## Task 1: notify.py — Telegram sender + config + filter

**Files:**
- Create: `labwatch/notify.py`
- Test: `labwatch/tests/test_notify.py`

- [ ] **Step 1: Write the failing test**

Create `labwatch/tests/test_notify.py`:
```python
import json

import notify


def test_load_config_reads_token_and_chat(tmp_path):
    p = tmp_path / "telegram.env"
    p.write_text("# comment\nTELEGRAM_BOT_TOKEN=abc123\nTELEGRAM_CHAT_ID=42\n", encoding="utf-8")
    assert notify.load_config(str(p)) == ("abc123", "42")


def test_load_config_missing_file():
    assert notify.load_config("/no/such/telegram.env") == (None, None)


def test_load_config_incomplete_returns_none(tmp_path):
    p = tmp_path / "t.env"
    p.write_text("TELEGRAM_BOT_TOKEN=x\n", encoding="utf-8")
    assert notify.load_config(str(p)) == (None, None)


def test_critical_telegram_filters_severity_and_channel():
    fired = [
        {"id": "service-down:stt", "host": "m4", "severity": "critical", "channels": ["tray", "telegram"]},
        {"id": "disk-pressure", "host": "m4", "severity": "warning", "channels": ["tray"]},
        {"id": "x", "host": "m4", "severity": "critical", "channels": ["tray"]},  # no telegram
    ]
    assert set(notify.critical_telegram(fired)) == {("service-down:stt", "m4")}


def test_send_message_posts_to_bot_api(monkeypatch):
    captured = {}

    class FakeResp:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def fake_urlopen(req, timeout=5.0):
        captured["url"] = req.full_url
        captured["data"] = req.data
        return FakeResp()

    monkeypatch.setattr(notify.urllib.request, "urlopen", fake_urlopen)
    assert notify.send_message("TOK", "42", "hi") is True
    assert "botTOK/sendMessage" in captured["url"]
    assert json.loads(captured["data"])["chat_id"] == "42"
    assert json.loads(captured["data"])["text"] == "hi"


def test_send_message_no_token_is_false():
    assert notify.send_message(None, "42", "hi") is False


def test_format_fire_and_clear():
    assert notify.format_fire({"severity": "critical", "id": "a", "message": "stt down on m4"}).startswith("🚨")
    assert "stt down on m4" in notify.format_fire({"severity": "critical", "id": "a", "message": "stt down on m4"})
    assert notify.format_clear(("service-down:stt", "m4")).startswith("✅")
    assert "service-down:stt" in notify.format_clear(("service-down:stt", "m4"))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest labwatch/tests/test_notify.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'notify'`).

- [ ] **Step 3: Write minimal implementation**

Create `labwatch/notify.py`:
```python
"""Telegram escape for critical alerts — stdlib only (urllib), no requests.

Sends to the Telegram Bot API. Config (bot token, chat id) lives in the unified
secret store at ~/.config/nautilus/secrets/telegram.env and is user-provided;
this module only reads it and never logs the value.
"""

import json
import os
import urllib.request

DEFAULT_CONFIG = os.path.join(
    os.path.expanduser("~"), ".config", "nautilus", "secrets", "telegram.env"
)


def load_config(path: str = DEFAULT_CONFIG):
    """Return (token, chat_id), or (None, None) if absent/incomplete."""
    token = chat = None
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip().strip('"').strip("'")
                if k == "TELEGRAM_BOT_TOKEN":
                    token = v
                elif k == "TELEGRAM_CHAT_ID":
                    chat = v
    except OSError:
        return None, None
    return (token, chat) if (token and chat) else (None, None)


def send_message(token: str, chat_id: str, text: str, timeout: float = 5.0) -> bool:
    if not token or not chat_id:
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return 200 <= r.status < 300
    except Exception:
        return False


def critical_telegram(fired: list) -> dict:
    """{(id, host): alert} for fired alerts that are critical AND telegram-channeled."""
    out = {}
    for a in fired:
        if a.get("severity") == "critical" and "telegram" in (a.get("channels") or []):
            out[(a["id"], a["host"])] = a
    return out


def format_fire(alert: dict) -> str:
    return f"🚨 {alert.get('severity', '').upper()}: {alert.get('message') or alert.get('id')}"


def format_clear(key) -> str:
    aid, host = key
    return f"✅ RESOLVED: {aid} on {host}"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest labwatch/tests/test_notify.py -v`
Expected: PASS (7 passed).

- [ ] **Step 5: Commit**

```bash
git add labwatch/notify.py labwatch/tests/test_notify.py
git commit -m "feat(notify): stdlib Telegram sender + config loader + critical filter"
```

---

## Task 2: Server wiring — tick-and-notify

**Files:**
- Modify: `labwatch/server.py`
- Test: `labwatch/tests/test_server_telegram.py`

- [ ] **Step 1: Write the failing integration test**

Create `labwatch/tests/test_server_telegram.py`:
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
    master = b"\x77" * 32
    krp = tmp_path / "kr.json"
    krp.write_text(json.dumps({"hosts": {"surface": {"active": "s-1",
        "keys": {"s-1": {"material": _b64(master), "created": "t", "revoked": False}}}}}),
        encoding="utf-8")
    monkeypatch.setattr(server, "KEYRING_PATH", str(krp))
    monkeypatch.setattr(server, "DB_PATH_OBS", str(tmp_path / "labwatch.db"))
    httpd = server.make_server(("127.0.0.1", 0))
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return server, httpd, port, master


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


def test_critical_fires_and_clears_telegram(tmp_path, monkeypatch):
    server, httpd, port, master = _start(tmp_path, monkeypatch)
    import notify
    sent = []
    monkeypatch.setattr(server, "_tg_token", "TOK")
    monkeypatch.setattr(server, "_tg_chat", "42")
    monkeypatch.setattr(server, "_tg_notified", set())
    monkeypatch.setattr(notify, "send_message",
                        lambda token, chat, text, timeout=5.0: sent.append(text) or True)
    try:
        # ollama down -> critical service-down -> fire telegram
        assert _ingest(port, master,
                       {"services": [{"name": "ollama", "port": 11434, "up": False}],
                        "host_metrics": {"cpu_pct": 1.0}}) == 200
        assert any("ollama" in s and s.startswith("🚨") for s in sent)

        # ollama up -> resolves -> clear telegram
        assert _ingest(port, master,
                       {"services": [{"name": "ollama", "port": 11434, "up": True}],
                        "host_metrics": {"cpu_pct": 1.0}}) == 200
        assert any(s.startswith("✅") for s in sent)
    finally:
        httpd.shutdown()


def test_no_telegram_when_unconfigured(tmp_path, monkeypatch):
    server, httpd, port, master = _start(tmp_path, monkeypatch)
    import notify
    sent = []
    monkeypatch.setattr(server, "_tg_token", None)   # not configured
    monkeypatch.setattr(server, "_tg_notified", set())
    monkeypatch.setattr(notify, "send_message",
                        lambda *a, **k: sent.append(1) or True)
    try:
        _ingest(port, master, {"services": [{"name": "ollama", "port": 11434, "up": False}],
                               "host_metrics": {"cpu_pct": 1.0}})
        assert sent == []   # no token → no send
    finally:
        httpd.shutdown()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest labwatch/tests/test_server_telegram.py -v`
Expected: FAIL (`AttributeError: module 'server' has no attribute '_tg_token'`).

- [ ] **Step 3: Modify `labwatch/server.py` — imports + globals + config load**

(a) Add `import notify` to the imports (next to `import collector`).

(b) Add globals after the `RULES = {}` line:
```python
_tg_token = None
_tg_chat = None
_tg_notified = set()   # {(id, host)} critical alerts already messaged this episode
```

(c) In `init_observability()`, after `RULES = _read_json(WATCHERS_PATH)`, add:
```python
    global _tg_token, _tg_chat
    _tg_token, _tg_chat = notify.load_config()
```

- [ ] **Step 4: Modify `labwatch/server.py` — notify + tick-and-notify helpers**

Add these two functions just above `_start_watcher_timer`:
```python
def _notify_telegram(fired):
    """Send a fire message for each newly-firing critical/telegram alert and a
    clear when one stops firing. Episode dedup via _tg_notified. Best-effort —
    runs OUTSIDE the DB lock so network never blocks ingest."""
    if not _tg_token:
        return
    current = notify.critical_telegram(fired)   # {(id,host): alert}
    for key in set(current) - _tg_notified:
        if notify.send_message(_tg_token, _tg_chat, notify.format_fire(current[key])):
            _tg_notified.add(key)
    for key in list(_tg_notified - set(current)):
        notify.send_message(_tg_token, _tg_chat, notify.format_clear(key))
        _tg_notified.discard(key)


def _tick_and_notify():
    """Run one collector tick under the DB lock, then notify outside the lock."""
    with _obs_lock:
        _state, fired = collector.tick(_obs_conn, RULES)
    _notify_telegram(fired)
```

- [ ] **Step 5: Modify `labwatch/server.py` — route /ingest + timer through it**

(a) In `Handler.do_POST` `/ingest` success branch, the Phase 2a code does the upsert and tick together under one lock:
```python
                with _obs_lock:
                    storemod.upsert_snapshot(_obs_conn, host, ts, payload)
                    collector.tick(_obs_conn, RULES)
```
Replace that with an upsert under the lock followed by the notify-aware tick:
```python
                with _obs_lock:
                    storemod.upsert_snapshot(_obs_conn, host, ts, payload)
                _tick_and_notify()
```

(b) In `_start_watcher_timer`, replace the in-loop `with _obs_lock: collector.tick(...)` body with a call to the helper:
```python
def _start_watcher_timer():
    def _loop():
        while True:
            time.sleep(WATCH_INTERVAL)
            try:
                _tick_and_notify()
            except Exception:
                pass
    t = threading.Thread(target=_loop, daemon=True)
    t.start()
    return t
```

- [ ] **Step 6: Run the integration test**

Run: `python -m pytest labwatch/tests/test_server_telegram.py -v`
Expected: PASS (2 passed).

- [ ] **Step 7: Run the full suite**

Run: `python -m pytest labwatch/tests/ -q`
Expected: all green.

- [ ] **Step 8: Commit**

```bash
git add labwatch/server.py labwatch/tests/test_server_telegram.py
git commit -m "feat(server): _tick_and_notify — Telegram escape for critical alerts (network outside DB lock)"
```

---

## Task 3: Deploy to M4 + configure + live test

**Files:** Ops only.

> The bot token + chat id are secret and USER-PROVIDED. The agent never reads, prints, or commits them. `notify.py` reads `~/.config/nautilus/secrets/telegram.env` on the M4 (where the collector runs).

- [ ] **Step 1: Sync modules to M4**

Run (PowerShell):
```powershell
$f = "C:\telo\Efforts\Ongoing\NAUTILUS\labwatch"
scp "$f\notify.py" "$f\server.py" m4:/Users/sovrnnode03/nautilus/labwatch/
```
Expected: 2 files copied.

- [ ] **Step 2: (User) create the secret config on M4**

The user runs this on the M4 (replace the two values; the agent must NOT type the real token). The here-doc keeps the token off the command line history:
```bash
mkdir -p ~/.config/nautilus/secrets && chmod 700 ~/.config/nautilus/secrets
cat > ~/.config/nautilus/secrets/telegram.env <<'EOF'
TELEGRAM_BOT_TOKEN=<paste bot token>
TELEGRAM_CHAT_ID=<paste your chat id>
EOF
chmod 600 ~/.config/nautilus/secrets/telegram.env
```
(The bot token can be the existing CC-channel bot's token, from `~/.claude/channels/telegram/.env`. Chat id = the user's own Telegram chat with the bot — obtainable from `https://api.telegram.org/bot<token>/getUpdates` after messaging the bot once.)

- [ ] **Step 3: Restart the collector (loads telegram config)**

Run (PowerShell):
```powershell
ssh m4 "sudo launchctl kickstart -k system/com.sovern.labwatch && sleep 3 && curl -s -o /dev/null -w 'health=%{http_code}\n' http://127.0.0.1:4002/health"
```
Expected: `health=200`.

- [ ] **Step 4: Live test — induce a critical alert**

The cleanest induced critical is `host-silent`: stop reporting for a host and let the timer tick fire it. Simplest: confirm config loaded and a fire path works by checking the M4 log after a forced down-service report. Run (PowerShell):
```powershell
ssh m4 "grep -c TELEGRAM ~/.config/nautilus/secrets/telegram.env"   # expect 2 (config present); value never printed
```
Then ask the user to confirm a Telegram message arrives when a real critical alert fires (e.g. stop the litellm daemon briefly: `ssh m4 'sudo launchctl kill TERM system/com.sovern.litellm'` → next M4 self-report's tick fires `service-down:litellm` → Telegram; then it auto-restarts via KeepAlive and a clear is sent). Only the user can confirm receipt on their phone.

- [ ] **Step 5: Note**

No code is committed in this task (ops only). `telegram.env` is gitignored by living under `~/.config` (outside the repo) — never in the repo tree.

---

## Phase 2b self-review checklist (run before handoff)

- [ ] Full suite green: `python -m pytest labwatch/tests/ -q`
- [ ] gitleaks clean: `gitleaks detect --no-banner --log-opts="main..HEAD"`
- [ ] No token/chat value anywhere in the repo or any commit
- [ ] `send_message` posts via stdlib urllib (no `requests` import)
- [ ] Notify runs OUTSIDE `_obs_lock` (network never holds the DB lock)
- [ ] Episode dedup: one fire per firing episode, one clear on resolve
- [ ] Unconfigured (no token) → zero sends, no errors

---

## Notes for Phase 3 (advisory tier — next plan)

- Adds the data sources for the deferred rules: `fallback-spike` (gateway fallback-rate in `domain_m4`), `deprecation-soon` (a deprecation calendar + key-age from the unified store), `backup-stale` (vault mirror mtime). The watchers engine already supports adding these as named evaluators.
- Hetzner reporter (behind CF tunnel, pinned-allowlist pull) + reachability matrix.
```
