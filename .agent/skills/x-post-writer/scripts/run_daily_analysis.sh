#!/bin/bash
# X投稿の日次分析ジョブを launchd から起動するラッパー。
# .claude/settings.local.json の env を読み込み、repo ルートを固定して実行する。

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"

if [ -f "$HOME/.config/team-info/env.sh" ]; then
  # shellcheck disable=SC1090
  source "$HOME/.config/team-info/env.sh"
fi

export TEAM_INFO_ROOT="${TEAM_INFO_ROOT:-$REPO_ROOT}"

python3 "$SCRIPT_DIR/with_local_env.py" -- \
  python3 "$SCRIPT_DIR/daily_analysis.py" "$@"
