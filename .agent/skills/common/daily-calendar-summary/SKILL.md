---
name: daily-calendar-summary
description: 当日のGoogleカレンダー予定を取得し、Zoom URLを付与してDiscordへ朝の予定サマリーを送信する。GWS CLI とローカル定期実行で毎朝8時に自動実行。
---

# daily-calendar-summary スキル

## 役割
- `syouma1674@gmail.com` のGoogleカレンダーから当日の予定を取得
- 既存のZoom/Meet URLを抽出、なければZoom APIで自動作成
- Zoom を新規作成した場合は、GWS CLI 経由で Google カレンダーの該当イベント説明欄へ Zoom リンク送信用メッセージを追記
- Discordへ概要1件 + イベント詳細1件ずつ送信

## Codex 実行ポリシー

- Google Calendar の取得と更新は `GWS CLI` で行う
- `gws calendar events list` と `gws calendar events patch` を使い、`googleapiclient` や `calendar_token.json` には依存しない
- 認証方式は `GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND=file` を前提にする
- Codex / launchd / cron からローカル実行できる形を正本とし、Claude のコネクタや Remote Trigger には依存しない
- `gws` が失敗した場合は Discord に誤った内容を送らず、失敗理由だけを短く残して終了する

## ファイル構成

| ファイル | 役割 |
|---------|------|
| `$TEAM_INFO_ROOT/scripts/personal/<account>/daily-calendar-summary/run_daily_summary.py` | GWS CLI で当日の予定を取得し `daily_calendar_summary.py` へ渡す |
| `$TEAM_INFO_ROOT/scripts/daily_calendar_summary.py` | Zoom API + Discord 送信 + GWS CLI による説明欄更新 |
| `$TEAM_INFO_ROOT/personal/<account>/discord/discord-daily-webhook.json` | Discord Webhook URL（gitignore済み） |
| `~/.config/zoom/credentials.json` | Zoom OAuth 認証情報 |
| `~/.config/gws/*` | GWS CLI の認証・OAuth クライアント設定 |

## 実行手順

### Step 1: 当日の日付を確認（JST）
実行時の日付を `YYYY-MM-DD` 形式で取得する。

### Step 2: Googleカレンダーから予定を取得
`gws calendar events list` を使って取得する。

- calendarId: `syouma1674@gmail.com`
- timeMin: `{date}T00:00:00`
- timeMax: `{date}T23:59:59`
- timeZone: `Asia/Tokyo`
- singleEvents: `true`
- orderBy: `startTime`

各イベントから以下を収集する:
- `event_id`: Google カレンダーのイベントID
- `calendar_id`: `primary`
- `title`: イベントタイトル（summary）
- `start`: 開始時刻 HH:MM（終日なら null）
- `end`: 終了時刻 HH:MM（終日なら null）
- `start_iso`: 開始時刻 UTC ISO8601 形式（例: `2026-04-04T01:00:00Z`）
  - JST → UTC は `-9h` で変換（例: 10:00 JST → 01:00:00Z）
- `duration`: 所要時間（分）。end - start で計算、不明なら 60
- `description`: イベントの説明文（そのまま渡す）
- `allDay`: 終日フラグ（boolean）

### Step 3: Pythonスクリプトを直接実行する

以下のように `run_daily_summary.py` を実行する。

```bash
GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND=file \
DISCORD_DAILY_WEBHOOK="WEBHOOK_URL_HERE" \
ZOOM_ACCOUNT_ID="ACCOUNT_ID_HERE" \
ZOOM_CLIENT_ID="CLIENT_ID_HERE" \
ZOOM_CLIENT_SECRET="CLIENT_SECRET_HERE" \
python3 "$TEAM_INFO_ROOT/scripts/personal/<account>/daily-calendar-summary/run_daily_summary.py"
```

- `run_daily_summary.py` が GWS CLI で当日の予定を取得し、`daily_calendar_summary.py` へ JSON を渡す
- 予定が0件の場合も実行すること（「予定なし」メッセージが送信される）
- `daily_calendar_summary.py` は、Zoom を新規作成したイベントについて GWS CLI で Google カレンダー説明欄へ送信用メッセージを追記する

## Discordメッセージの構成

1. **概要メッセージ**（1件）
   - 日付ヘッダー
   - 終日予定一覧
   - 時刻付き予定の番号リスト（🔗=会議URL付き、📅=なし）

2. **詳細メッセージ**（イベントごと）
   - タイトル・時刻
   - 説明文（300文字まで）
   - `Zoomリンク: https://...` をコードブロックとは別項目で明記
   - 会議リンク（コピペで相手に送れる文面付きコードブロック）

## 定期実行設定

**スケジュール**: 毎日 8:00 JST  
**実行方式**: launchd / cron / Codex 側の定期ジョブ  
**依存**: `gws` 認証済み、Zoom 認証済み、Discord Webhook 設定済み

### launchd / cron 実行コマンド例

```bash
export GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND=file
python3 "$TEAM_INFO_ROOT/scripts/personal/<account>/daily-calendar-summary/run_daily_summary.py"
```

## トラブルシューティング

| 症状 | 原因 | 対処 |
|-----|------|------|
| `HTTP Error 403` on Discord | Webhook URL が無効 | `personal/<account>/discord/discord-daily-webhook.json` の URL を更新 |
| `[Zoom] 認証失敗` | credentials.json の期限切れ | Zoom App で Server-to-Server OAuth を再発行 |
| `gws` で認証エラー | keyring backend 不一致 | `GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND=file` を付けて再実行 |
| イベントが取得できない | calendarId 誤り / `gws` 未認証 | `primary` と `gws auth status` を確認 |
| スクリプトが見つからない | パス誤り | `$TEAM_INFO_ROOT` が正しく設定されているか確認 |
