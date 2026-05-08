# Neon DBから下書きデータを取得してブラウザプレビューに渡すローカルAPIサーバー。
# Discord通知・localtunnelによる公開URLも管理する。
# 起動: bash start_preview.sh（推奨）または python preview_server.py

import json
import base64
import hashlib
import hmac
import html
import mimetypes
import os
import queue
import re
import secrets
import shlex
import select
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs, quote as urlquote, urlencode
from http.cookies import SimpleCookie
import psycopg2
from psycopg2.extras import RealDictCursor
from runtime_store import (
    get_runtime_root,
    load_character_setting,
    load_draft_metadata,
    save_character_setting,
    save_draft_metadata,
    slugify,
)
from draft_manager import update_draft_image

PORT = 8765
PREVIEW_DIR   = Path(__file__).parent / "preview"
BOOKMARKS_FILE = Path(__file__).parent / "bookmarks_latest.json"
REPO_ROOT = Path(__file__).resolve().parents[4]
ENV_PATH = REPO_ROOT / ".env"
ACCOUNTS_CONFIG_PATH = Path(__file__).parent / "accounts_config.json"
LOGO_PRESETS_PATH = Path(__file__).parent / "logo_presets.json"
ENV_SETTINGS_ALLOWED_EXACT = {"DISCORD_WEBHOOK_X_DRAFT", "NEON_DATABASE_URL"}
ENV_SETTINGS_ALLOWED_PREFIXES = ("X_", "NEON_")
AUTH_SESSION_COOKIE = "x_draft_session"
AUTH_STATE_COOKIE = "x_draft_oauth_state"
GOOGLE_OAUTH_SCOPES = "openid email profile"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"


def esc_html(value: str) -> str:
    return html.escape(str(value or ""), quote=True)


def parse_env_file(path: Path = ENV_PATH) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    pattern = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$")
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(raw_line)
        if not match:
            continue
        key, raw_value = match.groups()
        raw_value = raw_value.strip()
        try:
            parts = shlex.split(raw_value, comments=True, posix=True)
            value = parts[0] if parts else ""
        except ValueError:
            value = raw_value.strip("\"'")
        values[key] = value
    return values


def load_repo_env() -> dict[str, str]:
    values = parse_env_file()
    for key, value in values.items():
        os.environ.setdefault(key, value)
    return values


load_repo_env()

PUBLIC_URL = os.environ.get("LT_PUBLIC_URL", f"http://localhost:{PORT}")
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_X_DRAFT", "")
LOCAL_IMAGE_ROOTS = [
    Path(os.environ.get("TEAM_INFO_ROOT", Path.cwd())) / "personal",
    Path.home() / ".codex" / "generated_images",
]
OBSIDIAN_VAULT_ENV_KEYS = ("X_POST_OBSIDIAN_VAULT", "OBSIDIAN_VAULT_PATH")

# oauth2_setup.py からのコールバックを一時保存する（プロセス内共有）
_oauth2_pending: dict = {}
_image_generation_jobs: dict[str, dict] = {}
_image_generation_lock = threading.Lock()
_auto_post_jobs: dict[str, dict] = {}
_auto_post_lock = threading.Lock()
IMAGEGEN_SKILL_PATH = Path.home() / ".codex" / "skills" / ".system" / "imagegen" / "SKILL.md"
DEFAULT_CHARACTER_TRAITS = (
    "半目、眠そうな表情、舌を少し出す、頬杖、黒い短髪、黒いスーツ、"
    "白シャツ、赤ネクタイ、気だるい表情"
)
DEFAULT_CHARACTER_NEGATIVE = "明るい丸目の少年、パーカー、元気な笑顔、指差しポーズ"


def get_db_conn():
    url = os.environ.get("NEON_DATABASE_URL")
    if not url:
        print("❌ NEON_DATABASE_URL が設定されていません", file=sys.stderr)
        sys.exit(1)
    return psycopg2.connect(url)


