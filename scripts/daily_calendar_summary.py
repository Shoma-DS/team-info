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
  echo '<JSON>' | python3 /Users/deguchishouma/team-info/scripts/daily_calendar_summary.py
"""

import json
import sys
import urllib.request
import time
import base64
import re
import pathlib
from datetime import datetime

# ── 設定ファイルのパス ──────────────────────────────────────────
SCRIPT_DIR = pathlib.Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
ZOOM_CREDS_PATH = pathlib.Path.home() / ".config" / "zoom" / "credentials.json"
WEBHOOK_CONFIG_PATH = REPO_ROOT / "personal" / "discord-daily-webhook.json"


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


def create_zoom_meeting(token: str, title: str, start_iso: str, duration_min: int) -> str | None:
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


# ── URL 抽出 ────────────────────────────────────────────────────

_URL_PATTERNS = [
    r'https://[\w.-]*zoom\.us/j/[\w?=&%-]+',
    r'https://meet\.google\.com/[\w-]+',
]

def extract_meeting_url(description: str | None) -> str | None:
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
    events_raw: list[dict] = data.get("events", [])

    all_day_titles = [e["title"] for e in events_raw if e.get("allDay")]
    timed_events   = [e for e in events_raw if not e.get("allDay")]

    # Zoom トークン取得（時刻付き予定がある場合のみ）
    zoom_token: str | None = None
    if timed_events:
        try:
            zoom_token = get_zoom_token()
            print("[Zoom] 認証成功")
        except Exception as e:
            print(f"[Zoom] 認証失敗（Zoom なしで続行）: {e}", file=sys.stderr)

    # 各イベントに Zoom URL を付与
    processed = []
    for ev in timed_events:
        meeting_url = extract_meeting_url(ev.get("description"))
        if not meeting_url and zoom_token and ev.get("start_iso"):
            meeting_url = create_zoom_meeting(
                zoom_token,
                ev["title"],
                ev["start_iso"],
                ev.get("duration", 60),
            )
        processed.append({**ev, "meeting_url": meeting_url})

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
            copy_text = "\n".join([
                "お世話になっております。",
                f"本日 {ev['start']}〜{ev['end']} の「{ev['title']}」の会議リンクをお送りします。",
                "",
                ev["meeting_url"],
                "",
                "よろしくお願いいたします。",
            ])
            block.append(f"\n```\n{copy_text}\n```")

        send_discord(webhook_url, "\n".join(block))

    print(f"[完了] 送信数: 概要1件 + 詳細{len(processed)}件")


if __name__ == "__main__":
    main()
