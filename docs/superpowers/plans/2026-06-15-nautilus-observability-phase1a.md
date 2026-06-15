# NAUTILUS Observability — Phase 1a Implementation Plan (Surface Reporter)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Surface laptop report its own state to the M4 collector — Windows host metrics plus a live port of the agent-wallet signals — so the dashboard's wallets panel is fixed correctly (sourced from `hosts.surface.payload.domain.wallets`) and the fleet view gains a second host.

**Architecture:** Reuse the merged Phase 0 reporter scaffold. Add `domain_surface()` (a Python port of `collect-wallets.ps1`), refactor `run_once` to dispatch the domain by host, add an SSH tunnel helper so the remote Surface reporter can POST to M4's localhost-only `/ingest` (Surface:4002 → M4:127.0.0.1:4002), and extend `nautilus-keys` with `export-host`/`import-host` so the shared `surface` HMAC key exists on both boxes. The collector and dashboard are unchanged except the dashboard re-sources wallets.

**Tech Stack:** Python 3.13 (stdlib `http.client`, `socket`, `subprocess`, `glob`, `re`), `psutil`. Tests: `pytest`. SSH (OpenSSH client, `m4` host alias already configured). No new dependencies.

**Spec:** `docs/superpowers/specs/2026-06-14-nautilus-observability-design.md` (§7 Phase 1, §5 key management)
**Builds on:** Phase 0 (merged to `main`, commit `a52c7c6`) — flat modules `labwatch/{keys,keys_cli,schema,store,collector,reporter,server}.py`.

---

## Scope

This plan is **Phase 1a only**: the Surface reporter + the infrastructure it needs (tunnel helper, key distribution, dashboard wallets fix, Surface deploy). **Phase 1b** (the pystray tray app that manages a persistent tunnel + indicator + toasts) is deferred to its own plan and will reuse `tunnel.py` from this phase.

**Wallet semantics (important — the machine draft got this wrong):** "wallets" are **agent-CLI usage signals**, NOT crypto balances. They mirror `labwatch/collect-wallets.ps1`: Codex token totals from session logs, Gemini-CLI turn counts, Antigravity brain-dir counts, Claude unknown. Phase 1a ports that collection logic to Python so the Surface reporter generates the signals live.

## File structure (Phase 1a)

| File | Change | Responsibility |
|------|--------|----------------|
| `labwatch/reporter.py` | Modify | Add `domain_surface()` + wallet helpers; refactor `run_once` domain dispatch; add `surface` to `DEFAULT_SERVICES`; wire optional tunnel-ensure into `main()`. |
| `labwatch/tunnel.py` | Create | SSH local-forward lifecycle: `build_ssh_cmd`, `is_up`, `ensure`, `stop`. Shared with Phase 1b tray. |
| `labwatch/keys_cli.py` | Modify | Add `export-host` / `import-host` subcommands for secure key distribution. |
| `labwatch/static/index.html` | Modify | Re-source the wallets panel from `s.hosts.surface.payload.domain.wallets`. |
| `labwatch/run/run-reporter-surface.ps1` | Create | Windows launcher: sets env (host=surface, ingest, tunnel) and runs the reporter loop. |
| `labwatch/tests/test_domain_surface.py` | Create | Wallet-collection unit tests (tmp fixtures). |
| `labwatch/tests/test_tunnel.py` | Create | `build_ssh_cmd` + `is_up` tests. |
| `labwatch/tests/test_reporter.py` | Modify | Update `test_run_once` for the new dispatch; add a surface dispatch test. |
| `labwatch/tests/test_keys_cli.py` | Modify | Add export/import round-trip test. |

**Invariant preserved:** the Surface reporter signs with canonical bytes `json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")` — identical to the collector (already in `sign_envelope`). The Surface reporter does NOT import `server`/`schema`/`store` (those stay M4-side); it needs only `keys`, `reporter`, `tunnel`, and `psutil`.

---

## Task 1: Surface wallet domain (port of collect-wallets.ps1)

**Files:**
- Modify: `labwatch/reporter.py`
- Test: `labwatch/tests/test_domain_surface.py`

- [ ] **Step 1: Write the failing test**

