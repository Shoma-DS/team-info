#!/usr/bin/env python3
"""
daily_calendar_summary.py

Googleカレンダーのイベント一覧を標準入力から受け取り、
Zoom ミーティングを作成（必要な場合）し、LINE 送信と合わせて Discord へ投稿する。

入力 JSON 形式（Remote Trigger から渡す）:
{
  "date": "2026-04-03",       # JST の日付 YYYY-MM-DD
  "events": [
    {
      "title": "ミーティング",
      "start": "10:00",        # JST の HH:MM（終日の場合は null）
      "end": "11:00",          # JST の HH:MM（終日の場合は null）
      "start_iso": "2026-04-03T01:00:00Z",  # UTC の ISO8601（Zoom API 用）
      "duration": 60,          # 分単位
      "description": "...",    # Zoom/Meet URL が含まれる場合あり
      "allDay": false
    }
  ]
}

使い方:
  echo '<JSON>' | python3 "$TEAM_INFO_ROOT/scripts/daily_calendar_summary.py"
"""

import json
import sys
import urllib.parse
import urllib.request
import time
import base64
import re
import os
import pathlib
import subprocess
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List, Dict, Tuple
import unicodedata

# ── 設定ファイルのパス ──────────────────────────────────────────
SCRIPT_DIR = pathlib.Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
ZOOM_CREDS_PATH = pathlib.Path.home() / ".config" / "zoom" / "credentials.json"
GWS_BIN = str(pathlib.Path("/usr/local/bin/gws")) if pathlib.Path("/usr/local/bin/gws").exists() else "gws"
AUTO_GWS_CREDENTIALS_PATH = pathlib.Path.home() / ".config" / "team-info" / "gws_credentials_auto.json"
_AUTO_GWS_CREDENTIALS_CHECKED = False
_AUTO_GWS_CREDENTIALS_FILE: pathlib.Path | None = None
CALENDAR_ID = "primary"
ZOOM_MESSAGE_HEADER = "[team-info] Zoom情報"
GWS_BACKEND = "file"
GWS_BACKEND_CANDIDATES = ("file", "keyring")
ZOOM_STATUS_KEY = "team-info.zoom-status"
ZOOM_RUN_ID_KEY = "team-info.zoom-run-id"
ZOOM_URL_KEY = "team-info.zoom-url"
ZOOM_MEETING_ID_KEY = "team-info.zoom-meeting-id"
ZOOM_ACCOUNT_KEY = "team-info.zoom-account-key"
ZOOM_DEFAULT_ACCOUNT_KEY = "default"
MAX_ZOOM_VERIFICATION_ATTEMPTS = 3
LINE_SENDER_URL_ENV_KEYS = ("PROLINE_MESSAGE_SENDER_URL", "LINE_MESSAGE_SENDER_URL")
LINE_SENDER_TOKEN_ENV_KEYS = ("PROLINE_MESSAGE_SENDER_TOKEN", "LINE_MESSAGE_SENDER_TOKEN")
LINE_STATUS_KEY = "team-info.line-status"
LINE_UID_KEY = "team-info.line-uid"
LINE_SENT_URL_KEY = "team-info.line-sent-url"
HTTP_TIMEOUT_SEC = 20
GWS_TIMEOUT_SEC = 30


@dataclass(frozen=True)
class ZoomAccountConfig:
    key: str
    label: str
    credentials_path: pathlib.Path
    title_prefixes: tuple[str, ...] = ()
    is_default: bool = False
    host_user_id: str = "me"
    account_id_env: Optional[str] = None
    client_id_env: Optional[str] = None
    client_secret_env: Optional[str] = None


@dataclass
class ZoomAccountContext:
    config: ZoomAccountConfig
    token: Optional[str] = None
    token_error: Optional[str] = None
    meetings: List[dict] = field(default_factory=list)
    meetings_loaded: bool = False


@dataclass(frozen=True)
class DailySummarySettings:
    webhook_config_path: pathlib.Path
    zoom_accounts: tuple[ZoomAccountConfig, ...]
    default_zoom_account_key: str


