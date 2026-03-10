#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_PATH="$(dirname "$(dirname "$SCRIPT_DIR")")/common/scripts/team_info_runtime.py"

PYTHON_BIN="${PYTHON:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN="python"
fi

exec "$PYTHON_BIN" "$RUNTIME_PATH" run-remotion-python -- "$SCRIPT_DIR/setup.py" "$@"