Create `labwatch/tests/test_domain_surface.py`:
```python
import os
from datetime import datetime

import reporter


def _write(path, content=""):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def test_codex_tokens_sums_last_token_count_per_file(tmp_path):
    today = datetime.now().date()
    d = os.path.join(str(tmp_path), ".codex", "sessions",
                     f"{today.year}", f"{today.month:02d}", f"{today.day:02d}")
    _write(os.path.join(d, "rollout-1.jsonl"),
           '{"type":"x"}\n'
           '{"type":"token_count","total_tokens":100}\n'
           '{"type":"token_count","total_tokens":250}\n')
    # only the LAST token_count line counts (cumulative), → 250
    assert reporter._codex_tokens(str(tmp_path), today) == 250


def test_codex_tokens_missing_dir_returns_zero(tmp_path):
    assert reporter._codex_tokens(str(tmp_path), datetime.now().date()) == 0


def test_gemini_requests_counts_gemini_turns_today(tmp_path):
    today = datetime.now().date()
    f = os.path.join(str(tmp_path), ".gemini", "tmp", "proj", "chats", "session-1.jsonl")
    _write(f, '{"type":"gemini"}\n{"type":"user"}\n{"type":"gemini"}\n')
    assert reporter._gemini_requests(str(tmp_path), today) == 2


def test_agy_runs_counts_today_brain_dirs(tmp_path):
    today = datetime.now().date()
    base = os.path.join(str(tmp_path), ".gemini", "antigravity-cli", "brain")
    os.makedirs(os.path.join(base, "run1"))
    os.makedirs(os.path.join(base, "run2"))
    assert reporter._agy_runs(str(tmp_path), today) == 2


def test_domain_surface_shape(tmp_path):
    d = reporter.domain_surface(home=str(tmp_path), today=datetime.now().date())
    assert "wallets" in d
    w = d["wallets"]
    assert "as_of" in w
    assert set(w["agents"]) == {"codex", "gemini-cli", "antigravity", "claude"}
    assert w["agents"]["antigravity"]["budget"] == 20
    assert w["agents"]["claude"]["used_today"] is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest labwatch/tests/test_domain_surface.py -v`
Expected: FAIL (`AttributeError: module 'reporter' has no attribute '_codex_tokens'`).

- [ ] **Step 3: Write minimal implementation**

In `labwatch/reporter.py`, add `import glob` and `import re` to the imports at the top (next to `import json`, `import os`). Then add this section after the `domain_m4()` function:
```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest labwatch/tests/test_domain_surface.py -v`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
git add labwatch/reporter.py labwatch/tests/test_domain_surface.py
git commit -m "feat(reporter): domain_surface — Python port of collect-wallets.ps1 (agent usage signals)"
```

---

## Task 2: run_once domain dispatch + surface services

**Files:**
- Modify: `labwatch/reporter.py`
- Test: `labwatch/tests/test_reporter.py`

- [ ] **Step 1: Update the existing run_once test + add a surface test**

In `labwatch/tests/test_reporter.py`, the existing `test_run_once_posts_and_returns_bool` must isolate the new domain dispatch (run_once now calls `domain_m4()` for host m4). REPLACE that test with the version below and APPEND the surface test:
```python
def test_run_once_posts_and_returns_bool(monkeypatch):
    captured = {}
    monkeypatch.setattr(reporter, "domain_m4", lambda: None)
    monkeypatch.setattr(reporter, "build_payload", lambda cfg, domain=None: {"services": [], "host_metrics": {"cpu_pct": 1.0}})
    monkeypatch.setattr(reporter, "load_master", lambda host, keyring_path=None: b"\x44" * 32)

    def fake_post(url, host, master, body, spool_path=None):
        captured["host"] = host
        captured["url"] = url
        return True

    monkeypatch.setattr(reporter, "post_snapshot", fake_post)
    ok = reporter.run_once(host="m4", ingest_url="http://127.0.0.1:4002/ingest",
                           services_cfg=[], keyring_path="x")
    assert ok is True
    assert captured["host"] == "m4"


