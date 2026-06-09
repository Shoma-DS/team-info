# ProLine 公式 LINE アカウント GAS 台帳

ProLine の「旧」「新」公式 LINE アカウントで使う GAS をまとめた台帳。
デプロイ URL が変わったり新しい GAS を追加したら、このファイルを同じターンで更新する。

---

## 旧 公式 LINE アカウント

### 1. 友達追加 & フォーム受信（proline-free-referral-sync）

| 項目 | 値 |
| --- | --- |
| ローカル正本 | `GAS/proline/proline-free-referral-sync/` |
| scriptId | `1bEsFW9qhDRTWaN88HilgxXGwh_7l-VXWRTDqAtKznxBeqGn2tI9S2NEX` |
| Apps Script 編集先 | `https://script.google.com/home/projects/1bEsFW9qhDRTWaN88HilgxXGwh_7l-VXWRTDqAtKznxBeqGn2tI9S2NEX/edit` |
| デプロイ URL | `https://script.google.com/macros/s/AKfycbyXPAeDZeHe97EKCkY8Mfy3zFf3mj3Y6dIiUivcKT-ntKlFBF97L3k5dl6mdyJzS8TKQQ/exec` |
| 書き込み先スプレッドシート | `1BQOswkbIBjzMdya5MICAMBcMmrJWd7rXLANPbSDc5m4` |
| 最終デプロイ | 2026-06-09 version 7 |

**機能詳細**

- `GET /?uid=...` → ProLine 友達追加 / ブロック解除のトリガー。`友達追加情報` シートへ upsert する。
- `POST` → `form_8：在宅ワーク面談前アンケート` のフォーム回答を受信してスプレッドシートへ追記する。
- `新旧` 列には **「旧」** を書き込む。
- `ref_code` / `free2` から `アフィリエイター情報` シートで紹介者名を補完する。
- 重複 uid には「重複」ステータス、新規には「1S予定」を自動セット。
- `送信日` カラム名エイリアスに「送信日」を追加（空欄バグ修正済み）。

**ProLine 設定箇所（旧アカウント）**

| イベント | URL |
| --- | --- |
| 友達追加時 | `https://script.google.com/macros/s/AKfycbyXPAeDZeHe97EKCkY8Mfy3zFf3mj3Y6dIiUivcKT-ntKlFBF97L3k5dl6mdyJzS8TKQQ/exec?uid=[[uid]]&name=[[snsname]]&ref_code=[[free2]]` |
| フォーム送信時（form_8） | `https://script.google.com/macros/s/AKfycbyXPAeDZeHe97EKCkY8Mfy3zFf3mj3Y6dIiUivcKT-ntKlFBF97L3k5dl6mdyJzS8TKQQ/exec` （POST） |

---

### 2. メッセージ送信（proline-form-message-sender）

| 項目 | 値 |
| --- | --- |
| ローカル正本 | `GAS/proline/proline_form_message_sender.gs` |
| scriptId | `1FohG722QZcXH3oAeep3kH9jgGipWj93_odOpP2LlZY_cDMOByUbYPWSz` |
| Apps Script 編集先 | `https://script.google.com/home/projects/1FohG722QZcXH3oAeep3kH9jgGipWj93_odOpP2LlZY_cDMOByUbYPWSz/edit` |
| デプロイ URL | `https://script.google.com/macros/s/AKfycbzyxevEbPuU_-Gj24TYWKMOkmHWEdmi2ea4VlgTxouVE60G-9Fv_S5AP7ROOo3HUTyj/exec` |
| 環境変数 | `PROLINE_MESSAGE_SENDER_URL` |
| 最終デプロイ | 2026-05-01 version 1 |

**機能詳細**

- `POST` で JSON `{ "userId": "xxx", "messageContent": "本文" }` を受け取り、旧公式 LINE アカウントの ProLine フォーム API へ転送する。
- 8時スキル（`daily_calendar_summary.py`）が `[予約]在宅ワーク面談` のカレンダー予定を検出した際に呼び出す。
- ProLine フォーム URL は旧アカウント用。

---

## 新 公式 LINE アカウント

### 3. 友達追加 & フォーム受信（proline-new-friend-sync）

| 項目 | 値 |
| --- | --- |
| ローカル正本 | `GAS/proline/proline-new-friend-sync/` |
| scriptId | `1uK_EpMKs7wZy5c-U3GKlqmjLDiDPCKPV5zsYhiJO8cWbEwtqCfLVJ98v` |
| Apps Script 編集先 | `https://script.google.com/home/projects/1uK_EpMKs7wZy5c-U3GKlqmjLDiDPCKPV5zsYhiJO8cWbEwtqCfLVJ98v/edit` |
| デプロイ URL | `https://script.google.com/macros/s/AKfycbwvqBiTA7EevpA1D2JIzbaknfL0Si6ZKUOAZHJMH7l0ortuuE9-YJMGjRCkVlIE2vDP/exec` |
| 書き込み先スプレッドシート | `1BQOswkbIBjzMdya5MICAMBcMmrJWd7rXLANPbSDc5m4` |
| 最終デプロイ | 2026-06-09 version 1 |

**機能詳細**

