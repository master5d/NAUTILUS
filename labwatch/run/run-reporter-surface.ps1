# Surface observability reporter launcher.
# Reports host=surface to the M4 collector through an SSH tunnel (Surface:4002 -> M4:4002).
$env:REPORTER_HOST = "surface"
$env:INGEST_URL = "http://127.0.0.1:4002/ingest"
$env:REPORTER_TUNNEL = "m4"
$env:REPORTER_INTERVAL = "30"
Set-Location "$PSScriptRoot\..\"

# Resolve a REAL python, never the Microsoft Store alias stub (WindowsApps\python.exe).
# Under a hidden-window scheduled task the Store stub silently exits 0, so the reporter
# loop never starts. Pin to pythonw.exe by absolute path and fall back to a PATH lookup
# that explicitly skips WindowsApps.
$py = "$env:LOCALAPPDATA\Programs\Python\Python313\pythonw.exe"
if (-not (Test-Path $py)) {
    $py = Get-Command pythonw.exe -All -ErrorAction SilentlyContinue |
        Where-Object { $_.Source -notlike "*WindowsApps*" } |
        Select-Object -First 1 -ExpandProperty Source
}
if (-not $py) { throw "No real pythonw.exe found (only the Store alias)." }

# pythonw.exe has NO console: with no std handles sys.stdout/stderr are None and the
# first print() raises, killing a windowless process. Redirecting all streams to a log
# file gives pythonw real handles (so it survives) AND captures reporter diagnostics.
$logDir = "$env:LOCALAPPDATA\nautilus"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log = Join-Path $logDir "reporter-surface.log"

# Blocking call — keeps the scheduled task alive while the reporter loops.
& $py "labwatch\reporter.py" *>> $log