def test_run_once_surface_uses_domain_surface(monkeypatch):
    seen = {}
    monkeypatch.setattr(reporter, "load_master", lambda host, keyring_path=None: b"\x44" * 32)
    monkeypatch.setattr(reporter, "domain_surface", lambda: {"wallets": {"agents": {}}})

    def fake_build(cfg, domain=None):
        seen["domain"] = domain
        return {"services": [], "host_metrics": {"cpu_pct": 1.0}}

    monkeypatch.setattr(reporter, "build_payload", fake_build)
    monkeypatch.setattr(reporter, "post_snapshot", lambda *a, **k: True)
    ok = reporter.run_once(host="surface", ingest_url="http://127.0.0.1:4002/ingest",
                           services_cfg=[], keyring_path="x")
    assert ok is True
    assert seen["domain"] == {"wallets": {"agents": {}}}   # surface domain wired
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest labwatch/tests/test_reporter.py -k run_once -v`
Expected: FAIL (`test_run_once_surface_uses_domain_surface` fails — run_once passes `domain=None` for surface today).

- [ ] **Step 3: Refactor run_once + add surface services**

In `labwatch/reporter.py`, replace the `run_once` body and add `surface` to `DEFAULT_SERVICES`:
```python
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
```
and
```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest labwatch/tests/test_reporter.py -v`
Expected: PASS (all reporter tests, including both run_once tests).

- [ ] **Step 5: Commit**

```bash
git add labwatch/reporter.py labwatch/tests/test_reporter.py
git commit -m "feat(reporter): dispatch domain by host (m4/surface) + surface default services"
```

---

## Task 3: SSH tunnel helper + main() wiring

**Files:**
- Create: `labwatch/tunnel.py`
- Modify: `labwatch/reporter.py` (main loop)
- Test: `labwatch/tests/test_tunnel.py`

- [ ] **Step 1: Write the failing test**

Create `labwatch/tests/test_tunnel.py`:
```python
import socket

import tunnel


def test_build_ssh_cmd_default_remote_port():
    cmd = tunnel.build_ssh_cmd(4002, "m4")
    assert cmd[0] == "ssh"
    assert "-N" in cmd
    assert "-L" in cmd
    # local:remote_host:remote_port — default remote_port == local_port
    assert "4002:localhost:4002" in cmd
    assert cmd[-1] == "m4"


def test_build_ssh_cmd_custom_ports():
    cmd = tunnel.build_ssh_cmd(5002, "m4", remote_host="127.0.0.1", remote_port=4002)
    assert "5002:127.0.0.1:4002" in cmd


def test_is_up_true_when_socket_listening():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    port = srv.getsockname()[1]
    try:
        assert tunnel.is_up(port) is True
    finally:
        srv.close()


def test_is_up_false_on_closed_port():
    # bind+close to get a port nothing listens on
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))
    port = srv.getsockname()[1]
    srv.close()
    assert tunnel.is_up(port, timeout=0.3) is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest labwatch/tests/test_tunnel.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'tunnel'`).

- [ ] **Step 3: Write minimal implementation**

Create `labwatch/tunnel.py`:
```python
"""SSH local-forward tunnel helper.

The M4 collector binds 127.0.0.1 only, so a remote reporter (Surface) reaches
its /ingest through an SSH local forward: Surface:LOCAL -> M4:127.0.0.1:REMOTE.
Shared by the Surface reporter (Phase 1a) and the tray app (Phase 1b).
"""

import socket
import subprocess
import time

_proc = None


def build_ssh_cmd(local_port: int, remote: str, remote_host: str = "localhost",
                  remote_port: int = None) -> list:
    remote_port = remote_port or local_port
    return ["ssh", "-N", "-o", "ExitOnForwardFailure=yes",
            "-L", f"{local_port}:{remote_host}:{remote_port}", remote]


