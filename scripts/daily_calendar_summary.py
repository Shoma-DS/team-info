#!/usr/bin/env python3
"""
daily_calendar_summary.py

Googleカレンダーのイベント一覧を標準入力から受け取り、
Zoom ミーティングを作成（必要な場合）して Discord へ投稿する。

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
ZOOM_STATUS_KEY = "team-info.zoom-status"
ZOOM_RUN_ID_KEY = "team-info.zoom-run-id"
ZOOM_URL_KEY = "team-info.zoom-url"


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


# ── Zoom API ────────────────────────────────────────────────────

def get_zoom_token() -> str:
    """Server-to-Server OAuth でアクセストークンを取得する（env vars → 設定ファイルの順）"""
    import os
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


def create_zoom_meeting(token: str, title: str, start_iso: str, duration_min: int) -> Optional[str]:
    """Zoom ミーティングを作成して join_url を返す。失敗時は None"""
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
            return json.loads(resp.read())["join_url"]
    except Exception as e:
        print(f"[Zoom] ミーティング作成失敗（{title}）: {e}", file=sys.stderr)
        return None


def list_zoom_meetings(token: str) -> list[dict]:
    """Zoom の scheduled meetings を取得する"""
    url = "https://api.zoom.us/v2/users/me/meetings?type=scheduled&page_size=300"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            return data.get("meetings", [])
    except Exception as e:
        print(f"[Zoom] 既存ミーティング取得失敗: {e}", file=sys.stderr)
        return []


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


# ── Google Calendar via GWS CLI ────────────────────────────────

def gws_env() -> Dict[str, str]:
    import os

    env = dict(os.environ)
    env.setdefault("GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND", GWS_BACKEND)
    return env


def gws_event_patch(calendar_id: str, event_id: str, body: dict) -> bool:
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
        return False
    return True


def gws_event_get(calendar_id: str, event_id: str) -> Optional[dict]:
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
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print("[Google Calendar] GWS get 応答の JSON 解析に失敗", file=sys.stderr)
        return None


def merge_private_properties(event: Optional[dict], updates: Dict[str, str]) -> dict:
    """既存イベントの private extendedProperties を保持したまま更新する"""
    existing = ((event or {}).get("extendedProperties") or {}).get("private") or {}
    merged = dict(existing)
    merged.update(updates)
    return {"extendedProperties": {"private": merged}}


def try_acquire_zoom_creation_lock(event: dict) -> Tuple[bool, Optional[dict]]:
    """同時実行時に 1 つだけが Zoom 作成に進むようイベント上でロックする"""
    event_id = event.get("event_id")
    calendar_id = event.get("calendar_id", CALENDAR_ID)
    if not event_id:
        return False, None

    latest = gws_event_get(calendar_id, event_id)
    latest_description = (latest or {}).get("description") or event.get("description") or ""
    latest_url = extract_meeting_url(latest_description)
    if latest_url:
        event["description"] = latest_description
        return False, latest

    run_id = str(uuid.uuid4())
    patch_body = merge_private_properties(latest, {
        ZOOM_STATUS_KEY: "creating",
        ZOOM_RUN_ID_KEY: run_id,
    })
    if not gws_event_patch(calendar_id, event_id, patch_body):
        return False, latest

    current = gws_event_get(calendar_id, event_id)
    current_private = ((current or {}).get("extendedProperties") or {}).get("private") or {}
    current_description = (current or {}).get("description") or latest_description
    current_url = extract_meeting_url(current_description)
    if current_url:
        event["description"] = current_description
        return False, current

    return current_private.get(ZOOM_RUN_ID_KEY) == run_id, current


def build_zoom_share_message(title: str, start: str, end: str, meeting_url: str) -> str:
    """相手に送る Zoom リンク文面を返す"""
    return "\n".join([
        "お世話になっております。",
        f"本日 {start}〜{end} の「{title}」の会議リンクをお送りします。",
        "",
        meeting_url,
        "",
        "よろしくお願いいたします。",
    ])


def build_zoom_description_block(meeting_url: str, share_message: str) -> str:
    """説明欄へ追記する Zoom 情報ブロックを返す"""
    return "\n".join([
        ZOOM_MESSAGE_HEADER,
        "Zoom URL:",
        meeting_url,
        "",
        "Zoom URL送信メッセージ:",
        share_message,
    ])


def append_zoom_message(description: Optional[str], meeting_url: str, share_message: str) -> str:
    """既存説明欄へ Zoom URL と送信用メッセージを追記する"""
    base = (description or "").rstrip()
    block = build_zoom_description_block(meeting_url, share_message)
    if block in base:
        return base
    if not base:
        return block
    return f"{base}\n\n{block}"


def update_calendar_description(event: dict, meeting_url: str, share_message: str) -> None:
    """Google カレンダーの説明欄へ Zoom 送信用メッセージを追記する"""
    event_id = event.get("event_id")
    if not event_id:
        return

    calendar_id = event.get("calendar_id", CALENDAR_ID)
    latest = gws_event_get(calendar_id, event_id)
    current_description = (latest or {}).get("description") or event.get("description")
    new_description = append_zoom_message(current_description, meeting_url, share_message)
    patch_body = {"description": new_description}
    patch_body.update(merge_private_properties(latest, {
        ZOOM_STATUS_KEY: "created",
        ZOOM_URL_KEY: meeting_url,
    }))

    try:
        if gws_event_patch(calendar_id, event_id, patch_body):
            print(f"[Google Calendar] 説明欄更新: {event.get('title', '（タイトルなし）')}")
        else:
            print(f"[Google Calendar] 説明欄更新失敗（{event.get('title', '（タイトルなし）')}）", file=sys.stderr)
    except Exception as e:
        print(f"[Google Calendar] 説明欄更新失敗（{event.get('title', '（タイトルなし）')}）: {e}", file=sys.stderr)


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
    import os
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
    zoom_meetings: List[dict] = list_zoom_meetings(zoom_token) if zoom_token else []

    # 各イベントに Zoom URL を付与
    processed = []
    for ev in timed_events:
        original_description = ev.get("description") or ""
        meeting_url = extract_meeting_url(ev.get("description"))
        created_zoom = False
        if not meeting_url and zoom_token and ev.get("start_iso"):
            acquired, latest_event = try_acquire_zoom_creation_lock(ev)
            latest_description = (latest_event or {}).get("description") or ev.get("description") or ""
            latest_meeting_url = extract_meeting_url(latest_description)
            if latest_meeting_url:
                meeting_url = latest_meeting_url
                ev["description"] = latest_description
            elif acquired:
                existing_zoom_url = find_existing_zoom_meeting(
                    zoom_meetings,
                    ev["title"],
                    ev["start_iso"],
                )
                if existing_zoom_url:
                    meeting_url = existing_zoom_url
                    print(f"[Zoom] 既存ミーティング再利用: {ev['title']}")
                else:
                    meeting_url = create_zoom_meeting(
                        zoom_token,
                        ev["title"],
                        ev["start_iso"],
                        ev.get("duration", 60),
                    )
                    created_zoom = bool(meeting_url)
                    if created_zoom:
                        zoom_meetings = list_zoom_meetings(zoom_token)
            else:
                print(f"[Zoom] 重複作成回避: {ev['title']}", file=sys.stderr)

        zoom_share_message = None
        if meeting_url:
            zoom_share_message = build_zoom_share_message(
                ev["title"],
                ev["start"],
                ev["end"],
                meeting_url,
            )

        if meeting_url and zoom_share_message:
            update_calendar_description(ev, meeting_url, zoom_share_message)

        processed.append({
            **ev,
            "description": original_description,
            "meeting_url": meeting_url,
            "zoom_share_message": zoom_share_message,
        })

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
            copy_text = ev.get("zoom_share_message") or build_zoom_share_message(
                ev["title"],
                ev["start"],
                ev["end"],
                ev["meeting_url"],
            )
            block.append(f"\n```\n{copy_text}\n```")

        send_discord(webhook_url, "\n".join(block))

    print(f"[完了] 送信数: 概要1件 + 詳細{len(processed)}件")


if __name__ == "__main__":
    main()
