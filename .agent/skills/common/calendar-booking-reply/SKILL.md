---
name: calendar-booking-reply
description: 候補日時メッセージから1件を選び、Googleカレンダーの空き確認と予定作成を行い、相手へ送る返信文をコードブロックで返す。日程調整、候補からの本予約、返信文作成、仮予約運用に使う。
---

# Calendar Booking Reply

## 役割
- 相手から届いた候補日時を具体日付・曜日・時刻へ正規化する
- Googleカレンダーの実予定を確認し、重ならない候補を選ぶ
- ユーザーの許可方針に沿ってGoogleカレンダーへ予定を作成する
- 相手にそのまま送れる返信文をコードブロックで返す

## 入口
- Slash command: `/booking`
- Codex prompt: `/prompts:booking`
- Gemini command: `/booking`
- Claude Code wrapper: `.claude/commands/booking.md`

## 必須確認
予定作成に不足がある場合は、最小限だけ確認する。
- 予定タイトル（毎回必ず確認する。デフォルトタイトルで代用しない）
- 所要時間（未指定なら60分）
- 対象カレンダー（未指定なら `primary`）
- 場所・オンラインURL（未指定なら空欄でよい）

Googleカレンダーの読み書きは外部サービスへの通信を含むため、標準では実行前に日本語で確認し、次の4リスクを%で示す。
- パスワードや秘密鍵が外に漏れる可能性
- 外部サーバーにデータが送られる可能性
- 悪意あるコードが勝手に動く可能性
- PCの設定が書き換わる可能性

ただし、ユーザーが同一依頼内で「承認不要」「リスク提示不要」「そのまま作成して」などと明示した場合は、以後のこのスキル内の定型リスク提示と都度承認を省略してよい。省略できるのは、候補確認、予定作成、仮予約作成、仮予約の本予約化など、依頼目的に直接含まれるGoogleカレンダー操作に限る。

次の場合は省略指定があっても止めて確認する。
- 削除対象が複数あり、対象が曖昧
- 予定タイトル、日時、カレンダーIDのいずれかが不明確
- 候補外の日時へ作成しようとしている
- 秘密情報、個人情報、外部送信先が想定より増える
- repo の `AGENTS.md` や上位システム指示が確認を必須としている

## 標準判断
- 年が書かれていない日付は、現在日付から見て直近の未来日付として扱う
- 曜日が本文と暦で矛盾する場合は、必ず具体日付で確認する
- 「19:00以降」「20:00以降」は、未指定なら開始時刻をそのまま `19:00` / `20:00` にする
- 候補が複数空いている場合は、原則として最も早い空き候補を選ぶ
- ただし既存予定と近すぎる、同日に予定が詰まる、明らかに不自然な候補は避ける
- 予定タイトルはユーザーに毎回確認し、未指定のまま作成しない
- 返信文は敬体で短く、相手の文面に合わせる

## 手順
1. 候補日時を `YYYY-MM-DD HH:MM-HH:MM` に正規化する
2. `gws calendar events list` または既存 helper で対象期間の予定を読む
3. 所要時間ぶん空いている候補を選ぶ
4. 予定タイトルと許可方針を確認する。省略指定がなければ、予定作成前にリスク提示つきでユーザー承認を取る
5. 許可済みなら、`gws calendar events insert` で作成する
6. 作成結果と返信文を返す

## gws 例
予定確認:

```bash
gws calendar events list --params '{"calendarId":"primary","timeMin":"2026-06-05T00:00:00+09:00","timeMax":"2026-06-14T00:00:00+09:00","singleEvents":true,"orderBy":"startTime","timeZone":"Asia/Tokyo"}'
```

予定作成:

```bash
gws calendar events insert --params '{"calendarId":"primary"}' --json '{"summary":"予定タイトル","start":{"dateTime":"2026-06-05T19:00:00+09:00","timeZone":"Asia/Tokyo"},"end":{"dateTime":"2026-06-05T20:00:00+09:00","timeZone":"Asia/Tokyo"},"reminders":{"useDefault":true}}'
```

複数仮予約や返答後の本予約化が必要な場合は、既存の補助スクリプトを使う。

```bash
python "$TEAM_INFO_ROOT/.agent/skills/personal/deguchishouma/gws-calendar-booking-reply/scripts/manage_candidate_holds.py"
```

## 返答フォーマット
- 作成した予定: `YYYY年M月D日（曜）HH:MM-HH:MM`
- カレンダー作成結果: 成功 / 未実行 / 失敗
- 返信文:

```text
お世話になります。

それでは、6月5日（金）19:00からお願いいたします。

当日はよろしくお願いいたします。
```
