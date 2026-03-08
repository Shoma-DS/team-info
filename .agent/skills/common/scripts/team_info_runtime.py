#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from runtime_common import (
    clear_owner_machine,
    detect_shared_root,
    ensure_remotion_venv,
    get_local_state_path,
    get_machine_fingerprint,
    get_repo_root,
    is_owner_machine,
    resolve_input_path,
    save_owner_machine,
    save_repo_root,
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


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Resolve cross-platform paths used by team-info skills."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("repo-root")
    repo_path_parser = subparsers.add_parser("repo-path")
    repo_path_parser.add_argument("relative_path")
    subparsers.add_parser("remotion-python")
    subparsers.add_parser("shared-root")
    subparsers.add_parser("shared-jmty-root")
    subparsers.add_parser("local-state-path")
    subparsers.add_parser("machine-id")
    subparsers.add_parser("owner-status")
    subparsers.add_parser("mark-owner-machine")
    subparsers.add_parser("clear-owner-machine")

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
        print(ensure_remotion_venv())
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

    if args.command == "machine-id":
        print(get_machine_fingerprint())
        return 0

    if args.command == "owner-status":
        print("owner" if is_owner_machine() else "other")
        return 0

    if args.command == "mark-owner-machine":
        print(save_owner_machine())
        return 0

    if args.command == "clear-owner-machine":
        clear_owner_machine()
        print("cleared")
        return 0

    if args.command == "setup-local-machine":
        repo_root = save_repo_root(args.repo_root)
        print(f"Saved repo root: {repo_root}")
        print(f"Local state: {get_local_state_path()}")

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
        shared_root = (
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

        source = resolve_input_path(args.source)
        destination = _copy_to_shared(source, shared_root, args.subpath)
        print(destination)
        return 0

    if args.command == "run-remotion-python":
        run_args = list(args.run_args)
        if run_args and run_args[0] == "--":
            run_args = run_args[1:]
        if not run_args:
            print("No command was provided to run-remotion-python.", file=sys.stderr)
            return 1

        remotion_python = ensure_remotion_venv()
        completed = subprocess.run(
            [str(remotion_python), *run_args],
            cwd=str(get_repo_root()),
        )
        return completed.returncode

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
