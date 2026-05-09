---
name: daily-calendar-summary
description: 当日のGoogleカレンダー予定を取得し、Zoom URL を付与して LINE 送信と Discord への朝サマリー送信を行う。GWS CLI とローカル定期実行で毎朝8時に自動実行。
---

# daily-calendar-summary スキル

## 役割
- `syouma1674@gmail.com` のGoogleカレンダーから当日の予定を取得
- 既存の Zoom / Meet URL を抽出し、なければ Zoom API で自動作成する
- Google カレンダー説明欄の `uid` を使って LINE / ProLine へ Zoom リンク文面を送る
- Zoom を新規作成した場合は、GWS CLI 経由で Google カレンダーの該当イベント説明欄へ Zoom リンク送信用メッセージを追記し、`location` にも Zoom の join URL を入れる
- 説明欄に古い Zoom URL が残っている場合は Zoom scheduled meetings と照合し、本日の予定でなければ新しいリンクへ差し替える
- 説明欄に `Zoom開始URL（ホスト、主催者）` `Zoom招待URL（友だち用）` `※プロラインフリーで予約して作成されたスケジュール...` などの旧案内文が残っている場合は、`:` と `：` の両方を含めて正規化時に取り除く
- ただし `Zoom開始URL（ホスト、主催者）` や `Zoom会議室開始URL` に実際のホスト用 URL がすでに入っている予定は外部管理扱いにし、新規 Zoom 発行も旧案内文の削除も行わず、そのまま残す
- `Zoom招待URL（友だち用）` など友だち招待用しか残っていない場合だけ、その案内文とプロラインフリー注意書きを消してから通常の Zoom 再判定へ進む
- 新しいリンクを確定した後、同タイトル・同開始時刻で重複した古い Zoom scheduled meeting があれば削除する
- Discord の詳細メッセージには Zoom リンク、ミーティング ID、LINE送信結果を記載する
- Discordへ概要1件 + イベント詳細1件ずつ送信
- 朝サマリー送信が成功した後、当日予定のうち「面接」「2回目」または90分以上の予定を抽出し、取得済みカレンダー情報を `calendar-interview-closing` へ渡して Loom 文字起こし取得とクロージング台本作成に移行する

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
| `/tmp/team-info-daily-summary/calendar-interview-closing-YYYY-MM-DD.json` | 朝通知で取得済みの面接候補予定を `calendar-interview-closing` へ渡す一時JSON |
| `$TEAM_INFO_ROOT/personal/<account>/scripts/daily-calendar-summary/daily_summary_settings.json` | Discord Webhook の参照先と Zoom アカウント振り分け設定 |
| `$TEAM_INFO_ROOT/personal/<account>/scripts/daily-calendar-summary/zoom-credentials/*.json` | 追加した Zoom アカウントごとの Server-to-Server OAuth 資格情報 |
| `$TEAM_INFO_ROOT/personal/<account>/discord/discord-daily-webhook.json` | Discord Webhook URL（gitignore済み） |
| `~/.config/zoom/credentials.json` | Zoom OAuth 認証情報 |
| `~/.config/gws/*` | GWS CLI の認証・OAuth クライアント設定 |

## Zoom アカウント設定

- 予定タイトルは `daily_summary_settings.json` の `zoom_accounts` 上から順に評価し、`title_prefixes` に一致したアカウントで Zoom URL を発行する
- 一致しない予定は `default: true` のアカウントで発行する
- 現在の初期設定では、タイトル先頭が `★` の予定だけ `sugashita` を使い、それ以外は `default` を使う
- `host_user_id` で、その Zoom アカウント内のどのユーザーを会議ホストにするか指定できる。Server-to-Server OAuth では `me` ではなく、原則そのアカウント内ユーザーのメールアドレスまたは Zoom userId を入れる
- 菅下アカウントの資格情報は `zoom-credentials/sugashita.json` に `account_id` / `client_id` / `client_secret` を入れる
- 後からアカウントを増やすときは、資格情報 JSON を1つ追加し、`daily_summary_settings.json` の `zoom_accounts` に1件追記する

設定例:

```json
{
  "key": "tanaka",
  "label": "田中",
  "credentials_file": "zoom-credentials/tanaka.json",
  "host_user_id": "tanaka@example.com",
  "title_prefixes": ["◆", "田中:"]
}
```

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

以下のように `run_daily_summary.py` を実行する。Zoom は原則 `daily_summary_settings.json` に書いた資格情報ファイルを使う。

```bash
DISCORD_DAILY_WEBHOOK="WEBHOOK_URL_HERE" \
PROLINE_MESSAGE_SENDER_URL="WEB_APP_URL_HERE" \
PROLINE_MESSAGE_SENDER_TOKEN="TOKEN_IF_NEEDED" \
python3 "$TEAM_INFO_ROOT/personal/<account>/scripts/daily-calendar-summary/run_daily_summary.py"
```

- `run_daily_summary.py` が GWS CLI で当日の予定を取得し、`daily_calendar_summary.py` へ JSON を渡す
- 予定が0件の場合も実行すること（「予定なし」メッセージが送信される）
- `daily_calendar_summary.py` が成功した後、取得済みの予定から次の候補だけを抽出し、`calendar-interview-closing` を `codex exec` で起動する
  - `summary` または `description` に `面接`
  - `description` に `2回目`
  - `duration` が90分以上
- `calendar-interview-closing` へは `/tmp/team-info-daily-summary/calendar-interview-closing-YYYY-MM-DD.json` を渡す。後続スキルはこの JSON を正本として使い、JSON が読めない場合以外は Google Calendar を再取得しない
- 朝通知だけを検証したい場合は `--skip-interview-closing` を付ける
- `daily_calendar_summary.py` は、Zoom を新規作成したイベントだけでなく、既存 URL を再利用するイベントでも GWS CLI で Google カレンダー説明欄を正規化し、旧式の Zoom / ProLine 案内文を消してから最新の送信用メッセージへ寄せる
- Loom が会議リンクを拾いやすいように、Zoom URL は説明欄だけでなく Google カレンダーの `location` にも入れる。既存 `location` に会場名などがある場合は残したまま、先頭に Zoom URL を置く
- ただしホスト用の実 URL が既に説明欄にある場合は外部管理扱いにして、説明欄も Zoom 会議も触らない
- 説明欄に `uid` または `ユーザーID` があるイベントは、その値を宛先として LINE / ProLine へ同じ Zoom リンク文面を送る
- 同じ `uid` に同じ Zoom URL を送った記録が private extendedProperties にある場合は二重送信しない
- 既定アカウントだけ従来どおり `ZOOM_ACCOUNT_ID` / `ZOOM_CLIENT_ID` / `ZOOM_CLIENT_SECRET` の環境変数でも上書きできる

### Step 4: 日中に未来分だけ手動再実行したい場合

- 毎朝 8:00 の定期実行とは別に、当日途中で再送が必要なときは「本日の現在時刻以降の予定」だけを対象にする
- このときは Discord の朝サマリーを再送せず、説明欄の正規化、Zoom URL の再判定、LINE 送信だけを行う
- 対象判定は JST の現在時刻基準で、`start >= now` の時刻付き予定に限定する
- 手動再実行時も、古い Zoom URL が残っていれば scheduled meetings と照合して stale 判定し、必要なら新規発行と重複削除まで行う

手動再実行コマンド:

```bash
python3 "$TEAM_INFO_ROOT/personal/<account>/scripts/daily-calendar-summary/run_daily_summary.py" --date 2026-05-02 --future-only
```

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
