# ProLine GAS Deployment Inventory

プロライン関係の GAS について、Apps Script の編集先 URL、実行用デプロイ URL、機能の概要をまとめる台帳です。
`gws` で新規デプロイまたは再デプロイをしたら、このファイルを同じターンで更新します。

## 確認できた gws デプロイ済み

| ローカル正本 | scriptId | Apps Script 編集先 | デプロイ URL | 機能の概要 | 状態 |
| --- | --- | --- | --- | --- | --- |
| `GAS/proline/proline-free-referral-sync/` | `1bEsFW9qhDRTWaN88HilgxXGwh_7l-VXWRTDqAtKznxBeqGn2tI9S2NEX` | `https://script.google.com/home/projects/1bEsFW9qhDRTWaN88HilgxXGwh_7l-VXWRTDqAtKznxBeqGn2tI9S2NEX/edit` | `https://script.google.com/macros/s/AKfycbyXPAeDZeHe97EKCkY8Mfy3zFf3mj3Y6dIiUivcKT-ntKlFBF97L3k5dl6mdyJzS8TKQQ/exec` | 旧公式LINE。友だち追加 GET とフォーム回答 POST を受ける。`友達追加情報` と `form_8` へ書き込み、`新旧` 列に「旧」を記録。 | 2026-06-09 version 7 へ更新。新旧フラグ追加・送信日バグ修正。 |
| `GAS/proline/proline_form_message_sender.gs` | `1FohG722QZcXH3oAeep3kH9jgGipWj93_odOpP2LlZY_cDMOByUbYPWSz` | `https://script.google.com/home/projects/1FohG722QZcXH3oAeep3kH9jgGipWj93_odOpP2LlZY_cDMOByUbYPWSz/edit` | `https://script.google.com/macros/s/AKfycbzyxevEbPuU_-Gj24TYWKMOkmHWEdmi2ea4VlgTxouVE60G-9Fv_S5AP7ROOo3HUTyj/exec` | 旧公式LINE メッセージ送信。JSON で `userId` と `messageContent` を受け取り ProLine フォーム API へ転送。環境変数: `PROLINE_MESSAGE_SENDER_URL` | 2026-05-01 version 1 初回デプロイ。 |
| `GAS/proline/proline-new-account-sender/` | `1VC-E5EIsUSn1alOJovi_k8_Uv-qtmSWoRKkBKwCQBKSOtvR7IotH-ALd` | `https://script.google.com/home/projects/1VC-E5EIsUSn1alOJovi_k8_Uv-qtmSWoRKkBKwCQBKSOtvR7IotH-ALd/edit` | `https://script.google.com/macros/s/AKfycbxIhxnW7vGfw45tMt5AWbe4g6pT2kA9-Ln4hKEdrj0ol_DxbBZjfImsZI5jN_b2fRbfgw/exec` | 新公式LINE メッセージ送信。フォーム URL `bU7dgK2ysL` / フィールドキー `form9`。環境変数: `PROLINE_NEW_MESSAGE_SENDER_URL` | 2026-06-09 version 1 初回デプロイ。 |
| `GAS/proline/proline-new-friend-sync/` | `1uK_EpMKs7wZy5c-U3GKlqmjLDiDPCKPV5zsYhiJO8cWbEwtqCfLVJ98v` | `https://script.google.com/home/projects/1uK_EpMKs7wZy5c-U3GKlqmjLDiDPCKPV5zsYhiJO8cWbEwtqCfLVJ98v/edit` | `https://script.google.com/macros/s/AKfycbwvqBiTA7EevpA1D2JIzbaknfL0Si6ZKUOAZHJMH7l0ortuuE9-YJMGjRCkVlIE2vDP/exec` | 新公式LINE。友だち追加 GET とフォーム回答 POST を受ける。`新友達追加情報` と `form_8` へ書き込み、`新旧` 列に「新」を記録。 | 2026-06-09 version 1 初回デプロイ。 |

## ローカル資産だが gws デプロイ記録未確認

現在なし。

## 更新ルール

- ProLine 関係の GAS を `gws` でデプロイまたは再デプロイしたら、このファイルの該当行を同じターンで更新する。
- 追加する最低限の項目は、`scriptId`、編集先 URL、デプロイ URL、ローカル正本パス、機能の要約、確認日。
- 実行 URL が取れなかったときは空欄にせず、`未確認` と理由を書く。