- `GET /?uid=...` → 新公式 LINE アカウントの友達追加トリガー。`新友達追加情報` シートへ upsert する。
- `POST` → ユーザーが **新アカウントのアンケートフォーム（form9）** を送信したとき、ProLine がこの GAS へ POST webhook を送る。受け取ったデータを `form_8：在宅ワーク面談前アンケート` シートへ追記する。
- `新旧` 列には **「新」** を書き込む。
- その他の紹介者補完・重複チェックロジックは旧と同じ。

**データフロー（フォーム送信）**

```
ユーザーがフォームを入力・送信
  → https://ks215tqw.autosns.app/fm/bU7dgK2ysL?uid=[[uid]]  （ProLine form9）
  → ProLine が自動で POST webhook を送信
  → proline-new-friend-sync （このGAS）
  → スプレッドシート「form_8：在宅ワーク面談前アンケート」へ追記
     └ 「新旧」列に「新」を書き込む
```

**ProLine 管理画面での設定箇所（新アカウント）**

| イベント | 設定する URL |
| --- | --- |
| 友達追加時 | `https://script.google.com/macros/s/AKfycbwvqBiTA7EevpA1D2JIzbaknfL0Si6ZKUOAZHJMH7l0ortuuE9-YJMGjRCkVlIE2vDP/exec?uid=[[uid]]&name=[[snsname]]&ref_code=[[free2]]` |
| フォーム（form9）送信時 | `https://script.google.com/macros/s/AKfycbwvqBiTA7EevpA1D2JIzbaknfL0Si6ZKUOAZHJMH7l0ortuuE9-YJMGjRCkVlIE2vDP/exec` （POST） |

> **注意**: `proline-new-account-sender`（#4）も同じ `bU7dgK2ysL` フォームURLを使うが役割が逆。
> - `proline-new-friend-sync`: ユーザーがフォームを送信したときに **受け取る** GAS（inbound webhook）
> - `proline-new-account-sender`: 8時スキルがユーザーへメッセージを **送る** GAS（outbound API呼び出し）

---

### 4. メッセージ送信（proline-new-account-sender）

| 項目 | 値 |
| --- | --- |
| ローカル正本 | `GAS/proline/proline-new-account-sender/` |
| scriptId | `1VC-E5EIsUSn1alOJovi_k8_Uv-qtmSWoRKkBKwCQBKSOtvR7IotH-ALd` |
| Apps Script 編集先 | `https://script.google.com/home/projects/1VC-E5EIsUSn1alOJovi_k8_Uv-qtmSWoRKkBKwCQBKSOtvR7IotH-ALd/edit` |
| デプロイ URL | `https://script.google.com/macros/s/AKfycbxIhxnW7vGfw45tMt5AWbe4g6pT2kA9-Ln4hKEdrj0ol_DxbBZjfImsZI5jN_b2fRbfgw/exec` |
| 環境変数 | `PROLINE_NEW_MESSAGE_SENDER_URL` |
| 最終デプロイ | 2026-06-09 version 1 |

**機能詳細**

- `POST` で JSON `{ "userId": "xxx", "messageContent": "本文" }` を受け取り、新公式 LINE アカウントの ProLine フォーム API へ転送する。
- 8時スキル（`daily_calendar_summary.py`）が `[予約]（新）在宅ワーク面談` のカレンダー予定を検出した際に呼び出す。
- フォーム URL: `https://ks215tqw.autosns.app/fm/bU7dgK2ysL` / フィールドキー: `form9`

---

## 8時スキルとの連携

`daily_calendar_summary.py` はカレンダー予定タイトルに応じて呼び出す LINE アカウントを切り替える。

| タイトルのキーワード（部分一致） | 使用するアカウント | 環境変数 | 送信先 GAS |
| --- | --- | --- | --- |
| `[予約]（新）在宅ワーク面談` を含む | **新** 公式 LINE | `PROLINE_NEW_MESSAGE_SENDER_URL` | proline-new-account-sender |
| それ以外（デフォルト） | **旧** 公式 LINE | `PROLINE_MESSAGE_SENDER_URL` | proline-form-message-sender |

**`~/.config/team-info/env.sh` に追加が必要な変数**

```bash
export PROLINE_NEW_MESSAGE_SENDER_URL="https://script.google.com/macros/s/AKfycbxIhxnW7vGfw45tMt5AWbe4g6pT2kA9-Ln4hKEdrj0ol_DxbBZjfImsZI5jN_b2fRbfgw/exec"
```

---

## 共通スプレッドシート

スプレッドシート ID: `1BQOswkbIBjzMdya5MICAMBcMmrJWd7rXLANPbSDc5m4`

| シート名 | 書き込み元 | 用途 |
| --- | --- | --- |
| `友達追加情報` | proline-free-referral-sync（旧） | 旧アカウントの友達追加履歴 |
| `新友達追加情報` | proline-new-friend-sync（新） | 新アカウントの友達追加履歴 |
| `form_8：在宅ワーク面談前アンケート` | 旧・新どちらも書き込む | フォーム回答（`新旧` 列で判別） |
| `アフィリエイター情報` | 参照のみ | 紹介者コード→名前のマスタ |
