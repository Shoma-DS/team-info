#!/usr/bin/env python3
# このスクリプトは .claude/settings.local.json の env を読み込み、Codex を起動する。
# Claude Code 用のローカル設定を正本のまま使い、Codex でも同じ秘密情報を見えるようにする。
# 値そのものは表示せず、必要なら読めた項目名だけ確認できる。

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CLAUDE_SETTINGS_FILE = REPO_ROOT / ".claude" / "settings.local.json"


def fail(message: str) -> int:
    print(f"❌ {message}", file=sys.stderr)
    return 1


def load_claude_env() -> dict[str, str]:
    if not CLAUDE_SETTINGS_FILE.exists():
        raise FileNotFoundError(f"設定ファイルが見つかりません: {CLAUDE_SETTINGS_FILE}")

    try:
        config = json.loads(CLAUDE_SETTINGS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"settings.local.json の JSON が壊れています: {exc}") from exc

    env = config.get("env")
    if not isinstance(env, dict):
        raise ValueError("settings.local.json に env オブジェクトがありません")

    loaded_env: dict[str, str] = {}
    for key, value in env.items():
        if not isinstance(key, str):
            raise ValueError("env のキーは文字列である必要があります")
        if isinstance(value, str):
            loaded_env[key] = value
        else:
            loaded_env[key] = str(value)

    return loaded_env


def print_env_status(loaded_env: dict[str, str]) -> int:
    keys = sorted(loaded_env.keys())
    if not keys:
        print("読み込める env はありませんでした")
        return 0

    print(f"読み込み対象: {CLAUDE_SETTINGS_FILE}")
    for key in keys:
        print(f"{key}=set")
    return 0


def main() -> int:
    try:
        loaded_env = load_claude_env()
    except (FileNotFoundError, ValueError) as exc:
        return fail(str(exc))

    if len(sys.argv) > 1 and sys.argv[1] == "--check-env":
        return print_env_status(loaded_env)

    codex_path = shutil.which("codex")
    if not codex_path:
        return fail("codex コマンドが見つかりません")

    env = os.environ.copy()
    env.update(loaded_env)
    env.setdefault("TEAM_INFO_ROOT", str(REPO_ROOT))

    os.execvpe(codex_path, [codex_path, *sys.argv[1:]], env)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
