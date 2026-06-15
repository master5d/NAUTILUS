# NAUTILUS Observability — Phase 1b Implementation Plan (Surface Tray)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A pystray system-tray app on the Surface laptop that keeps a persistent SSH tunnel to M4, shows a green/amber/red indicator driven by fleet state, opens the dashboard on double-left-click, and fires native Windows toasts on new alerts.

**Architecture:** A thin GUI shell (`tray.py`) over pure, unit-tested logic (`tray_logic.py`). A background thread ensures the shared `tunnel.py` is up, polls `http://127.0.0.1:4002/api/state` through it, maps the snapshot to a color, and diffs alerts to toast new ones. Until Phase 2 adds alerts, color is driven by host freshness (live=green, any stale=amber, any down=red). `tunnel.py` is hardened for Windows (no console popup, keepalive, tree-kill).

**Tech Stack:** Python 3.13, `pystray` + `Pillow` (tray icon), `windows-toasts` (winsdk-backed notifications — `win10toast` is broken on Win11), stdlib `urllib`/`threading`/`subprocess`. Tests: `pytest`.

**Plan deps:** Builds on merged Phase 1a (`tunnel.py`, reporter, collector). `Pillow` already installed; `pystray`/`windows-toasts` are Surface-only and go in a SEPARATE `requirements-tray.txt` (NOT the shared `requirements.txt`, which is also installed on the macOS M4 where `windows-toasts`/`winsdk` cannot install).

**Research:** `docs/superpowers/drafts/research-gemini.md` (pystray/tunnel/toast gotchas — validated).

---

## Scope

Phase 1b = the tray only. It consumes Phase 1a's `tunnel.py` and the collector's `/api/state`. It does not add server-side features. Alerts do not exist until Phase 2; the tray colors by host freshness now and the alert/toast code paths are wired so they light up automatically once Phase 2 emits alerts.

## File structure (Phase 1b)

| File | Change | Responsibility |
|------|--------|----------------|
| `labwatch/tray_logic.py` | Create | Pure functions: `status_color(state)`, `alert_keys(state)`, `new_alert_keys(prev, state)`. No GUI/IO. |
| `labwatch/tunnel.py` | Modify | Windows hardening: `ServerAliveInterval=30` in the cmd, `CREATE_NO_WINDOW` on spawn, `taskkill /F /T` tree-kill in `stop()`. |
| `labwatch/tray.py` | Create | pystray glue: icon, menu, background poll thread, toasts, persistent `tunnel.ensure`. pystray/windows-toasts imported lazily so module-level helpers stay testable. |
| `labwatch/requirements-tray.txt` | Create | `pystray`, `Pillow`, `windows-toasts` (Surface-only). |
| `labwatch/run/run-tray-surface.ps1` | Create | Launches `pythonw labwatch\tray.py` (no console window). |
| `labwatch/tests/test_tray_logic.py` | Create | Color + alert-diff unit tests. |
| `labwatch/tests/test_tunnel.py` | Modify | Add keepalive / popen-kwargs / stop-noop tests. |
| `labwatch/tests/test_tray.py` | Create | `make_image` + `fetch_state` (monkeypatched) — no pystray/display needed. |

---

## Task 1: tray_logic — pure indicator + alert-diff logic

**Files:**
- Create: `labwatch/tray_logic.py`
- Test: `labwatch/tests/test_tray_logic.py`

- [ ] **Step 1: Write the failing test**

Create `labwatch/tests/test_tray_logic.py`:
```python
import tray_logic


def _st(hosts=None, alerts=None):
    return {"hosts": hosts or {}, "alerts": alerts or []}


def test_color_green_when_all_live():
    state = _st({"m4": {"freshness": "live"}, "surface": {"freshness": "live"}})
    assert tray_logic.status_color(state) == "green"


def test_color_amber_when_any_stale():
    assert tray_logic.status_color(_st({"m4": {"freshness": "stale"}})) == "amber"


def test_color_red_when_any_down():
    assert tray_logic.status_color(_st({"m4": {"freshness": "down"}})) == "red"


def test_color_gray_when_no_hosts():
    assert tray_logic.status_color(_st()) == "gray"


def test_critical_alert_forces_red_even_if_live():
    state = _st({"m4": {"freshness": "live"}},
               [{"id": "x", "host": "m4", "severity": "critical"}])
    assert tray_logic.status_color(state) == "red"


def test_warning_alert_is_amber():
    state = _st({"m4": {"freshness": "live"}}, [{"severity": "warning"}])
    assert tray_logic.status_color(state) == "amber"


def test_alert_keys_and_new_alert_keys_diff():
    state = _st(alerts=[{"id": "a", "host": "m4"}, {"id": "b", "host": "m4"}])
    assert tray_logic.alert_keys(state) == {("a", "m4"), ("b", "m4")}
    assert tray_logic.new_alert_keys({("a", "m4")}, state) == {("b", "m4")}


def test_alert_keys_empty_state():
    assert tray_logic.alert_keys(_st()) == set()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest labwatch/tests/test_tray_logic.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'tray_logic'`).

