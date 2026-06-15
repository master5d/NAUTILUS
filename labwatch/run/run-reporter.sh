#!/bin/bash
# M4 observability reporter launcher.
# Uses the SAME interpreter as labwatch (/opt/homebrew/bin/python3.12) so the
# collector + reporter share one set of deps (jsonschema, psutil). Runs as the
# sovrnnode03 user (set UserName in the LaunchDaemon plist) so that
# os.path.expanduser("~") resolves to /Users/sovrnnode03 and finds the keyring
# at ~/.config/nautilus/secrets/observability.keyring.json.
export PATH="/opt/homebrew/bin:$PATH"
export REPORTER_HOST="m4"
export INGEST_URL="http://127.0.0.1:4002/ingest"
export REPORTER_INTERVAL="30"
cd "$HOME/nautilus/labwatch" || exit 1
exec /opt/homebrew/bin/python3.12 reporter.py
