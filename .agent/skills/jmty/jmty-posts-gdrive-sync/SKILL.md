---
name: jmty-posts-gdrive-sync
description: ジモティー投稿出力（factory/remote）をGoogleドライブへ同期コピーする。既存フォルダがある場合は上書き保存（差分同期）する。
---

# ジモティー投稿 Google Drive 同期スキル

## 目的
- `outputs/jmty/factory` と `outputs/jmty/remote` をGoogleドライブへコピーする。
- コピー先に同名フォルダがすでにある場合は、最新状態で上書き同期する。

## 同期仕様
- 方式: `rsync -a --delete`
- 意味:
- 追加/更新ファイルはコピー
- コピー元で削除されたファイルはコピー先からも削除

## デフォルトコピー先
- `/Users/deguchishouma/Library/CloudStorage/GoogleDrive-syouma1674@gmail.com/マイドライブ/team-info/outputs/jmty/`

## 実行フロー
1. コピー元フォルダが存在するか確認する。
- `outputs/jmty/factory`
- `outputs/jmty/remote`
2. `.agent/skills/jmty/jmty-posts-gdrive-sync/scripts/sync_jmty_posts_to_gdrive.sh` を実行する。
3. 実行後、同期先に `factory` と `remote` が存在することを確認する。

## 実行コマンド
```bash
bash .agent/skills/jmty/jmty-posts-gdrive-sync/scripts/sync_jmty_posts_to_gdrive.sh
```

## 引数でコピー先を変更する場合
```bash
bash .agent/skills/jmty/jmty-posts-gdrive-sync/scripts/sync_jmty_posts_to_gdrive.sh "<destination_root>"
```

## 完了報告
- 同期したソース
- 同期先パス
- 実行結果（成功/失敗）
