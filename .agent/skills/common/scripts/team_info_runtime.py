#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from runtime_common import (
    detect_shared_root,
    ensure_remotion_venv,
    get_repo_root,
    resolve_input_path,
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


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Resolve cross-platform paths used by team-info skills."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("repo-root")
    subparsers.add_parser("remotion-python")
    subparsers.add_parser("shared-root")
    subparsers.add_parser("shared-jmty-root")

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