- [ ] **Step 3: Write minimal implementation**

Create `labwatch/tray_logic.py`:
```python
"""Pure tray-state logic — no GUI, no I/O, fully unit-testable.

status_color maps an /api/state snapshot to an indicator color. Until Phase 2
adds alerts, color is driven by host freshness; the alert branches are already
wired so the same function works unchanged once alerts exist.
"""


def alert_keys(state) -> set:
    """Stable identity set for the current alerts: (id, host) pairs."""
    return {(a.get("id"), a.get("host")) for a in (state.get("alerts") or [])}


def new_alert_keys(prev: set, state) -> set:
    """Alerts present now that were not in prev (→ toast these)."""
    return alert_keys(state) - (prev or set())


def status_color(state) -> str:
    alerts = state.get("alerts") or []
    severities = {a.get("severity") for a in alerts}
    hosts = state.get("hosts") or {}
    freshness = {h.get("freshness") for h in hosts.values()}
    if "critical" in severities or "down" in freshness:
        return "red"
    if "warning" in severities or "stale" in freshness:
        return "amber"
    if not hosts:
        return "gray"
    return "green"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest labwatch/tests/test_tray_logic.py -v`
Expected: PASS (8 passed).

- [ ] **Step 5: Commit**

```bash
git add labwatch/tray_logic.py labwatch/tests/test_tray_logic.py
git commit -m "feat(tray): pure status_color + alert-diff logic"
```

---

## Task 2: Harden tunnel.py for Windows

**Files:**
- Modify: `labwatch/tunnel.py`
- Test: `labwatch/tests/test_tunnel.py`

- [ ] **Step 1: Write the failing tests (append)**

Append to `labwatch/tests/test_tunnel.py`:
```python
def test_build_ssh_cmd_has_keepalive():
    cmd = tunnel.build_ssh_cmd(4002, "m4")
    assert "ServerAliveInterval=30" in cmd


def test_popen_kwargs_windows(monkeypatch):
    monkeypatch.setattr(tunnel.sys, "platform", "win32")
    kw = tunnel._popen_kwargs()
    assert "creationflags" in kw


def test_popen_kwargs_non_windows(monkeypatch):
    monkeypatch.setattr(tunnel.sys, "platform", "linux")
    assert tunnel._popen_kwargs() == {}


def test_stop_is_noop_when_no_proc():
    tunnel._proc = None
    tunnel.stop()  # must not raise
    assert tunnel._proc is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest labwatch/tests/test_tunnel.py -k "keepalive or popen or noop" -v`
Expected: FAIL (`AttributeError: module 'tunnel' has no attribute 'sys'` / `_popen_kwargs`).

- [ ] **Step 3: Modify `labwatch/tunnel.py`**

(a) Add `import sys` to the imports (next to `import socket`, `import subprocess`, `import time`).

(b) Replace `build_ssh_cmd` with the keepalive version:
```python
def build_ssh_cmd(local_port: int, remote: str, remote_host: str = "localhost",
                  remote_port: int = None) -> list:
    remote_port = remote_port or local_port
    return ["ssh", "-N",
            "-o", "ExitOnForwardFailure=yes",
            "-o", "ServerAliveInterval=30",
            "-L", f"{local_port}:{remote_host}:{remote_port}", remote]
```

(c) Add a `_popen_kwargs` helper just above `ensure`:
```python
def _popen_kwargs() -> dict:
    # On Windows, prevent a console window flashing for the background ssh.
    if sys.platform == "win32":
        return {"creationflags": subprocess.CREATE_NO_WINDOW}
    return {}
```

