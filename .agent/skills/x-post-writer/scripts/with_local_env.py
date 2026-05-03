# .claude/settings.local.json の env を読み込み、指定コマンドをその環境で実行する。
# launchd から起動したジョブでも、X API や Neon の秘密情報を同じ正本から参照できるようにする。
# 使い方: python with_local_env.py -- <command> [args...]

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
CLAUDE_SETTINGS_FILE = REPO_ROOT / ".claude" / "settings.local.json"


def load_settings_env() -> dict[str, str]:
    if not CLAUDE_SETTINGS_FILE.exists():
        return {}

    config = json.loads(CLAUDE_SETTINGS_FILE.read_text(encoding="utf-8"))
    env = config.get("env")
    if not isinstance(env, dict):
        return {}

    loaded: dict[str, str] = {}
    for key, value in env.items():
        if isinstance(key, str):
            loaded[key] = value if isinstance(value, str) else str(value)
    return loaded


def main() -> int:
    args = sys.argv[1:]
    if args[:1] == ["--"]:
        args = args[1:]
    if not args:
        print("❌ 実行コマンドが必要です", file=sys.stderr)
        return 1

    env = os.environ.copy()
    env.update(load_settings_env())
    env.setdefault("TEAM_INFO_ROOT", str(REPO_ROOT))

    completed = subprocess.run(args, cwd=str(REPO_ROOT), env=env)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