def auth_enabled() -> bool:
    return bool(os.environ.get("GOOGLE_OAUTH_CLIENT_ID") and os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET"))


def session_secret() -> str:
    return os.environ.get("SESSION_SECRET") or os.environ.get("APP_ENCRYPTION_KEY") or "x-draft-local-dev-session"


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def sign_session_payload(payload: dict) -> str:
    body = b64url(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    sig = hmac.new(session_secret().encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest()
    return f"{body}.{b64url(sig)}"


def verify_session_token(token: str) -> dict | None:
    if not token or "." not in token:
        return None
    body, sig = token.rsplit(".", 1)
    expected = b64url(hmac.new(session_secret().encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest())
    if not hmac.compare_digest(sig, expected):
        return None
    try:
        padded = body + "=" * (-len(body) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8"))
    except (ValueError, json.JSONDecodeError):
        return None
    if int(payload.get("exp") or 0) < int(time.time()):
        return None
    return payload if isinstance(payload, dict) else None


def parse_cookies(header: str) -> dict[str, str]:
    cookie = SimpleCookie()
    cookie.load(header or "")
    return {key: morsel.value for key, morsel in cookie.items()}


def ensure_multi_user_schema() -> None:
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS app_users (
                    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    google_sub TEXT UNIQUE,
                    email TEXT,
                    display_name TEXT,
                    picture_url TEXT,
                    role TEXT NOT NULL DEFAULT 'user',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id UUID NOT NULL REFERENCES app_users(user_id) ON DELETE CASCADE,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL DEFAULT '',
                    is_secret BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    PRIMARY KEY (user_id, key)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS global_logo_presets (
                    logo_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name TEXT NOT NULL UNIQUE,
                    aliases JSONB NOT NULL DEFAULT '[]'::jsonb,
                    image_url TEXT NOT NULL DEFAULT '',
                    image_path TEXT NOT NULL DEFAULT '',
                    source_url TEXT NOT NULL DEFAULT '',
                    usage_note TEXT NOT NULL DEFAULT '',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_logo_presets (
                    logo_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES app_users(user_id) ON DELETE CASCADE,
                    name TEXT NOT NULL,
                    aliases JSONB NOT NULL DEFAULT '[]'::jsonb,
                    image_url TEXT NOT NULL DEFAULT '',
                    image_path TEXT NOT NULL DEFAULT '',
                    source_url TEXT NOT NULL DEFAULT '',
                    usage_note TEXT NOT NULL DEFAULT '',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE (user_id, name)
                )
            """)
            for table in ("accounts", "drafts"):
                cur.execute(
                    """
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name = %s AND column_name = 'owner_user_id'
                    """,
                    (table,),
                )
                if not cur.fetchone():
                    cur.execute(f"ALTER TABLE {table} ADD COLUMN owner_user_id UUID NULL REFERENCES app_users(user_id) ON DELETE SET NULL")
            conn.commit()
    finally:
        conn.close()


def upsert_app_user(profile: dict) -> dict:
    google_sub = str(profile.get("sub") or "").strip()
    if not google_sub:
        raise ValueError("Google profile に sub がありません")
    conn = get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                INSERT INTO app_users (google_sub, email, display_name, picture_url)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (google_sub) DO UPDATE
                   SET email = EXCLUDED.email,
                       display_name = EXCLUDED.display_name,
                       picture_url = EXCLUDED.picture_url,
                       updated_at = NOW()
                RETURNING user_id, google_sub, email, display_name, picture_url, role
            """, (
                google_sub,
                profile.get("email") or "",
                profile.get("name") or profile.get("email") or "",
                profile.get("picture") or "",
            ))
            user = dict(cur.fetchone())
            conn.commit()
            return {**user, "user_id": str(user["user_id"])}
    finally:
        conn.close()


def get_app_user(user_id: str) -> dict | None:
    if not user_id:
        return None
    conn = get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT user_id, google_sub, email, display_name, picture_url, role
                FROM app_users
                WHERE user_id = %s
            """, (user_id,))
            row = cur.fetchone()
            return {**dict(row), "user_id": str(row["user_id"])} if row else None
    finally:
        conn.close()


def get_user_setting(user_id: str | None, key: str) -> str | None:
    if not user_id:
        return None
    conn = get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT value FROM user_settings WHERE user_id = %s AND key = %s", (user_id, key))
            row = cur.fetchone()
            return row["value"] if row else None
    finally:
        conn.close()


def save_user_settings(user_id: str, updates: dict[str, str]) -> dict:
    if not user_id:
        raise ValueError("ログインユーザーが必要です")
    invalid_keys = sorted(
        str(key).strip()
        for key in updates
        if not is_editable_env_key(str(key).strip())
    )
    if invalid_keys:
        raise ValueError("保存できない設定キーです: " + ", ".join(invalid_keys))

    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            for key, value in updates.items():
                clean_key = str(key).strip()
                if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", clean_key):
                    continue
                cur.execute("""
                    INSERT INTO user_settings (user_id, key, value, is_secret)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (user_id, key) DO UPDATE
                       SET value = EXCLUDED.value,
                           is_secret = EXCLUDED.is_secret,
                           updated_at = NOW()
                """, (user_id, clean_key, str(value), is_sensitive_env_key(clean_key)))
            conn.commit()
    finally:
        conn.close()
    return {"updated_keys": sorted(str(k).strip() for k in updates)}


def fetch_drafts(account: str = "", *, limit: int = 20, offset: int = 0, query: str = ""):
    limit = max(1, min(int(limit or 20), 100))
    offset = max(0, int(offset or 0))
    conn = get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            where_parts = []
            params: list[str] = []
            if account:
                where_parts.append("lower(a.x_username) = lower(%s)")
                params.append(account)
            if query:
                like = f"%{query.lower()}%"
                where_parts.append("""
                    (
                        lower(COALESCE(a.display_name, '')) LIKE %s
                        OR lower(COALESCE(a.x_username, '')) LIKE %s
                        OR lower(COALESCE(d.memo, '')) LIKE %s
                        OR EXISTS (
                            SELECT 1 FROM draft_parts sp
                            WHERE sp.draft_id = d.draft_id
                              AND lower(COALESCE(sp.content, '')) LIKE %s
                        )
                    )
                """)
                params.extend([like, like, like, like])
            where = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""

            cur.execute(f"""
                SELECT COUNT(*) AS total
                FROM drafts d
                JOIN accounts a ON d.account_id = a.account_id
                {where}
            """, tuple(params))
            total = int(cur.fetchone()["total"] or 0)

            cur.execute(f"""
                SELECT d.draft_id, a.x_username, a.display_name,
                       a.profile_image_url,
                       d.status, d.memo, d.created_at, d.published_at,
                       (
                           SELECT COUNT(*)
                           FROM draft_parts p
                           WHERE p.draft_id = d.draft_id
                       ) AS part_count,
                       (
                           SELECT p.content
                           FROM draft_parts p
                           WHERE p.draft_id = d.draft_id
                           ORDER BY p.position
                           LIMIT 1
                       ) AS preview_content,
                       EXISTS (
                           SELECT 1
                           FROM draft_parts p
                           WHERE p.draft_id = d.draft_id
                             AND COALESCE(p.image_url, '') <> ''
                       ) AS has_image
                FROM drafts d
                JOIN accounts a ON d.account_id = a.account_id
                {where}
                ORDER BY d.created_at DESC
                LIMIT %s OFFSET %s
            """, tuple([*params, limit, offset]))
            drafts = cur.fetchall()
            result = []
            for draft in drafts:
                result.append({
                    "draft_id": str(draft["draft_id"]),
                    "x_username": draft["x_username"],
                    "display_name": draft["display_name"] or draft["x_username"],
                    "profile_image_url": draft["profile_image_url"] or "",
                    "memo": draft["memo"] or "",
                    "status": draft["status"] or "draft",
                    "has_image": bool(draft["has_image"]),
                    "part_count": int(draft["part_count"] or 0),
                    "preview_content": draft["preview_content"] or "",
                    "created_at": draft["created_at"].strftime("%Y-%m-%d %H:%M"),
                    "published_at": draft["published_at"].strftime("%Y-%m-%d %H:%M") if draft["published_at"] else None,
                })
            return {
                "items": result,
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": offset + len(result) < total,
            }
    finally:
        conn.close()


def load_accounts_config() -> list[dict]:
    if not ACCOUNTS_CONFIG_PATH.exists():
        return []
    try:
        payload = json.loads(ACCOUNTS_CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    accounts = payload.get("accounts") if isinstance(payload, dict) else []
    return accounts if isinstance(accounts, list) else []


def fetch_accounts() -> list[dict]:
    presets: dict[str, dict] = {}
    for item in load_accounts_config():
        if not isinstance(item, dict):
            continue
        username = str(item.get("x_username") or "").strip()
        account_id = str(item.get("id") or username or "").strip()
        if not account_id and not username:
            continue
        key = username.lower() or account_id.lower()
        presets[key] = {
            "id": account_id,
            "x_username": username,
            "display_name": item.get("display_name") or username or account_id,
            "profile_image_url": item.get("profile_image_url") or "",
            "token_env": item.get("token_env") or "",
            "token_secret_env": item.get("token_secret_env") or "",
            "draft_count": 0,
        }

    try:
        conn = get_db_conn()
    except SystemExit:
        return list(presets.values())
    except Exception:
        return list(presets.values())

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT a.account_id, a.x_username, a.display_name, a.profile_image_url,
                       COUNT(d.draft_id) AS draft_count
                FROM accounts a
                LEFT JOIN drafts d ON d.account_id = a.account_id
                GROUP BY a.account_id, a.x_username, a.display_name, a.profile_image_url
                ORDER BY a.x_username
            """)
            for row in cur.fetchall():
                username = row["x_username"] or ""
                key = username.lower() or str(row["account_id"]).lower()
                preset = presets.get(key, {})
                preset.update({
                    "id": preset.get("id") or str(row["account_id"]),
                    "x_username": username,
                    "display_name": row["display_name"] or username,
                    "profile_image_url": row["profile_image_url"] or preset.get("profile_image_url") or "",
                    "draft_count": int(row["draft_count"] or 0),
                    "token_env": preset.get("token_env") or "",
                    "token_secret_env": preset.get("token_secret_env") or "",
                })
                presets[key] = preset
    finally:
        conn.close()

    return sorted(presets.values(), key=lambda item: (item.get("x_username") or item.get("id") or "").lower())


def _load_original_tweet(draft_id: str, seen: set[str] | None = None) -> dict | None:
    """draft-metadata と bookmarks_latest.json から元ツイート（スレッド含む）を返す。"""
    seen = seen or set()
    draft_id = str(draft_id)
    if draft_id in seen:
        return None
    seen.add(draft_id)

    metadata = load_draft_metadata(draft_id)
    if not metadata:
        return None
    tweet_id = str(metadata.get("bookmark_tweet_id") or "")
    author   = metadata.get("author_username") or ""
    if not tweet_id:
        return None

    if tweet_id.startswith("draft-"):
        source_draft_id = tweet_id.removeprefix("draft-")
        source_original = _load_original_tweet(source_draft_id, seen)
        if source_original:
            source_original["rewritten_from_draft_id"] = source_draft_id
            return source_original

    if BOOKMARKS_FILE.exists():
        try:
            data      = json.loads(BOOKMARKS_FILE.read_text(encoding="utf-8"))
            bookmarks = data.get("bookmarks", [])
            for bm in bookmarks:
                if str(bm.get("tweet_id")) == tweet_id:
                    username     = bm.get("author_username") or author
                    raw_parts    = bm.get("thread_parts") or []
                    # 各パーツに author_username を付与してフロントでURL生成できるようにする
                    thread_parts = [
                        {**p, "author_username": username,
                         "tweet_url": f"https://x.com/{username}/status/{p['tweet_id']}"}
                        for p in raw_parts
                    ]
                    text_raw = bm.get("text") or ""
                    raw_urls = re.findall(r'https?://\S+', text_raw)
                    urls = [re.sub(r'[.,);]+$', '', u) for u in raw_urls]
                    return {
                        "tweet_id":        tweet_id,
                        "tweet_url":       f"https://x.com/{username}/status/{tweet_id}",
                        "text":            text_raw,
                        "author_username": username,
                        "author_name":     bm.get("author_name") or "",
                        "thread_parts":    thread_parts,
                        "media":           bm.get("media") or [],
                        "urls":            urls,
                    }
        except Exception:
            pass
    # bookmarks_latest にないときは tweet_id と author だけ返す
    tweet_url = f"https://x.com/{author}/status/{tweet_id}" if author else ""
    return {
        "tweet_id":        tweet_id,
        "tweet_url":       tweet_url,
        "text":            None,
        "author_username": author,
        "author_name":     "",
        "thread_parts":    [],
    }


def fetch_draft(draft_id):
    conn = get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT d.draft_id, a.x_username, a.display_name,
                       a.profile_image_url,
                       d.status, d.memo, d.created_at, d.published_at
                FROM drafts d
                JOIN accounts a ON d.account_id = a.account_id
                WHERE d.draft_id = %s
            """, (draft_id,))
            draft = cur.fetchone()
            if not draft:
                return None
            cur.execute("""
                SELECT part_id, position, content, image_url
                FROM draft_parts WHERE draft_id = %s ORDER BY position
            """, (draft_id,))
            parts = cur.fetchall()
            metadata      = load_draft_metadata(str(draft["draft_id"])) or {}
            image_prompts = metadata.get("image_prompts") or []
            account_key = draft["x_username"] or str(draft["draft_id"])
            character_setting = merged_character_setting(account_key, draft["profile_image_url"] or "")
            has_image     = any((p["image_url"] or "").strip() for p in parts)
            return {
                "draft_id": str(draft["draft_id"]),
                "x_username": draft["x_username"],
                "display_name": draft["display_name"] or draft["x_username"],
                "profile_image_url": draft["profile_image_url"] or "",
                "memo": draft["memo"] or "",
                "status": draft["status"] or "draft",
                "has_image": has_image,
                "created_at": draft["created_at"].strftime("%Y-%m-%d %H:%M"),
                "published_at": draft["published_at"].strftime("%Y-%m-%d %H:%M") if draft["published_at"] else None,
                "parts": [
                    {
                        "part_id": str(p["part_id"]),
                        "position": p["position"],
                        "content": p["content"],
                        "image_url": p["image_url"],
                    }
                    for p in parts
                ],
                "image_prompts": image_prompts,
                "character_reference": metadata.get("character_reference") or {},
                "character_setting": character_setting,
                "original_tweet": _load_original_tweet(str(draft["draft_id"])),
            }
    finally:
        conn.close()


def delete_draft(draft_id):
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM draft_parts WHERE draft_id = %s", (draft_id,))
            cur.execute("DELETE FROM drafts WHERE draft_id = %s", (draft_id,))
            conn.commit()
            return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def add_draft_part(draft_id, content):
    conn = get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT COALESCE(MAX(position), 0) AS max_pos FROM draft_parts WHERE draft_id = %s",
                (draft_id,),
            )
            next_pos = cur.fetchone()["max_pos"] + 1
            cur.execute(
                "INSERT INTO draft_parts (draft_id, position, content) VALUES (%s, %s, %s)",
                (draft_id, next_pos, content),
            )
            conn.commit()
            return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_part_content(part_id, content):
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE draft_parts SET content = %s WHERE part_id = %s",
                (content, part_id),
            )
            conn.commit()
            return cur.rowcount > 0
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_draft_status(draft_id, status):
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            if status == "published":
                cur.execute(
                    "UPDATE drafts SET status = %s, published_at = NOW() WHERE draft_id = %s",
                    (status, draft_id),
                )
            else:
                cur.execute(
                    "UPDATE drafts SET status = %s, published_at = NULL WHERE draft_id = %s",
                    (status, draft_id),
                )
            conn.commit()
            return cur.rowcount > 0
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _git_account_slug() -> str:
    try:
        proc = subprocess.run(
            ["git", "config", "user.name"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            timeout=3,
            check=False,
        )
        raw = proc.stdout.strip()
    except Exception:
        raw = ""
    normalized = re.sub(r"[^0-9A-Za-z]+", "", raw.lower())
    if normalized:
        return normalized

    personal_root = REPO_ROOT / "personal"
    if personal_root.exists():
        accounts = [p.name for p in personal_root.iterdir() if p.is_dir()]
        if len(accounts) == 1:
            return accounts[0]
    return "deguchishouma"


def get_obsidian_vault_path() -> Path:
    for key in OBSIDIAN_VAULT_ENV_KEYS:
        value = os.environ.get(key, "").strip()
        if value:
            return Path(value).expanduser()
    return REPO_ROOT / "personal" / _git_account_slug() / "obsidian" / "claude-obsidian"


def _yaml_quote(value: str) -> str:
    return '"' + str(value or "").replace("\\", "\\\\").replace('"', '\\"') + '"'


def _markdown_list(items: list[str]) -> str:
    clean_items = [str(item).strip() for item in items if str(item).strip()]
    if not clean_items:
        return "- なし"
    return "\n".join(f"- {item}" for item in clean_items)


def _draft_markdown_parts(parts: list[dict]) -> str:
    lines: list[str] = []
    for part in parts:
        position = part.get("position") or len(lines) + 1
        content = str(part.get("content") or "").strip()
        image_url = str(part.get("image_url") or "").strip()
        lines.append(f"### Part {position}\n\n{content or '(空)'}")
        if image_url:
            lines.append(f"\n画像: {image_url}")
    return "\n\n".join(lines) if lines else "(下書き本文なし)"


def _original_markdown(original: dict | None) -> str:
    if not original:
        return "元投稿情報なし"
    lines = [
        f"- author: @{original.get('author_username') or ''}",
        f"- url: {original.get('tweet_url') or ''}",
    ]
    if original.get("rewritten_from_draft_id"):
        lines.append(f"- rewritten_from_draft_id: {original['rewritten_from_draft_id']}")
    thread_parts = original.get("thread_parts") or []
    if thread_parts:
        lines.append("\n### 元投稿スレッド")
        for part in thread_parts:
            text = str(part.get("text") or "").strip()
            url = str(part.get("tweet_url") or "").strip()
            lines.append(f"\n#### {url}\n\n{text or '(本文なし)'}")
    else:
        lines.append("\n### 元投稿本文\n")
        lines.append(str(original.get("text") or "").strip() or "(本文なし)")
    urls = original.get("urls") or []
    if urls:
        lines.append("\n### 外部リンク\n")
        lines.append(_markdown_list(urls))
    return "\n".join(lines)


def save_draft_to_obsidian(draft_id: str) -> dict:
    draft = fetch_draft(draft_id)
    if not draft:
        raise ValueError("下書きが見つかりません")

    vault = get_obsidian_vault_path()
    if not vault.exists():
        raise FileNotFoundError(f"Obsidian vault が見つかりません: {vault}")

    created_date = str(draft.get("created_at") or datetime.now().strftime("%Y-%m-%d")).split(" ")[0]
    first_text = draft.get("parts", [{}])[0].get("content", "")
    title_seed = draft.get("memo") or first_text[:36] or draft_id
    filename = f"{created_date}-x-{slugify(title_seed, str(draft_id))[:64]}.md"
    note_dir = vault / "wiki" / "sources" / "x-posts"
    note_dir.mkdir(parents=True, exist_ok=True)
    note_path = note_dir / filename

    original = draft.get("original_tweet") or {}
    source_url = original.get("tweet_url") or ""
    draft_url = f"{PUBLIC_URL}?draft={draft_id}"
    account_link = f"[[X/@{draft.get('x_username') or 'unknown'}]]"
    source_account = original.get("author_username")
    source_link = f"[[X/@{source_account}]]" if source_account else ""
    image_prompts = draft.get("image_prompts") or []

    body = f"""---
type: x-post-knowledge
source: x-draft-preview
draft_id: {_yaml_quote(str(draft_id))}
x_username: {_yaml_quote(draft.get("x_username") or "")}
status: {_yaml_quote(draft.get("status") or "")}
created_at: {_yaml_quote(draft.get("created_at") or "")}
source_url: {_yaml_quote(source_url)}
tags:
  - x-post
  - knowledge-seed
  - x-draft
---

# X投稿ナレッジ: {draft.get("memo") or first_text[:48] or draft_id}

関連: [[X投稿]] [[投稿テンプレート]] {account_link}{(" " + source_link) if source_link else ""}

## なぜ保存したか

- GUIから保存したナレッジ候補。後で「刺さった理由」「使える型」「自分の言葉への変換」を追記する。

## 下書き

- account: @{draft.get("x_username") or ""}
- preview: {draft_url}
- status: {draft.get("status") or ""}

{_draft_markdown_parts(draft.get("parts") or [])}

## 元投稿

{_original_markdown(original)}

## 抽出したい型

- フック:
- 展開:
- 感情:
- CTA:
- 自分の投稿へ転用する時の注意:
"""

    if image_prompts:
        body += "\n## 画像プロンプト\n\n"
        for idx, prompt in enumerate(image_prompts, 1):
            body += f"### Prompt {idx}\n\n"
            if prompt.get("copy"):
                body += f"- copy: {prompt.get('copy')}\n\n"
            body += f"```text\n{prompt.get('prompt') or ''}\n```\n\n"

    if note_path.exists():
        existing = note_path.read_text(encoding="utf-8")
        if f"draft_id: {_yaml_quote(str(draft_id))}" in existing:
            note_path.write_text(body, encoding="utf-8")
        else:
            timestamp = datetime.now().strftime("%H%M%S")
            note_path = note_dir / f"{note_path.stem}-{timestamp}.md"
            note_path.write_text(body, encoding="utf-8")
    else:
        note_path.write_text(body, encoding="utf-8")

    relative = note_path.relative_to(vault)
    obsidian_url = (
        "obsidian://open?"
        f"vault={urlquote(vault.name, safe='')}&file={urlquote(relative.as_posix(), safe='')}"
    )
    return {
        "path": str(note_path),
        "vault": str(vault),
        "relative_path": relative.as_posix(),
        "obsidian_url": obsidian_url,
    }


def update_image_prompt_metadata(draft_id: str, prompt: str, copy_text: str = "") -> dict:
    metadata = load_draft_metadata(str(draft_id)) or {}
    prompts = metadata.get("image_prompts")
    if not isinstance(prompts, list) or not prompts:
        prompts = [{"position": 1, "copy": "", "prompt": "", "file_path": ""}]
    character_reference = metadata.get("character_reference") or {}

    first = prompts[0] if isinstance(prompts[0], dict) else {}
    first["position"] = first.get("position") or 1
    first["copy"] = copy_text
    first["prompt"] = prompt
    if character_reference.get("url") and not first.get("character_reference_url"):
        first["character_reference_url"] = character_reference["url"]

    file_path = first.get("file_path")
    if file_path:
        path = Path(file_path)
        try:
            body = (
                f"# Image Prompt for Draft {draft_id} / Part {first['position']}\n\n"
                f"- copy: {copy_text}\n\n"
                "## Prompt\n\n"
                f"{prompt.strip()}\n"
            )
            path.write_text(body, encoding="utf-8")
        except OSError:
            pass

    prompts[0] = first
    metadata["image_prompts"] = prompts
    save_draft_metadata(str(draft_id), metadata)
    return first


def merged_character_setting(account_key: str, fallback_url: str = "") -> dict:
    setting = load_character_setting(account_key)
    reference_url = (setting.get("reference_url") or fallback_url or "").strip()
    traits = (setting.get("traits") or DEFAULT_CHARACTER_TRAITS).strip()
    negative = (setting.get("negative") or DEFAULT_CHARACTER_NEGATIVE).strip()
    placement = (setting.get("placement") or "右下20〜25%。図解が主役、キャラクターは補助。").strip()
    return {
        "account_key": account_key,
        "reference_url": reference_url,
        "traits": traits,
        "negative": negative,
        "placement": placement,
        "updated_at": setting.get("updated_at") or "",
    }


def update_character_setting(account_key: str, payload: dict) -> dict:
    setting = {
        "account_key": account_key,
        "reference_url": (payload.get("reference_url") or "").strip(),
        "traits": (payload.get("traits") or DEFAULT_CHARACTER_TRAITS).strip(),
        "negative": (payload.get("negative") or DEFAULT_CHARACTER_NEGATIVE).strip(),
        "placement": (payload.get("placement") or "右下20〜25%。図解が主役、キャラクターは補助。").strip(),
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    save_character_setting(account_key, setting)
    return setting


def is_sensitive_env_key(key: str) -> bool:
    return any(word in key.upper() for word in ("TOKEN", "SECRET", "KEY", "PASSWORD", "COOKIE", "DATABASE_URL"))


def is_editable_env_key(key: str) -> bool:
    return key in ENV_SETTINGS_ALLOWED_EXACT or key.startswith(ENV_SETTINGS_ALLOWED_PREFIXES)


def mask_env_value(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "********"
    return f"{value[:3]}********{value[-4:]}"


def dotenv_quote(value: str) -> str:
    if value == "":
        return '""'
    if re.fullmatch(r"[A-Za-z0-9_@%+=:,./-]+", value):
        return value
    return "'" + value.replace("'", "'\"'\"'") + "'"


def list_env_settings() -> list[dict]:
    values = parse_env_file()
    keys = sorted(key for key in values.keys() if is_editable_env_key(key))
    return [
        {
            "key": key,
            "value": values.get(key, ""),
            "masked": mask_env_value(values.get(key, "")),
            "is_set": bool(values.get(key, "")),
            "sensitive": is_sensitive_env_key(key),
            "source": str(ENV_PATH),
        }
        for key in keys
    ]


def list_settings_for_user(user_id: str | None = None) -> list[dict]:
    env_values = parse_env_file()
    keys = {key for key in env_values.keys() if is_editable_env_key(key)}
    user_values: dict[str, str] = {}
    if user_id:
        conn = get_db_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT key, value FROM user_settings WHERE user_id = %s ORDER BY key", (user_id,))
                for row in cur.fetchall():
                    key = row["key"]
                    if is_editable_env_key(key):
                        user_values[key] = row["value"]
                        keys.add(key)
        finally:
            conn.close()

    return [
        {
            "key": key,
            "value": user_values.get(key, env_values.get(key, "")),
            "masked": mask_env_value(user_values.get(key, env_values.get(key, ""))),
            "is_set": bool(user_values.get(key, env_values.get(key, ""))),
            "sensitive": is_sensitive_env_key(key),
            "source": "user_settings" if key in user_values else str(ENV_PATH),
        }
        for key in sorted(keys)
    ]


def save_env_settings(updates: dict[str, str]) -> dict:
    invalid_keys = sorted(
        str(key).strip()
        for key in updates
        if not is_editable_env_key(str(key).strip())
    )
    if invalid_keys:
        raise ValueError(
            "この画面から編集できるのは X / Neon / DISCORD_WEBHOOK_X_DRAFT の環境変数だけです: "
            + ", ".join(invalid_keys)
        )

    cleaned = {
        str(key).strip(): str(value)
        for key, value in updates.items()
        if (
            re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", str(key).strip())
            and is_editable_env_key(str(key).strip())
        )
    }
    ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = ENV_PATH.read_text(encoding="utf-8").splitlines() if ENV_PATH.exists() else []
    pattern = re.compile(r"^(\s*(?:export\s+)?)([A-Za-z_][A-Za-z0-9_]*)(\s*=\s*).*$")
    seen: set[str] = set()
    next_lines: list[str] = []

    for line in lines:
        match = pattern.match(line)
        if not match:
            next_lines.append(line)
            continue
        prefix, key, sep = match.groups()
        if key not in cleaned:
            next_lines.append(line)
            continue
        next_lines.append(f"{prefix}{key}{sep}{dotenv_quote(cleaned[key])}")
        seen.add(key)

    for key in sorted(cleaned.keys() - seen):
        next_lines.append(f"{key}={dotenv_quote(cleaned[key])}")

    ENV_PATH.write_text("\n".join(next_lines).rstrip() + "\n", encoding="utf-8")
    for key, value in cleaned.items():
        os.environ[key] = value
    return {"path": str(ENV_PATH), "updated_keys": sorted(cleaned.keys())}


def rewrite_image_prompt_with_codex(
    *,
    draft_id: str,
    current_prompt: str,
    instruction: str,
    copy_text: str,
    character_reference_url: str = "",
) -> str:
    codex_path = shutil.which("codex")
    if not codex_path:
        raise RuntimeError("codex コマンドが見つかりません")

    prompt = f"""
あなたはX投稿用の縦型インフォグラフィック画像プロンプト編集者です。
APIや画像生成APIの話は一切しないでください。
現在の画像プロンプトを、ユーザー指示に従ってリライトしてください。
出力は最終的な画像プロンプト本文のみ。説明、Markdown、コードブロックは禁止。

draft_id: {draft_id}
画像コピー: {copy_text}
キャラクター参照画像URL: {character_reference_url or "なし"}

必須:
- キャラクター参照画像URLがある場合は、画像プロンプト内に「このプロフィール画像をキャラクター参照として使う」と明記する。
- 参照キャラクターの髪型・表情・服装・雰囲気を保つ。
- キャラクターは図解の右下などに20〜25%以内で入れ、主役は図解にする。
- 画像生成APIやAPIキーの説明は絶対に入れない。

[現在の画像プロンプト]
{current_prompt}

[ユーザーのリライト指示]
{instruction or "より見やすく、Xのスマホ表示で読みやすい図解に改善する"}
""".strip()

    repo_root = Path(__file__).resolve().parents[4]
    return run_codex_app_server_turn(codex_path, repo_root, prompt)


def run_codex_app_server_turn(
    codex_path: str,
    cwd: Path,
    prompt: str,
    timeout: int = 300,
    *,
    developer_instructions: str | None = None,
    sandbox_policy: dict | None = None,
    input_items: list[dict] | None = None,
    status_callback=None,
    should_stop=None,
    allow_empty_result: bool = False,
) -> str:
    """Codex App Server の JSONL プロトコルで1ターン実行し、最終テキストを返す。"""
    proc = subprocess.Popen(
        [
            codex_path,
            "app-server",
            "--listen",
            "stdio://",
        ],
        cwd=str(cwd),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    assert proc.stdin is not None
    assert proc.stdout is not None

    stderr_lines: queue.Queue[str] = queue.Queue()

    def read_stderr():
        if proc.stderr is None:
            return
        for line in proc.stderr:
            stderr_lines.put(line.rstrip())

    threading.Thread(target=read_stderr, daemon=True).start()

    next_id = 0

    def send(method: str, params: dict | None = None, *, request: bool = True) -> int | None:
        nonlocal next_id
        message = {"method": method, "params": params or {}}
        request_id = None
        if request:
            request_id = next_id
            next_id += 1
            message["id"] = request_id
        proc.stdin.write(json.dumps(message, ensure_ascii=False) + "\n")
        proc.stdin.flush()
        return request_id

    def raise_if_error(msg: dict):
        if "error" in msg:
            error = msg.get("error") or {}
            raise RuntimeError(str(error.get("message") or error)[:1000])

    try:
        initialize_id = send(
            "initialize",
            {
                "clientInfo": {
                    "name": "team_info_x_post_preview",
                    "title": "team-info X Post Preview",
                    "version": "0.1.0",
                }
            },
        )
        send("initialized", request=False)
        thread_id_request = send(
            "thread/start",
            {
                "cwd": str(cwd),
                "sandbox": "read-only",
                "approvalPolicy": "never",
                "developerInstructions": (
                    developer_instructions
                    or "あなたは短いテキスト変換だけを行う。ファイル編集、外部送信、"
                    "コマンド実行、画像生成APIの提案は禁止。"
                ),
            },
        )

        deadline = time.monotonic() + timeout
        thread_id = None
        turn_started = False
        chunks: list[str] = []
        completed_texts: list[str] = []

        while time.monotonic() < deadline:
            if should_stop and should_stop():
                return ""
            ready, _, _ = select.select([proc.stdout], [], [], 0.2)
            if not ready:
                if proc.poll() is not None:
                    break
                continue
            line = proc.stdout.readline()
            if not line:
                if proc.poll() is not None:
                    break
                time.sleep(0.05)
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue

            raise_if_error(msg)

            if msg.get("id") == initialize_id:
                continue

            if msg.get("id") == thread_id_request:
                thread = (msg.get("result") or {}).get("thread") or {}
                thread_id = thread.get("id")
                if not thread_id:
                    raise RuntimeError("Codex App Server から thread_id が返りませんでした")
                send(
                    "turn/start",
                    {
                        "threadId": thread_id,
                        "input": input_items or [{"type": "text", "text": prompt}],
                        "cwd": str(cwd),
                        "sandboxPolicy": sandbox_policy or {"type": "readOnly"},
                    },
                )
                turn_started = True
                continue

            method = msg.get("method")
            params = msg.get("params") or {}
            if method == "item/agentMessage/delta":
                chunks.append(params.get("delta") or "")
                if status_callback:
                    status_callback(method, params)
            elif method == "item/completed":
                item = params.get("item") or {}
                if item.get("type") == "agentMessage" and item.get("text"):
                    completed_texts.append(item["text"])
                if status_callback:
                    status_callback(method, params)
            elif method == "turn/completed" and turn_started:
                if status_callback:
                    status_callback(method, params)
                break
            elif status_callback and method:
                status_callback(method, params)

        else:
            raise RuntimeError("Codex App Server の応答がタイムアウトしました")

        if proc.poll() is not None and not chunks and not completed_texts:
            errors = "\n".join(list(stderr_lines.queue)[-10:])
            raise RuntimeError((errors or "Codex App Server が終了しました")[:1000])

    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

    rewritten = ("".join(chunks).strip() or "\n".join(completed_texts).strip())
    if rewritten.startswith("```"):
        rewritten = re.sub(r"^```(?:text)?\s*", "", rewritten)
        rewritten = re.sub(r"\s*```$", "", rewritten)
    if not rewritten:
        if allow_empty_result:
            return ""
        errors = "\n".join(list(stderr_lines.queue)[-10:])
        raise RuntimeError((errors or "Codex App Server からリライト結果が返りませんでした")[:1000])
    return rewritten


def attach_generated_image(draft_id: str, image_path_text: str) -> str:
    image_path = resolve_local_image(image_path_text)
    if not image_path:
        raise ValueError("画像が見つからないか、許可されていないパスです")
    image_url = f"/local-image?path={str(image_path)}"
    update_draft_image(draft_id, 1, image_url)
    return image_url


def build_image_generation_request(
    copy_text: str,
    prompt: str,
    character_reference_url: str = "",
    character_traits: str = "",
    character_negative: str = "",
    character_placement: str = "",
    feedback: str = "",
    current_image_url: str = "",
    reference_image_url: str = "",
    reference_image_path: str = "",
    logo_references: list[dict] | None = None,
) -> str:
    traits = (character_traits or DEFAULT_CHARACTER_TRAITS).strip()
    negative = (character_negative or DEFAULT_CHARACTER_NEGATIVE).strip()
    placement = (character_placement or "右下20〜25%。図解が主役、キャラクターは補助。").strip()
    lines = [
        "Codex/ChatGPTサブスク内の画像生成で、次のX投稿用図解を1枚生成してください。",
        "APIは使わないでください。",
        "添付されたプロフィール画像をキャラクター参照として使い、同じキャラクターの外見を図解内に入れてください。",
        f"参照キャラクターの重要特徴: {traits}",
        f"禁止する見た目: {negative}",
        f"キャラクター配置: {placement}",
        "",
        f"[CHARACTER REFERENCE]\n{character_reference_url or '(なし)'}",
        "",
        f"[COPY]\n{copy_text or '(なし)'}",
        "",
        f"[IMAGE PROMPT]\n{prompt}",
    ]
    if logo_references:
        lines.extend([
            "",
            "[LOGO REFERENCE IMAGES]",
            "以下のロゴは参照画像として添付済みです。ロゴを描く必要がある場合は、記憶や推測ではなく添付された参照画像の形・比率・色を優先してください。",
        ])
        for logo in logo_references:
            aliases = ", ".join(logo.get("matched_aliases") or [])
            lines.append(f"- {logo.get('name')}: {aliases}")
    if feedback or current_image_url or reference_image_url or reference_image_path:
        lines.extend([
            "",
            "[REGENERATION CONTEXT]",
            f"現在の生成画像: {current_image_url or '(なし)'}",
            f"参照画像URL: {reference_image_url or '(なし)'}",
            f"参照画像ローカルパス: {reference_image_path or '(なし)'}",
            "",
            f"[USER FEEDBACK]\n{feedback or '(なし)'}",
            "",
            "現在の生成画像の良い部分は保ちつつ、ユーザーのフィードバックと参照画像を優先して再生成してください。",
            "ロゴやマークなど参照画像がある要素は、形状・比率・色・余白を参照画像に寄せてください。",
        ])
    return "\n".join(lines)


def seed_global_logo_presets() -> None:
    if not LOGO_PRESETS_PATH.exists():
        return
    try:
        payload = json.loads(LOGO_PRESETS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    logos = payload.get("logos") if isinstance(payload, dict) else []
    if not isinstance(logos, list):
        return
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            for logo in logos:
                if not isinstance(logo, dict) or not logo.get("name"):
                    continue
                cur.execute("""
                    INSERT INTO global_logo_presets (name, aliases, image_url, image_path, source_url, usage_note)
                    VALUES (%s, %s::jsonb, %s, %s, %s, %s)
                    ON CONFLICT (name) DO UPDATE
                       SET aliases = EXCLUDED.aliases,
                           image_url = EXCLUDED.image_url,
                           image_path = EXCLUDED.image_path,
                           source_url = EXCLUDED.source_url,
                           usage_note = EXCLUDED.usage_note,
                           updated_at = NOW()
                """, (
                    logo.get("name") or "",
                    json.dumps(logo.get("aliases") or [], ensure_ascii=False),
                    logo.get("image_url") or "",
                    logo.get("image_path") or "",
                    logo.get("source_url") or "",
                    logo.get("usage_note") or "",
                ))
            conn.commit()
    finally:
        conn.close()


def load_logo_presets(user_id: str | None = None) -> list[dict]:
    presets: list[dict] = []
    try:
        conn = get_db_conn()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT name, aliases, image_url, image_path, source_url, usage_note
                FROM global_logo_presets
                ORDER BY name
            """)
            presets.extend(dict(row) for row in cur.fetchall())
            if user_id:
                cur.execute("""
                    SELECT name, aliases, image_url, image_path, source_url, usage_note
                    FROM user_logo_presets
                    WHERE user_id = %s
                    ORDER BY name
                """, (user_id,))
                presets.extend(dict(row) for row in cur.fetchall())
        conn.close()
    except Exception:
        presets = []
    for path in [LOGO_PRESETS_PATH, get_runtime_root() / "logo_presets.json"]:
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        items = payload.get("logos") if isinstance(payload, dict) else payload
        if isinstance(items, list):
            presets.extend(item for item in items if isinstance(item, dict))
    return presets


def _normalize_logo_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").lower())


def detect_logo_references(*texts: str, user_id: str | None = None) -> list[dict]:
    haystack = _normalize_logo_text("\n".join(texts))
    detected: list[dict] = []
    seen: set[str] = set()
    for preset in load_logo_presets(user_id):
        name = str(preset.get("name") or "").strip()
        aliases = [name, *preset.get("aliases", [])]
        matched = [
            str(alias).strip()
            for alias in aliases
            if str(alias).strip() and _normalize_logo_text(str(alias)) in haystack
        ]
        if not name or not matched:
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        detected.append({**preset, "matched_aliases": matched})
    return detected[:6]


def build_logo_input_item(logo: dict) -> dict | None:
    image_path = str(logo.get("image_path") or "").strip()
    if image_path:
        path = Path(image_path).expanduser()
        if not path.is_absolute():
            path = (LOGO_PRESETS_PATH.parent / path).resolve()
        if path.exists() and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
            return {"type": "local_image", "path": str(path)}

    image_url = str(logo.get("image_url") or "").strip()
    if image_url:
        parsed = urlparse(image_url)
        if parsed.scheme in {"http", "https"}:
            return {"type": "image", "url": image_url}
    return None


def resolve_any_local_image(path_text: str) -> Path | None:
    path = Path(path_text).expanduser()
    if not path.is_absolute():
        return None
    try:
        resolved = path.resolve(strict=True)
    except FileNotFoundError:
        return None
    if resolved.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
        return None
    return resolved


def build_image_input_item(image_text: str, *, allow_any_local: bool = False) -> dict | None:
    image_text = (image_text or "").strip()
    if not image_text:
        return None
    local_path = resolve_draft_image_path(image_text) or resolve_local_image(image_text)
    if not local_path and allow_any_local:
        local_path = resolve_any_local_image(image_text)
    if local_path:
        return {"type": "local_image", "path": str(local_path)}
    parsed = urlparse(image_text)
    if parsed.scheme in {"http", "https"}:
        return {"type": "image", "url": image_text}
    return None


def append_image_generation_log(job: dict, message: str, *, level: str = "info", method: str = "") -> None:
    logs = job.setdefault("logs", [])
    logs.append({
        "at": datetime.now().strftime("%H:%M:%S"),
        "level": level,
        "method": method,
        "message": message,
    })
    del logs[:-60]


def list_generated_image_paths() -> set[str]:
    paths: set[str] = set()
    for root in [Path.home() / ".codex" / "generated_images"]:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
                continue
            try:
                paths.add(str(path.resolve()))
            except OSError:
                continue
    return paths


def find_generated_image_after(started_at: float, known_paths: set[str] | None = None) -> Path | None:
    candidates: list[Path] = []
    known_paths = known_paths or set()
    for root in [Path.home() / ".codex" / "generated_images"]:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
                continue
            try:
                resolved = str(path.resolve())
                if resolved in known_paths:
                    continue
                if path.stat().st_mtime >= started_at:
                    candidates.append(path)
            except OSError:
                continue
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def copy_generated_image_to_personal(draft_id: str, source_path: Path) -> Path:
    output_dir = Path(os.environ.get("TEAM_INFO_ROOT", REPO_ROOT)) / "personal" / "deguchishouma" / "outputs" / "x-post-images"
    output_dir.mkdir(parents=True, exist_ok=True)
    dest = output_dir / f"{draft_id}-p1{source_path.suffix.lower()}"
    if source_path.resolve() != dest.resolve():
        shutil.copy2(source_path, dest)
    return dest


def complete_image_generation_from_found(job_id: str, found: Path) -> bool:
    with _image_generation_lock:
        job = _image_generation_jobs.get(job_id)
        if not job or job.get("status") in {"completed", "failed"}:
            return False
        try:
            append_image_generation_log(job, f"生成画像を検出: {found}")
            personal_path = copy_generated_image_to_personal(job["draft_id"], found)
            append_image_generation_log(job, f"画像をコピー: {personal_path}")
            image_url = attach_generated_image(job["draft_id"], str(personal_path))
            append_image_generation_log(job, "1投稿目に画像を添付しました")
            job.update({
                "status": "completed",
                "progress": 100,
                "message": "画像生成完了。プレビューに反映しました",
                "image_path": str(personal_path),
                "image_url": image_url,
            })
            return True
        except Exception as exc:
            job.update({"status": "failed", "progress": 100, "message": str(exc)[:1000]})
            append_image_generation_log(job, str(exc)[:1000], level="error")
            return False


def watch_generated_image_job(job_id: str, timeout_seconds: float = 420.0) -> None:
    while True:
        job = _image_generation_jobs.get(job_id)
        if not job or job.get("status") in {"completed", "failed"}:
            return
        elapsed = time.time() - float(job["started_at"])
        if elapsed > timeout_seconds:
            return
        known_paths = set(job.get("known_image_paths") or [])
        found = find_generated_image_after(float(job["started_at"]), known_paths)
        if found and complete_image_generation_from_found(job_id, found):
            return
        time.sleep(2.0)


def start_image_generation_job(
    draft_id: str,
    copy_text: str,
    prompt: str,
    character_reference_url: str = "",
    character_traits: str = "",
    character_negative: str = "",
    character_placement: str = "",
    feedback: str = "",
    current_image_url: str = "",
    reference_image_url: str = "",
    reference_image_path: str = "",
    user_id: str | None = None,
) -> dict:
    with _image_generation_lock:
        running = [
            job
            for job in _image_generation_jobs.values()
            if job.get("status") not in {"completed", "failed"}
        ]
        if running:
            raise RuntimeError("別の画像生成がまだ実行中です。完了してから次の画像を生成してください。")
        known_image_paths = sorted(list_generated_image_paths())

    job_id = f"{int(time.time() * 1000)}-{draft_id}"
    logo_references = detect_logo_references(copy_text, prompt, user_id=user_id)
    _image_generation_jobs[job_id] = {
        "draft_id": draft_id,
        "user_id": user_id or "",
        "started_at": time.time(),
        "known_image_paths": known_image_paths,
        "status": "starting",
        "progress": 5,
        "request": build_image_generation_request(
            copy_text,
            prompt,
            character_reference_url,
            character_traits,
            character_negative,
            character_placement,
            feedback,
            current_image_url,
            reference_image_url,
            reference_image_path,
            logo_references,
        ),
        "logo_references": logo_references,
        "image_url": "",
        "message": "Codex App Server を起動しています",
        "logs": [],
    }
    append_image_generation_log(_image_generation_jobs[job_id], "ジョブを作成しました")
    thread = threading.Thread(
        target=run_image_generation_job,
        args=(job_id, copy_text, prompt, character_reference_url, character_traits, character_negative, character_placement, feedback, current_image_url, reference_image_url, reference_image_path),
        daemon=True,
    )
    thread.start()
    watcher = threading.Thread(target=watch_generated_image_job, args=(job_id,), daemon=True)
    watcher.start()
    return {"job_id": job_id, **_image_generation_jobs[job_id]}


def run_image_generation_job(
    job_id: str,
    copy_text: str,
    prompt: str,
    character_reference_url: str = "",
    character_traits: str = "",
    character_negative: str = "",
    character_placement: str = "",
    feedback: str = "",
    current_image_url: str = "",
    reference_image_url: str = "",
    reference_image_path: str = "",
) -> None:
    job = _image_generation_jobs[job_id]
    codex_path = shutil.which("codex")
    if not codex_path:
        job.update({"status": "failed", "progress": 100, "message": "codex コマンドが見つかりません"})
        append_image_generation_log(job, "codex コマンドが見つかりません", level="error")
        return

    started_at = float(job["started_at"])
    repo_root = Path(__file__).resolve().parents[4]
    image_request = build_image_generation_request(
        copy_text,
        prompt,
        character_reference_url,
        character_traits,
        character_negative,
        character_placement,
        feedback,
        current_image_url,
        reference_image_url,
        reference_image_path,
        job.get("logo_references") or [],
    )
    task_label = "修正フィードバック付きで再生成" if feedback or current_image_url or reference_image_url or reference_image_path else "生成"
    turn_prompt = f"""
imagegen スキルを使って、以下のX投稿用図解画像を1枚生成してください。
ユーザーはAPI利用を明示していないため、画像生成API・APIキー・OPENAI_API_KEY・SDK・CLI fallbackは使わないでください。
必ず Codex/ChatGPT サブスク内の組み込み画像生成として実行してください。
生成後は説明を短く返すだけでよいです。ファイル操作は不要です。
参照画像が添付されている場合は、ユーザーのフィードバックで指定された要素を参照画像に近づけてください。

{image_request}
""".strip()

    def on_status(method: str, params: dict) -> None:
        current = _image_generation_jobs.get(job_id)
        if not current or current.get("status") in {"completed", "failed"}:
            return
        if method == "turn/started":
            current.update({"status": "generating", "progress": 18, "message": "Codex App Server の turn を開始しました"})
            append_image_generation_log(current, "turn を開始しました", method=method)
        elif method == "item/started":
            item = params.get("item") or {}
            label = item.get("type") or "処理"
            current.update({"status": "generating", "progress": max(current.get("progress", 18), 32), "message": f"{label} を実行中"})
            append_image_generation_log(current, f"{label} を開始しました", method=method)
        elif method == "item/completed":
            item = params.get("item") or {}
            label = item.get("type") or "処理"
            current.update({"status": "generating", "progress": max(current.get("progress", 32), 70), "message": "画像生成結果を確認中"})
            append_image_generation_log(current, f"{label} が完了しました", method=method)
        elif method == "turn/completed":
            append_image_generation_log(current, "turn が完了しました。生成ファイルを確認します", method=method)
        elif method:
            append_image_generation_log(current, f"event: {method}", method=method)

    try:
        job.update({"status": "generating", "progress": 12, "message": "Codex App Server に画像生成を依頼しています"})
        append_image_generation_log(job, "Codex App Server に画像生成を依頼します")
        input_items = []
        if IMAGEGEN_SKILL_PATH.exists():
            input_items.append({"type": "skill", "name": "imagegen", "path": str(IMAGEGEN_SKILL_PATH)})
            append_image_generation_log(job, f"imagegen スキルを添付: {IMAGEGEN_SKILL_PATH}")
        else:
            append_image_generation_log(job, f"imagegen スキルが見つかりません: {IMAGEGEN_SKILL_PATH}", level="warn")
        if character_reference_url:
            character_item = build_image_input_item(character_reference_url)
            if character_item:
                input_items.append(character_item)
            append_image_generation_log(job, f"キャラクター参照画像を添付: {character_reference_url}")
        for logo in job.get("logo_references") or []:
            logo_item = build_logo_input_item(logo)
            if logo_item:
                input_items.append(logo_item)
                append_image_generation_log(job, f"ロゴ参照画像を添付: {logo.get('name')}")
            else:
                append_image_generation_log(job, f"ロゴ参照画像が未設定: {logo.get('name')}", level="warn")
        current_item = build_image_input_item(current_image_url)
        if current_item:
            input_items.append(current_item)
            append_image_generation_log(job, f"現在の生成画像を添付: {current_image_url}")
        reference_text = reference_image_path or reference_image_url
        reference_item = build_image_input_item(reference_text, allow_any_local=bool(reference_image_path))
        if reference_item:
            input_items.append(reference_item)
            append_image_generation_log(job, f"修正用参照画像を添付: {reference_text}")
        input_items.append({"type": "text", "text": turn_prompt})
        run_codex_app_server_turn(
            codex_path,
            repo_root,
            turn_prompt,
            timeout=420,
            developer_instructions=(
                f"あなたは画像生成担当です。今回のタスクは{task_label}です。ユーザーがAPI利用を明示していないため、"
                "画像生成API・APIキー・OPENAI_API_KEY・SDK・CLI fallbackは使わず、"
                "利用可能な組み込み画像生成/サブスク内画像生成を使ってください。"
            ),
            sandbox_policy={"type": "readOnly", "networkAccess": False},
            input_items=input_items,
            status_callback=on_status,
            should_stop=lambda: _image_generation_jobs.get(job_id, {}).get("status") == "completed",
            allow_empty_result=True,
        )
        if job.get("status") == "completed":
            return
        found = find_generated_image_after(started_at, set(job.get("known_image_paths") or []))
        if found:
            complete_image_generation_from_found(job_id, found)
            return
        if job.get("status") != "completed":
            job.update({
                "status": "failed",
                "progress": 100,
                "message": "Codex App Server の turn は完了しましたが、生成画像ファイルを検出できませんでした",
            })
            append_image_generation_log(job, "生成画像ファイルを検出できませんでした", level="error")
    except Exception as exc:
        job.update({"status": "failed", "progress": 100, "message": str(exc)[:1000]})
        append_image_generation_log(job, str(exc)[:1000], level="error")


def get_image_generation_job(job_id: str) -> dict:
    job = _image_generation_jobs.get(job_id)
    if not job:
        raise ValueError("画像生成ジョブが見つかりません")
    if job.get("status") == "completed":
        return job
    if job.get("status") == "failed":
        return job

    elapsed = max(0.0, time.time() - float(job["started_at"]))
    found = find_generated_image_after(float(job["started_at"]), set(job.get("known_image_paths") or []))
    if found:
        complete_image_generation_from_found(job_id, found)
    else:
        if job.get("status") == "generating":
            job["progress"] = min(92, max(int(job.get("progress", 12)), 12 + int(elapsed * 1.2)))
    return job


def append_auto_post_log(job: dict, message: str, *, level: str = "info") -> None:
    logs = job.setdefault("logs", [])
    logs.append({
        "at": datetime.now().strftime("%H:%M:%S"),
        "level": level,
        "message": message,
    })
    del logs[:-30]


def run_openclaw_browser(args: list[str], *, timeout: int = 60) -> str:
    openclaw = shutil.which("openclaw")
    if not openclaw:
        raise RuntimeError("openclaw コマンドが見つかりません")
    proc = subprocess.run([openclaw, "browser", *args], capture_output=True, text=True, timeout=timeout)
    output = "\n".join(part for part in [proc.stdout.strip(), proc.stderr.strip()] if part)
    if proc.returncode != 0:
        raise RuntimeError(output or f"openclaw browser {' '.join(args)} failed")
    return output


def resolve_draft_image_path(image_url: str) -> Path | None:
    if not image_url:
        return None
    parsed = urlparse(image_url)
    if parsed.path == "/local-image" or image_url.startswith("/local-image"):
        qs = parse_qs(parsed.query)
        return resolve_local_image(qs.get("path", [""])[0])
    return resolve_local_image(image_url)


def prepare_openclaw_upload_image(draft_id: str, image_url: str) -> Path | None:
    source = resolve_draft_image_path(image_url)
    if not source:
        return None
    upload_dir = Path("/tmp/openclaw/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    dest = upload_dir / f"x-draft-{draft_id}{source.suffix.lower()}"
    shutil.copy2(source, dest)
    return dest


def build_x_auto_post_script(parts: list[str]) -> str:
    parts_json = json.dumps(parts, ensure_ascii=False)
    return f"""async () => {{
  const parts = {parts_json};
  const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));
  const isVisible = (el) => {{
    if (!el) return false;
    const rect = el.getBoundingClientRect();
    const style = window.getComputedStyle(el);
    return rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
  }};
  const enabled = (el) => el && !el.disabled && el.getAttribute('aria-disabled') !== 'true';
  const textboxes = () => Array.from(document.querySelectorAll('div[role="textbox"][contenteditable="true"]')).filter(isVisible);
  const waitFor = async (fn, label, timeout = 45000) => {{
    const start = Date.now();
    while (Date.now() - start < timeout) {{
      const value = fn();
      if (value) return value;
      await sleep(300);
    }}
    throw new Error(label + ' が見つかりません');
  }};
  const setText = async (el, text) => {{
    el.scrollIntoView({{ block: 'center' }});
    el.focus();
    await sleep(100);
    document.execCommand('selectAll', false, null);
    document.execCommand('insertText', false, text);
    el.dispatchEvent(new InputEvent('input', {{ bubbles: true, inputType: 'insertText', data: text }}));
    el.dispatchEvent(new Event('change', {{ bubbles: true }}));
    await sleep(350);
  }};
  await waitFor(() => textboxes().length > 0, '本文入力欄');
  await setText(textboxes()[0], parts[0] || '');

  for (let i = 1; i < parts.length; i++) {{
    const before = textboxes().length;
    const addButton = await waitFor(() => {{
      const candidates = Array.from(document.querySelectorAll('[data-testid="addButton"], button[aria-label*="Add"], button[aria-label*="追加"]'));
      return candidates.find(el => isVisible(el) && enabled(el));
    }}, 'ツリー追加ボタン');
    addButton.click();
    const nextBox = await waitFor(() => {{
      const boxes = textboxes();
      return boxes.length > before ? boxes[boxes.length - 1] : null;
    }}, `パート ${{i + 1}} の入力欄`);
    await setText(nextBox, parts[i] || '');
  }}

  await sleep(1200);
  const postButton = await waitFor(() => {{
    const candidates = Array.from(document.querySelectorAll('[data-testid="tweetButton"], [data-testid="tweetButtonInline"]'));
    return candidates.reverse().find(el => isVisible(el) && enabled(el));
  }}, '投稿ボタン');
  postButton.click();
  return {{ ok: true, parts: parts.length }};
}}"""


def run_auto_post_job(job_id: str) -> None:
    with _auto_post_lock:
        job = _auto_post_jobs[job_id]
        job.update({"status": "running", "progress": 8, "message": "OpenClaw ブラウザを起動しています"})
        append_auto_post_log(job, "OpenClaw ブラウザを起動します")

    try:
        draft = fetch_draft(job["draft_id"])
        if not draft:
            raise RuntimeError("下書きが見つかりません")
        parts = [str(part.get("content") or "") for part in draft.get("parts", [])]
        if not parts or not parts[0].strip():
            raise RuntimeError("投稿本文が空です")

        run_openclaw_browser(["start"], timeout=90)
        with _auto_post_lock:
            job.update({"progress": 18, "message": "X の投稿画面を開いています"})
            append_auto_post_log(job, "https://x.com/compose/post を開きます")
        run_openclaw_browser(["open", "https://x.com/compose/post"], timeout=90)

        image_url = next((part.get("image_url") for part in draft.get("parts", []) if part.get("image_url")), "")
        upload_path = prepare_openclaw_upload_image(job["draft_id"], image_url) if image_url else None
        if upload_path:
            with _auto_post_lock:
                job.update({"progress": 34, "message": "画像を投稿画面に添付しています"})
                append_auto_post_log(job, f"画像アップロードを準備: {upload_path}")
            run_openclaw_browser([
                "upload",
                "--element",
                'input[data-testid="fileInput"], input[type="file"]',
                str(upload_path),
            ], timeout=120)
        elif image_url:
            with _auto_post_lock:
                append_auto_post_log(job, "画像URLはローカルファイルに解決できないため、本文のみ自動入力します", level="warn")

        with _auto_post_lock:
            job.update({"progress": 58, "message": "本文とツリーを入力しています"})
            append_auto_post_log(job, f"{len(parts)} パーツを入力します")
        run_openclaw_browser(["evaluate", "--fn", build_x_auto_post_script(parts)], timeout=180)

        with _auto_post_lock:
            job.update({"progress": 88, "message": "投稿済みステータスを反映しています"})
            append_auto_post_log(job, "X 側の投稿ボタンをクリックしました")
        update_draft_status(job["draft_id"], "published")
        send_discord(job["draft_id"], parts[0], draft.get("x_username", ""), job.get("user_id") or None)

        with _auto_post_lock:
            job.update({"status": "completed", "progress": 100, "message": "自動投稿が完了しました"})
            append_auto_post_log(job, "自動投稿が完了しました")
    except Exception as exc:
        with _auto_post_lock:
            job.update({"status": "failed", "progress": 100, "message": str(exc)[:1000]})
            append_auto_post_log(job, str(exc)[:1000], level="error")


def start_auto_post_job(draft_id: str, user_id: str | None = None) -> dict:
    with _auto_post_lock:
        active = [
            job for job in _auto_post_jobs.values()
            if job.get("draft_id") == draft_id and job.get("status") in {"queued", "running"}
        ]
        if active:
            return dict(active[-1])
        job_id = f"{int(time.time() * 1000)}-{draft_id}"
        _auto_post_jobs[job_id] = {
            "job_id": job_id,
            "draft_id": draft_id,
            "user_id": user_id or "",
            "status": "queued",
            "progress": 2,
            "message": "自動投稿ジョブを作成しました",
            "logs": [],
        }
        append_auto_post_log(_auto_post_jobs[job_id], "ジョブを作成しました")
    threading.Thread(target=run_auto_post_job, args=(job_id,), daemon=True).start()
    return {"job_id": job_id, **_auto_post_jobs[job_id]}


def get_auto_post_job(job_id: str) -> dict:
    job = _auto_post_jobs.get(job_id)
    if not job:
        raise ValueError("ジョブが見つかりません")
    return dict(job)


def setting_value(key: str, user_id: str | None = None) -> str:
    if user_id:
        value = get_user_setting(user_id, key)
        if value is not None:
            return value
    return os.environ.get(key, "")


def send_discord(draft_id, main_content, x_username, user_id: str | None = None):
    webhook = setting_value("DISCORD_WEBHOOK_X_DRAFT", user_id)
    if not webhook:
        return False, "DISCORD_WEBHOOK_X_DRAFT が未設定"

    preview_url = f"{PUBLIC_URL}?draft={draft_id}"
    metadata = load_draft_metadata(str(draft_id)) or {}
    image_prompt_block = ""
    image_prompts = metadata.get("image_prompts") or []
    if image_prompts:
        first = image_prompts[0]
        image_prompt_block = (
            "\n\n**画像プロンプト案内:**\n"
            f"- file: {first.get('file_path', 'なし')}\n"
            f"- copy: {str(first.get('copy', ''))[:120]}\n"
            "```"
            f"\n{str(first.get('prompt', ''))[:700]}\n"
            "```"
        )

    message = {
        "content": (
            f"📝 **@{x_username}** の下書きが投稿準備されました\n\n"
            f"🔗 プレビュー: {preview_url}\n\n"
            f"**投稿内容（メイン）:**\n"
            f"```\n{main_content[:800]}\n```"
            f"{image_prompt_block}"
        )
    }

    body = json.dumps(message).encode("utf-8")
    req = urllib.request.Request(
        webhook,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            return res.status in (200, 204), None
    except Exception as e:
        return False, str(e)


def get_oembed_html(tweet_url: str) -> str | None:
    """X の oEmbed API からレンダリング用 HTML を取得する。"""
    api = f"https://publish.twitter.com/oembed?url={urlquote(tweet_url)}&omit_script=true&theme=dark&dnt=true"
    try:
        req = urllib.request.Request(api, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("html") or None
    except Exception:
        return None


def resolve_local_image(path_text: str) -> Path | None:
    """許可されたローカル画像パスだけをプレビュー配信用に解決する。"""
    if not path_text:
        return None
    path = Path(path_text).expanduser()
    if not path.is_absolute():
        return None
    try:
        resolved = path.resolve(strict=True)
    except FileNotFoundError:
        return None
    if resolved.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
        return None
    for root in LOCAL_IMAGE_ROOTS:
        try:
            resolved.relative_to(root.expanduser().resolve())
            return resolved
        except ValueError:
            continue
    return None


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def cookie_header(self, name: str, value: str, *, max_age: int = 60 * 60 * 24 * 30) -> str:
        secure = " Secure;" if (self.headers.get("X-Forwarded-Proto") or "").lower() == "https" else ""
        return f"{name}={value}; Path=/; Max-Age={max_age}; HttpOnly; SameSite=Lax;{secure}"

    def clear_cookie_header(self, name: str) -> str:
        return f"{name}=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax"

    def current_session_payload(self) -> dict | None:
        cookies = parse_cookies(self.headers.get("Cookie") or "")
        return verify_session_token(cookies.get(AUTH_SESSION_COOKIE, ""))

    def current_user(self) -> dict | None:
        payload = self.current_session_payload()
        if not payload:
            return None
        try:
            return get_app_user(str(payload.get("user_id") or ""))
        except Exception:
            return None

    def current_user_id(self) -> str | None:
        user = self.current_user()
        return user["user_id"] if user else None

    def absolute_base_url(self) -> str:
        proto = self.headers.get("X-Forwarded-Proto") or ("https" if "ngrok" in (self.headers.get("Host") or "") else "http")
        host = self.headers.get("Host") or f"localhost:{PORT}"
        return f"{proto}://{host}"

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def send_redirect(self, location: str, headers: list[tuple[str, str]] | None = None):
        self.send_response(302)
        self.send_header("Location", location)
        for key, value in headers or []:
            self.send_header(key, value)
        self.end_headers()

    def send_html(self, body: str, status=200, headers: list[tuple[str, str]] | None = None):
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(encoded))
        for key, value in headers or []:
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(encoded)

    def send_file(self, path, content_type):
        try:
            body = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()

    def read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length else {}

    def is_local_request(self):
        host = (self.headers.get("Host") or "").lower()
        return (
            host.startswith("localhost:")
            or host.startswith("127.0.0.1:")
            or host in ("localhost", "127.0.0.1", "[::1]", "[::1]:8765")
        )

    def require_local(self):
        if self.is_local_request():
            return True
        self.send_json({"ok": False, "error": "この操作は localhost からのみ使えます"}, 403)
        return False

    def require_auth(self):
        if not auth_enabled():
            self.send_json({"ok": False, "error": "Googleログイン設定が未完了です"}, 503)
            return False
        if self.current_user():
            return True
        self.send_json({"ok": False, "error": "ログインが必要です"}, 401)
        return False

    def is_public_api_path(self, path: str) -> bool:
        return path in ("/api/auth/me", "/api/public-url")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, PATCH, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def start_google_login(self):
        if not auth_enabled():
            self.send_html("<html><body><h2>Google OAuth が未設定です</h2></body></html>", 400)
            return
        state = secrets.token_urlsafe(24)
        redirect_uri = f"{self.absolute_base_url()}/auth/google/callback"
        params = {
            "client_id": os.environ["GOOGLE_OAUTH_CLIENT_ID"],
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": GOOGLE_OAUTH_SCOPES,
            "state": state,
            "access_type": "offline",
            "include_granted_scopes": "true",
            "prompt": "select_account",
        }
        self.send_redirect(
            "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params),
            headers=[("Set-Cookie", self.cookie_header(AUTH_STATE_COOKIE, state, max_age=600))],
        )

    def finish_google_login(self, qs: dict):
        if not auth_enabled():
            self.send_html("<html><body><h2>Google OAuth が未設定です</h2></body></html>", 400)
            return
        cookies = parse_cookies(self.headers.get("Cookie") or "")
        expected_state = cookies.get(AUTH_STATE_COOKIE, "")
        state = qs.get("state", [""])[0]
        code = qs.get("code", [""])[0]
        if not code or not expected_state or not hmac.compare_digest(state, expected_state):
            self.send_html("<html><body><h2>認証 state が一致しません</h2></body></html>", 400)
            return

        redirect_uri = f"{self.absolute_base_url()}/auth/google/callback"
        token_body = urlencode({
            "code": code,
            "client_id": os.environ["GOOGLE_OAUTH_CLIENT_ID"],
            "client_secret": os.environ["GOOGLE_OAUTH_CLIENT_SECRET"],
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }).encode("utf-8")
        try:
            token_req = urllib.request.Request(
                GOOGLE_TOKEN_URL,
                data=token_body,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                method="POST",
            )
            with urllib.request.urlopen(token_req, timeout=10) as resp:
                token_payload = json.loads(resp.read().decode("utf-8"))
            access_token = token_payload.get("access_token")
            if not access_token:
                raise RuntimeError("access_token が返りませんでした")
            user_req = urllib.request.Request(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            with urllib.request.urlopen(user_req, timeout=10) as resp:
                profile = json.loads(resp.read().decode("utf-8"))
            user = upsert_app_user(profile)
            session = sign_session_payload({
                "user_id": user["user_id"],
                "email": user.get("email") or "",
                "exp": int(time.time()) + 60 * 60 * 24 * 30,
            })
        except Exception as exc:
            self.send_html(f"<html><body><h2>Googleログイン失敗</h2><p>{esc_html(str(exc))}</p></body></html>", 500)
            return

        self.send_redirect(
            "/",
            headers=[
                ("Set-Cookie", self.cookie_header(AUTH_SESSION_COOKIE, session)),
                ("Set-Cookie", self.clear_cookie_header(AUTH_STATE_COOKIE)),
            ],
        )

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path.startswith("/api/") and not self.is_public_api_path(path):
            if not self.require_auth():
                return

        if path in ("/", "/index.html"):
            self.send_file(PREVIEW_DIR / "index.html", "text/html; charset=utf-8")
        elif path == "/style.css":
            self.send_file(PREVIEW_DIR / "style.css", "text/css")
        elif path == "/app.js":
            self.send_file(PREVIEW_DIR / "app.js", "application/javascript")
        elif path == "/auth/google/start":
            self.start_google_login()
        elif path == "/auth/google/callback":
            self.finish_google_login(qs)
        elif path == "/auth/logout":
            self.send_redirect("/", headers=[("Set-Cookie", self.clear_cookie_header(AUTH_SESSION_COOKIE))])
        elif path == "/api/auth/me":
            user = self.current_user()
            self.send_json({
                "ok": True,
                "auth_enabled": auth_enabled(),
                "user": user,
            })
        elif path == "/api/accounts":
            self.send_json({"ok": True, "accounts": fetch_accounts()})
        elif path == "/api/env-settings":
            if not self.require_local():
                return
            user_id = self.current_user_id()
            self.send_json({
                "ok": True,
                "path": str(ENV_PATH),
                "items": list_settings_for_user(user_id),
                "storage": "user_settings" if user_id else "env",
                "user_id": user_id,
            })
        elif path == "/api/drafts":
            try:
                self.send_json(fetch_drafts(
                    qs.get("account", [""])[0].strip(),
                    limit=int(qs.get("limit", ["20"])[0] or 20),
                    offset=int(qs.get("offset", ["0"])[0] or 0),
                    query=qs.get("q", [""])[0].strip(),
                ))
            except Exception as e:
                self.send_json({"error": str(e)}, 500)
        elif path == "/api/draft":
            draft_id = qs.get("id", [None])[0]
            if not draft_id:
                self.send_json({"error": "id パラメータが必要です"}, 400)
                return
            try:
                data = fetch_draft(draft_id)
                self.send_json(data if data else {"error": "見つかりません"}, 200 if data else 404)
            except Exception as e:
                self.send_json({"error": str(e)}, 500)
        elif path == "/api/public-url":
            self.send_json({"url": PUBLIC_URL})
        elif path == "/api/character-settings":
            account_key = qs.get("account", [""])[0]
            fallback_url = qs.get("fallback_url", [""])[0]
            if not account_key:
                self.send_json({"error": "account パラメータが必要です"}, 400)
                return
            self.send_json({"ok": True, "setting": merged_character_setting(account_key, fallback_url)})
        elif path == "/api/image-generation/status":
            job_id = qs.get("id", [""])[0]
            if not job_id:
                self.send_json({"error": "id パラメータが必要です"}, 400)
                return
            try:
                self.send_json({"ok": True, **get_image_generation_job(job_id)})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)
        elif path == "/api/auto-post/status":
            if not self.require_local():
                return
            job_id = qs.get("id", [""])[0]
            if not job_id:
                self.send_json({"error": "id パラメータが必要です"}, 400)
                return
            try:
                self.send_json({"ok": True, **get_auto_post_job(job_id)})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)
        elif path == "/api/oembed":
            tweet_url = qs.get("url", [None])[0]
            if not tweet_url:
                self.send_json({"error": "url パラメータが必要です"}, 400)
                return
            html = get_oembed_html(tweet_url)
            if html:
                self.send_json({"ok": True, "html": html})
            else:
                self.send_json({"ok": False, "error": "oEmbed取得失敗"})
        elif path == "/local-image":
            image_path = resolve_local_image(qs.get("path", [""])[0])
            if not image_path:
                self.send_json({"error": "画像が見つからないか、許可されていないパスです"}, 404)
                return
            content_type = mimetypes.guess_type(str(image_path))[0] or "application/octet-stream"
            self.send_file(image_path, content_type)
        elif path == "/oauth2/callback":
            # oauth2_setup.py からのリダイレクトを受け取り、コードを一時保存する
            code  = qs.get("code",  [None])[0]
            state = qs.get("state", [None])[0]
            _oauth2_pending["code"]  = code
            _oauth2_pending["state"] = state
            body = "<html><body><h2>✅ 認証完了！このタブを閉じてターミナルに戻ってください。</h2></body></html>".encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)
        elif path == "/api/oauth2-callback":
            # oauth2_setup.py がポーリングしてコードを取得する。取得後はクリア
            if _oauth2_pending.get("code"):
                data = dict(_oauth2_pending)
                _oauth2_pending.clear()
                self.send_json({"ok": True, **data})
            else:
                self.send_json({"ok": False})
        else:
            self.send_response(404)
            self.end_headers()

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path.startswith("/api/") and not self.require_auth():
            return

        if path == "/api/draft":
            draft_id = qs.get("id", [None])[0]
            if not draft_id:
                self.send_json({"error": "id パラメータが必要です"}, 400)
                return
            try:
                delete_draft(draft_id)
                self.send_json({"ok": True})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)
        else:
            self.send_response(404)
            self.end_headers()

    def do_PUT(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/") and not self.require_auth():
            return

        if path == "/api/draft/part":
            body = self.read_body()
            part_id = body.get("part_id")
            content = body.get("content")
            if not part_id or content is None:
                self.send_json({"error": "part_id と content が必要です"}, 400)
                return
            try:
                ok = update_part_content(part_id, content)
                self.send_json({"ok": ok})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)
        else:
            self.send_response(404)
            self.end_headers()

    def do_PATCH(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/") and not self.require_auth():
            return

        if path == "/api/draft/status":
            body = self.read_body()
            draft_id = body.get("draft_id")
            status = body.get("status")
            if not draft_id or status not in ("draft", "published"):
                self.send_json({"error": "draft_id と status (draft|published) が必要です"}, 400)
                return
            try:
                ok = update_draft_status(draft_id, status)
                self.send_json({"ok": ok})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)
        elif path == "/api/image-prompt":
            body = self.read_body()
            draft_id = body.get("draft_id")
            prompt = (body.get("prompt") or "").strip()
            copy_text = (body.get("copy") or "").strip()
            if not draft_id or not prompt:
                self.send_json({"error": "draft_id と prompt が必要です"}, 400)
                return
            try:
                image_prompt = update_image_prompt_metadata(draft_id, prompt, copy_text)
                self.send_json({"ok": True, "image_prompt": image_prompt})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)
        elif path == "/api/character-settings":
            body = self.read_body()
            account_key = (body.get("account_key") or "").strip()
            if not account_key:
                self.send_json({"error": "account_key が必要です"}, 400)
                return
            try:
                setting = update_character_setting(account_key, body)
                self.send_json({"ok": True, "setting": setting})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)
        elif path == "/api/env-settings":
            if not self.require_local():
                return
            body = self.read_body()
            updates = body.get("updates")
            if not isinstance(updates, dict):
                self.send_json({"ok": False, "error": "updates が必要です"}, 400)
                return
            try:
                user_id = self.current_user_id()
                if user_id:
                    result = save_user_settings(user_id, updates)
                    self.send_json({
                        "ok": True,
                        **result,
                        "path": str(ENV_PATH),
                        "storage": "user_settings",
                        "items": list_settings_for_user(user_id),
                    })
                else:
                    result = save_env_settings(updates)
                    self.send_json({"ok": True, **result, "storage": "env", "items": list_settings_for_user(None)})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/") and not self.require_auth():
            return

        body = self.read_body()

        if path == "/api/notify":
            draft_id = body.get("draft_id")
            main_content = body.get("main_content", "")
            x_username = body.get("x_username", "")
            ok, err = send_discord(draft_id, main_content, x_username, self.current_user_id())
            if ok:
                self.send_json({"ok": True})
            else:
                self.send_json({"ok": False, "error": err}, 500)
        elif path == "/api/draft/part":
            draft_id = body.get("draft_id")
            content  = (body.get("content") or "").strip()
            if not draft_id or not content:
                self.send_json({"error": "draft_id と content が必要です"}, 400)
                return
            try:
                add_draft_part(draft_id, content)
                self.send_json({"ok": True})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)
        elif path == "/api/obsidian/save":
            if not self.require_local():
                return
            draft_id = body.get("draft_id")
            if not draft_id:
                self.send_json({"error": "draft_id が必要です"}, 400)
                return
            try:
                result = save_draft_to_obsidian(str(draft_id))
                self.send_json({"ok": True, **result})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)
        elif path == "/api/image-prompt/rewrite":
            draft_id = body.get("draft_id")
            prompt = (body.get("prompt") or "").strip()
            instruction = (body.get("instruction") or "").strip()
            copy_text = (body.get("copy") or "").strip()
            character_reference_url = (body.get("character_reference_url") or "").strip()
            if not draft_id or not prompt:
                self.send_json({"error": "draft_id と prompt が必要です"}, 400)
                return
            try:
                rewritten = rewrite_image_prompt_with_codex(
                    draft_id=draft_id,
                    current_prompt=prompt,
                    instruction=instruction,
                    copy_text=copy_text,
                    character_reference_url=character_reference_url,
                )
                self.send_json({"ok": True, "prompt": rewritten})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)
        elif path == "/api/draft/image":
            draft_id = body.get("draft_id")
            image_path = (body.get("image_path") or "").strip()
            if not draft_id or not image_path:
                self.send_json({"error": "draft_id と image_path が必要です"}, 400)
                return
            try:
                image_url = attach_generated_image(draft_id, image_path)
                self.send_json({"ok": True, "image_url": image_url})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)
        elif path == "/api/image-generation/start":
            draft_id = body.get("draft_id")
            prompt = (body.get("prompt") or "").strip()
            copy_text = (body.get("copy") or "").strip()
            character_reference_url = (body.get("character_reference_url") or "").strip()
            character_traits = (body.get("character_traits") or "").strip()
            character_negative = (body.get("character_negative") or "").strip()
            character_placement = (body.get("character_placement") or "").strip()
            feedback = (body.get("feedback") or "").strip()
            current_image_url = (body.get("current_image_url") or "").strip()
            reference_image_url = (body.get("reference_image_url") or "").strip()
            reference_image_path = (body.get("reference_image_path") or "").strip()
            if not draft_id or not prompt:
                self.send_json({"error": "draft_id と prompt が必要です"}, 400)
                return
            try:
                job = start_image_generation_job(
                    draft_id,
                    copy_text,
                    prompt,
                    character_reference_url,
                    character_traits,
                    character_negative,
                    character_placement,
                    feedback,
                    current_image_url,
                    reference_image_url,
                    reference_image_path,
                    self.current_user_id(),
                )
                self.send_json({"ok": True, **job})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)
        elif path == "/api/auto-post/start":
            if not self.require_local():
                return
            draft_id = body.get("draft_id")
            if not draft_id:
                self.send_json({"error": "draft_id が必要です"}, 400)
                return
            try:
                job = start_auto_post_job(str(draft_id), self.current_user_id())
                self.send_json({"ok": True, **job})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)
        else:
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    try:
        ensure_multi_user_schema()
        seed_global_logo_presets()
        print("✅ 複数ユーザー用DBスキーマを確認しました")
    except Exception as exc:
        print(f"⚠️  複数ユーザー用DBスキーマ確認をスキップ: {exc}")
    print(f"✅ プレビューサーバー起動: http://localhost:{PORT}")
    if PUBLIC_URL != f"http://localhost:{PORT}":
        print(f"🌐 公開URL: {PUBLIC_URL}")
    if not DISCORD_WEBHOOK:
        print("⚠️  DISCORD_WEBHOOK_X_DRAFT が未設定のため Discord 通知は無効です")
    print("   終了するには Ctrl+C を押してください\n")
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nサーバーを停止しました")
