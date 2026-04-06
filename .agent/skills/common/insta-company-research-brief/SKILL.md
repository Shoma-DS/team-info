---
name: insta-company-research-brief
description: Instagram 運用向けに、競合・バズ投稿・トレンドを整理して research ログへ落とし込む。
---

# insta-company-research-brief スキル

## 役割
- Instagram 運用のネタ元になる調査ログを作る
- 伸びた理由を構造化し、再利用できる形にする

## 入力
- 調べたいジャンル
- 競合候補
- 最近気になるテーマ

## 手順
1. `insta-company/CLAUDE.md` と `insta-company/employees/research/CLAUDE.md` を読む
2. 必要なら秘書ログの引き継ぎを見る
3. 今日の日付で `insta-company/employees/research/logs/YYYY-MM-DD.md` を作るか追記する
4. 次をまとめる
   - 競合アカウント
   - バズ投稿観察
   - なぜ伸びたか
   - 今週のおすすめネタ
5. 結論は、コンテンツ部がすぐ使える粒度で書く

## 出力形式
```md
# YYYY-MM-DD

## 競合アカウント
- アカウント名: 見るべき理由

## バズ投稿観察
- 投稿: 伸びた要因

## 再現パターン
- ...

## 今週のおすすめネタ
- ...
```

## Google Drive 共有が必要なとき
```bash
rclone copy "$TEAM_INFO_ROOT/insta-company/employees/research/logs/[ファイル名].md" "gdrive:1QKaUP9fvA46mINkpSR1b2wqrIBE6By0t/outputs/insta-company/" --progress
```