(d) In `ensure`, change the Popen line to pass the kwargs:
```python
    _proc = subprocess.Popen(build_ssh_cmd(local_port, remote, remote_port=remote_port),
                             **_popen_kwargs())
```

(e) Replace `stop` with the tree-kill version:
```python
def stop():
    global _proc
    if _proc is None:
        return
    try:
        _proc.terminate()
        _proc.wait(timeout=2)
    except Exception:
        # ssh on Windows can leave a child; tree-kill by PID.
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(_proc.pid)],
                           capture_output=True)
    finally:
        _proc = None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest labwatch/tests/test_tunnel.py -v`
Expected: PASS (8 passed — 4 original + 4 new).

- [ ] **Step 5: Commit**

```bash
git add labwatch/tunnel.py labwatch/tests/test_tunnel.py
git commit -m "harden(tunnel): keepalive + Windows CREATE_NO_WINDOW + tree-kill stop"
```

---

## Task 3: tray.py glue + tray requirements + tray test

**Files:**
- Create: `labwatch/tray.py`
- Create: `labwatch/requirements-tray.txt`
- Test: `labwatch/tests/test_tray.py`

- [ ] **Step 1: Write the failing test**

Create `labwatch/tests/test_tray.py`:
```python
import json


def test_make_image_is_64px():
    import tray
    img = tray.make_image("green")
    assert img.size == (64, 64)


def test_fetch_state_parses_json(monkeypatch):
    import tray

    class FakeResp:
        def __init__(self, data):
            self._d = data
        def read(self):
            return self._d
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False

    payload = json.dumps({"hosts": {}, "alerts": []}).encode()
    monkeypatch.setattr(tray.urllib.request, "urlopen",
                        lambda *a, **k: FakeResp(payload))
    assert tray.fetch_state() == {"hosts": {}, "alerts": []}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest labwatch/tests/test_tray.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'tray'`).

- [ ] **Step 3: Create `labwatch/requirements-tray.txt`**

```
pystray>=0.19
Pillow>=10.0
windows-toasts>=1.1
```

- [ ] **Step 4: Create `labwatch/tray.py`**

`pystray` and `windows_toasts` are imported LAZILY (inside methods) so that `import tray` — and the `make_image`/`fetch_state` tests — work without a GUI backend installed.
```python
"""NAUTILUS tray (Surface): persistent tunnel + fleet indicator + toasts.

Thin GUI shell over tray_logic (pure) and tunnel (shared). pystray and
windows_toasts are imported lazily so module import stays testable.
"""

import json
import threading
import time
import urllib.request
import webbrowser

from PIL import Image, ImageDraw

import tray_logic
import tunnel

API_URL = "http://127.0.0.1:4002/api/state"
DASH_URL = "http://localhost:4002"
POLL_S = 10

_RGB = {
    "green": (34, 197, 94),
    "amber": (251, 191, 36),
    "red": (239, 68, 68),
    "gray": (120, 120, 120),
}


def make_image(color: str) -> Image.Image:
    img = Image.new("RGB", (64, 64), (15, 23, 42))
    d = ImageDraw.Draw(img)
    d.ellipse((10, 10, 54, 54), fill=_RGB.get(color, _RGB["gray"]))
    return img


def fetch_state(url: str = API_URL, timeout: float = 3.0) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read())


class Tray:
    def __init__(self):
        import pystray
        self._prev_alerts = set()
        self._toaster = None
        self.icon = pystray.Icon(
            "nautilus", make_image("gray"), "NAUTILUS Mesh",
            menu=pystray.Menu(
                pystray.MenuItem("Open Dashboard", self._open, default=True),
                pystray.MenuItem("Restart Tunnel", self._restart),
                pystray.MenuItem("Quit", self._quit),
            ),
        )

    def _open(self, *_a):
        webbrowser.open(DASH_URL)

    def _restart(self, *_a):
        tunnel.stop()
        tunnel.ensure(4002, "m4", 4002)

    def _quit(self, *_a):
        tunnel.stop()
        self.icon.stop()

    def _toast(self, msg: str):
        try:
            from windows_toasts import Toast, WindowsToaster
            if self._toaster is None:
                self._toaster = WindowsToaster("NAUTILUS Mesh")
            t = Toast()
            t.text_fields = ["NAUTILUS Alert", msg]
            self._toaster.show_toast(t)
        except Exception:
            pass  # toasts are best-effort; never break the loop

    def _loop(self):
        while True:
            try:
                tunnel.ensure(4002, "m4", 4002)
                state = fetch_state()
                self.icon.icon = make_image(tray_logic.status_color(state))
                for (aid, host) in tray_logic.new_alert_keys(self._prev_alerts, state):
                    self._toast(f"{host}: {aid}")
                self._prev_alerts = tray_logic.alert_keys(state)
            except Exception:
                self.icon.icon = make_image("gray")
            time.sleep(POLL_S)

    def run(self):
        threading.Thread(target=self._loop, daemon=True).start()
        self.icon.run()


def main():
    Tray().run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest labwatch/tests/test_tray.py -v`
