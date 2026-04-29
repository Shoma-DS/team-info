#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path


def find_project_root() -> Path:
    current = Path(__file__).resolve().parent
    for candidate in (current, *current.parents):
        if (candidate / "AGENTS.md").exists():
            return candidate
    raise RuntimeError("AGENTS.md が見つからないため、project root を特定できませんでした。")


def load_env_values(env_path: Path) -> dict[str, str]:
    if not env_path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def normalize_cookie(cookie: str) -> str:
    cookie = cookie.strip()
    if not cookie:
        raise RuntimeError("LOOM_COOKIE が空です。")
    if cookie.startswith("connect.sid="):
        return cookie
    if cookie.startswith("connect.si="):
        return "connect.sid=" + cookie[len("connect.si=") :]
    return "connect.sid=" + cookie


def discover_loom_site_packages() -> Path:
    home = Path.home()
    candidates = [
        candidate.parent.parent
        for candidate in sorted(
            home.glob(".cache/uv/archive-v0/*/lib/python3.11/site-packages/loom_mcp/client.py")
        )
    ]
    for candidate in candidates:
        if (candidate / "httpx" / "__init__.py").exists():
            return candidate

    git_candidates = sorted(
        home.glob(".cache/uv/git-v0/checkouts/*/*/src/loom_mcp/client.py")
    )
    if git_candidates:
        return git_candidates[0].parent.parent

    raise RuntimeError("loom_mcp の import path を見つけられませんでした。")


def load_loom_client():
    sys.path.insert(0, str(discover_loom_site_packages()))
    from loom_mcp.client import LoomClient

    return LoomClient


async def search_videos(queries: list[str], limit: int) -> list[dict]:
    project_root = find_project_root()
    env_values = load_env_values(project_root / ".env")
    cookie = normalize_cookie(env_values.get("LOOM_COOKIE", ""))
    LoomClient = load_loom_client()

    client = LoomClient(cookies=cookie)
    try:
        results: list[dict] = []
        for query in queries:
            payload = await client.search_videos(query, limit=limit)
            results.append(
                {
                    "query": query,
                    "videos": payload.get("videos", []),
                    "endCursor": payload.get("endCursor"),
                    "hasNextPage": payload.get("hasNextPage"),
                }
            )
        return results
    finally:
        await client.aclose()


async def fetch_video(video_id: str) -> dict:
    project_root = find_project_root()
    env_values = load_env_values(project_root / ".env")
    cookie = normalize_cookie(env_values.get("LOOM_COOKIE", ""))
    LoomClient = load_loom_client()

    client = LoomClient(cookies=cookie)
    try:
        video = await client.get_video(video_id)
        transcript = await client.get_transcript_text(video_id)
        return {"video": video, "transcript": transcript}
    finally:
        await client.aclose()


def cmd_search(args: argparse.Namespace) -> int:
    results = asyncio.run(search_videos(args.query, args.limit))
    if args.format == "json":
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 0

    for result in results:
        print(f"QUERY={result['query']}")
        for video in result["videos"]:
            print(
                f"{video.get('id')}\t{video.get('createdAt')}\t"
                f"{video.get('playable_duration')}\t{video.get('name')}"
            )
        print("---")
    return 0


def cmd_fetch(args: argparse.Namespace) -> int:
    payload = asyncio.run(fetch_video(args.video_id))
    if args.save_dir:
        save_dir = Path(args.save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        (save_dir / "metadata.json").write_text(
            json.dumps(payload["video"], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (save_dir / "transcript.txt").write_text(
            payload["transcript"] or "",
            encoding="utf-8",
        )

    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("VIDEO_JSON_START")
    print(json.dumps(payload["video"], ensure_ascii=False, indent=2))
    print("VIDEO_JSON_END")
    print("TRANSCRIPT_START")
    print(payload["transcript"] or "")
    print("TRANSCRIPT_END")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=".env の LOOM_COOKIE を使って Loom を検索・取得する補助スクリプト"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    search_parser = subparsers.add_parser("search", help="候補検索")
    search_parser.add_argument("--query", action="append", required=True)
    search_parser.add_argument("--limit", type=int, default=20)
    search_parser.add_argument("--format", choices=("text", "json"), default="text")
    search_parser.set_defaults(func=cmd_search)

    fetch_parser = subparsers.add_parser("fetch", help="動画詳細と transcript 取得")
    fetch_parser.add_argument("--video-id", required=True)
    fetch_parser.add_argument("--save-dir")
    fetch_parser.add_argument("--format", choices=("text", "json"), default="text")
    fetch_parser.set_defaults(func=cmd_fetch)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
