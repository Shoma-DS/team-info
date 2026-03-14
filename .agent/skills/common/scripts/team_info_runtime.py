#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from runtime_common import (
    build_python_runtime_image,
    clear_worked_before,
    clear_owner_machine,
    configure_repo_git_hooks,
    detect_shared_root,
    ensure_remotion_venv,
    format_bytes_for_humans,
    get_git_lfs_free_plan_status,
    get_python_runtime_image,
    get_python_runtime_mode,
    get_worked_before_path,
    has_worked_before,
    get_local_state_path,
    get_machine_fingerprint,
    get_repo_root,
    get_voicevox_base_url,
    is_owner_machine,
    is_voicevox_available,
    is_voicevox_container_running,
    mark_worked_before,
    pull_voicevox_engine_image,
    resolve_input_path,
    run_remotion_python,
    save_owner_machine,
    save_repo_root,
    start_voicevox_engine_container,
    stop_voicevox_engine_container,
)


def _copy_to_shared(source: Path, shared_root: Path, subpath: str | None) -> Path:
    if not source.exists():
        raise FileNotFoundError(f"Source was not found: {source}")

    destination = shared_root / subpath if subpath else shared_root / source.name
    destination.parent.mkdir(parents=True, exist_ok=True)

    if source.is_dir():
        shutil.copytree(source, destination, dirs_exist_ok=True)
    else:
        shutil.copy2(source, destination)

    return destination


def _format_shell_export(repo_root: Path, shell_name: str) -> str:
    repo_root_str = str(repo_root)
    if shell_name == "powershell":
        return f'$env:TEAM_INFO_ROOT = "{repo_root_str}"'
    if shell_name == "cmd":
        return f"set TEAM_INFO_ROOT={repo_root_str}"
    return f'export TEAM_INFO_ROOT="{repo_root_str}"'


