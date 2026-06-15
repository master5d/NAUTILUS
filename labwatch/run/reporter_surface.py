"""Direct pythonw entrypoint for the Surface reporter scheduled task.

Calling `pythonw <this file>` directly (no PowerShell wrapper) mirrors the
working tray task and sidesteps three Windows pitfalls that silently killed the
old launcher:
  * bare `python` resolves to the Microsoft Store alias stub under a hidden
    scheduled task (exits 0, loop never starts) — `pythonw` has no such alias;
  * a `-WindowStyle Hidden` `-File` script never kept the child alive;
  * windowless pythonw has sys.stdout/stderr == None (handled by reporter's
    log guard so a transient cycle error can't terminate the loop).

Sets host=surface defaults via setdefault (so explicit env still wins), puts
labwatch/ on sys.path, then runs the reporter loop.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LABWATCH = os.path.dirname(HERE)
sys.path.insert(0, LABWATCH)
os.chdir(LABWATCH)  # spool/keyring default paths are relative to labwatch/

os.environ.setdefault("REPORTER_HOST", "surface")
os.environ.setdefault("INGEST_URL", "http://127.0.0.1:4002/ingest")
os.environ.setdefault("REPORTER_TUNNEL", "m4")
os.environ.setdefault("REPORTER_INTERVAL", "30")

import reporter  # noqa: E402  (path set up above)

reporter.main()
