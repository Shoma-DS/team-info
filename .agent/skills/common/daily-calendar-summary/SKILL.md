---
name: daily-calendar-summary
description: 当日のGoogleカレンダー予定を取得し、Zoom URLを付与してDiscordへ朝の予定サマリーを送信する。Remote Triggerで毎朝8時に自動実行。
---

# daily-calendar-summary スキル

## 役割
- `syouma1674@gmail.com` のGoogleカレンダーから当日の予定を取得
- 既存のZoom/Meet URLを抽出、なければZoom APIで自動作成
- Discordへ概要1件 + イベント詳細1件ずつ送信

## ファイル構成

| ファイル | 役割 |
|---------|------|
| `$TEAM_INFO_ROOT/scripts/daily_calendar_summary.py` | Zoom API + Discord 送信の本体 |
| `$TEAM_INFO_ROOT/personal/discord-daily-webhook.json` | Discord Webhook URL（gitignore済み） |
| `~/.config/zoom/credentials.json` | Zoom OAuth 認証情報 |

## 実行手順

### Step 1: 当日の日付を確認（JST）
実行時の日付を `YYYY-MM-DD` 形式で取得する。

### Step 2: Googleカレンダーから予定を取得
`gcal_list_events` を使って取得する。

- calendarId: `syouma1674@gmail.com`
- timeMin: `{date}T00:00:00`
- timeMax: `{date}T23:59:59`
- timeZone: `Asia/Tokyo`
- condenseEventDetails: false

各イベントから以下を収集する:
- `title`: イベントタイトル（summary）
- `start`: 開始時刻 HH:MM（終日なら null）
- `end`: 終了時刻 HH:MM（終日なら null）
- `start_iso`: 開始時刻 UTC ISO8601 形式（例: `2026-04-04T01:00:00Z`）
  - JST → UTC は `-9h` で変換（例: 10:00 JST → 01:00:00Z）
- `duration`: 所要時間（分）。end - start で計算、不明なら 60
- `description`: イベントの説明文（そのまま渡す）
- `allDay`: 終日フラグ（boolean）

### Step 3: JSONを組み立ててPythonスクリプトに渡す

以下のBashコマンドを実行する（JSONは実際のイベントデータで置き換え、`CREDENTIALS_HERE` の部分はプロンプトで渡された値に差し替えること）:

```bash
python3 - <<'PYEOF' | DISCORD_DAILY_WEBHOOK="WEBHOOK_URL_HERE" ZOOM_ACCOUNT_ID="ACCOUNT_ID_HERE" ZOOM_CLIENT_ID="CLIENT_ID_HERE" ZOOM_CLIENT_SECRET="CLIENT_SECRET_HERE" python3 ./scripts/daily_calendar_summary.py
import json
events = [
    # 収集したイベントデータをここに入れる
    # 例:
    # {
    #   "title": "ミーティング",
    #   "start": "10:00",
    #   "end": "11:00",
    #   "start_iso": "2026-04-04T01:00:00Z",
    #   "duration": 60,
    #   "description": "...",
    #   "allDay": False
    # }
]
print(json.dumps({"date": "YYYY-MM-DD", "events": events}, ensure_ascii=False))
PYEOF
```

- `date` は実行日の JST 日付（`YYYY-MM-DD`）に置き換える
- 予定が0件の場合も `events: []` で実行すること（「予定なし」メッセージが送信される）

## Discordメッセージの構成

1. **概要メッセージ**（1件）
   - 日付ヘッダー
   - 終日予定一覧
   - 時刻付き予定の番号リスト（🔗=会議URL付き、📅=なし）

2. **詳細メッセージ**（イベントごと）
   - タイトル・時刻
   - 説明文（300文字まで）
   - 会議リンク（コピペで相手に送れる文面付きコードブロック）

## Remote Trigger 設定

**スケジュール**: 毎日 8:00 JST（`0 23 * * *` UTC）  
**リポジトリ**: Shoma-DS/team-info  
**コネクタ**: Google Calendar

### Remote Trigger 手順欄テンプレート

```
You are Shoma's daily briefing assistant. Run every morning to send today's schedule to Discord.

Read and follow this skill file exactly:
/Users/deguchishouma/team-info/.agent/skills/common/daily-calendar-summary/SKILL.md

Execute all steps even if the calendar is empty.
```

## トラブルシューティング

| 症状 | 原因 | 対処 |
|-----|------|------|
| `HTTP Error 403` on Discord | Webhook URL が無効 | `personal/discord-daily-webhook.json` の URL を更新 |
| `[Zoom] 認証失敗` | credentials.json の期限切れ | Zoom App で Server-to-Server OAuth を再発行 |
| イベントが取得できない | calendarId 誤り | `syouma1674@gmail.com` を使用しているか確認 |
| スクリプトが見つからない | パス誤り | `$TEAM_INFO_ROOT` が正しく設定されているか確認 |
