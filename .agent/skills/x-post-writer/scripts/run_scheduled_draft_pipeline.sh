#!/bin/bash
# Xブックマーク→下書き生成の定時ジョブを launchd から起動するラッパー。
# .claude/settings.local.json の env を読み込み、repo ルートを固定して実行する。

set -euo pipefail

# launchd は PATH が /usr/bin:/bin:/usr/sbin:/sbin のみのため pyenv を明示的に追加する
export PYENV_ROOT="${PYENV_ROOT:-$HOME/.pyenv}"
export PATH="$PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH"
if command -v pyenv &>/dev/null; then
  eval "$(pyenv init -)"
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"

if [ -f "$HOME/.config/team-info/env.sh" ]; then
  # shellcheck disable=SC1090
  source "$HOME/.config/team-info/env.sh"
fi

export TEAM_INFO_ROOT="${TEAM_INFO_ROOT:-$REPO_ROOT}"

python3 "$SCRIPT_DIR/with_local_env.py" -- \
  python3 "$SCRIPT_DIR/scheduled_draft_pipeline.py" "$@"
