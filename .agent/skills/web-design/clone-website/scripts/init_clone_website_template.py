#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


TEMPLATE_ROOT = Path(__file__).resolve().parents[1] / "assets" / "template"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Initialize a website cloning workspace from the bundled template."
    )
    parser.add_argument("target", help="Target directory to create")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow copying into a non-empty directory",
    )
    return parser.parse_args()


def ensure_target(target: Path, force: bool) -> None:
    if target.exists():
        if not target.is_dir():
            raise SystemExit(f"Target exists and is not a directory: {target}")
        has_entries = any(target.iterdir())
        if has_entries and not force:
            raise SystemExit(
                "Target directory is not empty. Use --force only if you really want to merge files."
            )
    else:
        target.mkdir(parents=True, exist_ok=True)


def copy_template(target: Path) -> None:
    for source in TEMPLATE_ROOT.rglob("*"):
        relative = source.relative_to(TEMPLATE_ROOT)
        destination = target / relative
        if source.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def main() -> int:
    args = parse_args()
    target = Path(args.target).expanduser().resolve()

    if not TEMPLATE_ROOT.exists():
        raise SystemExit(f"Template root not found: {TEMPLATE_ROOT}")

    ensure_target(target, args.force)
    copy_template(target)

    print(f"Initialized website clone workspace at: {target}")
    print("Next steps:")
    print("  1. source \"$HOME/.nvm/nvm.sh\"")
    print("  2. nvm use 24")
    print(f"  3. cd \"{target}\"")
    print("  4. npm install")
    print("  5. npm run build")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
