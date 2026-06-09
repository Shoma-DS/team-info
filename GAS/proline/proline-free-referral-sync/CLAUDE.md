# proline-free-referral-sync

このフォルダは、プロラインフリーの友達追加 GET とフォーム回答 POST を、1 本の GAS Web アプリで受ける個人用コードを置く場所です。

## ファイル

- `Code.gs`: Web アプリ本体
- `appsscript.json`: Apps Script マニフェスト
- `README.md`: 設定とデプロイ手順

## 前提

- 友だち追加の書き込み先は `友達追加情報`
- フォーム回答の書き込み先は `form_8：在宅ワーク面談前アンケート`
- 紹介者マスタは `アフィリエイター情報`
- どちらもスプレッドシート ID `1BQOswkbIBjzMdya5MICAMBcMmrJWd7rXLANPbSDc5m4` を使う