Expected: PASS (2 passed). (These do not import pystray.)

- [ ] **Step 6: Run the full suite**

Run: `python -m pytest labwatch/tests/ -q`
Expected: all green.

- [ ] **Step 7: Commit**

```bash
git add labwatch/tray.py labwatch/requirements-tray.txt labwatch/tests/test_tray.py
git commit -m "feat(tray): pystray shell (indicator + tunnel mgr + toasts) + tray requirements"
```

---

## Task 4: Deploy the tray on Surface

**Files:**
- Create: `labwatch/run/run-tray-surface.ps1`
- Ops: install tray deps, launch + visual verify, scheduled task (user-gated).

> Runs on the Surface laptop (this machine). The tray icon appears in the USER's interactive session — visual confirmation is the user's. Scheduled-task registration needs an elevated shell (the agent session lacks rights — same gate as the reporter), so the registration command is handed to the user.

- [ ] **Step 1: Create the launcher**

Create `labwatch/run/run-tray-surface.ps1`:
```powershell
# NAUTILUS tray launcher (Surface). pythonw = no console window.
Set-Location "$PSScriptRoot\..\"
pythonw "labwatch\tray.py"
```

- [ ] **Step 2: Install the tray dependencies**

Run (PowerShell): `python -m pip install -r labwatch\requirements-tray.txt`
Expected: pystray, Pillow (already), windows-toasts install cleanly.

- [ ] **Step 3: Launch + visual verify (user)**

Run (PowerShell): `Start-Process pythonw -ArgumentList 'labwatch\tray.py' -WorkingDirectory 'C:\telo\Efforts\Ongoing\NAUTILUS'`
The USER confirms: a tray icon appears; its color reflects fleet freshness (green if m4+surface live; amber if surface stale because the reporter task isn't running yet); **double-left-click opens** `http://localhost:4002`; right-click shows Open Dashboard / Restart Tunnel / Quit.

- [ ] **Step 4: Commit the launcher**

```bash
git add labwatch/run/run-tray-surface.ps1
git commit -m "ops(tray): Surface tray launcher (pythonw, no console)"
```

- [ ] **Step 5: (User, elevated) register the logon scheduled task**

The agent session cannot create scheduled tasks (Access denied). In an elevated PowerShell the user runs:
```powershell
schtasks /Create /TN "NAUTILUS-Surface-Tray" /TR 'pythonw "C:\telo\Efforts\Ongoing\NAUTILUS\labwatch\tray.py"' /SC ONLOGON /F
```

---

## Phase 1b self-review checklist (run before handoff)

- [ ] Full suite green: `python -m pytest labwatch/tests/ -q`
- [ ] gitleaks clean: `gitleaks detect --no-banner --log-opts="main..HEAD"`
- [ ] `tray_logic.status_color` covers green/amber/red/gray + alert override
- [ ] tray.py imports without pystray installed (lazy import) — `make_image`/`fetch_state` tests pass
- [ ] tunnel.py spawns with no console window on Windows; `stop()` is None-safe
- [ ] Tray icon visible, double-click opens dashboard (user-confirmed)

---

## Notes for Phase 2 (alerts — next plan)

- The tray already toasts `new_alert_keys` and reddens on `critical`; Phase 2 only needs to make `/api/state.alerts` non-empty (watchers engine + `watchers.json`). No tray change required when alerts arrive.
- Telegram escape for `critical` (Phase 2) is independent of the tray.
- Draft to reconcile: `docs/superpowers/drafts/phase2-watchers-gemini.md`.
