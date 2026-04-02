#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


REQUIRED_HOST_COMMANDS = ("node", "npm", "codex", "gh", "rclone")


def _run(
    command: list[str],
    *,
    cwd: Path | None = None,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        check=check,
        capture_output=True,
        text=True,
    )


def _print_heading(title: str) -> None:
    print(f"\n== {title} ==")


def _truncate(text: str, limit: int = 240) -> str:
    compact = " ".join(text.strip().split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def _check_host_commands(failures: list[str]) -> None:
    _print_heading("基本コマンド")
    for command in REQUIRED_HOST_COMMANDS:
        path = shutil.which(command)
        if path:
            print(f"[OK] {command}: {path}")
        else:
            print(f"[NG] {command}: コマンドが見つかりません")
            failures.append(f"{command} が見つかりません。")


def _check_git_lfs(failures: list[str]) -> None:
    _print_heading("Git LFS")
    if shutil.which("git") is None:
        print("[NG] git lfs: git コマンドが見つかりません")
        failures.append("git が見つからないため git lfs を確認できません。")
        return

    completed = _run(["git", "lfs", "version"])
    if completed.returncode == 0:
        print(f"[OK] git lfs: {completed.stdout.strip()}")
        return

    message = _truncate(completed.stderr or completed.stdout or "git lfs version の取得に失敗しました")
    print(f"[NG] git lfs: {message}")
    failures.append("git lfs が使えません。")


def _check_gh_auth(failures: list[str]) -> None:
    _print_heading("GitHub CLI (gh) 認証")
    if shutil.which("gh") is None:
        print("[NG] gh: コマンドが見つかりません")
        failures.append("gh が見つかりません。")
        return

    completed = _run(["gh", "auth", "status"])
    if completed.returncode == 0:
        print("[OK] gh auth: ログイン済み")
    else:
        message = _truncate(completed.stderr or completed.stdout or "未ログインです")
        print(f"[NG] gh auth: {message}")
        failures.append("GitHub CLI (gh) でログインしていません。'gh auth login' を実行してください。")


def _check_remote_url(repo_root: Path, failures: list[str]) -> None:
    _print_heading("Git リモート URL")
    expected_urls = {
        "https://github.com/Shoma-DS/team-info.git",
        "git@github.com:Shoma-DS/team-info.git",
    }
    completed = _run(["git", "-C", str(repo_root), "remote", "get-url", "origin"])
    current_url = completed.stdout.strip()
    if completed.returncode == 0 and current_url in expected_urls:
        print(f"[OK] origin: {current_url}")
    else:
        print(f"[NG] origin: {current_url or '(empty)'}")
        expected_text = " / ".join(sorted(expected_urls))
        failures.append(f"リモート URL が想定値ではありません。期待値: {expected_text}")


def _check_repo_git_hooks(repo_root: Path, failures: list[str]) -> None:
    _print_heading("Git Hooks")
    completed = _run(["git", "-C", str(repo_root), "config", "--get", "core.hooksPath"])
    hooks_path = completed.stdout.strip()
    normalized_hooks_path = Path(hooks_path).expanduser() if hooks_path else None
    hooks_path_ok = False
    if completed.returncode == 0:
        if hooks_path == ".githooks":
            hooks_path_ok = True
        elif normalized_hooks_path is not None and normalized_hooks_path.is_absolute():
            hooks_path_ok = normalized_hooks_path.resolve() == (repo_root / ".githooks").resolve()

    if hooks_path_ok:
        print(f"[OK] core.hooksPath: {hooks_path}")
    else:
        print(f"[NG] core.hooksPath: {hooks_path or '(empty)'}")
        failures.append("Git hooks の置き場が .githooks に設定されていません。")

    pre_push = repo_root / ".githooks" / "pre-push"
    if pre_push.exists():
        print(f"[OK] pre-push hook: {pre_push}")
    else:
        print(f"[NG] pre-push hook: {pre_push}")
        failures.append("Git LFS 無料枠を守る pre-push hook が見つかりません。")


def _check_python_toolchain(failures: list[str]) -> None:
    _print_heading("Python ツールチェーン")
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f"[OK] python executable: {sys.executable}")
    print(f"[OK] python version: {version}")
    if sys.version_info[:2] != (3, 11):
        failures.append("setup 検証は Python 3.11 系で実行してください。")