def _print_git_lfs_free_plan_status(*, remote_name: str, remote_url: str | None, pre_push_lines: list[str] | None) -> int:
    try:
        status = get_git_lfs_free_plan_status(
            remote_name=remote_name,
            remote_url=remote_url,
            pre_push_lines=pre_push_lines,
        )
    except RuntimeError as exc:
        print(f"Git LFS 無料枠チェックに失敗しました: {exc}", file=sys.stderr)
        return 1

    target_remote = status.remote_url or status.remote_name
    print("Git LFS 無料枠チェック", file=sys.stderr)
    print(f"- リモート: {target_remote}", file=sys.stderr)
    print(
        f"- 無料枠: {format_bytes_for_humans(status.free_storage_bytes)}"
        f" / 予約分: {format_bytes_for_humans(status.reserved_bytes)}"
        f" / 利用可能: {format_bytes_for_humans(status.available_bytes)}",
        file=sys.stderr,
    )
    print(
        f"- 現在の推定総量: {format_bytes_for_humans(status.current_bytes)}"
        f" ({status.current_object_count} 個)",
        file=sys.stderr,
    )
    print(
        f"- 今回の push で増える見込み: {format_bytes_for_humans(status.incoming_bytes)}"
        f" ({status.incoming_object_count} 個)",
        file=sys.stderr,
    )
    print(
        f"- push 後の推定総量: {format_bytes_for_humans(status.projected_bytes)}"
        f" ({status.projected_object_count} 個)",
        file=sys.stderr,
    )

    if not status.has_lfs_content:
        print("- LFS ポインタは見つかりませんでした。", file=sys.stderr)
        return 0

    if status.warning:
        print(f"警告: {status.warning}", file=sys.stderr)

    if status.within_budget:
        print("結果: push 可能です。", file=sys.stderr)
        return 0

    print("結果: push を拒否しました。", file=sys.stderr)
    if status.rejection_reason:
        print(f"理由: {status.rejection_reason}", file=sys.stderr)
    print("対策:", file=sys.stderr)
    print("- LFS に入れる大きいファイルを減らす。", file=sys.stderr)
    print("- 既存の LFS 履歴を整理して容量を下げる。", file=sys.stderr)
    print("- 同じ GitHub アカウントで他の LFS を使うなら、予約分を設定する。", file=sys.stderr)
    print("- 有料枠を使わない方針なら、LFS 以外の置き場へ逃がす。", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Resolve cross-platform paths used by team-info skills."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("repo-root")
    repo_path_parser = subparsers.add_parser("repo-path")
    repo_path_parser.add_argument("relative_path")
    subparsers.add_parser("remotion-python")
    subparsers.add_parser("python-runtime-mode")
    subparsers.add_parser("build-remotion-python")
    subparsers.add_parser("pull-voicevox-engine")
    subparsers.add_parser("start-voicevox-engine")
    subparsers.add_parser("stop-voicevox-engine")
    subparsers.add_parser("voicevox-engine-status")
    subparsers.add_parser("shared-root")
    subparsers.add_parser("shared-jmty-root")
    subparsers.add_parser("local-state-path")
    subparsers.add_parser("worked-before-path")
    subparsers.add_parser("machine-id")
    subparsers.add_parser("owner-status")
    subparsers.add_parser("worked-before-status")
    subparsers.add_parser("mark-worked-before")
    subparsers.add_parser("clear-worked-before")
    subparsers.add_parser("mark-owner-machine")
    subparsers.add_parser("clear-owner-machine")
    subparsers.add_parser("install-git-hooks")

    git_lfs_status_parser = subparsers.add_parser("git-lfs-free-plan-status")
    git_lfs_status_parser.add_argument("--remote-name", default="origin")
    git_lfs_status_parser.add_argument("--remote-url")

    git_lfs_guard_parser = subparsers.add_parser("git-lfs-pre-push-guard")
    git_lfs_guard_parser.add_argument("--remote-name", default="origin")
    git_lfs_guard_parser.add_argument("--remote-url")

    setup_parser = subparsers.add_parser("setup-local-machine")
    setup_parser.add_argument(
        "--repo-root",
        default=".",
        help="Path to the local team-info checkout. Default: current directory.",
    )
    setup_parser.add_argument(
        "--owner",
        action="store_true",
        help="Mark the current machine as the owner machine.",
    )
    setup_parser.add_argument(
        "--shell",
        choices=("sh", "powershell", "cmd"),
        default="sh",
        help="Shell format used when printing TEAM_INFO_ROOT export guidance.",
    )

    shell_export_parser = subparsers.add_parser("shell-export")
    shell_export_parser.add_argument(
        "--shell",
        choices=("sh", "powershell", "cmd"),
        default="sh",
        help="Shell format used when printing TEAM_INFO_ROOT export guidance.",
    )

    copy_parser = subparsers.add_parser("copy-to-shared")
    copy_parser.add_argument("source")
    copy_parser.add_argument("--subpath")
    copy_parser.add_argument("--shared-root")

    run_parser = subparsers.add_parser("run-remotion-python")
    run_parser.add_argument("run_args", nargs=argparse.REMAINDER)

    args = parser.parse_args()

    if args.command == "repo-root":
        print(get_repo_root())
        return 0

    if args.command == "repo-path":
        print(get_repo_root() / args.relative_path)
        return 0

    if args.command == "remotion-python":
        if get_python_runtime_mode() == "docker":
            print(f"docker://{get_python_runtime_image()}")
        else:
            print(ensure_remotion_venv())
        return 0

    if args.command == "python-runtime-mode":
        print(get_python_runtime_mode())
        return 0

    if args.command == "build-remotion-python":
        print(build_python_runtime_image())
        return 0

    if args.command == "pull-voicevox-engine":
        print(pull_voicevox_engine_image())
        return 0

    if args.command == "start-voicevox-engine":
        print(start_voicevox_engine_container())
        return 0

    if args.command == "stop-voicevox-engine":
        print(stop_voicevox_engine_container())
        return 0

    if args.command == "voicevox-engine-status":
        if is_voicevox_container_running() and is_voicevox_available():
            print(f"running {get_voicevox_base_url()}")
        elif is_voicevox_container_running():
            print("starting")
        else:
            print("stopped")
        return 0

    if args.command == "shared-root":
        shared_root = detect_shared_root()
        if shared_root is None:
            print(
                "Shared root could not be detected. "
                "Set TEAM_INFO_SHARED_ROOT to the synced team-info directory.",
                file=sys.stderr,
            )
            return 1
        print(shared_root)
        return 0

    if args.command == "shared-jmty-root":
        shared_root = detect_shared_root()
        if shared_root is None:
            print(
                "Shared root could not be detected. "
                "Set TEAM_INFO_SHARED_ROOT to the synced team-info directory.",
                file=sys.stderr,
            )
            return 1
        print(shared_root / "outputs" / "jmty")
        return 0

    if args.command == "local-state-path":
        print(get_local_state_path())
        return 0

    if args.command == "worked-before-path":
        print(get_worked_before_path())
        return 0

    if args.command == "machine-id":
        print(get_machine_fingerprint())
        return 0

    if args.command == "owner-status":
        print("owner" if is_owner_machine() else "other")
        return 0

    if args.command == "worked-before-status":
        print("known" if has_worked_before() else "new")
        return 0

    if args.command == "mark-worked-before":
        print(mark_worked_before())
        return 0

    if args.command == "clear-worked-before":
        removed = clear_worked_before()
        print("cleared" if removed else "not-found")
        return 0

    if args.command == "mark-owner-machine":
        print(save_owner_machine())
        return 0

    if args.command == "clear-owner-machine":
        clear_owner_machine()
        print("cleared")
        return 0

    if args.command == "install-git-hooks":
        try:
            print(configure_repo_git_hooks())
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        return 0

    if args.command == "git-lfs-free-plan-status":
        return _print_git_lfs_free_plan_status(
            remote_name=args.remote_name,
            remote_url=args.remote_url,
            pre_push_lines=None,
        )

    if args.command == "git-lfs-pre-push-guard":
        pre_push_lines = [line.rstrip("\n") for line in sys.stdin]
        return _print_git_lfs_free_plan_status(
            remote_name=args.remote_name,
            remote_url=args.remote_url,
            pre_push_lines=pre_push_lines,
        )

    if args.command == "setup-local-machine":
        repo_root = save_repo_root(args.repo_root)
        print(f"Saved repo root: {repo_root}")
        print(f"Local state: {get_local_state_path()}")
        print(f"Worked before file: {mark_worked_before()}")
        print(f"Git hooks: {configure_repo_git_hooks(repo_root)}")

        if args.owner:
            save_owner_machine()
            print("Owner machine: current machine was marked as owner")
        else:
            print("Owner machine: unchanged")

        print("Shell export:")
        print(_format_shell_export(repo_root, args.shell))
        return 0

    if args.command == "shell-export":
        print(_format_shell_export(get_repo_root(), args.shell))
        return 0

    if args.command == "copy-to-shared":
        shared_root: Path | None = (
            resolve_input_path(args.shared_root)
            if args.shared_root
            else detect_shared_root()
        )
        if shared_root is None:
            print(
                "Shared root could not be detected. "
                "Set TEAM_INFO_SHARED_ROOT or pass --shared-root.",
                file=sys.stderr,
            )
            return 1

        assert shared_root is not None  # 型チェッカー向けナローイング
        source = resolve_input_path(args.source)
        destination = _copy_to_shared(source, shared_root, args.subpath)
        print(destination)
        return 0

    if args.command == "run-remotion-python":
        run_args: list[str] = list(args.run_args)
        if run_args and run_args[0] == "--":
            run_args.pop(0)
        if not run_args:
            print("No command was provided to run-remotion-python.", file=sys.stderr)
            return 1

        try:
            completed = run_remotion_python(run_args)
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        return completed.returncode

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