def is_up(local_port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", local_port), timeout=timeout):
            return True
    except OSError:
        return False


def ensure(local_port: int = 4002, remote: str = "m4", remote_port: int = 4002,
           wait_s: float = 8.0) -> bool:
    """Ensure a forward on local_port is live. No-op if something already serves
    it (e.g. the tray's persistent tunnel). Returns True if up within wait_s."""
    global _proc
    if is_up(local_port):
        return True
    _proc = subprocess.Popen(build_ssh_cmd(local_port, remote, remote_port=remote_port))
    t0 = time.time()
    while time.time() - t0 < wait_s:
        if is_up(local_port):
            return True
        time.sleep(0.4)
    return is_up(local_port)


def stop():
    global _proc
    if _proc is not None:
        _proc.terminate()
        _proc = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest labwatch/tests/test_tunnel.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Wire optional tunnel-ensure into reporter main()**

In `labwatch/reporter.py`, replace the `main()` function with:
```python
def main():
    host = os.environ.get("REPORTER_HOST", "m4")
    ingest = os.environ.get("INGEST_URL", "http://127.0.0.1:4002/ingest")
    interval = int(os.environ.get("REPORTER_INTERVAL", "30"))
    spool = os.environ.get("REPORTER_SPOOL", os.path.join(os.path.dirname(__file__), "spool.jsonl"))
    tunnel_remote = os.environ.get("REPORTER_TUNNEL")  # e.g. "m4" → ensure :4002 forward
    services = DEFAULT_SERVICES.get(host, [])
    while True:
        try:
            if tunnel_remote:
                import tunnel
                tunnel.ensure(local_port=4002, remote=tunnel_remote, remote_port=4002)
            run_once(host, ingest, services, spool_path=spool)
        except Exception as e:  # never let the loop die
            print(f"[reporter] cycle error: {type(e).__name__}", flush=True)
        time.sleep(interval)
```

- [ ] **Step 6: Run the full suite (no regressions)**

Run: `python -m pytest labwatch/tests/ -q`
Expected: all green.

- [ ] **Step 7: Commit**

```bash
git add labwatch/tunnel.py labwatch/reporter.py labwatch/tests/test_tunnel.py
git commit -m "feat(tunnel): SSH local-forward helper + reporter main() ensures tunnel for remote hosts"
```

---

## Task 4: nautilus-keys export-host / import-host (key distribution)

**Files:**
- Modify: `labwatch/keys_cli.py`
- Test: `labwatch/tests/test_keys_cli.py`

- [ ] **Step 1: Write the failing test (append)**

Append to `labwatch/tests/test_keys_cli.py`:
```python
def test_export_then_import_roundtrip(tmp_path):
    src = tmp_path / "m4_keyring.json"
    keys_cli.main(["gen", "--host", "surface", "--keyring", str(src)])
    transfer = tmp_path / "surface_key.json"
    rc = keys_cli.main(["export-host", "--host", "surface",
                        "--out", str(transfer), "--keyring", str(src)])
    assert rc == 0
    assert transfer.exists()

    dst = tmp_path / "surface_keyring.json"
    rc = keys_cli.main(["import-host", "--in", str(transfer), "--keyring", str(dst)])
    assert rc == 0

    src_kr = _read(src)
    dst_kr = _read(dst)
    # the surface host's acceptable keys must match across both keyrings
    assert dict(keys.acceptable(src_kr, "surface")) == dict(keys.acceptable(dst_kr, "surface"))


def test_export_unknown_host_returns_1(tmp_path):
    src = tmp_path / "kr.json"
    keys_cli.main(["gen", "--host", "m4", "--keyring", str(src)])
    rc = keys_cli.main(["export-host", "--host", "surface",
                        "--out", str(tmp_path / "x.json"), "--keyring", str(src)])
    assert rc == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest labwatch/tests/test_keys_cli.py -k "export or import" -v`
Expected: FAIL (argparse error / unknown subcommand `export-host`).

- [ ] **Step 3: Implement the subcommands**

In `labwatch/keys_cli.py`, add these two command functions (after `cmd_list`):
```python
def cmd_export_host(args):
    kr = _load(args.keyring)
    h = (kr.get("hosts") or {}).get(args.host)
    if not h:
        print(f"unknown host: {args.host}")
        return 1
    _save(args.out, {"hosts": {args.host: h}})
    for kid in (h.get("keys") or {}):
        print(f"exported {args.host} {kid} -> {args.out} (transfer securely, then delete)")
    return 0


def cmd_import_host(args):
    incoming = _load(args.infile)
    hosts = incoming.get("hosts") or {}
    if not hosts:
        print("no hosts in import file")
        return 1
    kr = _load(args.keyring)
    kr.setdefault("hosts", {})
    for host, h in hosts.items():
        kr["hosts"][host] = h
    _save(args.keyring, kr)
    print(f"imported hosts: {list(hosts)}")
    return 0
```
Then register them in `build_parser()` (add after the `revoke` parser, before `list`):
```python
    e = sub.add_parser("export-host"); e.add_argument("--host", required=True); e.add_argument("--out", required=True); e.set_defaults(fn=cmd_export_host)
    i = sub.add_parser("import-host"); i.add_argument("--in", dest="infile", required=True); i.set_defaults(fn=cmd_import_host)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest labwatch/tests/test_keys_cli.py -v`
Expected: PASS (all keys_cli tests).

- [ ] **Step 5: Commit**

```bash
git add labwatch/keys_cli.py labwatch/tests/test_keys_cli.py
git commit -m "feat(keys): export-host/import-host for cross-host key distribution"
```

---

## Task 5: Dashboard — re-source wallets from the surface host

**Files:**
- Modify: `labwatch/static/index.html`
- Test: manual (browser). Covered functionally by the live verify in Task 6.

- [ ] **Step 1: Re-source the wallets variable**

In `labwatch/static/index.html`, find the wallets block (around line 189-191) that starts:
```javascript
  // wallets
  const w = s.wallets || {};
```
Replace those two lines with:
```javascript
  // wallets (sourced from the surface host's reported domain, push-model)
  const surfaceDomain = ((((s.hosts || {}).surface || {}).payload || {}).domain) || {};
  const w = surfaceDomain.wallets || {};
```
Leave the rest of the wallets rendering (the `wAsOf` / `isOld` / `#wallets-hint` / `#wallets` map) unchanged — it already reads `w.as_of` and `w.agents`.

- [ ] **Step 2: Static sanity check**

Run: `grep -n "s.wallets" labwatch/static/index.html`
Expected: no matches (the only reference is now `surfaceDomain.wallets`).
Run: `grep -n "surfaceDomain" labwatch/static/index.html`
Expected: 2 matches (definition + use).

- [ ] **Step 3: Commit**

```bash
git add labwatch/static/index.html
git commit -m "feat(web): source wallets panel from hosts.surface.payload.domain.wallets"
```

---

## Task 6: Deploy the Surface reporter + live verify

**Files:**
- Create: `labwatch/run/run-reporter-surface.ps1`
- Ops: surface key gen on M4 → distribute to Surface; Windows Scheduled Task; live verify.

> These steps run on the Surface laptop (this machine) via the PowerShell tool, plus `ssh m4` for the M4-side key gen. No sudo needed. Paths use the Surface home `C:\Users\sasha`.

- [ ] **Step 1: Write the Surface launcher**

Create `labwatch/run/run-reporter-surface.ps1`:
```powershell
# Surface observability reporter launcher.
# Reports host=surface to the M4 collector through an SSH tunnel (Surface:4002 -> M4:4002).
$env:REPORTER_HOST = "surface"
$env:INGEST_URL = "http://127.0.0.1:4002/ingest"
$env:REPORTER_TUNNEL = "m4"
$env:REPORTER_INTERVAL = "30"
Set-Location "$PSScriptRoot\..\"
python "labwatch\reporter.py"
```

- [ ] **Step 2: Generate the surface key on M4 and distribute it**

The shared `surface` HMAC key must exist in BOTH the M4 collector keyring and the Surface local keyring. Run (PowerShell):
```powershell
# 1. gen on the M4 collector keyring
ssh m4 "/opt/homebrew/bin/python3.12 ~/nautilus/labwatch/keys_cli.py gen --host surface"
# 2. export just the surface entry to a transfer file on M4
ssh m4 "/opt/homebrew/bin/python3.12 ~/nautilus/labwatch/keys_cli.py export-host --host surface --out ~/surface_key.json"
# 3. copy the transfer file to Surface
scp m4:~/surface_key.json "$env:TEMP\surface_key.json"
# 4. import into the Surface local keyring
python "C:\telo\Efforts\Ongoing\NAUTILUS\labwatch\keys_cli.py" import-host --in "$env:TEMP\surface_key.json"
# 5. delete the transfer files (secret material)
Remove-Item "$env:TEMP\surface_key.json"
ssh m4 "rm -f ~/surface_key.json"
```
Expected: import prints `imported hosts: ['surface']`. Verify the Surface keyring exists:
```powershell
Test-Path "$env:USERPROFILE\.config\nautilus\secrets\observability.keyring.json"
```
Expected: `True`.

- [ ] **Step 3: One-shot manual verify (tunnel + ingest + wallets)**

Run (PowerShell) — runs a single reporter cycle for surface (the loop's body), proving tunnel+sign+ingest end-to-end:
```powershell
cd "C:\telo\Efforts\Ongoing\NAUTILUS\labwatch"
$env:REPORTER_TUNNEL="m4"
python -c "import tunnel, reporter; tunnel.ensure(4002,'m4',4002); print('posted=', reporter.run_once('surface','http://127.0.0.1:4002/ingest', reporter.DEFAULT_SERVICES['surface']))"
```
Expected: `posted= True`.

Then confirm the M4 collector stored the surface snapshot WITH wallets:
```powershell
ssh m4 "curl -s http://127.0.0.1:4002/api/state" | python -c "import sys,json; d=json.load(sys.stdin); s=d['hosts'].get('surface',{}); print('surface_freshness=', s.get('freshness')); w=((s.get('payload',{}).get('domain',{})).get('wallets',{})); print('wallet_agents=', list((w.get('agents') or {})))"
```
Expected: `surface_freshness= live` and `wallet_agents= ['codex', 'gemini-cli', 'antigravity', 'claude']`.

- [ ] **Step 4: Install the Windows Scheduled Task (runs at logon)**

Run (PowerShell):
```powershell
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -WindowStyle Hidden -File `"C:\telo\Efforts\Ongoing\NAUTILUS\labwatch\run\run-reporter-surface.ps1`""
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "NAUTILUS-Surface-Reporter" -Action $action -Trigger $trigger -Settings $settings -Description "Surface observability reporter -> M4 collector"
Start-ScheduledTask -TaskName "NAUTILUS-Surface-Reporter"
```
Expected: task registered and started.

- [ ] **Step 5: Verify the dashboard wallets panel is alive**

With the dashboard tunnel up (or the reporter's tunnel), open `http://localhost:4002` and confirm the "Delegate Wallets" panel shows agent rows with an `as_of` timestamp and the "data stale" hint is GONE. (The panel now reads `hosts.surface.payload.domain.wallets`.)

- [ ] **Step 6: Commit the launcher**

```bash
git add labwatch/run/run-reporter-surface.ps1
git commit -m "ops(reporter): Surface launcher + Scheduled Task (host=surface via SSH tunnel)"
```

---

## Phase 1a self-review checklist (run before handoff)

- [ ] Full suite green: `python -m pytest labwatch/tests/ -q`
- [ ] gitleaks clean on the branch: `gitleaks detect --no-banner --log-opts="main..HEAD"`
- [ ] `/api/state` shows BOTH `m4` and `surface` hosts live
- [ ] Surface snapshot carries `domain.wallets.agents` (codex/gemini-cli/antigravity/claude)
- [ ] Dashboard wallets panel populated; stale hint gone
- [ ] No secret key material committed; transfer files deleted after import

---

## Notes for Phase 1b (tray — next plan)

- `tunnel.py` is reused: the tray keeps a persistent `tunnel.ensure(4002, "m4")`; the reporter's per-cycle `ensure` then becomes a no-op.
- Tray = pystray + Pillow icon (green/amber/red from max alert severity / host freshness), left-click → open `http://localhost:4002`, native toast on new alert (lib choice per `docs/superpowers/drafts/research-gemini.md` — evaluate winsdk vs win10toast for 2026 maintenance).
- Alerts don't exist until Phase 2; until then the tray colors by host freshness (live=green, any stale=amber, any down=red).