def _check_lazy_bootstrap_scripts(repo_root: Path, failures: list[str]) -> None:
    _print_heading("初回自動準備の入口")
    targets = (
        (repo_root / ".agent" / "skills" / "common" / "scripts" / "team_info_runtime.py", "Remotion / Python runtime bootstrap"),
        (repo_root / ".agent" / "skills" / "common" / "agent-reach" / "scripts" / "team_info_agent_reach.py", "Agent Reach bootstrap"),
        (repo_root / ".agent" / "skills" / "common" / "agent-reach" / "scripts" / "install_team_info_agent_reach.py", "Agent Reach installer"),
        (repo_root / ".agent" / "skills" / "common" / "obsidian-claudian" / "scripts" / "team_info_obsidian_claudian.py", "Obsidian / Claudian bootstrap"),
        (repo_root / ".agent" / "skills" / "common" / "shared-agent-assets" / "scripts" / "sync_shared_agent_repo.sh", "Shared agent assets sync"),
        (repo_root / ".agent" / "skills" / "web-design" / "clone-website" / "scripts" / "init_clone_website_template.py", "clone-website bootstrap"),
    )

    for path, label in targets:
        if path.exists():
            print(f"[OK] {label}: {path}")
        else:
            print(f"[NG] {label}: {path}")
            failures.append(f"{label} が見つかりません。")


def _check_team_info_root(repo_root: Path, failures: list[str], warnings: list[str]) -> None:
    _print_heading("TEAM_INFO_ROOT")
    current = os.environ.get("TEAM_INFO_ROOT", "")
    if current == str(repo_root):
        print(f"[OK] current env: {current}")
    else:
        print(f"[NG] current env: {current or '(empty)'}")
        failures.append("現在のプロセスで TEAM_INFO_ROOT が正しく見えていません。")

    if sys.platform == "darwin":
        env_file = Path.home() / ".config" / "team-info" / "env.sh"
        expected = f'export TEAM_INFO_ROOT="{repo_root}"'
        if env_file.exists() and expected in env_file.read_text(encoding="utf-8"):
            print(f"[OK] env file: {env_file}")
        else:
            print(f"[NG] env file: {env_file}")
            failures.append("macOS の env.sh に TEAM_INFO_ROOT が保存されていません。")

        launchctl = _run(["launchctl", "getenv", "TEAM_INFO_ROOT"])
        launchctl_value = launchctl.stdout.strip()
        if launchctl.returncode == 0 and launchctl_value == str(repo_root):
            print(f"[OK] launchctl: {launchctl_value}")
        else:
            print(f"[NG] launchctl: {launchctl_value or '(empty)'}")
            failures.append("launchctl に TEAM_INFO_ROOT が正しく保存されていません。")
        return

    if sys.platform == "win32":
        ps = _run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "[System.Environment]::GetEnvironmentVariable('TEAM_INFO_ROOT','User')",
            ]
        )
        user_value = ps.stdout.strip()
        if ps.returncode == 0 and user_value == str(repo_root):
            print(f"[OK] user env: {user_value}")
        else:
            print(f"[NG] user env: {user_value or '(empty)'}")
            failures.append("Windows ユーザー環境変数に TEAM_INFO_ROOT が保存されていません。")
        return

    warnings.append("この OS の TEAM_INFO_ROOT 永続化チェックは未対応です。")


def _check_optional_tools(warnings: list[str]) -> None:
    _print_heading("任意ツールのヒント")
    for tool in ("docker", "obsidian", "openclaw"):
        path = shutil.which(tool)
        if path:
            print(f"[OK] {tool}: {path}")
        else:
            print(f"[SKIP] {tool}: まだ入っていません")
            warnings.append(f"{tool} は必要なスキルを初めて使うときに導入してください。")


def main() -> int:
    parser = argparse.ArgumentParser(description="team-info セットアップ検証")
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[1]),
        help="team-info repository root",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    failures: list[str] = []
    warnings: list[str] = []

    print("team-info セットアップ検証")
    print(f"repo: {repo_root}")

    _check_host_commands(failures)
    _check_git_lfs(failures)
    _check_gh_auth(failures)
    _check_remote_url(repo_root, failures)
    _check_repo_git_hooks(repo_root, failures)
    _check_team_info_root(repo_root, failures, warnings)
    _check_python_toolchain(failures)
    _check_lazy_bootstrap_scripts(repo_root, failures)
    _check_optional_tools(warnings)

    _print_heading("まとめ")
    if failures:
        print("[NG] セットアップ検証に失敗しました")
        for item in failures:
            print(f"  - {item}")
    else:
        print("[OK] セットアップ検証に成功しました")

    if warnings:
        print("警告:")
        for item in warnings:
            print(f"  - {item}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