def resolve_personal_account_slug() -> str:
    """Git アカウント名から personal フォルダ名を決める。"""
    webhook_configs = sorted(REPO_ROOT.glob("personal/*/discord/discord-daily-webhook.json"))
    if len(webhook_configs) == 1:
        return webhook_configs[0].parts[-3]

    candidates: list[str] = []
    try:
        completed = subprocess.run(
            ["git", "config", "user.name"],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode == 0 and completed.stdout.strip():
            candidates.append(completed.stdout.strip())
    except Exception:
        pass

    try:
        completed = subprocess.run(
            ["git", "config", "user.email"],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode == 0 and completed.stdout.strip():
            candidates.append(completed.stdout.strip().split("@", 1)[0])
    except Exception:
        pass

    for raw in candidates:
        normalized = unicodedata.normalize("NFKD", raw)
        slug = "".join(ch for ch in normalized.lower() if ch.isalnum())
        if slug:
            if (REPO_ROOT / "personal" / slug).exists():
                return slug
            return slug
    return "default"


PERSONAL_ACCOUNT = resolve_personal_account_slug()
WEBHOOK_CONFIG_PATH = REPO_ROOT / "personal" / PERSONAL_ACCOUNT / "discord" / "discord-daily-webhook.json"
PERSONAL_DAILY_SUMMARY_DIR = REPO_ROOT / "personal" / PERSONAL_ACCOUNT / "scripts" / "daily-calendar-summary"
DAILY_SUMMARY_SETTINGS_PATH = PERSONAL_DAILY_SUMMARY_DIR / "daily_summary_settings.json"


def default_daily_summary_settings_payload() -> dict:
    return {
        "discord_webhook_file": "../../discord/discord-daily-webhook.json",
        "zoom_accounts": [
            {
                "key": ZOOM_DEFAULT_ACCOUNT_KEY,
                "label": "既定",
                "default": True,
                "credentials_file": str(ZOOM_CREDS_PATH),
                "title_prefixes": [],
                "host_user_id": "me",
                "account_id_env": "ZOOM_ACCOUNT_ID",
                "client_id_env": "ZOOM_CLIENT_ID",
                "client_secret_env": "ZOOM_CLIENT_SECRET",
            }
        ],
    }


def resolve_first_env(*keys: str) -> Optional[str]:
    for key in keys:
        value = os.environ.get(key)
        if value:
            return value
    return None


def resolve_settings_path(path_value: str, base_dir: pathlib.Path) -> pathlib.Path:
    path = pathlib.Path(path_value).expanduser()
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def load_daily_summary_settings() -> DailySummarySettings:
    payload = default_daily_summary_settings_payload()
    base_dir = PERSONAL_DAILY_SUMMARY_DIR

    if DAILY_SUMMARY_SETTINGS_PATH.exists():
        loaded = json.loads(DAILY_SUMMARY_SETTINGS_PATH.read_text())
        if not isinstance(loaded, dict):
            raise ValueError(f"{DAILY_SUMMARY_SETTINGS_PATH} は JSON object である必要があります")
        payload = loaded
        base_dir = DAILY_SUMMARY_SETTINGS_PATH.parent

    webhook_value = str(payload.get("discord_webhook_file") or WEBHOOK_CONFIG_PATH)
    accounts_raw = payload.get("zoom_accounts")
    if not isinstance(accounts_raw, list) or not accounts_raw:
        raise ValueError("daily_summary_settings.json の `zoom_accounts` には1件以上の配列が必要です")

    zoom_accounts: List[ZoomAccountConfig] = []
    seen_keys: set[str] = set()
    explicit_default_key: Optional[str] = None

    for index, raw_account in enumerate(accounts_raw, start=1):
        if not isinstance(raw_account, dict):
            raise ValueError(f"zoom_accounts[{index}] は object である必要があります")

        key = str(raw_account.get("key") or "").strip()
        if not key:
            raise ValueError(f"zoom_accounts[{index}].key は必須です")
        if key in seen_keys:
            raise ValueError(f"Zoom アカウントキーが重複しています: {key}")
        seen_keys.add(key)

        label = str(raw_account.get("label") or key).strip() or key
        credentials_file = str(raw_account.get("credentials_file") or "").strip()
        if not credentials_file:
            raise ValueError(f"zoom_accounts[{index}].credentials_file は必須です")

        raw_prefixes = raw_account.get("title_prefixes") or []
        if not isinstance(raw_prefixes, list):
            raise ValueError(f"zoom_accounts[{index}].title_prefixes は配列である必要があります")
        title_prefixes = tuple(prefix.strip() for prefix in raw_prefixes if str(prefix).strip())

        is_default = bool(raw_account.get("default"))
        if is_default:
            if explicit_default_key is not None:
                raise ValueError("Zoom の default アカウントは1件だけ指定できます")
            explicit_default_key = key

        host_user_id = str(raw_account.get("host_user_id") or "me").strip() or "me"

        zoom_accounts.append(ZoomAccountConfig(
            key=key,
            label=label,
            credentials_path=resolve_settings_path(credentials_file, base_dir),
            title_prefixes=title_prefixes,
            is_default=is_default,
            host_user_id=host_user_id,
            account_id_env=(str(raw_account.get("account_id_env")).strip() or None)
            if raw_account.get("account_id_env") is not None else None,
            client_id_env=(str(raw_account.get("client_id_env")).strip() or None)
            if raw_account.get("client_id_env") is not None else None,
            client_secret_env=(str(raw_account.get("client_secret_env")).strip() or None)
            if raw_account.get("client_secret_env") is not None else None,
        ))

    default_key = explicit_default_key
    if default_key is None:
        for account in zoom_accounts:
            if account.key == ZOOM_DEFAULT_ACCOUNT_KEY:
                default_key = account.key
                break
    if default_key is None:
        default_key = zoom_accounts[0].key

    return DailySummarySettings(
        webhook_config_path=resolve_settings_path(webhook_value, base_dir),
        zoom_accounts=tuple(zoom_accounts),
        default_zoom_account_key=default_key,
    )


# ── Zoom API ────────────────────────────────────────────────────

def resolve_zoom_account_key(title: Optional[str], settings: DailySummarySettings) -> str:
    normalized = (title or "").lstrip()
    for account in settings.zoom_accounts:
        if account.key == settings.default_zoom_account_key:
            continue
        for prefix in account.title_prefixes:
            if normalized.startswith(prefix):
                return account.key
    return settings.default_zoom_account_key


def get_zoom_account_config(settings: DailySummarySettings, account_key: str) -> ZoomAccountConfig:
    for account in settings.zoom_accounts:
        if account.key == account_key:
            return account
    raise KeyError(f"未知の Zoom アカウントキーです: {account_key}")


def zoom_account_may_be_configured(config: ZoomAccountConfig) -> bool:
    env_values = (
        os.environ.get(config.account_id_env) if config.account_id_env else None,
        os.environ.get(config.client_id_env) if config.client_id_env else None,
        os.environ.get(config.client_secret_env) if config.client_secret_env else None,
    )
    if any(env_values):
        return True
    return config.credentials_path.exists()


def load_zoom_credentials(config: ZoomAccountConfig) -> Dict[str, str]:
    creds: dict = {}
    if config.credentials_path.exists():
        creds = json.loads(config.credentials_path.read_text())

    account_id = (os.environ.get(config.account_id_env) if config.account_id_env else None) or creds.get("account_id")
    client_id = (os.environ.get(config.client_id_env) if config.client_id_env else None) or creds.get("client_id")
    client_secret = (os.environ.get(config.client_secret_env) if config.client_secret_env else None) or creds.get("client_secret")
    missing = []
    if not account_id:
        missing.append("account_id")
    if not client_id:
        missing.append("client_id")
    if not client_secret:
        missing.append("client_secret")
    if missing:
        raise ValueError(
            f"{config.label}用 Zoom 資格情報が不足しています: {', '.join(missing)} "
            f"(env: {config.account_id_env or '-'} / {config.client_id_env or '-'} / {config.client_secret_env or '-'}, "
            f"file: {config.credentials_path})"
        )
    return {
        "account_id": account_id,
        "client_id": client_id,
        "client_secret": client_secret,
    }


def get_zoom_token(config: ZoomAccountConfig) -> str:
    """Server-to-Server OAuth でアクセストークンを取得する（env vars → 設定ファイルの順）"""
    credentials = load_zoom_credentials(config)
    account_id = credentials["account_id"]
    client_id = credentials["client_id"]
    client_secret = credentials["client_secret"]
    auth = base64.b64encode(
        f"{client_id}:{client_secret}".encode()
    ).decode()
    url = (
        f"https://zoom.us/oauth/token"
        f"?grant_type=account_credentials&account_id={account_id}"
    )
    req = urllib.request.Request(
        url, method="POST",
        headers={"Authorization": f"Basic {auth}"}
    )
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_SEC) as resp:
        return json.loads(resp.read())["access_token"]


def resolve_zoom_context(
    zoom_contexts: Dict[str, ZoomAccountContext],
    settings: DailySummarySettings,
    account_key: str,
) -> ZoomAccountContext:
    context = zoom_contexts.get(account_key)
    if context is None:
        context = ZoomAccountContext(config=get_zoom_account_config(settings, account_key))
        zoom_contexts[account_key] = context
    return context


def ensure_zoom_context_ready(
    zoom_contexts: Dict[str, ZoomAccountContext],
    settings: DailySummarySettings,
    account_key: str,
) -> ZoomAccountContext:
    context = resolve_zoom_context(zoom_contexts, settings, account_key)
    if context.token is None and context.token_error is None:
        try:
            context.token = get_zoom_token(context.config)
            print(f"[Zoom:{context.config.label}] 認証成功", file=sys.stderr)
        except Exception as e:
            context.token_error = str(e)
            print(f"[Zoom:{context.config.label}] 認証失敗: {e}", file=sys.stderr)
            return context

    if context.token and not context.meetings_loaded:
        meetings, list_error = list_zoom_meetings(
            context.token,
            context.config.label,
            context.config.host_user_id,
        )
        context.meetings = meetings
        context.meetings_loaded = True
        if list_error:
            print(f"[Zoom:{context.config.label}] {list_error}", file=sys.stderr)
    return context


def create_zoom_meeting(
    token: str,
    title: str,
    start_iso: str,
    duration_min: int,
    account_label: str,
    host_user_id: str,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Zoom ミーティングを作成して join_url と meeting id を返す。失敗時は理由も返す"""
    encoded_user_id = urllib.parse.quote(host_user_id, safe="")
    url = f"https://api.zoom.us/v2/users/{encoded_user_id}/meetings"
    payload = json.dumps({
        "topic": title,
        "type": 2,                   # スケジュールミーティング
        "start_time": start_iso,
        "duration": duration_min,
        "timezone": "Asia/Tokyo",
        "settings": {
            "join_before_host": True,
            "waiting_room": False,
        }
    }).encode()
    req = urllib.request.Request(
        url, data=payload, method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_SEC) as resp:
            payload = json.loads(resp.read())
            meeting_id = str(payload.get("id")) if payload.get("id") else None
            return payload["join_url"], meeting_id, None
    except Exception as e:
        reason = f"Zoom ミーティング作成失敗: {e}"
        print(f"[Zoom:{account_label}] {reason}（{title}）", file=sys.stderr)
        return None, None, reason


def list_zoom_meetings(token: str, account_label: str, host_user_id: str) -> Tuple[list[dict], Optional[str]]:
    """Zoom の scheduled meetings を取得する"""
    encoded_user_id = urllib.parse.quote(host_user_id, safe="")
    url = f"https://api.zoom.us/v2/users/{encoded_user_id}/meetings?type=scheduled&page_size=300"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_SEC) as resp:
            data = json.loads(resp.read())
            return data.get("meetings", []), None
    except Exception as e:
        reason = f"既存ミーティング取得失敗: {e}"
        print(f"[Zoom:{account_label}] {reason}", file=sys.stderr)
        return [], reason


def delete_zoom_meeting(token: str, meeting_id: str, account_label: str) -> Optional[str]:
    """Zoom の scheduled meeting を削除する。成功時は None を返す"""
    url = f"https://api.zoom.us/v2/meetings/{meeting_id}"
    req = urllib.request.Request(
        url,
        method="DELETE",
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_SEC):
            return None
    except Exception as e:
        reason = f"重複 Zoom ミーティング削除失敗: {e}"
        print(f"[Zoom:{account_label}] {reason}（meeting_id={meeting_id}）", file=sys.stderr)
        return reason


def normalize_zoom_datetime(value: Optional[str]) -> Optional[datetime]:
    """Zoom / Calendar の ISO 文字列を UTC datetime にそろえる"""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def find_existing_zoom_meeting(meetings: List[dict], title: str, start_iso: str) -> Optional[str]:
    """同タイトル・同開始時刻の Zoom scheduled meeting があれば join_url を返す"""
    target_dt = normalize_zoom_datetime(start_iso)
    if not target_dt:
        return None

    normalized_title = title.strip()
    for meeting in meetings:
        meeting_title = (meeting.get("topic") or "").strip()
        meeting_dt = normalize_zoom_datetime(meeting.get("start_time"))
        if not meeting_dt:
            continue
        if meeting_title != normalized_title:
            continue
        if abs((meeting_dt - target_dt).total_seconds()) <= 300:
            return meeting.get("join_url")
    return None


def find_zoom_meeting_by_id(meetings: List[dict], meeting_id: Optional[str]) -> Optional[dict]:
    if not meeting_id:
        return None
    for meeting in meetings:
        if str(meeting.get("id") or "") == str(meeting_id):
            return meeting
    return None


def is_matching_zoom_meeting(meeting: Optional[dict], title: str, start_iso: str) -> bool:
    if not meeting:
        return False

    target_dt = normalize_zoom_datetime(start_iso)
    meeting_dt = normalize_zoom_datetime(meeting.get("start_time"))
    if not target_dt or not meeting_dt:
        return False

    meeting_title = (meeting.get("topic") or "").strip()
    if meeting_title != title.strip():
        return False

    return abs((meeting_dt - target_dt).total_seconds()) <= 300


def list_matching_zoom_meetings(meetings: List[dict], title: str, start_iso: str) -> List[dict]:
    return [meeting for meeting in meetings if is_matching_zoom_meeting(meeting, title, start_iso)]


def is_reusable_zoom_url(meeting_url: Optional[str], meetings: List[dict], title: str, start_iso: Optional[str]) -> Tuple[bool, Optional[str]]:
    """Zoom URL が当日の対象予定に対応していれば再利用可とみなす"""
    if not meeting_url:
        return False, "Zoom URL がありません"
    if "zoom.us/" not in meeting_url:
        return True, None
    if not start_iso:
        return True, None

    meeting_id = extract_zoom_meeting_id(meeting_url)
    meeting = find_zoom_meeting_by_id(meetings, meeting_id)
    if not meeting:
        return False, "説明欄の Zoom URL が Zoom scheduled meetings に存在しません"
    if not is_matching_zoom_meeting(meeting, title, start_iso):
        return False, "説明欄の Zoom URL が本日の予定タイトルまたは開始時刻と一致しません"
    return True, None


def find_zoom_context_for_meeting_id(
    zoom_contexts: Dict[str, ZoomAccountContext],
    settings: DailySummarySettings,
    meeting_id: Optional[str],
) -> Optional[ZoomAccountContext]:
    if not meeting_id:
        return None

    for account in settings.zoom_accounts:
        if not zoom_account_may_be_configured(account):
            continue
        context = ensure_zoom_context_ready(zoom_contexts, settings, account.key)
        if not context.token:
            continue
        if find_zoom_meeting_by_id(context.meetings, meeting_id):
            return context
    return None


def cleanup_duplicate_zoom_meetings(
    zoom_contexts: Dict[str, ZoomAccountContext],
    settings: DailySummarySettings,
    account_key: str,
    title: str,
    start_iso: str,
    keep_url: str,
    extra_delete_urls: Optional[set[str]] = None,
) -> List[str]:
    """確定した meeting 以外の重複 scheduled meetings を削除する"""
    context = ensure_zoom_context_ready(zoom_contexts, settings, account_key)
    if not context.token:
        return [f"{context.config.label} Zoom トークンがないため重複ミーティングを削除できません"]

    keep_id = extract_zoom_meeting_id(keep_url)
    delete_targets: set[tuple[str, str]] = set()
    for meeting in list_matching_zoom_meetings(context.meetings, title, start_iso):
        meeting_id = str(meeting.get("id") or "")
        if meeting_id and meeting_id != keep_id:
            delete_targets.add((account_key, meeting_id))

    errors: List[str] = []
    for stale_url in sorted(extra_delete_urls or set()):
        stale_id = extract_zoom_meeting_id(stale_url)
        if not stale_id or stale_id == keep_id:
            continue
        owner_context = find_zoom_context_for_meeting_id(zoom_contexts, settings, stale_id)
        if owner_context:
            delete_targets.add((owner_context.config.key, stale_id))
        else:
            errors.append(f"古い Zoom ミーティング {stale_id} の所有アカウントを特定できません")

    if not delete_targets:
        return errors

    for target_account_key, meeting_id in sorted(delete_targets):
        target_context = ensure_zoom_context_ready(zoom_contexts, settings, target_account_key)
        if not target_context.token:
            errors.append(
                f"{target_context.config.label} Zoom トークンがないため重複ミーティング {meeting_id} を削除できません"
            )
            continue
        delete_error = delete_zoom_meeting(target_context.token, meeting_id, target_context.config.label)
        if delete_error:
            errors.append(delete_error)
        else:
            print(f"[Zoom:{target_context.config.label}] 重複ミーティング削除: {meeting_id}")
            target_context.meetings = [
                meeting for meeting in target_context.meetings
                if str(meeting.get("id") or "") != meeting_id
            ]
    return errors


def extract_zoom_meeting_id(meeting_url: Optional[str]) -> Optional[str]:
    if not meeting_url:
        return None
    match = re.search(r"/j/(\d+)", meeting_url)
    if match:
        return match.group(1)
    return None


def extract_line_user_id(description: Optional[str], event: Optional[dict] = None) -> Optional[str]:
    private = ((event or {}).get("extendedProperties") or {}).get("private") or {}
    private_uid = private.get(LINE_UID_KEY)
    if private_uid:
        return private_uid.strip()

    if not description:
        return None

    patterns = [
        r"[?&]uid=([A-Za-z0-9_-]+)",
        r"\buid\s*[:=]\s*([A-Za-z0-9_-]+)",
        r"ユーザーID\s*[:=：＝]\s*([A-Za-z0-9_-]+)",
        r"\"uid\"\s*:\s*\"([A-Za-z0-9_-]+)\"",
    ]
    for pattern in patterns:
        match = re.search(pattern, description, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def send_line_message(line_sender_url: str, user_id: str, content: str, shared_token: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    payload: Dict[str, str] = {
        "userId": user_id,
        "messageContent": content,
    }
    if shared_token:
        payload["token"] = shared_token

    req = urllib.request.Request(
        line_sender_url,
        data=json.dumps(payload, ensure_ascii=False).encode(),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "team-info daily-calendar-summary",
        },
        method="POST",
    )
    try:
        print(f"[LINE] 送信開始: uid={user_id}", file=sys.stderr, flush=True)
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_SEC) as resp:
            response_text = resp.read().decode("utf-8", errors="replace")
        try:
            response_json = json.loads(response_text)
        except json.JSONDecodeError:
            response_json = None
        if response_json and response_json.get("ok") is False:
            return False, response_json.get("error") or "LINE 送信先がエラーを返しました"
        print(f"[LINE] 送信完了: uid={user_id}", file=sys.stderr, flush=True)
        return True, None
    except Exception as e:
        return False, f"LINE 送信失敗: {e}"


# ── Google Calendar via GWS CLI ────────────────────────────────

def gws_env() -> Dict[str, str]:
    env = dict(os.environ)
    env["GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND"] = resolve_gws_backend()
    auto_credentials = ensure_auto_credentials_file()
    if auto_credentials:
        env["GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE"] = str(auto_credentials)
    return env


def auth_status_for_backend(backend: str) -> Optional[dict]:
    env = dict(os.environ)
    env["GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND"] = backend
    result = subprocess.run(
        [GWS_BIN, "auth", "status"],
        text=True,
        capture_output=True,
        env=env,
    )
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def auth_export_from_backend(backend: str) -> Optional[dict]:
    env = dict(os.environ)
    env["GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND"] = backend
    result = subprocess.run(
        [GWS_BIN, "auth", "export", "--unmasked"],
        text=True,
        capture_output=True,
        env=env,
    )
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def resolve_gws_backend() -> str:
    explicit = os.environ.get("GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND")
    if explicit:
        return explicit
    candidates = [explicit] if explicit else []
    for backend in GWS_BACKEND_CANDIDATES:
        if backend not in candidates:
            candidates.append(backend)

    for backend in candidates:
        status = auth_status_for_backend(backend)
        if not status:
            continue
        if status.get("auth_method") != "oauth2":
            continue
        if not status.get("encryption_valid", True):
            continue
        if not status.get("token_valid", False):
            continue
        return backend

    return explicit or GWS_BACKEND


def is_usable_backend_status(status: Optional[dict]) -> bool:
    if not status:
        return False
    if status.get("auth_method") != "oauth2":
        return False
    if not status.get("encryption_valid", True):
        return False
    if not status.get("token_valid", False):
        return False
    return True


def write_auto_credentials_file(payload: dict) -> pathlib.Path:
    AUTO_GWS_CREDENTIALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUTO_GWS_CREDENTIALS_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    os.chmod(AUTO_GWS_CREDENTIALS_PATH, 0o600)
    return AUTO_GWS_CREDENTIALS_PATH


def read_existing_auto_credentials_file() -> Optional[pathlib.Path]:
    if not AUTO_GWS_CREDENTIALS_PATH.exists():
        return None
    try:
        payload = json.loads(AUTO_GWS_CREDENTIALS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not payload.get("client_id") or not payload.get("refresh_token"):
        return None
    return AUTO_GWS_CREDENTIALS_PATH


def ensure_auto_credentials_file() -> Optional[pathlib.Path]:
    global _AUTO_GWS_CREDENTIALS_CHECKED, _AUTO_GWS_CREDENTIALS_FILE

    if _AUTO_GWS_CREDENTIALS_CHECKED:
        return _AUTO_GWS_CREDENTIALS_FILE
    _AUTO_GWS_CREDENTIALS_CHECKED = True

    explicit = os.environ.get("GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE")
    if explicit:
        explicit_path = pathlib.Path(explicit).expanduser()
        if explicit_path.exists():
            _AUTO_GWS_CREDENTIALS_FILE = explicit_path
        return _AUTO_GWS_CREDENTIALS_FILE

    if os.environ.get("GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND"):
        return None

    file_status = auth_status_for_backend("file")
    if is_usable_backend_status(file_status):
        return None

    keyring_status = auth_status_for_backend("keyring")
    if is_usable_backend_status(keyring_status):
        exported = auth_export_from_backend("keyring")
        if exported and exported.get("client_id") and exported.get("refresh_token"):
            _AUTO_GWS_CREDENTIALS_FILE = write_auto_credentials_file(exported)
            return _AUTO_GWS_CREDENTIALS_FILE

    _AUTO_GWS_CREDENTIALS_FILE = read_existing_auto_credentials_file()
    return _AUTO_GWS_CREDENTIALS_FILE


def gws_event_patch(calendar_id: str, event_id: str, body: dict) -> Tuple[bool, Optional[str]]:
    """GWS CLI でカレンダーイベントを patch する"""
    try:
        result = subprocess.run(
            [
                GWS_BIN, "calendar", "events", "patch",
                "--params", json.dumps({
                    "calendarId": calendar_id,
                    "eventId": event_id,
                    "sendUpdates": "none",
                }, ensure_ascii=False),
                "--json", json.dumps(body, ensure_ascii=False),
            ],
            text=True,
            capture_output=True,
            env=gws_env(),
            timeout=GWS_TIMEOUT_SEC,
        )
    except subprocess.TimeoutExpired:
        reason = f"GWS patch が {GWS_TIMEOUT_SEC} 秒でタイムアウトしました"
        print(f"[Google Calendar] {reason}", file=sys.stderr)
        return False, reason
    if result.returncode != 0:
        stderr = result.stderr.strip() or "unknown error"
        print(f"[Google Calendar] GWS patch 失敗: {stderr}", file=sys.stderr)
        return False, stderr
    return True, None


def gws_event_get(calendar_id: str, event_id: str) -> Tuple[Optional[dict], Optional[str]]:
    """GWS CLI でカレンダーイベントを取得する"""
    try:
        result = subprocess.run(
            [
                GWS_BIN, "calendar", "events", "get",
                "--params", json.dumps({
                    "calendarId": calendar_id,
                    "eventId": event_id,
                }, ensure_ascii=False),
            ],
            text=True,
            capture_output=True,
            env=gws_env(),
            timeout=GWS_TIMEOUT_SEC,
        )
    except subprocess.TimeoutExpired:
        reason = f"GWS get が {GWS_TIMEOUT_SEC} 秒でタイムアウトしました"
        print(f"[Google Calendar] {reason}", file=sys.stderr)
        return None, reason
    if result.returncode != 0:
        stderr = result.stderr.strip() or "unknown error"
        print(f"[Google Calendar] GWS get 失敗: {stderr}", file=sys.stderr)
        return None, stderr
    try:
        return json.loads(result.stdout), None
    except json.JSONDecodeError:
        reason = "GWS get 応答の JSON 解析に失敗"
        print(f"[Google Calendar] {reason}", file=sys.stderr)
        return None, reason


def merge_private_properties(event: Optional[dict], updates: Dict[str, str]) -> dict:
    """既存イベントの private extendedProperties を保持したまま更新する"""
    existing = ((event or {}).get("extendedProperties") or {}).get("private") or {}
    merged = dict(existing)
    merged.update(updates)
    return {"extendedProperties": {"private": merged}}


def try_acquire_zoom_creation_lock(
    event: dict,
    zoom_meetings: List[dict],
    account_key: str,
    account_label: str,
) -> Tuple[bool, Optional[dict], Optional[str]]:
    """同時実行時に 1 つだけが Zoom 作成に進むようイベント上でロックする"""
    event_id = event.get("event_id")
    calendar_id = event.get("calendar_id", CALENDAR_ID)
    if not event_id:
        return False, None, "event_id がないため Zoom 作成ロックを取得できません"

    latest, latest_error = gws_event_get(calendar_id, event_id)
    if latest_error:
        return False, latest, f"GWS get 失敗: {latest_error}"
    latest_description = (latest or {}).get("description") or event.get("description") or ""
    latest_url = extract_meeting_url(latest_description)
    if latest_url:
        reusable, reusable_reason = is_reusable_zoom_url(
            latest_url,
            zoom_meetings,
            event["title"],
            event.get("start_iso"),
        )
        if reusable:
            event["description"] = latest_description
            return False, latest, None
        print(
            f"[Zoom:{account_label}] 既存URLを stale 扱いにして再発行します（{event.get('title', '（タイトルなし）')}）: {reusable_reason}",
            file=sys.stderr,
        )

    run_id = str(uuid.uuid4())
    patch_body = merge_private_properties(latest, {
        ZOOM_STATUS_KEY: "creating",
        ZOOM_RUN_ID_KEY: run_id,
        ZOOM_ACCOUNT_KEY: account_key,
    })
    patched, patch_error = gws_event_patch(calendar_id, event_id, patch_body)
    if not patched:
        return False, latest, f"GWS patch 失敗: {patch_error}"

    current, current_error = gws_event_get(calendar_id, event_id)
    if current_error:
        return False, current, f"GWS get 再取得失敗: {current_error}"
    current_private = ((current or {}).get("extendedProperties") or {}).get("private") or {}
    current_description = (current or {}).get("description") or latest_description
    current_url = resolve_calendar_zoom_url(current, current_description)
    if current_url:
        reusable, reusable_reason = is_reusable_zoom_url(
            current_url,
            zoom_meetings,
            event["title"],
            event.get("start_iso"),
        )
        if reusable:
            event["description"] = current_description
            return False, current, None
        print(
            f"[Zoom:{account_label}] ロック取得後も stale URL を検出したため新規発行へ進みます（{event.get('title', '（タイトルなし）')}）: {reusable_reason}",
            file=sys.stderr,
        )

    if current_private.get(ZOOM_RUN_ID_KEY) != run_id:
        return False, current, "別プロセスが先に Zoom 作成ロックを取得しました"
    return True, current, None


def build_zoom_share_message(title: str, start: str, end: str, meeting_url: str, meeting_id: Optional[str] = None) -> str:
    """相手に送る Zoom リンク文面を返す"""
    lines = [
        "お世話になっております。",
        f"本日 {start}〜{end} の「{title}」の会議リンクをお送りします。",
        "",
    ]
    if meeting_id:
        lines.extend([
            f"ミーティングID: {meeting_id}",
            "",
        ])
    lines.extend([
        meeting_url,
        "",
        "よろしくお願いいたします。",
    ])
    return "\n".join(lines)


def log_zoom_ready(title: str, meeting_url: str, source: str) -> None:
    print(
        f"[Progress] Zoom確定: {title} / source={source} / url={meeting_url}",
        file=sys.stderr,
        flush=True,
    )


def build_zoom_description_block(meeting_url: str, share_message: str, meeting_id: Optional[str] = None) -> str:
    """説明欄へ追記する Zoom 情報ブロックを返す"""
    lines = [
        ZOOM_MESSAGE_HEADER,
    ]
    if meeting_id:
        lines.extend([
            "Zoom Meeting ID:",
            meeting_id,
            "",
        ])
    lines.extend([
        "Zoom URL:",
        meeting_url,
        "",
        "Zoom URL送信メッセージ:",
        share_message,
    ])
    return "\n".join(lines)


LEGACY_HOST_URL_LABELS = (
    "Zoom会議室開始URL",
    "Zoom開始URL（ホスト、主催者）",
)

LEGACY_GUEST_URL_LABELS = (
    "Zoom参加URL（ゲスト、予約者）",
    "Zoom招待URL（友だち用）",
)


def extract_legacy_labeled_url(stripped: str, labels: tuple[str, ...]) -> Optional[str]:
    """`ラベル: URL` / `ラベル：URL` 形式の行から URL を抜き出す。"""
    for label in labels:
        pattern = rf"^{re.escape(label)}[:：]\s*(https?://\S+)"
        match = re.match(pattern, stripped)
        if match:
            return match.group(1).rstrip(".,;)")
    return None


def extract_legacy_host_zoom_url(description: Optional[str]) -> Optional[str]:
    """旧説明欄のホスト用 Zoom URL があれば返す。"""
    if not description:
        return None
    for line in description.replace("\r\n", "\n").split("\n"):
        host_url = extract_legacy_labeled_url(line.strip(), LEGACY_HOST_URL_LABELS)
        if host_url:
            return host_url
    return None


def is_legacy_zoom_description_line(stripped: str) -> bool:
    """旧式の Zoom 案内行なら True を返す。"""
    for prefix in LEGACY_GUEST_URL_LABELS:
        if stripped == prefix:
            return True
        if stripped.startswith(f"{prefix}:") or stripped.startswith(f"{prefix}："):
            return True
    for prefix in LEGACY_HOST_URL_LABELS:
        if stripped == prefix:
            return True
        if (stripped.startswith(f"{prefix}:") or stripped.startswith(f"{prefix}：")) and not extract_legacy_labeled_url(stripped, (prefix,)):
            return True
    return False


def normalize_calendar_description(description: Optional[str]) -> str:
    """説明欄を正本フォーマットへ寄せるため、旧 Zoom 情報を取り除く"""
    if not description:
        return ""

    text = description.replace("\r\n", "\n")
    lines = text.split("\n")
    kept: List[str] = []
    skipping_team_info = False
    skipping_proline_footer = False

    for line in lines:
        stripped = line.strip()
        if stripped == ZOOM_MESSAGE_HEADER:
            skipping_team_info = True
            continue
        if skipping_team_info:
            continue
        if stripped == "予約を変更したい場合はこちら":
            skipping_proline_footer = True
            continue
        if skipping_proline_footer:
            if stripped.startswith("Powered by プロラインフリー"):
                continue
            if is_legacy_zoom_description_line(stripped):
                continue
            if stripped.startswith("※プロラインフリーで予約して作成されたスケジュール"):
                continue
            if stripped.startswith("https://"):
                continue
            if stripped == "":
                continue
            skipping_proline_footer = False
        if is_legacy_zoom_description_line(stripped):
            continue
        if stripped.startswith("Powered by プロラインフリー"):
            continue
        if stripped.startswith("※プロラインフリーで予約して作成されたスケジュール"):
            continue
        kept.append(line.rstrip())

    normalized = "\n".join(kept)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def append_zoom_message(description: Optional[str], meeting_url: str, share_message: str, meeting_id: Optional[str] = None) -> str:
    """既存説明欄へ Zoom URL と送信用メッセージを追記する"""
    base = normalize_calendar_description(description)
    block = build_zoom_description_block(meeting_url, share_message, meeting_id)
    if block in base:
        return base
    if not base:
        return block
    return f"{base}\n\n{block}"


def build_calendar_location(existing_location: Optional[str], meeting_url: str) -> str:
    """Loom/Zoom が拾いやすいよう、location にも Zoom URL を持たせる。"""
    current = (existing_location or "").strip()
    if not current:
        return meeting_url

    existing_url = extract_meeting_url(current)
    if existing_url:
        if current == existing_url or "zoom.us/" in existing_url or "meet.google.com/" in existing_url:
            return meeting_url

    if meeting_url in current:
        return current

    return f"{meeting_url}\n{current}"


def update_calendar_description(
    event: dict,
    meeting_url: str,
    share_message: str,
    meeting_id: Optional[str] = None,
    account_key: Optional[str] = None,
) -> Tuple[bool, Optional[str]]:
    """Google カレンダーの説明欄へ Zoom 送信用メッセージを追記する"""
    event_id = event.get("event_id")
    if not event_id:
        return False, "event_id がないため説明欄を更新できません"

    calendar_id = event.get("calendar_id", CALENDAR_ID)
    latest, latest_error = gws_event_get(calendar_id, event_id)
    if latest_error:
        return False, f"GWS get 失敗: {latest_error}"
    current_description = (latest or {}).get("description") or event.get("description")
    new_description = append_zoom_message(current_description, meeting_url, share_message, meeting_id)
    current_location = (latest or {}).get("location") or event.get("location")
    new_location = build_calendar_location(current_location, meeting_url)
    line_uid = extract_line_user_id(current_description, latest)
    patch_body = {
        "description": new_description,
        "location": new_location,
    }
    private_updates = {
        ZOOM_STATUS_KEY: "created",
        ZOOM_URL_KEY: meeting_url,
        ZOOM_MEETING_ID_KEY: meeting_id or "",
    }
    if account_key:
        private_updates[ZOOM_ACCOUNT_KEY] = account_key
    if line_uid:
        private_updates[LINE_UID_KEY] = line_uid
    patch_body.update(merge_private_properties(latest, private_updates))

    try:
        patched, patch_error = gws_event_patch(calendar_id, event_id, patch_body)
        if patched:
            print(f"[Google Calendar] 説明欄更新: {event.get('title', '（タイトルなし）')}")
            return True, None
        else:
            print(f"[Google Calendar] 説明欄更新失敗（{event.get('title', '（タイトルなし）')}）", file=sys.stderr)
            return False, f"GWS patch 失敗: {patch_error}"
    except Exception as e:
        print(f"[Google Calendar] 説明欄更新失敗（{event.get('title', '（タイトルなし）')}）: {e}", file=sys.stderr)
        return False, str(e)


# ── URL 抽出 ────────────────────────────────────────────────────

_URL_PATTERNS = [
    r'https://[\w.-]*zoom\.us/j/[\w?=&%-]+',
    r'https://meet\.google\.com/[\w-]+',
]

def extract_meeting_url(description: Optional[str]) -> Optional[str]:
    """説明文から Zoom / Meet の URL を探して返す"""
    if not description:
        return None
    for pattern in _URL_PATTERNS:
        match = re.search(pattern, description)
        if match:
            return match.group(0).rstrip(".,;)")
    return None


def resolve_calendar_zoom_url(event: Optional[dict], fallback_description: Optional[str] = None) -> Optional[str]:
    """カレンダーイベント本体と private properties の両方から Zoom URL を拾う"""
    location = (event or {}).get("location")
    location_url = extract_meeting_url(location)
    if location_url:
        return location_url
    description = (event or {}).get("description") or fallback_description
    description_url = extract_meeting_url(description)
    if description_url:
        return description_url
    private = ((event or {}).get("extendedProperties") or {}).get("private") or {}
    private_url = private.get(ZOOM_URL_KEY)
    if private_url:
        return private_url
    return None


def verify_zoom_link(event: dict, expected_url: Optional[str]) -> Tuple[bool, Optional[str], Optional[str]]:
    """説明欄へ Zoom URL が反映されたことを再取得で検証する"""
    event_id = event.get("event_id")
    if not event_id:
        return False, None, "event_id がないため Zoom URL を検証できません"

    latest, latest_error = gws_event_get(event.get("calendar_id", CALENDAR_ID), event_id)
    if latest_error:
        return False, None, f"GWS get 失敗: {latest_error}"

    latest_url = resolve_calendar_zoom_url(latest, event.get("description"))
    if not latest_url:
        return False, None, "カレンダー再取得後も Zoom URL が確認できません"
    if expected_url and latest_url != expected_url:
        print(
            f"[Zoom] 検証で別URLを検出（{event.get('title', '（タイトルなし）')}）: {latest_url}",
            file=sys.stderr,
        )
    return True, latest_url, None


def build_zoom_failure_report(date_str: str, failures: List[dict]) -> str:
    """Zoom 発行失敗の Discord 通知文面を返す"""
    header = [
        f"**Zoomリンク発行エラー（{date_str}）**",
        "Zoomリンクの発行または検証が最大3回でも完了しなかったため、通常の予定通知は止めています。",
        "",
    ]
    body: List[str] = []
    for index, failure in enumerate(failures, 1):
        title = failure.get("title", "（タイトルなし）")
        start = failure.get("start") or "--:--"
        end = failure.get("end") or "--:--"
        account_label = failure.get("zoom_account_label")
        body.append(f"{index}. {title} ({start}〜{end})")
        if account_label:
            body.append(f"- Zoomアカウント: {account_label}")
        for reason in failure.get("reasons", []):
            body.append(f"- {reason}")
        body.append("")
    return "\n".join(header + body).strip()


def build_line_failure_report(date_str: str, failures: List[dict]) -> str:
    header = [
        f"**LINE送信エラー（{date_str}）**",
        "Zoomリンクは作成できましたが、LINE 送信が完了しなかったため通常の予定通知は止めています。",
        "",
    ]
    body: List[str] = []
    for index, failure in enumerate(failures, 1):
        title = failure.get("title", "（タイトルなし）")
        start = failure.get("start") or "--:--"
        end = failure.get("end") or "--:--"
        uid = failure.get("line_user_id") or "不明"
        body.append(f"{index}. {title} ({start}〜{end})")
        body.append(f"- uid: {uid}")
        for reason in failure.get("reasons", []):
            body.append(f"- {reason}")
        body.append("")
    return "\n".join(header + body).strip()


def was_line_message_sent(event: Optional[dict], user_id: str, meeting_url: str) -> bool:
    private = ((event or {}).get("extendedProperties") or {}).get("private") or {}
    return (
        private.get(LINE_STATUS_KEY) == "sent"
        and private.get(LINE_UID_KEY) == user_id
        and private.get(LINE_SENT_URL_KEY) == meeting_url
    )


def mark_line_message_sent(event: dict, user_id: str, meeting_url: str) -> Tuple[bool, Optional[str]]:
    event_id = event.get("event_id")
    if not event_id:
        return False, "event_id がないため LINE 送信状態を保存できません"

    calendar_id = event.get("calendar_id", CALENDAR_ID)
    latest, latest_error = gws_event_get(calendar_id, event_id)
    if latest_error:
        return False, f"GWS get 失敗: {latest_error}"

    patch_body = merge_private_properties(latest, {
        LINE_STATUS_KEY: "sent",
        LINE_UID_KEY: user_id,
        LINE_SENT_URL_KEY: meeting_url,
    })
    patched, patch_error = gws_event_patch(calendar_id, event_id, patch_body)
    if not patched:
        return False, f"GWS patch 失敗: {patch_error}"
    return True, None


def send_line_message_for_event(
    event: dict,
    meeting_url: str,
    share_message: str,
    line_sender_url: Optional[str],
    line_sender_token: Optional[str],
) -> Tuple[bool, bool, Optional[str], Optional[str]]:
    latest_event, latest_error = gws_event_get(event.get("calendar_id", CALENDAR_ID), event.get("event_id"))
    if latest_error:
        return False, False, None, f"GWS get 失敗: {latest_error}"

    latest_description = (latest_event or {}).get("description") or event.get("description")
    line_user_id = extract_line_user_id(latest_description, latest_event)
    if not line_user_id:
        print(
            f"[LINE] 送信対象なし: {event.get('title', '（タイトルなし）')}",
            file=sys.stderr,
            flush=True,
        )
        return False, False, None, None

    if was_line_message_sent(latest_event, line_user_id, meeting_url):
        print(
            f"[LINE] 送信済みスキップ: {event.get('title', '（タイトルなし）')} uid={line_user_id}",
            file=sys.stderr,
            flush=True,
        )
        return True, True, line_user_id, None

    if not line_sender_url:
        return False, False, line_user_id, "PROLINE_MESSAGE_SENDER_URL または LINE_MESSAGE_SENDER_URL が未設定です"

    sent, send_error = send_line_message(line_sender_url, line_user_id, share_message, line_sender_token)
    if not sent:
        return False, False, line_user_id, send_error

    marked, mark_error = mark_line_message_sent(event, line_user_id, meeting_url)
    if not marked:
        return False, False, line_user_id, mark_error

    print(
        f"[LINE] 送信完了: {event.get('title', '（タイトルなし）')} uid={line_user_id}",
        file=sys.stderr,
        flush=True,
    )
    return True, False, line_user_id, None


def ensure_zoom_link_with_verification(
    event: dict,
    zoom_contexts: Dict[str, ZoomAccountContext],
    settings: DailySummarySettings,
    account_key: str,
) -> Tuple[Optional[str], Optional[str], List[str]]:
    """Zoom URL の作成・説明欄反映・再取得検証までを最大3回試す"""
    context = ensure_zoom_context_ready(zoom_contexts, settings, account_key)
    account_label = context.config.label
    reasons: List[str] = []
    stale_delete_urls: set[str] = set()
    current_url = extract_meeting_url(event.get("description"))
    if current_url:
        reusable, reusable_reason = is_reusable_zoom_url(
            current_url,
            context.meetings,
            event["title"],
            event.get("start_iso"),
        )
        if reusable:
            meeting_id = extract_zoom_meeting_id(current_url)
            share_message = build_zoom_share_message(
                event["title"],
                event["start"],
                event["end"],
                current_url,
                meeting_id,
            )
            updated, update_error = update_calendar_description(
                event,
                current_url,
                share_message,
                meeting_id,
                account_key=account_key,
            )
            if not updated and update_error:
                reasons.append(f"説明欄正規化失敗: {update_error}")
                print(
                    f"[Zoom:{account_label}] 説明欄正規化失敗（{event.get('title', '（タイトルなし）')}）: {update_error}",
                    file=sys.stderr,
                )
            log_zoom_ready(event["title"], current_url, "existing_description")
            return current_url, share_message, reasons
        stale_delete_urls.add(current_url)
        reasons.append(f"既存URL再利用不可: {reusable_reason}")
        print(
            f"[Zoom:{account_label}] 説明欄の既存URLは stale 扱いにします（{event.get('title', '（タイトルなし）')}）: {reusable_reason}",
            file=sys.stderr,
        )

    if not context.token:
        token_error = context.token_error or "Zoom トークンが取得できないため新規発行できません"
        return None, None, [token_error]
    if not event.get("start_iso"):
        return None, None, ["開始時刻がないため Zoom ミーティングを作成できません"]

    for attempt in range(1, MAX_ZOOM_VERIFICATION_ATTEMPTS + 1):
        attempt_prefix = f"{attempt}回目"
        acquired, latest_event, lock_reason = try_acquire_zoom_creation_lock(
            event,
            context.meetings,
            account_key,
            account_label,
        )
        latest_url = resolve_calendar_zoom_url(latest_event, event.get("description"))
        meeting_id = (((latest_event or {}).get("extendedProperties") or {}).get("private") or {}).get(ZOOM_MEETING_ID_KEY)
        meeting_url = None

        if latest_url:
            reusable, reusable_reason = is_reusable_zoom_url(
                latest_url,
                context.meetings,
                event["title"],
                event.get("start_iso"),
            )
            if reusable:
                meeting_url = latest_url
                if not meeting_id:
                    meeting_id = extract_zoom_meeting_id(meeting_url)
                print(f"[Zoom:{account_label}] カレンダー上の既存URLを再利用: {event['title']}")
            else:
                stale_delete_urls.add(latest_url)
                reasons.append(f"{attempt_prefix}: 既存URL再利用不可: {reusable_reason}")

        if not meeting_url and acquired:
            meeting_url = find_existing_zoom_meeting(
                context.meetings,
                event["title"],
                event["start_iso"],
            )
            if meeting_url:
                meeting_id = extract_zoom_meeting_id(meeting_url)
                print(f"[Zoom:{account_label}] 既存ミーティング再利用: {event['title']}")
            else:
                meeting_url, meeting_id, create_error = create_zoom_meeting(
                    context.token,
                    event["title"],
                    event["start_iso"],
                    event.get("duration", 60),
                    account_label,
                    context.config.host_user_id,
                )
                if create_error:
                    reasons.append(f"{attempt_prefix}: {create_error}")
                    continue
                if meeting_url:
                    meetings, list_error = list_zoom_meetings(
                        context.token,
                        account_label,
                        context.config.host_user_id,
                    )
                    context.meetings = meetings
                    context.meetings_loaded = True
                    if list_error:
                        reasons.append(f"{attempt_prefix}: {list_error}")
        elif not meeting_url:
            if lock_reason:
                reasons.append(f"{attempt_prefix}: {lock_reason}")
            else:
                reasons.append(f"{attempt_prefix}: Zoom 作成ロックを取得できませんでした")
            continue

        if not meeting_url:
            reasons.append(f"{attempt_prefix}: Zoom URL を取得できませんでした")
            continue

        share_message = build_zoom_share_message(
            event["title"],
            event["start"],
            event["end"],
            meeting_url,
            meeting_id,
        )
        updated, update_error = update_calendar_description(
            event,
            meeting_url,
            share_message,
            meeting_id,
            account_key=account_key,
        )
        if not updated:
            reasons.append(f"{attempt_prefix}: {update_error}")
            continue

        verified, resolved_url, verify_error = verify_zoom_link(event, meeting_url)
        if verified:
            final_url = resolved_url or meeting_url
            cleanup_errors = cleanup_duplicate_zoom_meetings(
                zoom_contexts,
                settings,
                account_key,
                event["title"],
                event["start_iso"],
                final_url,
                stale_delete_urls,
            )
            if cleanup_errors:
                reasons.extend(cleanup_errors)
            log_zoom_ready(event["title"], final_url, "verified")
            return final_url, build_zoom_share_message(
                event["title"],
                event["start"],
                event["end"],
                final_url,
                meeting_id or extract_zoom_meeting_id(final_url),
            ), reasons

        reasons.append(f"{attempt_prefix}: {verify_error}")

    return None, None, reasons


# ── Discord ─────────────────────────────────────────────────────

def send_discord(webhook_url: str, content: str) -> None:
    """Discord Webhook へメッセージを送る（2000 文字制限あり）"""
    preview = content.splitlines()[0][:80] if content else "(empty)"
    print(f"[Discord] 送信開始: {preview}", file=sys.stderr, flush=True)
    data = json.dumps({"content": content[:2000]}).encode()
    req = urllib.request.Request(
        webhook_url, data=data,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "DiscordBot (https://github.com, 1.0)",
        }
    )
    urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_SEC)
    time.sleep(0.5)   # レート制限対策
    print(f"[Discord] 送信完了: {preview}", file=sys.stderr, flush=True)


# ── メイン ──────────────────────────────────────────────────────

def main() -> None:
    settings = load_daily_summary_settings()

    # Webhook URL: 環境変数 → 設定ファイル の順で読む
    webhook_url = os.environ.get("DISCORD_DAILY_WEBHOOK")
    if not webhook_url:
        webhook_url = json.loads(settings.webhook_config_path.read_text())["url"]

    # 標準入力からイベント JSON を受け取る
    raw = sys.stdin.read().strip()
    if not raw:
        print("[ERROR] 標準入力にデータがありません", file=sys.stderr)
        sys.exit(1)
    data = json.loads(raw)

    date_str = data.get("date", datetime.now().strftime("%Y-%m-%d"))
    skip_discord_summary = bool(data.get("skip_discord_summary"))
    events_raw: List[dict] = data.get("events", [])

    all_day_titles = [e["title"] for e in events_raw if e.get("allDay")]
    timed_events   = [e for e in events_raw if not e.get("allDay")]

    line_sender_url = resolve_first_env(*LINE_SENDER_URL_ENV_KEYS)
    line_sender_token = resolve_first_env(*LINE_SENDER_TOKEN_ENV_KEYS)
    zoom_contexts: Dict[str, ZoomAccountContext] = {}

    # 各イベントに Zoom URL を付与し、必要なら LINE 送信する
    processed = []
    zoom_failures: List[dict] = []
    line_failures: List[dict] = []
    for ev in timed_events:
        account_key = resolve_zoom_account_key(ev.get("title"), settings)
        account_config = get_zoom_account_config(settings, account_key)
        print(
            f"[Event] 開始: {ev['title']} {ev.get('start')}〜{ev.get('end')} / Zoom={account_config.label}",
            file=sys.stderr,
            flush=True,
        )
        original_description = ev.get("description") or ""
        legacy_host_zoom_url = extract_legacy_host_zoom_url(original_description)
        if legacy_host_zoom_url:
            print(
                f"[Event] 既存ホストURLを優先: {ev['title']} / {legacy_host_zoom_url}",
                file=sys.stderr,
                flush=True,
            )
            print(
                f"[Progress] 外部Zoom維持: {ev['title']} / url={legacy_host_zoom_url}",
                file=sys.stderr,
                flush=True,
            )
            processed.append({
                **ev,
                "description": original_description,
                "meeting_url": None,
                "zoom_share_message": None,
                "zoom_failure_reasons": [],
                "zoom_account_key": account_key,
                "zoom_account_label": f"{account_config.label}（外部管理）",
                "line_user_id": None,
                "line_message_sent": False,
            })
            print(f"[Event] 完了: {ev['title']}", file=sys.stderr, flush=True)
            continue
        initial_meeting_url = extract_meeting_url(ev.get("description"))
        meeting_url = None
        zoom_share_message = None
        failure_reasons: List[str] = []
        line_user_id = None
        line_message_sent = False

        if ev.get("start_iso") or initial_meeting_url:
            meeting_url, zoom_share_message, failure_reasons = ensure_zoom_link_with_verification(
                ev,
                zoom_contexts,
                settings,
                account_key,
            )
            if not meeting_url:
                zoom_failures.append({
                    "title": ev["title"],
                    "start": ev.get("start"),
                    "end": ev.get("end"),
                    "zoom_account_label": account_config.label,
                    "reasons": failure_reasons or ["Zoom URL を検証済み状態にできませんでした"],
                })
        elif initial_meeting_url:
            meeting_url = initial_meeting_url
            zoom_share_message = build_zoom_share_message(
                ev["title"],
                ev["start"],
                ev["end"],
                meeting_url,
                extract_zoom_meeting_id(meeting_url),
            )

        if meeting_url and zoom_share_message:
            line_success, line_skipped, line_user_id, line_error = send_line_message_for_event(
                ev,
                meeting_url,
                zoom_share_message,
                line_sender_url,
                line_sender_token,
            )
            line_message_sent = line_success and not line_skipped
            if line_error:
                line_failures.append({
                    "title": ev["title"],
                    "start": ev.get("start"),
                    "end": ev.get("end"),
                    "line_user_id": line_user_id,
                    "reasons": [line_error],
                })

        processed.append({
            **ev,
            "description": original_description,
            "meeting_url": meeting_url,
            "zoom_share_message": zoom_share_message,
            "zoom_failure_reasons": failure_reasons,
            "zoom_account_key": account_key,
            "zoom_account_label": account_config.label,
            "line_user_id": line_user_id,
            "line_message_sent": line_message_sent,
        })
        print(f"[Event] 完了: {ev['title']}", file=sys.stderr, flush=True)

    if zoom_failures:
        error_report = build_zoom_failure_report(date_str, zoom_failures)
        send_discord(webhook_url, error_report)
        print(f"[ERROR] Zoom リンク発行失敗: {len(zoom_failures)} 件", file=sys.stderr)
        sys.exit(1)

    if line_failures:
        error_report = build_line_failure_report(date_str, line_failures)
        send_discord(webhook_url, error_report)
        print(f"[ERROR] LINE 送信失敗: {len(line_failures)} 件", file=sys.stderr)
        sys.exit(1)

    if skip_discord_summary:
        print(
            f"[完了] 手動再実行: 対象{len(processed)}件 / Discord朝サマリー送信なし",
            file=sys.stderr,
        )
        return

    # ── メッセージ 1: 一覧概要 ──
    d = datetime.strptime(date_str, "%Y-%m-%d")
    date_label = f"{d.month}月{d.day}日"

    lines = [f"**Shoの予定（{date_label}）**"]
    if all_day_titles:
        lines.append("【終日】 " + "、".join(all_day_titles))
    if processed:
        lines.append("")
        for i, ev in enumerate(processed, 1):
            icon = "🔗" if ev.get("meeting_url") else "📅"
            lines.append(f"{icon} {i}. {ev['title']}　{ev['start']}〜{ev['end']}")
    elif not all_day_titles:
        lines.append("今日は予定なし！ゆっくりどうぞ 😊")

    send_discord(webhook_url, "\n".join(lines))

    # ── メッセージ 2+: イベント詳細（1件ずつ） ──
    for i, ev in enumerate(processed, 1):
        block = [f"**{i}. {ev['title']}**", f"{ev['start']}〜{ev['end']}"]
        if ev.get("zoom_account_label"):
            block.append(f"Zoom発行アカウント: {ev['zoom_account_label']}")

        desc = (ev.get("description") or "").strip()
        if desc:
            # 長い説明は省略
            block.append(desc[:300] + ("…" if len(desc) > 300 else ""))

        if ev.get("meeting_url"):
            block.append(f"Zoomリンク: {ev['meeting_url']}")
            meeting_id = extract_zoom_meeting_id(ev["meeting_url"])
            if meeting_id:
                block.append(f"ミーティングID: {meeting_id}")
            if ev.get("line_message_sent"):
                block.append("LINE送信: 済み")
            copy_text = ev.get("zoom_share_message") or build_zoom_share_message(
                ev["title"],
                ev["start"],
                ev["end"],
                ev["meeting_url"],
                meeting_id,
            )
            block.append(f"\n```\n{copy_text}\n```")

        send_discord(webhook_url, "\n".join(block))

    print(f"[完了] 送信数: 概要1件 + 詳細{len(processed)}件")


if __name__ == "__main__":
    main()
