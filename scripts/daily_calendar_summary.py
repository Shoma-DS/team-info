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
import urllib.request
import time
import base64
import re
import os
import pathlib
import subprocess
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Tuple
import unicodedata

# ── 設定ファイルのパス ──────────────────────────────────────────
SCRIPT_DIR = pathlib.Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
ZOOM_CREDS_PATH = pathlib.Path.home() / ".config" / "zoom" / "credentials.json"
CALENDAR_ID = "primary"
ZOOM_MESSAGE_HEADER = "[team-info] Zoom情報"
GWS_BACKEND = "file"
GWS_BACKEND_CANDIDATES = ("file", "keyring")
ZOOM_STATUS_KEY = "team-info.zoom-status"
ZOOM_RUN_ID_KEY = "team-info.zoom-run-id"
ZOOM_URL_KEY = "team-info.zoom-url"
ZOOM_MEETING_ID_KEY = "team-info.zoom-meeting-id"
MAX_ZOOM_VERIFICATION_ATTEMPTS = 3
LINE_SENDER_URL_ENV_KEYS = ("PROLINE_MESSAGE_SENDER_URL", "LINE_MESSAGE_SENDER_URL")
LINE_SENDER_TOKEN_ENV_KEYS = ("PROLINE_MESSAGE_SENDER_TOKEN", "LINE_MESSAGE_SENDER_TOKEN")
LINE_STATUS_KEY = "team-info.line-status"
LINE_UID_KEY = "team-info.line-uid"
LINE_SENT_URL_KEY = "team-info.line-sent-url"


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


def resolve_first_env(*keys: str) -> Optional[str]:
    for key in keys:
        value = os.environ.get(key)
        if value:
            return value
    return None


# ── Zoom API ────────────────────────────────────────────────────

def get_zoom_token() -> str:
    """Server-to-Server OAuth でアクセストークンを取得する（env vars → 設定ファイルの順）"""
    account_id = os.environ.get("ZOOM_ACCOUNT_ID")
    client_id   = os.environ.get("ZOOM_CLIENT_ID")
    client_secret = os.environ.get("ZOOM_CLIENT_SECRET")
    if not all([account_id, client_id, client_secret]):
        creds = json.loads(ZOOM_CREDS_PATH.read_text())
        account_id    = creds["account_id"]
        client_id     = creds["client_id"]
        client_secret = creds["client_secret"]
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
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())["access_token"]


