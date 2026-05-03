# X投稿自動化のランタイム成果物を repo 外に保存する補助モジュール。
# 画像プロンプト、下書きメタデータ、処理済みブックマーク state を一元管理する。
# 保存先は ~/.config/team-info/x-post-writer/ 配下。

from __future__ import annotations

import json
import os
import re
from pathlib import Path


APP_NAME = "team-info"
FEATURE_DIR = "x-post-writer"
BOOKMARK_STATE_FILENAME = "processed_bookmarks_state.json"


def get_config_root() -> Path:
    base = Path(
        os.environ.get(
            "XDG_CONFIG_HOME",
            str(Path.home() / ".config"),
        )
    )
    return base / APP_NAME / FEATURE_DIR


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_runtime_root() -> Path:
    return ensure_dir(get_config_root())


def get_logs_dir() -> Path:
    return ensure_dir(get_runtime_root() / "logs")


def get_image_prompts_dir() -> Path:
    return ensure_dir(get_runtime_root() / "image-prompts")


def get_draft_metadata_dir() -> Path:
    return ensure_dir(get_runtime_root() / "draft-metadata")


def get_bookmark_state_path() -> Path:
    return get_runtime_root() / BOOKMARK_STATE_FILENAME


def slugify(text: str, fallback: str = "draft") -> str:
    normalized = re.sub(r"[^0-9A-Za-z_-]+", "-", text.strip())
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-_")
    return normalized or fallback


def write_image_prompt_file(
    *,
    draft_id: str,
    position: int,
    copy_text: str,
    prompt_text: str,
    source_tweet_id: str,
) -> Path:
    filename = f"{draft_id}-p{position}-{slugify(source_tweet_id, 'source')}.md"
    path = get_image_prompts_dir() / filename
    body = (
        f"# Image Prompt for Draft {draft_id} / Part {position}\n\n"
        f"- source_tweet_id: {source_tweet_id}\n"
        f"- copy: {copy_text}\n\n"
        "## Prompt\n\n"
        f"{prompt_text.strip()}\n"
    )
    path.write_text(body, encoding="utf-8")
    return path


def get_draft_metadata_path(draft_id: str) -> Path:
    return get_draft_metadata_dir() / f"{draft_id}.json"


def save_draft_metadata(draft_id: str, payload: dict) -> Path:
    path = get_draft_metadata_path(draft_id)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def load_draft_metadata(draft_id: str) -> dict | None:
    path = get_draft_metadata_path(draft_id)
    if not path.exists():
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def load_processed_bookmarks() -> set[str]:
    path = get_bookmark_state_path()
    if not path.exists():
        return set()

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()

    items = payload.get("processed_tweet_ids", [])
    if not isinstance(items, list):
        return set()
    return {str(item) for item in items if str(item).strip()}


def save_processed_bookmarks(tweet_ids: set[str]) -> Path:
    path = get_bookmark_state_path()
    payload = {"processed_tweet_ids": sorted(tweet_ids)}
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path
