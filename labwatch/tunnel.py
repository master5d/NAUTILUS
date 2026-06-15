"""SSH local-forward tunnel helper.

The M4 collector binds 127.0.0.1 only, so a remote reporter (Surface) reaches
its /ingest through an SSH local forward: Surface:LOCAL -> M4:127.0.0.1:REMOTE.
Shared by the Surface reporter (Phase 1a) and the tray app (Phase 1b).
"""

import socket
import subprocess
import sys
import time

_proc = None


def build_ssh_cmd(local_port: int, remote: str, remote_host: str = "localhost",
                  remote_port: int = None) -> list:
    remote_port = remote_port or local_port
    return ["ssh", "-N",
            "-o", "ExitOnForwardFailure=yes",
            "-o", "ServerAliveInterval=30",
            "-L", f"{local_port}:{remote_host}:{remote_port}", remote]


def is_up(local_port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", local_port), timeout=timeout):
            return True
    except OSError:
        return False


def _popen_kwargs() -> dict:
    # On Windows, prevent a console window flashing for the background ssh.
    if sys.platform == "win32":
        return {"creationflags": subprocess.CREATE_NO_WINDOW}
    return {}


def ensure(local_port: int = 4002, remote: str = "m4", remote_port: int = 4002,
           wait_s: float = 8.0) -> bool:
    """Ensure a forward on local_port is live. No-op if something already serves
    it (e.g. the tray's persistent tunnel). Returns True if up within wait_s."""
    global _proc
    if is_up(local_port):
        return True
    _proc = subprocess.Popen(build_ssh_cmd(local_port, remote, remote_port=remote_port),
                             **_popen_kwargs())
    t0 = time.time()
    while time.time() - t0 < wait_s:
        if is_up(local_port):
            return True
        time.sleep(0.4)
    return is_up(local_port)


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
