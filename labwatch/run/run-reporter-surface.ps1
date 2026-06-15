# Surface observability reporter launcher.
# Reports host=surface to the M4 collector through an SSH tunnel (Surface:4002 -> M4:4002).
$env:REPORTER_HOST = "surface"
$env:INGEST_URL = "http://127.0.0.1:4002/ingest"
$env:REPORTER_TUNNEL = "m4"
$env:REPORTER_INTERVAL = "30"
Set-Location "$PSScriptRoot\..\"
python "labwatch\reporter.py"
