#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN="python"
fi

cd "$REPO_ROOT"
"$PYTHON_BIN" .agent/skills/common/scripts/team_info_runtime.py run-remotion-python -- -m pip install requests

echo "Remotion/.venv のセットアップと requests のインストールが完了しました。"
echo "生成スクリプトは 'python .agent/skills/common/scripts/team_info_runtime.py run-remotion-python -- Remotion/generate_voice.py' で起動できます。"
echo "または './Remotion/run.sh' を実行してください。"