def create_zoom_meeting(token: str, title: str, start_iso: str, duration_min: int) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Zoom ミーティングを作成して join_url と meeting id を返す。失敗時は理由も返す"""
    url = "https://api.zoom.us/v2/users/me/meetings"
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
        with urllib.request.urlopen(req) as resp:
            payload = json.loads(resp.read())
            meeting_id = str(payload.get("id")) if payload.get("id") else None
            return payload["join_url"], meeting_id, None
    except Exception as e:
        reason = f"Zoom ミーティング作成失敗: {e}"
        print(f"[Zoom] {reason}（{title}）", file=sys.stderr)
        return None, None, reason


def list_zoom_meetings(token: str) -> Tuple[list[dict], Optional[str]]:
    """Zoom の scheduled meetings を取得する"""
    url = "https://api.zoom.us/v2/users/me/meetings?type=scheduled&page_size=300"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            return data.get("meetings", []), None
    except Exception as e:
        reason = f"既存ミーティング取得失敗: {e}"
        print(f"[Zoom] {reason}", file=sys.stderr)
        return [], reason


def delete_zoom_meeting(token: str, meeting_id: str) -> Optional[str]:
    """Zoom の scheduled meeting を削除する。成功時は None を返す"""
    url = f"https://api.zoom.us/v2/meetings/{meeting_id}"
    req = urllib.request.Request(
        url,
        method="DELETE",
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(req):
            return None
    except Exception as e:
        reason = f"重複 Zoom ミーティング削除失敗: {e}"
        print(f"[Zoom] {reason}（meeting_id={meeting_id}）", file=sys.stderr)
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


def cleanup_duplicate_zoom_meetings(
    token: Optional[str],
    meetings: List[dict],
    title: str,
    start_iso: str,
    keep_url: str,
    extra_delete_ids: Optional[set[str]] = None,
) -> Tuple[List[dict], List[str]]:
    """確定した meeting 以外の重複 scheduled meetings を削除する"""
    if not token:
        return meetings, ["Zoom トークンがないため重複ミーティングを削除できません"]

    keep_id = extract_zoom_meeting_id(keep_url)
    delete_ids: set[str] = set(extra_delete_ids or set())
    for meeting in list_matching_zoom_meetings(meetings, title, start_iso):
        meeting_id = str(meeting.get("id") or "")
        if meeting_id and meeting_id != keep_id:
            delete_ids.add(meeting_id)

    if keep_id in delete_ids:
        delete_ids.remove(keep_id)

    errors: List[str] = []
    if not delete_ids:
        return meetings, errors

    for meeting_id in sorted(delete_ids):
        delete_error = delete_zoom_meeting(token, meeting_id)
        if delete_error:
            errors.append(delete_error)
        else:
            print(f"[Zoom] 重複ミーティング削除: {meeting_id}")

    remaining = [meeting for meeting in meetings if str(meeting.get("id") or "") not in delete_ids]
    return remaining, errors


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
        with urllib.request.urlopen(req) as resp:
            response_text = resp.read().decode("utf-8", errors="replace")
        try:
            response_json = json.loads(response_text)
        except json.JSONDecodeError:
            response_json = None
        if response_json and response_json.get("ok") is False:
            return False, response_json.get("error") or "LINE 送信先がエラーを返しました"
        return True, None
    except Exception as e:
        return False, f"LINE 送信失敗: {e}"


# ── Google Calendar via GWS CLI ────────────────────────────────

def gws_env() -> Dict[str, str]:
    env = dict(os.environ)
    env["GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND"] = resolve_gws_backend()
    return env


def auth_status_for_backend(backend: str) -> Optional[dict]:
    env = dict(os.environ)
    env["GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND"] = backend
    result = subprocess.run(
        ["gws", "auth", "status"],
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


def gws_event_patch(calendar_id: str, event_id: str, body: dict) -> Tuple[bool, Optional[str]]:
    """GWS CLI でカレンダーイベントを patch する"""
    result = subprocess.run(
        [
            "gws", "calendar", "events", "patch",
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
    )
    if result.returncode != 0:
        stderr = result.stderr.strip() or "unknown error"
        print(f"[Google Calendar] GWS patch 失敗: {stderr}", file=sys.stderr)
        return False, stderr
    return True, None


def gws_event_get(calendar_id: str, event_id: str) -> Tuple[Optional[dict], Optional[str]]:
    """GWS CLI でカレンダーイベントを取得する"""
    result = subprocess.run(
        [
            "gws", "calendar", "events", "get",
            "--params", json.dumps({
                "calendarId": calendar_id,
                "eventId": event_id,
            }, ensure_ascii=False),
        ],
        text=True,
        capture_output=True,
        env=gws_env(),
    )
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


def try_acquire_zoom_creation_lock(event: dict, zoom_meetings: List[dict]) -> Tuple[bool, Optional[dict], Optional[str]]:
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
            f"[Zoom] 既存URLを stale 扱いにして再発行します（{event.get('title', '（タイトルなし）')}）: {reusable_reason}",
            file=sys.stderr,
        )

    run_id = str(uuid.uuid4())
    patch_body = merge_private_properties(latest, {
        ZOOM_STATUS_KEY: "creating",
        ZOOM_RUN_ID_KEY: run_id,
    })
    patched, patch_error = gws_event_patch(calendar_id, event_id, patch_body)
    if not patched:
        return False, latest, f"GWS patch 失敗: {patch_error}"

    current, current_error = gws_event_get(calendar_id, event_id)
    if current_error:
        return False, current, f"GWS get 再取得失敗: {current_error}"
    current_private = ((current or {}).get("extendedProperties") or {}).get("private") or {}
    current_description = (current or {}).get("description") or latest_description
    current_url = extract_meeting_url(current_description)
    if current_url:
        event["description"] = current_description
        return False, current, None

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
            if stripped.startswith("Zoom会議室開始URL:"):
                continue
            if stripped.startswith("Zoom開始URL（ホスト、主催者）:"):
                continue
            if stripped.startswith("Zoom参加URL（ゲスト、予約者）:"):
                continue
            if stripped.startswith("※プロラインフリーで予約して作成されたスケジュール"):
                continue
            if stripped.startswith("https://"):
                continue
            if stripped == "":
                continue
            skipping_proline_footer = False
        if stripped.startswith("Zoom会議室開始URL:"):
            continue
        if stripped.startswith("Zoom開始URL（ホスト、主催者）:"):
            continue
        if stripped.startswith("Zoom参加URL（ゲスト、予約者）:"):
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


def update_calendar_description(event: dict, meeting_url: str, share_message: str, meeting_id: Optional[str] = None) -> Tuple[bool, Optional[str]]:
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
    line_uid = extract_line_user_id(current_description, latest)
    patch_body = {"description": new_description}
    private_updates = {
        ZOOM_STATUS_KEY: "created",
        ZOOM_URL_KEY: meeting_url,
        ZOOM_MEETING_ID_KEY: meeting_id or "",
    }
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
        body.append(f"{index}. {title} ({start}〜{end})")
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
        return False, False, None, None

    if was_line_message_sent(latest_event, line_user_id, meeting_url):
        return True, True, line_user_id, None

    if not line_sender_url:
        return False, False, line_user_id, "PROLINE_MESSAGE_SENDER_URL または LINE_MESSAGE_SENDER_URL が未設定です"

    sent, send_error = send_line_message(line_sender_url, line_user_id, share_message, line_sender_token)
    if not sent:
        return False, False, line_user_id, send_error

    marked, mark_error = mark_line_message_sent(event, line_user_id, meeting_url)
    if not marked:
        return False, False, line_user_id, mark_error

    return True, False, line_user_id, None


def ensure_zoom_link_with_verification(
    event: dict,
    zoom_token: Optional[str],
    zoom_meetings: List[dict],
) -> Tuple[Optional[str], Optional[str], List[str], List[dict]]:
    """Zoom URL の作成・説明欄反映・再取得検証までを最大3回試す"""
    reasons: List[str] = []
    stale_delete_ids: set[str] = set()
    current_url = extract_meeting_url(event.get("description"))
    if current_url:
        reusable, reusable_reason = is_reusable_zoom_url(
            current_url,
            zoom_meetings,
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
            return current_url, share_message, reasons, zoom_meetings
        stale_meeting_id = extract_zoom_meeting_id(current_url)
        if stale_meeting_id:
            stale_delete_ids.add(stale_meeting_id)
        reasons.append(f"既存URL再利用不可: {reusable_reason}")
        print(
            f"[Zoom] 説明欄の既存URLは stale 扱いにします（{event.get('title', '（タイトルなし）')}）: {reusable_reason}",
            file=sys.stderr,
        )

    if not zoom_token:
        return None, None, ["Zoom トークンが取得できないため新規発行できません"], zoom_meetings
    if not event.get("start_iso"):
        return None, None, ["開始時刻がないため Zoom ミーティングを作成できません"], zoom_meetings

    for attempt in range(1, MAX_ZOOM_VERIFICATION_ATTEMPTS + 1):
        attempt_prefix = f"{attempt}回目"
        acquired, latest_event, lock_reason = try_acquire_zoom_creation_lock(event, zoom_meetings)
        latest_url = resolve_calendar_zoom_url(latest_event, event.get("description"))
        meeting_id = (((latest_event or {}).get("extendedProperties") or {}).get("private") or {}).get(ZOOM_MEETING_ID_KEY)

        if latest_url:
            reusable, reusable_reason = is_reusable_zoom_url(
                latest_url,
                zoom_meetings,
                event["title"],
                event.get("start_iso"),
            )
            if reusable:
                meeting_url = latest_url
                if not meeting_id:
                    meeting_id = extract_zoom_meeting_id(meeting_url)
                print(f"[Zoom] カレンダー上の既存URLを再利用: {event['title']}")
            else:
                stale_meeting_id = extract_zoom_meeting_id(latest_url)
                if stale_meeting_id:
                    stale_delete_ids.add(stale_meeting_id)
                reasons.append(f"{attempt_prefix}: 既存URL再利用不可: {reusable_reason}")
                meeting_url = None
        elif acquired:
            meeting_url = find_existing_zoom_meeting(
                zoom_meetings,
                event["title"],
                event["start_iso"],
            )
            if meeting_url:
                meeting_id = extract_zoom_meeting_id(meeting_url)
                print(f"[Zoom] 既存ミーティング再利用: {event['title']}")
            else:
                meeting_url, meeting_id, create_error = create_zoom_meeting(
                    zoom_token,
                    event["title"],
                    event["start_iso"],
                    event.get("duration", 60),
                )
                if create_error:
                    reasons.append(f"{attempt_prefix}: {create_error}")
                    continue
                if meeting_url:
                    zoom_meetings, list_error = list_zoom_meetings(zoom_token)
                    if list_error:
                        reasons.append(f"{attempt_prefix}: {list_error}")
        else:
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
        updated, update_error = update_calendar_description(event, meeting_url, share_message, meeting_id)
        if not updated:
            reasons.append(f"{attempt_prefix}: {update_error}")
            continue

        verified, resolved_url, verify_error = verify_zoom_link(event, meeting_url)
        if verified:
            final_url = resolved_url or meeting_url
            zoom_meetings, cleanup_errors = cleanup_duplicate_zoom_meetings(
                zoom_token,
                zoom_meetings,
                event["title"],
                event["start_iso"],
                final_url,
                stale_delete_ids,
            )
            if cleanup_errors:
                reasons.extend(cleanup_errors)
            return final_url, build_zoom_share_message(
                event["title"],
                event["start"],
                event["end"],
                final_url,
                meeting_id or extract_zoom_meeting_id(final_url),
            ), reasons, zoom_meetings

        reasons.append(f"{attempt_prefix}: {verify_error}")

    return None, None, reasons, zoom_meetings


# ── Discord ─────────────────────────────────────────────────────

def send_discord(webhook_url: str, content: str) -> None:
    """Discord Webhook へメッセージを送る（2000 文字制限あり）"""
    data = json.dumps({"content": content[:2000]}).encode()
    req = urllib.request.Request(
        webhook_url, data=data,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "DiscordBot (https://github.com, 1.0)",
        }
    )
    urllib.request.urlopen(req)
    time.sleep(0.5)   # レート制限対策


# ── メイン ──────────────────────────────────────────────────────

def main() -> None:
    # Webhook URL: 環境変数 → 設定ファイル の順で読む
    webhook_url = os.environ.get("DISCORD_DAILY_WEBHOOK")
    if not webhook_url:
        webhook_url = json.loads(WEBHOOK_CONFIG_PATH.read_text())["url"]

    # 標準入力からイベント JSON を受け取る
    raw = sys.stdin.read().strip()
    if not raw:
        print("[ERROR] 標準入力にデータがありません", file=sys.stderr)
        sys.exit(1)
    data = json.loads(raw)

    date_str = data.get("date", datetime.now().strftime("%Y-%m-%d"))
    events_raw: List[dict] = data.get("events", [])

    all_day_titles = [e["title"] for e in events_raw if e.get("allDay")]
    timed_events   = [e for e in events_raw if not e.get("allDay")]

    # Zoom トークン取得（時刻付き予定がある場合のみ）
    zoom_token: Optional[str] = None
    if timed_events:
        try:
            zoom_token = get_zoom_token()
            print("[Zoom] 認証成功")
        except Exception as e:
            print(f"[Zoom] 認証失敗（Zoom なしで続行）: {e}", file=sys.stderr)
    zoom_meetings: List[dict] = []
    if zoom_token:
        zoom_meetings, zoom_meetings_error = list_zoom_meetings(zoom_token)
        if zoom_meetings_error:
            print(f"[Zoom] {zoom_meetings_error}", file=sys.stderr)

    line_sender_url = resolve_first_env(*LINE_SENDER_URL_ENV_KEYS)
    line_sender_token = resolve_first_env(*LINE_SENDER_TOKEN_ENV_KEYS)

    # 各イベントに Zoom URL を付与し、必要なら LINE 送信する
    processed = []
    zoom_failures: List[dict] = []
    line_failures: List[dict] = []
    for ev in timed_events:
        original_description = ev.get("description") or ""
        initial_meeting_url = extract_meeting_url(ev.get("description"))
        meeting_url = initial_meeting_url
        zoom_share_message = None
        failure_reasons: List[str] = []
        line_user_id = None
        line_message_sent = False

        if not meeting_url and ev.get("start_iso"):
            meeting_url, zoom_share_message, failure_reasons, zoom_meetings = ensure_zoom_link_with_verification(
                ev,
                zoom_token,
                zoom_meetings,
            )
            if not meeting_url:
                zoom_failures.append({
                    "title": ev["title"],
                    "start": ev.get("start"),
                    "end": ev.get("end"),
                    "reasons": failure_reasons or ["Zoom URL を検証済み状態にできませんでした"],
                })
        elif meeting_url:
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
            "line_user_id": line_user_id,
            "line_message_sent": line_message_sent,
        })

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
