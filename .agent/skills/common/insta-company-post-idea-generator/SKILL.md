---
name: insta-company-post-idea-generator
description: 秘書ログとリサーチログをもとに、Instagram 投稿ネタと構成たたき台を content ログへ生成する。
---

# insta-company-post-idea-generator スキル

## 役割
- 秘書のメモとリサーチ結果から、今週使える投稿案を作る
- コンテンツ部の初稿として使える形にする

## 入力
- 秘書ログ
- リサーチログ
- ターゲット
- ジャンル

## 手順
1. `insta-company/CLAUDE.md` と `insta-company/employees/content/CLAUDE.md` を読む
2. 直近の秘書ログとリサーチログを確認する
3. `insta-company/employees/content/logs/YYYY-MM-DD.md` を作るか追記する
4. 次を 5 件前後出す
   - 投稿タイトル案
   - 向いている形式（カルーセル / リール / ストーリーズ）
   - フック
   - 構成の骨子
   - CTA
5. Instagram 向けに短く、会話調でまとめる

## 出力形式
```md
# YYYY-MM-DD

## 投稿案1
- 形式:
- タイトル:
- フック:
- 構成:
- CTA:
```

## Google Drive 共有が必要なとき
```bash
rclone copy "$TEAM_INFO_ROOT/insta-company/employees/content/logs/[ファイル名].md" "gdrive:1QKaUP9fvA46mINkpSR1b2wqrIBE6By0t/outputs/insta-company/" --progress
```
