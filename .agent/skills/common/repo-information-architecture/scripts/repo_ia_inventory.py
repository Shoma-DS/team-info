#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from collections import Counter, defaultdict
from pathlib import Path


IGNORE_NAMES = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    ".next",
    ".turbo",
    ".idea",
}

FLAGGED_TOKENS = ("personal", "tmp", "temp", "old", "backup", "copy", "draft", "test")


def should_skip(path: Path) -> bool:
    return any(part in IGNORE_NAMES for part in path.parts)


def walk_dirs(root: Path, max_depth: int) -> list[Path]:
    paths: list[Path] = []
    root = root.resolve()
    for current_root, dirnames, _ in os.walk(root):
        current = Path(current_root)
        rel_current = current.relative_to(root)

        dirnames[:] = [
            name
            for name in dirnames
            if name not in IGNORE_NAMES
        ]

        if rel_current.parts and len(rel_current.parts) <= max_depth:
            paths.append(rel_current)

        if len(rel_current.parts) >= max_depth:
            dirnames[:] = []
    return sorted(paths)


def summarize_top_level(paths: list[Path]) -> list[tuple[str, int]]:
    counter = Counter()
    for rel in paths:
        if not rel.parts:
            continue
        counter[rel.parts[0]] += 1
    return sorted(counter.items(), key=lambda item: (-item[1], item[0]))


def repeated_basenames(paths: list[Path], min_count: int) -> dict[str, list[str]]:
    buckets: dict[str, list[str]] = defaultdict(list)
    for rel in paths:
        if not rel.parts:
            continue
        buckets[rel.name].append(str(rel))
    return {
        name: sorted(items)
        for name, items in buckets.items()
        if len(items) >= min_count
    }


def flagged_paths(paths: list[Path]) -> list[str]:
    found: list[str] = []
    for rel in paths:
        lower = "/".join(rel.parts).lower()
        if any(token in lower for token in FLAGGED_TOKENS):
            found.append(str(rel))
    return found


def rules_alignment(root: Path) -> list[str]:
    expected = [
        "inputs",
        "outputs",
        "Remotion",
        ".agent",
        "scripts",
        "docker",
        "mcp-servers",
        "GAS",
    ]
    missing = [name for name in expected if not (root / name).exists()]
    return missing


def render_markdown(root: Path, max_depth: int, min_repeat: int) -> str:
    paths = walk_dirs(root, max_depth=max_depth)
    top = summarize_top_level(paths)
    repeats = repeated_basenames(paths, min_count=min_repeat)
    flagged = flagged_paths(paths)
    missing = rules_alignment(root)

    lines: list[str] = []
    lines.append("# Repo IA Inventory")
    lines.append("")
    lines.append(f"- root: `{root}`")
    lines.append(f"- scanned directories: `{len(paths)}`")
    lines.append(f"- max depth: `{max_depth}`")
    lines.append("")
    lines.append("## Top-level density")
    for name, count in top[:20]:
        lines.append(f"- `{name}`: {count}")
    lines.append("")
    lines.append("## Repeated basenames")
    if repeats:
        for name, items in sorted(repeats.items()):
            lines.append(f"- `{name}`")
            for item in items[:8]:
                lines.append(f"  - `{item}`")
            if len(items) > 8:
                lines.append(f"  - ... ({len(items) - 8} more)")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Flagged paths")
    if flagged:
        for item in flagged[:40]:
            lines.append(f"- `{item}`")
        if len(flagged) > 40:
            lines.append(f"- ... ({len(flagged) - 40} more)")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## RULES baseline missing")
    if missing:
        for item in missing:
            lines.append(f"- `{item}`")
    else:
        lines.append("- none")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Emit a compact repo inventory for information architecture reviews."
    )
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--max-depth", type=int, default=4, help="Max directory depth")
    parser.add_argument(
        "--min-repeat",
        type=int,
        default=2,
        help="Minimum repeated basename count to report",
    )
    parser.add_argument(
        "--format",
        choices=("markdown",),
        default="markdown",
        help="Output format",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    print(render_markdown(root, max_depth=args.max_depth, min_repeat=args.min_repeat))


if __name__ == "__main__":
    main()
