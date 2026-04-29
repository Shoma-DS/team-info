---
name: daily-calendar-summary
description: 当日のGoogleカレンダー予定を取得し、Zoom URL を付与して LINE 送信と Discord への朝サマリー送信を行う。GWS CLI とローカル定期実行で毎朝8時に自動実行。
---

# daily-calendar-summary スキル

## 役割
- `syouma1674@gmail.com` のGoogleカレンダーから当日の予定を取得
- 既存の Zoom / Meet URL を抽出し、なければ Zoom API で自動作成する
- Google カレンダー説明欄の `uid` を使って LINE / ProLine へ Zoom リンク文面を送る
- Zoom を新規作成した場合は、GWS CLI 経由で Google カレンダーの該当イベント説明欄へ Zoom リンク送信用メッセージを追記する
- 説明欄に古い Zoom URL が残っている場合は Zoom scheduled meetings と照合し、本日の予定でなければ新しいリンクへ差し替える
- 新しいリンクを確定した後、同タイトル・同開始時刻で重複した古い Zoom scheduled meeting があれば削除する
- Discord の詳細メッセージには Zoom リンク、ミーティング ID、LINE送信結果を記載する
- Discordへ概要1件 + イベント詳細1件ずつ送信

## Codex 実行ポリシー

- Google Calendar の取得と更新は `GWS CLI` で行う
- `gws calendar events list` と `gws calendar events patch` を使い、`googleapiclient` や `calendar_token.json` には依存しない
- 認証方式は固定せず、実行時は `file` / `keyring` のうち有効な `gws` 認証を自動選択する
- `file` backend が壊れていても `keyring` backend が有効なら、`gws auth export --unmasked` でローカル専用の OAuth 資格情報ファイルを自動再生成して継続する
- Codex / launchd / cron からローカル実行できる形を正本とし、Claude のコネクタや Remote Trigger には依存しない
- `gws` が失敗した場合は Discord に誤った予定を送らず、認証エラーなら再認証コマンドをコードブロック付きで、それ以外は原因と対処法を送って終了する
- LINE 送信先は Google カレンダー説明欄に含まれる `uid` から取得する
- 説明欄では `uid` だけでなく `ユーザーID` 表記も `uid` と同義として扱う
- `PROLINE_MESSAGE_SENDER_URL` または `LINE_MESSAGE_SENDER_URL` を環境変数で渡し、必要なら `PROLINE_MESSAGE_SENDER_TOKEN` または `LINE_MESSAGE_SENDER_TOKEN` も使う
- 常用する送信先 URL は `~/.config/team-info/env.sh` に `export PROLINE_MESSAGE_SENDER_URL="..."` の形で保存しておく

## ファイル構成

| ファイル | 役割 |
|---------|------|
| `$TEAM_INFO_ROOT/personal/<account>/scripts/daily-calendar-summary/run_daily_summary.py` | GWS CLI で当日の予定を取得し `daily_calendar_summary.py` へ渡す |
| `$TEAM_INFO_ROOT/scripts/daily_calendar_summary.py` | Zoom API + LINE送信 + Discord 送信 + GWS CLI による説明欄更新 |
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
DISCORD_DAILY_WEBHOOK="WEBHOOK_URL_HERE" \
PROLINE_MESSAGE_SENDER_URL="WEB_APP_URL_HERE" \
PROLINE_MESSAGE_SENDER_TOKEN="TOKEN_IF_NEEDED" \
ZOOM_ACCOUNT_ID="ACCOUNT_ID_HERE" \
ZOOM_CLIENT_ID="CLIENT_ID_HERE" \
ZOOM_CLIENT_SECRET="CLIENT_SECRET_HERE" \
python3 "$TEAM_INFO_ROOT/personal/<account>/scripts/daily-calendar-summary/run_daily_summary.py"
```

- `run_daily_summary.py` が GWS CLI で当日の予定を取得し、`daily_calendar_summary.py` へ JSON を渡す
- 予定が0件の場合も実行すること（「予定なし」メッセージが送信される）
- `daily_calendar_summary.py` は、Zoom を新規作成したイベントについて GWS CLI で Google カレンダー説明欄へ送信用メッセージを追記する
- 説明欄に `uid` または `ユーザーID` があるイベントは、その値を宛先として LINE / ProLine へ同じ Zoom リンク文面を送る
- 同じ `uid` に同じ Zoom URL を送った記録が private extendedProperties にある場合は二重送信しない

### Step 4: 日中に未来分だけ手動再実行したい場合

- 毎朝 8:00 の定期実行とは別に、当日途中で再送が必要なときは「本日の現在時刻以降の予定」だけを対象にする
- このときは Discord の朝サマリーを再送せず、説明欄の正規化、Zoom URL の再判定、LINE 送信だけを行う
- 対象判定は JST の現在時刻基準で、`start >= now` の時刻付き予定に限定する
- 手動再実行時も、古い Zoom URL が残っていれば scheduled meetings と照合して stale 判定し、必要なら新規発行と重複削除まで行う

## Discordメッセージの構成

1. **概要メッセージ**（1件）
   - 日付ヘッダー
   - 終日予定一覧
   - 時刻付き予定の番号リスト（🔗=会議URL付き、📅=なし）

2. **詳細メッセージ**（イベントごと）
   - タイトル・時刻
   - 説明文（300文字まで）
   - `Zoomリンク: https://...` をコードブロックとは別項目で明記
   - `ミーティングID: 123 4567 8901` を別項目で明記
   - `LINE送信: 済み` を送信成功時に明記
   - 会議リンク（コピペで相手に送れる文面付きコードブロック）

## 定期実行設定

**スケジュール**: 毎日 8:00 JST  
**実行方式**: launchd / cron / Codex 側の定期ジョブ  
**依存**: `gws` 認証済み、Zoom 認証済み、Discord Webhook 設定済み、LINE送信用 Web App URL 設定済み

### launchd / cron 実行コマンド例

```bash
python3 "$TEAM_INFO_ROOT/personal/<account>/scripts/daily-calendar-summary/run_daily_summary.py"
```

## トラブルシューティング

| 症状 | 原因 | 対処 |
|-----|------|------|
| `HTTP Error 403` on Discord | Webhook URL が無効 | `personal/<account>/discord/discord-daily-webhook.json` の URL を更新 |
| `[Zoom] 認証失敗` | credentials.json の期限切れ | Zoom App で Server-to-Server OAuth を再発行 |
| `LINE送信失敗` | `uid` / `ユーザーID` 不正 / Web App URL 未設定 / GAS 側エラー | Google カレンダー説明欄の `uid` または `ユーザーID` と `PROLINE_MESSAGE_SENDER_URL` を確認し、必要なら GAS の応答を確認 |
| `gws` で認証エラー | backend 不一致 / 保存済み資格情報なし | まず `gws auth status` を確認し、`keyring` が有効なら定期実行で `GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND=file` を固定しない。`file` も必要なら `GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND=file gws auth login -s sheets,drive,calendar` を実行 |
| イベントが取得できない | calendarId 誤り / `gws` 未認証 | `primary` と `gws auth status` を確認 |
| スクリプトが見つからない | パス誤り | `$TEAM_INFO_ROOT` が正しく設定されているか確認 |
