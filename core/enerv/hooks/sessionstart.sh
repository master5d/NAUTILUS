#!/bin/bash

# SessionStart hook: Automatically reindex tech and knowledge roots
# on Claude Code session initialization with hybrid debounce logic.

set -euo pipefail

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Invoke facet auto-index command
# Defaults use C:\telo (tech) and E:\ (knowledge)
python -m tools.tools auto-index > /dev/null 2>&1 || true

# Note: We silently succeed even if command fails, to avoid blocking session start.
# Errors are logged via semantic logging, not user-facing.
